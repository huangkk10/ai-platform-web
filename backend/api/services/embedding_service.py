"""
開源向量嵌入服務 - 替代 OpenAI Embedding API
使用 Sentence Transformers 來生成向量嵌入
"""
import logging
from typing import List, Optional, Union
import numpy as np
from sentence_transformers import SentenceTransformer
import hashlib
from django.conf import settings
from django.db import connection
import json

logger = logging.getLogger(__name__)

class OpenSourceEmbeddingService:
    """開源嵌入服務 - 使用 Sentence Transformers"""
    
    # 預定義模型配置
    MODEL_CONFIGS = {
        'lightweight': {
            'name': 'paraphrase-multilingual-MiniLM-L12-v2',
            'dimension': 384,
            'description': '輕量級多語言模型，平衡效能與精準度'
        },
        'standard': {
            'name': 'paraphrase-multilingual-mpnet-base-v2', 
            'dimension': 768,
            'description': '標準多語言模型，更高精準度'
        },
        'high_precision': {
            'name': 'sentence-transformers/all-mpnet-base-v2',
            'dimension': 768,
            'description': '高精準度模型，主要支援英文'
        },
        'ultra_high': {
            'name': 'intfloat/multilingual-e5-large',
            'dimension': 1024,
            'description': '超高精準度多語言模型，1024維向量'
        },
        'maximum': {
            'name': 'sentence-transformers/all-MiniLM-L6-v2',
            'dimension': 384,
            'description': '測試用 - 可擴展到1536維'
        }
    }
    
    def __init__(self, model_type: str = 'ultra_high'):
        """
        初始化嵌入服務
        
        Args:
            model_type: 模型類型 (預設: 'ultra_high' - 1024維多語言模型)
                       可選: 'lightweight' (384維), 'standard' (768維), 'high_precision' (768維)
        """
        if model_type not in self.MODEL_CONFIGS:
            # 如果是舊的模型名稱，回退到 ultra_high
            if isinstance(model_type, str) and 'MiniLM' in model_type:
                model_type = 'lightweight'
            else:
                model_type = 'ultra_high'  # 預設使用 1024 維模型（與資料庫一致）
            
        config = self.MODEL_CONFIGS[model_type]
        self.model_name = config['name']
        self.embedding_dimension = config['dimension']
        self.model_type = model_type
        self._model = None
        
        logger.info(f"選擇嵌入模型: {config['description']} ({self.embedding_dimension}維)")
        
    @property
    def model(self):
        """延遲載入模型"""
        if self._model is None:
            logger.info(f"載入 Sentence Transformers 模型: {self.model_name}")
            try:
                self._model = SentenceTransformer(self.model_name)
                logger.info("模型載入成功")
            except Exception as e:
                logger.error(f"模型載入失敗: {str(e)}")
                raise
        return self._model
    
    def generate_embedding(self, text: str) -> List[float]:
        """
        為單個文本生成向量嵌入
        
        Args:
            text: 要處理的文本
            
        Returns:
            向量嵌入列表
        """
        try:
            if not text or not text.strip():
                return [0.0] * self.embedding_dimension
                
            # 使用模型生成嵌入
            embedding = self.model.encode(text.strip())
            
            # 確保返回 Python 列表格式
            if isinstance(embedding, np.ndarray):
                embedding = embedding.tolist()
                
            return embedding
            
        except Exception as e:
            logger.error(f"生成嵌入失敗: {str(e)}")
            # 返回零向量作為備用
            return [0.0] * self.embedding_dimension
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        批量生成向量嵌入
        
        Args:
            texts: 文本列表
            
        Returns:
            向量嵌入列表的列表
        """
        try:
            if not texts:
                return []
                
            # 過濾空文本
            valid_texts = [text.strip() for text in texts if text and text.strip()]
            
            if not valid_texts:
                return [[0.0] * self.embedding_dimension] * len(texts)
            
            # 批量生成嵌入
            embeddings = self.model.encode(valid_texts)
            
            # 轉換為 Python 列表格式
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
                
            return embeddings
            
        except Exception as e:
            logger.error(f"批量生成嵌入失敗: {str(e)}")
            # 返回零向量作為備用
            return [[0.0] * self.embedding_dimension] * len(texts)
    
    def get_content_hash(self, content: str) -> str:
        """生成內容哈希值，用於檢查內容是否變更"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def store_document_embedding(self, source_table: str, source_id: int, content: str, use_1024_table: bool = False) -> bool:
        """
        存儲文檔嵌入到資料庫
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄ID
            content: 文檔內容
            use_1024_table: 是否使用 1024 維表格
            
        Returns:
            是否成功存儲
        """
        try:
            # 生成內容哈希
            content_hash = self.get_content_hash(content)
            
            # 選擇目標表格
            # 注意：document_embeddings 表已經是 1024 維，統一使用它
            target_table = 'document_embeddings'
            
            # 檢查是否已存在且內容未變更
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT content_hash FROM {target_table}
                    WHERE source_table = %s AND source_id = %s
                """, [source_table, source_id])
                
                existing = cursor.fetchone()
                if existing and existing[0] == content_hash:
                    logger.info(f"文檔 {source_table}:{source_id} 內容未變更，跳過嵌入生成")
                    return True
            
            # 生成嵌入向量
            embedding = self.generate_embedding(content)
            
            # 存儲到資料庫
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    INSERT INTO {target_table} (source_table, source_id, text_content, content_hash, embedding)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (source_table, source_id)
                    DO UPDATE SET 
                        text_content = EXCLUDED.text_content,
                        content_hash = EXCLUDED.content_hash,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """, [source_table, source_id, content, content_hash, json.dumps(embedding)])
                
            logger.info(f"成功存儲文檔嵌入到 {target_table}: {source_table}:{source_id}")
            return True
            
        except Exception as e:
            logger.error(f"存儲文檔嵌入失敗: {str(e)}")
            return False
    
    def delete_document_embedding(self, source_table: str, source_id: int, use_1024_table: bool = False) -> bool:
        """
        刪除指定文檔的向量嵌入
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄ID
            use_1024_table: 是否使用 1024 維表格
            
        Returns:
            是否成功刪除
        """
        try:
            # 選擇目標表格
            # 注意：document_embeddings 表已經是 1024 維，統一使用它
            target_table = 'document_embeddings'
            
            # 刪除向量記錄
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    DELETE FROM {target_table}
                    WHERE source_table = %s AND source_id = %s
                """, [source_table, source_id])
                
                deleted_count = cursor.rowcount
                
            if deleted_count > 0:
                table_name = "1024維" if use_1024_table else "768維"
                logger.info(f"成功刪除文檔嵌入 ({table_name}): {source_table}:{source_id}")
                return True
            else:
                logger.warning(f"未找到要刪除的文檔嵌入: {source_table}:{source_id}")
                return False
                
        except Exception as e:
            logger.error(f"刪除文檔嵌入失敗: {str(e)}")
            return False
    
    def search_similar_documents(self, query: str, source_table: str = None, limit: int = 5, threshold: float = 0.0, use_1024_table: bool = False) -> List[dict]:
        """
        搜索相似文檔
        
        Args:
            query: 查詢文本
            source_table: 限制搜索的來源表（可選）
            limit: 返回結果數量限制
            threshold: 相似度閾值
            use_1024_table: 是否使用 1024 維表格
            
        Returns:
            相似文檔列表
        """
        try:
            # 生成查詢向量
            query_embedding = self.generate_embedding(query)
            
            # 選擇目標表格
            # 注意：document_embeddings 表已經是 1024 維，統一使用它
            target_table = 'document_embeddings'
            
            # 構建 SQL 查詢
            sql_parts = []
            params = []
            
            if source_table:
                sql_parts.append("WHERE de.source_table = %s")
                params.append(source_table)
            
            sql = f"""
                SELECT 
                    de.source_table,
                    de.source_id,
                    1 - (de.embedding <=> %s) as similarity_score,
                    de.created_at,
                    de.updated_at
                FROM {target_table} de
                {' '.join(sql_parts)}
                ORDER BY de.embedding <=> %s
                LIMIT %s
            """
            
            params = [json.dumps(query_embedding)] + params + [json.dumps(query_embedding), limit]
            
            results = []
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                
                for row in cursor.fetchall():
                    source_table_name, source_id, similarity_score, created_at, updated_at = row
                    
                    # 過濾低於閾值的結果
                    if similarity_score >= threshold:
                        results.append({
                            'source_table': source_table_name,
                            'source_id': source_id,
                            'similarity_score': float(similarity_score),
                            'created_at': created_at,
                            'updated_at': updated_at
                        })
            
            table_name = "1024維" if use_1024_table else "768維"
            logger.info(f"向量搜索完成 ({table_name})，返回 {len(results)} 個結果")
            return results
            
        except Exception as e:
            logger.error(f"向量搜索失敗: {str(e)}")
            return []
    
    def store_document_embeddings_multi(
        self, 
        source_table: str, 
        source_id: int, 
        title: str,
        content: str,
        use_1024_table: bool = True
    ) -> bool:
        """
        為文檔生成並存儲標題和內容向量（方案 A：多向量方法）
        
        Args:
            source_table: 來源表名
            source_id: 來源記錄 ID
            title: 標題文本
            content: 內容文本
            use_1024_table: 是否使用 1024 維表（固定為 True）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 生成標題向量
            logger.info(f"生成標題向量: {source_table} ID {source_id}")
            title_embedding = self.generate_embedding(title) if title else [0.0] * self.embedding_dimension
            
            # 生成內容向量
            logger.info(f"生成內容向量: {source_table} ID {source_id}")
            content_embedding = self.generate_embedding(content) if content else [0.0] * self.embedding_dimension
            
            # 計算內容雜湊（用於檢測變更）
            combined_content = f"{title}|{content}"
            content_hash = hashlib.sha256(combined_content.encode()).hexdigest()
            
            # 存儲到資料庫（document_embeddings 表）
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO document_embeddings 
                        (source_table, source_id, text_content, content_hash, 
                         title_embedding, content_embedding, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (source_table, source_id) 
                    DO UPDATE SET
                        text_content = EXCLUDED.text_content,
                        content_hash = EXCLUDED.content_hash,
                        title_embedding = EXCLUDED.title_embedding,
                        content_embedding = EXCLUDED.content_embedding,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP;
                    """,
                    [
                        source_table,
                        source_id,
                        combined_content[:10000],  # 儲存前 10000 字元（提升 10 倍，涵蓋大部分文章）
                        content_hash,
                        json.dumps(title_embedding),
                        json.dumps(content_embedding),
                        json.dumps(title_embedding),  # 保留舊的 embedding 欄位（向後兼容）
                    ]
                )
            
            logger.info(f"✅ 多向量存儲成功: {source_table} ID {source_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 多向量存儲失敗: {source_table} ID {source_id}, 錯誤: {str(e)}")
            return False
    
    def search_similar_documents_multi(
        self, 
        query: str, 
        source_table: str = None, 
        limit: int = 5, 
        threshold: float = 0.0,
        title_weight: float = 0.6,
        content_weight: float = 0.4
    ) -> List[dict]:
        """
        使用多向量方法搜索相似文檔（方案 A：標題/內容分開計算）
        
        Args:
            query: 查詢文本
            source_table: 限制搜索的來源表
            limit: 返回結果數量
            threshold: 相似度閾值
            title_weight: 標題權重 (0.0 ~ 1.0)
            content_weight: 內容權重 (0.0 ~ 1.0)
        
        Returns:
            相似文檔列表（包含 title_score, content_score, final_score）
        """
        try:
            # 生成查詢向量
            query_embedding = self.generate_embedding(query)
            embedding_json = json.dumps(query_embedding)
            
            # 構建 SQL 查詢
            sql_parts = []
            params = []
            
            if source_table:
                sql_parts.append("WHERE de.source_table = %s")
                params.append(source_table)
            
            sql = f"""
                SELECT 
                    de.source_table,
                    de.source_id,
                    -- 標題相似度
                    1 - (de.title_embedding <=> %s::vector) as title_score,
                    -- 內容相似度
                    1 - (de.content_embedding <=> %s::vector) as content_score,
                    -- 加權最終分數
                    (%s * (1 - (de.title_embedding <=> %s::vector))) + 
                    (%s * (1 - (de.content_embedding <=> %s::vector))) as final_score,
                    de.created_at,
                    de.updated_at
                FROM document_embeddings de
                {' '.join(sql_parts)}
                ORDER BY final_score DESC
                LIMIT %s
            """
            
            # 準備參數
            query_params = [
                embedding_json,  # title_score
                embedding_json,  # content_score
                title_weight,    # title weight
                embedding_json,  # title weight calculation
                content_weight,  # content weight
                embedding_json,  # content weight calculation
            ]
            params = query_params + params + [limit]
            
            results = []
            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                
                for row in cursor.fetchall():
                    (source_table_name, source_id, title_score, content_score, 
                     final_score, created_at, updated_at) = row
                    
                    # 過濾低於閾值的結果
                    if final_score >= threshold:
                        # 判斷匹配類型
                        if title_score > content_score * 1.5:
                            match_type = 'title_primary'
                        elif content_score > title_score * 1.5:
                            match_type = 'content_primary'
                        else:
                            match_type = 'balanced'
                        
                        results.append({
                            'source_table': source_table_name,
                            'source_id': source_id,
                            'title_score': float(title_score),
                            'content_score': float(content_score),
                            'similarity_score': float(final_score),  # 向後兼容
                            'final_score': float(final_score),
                            'match_type': match_type,
                            'weights': {
                                'title': title_weight,
                                'content': content_weight
                            },
                            'created_at': created_at,
                            'updated_at': updated_at
                        })
            
            logger.info(
                f"多向量搜索完成，返回 {len(results)} 個結果 "
                f"(weights: title={title_weight}, content={content_weight})"
            )
            return results
            
        except Exception as e:
            logger.error(f"多向量搜索失敗: {str(e)}")
            return []

# 全局服務實例
_embedding_service = None

def get_embedding_service(model_type: str = 'ultra_high') -> OpenSourceEmbeddingService:
    """
    獲取全局嵌入服務實例
    
    Args:
        model_type: 模型類型 ('lightweight', 'standard', 'high_precision', 'ultra_high')
                   - lightweight: 384維，速度快，適合小規模應用
                   - standard: 768維，平衡精準度與效能
                   - high_precision: 768維，最高精準度
                   - ultra_high: 1024維，最佳精準度 (默認)
    """
    global _embedding_service
    if _embedding_service is None or _embedding_service.model_type != model_type:
        logger.info(f"初始化嵌入服務，模型類型: {model_type}")
        _embedding_service = OpenSourceEmbeddingService(model_type)
    return _embedding_service

def search_rvt_guide_with_vectors(query: str, limit: int = 5, threshold: float = 0.3, search_mode: str = 'auto') -> List[dict]:
    """
    使用向量搜索 RVT Guide (1024維 - 預設)
    
    ⚠️ 向後兼容函數 - 已重構使用 RVTGuideSearchService
    🔗 新代碼建議直接使用 RVTGuideSearchService.search_knowledge()
    
    Args:
        query: 查詢文本
        limit: 返回結果數量
        threshold: 相似度閾值
        search_mode: 搜索模式 ('auto', 'section_only', 'document_only')
        
    Returns:
        搜索結果列表
    """
    from library.rvt_guide.search_service import RVTGuideSearchService
    
    # ✅ 使用 RVTGuideSearchService（支援 search_mode）
    service = RVTGuideSearchService()
    return service.search_with_vectors(
        query=query,
        limit=limit,
        threshold=threshold,
        search_mode=search_mode
    )

# ✅ 768維相關函數已移除（2025-01-XX）
# 原因：系統已全面改用 1024 維向量，768 維相關程式碼已廢棄
# 參考：/docs/vector-search/vector-dimension-default-change-report.md


def _format_rvt_guide_content(item):
    """
    RVT Guide 特殊的內容格式化邏輯
    
    包含圖片檢測和提示
    """
    content = f"文檔標題: {item.title}\n"
    
    # 檢查是否包含圖片
    has_images = any(keyword in item.content.lower() for keyword in [
        '🖼️', '--- 相關圖片 ---', '圖片', '截圖', 'image', 'picture'
    ])
    
    if has_images:
        content += "📸 **重要：此內容包含相關圖片說明，請在回答時提及並引導用戶查看圖片資訊**\n\n"
    
    content += f"內容: {item.content}\n"
    return content


def search_know_issue_with_vectors(query: str, top_k: int = 5, threshold: float = 0.3) -> List[dict]:
    """
    使用向量搜索 Know Issue (1024維)
    
    ⚠️ 向後兼容函數 - 已重構使用 vector_search_helper
    🔗 新代碼建議直接使用 KnowIssueSearchService.search_knowledge()
    
    Args:
        query: 查詢文本
        top_k: 返回結果數量
        threshold: 相似度閾值
        
    Returns:
        搜索結果列表
    """
    from library.common.knowledge_base.vector_search_helper import search_with_vectors_generic
    from api.models import KnowIssue
    
    # 使用通用 helper（內部會自動處理 DB 查詢和格式化）
    return search_with_vectors_generic(
        query=query,
        model_class=KnowIssue,
        source_table='know_issue',
        limit=top_k,
        threshold=threshold,
        use_1024=True
    )


def _get_know_issue_results(vector_results: List[dict], version_info: str) -> List[dict]:
    """
    ⚠️ DEPRECATED - 已棄用，保留以防回滾需要
    
    此函數已被 vector_search_helper.format_vector_results() 取代
    新代碼請使用 search_with_vectors_generic() 或 KnowIssueSearchService
    
    從向量搜索結果獲取 Know Issue 詳細資料
    
    Args:
        vector_results: 向量搜索原始結果
        version_info: 版本信息（用於日誌）
        
    Returns:
        格式化的搜索結果
    """
    try:
        # 提取 source_id 列表
        source_ids = [result['source_id'] for result in vector_results]
        
        if not source_ids:
            return []
        
        # 從資料庫獲取 Know Issue 詳細資料
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(source_ids))
            cursor.execute(f"""
                SELECT 
                    ki.id, ki.issue_id, ki.project, ki.test_version,
                    ki.issue_type, ki.status, ki.error_message,
                    ki.supplement, ki.script, ki.jira_number,
                    ki.created_at, ki.updated_at,
                    tc.name as test_class_name
                FROM know_issue ki
                LEFT JOIN protocol_test_class tc ON ki.test_class_id = tc.id
                WHERE ki.id IN ({placeholders})
            """, source_ids)
            
            columns = [desc[0] for desc in cursor.description]
            know_issues = {}
            
            for row in cursor.fetchall():
                issue_data = dict(zip(columns, row))
                know_issues[issue_data['id']] = issue_data
        
        # 組合結果，保持向量搜索的順序
        final_results = []
        for vector_result in vector_results:
            source_id = vector_result['source_id']
            if source_id in know_issues:
                issue_data = know_issues[source_id]
                
                # 格式化內容用於 Dify
                content = f"問題編號: {issue_data['issue_id']}\n"
                content += f"專案: {issue_data['project']}\n"
                content += f"問題類型: {issue_data['issue_type']}\n"
                content += f"狀態: {issue_data['status']}\n"
                content += f"錯誤訊息: {issue_data['error_message']}\n"
                if issue_data['supplement']:
                    content += f"補充說明: {issue_data['supplement']}\n"
                if issue_data['script']:
                    content += f"相關腳本: {issue_data['script']}\n"
                
                final_results.append({
                    'id': str(source_id),
                    'title': f"{issue_data['issue_id']} - {issue_data['project']}",
                    'content': content,
                    'score': vector_result['similarity_score'],
                    'metadata': {
                        'source': f'know_issue_vector_search_{version_info}',
                        'issue_id': issue_data['issue_id'],
                        'project': issue_data['project'],
                        'issue_type': issue_data['issue_type'],
                        'status': issue_data['status']
                    }
                })
        
        logger.info(f"向量搜索返回 {len(final_results)} 個 Know Issue 結果 ({version_info})")
        return final_results
        
    except Exception as e:
        logger.error(f"獲取 Know Issue 詳細資料失敗: {str(e)}")
        return []