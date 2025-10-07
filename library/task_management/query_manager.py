"""
Task Query Manager - 任務查詢管理器

統一管理任務相關的查詢邏輯：
- 用戶權限過濾
- 複雜查詢條件
- 搜尋和排序功能
"""

import logging
from django.db import models

logger = logging.getLogger(__name__)


class TaskQueryManager:
    """任務查詢管理器 - 處理複雜的任務查詢邏輯"""
    
    def __init__(self):
        self.logger = logger
    
    def get_user_related_tasks(self, user, base_queryset=None):
        """
        獲取用戶相關的任務
        
        Args:
            user: Django User 實例
            base_queryset: 基礎查詢集，如果為 None 則使用 Task.objects.all()
            
        Returns:
            QuerySet: 過濾後的任務查詢集
        """
        try:
            if base_queryset is None:
                # 動態導入避免循環依賴
                from api.models import Task
                base_queryset = Task.objects.all()
            
            # 複雜的權限過濾邏輯
            user_tasks = base_queryset.filter(
                models.Q(assignee=user) |           # 指派給用戶的任務
                models.Q(creator=user) |            # 用戶創建的任務
                models.Q(project__owner=user) |     # 用戶擁有的專案下的任務
                models.Q(project__members=user)     # 用戶參與的專案下的任務
            ).distinct()
            
            self.logger.info(f"為用戶 {user.username} 過濾任務：{user_tasks.count()} 個")
            return user_tasks
            
        except Exception as e:
            self.logger.error(f"任務查詢失敗: {str(e)}")
            # 返回空的查詢集作為備用
            from api.models import Task
            return Task.objects.none()
    
    def filter_tasks_by_params(self, base_queryset, query_params):
        """
        根據查詢參數過濾任務
        
        Args:
            base_queryset: 基礎查詢集
            query_params: Django request.query_params
            
        Returns:
            QuerySet: 過濾後的查詢集
        """
        try:
            queryset = base_queryset
            
            # 搜尋功能
            search = query_params.get('search', None)
            if search:
                queryset = queryset.filter(
                    models.Q(title__icontains=search) |
                    models.Q(description__icontains=search)
                )
            
            # 狀態過濾
            status = query_params.get('status', None)
            if status:
                queryset = queryset.filter(status=status)
            
            # 優先級過濾
            priority = query_params.get('priority', None)
            if priority:
                queryset = queryset.filter(priority=priority)
            
            # 專案過濾
            project_id = query_params.get('project', None)
            if project_id:
                try:
                    queryset = queryset.filter(project_id=int(project_id))
                except (ValueError, TypeError):
                    self.logger.warning(f"無效的專案ID: {project_id}")
            
            # 指派人過濾
            assignee_id = query_params.get('assignee', None)
            if assignee_id:
                try:
                    if assignee_id.lower() == 'unassigned':
                        queryset = queryset.filter(assignee__isnull=True)
                    else:
                        queryset = queryset.filter(assignee_id=int(assignee_id))
                except (ValueError, TypeError):
                    self.logger.warning(f"無效的指派人ID: {assignee_id}")
            
            # 到期日過濾
            due_date_filter = query_params.get('due_date', None)
            if due_date_filter:
                from django.utils import timezone
                today = timezone.now().date()
                
                if due_date_filter == 'overdue':
                    queryset = queryset.filter(
                        due_date__isnull=False,
                        due_date__lt=today
                    )
                elif due_date_filter == 'today':
                    queryset = queryset.filter(due_date__date=today)
                elif due_date_filter == 'this_week':
                    week_start = today - timezone.timedelta(days=today.weekday())
                    week_end = week_start + timezone.timedelta(days=6)
                    queryset = queryset.filter(
                        due_date__date__gte=week_start,
                        due_date__date__lte=week_end
                    )
            
            # 排序
            ordering = query_params.get('ordering', '-created_at')
            valid_orderings = [
                'created_at', '-created_at',
                'updated_at', '-updated_at',
                'due_date', '-due_date',
                'priority', '-priority',
                'status', '-status',
                'title', '-title'
            ]
            
            if ordering in valid_orderings:
                queryset = queryset.order_by(ordering)
            else:
                queryset = queryset.order_by('-created_at')  # 預設排序
            
            self.logger.info(f"任務過濾完成，結果數量: {queryset.count()}")
            return queryset
            
        except Exception as e:
            self.logger.error(f"任務過濾失敗: {str(e)}")
            return base_queryset.order_by('-created_at')
    
    def get_task_statistics(self, user, base_queryset=None):
        """
        獲取用戶任務統計資料
        
        Args:
            user: Django User 實例
            base_queryset: 基礎查詢集
            
        Returns:
            dict: 統計資料字典
        """
        try:
            if base_queryset is None:
                user_tasks = self.get_user_related_tasks(user)
            else:
                user_tasks = base_queryset
            
            from django.db.models import Count
            
            # 基本統計
            total_tasks = user_tasks.count()
            
            # 按狀態統計
            status_stats = user_tasks.values('status').annotate(count=Count('id'))
            
            # 按優先級統計
            priority_stats = user_tasks.values('priority').annotate(count=Count('id'))
            
            # 按專案統計
            project_stats = user_tasks.values('project__title').annotate(count=Count('id'))
            
            # 我的任務（指派給我的）
            my_assigned_tasks = user_tasks.filter(assignee=user).count()
            
            # 我創建的任務
            my_created_tasks = user_tasks.filter(creator=user).count()
            
            # 逾期任務
            from django.utils import timezone
            overdue_tasks = user_tasks.filter(
                due_date__isnull=False,
                due_date__lt=timezone.now(),
                status__in=['pending', 'in_progress']
            ).count()
            
            statistics = {
                'total_tasks': total_tasks,
                'my_assigned_tasks': my_assigned_tasks,
                'my_created_tasks': my_created_tasks,
                'overdue_tasks': overdue_tasks,
                'status_distribution': list(status_stats),
                'priority_distribution': list(priority_stats),
                'project_distribution': list(project_stats)
            }
            
            self.logger.info(f"用戶 {user.username} 任務統計生成完成")
            return statistics
            
        except Exception as e:
            self.logger.error(f"任務統計生成失敗: {str(e)}")
            return {
                'total_tasks': 0,
                'my_assigned_tasks': 0,
                'my_created_tasks': 0,
                'overdue_tasks': 0,
                'error': str(e)
            }


# 便利函數
def create_task_query_manager():
    """創建任務查詢管理器"""
    try:
        return TaskQueryManager()
    except Exception as e:
        logger.warning(f"無法創建任務查詢管理器: {e}")
        return None


def get_user_related_tasks(user, base_queryset=None):
    """便利函數：獲取用戶相關任務"""
    manager = create_task_query_manager()
    if manager:
        return manager.get_user_related_tasks(user, base_queryset)
    else:
        # 備用實現
        logger.warning("使用備用任務查詢實現")
        try:
            from api.models import Task
            if base_queryset is None:
                base_queryset = Task.objects.all()
            
            return base_queryset.filter(
                models.Q(assignee=user) |
                models.Q(creator=user) |
                models.Q(project__owner=user) |
                models.Q(project__members=user)
            ).distinct()
        except Exception as e:
            logger.error(f"備用任務查詢也失敗: {e}")
            from api.models import Task
            return Task.objects.none()


# 備用查詢函數
def fallback_task_query(user, query_params=None):
    """備用任務查詢實現"""
    try:
        from api.models import Task
        
        # 基本的用戶相關任務查詢
        queryset = Task.objects.filter(
            models.Q(assignee=user) |
            models.Q(creator=user) |
            models.Q(project__owner=user) |
            models.Q(project__members=user)
        ).distinct()
        
        # 簡單的搜尋功能
        if query_params and query_params.get('search'):
            search = query_params.get('search')
            queryset = queryset.filter(
                models.Q(title__icontains=search) |
                models.Q(description__icontains=search)
            )
        
        return queryset.order_by('-created_at')
        
    except Exception as e:
        logger.error(f"備用任務查詢失敗: {e}")
        from api.models import Task
        return Task.objects.none()