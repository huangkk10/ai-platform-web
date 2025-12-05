"""
ProjectSummaryHandler - 查詢專案測試摘要
========================================

處理 query_project_summary 意圖。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class ProjectSummaryHandler(BaseHandler):
    """
    專案測試摘要查詢處理器
    
    處理查詢專案測試結果摘要的請求。
    """
    
    handler_name = "project_summary_handler"
    supported_intent = "query_project_summary"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行專案測試摘要查詢
        
        Args:
            parameters: {"project_name": "DEMETER"}
            
        Returns:
            QueryResult: 包含專案的測試結果摘要
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
            
            # 查找匹配的專案
            project_name_lower = project_name.lower()
            matched_project = None
            
            for project in projects_list:
                if project.get('projectName', '').lower() == project_name_lower:
                    matched_project = project
                    break
                elif project_name_lower in project.get('projectName', '').lower():
                    matched_project = project
                    break
            
            if not matched_project:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 '{project_name}'"
                )
            
            # 從專案資料中提取摘要
            formatted_summary = self._extract_summary_from_project(matched_project)
            
            result = QueryResult.success(
                data=formatted_summary,
                count=1,
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 '{matched_project.get('projectName')}' 的測試摘要"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _format_summary(self, summary: Dict, project_name: str) -> Dict[str, Any]:
        """
        格式化測試摘要
        
        Args:
            summary: 原始摘要資料
            project_name: 專案名稱
            
        Returns:
            Dict: 格式化後的摘要
        """
        return {
            'projectName': project_name,
            'totalTests': summary.get('totalTests', 0),
            'passedTests': summary.get('passedTests', 0),
            'failedTests': summary.get('failedTests', 0),
            'passRate': summary.get('passRate', '0%'),
            'lastTestDate': summary.get('lastTestDate', ''),
            'status': summary.get('status', 'Unknown'),
            'testCategories': summary.get('testCategories', []),
        }
    
    def _extract_summary_from_project(self, project: Dict) -> Dict[str, Any]:
        """
        從專案資料中提取測試摘要
        
        Args:
            project: 專案資料
            
        Returns:
            Dict: 提取的摘要
        """
        return {
            'projectName': project.get('projectName', ''),
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'totalTests': project.get('testCount', 0),
            'passRate': project.get('passRate', 'N/A'),
            'status': project.get('status', 'Active'),
            'lastUpdate': project.get('updateDate', ''),
            'note': '此為專案基本資訊，詳細測試結果請查詢測試報告'
        }
