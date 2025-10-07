"""
AI OCR 備用實現服務

當主要的 AI OCR library 組件不可用時，提供基本的備用功能實現。
這些備用實現確保系統在 library 組件故障時仍能提供基本服務。

使用場景：
- Library 組件初始化失敗
- 依賴服務不可用
- 緊急降級處理
"""

import json
import logging
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class AIOCRFallbackHandler:
    """AI OCR 備用實現處理器 - 提供基本的降級服務"""
    
    @staticmethod
    def handle_dify_ocr_chat_fallback(request):
        """
        備用實現：Dify OCR 聊天 API
        
        當主要的 AIOCRAPIHandler 不可用時使用此備用實現
        """
        try:
            logger.warning("使用 AI OCR 聊天備用實現")
            
            return Response({
                'success': False,
                'error': 'AI OCR 聊天服務暫時不可用，請稍後再試或聯絡管理員',
                'error_code': 'SERVICE_UNAVAILABLE',
                'fallback': True
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"AI OCR 聊天備用實現失敗: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '系統暫時不可用，請聯絡管理員'
            }, status=503)
    
    @staticmethod
    def handle_dify_chat_with_file_fallback(request):
        """
        備用實現：Dify 檔案分析 API
        
        當主要的檔案分析服務不可用時使用此備用實現
        """
        try:
            logger.warning("使用 AI OCR 檔案分析備用實現")
            
            return Response({
                'success': False,
                'error': 'AI OCR 檔案分析服務暫時不可用，請稍後再試或聯絡管理員',
                'error_code': 'FILE_ANALYSIS_UNAVAILABLE',
                'fallback': True
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"AI OCR 檔案分析備用實現失敗: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '檔案分析系統暫時不可用，請聯絡管理員'
            }, status=503)


def handle_dify_ocr_storage_benchmark_search_fallback(request):
    """
    Dify OCR Storage Benchmark 搜索 API 備用實現
    
    當主要服務不可用時的完整備用邏輯（從 views.py 遷移）
    """
    try:
        import json
        import logging
        from rest_framework.response import Response
        from rest_framework import status
        
        logger = logging.getLogger(__name__)
        
        # 從 views.py 遷移的完整備用邏輯
        logger.warning("AI OCR Library 主要服務不可用，使用備用實現")
        
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 嘗試使用搜索服務
        try:
            # 動態導入以避免循環依賴
            from ..data_processing.database_search import DatabaseSearchService
            service = DatabaseSearchService()
            search_results = service.search_ocr_storage_benchmark(query, limit=top_k)
        except Exception as search_error:
            logger.warning(f"DatabaseSearchService 不可用: {search_error}，使用最基本備用")
            # 最基本的模擬結果
            search_results = [{
                'id': 1,
                'title': f'OCR Storage Benchmark - {query}',
                'content': f'備用搜索結果: 專案名稱包含 "{query}" 的存儲基準測試資料',
                'score': 0.7,
                'metadata': {
                    'source': 'ocr_storage_benchmark_fallback',
                    'query': query,
                    'fallback_reason': 'Primary services unavailable'
                }
            }]
        
        # 過濾分數並構建響應
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        records = []
        for result in filtered_results:
            records.append({
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            })
        
        logger.info(f"OCR Storage Benchmark 備用實現返回 {len(records)} 個結果")
        return Response({'records': records}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"OCR Storage Benchmark 備用實現錯誤: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': f'Fallback implementation error: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def create_fallback_viewset_manager():
        """
        創建 ViewSet 的備用管理器
        
        當主要的 OCR ViewSet 管理器不可用時使用
        """
        return FallbackViewSetManager()


class FallbackViewSetManager:
    """ViewSet 備用管理器 - 提供基本的 ViewSet 功能"""
    
    def get_serializer_class(self, action):
        """備用序列化器選擇邏輯"""
        try:
            from backend.api.serializers import (
                OCRTestClassSerializer,
                OCRStorageBenchmarkSerializer,
                OCRStorageBenchmarkListSerializer
            )
            
            if action == 'list' and 'storage' in str(action).lower():
                return OCRStorageBenchmarkListSerializer
            elif 'storage' in str(action).lower():
                return OCRStorageBenchmarkSerializer
            else:
                return OCRTestClassSerializer
        except ImportError:
            logger.error("無法導入序列化器，ViewSet 功能受限")
            return None
    
    def perform_create(self, serializer, user):
        """備用創建邏輯"""
        logger.warning("使用 AI OCR ViewSet 備用創建邏輯")
        try:
            if hasattr(serializer, 'save'):
                return serializer.save(created_by=user)
            return None
        except Exception as e:
            logger.error(f"備用創建失敗: {e}")
            raise
    
    def get_filtered_queryset(self, queryset, query_params):
        """備用查詢過濾邏輯 - 僅支持基本搜索"""
        try:
            from django.db import models
            
            # 只支持基本的搜索
            search = query_params.get('search', None)
            if search:
                # 嘗試多個可能的字段
                try:
                    queryset = queryset.filter(
                        models.Q(name__icontains=search) |
                        models.Q(project_name__icontains=search) |
                        models.Q(device_model__icontains=search)
                    )
                except Exception:
                    # 如果字段不存在，使用最基本的過濾
                    try:
                        queryset = queryset.filter(name__icontains=search)
                    except Exception:
                        pass
            
            return queryset.order_by('-id')
        except Exception as e:
            logger.error(f"備用查詢過濾失敗: {str(e)}")
            return queryset
    
    def handle_upload_image(self, ocr_record, uploaded_file):
        """備用圖像上傳處理"""
        logger.warning("使用 AI OCR 圖像上傳備用實現")
        
        return Response({
            'error': 'AI OCR 圖像上傳服務暫時不可用，請稍後再試',
            'fallback': True
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def handle_verify_record(self, ocr_record, verification_notes, user):
        """備用記錄驗證處理"""
        logger.warning("使用 AI OCR 記錄驗證備用實現")
        
        return Response({
            'error': 'AI OCR 記錄驗證服務暫時不可用，請稍後再試',
            'fallback': True
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def handle_process_ocr(self, ocr_record):
        """備用 OCR 處理"""
        logger.warning("使用 AI OCR 處理備用實現")
        
        return Response({
            'error': 'AI OCR 處理服務暫時不可用，請稍後再試',
            'fallback': True
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    
    def get_statistics_data(self, queryset):
        """備用統計邏輯 - 僅提供基本統計"""
        try:
            total_records = queryset.count()
            
            return Response({
                'total_records': total_records,
                'message': 'AI OCR 統計服務使用備用實現，功能受限',
                'fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"備用統計失敗: {str(e)}")
            
            return Response({
                'error': f'統計功能暫時不可用: {str(e)}',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FallbackChatService:
    """備用聊天服務 - 提供基本聊天功能"""
    
    def __init__(self):
        self.logger = logger
        
    def handle_ocr_chat_request(self, message, conversation_id='', user=None):
        """
        備用 OCR 聊天處理
        
        當主要聊天服務不可用時使用
        """
        try:
            logger.warning(f"使用 AI OCR 聊天備用服務，訊息: {message[:50]}...")
            
            return {
                'success': False,
                'error': 'AI OCR 聊天服務暫時不可用，請稍後再試或聯絡管理員',
                'fallback': True,
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
            }
            
        except Exception as e:
            logger.error(f"備用聊天服務失敗: {str(e)}")
            return {
                'success': False,
                'error': '聊天系統暫時不可用，請聯絡管理員',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }
    
    def handle_file_analysis_request(self, uploaded_file, message='', user=None):
        """
        備用檔案分析處理
        
        當主要檔案分析服務不可用時使用
        """
        try:
            logger.warning(f"使用 AI OCR 檔案分析備用服務，檔案: {uploaded_file.name if uploaded_file else 'None'}")
            
            return {
                'success': False,
                'error': 'AI OCR 檔案分析服務暫時不可用，請稍後再試或聯絡管理員',
                'fallback': True,
                'status_code': status.HTTP_503_SERVICE_UNAVAILABLE
            }
            
        except Exception as e:
            logger.error(f"備用檔案分析服務失敗: {str(e)}")
            return {
                'success': False,
                'error': '檔案分析系統暫時不可用，請聯絡管理員',
                'status_code': status.HTTP_500_INTERNAL_SERVER_ERROR
            }


class FallbackSearchService:
    """備用搜索服務 - 提供基本搜索功能"""
    
    def __init__(self):
        self.logger = logger
        
    def search_ocr_storage_benchmark(self, query_text, limit=5):
        """
        備用 OCR Storage Benchmark 搜索實現
        
        僅使用基本的資料庫搜索，不包含向量搜索
        """
        try:
            logger.warning(f"使用 AI OCR 備用搜索服務，查詢: {query_text}")
            
            # 返回基本的備用結果
            return [{
                'id': '0',
                'title': 'OCR 搜索服務不可用',
                'content': f'正在搜索: {query_text}，但搜索服務暫時不可用。請稍後再試或聯絡管理員。',
                'score': 0.1,
                'metadata': {
                    'source': 'fallback',
                    'query': query_text,
                    'status': 'service_unavailable',
                    'fallback': True
                }
            }]
            
        except Exception as e:
            logger.error(f"備用搜索服務失敗: {str(e)}")
            return []


# 便利函數：快速調用備用 API 處理器
def fallback_dify_ocr_chat(request):
    """便利函數：Dify OCR Chat 備用實現"""
    handler = AIOCRFallbackHandler()
    return handler.handle_dify_ocr_chat_fallback(request)


def fallback_dify_chat_with_file(request):
    """便利函數：Dify Chat with File 備用實現"""
    handler = AIOCRFallbackHandler()
    return handler.handle_dify_chat_with_file_fallback(request)


def fallback_dify_ocr_storage_benchmark_search(request):
    """
    便利函數：Dify OCR Storage Benchmark Search 備用實現
    
    🔄 更新：使用從 views.py 遷移的完整備用邏輯
    """
    return handle_dify_ocr_storage_benchmark_search_fallback(request)
    """便利函數：OCR 聊天備用實現"""
    return AIOCRFallbackHandler.handle_dify_ocr_chat_fallback(request)


def fallback_dify_chat_with_file(request):
    """便利函數：檔案分析備用實現"""
    return AIOCRFallbackHandler.handle_dify_chat_with_file_fallback(request)


def fallback_dify_ocr_storage_benchmark_search(request):
    """便利函數：OCR Storage Benchmark 搜索備用實現"""
    return AIOCRFallbackHandler.handle_dify_ocr_storage_benchmark_search_fallback(request)


def create_fallback_ocr_test_class_viewset_manager():
    """便利函數：創建備用 OCR 測試類別管理器"""
    return FallbackViewSetManager()


def create_fallback_ocr_storage_benchmark_viewset_manager():
    """便利函數：創建備用 OCR 存儲基準管理器"""
    return FallbackViewSetManager()


def create_fallback_ai_ocr_chat_service():
    """便利函數：創建備用 AI OCR 聊天服務"""
    return FallbackChatService()


def create_fallback_ai_ocr_search_service():
    """便利函數：創建備用 AI OCR 搜索服務"""
    return FallbackSearchService()