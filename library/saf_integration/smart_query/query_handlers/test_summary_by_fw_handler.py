"""
TestSummaryByFWHandler - 按 FW 版本查詢專案測試結果
====================================================

處理 Phase 4 FW 版本查詢意圖：
- query_project_test_summary_by_fw: 查詢特定專案特定 FW 版本的測試結果

API 端點：GET /api/v1/projects/{project_uid}/test-summary

特點：
- FW 版本模糊匹配：用戶輸入 "Y1114B" 能匹配 "[MR1.2][Y1114B_629fa1a_Y1114A_8572096]"
- 同一 projectName 可能有多個 FW 版本（各有不同的 projectUid）
- 需要遍歷專案列表找到匹配的 FW 版本

作者：AI Platform Team
創建日期：2025-12-26
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class TestSummaryByFWHandler(BaseHandler):
    """
    按 FW 版本查詢專案測試結果處理器
    
    處理查詢特定 FW 版本測試結果的請求。
    
    支援的意圖：
    - query_project_test_summary_by_fw: 按專案名稱和 FW 版本查詢測試結果
    
    FW 版本匹配策略：
    1. 完全匹配（忽略大小寫）
    2. 包含匹配（用戶輸入是 FW 版本的子字串）
    3. 智能解析匹配（處理格式如 "[MR1.2][Y1114B_629fa1a]"）
    """
    
    handler_name = "test_summary_by_fw_handler"
    supported_intent = "query_project_test_summary_by_fw"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 FW 版本測試結果查詢
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "fw_version": "Y1114B"
            }
            
        Returns:
            QueryResult: 包含測試結果統計
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
                    fw_list = ", ".join(all_fw_versions[:5])  # 最多顯示 5 個
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
            
            # Step 2: 調用 Test Summary API
            test_summary = self.api_client.get_project_test_summary(project_uid)
            
            if not test_summary:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試摘要"
                )
            
            # Step 3: 格式化並返回結果
            return self._format_response(
                test_summary=test_summary,
                project_name=project_name,
                fw_version=matched_fw,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"FW 版本測試摘要查詢錯誤: {str(e)}")
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
        
        注意：SAF API 使用 'fw' 欄位而非 'fwVersion'
        
        Args:
            project_name: 專案名稱（如 "DEMETER"）
            fw_version: FW 版本（如 "Y1114B"）
            
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
            # 在精確匹配的專案中找 FW 版本
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
        3. 解析匹配（從格式如 "[MR1.2][Y1114B_xxx]" 中提取 Y1114B）
        
        注意：使用 'fw' 欄位而非 'fwVersion'
        
        Args:
            projects: 專案列表
            fw_version_lower: 小寫的 FW 版本
            
        Returns:
            匹配的專案，如果找不到則返回 None
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
        - "82CBW5QF" -> ["82CBW5QF"]
        - "FWX0926C" -> ["FWX0926C"]
        
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
            # 跳過版本標籤如 "MR1.2"
            if match.startswith('MR') or match.startswith('mr'):
                continue
            
            # 分割底線，提取可能的版本號
            parts = match.split('_')
            for part in parts:
                # 版本號通常是字母+數字的組合，長度 4-10
                if len(part) >= 4 and len(part) <= 10 and re.match(r'^[A-Za-z0-9]+$', part):
                    # 過濾純數字和純字母
                    if re.search(r'[A-Za-z]', part) and re.search(r'[0-9]', part):
                        versions.append(part)
        
        # 如果沒有找到方括號格式，直接使用整個字串
        if not versions and fw_string:
            # 清理字串
            clean_fw = fw_string.strip()
            if clean_fw:
                versions.append(clean_fw)
        
        return versions
    
    def _get_all_fw_versions(self, project_name: str) -> List[str]:
        """
        獲取指定專案名稱的所有 FW 版本
        
        注意：使用 'fw' 欄位而非 'fwVersion'
        
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
    
    def _format_response(
        self,
        test_summary: Dict[str, Any],
        project_name: str,
        fw_version: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化測試摘要回應
        
        Args:
            test_summary: API 返回的測試摘要
            project_name: 專案名稱
            fw_version: FW 版本
            project: 專案完整資料
            parameters: 原始查詢參數
            
        Returns:
            QueryResult: 格式化的結果
        """
        # 從 summary 或 categories 獲取總計
        summary = test_summary.get('summary', {})
        categories = test_summary.get('categories', [])
        
        if summary:
            total_pass = summary.get('total_pass', 0)
            total_fail = summary.get('total_fail', 0)
        else:
            total_pass = sum(cat.get('total', {}).get('pass', 0) for cat in categories)
            total_fail = sum(cat.get('total', {}).get('fail', 0) for cat in categories)
        
        total = total_pass + total_fail
        pass_rate = f"{(total_pass / total * 100):.1f}%" if total > 0 else "N/A"
        
        # 格式化類別資料
        formatted_categories = []
        for cat in categories:
            cat_total = cat.get('total', {})
            cat_pass = cat_total.get('pass', 0)
            cat_fail = cat_total.get('fail', 0)
            formatted_categories.append({
                'name': cat.get('name', ''),
                'pass': cat_pass,
                'fail': cat_fail,
                'total': cat_pass + cat_fail
            })
        
        # 構建回應資料
        formatted_data = {
            'projectName': project_name,
            'fwVersion': fw_version,
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'summary': {
                'pass': total_pass,
                'fail': total_fail,
                'total': total,
                'passRate': pass_rate
            },
            'categories': formatted_categories,
            'capacities': test_summary.get('capacities', [])
        }
        
        # 構建友好的訊息
        message = (
            f"專案 '{project_name}' FW 版本 '{fw_version}' 測試結果：\n"
            f"✅ Pass: {total_pass}  ❌ Fail: {total_fail}  "
            f"📊 通過率: {pass_rate}"
        )
        
        result = QueryResult.success(
            data=formatted_data,
            count=1,
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'total_pass': total_pass,
                'total_fail': total_fail,
                'pass_rate': pass_rate,
                'fw_version_matched': fw_version,
                'project_uid': project.get('projectUid', ''),
                'categories_count': len(categories),
                'capacities_count': len(test_summary.get('capacities', []))
            }
        )
        
        self._log_result(result)
        return result
