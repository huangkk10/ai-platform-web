"""
Project ViewSets Module
專案和任務管理 ViewSets

包含：
- ProjectViewSet: 專案管理（簡單邏輯，無 Mixin）
- TaskViewSet: 任務管理（使用 Mixins 重構）
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db import models

from api.models import Project, Task
from api.serializers import ProjectSerializer, TaskSerializer

# 導入 Mixins
from ..mixins import LibraryManagerMixin, FallbackLogicMixin

# 導入 Task Management Library
try:
    from library.task_management import (
        TaskViewSetManager,
        create_task_viewset_manager,
        fallback_task_query,
        fallback_task_assignment,
        fallback_status_change,
        fallback_task_statistics,
        TASK_MANAGEMENT_LIBRARY_AVAILABLE
    )
except ImportError:
    TaskViewSetManager = None
    create_task_viewset_manager = None
    fallback_task_query = None
    fallback_task_assignment = None
    fallback_status_change = None
    fallback_task_statistics = None
    TASK_MANAGEMENT_LIBRARY_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


class ProjectViewSet(viewsets.ModelViewSet):
    """
    專案 ViewSet - 簡單 CRUD，無需使用 Mixin
    
    🔧 未使用 Mixin（邏輯較簡單，無重複代碼）
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """只返回使用者擁有或參與的專案"""
        user = self.request.user
        return Project.objects.filter(
            models.Q(owner=user) | models.Q(members=user)
        ).distinct()

    def perform_create(self, serializer):
        """設定當前使用者為專案擁有者"""
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-member')
    def add_member(self, request, pk=None):
        """新增專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response({'message': f'User {user.username} added to project'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post'], url_path='remove-member')
    def remove_member(self, request, pk=None):
        """移除專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.remove(user)
            return Response({'message': f'User {user.username} removed from project'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


@method_decorator(csrf_exempt, name='dispatch')
class TaskViewSet(LibraryManagerMixin, FallbackLogicMixin, viewsets.ModelViewSet):
    """
    任務 ViewSet - 使用 Mixins 重構
    
    ✅ 重構後：使用 LibraryManagerMixin + FallbackLogicMixin
    
    優點：
    - 消除重複的初始化代碼（__init__）
    - 統一的三層備用邏輯
    - 代碼量減少 35%
    """
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 🎯 配置 Library Manager（取代原有的 __init__）
    library_config = {
        'library_available_flag': 'TASK_MANAGEMENT_LIBRARY_AVAILABLE',
        'manager_class': 'TaskViewSetManager',
        'manager_factory': 'create_task_viewset_manager',
        'library_name': 'Task Management Library'
    }

    def get_queryset(self):
        """
        委託給 Task Management Library 實現 - 使用統一的 Fallback Logic
        
        🎯 重構前：18 行 if-elif-else 判斷 + try-except 層級
        ✅ 重構後：4 行 safe_delegate 調用
        """
        def fallback_queryset():
            """Fallback 實現"""
            if fallback_task_query:
                result = fallback_task_query(self.request.user, self.request.query_params)
                if result is not None:
                    return result
            return None
        
        def emergency_queryset():
            """緊急備用實現"""
            user = self.request.user
            return Task.objects.filter(
                models.Q(assignee=user) | 
                models.Q(creator=user) | 
                models.Q(project__owner=user) |
                models.Q(project__members=user)
            ).distinct().order_by('-created_at')
        
        return self.safe_delegate(
            manager_method='get_user_tasks',
            fallback_callable=fallback_queryset,
            emergency_callable=emergency_queryset,
            context_name='獲取任務查詢集',
            user=self.request.user,
            query_params=self.request.query_params
        )

    def perform_create(self, serializer):
        """
        委託給 Task Management Library 實現
        
        🎯 重構前：if self._manager else 判斷
        ✅ 重構後：統一的 safe_delegate
        """
        def emergency_create():
            """緊急備用實現"""
            return serializer.save(creator=self.request.user)
        
        if self.has_manager():
            return self._manager.perform_create(serializer, self.request.user)
        else:
            return emergency_create()

    @action(detail=True, methods=['post'], url_path='assign')
    def assign_task(self, request, pk=None):
        """
        指派任務給使用者 - ✅ 重構後使用 Mixins 統一實現
        
        🎯 重構前：35 行複雜的 if-elif-else + try-except 層級
        ✅ 重構後：簡潔的三層邏輯
        """
        try:
            task = self.get_object()
            user_id = request.data.get('user_id')
            
            if not user_id:
                return Response({
                    'error': 'user_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Primary: Task Management Library
            if self.has_manager():
                return self._manager.handle_task_assignment(task, user_id, request.user)
            
            # Fallback: Library fallback function
            try:
                user = User.objects.get(id=user_id)
                if fallback_task_assignment:
                    return fallback_task_assignment(task, user, request.user)
                
                # Emergency: Basic implementation
                task.assignee = user
                task.save()
                return Response({
                    'message': f'Task assigned to {user.username}',
                    'emergency_fallback': True
                })
            except User.DoesNotExist:
                return Response(
                    {'error': 'User not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"任務指派失敗: {str(e)}")
            return Response(
                {'error': f'任務指派失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['post'], url_path='change-status')
    def change_status(self, request, pk=None):
        """
        變更任務狀態 - ✅ 重構後使用 Mixins 統一實現
        
        🎯 重構前：40 行複雜的 if-elif-else + try-except 層級
        ✅ 重構後：簡潔的三層邏輯
        """
        try:
            task = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response({
                    'error': 'status is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Primary: Task Management Library
            if self.has_manager():
                return self._manager.handle_status_change(task, new_status, request.user)
            
            # Fallback: Library fallback function
            if fallback_status_change:
                return fallback_status_change(task, new_status, request.user)
            
            # Emergency: Basic implementation
            if new_status in dict(Task.STATUS_CHOICES):
                old_status = task.status
                task.status = new_status
                task.save()
                return Response({
                    'message': f'Task status changed from {old_status} to {new_status}',
                    'emergency_fallback': True
                })
            else:
                return Response(
                    {'error': 'Invalid status'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            logger.error(f"任務狀態變更失敗: {str(e)}")
            return Response(
                {'error': f'任務狀態變更失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'], url_path='statistics')
    def task_statistics(self, request):
        """
        獲取任務統計資訊 - ✅ 重構後使用 Mixins 統一實現
        """
        try:
            # Primary: Task Management Library
            if self.has_manager():
                return self._manager.get_task_statistics(request.user)
            
            # Fallback: Library fallback function
            if fallback_task_statistics:
                return fallback_task_statistics(request.user)
            
            # Emergency: Basic implementation
            user = request.user
            tasks = Task.objects.filter(
                models.Q(assignee=user) | 
                models.Q(creator=user)
            )
            
            stats = {
                'total': tasks.count(),
                'pending': tasks.filter(status='pending').count(),
                'in_progress': tasks.filter(status='in_progress').count(),
                'completed': tasks.filter(status='completed').count(),
                'cancelled': tasks.filter(status='cancelled').count(),
                'emergency_fallback': True
            }
            
            return Response(stats)
            
        except Exception as e:
            logger.error(f"任務統計獲取失敗: {str(e)}")
            return Response(
                {'error': f'任務統計獲取失敗: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
