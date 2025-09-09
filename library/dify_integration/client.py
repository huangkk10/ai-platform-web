"""
Dify API 客戶端
提供對 Dify API 的統一訪問接口
"""

import requests
from typing import Dict, List, Optional, Any
import json


class DifyClient:
    """Dify API 客戶端"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.dify.ai"):
        """
        初始化 Dify 客戶端
        
        Args:
            api_key: Dify API 金鑰
            base_url: API 基礎 URL
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        """
        發送 API 請求
        
        Args:
            method: HTTP 方法
            endpoint: API 端點
            data: 請求數據
            params: 查詢參數
            
        Returns:
            API 響應數據
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                json=data,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"API 請求失敗: {str(e)}")
    
    def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """GET 請求"""
        return self.make_request('GET', endpoint, params=params)
    
    def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """POST 請求"""
        return self.make_request('POST', endpoint, data=data)
    
    def put(self, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """PUT 請求"""
        return self.make_request('PUT', endpoint, data=data)
    
    def delete(self, endpoint: str) -> Dict:
        """DELETE 請求"""
        return self.make_request('DELETE', endpoint)