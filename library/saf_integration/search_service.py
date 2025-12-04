"""
SAF 搜尋服務

處理 SAF 資料的搜尋和過濾邏輯
"""
import logging
from typing import Any, Dict, List, Optional

from .api_client import get_saf_api_client, SAFAPIClient
from .data_transformer import get_data_transformer, SAFDataTransformer

logger = logging.getLogger(__name__)


class SAFSearchService:
    """SAF 搜尋服務"""
    
    def __init__(
        self,
        api_client: Optional[SAFAPIClient] = None,
        transformer: Optional[SAFDataTransformer] = None
    ):
        """
        初始化搜尋服務
        
        Args:
            api_client: SAF API 客戶端（可選）
            transformer: 資料轉換器（可選）
        """
        self.api_client = api_client or get_saf_api_client()
        self.transformer = transformer or get_data_transformer()
    
    def search_projects(
        self,
        query: str,
        top_k: int = 10,
        score_threshold: float = 0.0,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜尋專案
        
        Args:
            query: 搜尋關鍵字
            top_k: 返回前 K 個結果
            score_threshold: 分數閾值
            filters: 額外過濾條件
            
        Returns:
            Dify 格式的搜尋結果
        """
        logger.info(f"搜尋專案: query='{query}', top_k={top_k}, threshold={score_threshold}")
        
        try:
            # 獲取所有專案
            projects = self.api_client.get_all_projects()
            
            if not projects:
                logger.warning("未獲取到任何專案")
                return {"records": []}
            
            # 應用過濾器（如果有）
            if filters:
                projects = self._apply_filters(projects, filters)
            
            # 轉換為 Dify 格式
            result = self.transformer.transform_projects(
                projects=projects,
                query=query,
                score_threshold=score_threshold
            )
            
            # 限制返回數量
            if result["records"]:
                result["records"] = result["records"][:top_k]
            
            logger.info(f"專案搜尋完成: 返回 {len(result['records'])} 個結果")
            
            return result
            
        except Exception as e:
            logger.error(f"搜尋專案失敗: {e}")
            return {"records": []}
    
    def search_summary(
        self,
        project_name: str,
        query: str = "",
        top_k: int = 10,
        score_threshold: float = 0.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜尋專案 Summary
        
        Args:
            project_name: 專案名稱
            query: 搜尋關鍵字（可選）
            top_k: 返回前 K 個結果
            score_threshold: 分數閾值
            
        Returns:
            Dify 格式的搜尋結果
        """
        logger.info(f"搜尋 Summary: project='{project_name}', query='{query}'")
        
        if not project_name:
            logger.warning("未提供專案名稱")
            return {"records": []}
        
        try:
            # 獲取 Summary
            summary_data = self.api_client.get_summary(project_name)
            
            if not summary_data:
                logger.warning(f"未找到專案 '{project_name}' 的 Summary")
                return {"records": []}
            
            # 轉換為 Dify 格式
            result = self.transformer.transform_summary(
                summary_data=summary_data,
                project_name=project_name,
                score_threshold=score_threshold
            )
            
            # 如果有查詢關鍵字，進一步過濾
            if query and result["records"]:
                result["records"] = self._filter_by_query(
                    result["records"],
                    query
                )
            
            # 限制返回數量
            if result["records"]:
                result["records"] = result["records"][:top_k]
            
            logger.info(f"Summary 搜尋完成: 返回 {len(result['records'])} 個結果")
            
            return result
            
        except Exception as e:
            logger.error(f"搜尋 Summary 失敗: {e}")
            return {"records": []}
    
    def search_project_names(
        self,
        query: str = "",
        top_k: int = 20,
        score_threshold: float = 0.0
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        搜尋專案名稱（輕量級）
        
        Args:
            query: 搜尋關鍵字
            top_k: 返回前 K 個結果
            score_threshold: 分數閾值
            
        Returns:
            Dify 格式的搜尋結果
        """
        logger.info(f"搜尋專案名稱: query='{query}', top_k={top_k}")
        
        try:
            # 獲取專案名稱列表
            projects = self.api_client.get_project_names()
            
            if not projects:
                logger.warning("未獲取到任何專案名稱")
                return {"records": []}
            
            # 轉換為 Dify 格式
            result = self.transformer.transform_project_names(
                projects=projects,
                query=query,
                score_threshold=score_threshold
            )
            
            # 限制返回數量
            if result["records"]:
                result["records"] = result["records"][:top_k]
            
            logger.info(f"專案名稱搜尋完成: 返回 {len(result['records'])} 個結果")
            
            return result
            
        except Exception as e:
            logger.error(f"搜尋專案名稱失敗: {e}")
            return {"records": []}
    
    def _apply_filters(
        self,
        projects: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        應用過濾條件
        
        Args:
            projects: 專案列表
            filters: 過濾條件
            
        Returns:
            過濾後的專案列表
        """
        filtered = projects
        
        # 客戶過濾
        if "customer" in filters:
            customer = filters["customer"].lower()
            filtered = [
                p for p in filtered
                if customer in p.get("customer", "").lower()
            ]
        
        # 儲存類型過濾
        if "storage_type" in filters:
            storage_type = filters["storage_type"].lower()
            filtered = [
                p for p in filtered
                if storage_type in p.get("storageType", "").lower()
            ]
        
        # 專案狀態過濾
        if "status" in filters:
            status = filters["status"].lower()
            filtered = [
                p for p in filtered
                if status in p.get("projectStatus", "").lower()
            ]
        
        logger.debug(f"過濾後剩餘 {len(filtered)} 個專案 (原 {len(projects)})")
        
        return filtered
    
    def _filter_by_query(
        self,
        records: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        根據查詢關鍵字過濾記錄
        
        Args:
            records: 記錄列表
            query: 查詢關鍵字
            
        Returns:
            過濾後的記錄列表
        """
        if not query:
            return records
        
        query_lower = query.lower()
        filtered = []
        
        for record in records:
            content = record.get("content", "").lower()
            title = record.get("title", "").lower()
            
            if query_lower in content or query_lower in title:
                # 根據匹配程度調整分數
                if query_lower in title:
                    record["score"] = min(1.0, record["score"] + 0.1)
                filtered.append(record)
        
        return filtered


# 全局搜尋服務實例
_search_service_instance: Optional[SAFSearchService] = None


def get_search_service() -> SAFSearchService:
    """
    獲取全局搜尋服務實例（單例模式）
    
    Returns:
        SAFSearchService 實例
    """
    global _search_service_instance
    if _search_service_instance is None:
        _search_service_instance = SAFSearchService()
    return _search_service_instance
