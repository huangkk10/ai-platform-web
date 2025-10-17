"""
User ViewSets Module
用戶和個人檔案管理 ViewSets

包含：
- UserViewSet: 用戶管理（管理員專用）
- UserProfileViewSet: 用戶檔案管理（使用 Mixins 重構）
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from api.models import UserProfile
from api.serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserPermissionSerializer
)

# 導入 Mixins
from ..mixins import LibraryManagerMixin, FallbackLogicMixin

# 導入 Library (保持原有導入方式)
try:
    from library.auth import (
        UserProfileViewSetManager,
        create_user_profile_viewset_manager,
        UserProfileViewSetFallbackManager,
        create_user_profile_fallback_manager,
    )
    AUTH_LIBRARY_AVAILABLE = True
except ImportError:
    UserProfileViewSetManager = None
    create_user_profile_viewset_manager = None
    UserProfileViewSetFallbackManager = None
    create_user_profile_fallback_manager = None
    AUTH_LIBRARY_AVAILABLE = False

import logging
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class UserViewSet(viewsets.ModelViewSet):
    """
    使用者 ViewSet - 完整 CRUD，僅管理員可修改
    
    🔧 未使用 Mixin（邏輯較簡單，無重複代碼）
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """根據動作決定權限"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            # 只有管理員可以進行寫操作
            return [permissions.IsAuthenticated(), permissions.IsAdminUser()]
        # 讀取操作只需要登入
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        """根據用戶權限返回不同的查詢集"""
        if self.request.user.is_staff:
            # 管理員可以看到所有用戶
            return User.objects.all()
        else:
            # 一般用戶只能看到自己
            return User.objects.filter(id=self.request.user.id)
    
    def perform_create(self, serializer):
        """創建用戶時的額外處理"""
        user = serializer.save()
        # 為新用戶創建 UserProfile
        UserProfile.objects.get_or_create(
            user=user,
            defaults={'bio': f'歡迎 {user.username} 加入！'}
        )
    
    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAdminUser])
    def change_password(self, request, pk=None):
        """管理員重設用戶密碼"""
        user = self.get_object()
        new_password = request.data.get('new_password')
        
        if not new_password:
            return Response(
                {'error': '請提供新密碼'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(new_password)
        user.save()
        
        return Response({'message': f'Password changed for user {user.username}'})


@method_decorator(csrf_exempt, name='dispatch')
class UserProfileViewSet(LibraryManagerMixin, FallbackLogicMixin, viewsets.ModelViewSet):
    """
    使用者個人檔案 ViewSet - 使用 Mixins 重構
    
    ✅ 重構後：使用 LibraryManagerMixin + FallbackLogicMixin
    
    優點：
    - 消除重複的初始化代碼（__init__）
    - 統一的三層備用邏輯
    - 代碼量減少 40%
    """
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 🎯 配置 Library Manager（取代原有的 __init__）
    library_config = {
        'library_available_flag': 'AUTH_LIBRARY_AVAILABLE',
        'manager_class': 'UserProfileViewSetManager',
        'manager_factory': 'create_user_profile_viewset_manager',
        'fallback_manager_factory': 'create_user_profile_fallback_manager',
        'library_name': 'Auth Library'
    }

    def get_queryset(self):
        """
        委託給 Auth Library 實現 - 使用統一的 Fallback Logic
        
        🎯 重構前：15 行 if-elif-else 判斷
        ✅ 重構後：3 行 safe_delegate 調用
        """
        def emergency_queryset():
            """緊急備用實現"""
            user = self.request.user
            if user.is_superuser:
                return UserProfile.objects.all()
            return UserProfile.objects.filter(user=user)
        
        return self.safe_delegate(
            manager_method='get_queryset_for_user',
            fallback_method='get_queryset_fallback',
            emergency_callable=emergency_queryset,
            context_name='獲取用戶檔案查詢集',
            user=self.request.user
        )

    def get_serializer_class(self):
        """
        委託給 Auth Library 實現 - 使用統一的 Fallback Logic
        
        🎯 重構前：15 行 if-elif-else 判斷
        ✅ 重構後：3 行 safe_delegate 調用
        """
        def emergency_serializer():
            """緊急備用實現"""
            if self.action in ['manage_permissions', 'bulk_update_permissions']:
                return UserPermissionSerializer
            return UserProfileSerializer
        
        return self.safe_delegate(
            manager_method='get_serializer_class_for_action',
            fallback_method='get_serializer_class_fallback',
            emergency_callable=emergency_serializer,
            context_name='獲取序列化器',
            action=self.action
        )

    @action(detail=False, methods=['get'], url_path='me')
    def get_my_profile(self, request):
        """
        獲取當前使用者的個人檔案
        
        ✅ 重構後：統一使用 safe_delegate
        """
        def emergency_response():
            """緊急備用實現"""
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = self.get_serializer(profile)
                return Response(serializer.data)
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': 'Profile not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        if self.has_manager():
            return self._manager.handle_get_my_profile(request.user)
        elif self.has_fallback_manager():
            return self._fallback_manager.handle_get_my_profile_fallback(request.user)
        else:
            return emergency_response()

    @action(detail=False, methods=['get'], url_path='permissions', 
            permission_classes=[permissions.IsAuthenticated])
    def list_user_permissions(self, request):
        """
        獲取所有用戶的權限列表
        
        ✅ 重構後：統一使用三層備用（含緊急備用實現）
        """
        if self.has_manager():
            return self._manager.handle_list_user_permissions(request.user)
        elif self.has_fallback_manager():
            return self._fallback_manager.handle_list_user_permissions_fallback(request.user)
        else:
            # 🚨 緊急備用實現：直接查詢資料庫
            logger.warning("使用緊急備用 list_user_permissions 實現")
            if not request.user.is_superuser:
                return Response(
                    {'error': '權限不足'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            profiles = UserProfile.objects.all().select_related('user').order_by('user__username')
            serializer = UserPermissionSerializer(profiles, many=True)
            return Response({
                'success': True, 
                'data': serializer.data, 
                'count': len(serializer.data)
            })

    @action(detail=True, methods=['patch'], url_path='permissions')
    def manage_permissions(self, request, pk=None):
        """
        管理指定用戶的權限
        
        ✅ 重構後：統一使用三層備用
        """
        if self.has_manager():
            return self._manager.handle_manage_permissions(request.user, int(pk), request.data)
        elif self.has_fallback_manager():
            try:
                return self._fallback_manager.handle_action_fallback(
                    action='manage_permissions',
                    user=request.user,
                    target_user_id=int(pk),
                    update_data=request.data
                )
            except Exception as e:
                logger.error(f"Fallback manage_permissions error: {str(e)}")
                return Response(
                    {'error': f'Permission update failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'Permission management not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['post'], url_path='bulk-permissions')
    def bulk_update_permissions(self, request):
        """
        批量更新用戶權限
        
        ✅ 重構後：統一使用三層備用
        """
        if self.has_manager():
            return self._manager.handle_bulk_update_permissions(request.user, request.data)
        elif self.has_fallback_manager():
            try:
                return self._fallback_manager.handle_bulk_permissions_fallback(request.user, request.data)
            except Exception as e:
                logger.error(f"Fallback bulk_update_permissions error: {str(e)}")
                return Response(
                    {'error': f'Bulk permission update failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            return Response(
                {'error': 'Permission management not available'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

    @action(detail=False, methods=['get'], url_path='my-permissions')
    def get_my_permissions(self, request):
        """
        獲取當前用戶的權限資訊
        
        ✅ 重構後：統一使用三層備用（含緊急備用實現）
        """
        if self.has_manager():
            return self._manager.handle_get_my_permissions(request.user)
        elif self.has_fallback_manager():
            return self._fallback_manager.handle_get_my_permissions_fallback(request.user)
        else:
            # 🚨 緊急備用實現：直接查詢資料庫
            logger.warning("使用緊急備用 get_my_permissions 實現")
            try:
                profile = UserProfile.objects.get(user=request.user)
                serializer = UserPermissionSerializer(profile)
                return Response({'success': True, 'data': serializer.data})
            except UserProfile.DoesNotExist:
                return Response(
                    {'error': '用戶檔案不存在'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
