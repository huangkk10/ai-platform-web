"""
Chat Analytics Fallback Handlers - 備用實現
==========================================

當主要 Chat Analytics Library 組件不可用時使用的備用實現
提供基本的統計和記錄功能，確保系統穩定運行

備用功能：
- 基本的統計數據生成
- 簡化的使用記錄
- 錯誤處理和日誌記錄
"""

import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class FallbackChatAnalyticsHandler:
    """
    備用聊天分析處理器
    
    提供基本的統計和記錄功能，當主要 library 不可用時使用
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def get_basic_statistics(self, days=30):
        """基本統計數據（空結果）"""
        self.logger.warning(f"使用備用統計處理器，返回空數據 (days={days})")
        
        return {
            'pie_chart': [],
            'daily_chart': [],
            'summary': {
                'total_chats': 0,
                'total_users': 0,
                'total_file_uploads': 0,
                'avg_response_time': 0.0,
                'date_range': {
                    'start': '未知',
                    'end': '未知',
                    'days': days
                }
            }
        }
    
    def record_basic_usage(self, request_data):
        """基本使用記錄（模擬成功）"""
        chat_type = request_data.get('chat_type', 'unknown')
        self.logger.warning(f"使用備用記錄處理器，模擬記錄: {chat_type}")
        
        return {
            'success': True,
            'record_id': 'fallback_record',
            'note': 'Using fallback recorder - limited functionality'
        }


def fallback_chat_usage_statistics_api(request):
    """
    備用聊天使用統計 API
    
    當主要 library 不可用時使用的簡化實現
    """
    logger.warning("使用 Chat Analytics 備用統計 API")
    
    try:
        days = int(request.GET.get('days', 30))
        
        if days < 1 or days > 365:
            return Response({
                'success': False,
                'error': '天數必須在 1-365 之間'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handler = FallbackChatAnalyticsHandler()
        fallback_data = handler.get_basic_statistics(days)
        
        return Response({
            'success': True,
            'data': fallback_data,
            'note': 'Using fallback analytics service - limited functionality'
        }, status=status.HTTP_200_OK)
        
    except ValueError:
        return Response({
            'success': False,
            'error': '天數參數必須是有效數字'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Fallback statistics API failed: {e}")
        return Response({
            'success': False,
            'error': 'Statistics service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def fallback_record_chat_usage_api(request):
    """
    備用記錄聊天使用 API
    
    當主要 library 不可用時使用的簡化實現
    """
    logger.warning("使用 Chat Analytics 備用記錄 API")
    
    try:
        request_data = dict(request.data)
        chat_type = request_data.get('chat_type')
        
        # 基本驗證
        valid_types = ['know_issue_chat', 'log_analyze_chat', 'rvt_assistant_chat', 'protocol_assistant_chat']
        if chat_type not in valid_types:
            return Response({
                'success': False,
                'error': '無效的聊天類型',
                'valid_types': valid_types
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handler = FallbackChatAnalyticsHandler()
        result = handler.record_basic_usage(request_data)
        
        return Response(result, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Fallback record usage API failed: {e}")
        return Response({
            'success': False,
            'error': 'Record usage service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def get_fallback_analytics_status():
    """獲取備用分析狀態"""
    return {
        'status': 'fallback_mode',
        'available_functions': [
            'fallback_chat_usage_statistics_api',
            'fallback_record_chat_usage_api'
        ],
        'note': 'Running in fallback mode with limited functionality'
    }


# 導出備用組件
__all__ = [
    'FallbackChatAnalyticsHandler',
    'fallback_chat_usage_statistics_api',
    'fallback_record_chat_usage_api',
    'get_fallback_analytics_status'
]