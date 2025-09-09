"""
Dify 配置管理
統一管理 Dify API 相關配置
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