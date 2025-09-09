"""
Dify 知識庫管理器
提供知識庫的創建、查詢、更新、刪除功能
"""

from typing import Dict, List, Optional, Any
from .client import DifyClient


class DatasetManager:
    """知識庫管理器"""
    
    def __init__(self, client: DifyClient):
        """
        初始化知識庫管理器
        
        Args:
            client: Dify API 客戶端
        """
        self.client = client
    
    def create_dataset(self, name: str, description: str = "", permission: str = "only_me") -> Dict:
        """
        創建知識庫
        
        Args:
            name: 知識庫名稱
            description: 知識庫描述
            permission: 權限設置 (only_me, all_team_members)
            
        Returns:
            創建的知識庫信息
        """
        data = {
            "name": name,
            "description": description,
            "permission": permission,
            "indexing_technique": "economy",  # 使用經濟模式
            "embedding_model": "",  # 空字符串表示使用默認
            "embedding_model_provider": "",
            "retrieval_model": {
                "search_method": "semantic_search",
                "reranking_enable": False,
                "reranking_model": {
                    "reranking_provider_name": "",
                    "reranking_model_name": ""
                },
                "top_k": 2,
                "score_threshold_enabled": False
            }
        }
        
        return self.client.post("/v1/datasets", data)
    
    def list_datasets(self, page: int = 1, limit: int = 20) -> Dict:
        """
        獲取知識庫列表
        
        Args:
            page: 頁數
            limit: 每頁數量
            
        Returns:
            知識庫列表
        """
        params = {"page": page, "limit": limit}
        return self.client.get("/v1/datasets", params)
    
    def get_dataset(self, dataset_id: str) -> Dict:
        """
        獲取知識庫詳情
        
        Args:
            dataset_id: 知識庫 ID
            
        Returns:
            知識庫詳情
        """
        return self.client.get(f"/v1/datasets/{dataset_id}")
    
    def update_dataset(self, dataset_id: str, name: str = None, description: str = None) -> Dict:
        """
        更新知識庫
        
        Args:
            dataset_id: 知識庫 ID
            name: 新名稱
            description: 新描述
            
        Returns:
            更新後的知識庫信息
        """
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
            
        return self.client.put(f"/v1/datasets/{dataset_id}", data)
    
    def delete_dataset(self, dataset_id: str) -> Dict:
        """
        刪除知識庫
        
        Args:
            dataset_id: 知識庫 ID
            
        Returns:
            刪除結果
        """
        return self.client.delete(f"/v1/datasets/{dataset_id}")