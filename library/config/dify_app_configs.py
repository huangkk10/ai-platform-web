#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 應用配置管理
維護各種 Dify 應用的 API 配置信息
"""

import os
from typing import Dict, Optional
from .dify_config import ChatConfig, get_chat_config


class DifyAppConfigs:
    """Dify 應用配置管理器"""
    
    # Protocol Known Issue System 工作室配置
    PROTOCOL_KNOWN_ISSUE_SYSTEM = {
        'api_url': 'http://10.10.172.5/v1/chat-messages',
        'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
        'base_url': 'http://10.10.172.5',
        'app_name': 'Protocol Known Issue System',
        'workspace': 'Protocol_known_issue_system',
        'description': 'Dify Chat 應用，用於查詢 Know Issue 知識庫',
        'features': ['知識庫查詢', '員工資訊', 'Know Issue 管理'],
        'timeout': 60,
        'response_mode': 'blocking'
    }
    
    # 其他應用配置可以在此添加
    # 例如：
    # OTHER_APP_CONFIG = {
    #     'api_url': 'http://...',
    #     'api_key': 'app-...',
    #     ...
    # }
    
    @classmethod
    def get_protocol_known_issue_config(cls) -> Dict[str, str]:
        """
        獲取 Protocol Known Issue System 配置
        
        Returns:
            Dict: 應用配置
        """
        config = cls.PROTOCOL_KNOWN_ISSUE_SYSTEM.copy()
        
        # 支援環境變數覆蓋
        env_overrides = {
            'DIFY_PROTOCOL_API_URL': 'api_url',
            'DIFY_PROTOCOL_API_KEY': 'api_key',
            'DIFY_PROTOCOL_BASE_URL': 'base_url',
            'DIFY_PROTOCOL_TIMEOUT': 'timeout'
        }
        
        for env_key, config_key in env_overrides.items():
            env_value = os.getenv(env_key)
            if env_value:
                if config_key == 'timeout':
                    config[config_key] = int(env_value)
                else:
                    config[config_key] = env_value
        
        return config
    
    @classmethod
    def create_protocol_chat_client(cls):
        """
        創建 Protocol Known Issue System 的 Chat 客戶端
        
        Returns:
            DifyChatClient: 配置好的客戶端
        """
        from ..dify_integration.chat_client import create_chat_client
        
        config = cls.get_protocol_known_issue_config()
        return create_chat_client(
            api_url=config['api_url'],
            api_key=config['api_key'],
            base_url=config['base_url']
        )
    
    @classmethod
    def get_all_app_configs(cls) -> Dict[str, Dict]:
        """
        獲取所有應用配置
        
        Returns:
            Dict: 所有應用配置的字典
        """
        return {
            'protocol_known_issue_system': cls.get_protocol_known_issue_config(),
            # 其他應用配置
        }
    
    @classmethod
    def validate_config(cls, config_name: str) -> bool:
        """
        驗證配置是否有效
        
        Args:
            config_name: 配置名稱
            
        Returns:
            bool: 配置是否有效
        """
        if config_name == 'protocol_known_issue_system':
            config = cls.get_protocol_known_issue_config()
            required_keys = ['api_url', 'api_key', 'base_url']
            
            for key in required_keys:
                if not config.get(key):
                    raise ValueError(f"Missing required config key: {key}")
            
            # 驗證 API Key 格式
            if not config['api_key'].startswith('app-'):
                raise ValueError("Invalid API key format. Must start with 'app-'")
            
            return True
        
        raise ValueError(f"Unknown config name: {config_name}")


# 便利函數
def get_protocol_known_issue_config() -> Dict[str, str]:
    """
    獲取 Protocol Known Issue System 配置的便利函數
    
    Returns:
        Dict: 應用配置
    """
    return DifyAppConfigs.get_protocol_known_issue_config()


def create_protocol_chat_client():
    """
    創建 Protocol Known Issue System Chat 客戶端的便利函數
    
    Returns:
        DifyChatClient: 配置好的客戶端
    """
    return DifyAppConfigs.create_protocol_chat_client()


def validate_protocol_config() -> bool:
    """
    驗證 Protocol Known Issue System 配置的便利函數
    
    Returns:
        bool: 配置是否有效
    """
    return DifyAppConfigs.validate_config('protocol_known_issue_system')


# 向後兼容的配置字典（用於現有代碼）
DIFY_PROTOCOL_CONFIG = DifyAppConfigs.PROTOCOL_KNOWN_ISSUE_SYSTEM


# 環境變數配置說明
"""
支援的環境變數：

DIFY_PROTOCOL_API_URL     - Chat API 端點 URL
DIFY_PROTOCOL_API_KEY     - API Key (app-開頭)
DIFY_PROTOCOL_BASE_URL    - Dify 基礎 URL
DIFY_PROTOCOL_TIMEOUT     - 請求超時時間（秒）

使用範例：
export DIFY_PROTOCOL_API_KEY="app-YourNewApiKey"
export DIFY_PROTOCOL_TIMEOUT=120
"""