"""
SAF Authentication Manager
==========================

SAF API 認證管理器，負責管理 SAF API 的認證資訊。

SAF API 使用 Header 認證方式：
- Authorization: {user_id}
- Authorization-Name: {user_name}

作者：AI Platform Team
創建日期：2025-12-04
"""

import logging
from typing import Dict, Optional
from django.conf import settings


logger = logging.getLogger(__name__)


class SAFAuthManager:
    """SAF API 認證管理器"""
    
    # 預設認證資訊
    DEFAULT_USER_ID = "150"
    DEFAULT_USER_NAME = "Chunwei.Huang"
    
    def __init__(
        self,
        user_id: Optional[str] = None,
        user_name: Optional[str] = None
    ):
        """
        初始化認證管理器
        
        Args:
            user_id: SAF 使用者 ID
            user_name: SAF 使用者名稱
        """
        # 優先順序：參數 > settings > 環境變數 > 預設值
        self.user_id = user_id or self._get_config_value(
            'SAF_API_USER_ID',
            self.DEFAULT_USER_ID
        )
        self.user_name = user_name or self._get_config_value(
            'SAF_API_USER_NAME',
            self.DEFAULT_USER_NAME
        )
        
        logger.debug(f"SAF Auth Manager 初始化: user_id={self.user_id}, user_name={self.user_name}")
    
    def _get_config_value(self, key: str, default: str) -> str:
        """
        從配置中獲取值
        
        Args:
            key: 配置鍵名
            default: 預設值
            
        Returns:
            配置值
        """
        import os
        
        # 嘗試從 Django settings 獲取
        if hasattr(settings, key):
            return getattr(settings, key)
        
        # 嘗試從環境變數獲取
        env_value = os.environ.get(key)
        if env_value:
            return env_value
        
        # 返回預設值
        return default
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        獲取認證 headers
        
        Returns:
            包含認證資訊的 headers 字典
        """
        return {
            "Authorization": self.user_id,
            "Authorization-Name": self.user_name
        }
    
    def update_credentials(self, user_id: str, user_name: str) -> None:
        """
        更新認證資訊
        
        Args:
            user_id: 新的使用者 ID
            user_name: 新的使用者名稱
        """
        self.user_id = user_id
        self.user_name = user_name
        logger.info(f"SAF 認證資訊已更新: user_id={user_id}")
    
    def validate_credentials(self) -> bool:
        """
        驗證認證資訊是否有效
        
        Returns:
            認證資訊是否有效
        """
        if not self.user_id or not self.user_name:
            return False
        
        # 基本驗證：user_id 應該是數字
        try:
            int(self.user_id)
            return True
        except ValueError:
            return False
    
    def get_credentials_info(self) -> Dict[str, str]:
        """
        獲取認證資訊（用於日誌和調試）
        
        Returns:
            認證資訊字典（隱藏敏感部分）
        """
        return {
            "user_id": self.user_id,
            "user_name": self.user_name[:3] + "***" if len(self.user_name) > 3 else "***"
        }
