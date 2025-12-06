"""
FWDetailSummaryHandler - 查詢 FW 詳細統計
=========================================

處理 Phase 6.2 FW 詳細統計意圖：
- query_fw_detail_summary: 查詢特定 FW 版本的整體統計指標

API 端點：GET /api/v1/projects/{project_uid}/firmware-summary

提供資訊：
- overview: 總測試項目、Pass/Fail、完成率、通過率
- sample_stats: 樣本總數、已使用、使用率
- test_item_stats: 項目數、執行率、失敗率

與 test-summary 的差異：
- test-summary: 按測試類別和容量分組的 Pass/Fail 明細
- firmware-summary: 整體統計指標（完成率、樣本、執行率）

作者：AI Platform Team
創建日期：2025-12-07
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class FWDetailSummaryHandler(BaseHandler):
    """
    FW 詳細統計處理器
    
    處理查詢特定 FW 版本整體統計指標的請求。
    
    支援的意圖：
    - query_fw_detail_summary: 按專案名稱和 FW 版本查詢詳細統計
    
    觸發關鍵字：
    - 詳細統計、統計資訊
    - 完成率、測試進度
    - 樣本、樣本使用率
    - 執行率、失敗率
    - 概覽、總覽
    """
    
    handler_name = "fw_detail_summary_handler"
    supported_intent = "query_fw_detail_summary"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 FW 詳細統計查詢
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "fw_version": "G200X6EC"
            }
            
        Returns:
            QueryResult: 包含詳細統計資訊
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name', 'fw_version']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        fw_version = parameters.get('fw_version')
        
        try:
            # Step 1: 根據 projectName 和 FW version 找到對應的專案
            matched_project = self._find_project_by_fw(project_name, fw_version)
            
            if not matched_project:
                # 獲取該 projectName 的所有 FW 版本，提供建議
                all_fw_versions = self._get_all_fw_versions(project_name)
                
                if all_fw_versions:
                    fw_list = ", ".join(all_fw_versions[:5])
                    more_info = f"（共 {len(all_fw_versions)} 個版本）" if len(all_fw_versions) > 5 else ""
                    return QueryResult.no_results(
                        query_type=self.handler_name,
                        parameters=parameters,
                        message=f"找不到專案 '{project_name}' 的 FW 版本 '{fw_version}'。\n可用版本：{fw_list}{more_info}"
                    )
                else:
                    return QueryResult.no_results(
                        query_type=self.handler_name,
                        parameters=parameters,
                        message=f"找不到專案 '{project_name}' 或該專案沒有 FW 版本資料"
                    )
            
            project_uid = matched_project.get('projectUid')
            matched_fw = matched_project.get('fw', '')
            
            logger.info(
                f"FW 版本匹配成功: {project_name} + {fw_version} "
                f"-> {matched_fw} (uid: {project_uid})"
            )
            
            # Step 2: 調用 Firmware Summary API
            firmware_summary = self.api_client.get_firmware_summary(project_uid)
            
            if not firmware_summary:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的詳細統計"
                )
            
            # Step 3: 格式化並返回結果
            return self._format_response(
                firmware_summary=firmware_summary,
                project_name=project_name,
                fw_version=matched_fw,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 詳細統計查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _find_project_by_fw(
        self, 
        project_name: str, 
        fw_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        根據專案名稱和 FW 版本找到對應的專案
        
        匹配策略（按優先順序）：
        1. projectName 精確匹配 + fw 精確匹配
        2. projectName 精確匹配 + fw 包含匹配
        3. projectName 模糊匹配 + fw 精確/包含匹配
        
        Args:
            project_name: 專案名稱（如 "Springsteen"）
            fw_version: FW 版本（如 "G200X6EC"）
            
        Returns:
            匹配的專案資料，如果找不到則返回 None
        """
        projects = self.api_client.get_all_projects()
        
        if not projects:
            logger.warning("無法獲取專案列表")
            return None
        
        project_name_lower = project_name.lower()
        fw_version_lower = fw_version.lower()
        
        # 第一輪：精確匹配專案名稱
        exact_name_matches = []
        for project in projects:
            pname = project.get('projectName', '')
            # 處理完整專案名稱（如 "Client_PCIe_Micron_Springsteen_..."）
            if project_name_lower in pname.lower():
                exact_name_matches.append(project)
        
        if exact_name_matches:
            # 在匹配的專案中找 FW 版本
            for project in exact_name_matches:
                fw = project.get('fw', '')
                if self._match_fw_version(fw, fw_version_lower):
                    return project
        
        logger.warning(
            f"找不到匹配的專案: project_name='{project_name}', fw_version='{fw_version}'"
        )
        return None
    
    def _match_fw_version(self, fw_field: str, fw_query: str) -> bool:
        """
        匹配 FW 版本
        
        支援多種匹配方式：
        1. 完全匹配（忽略大小寫）
        2. 包含匹配
        3. 解析格式如 "[MR1.2][Y1114B_629fa1a]" 中的 Y1114B
        
        Args:
            fw_field: API 返回的 fw 欄位值
            fw_query: 用戶查詢的 FW 版本
            
        Returns:
            是否匹配
        """
        if not fw_field:
            return False
        
        fw_field_lower = fw_field.lower()
        fw_query_lower = fw_query.lower()
        
        # 1. 完全匹配
        if fw_field_lower == fw_query_lower:
            return True
        
        # 2. 包含匹配
        if fw_query_lower in fw_field_lower:
            return True
        
        # 3. 解析格式匹配 "[XXX][YYY_zzz]" -> 匹配 YYY
        brackets = re.findall(r'\[([^\]]+)\]', fw_field)
        for content in brackets:
            # 提取主版本號（如 Y1114B_629fa1a -> Y1114B）
            main_version = content.split('_')[0]
            if main_version.lower() == fw_query_lower:
                return True
            if fw_query_lower in content.lower():
                return True
        
        return False
    
    def _get_all_fw_versions(self, project_name: str) -> List[str]:
        """
        獲取指定專案的所有 FW 版本
        
        Args:
            project_name: 專案名稱
            
        Returns:
            FW 版本列表
        """
        projects = self.api_client.get_all_projects()
        
        if not projects:
            return []
        
        project_name_lower = project_name.lower()
        fw_versions = []
        
        for project in projects:
            pname = project.get('projectName', '')
            if project_name_lower in pname.lower():
                fw = project.get('fw', '')
                if fw and fw not in fw_versions:
                    fw_versions.append(fw)
        
        return fw_versions
    
    def _format_response(
        self,
        firmware_summary: Dict[str, Any],
        project_name: str,
        fw_version: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化 Firmware Summary 回應
        
        Args:
            firmware_summary: API 返回的統計資料
            project_name: 專案名稱
            fw_version: FW 版本
            project: 專案資料
            parameters: 原始參數
            
        Returns:
            QueryResult: 格式化的查詢結果
        """
        # 提取資料
        overview = firmware_summary.get('overview', {})
        sample_stats = firmware_summary.get('sample_stats', {})
        test_item_stats = firmware_summary.get('test_item_stats', {})
        
        # 提取概覽指標
        total_test_items = overview.get('total_test_items', 0)
        passed = overview.get('passed', 0)
        failed = overview.get('failed', 0)
        conditional_passed = overview.get('conditional_passed', 0)
        completion_rate = overview.get('completion_rate', 0)
        pass_rate = overview.get('pass_rate', 0)
        
        # 提取樣本統計
        total_samples = sample_stats.get('total_samples', 0)
        samples_used = sample_stats.get('samples_used', 0)
        utilization_rate = sample_stats.get('utilization_rate', 0)
        
        # 提取測試項目統計
        total_items = test_item_stats.get('total_items', 0)
        passed_items = test_item_stats.get('passed_items', 0)
        failed_items = test_item_stats.get('failed_items', 0)
        execution_rate = test_item_stats.get('execution_rate', 0)
        fail_rate = test_item_stats.get('fail_rate', 0)
        
        # 建構回應訊息
        response_parts = []
        
        # 標題
        response_parts.append(f"## 📈 {project_name} {fw_version} 詳細統計\n")
        
        # 基本資訊
        response_parts.append("### 基本資訊")
        response_parts.append(f"- **專案**: {project_name}")
        response_parts.append(f"- **FW 版本**: {fw_version}")
        sub_version = firmware_summary.get('sub_version', '')
        if sub_version:
            response_parts.append(f"- **Sub Version**: {sub_version}")
        task_name = firmware_summary.get('task_name', '')
        if task_name:
            response_parts.append(f"- **Task**: {task_name}")
        response_parts.append("")
        
        # 測試概覽
        response_parts.append("### 📊 測試概覽 (Overview)")
        response_parts.append("| 指標 | 數值 |")
        response_parts.append("|------|------|")
        response_parts.append(f"| 總測試項目 | {total_test_items} |")
        response_parts.append(f"| 已通過 | {passed} |")
        response_parts.append(f"| 已失敗 | {failed} |")
        if conditional_passed > 0:
            response_parts.append(f"| 條件通過 | {conditional_passed} |")
        response_parts.append(f"| **完成率** | {completion_rate}% |")
        response_parts.append(f"| **通過率** | {pass_rate}% |")
        response_parts.append("")
        
        # 樣本統計
        response_parts.append("### 🧪 樣本統計 (Sample Stats)")
        response_parts.append("| 指標 | 數值 |")
        response_parts.append("|------|------|")
        response_parts.append(f"| 總樣本數 | {total_samples} |")
        response_parts.append(f"| 已使用樣本 | {samples_used} |")
        response_parts.append(f"| **使用率** | {utilization_rate}% |")
        response_parts.append("")
        
        # 測試項目統計
        response_parts.append("### 📋 測試項目統計 (Test Item Stats)")
        response_parts.append("| 指標 | 數值 |")
        response_parts.append("|------|------|")
        response_parts.append(f"| 總項目數 | {total_items} |")
        response_parts.append(f"| 通過項目 | {passed_items} |")
        response_parts.append(f"| 失敗項目 | {failed_items} |")
        response_parts.append(f"| **執行率** | {execution_rate}% |")
        response_parts.append(f"| **失敗率** | {fail_rate}% |")
        response_parts.append("")
        
        # 狀態摘要
        response_parts.append("### 狀態摘要")
        
        # 進度狀態
        if completion_rate >= 100:
            response_parts.append(f"- ✅ **測試進度**: 已完成 ({completion_rate}%)")
        elif completion_rate >= 80:
            response_parts.append(f"- 🔵 **測試進度**: 接近完成 ({completion_rate}%)")
        elif completion_rate >= 50:
            response_parts.append(f"- ⏳ **測試進度**: 進行中 ({completion_rate}%)")
        else:
            response_parts.append(f"- 🔴 **測試進度**: 剛開始 ({completion_rate}%)")
        
        # 通過率狀態
        if pass_rate >= 90:
            response_parts.append(f"- ✅ **測試品質**: 優秀 ({pass_rate}% 通過率)")
        elif pass_rate >= 70:
            response_parts.append(f"- 🔵 **測試品質**: 良好 ({pass_rate}% 通過率)")
        elif pass_rate >= 50:
            response_parts.append(f"- ⚠️ **測試品質**: 需關注 ({pass_rate}% 通過率)")
        else:
            response_parts.append(f"- 🔴 **測試品質**: 需改善 ({pass_rate}% 通過率)")
        
        # 失敗項目警告
        if failed_items > 0:
            response_parts.append(f"- ⚠️ **待處理**: {failed_items} 個測試項目失敗 (失敗率 {fail_rate}%)")
        
        message = "\n".join(response_parts)
        
        # 建構結構化資料
        data = {
            "project_name": project_name,
            "fw_version": fw_version,
            "sub_version": sub_version,
            "task_name": task_name,
            "project_uid": project.get('projectUid', ''),
            "overview": {
                "total_test_items": total_test_items,
                "passed": passed,
                "failed": failed,
                "conditional_passed": conditional_passed,
                "completion_rate": completion_rate,
                "pass_rate": pass_rate
            },
            "sample_stats": {
                "total_samples": total_samples,
                "samples_used": samples_used,
                "utilization_rate": utilization_rate
            },
            "test_item_stats": {
                "total_items": total_items,
                "passed_items": passed_items,
                "failed_items": failed_items,
                "execution_rate": execution_rate,
                "fail_rate": fail_rate
            }
        }
        
        return QueryResult.success(
            message=message,
            data=data,
            query_type=self.handler_name,
            parameters=parameters,
            metadata={
                "api_endpoint": "firmware-summary",
                "project_uid": project.get('projectUid', ''),
                "matched_fw": fw_version
            }
        )
