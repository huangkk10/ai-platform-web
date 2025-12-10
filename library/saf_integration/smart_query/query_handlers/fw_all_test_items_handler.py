"""
FWAllTestItemsHandler - 專案 FW 全部測項查詢
============================================

處理 Phase 2 意圖 7：專案 FW 全部測項查詢
- 查詢特定專案特定 FW 版本的所有測項（不分類別）

API 端點：GET /api/v1/projects/{project_uid}/test-details

欄位順序：Ongoing / Passed / Conditional Passed / Failed / Interrupted

特點：
- 繼承 FWTestCategoriesHandler 的 FW 匹配邏輯
- 從 test-details API 獲取所有測項
- 按類別分組顯示所有測試項目

作者：AI Platform Team
創建日期：2025-12-10
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class FWAllTestItemsHandler(BaseHandler):
    """
    專案 FW 全部測項查詢處理器
    
    查詢特定專案特定 FW 版本的所有測項。
    
    支援的意圖：
    - query_project_fw_all_test_items: 查詢專案 FW 的所有測項
    
    用戶問法範例：
    - Springsteen 的 GD10YBJD_Opal 有哪些測項？
    - DEMETER 的 Y1114B 所有測試項目？
    - 列出這個案子 512GB 的全部測試項目
    """
    
    handler_name = "fw_all_test_items_handler"
    supported_intent = "query_project_fw_all_test_items"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 FW 全部測項查詢
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "fw_version": "GD10YBJD_Opal"
            }
            
        Returns:
            QueryResult: 包含所有測項列表
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
                f"FW 全部測項查詢 - 版本匹配成功: {project_name} + {fw_version} "
                f"-> {matched_fw} (uid: {project_uid})"
            )
            
            # Step 2: 調用 Test Details API
            test_details = self.api_client.get_project_test_details(project_uid)
            
            if not test_details:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試詳細資料"
                )
            
            # Step 3: 格式化所有測項
            return self._format_all_test_items_response(
                test_details=test_details,
                project_name=project_name,
                fw_version=matched_fw,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 全部測項查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _format_all_test_items_response(
        self,
        test_details: Dict[str, Any],
        project_name: str,
        fw_version: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化所有測項回應（按類別分組）
        
        Args:
            test_details: test-details API 返回的完整資料
            project_name: 專案名稱
            fw_version: FW 版本
            project: 專案完整資料
            parameters: 原始查詢參數
            
        Returns:
            QueryResult: 格式化的測項列表結果
        """
        details = test_details.get('details', [])
        capacities = test_details.get('capacities', [])
        summary = test_details.get('summary', {})
        
        if not details:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 '{project_name}' FW '{fw_version}' 沒有測試資料"
            )
        
        # 按類別分組
        categories_map = {}
        total_ongoing = 0
        total_passed = 0
        total_conditional_passed = 0
        total_failed = 0
        total_interrupted = 0
        
        for item in details:
            category_name = item.get('category_name', 'Unknown')
            test_item_name = item.get('test_item_name', 'Unknown')
            total = item.get('total', {})
            
            ongoing = total.get('ongoing', 0)
            passed = total.get('passed', 0)
            conditional_passed = total.get('conditional_passed', 0)
            failed = total.get('failed', 0)
            interrupted = total.get('interrupted', 0)
            
            total_ongoing += ongoing
            total_passed += passed
            total_conditional_passed += conditional_passed
            total_failed += failed
            total_interrupted += interrupted
            
            # 計算狀態
            status = self._determine_item_status(
                passed, failed, ongoing, conditional_passed, interrupted
            )
            
            if category_name not in categories_map:
                categories_map[category_name] = {
                    'name': category_name,
                    'items': [],
                    'total_ongoing': 0,
                    'total_passed': 0,
                    'total_conditional_passed': 0,
                    'total_failed': 0,
                    'total_interrupted': 0
                }
            
            categories_map[category_name]['items'].append({
                'name': test_item_name,
                'ongoing': ongoing,
                'passed': passed,
                'conditional_passed': conditional_passed,
                'failed': failed,
                'interrupted': interrupted,
                'total': ongoing + passed + conditional_passed + failed + interrupted,
                'status': status,
                'sample_capacity': item.get('sample_capacity', ''),
                'note': item.get('note', '')
            })
            
            categories_map[category_name]['total_ongoing'] += ongoing
            categories_map[category_name]['total_passed'] += passed
            categories_map[category_name]['total_conditional_passed'] += conditional_passed
            categories_map[category_name]['total_failed'] += failed
            categories_map[category_name]['total_interrupted'] += interrupted
        
        # 轉換為列表並排序
        categories_list = list(categories_map.values())
        categories_list.sort(key=lambda x: x['name'])
        
        # 對每個類別內的測項排序
        for cat in categories_list:
            cat['items'].sort(key=lambda x: x['name'])
        
        # 構建回應資料
        formatted_data = {
            'projectName': project_name,
            'fwVersion': fw_version,
            'categories': categories_list,
            'capacities': capacities,
            'summary': {
                'total_categories': len(categories_list),
                'total_items': len(details),
                'total_ongoing': total_ongoing,
                'total_passed': total_passed,
                'total_conditional_passed': total_conditional_passed,
                'total_failed': total_failed,
                'total_interrupted': total_interrupted
            }
        }
        
        # 構建友好的訊息（分類別的表格格式）
        message_lines = [
            f"**專案 '{project_name}' FW '{fw_version}' 全部測項**",
            "",
            f"📋 共 {len(categories_list)} 個類別，{len(details)} 個測試項目：",
        ]
        
        for cat in categories_list:
            cat_status = self._determine_category_status(cat)
            status_emoji = self._get_status_emoji(cat_status)
            
            message_lines.extend([
                "",
                f"### {status_emoji} **{cat['name']}** ({len(cat['items'])} 項)",
                "",
                "| # | 測試項目 | 狀態 | Ongoing | Passed | Cond.Pass | Failed | Interrupted |",
                "|---|----------|------|---------|--------|-----------|--------|-------------|"
            ])
            
            for i, item in enumerate(cat['items'], 1):
                item_status_emoji = self._get_status_emoji(item['status'])
                item_name = item['name']
                if len(item_name) > 35:
                    item_name = item_name[:32] + "..."
                
                message_lines.append(
                    f"| {i} | {item_name} | {item_status_emoji} | {item['ongoing']} | {item['passed']} | {item['conditional_passed']} | {item['failed']} | {item['interrupted']} |"
                )
        
        # 添加總計
        message_lines.extend([
            "",
            "---",
            f"📊 **總計**: {len(details)} 測項 | Ongoing: {total_ongoing}, Passed: {total_passed}, Cond.Pass: {total_conditional_passed}, Failed: {total_failed}, Interrupted: {total_interrupted}",
            f"💡 可用容量: {', '.join(capacities)}" if capacities else ""
        ])
        
        message = "\n".join(filter(None, message_lines))
        
        result = QueryResult.success(
            data=formatted_data,
            count=len(details),
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'total_categories': len(categories_list),
                'total_items': len(details),
                'total_ongoing': total_ongoing,
                'total_passed': total_passed,
                'total_conditional_passed': total_conditional_passed,
                'total_failed': total_failed,
                'total_interrupted': total_interrupted,
                'fw_version_matched': fw_version,
                'project_uid': project.get('projectUid', '')
            }
        )
        
        self._log_result(result)
        return result
    
    def _determine_item_status(
        self, 
        pass_count: int, 
        fail_count: int, 
        ongoing_count: int,
        conditional_count: int = 0,
        interrupted_count: int = 0
    ) -> str:
        """判斷測項的整體狀態"""
        if fail_count > 0:
            return 'failed'
        elif interrupted_count > 0:
            return 'interrupted'
        elif ongoing_count > 0:
            return 'in_progress'
        elif conditional_count > 0:
            return 'conditional'
        elif pass_count > 0:
            return 'passed'
        else:
            return 'no_data'
    
    def _determine_category_status(self, category: Dict[str, Any]) -> str:
        """判斷類別的整體狀態"""
        if category['total_failed'] > 0:
            return 'failed'
        elif category['total_interrupted'] > 0:
            return 'interrupted'
        elif category['total_ongoing'] > 0:
            return 'in_progress'
        elif category['total_conditional_passed'] > 0:
            return 'conditional'
        elif category['total_passed'] > 0:
            return 'passed'
        else:
            return 'no_data'
    
    def _get_status_emoji(self, status: str) -> str:
        """獲取狀態對應的 emoji"""
        status_emoji_map = {
            'passed': '✅',
            'failed': '❌',
            'in_progress': '🔄',
            'conditional': '⚠️',
            'interrupted': '🛑',
            'no_data': '⚪'
        }
        return status_emoji_map.get(status, '❓')
    
    # ==================== 從 FWTestCategoriesHandler 複用的方法 ====================
    
    def _find_project_by_fw(
        self, 
        project_name: str, 
        fw_version: str
    ) -> Optional[Dict[str, Any]]:
        """根據專案名稱和 FW 版本找到對應的專案"""
        projects = self.api_client.get_all_projects()
        
        if not projects:
            logger.warning("無法獲取專案列表")
            return None
        
        project_name_lower = project_name.lower()
        fw_version_lower = fw_version.lower()
        
        exact_name_matches = [
            p for p in projects 
            if p.get('projectName', '').lower() == project_name_lower
        ]
        
        if exact_name_matches:
            result = self._find_fw_match(exact_name_matches, fw_version_lower)
            if result:
                return result
        
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
        """在專案列表中找到 FW 版本匹配的專案"""
        for project in projects:
            fw = project.get('fw', '').lower()
            if fw == fw_version_lower:
                return project
        
        for project in projects:
            fw = project.get('fw', '').lower()
            if fw_version_lower in fw:
                return project
        
        for project in projects:
            fw = project.get('fw', '')
            extracted_versions = self._extract_fw_versions(fw)
            for extracted in extracted_versions:
                if extracted.lower() == fw_version_lower:
                    return project
        
        return None
    
    def _extract_fw_versions(self, fw_string: str) -> List[str]:
        """從 FW 版本字串中提取版本號"""
        versions = []
        
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
        
        if not versions and fw_string:
            clean_fw = fw_string.strip()
            if clean_fw:
                versions.append(clean_fw)
        
        return versions
    
    def _get_all_fw_versions(self, project_name: str) -> List[str]:
        """獲取指定專案名稱的所有 FW 版本"""
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
