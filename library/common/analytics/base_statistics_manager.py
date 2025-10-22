"""
Base Statistics Manager - 共用統計管理器基礎類別

提供所有 Assistant 統計管理的共用邏輯和抽象介面。
各個 Assistant 繼承此類別並實作特定邏輯。

Usage:
    from library.common.analytics.base_statistics_manager import BaseStatisticsManager
    
    class RVTStatisticsManager(BaseStatisticsManager):
        def get_assistant_type(self):
            return 'rvt_assistant'
        
        def get_message_model(self):
            from api.models import ChatMessage
            return ChatMessage
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseStatisticsManager(ABC):
    """
    統計管理器基礎類別
    
    提供共用的統計邏輯，子類別需要實作 Assistant 特定的方法
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    # ==================== 抽象方法（子類別必須實作） ====================
    
    @abstractmethod
    def get_assistant_type(self) -> str:
        """
        返回 Assistant 類型識別符
        
        Examples:
            - 'rvt_assistant'
            - 'protocol_assistant'
            - 'qa_assistant'
        """
        pass
    
    @abstractmethod
    def get_conversation_model(self):
        """
        返回對話 Model 類別
        
        Returns:
            Django Model: 如 ConversationSession
        """
        pass
    
    @abstractmethod
    def get_message_model(self):
        """
        返回消息 Model 類別
        
        Returns:
            Django Model: 如 ChatMessage
        """
        pass
    
    # ==================== 可選覆寫方法 ====================
    
    def get_system_type_filter(self) -> str:
        """
        返回 system_type 過濾值（預設使用 get_assistant_type）
        
        如果資料庫中的 system_type 與 assistant_type 不同，可以覆寫此方法
        """
        return self.get_assistant_type()
    
    def get_additional_conversation_filters(self) -> Dict:
        """
        返回額外的對話查詢過濾條件（子類別可選覆寫）
        
        Returns:
            dict: Django ORM 過濾參數
        """
        return {}
    
    def get_additional_message_filters(self) -> Dict:
        """
        返回額外的消息查詢過濾條件（子類別可選覆寫）
        
        Returns:
            dict: Django ORM 過濾參數
        """
        return {}
    
    # ==================== 共用統計方法 ====================
    
    def get_comprehensive_stats(self, days=30, user=None) -> Dict:
        """
        獲取綜合統計數據（共用邏輯）
        
        Args:
            days: 統計天數
            user: 特定用戶（可選）
            
        Returns:
            dict: 綜合統計結果
        """
        try:
            # 獲取各項統計
            overview_stats = self._get_overview_stats(days, user)
            performance_stats = self._get_performance_stats(days, user)
            trend_stats = self._get_trend_stats(days, user)
            
            return {
                'generated_at': datetime.now().isoformat(),
                'period': f'{days} 天',
                'assistant_type': self.get_assistant_type(),
                'user_filter': user.username if user else 'all',
                'overview': overview_stats,
                'performance_metrics': performance_stats,
                'trends': trend_stats
            }
            
        except Exception as e:
            self.logger.error(f"獲取綜合統計失敗: {str(e)}", exc_info=True)
            return {
                'error': f'統計生成失敗: {str(e)}',
                'generated_at': datetime.now().isoformat(),
                'assistant_type': self.get_assistant_type()
            }
    
    def _get_overview_stats(self, days: int, user=None) -> Dict:
        """獲取概覽統計（共用邏輯）"""
        try:
            from django.utils import timezone
            
            ConversationModel = self.get_conversation_model()
            MessageModel = self.get_message_model()
            
                        # 基礎查詢
            start_date = timezone.now() - timedelta(days=days)
            assistant_type = self.get_assistant_type()
            
            # 會話統計（按 chat_type 過濾）
            # 注意：assistant_type 需要添加 '_chat' 後綴
            chat_type = f"{assistant_type}_chat" if not assistant_type.endswith('_chat') else assistant_type
            sessions_query = ConversationModel.objects.filter(
                created_at__gte=start_date,
                chat_type=chat_type
            )
            
            # 應用額外過濾條件
            extra_filters = self.get_additional_conversation_filters()
            if extra_filters:
                sessions_query = sessions_query.filter(**extra_filters)
            
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            total_sessions = sessions_query.count()
            active_sessions = sessions_query.filter(is_active=True).count() if hasattr(ConversationModel, 'is_active') else 0
            guest_sessions = sessions_query.filter(is_guest_session=True).count() if hasattr(ConversationModel, 'is_guest_session') else 0
            
            # 消息統計（conversation_id 指向 conversation_sessions.id）
            conversation_ids = sessions_query.values_list('id', flat=True)
            messages_query = MessageModel.objects.filter(
                conversation_id__in=conversation_ids,
                created_at__gte=start_date
            )
            
            # 應用消息額外過濾條件
            extra_message_filters = self.get_additional_message_filters()
            if extra_message_filters:
                messages_query = messages_query.filter(**extra_message_filters)
            
            total_messages = messages_query.count()
            user_messages = messages_query.filter(role='user').count()
            assistant_messages = messages_query.filter(role='assistant').count()
            
            # 計算平均值
            avg_messages_per_session = total_messages / total_sessions if total_sessions > 0 else 0
            
            return {
                'total_conversations': total_sessions,
                'active_conversations': active_sessions,
                'guest_conversations': guest_sessions,
                'registered_user_conversations': total_sessions - guest_sessions if guest_sessions > 0 else total_sessions,
                'total_messages': total_messages,
                'user_messages': user_messages,
                'assistant_messages': assistant_messages,
                'avg_messages_per_conversation': round(avg_messages_per_session, 2)
            }
            
        except Exception as e:
            self.logger.error(f"獲取概覽統計失敗: {str(e)}", exc_info=True)
            return {
                'total_conversations': 0,
                'total_messages': 0,
                'error': str(e)
            }
    
    def _get_performance_stats(self, days: int, user=None) -> Dict:
        """獲取性能統計（共用邏輯）"""
        try:
            from django.utils import timezone
            from django.db.models import Avg, Max, Min, Count, Q, F
            
            MessageModel = self.get_message_model()
            ConversationModel = self.get_conversation_model()
            
            start_date = timezone.now() - timedelta(days=days)
            assistant_type = self.get_assistant_type()
            
            # 注意：assistant_type 需要添加 '_chat' 後綴
            chat_type = f"{assistant_type}_chat" if not assistant_type.endswith('_chat') else assistant_type
            
            # 獲取對話 IDs
            sessions_query = ConversationModel.objects.filter(
                created_at__gte=start_date,
                chat_type=chat_type
            )
            
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            conversation_ids = sessions_query.values_list('id', flat=True)
            
            # 查詢 assistant 消息（有 response_time 欄位）
            messages_query = MessageModel.objects.filter(
                conversation_id__in=conversation_ids,
                role='assistant',
                created_at__gte=start_date
            )
            
            # 如果有 response_time 欄位，計算性能指標
            if hasattr(MessageModel, 'response_time'):
                # 過濾掉異常值（response_time 為 None 或過大）
                messages_with_time = messages_query.filter(
                    response_time__isnull=False,
                    response_time__lt=300  # 5 分鐘以內
                )
                
                stats = messages_with_time.aggregate(
                    avg_time=Avg('response_time'),
                    max_time=Max('response_time'),
                    min_time=Min('response_time'),
                    total_count=Count('id')
                )
                
                # 回應時間分布
                response_time_dist = {
                    '< 3s': messages_with_time.filter(response_time__lt=3).count(),
                    '3-10s': messages_with_time.filter(response_time__gte=3, response_time__lt=10).count(),
                    '10-30s': messages_with_time.filter(response_time__gte=10, response_time__lt=30).count(),
                    '> 30s': messages_with_time.filter(response_time__gte=30).count()
                }
                
                return {
                    'avg_response_time': round(stats['avg_time'], 2) if stats['avg_time'] else 0,
                    'max_response_time': round(stats['max_time'], 2) if stats['max_time'] else 0,
                    'min_response_time': round(stats['min_time'], 2) if stats['min_time'] else 0,
                    'total_responses': stats['total_count'] or 0,
                    'response_time_distribution': response_time_dist
                }
            else:
                return {
                    'avg_response_time': 0,
                    'max_response_time': 0,
                    'message': 'Response time tracking not available'
                }
            
        except Exception as e:
            self.logger.error(f"獲取性能統計失敗: {str(e)}", exc_info=True)
            return {
                'avg_response_time': 0,
                'error': str(e)
            }
    
    def _get_trend_stats(self, days: int, user=None) -> Dict:
        """獲取趨勢統計（共用邏輯）"""
        try:
            from django.utils import timezone
            from django.db.models.functions import TruncDate
            from django.db.models import Count
            
            ConversationModel = self.get_conversation_model()
            MessageModel = self.get_message_model()
            
            start_date = timezone.now() - timedelta(days=days)
            assistant_type = self.get_assistant_type()
            
            # 注意：assistant_type 需要添加 '_chat' 後綴
            chat_type = f"{assistant_type}_chat" if not assistant_type.endswith('_chat') else assistant_type
            
            # 會話趨勢
            sessions_query = ConversationModel.objects.filter(
                created_at__gte=start_date,
                chat_type=chat_type
            )
            
            if user:
                sessions_query = sessions_query.filter(user=user)
            
            daily_conversations = sessions_query.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            # 消息趨勢（conversation_id 指向 conversation_sessions.id）
            conversation_ids = sessions_query.values_list('id', flat=True)
            messages_query = MessageModel.objects.filter(
                conversation_id__in=conversation_ids,
                created_at__gte=start_date
            )
            
            daily_messages = messages_query.annotate(
                date=TruncDate('created_at')
            ).values('date').annotate(
                count=Count('id')
            ).order_by('date')
            
            # 轉換為字典格式
            conversations_dict = {
                str(item['date']): item['count'] 
                for item in daily_conversations
            }
            
            messages_dict = {
                str(item['date']): item['count'] 
                for item in daily_messages
            }
            
            return {
                'daily_conversations': conversations_dict,
                'daily_messages': messages_dict
            }
            
        except Exception as e:
            self.logger.error(f"獲取趨勢統計失敗: {str(e)}", exc_info=True)
            return {
                'daily_conversations': {},
                'daily_messages': {},
                'error': str(e)
            }


# 便利函數
def create_statistics_manager(assistant_type: str):
    """
    工廠函數：根據 assistant_type 創建對應的統計管理器
    
    Args:
        assistant_type: 'rvt_assistant', 'protocol_assistant', etc.
        
    Returns:
        BaseStatisticsManager: 對應的統計管理器實例
    """
    if assistant_type == 'rvt_assistant':
        try:
            from library.rvt_analytics.statistics_manager import StatisticsManager
            return StatisticsManager()
        except ImportError:
            logger.warning("RVT StatisticsManager not available")
            return None
    elif assistant_type == 'protocol_assistant':
        try:
            from library.protocol_analytics.statistics_manager import ProtocolStatisticsManager
            return ProtocolStatisticsManager()
        except ImportError:
            logger.warning("Protocol StatisticsManager not available")
            return None
    else:
        logger.error(f"Unknown assistant type: {assistant_type}")
        return None
