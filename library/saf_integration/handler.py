"""
SAF Knowledge Handler

Dify 外部知識庫的主處理器，處理來自 Dify 的請求並返回相應結果
"""
import logging
from typing import Any, Dict, List, Optional

from .endpoint_registry import (
    SAF_ENDPOINTS,
    KNOWLEDGE_ID_TO_ENDPOINT,
    get_endpoint_config,
    is_valid_knowledge_id
)
from .search_service import get_search_service, SAFSearchService
from .api_client import get_saf_api_client

logger = logging.getLogger(__name__)


class SAFKnowledgeHandler:
    """SAF 知識庫處理器"""
    
    def __init__(self, search_service: Optional[SAFSearchService] = None):
        """
        初始化處理器
        
        Args:
            search_service: 搜尋服務（可選）
        """
        self.search_service = search_service or get_search_service()
    
    def handle_retrieval(
        self,
        knowledge_id: str,
        query: str,
        retrieval_setting: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        處理 Dify 外部知識庫檢索請求
        
        這是主要的入口方法，根據 knowledge_id 路由到不同的處理方法
        
        Args:
            knowledge_id: 知識庫 ID (saf_projects, saf_summary, saf_project_names)
            query: 搜尋查詢
            retrieval_setting: 檢索設定
                - top_k: 返回結果數量
                - score_threshold: 分數閾值
                
        Returns:
            Dify 格式的回應:
            {
                "records": [
                    {
                        "content": str,
                        "score": float,
                        "title": str,
                        "metadata": dict
                    }
                ]
            }
        """
        logger.info(f"處理 SAF 知識庫請求: knowledge_id='{knowledge_id}', query='{query}'")
        
        # 驗證 knowledge_id
        if not is_valid_knowledge_id(knowledge_id):
            logger.error(f"無效的 knowledge_id: {knowledge_id}")
            return self._error_response(
                f"無效的 knowledge_id: {knowledge_id}。有效值: {list(KNOWLEDGE_ID_TO_ENDPOINT.keys())}"
            )
        
        # 解析檢索設定
        retrieval_setting = retrieval_setting or {}
        top_k = retrieval_setting.get("top_k", 10)
        score_threshold = retrieval_setting.get("score_threshold", 0.0)
        
        # 路由到對應的處理方法
        endpoint_type = KNOWLEDGE_ID_TO_ENDPOINT.get(knowledge_id)
        
        try:
            if endpoint_type == "projects":
                return self._handle_projects(query, top_k, score_threshold)
            
            elif endpoint_type == "summary":
                return self._handle_summary(query, top_k, score_threshold)
            
            elif endpoint_type == "project_names":
                return self._handle_project_names(query, top_k, score_threshold)
            
            else:
                logger.error(f"未實現的端點類型: {endpoint_type}")
                return self._error_response(f"未實現的端點類型: {endpoint_type}")
                
        except Exception as e:
            logger.error(f"處理請求失敗: {e}", exc_info=True)
            return self._error_response(f"處理請求時發生錯誤: {str(e)}")
    
    def _handle_projects(
        self,
        query: str,
        top_k: int,
        score_threshold: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        處理專案搜尋請求
        
        Args:
            query: 搜尋關鍵字
            top_k: 返回數量
            score_threshold: 分數閾值
            
        Returns:
            搜尋結果
        """
        logger.debug(f"處理專案搜尋: query='{query}', top_k={top_k}")
        
        return self.search_service.search_projects(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold
        )
    
    def _handle_summary(
        self,
        query: str,
        top_k: int,
        score_threshold: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        處理 Summary 搜尋請求
        
        查詢格式: "專案名稱" 或 "專案名稱 關鍵字"
        
        Args:
            query: 搜尋查詢（包含專案名稱）
            top_k: 返回數量
            score_threshold: 分數閾值
            
        Returns:
            搜尋結果
        """
        logger.debug(f"處理 Summary 搜尋: query='{query}', top_k={top_k}")
        
        # 解析查詢：第一個詞作為專案名稱，其餘作為搜尋關鍵字
        parts = query.strip().split(None, 1)
        
        if not parts:
            return self._error_response("請提供專案名稱")
        
        project_name = parts[0]
        search_query = parts[1] if len(parts) > 1 else ""
        
        return self.search_service.search_summary(
            project_name=project_name,
            query=search_query,
            top_k=top_k,
            score_threshold=score_threshold
        )
    
    def _handle_project_names(
        self,
        query: str,
        top_k: int,
        score_threshold: float
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        處理專案名稱搜尋請求（輕量級）
        
        Args:
            query: 搜尋關鍵字
            top_k: 返回數量
            score_threshold: 分數閾值
            
        Returns:
            搜尋結果
        """
        logger.debug(f"處理專案名稱搜尋: query='{query}', top_k={top_k}")
        
        return self.search_service.search_project_names(
            query=query,
            top_k=top_k,
            score_threshold=score_threshold
        )
    
    def _error_response(self, message: str) -> Dict[str, Any]:
        """
        生成錯誤回應
        
        Args:
            message: 錯誤訊息
            
        Returns:
            Dify 格式的錯誤回應
        """
        return {
            "records": [
                {
                    "content": f"錯誤: {message}",
                    "score": 0.0,
                    "title": "錯誤",
                    "metadata": {
                        "source": "saf_error",
                        "error": True,
                        "message": message
                    }
                }
            ]
        }
    
    def get_supported_knowledge_ids(self) -> List[str]:
        """
        獲取支援的 knowledge_id 列表
        
        Returns:
            knowledge_id 列表
        """
        return list(KNOWLEDGE_ID_TO_ENDPOINT.keys())
    
    def get_endpoint_info(self, knowledge_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取端點資訊
        
        Args:
            knowledge_id: 知識庫 ID
            
        Returns:
            端點配置，如果不存在則返回 None
        """
        endpoint_type = KNOWLEDGE_ID_TO_ENDPOINT.get(knowledge_id)
        if endpoint_type:
            return get_endpoint_config(endpoint_type)
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """
        健康檢查
        
        Returns:
            健康狀態資訊
        """
        api_client = get_saf_api_client()
        saf_health = api_client.health_check()
        
        return {
            "status": "healthy" if saf_health["status"] == "healthy" else "degraded",
            "saf_server": saf_health,
            "supported_knowledge_ids": self.get_supported_knowledge_ids(),
            "endpoints": list(SAF_ENDPOINTS.keys())
        }


# 全局處理器實例
_handler_instance: Optional[SAFKnowledgeHandler] = None


def get_saf_knowledge_handler() -> SAFKnowledgeHandler:
    """
    獲取全局 SAF 知識庫處理器實例（單例模式）
    
    Returns:
        SAFKnowledgeHandler 實例
    """
    global _handler_instance
    if _handler_instance is None:
        _handler_instance = SAFKnowledgeHandler()
    return _handler_instance
