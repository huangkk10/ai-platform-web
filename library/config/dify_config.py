"""
Dify 配置管理
統一管理 Dify API 相關配置，包括 Chat API 和 Dataset API
"""

import os
from typing import Dict, Optional


class DifyConfig:
    """Dify 配置管理器"""
    
    # 默認配置
    DEFAULT_CONFIG = {
        'base_url': 'https://api.dify.ai',
        'timeout': 30,
        'max_retries': 3,
        'embedding_model': '',
        'indexing_technique': 'economy'
    }
    
    # Chat API 默認配置
    DEFAULT_CHAT_CONFIG = {
        'base_url': 'http://10.10.172.127',
        'api_url': 'http://10.10.172.127/v1/chat-messages',
        'api_key': '',
        'timeout': 60,
        'response_mode': 'blocking',
        'user': 'default_user'
    }
    
    # Dataset API 默認配置
    DEFAULT_DATASET_CONFIG = {
        'base_url': 'http://10.10.172.127',
        'dataset_api_url': 'http://10.10.172.127/v1/datasets',
        'dataset_key': '',
        'timeout': 30,
        'top_k': 5,
        'score_threshold': 0.5
    }
    
    def __init__(self, api_key: str = None, config: Dict = None):
        """
        初始化配置
        
        Args:
            api_key: API 金鑰
            config: 自定義配置
        """
        self.api_key = api_key or os.getenv('DIFY_API_KEY')
        self.config = {**self.DEFAULT_CONFIG}
        
        if config:
            self.config.update(config)
        
        # 從環境變數載入配置
        self._load_from_env()
    
    def _load_from_env(self):
        """從環境變數載入配置"""
        env_mappings = {
            'DIFY_BASE_URL': 'base_url',
            'DIFY_TIMEOUT': 'timeout',
            'DIFY_MAX_RETRIES': 'max_retries',
            'DIFY_EMBEDDING_MODEL': 'embedding_model',
            'DIFY_INDEXING_TECHNIQUE': 'indexing_technique'
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                # 轉換數據類型
                if config_key in ['timeout', 'max_retries']:
                    self.config[config_key] = int(env_value)
                else:
                    self.config[config_key] = env_value
    
    def get(self, key: str, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        """設置配置值"""
        self.config[key] = value
    
    def get_headers(self) -> Dict[str, str]:
        """獲取請求標頭"""
        return {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def validate(self) -> bool:
        """驗證配置是否有效"""
        if not self.api_key:
            raise ValueError("API key is required")
        
        required_configs = ['base_url', 'timeout']
        for key in required_configs:
            if not self.config.get(key):
                raise ValueError(f"Missing required config: {key}")
        
        return True


class ChatConfig:
    """Chat API 配置管理器"""
    
    def __init__(self, api_url: str = None, api_key: str = None, 
                 base_url: str = None, config: Dict = None):
        """
        初始化 Chat 配置
        
        Args:
            api_url: Chat API 端點 URL
            api_key: API Key
            base_url: Dify 基礎 URL
            config: 自定義配置
        """
        self.config = {**DifyConfig.DEFAULT_CHAT_CONFIG}
        
        # 更新提供的配置
        if api_url:
            self.config['api_url'] = api_url
        if api_key:
            self.config['api_key'] = api_key
        if base_url:
            self.config['base_url'] = base_url
        
        if config:
            self.config.update(config)
        
        # 從環境變數載入
        self._load_from_env()
    
    def _load_from_env(self):
        """從環境變數載入 Chat 配置"""
        env_mappings = {
            'DIFY_CHAT_API_URL': 'api_url',
            'DIFY_CHAT_API_KEY': 'api_key',
            'DIFY_CHAT_BASE_URL': 'base_url',
            'DIFY_CHAT_TIMEOUT': 'timeout',
            'DIFY_CHAT_RESPONSE_MODE': 'response_mode',
            'DIFY_CHAT_DEFAULT_USER': 'user'
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                if config_key == 'timeout':
                    self.config[config_key] = int(env_value)
                else:
                    self.config[config_key] = env_value
    
    def get(self, key: str, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def validate(self) -> bool:
        """驗證 Chat 配置"""
        required_keys = ['api_url', 'api_key']
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"Missing required Chat config: {key}")
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """獲取 Chat API 請求標頭"""
        return {
            'Authorization': f'Bearer {self.config["api_key"]}',
            'Content-Type': 'application/json'
        }


class DatasetConfig:
    """Dataset API 配置管理器"""
    
    def __init__(self, dataset_api_url: str = None, dataset_key: str = None,
                 base_url: str = None, config: Dict = None):
        """
        初始化 Dataset 配置
        
        Args:
            dataset_api_url: Dataset API 端點 URL
            dataset_key: Dataset API Key
            base_url: Dify 基礎 URL
            config: 自定義配置
        """
        self.config = {**DifyConfig.DEFAULT_DATASET_CONFIG}
        
        # 更新提供的配置
        if dataset_api_url:
            self.config['dataset_api_url'] = dataset_api_url
        if dataset_key:
            self.config['dataset_key'] = dataset_key
        if base_url:
            self.config['base_url'] = base_url
        
        if config:
            self.config.update(config)
        
        # 從環境變數載入
        self._load_from_env()
    
    def _load_from_env(self):
        """從環境變數載入 Dataset 配置"""
        env_mappings = {
            'DIFY_DATASET_API_URL': 'dataset_api_url',
            'DIFY_DATASET_API_KEY': 'dataset_key',
            'DIFY_DATASET_BASE_URL': 'base_url',
            'DIFY_DATASET_TIMEOUT': 'timeout',
            'DIFY_DATASET_TOP_K': 'top_k',
            'DIFY_DATASET_SCORE_THRESHOLD': 'score_threshold'
        }
        
        for env_key, config_key in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value:
                if config_key in ['timeout', 'top_k']:
                    self.config[config_key] = int(env_value)
                elif config_key == 'score_threshold':
                    self.config[config_key] = float(env_value)
                else:
                    self.config[config_key] = env_value
    
    def get(self, key: str, default=None):
        """獲取配置值"""
        return self.config.get(key, default)
    
    def validate(self) -> bool:
        """驗證 Dataset 配置"""
        required_keys = ['dataset_api_url', 'dataset_key']
        for key in required_keys:
            if not self.config.get(key):
                raise ValueError(f"Missing required Dataset config: {key}")
        return True
    
    def get_headers(self) -> Dict[str, str]:
        """獲取 Dataset API 請求標頭"""
        return {
            'Authorization': f'Bearer {self.config["dataset_key"]}',
            'Content-Type': 'application/json'
        }


# 便利函數
def get_chat_config(api_url: str = None, api_key: str = None, 
                   base_url: str = None) -> Dict[str, str]:
    """
    獲取 Chat API 配置
    
    Args:
        api_url: Chat API 端點 URL
        api_key: API Key
        base_url: Dify 基礎 URL
        
    Returns:
        Dict: Chat 配置字典
    """
    chat_config = ChatConfig(api_url, api_key, base_url)
    chat_config.validate()
    return chat_config.config


def get_dataset_config(dataset_api_url: str = None, dataset_key: str = None,
                      base_url: str = None) -> Dict[str, str]:
    """
    獲取 Dataset API 配置
    
    Args:
        dataset_api_url: Dataset API 端點 URL
        dataset_key: Dataset API Key
        base_url: Dify 基礎 URL
        
    Returns:
        Dict: Dataset 配置字典
    """
    dataset_config = DatasetConfig(dataset_api_url, dataset_key, base_url)
    dataset_config.validate()
    return dataset_config.config


def create_chat_config_from_dict(config_dict: Dict) -> ChatConfig:
    """從字典創建 Chat 配置"""
    return ChatConfig(
        api_url=config_dict.get('api_url'),
        api_key=config_dict.get('api_key'),
        base_url=config_dict.get('base_url'),
        config=config_dict
    )


def create_dataset_config_from_dict(config_dict: Dict) -> DatasetConfig:
    """從字典創建 Dataset 配置"""
    return DatasetConfig(
        dataset_api_url=config_dict.get('dataset_api_url'),
        dataset_key=config_dict.get('dataset_key'),
        base_url=config_dict.get('base_url'),
        config=config_dict
    )