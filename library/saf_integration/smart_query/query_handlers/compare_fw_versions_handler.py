"""
CompareFWVersionsHandler - 比較兩個 FW 版本測試結果
====================================================

處理 Phase 5.1 FW 版本比較意圖：
- compare_fw_versions: 比較同一專案中兩個指定 FW 版本的測試結果

功能：
- 調用 Phase 4 的 FW 版本查詢獲取兩個版本的測試數據
- 計算 Pass/Fail/PassRate 差異
- 分析趨勢（改善/退步/持平）

作者：AI Platform Team
創建日期：2025-12-07
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult
from .test_summary_by_fw_handler import TestSummaryByFWHandler

logger = logging.getLogger(__name__)


class CompareFWVersionsHandler(BaseHandler):
    """
    比較兩個 FW 版本測試結果處理器
    
    處理比較兩個指定 FW 版本的測試結果請求。
    
    支援的意圖：
    - compare_fw_versions: 比較兩個指定的 FW 版本
    
    功能：
    1. 獲取兩個 FW 版本的測試數據（複用 Phase 4 邏輯）
    2. 計算差異（pass_change, fail_change, passRate_change）
    3. 分析趨勢（improved, declined, stable）
    """
    
    handler_name = "compare_fw_versions_handler"
    supported_intent = "compare_fw_versions"
    
    def __init__(self):
        """初始化 Handler"""
        super().__init__()
        # 複用 Phase 4 的 Handler 來獲取 FW 版本測試數據
        self.fw_handler = TestSummaryByFWHandler()
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 FW 版本比較
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "fw_version_1": "Y1114B",
                "fw_version_2": "Y1114A"
            }
            
        Returns:
            QueryResult: 包含比較結果
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name', 'fw_version_1', 'fw_version_2']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        fw_version_1 = parameters.get('fw_version_1')
        fw_version_2 = parameters.get('fw_version_2')
        
        # 檢查是否比較相同版本
        if fw_version_1.lower() == fw_version_2.lower():
            return QueryResult.error(
                f"無法比較相同的 FW 版本：{fw_version_1}",
                self.handler_name,
                parameters
            )
        
        try:
            # Step 1: 獲取第一個 FW 版本的測試數據
            result_1 = self.fw_handler.execute({
                'project_name': project_name,
                'fw_version': fw_version_1
            })
            
            if not result_1.is_success():
                return QueryResult.error(
                    f"無法獲取 FW 版本 '{fw_version_1}' 的測試數據：{result_1.message}",
                    self.handler_name,
                    parameters
                )
            
            # Step 2: 獲取第二個 FW 版本的測試數據
            result_2 = self.fw_handler.execute({
                'project_name': project_name,
                'fw_version': fw_version_2
            })
            
            if not result_2.is_success():
                return QueryResult.error(
                    f"無法獲取 FW 版本 '{fw_version_2}' 的測試數據：{result_2.message}",
                    self.handler_name,
                    parameters
                )
            
            # Step 3: 計算比較結果
            comparison = self._calculate_comparison(
                result_1.data,
                result_2.data
            )
            
            # Step 4: 格式化並返回結果
            return self._format_comparison_response(
                comparison=comparison,
                fw_data_1=result_1.data,
                fw_data_2=result_2.data,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 版本比較錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _calculate_comparison(
        self,
        data_1: Dict[str, Any],
        data_2: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        計算兩個 FW 版本的比較結果
        
        Args:
            data_1: 第一個 FW 版本的測試數據
            data_2: 第二個 FW 版本的測試數據
            
        Returns:
            比較結果字典
        """
        summary_1 = data_1.get('summary', {})
        summary_2 = data_2.get('summary', {})
        
        pass_1 = summary_1.get('pass', 0)
        fail_1 = summary_1.get('fail', 0)
        pass_2 = summary_2.get('pass', 0)
        fail_2 = summary_2.get('fail', 0)
        
        # 計算通過率
        total_1 = pass_1 + fail_1
        total_2 = pass_2 + fail_2
        pass_rate_1 = (pass_1 / total_1 * 100) if total_1 > 0 else 0
        pass_rate_2 = (pass_2 / total_2 * 100) if total_2 > 0 else 0
        
        # 計算變化（第一個版本相對於第二個版本）
        pass_change = pass_1 - pass_2
        fail_change = fail_1 - fail_2
        pass_rate_change = pass_rate_1 - pass_rate_2
        
        # 判斷趨勢
        # 邏輯：pass 增加或 fail 減少視為改善
        if pass_rate_change > 1:  # 通過率提升超過 1%
            trend = 'improved'
        elif pass_rate_change < -1:  # 通過率下降超過 1%
            trend = 'declined'
        else:
            trend = 'stable'
        
        return {
            'pass_change': pass_change,
            'fail_change': fail_change,
            'pass_rate_change': pass_rate_change,
            'pass_rate_change_formatted': f"{pass_rate_change:+.1f}%",
            'trend': trend,
            'summary': {
                'fw_1': {
                    'pass': pass_1,
                    'fail': fail_1,
                    'total': total_1,
                    'pass_rate': pass_rate_1
                },
                'fw_2': {
                    'pass': pass_2,
                    'fail': fail_2,
                    'total': total_2,
                    'pass_rate': pass_rate_2
                }
            }
        }
    
    def _format_comparison_response(
        self,
        comparison: Dict[str, Any],
        fw_data_1: Dict[str, Any],
        fw_data_2: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化比較結果回應
        
        Args:
            comparison: 比較計算結果
            fw_data_1: 第一個 FW 版本的完整數據
            fw_data_2: 第二個 FW 版本的完整數據
            parameters: 原始查詢參數
            
        Returns:
            QueryResult: 格式化的結果
        """
        project_name = parameters.get('project_name')
        fw_version_1 = fw_data_1.get('fwVersion', parameters.get('fw_version_1'))
        fw_version_2 = fw_data_2.get('fwVersion', parameters.get('fw_version_2'))
        
        summary_1 = comparison['summary']['fw_1']
        summary_2 = comparison['summary']['fw_2']
        
        # 構建格式化的數據
        formatted_data = {
            'projectName': project_name,
            'comparison_type': 'two_versions',
            'fw_1': {
                'version': fw_version_1,
                'pass': summary_1['pass'],
                'fail': summary_1['fail'],
                'total': summary_1['total'],
                'passRate': f"{summary_1['pass_rate']:.1f}%",
                'categories': fw_data_1.get('categories', []),
                'capacities': fw_data_1.get('capacities', [])
            },
            'fw_2': {
                'version': fw_version_2,
                'pass': summary_2['pass'],
                'fail': summary_2['fail'],
                'total': summary_2['total'],
                'passRate': f"{summary_2['pass_rate']:.1f}%",
                'categories': fw_data_2.get('categories', []),
                'capacities': fw_data_2.get('capacities', [])
            },
            'diff': {
                'pass_change': comparison['pass_change'],
                'fail_change': comparison['fail_change'],
                'passRate_change': comparison['pass_rate_change_formatted'],
                'trend': comparison['trend']
            }
        }
        
        # 生成趨勢描述
        trend_desc = {
            'improved': '📈 改善',
            'declined': '📉 退步',
            'stable': '➡️ 持平'
        }.get(comparison['trend'], '➡️ 持平')
        
        # 生成變化描述
        def format_change(val):
            if val > 0:
                return f"+{val} ⬆️"
            elif val < 0:
                return f"{val} ⬇️"
            return "0 ➡️"
        
        # 構建友好的訊息
        message = (
            f"📊 {project_name} 專案 FW 版本比較\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 {fw_version_1}：Pass {summary_1['pass']} | Fail {summary_1['fail']} | 通過率 {summary_1['pass_rate']:.1f}%\n"
            f"🔹 {fw_version_2}：Pass {summary_2['pass']} | Fail {summary_2['fail']} | 通過率 {summary_2['pass_rate']:.1f}%\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"📈 變化：Pass {format_change(comparison['pass_change'])} | "
            f"Fail {format_change(comparison['fail_change'])} | "
            f"通過率 {comparison['pass_rate_change_formatted']}\n"
            f"📊 趨勢：{trend_desc}"
        )
        
        result = QueryResult.success(
            data=formatted_data,
            count=2,  # 比較兩個版本
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'fw_version_1': fw_version_1,
                'fw_version_2': fw_version_2,
                'pass_change': comparison['pass_change'],
                'fail_change': comparison['fail_change'],
                'pass_rate_change': comparison['pass_rate_change'],
                'trend': comparison['trend']
            }
        )
        
        self._log_result(result)
        return result
