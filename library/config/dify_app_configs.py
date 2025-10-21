"""
Dify App 配置向後兼容層
此文件為舊版代碼提供向後兼容性，所有函數都轉發到新的 dify_config_manager.py
建議逐步遷移到新的 DifyConfigManager API
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# 從新的配置管理器導入所有功能
try:
    from library.config.dify_config_manager import (
        DifyAppConfig,
        DifyConfigManager,
        default_config_manager,
        # 便利函數
        get_protocol_known_issue_config,
        get_protocol_guide_config,
        get_rvt_guide_config,
        get_report_analyzer_3_config,
        get_ai_ocr_config,
        # 字典版本（向後兼容）
        get_protocol_known_issue_config_dict,
        get_protocol_guide_config_dict,
        get_rvt_guide_config_dict,
        get_report_analyzer_3_config_dict,
        get_ai_ocr_config_dict,
        # 驗證函數
        validate_all_dify_configs,
        get_all_dify_configs_safe,
    )
    
    logger.info("✅ Dify 配置向後兼容層載入成功")
    
except ImportError as e:
    logger.error(f"❌ 無法從 dify_config_manager 導入配置: {e}")
    raise


# ============= 向後兼容的類別 =============

class DifyAppConfigs:
    """
    舊版 DifyAppConfigs 類別（向後兼容）
    建議使用新的 DifyConfigManager
    """
    
    def __init__(self):
        self.manager = default_config_manager
        logger.warning("⚠️  使用舊版 DifyAppConfigs，建議遷移到 DifyConfigManager")
    
    def get_protocol_known_issue_config(self) -> Dict[str, Any]:
        """獲取 Protocol Known Issue 配置"""
        return self.manager.get_protocol_known_issue_config().to_dict()
    
    def get_protocol_guide_config(self) -> Dict[str, Any]:
        """獲取 Protocol Guide 配置"""
        return self.manager.get_protocol_guide_config().to_dict()
    
    def get_rvt_guide_config(self) -> Dict[str, Any]:
        """獲取 RVT Guide 配置"""
        return self.manager.get_rvt_guide_config().to_dict()
    
    def get_report_analyzer_3_config(self) -> Dict[str, Any]:
        """獲取 Report Analyzer 3 配置"""
        return self.manager.get_report_analyzer_3_config().to_dict()
    
    def get_ai_ocr_config(self) -> Dict[str, Any]:
        """獲取 AI OCR 配置"""
        return self.manager.get_ai_ocr_config().to_dict()


# ============= 便利函數（創建客戶端）=============

def create_protocol_chat_client():
    """
    創建 Protocol Known Issue 聊天客戶端（向後兼容）
    
    Returns:
        配置好的 DifyRequestManager 實例
    """
    from library.dify_integration.dify_request_manager import DifyRequestManager
    
    config = get_protocol_known_issue_config()
    
    return DifyRequestManager(
        api_url=config.api_url,
        api_key=config.api_key,
        timeout=config.timeout
    )


def create_rvt_guide_chat_client():
    """
    創建 RVT Guide 聊天客戶端（向後兼容）
    
    Returns:
        配置好的 DifyRequestManager 實例
    """
    from library.dify_integration.dify_request_manager import DifyRequestManager
    
    config = get_rvt_guide_config()
    
    return DifyRequestManager(
        api_url=config.api_url,
        api_key=config.api_key,
        timeout=config.timeout
    )


def create_protocol_guide_chat_client():
    """
    創建 Protocol Guide 聊天客戶端
    
    Returns:
        配置好的 DifyRequestManager 實例
    """
    from library.dify_integration.dify_request_manager import DifyRequestManager
    
    config = get_protocol_guide_config()
    
    return DifyRequestManager(
        api_url=config.api_url,
        api_key=config.api_key,
        timeout=config.timeout
    )


# ============= 驗證函數（向後兼容）=============

def validate_protocol_config() -> bool:
    """驗證 Protocol Known Issue 配置"""
    try:
        config = get_protocol_known_issue_config()
        return config.validate()
    except Exception as e:
        logger.error(f"Protocol 配置驗證失敗: {e}")
        return False


def validate_rvt_guide_config() -> bool:
    """驗證 RVT Guide 配置"""
    try:
        config = get_rvt_guide_config()
        return config.validate()
    except Exception as e:
        logger.error(f"RVT Guide 配置驗證失敗: {e}")
        return False


def validate_protocol_guide_config() -> bool:
    """驗證 Protocol Guide 配置"""
    try:
        config = get_protocol_guide_config()
        return config.validate()
    except Exception as e:
        logger.error(f"Protocol Guide 配置驗證失敗: {e}")
        return False


# ============= 導出所有內容 =============

__all__ = [
    # 數據類
    'DifyAppConfig',
    'DifyAppConfigs',
    # 配置管理器
    'DifyConfigManager',
    'default_config_manager',
    # Protocol Known Issue
    'get_protocol_known_issue_config',
    'get_protocol_known_issue_config_dict',
    'create_protocol_chat_client',
    'validate_protocol_config',
    # Protocol Guide
    'get_protocol_guide_config',
    'get_protocol_guide_config_dict',
    'create_protocol_guide_chat_client',
    'validate_protocol_guide_config',
    # RVT Guide
    'get_rvt_guide_config',
    'get_rvt_guide_config_dict',
    'create_rvt_guide_chat_client',
    'validate_rvt_guide_config',
    # Report Analyzer 3
    'get_report_analyzer_3_config',
    'get_report_analyzer_3_config_dict',
    # AI OCR
    'get_ai_ocr_config',
    'get_ai_ocr_config_dict',
    # 工具函數
    'validate_all_dify_configs',
    'get_all_dify_configs_safe',
]
