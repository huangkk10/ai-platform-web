"""
PLHandler - 按專案負責人查詢專案
================================

處理 query_projects_by_pl 意圖。

作者：AI Platform Team
創建日期：2025-12-08
Phase：7

更新記錄：
- 2025-12-08: 添加按 PL 名稱分組功能，改善結果呈現
"""

import logging
from typing import Dict, Any, List
from collections import defaultdict

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
            QueryResult: 包含該 PL 負責的所有專案，按實際 PL 名稱分組
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
            
            # 去重：根據 projectName 去除重複的專案
            # SAF API 可能返回多個子專案（同一個專案名稱多個記錄）
            unique_projects = self._deduplicate_projects_by_name(filtered_projects)
            
            # 格式化所有專案
            formatted_projects = [
                self._format_project_data(p) for p in unique_projects
            ]
            
            # 按實際 PL 名稱分組
            groups = self._group_projects_by_pl(formatted_projects)
            
            # 構建結果訊息（顯示去重前後的數量差異）
            group_count = len(groups)
            original_count = len(filtered_projects)
            unique_count = len(formatted_projects)
            
            if group_count == 1:
                if original_count != unique_count:
                    message = f"找到 {unique_count} 個 {pl} 負責的不同專案（原始 {original_count} 筆記錄）"
                else:
                    message = f"找到 {unique_count} 個 {pl} 負責的專案"
            else:
                if original_count != unique_count:
                    message = f"找到 {unique_count} 個與 '{pl}' 相關的不同專案（原始 {original_count} 筆，{group_count} 種 PL 格式）"
                else:
                    message = f"找到 {unique_count} 個與 '{pl}' 相關的專案（{group_count} 種 PL 格式）"
            
            # 構建結果資料（包含分組資訊）
            result_data = {
                'query_pl': pl,
                'total_count': len(formatted_projects),
                'groups': groups,
                'projects': formatted_projects  # 保留扁平列表以向後相容
            }
            
            result = QueryResult.success(
                data=result_data,
                query_type=self.handler_name,
                parameters=parameters,
                message=message
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
        按 PL 過濾專案（智能匹配）
        
        匹配規則（大小寫不敏感）：
        
        1. 如果用戶輸入的是完整 ID 格式（包含 "."，如 ryder.lin）：
           - 精確匹配：project.pl == pl
           - 前向包含：pl 在 project.pl 中（處理多人 PL，如 "ryder.lin, bruce.zhang"）
           - 不做反向匹配（避免 ryder.lin 匹配到 Ryder）
           
        2. 如果用戶輸入的是簡短名字（如 Ryder）：
           - 精確匹配：project.pl == pl
           - 雙向包含：允許 Ryder 匹配到 ryder.lin
        
        Args:
            projects: 專案列表
            pl: PL 名稱（如 Ryder, ryder.lin）
            
        Returns:
            過濾後的專案列表
        """
        pl_lower = pl.lower()
        filtered = []
        
        # 判斷是否為完整 ID 格式（包含 "."）
        is_full_id = '.' in pl
        
        for project in projects:
            project_pl = project.get('pl', '')
            if not project_pl:
                continue
                
            project_pl_lower = project_pl.lower()
            
            # 精確匹配（總是允許）
            if project_pl_lower == pl_lower:
                filtered.append(project)
                continue
            
            # 前向包含：查詢的 PL 在專案的 PL 中（處理多人 PL）
            # 例：ryder.lin 查詢 → 匹配 "ryder.lin, bruce.zhang"
            if pl_lower in project_pl_lower:
                filtered.append(project)
                continue
            
            # 反向包含：只在簡短名字時允許
            # 例：Ryder 查詢 → 匹配 "ryder.lin"
            if not is_full_id and project_pl_lower in pl_lower:
                filtered.append(project)
                continue
        
        # 按專案名稱排序
        filtered.sort(key=lambda x: x.get('projectName', ''))
        
        return filtered
    
    def _group_projects_by_pl(
        self,
        projects: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        按實際 PL 名稱分組專案
        
        將專案按其原始 pl 欄位值進行分組，這樣可以清楚區分
        不同格式的 PL 名稱（如 "Ryder" vs "ryder.lin, bruce.zhang"）。
        
        Args:
            projects: 格式化後的專案列表
            
        Returns:
            分組結果列表，每個分組包含：
            - pl_name: 實際 PL 名稱
            - count: 專案數量
            - projects: 該 PL 的專案列表
        """
        # 使用 defaultdict 進行分組
        groups = defaultdict(list)
        
        for project in projects:
            # 直接從專案資料中取得 pl 值
            pl_name = project.get('pl', '未知')
            groups[pl_name].append(project)
        
        # 轉換為列表格式，並按 PL 名稱排序
        result = []
        for pl_name in sorted(groups.keys()):
            result.append({
                'pl_name': pl_name,
                'count': len(groups[pl_name]),
                'projects': groups[pl_name]
            })
        
        return result
