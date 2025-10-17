"""
快速冒煙測試 - 驗證測試框架正常工作
"""
from django.test import TestCase
from api.views.mixins import (
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    ReadOnlyForUserWriteForAdminMixin
)


class QuickSmokeTest(TestCase):
    """快速冒煙測試 - 驗證所有 Mixin 可以導入和實例化"""
    
    def test_all_mixins_importable(self):
        """測試所有 Mixin 可以導入"""
        self.assertIsNotNone(LibraryManagerMixin)
        self.assertIsNotNone(FallbackLogicMixin)
        self.assertIsNotNone(VectorManagementMixin)
        self.assertIsNotNone(ReadOnlyForUserWriteForAdminMixin)
    
    def test_library_manager_mixin_exists(self):
        """測試 LibraryManagerMixin 有正確的方法"""
        self.assertTrue(hasattr(LibraryManagerMixin, 'has_manager'))
        self.assertTrue(hasattr(LibraryManagerMixin, 'get_manager'))
        self.assertTrue(hasattr(LibraryManagerMixin, 'has_fallback_manager'))
        self.assertTrue(hasattr(LibraryManagerMixin, 'get_fallback_manager'))
    
    def test_fallback_logic_mixin_exists(self):
        """測試 FallbackLogicMixin 有正確的方法"""
        self.assertTrue(hasattr(FallbackLogicMixin, 'safe_delegate'))
        self.assertTrue(hasattr(FallbackLogicMixin, 'execute_with_fallback'))
    
    def test_vector_management_mixin_exists(self):
        """測試 VectorManagementMixin 有正確的方法"""
        self.assertTrue(hasattr(VectorManagementMixin, 'generate_vector_for_instance'))
        self.assertTrue(hasattr(VectorManagementMixin, 'update_vector_for_instance'))
        self.assertTrue(hasattr(VectorManagementMixin, 'delete_vector_for_instance'))
    
    def test_permission_mixin_exists(self):
        """測試 PermissionMixin 有正確的方法"""
        self.assertTrue(hasattr(ReadOnlyForUserWriteForAdminMixin, 'get_permissions'))
    
    def test_viewsets_importable(self):
        """測試所有 ViewSet 可以導入"""
        from api.views import (
            UserViewSet,
            UserProfileViewSet,
            ProjectViewSet,
            TaskViewSet,
            KnowIssueViewSet,
            RVTGuideViewSet,
            ProtocolGuideViewSet,
            TestClassViewSet,
            OCRTestClassViewSet,
            OCRStorageBenchmarkViewSet,
            ContentImageViewSet
        )
        
        # 驗證所有 ViewSet 都存在
        self.assertIsNotNone(UserViewSet)
        self.assertIsNotNone(UserProfileViewSet)
        self.assertIsNotNone(ProjectViewSet)
        self.assertIsNotNone(TaskViewSet)
        self.assertIsNotNone(KnowIssueViewSet)
        self.assertIsNotNone(RVTGuideViewSet)
        self.assertIsNotNone(ProtocolGuideViewSet)
        self.assertIsNotNone(TestClassViewSet)
        self.assertIsNotNone(OCRTestClassViewSet)
        self.assertIsNotNone(OCRStorageBenchmarkViewSet)
        self.assertIsNotNone(ContentImageViewSet)
    
    def test_monitoring_functions_importable(self):
        """測試監控函數可以導入"""
        from api.views import (
            system_logs,
            simple_system_status,
            basic_system_status
        )
        
        self.assertIsNotNone(system_logs)
        self.assertIsNotNone(simple_system_status)
        self.assertIsNotNone(basic_system_status)
    
    def test_knowissue_viewset_has_mixins(self):
        """測試 KnowIssueViewSet 使用了正確的 Mixins"""
        from api.views.viewsets.knowledge_viewsets import KnowIssueViewSet
        
        # 檢查繼承鏈
        mro = [cls.__name__ for cls in KnowIssueViewSet.__mro__]
        
        self.assertIn('LibraryManagerMixin', mro)
        self.assertIn('FallbackLogicMixin', mro)
        self.assertIn('VectorManagementMixin', mro)
    
    def test_knowissue_viewset_has_configs(self):
        """測試 KnowIssueViewSet 有正確的配置"""
        from api.views.viewsets.knowledge_viewsets import KnowIssueViewSet
        
        self.assertTrue(hasattr(KnowIssueViewSet, 'library_config'))
        self.assertTrue(hasattr(KnowIssueViewSet, 'vector_config'))
        
        # 驗證配置內容
        self.assertIn('library_name', KnowIssueViewSet.library_config)
        self.assertIn('source_table', KnowIssueViewSet.vector_config)
