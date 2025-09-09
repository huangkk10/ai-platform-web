"""
Dify 文檔管理器
提供文檔的上傳、查詢、更新、刪除功能
"""

from typing import Dict, List, Optional, Any
from .client import DifyClient


class DocumentManager:
    """文檔管理器"""
    
    def __init__(self, client: DifyClient):
        """
        初始化文檔管理器
        
        Args:
            client: Dify API 客戶端
        """
        self.client = client
    
    def create_document_by_text(self, dataset_id: str, name: str, text: str) -> Dict:
        """
        通過文本創建文檔
        
        Args:
            dataset_id: 知識庫 ID
            name: 文檔名稱
            text: 文檔內容
            
        Returns:
            創建的文檔信息
        """
        data = {
            "name": name,
            "text": text,
            "indexing_technique": "economy",
            "process_rule": {
                "rules": {
                    "pre_processing_rules": [
                        {
                            "id": "remove_extra_spaces",
                            "enabled": True
                        },
                        {
                            "id": "remove_urls_emails",
                            "enabled": False
                        }
                    ],
                    "segmentation": {
                        "separator": "###",
                        "max_tokens": 1000
                    }
                },
                "mode": "custom"
            }
        }
        
        return self.client.post(f"/v1/datasets/{dataset_id}/documents", data)
    
    def list_documents(self, dataset_id: str, page: int = 1, limit: int = 20, keyword: str = "") -> Dict:
        """
        獲取文檔列表
        
        Args:
            dataset_id: 知識庫 ID
            page: 頁數
            limit: 每頁數量
            keyword: 關鍵字搜索
            
        Returns:
            文檔列表
        """
        params = {
            "page": page,
            "limit": limit,
            "keyword": keyword
        }
        return self.client.get(f"/v1/datasets/{dataset_id}/documents", params)
    
    def get_document(self, dataset_id: str, document_id: str) -> Dict:
        """
        獲取文檔詳情
        
        Args:
            dataset_id: 知識庫 ID
            document_id: 文檔 ID
            
        Returns:
            文檔詳情
        """
        return self.client.get(f"/v1/datasets/{dataset_id}/documents/{document_id}")
    
    def update_document(self, dataset_id: str, document_id: str, name: str = None, text: str = None) -> Dict:
        """
        更新文檔
        
        Args:
            dataset_id: 知識庫 ID
            document_id: 文檔 ID
            name: 新名稱
            text: 新內容
            
        Returns:
            更新後的文檔信息
        """
        data = {}
        if name is not None:
            data["name"] = name
        if text is not None:
            data["text"] = text
            
        return self.client.put(f"/v1/datasets/{dataset_id}/documents/{document_id}", data)
    
    def delete_document(self, dataset_id: str, document_id: str) -> Dict:
        """
        刪除文檔
        
        Args:
            dataset_id: 知識庫 ID
            document_id: 文檔 ID
            
        Returns:
            刪除結果
        """
        return self.client.delete(f"/v1/datasets/{dataset_id}/documents/{document_id}")
    
    def retrieve_documents(self, dataset_id: str, query: str, top_k: int = 2, score_threshold: float = 0.5) -> Dict:
        """
        檢索文檔
        
        Args:
            dataset_id: 知識庫 ID
            query: 查詢文本
            top_k: 返回文檔數量
            score_threshold: 相似度閾值
            
        Returns:
            檢索結果
        """
        data = {
            "query": query,
            "retrieval_setting": {
                "top_k": top_k,
                "score_threshold": score_threshold
            }
        }
        
        return self.client.post(f"/v1/datasets/{dataset_id}/retrieve", data)