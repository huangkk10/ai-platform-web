"""
认证模块 - Authentication Library

提供用户认证、用户资料处理、输入验证和响应格式化等功能。

主要组件：
- AuthenticationService: 用户认证核心服务
- UserProfileService: 用户资料管理服务  
- ValidationService: 输入验证服务
- AuthResponseFormatter: 认证响应格式化器
- LoginHandler: 完整登入流程处理器 (NEW)
"""

from .authentication_service import AuthenticationService
from .user_profile_service import UserProfileService
from .validation_service import ValidationService
from .response_formatter import AuthResponseFormatter
from .login_handler import LoginHandler

__all__ = [
    'AuthenticationService',
    'UserProfileService', 
    'ValidationService',
    'AuthResponseFormatter',
    'LoginHandler'
]