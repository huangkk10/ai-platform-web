"""
FallbackLogicMixin 單元測試

測試三層備用邏輯（Primary → Fallback → Emergency）
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from api.views.mixins import FallbackLogicMixin, LibraryManagerMixin


class MockViewSetWithFallback(LibraryManagerMixin, FallbackLogicMixin):
    """測試用的 Mock ViewSet"""
    
    library_config = {
        'library_available_flag': 'MOCK_LIBRARY_AVAILABLE',
        'manager_factory': 'create_mock_manager',
        'library_name': 'Mock Library',
        'fallback_available_flag': 'MOCK_FALLBACK_AVAILABLE',
        'fallback_manager_factory': 'create_mock_fallback_manager',
        'fallback_library_name': 'Mock Fallback Library'
    }


class TestFallbackLogicMixin(TestCase):
    """FallbackLogicMixin 單元測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.viewset = MockViewSetWithFallback()
    
    # ========================================
    # 測試 safe_delegate() - Primary 成功場景
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_safe_delegate_primary_success(self, mock_factory):
        """測試 Primary Manager 成功執行"""
        # Mock Primary Manager
        mock_manager = Mock()
        mock_manager.test_method = Mock(return_value='primary_result')
        mock_factory.return_value = mock_manager
        
        # Mock Fallback 和 Emergency
        fallback_callable = Mock(return_value='fallback_result')
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證結果
        self.assertEqual(result, 'primary_result')
        
        # 驗證 Primary 被調用
        mock_manager.test_method.assert_called_once()
        
        # 驗證 Fallback 和 Emergency 沒有被調用
        fallback_callable.assert_not_called()
        emergency_callable.assert_not_called()
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_safe_delegate_primary_with_args(self, mock_factory):
        """測試 Primary Manager 接收參數"""
        mock_manager = Mock()
        mock_manager.test_method = Mock(return_value='result')
        mock_factory.return_value = mock_manager
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            method_args=['arg1', 'arg2'],
            method_kwargs={'key': 'value'},
            emergency_callable=lambda: 'emergency'
        )
        
        # 驗證參數傳遞正確
        mock_manager.test_method.assert_called_once_with('arg1', 'arg2', key='value')
    
    # ========================================
    # 測試 safe_delegate() - Fallback 場景
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_safe_delegate_fallback_when_primary_fails(self, mock_factory):
        """測試 Primary 失敗時使用 Fallback"""
        # Mock Primary Manager (會拋出異常)
        mock_manager = Mock()
        mock_manager.test_method = Mock(side_effect=Exception("Primary error"))
        mock_factory.return_value = mock_manager
        
        # Mock Fallback
        fallback_callable = Mock(return_value='fallback_result')
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證使用了 Fallback
        self.assertEqual(result, 'fallback_result')
        fallback_callable.assert_called_once()
        emergency_callable.assert_not_called()
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=False)
    def test_safe_delegate_fallback_when_primary_disabled(self):
        """測試 Primary 停用時直接使用 Fallback"""
        fallback_callable = Mock(return_value='fallback_result')
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證使用了 Fallback
        self.assertEqual(result, 'fallback_result')
        fallback_callable.assert_called_once()
        emergency_callable.assert_not_called()
    
    # ========================================
    # 測試 safe_delegate() - Emergency 場景
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_safe_delegate_emergency_when_all_fail(self, mock_factory):
        """測試 Primary 和 Fallback 都失敗時使用 Emergency"""
        # Mock Primary Manager (失敗)
        mock_manager = Mock()
        mock_manager.test_method = Mock(side_effect=Exception("Primary error"))
        mock_factory.return_value = mock_manager
        
        # Mock Fallback (也失敗)
        fallback_callable = Mock(side_effect=Exception("Fallback error"))
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證使用了 Emergency
        self.assertEqual(result, 'emergency_result')
        fallback_callable.assert_called_once()
        emergency_callable.assert_called_once()
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=False)
    def test_safe_delegate_emergency_when_fallback_fails(self):
        """測試 Fallback 失敗時使用 Emergency"""
        fallback_callable = Mock(side_effect=Exception("Fallback error"))
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證使用了 Emergency
        self.assertEqual(result, 'emergency_result')
        emergency_callable.assert_called_once()
    
    def test_safe_delegate_emergency_always_succeeds(self):
        """測試 Emergency 必須總是成功"""
        emergency_callable = Mock(return_value='safe_result')
        
        # 不提供 Primary 和 Fallback
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            emergency_callable=emergency_callable
        )
        
        self.assertEqual(result, 'safe_result')
        emergency_callable.assert_called_once()
    
    # ========================================
    # 測試 execute_with_fallback()
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_execute_with_fallback_primary_success(self, mock_factory):
        """測試 execute_with_fallback 使用 Primary"""
        mock_manager = Mock()
        mock_manager.execute = Mock(return_value='primary_result')
        mock_factory.return_value = mock_manager
        
        primary_func = lambda: mock_manager.execute()
        fallback_func = Mock(return_value='fallback_result')
        
        result = self.viewset.execute_with_fallback(
            primary_callable=primary_func,
            fallback_callable=fallback_func
        )
        
        self.assertEqual(result, 'primary_result')
        fallback_func.assert_not_called()
    
    def test_execute_with_fallback_uses_fallback(self):
        """測試 execute_with_fallback 使用 Fallback"""
        primary_func = Mock(side_effect=Exception("Primary error"))
        fallback_func = Mock(return_value='fallback_result')
        
        result = self.viewset.execute_with_fallback(
            primary_callable=primary_func,
            fallback_callable=fallback_func
        )
        
        self.assertEqual(result, 'fallback_result')
        primary_func.assert_called_once()
        fallback_func.assert_called_once()
    
    # ========================================
    # 測試異常處理
    # ========================================
    
    def test_safe_delegate_handles_none_emergency(self):
        """測試沒有 Emergency 時的處理"""
        # 應該返回 None 而不是崩潰
        result = self.viewset.safe_delegate(
            manager_method='test_method'
        )
        
        # 根據實現，可能返回 None 或拋出異常
        # 這裡假設返回 None
        self.assertIsNone(result)
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_safe_delegate_handles_method_not_found(self, mock_factory):
        """測試方法不存在時的處理"""
        mock_manager = Mock()
        # 不設置 test_method，模擬方法不存在
        mock_manager.test_method = None
        mock_factory.return_value = mock_manager
        
        emergency_callable = Mock(return_value='emergency_result')
        
        result = self.viewset.safe_delegate(
            manager_method='test_method',
            emergency_callable=emergency_callable
        )
        
        # 應該使用 Emergency
        self.assertEqual(result, 'emergency_result')
    
    # ========================================
    # 測試日誌記錄
    # ========================================
    
    @override_settings(MOCK_LIBRARY_AVAILABLE=True)
    @patch('api.views.mixins.fallback_logic_mixin.logger')
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    def test_logging_on_primary_success(self, mock_factory, mock_logger):
        """測試 Primary 成功時的日誌"""
        mock_manager = Mock()
        mock_manager.test_method = Mock(return_value='result')
        mock_factory.return_value = mock_manager
        
        self.viewset.safe_delegate(
            manager_method='test_method',
            emergency_callable=lambda: 'emergency'
        )
        
        # 驗證有成功日誌
        self.assertTrue(mock_logger.info.called or mock_logger.debug.called)
    
    @patch('api.views.mixins.fallback_logic_mixin.logger')
    def test_logging_on_fallback_usage(self, mock_logger):
        """測試使用 Fallback 時的日誌"""
        fallback_callable = Mock(return_value='fallback_result')
        
        self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=lambda: 'emergency'
        )
        
        # 驗證有 Fallback 警告日誌
        self.assertTrue(mock_logger.warning.called or mock_logger.info.called)
    
    @patch('api.views.mixins.fallback_logic_mixin.logger')
    def test_logging_on_emergency_usage(self, mock_logger):
        """測試使用 Emergency 時的日誌"""
        fallback_callable = Mock(side_effect=Exception("Fallback error"))
        emergency_callable = Mock(return_value='emergency_result')
        
        self.viewset.safe_delegate(
            manager_method='test_method',
            fallback_callable=fallback_callable,
            emergency_callable=emergency_callable
        )
        
        # 驗證有 Emergency 錯誤日誌
        self.assertTrue(mock_logger.error.called or mock_logger.warning.called)


class TestFallbackLogicMixinIntegration(TestCase):
    """FallbackLogicMixin 整合測試"""
    
    @override_settings(
        MOCK_LIBRARY_AVAILABLE=True,
        MOCK_FALLBACK_AVAILABLE=True
    )
    @patch('api.views.mixins.library_manager_mixin.create_mock_manager')
    @patch('api.views.mixins.library_manager_mixin.create_mock_fallback_manager')
    def test_three_tier_fallback_full_flow(
        self, 
        mock_fallback_factory, 
        mock_primary_factory
    ):
        """測試完整的三層備用邏輯流程"""
        viewset = MockViewSetWithFallback()
        
        # Scenario 1: Primary 成功
        mock_primary = Mock()
        mock_primary.method1 = Mock(return_value='primary_result')
        mock_primary_factory.return_value = mock_primary
        
        result1 = viewset.safe_delegate(
            manager_method='method1',
            emergency_callable=lambda: 'emergency'
        )
        self.assertEqual(result1, 'primary_result')
        
        # Scenario 2: Primary 失敗，Fallback 成功
        mock_primary.method2 = Mock(side_effect=Exception("Error"))
        mock_fallback = Mock()
        mock_fallback.method2 = Mock(return_value='fallback_result')
        mock_fallback_factory.return_value = mock_fallback
        
        result2 = viewset.safe_delegate(
            manager_method='method2',
            fallback_callable=lambda: mock_fallback.method2(),
            emergency_callable=lambda: 'emergency'
        )
        self.assertEqual(result2, 'fallback_result')
        
        # Scenario 3: 全部失敗，使用 Emergency
        result3 = viewset.safe_delegate(
            manager_method='method3',
            fallback_callable=lambda: (_ for _ in ()).throw(Exception("Fallback error")),
            emergency_callable=lambda: 'emergency_result'
        )
        self.assertEqual(result3, 'emergency_result')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
