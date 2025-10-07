"""
Know Issue Convenience Functions - 便利函數
==========================================

提供簡化的接口函數，讓其他模組更容易使用 Know Issue 功能
"""

import logging
from typing import Optional
from rest_framework import status
from rest_framework.response import Response
from .processors import KnowIssueProcessor
from .viewset_manager import KnowIssueViewSetManager
from .api_handlers import KnowIssueAPIHandler

logger = logging.getLogger(__name__)


def process_know_issue_create(request, serializer, user=None) -> Response:
    """
    處理 Know Issue 創建的便利函數
    
    Args:
        request: HTTP 請求
        serializer: 序列化器
        user: 用戶對象（可選，從 request 中獲取）
        
    Returns:
        Response: DRF 回應
    """
    try:
        manager = KnowIssueViewSetManager()
        
        # 如果沒有提供用戶，從請求中獲取
        if not user and hasattr(request, 'user'):
            user = request.user
            
        # 設置用戶到請求中
        request.user = user
        
        return manager.handle_create(request, serializer)
        
    except Exception as e:
        logger.error(f"process_know_issue_create 失敗: {e}")
        return Response({
            'error': f'Know Issue 創建處理失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def process_know_issue_update(request, instance, serializer, user=None) -> Response:
    """
    處理 Know Issue 更新的便利函數
    
    Args:
        request: HTTP 請求
        instance: Know Issue 實例
        serializer: 序列化器
        user: 用戶對象（可選，從 request 中獲取）
        
    Returns:
        Response: DRF 回應
    """
    try:
        manager = KnowIssueViewSetManager()
        
        # 如果沒有提供用戶，從請求中獲取
        if not user and hasattr(request, 'user'):
            user = request.user
            
        # 設置用戶到請求中
        request.user = user
        
        return manager.handle_update(request, instance, serializer)
        
    except Exception as e:
        logger.error(f"process_know_issue_update 失敗: {e}")
        return Response({
            'error': f'Know Issue 更新處理失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def handle_dify_know_issue_search_api(request) -> Response:
    """
    處理 Dify Know Issue 搜索 API 的便利函數
    
    Args:
        request: HTTP 請求
        
    Returns:
        Response: DRF 回應
    """
    try:
        handler = KnowIssueAPIHandler()
        return handler.handle_dify_know_issue_search_api(request)
    except Exception as e:
        logger.error(f"handle_dify_know_issue_search_api 失敗: {e}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def create_know_issue_processor() -> Optional[KnowIssueProcessor]:
    """創建 Know Issue 處理器"""
    try:
        return KnowIssueProcessor()
    except Exception as e:
        logger.warning(f"無法創建 Know Issue 處理器: {e}")
        return None


def create_know_issue_viewset_manager() -> Optional[KnowIssueViewSetManager]:
    """創建 Know Issue ViewSet 管理器"""
    try:
        return KnowIssueViewSetManager()
    except Exception as e:
        logger.warning(f"無法創建 Know Issue ViewSet 管理器: {e}")
        return None


def create_know_issue_api_handler() -> Optional[KnowIssueAPIHandler]:
    """創建 Know Issue API 處理器"""
    try:
        return KnowIssueAPIHandler()
    except Exception as e:
        logger.warning(f"無法創建 Know Issue API 處理器: {e}")
        return None