"""
SAF API Client
==============

SAF API 客戶端，負責與 SAF API Server 通訊。

功能：
- 健康檢查
- 專案列表查詢
- 專案統計查詢
- 認證管理
- 錯誤處理和重試

作者：AI Platform Team
創建日期：2025-12-04
"""

import logging
import requests
from typing import Dict, Any, List, Optional
from django.conf import settings

from .endpoint_registry import SAF_ENDPOINTS, get_endpoint_config
from .auth_manager import SAFAuthManager
from .cache_manager import SAFCacheManager


logger = logging.getLogger(__name__)


class SAFAPIClient:
    """SAF API 客戶端"""
    
    # 預設配置
    DEFAULT_BASE_URL = "http://10.252.170.171:8080"
    DEFAULT_TIMEOUT = 30
    DEFAULT_RETRY_COUNT = 3
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
        use_cache: bool = True
    ):
        """
        初始化 SAF API 客戶端
        
        Args:
            base_url: SAF API 基礎 URL
            timeout: 請求超時時間（秒）
            use_cache: 是否啟用快取
        """
        # 從 settings 或使用預設值
        self.base_url = base_url or getattr(
            settings, 'SAF_API_BASE_URL', self.DEFAULT_BASE_URL
        )
        self.timeout = timeout or getattr(
            settings, 'SAF_API_TIMEOUT', self.DEFAULT_TIMEOUT
        )
        self.retry_count = getattr(
            settings, 'SAF_API_RETRY_COUNT', self.DEFAULT_RETRY_COUNT
        )
        
        # 初始化認證管理器和快取管理器
        self.auth_manager = SAFAuthManager()
        self.cache_manager = SAFCacheManager() if use_cache else None
        
        logger.info(f"SAF API Client 初始化: base_url={self.base_url}")
    
    def health_check(self) -> Dict[str, Any]:
        """
        檢查 SAF API Server 健康狀態
        
        Returns:
            健康狀態資訊
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "healthy",
                    "saf_server": self.base_url,
                    "version": data.get("version", "unknown"),
                    "timestamp": data.get("timestamp", "")
                }
            else:
                return {
                    "status": "unhealthy",
                    "saf_server": self.base_url,
                    "error": f"HTTP {response.status_code}"
                }
                
        except requests.exceptions.Timeout:
            logger.error(f"SAF API 健康檢查超時: {self.base_url}")
            return {
                "status": "unhealthy",
                "saf_server": self.base_url,
                "error": "Connection timeout"
            }
        except requests.exceptions.ConnectionError as e:
            logger.error(f"SAF API 連線失敗: {str(e)}")
            return {
                "status": "unhealthy",
                "saf_server": self.base_url,
                "error": f"Connection error: {str(e)}"
            }
        except Exception as e:
            logger.error(f"SAF API 健康檢查失敗: {str(e)}")
            return {
                "status": "error",
                "saf_server": self.base_url,
                "error": str(e)
            }
    
    def _make_request(
        self,
        endpoint_name: str,
        params: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        發送 API 請求
        
        Args:
            endpoint_name: endpoint 名稱
            params: 額外的查詢參數
            use_cache: 是否使用快取
            
        Returns:
            API 回應資料
        """
        # 獲取 endpoint 配置
        config = get_endpoint_config(endpoint_name)
        if not config:
            logger.error(f"未知的 endpoint: {endpoint_name}")
            return None
        
        if not config.get('enabled', True):
            logger.warning(f"Endpoint 未啟用: {endpoint_name}")
            return None
        
        # 構建 URL 和參數
        url = f"{self.base_url}{config['path']}"
        request_params = {**config.get('params', {}), **(params or {})}
        
        # 檢查快取
        cache_key = f"{endpoint_name}:{str(request_params)}"
        if use_cache and self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.debug(f"使用快取資料: {endpoint_name}")
                return cached_data
        
        # 獲取認證 headers
        headers = self.auth_manager.get_auth_headers()
        
        # 發送請求（帶重試）
        last_error = None
        for attempt in range(self.retry_count):
            try:
                logger.debug(f"SAF API 請求: {url} (嘗試 {attempt + 1}/{self.retry_count})")
                
                response = requests.request(
                    method=config.get('method', 'GET'),
                    url=url,
                    params=request_params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # 檢查 SAF API 回應格式
                    if data.get('success'):
                        result = data.get('data', {})
                        
                        # 存入快取
                        if self.cache_manager:
                            self.cache_manager.set(cache_key, result)
                        
                        logger.info(f"SAF API 請求成功: {endpoint_name}")
                        return result
                    else:
                        logger.warning(f"SAF API 回應失敗: {data.get('message', 'Unknown error')}")
                        return None
                else:
                    logger.warning(f"SAF API HTTP 錯誤: {response.status_code}")
                    last_error = f"HTTP {response.status_code}"
                    
            except requests.exceptions.Timeout:
                logger.warning(f"SAF API 請求超時 (嘗試 {attempt + 1})")
                last_error = "Timeout"
            except requests.exceptions.ConnectionError as e:
                logger.warning(f"SAF API 連線錯誤: {str(e)}")
                last_error = str(e)
            except Exception as e:
                logger.error(f"SAF API 請求異常: {str(e)}")
                last_error = str(e)
                break  # 非預期錯誤不重試
        
        logger.error(f"SAF API 請求失敗: {endpoint_name}, 錯誤: {last_error}")
        return None
    
    def get_projects(
        self,
        page: int = 1,
        size: int = 200
    ) -> List[Dict[str, Any]]:
        """
        獲取專案列表
        
        Args:
            page: 頁碼
            size: 每頁數量
            
        Returns:
            專案列表
        """
        result = self._make_request(
            endpoint_name="projects",
            params={"page": page, "size": size}
        )
        
        if result:
            items = result.get('items', [])
            logger.info(f"獲取到 {len(items)} 個專案 (總計: {result.get('total', 0)})")
            return items
        
        return []
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """
        獲取所有專案（自動分頁）
        
        注意: SAF API 限制每頁最大 100 筆
        
        Returns:
            所有專案列表
        """
        all_projects = []
        page = 1
        page_size = 100  # SAF API 限制最大 100
        
        while True:
            result = self._make_request(
                endpoint_name="projects",
                params={"page": page, "size": page_size},
                use_cache=False  # 分頁查詢不使用快取
            )
            
            if not result:
                break
            
            items = result.get('items', [])
            all_projects.extend(items)
            
            total = result.get('total', 0)
            if len(all_projects) >= total or len(items) == 0:
                break
            
            page += 1
        
        logger.info(f"獲取所有專案完成: 共 {len(all_projects)} 個")
        return all_projects
    
    def get_summary(self) -> Optional[Dict[str, Any]]:
        """
        獲取專案統計摘要
        
        Returns:
            統計摘要資料
        """
        return self._make_request(endpoint_name="summary")
    
    def get_project_names(self) -> List[Dict[str, Any]]:
        """
        獲取所有專案名稱（輕量級）
        
        注意: 使用 get_all_projects() 獲取完整專案列表
        
        Returns:
            包含專案名稱和客戶的列表
        """
        projects = self.get_all_projects()
        return projects


# 全局客戶端實例
_client_instance: Optional[SAFAPIClient] = None


def get_saf_api_client() -> SAFAPIClient:
    """
    獲取全局 SAF API 客戶端實例（單例模式）
    
    Returns:
        SAFAPIClient 實例
    """
    global _client_instance
    if _client_instance is None:
        _client_instance = SAFAPIClient()
    return _client_instance
