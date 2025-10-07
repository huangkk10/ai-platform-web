"""
Task ViewSet Manager - 任務 ViewSet 管理器

統一管理 TaskViewSet 的所有邏輯：
- 整合查詢、指派、狀態管理器
- 提供統一的 API 接口
- 處理備用邏輯
"""

import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class TaskViewSetManager:
    """任務 ViewSet 管理器 - 統一管理所有任務相關操作"""
    
    def __init__(self):
        self.logger = logger
        
        # 初始化各個管理器
        try:
            from .query_manager import create_task_query_manager
            self.query_manager = create_task_query_manager()
        except Exception as e:
            self.logger.warning(f"無法創建查詢管理器: {e}")
            self.query_manager = None
        
        try:
            from .assignment_handler import create_task_assignment_handler
            self.assignment_handler = create_task_assignment_handler()
        except Exception as e:
            self.logger.warning(f"無法創建指派處理器: {e}")
            self.assignment_handler = None
        
        try:
            from .status_manager import create_task_status_manager
            self.status_manager = create_task_status_manager()
        except Exception as e:
            self.logger.warning(f"無法創建狀態管理器: {e}")
            self.status_manager = None
    
    def get_user_tasks(self, user, query_params=None):
        """
        獲取用戶相關的任務
        
        Args:
            user: Django User 實例
            query_params: 查詢參數
            
        Returns:
            QuerySet: 任務查詢集
        """
        try:
            if self.query_manager:
                # 使用查詢管理器
                from api.models import Task
                base_queryset = Task.objects.all()
                user_tasks = self.query_manager.get_user_related_tasks(user, base_queryset)
                
                if query_params:
                    user_tasks = self.query_manager.filter_tasks_by_params(user_tasks, query_params)
                
                return user_tasks
            else:
                # 使用備用實現
                self.logger.warning("查詢管理器不可用，使用備用實現")
                return self._fallback_get_user_tasks(user, query_params)
                
        except Exception as e:
            self.logger.error(f"獲取用戶任務失敗: {str(e)}")
            return self._emergency_get_user_tasks(user)
    
    def handle_task_assignment(self, task, user_id, assigner):
        """
        處理任務指派
        
        Args:
            task: 任務實例
            user_id: 被指派用戶的 ID
            assigner: 執行指派的用戶
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 獲取被指派的用戶
            from django.contrib.auth.models import User
            try:
                assignee = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({
                    'error': 'User not found',
                    'user_id': user_id
                }, status=status.HTTP_404_NOT_FOUND)
            
            if self.assignment_handler:
                # 使用指派處理器
                return self.assignment_handler.assign_task(task, assignee, assigner)
            else:
                # 使用備用實現
                self.logger.warning("指派處理器不可用，使用備用實現")
                return self._fallback_assign_task(task, assignee, assigner)
                
        except Exception as e:
            self.logger.error(f"任務指派處理失敗: {str(e)}")
            return Response({
                'error': f'Task assignment failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def handle_status_change(self, task, new_status, user):
        """
        處理任務狀態變更
        
        Args:
            task: 任務實例
            new_status: 新狀態
            user: 執行狀態變更的用戶
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            if self.status_manager:
                # 使用狀態管理器
                return self.status_manager.change_task_status(task, new_status, user)
            else:
                # 使用備用實現
                self.logger.warning("狀態管理器不可用，使用備用實現")
                return self._fallback_change_status(task, new_status, user)
                
        except Exception as e:
            self.logger.error(f"任務狀態變更處理失敗: {str(e)}")
            return Response({
                'error': f'Status change failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def get_task_statistics(self, user):
        """
        獲取用戶任務統計資料
        
        Args:
            user: Django User 實例
            
        Returns:
            dict: 統計資料
        """
        try:
            if self.query_manager:
                # 使用查詢管理器獲取統計
                return self.query_manager.get_task_statistics(user)
            else:
                # 使用備用統計實現
                return self._fallback_get_statistics(user)
                
        except Exception as e:
            self.logger.error(f"任務統計獲取失敗: {str(e)}")
            return {
                'error': str(e),
                'total_tasks': 0
            }
    
    def get_available_status_transitions(self, task):
        """
        獲取任務可用的狀態轉換
        
        Args:
            task: 任務實例
            
        Returns:
            list: 可用狀態列表
        """
        try:
            if self.status_manager:
                return self.status_manager.get_available_transitions(task.status)
            else:
                # 備用實現：返回所有狀態
                from api.models import Task
                return [choice[0] for choice in Task.STATUS_CHOICES if choice[0] != task.status]
        except Exception as e:
            self.logger.error(f"獲取狀態轉換失敗: {str(e)}")
            return []
    
    def perform_create(self, serializer, user):
        """處理任務創建"""
        try:
            # 設定創建者
            task = serializer.save(creator=user)
            self.logger.info(f"任務創建成功: {task.id} by {user.username}")
            return task
        except Exception as e:
            self.logger.error(f"任務創建失敗: {str(e)}")
            raise
    
    # ===== 備用實現方法 =====
    
    def _fallback_get_user_tasks(self, user, query_params=None):
        """備用的用戶任務獲取實現"""
        try:
            from api.models import Task
            from django.db import models
            
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
            
            # 狀態過濾
            if query_params and query_params.get('status'):
                queryset = queryset.filter(status=query_params.get('status'))
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            self.logger.error(f"備用任務查詢失敗: {str(e)}")
            return self._emergency_get_user_tasks(user)
    
    def _emergency_get_user_tasks(self, user):
        """緊急備用任務查詢實現"""
        try:
            from api.models import Task
            # 只返回用戶創建或被指派的任務
            return Task.objects.filter(
                models.Q(assignee=user) | models.Q(creator=user)
            ).order_by('-created_at')
        except Exception as e:
            self.logger.error(f"緊急備用任務查詢也失敗: {str(e)}")
            from api.models import Task
            return Task.objects.none()
    
    def _fallback_assign_task(self, task, assignee, assigner):
        """備用任務指派實現"""
        try:
            # 簡化的權限檢查
            if not (assigner == task.creator or 
                    assigner == task.project.owner or 
                    assigner.is_staff):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 執行指派
            task.assignee = assignee
            task.save()
            
            return Response({
                'message': f'Task assigned to {assignee.username}',
                'fallback_mode': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"備用任務指派失敗: {str(e)}")
            return Response({
                'error': f'Task assignment failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _fallback_change_status(self, task, new_status, user):
        """備用狀態變更實現"""
        try:
            # 簡化的權限檢查
            if not (user == task.assignee or 
                    user == task.creator or 
                    user == task.project.owner or 
                    user.is_staff):
                return Response({
                    'error': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 驗證狀態
            from api.models import Task
            valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
            
            if new_status not in valid_statuses:
                return Response({
                    'error': f'Invalid status: {new_status}'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            old_status = task.status
            task.status = new_status
            task.save()
            
            return Response({
                'message': f'Task status changed from {old_status} to {new_status}',
                'fallback_mode': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"備用狀態變更失敗: {str(e)}")
            return Response({
                'error': f'Status change failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _fallback_get_statistics(self, user):
        """備用統計實現"""
        try:
            from api.models import Task
            from django.db import models
            
            user_tasks = Task.objects.filter(
                models.Q(assignee=user) |
                models.Q(creator=user) |
                models.Q(project__owner=user) |
                models.Q(project__members=user)
            ).distinct()
            
            return {
                'total_tasks': user_tasks.count(),
                'my_assigned_tasks': user_tasks.filter(assignee=user).count(),
                'my_created_tasks': user_tasks.filter(creator=user).count(),
                'fallback_mode': True
            }
            
        except Exception as e:
            self.logger.error(f"備用統計獲取失敗: {str(e)}")
            return {
                'total_tasks': 0,
                'error': str(e),
                'fallback_mode': True
            }


# 便利函數
def create_task_viewset_manager():
    """創建任務 ViewSet 管理器"""
    try:
        return TaskViewSetManager()
    except Exception as e:
        logger.warning(f"無法創建任務 ViewSet 管理器: {e}")
        return None