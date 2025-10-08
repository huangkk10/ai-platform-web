"""
Chat Vector Service - 聊天消息向量化服務

此模組負責：
- 將聊天消息轉換為 1024 維向量
- 管理 chat_message_embeddings_1024 表
- 提供向量搜索和相似度計算
- 支持批量處理和增量更新
"""

import logging
import hashlib
import re
from typing import List, Dict, Optional, Any, Tuple
from django.db import connection, transaction
from django.conf import settings

# 導入 embedding 服務
try:
    from api.services.embedding_service import get_embedding_service
    EMBEDDING_SERVICE_AVAILABLE = True
except ImportError:
    EMBEDDING_SERVICE_AVAILABLE = False
    logging.warning("Embedding service 不可用")

logger = logging.getLogger(__name__)

class ChatVectorService:
    """聊天消息向量化服務"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.embedding_service = None
        if EMBEDDING_SERVICE_AVAILABLE:
            self.embedding_service = get_embedding_service('ultra_high')  # 使用 1024 維模型
    
    def generate_content_hash(self, content: str) -> str:
        """生成內容雜湊值"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def extract_keywords(self, content: str, max_keywords: int = 10) -> List[str]:
        """
        提取關鍵字
        
        Args:
            content: 文本內容
            max_keywords: 最大關鍵字數量
            
        Returns:
            關鍵字列表
        """
        try:
            # 簡單的關鍵字提取（可以後續優化為更複雜的 NLP）
            # 移除標點符號和多餘空格
            clean_content = re.sub(r'[^\w\s]', ' ', content)
            words = clean_content.split()
            
            # 過濾短詞和常用詞
            stop_words = {'的', '是', '在', '有', '和', '就', '不', '了', '我', '你', '他', '她', '它',
                         'the', 'is', 'in', 'and', 'or', 'not', 'a', 'an', 'to', 'for', 'of', 'with'}
            
            keywords = []
            for word in words:
                if len(word) > 1 and word.lower() not in stop_words:
                    keywords.append(word)
            
            # 去重並限制數量
            unique_keywords = list(dict.fromkeys(keywords))[:max_keywords]
            return unique_keywords
            
        except Exception as e:
            self.logger.error(f"關鍵字提取失敗: {str(e)}")
            return []
    
    def detect_language(self, content: str) -> str:
        """
        檢測語言
        
        Args:
            content: 文本內容
            
        Returns:
            語言代碼 (zh/en)
        """
        try:
            # 簡單的語言檢測
            chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', content))
            english_chars = len(re.findall(r'[a-zA-Z]', content))
            
            if chinese_chars > english_chars:
                return 'zh'
            elif english_chars > 0:
                return 'en'
            else:
                return 'zh'  # 預設中文
                
        except Exception as e:
            self.logger.error(f"語言檢測失敗: {str(e)}")
            return 'zh'
    
    def generate_and_store_vector(self, chat_message_id: int, content: str, 
                                conversation_id: Optional[int] = None,
                                user_role: str = 'user') -> bool:
        """
        為聊天消息生成並存儲向量
        
        Args:
            chat_message_id: 聊天消息 ID
            content: 消息內容
            conversation_id: 對話 ID
            user_role: 用戶角色
            
        Returns:
            是否成功
        """
        try:
            if not self.embedding_service:
                self.logger.warning("Embedding service 不可用，跳過向量生成")
                return False
            
            # 生成內容雜湊
            content_hash = self.generate_content_hash(content)
            
            # 檢查是否已存在
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT id FROM chat_message_embeddings_1024 WHERE chat_message_id = %s",
                    [chat_message_id]
                )
                if cursor.fetchone():
                    self.logger.info(f"聊天消息 {chat_message_id} 的向量已存在，跳過")
                    return True
            
            # 生成向量
            embedding = self.embedding_service.generate_embedding(content)
            if not embedding:
                self.logger.error(f"向量生成失敗: chat_message_id={chat_message_id}")
                return False
            
            # 提取元數據
            keywords = self.extract_keywords(content)
            language = self.detect_language(content)
            message_length = len(content)
            
            # 存儲到資料庫
            with connection.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO chat_message_embeddings_1024 
                    (chat_message_id, conversation_id, text_content, embedding, content_hash,
                     user_role, message_length, question_keywords, language_detected, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (chat_message_id) DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        embedding = EXCLUDED.embedding,
                        content_hash = EXCLUDED.content_hash,
                        message_length = EXCLUDED.message_length,
                        question_keywords = EXCLUDED.question_keywords,
                        language_detected = EXCLUDED.language_detected,
                        updated_at = NOW()
                """, [
                    chat_message_id, conversation_id, content, embedding, content_hash,
                    user_role, message_length, keywords, language
                ])
            
            self.logger.info(f"聊天消息向量存儲成功: chat_message_id={chat_message_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"生成和存儲向量失敗: {str(e)}")
            return False
    
    def search_similar_messages(self, query: str, limit: int = 10, 
                              threshold: float = 0.3, 
                              user_role: str = 'user') -> List[Dict]:
        """
        搜索相似的聊天消息
        
        Args:
            query: 查詢文本
            limit: 返回數量限制
            threshold: 相似度閾值
            user_role: 用戶角色過濾
            
        Returns:
            相似消息列表
        """
        try:
            if not self.embedding_service:
                self.logger.warning("Embedding service 不可用")
                return []
            
            # 生成查詢向量
            query_embedding = self.embedding_service.generate_embedding(query)
            if not query_embedding:
                self.logger.error("查詢向量生成失敗")
                return []
            
            # 向量相似度搜索
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        chat_message_id,
                        conversation_id,
                        text_content,
                        predicted_category,
                        cluster_id,
                        confidence_score,
                        message_length,
                        question_keywords,
                        language_detected,
                        created_at,
                        (embedding <=> %s::vector) as distance,
                        (1 - (embedding <=> %s::vector)) as similarity
                    FROM chat_message_embeddings_1024
                    WHERE user_role = %s
                    AND (embedding <=> %s::vector) < %s
                    ORDER BY embedding <=> %s::vector
                    LIMIT %s
                """, [
                    query_embedding, query_embedding, user_role, 
                    query_embedding, 1 - threshold, query_embedding, limit
                ])
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    result['similarity'] = float(result['similarity'])
                    result['distance'] = float(result['distance'])
                    results.append(result)
                
                return results
                
        except Exception as e:
            self.logger.error(f"搜索相似消息失敗: {str(e)}")
            return []
    
    def batch_process_messages(self, chat_messages: List[Dict]) -> Dict:
        """
        批量處理聊天消息向量化
        
        Args:
            chat_messages: 聊天消息列表 [{'id': int, 'content': str, 'conversation_id': int, 'role': str}, ...]
            
        Returns:
            處理結果統計
        """
        results = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'errors': []
        }
        
        try:
            for msg in chat_messages:
                results['total_processed'] += 1
                
                try:
                    success = self.generate_and_store_vector(
                        chat_message_id=msg['id'],
                        content=msg['content'],
                        conversation_id=msg.get('conversation_id'),
                        user_role=msg.get('role', 'user')
                    )
                    
                    if success:
                        results['successful'] += 1
                    else:
                        results['failed'] += 1
                        
                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append({
                        'message_id': msg['id'],
                        'error': str(e)
                    })
            
            self.logger.info(f"批量處理完成: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"批量處理失敗: {str(e)}")
            results['errors'].append({'general_error': str(e)})
            return results
    
    def get_embedding_stats(self) -> Dict:
        """
        獲取向量化統計資訊
        
        Returns:
            統計資訊
        """
        try:
            with connection.cursor() as cursor:
                # 基本統計
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_embeddings,
                        COUNT(DISTINCT conversation_id) as unique_conversations,
                        COUNT(CASE WHEN user_role = 'user' THEN 1 END) as user_messages,
                        COUNT(CASE WHEN user_role = 'assistant' THEN 1 END) as assistant_messages,
                        COUNT(CASE WHEN predicted_category IS NOT NULL THEN 1 END) as categorized_messages,
                        COUNT(CASE WHEN cluster_id IS NOT NULL THEN 1 END) as clustered_messages,
                        AVG(message_length) as avg_message_length,
                        AVG(confidence_score) as avg_confidence_score
                    FROM chat_message_embeddings_1024
                """)
                
                basic_stats = dict(zip(
                    [col[0] for col in cursor.description],
                    cursor.fetchone()
                ))
                
                # 語言分布
                cursor.execute("""
                    SELECT language_detected, COUNT(*) as count
                    FROM chat_message_embeddings_1024
                    GROUP BY language_detected
                """)
                
                language_distribution = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 類別分布
                cursor.execute("""
                    SELECT predicted_category, COUNT(*) as count
                    FROM chat_message_embeddings_1024
                    WHERE predicted_category IS NOT NULL
                    GROUP BY predicted_category
                    ORDER BY count DESC
                """)
                
                category_distribution = {row[0]: row[1] for row in cursor.fetchall()}
                
                # 聚類分布
                cursor.execute("""
                    SELECT cluster_id, COUNT(*) as count
                    FROM chat_message_embeddings_1024
                    WHERE cluster_id IS NOT NULL
                    GROUP BY cluster_id
                    ORDER BY count DESC
                """)
                
                cluster_distribution = {row[0]: row[1] for row in cursor.fetchall()}
                
                return {
                    'basic_stats': basic_stats,
                    'language_distribution': language_distribution,
                    'category_distribution': category_distribution,
                    'cluster_distribution': cluster_distribution
                }
                
        except Exception as e:
            self.logger.error(f"獲取統計資訊失敗: {str(e)}")
            return {'error': str(e)}
    
    def delete_message_embedding(self, chat_message_id: int) -> bool:
        """
        刪除聊天消息的向量
        
        Args:
            chat_message_id: 聊天消息 ID
            
        Returns:
            是否成功
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM chat_message_embeddings_1024 WHERE chat_message_id = %s",
                    [chat_message_id]
                )
                deleted_count = cursor.rowcount
                
            self.logger.info(f"刪除向量成功: chat_message_id={chat_message_id}, 刪除數量={deleted_count}")
            return deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"刪除向量失敗: {str(e)}")
            return False

# 便利函數
def get_chat_vector_service() -> ChatVectorService:
    """獲取聊天向量服務實例"""
    return ChatVectorService()

def generate_message_vector(chat_message_id: int, content: str, 
                          conversation_id: Optional[int] = None) -> bool:
    """生成消息向量便利函數"""
    service = get_chat_vector_service()
    return service.generate_and_store_vector(chat_message_id, content, conversation_id)

def search_similar_chat_messages(query: str, limit: int = 10, threshold: float = 0.3) -> List[Dict]:
    """搜索相似聊天消息便利函數"""
    service = get_chat_vector_service()
    return service.search_similar_messages(query, limit, threshold)