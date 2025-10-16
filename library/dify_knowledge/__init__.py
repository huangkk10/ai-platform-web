"""
Dify Knowledge Search Library - 統一知識庫搜索管理
==================================================

這個模組提供統一的 Dify 知識庫搜索功能，支援多種知識源：
- Employee Database (員工資料庫)
- Know Issue Database (問題知識庫) 
- RVT Guide Database (RVT 指導文檔)
- OCR Storage Benchmark (OCR 存儲基準測試)

主要組件：
- DifyKnowledgeSearchHandler: 主要搜索處理器
- DifyKnowledgeAPIProcessor: API 請求處理器
- DifyKnowledgeManager: 統一管理器

使用方式：
```python
from library.dify_knowledge import (
    DifyKnowledgeSearchHandler,
    handle_dify_knowledge_search_api,
    process_dify_knowledge_request,
    DIFY_KNOWLEDGE_LIBRARY_AVAILABLE
)

# 直接處理 API 請求
response = handle_dify_knowledge_search_api(request)

# 或使用處理器
handler = DifyKnowledgeSearchHandler()
result = handler.search(knowledge_id, query, top_k, score_threshold)
```
"""

import json
import logging

try:
    from rest_framework.response import Response
    from rest_framework import status
    from django.views.decorators.csrf import csrf_exempt
    DJANGO_REST_AVAILABLE = True
except ImportError:
    Response = None
    status = None
    csrf_exempt = None
    DJANGO_REST_AVAILABLE = False

logger = logging.getLogger(__name__)

# 標記 library 可用性
DIFY_KNOWLEDGE_LIBRARY_AVAILABLE = True

try:
    # 嘗試導入依賴
    from django.db import connection
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

# 知識庫 ID 映射
KNOWLEDGE_ID_MAPPING = {
    # Know Issue 相關
    'know_issue_db': 'know_issue',
    'know_issue': 'know_issue', 
    'know-issue': 'know_issue',
    
    # RVT Guide 相關
    'rvt_guide_db': 'rvt_guide',
    'rvt_guide': 'rvt_guide',
    'rvt-guide': 'rvt_guide',
    'rvt_user_guide': 'rvt_guide',
    
    # Protocol Guide 相關
    'protocol_guide_db': 'protocol_guide',
    'protocol_guide': 'protocol_guide',
    'protocol-guide': 'protocol_guide',
    'protocol_assistant': 'protocol_guide',
    
    # OCR Storage Benchmark 相關
    'ocr_storage_benchmark': 'ocr_benchmark',
    'ocr_benchmark': 'ocr_benchmark',
    'storage_benchmark': 'ocr_benchmark',
    'benchmark_db': 'ocr_benchmark',
    
    # Employee Database (默認)
    'employee_database': 'employee',
    'employee_db': 'employee',
    'employee': 'employee'
}


class DifyKnowledgeSearchHandler:
    """
    Dify 知識庫搜索處理器
    
    負責根據不同的 knowledge_id 調用相應的搜索服務
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._initialize_search_services()
    
    def _initialize_search_services(self):
        """初始化各種搜索服務"""
        try:
            # 導入向量搜索服務（動態導入）
            try:
                import importlib
                embedding_module = importlib.import_module('api.services.embedding_service')
                self.search_rvt_guide_with_vectors = getattr(embedding_module, 'search_rvt_guide_with_vectors', None)
                self.vector_search_available = self.search_rvt_guide_with_vectors is not None
                
                if self.vector_search_available:
                    self.logger.info("✅ 向量搜索服務可用")
                else:
                    self.logger.warning("⚠️ 向量搜索函數不存在")
            except ImportError:
                self.vector_search_available = False
                self.search_rvt_guide_with_vectors = None
                self.logger.warning("⚠️ 向量搜索模組不可用")
                
            # 導入各種搜索函數
            self._import_search_functions()
            
        except Exception as e:
            self.logger.error(f"初始化搜索服務失敗: {e}")
            self._set_fallback_services()
    
    def _import_search_functions(self):
        """導入搜索函數（動態導入避免循環依賴）"""
        try:
            # 動態導入避免循環依賴問題
            import importlib
            
            # 嘗試從 views 模組導入搜索函數
            views_module = importlib.import_module('api.views')
            
            self.search_know_issue_knowledge = getattr(views_module, 'search_know_issue_knowledge', self._fallback_search)
            self.search_rvt_guide_knowledge = getattr(views_module, 'search_rvt_guide_knowledge', self._fallback_search)
            self.search_protocol_guide_knowledge = getattr(views_module, 'search_protocol_guide_knowledge', self._fallback_search)
            self.search_ocr_storage_benchmark = getattr(views_module, 'search_ocr_storage_benchmark', self._fallback_search)
            self.search_postgres_knowledge = getattr(views_module, 'search_postgres_knowledge', self._fallback_search)
            
            self.logger.info("✅ 成功動態導入搜索函數")
            
        except ImportError as e:
            self.logger.error(f"動態導入搜索函數失敗: {e}")
            self._set_fallback_search_functions()
        except Exception as e:
            self.logger.error(f"搜索函數導入異常: {e}")
            self._set_fallback_search_functions()
    
    def _set_fallback_services(self):
        """設置備用服務"""
        self.vector_search_available = False
        self.search_rvt_guide_with_vectors = None
        self._set_fallback_search_functions()
    
    def _set_fallback_search_functions(self):
        """設置備用搜索函數"""
        self.search_know_issue_knowledge = self._fallback_search
        self.search_rvt_guide_knowledge = self._fallback_search
        self.search_protocol_guide_knowledge = self._fallback_search
        self.search_ocr_storage_benchmark = self._fallback_search
        self.search_postgres_knowledge = self._fallback_search
        self.logger.warning("使用備用搜索函數")
    
    def _fallback_search(self, query, limit=5):
        """備用搜索實現"""
        self.logger.warning(f"備用搜索被調用: query='{query}', limit={limit}")
        return []
    
    def normalize_knowledge_id(self, knowledge_id):
        """標準化 knowledge_id"""
        normalized = KNOWLEDGE_ID_MAPPING.get(knowledge_id, 'employee')
        self.logger.info(f"Knowledge ID 標準化: '{knowledge_id}' -> '{normalized}'")
        return normalized
    
    def search_knowledge_by_type(self, knowledge_type, query, limit=5):
        """
        根據知識類型執行搜索
        
        Args:
            knowledge_type: 標準化的知識類型
            query: 搜索查詢
            limit: 結果數量限制
            
        Returns:
            list: 搜索結果列表
        """
        self.logger.info(f"執行搜索: type={knowledge_type}, query='{query}', limit={limit}")
        
        try:
            if knowledge_type == 'know_issue':
                results = self.search_know_issue_knowledge(query, limit=limit)
                self.logger.info(f"Know Issue 搜索結果: {len(results)} 條")
                return results
                
            elif knowledge_type == 'rvt_guide':
                # 優先使用向量搜索
                if self.vector_search_available and self.search_rvt_guide_with_vectors:
                    try:
                        results = self.search_rvt_guide_with_vectors(query, limit=limit, threshold=0.1)
                        self.logger.info(f"RVT Guide 向量搜索結果: {len(results)} 條")
                        
                        # 如果向量搜索無結果，回退到關鍵字搜索
                        if not results:
                            self.logger.info("向量搜索無結果，回退到關鍵字搜索")
                            results = self.search_rvt_guide_knowledge(query, limit=limit)
                            self.logger.info(f"RVT Guide 關鍵字搜索結果: {len(results)} 條")
                        return results
                    except Exception as e:
                        self.logger.error(f"向量搜索失敗，回退到關鍵字搜索: {e}")
                        results = self.search_rvt_guide_knowledge(query, limit=limit)
                        self.logger.info(f"RVT Guide 備用搜索結果: {len(results)} 條")
                        return results
                else:
                    results = self.search_rvt_guide_knowledge(query, limit=limit)
                    self.logger.info(f"RVT Guide 關鍵字搜索結果: {len(results)} 條")
                    return results
                    
            elif knowledge_type == 'protocol_guide':
                # Protocol Guide 搜索（暫時使用關鍵字搜索，之後可添加向量搜索）
                results = self.search_protocol_guide_knowledge(query, limit=limit)
                self.logger.info(f"Protocol Guide 搜索結果: {len(results)} 條")
                return results
                    
            elif knowledge_type == 'ocr_benchmark':
                results = self.search_ocr_storage_benchmark(query, limit=limit)
                self.logger.info(f"OCR Storage Benchmark 搜索結果: {len(results)} 條")
                return results
                
            elif knowledge_type == 'employee':
                results = self.search_postgres_knowledge(query, limit=limit)
                self.logger.info(f"Employee 搜索結果: {len(results)} 條")
                return results
                
            else:
                self.logger.warning(f"未知的知識類型: {knowledge_type}")
                return []
                
        except Exception as e:
            self.logger.error(f"搜索執行失敗: {e}")
            return []
    
    def filter_results_by_score(self, results, score_threshold):
        """根據分數閾值過濾結果"""
        if score_threshold <= 0:
            return results
            
        filtered_results = [
            result for result in results 
            if result.get('score', 0) >= score_threshold
        ]
        
        self.logger.info(f"分數過濾: {len(results)} -> {len(filtered_results)} (threshold: {score_threshold})")
        return filtered_results
    
    def format_dify_response(self, results):
        """格式化為 Dify 期望的回應格式"""
        records = []
        for result in results:
            record = {
                'content': result.get('content', ''),
                'score': result.get('score', 0.0),
                'title': result.get('title', ''),
                'metadata': result.get('metadata', {})
            }
            records.append(record)
            self.logger.debug(f"格式化記錄: {record['title']}")
        
        return {'records': records}
    
    def search(self, knowledge_id, query, top_k=5, score_threshold=0.0, metadata_condition=None):
        """
        統一搜索接口
        
        Args:
            knowledge_id: 知識庫 ID
            query: 搜索查詢
            top_k: 返回結果數量
            score_threshold: 分數閾值
            metadata_condition: 元數據條件（可選）
            
        Returns:
            dict: Dify 格式的回應
        """
        try:
            # 標準化知識庫 ID
            knowledge_type = self.normalize_knowledge_id(knowledge_id)
            
            # 執行搜索
            search_results = self.search_knowledge_by_type(knowledge_type, query, top_k)
            
            # 根據分數過濾
            filtered_results = self.filter_results_by_score(search_results, score_threshold)
            
            # 格式化回應
            response_data = self.format_dify_response(filtered_results)
            
            self.logger.info(f"搜索完成: 找到 {len(filtered_results)} 條結果")
            return response_data
            
        except Exception as e:
            self.logger.error(f"搜索過程失敗: {e}")
            return {'records': []}


class DifyKnowledgeAPIProcessor:
    """
    Dify Knowledge API 請求處理器
    
    負責解析 HTTP 請求，驗證參數，調用搜索處理器
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.search_handler = DifyKnowledgeSearchHandler()
    
    def validate_authorization(self, request):
        """驗證 Authorization header"""
        auth_header = request.headers.get('Authorization', '')
        if auth_header and not auth_header.startswith('Bearer '):
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid Authorization header format. Expected "Bearer <api-key>" format.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        return None
    
    def parse_request_data(self, request):
        """解析請求資料"""
        try:
            data = json.loads(request.body) if request.body else {}
            
            knowledge_id = data.get('knowledge_id', 'employee_database')
            query = data.get('query', '')
            retrieval_setting = data.get('retrieval_setting', {})
            metadata_condition = data.get('metadata_condition', {})
            
            top_k = retrieval_setting.get('top_k', 5)
            score_threshold = retrieval_setting.get('score_threshold', 0.0)
            
            # 確保分數閾值不會太高
            if score_threshold > 0.9:
                score_threshold = 0.0
                self.logger.warning("Score threshold was too high, reset to 0.0")
            
            return {
                'knowledge_id': knowledge_id,
                'query': query,
                'top_k': top_k,
                'score_threshold': score_threshold,
                'metadata_condition': metadata_condition
            }
            
        except json.JSONDecodeError:
            return None
    
    def validate_query(self, query):
        """驗證查詢參數"""
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        return None
    
    def process_request(self, request):
        """
        處理 Dify 知識搜索請求
        
        Args:
            request: Django HttpRequest 對象
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 驗證 Authorization
            auth_error = self.validate_authorization(request)
            if auth_error:
                return auth_error
            
            # 解析請求資料
            parsed_data = self.parse_request_data(request)
            if parsed_data is None:
                return Response({
                    'error_code': 1001,
                    'error_msg': 'Invalid JSON format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 驗證查詢參數
            query_error = self.validate_query(parsed_data['query'])
            if query_error:
                return query_error
            
            # 記錄請求信息
            self.logger.info(
                f"Dify request - Query: '{parsed_data['query']}', "
                f"top_k: {parsed_data['top_k']}, "
                f"score_threshold: {parsed_data['score_threshold']}, "
                f"knowledge_id: '{parsed_data['knowledge_id']}'"
            )
            
            # 執行搜索
            search_result = self.search_handler.search(
                knowledge_id=parsed_data['knowledge_id'],
                query=parsed_data['query'],
                top_k=parsed_data['top_k'],
                score_threshold=parsed_data['score_threshold'],
                metadata_condition=parsed_data['metadata_condition']
            )
            
            self.logger.info(f"Dify knowledge search - Found {len(search_result['records'])} results")
            return Response(search_result, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"Dify knowledge search error: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DifyKnowledgeManager:
    """
    Dify 知識管理器
    
    提供高級管理功能和便利方法
    """
    
    def __init__(self):
        self.search_handler = DifyKnowledgeSearchHandler()
        self.api_processor = DifyKnowledgeAPIProcessor()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_supported_knowledge_types(self):
        """獲取支援的知識庫類型"""
        return list(set(KNOWLEDGE_ID_MAPPING.values()))
    
    def get_knowledge_id_aliases(self, knowledge_type):
        """獲取知識庫類型的所有別名"""
        aliases = [k for k, v in KNOWLEDGE_ID_MAPPING.items() if v == knowledge_type]
        return aliases
    
    def test_search_functionality(self):
        """測試搜索功能"""
        test_results = {}
        
        for knowledge_type in self.get_supported_knowledge_types():
            try:
                result = self.search_handler.search_knowledge_by_type(
                    knowledge_type, "test", limit=1
                )
                test_results[knowledge_type] = {
                    'available': True,
                    'result_count': len(result)
                }
            except Exception as e:
                test_results[knowledge_type] = {
                    'available': False,
                    'error': str(e)
                }
        
        return test_results


# 便利函數和工廠方法

def create_dify_knowledge_search_handler():
    """創建 Dify 知識搜索處理器"""
    return DifyKnowledgeSearchHandler()

def create_dify_knowledge_api_processor():
    """創建 Dify 知識 API 處理器"""
    return DifyKnowledgeAPIProcessor()

def create_dify_knowledge_manager():
    """創建 Dify 知識管理器"""
    return DifyKnowledgeManager()

def handle_dify_knowledge_search_api(request):
    """
    處理 Dify 知識搜索 API 請求 - 便利函數
    
    Args:
        request: Django HttpRequest 對象
        
    Returns:
        Response: DRF Response 對象
    """
    try:
        processor = create_dify_knowledge_api_processor()
        return processor.process_request(request)
    except Exception as e:
        logger.error(f"Handle Dify knowledge search API failed: {e}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

def process_dify_knowledge_request(knowledge_id, query, top_k=5, score_threshold=0.0):
    """
    處理 Dify 知識請求 - 便利函數（用於程式化調用）
    
    Args:
        knowledge_id: 知識庫 ID
        query: 搜索查詢
        top_k: 返回結果數量
        score_threshold: 分數閾值
        
    Returns:
        dict: 搜索結果
    """
    try:
        handler = create_dify_knowledge_search_handler()
        return handler.search(knowledge_id, query, top_k, score_threshold)
    except Exception as e:
        logger.error(f"Process Dify knowledge request failed: {e}")
        return {'records': []}

def get_dify_knowledge_library_status():
    """獲取 Dify Knowledge Library 狀態"""
    try:
        manager = create_dify_knowledge_manager()
        test_results = manager.test_search_functionality()
        
        return {
            'available': DIFY_KNOWLEDGE_LIBRARY_AVAILABLE,
            'django_available': DJANGO_AVAILABLE,
            'supported_types': manager.get_supported_knowledge_types(),
            'search_services': test_results,
            'components': {
                'DifyKnowledgeSearchHandler': True,
                'DifyKnowledgeAPIProcessor': True, 
                'DifyKnowledgeManager': True
            }
        }
    except Exception as e:
        logger.error(f"Get library status failed: {e}")
        return {
            'available': False,
            'error': str(e),
            'components': {}
        }

# 備用處理器（如果主要組件失敗）
def fallback_dify_knowledge_search(request):
    """
    備用 Dify 知識搜索實現
    
    當主要組件不可用時使用的簡化實現
    """
    logger.warning("使用備用 Dify 知識搜索實現")
    
    try:
        import json
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 返回空結果但符合格式
        return Response({
            'records': []
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Fallback Dify knowledge search failed: {e}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

# 導出主要組件
__all__ = [
    'DifyKnowledgeSearchHandler',
    'DifyKnowledgeAPIProcessor', 
    'DifyKnowledgeManager',
    'handle_dify_knowledge_search_api',
    'process_dify_knowledge_request',
    'create_dify_knowledge_search_handler',
    'create_dify_knowledge_api_processor',
    'create_dify_knowledge_manager',
    'get_dify_knowledge_library_status',
    'fallback_dify_knowledge_search',
    'DIFY_KNOWLEDGE_LIBRARY_AVAILABLE',
    'KNOWLEDGE_ID_MAPPING'
]