"""
ViewSet Mixins Module
統一管理所有 ViewSet 共用的 Mixin 類別

包含的 Mixins：
- LibraryManagerMixin: 統一 Library 初始化和可用性檢查
- FallbackLogicMixin: 統一三層備用邏輯處理
- ReadOnlyForUserWriteForAdminMixin: 讀取開放，寫入需管理員
- DelegatedPermissionMixin: 委託給 Library Manager 處理權限
- VectorManagementMixin: 統一向量資料生成和管理
"""

from .library_manager_mixin import LibraryManagerMixin
from .fallback_logic_mixin import FallbackLogicMixin
from .permission_mixin import ReadOnlyForUserWriteForAdminMixin, DelegatedPermissionMixin
from .vector_management_mixin import VectorManagementMixin

__all__ = [
    'LibraryManagerMixin',
    'FallbackLogicMixin',
    'ReadOnlyForUserWriteForAdminMixin',
    'DelegatedPermissionMixin',
    'VectorManagementMixin',
]
