"""
用戶檔案 ViewSet 管理器 - User Profile ViewSet Manager

統一管理 UserProfileViewSet 的複雜邏輯，提供結構化的方法來處理各種操作。

Author: AI Platform Team  
Created: 2024-10-08
"""

import logging
from typing import Dict, Any, Optional
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.request import Request

from .permission_service import (
    PermissionService, 
    UserPermissionManager, 
    UserProfileQueryHelper,
    get_user_profile_queryset
)

logger = logging.getLogger(__name__)


class UserProfileViewSetManager:
    """用戶檔案 ViewSet 管理器"""
    
    def __init__(self):
        """初始化管理器"""
        self.permission_service = PermissionService()
        self.permission_manager = UserPermissionManager()
        self.query_helper = UserProfileQueryHelper()
    
    def get_queryset_for_user(self, user: User):
        """
        根據用戶權限獲取適當的查詢集
        
        Args:
            user: Django User 對象
            
        Returns:
            QuerySet: UserProfile 查詢集
        """
        return get_user_profile_queryset(user)
    
    def get_serializer_class_for_action(self, action: str):
        """
        根據不同的 action 選擇合適的序列化器
        
        Args:
            action: ViewSet 操作名稱
            
        Returns:
            序列化器類
        """
        try:
            # 動態導入避免循環引用
            from api.serializers import UserProfileSerializer, UserPermissionSerializer
            
            if action in ['manage_permissions', 'bulk_update_permissions']:
                return UserPermissionSerializer
            return UserProfileSerializer
            
        except ImportError as e:
            logger.error(f"導入序列化器失敗: {str(e)}")
            # 備用：返回 None，讓 ViewSet 使用默認的序列化器
            return None
    
    def handle_get_my_profile(self, user: User) -> Response:
        """
        處理獲取當前用戶個人檔案的請求
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        return self.query_helper.get_my_profile(user)
    
    def handle_list_user_permissions(self, user: User) -> Response:
        """
        處理獲取所有用戶權限列表的請求
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        return self.permission_manager.list_all_user_permissions(user)
    
    def handle_manage_permissions(self, user: User, target_user_id: int, update_data: Dict) -> Response:
        """
        處理管理指定用戶權限的請求
        
        Args:
            user: 當前用戶
            target_user_id: 目標用戶ID
            update_data: 更新數據
            
        Returns:
            Response: API 響應
        """
        return self.permission_manager.manage_user_permission(user, target_user_id, update_data)
    
    def handle_bulk_update_permissions(self, user: User, request_data: Dict) -> Response:
        """
        處理批量更新用戶權限的請求
        
        Args:
            user: 當前用戶
            request_data: 請求數據
            
        Returns:
            Response: API 響應
        """
        updates = request_data.get('updates', [])
        return self.permission_manager.bulk_update_permissions(user, updates)
    
    def handle_get_my_permissions(self, user: User) -> Response:
        """
        處理獲取當前用戶權限資訊的請求
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        return self.permission_manager.get_my_permissions(user)
    
    def check_action_permissions(self, action: str, user: User) -> bool:
        """
        檢查用戶是否有執行指定操作的權限
        
        Args:
            action: ViewSet 操作名稱
            user: 當前用戶
            
        Returns:
            bool: 是否有權限
        """
        # 需要超級管理員權限的操作
        super_admin_actions = [
            'manage_permissions',
            'bulk_update_permissions', 
            'list_user_permissions'
        ]
        
        if action in super_admin_actions:
            return self.permission_service.is_super_admin(user)
        
        # 其他操作只需要登入
        return user.is_authenticated
    
    def get_permission_classes_for_action(self, action: str) -> list:
        """
        根據操作獲取權限類列表
        
        Args:
            action: ViewSet 操作名稱
            
        Returns:
            list: 權限類列表
        """
        # 所有操作都至少需要登入
        return [permissions.IsAuthenticated]
    
    def validate_request_data(self, action: str, data: Dict) -> Dict:
        """
        驗證請求數據
        
        Args:
            action: ViewSet 操作名稱
            data: 請求數據
            
        Returns:
            Dict: 驗證結果 {'is_valid': bool, 'errors': dict, 'cleaned_data': dict}
        """
        errors = {}
        cleaned_data = data.copy()
        
        if action == 'bulk_update_permissions':
            updates = data.get('updates', [])
            if not updates:
                errors['updates'] = '請提供要更新的用戶權限資料'
            elif not isinstance(updates, list):
                errors['updates'] = '更新資料必須是一個列表'
            else:
                # 驗證每個更新項目
                for i, update in enumerate(updates):
                    if not isinstance(update, dict):
                        errors[f'updates[{i}]'] = '更新項目必須是一個字典'
                    elif 'profile_id' not in update:
                        errors[f'updates[{i}].profile_id'] = '缺少 profile_id'
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': cleaned_data
        }
    
    def log_action(self, action: str, user: User, result: str, **kwargs):
        """
        記錄操作日誌
        
        Args:
            action: 操作名稱
            user: 執行操作的用戶
            result: 操作結果
            **kwargs: 額外的日誌信息
        """
        try:
            log_msg = f"UserProfile操作 - 用戶: {user.username}, 操作: {action}, 結果: {result}"
            if kwargs:
                log_msg += f", 詳情: {kwargs}"
            logger.info(log_msg)
        except Exception as e:
            logger.error(f"記錄操作日誌失敗: {str(e)}")


class UserProfileAPIHandler:
    """用戶檔案 API 處理器"""
    
    @staticmethod
    def handle_get_my_profile_api(user: User) -> Response:
        """
        處理獲取個人檔案 API
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        manager = UserProfileViewSetManager()
        return manager.handle_get_my_profile(user)
    
    @staticmethod
    def handle_list_permissions_api(user: User) -> Response:
        """
        處理列出所有用戶權限 API
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        manager = UserProfileViewSetManager()
        return manager.handle_list_user_permissions(user)
    
    @staticmethod
    def handle_manage_permissions_api(user: User, target_user_id: int, update_data: Dict) -> Response:
        """
        處理管理用戶權限 API
        
        Args:
            user: 當前用戶
            target_user_id: 目標用戶ID
            update_data: 更新數據
            
        Returns:
            Response: API 響應
        """
        manager = UserProfileViewSetManager()
        return manager.handle_manage_permissions(user, target_user_id, update_data)
    
    @staticmethod
    def handle_bulk_permissions_api(user: User, request_data: Dict) -> Response:
        """
        處理批量權限更新 API
        
        Args:
            user: 當前用戶
            request_data: 請求數據
            
        Returns:
            Response: API 響應
        """
        manager = UserProfileViewSetManager()
        return manager.handle_bulk_update_permissions(user, request_data)
    
    @staticmethod
    def handle_my_permissions_api(user: User) -> Response:
        """
        處理獲取我的權限 API
        
        Args:
            user: 當前用戶
            
        Returns:
            Response: API 響應
        """
        manager = UserProfileViewSetManager()
        return manager.handle_get_my_permissions(user)


# 便利函數
def create_user_profile_viewset_manager() -> UserProfileViewSetManager:
    """
    創建用戶檔案 ViewSet 管理器
    
    Returns:
        UserProfileViewSetManager: 管理器實例
    """
    return UserProfileViewSetManager()


def handle_user_profile_action(action: str, user: User, **kwargs) -> Response:
    """
    統一處理用戶檔案相關操作
    
    Args:
        action: 操作名稱
        user: 當前用戶
        **kwargs: 操作參數
        
    Returns:
        Response: API 響應
    """
    try:
        manager = create_user_profile_viewset_manager()
        
        if action == 'get_my_profile':
            return manager.handle_get_my_profile(user)
        elif action == 'list_permissions':
            return manager.handle_list_user_permissions(user)
        elif action == 'manage_permissions':
            target_user_id = kwargs.get('target_user_id')
            update_data = kwargs.get('update_data', {})
            return manager.handle_manage_permissions(user, target_user_id, update_data)
        elif action == 'bulk_permissions':
            request_data = kwargs.get('request_data', {})
            return manager.handle_bulk_update_permissions(user, request_data)
        elif action == 'get_my_permissions':
            return manager.handle_get_my_permissions(user)
        else:
            from rest_framework import status
            return Response(
                {'error': f'不支援的操作: {action}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
    except Exception as e:
        logger.error(f"處理用戶檔案操作失敗 - 操作: {action}, 錯誤: {str(e)}")
        from rest_framework import status
        return Response(
            {'error': f'操作失敗: {str(e)}'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )