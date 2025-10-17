"""
PermissionMixin 單元測試

測試標準權限控制模式
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIRequestFactory
from rest_framework import permissions

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from api.views.mixins import ReadOnlyForUserWriteForAdminMixin, DelegatedPermissionMixin


class MockViewSetReadOnly(ReadOnlyForUserWriteForAdminMixin):
    """測試用的 ReadOnly Mock ViewSet"""
    pass


class MockViewSetDelegated(DelegatedPermissionMixin):
    """測試用的 Delegated Mock ViewSet"""
    
    def get_manager(self):
        """Mock get_manager 方法"""
        return Mock()


class TestReadOnlyForUserWriteForAdminMixin(TestCase):
    """ReadOnlyForUserWriteForAdminMixin 單元測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.factory = APIRequestFactory()
        self.viewset = MockViewSetReadOnly()
        
        # Mock 普通用戶
        self.normal_user = Mock()
        self.normal_user.is_staff = False
        self.normal_user.is_authenticated = True
        
        # Mock 管理員
        self.admin_user = Mock()
        self.admin_user.is_staff = True
        self.admin_user.is_authenticated = True
        
        # Mock 匿名用戶
        self.anon_user = Mock()
        self.anon_user.is_authenticated = False
    
    # ========================================
    # 測試 get_permissions() - 讀操作
    # ========================================
    
    def test_get_permissions_for_list_action(self):
        """測試 list 動作的權限"""
        self.viewset.action = 'list'
        
        perms = self.viewset.get_permissions()
        
        # 應該只需要認證
        self.assertTrue(any(isinstance(p, permissions.IsAuthenticated) for p in perms))
    
    def test_get_permissions_for_retrieve_action(self):
        """測試 retrieve 動作的權限"""
        self.viewset.action = 'retrieve'
        
        perms = self.viewset.get_permissions()
        
        # 應該只需要認證
        self.assertTrue(any(isinstance(p, permissions.IsAuthenticated) for p in perms))
    
    # ========================================
    # 測試 get_permissions() - 寫操作
    # ========================================
    
    def test_get_permissions_for_create_action(self):
        """測試 create 動作的權限"""
        self.viewset.action = 'create'
        
        perms = self.viewset.get_permissions()
        
        # 應該需要管理員權限
        self.assertTrue(any(isinstance(p, permissions.IsAdminUser) for p in perms))
    
    def test_get_permissions_for_update_action(self):
        """測試 update 動作的權限"""
        self.viewset.action = 'update'
        
        perms = self.viewset.get_permissions()
        
        # 應該需要管理員權限
        self.assertTrue(any(isinstance(p, permissions.IsAdminUser) for p in perms))
    
    def test_get_permissions_for_partial_update_action(self):
        """測試 partial_update 動作的權限"""
        self.viewset.action = 'partial_update'
        
        perms = self.viewset.get_permissions()
        
        # 應該需要管理員權限
        self.assertTrue(any(isinstance(p, permissions.IsAdminUser) for p in perms))
    
    def test_get_permissions_for_destroy_action(self):
        """測試 destroy 動作的權限"""
        self.viewset.action = 'destroy'
        
        perms = self.viewset.get_permissions()
        
        # 應該需要管理員權限
        self.assertTrue(any(isinstance(p, permissions.IsAdminUser) for p in perms))
    
    # ========================================
    # 測試實際權限檢查
    # ========================================
    
    def test_normal_user_can_list(self):
        """測試普通用戶可以列表"""
        self.viewset.action = 'list'
        request = self.factory.get('/api/test/')
        request.user = self.normal_user
        
        perms = self.viewset.get_permissions()
        
        # 驗證普通用戶通過認證權限
        for perm in perms:
            if isinstance(perm, permissions.IsAuthenticated):
                has_perm = perm.has_permission(request, self.viewset)
                self.assertTrue(has_perm)
    
    def test_normal_user_cannot_create(self):
        """測試普通用戶不能創建"""
        self.viewset.action = 'create'
        request = self.factory.post('/api/test/')
        request.user = self.normal_user
        
        perms = self.viewset.get_permissions()
        
        # 驗證普通用戶不通過管理員權限
        for perm in perms:
            if isinstance(perm, permissions.IsAdminUser):
                has_perm = perm.has_permission(request, self.viewset)
                self.assertFalse(has_perm)
    
    def test_admin_user_can_create(self):
        """測試管理員可以創建"""
        self.viewset.action = 'create'
        request = self.factory.post('/api/test/')
        request.user = self.admin_user
        
        perms = self.viewset.get_permissions()
        
        # 驗證管理員通過權限
        for perm in perms:
            if isinstance(perm, permissions.IsAdminUser):
                has_perm = perm.has_permission(request, self.viewset)
                self.assertTrue(has_perm)
    
    def test_anon_user_cannot_list(self):
        """測試匿名用戶不能列表"""
        self.viewset.action = 'list'
        request = self.factory.get('/api/test/')
        request.user = self.anon_user
        
        perms = self.viewset.get_permissions()
        
        # 驗證匿名用戶不通過認證
        for perm in perms:
            if isinstance(perm, permissions.IsAuthenticated):
                has_perm = perm.has_permission(request, self.viewset)
                self.assertFalse(has_perm)
    
    # ========================================
    # 測試自定義動作
    # ========================================
    
    def test_custom_action_defaults_to_read_permission(self):
        """測試自定義動作默認使用讀權限"""
        self.viewset.action = 'custom_action'
        
        perms = self.viewset.get_permissions()
        
        # 自定義動作應該默認為讀權限
        self.assertTrue(any(isinstance(p, permissions.IsAuthenticated) for p in perms))


class TestDelegatedPermissionMixin(TestCase):
    """DelegatedPermissionMixin 單元測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.factory = APIRequestFactory()
        self.viewset = MockViewSetDelegated()
        
        self.user = Mock()
        self.user.is_authenticated = True
    
    # ========================================
    # 測試委託權限
    # ========================================
    
    def test_get_permissions_delegates_to_manager(self):
        """測試權限委託給 Manager"""
        mock_manager = Mock()
        mock_manager.get_permissions = Mock(return_value=[permissions.IsAuthenticated()])
        
        self.viewset.get_manager = Mock(return_value=mock_manager)
        
        perms = self.viewset.get_permissions()
        
        # 驗證調用了 Manager 的方法
        mock_manager.get_permissions.assert_called_once()
        self.assertTrue(any(isinstance(p, permissions.IsAuthenticated) for p in perms))
    
    def test_get_permissions_falls_back_when_no_manager(self):
        """測試沒有 Manager 時的備用權限"""
        self.viewset.get_manager = Mock(return_value=None)
        
        perms = self.viewset.get_permissions()
        
        # 應該返回默認權限（IsAuthenticated）
        self.assertTrue(any(isinstance(p, permissions.IsAuthenticated) for p in perms))
    
    def test_get_permissions_handles_manager_exception(self):
        """測試 Manager 拋出異常時的處理"""
        mock_manager = Mock()
        mock_manager.get_permissions = Mock(side_effect=Exception("Manager error"))
        
        self.viewset.get_manager = Mock(return_value=mock_manager)
        
        # 應該不會崩潰，返回默認權限
        perms = self.viewset.get_permissions()
        self.assertTrue(isinstance(perms, list))


class TestPermissionMixinIntegration(TestCase):
    """PermissionMixin 整合測試"""
    
    def setUp(self):
        """設置測試環境"""
        self.factory = APIRequestFactory()
    
    def test_readonly_mixin_with_different_users(self):
        """測試 ReadOnly Mixin 與不同用戶的整合"""
        viewset = MockViewSetReadOnly()
        
        # 普通用戶
        normal_user = Mock()
        normal_user.is_staff = False
        normal_user.is_authenticated = True
        
        # 管理員
        admin_user = Mock()
        admin_user.is_staff = True
        admin_user.is_authenticated = True
        
        # 測試讀操作
        viewset.action = 'list'
        list_request = self.factory.get('/api/test/')
        
        list_request.user = normal_user
        perms_normal = viewset.get_permissions()
        self.assertTrue(len(perms_normal) > 0)
        
        # 測試寫操作
        viewset.action = 'create'
        create_request = self.factory.post('/api/test/')
        
        create_request.user = admin_user
        perms_admin = viewset.get_permissions()
        
        # 驗證權限不同
        self.assertNotEqual(type(perms_normal[0]), type(perms_admin[0]))
    
    def test_all_crud_actions_permissions(self):
        """測試所有 CRUD 動作的權限"""
        viewset = MockViewSetReadOnly()
        
        read_actions = ['list', 'retrieve']
        write_actions = ['create', 'update', 'partial_update', 'destroy']
        
        # 測試讀動作
        for action in read_actions:
            viewset.action = action
            perms = viewset.get_permissions()
            self.assertTrue(
                any(isinstance(p, permissions.IsAuthenticated) for p in perms),
                f"Action {action} should use IsAuthenticated"
            )
        
        # 測試寫動作
        for action in write_actions:
            viewset.action = action
            perms = viewset.get_permissions()
            self.assertTrue(
                any(isinstance(p, permissions.IsAdminUser) for p in perms),
                f"Action {action} should use IsAdminUser"
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
