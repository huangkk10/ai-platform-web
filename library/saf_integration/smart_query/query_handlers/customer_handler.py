"""
CustomerHandler - 按客戶查詢專案
================================

處理 query_projects_by_customer 意圖。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class CustomerHandler(BaseHandler):
    """
    客戶查詢處理器
    
    處理按客戶名稱查詢專案的請求。
    """
    
    handler_name = "customer_handler"
    supported_intent = "query_projects_by_customer"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按客戶查詢專案
        
        Args:
            parameters: {"customer": "WD"}
            
        Returns:
            QueryResult: 包含該客戶的所有專案
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['customer'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        customer = parameters.get('customer')
        
        try:
            # 使用正確的 API 方法獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # 過濾指定客戶的專案
            filtered_projects = self._filter_projects(
                projects_list, 
                'customer', 
                customer
            )
            
            if not filtered_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到客戶 '{customer}' 的專案"
                )
            
            # 去重：根據 projectName 去除重複的專案
            # SAF API 可能返回多個子專案（同一個專案名稱多個記錄）
            unique_projects = self._deduplicate_projects_by_name(filtered_projects)
            
            # 格式化結果
            formatted_projects = [
                self._format_project_data(p) for p in unique_projects
            ]
            
            # 構建訊息（顯示去重前後的數量差異）
            original_count = len(filtered_projects)
            unique_count = len(formatted_projects)
            
            if original_count != unique_count:
                message = f"找到 {unique_count} 個 {customer} 的不同專案（原始 {original_count} 筆記錄）"
            else:
                message = f"找到 {unique_count} 個 {customer} 的專案"
            
            result = QueryResult.success(
                data=formatted_projects,
                query_type=self.handler_name,
                parameters=parameters,
                message=message
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
