"""
TestCategorySearchHandler - 跨專案測試類別搜尋
==============================================

處理「哪些案子有測試過 XXX？」這類跨專案的測試類別搜尋請求。

意圖類型：query_projects_by_test_category
用戶問法範例：
- 「哪些案子有測試過 PCIe CV5？」
- 「有做過 USB4 CV 測試的專案有哪些？」
- 「找出所有測試過 NVMe 的專案」

作者：AI Platform Team
創建日期：2025-12-09
版本：1.0 (Phase 1)
"""

import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class TestCategorySearchHandler(BaseHandler):
    """
    跨專案測試類別搜尋處理器
    
    搜尋所有包含特定測試類別的專案，並返回測試結果摘要。
    
    支援的意圖：
    - query_projects_by_test_category: 搜尋哪些專案有執行過特定測試類別
    """
    
    handler_name = "test_category_search_handler"
    supported_intent = "query_projects_by_test_category"
    
    # 測試類別名稱對應表（標準化）
    CATEGORY_ALIASES = {
        # PCIe 相關
        'pcie': 'PCIe',
        'pcie cv': 'PCIe',
        'pcie cv5': 'PCIe',
        'pcie_cv': 'PCIe',
        'pci express': 'PCIe',
        
        # NVMe 相關
        'nvme': 'NVMe_Validation_Tool',
        'nvme validation': 'NVMe_Validation_Tool',
        'nvme_validation_tool': 'NVMe_Validation_Tool',
        
        # OAKGATE 相關
        'oakgate': 'OAKGATE',
        'oak gate': 'OAKGATE',
        
        # Performance 相關
        'performance': 'Performance',
        'perf': 'Performance',
        '效能': 'Performance',
        '效能測試': 'Performance',
        
        # Compatibility 相關
        'compatibility': 'Compatibility',
        'compat': 'Compatibility',
        '相容性': 'Compatibility',
        '相容測試': 'Compatibility',
        
        # Functionality 相關
        'functionality': 'Functionality',
        'func': 'Functionality',
        '功能': 'Functionality',
        '功能測試': 'Functionality',
        
        # MANDi 相關
        'mandi': 'MANDi',
        
        # USB4 相關
        'usb4': 'USB4',
        'usb4 cv': 'USB4',
        'usb 4': 'USB4',
        
        # SATA 相關
        'sata': 'SATA',
        'sata cv': 'SATA',
        
        # CrystalDiskMark 相關
        'crystaldiskmark': 'CrystalDiskMark',
        'crystal disk mark': 'CrystalDiskMark',
        'cdm': 'CrystalDiskMark',
    }
    
    # 最大並行查詢數
    MAX_WORKERS = 10
    
    # 最大搜尋專案數（避免過長的等待時間）
    MAX_PROJECTS_TO_SEARCH = 100

    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行跨專案測試類別搜尋
        
        Args:
            parameters: {
                "test_category": "PCIe CV5" / "NVMe" / "Performance" 等,
                "status_filter": "pass" / "fail" / "all" (可選，預設 "all"),
                "customer": "WD" (可選，限定特定客戶)
            }
            
        Returns:
            QueryResult: 包含符合條件的專案列表和測試結果
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['test_category'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        test_category = parameters.get('test_category')
        status_filter = parameters.get('status_filter', 'all').lower()
        customer_filter = parameters.get('customer')
        
        # 標準化測試類別名稱
        normalized_category = self._normalize_category(test_category)
        
        if not normalized_category:
            return QueryResult.error(
                f"無法識別測試類別 '{test_category}'。請使用標準名稱如 NVMe、Performance、PCIe 等。",
                self.handler_name,
                parameters
            )
        
        try:
            # Step 1: 獲取專案列表
            logger.info(f"開始搜尋包含 '{normalized_category}' 測試的專案...")
            
            all_projects = self.api_client.get_all_projects()
            
            if not all_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message="無法獲取專案列表"
                )
            
            # 如果有客戶篩選，先過濾
            if customer_filter:
                all_projects = [
                    p for p in all_projects 
                    if customer_filter.lower() in p.get('customer', '').lower()
                ]
                logger.info(f"客戶篩選後剩餘 {len(all_projects)} 個專案")
            
            # 限制搜尋數量
            projects_to_search = all_projects[:self.MAX_PROJECTS_TO_SEARCH]
            
            # Step 2: 並行查詢每個專案的測試摘要
            matching_projects = []
            
            with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
                future_to_project = {
                    executor.submit(
                        self._check_project_category,
                        project,
                        normalized_category,
                        status_filter
                    ): project
                    for project in projects_to_search
                }
                
                for future in as_completed(future_to_project):
                    result = future.result()
                    if result:
                        matching_projects.append(result)
            
            # Step 3: 根據狀態篩選排序（Pass 多的排前面）
            matching_projects.sort(
                key=lambda x: (
                    -x.get('test_results', {}).get('pass', 0),
                    x.get('project_name', '')
                )
            )
            
            # Step 4: 格式化結果
            if not matching_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"在前 {len(projects_to_search)} 個專案中，沒有找到包含 '{normalized_category}' 測試的專案"
                )
            
            formatted_data = self._format_results(
                matching_projects, 
                normalized_category,
                status_filter
            )
            
            result = QueryResult.success(
                data=formatted_data,
                count=len(matching_projects),
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找到 {len(matching_projects)} 個專案包含 '{normalized_category}' 測試",
                metadata={
                    'search_category': normalized_category,
                    'original_query': test_category,
                    'status_filter': status_filter,
                    'total_projects_searched': len(projects_to_search)
                }
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            logger.error(f"測試類別搜尋錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _normalize_category(self, category: str) -> Optional[str]:
        """
        標準化測試類別名稱
        
        Args:
            category: 用戶輸入的類別名稱
            
        Returns:
            標準化的類別名稱，如果無法識別則返回 None
        """
        if not category:
            return None
        
        # 轉小寫並移除多餘空白
        normalized = category.lower().strip()
        
        # 檢查別名對應表
        if normalized in self.CATEGORY_ALIASES:
            return self.CATEGORY_ALIASES[normalized]
        
        # 嘗試部分匹配
        for alias, standard in self.CATEGORY_ALIASES.items():
            if alias in normalized or normalized in alias:
                return standard
        
        # 如果沒有找到對應，返回原始值（首字母大寫）
        return category.title()
    
    def _check_project_category(
        self,
        project: Dict[str, Any],
        category: str,
        status_filter: str
    ) -> Optional[Dict[str, Any]]:
        """
        檢查專案是否包含指定的測試類別
        
        Args:
            project: 專案資訊
            category: 測試類別名稱
            status_filter: 狀態篩選 (pass/fail/all)
            
        Returns:
            如果包含則返回專案和測試結果，否則返回 None
        """
        project_uid = project.get('projectUid')
        project_name = project.get('projectName', 'Unknown')
        
        if not project_uid:
            return None
        
        try:
            # 獲取測試摘要
            test_summary = self.api_client.get_project_test_summary(project_uid)
            
            if not test_summary:
                return None
            
            # 搜尋是否包含目標類別
            categories = test_summary.get('categories', [])
            
            for cat in categories:
                cat_name = cat.get('name', '')
                
                # 比對類別名稱（忽略大小寫，支援部分匹配）
                if category.lower() in cat_name.lower() or cat_name.lower() in category.lower():
                    cat_total = cat.get('total', {})
                    pass_count = cat_total.get('pass', 0)
                    fail_count = cat_total.get('fail', 0)
                    ongoing_count = cat_total.get('ongoing', 0)
                    total_count = cat_total.get('total', 0)
                    
                    # 根據狀態篩選
                    if status_filter == 'pass' and pass_count == 0:
                        return None
                    if status_filter == 'fail' and fail_count == 0:
                        return None
                    
                    return {
                        'project_uid': project_uid,
                        'project_name': project_name,
                        'customer': project.get('customer', ''),
                        'controller': project.get('controller', ''),
                        'category_name': cat_name,
                        'test_results': {
                            'pass': pass_count,
                            'fail': fail_count,
                            'ongoing': ongoing_count,
                            'total': total_count,
                            'pass_rate': cat_total.get('pass_rate', 0)
                        },
                        'capacities': test_summary.get('capacities', [])
                    }
            
            return None
            
        except Exception as e:
            logger.debug(f"檢查專案 {project_name} 失敗: {str(e)}")
            return None
    
    def _format_results(
        self,
        projects: List[Dict[str, Any]],
        category: str,
        status_filter: str
    ) -> Dict[str, Any]:
        """
        格式化搜尋結果
        
        Args:
            projects: 符合條件的專案列表
            category: 搜尋的類別
            status_filter: 狀態篩選
            
        Returns:
            格式化的結果資料
        """
        # 統計總計
        total_pass = sum(p.get('test_results', {}).get('pass', 0) for p in projects)
        total_fail = sum(p.get('test_results', {}).get('fail', 0) for p in projects)
        total_ongoing = sum(p.get('test_results', {}).get('ongoing', 0) for p in projects)
        
        # 依客戶分組統計
        by_customer = {}
        for p in projects:
            customer = p.get('customer', 'Unknown')
            if customer not in by_customer:
                by_customer[customer] = []
            by_customer[customer].append(p)
        
        return {
            'search_category': category,
            'status_filter': status_filter,
            'total_projects': len(projects),
            'summary': {
                'total_pass': total_pass,
                'total_fail': total_fail,
                'total_ongoing': total_ongoing
            },
            'by_customer': {
                customer: len(prjs) for customer, prjs in by_customer.items()
            },
            'projects': [
                {
                    'project_name': p.get('project_name'),
                    'project_uid': p.get('project_uid'),
                    'customer': p.get('customer'),
                    'controller': p.get('controller'),
                    'category': p.get('category_name'),
                    'pass': p.get('test_results', {}).get('pass', 0),
                    'fail': p.get('test_results', {}).get('fail', 0),
                    'ongoing': p.get('test_results', {}).get('ongoing', 0),
                    'total': p.get('test_results', {}).get('total', 0),
                    'pass_rate': p.get('test_results', {}).get('pass_rate', 0),
                    'capacities': p.get('capacities', [])
                }
                for p in projects
            ]
        }
    
    def _log_query(self, parameters: Dict[str, Any]):
        """記錄查詢參數"""
        logger.info(f"[{self.handler_name}] 查詢參數: {parameters}")
    
    def _log_result(self, result: QueryResult):
        """記錄查詢結果"""
        logger.info(
            f"[{self.handler_name}] 查詢結果: status={result.status.value}, "
            f"count={result.count}, message={result.message}"
        )
    
    def _handle_api_error(self, error: Exception, parameters: Dict[str, Any]) -> QueryResult:
        """處理 API 錯誤"""
        error_msg = f"API 錯誤: {str(error)}"
        logger.error(f"[{self.handler_name}] {error_msg}")
        return QueryResult.error(error_msg, self.handler_name, parameters)
