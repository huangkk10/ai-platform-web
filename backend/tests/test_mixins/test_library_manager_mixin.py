"""
LibraryManagerMixin 單元測試

測試 Library Manager 初始化和管理功能
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
from django.conf import settings

# 導入待測試的 Mixin
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from api.views.mixins import LibraryManagerMixin


class MockViewSetWithLibrary(LibraryManagerMixin):
    """測試用的 Mock ViewSet"""
    
    library_config = {
        'library_available_flag': 'MOCK_LIBRARY_AVAILABLE',
        'manager_factory': 'create_mock_manager',
        'library_name': 'Mock Library',
        'fallback_available_flag': 'MOCK_FALLBACK_AVAILABLE',
        'fallback_manager_factory': 'create_mock_fallback_manager',
        'fallback_library_name': 'Mock Fallback Library'
    }


class MockViewSetWithoutFallback(LibraryManagerMixin):
    """沒有 Fallback 配置的 Mock ViewSet"""
    
    library_config = {
        'library_available_flag': 'MOCK_LIBRARY_AVAILABLE',
        'manager_factory': 'create_mock_manager',
        'library_name': 'Mock Library'
    }


class MockViewSetInvalidConfig(LibraryManagerMixin):
    """配置錯誤的 Mock ViewSet"""
    
    library_config = {
        'library_available_flag': 'MOCK_LIBRARY_AVAILABLE'
        # 缺少 manager_factory
    }


class TestLibraryManagerMixin(TestCase):
    """LibraryManagerMixin 單元測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.viewset = MockViewSetWithLibrary()
        self.viewset_no_fallback = MockViewSetWithoutFallback()
        self.viewset_invalid = MockViewSetInvalidConfig()
    
    # ========================================
    # 測試 has_manager() 方法
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    def test_has_manager_true_when_library_enabled(self):
        """測試 Library 啟用時 has_manager() 返回 True"""
        result = self.viewset.has_manager()
        self.assertTrue(result)
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=False)
    def test_has_manager_false_when_library_disabled(self):
        """測試 Library 停用時 has_manager() 返回 False"""
        result = self.viewset.has_manager()
        self.assertFalse(result)
    
    def test_has_manager_false_when_flag_not_exists(self):
        """測試 Library flag 不存在時返回 False"""
        # 使用不存在的 flag
        if hasattr(settings, 'MOCK_LIBRARY_AVAILABLE'):
            delattr(settings, 'MOCK_LIBRARY_AVAILABLE')
        
        result = self.viewset.has_manager()
        self.assertFalse(result)
    
    def test_has_manager_handles_invalid_config(self):
        """測試配置錯誤時的處理"""
        # 應該不會崩潰，返回 False
        result = self.viewset_invalid.has_manager()
        self.assertFalse(result)
    
    # ========================================
    # 測試 has_fallback_manager() 方法
    # ========================================
    
    @override_settings(MOCK_FALLBACK_AVAILABLE=True)
    def test_has_fallback_manager_true_when_enabled(self):
        """測試 Fallback Library 啟用時返回 True"""
        result = self.viewset.has_fallback_manager()
        self.assertTrue(result)
    
    @override_settings(MOCK_FALLBACK_AVAILABLE=False)
    def test_has_fallback_manager_false_when_disabled(self):
        """測試 Fallback Library 停用時返回 False"""
        result = self.viewset.has_fallback_manager()
        self.assertFalse(result)
    
    def test_has_fallback_manager_false_when_not_configured(self):
        """測試沒有配置 Fallback 時返回 False"""
        result = self.viewset_no_fallback.has_fallback_manager()
        self.assertFalse(result)
    
    # ========================================
    # 測試 get_manager() 方法
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_get_manager_success_when_enabled(self, mock_factory):
        """測試 Library 啟用時成功獲取 Manager"""
        # Mock manager factory
        mock_manager = Mock()
        mock_factory.return_value = mock_manager
        
        result = self.viewset.get_manager()
        
        # 驗證返回正確的 manager
        self.assertEqual(result, mock_manager)
        mock_factory.assert_called_once()
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=False)
    def test_get_manager_none_when_disabled(self):
        """測試 Library 停用時返回 None"""
        result = self.viewset.get_manager()
        self.assertIsNone(result)
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_get_manager_caches_result(self, mock_factory):
        """測試 Manager 會被緩存"""
        mock_manager = Mock()
        mock_factory.return_value = mock_manager
        
        # 第一次調用
        result1 = self.viewset.get_manager()
        # 第二次調用
        result2 = self.viewset.get_manager()
        
        # 應該返回相同的實例
        self.assertEqual(result1, result2)
        # Factory 只應該被調用一次
        mock_factory.assert_called_once()
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_get_manager_handles_factory_exception(self, mock_factory):
        """測試 Factory 拋出異常時的處理"""
        mock_factory.side_effect = Exception("Factory error")
        
        # 應該返回 None 而不是崩潰
        result = self.viewset.get_manager()
        self.assertIsNone(result)
    
    # ========================================
    # 測試 get_fallback_manager() 方法
    # ========================================
    
    @override_settings(MOCK_FALLBACK_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_fallback_manager')
    def test_get_fallback_manager_success(self, mock_factory):
        """測試成功獲取 Fallback Manager"""
        mock_manager = Mock()
        mock_factory.return_value = mock_manager
        
        result = self.viewset.get_fallback_manager()
        
        self.assertEqual(result, mock_manager)
        mock_factory.assert_called_once()
    
    @override_settings(MOCK_FALLBACK_AVAILABLE=False)
    def test_get_fallback_manager_none_when_disabled(self):
        """測試 Fallback 停用時返回 None"""
        result = self.viewset.get_fallback_manager()
        self.assertIsNone(result)
    
    def test_get_fallback_manager_none_when_not_configured(self):
        """測試未配置 Fallback 時返回 None"""
        result = self.viewset_no_fallback.get_fallback_manager()
        self.assertIsNone(result)
    
    # ========================================
    # 測試日誌記錄
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    @patch('api.views.mixins.library_manager_mixin.logger')
    def test_logging_on_manager_creation(self, mock_logger, mock_factory):
        """測試創建 Manager 時的日誌記錄"""
        mock_manager = Mock()
        mock_factory.return_value = mock_manager
        
        self.viewset.get_manager()
        
        # 驗證有日誌記錄
        self.assertTrue(mock_logger.info.called or mock_logger.debug.called)
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=False)
    @patch('api.views.mixins.library_manager_mixin.logger')
    def test_logging_when_library_disabled(self, mock_logger):
        """測試 Library 停用時的日誌記錄"""
        self.viewset.get_manager()
        
        # 驗證有警告或信息日誌
        self.assertTrue(mock_logger.warning.called or mock_logger.info.called)
    
    # ========================================
    # 測試配置驗證
    # ========================================
    
    def test_config_with_all_required_fields(self):
        """測試包含所有必需字段的配置"""
        config = self.viewset.library_config
        
        self.assertIn('library_available_flag', config)
        self.assertIn('manager_factory', config)
        self.assertIn('library_name', config)
    
    def test_config_without_required_fields(self):
        """測試缺少必需字段的配置"""
        config = self.viewset_invalid.library_config
        
        self.assertIn('library_available_flag', config)
        self.assertNotIn('manager_factory', config)  # 缺少這個
    
    def test_viewset_without_config(self):
        """測試沒有 library_config 的 ViewSet"""
        class ViewSetNoConfig(LibraryManagerMixin):
            pass
        
        viewset = ViewSetNoConfig()
        
        # 應該不會崩潰
        result = viewset.has_manager()
        self.assertFalse(result)


class TestLibraryManagerMixinIntegration(TestCase):
    """LibraryManagerMixin 整合測試"""
    
    @override_settings(
        MOCK_LIBRARY_AVAILABLE=True,
        MOCK_FALLBACK_AVAILABLE=True
    )
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    @patch('api.views.mixins.library_manager_mixin.create_mock_fallback_manager')
    def test_primary_and_fallback_both_available(
        self, 
        mock_fallback_factory, 
        mock_primary_factory
    ):
        """測試 Primary 和 Fallback 都可用的情況"""
        viewset = MockViewSetWithLibrary()
        
        mock_primary = Mock()
        mock_fallback = Mock()
        mock_primary_factory.return_value = mock_primary
        mock_fallback_factory.return_value = mock_fallback
        
        # 應該優先使用 Primary
        primary = viewset.get_manager()
        self.assertEqual(primary, mock_primary)
        
        # Fallback 也應該可用
        fallback = viewset.get_fallback_manager()
        self.assertEqual(fallback, mock_fallback)
    
    @override_settings(
        MOCK_LIBRARY_AVAILABLE=False,
        MOCK_FALLBACK_AVAILABLE=True
    )
    @patch('api.views.mixins.library_manager_mixin.create_mock_fallback_manager')
    def test_fallback_when_primary_disabled(self, mock_fallback_factory):
        """測試 Primary 停用時 Fallback 可用"""
        viewset = MockViewSetWithLibrary()
        
        mock_fallback = Mock()
        mock_fallback_factory.return_value = mock_fallback
        
        # Primary 應該返回 None
        primary = viewset.get_manager()
        self.assertIsNone(primary)
        
        # Fallback 應該可用
        fallback = viewset.get_fallback_manager()
        self.assertEqual(fallback, mock_fallback)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
