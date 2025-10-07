"""
认证模块 - Authentication Library

提供用户认证、用户资料处理、权限管理、输入验证和响应格式化等功能。

主要组件：
- AuthenticationService: 用户认证核心服务
- UserProfileService: 用户资料管理服务  
- PermissionService: 权限检查和管理服务
- UserPermissionManager: 用户权限管理器
- UserProfileViewSetManager: 用户档案 ViewSet 管理器
- UserProfileAPIHandler: 用户档案 API 处理器
- UserProfileFallbackHandler: 备用处理器 (NEW)
- UserProfileViewSetFallbackManager: ViewSet 备用管理器 (NEW)
- ValidationService: 输入验证服务
- AuthResponseFormatter: 认证响应格式化器
- LoginHandler: 完整登入流程处理器
- DRFAuthHandler: Django REST Framework API 处理器
"""

from .authentication_service import AuthenticationService
from .user_profile_service import UserProfileService
from .permission_service import (
    PermissionService, 
    UserPermissionManager, 
    UserProfileQueryHelper,
    check_super_admin,
    get_user_profile_queryset,
    manage_user_permissions,
    bulk_update_user_permissions
)
from .user_profile_viewset_manager import (
    UserProfileViewSetManager,
    UserProfileAPIHandler,
    create_user_profile_viewset_manager,
    handle_user_profile_action
)
# 🆕 導入備用處理器
from .fallback_handlers import (
    UserProfileFallbackHandler,
    UserProfileViewSetFallbackManager,
    create_user_profile_fallback_manager,
    handle_user_profile_fallback,
    get_user_profile_queryset_fallback,
    get_user_profile_serializer_fallback
)
from .validation_service import ValidationService
from .response_formatter import AuthResponseFormatter
from .login_handler import LoginHandler
from .api_handlers import DRFAuthHandler

__all__ = [
    'AuthenticationService',
    'UserProfileService',
    'PermissionService',
    'UserPermissionManager', 
    'UserProfileQueryHelper',
    'UserProfileViewSetManager',
    'UserProfileAPIHandler',
    # 🆕 備用處理器
    'UserProfileFallbackHandler',
    'UserProfileViewSetFallbackManager',
    'ValidationService',
    'AuthResponseFormatter',
    'LoginHandler',
    'DRFAuthHandler',
    # 便利函数
    'check_super_admin',
    'get_user_profile_queryset',
    'manage_user_permissions',
    'bulk_update_user_permissions',
    'create_user_profile_viewset_manager',
    'handle_user_profile_action',
    # 🆕 備用處理器便利函數
    'create_user_profile_fallback_manager',
    'handle_user_profile_fallback',
    'get_user_profile_queryset_fallback',
    'get_user_profile_serializer_fallback'
]