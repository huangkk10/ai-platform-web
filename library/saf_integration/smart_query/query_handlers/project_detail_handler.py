"""
ProjectDetailHandler - 查詢專案詳細資訊
=======================================

處理 query_project_detail 意圖。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class ProjectDetailHandler(BaseHandler):
    """
    專案詳情查詢處理器
    
    處理查詢單一專案詳細資訊的請求。
    """
    
    handler_name = "project_detail_handler"
    supported_intent = "query_project_detail"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行專案詳情查詢
        
        Args:
            parameters: {"project_name": "DEMETER"}
            
        Returns:
            QueryResult: 包含專案的詳細資訊
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['project_name'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        
        try:
            # 從專案列表中查找
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案資訊",
                    self.handler_name,
                    parameters
                )
            
            # 查找匹配的專案（不區分大小寫）
            project_name_lower = project_name.lower()
            matched_project = None
            
            for project in projects_list:
                if project.get('projectName', '').lower() == project_name_lower:
                    matched_project = project
                    break
            
            if not matched_project:
                # 嘗試部分匹配
                for project in projects_list:
                    if project_name_lower in project.get('projectName', '').lower():
                        matched_project = project
                        break
            
            if not matched_project:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 '{project_name}'"
                )
            
            # 格式化專案詳情
            formatted_detail = self._format_project_detail(matched_project)
            
            result = QueryResult.success(
                data=formatted_detail,
                count=1,
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 '{matched_project.get('projectName')}' 的詳細資訊"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _format_project_detail(self, project: Dict) -> Dict[str, Any]:
        """
        格式化專案詳細資訊
        
        Args:
            project: 原始專案資料
            
        Returns:
            Dict: 格式化後的詳細資訊
        """
        return {
            'projectName': project.get('projectName', ''),
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'nand': project.get('nand', ''),
            'pl': project.get('pl', ''),
            'status': project.get('status', 'Active'),
            'createDate': project.get('createDate', ''),
            'updateDate': project.get('updateDate', ''),
            'description': project.get('description', ''),
            'testCount': project.get('testCount', 0),
            'passRate': project.get('passRate', ''),
        }
