"""
統計分析 - Statistics

提供對話數據的統計和分析功能。

Author: AI Platform Team
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Sum, Avg, Q

logger = logging.getLogger(__name__)

# 延遲導入避免循環依賴
def get_models():
    """延遲導入 Django 模型"""
    try:
        from api.models import ConversationSession, ChatMessage
        return ConversationSession, ChatMessage
    except ImportError:
        return None, None


class ConversationStatistics:
    """對話統計分析類"""
    
    @staticmethod
    def get_user_stats(user_id: Optional[int] = None, guest_id: Optional[str] = None) -> Dict[str, Any]:
        """
        獲取用戶或訪客的統計資料
        
        Args:
            user_id: 用戶ID
            guest_id: 訪客標識
            
        Returns:
            dict: 統計資料
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession or not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 構建查詢條件
            if user_id:
                session_filter = Q(user_id=user_id, is_guest_session=False)
                user_type = "registered"
            elif guest_id:
                session_filter = Q(guest_identifier=guest_id, is_guest_session=True)
                user_type = "guest"
            else:
                return {"success": False, "error": "Either user_id or guest_id is required"}
            
            # 基本統計
            sessions = ConversationSession.objects.filter(session_filter)
            total_sessions = sessions.count()
            
            if total_sessions == 0:
                return {
                    "success": True,
                    "user_type": user_type,
                    "total_sessions": 0,
                    "total_messages": 0,
                    "total_tokens": 0,
                    "avg_messages_per_session": 0,
                    "avg_response_time": 0
                }
            
            # 聚合統計
            session_stats = sessions.aggregate(
                total_messages=Sum('message_count'),
                total_tokens=Sum('total_tokens'),
                avg_messages=Avg('message_count'),
                total_response_time=Sum('total_response_time')
            )
            
            # 訊息統計
            messages = ChatMessage.objects.filter(conversation__in=sessions)
            message_stats = messages.aggregate(
                user_messages=Count('id', filter=Q(role='user')),
                assistant_messages=Count('id', filter=Q(role='assistant')),
                avg_response_time=Avg('response_time', filter=Q(role='assistant'))
            )
            
            return {
                "success": True,
                "user_type": user_type,
                "total_sessions": total_sessions,
                "total_messages": session_stats['total_messages'] or 0,
                "total_tokens": session_stats['total_tokens'] or 0,
                "avg_messages_per_session": round(session_stats['avg_messages'] or 0, 2),
                "total_response_time": session_stats['total_response_time'] or 0,
                "user_messages": message_stats['user_messages'] or 0,
                "assistant_messages": message_stats['assistant_messages'] or 0,
                "avg_response_time": round(message_stats['avg_response_time'] or 0, 2)
            }
            
        except Exception as e:
            logger.error(f"Failed to get user stats: {str(e)}")
            return {"success": False, "error": f"Stats calculation failed: {str(e)}"}
    
    @staticmethod
    def get_daily_stats(
        date: Optional[datetime] = None,
        chat_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        獲取每日統計資料
        
        Args:
            date: 指定日期（預設今天）
            chat_type: 聊天類型篩選
            
        Returns:
            dict: 每日統計
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession or not ChatMessage:
            return {"success": False, "error": "Models not available"}
        
        try:
            if not date:
                date = timezone.now().date()
            
            # 查詢條件
            session_filter = Q(created_at__date=date)
            if chat_type:
                session_filter &= Q(chat_type=chat_type)
            
            sessions = ConversationSession.objects.filter(session_filter)
            
            # 統計資料
            stats = {
                "date": date.isoformat(),
                "chat_type": chat_type or "all",
                "total_sessions": sessions.count(),
                "registered_user_sessions": sessions.filter(is_guest_session=False).count(),
                "guest_sessions": sessions.filter(is_guest_session=True).count(),
            }
            
            # 聚合統計
            if stats["total_sessions"] > 0:
                session_aggregates = sessions.aggregate(
                    total_messages=Sum('message_count'),
                    total_tokens=Sum('total_tokens'),
                    avg_messages=Avg('message_count')
                )
                
                stats.update({
                    "total_messages": session_aggregates['total_messages'] or 0,
                    "total_tokens": session_aggregates['total_tokens'] or 0,
                    "avg_messages_per_session": round(session_aggregates['avg_messages'] or 0, 2)
                })
            else:
                stats.update({
                    "total_messages": 0,
                    "total_tokens": 0,
                    "avg_messages_per_session": 0
                })
            
            return {"success": True, "stats": stats}
            
        except Exception as e:
            logger.error(f"Failed to get daily stats: {str(e)}")
            return {"success": False, "error": f"Daily stats failed: {str(e)}"}
    
    @staticmethod
    def get_period_stats(
        start_date: datetime,
        end_date: datetime,
        chat_type: Optional[str] = None,
        group_by: str = "day"  # "day", "week", "month"
    ) -> Dict[str, Any]:
        """
        獲取期間統計資料
        
        Args:
            start_date: 開始日期
            end_date: 結束日期
            chat_type: 聊天類型篩選
            group_by: 分組方式
            
        Returns:
            dict: 期間統計
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 查詢條件
            session_filter = Q(
                created_at__date__gte=start_date.date(),
                created_at__date__lte=end_date.date()
            )
            if chat_type:
                session_filter &= Q(chat_type=chat_type)
            
            sessions = ConversationSession.objects.filter(session_filter)
            
            # 根據分組方式進行統計
            if group_by == "day":
                # 按日分組
                from django.db.models.functions import TruncDate
                grouped_stats = sessions.annotate(
                    period=TruncDate('created_at')
                ).values('period').annotate(
                    session_count=Count('id'),
                    message_count=Sum('message_count'),
                    token_count=Sum('total_tokens')
                ).order_by('period')
                
            elif group_by == "week":
                # 按週分組
                from django.db.models.functions import TruncWeek
                grouped_stats = sessions.annotate(
                    period=TruncWeek('created_at')
                ).values('period').annotate(
                    session_count=Count('id'),
                    message_count=Sum('message_count'),
                    token_count=Sum('total_tokens')
                ).order_by('period')
                
            elif group_by == "month":
                # 按月分組
                from django.db.models.functions import TruncMonth
                grouped_stats = sessions.annotate(
                    period=TruncMonth('created_at')
                ).values('period').annotate(
                    session_count=Count('id'),
                    message_count=Sum('message_count'),
                    token_count=Sum('total_tokens')
                ).order_by('period')
            else:
                return {"success": False, "error": "Invalid group_by parameter"}
            
            # 轉換為列表
            stats_list = []
            for item in grouped_stats:
                stats_list.append({
                    "period": item['period'].isoformat() if item['period'] else None,
                    "session_count": item['session_count'] or 0,
                    "message_count": item['message_count'] or 0,
                    "token_count": item['token_count'] or 0
                })
            
            # 總計
            totals = sessions.aggregate(
                total_sessions=Count('id'),
                total_messages=Sum('message_count'),
                total_tokens=Sum('total_tokens')
            )
            
            return {
                "success": True,
                "period": {
                    "start_date": start_date.date().isoformat(),
                    "end_date": end_date.date().isoformat(),
                    "group_by": group_by,
                    "chat_type": chat_type or "all"
                },
                "totals": {
                    "total_sessions": totals['total_sessions'] or 0,
                    "total_messages": totals['total_messages'] or 0,
                    "total_tokens": totals['total_tokens'] or 0
                },
                "grouped_stats": stats_list
            }
            
        except Exception as e:
            logger.error(f"Failed to get period stats: {str(e)}")
            return {"success": False, "error": f"Period stats failed: {str(e)}"}
    
    @staticmethod
    def get_chat_type_distribution() -> Dict[str, Any]:
        """
        獲取聊天類型分佈統計
        
        Returns:
            dict: 聊天類型分佈
        """
        ConversationSession, ChatMessage = get_models()
        if not ConversationSession:
            return {"success": False, "error": "Models not available"}
        
        try:
            # 按聊天類型統計
            type_stats = ConversationSession.objects.values('chat_type').annotate(
                session_count=Count('id'),
                message_count=Sum('message_count'),
                token_count=Sum('total_tokens'),
                registered_users=Count('id', filter=Q(is_guest_session=False)),
                guest_users=Count('id', filter=Q(is_guest_session=True))
            ).order_by('-session_count')
            
            # 轉換為列表
            distribution = []
            for item in type_stats:
                distribution.append({
                    "chat_type": item['chat_type'],
                    "session_count": item['session_count'],
                    "message_count": item['message_count'] or 0,
                    "token_count": item['token_count'] or 0,
                    "registered_users": item['registered_users'],
                    "guest_users": item['guest_users']
                })
            
            return {
                "success": True,
                "distribution": distribution
            }
            
        except Exception as e:
            logger.error(f"Failed to get chat type distribution: {str(e)}")
            return {"success": False, "error": f"Distribution stats failed: {str(e)}"}