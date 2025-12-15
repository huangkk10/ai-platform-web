"""
SupportedCapacitiesHandler - 查詢專案 FW 支援的容量
====================================================

處理 Phase 14 意圖：
- query_supported_capacities: 查詢特定專案 FW 版本支援哪些儲存容量

功能：
- 從 Test Summary API 獲取 capacities 列表
- 計算每個容量的測試統計（Pass/Fail）
- 判斷支援與未支援的容量
- 提供容量測試摘要

作者：AI Platform Team
創建日期：2025-12-15
"""

import logging
import re
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)

# 系統支援的所有可能容量（用於判斷「未支援」的容量）
ALL_POSSIBLE_CAPACITIES = [
    '256GB', '512GB', '1024GB', '2048GB', '4096GB', '8192GB'
]


class SupportedCapacitiesHandler(BaseHandler):
    """
    專案 FW 支援容量查詢處理器
    
    處理查詢特定專案 FW 版本支援哪些儲存容量的請求。
    
    支援的意圖：
    - query_supported_capacities: 查詢專案 FW 支援的容量
    
    範例查詢：
    - 「Springsteen FW PH10YC3H 支援哪些容量？」
    - 「TITAN 最新 FW 有支援哪些容量」
    - 「Channel 這個版本支援多大的硬碟？」
    """
    
    handler_name = "supported_capacities_handler"
    supported_intent = "query_supported_capacities"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行專案 FW 支援容量查詢
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "fw_version": "PH10YC3H"
            }
            
        Returns:
            QueryResult: 包含支援容量的結果
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
            # Step 1: 找到匹配的專案
            matched_project = self._find_project_by_fw(project_name, fw_version)
            
            if not matched_project:
                # 獲取該專案的所有 FW 版本，提供建議
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
            
            logger.info(f"FW 版本匹配成功: {project_name} + {fw_version} -> {matched_fw}")
            
            # Step 2: 獲取測試摘要
            test_summary = self.api_client.get_project_test_summary(project_uid)
            
            if not test_summary:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試資料"
                )
            
            # Step 3: 獲取支援的容量列表
            supported_capacities = test_summary.get('capacities', [])
            
            if not supported_capacities:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"專案 '{project_name}' FW '{matched_fw}' 沒有容量測試資料"
                )
            
            # Step 4: 計算每個容量的測試統計
            capacity_stats = self._calculate_capacity_stats(test_summary, supported_capacities)
            
            # Step 5: 判斷未支援的容量
            unsupported_capacities = [
                cap for cap in ALL_POSSIBLE_CAPACITIES 
                if cap not in supported_capacities
            ]
            
            # Step 6: 格式化回應
            message = self._format_response(
                project_name=project_name,
                fw_version=matched_fw,
                project=matched_project,
                supported_capacities=supported_capacities,
                unsupported_capacities=unsupported_capacities,
                capacity_stats=capacity_stats
            )
            
            return QueryResult.success(
                data={
                    'projectName': project_name,
                    'fwVersion': matched_fw,
                    'customer': matched_project.get('customer', ''),
                    'controller': matched_project.get('controller', ''),
                    'supportedCapacities': supported_capacities,
                    'unsupportedCapacities': unsupported_capacities,
                    'capacityStats': capacity_stats
                },
                count=len(supported_capacities),
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_uid': project_uid,
                    'fw_version_matched': matched_fw,
                    'supported_count': len(supported_capacities),
                    'unsupported_count': len(unsupported_capacities)
                }
            )
            
        except Exception as e:
            logger.error(f"支援容量查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _find_project_by_fw(self, project_name: str, fw_version: str) -> Optional[Dict[str, Any]]:
        """
        根據專案名稱和 FW 版本找到對應的專案
        
        匹配策略：
        1. projectName 精確匹配 + fw 精確匹配
        2. projectName 精確匹配 + fw 包含匹配
        3. projectName 模糊匹配 + fw 精確/包含匹配
        
        Args:
            project_name: 專案名稱
            fw_version: FW 版本
            
        Returns:
            匹配的專案資料，如果找不到則返回 None
        """
        projects = self.api_client.get_all_projects()
        
        if not projects:
            logger.warning("無法獲取專案列表")
            return None
        
        project_name_lower = project_name.lower()
        fw_version_lower = fw_version.lower()
        
        # 第一輪：projectName 精確匹配
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
        
        logger.warning(f"找不到匹配: project_name={project_name}, fw_version={fw_version}")
        return None
    
    def _find_fw_match(self, projects: List[Dict[str, Any]], fw_version_lower: str) -> Optional[Dict[str, Any]]:
        """
        在專案列表中找到 FW 版本匹配的專案
        
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
        
        Args:
            fw_string: FW 版本字串
            
        Returns:
            提取的版本號列表
        """
        versions = []
        
        # 模式：提取 [XXX] 中的內容
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
    
    def _calculate_capacity_stats(self, test_summary: Dict[str, Any], 
                                   capacities: List[str]) -> Dict[str, Dict]:
        """
        計算每個容量的測試統計
        
        Args:
            test_summary: API 返回的測試摘要
            capacities: 支援的容量列表
            
        Returns:
            Dict: 每個容量的統計資料
        """
        categories = test_summary.get('categories', [])
        
        stats = {}
        for cap_name in capacities:
            cap_pass = 0
            cap_fail = 0
            
            for cat in categories:
                results_by_cap = cat.get('results_by_capacity', {})
                cap_results = results_by_cap.get(cap_name, {})
                cap_pass += cap_results.get('pass', 0)
                cap_fail += cap_results.get('fail', 0)
            
            total = cap_pass + cap_fail
            pass_rate = (cap_pass / total * 100) if total > 0 else 0
            
            stats[cap_name] = {
                'pass': cap_pass,
                'fail': cap_fail,
                'total': total,
                'pass_rate': round(pass_rate, 1)
            }
        
        return stats
    
    def _format_response(self, project_name: str, fw_version: str,
                         project: Dict[str, Any],
                         supported_capacities: List[str],
                         unsupported_capacities: List[str],
                         capacity_stats: Dict[str, Dict]) -> str:
        """
        格式化回應訊息
        
        Args:
            project_name: 專案名稱
            fw_version: FW 版本
            project: 專案資料
            supported_capacities: 支援的容量列表
            unsupported_capacities: 未支援的容量列表
            capacity_stats: 容量統計資料
            
        Returns:
            str: Markdown 格式的回應
        """
        customer = project.get('customer', '')
        controller = project.get('controller', '')
        
        lines = [
            f"## 💾 {project_name} FW {fw_version} 支援容量",
            "",
            f"**客戶**：{customer} | **控制器**：{controller}",
            "",
            f"### ✅ 支援的容量（{len(supported_capacities)} 種）",
            "",
            "| 容量 | 測試項目 | Pass | Fail | 通過率 |",
            "|------|---------|------|------|--------|"
        ]
        
        # 總計統計
        total_items = 0
        total_pass = 0
        total_fail = 0
        
        # 按容量大小排序
        sorted_capacities = self._sort_capacities(supported_capacities)
        
        for cap in sorted_capacities:
            stat = capacity_stats.get(cap, {})
            cap_pass = stat.get('pass', 0)
            cap_fail = stat.get('fail', 0)
            cap_total = stat.get('total', 0)
            pass_rate = stat.get('pass_rate', 0)
            
            total_items += cap_total
            total_pass += cap_pass
            total_fail += cap_fail
            
            # 狀態標記
            if cap_fail == 0 and cap_pass > 0:
                status = "✅"
            elif cap_fail > 0:
                status = "⚠️"
            else:
                status = "🔄"
            
            lines.append(f"| {status} {cap} | {cap_total} | {cap_pass} | {cap_fail} | {pass_rate}% |")
        
        lines.append("")
        
        # 摘要統計
        overall_pass_rate = (total_pass / total_items * 100) if total_items > 0 else 0
        
        lines.extend([
            "### 📊 容量測試摘要",
            "",
            f"- **支援容量數**：{len(supported_capacities)} 種",
            f"- **總測試項目**：{total_items} 項",
            f"- **整體通過率**：{overall_pass_rate:.1f}%",
        ])
        
        return "\n".join(lines)
    
    def _sort_capacities(self, capacities: List[str]) -> List[str]:
        """
        按容量大小排序
        
        Args:
            capacities: 容量列表（如 ['512GB', '1024GB', '256GB']）
            
        Returns:
            排序後的容量列表
        """
        def extract_size(cap: str) -> int:
            """從容量字串提取數字"""
            match = re.search(r'(\d+)', cap)
            return int(match.group(1)) if match else 0
        
        return sorted(capacities, key=extract_size)
