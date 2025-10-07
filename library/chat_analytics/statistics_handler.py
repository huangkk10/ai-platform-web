"""
Chat Analytics Statistics Handler - 統計分析處理器
===============================================

處理聊天使用統計相關的邏輯：
- 日期範圍計算
- 查詢集處理
- 圓餅圖數據生成
- 每日統計數據生成
- 總體統計計算
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

try:
    from django.db.models import Count, Avg
    from django.utils import timezone
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

logger = logging.getLogger(__name__)

# 聊天類型映射
CHAT_TYPE_DISPLAY_MAP = {
    'know_issue_chat': 'Protocol RAG',
    'log_analyze_chat': 'AI OCR', 
    'rvt_assistant_chat': 'RVT Assistant'
}


class ChatUsageStatisticsHandler:
    """聊天使用統計處理器 - 處理各種統計分析"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.chat_type_map = CHAT_TYPE_DISPLAY_MAP
        
    def _get_date_range(self, days: int) -> Tuple[datetime, datetime]:
        """
        獲取日期範圍
        
        Args:
            days: 天數
            
        Returns:
            Tuple[datetime, datetime]: (開始日期, 結束日期)
        """
        try:
            current_time = timezone.now()
            end_date = current_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            start_date = (current_time - timedelta(days=days-1)).replace(hour=0, minute=0, second=0, microsecond=0)
            
            self.logger.info(f"統計日期範圍: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
            return start_date, end_date
            
        except Exception as e:
            self.logger.error(f"日期範圍計算失敗: {e}")
            raise
    
    def _get_base_queryset(self, days: int) -> Tuple[Any, datetime, datetime]:
        """
        獲取基礎查詢集
        
        Args:
            days: 天數
            
        Returns:
            Tuple: (QuerySet, 開始日期, 結束日期)
        """
        try:
            # 動態導入避免循環依賴
            from api.models import ChatUsage
            
            start_date, end_date = self._get_date_range(days)
            
            base_queryset = ChatUsage.objects.filter(
                created_at__gte=start_date,
                created_at__lte=end_date
            )
            
            self.logger.info(f"基礎查詢集記錄數: {base_queryset.count()}")
            return base_queryset, start_date, end_date
            
        except ImportError:
            self.logger.error("ChatUsage model 不可用")
            raise
        except Exception as e:
            self.logger.error(f"基礎查詢集獲取失敗: {e}")
            raise
    
    def get_pie_chart_data(self, base_queryset) -> List[Dict[str, Any]]:
        """
        生成圓餅圖數據
        
        Args:
            base_queryset: 基礎查詢集
            
        Returns:
            List[Dict[str, Any]]: 圓餅圖數據
        """
        try:
            chat_type_stats = base_queryset.values('chat_type').annotate(
                count=Count('id'),
                avg_response_time=Avg('response_time')
            ).order_by('-count')
            
            pie_chart_data = []
            
            for stat in chat_type_stats:
                pie_chart_data.append({
                    'name': self.chat_type_map.get(stat['chat_type'], stat['chat_type']),
                    'value': stat['count'],
                    'type': stat['chat_type'],
                    'avg_response_time': round(stat['avg_response_time'] or 0, 2)
                })
            
            self.logger.info(f"圓餅圖數據生成完成: {len(pie_chart_data)} 個類型")
            return pie_chart_data
            
        except Exception as e:
            self.logger.error(f"圓餅圖數據生成失敗: {e}")
            return []
    
    def get_daily_chart_data(self, base_queryset, start_date: datetime, days: int) -> List[Dict[str, Any]]:
        """
        生成每日統計數據
        
        Args:
            base_queryset: 基礎查詢集
            start_date: 開始日期
            days: 天數
            
        Returns:
            List[Dict[str, Any]]: 每日統計數據
        """
        try:
            daily_stats = []
            
            for i in range(days):
                current_date = (start_date + timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                next_date = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                
                day_usage = base_queryset.filter(
                    created_at__gte=current_date,
                    created_at__lte=next_date
                )
                
                # 各類型當日使用次數
                know_issue_count = day_usage.filter(chat_type='know_issue_chat').count()
                log_analyze_count = day_usage.filter(chat_type='log_analyze_chat').count()
                rvt_assistant_count = day_usage.filter(chat_type='rvt_assistant_chat').count()
                total_count = day_usage.count()
                
                daily_stats.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'total': total_count,
                    'know_issue_chat': know_issue_count,
                    'log_analyze_chat': log_analyze_count,
                    'rvt_assistant_chat': rvt_assistant_count
                })
            
            self.logger.info(f"每日統計數據生成完成: {days} 天")
            return daily_stats
            
        except Exception as e:
            self.logger.error(f"每日統計數據生成失敗: {e}")
            return []
    
    def get_summary_statistics(self, base_queryset, start_date: datetime, end_date: datetime, days: int) -> Dict[str, Any]:
        """
        生成總體統計
        
        Args:
            base_queryset: 基礎查詢集
            start_date: 開始日期
            end_date: 結束日期
            days: 天數
            
        Returns:
            Dict[str, Any]: 總體統計數據
        """
        try:
            total_usage = base_queryset.count()
            total_users = base_queryset.values('user').distinct().count()
            total_files = base_queryset.filter(has_file_upload=True).count()
            avg_response_time = base_queryset.aggregate(avg=Avg('response_time'))['avg']
            
            summary_stats = {
                'total_chats': total_usage,
                'total_users': total_users,
                'total_file_uploads': total_files,
                'avg_response_time': round(avg_response_time or 0, 2),
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'days': days
                }
            }
            
            self.logger.info(f"總體統計完成: {total_usage} 次聊天, {total_users} 個用戶")
            return summary_stats
            
        except Exception as e:
            self.logger.error(f"總體統計生成失敗: {e}")
            return {}
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """
        獲取完整統計數據
        
        Args:
            days: 統計天數
            
        Returns:
            Dict[str, Any]: 完整統計數據
        """
        try:
            # 獲取基礎查詢集
            base_queryset, start_date, end_date = self._get_base_queryset(days)
            
            # 生成各種統計數據
            pie_chart_data = self.get_pie_chart_data(base_queryset)
            daily_chart_data = self.get_daily_chart_data(base_queryset, start_date, days)
            summary_stats = self.get_summary_statistics(base_queryset, start_date, end_date, days)
            
            result = {
                'pie_chart': pie_chart_data,
                'daily_chart': daily_chart_data,
                'summary': summary_stats
            }
            
            self.logger.info("完整統計數據生成完成")
            return result
            
        except Exception as e:
            self.logger.error(f"統計數據生成失敗: {e}")
            return {
                'pie_chart': [],
                'daily_chart': [],
                'summary': {}
            }