"""
RVT Guide 備用實現服務

當主要的 RVT Guide library 組件不可用時，提供基本的備用功能實現。
這些備用實現確保系統在 library 組件故障時仍能提供基本服務。

使用場景：
- Library 組件初始化失敗
- 依賴服務不可用
- 緊急降級處理
"""

import json
import logging
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RVTGuideFallbackHandler:
    """RVT Guide 備用實現處理器 - 提供基本的降級服務"""
    
    @staticmethod
    def handle_dify_search_fallback(request):
        """
        備用實現：Dify RVT Guide 搜索 API
        
        當主要的 RVTGuideAPIHandler 不可用時使用此備用實現
        提供基本的搜索功能，確保 API 不完全失效
        """
        try:
            from rest_framework.response import Response
            from rest_framework import status
            
            # 解析請求數據
            data = json.loads(request.body) if request.body else {}
            query = data.get('query', '')
            top_k = data.get('retrieval_setting', {}).get('top_k', 5)
            
            logger.warning(f"使用 RVT Guide 搜索備用實現，查詢: {query}")
            
            # 驗證必要參數
            if not query:
                return Response({
                    'error_code': 2001,
                    'error_msg': 'Query parameter is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用簡單的搜索實現
            try:
                # 嘗試使用基本搜索功能
                from backend.api.views import search_rvt_guide_knowledge
                search_results = search_rvt_guide_knowledge(query, limit=top_k)
                
                # 格式化為 Dify 期望的格式
                records = [{
                    'content': result['content'],
                    'score': result['score'],
                    'title': result['title'],
                    'metadata': result['metadata']
                } for result in search_results]
                
                logger.info(f"RVT Guide 備用搜索完成，返回 {len(records)} 結果")
                
                return Response({
                    'records': records,
                    'warning': 'Using fallback search implementation'
                }, status=status.HTTP_200_OK)
                
            except Exception as search_error:
                logger.error(f"備用搜索也失敗: {str(search_error)}")
                return Response({
                    'records': [],
                    'warning': 'Search service temporarily unavailable'
                }, status=status.HTTP_200_OK)
                
        except json.JSONDecodeError:
            return Response({
                'error_code': 1001,
                'error_msg': 'Invalid JSON format'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"RVT Guide 搜索備用實現失敗: {str(e)}")
            return Response({
                'error_code': 2001,
                'error_msg': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def handle_chat_fallback(request):
        """
        備用實現：RVT Guide 聊天 API
        
        當主要的聊天服務不可用時，返回友好的錯誤訊息
        """
        try:
            from rest_framework.response import Response
            from rest_framework import status
            
            logger.warning("RVT Guide 聊天服務使用備用實現")
            
            return Response({
                'success': False,
                'error': 'RVT Guide 聊天服務暫時不可用，請稍後再試或聯絡管理員',
                'error_code': 'SERVICE_UNAVAILABLE',
                'fallback': True
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"RVT Guide 聊天備用實現失敗: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '系統暫時不可用，請聯絡管理員'
            }, status=503)
    
    @staticmethod
    def handle_config_fallback(request):
        """
        備用實現：RVT Guide 配置 API
        
        當配置服務不可用時，返回基本的錯誤信息
        """
        try:
            from rest_framework.response import Response
            from rest_framework import status
            
            logger.warning("RVT Guide 配置服務使用備用實現")
            
            return Response({
                'success': False,
                'error': 'RVT Guide 配置服務暫時不可用，請稍後再試或聯絡管理員',
                'error_code': 'CONFIG_SERVICE_UNAVAILABLE',
                'fallback': True
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as e:
            logger.error(f"RVT Guide 配置備用實現失敗: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': '配置服務暫時不可用，請聯絡管理員'
            }, status=503)
    
    @staticmethod
    def create_fallback_viewset_manager():
        """
        創建 ViewSet 的備用管理器
        
        當主要的 RVTGuideViewSetManager 不可用時使用
        """
        return FallbackViewSetManager()


class FallbackViewSetManager:
    """ViewSet 備用管理器 - 提供基本的 ViewSet 功能"""
    
    def get_serializer_class(self, action):
        """備用序列化器選擇邏輯"""
        try:
            from backend.api.serializers import RVTGuideSerializer, RVTGuideListSerializer
            
            if action == 'list':
                return RVTGuideListSerializer
            return RVTGuideSerializer
        except ImportError:
            logger.error("無法導入序列化器，ViewSet 功能受限")
            return None
    
    def perform_create(self, serializer):
        """備用創建邏輯 - 不包含向量處理"""
        logger.warning("使用 RVT Guide ViewSet 備用創建邏輯（無向量生成）")
        return serializer.save()
    
    def perform_update(self, serializer):
        """備用更新邏輯 - 不包含向量處理"""
        logger.warning("使用 RVT Guide ViewSet 備用更新邏輯（無向量生成）")
        return serializer.save()
    
    def get_filtered_queryset(self, queryset, query_params):
        """備用查詢過濾邏輯 - 僅支持基本搜索"""
        try:
            from django.db import models
            
            # 只支持基本的標題和內容搜索
            search = query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(content__icontains=search)
                )
            
            return queryset.order_by('-created_at')
        except Exception as e:
            logger.error(f"備用查詢過濾失敗: {str(e)}")
            return queryset
    
    def get_statistics_data(self, queryset):
        """備用統計邏輯 - 僅提供基本統計"""
        try:
            from rest_framework.response import Response
            from rest_framework import status
            
            total_guides = queryset.count()
            
            return Response({
                'total_guides': total_guides,
                'message': 'RVT Guide 統計服務使用備用實現，功能受限',
                'fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"備用統計失敗: {str(e)}")
            from rest_framework.response import Response
            from rest_framework import status
            
            return Response({
                'error': f'統計功能暫時不可用: {str(e)}',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class FallbackSearchService:
    """備用搜索服務 - 提供基本搜索功能"""
    
    def __init__(self):
        self.logger = logger
        
    def search_knowledge(self, query_text, limit=5):
        """
        備用知識搜索實現
        
        僅使用基本的資料庫搜索，不包含向量搜索
        """
        try:
            logger.warning(f"使用 RVT Guide 備用搜索服務，查詢: {query_text}")
            
            # 嘗試使用基本的資料庫搜索
            from backend.api.views import search_rvt_guide_knowledge
            results = search_rvt_guide_knowledge(query_text, limit)
            
            logger.info(f"備用搜索完成，返回 {len(results)} 結果")
            return results
            
        except Exception as e:
            logger.error(f"備用搜索服務失敗: {str(e)}")
            return []


# 便利函數：直接使用備用實現
def fallback_dify_rvt_guide_search(request):
    """便利函數：Dify 搜索備用實現"""
    return RVTGuideFallbackHandler.handle_dify_search_fallback(request)


def fallback_rvt_guide_chat(request):
    """便利函數：聊天備用實現"""
    return RVTGuideFallbackHandler.handle_chat_fallback(request)


def fallback_rvt_guide_config(request):
    """便利函數：配置備用實現"""
    return RVTGuideFallbackHandler.handle_config_fallback(request)