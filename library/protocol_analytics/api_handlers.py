"""
Protocol Analytics API Handlers - Protocol Analytics API 處理器

此模組負責：
- 處理 Protocol Analytics 統計 API 請求
- 統一錯誤處理和回應格式
- API 認證和權限控制
- 提供 Overview、Questions、Satisfaction、Trends 等端點

基於 Common Analytics 基礎設施
"""

import logging
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime

logger = logging.getLogger(__name__)


class ProtocolAnalyticsAPIHandler:
    """Protocol Analytics API 處理器"""
    
    def __init__(self):
        """初始化處理器"""
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def handle_overview_request(self, request) -> Response:
        """
        處理總覽統計請求
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 獲取參數
            days = int(request.GET.get('days', 7))
            
            # 🔥 修正權限邏輯：參考 RVT Analytics 的實現
            # 管理員可以查看所有用戶資料，一般用戶只能看自己的
            user_id_param = request.GET.get('user_id', None)
            target_user = None  # 預設查看所有資料（管理員）
            
            if user_id_param and user_id_param != 'all':
                # 明確指定 user_id，且不是 'all'
                if not (request.user.is_staff or request.user.is_superuser):
                    return Response({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                # 管理員可以查看特定用戶
                try:
                    from django.contrib.auth.models import User
                    target_user = User.objects.get(id=user_id_param)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': '用戶不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            elif not (request.user.is_staff or request.user.is_superuser):
                # 非管理員只能查看自己的數據
                target_user = request.user if request.user.is_authenticated else None
            # else: 管理員且未指定 user_id，target_user = None（查看所有資料）
            
            # 獲取統計數據
            from .statistics_manager import ProtocolStatisticsManager
            manager = ProtocolStatisticsManager()
            stats = manager.get_comprehensive_stats(days=days, user=target_user)
            
            # 返回成功回應
            return Response({
                'success': True,
                'data': stats,
                'generated_at': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"處理總覽請求失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_questions_request(self, request) -> Response:
        """
        處理問題分析請求
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 獲取參數
            days = int(request.GET.get('days', 30))
            
            # 🔥 修正權限邏輯：與 overview 保持一致
            user_id_param = request.GET.get('user_id', None)
            target_user = None  # 預設查看所有資料（管理員）
            
            if user_id_param and user_id_param != 'all':
                # 明確指定 user_id
                if not (request.user.is_staff or request.user.is_superuser):
                    return Response({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                try:
                    from django.contrib.auth.models import User
                    target_user = User.objects.get(id=user_id_param)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': '用戶不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            elif not (request.user.is_staff or request.user.is_superuser):
                # 非管理員只能查看自己的數據
                target_user = request.user if request.user.is_authenticated else None
            
            # 獲取問題統計
            from .statistics_manager import ProtocolStatisticsManager
            manager = ProtocolStatisticsManager()
            question_stats = manager._get_question_stats(days=days, user=target_user)
            
            # 返回成功回應（包裝在 data 中，與 RVT 格式一致）
            return Response({
                'success': True,
                'data': question_stats,  # 包裝在 data 中
                'generated_at': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"處理問題分析請求失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_satisfaction_request(self, request) -> Response:
        """
        處理滿意度分析請求
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 獲取參數
            days = int(request.GET.get('days', 30))
            
            # 🔥 修正權限邏輯：與 overview 保持一致
            user_id_param = request.GET.get('user_id', None)
            target_user = None  # 預設查看所有資料（管理員）
            
            if user_id_param and user_id_param != 'all':
                # 明確指定 user_id
                if not (request.user.is_staff or request.user.is_superuser):
                    return Response({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                try:
                    from django.contrib.auth.models import User
                    target_user = User.objects.get(id=user_id_param)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': '用戶不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            elif not (request.user.is_staff or request.user.is_superuser):
                # 非管理員只能查看自己的數據
                target_user = request.user if request.user.is_authenticated else None
            
            # 獲取滿意度統計
            from .statistics_manager import ProtocolStatisticsManager
            manager = ProtocolStatisticsManager()
            satisfaction_stats = manager._get_satisfaction_stats(days=days, user=target_user)
            
            # 返回成功回應
            return Response({
                'success': True,
                **satisfaction_stats,  # 直接展開滿意度數據
                'generated_at': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"處理滿意度分析請求失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_trends_request(self, request) -> Response:
        """
        處理趨勢分析請求
        
        Args:
            request: Django request 對象
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 獲取參數
            days = int(request.GET.get('days', 30))
            
            # 🔥 修正權限邏輯：與 overview 保持一致
            user_id_param = request.GET.get('user_id', None)
            target_user = None  # 預設查看所有資料（管理員）
            
            if user_id_param and user_id_param != 'all':
                # 明確指定 user_id
                if not (request.user.is_staff or request.user.is_superuser):
                    return Response({
                        'success': False,
                        'error': '無權限查看其他用戶數據'
                    }, status=status.HTTP_403_FORBIDDEN)
                
                try:
                    from django.contrib.auth.models import User
                    target_user = User.objects.get(id=user_id_param)
                except User.DoesNotExist:
                    return Response({
                        'success': False,
                        'error': '用戶不存在'
                    }, status=status.HTTP_404_NOT_FOUND)
            elif not (request.user.is_staff or request.user.is_superuser):
                # 非管理員只能查看自己的數據
                target_user = request.user if request.user.is_authenticated else None
            
            # TODO: 實現趨勢分析邏輯
            # 目前返回基本趨勢數據
            from django.utils import timezone
            from datetime import timedelta
            from api.models import ChatMessage, ConversationSession
            
            start_date = timezone.now() - timedelta(days=days)
            
            # 簡單的每日統計
            daily_stats = []
            for i in range(days):
                date = start_date + timedelta(days=i)
                next_date = date + timedelta(days=1)
                
                messages_count = ChatMessage.objects.filter(
                    created_at__gte=date,
                    created_at__lt=next_date,
                    role='user'
                ).count()
                
                daily_stats.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'messages': messages_count
                })
            
            trends = {
                'daily_message_counts': daily_stats,
                'period': f'{days} days'
            }
            
            # 返回成功回應
            return Response({
                'success': True,
                'trends': trends,
                'generated_at': datetime.now().isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"處理趨勢分析請求失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== 便利函數 ====================

def handle_protocol_analytics_api(request, endpoint='overview') -> Response:
    """
    便利函數：路由 Protocol Analytics API 請求
    
    Args:
        request: Django request 對象
        endpoint: API 端點名稱
        
    Returns:
        Response: DRF Response 對象
    """
    handler = ProtocolAnalyticsAPIHandler()
    
    if endpoint == 'overview':
        return handler.handle_overview_request(request)
    elif endpoint == 'questions':
        return handler.handle_questions_request(request)
    elif endpoint == 'satisfaction':
        return handler.handle_satisfaction_request(request)
    elif endpoint == 'trends':
        return handler.handle_trends_request(request)
    else:
        return Response({
            'success': False,
            'error': f'Unknown endpoint: {endpoint}'
        }, status=status.HTTP_404_NOT_FOUND)


def handle_protocol_feedback_api(request) -> Response:
    """
    便利函數：處理反饋 API（暫時佔位，未來實現）
    
    Args:
        request: Django request 對象
        
    Returns:
        Response: DRF Response 對象
    """
    # 未來可實現 Protocol 專屬的反饋機制
    return Response({
        'success': False,
        'error': 'Feedback API not implemented yet'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


__all__ = [
    'ProtocolAnalyticsAPIHandler',
    'handle_protocol_analytics_api',
    'handle_protocol_feedback_api',
]
