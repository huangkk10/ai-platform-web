"""
AI OCR 搜索服務

處理所有 AI OCR 相關的搜索功能：
- OCR Storage Benchmark 搜索
- 搜索結果格式化
- Dify 響應格式轉換

提供統一的搜索介面，減少 views.py 中的重複程式碼
"""

import logging
from django.db import connection

logger = logging.getLogger(__name__)


class AIOCRSearchService:
    """AI OCR 搜索服務 - 統一管理所有 AI OCR 搜索功能"""
    
    def __init__(self):
        self.logger = logger
        
    def search_ocr_storage_benchmark(self, query_text, limit=5):
        """
        PostgreSQL 全文搜索 OCR 存儲基準測試資料
        
        Args:
            query_text (str): 搜索查詢文本
            limit (int): 返回結果數量限制
            
        Returns:
            list: 搜索結果列表
        """
        try:
            # 首先嘗試使用 library 中的 DatabaseSearchService
            try:
                from library.data_processing.database_search import DatabaseSearchService
                service = DatabaseSearchService()
                return service.search_ocr_storage_benchmark(query_text, limit)
            except ImportError:
                # 如果 DatabaseSearchService 不可用，使用本地實現
                self.logger.warning("DatabaseSearchService 不可用，使用本地實現")
                return self._local_search_ocr_storage_benchmark(query_text, limit)
                
        except Exception as e:
            self.logger.error(f"OCR Storage Benchmark 搜索失敗: {str(e)}")
            return []
    
    def _local_search_ocr_storage_benchmark(self, query_text, limit=5):
        """
        本地 OCR Storage Benchmark 搜索實現
        
        當 DatabaseSearchService 不可用時使用此備用實現
        """
        try:
            with connection.cursor() as cursor:
                # 使用全文搜索查詢 OCR Storage Benchmark 資料
                sql = """
                SELECT 
                    id,
                    project_name,
                    device_model,
                    firmware_version,
                    benchmark_score,
                    average_bandwidth,
                    test_datetime,
                    ocr_raw_text,
                    verification_notes,
                    CASE 
                        WHEN project_name ILIKE %s OR device_model ILIKE %s THEN 1.0
                        WHEN firmware_version ILIKE %s OR ocr_raw_text ILIKE %s THEN 0.8
                        WHEN verification_notes ILIKE %s THEN 0.6
                        ELSE 0.4
                    END as score
                FROM api_ocrstoragebenchmark
                WHERE 
                    project_name ILIKE %s OR
                    device_model ILIKE %s OR
                    firmware_version ILIKE %s OR
                    ocr_raw_text ILIKE %s OR
                    verification_notes ILIKE %s
                ORDER BY score DESC, test_datetime DESC
                LIMIT %s
                """
                
                search_pattern = f'%{query_text}%'
                cursor.execute(sql, [
                    search_pattern, search_pattern, search_pattern, search_pattern, search_pattern,  # for CASE
                    search_pattern, search_pattern, search_pattern, search_pattern, search_pattern,  # for WHERE
                    limit
                ])
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                results = []
                for row in rows:
                    ocr_data = dict(zip(columns, row))
                    
                    # 格式化為知識片段
                    content = f"專案名稱: {ocr_data['project_name']}\n"
                    content += f"裝置型號: {ocr_data['device_model']}\n"
                    content += f"韌體版本: {ocr_data['firmware_version']}\n"
                    content += f"基準測試分數: {ocr_data['benchmark_score']}\n"
                    content += f"平均帶寬: {ocr_data['average_bandwidth']}\n"
                    content += f"測試時間: {ocr_data['test_datetime']}\n"
                    
                    if ocr_data['ocr_raw_text']:
                        content += f"OCR 原始文本: {ocr_data['ocr_raw_text'][:200]}...\n"
                    
                    if ocr_data['verification_notes']:
                        content += f"驗證備註: {ocr_data['verification_notes']}\n"
                    
                    results.append({
                        'id': str(ocr_data['id']),
                        'title': f"{ocr_data['project_name']} - {ocr_data['device_model']}",
                        'content': content,
                        'score': float(ocr_data['score']),
                        'metadata': {
                            'source': 'ocr_storage_benchmark',
                            'record_id': ocr_data['id'],
                            'project_name': ocr_data['project_name'],
                            'device_model': ocr_data['device_model'],
                            'firmware_version': ocr_data['firmware_version'],
                            'benchmark_score': ocr_data['benchmark_score'],
                            'test_datetime': str(ocr_data['test_datetime'])
                        }
                    })
                
                self.logger.info(f"本地 OCR Storage Benchmark 搜索完成，返回 {len(results)} 結果")
                return results
                
        except Exception as e:
            self.logger.error(f"本地 OCR Storage Benchmark 搜索失敗: {str(e)}")
            return []
    
    def format_dify_response(self, search_results, score_threshold=0.0):
        """
        格式化搜索結果為 Dify 期望的格式
        
        Args:
            search_results (list): 原始搜索結果
            score_threshold (float): 分數閾值
            
        Returns:
            dict: Dify 格式的響應數據
        """
        try:
            # 過濾分數低於閾值的結果
            filtered_results = [
                result for result in search_results 
                if result['score'] >= score_threshold
            ]
            
            # 轉換為 Dify 期望的格式
            records = []
            for result in filtered_results:
                record = {
                    'content': result['content'],
                    'score': result['score'],
                    'title': result['title'],
                    'metadata': result['metadata']
                }
                records.append(record)
            
            response_data = {
                'records': records
            }
            
            self.logger.info(f"Dify 響應格式化完成: {len(records)} 記錄")
            return response_data
            
        except Exception as e:
            self.logger.error(f"Dify 響應格式化失敗: {str(e)}")
            return {'records': []}
    
    def search_with_vector_fallback(self, query_text, limit=5, use_vector=True):
        """
        帶向量搜索備用的智能搜索
        
        優先使用向量搜索，如果不可用則回退到關鍵字搜索
        """
        try:
            if use_vector:
                # 嘗試向量搜索
                try:
                    # 這裡可以集成向量搜索邏輯
                    # from ..embedding_service import search_ocr_with_vectors
                    # return search_ocr_with_vectors(query_text, limit)
                    pass
                except Exception as e:
                    self.logger.warning(f"向量搜索失敗，回退到關鍵字搜索: {e}")
            
            # 使用關鍵字搜索作為備用
            return self.search_ocr_storage_benchmark(query_text, limit)
            
        except Exception as e:
            self.logger.error(f"智能搜索失敗: {str(e)}")
            return []


class AIOCRSearchServiceFallback:
    """AI OCR 搜索服務備用實現 - 簡化版本"""
    
    def __init__(self):
        self.logger = logger
        
    def search_ocr_storage_benchmark(self, query_text, limit=5):
        """備用的 OCR Storage Benchmark 搜索實現"""
        try:
            self.logger.warning("使用 AI OCR 搜索服務備用實現")
            
            # 簡化的搜索邏輯
            return [{
                'id': '0',
                'title': 'OCR 搜索服務不可用',
                'content': f'正在搜索: {query_text}，但搜索服務暫時不可用',
                'score': 0.1,
                'metadata': {
                    'source': 'fallback',
                    'query': query_text,
                    'status': 'service_unavailable'
                }
            }]
            
        except Exception as e:
            self.logger.error(f"備用搜索服務也失敗: {str(e)}")
            return []


# 便利函數
def create_ai_ocr_search_service():
    """創建 AI OCR 搜索服務實例"""
    try:
        return AIOCRSearchService()
    except Exception as e:
        logger.warning(f"無法創建 AI OCR 搜索服務，使用備用實現: {e}")
        return AIOCRSearchServiceFallback()


def search_ocr_storage_benchmark_unified(query_text, limit=5):
    """統一的 OCR Storage Benchmark 搜索介面"""
    service = create_ai_ocr_search_service()
    return service.search_ocr_storage_benchmark(query_text, limit)