"""
认证服务 - Authentication Service

提供用户认证的核心功能，包括用户登录验证、Session 管理等。

Author: AI Platform Team
Created: 2024-10-02
"""

import logging
from typing import Dict, Tuple, Optional, Union
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.http import HttpRequest
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuthenticationService:
    """用户认证服务类"""
    
    @staticmethod
    def authenticate_user(username: str, password: str, request: HttpRequest = None) -> Dict:
        """
        认证用户
        
        Args:
            username: 用户名
            password: 密码
            request: Django request 对象（可选）
            
        Returns:
            dict: 认证结果
            {
                'success': bool,
                'user': User object or None,
                'message': str,
                'error_code': str or None
            }
        """
        try:
            # 基本参数验证
            if not username or not password:
                return {
                    'success': False,
                    'user': None,
                    'message': '用户名和密码不能为空',
                    'error_code': 'EMPTY_CREDENTIALS'
                }
            
            # Django 认证
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                # 🆕 檢查帳號審核狀態
                try:
                    from api.models import UserProfile
                    profile = user.userprofile
                    
                    if profile.account_status == 'pending':
                        logger.warning(f"嘗試登入待審核帳號: {username}")
                        return {
                            'success': False,
                            'user': None,
                            'message': '您的帳號尚未通過審核，請耐心等待管理員審核通知',
                            'error_code': 'ACCOUNT_PENDING',
                            'account_status': 'pending'
                        }
                    
                    elif profile.account_status == 'rejected':
                        rejection_reason = profile.rejection_reason or '未提供原因'
                        logger.warning(f"嘗試登入已拒絕帳號: {username}")
                        return {
                            'success': False,
                            'user': None,
                            'message': f'您的帳號申請已被拒絕。原因：{rejection_reason}',
                            'error_code': 'ACCOUNT_REJECTED',
                            'account_status': 'rejected',
                            'rejection_reason': rejection_reason
                        }
                    
                    elif profile.account_status == 'suspended':
                        logger.warning(f"嘗試登入已停用帳號: {username}")
                        return {
                            'success': False,
                            'user': None,
                            'message': '您的帳號已被停用，請聯絡系統管理員',
                            'error_code': 'ACCOUNT_SUSPENDED',
                            'account_status': 'suspended'
                        }
                
                except UserProfile.DoesNotExist:
                    # 向後相容：舊用戶沒有 profile，自動創建並設為已批准
                    profile = UserProfile.objects.create(
                        user=user,
                        account_status='approved'
                    )
                    logger.info(f"為現有用戶 {username} 自動創建 UserProfile")
                
                # 檢查用戶是否啟用
                if user.is_active:
                    # SuperUser 豁免審核檢查
                    if user.is_superuser and profile.account_status != 'approved':
                        profile.account_status = 'approved'
                        profile.save()
                    
                    # 用户存在且激活
                    if request:
                        login(request, user)
                        logger.info(f"用户登录成功: {username}")
                    
                    return {
                        'success': True,
                        'user': user,
                        'message': '认证成功',
                        'error_code': None
                    }
                else:
                    # 用户存在但被停用
                    logger.warning(f"尝试登录被停用账号: {username}")
                    return {
                        'success': False,
                        'user': None,
                        'message': '该账号已被停用',
                        'error_code': 'USER_INACTIVE'
                    }
            else:
                # 认证失败
                logger.warning(f"认证失败: {username}")
                return {
                    'success': False,
                    'user': None,
                    'message': '用户名或密码错误',
                    'error_code': 'INVALID_CREDENTIALS'
                }
                
        except Exception as e:
            logger.error(f"认证过程发生错误 - 用户: {username}, 错误: {str(e)}")
            return {
                'success': False,
                'user': None,
                'message': '认证过程发生错误',
                'error_code': 'AUTH_ERROR'
            }
    
    @staticmethod
    def logout_user(request: HttpRequest, force_clear_all_sessions: bool = True) -> Dict:
        """
        用户登出
        
        Args:
            request: Django request 对象
            force_clear_all_sessions: 是否强制清除该用户的所有 session
            
        Returns:
            dict: 登出结果
        """
        try:
            username = None
            
            # 获取用户名（如果已认证）
            if hasattr(request, 'user') and request.user.is_authenticated:
                username = request.user.username
            
            # 强制清除 session
            if hasattr(request, 'session'):
                request.session.flush()  # 完全清除 session
            
            # Django logout
            logout(request)
            
            # 清除该用户的所有 session（可选）
            if force_clear_all_sessions and username:
                try:
                    # 清除该用户的所有 session
                    user_sessions = Session.objects.filter(
                        session_data__contains=username
                    )
                    deleted_count = user_sessions.count()
                    user_sessions.delete()
                    logger.info(f"已清除用户 {username} 的 {deleted_count} 个 session")
                except Exception as session_error:
                    logger.warning(f"清除用户 session 时出错: {str(session_error)}")
            
            message = f'用户 {username or "用户"} 已成功登出'
            if force_clear_all_sessions:
                message += '并清除所有 session'
                
            logger.info(f"用户登出成功: {username}")
            
            return {
                'success': True,
                'message': message,
                'username': username
            }
            
        except Exception as e:
            logger.error(f"登出过程发生错误: {str(e)}")
            
            # 即使出错也要尝试清除 session
            try:
                if hasattr(request, 'session'):
                    request.session.flush()
                logout(request)
            except:
                pass
            
            return {
                'success': True,  # 即使出错也返回成功，确保前端状态正确
                'message': '已强制清除登录状态',
                'username': username
            }
    
    @staticmethod
    def check_user_permissions(user: User, required_permissions: list = None) -> Dict:
        """
        检查用户权限
        
        Args:
            user: Django User 对象
            required_permissions: 需要的权限列表
            
        Returns:
            dict: 权限检查结果
        """
        try:
            if not user or not user.is_authenticated:
                return {
                    'has_permission': False,
                    'message': '用户未认证',
                    'missing_permissions': required_permissions or []
                }
            
            if not required_permissions:
                # 如果没有指定权限要求，只需要认证即可
                return {
                    'has_permission': True,
                    'message': '用户已认证',
                    'missing_permissions': []
                }
            
            # 检查用户是否是超级管理员或职员
            if user.is_superuser or user.is_staff:
                return {
                    'has_permission': True,
                    'message': '管理员权限',
                    'missing_permissions': []
                }
            
            # 检查具体权限
            missing_permissions = []
            for permission in required_permissions:
                if not user.has_perm(permission):
                    missing_permissions.append(permission)
            
            has_permission = len(missing_permissions) == 0
            
            return {
                'has_permission': has_permission,
                'message': '权限检查完成' if has_permission else '缺少必要权限',
                'missing_permissions': missing_permissions
            }
            
        except Exception as e:
            logger.error(f"权限检查发生错误: {str(e)}")
            return {
                'has_permission': False,
                'message': '权限检查发生错误',
                'missing_permissions': required_permissions or []
            }
    
    @staticmethod
    def change_user_password(user: User, old_password: str, new_password: str) -> Dict:
        """
        更改用户密码
        
        Args:
            user: Django User 对象
            old_password: 旧密码
            new_password: 新密码
            
        Returns:
            dict: 密码更改结果
        """
        try:
            # 验证旧密码
            if not user.check_password(old_password):
                return {
                    'success': False,
                    'message': '当前密码不正确',
                    'error_code': 'INVALID_OLD_PASSWORD'
                }
            
            # 检查新密码是否与旧密码相同
            if user.check_password(new_password):
                return {
                    'success': False,
                    'message': '新密码不能与当前密码相同',
                    'error_code': 'SAME_PASSWORD'
                }
            
            # 更改密码
            user.set_password(new_password)
            user.save()
            
            logger.info(f"用户密码更改成功: {user.username}")
            
            return {
                'success': True,
                'message': '密码更改成功',
                'error_code': None
            }
            
        except Exception as e:
            logger.error(f"密码更改发生错误 - 用户: {user.username}, 错误: {str(e)}")
            return {
                'success': False,
                'message': '密码更改失败',
                'error_code': 'PASSWORD_CHANGE_ERROR'
            }
    
    @staticmethod
    def get_session_info(request: HttpRequest) -> Dict:
        """
        获取 session 信息
        
        Args:
            request: Django request 对象
            
        Returns:
            dict: session 信息
        """
        try:
            session_data = {
                'session_key': request.session.session_key,
                'is_authenticated': request.user.is_authenticated,
                'session_items_count': len(request.session.items()),
                'session_age': None,
                'last_activity': None
            }
            
            # 获取 session 创建时间和最后活动时间
            if request.session.session_key:
                try:
                    session_obj = Session.objects.get(session_key=request.session.session_key)
                    session_data.update({
                        'last_activity': session_obj.expire_date.isoformat(),
                        'session_age': (timezone.now() - session_obj.expire_date).total_seconds()
                    })
                except Session.DoesNotExist:
                    pass
            
            # 添加用户信息
            if request.user.is_authenticated:
                session_data.update({
                    'user_id': request.user.id,
                    'username': request.user.username,
                    'user_is_staff': request.user.is_staff,
                    'user_is_superuser': request.user.is_superuser
                })
            
            return session_data
            
        except Exception as e:
            logger.error(f"获取 session 信息发生错误: {str(e)}")
            return {
                'error': f'获取 session 信息失败: {str(e)}'
            }


# 便利函数
def authenticate_and_login(username: str, password: str, request: HttpRequest) -> Dict:
    """
    便利函数：认证并登录用户
    
    Args:
        username: 用户名
        password: 密码  
        request: Django request 对象
        
    Returns:
        dict: 认证和登录结果
    """
    return AuthenticationService.authenticate_user(username, password, request)


def safe_logout(request: HttpRequest, force_clear_all_sessions: bool = True) -> Dict:
    """
    便利函数：安全登出用户
    
    Args:
        request: Django request 对象
        force_clear_all_sessions: 是否强制清除所有 session
        
    Returns:
        dict: 登出结果
    """
    return AuthenticationService.logout_user(request, force_clear_all_sessions)