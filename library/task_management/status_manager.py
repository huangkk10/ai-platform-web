"""
Task Status Manager - 任務狀態管理器

統一管理任務狀態相關邏輯：
- 狀態驗證
- 狀態變更處理
- 狀態變更歷史
- 狀態變更通知
"""

import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class TaskStatusManager:
    """任務狀態管理器 - 處理任務狀態變更的完整流程"""
    
    # 狀態轉換規則
    VALID_STATUS_TRANSITIONS = {
        'pending': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'pending', 'cancelled'],
        'completed': ['in_progress'],  # 允許重新開始
        'cancelled': ['pending', 'in_progress']  # 允許重新啟動
    }
    
    def __init__(self):
        self.logger = logger
    
    def can_change_status(self, user, task):
        """
        檢查用戶是否有權限變更任務狀態
        
        Args:
            user: 執行狀態變更的用戶
            task: 要變更狀態的任務
            
        Returns:
            tuple: (can_change: bool, reason: str)
        """
        try:
            # 任務指派人可以變更狀態
            if task.assignee == user:
                return True, "Assignee can change status"
            
            # 任務創建者可以變更狀態
            if task.creator == user:
                return True, "Task creator can change status"
            
            # 專案擁有者可以變更狀態
            if task.project.owner == user:
                return True, "Project owner can change status"
            
            # 專案成員可以變更狀態（如果有權限）
            if user in task.project.members.all():
                return True, "Project member can change status"
            
            # 管理員可以變更任何任務狀態
            if user.is_staff or user.is_superuser:
                return True, "Admin can change any task status"
            
            return False, "Insufficient permissions to change task status"
            
        except Exception as e:
            self.logger.error(f"狀態變更權限檢查失敗: {str(e)}")
            return False, f"Permission check failed: {str(e)}"
    
    def validate_status_transition(self, current_status, new_status):
        """
        驗證狀態轉換是否有效
        
        Args:
            current_status: 當前狀態
            new_status: 新狀態
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        try:
            # 檢查新狀態是否存在於選項中
            from api.models import Task
            valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
            
            if new_status not in valid_statuses:
                return False, f"Invalid status: {new_status}"
            
            # 如果狀態相同，不需要變更
            if current_status == new_status:
                return False, "Status is already set to this value"
            
            # 檢查狀態轉換是否允許
            allowed_transitions = self.VALID_STATUS_TRANSITIONS.get(current_status, [])
            if new_status not in allowed_transitions:
                return False, f"Invalid transition from {current_status} to {new_status}"
            
            return True, "Valid status transition"
            
        except Exception as e:
            self.logger.error(f"狀態轉換驗證失敗: {str(e)}")
            return False, f"Status validation failed: {str(e)}"
    
    def change_task_status(self, task, new_status, user, notes=None):
        """
        執行任務狀態變更
        
        Args:
            task: 任務實例
            new_status: 新狀態
            user: 執行狀態變更的用戶
            notes: 狀態變更備註
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 檢查變更權限
            can_change, permission_reason = self.can_change_status(user, task)
            if not can_change:
                return Response({
                    'error': 'Permission denied',
                    'reason': permission_reason
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 驗證狀態轉換
            is_valid_transition, validation_reason = self.validate_status_transition(
                task.status, new_status
            )
            if not is_valid_transition:
                return Response({
                    'error': 'Invalid status transition',
                    'reason': validation_reason,
                    'current_status': task.status,
                    'requested_status': new_status,
                    'allowed_transitions': self.VALID_STATUS_TRANSITIONS.get(task.status, [])
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 記錄原始狀態
            old_status = task.status
            
            # 執行狀態變更
            task.status = new_status
            
            # 處理狀態相關的邏輯
            self._handle_status_specific_logic(task, old_status, new_status)
            
            task.save()
            
            # 記錄狀態變更歷史
            self._record_status_history(
                task=task,
                old_status=old_status,
                new_status=new_status,
                user=user,
                notes=notes
            )
            
            # 發送狀態變更通知
            self._send_status_change_notification(task, old_status, new_status, user)
            
            self.logger.info(
                f"任務 {task.id} 狀態從 {old_status} 變更為 {new_status} "
                f"by {user.username}"
            )
            
            return Response({
                'message': f'Task status changed from {old_status} to {new_status}',
                'task_id': task.id,
                'old_status': old_status,
                'new_status': new_status,
                'changed_by': user.username,
                'changed_at': task.updated_at.isoformat(),
                'status_display': task.get_status_display()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"任務狀態變更失敗: {str(e)}")
            return Response({
                'error': f'Status change failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_status_specific_logic(self, task, old_status, new_status):
        """處理狀態相關的特殊邏輯"""
        try:
            from django.utils import timezone
            
            # 當任務變為進行中時，自動指派給當前用戶（如果沒有指派人）
            if new_status == 'in_progress' and not task.assignee:
                # 可以在這裡實現自動指派邏輯
                pass
            
            # 當任務完成時，記錄完成時間
            if new_status == 'completed':
                # 如果有完成時間字段，可以在這裡設置
                # task.completed_at = timezone.now()
                pass
            
            # 當任務取消時，清除指派人（可選）
            if new_status == 'cancelled':
                # task.assignee = None  # 可選：取消指派
                pass
            
            self.logger.info(f"狀態特殊邏輯處理完成: {old_status} -> {new_status}")
            
        except Exception as e:
            self.logger.warning(f"狀態特殊邏輯處理失敗: {str(e)}")
    
    def _record_status_history(self, task, old_status, new_status, user, notes):
        """記錄狀態變更歷史（可選功能）"""
        try:
            # 這裡可以實現狀態變更歷史記錄功能
            # 例如創建 TaskStatusHistory 模型記錄
            self.logger.info(
                f"狀態變更歷史記錄: 任務 {task.id}, "
                f"從 {old_status} 到 {new_status}, "
                f"執行者: {user.username}, 備註: {notes}"
            )
        except Exception as e:
            self.logger.warning(f"狀態變更歷史記錄失敗: {str(e)}")
    
    def _send_status_change_notification(self, task, old_status, new_status, user):
        """發送狀態變更通知（可選功能）"""
        try:
            # 這裡可以實現通知功能
            # 例如通知任務指派人、創建者等
            recipients = []
            if task.assignee and task.assignee != user:
                recipients.append(task.assignee)
            if task.creator != user:
                recipients.append(task.creator)
            
            self.logger.info(
                f"狀態變更通知: 任務 '{task.title}' 狀態從 {old_status} "
                f"變更為 {new_status} by {user.username}, "
                f"通知對象: {[r.username for r in recipients]}"
            )
        except Exception as e:
            self.logger.warning(f"狀態變更通知發送失敗: {str(e)}")
    
    def get_available_transitions(self, current_status):
        """獲取當前狀態可用的轉換選項"""
        return self.VALID_STATUS_TRANSITIONS.get(current_status, [])
    
    def get_status_history(self, task):
        """獲取任務的狀態變更歷史"""
        try:
            # 這裡可以實現獲取狀態歷史的功能
            # 目前返回基本信息
            return {
                'task_id': task.id,
                'current_status': task.status,
                'status_display': task.get_status_display(),
                'available_transitions': self.get_available_transitions(task.status),
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        except Exception as e:
            self.logger.error(f"獲取狀態歷史失敗: {str(e)}")
            return {'error': str(e)}


# 便利函數
def create_task_status_manager():
    """創建任務狀態管理器"""
    try:
        return TaskStatusManager()
    except Exception as e:
        logger.warning(f"無法創建任務狀態管理器: {e}")
        return None


def handle_status_change(task, new_status, user, notes=None):
    """便利函數：處理任務狀態變更"""
    manager = create_task_status_manager()
    if manager:
        return manager.change_task_status(task, new_status, user, notes)
    else:
        # 備用實現
        return fallback_status_change(task, new_status, user, notes)


# 備用狀態變更函數
def fallback_status_change(task, new_status, user, notes=None):
    """備用任務狀態變更實現"""
    try:
        # 簡化的權限檢查
        if not (user == task.assignee or 
                user == task.creator or 
                user == task.project.owner or 
                user.is_staff):
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 簡化的狀態驗證
        from api.models import Task
        valid_statuses = [choice[0] for choice in Task.STATUS_CHOICES]
        
        if new_status not in valid_statuses:
            return Response({
                'error': f'Invalid status: {new_status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 簡化的狀態變更邏輯
        old_status = task.status
        task.status = new_status
        task.save()
        
        logger.info(f"備用實現：任務 {task.id} 狀態從 {old_status} 變更為 {new_status}")
        
        return Response({
            'message': f'Task status changed from {old_status} to {new_status} (fallback mode)',
            'task_id': task.id,
            'old_status': old_status,
            'new_status': new_status
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"備用狀態變更失敗: {str(e)}")
        return Response({
            'error': f'Status change failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)