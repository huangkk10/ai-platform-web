"""
Chat Analytics API Handler - API 處理器
=====================================

處理聊天分析相關的 HTTP API 請求：
- 統計請求處理
- 記錄請求處理
- 參數驗證
- 錯誤處理
"""

import logging
from typing import Dict, Any

try:
    from rest_framework import status
    from rest_framework.response import Response
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False

from .statistics_handler import ChatUsageStatisticsHandler
from .usage_recorder import ChatUsageRecorder

logger = logging.getLogger(__name__)


class ChatAnalyticsAPIHandler:
    """聊天分析 API 處理器 - 處理 HTTP 請求和回應"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.statistics_handler = ChatUsageStatisticsHandler()
        self.usage_recorder = ChatUsageRecorder()
    
    def handle_statistics_request(self, request) -> 'Response':
        """
        處理統計請求
        
        Args:
            request: HTTP 請求對象
            
        Returns:
            Response: DRF 回應
        """
        try:
            # 解析查詢參數：days=None 時查詢所有歷史資料
            days_param = request.GET.get('days')
            days = int(days_param) if days_param else None
            
            # 驗證參數範圍（如果有指定）
            if days is not None and (days < 1 or days > 3650):
                return Response({
                    'success': False,
                    'error': '天數必須在 1-3650 之間'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            self.logger.info(f"處理統計請求: days={days if days else '全部歷史'}")
            
            # 獲取統計數據
            statistics_data = self.statistics_handler.get_statistics(days)
            
            return Response({
                'success': True,
                'data': statistics_data
            }, status=status.HTTP_200_OK)
            
        except ValueError:
            return Response({
                'success': False,
                'error': '天數參數必須是有效數字'
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            self.logger.error(f"統計請求處理失敗: {e}")
            return Response({
                'success': False,
                'error': f'統計數據獲取失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_record_usage_request(self, request) -> 'Response':
        """
        處理記錄使用請求
        
        Args:
            request: HTTP 請求對象
            
        Returns:
            Response: DRF 回應
        """
        try:
            # 提取請求數據
            request_data = dict(request.data)
            
            # 提取客戶端信息
            client_info = self.usage_recorder.extract_client_info(request)
            
            # 記錄聊天使用
            result = self.usage_recorder.record_chat_usage(
                request_data, 
                client_info, 
                getattr(request, 'user', None)
            )
            
            if result['success']:
                self.logger.info(f"聊天使用記錄成功: {result.get('record_id')}")
                return Response(result, status=status.HTTP_201_CREATED)
            else:
                self.logger.warning(f"聊天使用記錄失敗: {result.get('error')}")
                return Response(result, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            self.logger.error(f"記錄使用請求處理失敗: {e}")
            return Response({
                'success': False,
                'error': f'記錄使用情況失敗: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)