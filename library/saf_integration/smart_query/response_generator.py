"""
SAF 回答生成器
==============

根據查詢結果生成自然語言回答，包含 Markdown Table 格式。
支援圖表視覺化（圓餅圖、折線圖、柱狀圖）。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any, List, Optional

from .intent_types import IntentType
from .query_handlers import QueryResult, QueryStatus
from library.common.chart_formatter import ChartFormatter

logger = logging.getLogger(__name__)


class SAFResponseGenerator:
    """
    SAF 回答生成器
    
    根據查詢結果生成格式化的自然語言回答。
    """
    
    def __init__(self):
        """初始化回答生成器"""
        pass
    
    def generate(self, query_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成回答
        
        Args:
            query_result: 來自 SmartQueryService.query() 的結果
            
        Returns:
            Dict: 包含 answer（自然語言）和 table（結構化資料）
        """
        intent_type = query_result.get('intent', {}).get('type', 'unknown')
        result_data = query_result.get('result', {})
        status = result_data.get('status', 'error')
        
        # 處理錯誤情況
        if status == 'error':
            return self._generate_error_response(result_data)
        
        # 處理無結果情況
        if status == 'no_results':
            return self._generate_no_results_response(intent_type, result_data)
        
        # 根據意圖類型生成回答
        intent_enum = IntentType.from_string(intent_type)
        
        generators = {
            IntentType.QUERY_PROJECTS_BY_CUSTOMER: self._generate_customer_projects_response,
            IntentType.QUERY_PROJECTS_BY_CONTROLLER: self._generate_controller_projects_response,
            IntentType.QUERY_PROJECT_DETAIL: self._generate_project_detail_response,
            IntentType.QUERY_PROJECT_SUMMARY: self._generate_project_summary_response,
            # Phase 3: 測試摘要回應生成器
            IntentType.QUERY_PROJECT_TEST_SUMMARY: self._generate_test_summary_response,
            IntentType.QUERY_PROJECT_TEST_BY_CATEGORY: self._generate_test_by_category_response,
            IntentType.QUERY_PROJECT_TEST_BY_CAPACITY: self._generate_test_by_capacity_response,
            # Phase 4: FW 版本查詢回應生成器
            IntentType.QUERY_PROJECT_TEST_SUMMARY_BY_FW: self._generate_test_summary_by_fw_response,
            # Phase 5.1: FW 版本比較回應生成器
            IntentType.COMPARE_FW_VERSIONS: self._generate_compare_fw_versions_response,
            # Phase 5.2: 智能版本選擇回應生成器
            IntentType.COMPARE_LATEST_FW: self._generate_compare_latest_fw_response,
            IntentType.LIST_FW_VERSIONS: self._generate_list_fw_versions_response,
            # Phase 5.4: 多版本趨勢比較回應生成器
            IntentType.COMPARE_MULTIPLE_FW: self._generate_compare_multiple_fw_response,
            # Phase 7: PL 查詢回應生成器
            IntentType.QUERY_PROJECTS_BY_PL: self._generate_pl_projects_response,
            # Phase 8: 日期/月份查詢回應生成器
            IntentType.QUERY_PROJECTS_BY_DATE: self._generate_date_projects_response,
            IntentType.QUERY_PROJECTS_BY_MONTH: self._generate_date_projects_response,
            # Phase 9: Sub Version 查詢回應生成器
            IntentType.LIST_SUB_VERSIONS: self._generate_sub_versions_response,
            IntentType.LIST_FW_BY_SUB_VERSION: self._generate_fw_by_sub_version_response,
            # Phase 13: FW 日期範圍查詢回應生成器
            IntentType.LIST_FW_BY_DATE_RANGE: self._generate_fw_by_date_range_response,
            # Phase 15: Known Issues 查詢回應生成器
            IntentType.QUERY_PROJECT_KNOWN_ISSUES: self._generate_known_issues_response,
            IntentType.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: self._generate_known_issues_response,
            IntentType.COUNT_PROJECT_KNOWN_ISSUES: self._generate_known_issues_response,
            IntentType.RANK_PROJECTS_BY_KNOWN_ISSUES: self._generate_known_issues_rank_response,
            IntentType.QUERY_KNOWN_ISSUES_BY_CREATOR: self._generate_known_issues_response,
            IntentType.LIST_KNOWN_ISSUES_CREATORS: self._generate_known_issues_creators_response,
            IntentType.QUERY_KNOWN_ISSUES_WITH_JIRA: self._generate_known_issues_response,
            IntentType.QUERY_KNOWN_ISSUES_WITHOUT_JIRA: self._generate_known_issues_response,
            IntentType.QUERY_RECENT_KNOWN_ISSUES: self._generate_known_issues_response,
            IntentType.QUERY_KNOWN_ISSUES_BY_DATE_RANGE: self._generate_known_issues_response,
            IntentType.SEARCH_KNOWN_ISSUES_BY_KEYWORD: self._generate_known_issues_response,
            IntentType.QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM: self._generate_known_issues_response,
            # Phase 16: Test Jobs 查詢回應生成器
            IntentType.QUERY_PROJECT_FW_TEST_JOBS: self._generate_test_jobs_response,
            # Phase 17: Compare Test Jobs 查詢回應生成器
            IntentType.COMPARE_FW_TEST_JOBS: self._generate_compare_test_jobs_response,
            IntentType.COUNT_PROJECTS: self._generate_count_response,
            IntentType.LIST_ALL_CUSTOMERS: self._generate_customers_list_response,
            IntentType.LIST_ALL_CONTROLLERS: self._generate_controllers_list_response,
            IntentType.LIST_ALL_PLS: self._generate_pls_list_response,
            IntentType.UNKNOWN: self._generate_unknown_response,
        }
        
        generator = generators.get(intent_enum, self._generate_default_response)
        return generator(result_data, query_result)
    
    def _generate_customer_projects_response(self, result_data: Dict, 
                                              full_result: Dict) -> Dict[str, Any]:
        """生成客戶專案查詢的回答"""
        data = result_data.get('data', [])
        parameters = result_data.get('parameters', {})
        customer = parameters.get('customer', '未知客戶')
        count = len(data)
        
        # 生成自然語言回答
        if count == 0:
            answer = f"找不到 **{customer}** 的專案。"
            return {'answer': answer, 'table': []}
        
        answer = f"**{customer}** 目前擁有 **{count}** 個專案：\n\n"
        answer += self._generate_projects_table(data)
        
        return {
            'answer': answer,
            'table': data,
            'summary': f"{customer} 擁有 {count} 個專案"
        }
    
    def _generate_controller_projects_response(self, result_data: Dict,
                                                full_result: Dict) -> Dict[str, Any]:
        """生成控制器專案查詢的回答"""
        data = result_data.get('data', [])
        parameters = result_data.get('parameters', {})
        controller = parameters.get('controller', '未知控制器')
        count = len(data)
        
        if count == 0:
            answer = f"找不到使用 **{controller}** 控制器的專案。"
            return {'answer': answer, 'table': []}
        
        answer = f"使用 **{controller}** 控制器的專案共有 **{count}** 個：\n\n"
        answer += self._generate_projects_table(data)
        
        return {
            'answer': answer,
            'table': data,
            'summary': f"{count} 個專案使用 {controller} 控制器"
        }
    
    # ============================================================
    # Phase 7: PL 查詢回應生成方法
    # ============================================================
    
    def _generate_pl_projects_response(self, result_data: Dict,
                                        full_result: Dict) -> Dict[str, Any]:
        """
        生成 PL（專案負責人）專案查詢的回答
        
        支援分組顯示：當查詢結果包含多種 PL 格式時，
        會按實際 PL 名稱分組顯示。
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        parameters = result_data.get('parameters', {})
        pl = parameters.get('pl', '未知 PL')
        
        # 新格式：包含分組資訊
        if isinstance(data, dict) and 'groups' in data:
            return self._generate_pl_grouped_response(data, pl)
        
        # 向後相容：舊格式（扁平列表）
        if isinstance(data, list):
            return self._generate_pl_flat_response(data, pl)
        
        # 其他情況：空結果
        return {
            'answer': f"找不到專案負責人 **{pl}** 的專案。",
            'table': [],
            'summary': f"找不到 {pl} 的專案"
        }
    
    def _generate_pl_grouped_response(self, data: Dict, pl: str) -> Dict[str, Any]:
        """
        生成按 PL 分組的回應
        
        Args:
            data: 包含 groups 的資料結構
            pl: 查詢的 PL 名稱
            
        Returns:
            Dict: 格式化的回應
        """
        query_pl = data.get('query_pl', pl)
        total_count = data.get('total_count', 0)
        groups = data.get('groups', [])
        flat_projects = data.get('projects', [])
        
        if total_count == 0:
            return {
                'answer': f"找不到專案負責人 **{query_pl}** 的專案。",
                'table': [],
                'summary': f"找不到 {query_pl} 的專案"
            }
        
        # 生成回答
        group_count = len(groups)
        
        if group_count == 1:
            # 單一 PL 格式
            answer = f"**{query_pl}** 負責 **{total_count}** 個專案：\n\n"
            answer += self._generate_projects_table(flat_projects)
        else:
            # 多種 PL 格式 - 按分組顯示
            answer = f"找到 **{total_count}** 個與 **{query_pl}** 相關的專案（{group_count} 種 PL 格式）：\n\n"
            
            for group in groups:
                pl_name = group.get('pl_name', '未知')
                count = group.get('count', 0)
                projects = group.get('projects', [])
                
                answer += f"### PL: {pl_name} ({count} 個專案)\n\n"
                answer += self._generate_projects_table(projects)
                answer += "\n"
        
        return {
            'answer': answer,
            'table': flat_projects,
            'groups': groups,
            'summary': f"{query_pl} 相關專案共 {total_count} 個（{group_count} 種 PL 格式）"
        }
    
    def _generate_pl_flat_response(self, data: List, pl: str) -> Dict[str, Any]:
        """
        生成扁平列表的 PL 回應（向後相容）
        
        Args:
            data: 專案列表
            pl: PL 名稱
            
        Returns:
            Dict: 格式化的回應
        """
        count = len(data)
        
        if count == 0:
            return {
                'answer': f"找不到專案負責人 **{pl}** 的專案。",
                'table': [],
                'summary': f"找不到 {pl} 的專案"
            }
        
        answer = f"**{pl}** 負責 **{count}** 個專案：\n\n"
        answer += self._generate_projects_table(data)
        
        return {
            'answer': answer,
            'table': data,
            'summary': f"{pl} 負責 {count} 個專案"
        }

    # ============================================================
    # Phase 8: 日期/月份查詢回應生成方法
    # ============================================================

    def _generate_date_projects_response(self, result_data: Dict,
                                          full_result: Dict) -> Dict[str, Any]:
        """
        生成日期/月份專案查詢的回答
        
        支援格式：
        - 月份查詢：「2025年12月有哪些專案」
        - 年份查詢：「今年有哪些專案」
        - 相對查詢：「本月」「上個月」
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        parameters = result_data.get('parameters', {})
        
        # 判斷資料格式：新格式（有 summary）或舊格式（直接列表）
        if isinstance(data, dict):
            projects = data.get('projects', [])
            summary = data.get('summary', {})
            query_info = data.get('query_info', {})
        else:
            projects = data if isinstance(data, list) else []
            summary = {}
            query_info = parameters
        
        total_count = len(projects)
        
        # 構建時間描述
        time_desc = self._build_time_description(query_info or parameters)
        
        if total_count == 0:
            return {
                'answer': f"在 **{time_desc}** 期間找不到任何新建立的專案。",
                'table': [],
                'summary': f"{time_desc} 無專案"
            }
        
        # 生成回答
        answer = f"## 📅 {time_desc} 新建專案列表\n\n"
        answer += f"在 **{time_desc}** 期間共有 **{total_count}** 個專案建立：\n\n"
        
        # 如果有月度統計，顯示分組
        if 'by_month' in data and data['by_month']:
            answer += self._generate_monthly_grouped_table(data['by_month'], projects)
        else:
            # 簡單表格
            answer += self._generate_date_projects_table(projects)
        
        return {
            'answer': answer,
            'table': projects,
            'summary': f"{time_desc} 共 {total_count} 個專案"
        }
    
    def _build_time_description(self, query_info: Dict) -> str:
        """
        構建時間描述字串
        
        Args:
            query_info: 查詢參數
            
        Returns:
            str: 時間描述（如「2025年12月」「本月」「今年」）
        """
        date_range = query_info.get('date_range', '')
        year = query_info.get('year')
        month = query_info.get('month')
        
        if date_range == 'this_month':
            return "本月"
        elif date_range == 'last_month':
            return "上個月"
        elif date_range == 'this_year':
            return "今年"
        elif year and month:
            return f"{year}年{month}月"
        elif year:
            return f"{year}年"
        elif month:
            return f"{month}月"
        else:
            return "指定期間"
    
    def _generate_date_projects_table(self, projects: List[Dict]) -> str:
        """
        生成日期專案的 Markdown 表格
        
        Args:
            projects: 專案列表
            
        Returns:
            str: Markdown 表格
        """
        if not projects:
            return ""
        
        table = "| 專案名稱 | 客戶 | 控制器 | 建立日期 | PL |\n"
        table += "|----------|------|--------|----------|----|\n"
        
        for project in projects:
            name = project.get('projectName', '-')
            customer = project.get('customer', '-')
            controller = project.get('controller', '-')
            created_date = project.get('createdDate', '-')
            pl = project.get('pl', '-')
            
            table += f"| {name} | {customer} | {controller} | {created_date} | {pl} |\n"
        
        return table + "\n"
    
    def _generate_monthly_grouped_table(self, by_month: List[Dict], projects: List[Dict]) -> str:
        """
        生成按月份分組的表格
        
        Args:
            by_month: 月度統計
            projects: 專案列表
            
        Returns:
            str: Markdown 格式的分組表格
        """
        # 先顯示月度統計
        table = "### 📊 月度統計\n\n"
        table += "| 月份 | 專案數 |\n"
        table += "|------|--------|\n"
        
        for month_data in by_month:
            month = month_data.get('month', '-')
            count = month_data.get('count', 0)
            table += f"| {month} | {count} |\n"
        
        table += "\n### 📋 專案明細\n\n"
        table += self._generate_date_projects_table(projects)
        
        return table

    def _generate_project_detail_response(self, result_data: Dict,
                                           full_result: Dict) -> Dict[str, Any]:
        """生成專案詳情查詢的回答"""
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該專案的詳細資訊。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        
        answer = f"**{project_name}** 專案詳細資訊：\n\n"
        answer += self._generate_detail_table(data)
        
        return {
            'answer': answer,
            'table': [data] if isinstance(data, dict) else data,
            'summary': f"{project_name} 專案詳情"
        }
    
    def _generate_project_summary_response(self, result_data: Dict,
                                            full_result: Dict) -> Dict[str, Any]:
        """生成專案測試摘要的回答"""
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該專案的測試摘要。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        
        answer = f"**{project_name}** 專案測試摘要：\n\n"
        answer += self._generate_summary_table(data)
        
        return {
            'answer': answer,
            'table': [data] if isinstance(data, dict) else data,
            'summary': f"{project_name} 測試摘要"
        }
    
    # ============================================================
    # Phase 3: 測試摘要回應生成方法
    # ============================================================
    
    def _generate_test_summary_response(self, result_data: Dict,
                                         full_result: Dict) -> Dict[str, Any]:
        """
        生成專案測試結果統計的回答
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該專案的測試結果統計。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        summary = data.get('summary', {})
        by_category = data.get('byCategory', [])
        by_capacity = data.get('byCapacity', [])
        
        # 構建回答
        total_pass = summary.get('totalPass', 0)
        total_fail = summary.get('totalFail', 0)
        pass_rate = summary.get('overallPassRate', 'N/A')
        
        answer = f"## 📊 **{project_name}** 專案測試結果統計\n\n"
        answer += f"### 整體統計\n"
        answer += f"- **總通過數**：{total_pass}\n"
        answer += f"- **總失敗數**：{total_fail}\n"
        answer += f"- **通過率**：{pass_rate}\n\n"
        
        # 按類別統計表格
        if by_category:
            answer += "### 📁 按測試類別\n\n"
            answer += "| 類別 | Pass | Fail | 總數 | 通過率 |\n"
            answer += "|------|------|------|------|--------|\n"
            for cat in by_category:
                answer += f"| {cat.get('name', '-')} | {cat.get('pass', 0)} | {cat.get('fail', 0)} | {cat.get('total', 0)} | {cat.get('passRate', 'N/A')} |\n"
            answer += "\n"
        
        # 按容量統計表格
        if by_capacity:
            answer += "### 💾 按容量規格\n\n"
            answer += "| 容量 | Pass | Fail | 總數 | 通過率 |\n"
            answer += "|------|------|------|------|--------|\n"
            for cap in by_capacity:
                answer += f"| {cap.get('name', '-')} | {cap.get('pass', 0)} | {cap.get('fail', 0)} | {cap.get('total', 0)} | {cap.get('passRate', 'N/A')} |\n"
            answer += "\n"
        
        # 提示可用的進一步查詢
        answer += f"\n💡 **提示**：您可以查詢特定類別或容量的詳細資訊，例如：\n"
        answer += f"- 「{project_name} 的 Compliance 測試結果」\n"
        answer += f"- 「{project_name} 的 1TB 測試狀況」\n"
        
        return {
            'answer': answer,
            'table': {
                'summary': summary,
                'byCategory': by_category,
                'byCapacity': by_capacity
            },
            'summary': f"{project_name} 測試統計：{total_pass} Pass, {total_fail} Fail ({pass_rate})"
        }
    
    def _generate_test_by_category_response(self, result_data: Dict,
                                             full_result: Dict) -> Dict[str, Any]:
        """
        生成按類別查詢測試結果的回答
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該類別的測試結果。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        category = data.get('category', '未知類別')
        pass_count = data.get('pass', 0)
        fail_count = data.get('fail', 0)
        total = data.get('total', 0)
        pass_rate = data.get('passRate', 'N/A')
        capacity_filter = data.get('capacity_filter')
        
        answer = f"## 📁 **{project_name}** - {category} 測試結果\n\n"
        
        if capacity_filter:
            answer += f"（已按 {capacity_filter} 容量過濾）\n\n"
        
        answer += f"| 指標 | 數值 |\n"
        answer += f"|------|------|\n"
        answer += f"| 通過數 | **{pass_count}** |\n"
        answer += f"| 失敗數 | **{fail_count}** |\n"
        answer += f"| 總數 | {total} |\n"
        answer += f"| 通過率 | **{pass_rate}** |\n"
        
        # 狀態指示
        if pass_rate != 'N/A':
            rate_value = float(pass_rate.replace('%', ''))
            if rate_value >= 95:
                answer += f"\n✅ 測試狀態：**優秀**\n"
            elif rate_value >= 80:
                answer += f"\n🟡 測試狀態：**良好**\n"
            else:
                answer += f"\n🔴 測試狀態：**需要關注**\n"
        
        return {
            'answer': answer,
            'table': [data],
            'summary': f"{project_name} {category}：{pass_count} Pass, {fail_count} Fail"
        }
    
    def _generate_test_by_capacity_response(self, result_data: Dict,
                                             full_result: Dict) -> Dict[str, Any]:
        """
        生成按容量查詢測試結果的回答
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該容量規格的測試結果。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        capacity = data.get('capacity', '未知容量')
        pass_count = data.get('pass', 0)
        fail_count = data.get('fail', 0)
        total = data.get('total', 0)
        pass_rate = data.get('passRate', 'N/A')
        
        answer = f"## 💾 **{project_name}** - {capacity} 測試結果\n\n"
        
        answer += f"| 指標 | 數值 |\n"
        answer += f"|------|------|\n"
        answer += f"| 通過數 | **{pass_count}** |\n"
        answer += f"| 失敗數 | **{fail_count}** |\n"
        answer += f"| 總數 | {total} |\n"
        answer += f"| 通過率 | **{pass_rate}** |\n"
        
        # 狀態指示
        if pass_rate != 'N/A':
            rate_value = float(pass_rate.replace('%', ''))
            if rate_value >= 95:
                answer += f"\n✅ 測試狀態：**優秀**\n"
            elif rate_value >= 80:
                answer += f"\n🟡 測試狀態：**良好**\n"
            else:
                answer += f"\n🔴 測試狀態：**需要關注**\n"
        
        return {
            'answer': answer,
            'table': [data],
            'summary': f"{project_name} {capacity}：{pass_count} Pass, {fail_count} Fail"
        }
    
    # ============================================================
    # Phase 4: FW 版本查詢回應生成方法
    # ============================================================
    
    def _generate_test_summary_by_fw_response(self, result_data: Dict,
                                               full_result: Dict) -> Dict[str, Any]:
        """
        生成按 FW 版本查詢測試結果的回答
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "找不到該 FW 版本的測試結果。",
                'table': []
            }
        
        project_name = data.get('projectName', '未知專案')
        fw_version = data.get('fwVersion', '未知版本')
        customer = data.get('customer', '-')
        controller = data.get('controller', '-')
        summary = data.get('summary', {})
        categories = data.get('categories', [])
        capacities = data.get('capacities', [])
        
        # 構建回答
        total_pass = summary.get('pass', 0)
        total_fail = summary.get('fail', 0)
        pass_rate = summary.get('passRate', 'N/A')
        
        # 標題區
        answer = f"專案 '{project_name}' FW 版本 '{fw_version}' 測試結果：\n"
        answer += f"✅ Pass: {total_pass}  ❌ Fail: {total_fail}  📊 通過率: {pass_rate}\n\n"
        
        # 專案資訊表格
        answer += "| 項目 | 內容 |\n"
        answer += "|------|------|\n"
        answer += f"| 專案名稱 | {project_name} |\n"
        answer += f"| FW 版本 | {fw_version} |\n"
        answer += f"| 客戶 | {customer} |\n"
        answer += f"| 控制器 | {controller} |\n"
        
        # 如果有類別統計
        if categories:
            answer += "\n### 📁 按測試類別\n\n"
            answer += "| 類別 | Pass | Fail | 總數 |\n"
            answer += "|------|------|------|------|\n"
            for cat in categories:
                # categories 可能是字典或字串
                if isinstance(cat, dict):
                    cat_name = cat.get('name', '-')
                    cat_pass = cat.get('pass', 0)
                    cat_fail = cat.get('fail', 0)
                    cat_total = cat.get('total', cat_pass + cat_fail)
                    answer += f"| {cat_name} | {cat_pass} | {cat_fail} | {cat_total} |\n"
                else:
                    # 如果只是字串，只顯示名稱
                    answer += f"| {cat} | - | - | - |\n"
        
        # 如果有容量統計
        if capacities:
            answer += "\n### 💾 可用容量規格\n\n"
            # capacities 可能是字串列表（如 ['512GB', '1TB']）或字典列表
            first_item = capacities[0] if capacities else None
            if isinstance(first_item, dict):
                # 字典格式：有詳細統計
                answer += "| 容量 | Pass | Fail | 總數 |\n"
                answer += "|------|------|------|------|\n"
                for cap in capacities:
                    cap_name = cap.get('name', '-')
                    cap_pass = cap.get('pass', 0)
                    cap_fail = cap.get('fail', 0)
                    cap_total = cap.get('total', cap_pass + cap_fail)
                    answer += f"| {cap_name} | {cap_pass} | {cap_fail} | {cap_total} |\n"
            else:
                # 字串列表格式：只顯示可用容量
                answer += "可用容量：" + ", ".join(str(c) for c in capacities) + "\n"
        
        # 📊 添加圖表視覺化
        answer += self._generate_test_summary_charts(
            project_name=project_name,
            fw_version=fw_version,
            total_pass=total_pass,
            total_fail=total_fail,
            categories=categories
        )
        
        return {
            'answer': answer,
            'table': [data],
            'summary': f"{project_name} FW {fw_version}：{total_pass} Pass, {total_fail} Fail ({pass_rate})"
        }
    
    def _generate_test_summary_charts(
        self,
        project_name: str,
        fw_version: str,
        total_pass: int,
        total_fail: int,
        categories: List[Dict]
    ) -> str:
        """
        📊 生成測試摘要圖表視覺化
        
        生成兩種圓餅圖：
        1. Pass/Fail 整體分佈
        2. 各測試類別 Fail 分佈（只顯示 Fail > 0 的類別）
        
        Args:
            project_name: 專案名稱
            fw_version: FW 版本
            total_pass: 總通過數
            total_fail: 總失敗數
            categories: 類別統計列表
            
        Returns:
            str: 包含圖表標記的 Markdown 字串
        """
        charts_md = "\n\n### 📊 測試結果視覺化\n\n"
        
        try:
            # ===== 圖表 1: Pass/Fail 整體分佈圓餅圖 =====
            if total_pass > 0 or total_fail > 0:
                pass_fail_chart = ChartFormatter.pie_chart(
                    title=f"{project_name} {fw_version} Pass/Fail 分佈",
                    items=[
                        {"name": "Pass", "value": total_pass, "color": "#52c41a"},
                        {"name": "Fail", "value": total_fail, "color": "#ff4d4f"}
                    ],
                    description=f"總計 {total_pass + total_fail} 個測試案例",
                    options={
                        "height": 280,
                        "showLegend": True,
                        "innerRadius": 0  # 一般圓餅圖
                    }
                )
                charts_md += pass_fail_chart + "\n\n"
            
            # ===== 圖表 2: 各類別 Fail 分佈圓餅圖 =====
            # 只顯示 Fail > 0 的類別
            fail_by_category = []
            category_colors = [
                '#ff4d4f',   # 紅色
                '#faad14',   # 橙色
                '#722ed1',   # 紫色
                '#13c2c2',   # 青色
                '#1890ff',   # 藍色
                '#eb2f96',   # 洋紅
                '#a0d911',   # 青檸
                '#2f54eb',   # 深藍
                '#fa8c16',   # 深橙
                '#52c41a'    # 綠色
            ]
            
            for cat in categories:
                if isinstance(cat, dict):
                    cat_name = cat.get('name', '')
                    cat_fail = cat.get('fail', 0)
                    if cat_fail > 0 and cat_name:
                        fail_by_category.append({
                            "name": cat_name,
                            "value": cat_fail
                        })
            
            # 排序：Fail 數量由大到小
            fail_by_category.sort(key=lambda x: x['value'], reverse=True)
            
            # 分配顏色
            for i, item in enumerate(fail_by_category):
                item['color'] = category_colors[i % len(category_colors)]
            
            if fail_by_category:
                category_fail_chart = ChartFormatter.pie_chart(
                    title="各測試類別 Fail 分佈",
                    items=fail_by_category,
                    description=f"顯示 {len(fail_by_category)} 個有 Fail 的測試類別",
                    options={
                        "height": 300,
                        "showLegend": True,
                        "innerRadius": 60  # 甜甜圈圖
                    }
                )
                charts_md += category_fail_chart
            
            logger.info(f"📊 已生成測試摘要圖表：Pass/Fail 分佈 + {len(fail_by_category)} 個類別 Fail 分佈")
            
        except Exception as e:
            logger.error(f"生成測試摘要圖表時發生錯誤: {str(e)}")
            charts_md += f"*（圖表生成失敗：{str(e)}）*\n"
        
        return charts_md
    
    # ============================================================
    # Phase 5: FW 版本比較回應生成方法
    # ============================================================
    
    def _generate_compare_fw_versions_response(self, result_data: Dict,
                                                full_result: Dict) -> Dict[str, Any]:
        """
        生成 FW 版本比較的回答
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        data = result_data.get('data', {})
        
        if not data:
            return {
                'answer': "無法生成比較結果。",
                'table': []
            }
        
        # 優先使用 Handler 返回的 message（包含完整的比較資訊）
        handler_message = result_data.get('message', '')
        if handler_message:
            # Handler 已經生成了完整的格式化訊息
            project_name = data.get('projectName', '未知專案')
            fw_1 = data.get('fw_1', {})
            fw_2 = data.get('fw_2', {})
            diff = data.get('diff', {})
            
            fw_version_1 = fw_1.get('version', '版本1')
            fw_version_2 = fw_2.get('version', '版本2')
            trend = diff.get('trend', 'stable')
            
            trend_icon = {
                'improved': '📈 改善',
                'declined': '📉 退步',
                'stable': '➡️ 持平'
            }.get(trend, '➡️ 持平')
            
            # 生成表格資料（用於前端顯示）
            table_data = [
                {
                    'fw_version': fw_version_1,
                    'pass': fw_1.get('pass', 0),
                    'fail': fw_1.get('fail', 0),
                    'total': fw_1.get('total', 0),
                    'passRate': fw_1.get('passRate', 'N/A')
                },
                {
                    'fw_version': fw_version_2,
                    'pass': fw_2.get('pass', 0),
                    'fail': fw_2.get('fail', 0),
                    'total': fw_2.get('total', 0),
                    'passRate': fw_2.get('passRate', 'N/A')
                }
            ]
            
            return {
                'answer': handler_message,  # 直接使用 Handler 的完整訊息
                'table': table_data,
                'summary': f"{project_name} {fw_version_1} vs {fw_version_2}: {trend_icon}",
                'diff': diff
            }
        
        # Fallback: 如果沒有 handler_message，使用舊邏輯
        project_name = data.get('projectName', '未知專案')
        fw_1 = data.get('fw_1', {})
        fw_2 = data.get('fw_2', {})
        diff = data.get('diff', {})
        
        fw_version_1 = fw_1.get('version', '版本1')
        fw_version_2 = fw_2.get('version', '版本2')
        
        # 趨勢圖示
        trend = diff.get('trend', 'stable')
        trend_icon = {
            'improved': '📈 改善',
            'declined': '📉 退步',
            'stable': '➡️ 持平'
        }.get(trend, '➡️ 持平')
        
        # 變化箭頭
        def format_change(val):
            if isinstance(val, (int, float)):
                if val > 0:
                    return f"+{val} ⬆️"
                elif val < 0:
                    return f"{val} ⬇️"
            return "0 ➡️"
        
        # 構建回答
        answer = f"## 📊 {project_name} 專案 FW 版本比較\n\n"
        answer += f"### 版本對比：{fw_version_1} vs {fw_version_2}\n\n"
        
        # 比較表格
        answer += "| 指標 | " + fw_version_1 + " | " + fw_version_2 + " | 變化 |\n"
        answer += "|------|--------|--------|------|\n"
        answer += f"| Pass | {fw_1.get('pass', 0)} | {fw_2.get('pass', 0)} | {format_change(diff.get('pass_change', 0))} |\n"
        answer += f"| Fail | {fw_1.get('fail', 0)} | {fw_2.get('fail', 0)} | {format_change(diff.get('fail_change', 0))} |\n"
        answer += f"| 通過率 | {fw_1.get('passRate', 'N/A')} | {fw_2.get('passRate', 'N/A')} | {diff.get('passRate_change', 'N/A')} |\n\n"
        
        # 趨勢分析
        answer += f"### 📈 趨勢分析\n\n"
        answer += f"**{trend_icon}**：{fw_version_1} 相較於 {fw_version_2} "
        
        if trend == 'improved':
            answer += "表現**更好**\n"
        elif trend == 'declined':
            answer += "表現**較差**\n"
        else:
            answer += "表現**相當**\n"
        
        # 生成表格資料（用於前端顯示）
        table_data = [
            {
                'fw_version': fw_version_1,
                'pass': fw_1.get('pass', 0),
                'fail': fw_1.get('fail', 0),
                'total': fw_1.get('total', 0),
                'passRate': fw_1.get('passRate', 'N/A')
            },
            {
                'fw_version': fw_version_2,
                'pass': fw_2.get('pass', 0),
                'fail': fw_2.get('fail', 0),
                'total': fw_2.get('total', 0),
                'passRate': fw_2.get('passRate', 'N/A')
            }
        ]
        
        return {
            'answer': answer,
            'table': table_data,
            'summary': f"{project_name} {fw_version_1} vs {fw_version_2}: {trend_icon}",
            'diff': diff
        }
    
    # ============================================================
    # Phase 5.2: 智能版本選擇回應生成方法
    # ============================================================
    
    def _generate_compare_latest_fw_response(self, result_data: Dict,
                                              full_result: Dict) -> Dict[str, Any]:
        """
        生成自動比較最新 FW 版本的回答
        
        此方法直接使用 Handler 返回的 message，因為：
        1. CompareLatestFWHandler 已經加入了自動選擇的說明
        2. 比較邏輯由 CompareFWVersionsHandler 處理，格式一致
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        # 優先使用 Handler 返回的 message
        handler_message = result_data.get('message', '')
        
        if handler_message:
            data = result_data.get('data', {})
            project_name = data.get('projectName', '未知專案')
            fw_1 = data.get('fw_1', {})
            fw_2 = data.get('fw_2', {})
            diff = data.get('diff', {})
            metadata = result_data.get('metadata', {})
            
            fw_version_1 = fw_1.get('version', '版本1')
            fw_version_2 = fw_2.get('version', '版本2')
            trend = diff.get('trend', 'stable')
            
            trend_icon = {
                'improved': '📈 改善',
                'declined': '📉 退步',
                'stable': '➡️ 持平'
            }.get(trend, '➡️ 持平')
            
            # 生成表格資料
            table_data = []
            if fw_1:
                table_data.append({
                    'fw_version': fw_version_1,
                    'pass': fw_1.get('pass', 0),
                    'fail': fw_1.get('fail', 0),
                    'total': fw_1.get('total', 0),
                    'passRate': fw_1.get('passRate', 'N/A')
                })
            if fw_2:
                table_data.append({
                    'fw_version': fw_version_2,
                    'pass': fw_2.get('pass', 0),
                    'fail': fw_2.get('fail', 0),
                    'total': fw_2.get('total', 0),
                    'passRate': fw_2.get('passRate', 'N/A')
                })
            
            return {
                'answer': handler_message,
                'table': table_data,
                'summary': f"[自動選擇] {project_name} {fw_version_1} vs {fw_version_2}: {trend_icon}",
                'diff': diff,
                'metadata': {
                    'auto_selected': metadata.get('auto_selected', True),
                    'total_versions': metadata.get('total_versions', 0)
                }
            }
        
        # Fallback
        return {
            'answer': "無法生成比較結果。",
            'table': []
        }
    
    def _generate_list_fw_versions_response(self, result_data: Dict,
                                             full_result: Dict) -> Dict[str, Any]:
        """
        生成列出 FW 版本的回答
        
        直接使用 Handler 返回的 message，因為 ListFWVersionsHandler
        已經格式化了完整的版本列表表格。
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer 和 table 的回應
        """
        # 優先使用 Handler 返回的 message
        handler_message = result_data.get('message', '')
        
        if handler_message:
            data = result_data.get('data', {})
            project_name = data.get('project_name', '未知專案')
            fw_versions = data.get('fw_versions', [])
            total_versions = data.get('total_versions', len(fw_versions))
            
            # 生成表格資料（給前端用）
            table_data = []
            for fw in fw_versions:
                table_data.append({
                    'fw_version': fw.get('fw_version', 'N/A'),
                    'completion_rate': fw.get('completion_rate', 0),
                    'pass': fw.get('pass', 0),
                    'fail': fw.get('fail', 0),
                    'samples_used': fw.get('samples_used', 0),
                    'total_samples': fw.get('total_samples', 0)
                })
            
            return {
                'answer': handler_message,
                'table': table_data,
                'summary': f"{project_name} 共有 {total_versions} 個 FW 版本"
            }
        
        # Fallback: 如果沒有 handler_message
        data = result_data.get('data', {})
        project_name = data.get('project_name', '未知專案')
        fw_versions = data.get('fw_versions', [])
        
        if not fw_versions:
            return {
                'answer': f"找不到 {project_name} 的 FW 版本資訊。",
                'table': []
            }
        
        # 簡易格式化
        answer = f"## 📋 {project_name} FW 版本列表\n\n"
        answer += f"共找到 **{len(fw_versions)}** 個版本：\n\n"
        
        for i, fw in enumerate(fw_versions, 1):
            version = fw.get('fw_version', 'N/A')
            completion = fw.get('completion_rate', 0)
            answer += f"{i}. **{version}** - 完成率 {completion:.1f}%\n"
        
        return {
            'answer': answer,
            'table': fw_versions,
            'summary': f"{project_name} 共有 {len(fw_versions)} 個 FW 版本"
        }
    
    def _generate_compare_multiple_fw_response(self, result_data: Dict,
                                                full_result: Dict) -> Dict[str, Any]:
        """
        生成多版本 FW 趨勢比較的回答（Phase 5.4）
        
        直接使用 Handler 返回的 message，因為 CompareMultipleFWHandler
        已經格式化了完整的趨勢比較表格。
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含 answer、table、chart_data 的回應
        """
        # 優先使用 Handler 返回的 message
        handler_message = result_data.get('message', '')
        
        if handler_message:
            data = result_data.get('data', {})
            project_name = data.get('project_name', '未知專案')
            versions_count = data.get('versions_count', 0)
            versions_compared = data.get('versions_compared', [])
            chart_data = data.get('chart_data', {})
            
            # 生成表格資料（給前端用）
            versions_data = data.get('versions_data', [])
            table_data = []
            for v in versions_data:
                table_data.append({
                    'fw_version': v.get('fw_version', 'N/A'),
                    'pass': v.get('pass', 0),
                    'fail': v.get('fail', 0),
                    'pass_rate': v.get('pass_rate', 0),
                    'completion_rate': v.get('completion_rate', 0)
                })
            
            return {
                'answer': handler_message,
                'table': table_data,
                'chart_data': chart_data,
                'summary': f"{project_name} 共比較 {versions_count} 個版本：{', '.join(versions_compared)}"
            }
        
        # Fallback: 如果沒有 handler_message
        data = result_data.get('data', {})
        project_name = data.get('project_name', '未知專案')
        versions_data = data.get('versions_data', [])
        
        if not versions_data:
            return {
                'answer': f"找不到 {project_name} 的多版本比較資料。",
                'table': []
            }
        
        # 簡易格式化
        answer = f"## 📊 {project_name} 多版本趨勢比較\n\n"
        answer += f"共比較 **{len(versions_data)}** 個版本。\n"
        
        return {
            'answer': answer,
            'table': versions_data,
            'summary': f"{project_name} 共比較 {len(versions_data)} 個版本"
        }

    def _generate_count_response(self, result_data: Dict,
                                  full_result: Dict) -> Dict[str, Any]:
        """生成專案數量統計的回答"""
        data = result_data.get('data', {})
        count = data.get('total_count', 0)
        customer = data.get('customer', '全部')
        
        if customer and customer != '全部':
            answer = f"**{customer}** 目前擁有 **{count}** 個專案。"
        else:
            answer = f"目前共有 **{count}** 個專案。"
        
        # 如果有按客戶分組的統計，添加詳情
        by_customer = data.get('by_customer', {})
        if by_customer and customer == '全部':
            answer += "\n\n**按客戶分組統計：**\n\n"
            answer += "| 客戶 | 專案數量 |\n"
            answer += "|------|----------|\n"
            for cust, cnt in by_customer.items():
                answer += f"| {cust} | {cnt} |\n"
        
        answer += f"\n\n如需查看詳細列表，可以詢問「有哪些專案？」或「{customer} 有哪些專案？」"
        
        return {
            'answer': answer,
            'table': [{'customer': k, 'count': v} for k, v in by_customer.items()] if by_customer else [],
            'summary': f"共 {count} 個專案"
        }
    
    def _generate_customers_list_response(self, result_data: Dict,
                                           full_result: Dict) -> Dict[str, Any]:
        """生成客戶列表的回答"""
        data = result_data.get('data', {})
        customers = data.get('customers', [])
        customer_stats = data.get('customer_stats', {})
        count = len(customers)
        
        if count == 0:
            return {
                'answer': "目前沒有任何客戶資料。",
                'table': []
            }
        
        answer = f"目前共有 **{count}** 個客戶：\n\n"
        answer += "| 客戶 | 專案數量 |\n"
        answer += "|------|----------|\n"
        
        for customer in customers:
            project_count = customer_stats.get(customer, 0)
            answer += f"| {customer} | {project_count} |\n"
        
        return {
            'answer': answer,
            'table': [{'customer': c, 'project_count': customer_stats.get(c, 0)} 
                     for c in customers],
            'summary': f"共 {count} 個客戶"
        }
    
    def _generate_controllers_list_response(self, result_data: Dict,
                                             full_result: Dict) -> Dict[str, Any]:
        """生成控制器列表的回答"""
        data = result_data.get('data', {})
        controllers = data.get('controllers', [])
        controller_stats = data.get('controller_stats', {})
        count = len(controllers)
        
        if count == 0:
            return {
                'answer': "目前沒有任何控制器資料。",
                'table': []
            }
        
        answer = f"目前共有 **{count}** 種控制器：\n\n"
        answer += "| 控制器 | 專案數量 |\n"
        answer += "|--------|----------|\n"
        
        for controller in controllers:
            project_count = controller_stats.get(controller, 0)
            answer += f"| {controller} | {project_count} |\n"
        
        return {
            'answer': answer,
            'table': [{'controller': c, 'project_count': controller_stats.get(c, 0)} 
                     for c in controllers],
            'summary': f"共 {count} 種控制器"
        }
    
    def _generate_pls_list_response(self, result_data: Dict,
                                     full_result: Dict) -> Dict[str, Any]:
        """生成專案負責人 (PL) 列表的回答"""
        data = result_data.get('data', {})
        pls = data.get('pls', [])
        pl_stats = data.get('pl_stats', {})
        count = len(pls)
        
        if count == 0:
            return {
                'answer': "目前沒有任何專案負責人資料。",
                'table': []
            }
        
        # 按專案數量排序（降序）
        sorted_pls = sorted(pls, key=lambda x: pl_stats.get(x, 0), reverse=True)
        
        # 取第一名用於提示
        top_pl = sorted_pls[0] if sorted_pls else 'Ryder'
        
        answer = f"目前共有 **{count}** 位專案負責人 (PL)：\n\n"
        answer += "| 專案負責人 | 專案數量 |\n"
        answer += "|------------|----------|\n"
        
        # 按專案數量排序顯示
        for pl in sorted_pls:
            project_count = pl_stats.get(pl, 0)
            answer += f"| {pl} | {project_count} |\n"
        
        answer += f"\n\n如需查看特定 PL 負責的專案，可以詢問「{top_pl} 負責哪些專案？」"
        
        return {
            'answer': answer,
            'table': [{'pl': p, 'project_count': pl_stats.get(p, 0)} 
                     for p in sorted_pls],
            'summary': f"共 {count} 位專案負責人"
        }
    
    def _generate_unknown_response(self, result_data: Dict,
                                    full_result: Dict) -> Dict[str, Any]:
        """生成未知意圖的回答"""
        data = result_data.get('data', {})
        help_text = data.get('help', '')
        
        answer = "抱歉，我無法理解您的問題。\n\n"
        
        if help_text:
            answer += help_text
        else:
            answer += self._get_help_message()
        
        return {
            'answer': answer,
            'table': [],
            'summary': "無法識別查詢意圖"
        }
    
    def _generate_error_response(self, result_data: Dict) -> Dict[str, Any]:
        """生成錯誤回答"""
        error = result_data.get('error', '未知錯誤')
        
        answer = f"❌ **查詢失敗**\n\n錯誤訊息：{error}\n\n"
        answer += "請稍後再試，或聯繫系統管理員。"
        
        return {
            'answer': answer,
            'table': [],
            'summary': f"錯誤: {error}"
        }
    
    def _generate_no_results_response(self, intent_type: str, 
                                       result_data: Dict) -> Dict[str, Any]:
        """生成無結果回答"""
        message = result_data.get('message', '找不到符合條件的資料')
        parameters = result_data.get('parameters', {})
        
        answer = f"📭 {message}\n\n"
        
        if parameters:
            answer += "**查詢條件：**\n"
            for key, value in parameters.items():
                answer += f"- {key}: {value}\n"
        
        answer += f"\n{self._get_help_message()}"
        
        return {
            'answer': answer,
            'table': [],
            'summary': message
        }
    
    # ============================================================
    # Phase 9: Sub Version 查詢回應生成方法
    # ============================================================
    
    def _generate_sub_versions_response(self, result_data: Dict,
                                         full_result: Dict) -> Dict[str, Any]:
        """
        生成 Sub Version 列表回答
        
        直接使用 Handler 回傳的 message（已經是完整格式化的 Markdown）
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含格式化回答
        """
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        
        # Handler 已經生成完整的 Markdown 格式回答，直接使用
        return {
            'answer': message,
            'table': data.get('sub_versions', []),
            'summary': f"列出 {data.get('project_name', '')} 的 {data.get('total_sub_versions', 0)} 個 Sub Version"
        }
    
    def _generate_fw_by_sub_version_response(self, result_data: Dict,
                                              full_result: Dict) -> Dict[str, Any]:
        """
        生成特定 Sub Version 的 FW 版本列表回答
        
        直接使用 Handler 回傳的 message（已經是完整格式化的 Markdown）
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含格式化回答
        """
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        
        # Handler 已經生成完整的 Markdown 格式回答，直接使用
        return {
            'answer': message,
            'table': data.get('fw_versions', []),
            'summary': f"列出 {data.get('project_name', '')} {data.get('sub_version', '')} 的 {data.get('displayed_versions', 0)} 個 FW 版本"
        }
    
    def _generate_fw_by_date_range_response(self, result_data: Dict,
                                             full_result: Dict) -> Dict[str, Any]:
        """
        生成按日期範圍查詢 FW 版本的回答
        
        直接使用 Handler 回傳的 message（已經是完整格式化的 Markdown）
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含格式化回答
        """
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        date_range = data.get('date_range', {})
        
        # Handler 已經生成完整的 Markdown 格式回答，直接使用
        return {
            'answer': message,
            'table': data.get('fw_versions', []),
            'summary': f"列出 {data.get('project_name', '')} 在 {date_range.get('description', '')} 的 {data.get('total_in_range', 0)} 個 FW 版本"
        }
    
    def _generate_test_jobs_response(self, result_data: Dict,
                                      full_result: Dict) -> Dict[str, Any]:
        """
        生成測試工作結果回答（Phase 16）
        
        test_jobs_handler 已經生成完整的 Markdown 格式回答（含 HTML details 摺疊區塊），
        此方法直接使用 handler 的 message，不做額外處理。
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含格式化回答
        """
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        
        project_name = data.get('project_name', '')
        fw_version = data.get('fw_version', '')
        pass_count = data.get('pass_count', 0)
        fail_count = data.get('fail_count', 0)
        total = data.get('total', 0)
        
        # Handler 已經生成完整的 Markdown 格式回答，直接使用
        return {
            'answer': message,
            'table': data.get('table', []),
            'summary': f"{project_name} FW {fw_version} 測試結果：{pass_count} Pass / {fail_count} Fail（共 {total} 項）"
        }
    
    def _generate_compare_test_jobs_response(self, result_data: Dict,
                                              full_result: Dict) -> Dict[str, Any]:
        """
        生成比較測試項目結果回答（Phase 18 更新：支援多版本比較）
        
        compare_test_jobs_handler 已經生成完整的 Markdown 格式回答（含 HTML details 摺疊區塊），
        此方法直接使用 handler 的 message，不做額外處理。
        
        Args:
            result_data: 查詢結果資料
            full_result: 完整查詢結果
            
        Returns:
            Dict: 包含格式化回答
        """
        message = result_data.get('message', '')
        data = result_data.get('data', {})
        
        project_name = data.get('project_name', '')
        statistics = data.get('statistics', {})
        
        # Phase 18：支援多版本陣列，同時向後相容舊格式
        fw_versions = data.get('fw_versions', [])
        if not fw_versions:
            # 向後相容：從 fw_version_1/fw_version_2 構建
            fw_v1 = data.get('fw_version_1', '')
            fw_v2 = data.get('fw_version_2', '')
            if fw_v1 and fw_v2:
                fw_versions = [fw_v1, fw_v2]
        
        # 構建摘要
        total_diff = statistics.get('total_differences', 0)
        pass_to_fail = statistics.get('pass_to_fail_count', 0)
        fail_to_pass = statistics.get('fail_to_pass_count', 0)
        
        # 動態生成版本列表字串
        if len(fw_versions) == 2:
            version_str = f"{fw_versions[0]} vs {fw_versions[1]}"
        elif len(fw_versions) > 2:
            version_str = f"{fw_versions[0]} 等 {len(fw_versions)} 個版本"
        else:
            version_str = ', '.join(fw_versions) if fw_versions else '未知版本'
        
        summary = f"{project_name} FW {version_str}：共 {total_diff} 項差異"
        if pass_to_fail > 0:
            summary += f"（⚠️ {pass_to_fail} 項退化）"
        if fail_to_pass > 0:
            summary += f"（✅ {fail_to_pass} 項改善）"
        
        # Handler 已經生成完整的 Markdown 格式回答，直接使用
        return {
            'answer': message,
            'table': data.get('comparison', {}),
            'summary': summary
        }
    
    def _generate_default_response(self, result_data: Dict,
                                    full_result: Dict) -> Dict[str, Any]:
        """生成預設回答"""
        data = result_data.get('data', [])
        message = result_data.get('message', '查詢完成')
        
        answer = f"{message}\n\n"
        
        if isinstance(data, list) and len(data) > 0:
            answer += self._generate_projects_table(data)
        elif isinstance(data, dict):
            answer += self._generate_detail_table(data)
        
        return {
            'answer': answer,
            'table': data if isinstance(data, list) else [data],
            'summary': message
        }
    
    def _generate_projects_table(self, projects: List[Dict]) -> str:
        """
        生成專案列表的 Markdown Table
        
        Args:
            projects: 專案列表
            
        Returns:
            str: Markdown Table
        """
        if not projects:
            return "（無資料）\n"
        
        table = "| 專案名稱 | 客戶 | 控制器 | NAND 類型 | 負責人 |\n"
        table += "|----------|------|--------|-----------|--------|\n"
        
        for project in projects:
            name = project.get('projectName', '-')
            customer = project.get('customer', '-')
            controller = project.get('controller', '-')
            nand = project.get('nand', '-')
            pl = project.get('pl', '-')
            
            table += f"| {name} | {customer} | {controller} | {nand} | {pl} |\n"
        
        return table
    
    def _generate_detail_table(self, detail: Dict) -> str:
        """
        生成專案詳情的 Markdown Table
        
        Args:
            detail: 專案詳情
            
        Returns:
            str: Markdown Table
        """
        if not detail:
            return "（無資料）\n"
        
        field_names = {
            'projectName': '專案名稱',
            'customer': '客戶',
            'controller': '控制器',
            'nand': 'NAND 類型',
            'pl': '負責人',
            'status': '狀態',
            'createDate': '建立日期',
            'updateDate': '更新日期',
            'description': '描述',
            'testCount': '測試數量',
            'passRate': '通過率',
        }
        
        # 先收集有值的欄位
        rows = []
        for key, display_name in field_names.items():
            value = detail.get(key, '')
            if value:
                rows.append(f"| {display_name} | {value} |")
        
        # 如果沒有任何有值的欄位，不生成表格（返回空字串）
        if not rows:
            return ""
        
        table = "| 項目 | 內容 |\n"
        table += "|------|------|\n"
        table += "\n".join(rows) + "\n"
        
        return table
    
    def _generate_summary_table(self, summary: Dict) -> str:
        """
        生成測試摘要的 Markdown Table
        
        Args:
            summary: 測試摘要
            
        Returns:
            str: Markdown Table
        """
        if not summary:
            return "（無資料）\n"
        
        field_names = {
            'projectName': '專案名稱',
            'customer': '客戶',
            'controller': '控制器',
            'totalTests': '測試總數',
            'passedTests': '通過數',
            'failedTests': '失敗數',
            'passRate': '通過率',
            'lastTestDate': '最後測試日期',
            'lastUpdate': '最後更新',
            'status': '狀態',
            'note': '備註',
        }
        
        # 先收集有值的欄位
        rows = []
        for key, display_name in field_names.items():
            value = summary.get(key, '')
            if value or value == 0:
                rows.append(f"| {display_name} | {value} |")
        
        # 如果沒有任何有值的欄位，不生成表格
        if not rows:
            return "（無摘要資料）\n"
        
        table = "| 項目 | 內容 |\n"
        table += "|------|------|\n"
        table += "\n".join(rows) + "\n"
        
        return table
    
    # =========================================================================
    # Phase 15: Known Issues 回應生成器
    # =========================================================================
    
    def _generate_known_issues_response(self, result_data: Dict,
                                         full_result: Dict) -> Dict[str, Any]:
        """
        生成 Known Issues 查詢的回答
        
        適用於所有 Known Issues 列表型查詢
        """
        data = result_data.get('data', [])
        message = result_data.get('message', '')
        parameters = result_data.get('parameters', {})
        
        if not data:
            return {
                'answer': message or '找不到符合條件的 Known Issues',
                'table': []
            }
        
        # 生成自然語言回答
        answer = f"{message}\n\n"
        answer += self._generate_known_issues_table(data)
        
        return {
            'answer': answer,
            'table': data,
            'summary': message
        }
    
    def _generate_known_issues_rank_response(self, result_data: Dict,
                                              full_result: Dict) -> Dict[str, Any]:
        """
        生成 Known Issues 專案排名的回答
        """
        data = result_data.get('data', [])
        message = result_data.get('message', '')
        
        if not data:
            return {
                'answer': message or '找不到 Known Issues 資料',
                'table': []
            }
        
        # 生成排名表格
        answer = f"{message}\n\n"
        answer += "| 排名 | 專案名稱 | Issues 數量 | 有 JIRA | 啟用中 |\n"
        answer += "|------|----------|-------------|---------|--------|\n"
        
        for idx, item in enumerate(data, 1):
            project_name = item.get('project_name', '-')
            issue_count = item.get('issue_count', 0)
            with_jira = item.get('with_jira_count', 0)
            enabled = item.get('enabled_count', 0)
            
            answer += f"| {idx} | {project_name} | {issue_count} | {with_jira} | {enabled} |\n"
        
        return {
            'answer': answer,
            'table': data,
            'summary': message
        }
    
    def _generate_known_issues_creators_response(self, result_data: Dict,
                                                  full_result: Dict) -> Dict[str, Any]:
        """
        生成 Known Issues 建立者列表的回答
        """
        data = result_data.get('data', [])
        message = result_data.get('message', '')
        
        if not data:
            return {
                'answer': message or '找不到 Known Issues 建立者資料',
                'table': []
            }
        
        # 生成建立者表格
        answer = f"{message}\n\n"
        answer += "| 建立者 | Issues 數量 |\n"
        answer += "|--------|-------------|\n"
        
        for item in data:
            creator = item.get('creator', '-')
            count = item.get('issue_count', item.get('count', 0))
            answer += f"| {creator} | {count} |\n"
        
        return {
            'answer': answer,
            'table': data,
            'summary': message
        }
    
    def _generate_known_issues_table(self, issues: List[Dict]) -> str:
        """
        生成 Known Issues 的 Markdown Table（按 Test Item 分組）
        
        Args:
            issues: Known Issues 列表
            
        Returns:
            str: Markdown Table（分組顯示）
        """
        if not issues:
            return "（無資料）\n"
        
        # 按 test_item_name 分組
        from collections import defaultdict
        grouped = defaultdict(list)
        for issue in issues:
            test_item = issue.get('test_item_name', '其他')
            grouped[test_item].append(issue)
        
        # 按每組數量排序（多的排前面）
        sorted_groups = sorted(grouped.items(), key=lambda x: len(x[1]), reverse=True)
        
        result = ""
        for test_item, group_issues in sorted_groups:
            # 每個分組加上標題
            result += f"\n**📋 {test_item}** ({len(group_issues)} 筆)\n\n"
            result += "| Issue ID | Case Name | JIRA | 建立者 |\n"
            result += "|----------|-----------|------|--------|\n"
            
            for issue in group_issues:
                issue_id = issue.get('issue_id', '-')
                case_name = issue.get('case_name', '-')
                jira_id = issue.get('jira_id', '-')
                created_by = issue.get('created_by', '-')
                
                # 如果有 JIRA 連結，生成超連結
                if issue.get('jira_link'):
                    jira_display = f"[{jira_id}]({issue.get('jira_link')})"
                else:
                    jira_display = jira_id or '-'
                
                # 截斷過長的 case_name
                if len(case_name) > 50:
                    case_name = case_name[:47] + '...'
                
                result += f"| {issue_id} | {case_name} | {jira_display} | {created_by} |\n"
        
        return result
    
    def _get_help_message(self) -> str:
        """獲取幫助訊息"""
        return """
**我可以幫您查詢以下資訊：**
- 某客戶的專案列表（如：「WD 有哪些專案？」）
- 某控制器的專案（如：「SM2264 用在哪些專案？」）
- 專案詳細資訊（如：「DEMETER 專案的詳細資訊」）
- 專案測試結果（如：「DEMETER 的測試結果」）
- 專案數量統計（如：「WD 有幾個專案？」）
- 客戶列表（如：「有哪些客戶？」）
- 控制器列表（如：「有哪些控制器？」）
- **🆕 Known Issues 查詢**
  - 「Springsteen 專案有多少 Known Issues？」
  - 「哪些專案的 Known Issues 最多？」
  - 「有哪些人建立過 Known Issues？」
  - 「搜尋 Known Issues 關鍵字 PCIe」
""".strip()


# 便利函數
def generate_response(query_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    生成回答的便利函數
    
    Args:
        query_result: 查詢結果
        
    Returns:
        Dict: 包含 answer 和 table 的回答
    """
    generator = SAFResponseGenerator()
    return generator.generate(query_result)
