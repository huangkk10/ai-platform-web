"""
Task Assignment Handler - 任務指派處理器

統一管理任務指派相關邏輯：
- 指派權限驗證
- 指派操作處理
- 指派歷史記錄
- 通知機制
"""

import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class TaskAssignmentHandler:
    """任務指派處理器 - 處理任務指派的完整流程"""
    
    def __init__(self):
        self.logger = logger
    
    def can_assign_task(self, user, task):
        """
        檢查用戶是否有權限指派任務
        
        Args:
            user: 執行指派的用戶
            task: 要指派的任務
            
        Returns:
            tuple: (can_assign: bool, reason: str)
        """
        try:
            # 任務創建者可以指派
            if task.creator == user:
                return True, "Task creator can assign"
            
            # 專案擁有者可以指派
            if task.project.owner == user:
                return True, "Project owner can assign"
            
            # 專案成員可以指派（如果有權限）
            if user in task.project.members.all():
                return True, "Project member can assign"
            
            # 管理員可以指派任何任務
            if user.is_staff or user.is_superuser:
                return True, "Admin can assign any task"
            
            return False, "Insufficient permissions to assign this task"
            
        except Exception as e:
            self.logger.error(f"權限檢查失敗: {str(e)}")
            return False, f"Permission check failed: {str(e)}"
    
    def validate_assignee(self, assignee, task):
        """
        驗證被指派人是否有效
        
        Args:
            assignee: 被指派的用戶
            task: 任務實例
            
        Returns:
            tuple: (is_valid: bool, reason: str)
        """
        try:
            # 檢查用戶是否存在且活躍
            if not assignee.is_active:
                return False, "Assignee is not an active user"
            
            # 檢查用戶是否是專案成員或擁有者
            if (assignee == task.project.owner or 
                assignee in task.project.members.all()):
                return True, "Assignee is project member"
            
            # 管理員可以被指派任何任務
            if assignee.is_staff or assignee.is_superuser:
                return True, "Assignee is admin"
            
            return False, "Assignee is not a member of this project"
            
        except Exception as e:
            self.logger.error(f"被指派人驗證失敗: {str(e)}")
            return False, f"Assignee validation failed: {str(e)}"
    
    def assign_task(self, task, assignee, assigner, notes=None):
        """
        執行任務指派
        
        Args:
            task: 任務實例
            assignee: 被指派的用戶
            assigner: 執行指派的用戶
            notes: 指派備註
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 檢查指派權限
            can_assign, permission_reason = self.can_assign_task(assigner, task)
            if not can_assign:
                return Response({
                    'error': 'Permission denied',
                    'reason': permission_reason
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 驗證被指派人
            is_valid_assignee, validation_reason = self.validate_assignee(assignee, task)
            if not is_valid_assignee:
                return Response({
                    'error': 'Invalid assignee',
                    'reason': validation_reason
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 記錄原始指派人（用於歷史記錄）
            original_assignee = task.assignee
            
            # 執行指派
            task.assignee = assignee
            task.save()
            
            # 記錄指派歷史
            self._record_assignment_history(
                task=task,
                old_assignee=original_assignee,
                new_assignee=assignee,
                assigner=assigner,
                notes=notes
            )
            
            # 發送通知（如果需要）
            self._send_assignment_notification(task, assignee, assigner)
            
            self.logger.info(
                f"任務 {task.id} 成功指派給 {assignee.username} "
                f"by {assigner.username}"
            )
            
            return Response({
                'message': f'Task successfully assigned to {assignee.username}',
                'task_id': task.id,
                'assignee': {
                    'id': assignee.id,
                    'username': assignee.username,
                    'email': assignee.email
                },
                'assigned_by': assigner.username,
                'assigned_at': task.updated_at.isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"任務指派失敗: {str(e)}")
            return Response({
                'error': f'Task assignment failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def unassign_task(self, task, unassigner, notes=None):
        """
        取消任務指派
        
        Args:
            task: 任務實例
            unassigner: 執行取消指派的用戶
            notes: 取消指派備註
            
        Returns:
            Response: DRF Response 對象
        """
        try:
            # 檢查取消指派權限
            can_assign, permission_reason = self.can_assign_task(unassigner, task)
            if not can_assign:
                return Response({
                    'error': 'Permission denied',
                    'reason': permission_reason
                }, status=status.HTTP_403_FORBIDDEN)
            
            # 檢查是否有指派人
            if not task.assignee:
                return Response({
                    'error': 'Task is not assigned to anyone'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 記錄原始指派人
            original_assignee = task.assignee
            
            # 取消指派
            task.assignee = None
            task.save()
            
            # 記錄指派歷史
            self._record_assignment_history(
                task=task,
                old_assignee=original_assignee,
                new_assignee=None,
                assigner=unassigner,
                notes=notes or "Task unassigned"
            )
            
            self.logger.info(
                f"任務 {task.id} 取消指派 "
                f"(原指派人: {original_assignee.username}) "
                f"by {unassigner.username}"
            )
            
            return Response({
                'message': 'Task assignment removed successfully',
                'task_id': task.id,
                'previous_assignee': original_assignee.username,
                'unassigned_by': unassigner.username,
                'unassigned_at': task.updated_at.isoformat()
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            self.logger.error(f"取消任務指派失敗: {str(e)}")
            return Response({
                'error': f'Task unassignment failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _record_assignment_history(self, task, old_assignee, new_assignee, assigner, notes):
        """記錄指派歷史（可選功能）"""
        try:
            # 這裡可以實現指派歷史記錄功能
            # 例如創建 TaskAssignmentHistory 模型記錄
            self.logger.info(
                f"指派歷史記錄: 任務 {task.id}, "
                f"從 {old_assignee.username if old_assignee else 'None'} "
                f"到 {new_assignee.username if new_assignee else 'None'}, "
                f"執行者: {assigner.username}, 備註: {notes}"
            )
        except Exception as e:
            self.logger.warning(f"指派歷史記錄失敗: {str(e)}")
    
    def _send_assignment_notification(self, task, assignee, assigner):
        """發送指派通知（可選功能）"""
        try:
            # 這裡可以實現通知功能
            # 例如發送郵件或系統內通知
            self.logger.info(
                f"通知發送: 任務 '{task.title}' 已指派給 {assignee.username} "
                f"by {assigner.username}"
            )
        except Exception as e:
            self.logger.warning(f"指派通知發送失敗: {str(e)}")
    
    def get_assignment_history(self, task):
        """獲取任務的指派歷史"""
        try:
            # 這裡可以實現獲取指派歷史的功能
            # 目前返回基本信息
            return {
                'task_id': task.id,
                'current_assignee': {
                    'id': task.assignee.id,
                    'username': task.assignee.username
                } if task.assignee else None,
                'created_by': {
                    'id': task.creator.id,
                    'username': task.creator.username
                },
                'created_at': task.created_at.isoformat(),
                'updated_at': task.updated_at.isoformat()
            }
        except Exception as e:
            self.logger.error(f"獲取指派歷史失敗: {str(e)}")
            return {'error': str(e)}


# 便利函數
def create_task_assignment_handler():
    """創建任務指派處理器"""
    try:
        return TaskAssignmentHandler()
    except Exception as e:
        logger.warning(f"無法創建任務指派處理器: {e}")
        return None


def handle_task_assignment(task, assignee, assigner, notes=None):
    """便利函數：處理任務指派"""
    handler = create_task_assignment_handler()
    if handler:
        return handler.assign_task(task, assignee, assigner, notes)
    else:
        # 備用實現
        return fallback_task_assignment(task, assignee, assigner, notes)


# 備用指派函數
def fallback_task_assignment(task, assignee, assigner, notes=None):
    """備用任務指派實現"""
    try:
        # 簡化的權限檢查
        if not (assigner == task.creator or 
                assigner == task.project.owner or 
                assigner.is_staff):
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # 簡化的指派邏輯
        task.assignee = assignee
        task.save()
        
        logger.info(f"備用實現：任務 {task.id} 指派給 {assignee.username}")
        
        return Response({
            'message': f'Task assigned to {assignee.username} (fallback mode)',
            'task_id': task.id,
            'assignee': assignee.username
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"備用任務指派失敗: {str(e)}")
        return Response({
            'error': f'Task assignment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)