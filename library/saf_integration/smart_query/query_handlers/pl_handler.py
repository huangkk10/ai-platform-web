"""
PLHandler - 按專案負責人查詢專案
================================

處理 query_projects_by_pl 意圖。

作者：AI Platform Team
創建日期：2025-12-08
Phase：7
"""

import logging
from typing import Dict, Any, List

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class PLHandler(BaseHandler):
    """
    專案負責人查詢處理器
    
    處理按 PL（Project Leader）名稱查詢專案的請求。
    支援模糊匹配，例如：
    - "Ryder" 可以匹配 "ryder.lin"
    - "ryder.lin" 可以匹配 "Ryder"
    """
    
    handler_name = "pl_handler"
    supported_intent = "query_projects_by_pl"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按 PL 查詢專案
        
        Args:
            parameters: {"pl": "Ryder"}
            
        Returns:
            QueryResult: 包含該 PL 負責的所有專案
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['pl'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        pl = parameters.get('pl')
        
        try:
            # 獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # 過濾指定 PL 的專案（使用模糊匹配）
            filtered_projects = self._filter_projects_by_pl(
                projects_list, 
                pl
            )
            
            if not filtered_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案負責人 '{pl}' 的專案"
                )
            
            # 格式化結果
            formatted_projects = [
                self._format_project_data(p) for p in filtered_projects
            ]
            
            result = QueryResult.success(
                data=formatted_projects,
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找到 {len(formatted_projects)} 個 {pl} 負責的專案"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _filter_projects_by_pl(
        self, 
        projects: List[Dict[str, Any]], 
        pl: str
    ) -> List[Dict[str, Any]]:
        """
        按 PL 過濾專案（支援模糊匹配）
        
        匹配規則（大小寫不敏感）：
        1. 精確匹配：project.pl == pl
        2. 包含匹配：pl 在 project.pl 中（用於 ryder.lin 匹配 Ryder）
        3. 反向包含：project.pl 在 pl 中（用於 Ryder 匹配 ryder.lin）
        
        Args:
            projects: 專案列表
            pl: PL 名稱（如 Ryder, ryder.lin）
            
        Returns:
            過濾後的專案列表
        """
        pl_lower = pl.lower()
        filtered = []
        
        for project in projects:
            project_pl = project.get('pl', '')
            if not project_pl:
                continue
                
            project_pl_lower = project_pl.lower()
            
            # 精確匹配或包含匹配（雙向）
            if (project_pl_lower == pl_lower or 
                pl_lower in project_pl_lower or
                project_pl_lower in pl_lower):
                filtered.append(project)
        
        # 按專案名稱排序
        filtered.sort(key=lambda x: x.get('projectName', ''))
        
        return filtered
