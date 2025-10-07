"""
Task Management Fallback Handlers - 任務管理備用處理器

當主要的任務管理組件不可用時，提供基本的備用功能實現。
這些備用實現確保系統在組件故障時仍能提供基本服務。
"""

import logging
from rest_framework.response import Response
from rest_framework import status
from django.db import models

logger = logging.getLogger(__name__)


class TaskFallbackHandler:
    """任務管理備用處理器 - 提供基本的降級服務"""
    
    @staticmethod
    def fallback_get_user_tasks(user, query_params=None):
        """
        備用實現：獲取用戶相關任務
        
        當主要的 TaskQueryManager 不可用時使用此備用實現
        """
        try:
            logger.warning("使用任務查詢備用實現")
            
            # 動態導入避免循環依賴
            try:
                from api.models import Task
            except ImportError:
                logger.error("無法導入 Task 模型")
                return None
            
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
            
            # 狀態過濾
            if query_params and query_params.get('status'):
                queryset = queryset.filter(status=query_params.get('status'))
            
            return queryset.order_by('-created_at')
            
        except Exception as e:
            logger.error(f"任務查詢備用實現失敗: {str(e)}")
            return None
    
    @staticmethod
    def fallback_assign_task(task, assignee, assigner, notes=None):
        """
        備用實現：任務指派
        
        當主要的 TaskAssignmentHandler 不可用時使用此備用實現
        """
        try:
            logger.warning("使用任務指派備用實現")
            
            # 簡化的權限檢查
            if not (assigner == task.creator or 
                    assigner == task.project.owner or 
                    assigner.is_staff or
                    assigner.is_superuser):
                return Response({
                    'error': 'Permission denied',
                    'fallback': True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 檢查被指派人是否存在
            if not assignee.is_active:
                return Response({
                    'error': 'Assignee is not active',
                    'fallback': True
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 執行指派
            task.assignee = assignee
            task.save()
            
            logger.info(f"備用實現：任務 {task.id} 指派給 {assignee.username}")
            
            return Response({
                'message': f'Task assigned to {assignee.username}',
                'task_id': task.id,
                'assignee': assignee.username,
                'assigned_by': assigner.username,
                'fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"任務指派備用實現失敗: {str(e)}")
            return Response({
                'error': f'Task assignment failed: {str(e)}',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def fallback_change_status(task, new_status, user, notes=None):
        """
        備用實現：任務狀態變更
        
        當主要的 TaskStatusManager 不可用時使用此備用實現
        """
        try:
            logger.warning("使用任務狀態變更備用實現")
            
            # 簡化的權限檢查
            if not (user == task.assignee or 
                    user == task.creator or 
                    user == task.project.owner or 
                    user.is_staff or
                    user.is_superuser or
                    user in task.project.members.all()):
                return Response({
                    'error': 'Permission denied',
                    'fallback': True
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 驗證新狀態
            try:
                from api.models import Task
                valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
                
                if new_status not in valid_statuses:
                    return Response({
                        'error': f'Invalid status: {new_status}',
                        'valid_statuses': valid_statuses,
                        'fallback': True
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except ImportError:
                logger.error("無法導入 Task 模型進行狀態驗證")
                return Response({
                    'error': 'Status validation failed',
                    'fallback': True
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # 執行狀態變更
            old_status = task.status
            task.status = new_status
            task.save()
            
            logger.info(f"備用實現：任務 {task.id} 狀態從 {old_status} 變更為 {new_status}")
            
            return Response({
                'message': f'Task status changed from {old_status} to {new_status}',
                'task_id': task.id,
                'old_status': old_status,
                'new_status': new_status,
                'changed_by': user.username,
                'fallback': True
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"任務狀態變更備用實現失敗: {str(e)}")
            return Response({
                'error': f'Status change failed: {str(e)}',
                'fallback': True
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @staticmethod
    def fallback_get_statistics(user):
        """
        備用實現：獲取任務統計
        
        當主要的統計功能不可用時使用此備用實現
        """
        try:
            logger.warning("使用任務統計備用實現")
            
            try:
                from api.models import Task
            except ImportError:
                logger.error("無法導入 Task 模型")
                return {
                    'error': 'Task model not available',
                    'total_tasks': 0,
                    'fallback': True
                }
            
            # 基本統計查詢
            user_tasks = Task.objects.filter(
                models.Q(assignee=user) |
                models.Q(creator=user) |
                models.Q(project__owner=user) |
                models.Q(project__members=user)
            ).distinct()
            
            statistics = {
                'total_tasks': user_tasks.count(),
                'my_assigned_tasks': user_tasks.filter(assignee=user).count(),
                'my_created_tasks': user_tasks.filter(creator=user).count(),
                'pending_tasks': user_tasks.filter(status='pending').count(),
                'in_progress_tasks': user_tasks.filter(status='in_progress').count(),
                'completed_tasks': user_tasks.filter(status='completed').count(),
                'fallback': True
            }
            
            logger.info(f"備用實現：用戶 {user.username} 任務統計生成完成")
            return statistics
            
        except Exception as e:
            logger.error(f"任務統計備用實現失敗: {str(e)}")
            return {
                'error': str(e),
                'total_tasks': 0,
                'fallback': True
            }


# 便利函數 - 直接使用備用實現
def fallback_task_query(user, query_params=None):
    """便利函數：備用任務查詢"""
    return TaskFallbackHandler.fallback_get_user_tasks(user, query_params)


def fallback_task_assignment(task, assignee, assigner, notes=None):
    """便利函數：備用任務指派"""
    return TaskFallbackHandler.fallback_assign_task(task, assignee, assigner, notes)


def fallback_status_change(task, new_status, user, notes=None):
    """便利函數：備用狀態變更"""
    return TaskFallbackHandler.fallback_change_status(task, new_status, user, notes)


def fallback_task_statistics(user):
    """便利函數：備用任務統計"""
    return TaskFallbackHandler.fallback_get_statistics(user)


# 緊急最終備用實現
def emergency_task_query(user):
    """緊急備用：最基本的任務查詢"""
    try:
        from api.models import Task
        # 只查詢用戶創建或被指派的任務
        return Task.objects.filter(
            models.Q(assignee=user) | models.Q(creator=user)
        ).order_by('-created_at')
    except Exception as e:
        logger.error(f"緊急任務查詢失敗: {str(e)}")
        try:
            from api.models import Task
            return Task.objects.none()
        except:
            return None


def emergency_task_assignment(task, assignee):
    """緊急備用：最基本的任務指派"""
    try:
        task.assignee = assignee
        task.save()
        return True
    except Exception as e:
        logger.error(f"緊急任務指派失敗: {str(e)}")
        return False


def emergency_status_change(task, new_status):
    """緊急備用：最基本的狀態變更"""
    try:
        task.status = new_status
        task.save()
        return True
    except Exception as e:
        logger.error(f"緊急狀態變更失敗: {str(e)}")
        return False