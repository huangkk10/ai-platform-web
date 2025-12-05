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
