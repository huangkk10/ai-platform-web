"""
Dify Knowledge Fallback Handlers - 備用實現
=========================================

當主要 Dify Knowledge Library 組件不可用時使用的備用實現
提供基本的搜索功能，確保系統穩定運行

備用功能：
- 基本的請求解析和驗證
- 簡化的搜索邏輯
- 符合 Dify 規格的回應格式
- 錯誤處理和日誌記錄
"""

import json
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class FallbackDifyKnowledgeProcessor:
    """
    備用 Dify 知識搜索處理器
    
    提供基本的搜索功能，當主要 library 不可用時使用
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def parse_basic_request(self, request):
        """基本的請求解析"""
        try:
            data = json.loads(request.body) if request.body else {}
            
            return {
                'knowledge_id': data.get('knowledge_id', 'employee_database'),
                'query': data.get('query', ''),
                'top_k': data.get('retrieval_setting', {}).get('top_k', 5),
                'score_threshold': data.get('retrieval_setting', {}).get('score_threshold', 0.0)
            }
        except:
            return None
    
    def create_empty_response(self):
        """創建符合 Dify 格式的空回應"""
        return {
            'records': []
        }
    
    def process_fallback_search(self, request):
        """處理備用搜索請求"""
        try:
            # 基本的請求驗證
            parsed_data = self.parse_basic_request(request)
            if not parsed_data:
                return Response({
                    'error_code': 1001,
                    'error_msg': 'Invalid JSON format'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not parsed_data['query']:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            self.logger.warning(
                f"Fallback search: query='{parsed_data['query']}', "
                f"knowledge_id='{parsed_data['knowledge_id']}'"
            )
            
            # 返回空結果但符合格式
            empty_response = self.create_empty_response()
            return Response(empty_response, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"Fallback search failed: {e}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Service temporarily unavailable'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def fallback_dify_knowledge_search(request):
    """
    備用 Dify 知識搜索函數
    
    當主要 library 不可用時使用的全域函數
    """
    logger.warning("使用 Dify Knowledge 備用實現")
    
    try:
        processor = FallbackDifyKnowledgeProcessor()
        return processor.process_fallback_search(request)
    except Exception as e:
        logger.error(f"Fallback Dify knowledge search completely failed: {e}")
        return Response({
            'error_code': 2001,
            'error_msg': 'All knowledge search services are temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def fallback_search_postgres_knowledge(query_text, limit=5):
    """備用的 PostgreSQL 員工知識搜索"""
    logger.warning(f"Fallback PostgreSQL search: query='{query_text}'")
    return []


def fallback_search_know_issue_knowledge(query_text, limit=5):
    """備用的 Know Issue 知識搜索"""
    logger.warning(f"Fallback Know Issue search: query='{query_text}'")
    return []


def fallback_search_rvt_guide_knowledge(query_text, limit=5):
    """備用的 RVT Guide 知識搜索"""
    logger.warning(f"Fallback RVT Guide search: query='{query_text}'")
    return []


def fallback_search_ocr_storage_benchmark(query_text, limit=5):
    """備用的 OCR Storage Benchmark 搜索"""
    logger.warning(f"Fallback OCR Storage Benchmark search: query='{query_text}'")
    return []


def get_fallback_knowledge_status():
    """獲取備用知識庫狀態"""
    return {
        'status': 'fallback_mode',
        'available_functions': [
            'fallback_dify_knowledge_search',
            'fallback_search_postgres_knowledge',
            'fallback_search_know_issue_knowledge', 
            'fallback_search_rvt_guide_knowledge',
            'fallback_search_ocr_storage_benchmark'
        ],
        'note': 'Running in fallback mode with limited functionality'
    }


# 導出備用組件
__all__ = [
    'FallbackDifyKnowledgeProcessor',
    'fallback_dify_knowledge_search',
    'fallback_search_postgres_knowledge',
    'fallback_search_know_issue_knowledge',
    'fallback_search_rvt_guide_knowledge', 
    'fallback_search_ocr_storage_benchmark',
    'get_fallback_knowledge_status'
]