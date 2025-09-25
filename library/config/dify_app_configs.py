#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify 應用配置管理
維護各種 Dify 應用的 API 配置信息
"""

import os
from typing import Dict, Optional
from .dify_config import ChatConfig, get_chat_config

# 導入配置載入器
try:
    import sys
    from pathlib import Path
    # 添加專案根目錄到 Python 路徑
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    from config.config_loader import get_ai_pc_ip_with_env
    CONFIG_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  配置載入器不可用，使用預設 IP: {e}")
    CONFIG_AVAILABLE = False
    
    def get_ai_pc_ip_with_env():
        """備用函數：如果配置載入器不可用，返回預設 IP"""
        return os.getenv('AI_PC_IP', '10.10.172.37')


class DifyAppConfigs:
    """Dify 應用配置管理器"""
    
    @staticmethod
    def _get_ai_pc_ip():
        """獲取 AI PC IP 地址"""
        return get_ai_pc_ip_with_env()
    
    # Protocol Known Issue System 工作室配置
    @classmethod
    def _get_protocol_known_issue_system_config(cls):
        """動態獲取 Protocol Known Issue System 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'Protocol Known Issue System',
            'workspace': 'Protocol_known_issue_system',
            'description': 'Dify Chat 應用，用於查詢 Know Issue 知識庫',
            'features': ['知識庫查詢', '員工資訊', 'Know Issue 管理'],
            'timeout': 75,  # 增加超時時間到75秒
            'response_mode': 'blocking'
        }
    
    # Report Analyzer 3 工作室配置
    @classmethod
    def _get_report_analyzer_3_config(cls):
        """動態獲取 Report Analyzer 3 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-DmCCl8KwXhhjND0WbEf0ULlR',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'Report Analyzer 3',
            'workspace': 'Report_Analyzer_3',
            'description': 'Dify Chat 應用，用於報告分析和日誌處理',
            'features': ['報告分析', '日誌處理', '數據分析'],
            'timeout': 120,
            'response_mode': 'blocking'
        }
    
    # RVT Guide 工作室配置
    @classmethod
    def _get_rvt_guide_config(cls):
        """動態獲取 RVT Guide 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-Lp4mlfIWHqMWPHTlzF9ywT4F',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'RVT Guide',
            'workspace': 'RVT_Guide',
            'description': 'Dify Chat 應用，用於 RVT 相關指導和協助',
            'features': ['RVT 指導', '技術支援', 'RVT 流程管理'],
            'timeout': 75,  # 增加超時時間到75秒
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
        config = cls._get_protocol_known_issue_system_config()
        
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
    def get_report_analyzer_3_config(cls) -> Dict[str, str]:
        """
        獲取 Report Analyzer 3 配置
        
        Returns:
            Dict: 應用配置
        """
        config = cls._get_report_analyzer_3_config()
        
        # 支援環境變數覆蓋
        env_overrides = {
            'DIFY_REPORT_ANALYZER_API_URL': 'api_url',
            'DIFY_REPORT_ANALYZER_API_KEY': 'api_key',
            'DIFY_REPORT_ANALYZER_BASE_URL': 'base_url',
            'DIFY_REPORT_ANALYZER_TIMEOUT': 'timeout'
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
    def get_rvt_guide_config(cls) -> Dict[str, str]:
        """
        獲取 RVT Guide 配置
        
        Returns:
            Dict: 應用配置
        """
        config = cls._get_rvt_guide_config()
        
        # 支援環境變數覆蓋
        env_overrides = {
            'DIFY_RVT_GUIDE_API_URL': 'api_url',
            'DIFY_RVT_GUIDE_API_KEY': 'api_key',
            'DIFY_RVT_GUIDE_BASE_URL': 'base_url',
            'DIFY_RVT_GUIDE_TIMEOUT': 'timeout'
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
    def create_report_analyzer_3_chat_client(cls):
        """
        創建 Report Analyzer 3 的 Chat 客戶端
        
        Returns:
            DifyChatClient: 配置好的客戶端
        """
        from ..dify_integration.chat_client import create_chat_client
        
        config = cls.get_report_analyzer_3_config()
        return create_chat_client(
            api_url=config['api_url'],
            api_key=config['api_key'],
            base_url=config['base_url']
        )
    
    @classmethod
    def create_rvt_guide_chat_client(cls):
        """
        創建 RVT Guide 的 Chat 客戶端
        
        Returns:
            DifyChatClient: 配置好的客戶端
        """
        from ..dify_integration.chat_client import create_chat_client
        
        config = cls.get_rvt_guide_config()
        return create_chat_client(
            api_url=config['api_url'],
            api_key=config['api_key'],
            base_url=config['base_url']
        )
    
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
            'report_analyzer_3': cls.get_report_analyzer_3_config(),
            'rvt_guide': cls.get_rvt_guide_config(),
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
        
        elif config_name == 'report_analyzer_3':
            config = cls.get_report_analyzer_3_config()
            required_keys = ['api_url', 'api_key', 'base_url']
            
            for key in required_keys:
                if not config.get(key):
                    raise ValueError(f"Missing required config key: {key}")
            
            # 驗證 API Key 格式
            if not config['api_key'].startswith('app-'):
                raise ValueError("Invalid API key format. Must start with 'app-'")
            
            return True
        
        elif config_name == 'rvt_guide':
            config = cls.get_rvt_guide_config()
            required_keys = ['api_url', 'api_key', 'base_url']
            
            for key in required_keys:
                if not config.get(key):
                    raise ValueError(f"Missing required config key: {key}")
            
            # 驗證 API Key 格式
            if not config['api_key'].startswith('app-'):
                raise ValueError("Invalid API key format. Must start with 'app-'")
            
            return True
        
        raise ValueError(f"Unknown config name: {config_name}")


def get_report_analyzer_3_config() -> Dict[str, str]:
    """
    獲取 Report Analyzer 3 配置的便利函數
    
    Returns:
        Dict: 應用配置
    """
    return DifyAppConfigs.get_report_analyzer_3_config()


def create_report_analyzer_3_chat_client():
    """
    創建 Report Analyzer 3 Chat 客戶端的便利函數
    
    Returns:
        DifyChatClient: 配置好的客戶端
    """
    return DifyAppConfigs.create_report_analyzer_3_chat_client()


def validate_report_analyzer_3_config() -> bool:
    """
    驗證 Report Analyzer 3 配置的便利函數
    
    Returns:
        bool: 配置是否有效
    """
    return DifyAppConfigs.validate_config('report_analyzer_3')


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


def get_rvt_guide_config() -> Dict[str, str]:
    """
    獲取 RVT Guide 配置的便利函數
    
    Returns:
        Dict: 應用配置
    """
    return DifyAppConfigs.get_rvt_guide_config()


def create_rvt_guide_chat_client():
    """
    創建 RVT Guide Chat 客戶端的便利函數
    
    Returns:
        DifyChatClient: 配置好的客戶端
    """
    return DifyAppConfigs.create_rvt_guide_chat_client()


def validate_rvt_guide_config() -> bool:
    """
    驗證 RVT Guide 配置的便利函數
    
    Returns:
        bool: 配置是否有效
    """
    return DifyAppConfigs.validate_config('rvt_guide')


# 向後兼容的配置字典（用於現有代碼）
# 這個會動態生成，包含當前的 IP 配置
@property 
def DIFY_PROTOCOL_CONFIG():
    return DifyAppConfigs.get_protocol_known_issue_config()

# 但為了向後兼容，我們也提供一個靜態的方法
def get_legacy_dify_protocol_config():
    """獲取向後兼容的 Protocol 配置"""
    return DifyAppConfigs.get_protocol_known_issue_config()

# 確保向後兼容
DIFY_PROTOCOL_CONFIG = get_legacy_dify_protocol_config()


# 環境變數配置說明
"""
支援的環境變數：

Protocol Known Issue System:
DIFY_PROTOCOL_API_URL     - Chat API 端點 URL
DIFY_PROTOCOL_API_KEY     - API Key (app-開頭)
DIFY_PROTOCOL_BASE_URL    - Dify 基礎 URL
DIFY_PROTOCOL_TIMEOUT     - 請求超時時間（秒）

Report Analyzer 3:
DIFY_REPORT_ANALYZER_API_URL     - Chat API 端點 URL
DIFY_REPORT_ANALYZER_API_KEY     - API Key (app-開頭)
DIFY_REPORT_ANALYZER_BASE_URL    - Dify 基礎 URL
DIFY_REPORT_ANALYZER_TIMEOUT     - 請求超時時間（秒）

RVT Guide:
DIFY_RVT_GUIDE_API_URL     - Chat API 端點 URL
DIFY_RVT_GUIDE_API_KEY     - API Key (app-開頭)
DIFY_RVT_GUIDE_BASE_URL    - Dify 基礎 URL
DIFY_RVT_GUIDE_TIMEOUT     - 請求超時時間（秒）

使用範例：
export DIFY_PROTOCOL_API_KEY="app-YourNewApiKey"
export DIFY_PROTOCOL_TIMEOUT=120
export DIFY_REPORT_ANALYZER_API_KEY="app-DmCCl8KwXhhjND0WbEf0ULlR"
export DIFY_REPORT_ANALYZER_TIMEOUT=120
export DIFY_RVT_GUIDE_API_KEY="app-Lp4mlfIWHqMWPHTlzF9ywT4F"
export DIFY_RVT_GUIDE_TIMEOUT=60
"""