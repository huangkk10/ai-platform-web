"""
Dify 配置管理器
提供統一的 Dify 應用配置管理，支援動態配置、環境變數覆蓋和配置驗證
"""

import os
import logging
from typing import Dict, Optional, List, Any, Union
from dataclasses import dataclass

logger = logging.getLogger(__name__)


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
    logger.warning(f"配置載入器不可用，使用預設 IP: {e}")
    CONFIG_AVAILABLE = False
    
    def get_ai_pc_ip_with_env():
        """備用函數：如果配置載入器不可用，返回預設 IP"""
        return os.getenv('AI_PC_IP', '10.10.172.37')


@dataclass
class DifyAppConfig:
    """Dify 應用配置數據類"""
    app_name: str
    workspace: str
    api_url: str
    api_key: str
    base_url: str
    description: str = ""
    features: List[str] = None
    timeout: int = 60
    response_mode: str = "blocking"
    
    def __post_init__(self):
        if self.features is None:
            self.features = []
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'app_name': self.app_name,
            'workspace': self.workspace,
            'api_url': self.api_url,
            'api_key': self.api_key,
            'base_url': self.base_url,
            'description': self.description,
            'features': self.features,
            'timeout': self.timeout,
            'response_mode': self.response_mode
        }
    
    def validate(self) -> bool:
        """驗證配置是否有效"""
        required_fields = ['app_name', 'workspace', 'api_url', 'api_key', 'base_url']
        for field in required_fields:
            value = getattr(self, field, None)
            if not value or (isinstance(value, str) and value.strip() == ''):
                logger.error(f"配置驗證失敗: {field} 不能為空")
                return False
        return True
    
    def get_safe_config(self) -> Dict[str, Any]:
        """獲取安全的配置（隱藏 API key）"""
        config = self.to_dict()
        if config.get('api_key'):
            config['api_key_prefix'] = config['api_key'][:10] + '...'
            config.pop('api_key', None)
        return config


class DifyConfigManager:
    """Dify 配置管理器 - 整合版"""
    
    # 支援的應用類型
    SUPPORTED_APPS = {
        'protocol_known_issue': 'Protocol Known Issue System',
        'protocol_guide': 'Protocol Guide',
        'rvt_guide': 'RVT Guide',
        'report_analyzer_3': 'Report Analyzer 3',
        'ai_ocr': 'AI OCR System',
        'ocr_function': 'OCR Function',
        'saf_intent_analyzer': 'SAF Intent Analyzer',
        'saf_analyzer': 'SAF Analyzer',
    }
    
    def __init__(self):
        """初始化配置管理器"""
        self._configs_cache = {}
    
    @staticmethod
    def _get_ai_pc_ip():
        """獲取 AI PC IP 地址"""
        return get_ai_pc_ip_with_env()
    
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
    
    @classmethod
    def _get_protocol_guide_config(cls):
        """動態獲取 Protocol Guide 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-MgZZOhADkEmdUrj2DtQLJ23G',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'Protocol Guide',
            'workspace': 'Protocol_Guide',
            'description': 'Dify Chat 應用，用於 Protocol 相關指導和協助',
            'features': ['Protocol 指導', '技術支援', 'Protocol 流程管理'],
            'timeout': 75,  # 增加超時時間到75秒
            'response_mode': 'blocking'
        }
    
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
    
    @classmethod
    def _get_ocr_function_config(cls):
        """動態獲取 OCR Function 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-eFCJ5fDpoWV7CGKQ7VSoKgi0',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'OCR Function',
            'workspace': 'OCR_Function',
            'description': 'Dify 工作流應用，提供 OCR 圖像識別功能，供各 Web Assistant 調用',
            'features': ['圖像識別', 'OCR 文字擷取', '結構化資料解析', '跨 Assistant 共用'],
            'timeout': 90,  # OCR 處理可能需要較長時間
            'response_mode': 'blocking'
        }
    
    @classmethod
    def _get_saf_intent_analyzer_config(cls):
        """動態獲取 SAF Intent Analyzer 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-vMNSUqgEIoejnXo3fuFvp1hC',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'SAF Intent Analyzer',
            'workspace': 'SAF_Intent_Analyzer',
            'description': 'Dify Chat 應用，用於分析用戶查詢意圖，輸出 JSON 格式的意圖識別結果',
            'features': ['意圖分析', 'JSON 輸出', 'SAF 查詢路由'],
            'timeout': 30,  # 意圖分析應該快速完成
            'response_mode': 'blocking'
        }
    
    @classmethod
    def _get_saf_analyzer_config(cls):
        """動態獲取 SAF Analyzer 配置"""
        ai_pc_ip = cls._get_ai_pc_ip()
        return {
            'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
            'api_key': 'app-0GyoZLrr4tDpT4EO2Kihuvux',
            'base_url': f'http://{ai_pc_ip}',
            'app_name': 'SAF Analyzer',
            'workspace': 'SAF_Analyzer',
            'description': 'Dify Chat 應用，用於根據 SAF API 查詢結果生成自然語言回答',
            'features': ['回答生成', '自然語言處理', 'Table 格式化'],
            'timeout': 60,  # 回答生成可能需要較長時間
            'response_mode': 'blocking'
        }
    
    def _get_base_config_with_env_override(self, base_config: Dict[str, Any], env_prefix: str) -> Dict[str, Any]:
        """
        獲取基礎配置並支援環境變數覆蓋
        
        Args:
            base_config: 基礎配置字典
            env_prefix: 環境變數前綴 (例如: 'DIFY_PROTOCOL')
            
        Returns:
            Dict: 應用環境變數覆蓋後的配置
        """
        config = base_config.copy()
        
        # 支援環境變數覆蓋
        env_overrides = {
            f'{env_prefix}_API_URL': 'api_url',
            f'{env_prefix}_API_KEY': 'api_key',
            f'{env_prefix}_BASE_URL': 'base_url',
            f'{env_prefix}_TIMEOUT': 'timeout'
        }
        
        for env_key, config_key in env_overrides.items():
            env_value = os.getenv(env_key)
            if env_value:
                if config_key == 'timeout':
                    try:
                        config[config_key] = int(env_value)
                    except ValueError:
                        logger.warning(f"無效的超時值: {env_value}，使用預設值")
                else:
                    config[config_key] = env_value
        
        return config
    
    def get_app_config(self, app_type: str) -> DifyAppConfig:
        """
        獲取指定應用的配置
        
        Args:
            app_type: 應用類型 ('protocol_known_issue', 'rvt_guide', etc.)
            
        Returns:
            DifyAppConfig: 應用配置對象
            
        Raises:
            ValueError: 不支援的應用類型
        """
        if app_type not in self.SUPPORTED_APPS:
            raise ValueError(f"不支援的應用類型: {app_type}")
        
        # 檢查緩存
        cache_key = f"{app_type}_config"
        if cache_key in self._configs_cache:
            return self._configs_cache[cache_key]
        
        # 獲取配置
        config_dict = self._get_config_dict(app_type)
        
        # 轉換為 DifyAppConfig 對象
        app_config = DifyAppConfig(**config_dict)
        
        # 驗證配置
        if not app_config.validate():
            raise ValueError(f"應用 {app_type} 的配置驗證失敗")
        
        # 緩存配置
        self._configs_cache[cache_key] = app_config
        
        return app_config
    
    def _get_config_dict(self, app_type: str) -> Dict[str, Any]:
        """獲取配置字典"""
        if app_type == 'protocol_known_issue':
            base_config = self._get_protocol_known_issue_system_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_PROTOCOL')
        elif app_type == 'protocol_guide':
            base_config = self._get_protocol_guide_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_PROTOCOL_GUIDE')
        elif app_type == 'rvt_guide':
            base_config = self._get_rvt_guide_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_RVT_GUIDE')
        elif app_type == 'report_analyzer_3':
            base_config = self._get_report_analyzer_3_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_REPORT_ANALYZER')
        elif app_type == 'ai_ocr':
            # AI OCR 使用相同的 Report Analyzer 3 配置
            base_config = self._get_report_analyzer_3_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_REPORT_ANALYZER')
        elif app_type == 'ocr_function':
            base_config = self._get_ocr_function_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_OCR_FUNCTION')
        elif app_type == 'saf_intent_analyzer':
            base_config = self._get_saf_intent_analyzer_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_SAF_INTENT')
        elif app_type == 'saf_analyzer':
            base_config = self._get_saf_analyzer_config()
            return self._get_base_config_with_env_override(base_config, 'DIFY_SAF_ANALYZER')
        else:
            raise ValueError(f"無法找到應用 {app_type} 的配置方法")
    
    def get_protocol_guide_config(self) -> DifyAppConfig:
        """
        獲取 Protocol Guide 配置的便利方法
        
        Returns:
            DifyAppConfig: Protocol Guide 配置
        """
        return self.get_app_config('protocol_guide')
    
    def get_rvt_guide_config(self) -> DifyAppConfig:
        """
        獲取 RVT Guide 配置的便利方法
        
        Returns:
            DifyAppConfig: RVT Guide 配置
        """
        return self.get_app_config('rvt_guide')
    
    def get_protocol_known_issue_config(self) -> DifyAppConfig:
        """
        獲取 Protocol Known Issue 配置的便利方法
        
        Returns:
            DifyAppConfig: Protocol Known Issue 配置
        """
        return self.get_app_config('protocol_known_issue')
    
    def get_report_analyzer_config(self) -> DifyAppConfig:
        """
        獲取 Report Analyzer 3 配置的便利方法
        
        Returns:
            DifyAppConfig: Report Analyzer 3 配置
        """
        return self.get_app_config('report_analyzer_3')
    
    def get_ai_ocr_config(self) -> DifyAppConfig:
        """
        獲取 AI OCR 配置的便利方法
        
        Returns:
            DifyAppConfig: AI OCR 配置
        """
        return self.get_app_config('ai_ocr')
    
    def get_ocr_function_config(self) -> DifyAppConfig:
        """
        獲取 OCR Function 配置的便利方法
        
        Returns:
            DifyAppConfig: OCR Function 配置
        """
        return self.get_app_config('ocr_function')
    
    def get_saf_intent_analyzer_config(self) -> DifyAppConfig:
        """
        獲取 SAF Intent Analyzer 配置的便利方法
        
        Returns:
            DifyAppConfig: SAF Intent Analyzer 配置
        """
        return self.get_app_config('saf_intent_analyzer')
    
    def get_saf_analyzer_config(self) -> DifyAppConfig:
        """
        獲取 SAF Analyzer 配置的便利方法
        
        Returns:
            DifyAppConfig: SAF Analyzer 配置
        """
        return self.get_app_config('saf_analyzer')
    
    def list_available_apps(self) -> Dict[str, str]:
        """
        獲取所有可用的應用類型
        
        Returns:
            Dict[str, str]: 應用類型 -> 應用名稱映射
        """
        return self.SUPPORTED_APPS.copy()
    
    def validate_all_configs(self) -> Dict[str, bool]:
        """
        驗證所有配置
        
        Returns:
            Dict[str, bool]: 應用類型 -> 驗證結果映射
        """
        results = {}
        
        for app_type in self.SUPPORTED_APPS.keys():
            try:
                config = self.get_app_config(app_type)
                results[app_type] = config.validate()
            except Exception as e:
                logger.error(f"驗證應用 {app_type} 配置時發生錯誤: {e}")
                results[app_type] = False
        
        return results
    
    def get_all_safe_configs(self) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有應用的安全配置（隱藏敏感信息）
        
        Returns:
            Dict[str, Dict]: 應用類型 -> 安全配置映射
        """
        configs = {}
        
        for app_type in self.SUPPORTED_APPS.keys():
            try:
                config = self.get_app_config(app_type)
                configs[app_type] = config.get_safe_config()
            except Exception as e:
                logger.error(f"獲取應用 {app_type} 安全配置時發生錯誤: {e}")
                configs[app_type] = {'error': str(e)}
        
        return configs
    
    def clear_cache(self):
        """清除配置緩存"""
        self._configs_cache.clear()
        logger.info("配置緩存已清除")
    
    def refresh_config(self, app_type: str) -> DifyAppConfig:
        """
        刷新指定應用的配置
        
        Args:
            app_type: 應用類型
            
        Returns:
            DifyAppConfig: 刷新後的配置
        """
        # 從緩存中移除
        cache_key = f"{app_type}_config"
        self._configs_cache.pop(cache_key, None)
        
        # 重新獲取
        return self.get_app_config(app_type)


# 創建全局配置管理器實例
default_config_manager = DifyConfigManager()


# 便利函數
def get_protocol_guide_config() -> DifyAppConfig:
    """
    獲取 Protocol Guide 配置的便利函數
    
    Returns:
        DifyAppConfig: Protocol Guide 配置對象
    """
    return default_config_manager.get_protocol_guide_config()


def get_rvt_guide_config() -> DifyAppConfig:
    """
    獲取 RVT Guide 配置的便利函數
    
    Returns:
        DifyAppConfig: RVT Guide 配置對象
    """
    return default_config_manager.get_rvt_guide_config()


def get_protocol_known_issue_config() -> DifyAppConfig:
    """
    獲取 Protocol Known Issue 配置的便利函數
    
    Returns:
        DifyAppConfig: Protocol Known Issue 配置對象
    """
    return default_config_manager.get_protocol_known_issue_config()


def get_report_analyzer_config() -> DifyAppConfig:
    """
    獲取 Report Analyzer 3 配置的便利函數
    
    Returns:
        DifyAppConfig: Report Analyzer 3 配置對象
    """
    return default_config_manager.get_report_analyzer_config()


def get_ai_ocr_config() -> DifyAppConfig:
    """
    獲取 AI OCR 配置的便利函數
    
    Returns:
        DifyAppConfig: AI OCR 配置對象
    """
    return default_config_manager.get_ai_ocr_config()


def get_ocr_function_config() -> DifyAppConfig:
    """
    獲取 OCR Function 配置的便利函數
    
    Returns:
        DifyAppConfig: OCR Function 配置對象
    """
    return default_config_manager.get_ocr_function_config()


def get_saf_intent_analyzer_config() -> DifyAppConfig:
    """
    獲取 SAF Intent Analyzer 配置的便利函數
    
    Returns:
        DifyAppConfig: SAF Intent Analyzer 配置對象
    """
    return default_config_manager.get_saf_intent_analyzer_config()


def get_saf_analyzer_config() -> DifyAppConfig:
    """
    獲取 SAF Analyzer 配置的便利函數
    
    Returns:
        DifyAppConfig: SAF Analyzer 配置對象
    """
    return default_config_manager.get_saf_analyzer_config()


def validate_all_dify_configs() -> Dict[str, bool]:
    """
    驗證所有 Dify 配置的便利函數
    
    Returns:
        Dict[str, bool]: 驗證結果
    """
    return default_config_manager.validate_all_configs()


def get_all_dify_configs_safe() -> Dict[str, Dict[str, Any]]:
    """
    獲取所有安全配置的便利函數
    
    Returns:
        Dict[str, Dict]: 安全配置映射
    """
    return default_config_manager.get_all_safe_configs()


# 向後兼容函數
def get_protocol_guide_config_dict() -> Dict[str, Any]:
    """
    獲取 Protocol Guide 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_protocol_guide_config().to_dict()


def get_rvt_guide_config_dict() -> Dict[str, Any]:
    """
    獲取 RVT Guide 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_rvt_guide_config().to_dict()


def get_protocol_known_issue_config_dict() -> Dict[str, Any]:
    """
    獲取 Protocol Known Issue 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_protocol_known_issue_config().to_dict()


def get_report_analyzer_3_config() -> DifyAppConfig:
    """
    獲取 Report Analyzer 3 配置（別名函數，向後兼容）
    
    Returns:
        DifyAppConfig: Report Analyzer 3 配置對象
    """
    return get_report_analyzer_config()


def get_report_analyzer_3_config_dict() -> Dict[str, Any]:
    """
    獲取 Report Analyzer 3 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_report_analyzer_3_config().to_dict()


def get_ai_ocr_config_dict() -> Dict[str, Any]:
    """
    獲取 AI OCR 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_ai_ocr_config().to_dict()


def get_ocr_function_config_dict() -> Dict[str, Any]:
    """
    獲取 OCR Function 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_ocr_function_config().to_dict()


def get_saf_intent_analyzer_config_dict() -> Dict[str, Any]:
    """
    獲取 SAF Intent Analyzer 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_saf_intent_analyzer_config().to_dict()


def get_saf_analyzer_config_dict() -> Dict[str, Any]:
    """
    獲取 SAF Analyzer 配置字典（向後兼容）
    
    Returns:
        Dict[str, Any]: 配置字典
    """
    return get_saf_analyzer_config().to_dict()