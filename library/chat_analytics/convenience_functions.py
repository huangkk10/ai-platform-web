"""
Chat Analytics Convenience Functions - 便利函數
==============================================

提供簡化的接口函數，讓其他模組更容易使用 Chat Analytics 功能
"""

import logging
from typing import Optional

try:
    from rest_framework import status
    from rest_framework.response import Response
    DRF_AVAILABLE = True
except ImportError:
    DRF_AVAILABLE = False

from .statistics_handler import ChatUsageStatisticsHandler
from .usage_recorder import ChatUsageRecorder
from .api_handler import ChatAnalyticsAPIHandler

logger = logging.getLogger(__name__)


def handle_chat_usage_statistics_api(request) -> 'Response':
    """
    處理聊天使用統計 API 請求的便利函數
    
    Args:
        request: HTTP 請求對象
        
    Returns:
        Response: DRF 回應
    """
    try:
        handler = ChatAnalyticsAPIHandler()
        return handler.handle_statistics_request(request)
    except Exception as e:
        logger.error(f"Chat usage statistics API failed: {e}")
        return Response({
            'success': False,
            'error': 'Chat analytics service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def handle_record_chat_usage_api(request) -> 'Response':
    """
    處理記錄聊天使用 API 請求的便利函數
    
    Args:
        request: HTTP 請求對象
        
    Returns:
        Response: DRF 回應
    """
    try:
        handler = ChatAnalyticsAPIHandler()
        return handler.handle_record_usage_request(request)
    except Exception as e:
        logger.error(f"Record chat usage API failed: {e}")
        return Response({
            'success': False,
            'error': 'Chat analytics service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


def create_chat_statistics_handler() -> Optional[ChatUsageStatisticsHandler]:
    """創建聊天統計處理器"""
    try:
        return ChatUsageStatisticsHandler()
    except Exception as e:
        logger.warning(f"無法創建聊天統計處理器: {e}")
        return None


def create_chat_usage_recorder() -> Optional[ChatUsageRecorder]:
    """創建聊天使用記錄器"""
    try:
        return ChatUsageRecorder()
    except Exception as e:
        logger.warning(f"無法創建聊天使用記錄器: {e}")
        return None


def create_chat_analytics_api_handler() -> Optional[ChatAnalyticsAPIHandler]:
    """創建聊天分析 API 處理器"""
    try:
        return ChatAnalyticsAPIHandler()
    except Exception as e:
        logger.warning(f"無法創建聊天分析 API 處理器: {e}")
        return None


def get_statistics_for_days(days: int = 30) -> dict:
    """
    獲取指定天數的統計數據 - 便利函數
    
    Args:
        days: 統計天數
        
    Returns:
        dict: 統計數據
    """
    try:
        handler = create_chat_statistics_handler()
        if handler:
            return handler.get_statistics(days)
        else:
            return {
                'pie_chart': [],
                'daily_chart': [],
                'summary': {}
            }
    except Exception as e:
        logger.error(f"獲取統計數據失敗: {e}")
        return {
            'pie_chart': [],
            'daily_chart': [],
            'summary': {}
        }