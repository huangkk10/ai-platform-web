"""
VectorManagementMixin 單元測試

測試向量自動管理功能（生成、更新、刪除）
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../backend'))

from api.views.mixins import VectorManagementMixin


class MockModel:
    """Mock Django Model"""
    def __init__(self, id=1, title="Test", content="Content"):
        self.id = id
        self.title = title
        self.content = content


class MockViewSetWithVector(VectorManagementMixin):
    """測試用的 Mock ViewSet"""
    
    vector_config = {
        'source_table': 'test_table',
        'content_fields': ['title', 'content'],
        'use_1024_table': True
    }


class MockViewSetInvalidVector(VectorManagementMixin):
    """配置錯誤的 Mock ViewSet"""
    
    vector_config = {
        'source_table': 'test_table'
        # 缺少 content_fields
    }


class TestVectorManagementMixin(TestCase):
    """VectorManagementMixin 單元測試類"""
    
    def setUp(self):
        """設置測試環境"""
        self.viewset = MockViewSetWithVector()
        self.viewset_invalid = MockViewSetInvalidVector()
        self.mock_instance = MockModel(id=1, title="Test Title", content="Test Content")
    
    # ========================================
    # 測試 generate_vector_for_instance()
    # ========================================
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_generate_vector_success(self, mock_generate):
        """測試成功生成向量"""
        mock_generate.return_value = True
        
        result = self.viewset.generate_vector_for_instance(self.mock_instance)
        
        # 驗證調用正確
        mock_generate.assert_called_once()
        call_args = mock_generate.call_args
        
        # 驗證參數
        self.assertEqual(call_args[1]['source_table'], 'test_table')
        self.assertEqual(call_args[1]['source_id'], 1)
        self.assertIn('Test Title', call_args[1]['content'])
        self.assertIn('Test Content', call_args[1]['content'])
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_generate_vector_with_multiple_fields(self, mock_generate):
        """測試多個內容字段的處理"""
        mock_generate.return_value = True
        
        instance = MockModel(id=2, title="Title", content="Content")
        self.viewset.generate_vector_for_instance(instance)
        
        call_args = mock_generate.call_args[1]
        content = call_args['content']
        
        # 驗證所有字段都被包含
        self.assertIn('Title', content)
        self.assertIn('Content', content)
    
    def test_generate_vector_without_config(self):
        """測試沒有配置時的處理"""
        class ViewSetNoConfig(VectorManagementMixin):
            pass
        
        viewset = ViewSetNoConfig()
        
        # 應該不會崩潰
        result = viewset.generate_vector_for_instance(self.mock_instance)
        # 根據實現，可能返回 False 或 None
    
    def test_generate_vector_with_invalid_config(self):
        """測試配置錯誤時的處理"""
        # 應該不會崩潰
        result = self.viewset_invalid.generate_vector_for_instance(self.mock_instance)
        # 根據實現，應該優雅地失敗
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_generate_vector_handles_missing_fields(self, mock_generate):
        """測試實例缺少字段時的處理"""
        mock_generate.return_value = True
        
        # 創建缺少 content 字段的實例
        class IncompleteModel:
            def __init__(self):
                self.id = 1
                self.title = "Test"
                # 沒有 content 字段
        
        instance = IncompleteModel()
        
        # 應該仍然能生成向量（使用可用的字段）
        result = self.viewset.generate_vector_for_instance(instance)
        
        # 驗證至少使用了 title
        if mock_generate.called:
            call_args = mock_generate.call_args[1]
            self.assertIn('Test', call_args['content'])
    
    # ========================================
    # 測試 update_vector_for_instance()
    # ========================================
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_update_vector_success(self, mock_generate, mock_objects):
        """測試成功更新向量"""
        # Mock 現有向量
        mock_vector = Mock()
        mock_objects.filter.return_value.first.return_value = mock_vector
        mock_objects.filter.return_value.delete.return_value = (1, {})
        
        mock_generate.return_value = True
        
        result = self.viewset.update_vector_for_instance(self.mock_instance)
        
        # 驗證刪除舊向量
        mock_objects.filter.assert_called()
        
        # 驗證生成新向量
        mock_generate.assert_called_once()
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_update_vector_when_not_exists(self, mock_generate, mock_objects):
        """測試向量不存在時的更新（相當於創建）"""
        # Mock 不存在的向量
        mock_objects.filter.return_value.first.return_value = None
        mock_generate.return_value = True
        
        result = self.viewset.update_vector_for_instance(self.mock_instance)
        
        # 仍然應該生成新向量
        mock_generate.assert_called_once()
    
    # ========================================
    # 測試 delete_vector_for_instance()
    # ========================================
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    def test_delete_vector_success(self, mock_objects):
        """測試成功刪除向量"""
        mock_objects.filter.return_value.delete.return_value = (1, {})
        
        result = self.viewset.delete_vector_for_instance(self.mock_instance)
        
        # 驗證調用正確
        mock_objects.filter.assert_called_once()
        filter_args = mock_objects.filter.call_args[1]
        
        self.assertEqual(filter_args['source_table'], 'test_table')
        self.assertEqual(filter_args['source_id'], 1)
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    def test_delete_vector_when_not_exists(self, mock_objects):
        """測試刪除不存在的向量"""
        mock_objects.filter.return_value.delete.return_value = (0, {})
        
        # 應該不會崩潰
        result = self.viewset.delete_vector_for_instance(self.mock_instance)
    
    # ========================================
    # 測試 1024 維向量配置
    # ========================================
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_use_1024_table_true(self, mock_generate):
        """測試使用 1024 維向量表"""
        self.viewset.vector_config['use_1024_table'] = True
        mock_generate.return_value = True
        
        self.viewset.generate_vector_for_instance(self.mock_instance)
        
        # 驗證使用 1024 維函數
        mock_generate.assert_called_once()
    
    @patch('library.vector_database.utils.generate_and_store_embedding')
    def test_use_1024_table_false(self, mock_generate):
        """測試使用舊版向量表"""
        viewset = MockViewSetWithVector()
        viewset.vector_config = {
            'source_table': 'test_table',
            'content_fields': ['title', 'content'],
            'use_1024_table': False
        }
        mock_generate.return_value = True
        
        viewset.generate_vector_for_instance(self.mock_instance)
        
        # 驗證使用舊版函數
        mock_generate.assert_called_once()
    
    # ========================================
    # 測試異常處理
    # ========================================
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_generate_vector_handles_exception(self, mock_generate):
        """測試生成向量時的異常處理"""
        mock_generate.side_effect = Exception("Vector generation error")
        
        # 應該不會崩潰
        result = self.viewset.generate_vector_for_instance(self.mock_instance)
        
        # 根據實現，應該返回 False 或記錄日誌
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    def test_delete_vector_handles_exception(self, mock_objects):
        """測試刪除向量時的異常處理"""
        mock_objects.filter.side_effect = Exception("Database error")
        
        # 應該不會崩潰
        result = self.viewset.delete_vector_for_instance(self.mock_instance)
    
    # ========================================
    # 測試日誌記錄
    # ========================================
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    @patch('api.views.mixins.vector_management_mixin.logger')
    def test_logging_on_vector_generation(self, mock_logger, mock_generate):
        """測試生成向量時的日誌"""
        mock_generate.return_value = True
        
        self.viewset.generate_vector_for_instance(self.mock_instance)
        
        # 驗證有日誌記錄
        self.assertTrue(
            mock_logger.info.called or 
            mock_logger.debug.called or 
            mock_logger.error.called
        )
    
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    @patch('api.views.mixins.vector_management_mixin.logger')
    def test_logging_on_vector_deletion(self, mock_logger, mock_objects):
        """測試刪除向量時的日誌"""
        mock_objects.filter.return_value.delete.return_value = (1, {})
        
        self.viewset.delete_vector_for_instance(self.mock_instance)
        
        # 驗證有日誌記錄
        self.assertTrue(
            mock_logger.info.called or 
            mock_logger.debug.called
        )


class TestVectorManagementMixinIntegration(TestCase):
    """VectorManagementMixin 整合測試"""
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    @patch('library.vector_database.models.DocumentEmbedding1024.objects')
    def test_full_vector_lifecycle(self, mock_objects, mock_generate):
        """測試完整的向量生命週期（創建、更新、刪除）"""
        viewset = MockViewSetWithVector()
        instance = MockModel(id=1, title="Title", content="Content")
        
        # 1. 創建向量
        mock_generate.return_value = True
        result1 = viewset.generate_vector_for_instance(instance)
        mock_generate.assert_called()
        
        # 2. 更新向量
        mock_objects.filter.return_value.first.return_value = Mock()
        mock_objects.filter.return_value.delete.return_value = (1, {})
        mock_generate.reset_mock()
        
        result2 = viewset.update_vector_for_instance(instance)
        mock_generate.assert_called()
        
        # 3. 刪除向量
        result3 = viewset.delete_vector_for_instance(instance)
        mock_objects.filter.assert_called()
    
    @patch('library.vector_database.utils.generate_and_store_embedding_1024')
    def test_batch_vector_generation(self, mock_generate):
        """測試批量生成向量"""
        viewset = MockViewSetWithVector()
        mock_generate.return_value = True
        
        instances = [
            MockModel(id=i, title=f"Title {i}", content=f"Content {i}")
            for i in range(1, 6)
        ]
        
        for instance in instances:
            viewset.generate_vector_for_instance(instance)
        
        # 驗證每個實例都生成了向量
        self.assertEqual(mock_generate.call_count, 5)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
