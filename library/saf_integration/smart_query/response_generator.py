"""
SAF 回答生成器
==============

根據查詢結果生成自然語言回答，包含 Markdown Table 格式。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any, List, Optional

from .intent_types import IntentType
from .query_handlers import QueryResult, QueryStatus

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
            # Phase 5: FW 版本比較回應生成器
            IntentType.COMPARE_FW_VERSIONS: self._generate_compare_fw_versions_response,
            IntentType.COUNT_PROJECTS: self._generate_count_response,
            IntentType.LIST_ALL_CUSTOMERS: self._generate_customers_list_response,
            IntentType.LIST_ALL_CONTROLLERS: self._generate_controllers_list_response,
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
        
        return {
            'answer': answer,
            'table': [data],
            'summary': f"{project_name} FW {fw_version}：{total_pass} Pass, {total_fail} Fail ({pass_rate})"
        }
    
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
        
        table = "| 項目 | 內容 |\n"
        table += "|------|------|\n"
        
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
        
        for key, display_name in field_names.items():
            value = detail.get(key, '')
            if value:
                table += f"| {display_name} | {value} |\n"
        
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
        
        table = "| 項目 | 內容 |\n"
        table += "|------|------|\n"
        
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
        
        for key, display_name in field_names.items():
            value = summary.get(key, '')
            if value or value == 0:
                table += f"| {display_name} | {value} |\n"
        
        return table
    
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
