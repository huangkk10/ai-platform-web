"""
Fallback Logic Mixin
統一三層備用邏輯處理

消除 20+ 個重複的 if-elif-else 判斷
"""

import logging
from typing import Callable, Any, Optional

logger = logging.getLogger(__name__)


class FallbackLogicMixin:
    """
    三層備用邏輯統一處理 Mixin
    
    處理模式：
    1. 優先使用 Library Manager
    2. 其次使用 Fallback Manager
    3. 最後使用緊急本地實現
    
    自動記錄日誌和錯誤處理
    
    使用方式：
        def get_queryset(self):
            return self.execute_with_fallback(
                method_name='get_queryset',
                primary_method=lambda: self._manager.get_queryset_for_user(self.request.user),
                fallback_method=lambda: self._fallback_manager.get_queryset_fallback(self.request.user),
                emergency_method=lambda: Model.objects.filter(user=self.request.user),
                context_name='獲取查詢集'
            )
    """
    
    def execute_with_fallback(
        self,
        method_name: str,
        primary_method: Optional[Callable] = None,
        fallback_method: Optional[Callable] = None,
        emergency_method: Optional[Callable] = None,
        context_name: str = "操作",
        silent_fallback: bool = False,  # 是否靜默降級（不記錄 warning）
    ) -> Any:
        """
        執行帶三層備用的方法調用
        
        Args:
            method_name: 方法名稱（用於日誌）
            primary_method: 主要方法（Library Manager）
            fallback_method: 備用方法（Fallback Manager）
            emergency_method: 緊急方法（本地實現）
            context_name: 上下文名稱（用於日誌）
            silent_fallback: 是否靜默降級
        
        Returns:
            方法執行結果
        """
        # 第一層：Library Manager
        if primary_method:
            try:
                result = primary_method()
                logger.debug(f"✅ {context_name} - 使用 Library Manager: {method_name}")
                return result
            except Exception as e:
                if not silent_fallback:
                    logger.warning(f"⚠️ Library Manager 失敗: {method_name} - {str(e)}")
        
        # 第二層：Fallback Manager
        if fallback_method:
            try:
                result = fallback_method()
                if not silent_fallback:
                    logger.info(f"🔄 {context_name} - 使用 Fallback Manager: {method_name}")
                return result
            except Exception as e:
                if not silent_fallback:
                    logger.warning(f"⚠️ Fallback Manager 失敗: {method_name} - {str(e)}")
        
        # 第三層：緊急本地實現
        if emergency_method:
            try:
                result = emergency_method()
                logger.warning(f"🚨 {context_name} - 使用緊急本地實現: {method_name}")
                return result
            except Exception as e:
                logger.error(f"❌ 緊急實現也失敗: {method_name} - {str(e)}")
                raise
        
        raise RuntimeError(f"所有備用方法都不可用: {method_name}")
    
    def safe_delegate(
        self,
        manager_method: str,
        fallback_method: Optional[str] = None,
        emergency_callable: Optional[Callable] = None,
        context_name: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        簡化版的安全委託方法
        
        自動從 self._manager 和 self._fallback_manager 獲取方法
        
        Args:
            manager_method: Manager 方法名稱（字串）
            fallback_method: Fallback Manager 方法名稱（字串）
            emergency_callable: 緊急備用函數
            context_name: 上下文名稱
            **kwargs: 傳遞給方法的參數
        
        Returns:
            方法執行結果
        """
        if context_name is None:
            context_name = manager_method
        
        # 構建主要方法
        primary = None
        if hasattr(self, '_manager') and self._manager:
            method = getattr(self._manager, manager_method, None)
            if method:
                primary = lambda: method(**kwargs)
        
        # 構建備用方法
        fallback = None
        if fallback_method and hasattr(self, '_fallback_manager') and self._fallback_manager:
            method = getattr(self._fallback_manager, fallback_method, None)
            if method:
                fallback = lambda: method(**kwargs)
        
        return self.execute_with_fallback(
            method_name=manager_method,
            primary_method=primary,
            fallback_method=fallback,
            emergency_method=emergency_callable,
            context_name=context_name
        )
