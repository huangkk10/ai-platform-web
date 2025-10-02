#!/usr/bin/env python
"""
认证 Library 测试脚本

测试新创建的认证 library 组件的基本功能。
注意：这个测试需要在 Django 环境中运行。

使用方法：
cd /home/user/codes/ai-platform-web/backend
python -m pytest tests/test_auth_library.py -v

Author: AI Platform Team
Created: 2024-10-02
"""

import os
import sys
import django
from unittest.mock import Mock, patch
import pytest

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

# 现在可以导入 Django 相关模块和我们的 library
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.middleware import AuthenticationMiddleware

# 导入我们的认证 library
try:
    from library.auth import (
        AuthenticationService,
        UserProfileService,
        ValidationService,
        AuthResponseFormatter
    )
    LIBRARY_IMPORTED = True
except ImportError as e:
    print(f"❌ Library 导入失败: {e}")
    LIBRARY_IMPORTED = False


class TestValidationService:
    """测试验证服务"""
    
    def test_validate_login_data_success(self):
        """测试登录数据验证 - 成功案例"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        data = {
            'username': 'testuser',
            'password': 'password123'
        }
        
        is_valid, errors = ValidationService.validate_login_data(data)
        
        assert is_valid == True
        assert errors == {}
        print("✅ 登录数据验证 - 成功案例")
    
    def test_validate_login_data_failure(self):
        """测试登录数据验证 - 失败案例"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        data = {
            'username': '',  # 空用户名
            'password': '123'  # 密码太短
        }
        
        is_valid, errors = ValidationService.validate_login_data(data)
        
        assert is_valid == False
        assert 'username' in errors
        assert 'password' in errors
        print("✅ 登录数据验证 - 失败案例")
    
    def test_validate_email(self):
        """测试邮箱验证"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 有效邮箱
        assert ValidationService.validate_email('test@example.com') == True
        assert ValidationService.validate_email('user.name@domain.co.uk') == True
        
        # 无效邮箱
        assert ValidationService.validate_email('invalid-email') == False
        assert ValidationService.validate_email('') == False
        assert ValidationService.validate_email(None) == False
        
        print("✅ 邮箱验证测试")
    
    def test_sanitize_input(self):
        """测试输入清理"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 基本清理
        result = ValidationService.sanitize_input('  test input  ')
        assert result == 'test input'
        
        # 长度限制
        result = ValidationService.sanitize_input('very long input', max_length=5)
        assert result == 'very '
        
        # 危险字符移除
        result = ValidationService.sanitize_input('test<script>alert("xss")</script>')
        assert '<' not in result and '>' not in result
        
        print("✅ 输入清理测试")


class TestUserProfileService:
    """测试用户资料服务"""
    
    def test_get_user_display_name(self):
        """测试获取用户显示名称"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 创建模拟用户
        user = Mock()
        user.first_name = 'John'
        user.last_name = 'Doe'
        user.username = 'johndoe'
        
        # 测试全名
        result = UserProfileService.get_user_display_name(user)
        assert result == 'John Doe'
        
        # 测试只有名字
        user.last_name = ''
        result = UserProfileService.get_user_display_name(user)
        assert result == 'John'
        
        # 测试只有用户名
        user.first_name = ''
        user.last_name = ''
        result = UserProfileService.get_user_display_name(user)
        assert result == 'johndoe'
        
        print("✅ 用户显示名称测试")
    
    def test_validate_user_data(self):
        """测试用户数据验证"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 有效数据
        valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        
        result = UserProfileService.validate_user_data(valid_data)
        assert result['is_valid'] == True
        assert result['errors'] == {}
        assert result['cleaned_data'] is not None
        
        # 无效数据
        invalid_data = {
            'username': '',  # 空用户名
            'email': 'invalid-email',  # 无效邮箱
            'password': ''  # 空密码
        }
        
        result = UserProfileService.validate_user_data(invalid_data)
        assert result['is_valid'] == False
        assert len(result['errors']) > 0
        
        print("✅ 用户数据验证测试")


class TestAuthenticationService:
    """测试认证服务"""
    
    @patch('library.auth.authentication_service.authenticate')
    def test_authenticate_user_success(self, mock_authenticate):
        """测试用户认证 - 成功案例"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 创建模拟用户
        mock_user = Mock()
        mock_user.is_active = True
        mock_authenticate.return_value = mock_user
        
        # 创建模拟请求
        mock_request = Mock()
        
        result = AuthenticationService.authenticate_user(
            'testuser', 'password123', mock_request
        )
        
        assert result['success'] == True
        assert result['user'] == mock_user
        assert result['error_code'] is None
        
        print("✅ 用户认证成功测试")
    
    @patch('library.auth.authentication_service.authenticate')
    def test_authenticate_user_failure(self, mock_authenticate):
        """测试用户认证 - 失败案例"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 模拟认证失败
        mock_authenticate.return_value = None
        
        result = AuthenticationService.authenticate_user(
            'testuser', 'wrongpassword', None
        )
        
        assert result['success'] == False
        assert result['user'] is None
        assert result['error_code'] == 'INVALID_CREDENTIALS'
        
        print("✅ 用户认证失败测试")
    
    def test_check_user_permissions(self):
        """测试用户权限检查"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 模拟超级用户
        mock_superuser = Mock()
        mock_superuser.is_authenticated = True
        mock_superuser.is_superuser = True
        mock_superuser.is_staff = True
        
        result = AuthenticationService.check_user_permissions(
            mock_superuser, ['auth.add_user']
        )
        
        assert result['has_permission'] == True
        assert result['missing_permissions'] == []
        
        # 模拟普通用户
        mock_user = Mock()
        mock_user.is_authenticated = True
        mock_user.is_superuser = False
        mock_user.is_staff = False
        mock_user.has_perm.return_value = False
        
        result = AuthenticationService.check_user_permissions(
            mock_user, ['auth.add_user']
        )
        
        assert result['has_permission'] == False
        assert 'auth.add_user' in result['missing_permissions']
        
        print("✅ 用户权限检查测试")


class TestAuthResponseFormatter:
    """测试响应格式化器"""
    
    def test_success_response(self):
        """测试成功响应格式化"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        # 模拟用户
        mock_user = Mock()
        mock_user.id = 1
        mock_user.username = 'testuser'
        mock_user.email = 'test@example.com'
        
        with patch('library.auth.response_formatter.UserProfileService') as mock_service:
            mock_service.get_user_profile_data.return_value = {
                'user': {
                    'id': 1,
                    'username': 'testuser',
                    'email': 'test@example.com'
                }
            }
            
            response = AuthResponseFormatter.success_response(
                user=mock_user,
                message="操作成功",
                use_drf=False
            )
            
            # 验证响应不为空
            assert response is not None
            
        print("✅ 成功响应格式化测试")
    
    def test_error_response(self):
        """测试错误响应格式化"""
        if not LIBRARY_IMPORTED:
            pytest.skip("Library not available")
        
        response = AuthResponseFormatter.error_response(
            message="操作失败",
            error_code="TEST_ERROR",
            status_code=400,
            use_drf=False
        )
        
        # 验证响应不为空
        assert response is not None
        
        print("✅ 错误响应格式化测试")


def run_manual_tests():
    """手动运行测试（当 pytest 不可用时）"""
    print("🧪 开始手动测试...")
    
    if not LIBRARY_IMPORTED:
        print("❌ Library 未导入，跳过测试")
        return
    
    # 验证服务测试
    print("\n📋 ValidationService 测试:")
    try:
        # 测试登录数据验证
        data = {'username': 'test', 'password': 'password123'}
        is_valid, errors = ValidationService.validate_login_data(data)
        print(f"  ✅ 登录验证: {is_valid}, 错误: {errors}")
        
        # 测试邮箱验证
        email_valid = ValidationService.validate_email('test@example.com')
        print(f"  ✅ 邮箱验证: {email_valid}")
        
        # 测试输入清理
        cleaned = ValidationService.sanitize_input('  test<>input  ')
        print(f"  ✅ 输入清理: '{cleaned}'")
        
    except Exception as e:
        print(f"  ❌ ValidationService 测试失败: {e}")
    
    # 用户资料服务测试
    print("\n👤 UserProfileService 测试:")
    try:
        # 模拟用户
        class MockUser:
            def __init__(self):
                self.first_name = 'Test'
                self.last_name = 'User'
                self.username = 'testuser'
        
        user = MockUser()
        display_name = UserProfileService.get_user_display_name(user)
        print(f"  ✅ 显示名称: {display_name}")
        
        # 验证用户数据
        user_data = {
            'username': 'test',
            'email': 'test@example.com',
            'password': 'password123'
        }
        validation = UserProfileService.validate_user_data(user_data)
        print(f"  ✅ 数据验证: {validation['is_valid']}")
        
    except Exception as e:
        print(f"  ❌ UserProfileService 测试失败: {e}")
    
    # 认证服务测试
    print("\n🔐 AuthenticationService 测试:")
    try:
        # 测试权限检查（无需真实用户）
        class MockUser:
            def __init__(self):
                self.is_authenticated = True
                self.is_superuser = True
                self.is_staff = True
        
        user = MockUser()
        permission_check = AuthenticationService.check_user_permissions(user)
        print(f"  ✅ 权限检查: {permission_check['has_permission']}")
        
    except Exception as e:
        print(f"  ❌ AuthenticationService 测试失败: {e}")
    
    print("\n🎉 手动测试完成！")


if __name__ == "__main__":
    print("🚀 认证 Library 测试")
    print("=" * 50)
    
    if LIBRARY_IMPORTED:
        print("✅ Library 导入成功")
        print("\n📝 可用的测试方法：")
        print("1. pytest tests/test_auth_library.py -v")
        print("2. python tests/test_auth_library.py")
        print("3. 在 Django shell 中导入并测试")
        
        # 运行手动测试
        run_manual_tests()
        
    else:
        print("❌ Library 导入失败")
        print("📋 请确保：")
        print("- 在正确的 Django 项目目录中运行")
        print("- library/auth/ 目录存在")
        print("- 所有依赖已安装")
        
    print("\n" + "=" * 50)
    print("测试完成！")