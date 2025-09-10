"""
Dify 知識庫管理器
提供知識庫的創建、查詢、更新、刪除功能
"""

import time
from typing import Dict, List, Optional, Any, Union
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
    
    def create_team_dataset(self, name: str, description: str = "", permission: str = "all_team_members") -> Dict:
        """
        創建團隊共享知識庫
        
        Args:
            name: 知識庫名稱
            description: 知識庫描述
            permission: 權限設置 (only_me, all_team_members, public)
            
        Returns:
            創建的知識庫信息
        """
        # 為名稱添加時間戳避免重複
        unique_name = f"{name}_{int(time.time())}"
        
        data = {
            "name": unique_name,
            "description": description,
            "permission": permission,
            "indexing_technique": "economy",
            "embedding_model": "",
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
    
    def create_multiple_datasets_with_permissions(self, base_name: str, description_prefix: str = "") -> List[Dict]:
        """
        創建多個不同權限的知識庫用於測試
        
        Args:
            base_name: 基礎名稱
            description_prefix: 描述前綴
            
        Returns:
            成功創建的知識庫列表
        """
        test_configs = [
            {
                'name': f'{base_name}_團隊共享',
                'description': f'{description_prefix}所有團隊成員都能看到的知識庫',
                'permission': 'all_team_members'
            },
            {
                'name': f'{base_name}_僅限自己',
                'description': f'{description_prefix}僅限創建者查看的知識庫',
                'permission': 'only_me'
            }
        ]
        
        successful_datasets = []
        
        for config in test_configs:
            try:
                result = self.create_team_dataset(
                    config['name'],
                    config['description'],
                    config['permission']
                )
                
                if result.get('id'):
                    successful_datasets.append({
                        'id': result['id'],
                        'name': result.get('name'),
                        'permission': result.get('permission'),
                        'created_by': result.get('created_by'),
                        'config': config
                    })
                    
            except Exception as e:
                print(f"❌ 創建知識庫失敗 ({config['name']}): {e}")
                
        return successful_datasets
    
    def get_dataset_direct_url(self, dataset_id: str, base_url: str = None) -> str:
        """
        獲取知識庫的直接訪問 URL
        
        Args:
            dataset_id: 知識庫 ID
            base_url: 基礎 URL，如果不提供則使用客戶端的 base_url
            
        Returns:
            直接訪問 URL
        """
        if base_url is None:
            base_url = self.client.base_url
        
        return f"{base_url}/datasets/{dataset_id}"
    
    def search_datasets_by_name(self, keyword: str, page: int = 1, limit: int = 20) -> Dict:
        """
        按名稱搜尋知識庫
        
        Args:
            keyword: 搜尋關鍵字
            page: 頁數
            limit: 每頁數量
            
        Returns:
            搜尋結果
        """
        params = {
            "page": page,
            "limit": limit,
            "keyword": keyword
        }
        return self.client.get("/v1/datasets", params)