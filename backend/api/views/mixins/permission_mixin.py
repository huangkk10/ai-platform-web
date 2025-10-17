"""
Permission Mixins
統一權限檢查邏輯

消除重複的權限處理代碼
"""

import logging
from rest_framework import permissions

logger = logging.getLogger(__name__)


class ReadOnlyForUserWriteForAdminMixin:
    """
    讀取開放，寫入需要管理員權限
    
    適用於：TestClass, OCRTestClass 等資源
    
    使用方式：
        class MyViewSet(ReadOnlyForUserWriteForAdminMixin, viewsets.ModelViewSet):
            # 不需要實現 get_permissions()
            pass
    """
    
    read_actions = ['list', 'retrieve']
    write_actions = ['create', 'update', 'partial_update', 'destroy']
    
    def get_permissions(self):
        """根據操作類型返回不同權限"""
        if self.action in self.read_actions:
            # 讀取操作：所有認證用戶都可以訪問
            return [permissions.IsAuthenticated()]
        
        # 寫操作檢查管理員權限
        if self.action in self.write_actions:
            user = getattr(self.request, 'user', None)
            if user and not (user.is_staff or user.is_superuser):
                logger.warning(
                    f"非管理員用戶 {user.username} 嘗試執行 {self.action} 操作"
                )
        
        # 預設：需要認證
        return [permissions.IsAuthenticated()]


class DelegatedPermissionMixin:
    """
    委託給 Library Manager 處理權限
    
    適用於：有複雜權限邏輯的 ViewSet
    
    使用方式：
        class MyViewSet(LibraryManagerMixin, DelegatedPermissionMixin, viewsets.ModelViewSet):
            # Manager 會處理權限邏輯
            pass
    """
    
    def get_permissions(self):
        """委託給 Manager 處理權限（如果可用）"""
        # 優先使用 Manager
        if hasattr(self, '_manager') and self._manager:
            try:
                permissions_result = self._manager.get_permissions_for_action(
                    self.action, 
                    self.request.user
                )
                if permissions_result is not None:
                    logger.debug(f"使用 Manager 權限邏輯: {self.action}")
                    return permissions_result
            except Exception as e:
                logger.warning(f"Manager 權限處理失敗: {str(e)}")
        
        # 備用：基本認證
        logger.debug(f"使用預設權限: {self.action}")
        return [permissions.IsAuthenticated()]
