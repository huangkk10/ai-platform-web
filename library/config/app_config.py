"""
應用程式配置管理
"""

import os
from typing import Dict, Any


class AppConfig:
    """應用程式配置管理器"""
    
    def __init__(self):
        self.config = {
            'debug': os.getenv('DEBUG', '0') == '1',
            'secret_key': os.getenv('SECRET_KEY', 'your-secret-key'),
            'timezone': os.getenv('TZ', 'Asia/Taipei'),
            'api_url': os.getenv('REACT_APP_API_URL', 'http://localhost:8000'),
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """獲取配置值"""
        return self.config.get(key, default)
    
    def is_debug(self) -> bool:
        """是否為除錯模式"""
        return self.config['debug']
    
    def get_all(self) -> Dict[str, Any]:
        """獲取所有配置"""
        return self.config.copy()