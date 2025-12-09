"""
ListSubVersionsHandler - 列出專案所有 Sub Version（容量版本）
=============================================================

處理 Phase 9 Sub Version 查詢意圖：
- list_sub_versions: 列出專案所有的 Sub Version（如 AA, AB, AC, AD）

功能：
- 獲取專案下所有 FW 版本
- 從中提取唯一的 Sub Version
- 統計每個 Sub Version 下的 FW 數量
- 格式化輸出供用戶了解專案的容量版本分布

SubVersion 說明：
- AA = 512GB
- AB = 1024GB / 1TB
- AC = 2048GB / 2TB
- AD = 4096GB / 4TB

作者：AI Platform Team
創建日期：2025-12-09
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


# Sub Version 到容量的對應表
SUB_VERSION_CAPACITY_MAP = {
    'AA': '512GB',
    'AB': '1024GB (1TB)',
    'AC': '2048GB (2TB)',
    'AD': '4096GB (4TB)',
}


class ListSubVersionsHandler(BaseHandler):
    """
    列出專案 Sub Version 處理器
    
    支援的意圖：
    - list_sub_versions: 列出專案所有的 Sub Version
    
    功能：
    1. 獲取專案下所有 FW 版本
    2. 提取每個 FW 的 Sub Version 資訊
    3. 統計每個 Sub Version 下的 FW 數量
    4. 格式化輸出
    """
    
    handler_name = "list_sub_versions_handler"
    supported_intent = "list_sub_versions"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行列出 Sub Version
        
        Args:
            parameters: {
                "project_name": "Springsteen"
            }
            
        Returns:
            QueryResult: 包含 Sub Version 列表
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        
        try:
            # Step 1: 獲取所有專案列表
            all_projects = self.api_client.get_all_projects(flatten=True)
            
            if not all_projects:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # Step 2: 篩選匹配專案名稱的專案
            project_name_lower = project_name.lower()
            matching_projects = [
                p for p in all_projects
                if project_name_lower in p.get('projectName', '').lower()
            ]
            
            if not matching_projects:
                return QueryResult.error(
                    f"找不到專案：{project_name}",
                    self.handler_name,
                    parameters
                )
            
            # Step 3: 提取 Sub Version 資訊
            sub_versions = self._extract_sub_versions(matching_projects)
            
            if not sub_versions:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"專案 {project_name} 目前沒有 Sub Version 資訊"
                )
            
            # Step 4: 格式化回應
            message = self._format_response(project_name, sub_versions)
            
            # 提取第一個專案的基本資訊
            first_project = matching_projects[0]
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'sub_versions': sub_versions,
                    'total_sub_versions': len(sub_versions)
                },
                count=len(sub_versions),
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': first_project.get('projectName'),
                    'customer': first_project.get('customer'),
                    'controller': first_project.get('controller'),
                    'total_fw_versions': len(matching_projects)
                }
            )
            
        except Exception as e:
            logger.error(f"列出 Sub Version 錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _extract_sub_versions(self, projects: List[Dict]) -> List[Dict]:
        """
        從專案列表中提取 Sub Version 資訊
        
        SAF 資料結構中，Sub Version 可能來自：
        1. 專案名稱中的後綴（如 Springsteen_AA）
        2. subVersion 欄位
        3. fw 欄位中的特定格式
        
        Args:
            projects: 專案列表
            
        Returns:
            Sub Version 資訊列表
        """
        sub_version_stats = {}
        
        for project in projects:
            # 嘗試從多個可能的來源提取 Sub Version
            sv = self._extract_sv_from_project(project)
            
            if sv:
                if sv not in sub_version_stats:
                    sub_version_stats[sv] = {
                        'sub_version': sv,
                        'capacity': SUB_VERSION_CAPACITY_MAP.get(sv, 'Unknown'),
                        'fw_count': 0,
                        'fw_list': [],
                        'latest_fw': None
                    }
                
                fw_version = project.get('fw', project.get('projectName', 'N/A'))
                sub_version_stats[sv]['fw_count'] += 1
                sub_version_stats[sv]['fw_list'].append(fw_version)
                
                # 記錄最新的 FW（假設列表已按時間排序）
                if sub_version_stats[sv]['latest_fw'] is None:
                    sub_version_stats[sv]['latest_fw'] = fw_version
        
        # 轉換為列表並排序
        result = list(sub_version_stats.values())
        # 按 Sub Version 代碼排序 (AA, AB, AC, AD)
        result.sort(key=lambda x: x['sub_version'])
        
        return result
    
    def _extract_sv_from_project(self, project: Dict) -> Optional[str]:
        """
        從單個專案中提取 Sub Version
        
        嘗試多種方式提取：
        1. subVersion 欄位
        2. 專案名稱中的後綴（_AA, _AB 等）
        3. fw 欄位中的模式
        
        Args:
            project: 專案資料
            
        Returns:
            Sub Version 代碼（AA/AB/AC/AD），或 None
        """
        import re
        
        # 方式 1：直接從 subVersion 欄位獲取
        sv = project.get('subVersion') or project.get('sub_version')
        if sv and sv.upper() in ['AA', 'AB', 'AC', 'AD']:
            return sv.upper()
        
        # 方式 2：從專案名稱中提取（如 Springsteen_AA）
        project_name = project.get('projectName', '')
        sv_match = re.search(r'[_\-](A[ABCD])$', project_name, re.IGNORECASE)
        if sv_match:
            return sv_match.group(1).upper()
        
        # 方式 3：從 projectUid 或其他欄位提取
        project_uid = project.get('projectUid', '')
        sv_match = re.search(r'[_\-](A[ABCD])[_\-]', project_uid, re.IGNORECASE)
        if sv_match:
            return sv_match.group(1).upper()
        
        # 方式 4：嘗試從容量欄位推斷
        capacity = project.get('capacity', '')
        if capacity:
            capacity_to_sv = {
                '512': 'AA', '512GB': 'AA',
                '1024': 'AB', '1024GB': 'AB', '1TB': 'AB',
                '2048': 'AC', '2048GB': 'AC', '2TB': 'AC',
                '4096': 'AD', '4096GB': 'AD', '4TB': 'AD',
            }
            for cap, sv in capacity_to_sv.items():
                if cap.upper() in str(capacity).upper():
                    return sv
        
        return None
    
    def _format_response(self, project_name: str, sub_versions: List[Dict]) -> str:
        """
        格式化回應訊息
        
        Args:
            project_name: 專案名稱
            sub_versions: Sub Version 列表
            
        Returns:
            格式化的回應字串
        """
        lines = [
            f"📋 **{project_name}** 專案的 Sub Version（容量版本）列表：",
            ""
        ]
        
        # 建立表格
        lines.append("| Sub Version | 容量 | FW 版本數 | 最新 FW |")
        lines.append("|-------------|------|-----------|---------|")
        
        total_fw = 0
        for sv in sub_versions:
            sv_code = sv['sub_version']
            capacity = sv['capacity']
            fw_count = sv['fw_count']
            latest_fw = sv['latest_fw'] or 'N/A'
            
            lines.append(f"| {sv_code} | {capacity} | {fw_count} 個 | {latest_fw} |")
            total_fw += fw_count
        
        lines.append("")
        lines.append(f"📊 **統計**：共 {len(sub_versions)} 個 Sub Version，{total_fw} 個 FW 版本")
        lines.append("")
        lines.append(f"💡 **提示**：可以使用「{project_name} AC 有哪些 FW」查詢特定容量版本的 FW 列表")
        
        return "\n".join(lines)
