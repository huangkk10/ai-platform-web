#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
專案配置載入器
從 config/settings.yaml 讀取專案配置
"""

import os
import yaml
from typing import Dict, Any, Optional
from pathlib import Path


class ConfigLoader:
    """配置載入器類"""
    
    _instance = None
    _config = None
    
    def __new__(cls):
        """單例模式確保只有一個配置實例"""
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._config is None:
            self.load_config()
    
    def load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        載入配置文件
        
        Args:
            config_path: 配置文件路徑，如果為 None 則使用預設路徑
            
        Returns:
            Dict: 配置字典
        """
        if config_path is None:
            # 預設配置文件路徑
            project_root = Path(__file__).parent.parent
            config_path = project_root / "config" / "settings.yaml"
        
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                self._config = yaml.safe_load(file)
            
            print(f"✅ 配置載入成功: {config_path}")
            return self._config
            
        except FileNotFoundError:
            print(f"❌ 配置文件不存在: {config_path}")
            # 使用預設配置
            self._config = self._get_default_config()
            return self._config
            
        except yaml.YAMLError as e:
            print(f"❌ YAML 解析錯誤: {e}")
            # 使用預設配置
            self._config = self._get_default_config()
            return self._config
            
        except Exception as e:
            print(f"❌ 載入配置時發生錯誤: {e}")
            # 使用預設配置
            self._config = self._get_default_config()
            return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        獲取預設配置
        
        Returns:
            Dict: 預設配置字典
        """
        return {
            "ai_server": {
                "ai_pc_ip": "10.10.172.5"  # 預設 IP
            },
            "database": {},
            "api": {
                "timeout": 60
            },
            "frontend": {},
            "logging": {
                "level": "INFO"
            },
            "version": "1.0.0"
        }
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """
        獲取配置值，支持點號路徑
        
        Args:
            key_path: 配置鍵路徑，如 'ai_server.ai_pc_ip'
            default: 預設值
            
        Returns:
            配置值
        """
        if self._config is None:
            self.load_config()
        
        keys = key_path.split('.')
        value = self._config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_ai_pc_ip(self) -> str:
        """
        獲取 AI PC IP 地址
        
        Returns:
            str: IP 地址
        """
        return self.get('ai_server.ai_pc_ip', '10.10.172.5')
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        獲取完整配置
        
        Returns:
            Dict: 完整配置字典
        """
        if self._config is None:
            self.load_config()
        return self._config.copy()
    
    def reload_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """
        重新載入配置
        
        Args:
            config_path: 配置文件路徑
            
        Returns:
            Dict: 配置字典
        """
        self._config = None
        return self.load_config(config_path)
    
    def update_config(self, key_path: str, value: Any) -> bool:
        """
        更新配置值（僅在記憶體中，不寫入文件）
        
        Args:
            key_path: 配置鍵路徑
            value: 新值
            
        Returns:
            bool: 是否更新成功
        """
        if self._config is None:
            self.load_config()
        
        keys = key_path.split('.')
        config = self._config
        
        # 導航到目標位置
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # 設置值
        config[keys[-1]] = value
        return True


# 全域配置實例
config_loader = ConfigLoader()


# 便利函數
def get_config(key_path: str, default: Any = None) -> Any:
    """
    獲取配置值的便利函數
    
    Args:
        key_path: 配置鍵路徑
        default: 預設值
        
    Returns:
        配置值
    """
    return config_loader.get(key_path, default)


def get_ai_pc_ip() -> str:
    """
    獲取 AI PC IP 地址的便利函數
    
    Returns:
        str: IP 地址
    """
    return config_loader.get_ai_pc_ip()


def reload_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    重新載入配置的便利函數
    
    Args:
        config_path: 配置文件路徑
        
    Returns:
        Dict: 配置字典
    """
    return config_loader.reload_config(config_path)


def get_full_config() -> Dict[str, Any]:
    """
    獲取完整配置的便利函數
    
    Returns:
        Dict: 完整配置字典
    """
    return config_loader.get_full_config()


# 環境變數支持
def get_config_with_env_override(key_path: str, env_var_name: str, default: Any = None) -> Any:
    """
    獲取配置值，支持環境變數覆蓋
    
    Args:
        key_path: 配置鍵路徑
        env_var_name: 環境變數名稱
        default: 預設值
        
    Returns:
        配置值
    """
    # 首先檢查環境變數
    env_value = os.getenv(env_var_name)
    if env_value is not None:
        return env_value
    
    # 如果沒有環境變數，使用配置文件
    return get_config(key_path, default)


def get_ai_pc_ip_with_env() -> str:
    """
    獲取 AI PC IP，支持環境變數 AI_PC_IP 覆蓋
    
    Returns:
        str: IP 地址
    """
    return get_config_with_env_override('ai_server.ai_pc_ip', 'AI_PC_IP', '10.10.172.5')


if __name__ == "__main__":
    # 測試配置載入
    print("=== 配置載入測試 ===")
    print(f"AI PC IP: {get_ai_pc_ip()}")
    print(f"完整配置: {get_full_config()}")
    print(f"支持環境變數的 AI PC IP: {get_ai_pc_ip_with_env()}")