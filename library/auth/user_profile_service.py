"""
用户资料服务 - User Profile Service

提供用户资料的获取、格式化和管理功能。

Author: AI Platform Team  
Created: 2024-10-02
"""

import logging
from typing import Dict, Optional
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class UserProfileService:
    """用户资料服务类"""
    
    @staticmethod
    def get_user_profile_data(user: User) -> Dict:
        """
        获取用户完整资料并格式化
        
        Args:
            user: Django User 对象
            
        Returns:
            dict: 格式化的用户数据
        """
        try:
            if not user:
                return {
                    'error': '用户对象不能为空',
                    'user': None
                }
            
            # 获取用户基本信息
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            
            # 尝试获取 UserProfile 扩展信息
            try:
                # 动态导入避免循环引用
                from api.models import UserProfile
                
                profile = UserProfile.objects.get(user=user)
                user_data.update({
                    'bio': profile.bio or '',
                    'phone': getattr(profile, 'phone', ''),
                    'avatar': getattr(profile, 'avatar', ''),
                    'department': getattr(profile, 'department', ''),
                    'position': getattr(profile, 'position', ''),
                })
                
            except Exception:
                # UserProfile 不存在或获取失败，使用默认值
                user_data.update({
                    'bio': '',
                    'phone': '',
                    'avatar': '',
                    'department': '',
                    'position': '',
                })
            
            return {
                'error': None,
                'user': user_data
            }
            
        except Exception as e:
            logger.error(f"获取用户资料失败 - 用户ID: {user.id if user else 'None'}, 错误: {str(e)}")
            return {
                'error': f'获取用户资料失败: {str(e)}',
                'user': None
            }
    
    @staticmethod
    def create_or_update_user_profile(user: User, profile_data: Dict) -> Dict:
        """
        创建或更新用户资料
        
        Args:
            user: Django User 对象
            profile_data: 用户资料数据
            
        Returns:
            dict: 操作结果
        """
        try:
            # 动态导入避免循环引用
            from api.models import UserProfile
            
            # 获取或创建 UserProfile
            profile, created = UserProfile.objects.get_or_create(
                user=user,
                defaults={'bio': f'欢迎 {user.first_name or user.username} 加入！'}
            )
            
            # 更新资料字段
            updated_fields = []
            
            if 'bio' in profile_data:
                profile.bio = profile_data['bio']
                updated_fields.append('bio')
            
            if 'phone' in profile_data and hasattr(profile, 'phone'):
                profile.phone = profile_data['phone']
                updated_fields.append('phone')
            
            if 'department' in profile_data and hasattr(profile, 'department'):
                profile.department = profile_data['department']
                updated_fields.append('department')
            
            if 'position' in profile_data and hasattr(profile, 'position'):
                profile.position = profile_data['position']
                updated_fields.append('position')
            
            # 保存更改
            if updated_fields or created:
                profile.save()
                action = '创建' if created else '更新'
                logger.info(f"用户资料{action}成功 - 用户: {user.username}, 字段: {updated_fields}")
            
            return {
                'success': True,
                'created': created,
                'updated_fields': updated_fields,
                'profile': profile,
                'message': f'用户资料{"创建" if created else "更新"}成功'
            }
            
        except Exception as e:
            logger.error(f"创建/更新用户资料失败 - 用户: {user.username}, 错误: {str(e)}")
            return {
                'success': False,
                'created': False,
                'updated_fields': [],
                'profile': None,
                'message': f'用户资料操作失败: {str(e)}'
            }
    
    @staticmethod
    def get_user_display_name(user: User) -> str:
        """
        获取用户显示名称
        
        Args:
            user: Django User 对象
            
        Returns:
            str: 用户显示名称
        """
        try:
            if not user:
                return '未知用户'
            
            # 优先使用全名
            if user.first_name and user.last_name:
                return f"{user.first_name} {user.last_name}"
            elif user.first_name:
                return user.first_name
            elif user.last_name:
                return user.last_name
            else:
                return user.username
                
        except Exception as e:
            logger.error(f"获取用户显示名称失败: {str(e)}")
            return '用户'
    
    @staticmethod
    def get_user_safe_info(user: User) -> Dict:
        """
        获取用户安全信息（不包含敏感数据）
        
        Args:
            user: Django User 对象
            
        Returns:
            dict: 安全的用户信息
        """
        try:
            if not user:
                return {}
            
            return {
                'id': user.id,
                'username': user.username,
                'display_name': UserProfileService.get_user_display_name(user),
                'is_staff': user.is_staff,
                'is_active': user.is_active,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None
            }
            
        except Exception as e:
            logger.error(f"获取用户安全信息失败: {str(e)}")
            return {}
    
    @staticmethod
    def validate_user_data(user_data: Dict) -> Dict:
        """
        验证用户数据
        
        Args:
            user_data: 用户数据字典
            
        Returns:
            dict: 验证结果
        """
        errors = {}
        
        # 验证用户名
        username = user_data.get('username', '').strip()
        if not username:
            errors['username'] = '用户名不能为空'
        elif len(username) < 3:
            errors['username'] = '用户名至少需要3个字符'
        elif len(username) > 150:
            errors['username'] = '用户名不能超过150个字符'
        
        # 验证邮箱
        email = user_data.get('email', '').strip()
        if not email:
            errors['email'] = 'Email不能为空'
        elif '@' not in email or '.' not in email:
            errors['email'] = 'Email格式不正确'
        
        # 验证密码
        password = user_data.get('password', '')
        if not password:
            errors['password'] = '密码不能为空'
        elif len(password) < 6:
            errors['password'] = '密码至少需要6个字符'
        
        # 验证姓名长度
        first_name = user_data.get('first_name', '').strip()
        if first_name and len(first_name) > 30:
            errors['first_name'] = '名字不能超过30个字符'
            
        last_name = user_data.get('last_name', '').strip()
        if last_name and len(last_name) > 30:
            errors['last_name'] = '姓氏不能超过30个字符'
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'cleaned_data': {
                'username': username,
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
                'password': password
            } if len(errors) == 0 else None
        }


# 便利函数
def get_user_data(user: User) -> Dict:
    """
    便利函数：获取用户数据
    
    Args:
        user: Django User 对象
        
    Returns:
        dict: 用户数据
    """
    result = UserProfileService.get_user_profile_data(user)
    return result.get('user') or {}


def get_display_name(user: User) -> str:
    """
    便利函数：获取用户显示名称
    
    Args:
        user: Django User 对象
        
    Returns:
        str: 显示名称
    """
    return UserProfileService.get_user_display_name(user)