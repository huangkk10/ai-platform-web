"""
Library Manager Mixin
統一管理 Library 初始化和可用性檢查

消除 7 個 ViewSet 中的重複 __init__ 代碼
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class LibraryManagerMixin:
    """
    Library Manager 統一初始化 Mixin
    
    自動處理：
    1. Library 可用性檢查
    2. Manager 實例化
    3. Fallback Manager 初始化
    4. 錯誤日誌記錄
    
    使用方式：
        class MyViewSet(LibraryManagerMixin, viewsets.ModelViewSet):
            library_config = {
                'library_available_flag': 'AUTH_LIBRARY_AVAILABLE',
                'manager_class': 'UserProfileViewSetManager',
                'manager_factory': 'create_user_profile_viewset_manager',
                'fallback_manager_factory': 'create_user_profile_fallback_manager',
                'library_name': 'Auth Library'
            }
    """
    
    library_config: Optional[Dict[str, Any]] = None  # 子類必須定義
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._manager = None
        self._fallback_manager = None
        
        if self.library_config:
            self._initialize_library_managers()
    
    def _initialize_library_managers(self):
        """初始化 Library Managers"""
        config = self.library_config
        library_name = config.get('library_name', 'Unknown Library')
        
        # 檢查 Library 是否可用
        library_flag_name = config.get('library_available_flag')
        if not library_flag_name:
            logger.warning(f"{library_name}: 未指定 library_available_flag")
            return
        
        # 從 ViewSet 類別的 module 獲取 flag（正確的 scope）
        viewset_module = self.__class__.__module__
        import sys
        module = sys.modules.get(viewset_module)
        
        library_available = getattr(module, library_flag_name, False) if module else False
        
        if not library_available:
            logger.warning(f"{library_name} 不可用，將使用備用實現")
            # 不要 return！仍然需要初始化 fallback manager
        else:
            # 只有當 Library 可用時才初始化主 Manager
            manager_class_name = config.get('manager_class')
            manager_factory_name = config.get('manager_factory')
            
            if manager_factory_name:
                manager_factory = getattr(module, manager_factory_name, None) if module else None
                if manager_factory:
                    try:
                        self._manager = manager_factory()
                        logger.info(f"✅ {library_name} Manager 初始化成功 (工廠方法)")
                    except Exception as e:
                        logger.error(f"❌ {library_name} Manager 工廠方法失敗: {str(e)}")
                else:
                    logger.warning(f"⚠️ {library_name} Manager 工廠方法 '{manager_factory_name}' 不可用")
            elif manager_class_name:
                manager_class = getattr(module, manager_class_name, None) if module else None
                if manager_class:
                    try:
                        self._manager = manager_class()
                        logger.info(f"✅ {library_name} Manager 初始化成功 (直接實例化)")
                    except Exception as e:
                        logger.error(f"❌ {library_name} Manager 實例化失敗: {str(e)}")
                else:
                    logger.warning(f"⚠️ {library_name} Manager 類別 '{manager_class_name}' 不可用")
        
        # 總是嘗試初始化 Fallback Manager (無論主 Library 是否可用)
        fallback_factory_name = config.get('fallback_manager_factory')
        if fallback_factory_name:
            fallback_factory = getattr(module, fallback_factory_name, None) if module else None
            if fallback_factory:
                try:
                    self._fallback_manager = fallback_factory()
                    logger.info(f"✅ {library_name} Fallback Manager 初始化成功")
                except Exception as e:
                    logger.error(f"❌ {library_name} Fallback Manager 失敗: {str(e)}")
            else:
                logger.warning(f"⚠️ {library_name} Fallback Manager 工廠方法 '{fallback_factory_name}' 不可用 in module {viewset_module}")
    
    def has_manager(self) -> bool:
        """檢查是否有可用的 Manager"""
        return self._manager is not None
    
    def has_fallback_manager(self) -> bool:
        """檢查是否有可用的 Fallback Manager"""
        return self._fallback_manager is not None
    
    def get_manager(self):
        """獲取主 Manager（如果可用）"""
        return self._manager
    
    def get_fallback_manager(self):
        """獲取 Fallback Manager（如果可用）"""
        return self._fallback_manager
