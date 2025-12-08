"""
SAF Endpoint Registry
=====================

SAF API 端點定義註冊表，管理所有可用的 SAF API endpoint 配置。

作者：AI Platform Team
創建日期：2025-12-04
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field


@dataclass
class EndpointConfig:
    """API 端點配置"""
    path: str                          # 端點路徑
    method: str = "GET"                # HTTP 方法
    description: str = ""              # 端點說明
    params: Dict[str, Any] = field(default_factory=dict)  # 預設參數
    search_fields: List[str] = field(default_factory=list)  # 搜尋欄位
    transformer: str = ""              # 資料轉換器名稱
    enabled: bool = True               # 是否啟用
    extract_fields: List[str] = field(default_factory=list)  # 要提取的欄位


# SAF API Endpoint 定義
# 注意: SAF API 的 size 參數最大值為 100，超過會返回 422 錯誤
SAF_ENDPOINTS: Dict[str, Dict[str, Any]] = {
    "projects": {
        "path": "/api/v1/projects",
        "method": "GET",
        "description": "查詢 SAF 專案列表（完整資訊）",
        "params": {
            "page": 1,
            "size": 100  # SAF API 最大限制 100
        },
        "search_fields": ["projectName", "customer", "controller", "nand", "fw", "productCategory", "pl"],
        "transformer": "project_to_dify_record",
        "enabled": True
    },
    "summary": {
        "path": "/api/v1/projects/summary",
        "method": "GET",
        "description": "查詢 SAF 專案統計摘要",
        "params": {},
        "search_fields": [],
        "transformer": "summary_to_dify_record",
        "enabled": True
    },
    "project_names": {
        "path": "/api/v1/projects",
        "method": "GET",
        "description": "取得所有專案名稱清單（輕量級）",
        "params": {
            "page": 1,
            "size": 100  # SAF API 最大限制 100（需分頁獲取全部）
        },
        "search_fields": ["projectName"],
        "transformer": "project_names_to_dify_record",
        "enabled": True,
        "extract_fields": ["projectName", "customer", "controller"]  # 只提取需要的欄位
    },
    # 🔮 未來擴展
    "project_detail": {
        "path": "/api/v1/projects/{project_id}",
        "method": "GET",
        "description": "查詢單一專案詳情",
        "params": {},
        "path_params": ["project_id"],
        "transformer": "project_detail_to_dify_record",
        "enabled": False  # 尚未啟用
    },
    # 🆕 Phase 3: Test Summary API
    "project_test_summary": {
        "path": "/api/v1/projects/{project_uid}/test-summary",
        "method": "GET",
        "description": "查詢專案測試結果摘要（按類別和容量）",
        "params": {},
        "path_params": ["project_uid"],
        "transformer": "test_summary_to_dify_record",
        "enabled": True
    }
}


# Knowledge ID 到 Endpoint 的映射
KNOWLEDGE_ID_TO_ENDPOINT: Dict[str, str] = {
    "saf_projects": "projects",         # 專案搜尋 → projects API
    "saf_summary": "summary",           # 專案統計 → summary API
    "saf_project_names": "project_names",  # 專案名稱清單
    "saf_db": "projects",               # 預設（向後相容）
}


def get_endpoint_config(endpoint_name: str) -> Optional[Dict[str, Any]]:
    """
    獲取指定 endpoint 的配置
    
    Args:
        endpoint_name: endpoint 名稱
        
    Returns:
        endpoint 配置，如果不存在則返回 None
    """
    return SAF_ENDPOINTS.get(endpoint_name)


def get_endpoint_by_knowledge_id(knowledge_id: str) -> str:
    """
    根據 knowledge_id 獲取對應的 endpoint
    
    Args:
        knowledge_id: Dify 知識庫 ID
        
    Returns:
        對應的 endpoint 名稱，預設為 'projects'
    """
    return KNOWLEDGE_ID_TO_ENDPOINT.get(knowledge_id, "projects")


def list_enabled_endpoints() -> Dict[str, Dict[str, Any]]:
    """
    列出所有啟用的 endpoints
    
    Returns:
        啟用的 endpoint 配置字典
    """
    return {
        name: config 
        for name, config in SAF_ENDPOINTS.items() 
        if config.get('enabled', True)
    }


def is_endpoint_enabled(endpoint_name: str) -> bool:
    """
    檢查 endpoint 是否啟用
    
    Args:
        endpoint_name: endpoint 名稱
        
    Returns:
        是否啟用
    """
    config = SAF_ENDPOINTS.get(endpoint_name)
    return config.get('enabled', False) if config else False


def is_valid_knowledge_id(knowledge_id: str) -> bool:
    """
    檢查 knowledge_id 是否有效
    
    Args:
        knowledge_id: Dify 知識庫 ID
        
    Returns:
        是否有效
    """
    return knowledge_id in KNOWLEDGE_ID_TO_ENDPOINT
