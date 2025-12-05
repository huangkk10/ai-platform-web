"""
ControllerHandler - 按控制器查詢專案
====================================

處理 query_projects_by_controller 意圖。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class ControllerHandler(BaseHandler):
    """
    控制器查詢處理器
    
    處理按控制器型號查詢專案的請求。
    """
    
    handler_name = "controller_handler"
    supported_intent = "query_projects_by_controller"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按控制器查詢專案
        
        Args:
            parameters: {"controller": "SM2264"}
            
        Returns:
            QueryResult: 包含使用該控制器的所有專案
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['controller'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        controller = parameters.get('controller')
        
        try:
            # 使用正確的 API 方法獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # 過濾指定控制器的專案
            filtered_projects = self._filter_projects(
                projects_list, 
                'controller', 
                controller
            )
            
            if not filtered_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到使用控制器 '{controller}' 的專案"
                )
            
            # 格式化結果
            formatted_projects = [
                self._format_project_data(p) for p in filtered_projects
            ]
            
            result = QueryResult.success(
                data=formatted_projects,
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找到 {len(formatted_projects)} 個使用 {controller} 控制器的專案"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
