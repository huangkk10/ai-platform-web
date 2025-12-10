"""
FWTestCategoriesHandler - 專案 FW 測試類別查詢
=============================================

處理 Phase 2 意圖 5：專案 FW 測試類別查詢
- 查詢特定專案特定 FW 版本有哪些測試類別

API 端點：GET /api/v1/projects/{project_uid}/test-details

欄位順序：Ongoing / Passed / Conditional Passed / Failed / Interrupted

特點：
- 基於 TestSummaryByFWHandler 的 FW 匹配邏輯
- 從 test-details API 的 details 彙整各類別統計
- 返回 FW 下所有測試類別及其統計數據
- 支援按容量過濾

作者：AI Platform Team
創建日期：2025-12-09
更新日期：2025-12-10 - 改用 test-details API
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class FWTestCategoriesHandler(BaseHandler):
    """
    專案 FW 測試類別查詢處理器
    
    查詢特定專案特定 FW 版本有哪些測試類別。
    
    支援的意圖：
    - query_project_fw_test_categories: 查詢專案 FW 的測試類別
    
    用戶問法範例：
    - Project Alpha 的 512GB FW 有哪些測試類別？
    - DEMETER 的 Y1114B 版本包含哪些測試？
    - 這個案子的 1024GB FW 有什麼 Category？
    """
    
    handler_name = "fw_test_categories_handler"
    supported_intent = "query_project_fw_test_categories"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 FW 測試類別查詢
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "fw_version": "Y1114B"  # 或 "512GB"
            }
            
        Returns:
            QueryResult: 包含測試類別列表
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
                f"FW 測試類別查詢 - 版本匹配成功: {project_name} + {fw_version} "
                f"-> {matched_fw} (uid: {project_uid})"
            )
            
            # Step 2: 調用 Test Details API（包含完整 test items 明細）
            test_details = self.api_client.get_project_test_details(project_uid)
            
            if not test_details:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試詳細資料"
                )
            
            # Step 3: 從 details 彙整類別統計並格式化
            return self._format_categories_response(
                test_details=test_details,
                project_name=project_name,
                fw_version=matched_fw,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 測試類別查詢錯誤: {str(e)}")
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
            project_name: 專案名稱（如 "DEMETER"）
            fw_version: FW 版本（如 "Y1114B" 或 "512GB"）
            
        Returns:
            匹配的專案資料，如果找不到則返回 None
        """
        projects = self.api_client.get_all_projects()
        
        if not projects:
            logger.warning("無法獲取專案列表")
            return None
        
        project_name_lower = project_name.lower()
        fw_version_lower = fw_version.lower()
        
        # 第一輪：projectName 精確匹配（忽略大小寫）
        exact_name_matches = [
            p for p in projects 
            if p.get('projectName', '').lower() == project_name_lower
        ]
        
        if exact_name_matches:
            result = self._find_fw_match(exact_name_matches, fw_version_lower)
            if result:
                return result
        
        # 第二輪：projectName 模糊匹配（包含）
        fuzzy_name_matches = [
            p for p in projects 
            if project_name_lower in p.get('projectName', '').lower()
        ]
        
        if fuzzy_name_matches:
            result = self._find_fw_match(fuzzy_name_matches, fw_version_lower)
            if result:
                return result
        
        logger.warning(
            f"找不到匹配: project_name={project_name}, fw_version={fw_version}"
        )
        return None
    
    def _find_fw_match(
        self, 
        projects: List[Dict[str, Any]], 
        fw_version_lower: str
    ) -> Optional[Dict[str, Any]]:
        """
        在專案列表中找到 FW 版本匹配的專案
        
        匹配策略：
        1. 精確匹配（忽略大小寫）
        2. 包含匹配（fw_version 是 fw 的子字串）
        3. 解析匹配（從格式如 "[MR1.2][Y1114B_xxx]" 中提取）
        
        Args:
            projects: 專案列表
            fw_version_lower: 小寫的 FW 版本
            
        Returns:
            匹配的專案
        """
        # 優先級 1：精確匹配
        for project in projects:
            fw = project.get('fw', '').lower()
            if fw == fw_version_lower:
                return project
        
        # 優先級 2：包含匹配
        for project in projects:
            fw = project.get('fw', '').lower()
            if fw_version_lower in fw:
                return project
        
        # 優先級 3：智能解析匹配
        for project in projects:
            fw = project.get('fw', '')
            extracted_versions = self._extract_fw_versions(fw)
            for extracted in extracted_versions:
                if extracted.lower() == fw_version_lower:
                    return project
        
        return None
    
    def _extract_fw_versions(self, fw_string: str) -> List[str]:
        """
        從 FW 版本字串中提取版本號
        
        支援的格式：
        - "[MR1.2][Y1114B_629fa1a_Y1114A_8572096]" -> ["Y1114B", "Y1114A"]
        - "FWY0512A_PKGY0512V1" -> ["FWY0512A", "PKGY0512V1"]
        
        Args:
            fw_string: FW 版本字串
            
        Returns:
            提取的版本號列表
        """
        versions = []
        
        # 模式 1：提取 [XXX] 中的內容
        bracket_pattern = r'\[([^\]]+)\]'
        bracket_matches = re.findall(bracket_pattern, fw_string)
        
        for match in bracket_matches:
            if match.startswith('MR') or match.startswith('mr'):
                continue
            
            parts = match.split('_')
            for part in parts:
                if len(part) >= 4 and len(part) <= 10 and re.match(r'^[A-Za-z0-9]+$', part):
                    if re.search(r'[A-Za-z]', part) and re.search(r'[0-9]', part):
                        versions.append(part)
        
        # 如果沒有找到方括號格式，直接使用整個字串
        if not versions and fw_string:
            clean_fw = fw_string.strip()
            if clean_fw:
                versions.append(clean_fw)
        
        return versions
    
    def _get_all_fw_versions(self, project_name: str) -> List[str]:
        """
        獲取指定專案名稱的所有 FW 版本
        
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
            if project.get('projectName', '').lower() == project_name_lower:
                fw = project.get('fw', '')
                if fw and fw not in fw_versions:
                    fw_versions.append(fw)
        
        return fw_versions
    
    def _format_categories_response(
        self,
        test_details: Dict[str, Any],
        project_name: str,
        fw_version: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化測試類別回應（從 test-details API 彙整）
        
        Args:
            test_details: test-details API 返回的完整資料
            project_name: 專案名稱
            fw_version: FW 版本
            project: 專案完整資料
            parameters: 原始查詢參數
            
        Returns:
            QueryResult: 格式化的類別列表結果
        """
        details = test_details.get('details', [])
        capacities = test_details.get('capacities', [])
        summary = test_details.get('summary', {})
        
        if not details:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 '{project_name}' FW '{fw_version}' 沒有測試類別資料"
            )
        
        # 從 details 彙整各 Category 的統計
        category_stats = self._aggregate_categories_from_details(details)
        
        if not category_stats:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 '{project_name}' FW '{fw_version}' 沒有測試類別資料"
            )
        
        # 格式化類別資料
        formatted_categories = []
        total_ongoing = 0
        total_passed = 0
        total_conditional_passed = 0
        total_failed = 0
        total_interrupted = 0
        
        for cat_name, cat_data in category_stats.items():
            cat_ongoing = cat_data.get('ongoing', 0)
            cat_passed = cat_data.get('passed', 0)
            cat_conditional_passed = cat_data.get('conditional_passed', 0)
            cat_failed = cat_data.get('failed', 0)
            cat_interrupted = cat_data.get('interrupted', 0)
            
            total_ongoing += cat_ongoing
            total_passed += cat_passed
            total_conditional_passed += cat_conditional_passed
            total_failed += cat_failed
            total_interrupted += cat_interrupted
            
            # 計算狀態
            status = self._determine_category_status(
                cat_passed, cat_failed, cat_ongoing, cat_conditional_passed, cat_interrupted
            )
            
            formatted_categories.append({
                'name': cat_name,
                'ongoing': cat_ongoing,
                'passed': cat_passed,
                'conditional_passed': cat_conditional_passed,
                'failed': cat_failed,
                'interrupted': cat_interrupted,
                'total': cat_ongoing + cat_passed + cat_conditional_passed + cat_failed + cat_interrupted,
                'status': status,
                'test_item_count': cat_data.get('test_item_count', 0)
            })
        
        # 按類別名稱排序
        formatted_categories.sort(key=lambda x: x['name'])
        
        # 構建回應資料
        formatted_data = {
            'projectName': project_name,
            'fwVersion': fw_version,
            'fwNameFromApi': test_details.get('fw_name', ''),
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'categories': formatted_categories,
            'capacities': capacities,
            'summary': {
                'total_categories': len(formatted_categories),
                'total_ongoing': total_ongoing,
                'total_passed': total_passed,
                'total_conditional_passed': total_conditional_passed,
                'total_failed': total_failed,
                'total_interrupted': total_interrupted,
                'total_items': test_details.get('total_items', 0),
                'pass_rate': summary.get('pass_rate', 0)
            }
        }
        
        # 構建友好的訊息（表格格式）
        # 欄位順序：Ongoing / Passed / Conditional Passed / Failed / Interrupted
        message_lines = [
            f"**專案 '{project_name}' FW '{fw_version}' 測試類別**",
            f"",
            f"📋 共 {len(formatted_categories)} 個測試類別，{test_details.get('total_items', 0)} 個測項：",
            "",
            "| # | 測試類別 | 狀態 | Ongoing | Passed | Cond.Pass | Failed | Interrupted |",
            "|---|----------|------|---------|--------|-----------|--------|-------------|"
        ]
        
        for i, cat in enumerate(formatted_categories, 1):
            status_emoji = self._get_status_emoji(cat['status'])
            message_lines.append(
                f"| {i} | {cat['name']} | {status_emoji} | {cat['ongoing']} | {cat['passed']} | {cat['conditional_passed']} | {cat['failed']} | {cat['interrupted']} |"
            )
        
        # 添加總計和可用容量
        message_lines.extend([
            "",
            f"� **總計**: Ongoing: {total_ongoing}, Passed: {total_passed}, Cond.Pass: {total_conditional_passed}, Failed: {total_failed}, Interrupted: {total_interrupted}",
            f"�💡 可用容量: {', '.join(capacities)}" if capacities else ""
        ])
        
        message = "\n".join(filter(None, message_lines))
        
        result = QueryResult.success(
            data=formatted_data,
            count=len(formatted_categories),
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'total_categories': len(formatted_categories),
                'total_ongoing': total_ongoing,
                'total_passed': total_passed,
                'total_conditional_passed': total_conditional_passed,
                'total_failed': total_failed,
                'total_interrupted': total_interrupted,
                'fw_version_matched': fw_version,
                'project_uid': project.get('projectUid', ''),
                'capacities_count': len(capacities),
                'total_items': test_details.get('total_items', 0)
            }
        )
        
        self._log_result(result)
        return result
    
    def _aggregate_categories_from_details(
        self, 
        details: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        從 test-details 的 details 彙整各 Category 的統計
        
        Args:
            details: test-details API 返回的 details 列表
            
        Returns:
            Dict[category_name, stats]: 各類別的統計資料
        """
        category_stats = {}
        
        for item in details:
            cat_name = item.get('category_name', '')
            if not cat_name:
                continue
            
            total = item.get('total', {})
            
            if cat_name not in category_stats:
                category_stats[cat_name] = {
                    'ongoing': 0,
                    'passed': 0,
                    'conditional_passed': 0,
                    'failed': 0,
                    'interrupted': 0,
                    'test_item_count': 0
                }
            
            # 累加統計（使用正確的欄位名稱）
            category_stats[cat_name]['ongoing'] += total.get('ongoing', 0)
            category_stats[cat_name]['passed'] += total.get('passed', 0)
            category_stats[cat_name]['conditional_passed'] += total.get('conditional_passed', 0)
            category_stats[cat_name]['failed'] += total.get('failed', 0)
            category_stats[cat_name]['interrupted'] += total.get('interrupted', 0)
            category_stats[cat_name]['test_item_count'] += 1
        
        return category_stats
    
    def _determine_category_status(
        self, 
        passed_count: int, 
        failed_count: int, 
        ongoing_count: int,
        conditional_passed_count: int = 0,
        interrupted_count: int = 0
    ) -> str:
        """
        判斷類別的整體狀態
        
        Args:
            passed_count: 通過數量
            failed_count: 失敗數量
            ongoing_count: 進行中數量
            conditional_passed_count: 條件通過數量
            interrupted_count: 中斷數量
            
        Returns:
            狀態字串: 'passed', 'failed', 'in_progress', 'no_data', 'conditional'
        """
        total = passed_count + failed_count + ongoing_count + conditional_passed_count + interrupted_count
        
        if total == 0:
            return 'no_data'
        elif ongoing_count > 0:
            return 'in_progress'
        elif failed_count > 0:
            return 'failed'
        elif interrupted_count > 0:
            return 'interrupted'
        elif conditional_passed_count > 0 and passed_count == 0:
            return 'conditional'
        else:
            return 'passed'
    
    def _get_status_emoji(self, status: str) -> str:
        """
        獲取狀態對應的 emoji
        
        Args:
            status: 狀態字串
            
        Returns:
            狀態 emoji
        """
        status_emoji_map = {
            'passed': '✅',
            'failed': '❌',
            'in_progress': '🔄',
            'no_data': '⚪',
            'conditional': '⚠️',
            'interrupted': '🛑'
        }
        return status_emoji_map.get(status, '❓')
