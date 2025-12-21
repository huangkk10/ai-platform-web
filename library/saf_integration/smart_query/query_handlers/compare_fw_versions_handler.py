"""
CompareFWVersionsHandler - 比較兩個 FW 版本測試結果
====================================================

處理 Phase 5.1 FW 版本比較意圖：
- compare_fw_versions: 比較同一專案中兩個指定 FW 版本的測試結果

功能：
- 調用 Phase 4 的 FW 版本查詢獲取兩個版本的測試數據
- 調用 Phase 6.2 的 firmware-summary API 獲取整體指標（完成率、樣本等）
- 計算 Pass/Fail/PassRate 差異
- 分析趨勢（改善/退步/持平）

作者：AI Platform Team
創建日期：2025-12-07
更新日期：2025-12-07（整合 firmware-summary 整體指標）
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
            
            # Step 3: 獲取 firmware-summary 整體指標（完成率、樣本等）
            firmware_stats_1 = self._get_firmware_stats(result_1.metadata.get('project_uid'))
            firmware_stats_2 = self._get_firmware_stats(result_2.metadata.get('project_uid'))
            
            # Step 4: 計算比較結果
            comparison = self._calculate_comparison(
                result_1.data,
                result_2.data,
                firmware_stats_1,
                firmware_stats_2
            )
            
            # Step 5: 格式化並返回結果
            return self._format_comparison_response(
                comparison=comparison,
                fw_data_1=result_1.data,
                fw_data_2=result_2.data,
                firmware_stats_1=firmware_stats_1,
                firmware_stats_2=firmware_stats_2,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 版本比較錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _get_firmware_stats(self, project_uid: str) -> Optional[Dict[str, Any]]:
        """
        獲取 firmware-summary 整體指標
        
        Args:
            project_uid: 專案 UID
            
        Returns:
            整體指標字典，獲取失敗返回 None
        """
        if not project_uid:
            return None
        
        try:
            stats = self.api_client.get_firmware_summary(project_uid)
            if stats:
                overview = stats.get('overview', {})
                sample_stats = stats.get('sample_stats', {})
                test_item_stats = stats.get('test_item_stats', {})
                
                return {
                    'completion_rate': overview.get('completion_rate', 0),
                    'pass_rate': overview.get('pass_rate', 0),
                    'total_samples': sample_stats.get('total_samples', 0),
                    'samples_used': sample_stats.get('samples_used', 0),
                    'utilization_rate': sample_stats.get('utilization_rate', 0),
                    'execution_rate': test_item_stats.get('execution_rate', 0),
                    'fail_rate': test_item_stats.get('fail_rate', 0)
                }
        except Exception as e:
            logger.warning(f"獲取 firmware-summary 失敗 (uid={project_uid}): {str(e)}")
        
        return None
    
    def _calculate_comparison(
        self,
        data_1: Dict[str, Any],
        data_2: Dict[str, Any],
        firmware_stats_1: Optional[Dict[str, Any]] = None,
        firmware_stats_2: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        計算兩個 FW 版本的比較結果
        
        Args:
            data_1: 第一個 FW 版本的測試數據
            data_2: 第二個 FW 版本的測試數據
            firmware_stats_1: 第一個 FW 版本的整體指標（可選）
            firmware_stats_2: 第二個 FW 版本的整體指標（可選）
            
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
        
        result = {
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
        
        # 添加整體指標比較（如果有）
        if firmware_stats_1 or firmware_stats_2:
            stats_1 = firmware_stats_1 or {}
            stats_2 = firmware_stats_2 or {}
            
            result['overall_metrics'] = {
                'fw_1': {
                    'completion_rate': stats_1.get('completion_rate', 0),
                    'pass_rate': stats_1.get('pass_rate', 0),
                    'total_samples': stats_1.get('total_samples', 0),
                    'samples_used': stats_1.get('samples_used', 0),
                    'utilization_rate': stats_1.get('utilization_rate', 0),
                    'execution_rate': stats_1.get('execution_rate', 0),
                    'fail_rate': stats_1.get('fail_rate', 0)
                },
                'fw_2': {
                    'completion_rate': stats_2.get('completion_rate', 0),
                    'pass_rate': stats_2.get('pass_rate', 0),
                    'total_samples': stats_2.get('total_samples', 0),
                    'samples_used': stats_2.get('samples_used', 0),
                    'utilization_rate': stats_2.get('utilization_rate', 0),
                    'execution_rate': stats_2.get('execution_rate', 0),
                    'fail_rate': stats_2.get('fail_rate', 0)
                },
                'diff': {
                    'completion_rate_change': stats_1.get('completion_rate', 0) - stats_2.get('completion_rate', 0),
                    'execution_rate_change': stats_1.get('execution_rate', 0) - stats_2.get('execution_rate', 0),
                    'fail_rate_change': stats_1.get('fail_rate', 0) - stats_2.get('fail_rate', 0),
                    'samples_used_change': stats_1.get('samples_used', 0) - stats_2.get('samples_used', 0)
                }
            }
        
        return result
    
    def _format_comparison_response(
        self,
        comparison: Dict[str, Any],
        fw_data_1: Dict[str, Any],
        fw_data_2: Dict[str, Any],
        firmware_stats_1: Optional[Dict[str, Any]],
        firmware_stats_2: Optional[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化比較結果回應
        
        Args:
            comparison: 比較計算結果
            fw_data_1: 第一個 FW 版本的完整數據
            fw_data_2: 第二個 FW 版本的完整數據
            firmware_stats_1: 第一個 FW 版本的整體指標
            firmware_stats_2: 第二個 FW 版本的整體指標
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
        
        # 添加整體指標數據
        if 'overall_metrics' in comparison:
            formatted_data['overall_metrics'] = comparison['overall_metrics']
        
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
        
        def format_percent_change(val):
            if val > 0:
                return f"+{val:.1f}% ⬆️"
            elif val < 0:
                return f"{val:.1f}% ⬇️"
            return "0.0% ➡️"
        
        # 構建友好的訊息
        message_parts = [
            f"📊 {project_name} 專案 FW 版本比較",
            f"版本對比：{fw_version_1} vs {fw_version_2}",
            "",
            "### 測試結果比較",
            f"| 指標 | {fw_version_1} | {fw_version_2} | 變化 |",
            "|------|--------|--------|------|",
            f"| Pass | {summary_1['pass']} | {summary_2['pass']} | {format_change(comparison['pass_change'])} |",
            f"| Fail | {summary_1['fail']} | {summary_2['fail']} | {format_change(comparison['fail_change'])} |",
            f"| 通過率 | {summary_1['pass_rate']:.1f}% | {summary_2['pass_rate']:.1f}% | {comparison['pass_rate_change_formatted']} |",
        ]
        
        # 添加整體指標比較（如果有）
        if 'overall_metrics' in comparison:
            metrics = comparison['overall_metrics']
            m1 = metrics['fw_1']
            m2 = metrics['fw_2']
            diff = metrics['diff']
            
            message_parts.extend([
                "",
                "### 📈 整體指標比較",
                f"| 指標 | {fw_version_1} | {fw_version_2} | 變化 |",
                "|------|--------|--------|------|",
                f"| 完成率 | {m1['completion_rate']:.1f}% | {m2['completion_rate']:.1f}% | {format_percent_change(diff['completion_rate_change'])} |",
                f"| 執行率 | {m1['execution_rate']:.1f}% | {m2['execution_rate']:.1f}% | {format_percent_change(diff['execution_rate_change'])} |",
                f"| 失敗率 | {m1['fail_rate']:.1f}% | {m2['fail_rate']:.1f}% | {format_percent_change(diff['fail_rate_change'])} |",
                f"| 樣本使用 | {m1['samples_used']}/{m1['total_samples']} | {m2['samples_used']}/{m2['total_samples']} | {format_change(diff['samples_used_change'])} |",
            ])
        
        # 添加按測試類別比較
        categories_1 = fw_data_1.get('categories', [])
        categories_2 = fw_data_2.get('categories', [])
        
        if categories_1 or categories_2:
            # 建立類別名稱到數據的映射
            cat_map_1 = {cat['name']: cat for cat in categories_1}
            cat_map_2 = {cat['name']: cat for cat in categories_2}
            
            # 合併所有類別名稱
            all_categories = sorted(set(cat_map_1.keys()) | set(cat_map_2.keys()))
            
            # 過濾只顯示有測試結果的類別
            active_categories = [
                cat for cat in all_categories
                if (cat_map_1.get(cat, {}).get('total', 0) > 0 or 
                    cat_map_2.get(cat, {}).get('total', 0) > 0)
            ]
            
            if active_categories:
                message_parts.extend([
                    "",
                    "### 📁 按測試類別比較",
                    f"| 類別 | {fw_version_1} (Pass/Fail) | {fw_version_2} (Pass/Fail) | Pass 變化 | Fail 變化 |",
                    "|------|--------|--------|--------|--------|",
                ])
                
                for cat_name in active_categories:
                    cat_1 = cat_map_1.get(cat_name, {'pass': 0, 'fail': 0, 'total': 0})
                    cat_2 = cat_map_2.get(cat_name, {'pass': 0, 'fail': 0, 'total': 0})
                    
                    pass_change = cat_1.get('pass', 0) - cat_2.get('pass', 0)
                    fail_change = cat_1.get('fail', 0) - cat_2.get('fail', 0)
                    
                    # 格式化顯示
                    fw1_display = f"{cat_1.get('pass', 0)}/{cat_1.get('fail', 0)}"
                    fw2_display = f"{cat_2.get('pass', 0)}/{cat_2.get('fail', 0)}"
                    
                    message_parts.append(
                        f"| {cat_name} | {fw1_display} | {fw2_display} | {format_change(pass_change)} | {format_change(fail_change)} |"
                    )
                
                # 生成測試類別雷達圖（永遠顯示）
                radar_chart = self._generate_category_radar_chart(
                    fw_version_1=fw_version_1,
                    fw_version_2=fw_version_2,
                    cat_map_1=cat_map_1,
                    cat_map_2=cat_map_2,
                    active_categories=active_categories
                )
                if radar_chart:
                    message_parts.extend(["", radar_chart])
        
        # 趨勢分析
        message_parts.extend([
            "",
            f"### 📊 趨勢分析",
            f"{trend_desc}：{fw_version_1} 相較於 {fw_version_2} 表現{'更好' if comparison['trend'] == 'improved' else '較差' if comparison['trend'] == 'declined' else '相當'}"
        ])
        
        message = "\n".join(message_parts)
        
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
                'trend': comparison['trend'],
                'has_overall_metrics': 'overall_metrics' in comparison
            }
        )
        
        self._log_result(result)
        return result

    def _generate_category_radar_chart(
        self,
        fw_version_1: str,
        fw_version_2: str,
        cat_map_1: Dict[str, Any],
        cat_map_2: Dict[str, Any],
        active_categories: List[str]
    ) -> Optional[str]:
        """
        生成測試類別雷達圖
        
        Args:
            fw_version_1: 第一個 FW 版本名稱
            fw_version_2: 第二個 FW 版本名稱
            cat_map_1: 第一個版本的類別數據映射
            cat_map_2: 第二個版本的類別數據映射
            active_categories: 有效的類別名稱列表
            
        Returns:
            雷達圖的 Markdown 標記，失敗返回 None
        """
        try:
            from library.common.chart_formatter import ChartFormatter
            
            # 檢查是否有足夠的類別（雷達圖至少需要 3 個維度）
            if len(active_categories) < 3:
                logger.debug(f"類別數量不足 ({len(active_categories)} < 3)，跳過雷達圖生成")
                return None
            
            # 準備雷達圖數據
            fw_versions = [
                {
                    'name': fw_version_1,
                    'pass_counts': [
                        cat_map_1.get(cat, {}).get('pass', 0) 
                        for cat in active_categories
                    ]
                },
                {
                    'name': fw_version_2,
                    'pass_counts': [
                        cat_map_2.get(cat, {}).get('pass', 0) 
                        for cat in active_categories
                    ]
                }
            ]
            
            # 生成雷達圖
            radar_chart = ChartFormatter.fw_category_comparison_radar(
                title="🕸️ 測試類別分佈對比",
                categories=active_categories,
                fw_versions=fw_versions
            )
            
            return radar_chart
            
        except Exception as e:
            logger.warning(f"生成測試類別雷達圖失敗: {str(e)}")
            return None
