"""
配置管理模組
統一管理 API 金鑰、服務端點、環境變數等配置
"""

from .dify_config import DifyConfig
from .database_config import DatabaseConfig
from .app_config import AppConfig
from .dify_config_manager import (
    DifyConfigManager, 
    DifyAppConfig,
    get_rvt_guide_config,
    get_protocol_known_issue_config,
    get_report_analyzer_config,
    get_ai_ocr_config,
    validate_all_dify_configs,
    get_all_dify_configs_safe,
    # 向後兼容
    get_rvt_guide_config_dict,
    get_protocol_known_issue_config_dict
)

__all__ = [
    'DifyConfig', 
    'DatabaseConfig', 
    'AppConfig',
    # 新的配置管理器
    'DifyConfigManager',
    'DifyAppConfig',
    'get_rvt_guide_config',
    'get_protocol_known_issue_config',
    'get_report_analyzer_config',
    'get_ai_ocr_config',
    'validate_all_dify_configs',
    'get_all_dify_configs_safe',
    # 向後兼容
    'get_rvt_guide_config_dict',
    'get_protocol_known_issue_config_dict'
]