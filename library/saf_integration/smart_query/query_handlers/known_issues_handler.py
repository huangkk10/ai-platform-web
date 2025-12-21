"""
KnownIssuesHandler - Known Issues 查詢處理器
============================================

處理所有與 Known Issues 相關的意圖查詢，包括：
- 專案 Known Issues 查詢
- 按 Test Item 查詢
- 統計與排名
- 建立者查詢
- JIRA 狀態查詢
- 時間範圍查詢
- 關鍵字搜尋
- 跨專案搜尋

作者：AI Platform Team
創建日期：2025-01-20
Phase: 15 - Known Issues Integration
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class KnownIssuesHandler(BaseHandler):
    """
    Known Issues 查詢處理器
    
    處理所有 Known Issues 相關的查詢意圖。
    支援 12 種不同的查詢類型。
    """
    
    handler_name = "known_issues_handler"
    
    # 支援的所有意圖類型
    SUPPORTED_INTENTS = [
        "query_project_known_issues",
        "query_project_test_item_known_issues",
        "count_project_known_issues",
        "rank_projects_by_known_issues",
        "query_known_issues_by_creator",
        "list_known_issues_creators",
        "query_known_issues_with_jira",
        "query_known_issues_without_jira",
        "query_recent_known_issues",
        "query_known_issues_by_date_range",
        "search_known_issues_by_keyword",
        "query_all_known_issues_by_test_item"
    ]
    
    def execute(self, parameters: Dict[str, Any], intent: str = None) -> QueryResult:
        """
        執行 Known Issues 查詢
        
        Args:
            parameters: 查詢參數
            intent: 意圖類型（用於區分不同的查詢模式）
            
        Returns:
            QueryResult: 查詢結果
        """
        self._log_query(parameters)
        
        # 根據 intent 調用對應的處理方法
        intent_handlers = {
            "query_project_known_issues": self._handle_project_known_issues,
            "query_project_test_item_known_issues": self._handle_project_test_item_known_issues,
            "count_project_known_issues": self._handle_count_project_known_issues,
            "rank_projects_by_known_issues": self._handle_rank_projects,
            "query_known_issues_by_creator": self._handle_query_by_creator,
            "list_known_issues_creators": self._handle_list_creators,
            "query_known_issues_with_jira": self._handle_with_jira,
            "query_known_issues_without_jira": self._handle_without_jira,
            "query_recent_known_issues": self._handle_recent_issues,
            "query_known_issues_by_date_range": self._handle_by_date_range,
            "search_known_issues_by_keyword": self._handle_keyword_search,
            "query_all_known_issues_by_test_item": self._handle_all_by_test_item
        }
        
        handler = intent_handlers.get(intent)
        if handler:
            try:
                result = handler(parameters)
                self._log_result(result)
                return result
            except Exception as e:
                return self._handle_api_error(e, parameters)
        else:
            return QueryResult.error(
                f"未知的 Known Issues 意圖類型: {intent}",
                self.handler_name,
                parameters
            )
    
    # =========================================================================
    # 主要意圖處理方法
    # =========================================================================
    
    def _handle_project_known_issues(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_project_known_issues - 查詢專案 Known Issues
        
        注意：由於 SAF API 的專案 ID 和 Known Issues 的 project_id 使用不同的 ID 系統，
        所以改用 project_name 模糊匹配過濾 Known Issues。
        
        Args:
            parameters: {"project_name": "DEMETER", "show_disabled": True}
        """
        error = self.validate_parameters(parameters, required=['project_name'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        show_disabled = parameters.get('show_disabled', True)
        
        # 使用 project_name 過濾 Known Issues（不使用 project_id）
        issues = self._fetch_known_issues_by_project_name(
            project_name=project_name,
            show_disabled=show_disabled
        )
        
        if not issues:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 {project_name} 沒有 Known Issues"
            )
        
        # 格式化結果
        formatted_issues = [self._format_issue(issue) for issue in issues]
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"專案 {project_name} 共有 {len(formatted_issues)} 個 Known Issues"
        )
    
    def _handle_project_test_item_known_issues(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_project_test_item_known_issues - 按 Test Item 查詢
        
        Args:
            parameters: {"project_name": "DEMETER", "test_item": "Sequential Read"}
        """
        error = self.validate_parameters(parameters, required=['project_name', 'test_item'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        test_item = parameters.get('test_item')
        show_disabled = parameters.get('show_disabled', True)
        
        # 使用 project_name 過濾 Known Issues（不使用 project_id）
        issues = self._fetch_known_issues_by_project_name(
            project_name=project_name,
            show_disabled=show_disabled
        )
        
        if not issues:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找不到專案 {project_name} 的 Known Issues"
            )
        
        # 過濾特定 Test Item
        filtered_issues = [
            issue for issue in issues
            if test_item.lower() in issue.get('test_item_name', '').lower()
        ]
        
        if not filtered_issues:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 {project_name} 的 {test_item} 測項沒有 Known Issues"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in filtered_issues]
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"專案 {project_name} 的 {test_item} 測項共有 {len(formatted_issues)} 個 Known Issues"
        )
    
    def _handle_count_project_known_issues(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 count_project_known_issues - 統計專案 Known Issues 數量
        
        返回統計資訊和詳細列表，讓前端可以顯示表格
        
        Args:
            parameters: {"project_name": "DEMETER", "show_disabled": True}
        """
        error = self.validate_parameters(parameters, required=['project_name'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        show_disabled = parameters.get('show_disabled', True)
        
        # 使用 project_name 過濾 Known Issues（不使用 project_id）
        issues = self._fetch_known_issues_by_project_name(
            project_name=project_name,
            show_disabled=show_disabled
        )
        
        if not issues:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 {project_name} 沒有 Known Issues"
            )
        
        # 統計資訊
        total_count = len(issues)
        enabled_count = sum(1 for i in issues if i.get('is_enable', True))
        disabled_count = total_count - enabled_count
        with_jira_count = sum(1 for i in issues if i.get('jira_id'))
        
        # 格式化 Issues 列表供前端顯示
        formatted_issues = [self._format_issue(issue) for issue in issues]
        
        return QueryResult.success(
            data=formatted_issues,  # 返回列表讓前端可以顯示表格
            count=total_count,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"專案 {project_name} 共有 {total_count} 個 Known Issues（啟用: {enabled_count}，停用: {disabled_count}）",
            metadata={
                "stats": {
                    "project_name": project_name,
                    "total_count": total_count,
                    "enabled_count": enabled_count,
                    "disabled_count": disabled_count,
                    "with_jira_count": with_jira_count,
                    "without_jira_count": total_count - with_jira_count
                }
            }
        )
    
    def _handle_rank_projects(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 rank_projects_by_known_issues - 排名專案 Known Issues 數量
        
        優化：直接從所有 Known Issues 中統計，避免每個專案單獨 API 調用
        
        Args:
            parameters: {"top_n": 10, "customer": "WD"}
        """
        top_n = parameters.get('top_n', 10)
        customer = parameters.get('customer')
        
        # 獲取所有 Known Issues（一次性）
        all_issues = self._fetch_all_known_issues()
        
        if not all_issues:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message="沒有找到 Known Issues 資料"
            )
        
        # 按 project_name 分組統計
        from collections import defaultdict
        project_stats_dict = defaultdict(lambda: {
            "project_name": None,
            "issue_count": 0,
            "with_jira_count": 0,
            "enabled_count": 0
        })
        
        for issue in all_issues:
            project_name_key = issue.get('project_name', 'Unknown')
            stats = project_stats_dict[project_name_key]
            stats["project_name"] = project_name_key
            stats["issue_count"] += 1
            if issue.get('jira_id'):
                stats["with_jira_count"] += 1
            if issue.get('is_enable', True):
                stats["enabled_count"] += 1
        
        # 轉換為列表
        project_stats = list(project_stats_dict.values())
        
        # 如果指定客戶，過濾（注意：Known Issues 中可能沒有 customer 欄位）
        # 這裡用 project_name 模糊匹配客戶名稱
        if customer:
            customer_lower = customer.lower()
            project_stats = [
                p for p in project_stats
                if customer_lower in (p.get('project_name') or '').lower()
            ]
        
        # 按 issue_count 排序
        project_stats.sort(key=lambda x: x['issue_count'], reverse=True)
        
        # 取前 N 個
        top_projects = project_stats[:top_n]
        
        if not top_projects:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message="沒有找到專案的 Known Issues 資料"
            )
        
        customer_msg = f"（包含 '{customer}' 的專案）" if customer else ""
        
        return QueryResult.success(
            data=top_projects,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"Known Issues 數量前 {len(top_projects)} 的專案{customer_msg}"
        )
    
    def _handle_query_by_creator(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_known_issues_by_creator - 按建立者查詢
        
        Args:
            parameters: {"creator": "Ryder", "project_name": "DEMETER"}
        """
        error = self.validate_parameters(parameters, required=['creator'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        creator = parameters.get('creator')
        project_name = parameters.get('project_name')
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
        else:
            # 獲取所有專案的 Issues
            issues = self._fetch_all_known_issues()
        
        # 過濾建立者
        filtered_issues = [
            issue for issue in issues
            if creator.lower() in issue.get('created_by', '').lower()
        ]
        
        if not filtered_issues:
            scope_msg = f"專案 {project_name} 中" if project_name else ""
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}找不到 {creator} 建立的 Known Issues"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in filtered_issues]
        
        scope_msg = f"在專案 {project_name} 中" if project_name else ""
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{creator} {scope_msg}共建立了 {len(formatted_issues)} 個 Known Issues"
        )
    
    def _handle_list_creators(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 list_known_issues_creators - 列出建立者清單
        
        Args:
            parameters: {"project_name": "DEMETER"}
        """
        project_name = parameters.get('project_name')
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
            if not issues:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 {project_name} 的 Known Issues"
                )
        else:
            issues = self._fetch_all_known_issues()
        
        # 統計每個建立者的數量
        creator_stats = {}
        for issue in issues:
            creator = issue.get('created_by', 'Unknown')
            if creator not in creator_stats:
                creator_stats[creator] = 0
            creator_stats[creator] += 1
        
        # 格式化並排序
        creators = [
            {"creator": creator, "issue_count": count}
            for creator, count in creator_stats.items()
        ]
        creators.sort(key=lambda x: x['issue_count'], reverse=True)
        
        if not creators:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message="沒有找到 Known Issues 建立者資訊"
            )
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        
        return QueryResult.success(
            data=creators,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}共有 {len(creators)} 位建立者"
        )
    
    def _handle_with_jira(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_known_issues_with_jira - 查詢有 JIRA 的 Issues
        
        Args:
            parameters: {"project_name": "DEMETER"}
        """
        project_name = parameters.get('project_name')
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
            if not issues:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 {project_name} 的 Known Issues"
                )
        else:
            issues = self._fetch_all_known_issues()
        
        # 過濾有 JIRA 的
        issues_with_jira = [
            issue for issue in issues
            if issue.get('jira_id')
        ]
        
        if not issues_with_jira:
            scope_msg = f"專案 {project_name}" if project_name else "所有專案"
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}沒有關聯 JIRA 的 Known Issues"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in issues_with_jira]
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}有 {len(formatted_issues)} 個 Known Issues 關聯了 JIRA"
        )
    
    def _handle_without_jira(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_known_issues_without_jira - 查詢沒有 JIRA 的 Issues
        
        Args:
            parameters: {"project_name": "DEMETER"}
        """
        project_name = parameters.get('project_name')
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
            if not issues:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 {project_name} 的 Known Issues"
                )
        else:
            issues = self._fetch_all_known_issues()
        
        # 過濾沒有 JIRA 的
        issues_without_jira = [
            issue for issue in issues
            if not issue.get('jira_id')
        ]
        
        if not issues_without_jira:
            scope_msg = f"專案 {project_name}" if project_name else "所有專案"
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}所有 Known Issues 都已關聯 JIRA"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in issues_without_jira]
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}有 {len(formatted_issues)} 個 Known Issues 尚未關聯 JIRA"
        )
    
    def _handle_recent_issues(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_recent_known_issues - 查詢最近的 Issues
        
        Args:
            parameters: {"project_name": "DEMETER", "days": 7, "date_range": "this_week"}
        """
        project_name = parameters.get('project_name')
        days = parameters.get('days', 7)
        date_range = parameters.get('date_range')
        
        # 計算日期範圍
        now = datetime.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'this_week':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'this_month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = now - timedelta(days=days)
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
            if not issues:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 {project_name} 的 Known Issues"
                )
        else:
            issues = self._fetch_all_known_issues()
        
        # 過濾日期範圍
        recent_issues = []
        for issue in issues:
            created_at = issue.get('created_at')
            if created_at:
                try:
                    issue_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    if issue_date.replace(tzinfo=None) >= start_date:
                        recent_issues.append(issue)
                except Exception:
                    pass
        
        if not recent_issues:
            scope_msg = f"專案 {project_name}" if project_name else "所有專案"
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}最近沒有新的 Known Issues"
            )
        
        # 按建立時間排序（最新的在前）
        recent_issues.sort(
            key=lambda x: x.get('created_at', ''),
            reverse=True
        )
        
        formatted_issues = [self._format_issue(issue) for issue in recent_issues]
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        time_msg = date_range or f"最近 {days} 天"
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}{time_msg}新增了 {len(formatted_issues)} 個 Known Issues"
        )
    
    def _handle_by_date_range(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_known_issues_by_date_range - 按日期範圍查詢
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "start_date": "2025-01-01",
                "end_date": "2025-01-31",
                "year": 2025,
                "month": 1
            }
        """
        project_name = parameters.get('project_name')
        start_date_str = parameters.get('start_date')
        end_date_str = parameters.get('end_date')
        year = parameters.get('year')
        month = parameters.get('month')
        date_range = parameters.get('date_range')
        
        # 計算日期範圍
        now = datetime.now()
        
        if start_date_str and end_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        elif year and month:
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
        elif year:
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
        elif date_range == 'last_month':
            first_day_this_month = now.replace(day=1)
            end_date = first_day_this_month - timedelta(days=1)
            start_date = end_date.replace(day=1)
        else:
            return QueryResult.error(
                "請指定日期範圍（年份、月份或起迄日期）",
                self.handler_name,
                parameters
            )
        
        # 使用 project_name 過濾（如果指定）
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
            if not issues:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 {project_name} 的 Known Issues"
                )
        else:
            issues = self._fetch_all_known_issues()
        
        # 過濾日期範圍
        filtered_issues = []
        for issue in issues:
            created_at = issue.get('created_at')
            if created_at:
                try:
                    issue_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    issue_date = issue_date.replace(tzinfo=None)
                    if start_date <= issue_date <= end_date.replace(hour=23, minute=59, second=59):
                        filtered_issues.append(issue)
                except Exception:
                    pass
        
        if not filtered_issues:
            scope_msg = f"專案 {project_name}" if project_name else "所有專案"
            date_msg = f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}"
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}在 {date_msg} 期間沒有 Known Issues"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in filtered_issues]
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        date_msg = f"{start_date.strftime('%Y-%m-%d')} 到 {end_date.strftime('%Y-%m-%d')}"
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}在 {date_msg} 期間有 {len(formatted_issues)} 個 Known Issues"
        )
    
    def _handle_keyword_search(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 search_known_issues_by_keyword - 關鍵字搜尋
        
        Args:
            parameters: {
                "keyword": "timeout",
                "project_name": "DEMETER",
                "search_fields": ["issue_id", "test_item_name", "case_name", "note"]
            }
        """
        error = self.validate_parameters(parameters, required=['keyword'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        keyword = parameters.get('keyword', '').lower()
        project_name = parameters.get('project_name')
        search_fields = parameters.get('search_fields', [
            'issue_id', 'test_item_name', 'case_name', 'note', 'jira_id'
        ])
        
        # 獲取 Issues - 使用 project_name 過濾
        if project_name:
            issues = self._fetch_known_issues_by_project_name(project_name)
        else:
            issues = self._fetch_all_known_issues()
        
        # 關鍵字搜尋
        matched_issues = []
        for issue in issues:
            for field in search_fields:
                field_value = str(issue.get(field, '')).lower()
                if keyword in field_value:
                    matched_issues.append(issue)
                    break
        
        if not matched_issues:
            scope_msg = f"專案 {project_name}" if project_name else "所有專案"
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{scope_msg}找不到包含 '{keyword}' 的 Known Issues"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in matched_issues]
        
        scope_msg = f"專案 {project_name}" if project_name else "所有專案"
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"{scope_msg}找到 {len(formatted_issues)} 個包含 '{keyword}' 的 Known Issues"
        )
    
    def _handle_all_by_test_item(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 query_all_known_issues_by_test_item - 跨專案搜尋 Test Item 的 Issues
        
        Args:
            parameters: {"test_item": "Sequential Read", "customer": "WD"}
        """
        error = self.validate_parameters(parameters, required=['test_item'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        test_item = parameters.get('test_item')
        customer = parameters.get('customer')
        
        # 獲取所有專案
        projects = self.api_client.get_all_projects()
        
        # 如果指定客戶，先過濾
        if customer:
            projects = [
                p for p in projects
                if customer.lower() in p.get('customer', '').lower()
            ]
        
        # 收集所有專案中該測項的 Issues
        all_issues = []
        projects_with_issues = []
        
        for project in projects:
            project_id = project.get('id') or project.get('projectUid')
            if not project_id:
                continue
            
            issues = self._fetch_known_issues(project_ids=[project_id])
            
            # 過濾特定 Test Item
            matching_issues = [
                {**issue, 'project_name': project.get('projectName')}
                for issue in issues
                if test_item.lower() in issue.get('test_item_name', '').lower()
            ]
            
            if matching_issues:
                all_issues.extend(matching_issues)
                projects_with_issues.append(project.get('projectName'))
        
        if not all_issues:
            customer_msg = f"（{customer} 客戶）" if customer else ""
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"沒有找到 {test_item} 測項的 Known Issues{customer_msg}"
            )
        
        formatted_issues = [self._format_issue(issue) for issue in all_issues]
        
        customer_msg = f"（{customer} 客戶）" if customer else ""
        projects_msg = f"涉及專案: {', '.join(projects_with_issues[:5])}"
        if len(projects_with_issues) > 5:
            projects_msg += f" 等 {len(projects_with_issues)} 個專案"
        
        return QueryResult.success(
            data=formatted_issues,
            query_type=self.handler_name,
            parameters=parameters,
            message=f"找到 {len(formatted_issues)} 個 {test_item} 的 Known Issues{customer_msg}。{projects_msg}",
            metadata={"projects_with_issues": projects_with_issues}
        )
    
    # =========================================================================
    # 輔助方法
    # =========================================================================
    
    def _get_project_id(self, project_name: str) -> Optional[int]:
        """
        根據專案名稱獲取專案 ID
        
        Args:
            project_name: 專案名稱
            
        Returns:
            專案 ID，如果找不到則返回 None
        """
        projects = self.api_client.get_all_projects()
        project_name_lower = project_name.lower()
        
        # 精確匹配
        for project in projects:
            if project.get('projectName', '').lower() == project_name_lower:
                return project.get('id') or project.get('projectUid')
        
        # 模糊匹配
        for project in projects:
            if project_name_lower in project.get('projectName', '').lower():
                return project.get('id') or project.get('projectUid')
        
        return None
    
    def _fetch_known_issues(
        self,
        project_ids: List[str] = None,
        root_ids: List[str] = None,
        show_disabled: bool = True
    ) -> List[Dict[str, Any]]:
        """
        從 SAF API 獲取 Known Issues
        
        注意：SAF API 目前不支援 project_id 過濾，返回所有 Issues。
        因此這裡需要做客戶端過濾。
        
        Args:
            project_ids: 專案 ID 列表（用於客戶端過濾）
            root_ids: Root ID 列表
            show_disabled: 是否顯示已停用的 Issues
            
        Returns:
            Known Issues 列表（已過濾）
        """
        try:
            # SAF API 不支援 project_id 過濾，總是返回所有 Issues
            # 傳入空列表讓 API 返回全部，然後在客戶端過濾
            all_issues = self.api_client.get_known_issues(
                project_ids=None,  # 不傳 project_ids，因為 API 不支援
                root_ids=root_ids,
                show_disabled=show_disabled
            )
            
            # 客戶端過濾：如果指定了 project_ids，則過濾
            if project_ids and all_issues:
                # 轉換為 set 加速查找
                project_id_set = set(str(pid) for pid in project_ids)
                filtered_issues = [
                    issue for issue in all_issues
                    if str(issue.get('project_id', '')) in project_id_set
                ]
                logger.info(f"Known Issues 客戶端過濾: {len(all_issues)} -> {len(filtered_issues)} (project_ids={project_ids})")
                return filtered_issues
            
            return all_issues
            
        except Exception as e:
            logger.error(f"獲取 Known Issues 失敗: {str(e)}")
            return []
    
    def _fetch_all_known_issues(self) -> List[Dict[str, Any]]:
        """
        獲取所有專案的 Known Issues
        
        Returns:
            所有 Known Issues 列表
        """
        # 直接獲取所有 Known Issues（SAF API 不支援過濾）
        return self._fetch_known_issues(show_disabled=True)
    
    def _fetch_known_issues_by_project_name(
        self,
        project_name: str,
        show_disabled: bool = True
    ) -> List[Dict[str, Any]]:
        """
        用 project_name 過濾 Known Issues
        
        由於 SAF API 的專案 ID 和 Known Issues 使用不同的 ID 系統，
        這個方法先獲取所有 Known Issues，然後用 project_name 模糊匹配過濾。
        
        Args:
            project_name: 專案名稱（支援模糊匹配）
            show_disabled: 是否顯示已停用的 Issues
            
        Returns:
            符合的 Known Issues 列表
        """
        try:
            # 獲取所有 Known Issues
            all_issues = self.api_client.get_known_issues(show_disabled=show_disabled)
            
            if not all_issues:
                return []
            
            # 用 project_name 模糊匹配過濾
            project_name_lower = project_name.lower()
            filtered_issues = [
                issue for issue in all_issues
                if project_name_lower in issue.get('project_name', '').lower()
            ]
            
            logger.info(f"Known Issues 按 project_name 過濾: {len(all_issues)} -> {len(filtered_issues)} (project_name={project_name})")
            return filtered_issues
            
        except Exception as e:
            logger.error(f"獲取 Known Issues by project_name 失敗: {str(e)}")
            return []
    
    def _format_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化 Known Issue 資料
        
        Args:
            issue: 原始 Issue 資料
            
        Returns:
            格式化後的 Issue 資料
        """
        return {
            "id": issue.get('id'),
            "issue_id": issue.get('issue_id'),
            "project_name": issue.get('project_name'),
            "test_item_name": issue.get('test_item_name'),
            "case_name": issue.get('case_name'),
            "case_path": issue.get('case_path'),
            "jira_id": issue.get('jira_id'),
            "jira_link": issue.get('jira_link'),
            "note": issue.get('note'),
            "is_enabled": issue.get('is_enable', True),
            "created_by": issue.get('created_by'),
            "created_at": issue.get('created_at')
        }
