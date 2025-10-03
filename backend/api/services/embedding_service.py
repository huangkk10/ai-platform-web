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
    
    def __init__(self, model_type: str = 'standard'):
        """
        初始化嵌入服務
        
        Args:
            model_type: 模型類型 ('lightweight', 'standard', 'high_precision')
        """
        if model_type not in self.MODEL_CONFIGS:
            # 如果是舊的模型名稱，回退到輕量級模型
            if isinstance(model_type, str) and 'MiniLM' in model_type:
                model_type = 'lightweight'
            else:
                model_type = 'standard'  # 默認使用 768 維標準模型
            
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
            target_table = 'document_embeddings_1024' if use_1024_table else 'document_embeddings'
            
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
            target_table = 'document_embeddings_1024' if use_1024_table else 'document_embeddings'
            
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

def search_rvt_guide_with_vectors(query: str, limit: int = 5, threshold: float = 0.3) -> List[dict]:
    """
    使用向量搜索 RVT Guide (1024維 - 預設)
    
    Args:
        query: 查詢文本
        limit: 返回結果數量
        threshold: 相似度閾值
        
    Returns:
        搜索結果列表
    """
    service = get_embedding_service()  # 現在預設使用 1024 維
    
    # 搜索相似向量
    vector_results = service.search_similar_documents(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        use_1024_table=True  # 使用新的 1024 維表格
    )
    
    if not vector_results:
        logger.info("向量搜索無結果")
        return []
    
    return _get_rvt_guide_results(vector_results, "1024維")

def search_rvt_guide_with_vectors_768_legacy(query: str, limit: int = 5, threshold: float = 0.3) -> List[dict]:
    """
    使用向量搜索 RVT Guide (768維 - 舊版本)
    
    Args:
        query: 查詢文本
        limit: 返回結果數量
        threshold: 相似度閾值
        
    Returns:
        搜索結果列表
    """
    service = get_embedding_service('standard')  # 使用768維模型
    
    # 搜索相似向量
    vector_results = service.search_similar_documents(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        use_1024_table=False  # 使用舊的768維表格
    )
    
    if not vector_results:
        logger.info("768維向量搜索無結果")
        return []
    
    return _get_rvt_guide_results(vector_results, "768維")

def _get_rvt_guide_results(vector_results: List[dict], version_info: str) -> List[dict]:
    """
    獲取 RVT Guide 的完整結果資料
    
    Args:
        vector_results: 向量搜索結果
        version_info: 版本資訊 (用於日誌)
        
    Returns:
        完整的 RVT Guide 結果列表
    """
    # 獲取完整的 RVT Guide 資料
    source_ids = [result['source_id'] for result in vector_results]
    
    try:
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(source_ids))
            cursor.execute(f"""
                SELECT 
                    id, title,
                    content,
                    created_at, updated_at
                FROM rvt_guide
                WHERE id IN ({placeholders})
            """, source_ids)
            
            columns = [desc[0] for desc in cursor.description]
            rvt_guides = {}
            
            for row in cursor.fetchall():
                rvt_data = dict(zip(columns, row))
                rvt_guides[rvt_data['id']] = rvt_data
        
        # 組合結果，保持向量搜索的順序
        final_results = []
        for vector_result in vector_results:
            source_id = vector_result['source_id']
            if source_id in rvt_guides:
                rvt_data = rvt_guides[source_id]
                
                # 格式化內容用於 Dify
                content = f"文檔標題: {rvt_data['title']}\n"
                content += f"內容: {rvt_data['content']}\n"
                
                final_results.append({
                    'id': str(source_id),
                    'title': rvt_data['title'],
                    'content': content,
                    'score': vector_result['similarity_score'],
                    'metadata': {
                        'source': f'rvt_guide_vector_search_{version_info}'
                    }
                })
        
        logger.info(f"向量搜索返回 {len(final_results)} 個 RVT Guide 結果 ({version_info})")
        return final_results
        
    except Exception as e:
        logger.error(f"獲取 RVT Guide 詳細資料失敗: {str(e)}")
        return []


def search_know_issue_with_vectors(query: str, top_k: int = 5, threshold: float = 0.3) -> List[dict]:
    """
    🆕 使用向量搜索 Know Issue (1024維)
    
    Args:
        query: 查詢文本
        top_k: 返回結果數量
        threshold: 相似度閾值
        
    Returns:
        搜索結果列表
    """
    try:
        service = get_embedding_service()  # 使用 1024 維模型
        
        # 搜索相似向量
        vector_results = service.search_similar_documents(
            query=query,
            source_table='know_issue',
            limit=top_k,
            use_1024_table=True  # 使用 1024 維表格
        )
        
        if not vector_results:
            logger.info("Know Issue 向量搜索無結果")
            return []
        
        return _get_know_issue_results(vector_results, "1024維")
        
    except Exception as e:
        logger.error(f"Know Issue 向量搜索失敗: {str(e)}")
        return []


def _get_know_issue_results(vector_results: List[dict], version_info: str) -> List[dict]:
    """
    🆕 從向量搜索結果獲取 Know Issue 詳細資料
    
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