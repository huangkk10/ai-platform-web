"""
输入验证服务 - Validation Service

提供各种输入数据的验证功能。

Author: AI Platform Team
Created: 2024-10-02
"""

import logging
import re
from typing import Dict, Tuple, Optional, List

logger = logging.getLogger(__name__)


class ValidationService:
    """输入验证服务类"""
    
    # 常用正则表达式
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,150}$')
    PHONE_PATTERN = re.compile(r'^(\+?86)?1[3-9]\d{9}$')  # 中国手机号
    
    @staticmethod
    def validate_login_data(data: Dict) -> Tuple[bool, Dict]:
        """
        验证登录数据
        
        Args:
            data: 登录数据字典 {'username': str, 'password': str}
            
        Returns:
            tuple: (is_valid: bool, error_messages: dict)
        """
        errors = {}
        
        try:
            username = data.get('username', '').strip()
            password = data.get('password', '')
            
            # 验证用户名
            if not username:
                errors['username'] = '用户名不能为空'
            elif len(username) < 3:
                errors['username'] = '用户名至少需要3个字符'
            elif len(username) > 150:
                errors['username'] = '用户名过长'
            
            # 验证密码
            if not password:
                errors['password'] = '密码不能为空'
            elif len(password) < 6:
                errors['password'] = '密码至少需要6个字符'
                
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"登录数据验证失败: {str(e)}")
            return False, {'general': '数据验证失败'}
    
    @staticmethod
    def validate_registration_data(data: Dict) -> Tuple[bool, Dict]:
        """
        验证注册数据
        
        Args:
            data: 注册数据字典
            
        Returns:
            tuple: (is_valid: bool, error_messages: dict)
        """
        errors = {}
        
        try:
            username = data.get('username', '').strip()
            password = data.get('password', '')
            email = data.get('email', '').strip()
            first_name = data.get('first_name', '').strip()
            last_name = data.get('last_name', '').strip()
            
            # 验证用户名
            if not username:
                errors['username'] = '用户名不能为空'
            elif not ValidationService.USERNAME_PATTERN.match(username):
                errors['username'] = '用户名只能包含字母、数字、下划线和连字符，长度3-150字符'
            
            # 验证密码
            if not password:
                errors['password'] = '密码不能为空'
            elif len(password) < 6:
                errors['password'] = '密码至少需要6个字符'
            elif len(password) > 128:
                errors['password'] = '密码不能超过128个字符'
            
            # 验证邮箱
            if not email:
                errors['email'] = 'Email不能为空'
            elif not ValidationService.EMAIL_PATTERN.match(email):
                errors['email'] = 'Email格式不正确'
            elif len(email) > 254:
                errors['email'] = 'Email地址过长'
            
            # 验证姓名（可选字段）
            if first_name and len(first_name) > 30:
                errors['first_name'] = '名字不能超过30个字符'
            if last_name and len(last_name) > 30:
                errors['last_name'] = '姓氏不能超过30个字符'
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"注册数据验证失败: {str(e)}")
            return False, {'general': '数据验证失败'}
    
    @staticmethod
    def validate_password_change_data(data: Dict) -> Tuple[bool, Dict]:
        """
        验证密码更改数据
        
        Args:
            data: 密码更改数据字典
            
        Returns:
            tuple: (is_valid: bool, error_messages: dict)
        """
        errors = {}
        
        try:
            old_password = data.get('old_password', '')
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
            
            # 验证旧密码
            if not old_password:
                errors['old_password'] = '当前密码不能为空'
            
            # 验证新密码
            if not new_password:
                errors['new_password'] = '新密码不能为空'
            elif len(new_password) < 6:
                errors['new_password'] = '新密码至少需要6个字符'
            elif len(new_password) > 128:
                errors['new_password'] = '新密码不能超过128个字符'
            elif new_password == old_password:
                errors['new_password'] = '新密码不能与当前密码相同'
            
            # 验证确认密码（如果提供）
            if confirm_password and confirm_password != new_password:
                errors['confirm_password'] = '确认密码与新密码不匹配'
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"密码更改数据验证失败: {str(e)}")
            return False, {'general': '数据验证失败'}
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        验证邮箱格式
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        try:
            if not email or not isinstance(email, str):
                return False
            return ValidationService.EMAIL_PATTERN.match(email.strip()) is not None
        except Exception:
            return False
    
    @staticmethod
    def validate_username(username: str) -> Tuple[bool, str]:
        """
        验证用户名
        
        Args:
            username: 用户名
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        try:
            if not username or not isinstance(username, str):
                return False, '用户名不能为空'
            
            username = username.strip()
            
            if len(username) < 3:
                return False, '用户名至少需要3个字符'
            elif len(username) > 150:
                return False, '用户名不能超过150个字符'
            elif not ValidationService.USERNAME_PATTERN.match(username):
                return False, '用户名只能包含字母、数字、下划线和连字符'
            else:
                return True, ''
                
        except Exception as e:
            logger.error(f"用户名验证失败: {str(e)}")
            return False, '用户名验证失败'
    
    @staticmethod
    def validate_phone(phone: str) -> bool:
        """
        验证手机号格式（中国）
        
        Args:
            phone: 手机号
            
        Returns:
            bool: 是否有效
        """
        try:
            if not phone or not isinstance(phone, str):
                return False
            return ValidationService.PHONE_PATTERN.match(phone.strip()) is not None
        except Exception:
            return False
    
    @staticmethod
    def validate_required_fields(data: Dict, required_fields: List[str]) -> Tuple[bool, Dict]:
        """
        验证必填字段
        
        Args:
            data: 数据字典
            required_fields: 必填字段列表
            
        Returns:
            tuple: (is_valid: bool, error_messages: dict)
        """
        errors = {}
        
        try:
            for field in required_fields:
                value = data.get(field)
                if not value or (isinstance(value, str) and not value.strip()):
                    errors[field] = f'{field} 不能为空'
            
            return len(errors) == 0, errors
            
        except Exception as e:
            logger.error(f"必填字段验证失败: {str(e)}")
            return False, {'general': '字段验证失败'}
    
    @staticmethod
    def sanitize_input(input_str: str, max_length: Optional[int] = None) -> str:
        """
        清理输入字符串
        
        Args:
            input_str: 输入字符串
            max_length: 最大长度限制
            
        Returns:
            str: 清理后的字符串
        """
        try:
            if not isinstance(input_str, str):
                return ''
            
            # 去除首尾空格
            cleaned = input_str.strip()
            
            # 长度限制
            if max_length and len(cleaned) > max_length:
                cleaned = cleaned[:max_length]
            
            # 移除危险字符（基本 XSS 防护）
            dangerous_chars = ['<', '>', '"', "'", '&']
            for char in dangerous_chars:
                cleaned = cleaned.replace(char, '')
            
            return cleaned
            
        except Exception as e:
            logger.error(f"输入清理失败: {str(e)}")
            return ''
    
    @staticmethod
    def validate_file_upload(file_data: Dict) -> Tuple[bool, str]:
        """
        验证文件上传
        
        Args:
            file_data: 文件数据字典
            
        Returns:
            tuple: (is_valid: bool, error_message: str)
        """
        try:
            if not file_data:
                return False, '没有文件数据'
            
            # 检查文件大小
            max_size = 10 * 1024 * 1024  # 10MB
            file_size = file_data.get('size', 0)
            if file_size > max_size:
                return False, '文件大小不能超过10MB'
            
            # 检查文件类型
            allowed_types = [
                'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
                'application/pdf', 'text/plain'
            ]
            content_type = file_data.get('content_type', '')
            if content_type not in allowed_types:
                return False, '不支持的文件类型'
            
            # 检查文件名
            filename = file_data.get('name', '')
            if not filename:
                return False, '文件名不能为空'
            elif len(filename) > 255:
                return False, '文件名过长'
            
            return True, ''
            
        except Exception as e:
            logger.error(f"文件上传验证失败: {str(e)}")
            return False, '文件验证失败'


# 便利函数
def validate_login(username: str, password: str) -> Tuple[bool, Dict]:
    """
    便利函数：验证登录数据
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        tuple: (is_valid, errors)
    """
    return ValidationService.validate_login_data({
        'username': username,
        'password': password
    })


def is_valid_email(email: str) -> bool:
    """
    便利函数：验证邮箱
    
    Args:
        email: 邮箱地址
        
    Returns:
        bool: 是否有效
    """
    return ValidationService.validate_email(email)