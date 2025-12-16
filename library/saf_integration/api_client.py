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
        size: int = 100  # SAF API 最大限制 100
    ) -> List[Dict[str, Any]]:
        """
        獲取專案列表
        
        Args:
            page: 頁碼
            size: 每頁數量 (SAF API 最大限制 100)
            
        Returns:
            專案列表
        """
        # 確保 size 不超過 API 限制
        size = min(size, 100)
        
        result = self._make_request(
            endpoint_name="projects",
            params={"page": page, "size": size}
        )
        
        if result:
            items = result.get('items', [])
            logger.info(f"獲取到 {len(items)} 個專案 (總計: {result.get('total', 0)})")
            return items
        
        return []
    
    def get_all_projects(self, flatten: bool = True) -> List[Dict[str, Any]]:
        """
        獲取所有專案（自動分頁）
        
        注意: SAF API 限制每頁最大 100 筆
        
        Args:
            flatten: 是否展開 children 子專案到同一層級
                    - True: 返回所有專案（含子專案）的平坦列表
                    - False: 保留原始階層結構
        
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
        
        # 展開 children 子專案
        if flatten:
            all_projects = self._flatten_projects(all_projects)
            logger.info(f"獲取所有專案完成（含子專案）: 共 {len(all_projects)} 個")
        else:
            logger.info(f"獲取所有專案完成（頂層）: 共 {len(all_projects)} 個")
        
        return all_projects
    
    def _flatten_projects(self, projects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        遞迴展開專案列表中的 children 子專案
        
        Args:
            projects: 專案列表
            
        Returns:
            展開後的平坦專案列表
        """
        result = []
        for project in projects:
            result.append(project)
            children = project.get('children', [])
            if children:
                result.extend(self._flatten_projects(children))
        return result
    
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
    
    def get_project_uid_by_name(self, project_name: str) -> Optional[str]:
        """
        根據專案名稱獲取專案 UID（帶快取）
        
        Args:
            project_name: 專案名稱
            
        Returns:
            專案 UID，如果找不到則返回 None
        """
        if not project_name:
            return None
        
        # 檢查快取
        cache_key = f"project_uid:{project_name.lower()}"
        if self.cache_manager:
            cached_uid = self.cache_manager.get(cache_key)
            if cached_uid:
                logger.debug(f"從快取獲取 project_uid: {project_name} -> {cached_uid}")
                return cached_uid
        
        # 從專案列表中查找
        projects = self.get_all_projects()
        project_name_lower = project_name.lower()
        
        for project in projects:
            # 精確匹配
            if project.get('projectName', '').lower() == project_name_lower:
                uid = project.get('projectUid')
                # 存入快取
                if self.cache_manager and uid:
                    self.cache_manager.set(cache_key, uid)
                logger.info(f"找到專案 UID: {project_name} -> {uid}")
                return uid
        
        # 模糊匹配（專案名稱包含搜尋詞）
        for project in projects:
            if project_name_lower in project.get('projectName', '').lower():
                uid = project.get('projectUid')
                if self.cache_manager and uid:
                    self.cache_manager.set(cache_key, uid)
                logger.info(f"模糊匹配專案 UID: {project_name} -> {project.get('projectName')} -> {uid}")
                return uid
        
        logger.warning(f"找不到專案: {project_name}")
        return None
    
    def get_project_test_summary(self, project_uid: str) -> Optional[Dict[str, Any]]:
        """
        獲取專案測試摘要
        
        Args:
            project_uid: 專案 UID
            
        Returns:
            測試摘要資料
        """
        if not project_uid:
            logger.error("project_uid 不能為空")
            return None
        
        # 獲取 endpoint 配置
        config = get_endpoint_config("project_test_summary")
        if not config:
            logger.error("找不到 project_test_summary endpoint 配置")
            return None
        
        # 構建 URL（替換 path_params）
        path = config['path'].replace('{project_uid}', project_uid)
        url = f"{self.base_url}{path}"
        
        # 檢查快取
        cache_key = f"test_summary:{project_uid}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"從快取獲取測試摘要: {project_uid}")
                return cached_data
        
        # 獲取認證 headers
        headers = self.auth_manager.get_auth_headers()
        
        try:
            logger.info(f"調用 Test Summary API: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data')
                    # 存入快取
                    if self.cache_manager and result:
                        self.cache_manager.set(cache_key, result)
                    logger.info(f"獲取測試摘要成功: {project_uid}")
                    return result
                else:
                    logger.warning(f"Test Summary API 返回失敗: {data.get('message')}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"專案不存在: {project_uid}")
                return None
            else:
                logger.error(f"Test Summary API HTTP 錯誤: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Test Summary API 請求超時: {project_uid}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Test Summary API 連線錯誤: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Test Summary API 請求異常: {str(e)}")
            return None

    def get_firmware_summary(self, project_uid: str) -> Optional[Dict[str, Any]]:
        """
        獲取 Firmware 詳細統計摘要
        
        使用 /api/v1/projects/{project_uid}/firmware-summary API
        
        提供的資訊：
        - overview: 總測試項目、Pass/Fail、完成率、通過率
        - sample_stats: 樣本總數、已使用、使用率
        - test_item_stats: 項目數、執行率、失敗率
        
        Args:
            project_uid: 專案 UID（特定 FW 版本的唯一識別碼）
            
        Returns:
            Firmware 統計資料，如果失敗則返回 None
        """
        if not project_uid:
            logger.warning("get_firmware_summary: project_uid 為空")
            return None
        
        # 構建 URL
        url = f"{self.base_url}/api/v1/projects/{project_uid}/firmware-summary"
        
        # 檢查快取
        cache_key = f"firmware_summary:{project_uid}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"從快取獲取 Firmware 統計: {project_uid}")
                return cached_data
        
        # 獲取認證 headers
        headers = self.auth_manager.get_auth_headers()
        
        try:
            logger.info(f"調用 Firmware Summary API: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data')
                    # 存入快取（TTL 較短，因為統計資料可能常更新）
                    if self.cache_manager and result:
                        self.cache_manager.set(cache_key, result, ttl=300)  # 5 分鐘
                    logger.info(f"獲取 Firmware 統計成功: {project_uid}")
                    return result
                else:
                    logger.warning(f"Firmware Summary API 返回失敗: {data.get('message')}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"專案不存在: {project_uid}")
                return None
            else:
                logger.error(f"Firmware Summary API HTTP 錯誤: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Firmware Summary API 請求超時: {project_uid}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Firmware Summary API 連線錯誤: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Firmware Summary API 請求異常: {str(e)}")
            return None

    def get_project_test_details(self, project_uid: str) -> Optional[Dict[str, Any]]:
        """
        獲取專案測試詳細資料（包含所有 test items 明細）
        
        使用 /api/v1/projects/{project_uid}/test-details API
        
        提供的資訊：
        - project_uid: 專案 UID
        - project_name: 專案名稱
        - fw_name: Firmware 名稱
        - sub_version: 子版本
        - capacities: 可用容量列表
        - total_items: 測試項目總數
        - details: 每個測試項目的詳細資料（含 category、test_item、各容量結果）
        - summary: 總體統計（ongoing、passed、conditional_passed、failed、interrupted）
        
        欄位順序：Ongoing / Passed / Conditional Passed / Failed / Interrupted
        
        Args:
            project_uid: 專案 UID（特定 FW 版本的唯一識別碼）
            
        Returns:
            測試詳細資料，如果失敗則返回 None
        """
        if not project_uid:
            logger.warning("get_project_test_details: project_uid 為空")
            return None
        
        # 獲取 endpoint 配置
        config = get_endpoint_config("project_test_details")
        if not config:
            logger.error("找不到 project_test_details endpoint 配置")
            return None
        
        # 構建 URL
        path = config['path'].replace('{project_uid}', project_uid)
        url = f"{self.base_url}{path}"
        
        # 檢查快取
        cache_key = f"test_details:{project_uid}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data:
                logger.debug(f"從快取獲取測試詳細資料: {project_uid}")
                return cached_data
        
        # 獲取認證 headers
        headers = self.auth_manager.get_auth_headers()
        
        try:
            logger.info(f"調用 Test Details API: {url}")
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    result = data.get('data')
                    # 存入快取（TTL 較短，因為測試資料可能常更新）
                    if self.cache_manager and result:
                        self.cache_manager.set(cache_key, result, ttl=300)  # 5 分鐘
                    logger.info(f"獲取測試詳細資料成功: {project_uid}")
                    return result
                else:
                    logger.warning(f"Test Details API 返回失敗: {data.get('message')}")
                    return None
            elif response.status_code == 404:
                logger.warning(f"專案不存在: {project_uid}")
                return None
            else:
                logger.error(f"Test Details API HTTP 錯誤: {response.status_code}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"Test Details API 請求超時: {project_uid}")
            return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Test Details API 連線錯誤: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Test Details API 請求異常: {str(e)}")
            return None

    def get_known_issues(
        self,
        project_ids: List[int] = None,
        root_ids: List[int] = None,
        show_disabled: bool = True
    ) -> List[Dict[str, Any]]:
        """
        獲取 Known Issues (Phase 15 新增)
        
        使用 POST /api/v1/projects/known-issues API
        
        Args:
            project_ids: 專案 ID 列表 (對應 API 的 project_id[] 參數)
            root_ids: Root ID 列表 (對應 API 的 root_id[] 參數)
            show_disabled: 是否顯示已停用的 Issues (預設 True)
            
        Returns:
            Known Issues 列表，每個 Issue 包含:
            - id: Issue 內部 ID
            - project_id: 專案 ID
            - project_name: 專案名稱
            - root_id: Root ID
            - test_item_name: 測試項目名稱
            - issue_id: Issue 識別碼
            - case_name: 案例名稱
            - case_path: 案例路徑
            - created_by: 建立者
            - created_at: 建立時間
            - jira_id: JIRA ID
            - jira_link: JIRA 連結
            - note: 備註
            - is_enable: 是否啟用
        """
        url = f"{self.base_url}/api/v1/projects/known-issues"
        
        # 構建請求參數
        params = {
            "show_disable": show_disabled
        }
        
        # 添加 project_id[] 參數
        if project_ids:
            for pid in project_ids:
                if 'project_id[]' not in params:
                    params['project_id[]'] = []
                params['project_id[]'].append(pid)
        
        # 添加 root_id[] 參數
        if root_ids:
            for rid in root_ids:
                if 'root_id[]' not in params:
                    params['root_id[]'] = []
                params['root_id[]'].append(rid)
        
        # 檢查快取
        cache_key = f"known_issues:{str(project_ids)}:{str(root_ids)}:{show_disabled}"
        if self.cache_manager:
            cached_data = self.cache_manager.get(cache_key)
            if cached_data is not None:
                logger.debug(f"從快取獲取 Known Issues")
                return cached_data
        
        # 獲取認證 headers
        headers = self.auth_manager.get_auth_headers()
        headers['Content-Type'] = 'application/json'
        
        # 構建 POST 請求的 body
        # SAF API 使用 form 參數格式
        form_data = {
            "show_disable": show_disabled
        }
        if project_ids:
            form_data["project_id[]"] = project_ids
        if root_ids:
            form_data["root_id[]"] = root_ids
        
        try:
            logger.info(f"調用 Known Issues API: {url}, project_ids={project_ids}")
            
            # SAF API 使用 POST 請求
            response = requests.post(
                url,
                headers=headers,
                data=form_data,  # 使用 form data 格式
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    # SAF API 返回格式: {"success": true, "data": {"items": [...], "total": N}}
                    raw_data = data.get('data', {})
                    if isinstance(raw_data, dict):
                        result = raw_data.get('items', [])
                    else:
                        result = raw_data if isinstance(raw_data, list) else []
                    
                    # 存入快取（TTL 5 分鐘，Known Issues 可能常更新）
                    if self.cache_manager and result:
                        self.cache_manager.set(cache_key, result, ttl=300)
                    
                    logger.info(f"獲取 Known Issues 成功: {len(result)} 筆")
                    return result
                else:
                    logger.warning(f"Known Issues API 返回失敗: {data.get('message')}")
                    return []
            elif response.status_code == 404:
                logger.warning(f"Known Issues API 路徑不存在")
                return []
            else:
                logger.error(f"Known Issues API HTTP 錯誤: {response.status_code}")
                return []
                
        except requests.exceptions.Timeout:
            logger.error(f"Known Issues API 請求超時")
            return []
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Known Issues API 連線錯誤: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"Known Issues API 請求異常: {str(e)}")
            return []


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
