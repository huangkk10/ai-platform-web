"""
TestSummaryHandler - 查詢專案測試結果統計
=========================================

處理 Phase 3 測試摘要相關意圖：
- query_project_test_summary: 查詢專案測試結果統計（按類別和容量）
- query_project_test_by_category: 按類別查詢測試結果
- query_project_test_by_capacity: 按容量查詢測試結果

API 端點：GET /api/v1/projects/{project_uid}/test-summary

作者：AI Platform Team
創建日期：2025-12-24
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class TestSummaryHandler(BaseHandler):
    """
    專案測試結果統計處理器
    
    處理查詢專案測試結果統計的請求，支援按類別和容量過濾。
    
    支援的意圖：
    - query_project_test_summary: 完整測試統計
    - query_project_test_by_category: 按類別過濾
    - query_project_test_by_capacity: 按容量過濾
    """
    
    handler_name = "test_summary_handler"
    supported_intent = "query_project_test_summary"
    
    # 支援的測試類別
    VALID_CATEGORIES = [
        'Compliance', 'Functionality', 'Performance', 
        'Interoperability', 'Stress', 'Compatibility'
    ]
    
    # 支援的容量規格
    VALID_CAPACITIES = ['256GB', '512GB', '1TB', '2TB', '4TB', '8TB']
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行測試結果統計查詢
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "category": "Compliance" (可選),
                "capacity": "1TB" (可選)
            }
            
        Returns:
            QueryResult: 包含測試結果統計
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['project_name'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        category = parameters.get('category')
        capacity = parameters.get('capacity')
        
        try:
            # Step 1: 獲取 project_uid（帶快取）
            project_uid = self.api_client.get_project_uid_by_name(project_name)
            
            if not project_uid:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 '{project_name}'"
                )
            
            # Step 2: 調用 Test Summary API
            test_summary = self.api_client.get_project_test_summary(project_uid)
            
            if not test_summary:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' 的測試摘要"
                )
            
            # Step 3: 根據過濾條件處理結果
            if category:
                return self._handle_category_query(
                    test_summary, project_name, category, capacity
                )
            elif capacity:
                return self._handle_capacity_query(
                    test_summary, project_name, capacity
                )
            else:
                return self._handle_full_summary(
                    test_summary, project_name, parameters
                )
            
        except Exception as e:
            logger.error(f"測試摘要查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _handle_full_summary(
        self, 
        test_summary: Dict[str, Any], 
        project_name: str,
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        處理完整測試摘要查詢
        
        Args:
            test_summary: API 返回的測試摘要
            project_name: 專案名稱
            parameters: 原始查詢參數
            
        Returns:
            QueryResult: 格式化的完整摘要
        """
        formatted_data = self._format_full_summary(test_summary, project_name)
        
        total_pass = sum(cat.get('pass', 0) for cat in test_summary.get('categories', []))
        total_fail = sum(cat.get('fail', 0) for cat in test_summary.get('categories', []))
        
        result = QueryResult.success(
            data=formatted_data,
            count=1,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"專案 '{project_name}' 測試結果：{total_pass} Pass, {total_fail} Fail",
            metadata={
                'total_pass': total_pass,
                'total_fail': total_fail,
                'categories_count': len(test_summary.get('categories', [])),
                'capacities_count': len(test_summary.get('capacities', []))
            }
        )
        
        self._log_result(result)
        return result
    
    def _handle_category_query(
        self, 
        test_summary: Dict[str, Any], 
        project_name: str,
        category: str,
        capacity: Optional[str] = None
    ) -> QueryResult:
        """
        處理按類別查詢
        
        Args:
            test_summary: API 返回的測試摘要
            project_name: 專案名稱
            category: 測試類別
            capacity: 可選的容量過濾
            
        Returns:
            QueryResult: 特定類別的測試結果
        """
        # 標準化類別名稱
        normalized_category = self._normalize_category(category)
        
        if not normalized_category:
            return QueryResult.error(
                f"無效的測試類別 '{category}'。有效類別：{', '.join(self.VALID_CATEGORIES)}",
                self.handler_name,
                {'project_name': project_name, 'category': category}
            )
        
        # 查找類別資料
        categories = test_summary.get('categories', [])
        category_data = None
        
        for cat in categories:
            if cat.get('name', '').lower() == normalized_category.lower():
                category_data = cat
                break
        
        if not category_data:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters={'project_name': project_name, 'category': category},
                message=f"專案 '{project_name}' 沒有 '{normalized_category}' 類別的測試資料"
            )
        
        # 如果有容量過濾，進一步過濾
        if capacity:
            capacity_filtered = self._filter_by_capacity(category_data, capacity)
            if capacity_filtered:
                category_data = capacity_filtered
        
        formatted_data = {
            'projectName': project_name,
            'category': normalized_category,
            'pass': category_data.get('pass', 0),
            'fail': category_data.get('fail', 0),
            'total': category_data.get('pass', 0) + category_data.get('fail', 0),
            'passRate': self._calculate_pass_rate(
                category_data.get('pass', 0),
                category_data.get('fail', 0)
            ),
            'capacity_filter': capacity
        }
        
        result = QueryResult.success(
            data=formatted_data,
            count=1,
            query_type="query_project_test_by_category",
            parameters={'project_name': project_name, 'category': category},
            message=f"'{project_name}' 的 {normalized_category} 測試：{formatted_data['pass']} Pass, {formatted_data['fail']} Fail"
        )
        
        self._log_result(result)
        return result
    
    def _handle_capacity_query(
        self, 
        test_summary: Dict[str, Any], 
        project_name: str,
        capacity: str
    ) -> QueryResult:
        """
        處理按容量查詢
        
        Args:
            test_summary: API 返回的測試摘要
            project_name: 專案名稱
            capacity: 容量規格
            
        Returns:
            QueryResult: 特定容量的測試結果
        """
        # 標準化容量
        normalized_capacity = self._normalize_capacity(capacity)
        
        if not normalized_capacity:
            return QueryResult.error(
                f"無效的容量規格 '{capacity}'。有效規格：{', '.join(self.VALID_CAPACITIES)}",
                self.handler_name,
                {'project_name': project_name, 'capacity': capacity}
            )
        
        # 查找容量資料
        capacities = test_summary.get('capacities', [])
        capacity_data = None
        
        for cap in capacities:
            cap_name = cap.get('name', '').upper()
            if cap_name == normalized_capacity.upper():
                capacity_data = cap
                break
        
        if not capacity_data:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters={'project_name': project_name, 'capacity': capacity},
                message=f"專案 '{project_name}' 沒有 '{normalized_capacity}' 容量的測試資料"
            )
        
        formatted_data = {
            'projectName': project_name,
            'capacity': normalized_capacity,
            'pass': capacity_data.get('pass', 0),
            'fail': capacity_data.get('fail', 0),
            'total': capacity_data.get('pass', 0) + capacity_data.get('fail', 0),
            'passRate': self._calculate_pass_rate(
                capacity_data.get('pass', 0),
                capacity_data.get('fail', 0)
            )
        }
        
        result = QueryResult.success(
            data=formatted_data,
            count=1,
            query_type="query_project_test_by_capacity",
            parameters={'project_name': project_name, 'capacity': capacity},
            message=f"'{project_name}' 的 {normalized_capacity} 測試：{formatted_data['pass']} Pass, {formatted_data['fail']} Fail"
        )
        
        self._log_result(result)
        return result
    
    def _format_full_summary(
        self, 
        test_summary: Dict[str, Any], 
        project_name: str
    ) -> Dict[str, Any]:
        """
        格式化完整測試摘要
        
        Args:
            test_summary: API 返回的原始資料
            project_name: 專案名稱
            
        Returns:
            Dict: 格式化後的摘要
        """
        categories = test_summary.get('categories', [])
        capacities = test_summary.get('capacities', [])
        
        # 計算總計
        total_pass = sum(cat.get('pass', 0) for cat in categories)
        total_fail = sum(cat.get('fail', 0) for cat in categories)
        
        # 格式化類別資料
        formatted_categories = []
        for cat in categories:
            cat_pass = cat.get('pass', 0)
            cat_fail = cat.get('fail', 0)
            formatted_categories.append({
                'name': cat.get('name', ''),
                'pass': cat_pass,
                'fail': cat_fail,
                'total': cat_pass + cat_fail,
                'passRate': self._calculate_pass_rate(cat_pass, cat_fail)
            })
        
        # 格式化容量資料
        formatted_capacities = []
        for cap in capacities:
            cap_pass = cap.get('pass', 0)
            cap_fail = cap.get('fail', 0)
            formatted_capacities.append({
                'name': cap.get('name', ''),
                'pass': cap_pass,
                'fail': cap_fail,
                'total': cap_pass + cap_fail,
                'passRate': self._calculate_pass_rate(cap_pass, cap_fail)
            })
        
        return {
            'projectName': project_name,
            'summary': {
                'totalPass': total_pass,
                'totalFail': total_fail,
                'total': total_pass + total_fail,
                'overallPassRate': self._calculate_pass_rate(total_pass, total_fail)
            },
            'byCategory': formatted_categories,
            'byCapacity': formatted_capacities
        }
    
    def _normalize_category(self, category: str) -> Optional[str]:
        """
        標準化類別名稱
        
        Args:
            category: 輸入的類別名稱
            
        Returns:
            Optional[str]: 標準化的類別名稱，無效則返回 None
        """
        category_mapping = {
            'compliance': 'Compliance',
            'comp': 'Compliance',
            '合規': 'Compliance',
            'functionality': 'Functionality',
            'func': 'Functionality',
            '功能': 'Functionality',
            'performance': 'Performance',
            'perf': 'Performance',
            '效能': 'Performance',
            'interoperability': 'Interoperability',
            'inter': 'Interoperability',
            '互通': 'Interoperability',
            'stress': 'Stress',
            '壓力': 'Stress',
            'compatibility': 'Compatibility',
            'compat': 'Compatibility',
            '相容': 'Compatibility',
        }
        
        return category_mapping.get(category.lower(), None)
    
    def _normalize_capacity(self, capacity: str) -> Optional[str]:
        """
        標準化容量名稱
        
        Args:
            capacity: 輸入的容量
            
        Returns:
            Optional[str]: 標準化的容量，無效則返回 None
        """
        capacity_mapping = {
            '256gb': '256GB',
            '256g': '256GB',
            '512gb': '512GB',
            '512g': '512GB',
            '1tb': '1TB',
            '1t': '1TB',
            '2tb': '2TB',
            '2t': '2TB',
            '4tb': '4TB',
            '4t': '4TB',
            '8tb': '8TB',
            '8t': '8TB',
        }
        
        return capacity_mapping.get(capacity.lower(), None)
    
    def _calculate_pass_rate(self, passed: int, failed: int) -> str:
        """
        計算通過率
        
        Args:
            passed: 通過數量
            failed: 失敗數量
            
        Returns:
            str: 通過率百分比（如 "85.5%"）
        """
        total = passed + failed
        if total == 0:
            return "N/A"
        
        rate = (passed / total) * 100
        return f"{rate:.1f}%"
    
    def _filter_by_capacity(
        self, 
        category_data: Dict[str, Any], 
        capacity: str
    ) -> Optional[Dict[str, Any]]:
        """
        按容量過濾類別資料
        
        注意：這需要 API 支援更細粒度的資料。
        如果 API 不支援，返回 None 表示無法過濾。
        
        Args:
            category_data: 類別資料
            capacity: 容量過濾條件
            
        Returns:
            Optional[Dict]: 過濾後的資料，或 None
        """
        # 當前 API 可能不支援細粒度過濾
        # 如果有 breakdown 資料，使用它
        breakdown = category_data.get('capacityBreakdown', {})
        
        if capacity in breakdown:
            return breakdown[capacity]
        
        # API 不支援細粒度，返回原始資料
        return None
