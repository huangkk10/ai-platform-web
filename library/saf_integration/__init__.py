"""
SAF Integration Library
=======================

SAF 外部知識庫整合模組，提供與 SAF API Server 的整合功能。

主要功能：
- SAF API 客戶端（專案查詢、統計資訊）
- 資料轉換（SAF 格式 → Dify 知識庫格式）
- 認證管理
- 快取機制

Endpoints 支援：
- projects: 專案搜尋（完整資訊）
- summary: 專案統計
- project_names: 專案名稱清單（輕量級）

使用範例：
    from library.saf_integration import SAFKnowledgeHandler
    
    handler = SAFKnowledgeHandler()
    result = handler.handle_request(request)

作者：AI Platform Team
創建日期：2025-12-04
"""

# 標記 Library 是否可用
SAF_INTEGRATION_LIBRARY_AVAILABLE = True

# 版本資訊
__version__ = '1.0.0'

# 延遲導入，避免循環依賴
def get_saf_api_client():
    """獲取 SAF API 客戶端"""
    from .api_client import SAFAPIClient
    return SAFAPIClient()


def get_saf_knowledge_handler():
    """獲取 SAF 知識庫處理器"""
    from .handler import get_saf_knowledge_handler as _get_handler
    return _get_handler()


def get_search_service():
    """獲取 SAF 搜尋服務"""
    from .search_service import get_search_service as _get_service
    return _get_service()


def get_data_transformer():
    """獲取 SAF 資料轉換器"""
    from .data_transformer import get_data_transformer as _get_transformer
    return _get_transformer()


def get_available_endpoints():
    """獲取可用的 endpoint 列表"""
    from .endpoint_registry import SAF_ENDPOINTS
    return {
        name: {
            'description': config.get('description', ''),
            'enabled': config.get('enabled', True)
        }
        for name, config in SAF_ENDPOINTS.items()
    }


def get_supported_knowledge_ids():
    """獲取支援的 knowledge_id 列表"""
    from .endpoint_registry import KNOWLEDGE_ID_TO_ENDPOINT
    return list(KNOWLEDGE_ID_TO_ENDPOINT.keys())


def check_saf_health():
    """檢查 SAF API 連線狀態"""
    from .api_client import SAFAPIClient
    client = SAFAPIClient()
    return client.health_check()


# 導出的類別和函數
__all__ = [
    'SAF_INTEGRATION_LIBRARY_AVAILABLE',
    'get_saf_api_client',
    'get_saf_knowledge_handler',
    'get_search_service',
    'get_data_transformer',
    'get_available_endpoints',
    'get_supported_knowledge_ids',
    'check_saf_health',
]
