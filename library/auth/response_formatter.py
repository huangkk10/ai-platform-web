"""
认证响应格式化器 - Auth Response Formatter

提供统一的认证相关 API 响应格式化功能。

Author: AI Platform Team
Created: 2024-10-02
"""

import logging
from typing import Dict, Any, Optional
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class AuthResponseFormatter:
    """认证响应格式化器类"""
    
    @staticmethod
    def success_response(user: Any = None, message: str = "操作成功", 
                        data: Optional[Dict] = None, 
                        use_drf: bool = True) -> Response:
        """
        格式化成功响应
        
        Args:
            user: 用户对象（可选）
            message: 成功消息
            data: 额外数据
            use_drf: 是否使用 DRF Response（默认 True）
            
        Returns:
            Response: 格式化的响应
        """
        try:
            response_data = {
                'success': True,
                'message': message
            }
            
            # 添加用户信息
            if user:
                # 动态导入避免循环引用
                try:
                    from ..auth.user_profile_service import UserProfileService
                    user_result = UserProfileService.get_user_profile_data(user)
                    if user_result.get('user'):
                        response_data['user'] = user_result['user']
                    else:
                        response_data['user'] = {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email
                        }
                except Exception as e:
                    logger.warning(f"获取用户资料失败，使用基本信息: {str(e)}")
                    response_data['user'] = {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email
                    }
            
            # 添加额外数据
            if data:
                response_data.update(data)
            
            # 选择响应类型
            if use_drf:
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return JsonResponse(response_data, status=200)
                
        except Exception as e:
            logger.error(f"格式化成功响应失败: {str(e)}")
            return AuthResponseFormatter.error_response(
                message="响应格式化失败", 
                status_code=500,
                use_drf=use_drf
            )
    
    @staticmethod
    def error_response(message: str = "操作失败", 
                      error_code: Optional[str] = None,
                      status_code: int = 400,
                      errors: Optional[Dict] = None,
                      use_drf: bool = True) -> Response:
        """
        格式化错误响应
        
        Args:
            message: 错误消息
            error_code: 错误代码
            status_code: HTTP 状态码
            errors: 详细错误信息
            use_drf: 是否使用 DRF Response（默认 True）
            
        Returns:
            Response: 格式化的响应
        """
        try:
            response_data = {
                'success': False,
                'message': message
            }
            
            # 添加错误代码
            if error_code:
                response_data['error_code'] = error_code
            
            # 添加详细错误信息
            if errors:
                response_data['errors'] = errors
            
            # 选择响应类型和状态码
            if use_drf:
                drf_status = getattr(status, f'HTTP_{status_code}_BAD_REQUEST', status.HTTP_400_BAD_REQUEST)
                if status_code == 401:
                    drf_status = status.HTTP_401_UNAUTHORIZED
                elif status_code == 403:
                    drf_status = status.HTTP_403_FORBIDDEN
                elif status_code == 404:
                    drf_status = status.HTTP_404_NOT_FOUND
                elif status_code == 500:
                    drf_status = status.HTTP_500_INTERNAL_SERVER_ERROR
                    
                return Response(response_data, status=drf_status)
            else:
                return JsonResponse(response_data, status=status_code)
                
        except Exception as e:
            logger.error(f"格式化错误响应失败: {str(e)}")
            # 降级到最基本的响应
            basic_response = {
                'success': False,
                'message': '服务器内部错误'
            }
            if use_drf:
                return Response(basic_response, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            else:
                return JsonResponse(basic_response, status=500)
    
    @staticmethod
    def login_success_response(user: Any, message: str = "登录成功",
                              session_info: Optional[Dict] = None,
                              use_drf: bool = True) -> Response:
        """
        格式化登录成功响应
        
        Args:
            user: 用户对象
            message: 成功消息
            session_info: Session 信息
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        try:
            # 准备额外数据
            extra_data = {}
            
            # 添加 Session 信息
            if session_info:
                extra_data['session'] = session_info
            
            # 添加登录时间戳
            from django.utils import timezone
            extra_data['login_timestamp'] = timezone.now().isoformat()
            
            return AuthResponseFormatter.success_response(
                user=user,
                message=message,
                data=extra_data,
                use_drf=use_drf
            )
            
        except Exception as e:
            logger.error(f"格式化登录成功响应失败: {str(e)}")
            return AuthResponseFormatter.error_response(
                message="登录响应格式化失败",
                status_code=500,
                use_drf=use_drf
            )
    
    @staticmethod
    def logout_success_response(message: str = "登出成功", 
                               username: Optional[str] = None,
                               use_drf: bool = True) -> Response:
        """
        格式化登出成功响应
        
        Args:
            message: 成功消息
            username: 用户名
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        try:
            extra_data = {}
            
            if username:
                extra_data['username'] = username
            
            # 添加登出时间戳
            from django.utils import timezone
            extra_data['logout_timestamp'] = timezone.now().isoformat()
            
            return AuthResponseFormatter.success_response(
                message=message,
                data=extra_data,
                use_drf=use_drf
            )
            
        except Exception as e:
            logger.error(f"格式化登出响应失败: {str(e)}")
            return AuthResponseFormatter.error_response(
                message="登出响应格式化失败",
                status_code=500,
                use_drf=use_drf
            )
    
    @staticmethod
    def validation_error_response(validation_errors: Dict,
                                 message: str = "数据验证失败",
                                 use_drf: bool = True) -> Response:
        """
        格式化验证错误响应
        
        Args:
            validation_errors: 验证错误字典
            message: 错误消息
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        return AuthResponseFormatter.error_response(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            errors=validation_errors,
            use_drf=use_drf
        )
    
    @staticmethod
    def unauthorized_response(message: str = "未授权访问",
                            use_drf: bool = True) -> Response:
        """
        格式化未授权响应
        
        Args:
            message: 错误消息
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        return AuthResponseFormatter.error_response(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
            use_drf=use_drf
        )
    
    @staticmethod
    def forbidden_response(message: str = "权限不足",
                          use_drf: bool = True) -> Response:
        """
        格式化权限不足响应
        
        Args:
            message: 错误消息
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        return AuthResponseFormatter.error_response(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            use_drf=use_drf
        )
    
    @staticmethod
    def server_error_response(message: str = "服务器内部错误",
                             error_details: Optional[str] = None,
                             use_drf: bool = True) -> Response:
        """
        格式化服务器错误响应
        
        Args:
            message: 错误消息
            error_details: 错误详情（开发环境可包含）
            use_drf: 是否使用 DRF Response
            
        Returns:
            Response: 格式化的响应
        """
        extra_data = {}
        if error_details:
            extra_data['error_details'] = error_details
            
        return AuthResponseFormatter.error_response(
            message=message,
            error_code="SERVER_ERROR",
            status_code=500,
            errors=extra_data if extra_data else None,
            use_drf=use_drf
        )


# 便利函数
def success(user=None, message="操作成功", **kwargs):
    """便利函数：成功响应"""
    return AuthResponseFormatter.success_response(user=user, message=message, **kwargs)


def error(message="操作失败", status_code=400, **kwargs):
    """便利函数：错误响应"""
    return AuthResponseFormatter.error_response(message=message, status_code=status_code, **kwargs)


def login_success(user, message="登录成功", **kwargs):
    """便利函数：登录成功响应"""
    return AuthResponseFormatter.login_success_response(user=user, message=message, **kwargs)


def logout_success(message="登出成功", **kwargs):
    """便利函数：登出成功响应"""
    return AuthResponseFormatter.logout_success_response(message=message, **kwargs)


def validation_error(errors, message="数据验证失败"):
    """便利函数：验证错误响应"""
    return AuthResponseFormatter.validation_error_response(errors, message)