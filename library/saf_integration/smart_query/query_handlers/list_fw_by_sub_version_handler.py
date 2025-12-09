"""
ListFWBySubVersionHandler - 列出特定 Sub Version 的 FW 版本
============================================================

處理 Phase 9 Sub Version 查詢意圖：
- list_fw_by_sub_version: 列出專案特定 Sub Version 下的所有 FW 版本

功能：
- 接收專案名稱和 Sub Version（如 AA, AB, AC, AD）
- 過濾出該 Sub Version 下的所有 FW 版本
- 可選：獲取每個 FW 的統計資訊

SubVersion 說明：
- AA = 512GB
- AB = 1024GB / 1TB
- AC = 2048GB / 2TB
- AD = 4096GB / 4TB

作者：AI Platform Team
創建日期：2025-12-09
"""

import logging
import re
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


# Sub Version 到容量的對應表
SUB_VERSION_CAPACITY_MAP = {
    'AA': '512GB',
    'AB': '1024GB (1TB)',
    'AC': '2048GB (2TB)',
    'AD': '4096GB (4TB)',
}

# 容量到 Sub Version 的反向對應
CAPACITY_TO_SUB_VERSION = {
    '512GB': 'AA', '512G': 'AA', '512': 'AA',
    '1024GB': 'AB', '1024G': 'AB', '1024': 'AB', '1TB': 'AB', '1T': 'AB',
    '2048GB': 'AC', '2048G': 'AC', '2048': 'AC', '2TB': 'AC', '2T': 'AC',
    '4096GB': 'AD', '4096G': 'AD', '4096': 'AD', '4TB': 'AD', '4T': 'AD',
}

# 預設配置
DEFAULT_MAX_VERSIONS = 20
MAX_PARALLEL_REQUESTS = 5


class ListFWBySubVersionHandler(BaseHandler):
    """
    列出特定 Sub Version 的 FW 版本處理器
    
    支援的意圖：
    - list_fw_by_sub_version: 列出專案特定 Sub Version 的 FW 版本
    
    功能：
    1. 接收專案名稱和 Sub Version
    2. 過濾出匹配的 FW 版本
    3. 可選獲取統計資訊
    4. 格式化輸出
    """
    
    handler_name = "list_fw_by_sub_version_handler"
    supported_intent = "list_fw_by_sub_version"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行列出特定 Sub Version 的 FW 版本
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "sub_version": "AC",
                "include_stats": False  # 可選
            }
            
        Returns:
            QueryResult: 包含 FW 版本列表
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name', 'sub_version']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        sub_version = parameters.get('sub_version')
        include_stats = parameters.get('include_stats', False)
        max_versions = parameters.get('max_versions', DEFAULT_MAX_VERSIONS)
        
        # 標準化 Sub Version（處理容量描述轉換）
        normalized_sv = self._normalize_sub_version(sub_version)
        if not normalized_sv:
            return QueryResult.error(
                f"無效的 Sub Version：{sub_version}。有效值為 AA, AB, AC, AD 或對應容量（512GB, 1TB, 2TB, 4TB）",
                self.handler_name,
                parameters
            )
        
        try:
            # Step 1: 獲取所有專案列表
            all_projects = self.api_client.get_all_projects(flatten=True)
            
            if not all_projects:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # Step 2: 篩選匹配的專案（專案名稱 + Sub Version）
            project_name_lower = project_name.lower()
            matching_projects = []
            
            for p in all_projects:
                # 檢查專案名稱是否匹配
                if project_name_lower not in p.get('projectName', '').lower():
                    continue
                
                # 檢查 Sub Version 是否匹配
                project_sv = self._extract_sv_from_project(p)
                if project_sv and project_sv.upper() == normalized_sv.upper():
                    matching_projects.append(p)
            
            if not matching_projects:
                # 嘗試提供更好的錯誤訊息
                all_matching = [
                    p for p in all_projects
                    if project_name_lower in p.get('projectName', '').lower()
                ]
                
                if not all_matching:
                    return QueryResult.error(
                        f"找不到專案：{project_name}",
                        self.handler_name,
                        parameters
                    )
                else:
                    # 找到專案但沒有該 Sub Version
                    available_svs = set()
                    for p in all_matching:
                        sv = self._extract_sv_from_project(p)
                        if sv:
                            available_svs.add(sv)
                    
                    sv_list = ', '.join(sorted(available_svs)) if available_svs else '無'
                    return QueryResult.error(
                        f"專案 {project_name} 沒有 Sub Version '{normalized_sv}'。可用的 Sub Version：{sv_list}",
                        self.handler_name,
                        parameters
                    )
            
            # Step 3: 按建立時間排序（最新的在前）
            matching_projects.sort(
                key=lambda x: self._get_timestamp(x.get('createdAt')),
                reverse=True
            )
            
            # Step 4: 限制數量
            total_versions = len(matching_projects)
            limited_projects = matching_projects[:max_versions]
            
            # Step 5: 獲取 FW 版本資訊
            if include_stats:
                fw_versions = self._get_versions_with_stats(limited_projects)
            else:
                fw_versions = self._get_versions_basic(limited_projects)
            
            if not fw_versions:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"專案 {project_name} 的 Sub Version {normalized_sv} 目前沒有 FW 版本"
                )
            
            # Step 6: 格式化回應
            capacity = SUB_VERSION_CAPACITY_MAP.get(normalized_sv, 'Unknown')
            message = self._format_response(
                project_name,
                normalized_sv,
                capacity,
                fw_versions,
                total_versions,
                max_versions,
                include_stats
            )
            
            # 提取第一個專案的基本資訊
            first_project = matching_projects[0]
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'sub_version': normalized_sv,
                    'capacity': capacity,
                    'fw_versions': fw_versions,
                    'total_versions': total_versions,
                    'displayed_versions': len(fw_versions)
                },
                count=len(fw_versions),
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': first_project.get('projectName'),
                    'customer': first_project.get('customer'),
                    'controller': first_project.get('controller'),
                    'sub_version': normalized_sv,
                    'capacity': capacity,
                    'total_available': total_versions,
                    'include_stats': include_stats
                }
            )
            
        except Exception as e:
            logger.error(f"列出 FW by Sub Version 錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _normalize_sub_version(self, sv: str) -> Optional[str]:
        """
        標準化 Sub Version
        
        支援輸入：
        - 直接代碼：AA, AB, AC, AD
        - 容量描述：512GB, 1TB, 2TB, 4TB 等
        
        Args:
            sv: 用戶輸入的 Sub Version
            
        Returns:
            標準化的 Sub Version 代碼（AA/AB/AC/AD），或 None
        """
        sv_upper = sv.upper().strip()
        
        # 直接是 Sub Version 代碼
        if sv_upper in ['AA', 'AB', 'AC', 'AD']:
            return sv_upper
        
        # 嘗試從容量轉換
        return CAPACITY_TO_SUB_VERSION.get(sv_upper)
    
    def _extract_sv_from_project(self, project: Dict) -> Optional[str]:
        """
        從單個專案中提取 Sub Version
        
        Args:
            project: 專案資料
            
        Returns:
            Sub Version 代碼（AA/AB/AC/AD），或 None
        """
        # 方式 1：直接從 subVersion 欄位獲取
        sv = project.get('subVersion') or project.get('sub_version')
        if sv and sv.upper() in ['AA', 'AB', 'AC', 'AD']:
            return sv.upper()
        
        # 方式 2：從專案名稱中提取（如 Springsteen_AA）
        project_name = project.get('projectName', '')
        sv_match = re.search(r'[_\-](A[ABCD])$', project_name, re.IGNORECASE)
        if sv_match:
            return sv_match.group(1).upper()
        
        # 方式 3：從 projectUid 中提取
        project_uid = project.get('projectUid', '')
        sv_match = re.search(r'[_\-](A[ABCD])[_\-]', project_uid, re.IGNORECASE)
        if sv_match:
            return sv_match.group(1).upper()
        
        # 方式 4：從容量欄位推斷
        capacity = project.get('capacity', '')
        if capacity:
            for cap, sv in CAPACITY_TO_SUB_VERSION.items():
                if cap.upper() in str(capacity).upper():
                    return sv
        
        return None
    
    def _get_timestamp(self, created_at: Any) -> int:
        """從 createdAt 欄位提取 Unix timestamp"""
        try:
            if isinstance(created_at, dict):
                seconds = created_at.get('seconds', {})
                if isinstance(seconds, dict):
                    return seconds.get('low', 0)
                elif isinstance(seconds, int):
                    return seconds
                return 0
            elif isinstance(created_at, str):
                from datetime import datetime
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                return int(dt.timestamp())
            elif isinstance(created_at, (int, float)):
                return int(created_at)
            else:
                return 0
        except Exception:
            return 0
    
    def _format_timestamp(self, created_at: Any) -> str:
        """格式化 createdAt 為可讀字串"""
        try:
            timestamp = self._get_timestamp(created_at)
            if timestamp > 0:
                from datetime import datetime
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d')
            return 'N/A'
        except Exception:
            return 'N/A'
    
    def _get_versions_basic(self, projects: List[Dict]) -> List[Dict]:
        """
        獲取 FW 版本基本資訊（快速，不需要額外 API 調用）
        """
        fw_versions = []
        
        for project in projects:
            fw_version = project.get('fw', project.get('projectName', 'N/A'))
            created_at_raw = project.get('createdAt', '')
            
            fw_info = {
                'fw_version': fw_version,
                'fw': fw_version,
                'project_uid': project.get('projectUid'),
                'project_name': project.get('projectName', ''),
                'customer': project.get('customer', ''),
                'controller': project.get('controller', ''),
                'created_at': self._format_timestamp(created_at_raw),
                'created_at_raw': created_at_raw,
                'has_stats': False
            }
            
            fw_versions.append(fw_info)
        
        return fw_versions
    
    def _get_versions_with_stats(self, projects: List[Dict]) -> List[Dict]:
        """
        獲取 FW 版本詳細統計資訊（較慢，需要並行 API 調用）
        """
        fw_versions = []
        
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as executor:
            future_to_project = {
                executor.submit(self._get_fw_version_info, project): project
                for project in projects
            }
            
            for future in as_completed(future_to_project):
                try:
                    fw_info = future.result()
                    if fw_info:
                        fw_versions.append(fw_info)
                except Exception as e:
                    project = future_to_project[future]
                    logger.warning(f"獲取 FW {project.get('fw')} 統計失敗: {str(e)}")
        
        # 按建立時間排序
        fw_versions.sort(
            key=lambda x: self._get_timestamp(x.get('created_at_raw')),
            reverse=True
        )
        
        return fw_versions
    
    def _get_fw_version_info(self, project: Dict) -> Optional[Dict]:
        """獲取 FW 版本的統計資訊"""
        try:
            project_uid = project.get('projectUid')
            fw_version = project.get('fw', project.get('projectName', 'N/A'))
            created_at_raw = project.get('createdAt', '')
            created_at_formatted = self._format_timestamp(created_at_raw)
            
            # 嘗試獲取 firmware-summary
            stats = self.api_client.get_firmware_summary(project_uid)
            
            if stats:
                overview = stats.get('overview', {})
                sample_stats = stats.get('sample_stats', {})
                test_item_stats = stats.get('test_item_stats', {})
                
                return {
                    'fw_version': fw_version,
                    'fw': fw_version,
                    'project_uid': project_uid,
                    'project_name': project.get('projectName', ''),
                    'customer': project.get('customer', ''),
                    'controller': project.get('controller', ''),
                    'pass': overview.get('total_pass', 0),
                    'fail': overview.get('total_fail', 0),
                    'completion_rate': overview.get('completion_rate', 0),
                    'pass_rate': overview.get('pass_rate', 0),
                    'execution_rate': test_item_stats.get('execution_rate', 0),
                    'samples_used': sample_stats.get('samples_used', 0),
                    'total_samples': sample_stats.get('total_samples', 0),
                    'created_at': created_at_formatted,
                    'created_at_raw': created_at_raw,
                    'has_stats': True
                }
            else:
                return {
                    'fw_version': fw_version,
                    'fw': fw_version,
                    'project_uid': project_uid,
                    'project_name': project.get('projectName', ''),
                    'customer': project.get('customer', ''),
                    'controller': project.get('controller', ''),
                    'pass': 0,
                    'fail': 0,
                    'completion_rate': 0,
                    'pass_rate': 0,
                    'execution_rate': 0,
                    'samples_used': 0,
                    'total_samples': 0,
                    'created_at': created_at_formatted,
                    'created_at_raw': created_at_raw,
                    'has_stats': False
                }
                
        except Exception as e:
            logger.warning(f"獲取 FW {project.get('fw')} 統計失敗: {str(e)}")
            return None
    
    def _format_response(
        self,
        project_name: str,
        sub_version: str,
        capacity: str,
        fw_versions: List[Dict],
        total_versions: int,
        max_versions: int,
        include_stats: bool
    ) -> str:
        """
        格式化回應訊息
        """
        lines = [
            f"📋 **{project_name}** 專案 **{sub_version}** ({capacity}) 版本的 FW 列表：",
            ""
        ]
        
        # 根據是否包含統計資訊選擇表格格式
        if include_stats:
            lines.append("| FW 版本 | 建立日期 | Pass Rate | 完成率 |")
            lines.append("|---------|----------|-----------|--------|")
            
            for fw in fw_versions:
                fw_version = fw['fw_version']
                created_at = fw['created_at']
                
                if fw['has_stats']:
                    pass_rate = f"{fw['pass_rate']:.1f}%"
                    completion_rate = f"{fw['completion_rate']:.1f}%"
                else:
                    pass_rate = 'N/A'
                    completion_rate = 'N/A'
                
                lines.append(f"| {fw_version} | {created_at} | {pass_rate} | {completion_rate} |")
        else:
            lines.append("| # | FW 版本 | 建立日期 |")
            lines.append("|---|---------|----------|")
            
            for idx, fw in enumerate(fw_versions, 1):
                fw_version = fw['fw_version']
                created_at = fw['created_at']
                lines.append(f"| {idx} | {fw_version} | {created_at} |")
        
        # 添加統計和提示
        lines.append("")
        
        if total_versions > max_versions:
            lines.append(f"📊 **統計**：顯示最新 {len(fw_versions)} 個，共 {total_versions} 個 FW 版本")
        else:
            lines.append(f"📊 **統計**：共 {len(fw_versions)} 個 FW 版本")
        
        lines.append("")
        
        # 根據情況提供不同的提示
        if not include_stats:
            lines.append(f"💡 **提示**：")
            lines.append(f"  - 查詢特定 FW 的詳細統計：「{project_name} FW {fw_versions[0]['fw_version'] if fw_versions else 'XXX'} 的詳細統計」")
            lines.append(f"  - 比較最新版本差異：「{project_name} 最新 FW 比較」")
        else:
            lines.append(f"💡 **提示**：可以使用「{project_name} FW XXX 的詳細統計」查詢特定版本的完整資訊")
        
        return "\n".join(lines)
