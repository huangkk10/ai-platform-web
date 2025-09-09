"""
資料庫配置管理
"""

import os
from typing import Dict


class DatabaseConfig:
    """資料庫配置管理器"""
    
    def __init__(self):
        self.config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5432)),
            'name': os.getenv('DB_NAME', 'ai_platform'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', 'postgres123'),
        }
    
    def get_database_url(self) -> str:
        """獲取資料庫連接 URL"""
        return f"postgresql://{self.config['user']}:{self.config['password']}@{self.config['host']}:{self.config['port']}/{self.config['name']}"
    
    def get_config(self) -> Dict:
        """獲取配置字典"""
        return self.config.copy()