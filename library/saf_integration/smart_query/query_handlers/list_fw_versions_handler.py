"""
ListFWVersionsHandler - 列出專案可比較的 FW 版本
=================================================

處理 Phase 5.2.2 列出 FW 版本意圖：
- list_fw_versions: 列出專案中所有可比較的 FW 版本

功能：
- 獲取專案下所有子專案（FW 版本）
- 取得每個版本的基本資訊（從專案列表取得，不需要額外 API 調用）
- 按照建立時間排序

優化策略：
- 預設只返回最新 20 個版本
- 基本資訊直接從專案列表取得，不需要額外 API 調用
- 只有在需要詳細統計時才調用 firmware-summary API

作者：AI Platform Team
創建日期：2025-12-07
"""

import logging
from typing import Dict, Any, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)

# 預設配置
DEFAULT_MAX_VERSIONS = 20  # 預設最多返回 20 個版本
MAX_PARALLEL_REQUESTS = 5  # 並行 API 請求數


class ListFWVersionsHandler(BaseHandler):
    """
    列出專案 FW 版本處理器
    
    支援的意圖：
    - list_fw_versions: 列出專案可比較的 FW 版本
    
    功能：
    1. 獲取專案下所有子專案（FW 版本）
    2. 取得每個版本的基本資訊
    3. 格式化輸出供用戶選擇
    
    效能優化：
    - 預設只返回最新 20 個版本，避免 API 調用過多
    - 基本資訊從專案列表獲取，不需要額外 API 調用
    - 可選：使用 include_stats=True 獲取詳細統計（較慢）
    """
    
    handler_name = "list_fw_versions_handler"
    supported_intent = "list_fw_versions"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行列出 FW 版本
        
        Args:
            parameters: {
                "project_name": "DEMETER",
                "max_versions": 20,      # 可選，預設 20
                "include_stats": False   # 可選，是否獲取詳細統計（較慢）
            }
            
        Returns:
            QueryResult: 包含 FW 版本列表
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
        max_versions = parameters.get('max_versions', DEFAULT_MAX_VERSIONS)
        include_stats = parameters.get('include_stats', False)
        
        try:
            # Step 1: 獲取所有專案列表（使用 get_all_projects 以支援分頁）
            all_projects = self.api_client.get_all_projects(flatten=True)
            
            if not all_projects:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # Step 2: 找到所有匹配專案名稱的專案（作為 FW 版本）
            # SAF 資料結構：每個 FW 版本是獨立的頂層專案，projectName 相同但 fw 欄位不同
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
            
            # Step 3: 按建立時間排序（最新的在前）
            # 注意：createdAt 是一個 dict，格式為 {'seconds': {'low': timestamp, ...}}
            matching_projects.sort(
                key=lambda x: self._get_timestamp(x.get('createdAt')),
                reverse=True
            )
            
            # Step 4: 限制數量
            total_versions = len(matching_projects)
            limited_projects = matching_projects[:max_versions]
            
            # Step 5: 獲取 FW 版本資訊
            if include_stats:
                # 獲取詳細統計（較慢，需要額外 API 調用）
                fw_versions = self._get_versions_with_stats(limited_projects)
            else:
                # 只獲取基本資訊（快速，不需要額外 API 調用）
                fw_versions = self._get_versions_basic(limited_projects)
            
            if not fw_versions:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"專案 {project_name} 目前沒有任何 FW 版本資訊"
                )
            
            # Step 6: 格式化回應訊息
            message = self._format_response(
                project_name, 
                fw_versions, 
                total_versions,
                max_versions,
                include_stats
            )
            
            # 提取第一個專案的基本資訊作為代表
            first_project = matching_projects[0]
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
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
                    'total_available': total_versions,
                    'include_stats': include_stats
                }
            )
            
        except Exception as e:
            logger.error(f"列出 FW 版本錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _get_timestamp(self, created_at: Any) -> int:
        """
        從 createdAt 欄位提取 Unix timestamp
        
        SAF API 的 createdAt 格式可能是：
        1. dict: {'seconds': {'low': timestamp, 'high': 0, 'unsigned': False}}
        2. str: ISO 格式字串 '2025-01-01T00:00:00Z'
        3. int: Unix timestamp
        
        Args:
            created_at: 建立時間資料
            
        Returns:
            Unix timestamp (int)，如果解析失敗返回 0
        """
        try:
            if isinstance(created_at, dict):
                # 嘗試從 dict 提取 timestamp
                seconds = created_at.get('seconds', {})
                if isinstance(seconds, dict):
                    return seconds.get('low', 0)
                elif isinstance(seconds, int):
                    return seconds
                return 0
            elif isinstance(created_at, str):
                # ISO 格式字串
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
        """
        格式化 createdAt 為可讀字串
        
        Args:
            created_at: 建立時間資料
            
        Returns:
            格式化的日期字串 (YYYY-MM-DD) 或 'N/A'
        """
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
        
        Args:
            projects: 專案列表
            
        Returns:
            FW 版本資訊列表
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
                # 基本模式不包含統計資訊
                'has_stats': False
            }
            
            fw_versions.append(fw_info)
        
        return fw_versions
    
    def _get_versions_with_stats(self, projects: List[Dict]) -> List[Dict]:
        """
        獲取 FW 版本詳細統計資訊（較慢，需要並行 API 調用）
        
        Args:
            projects: 專案列表
            
        Returns:
            FW 版本資訊列表（含統計）
        """
        fw_versions = []
        
        # 使用 ThreadPoolExecutor 並行獲取統計資訊
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as executor:
            # 提交所有任務
            future_to_project = {
                executor.submit(self._get_fw_version_info, project): project
                for project in projects
            }
            
            # 收集結果
            for future in as_completed(future_to_project):
                try:
                    fw_info = future.result()
                    if fw_info:
                        fw_versions.append(fw_info)
                except Exception as e:
                    project = future_to_project[future]
                    logger.warning(f"獲取 FW {project.get('fw', project.get('projectName'))} 統計失敗: {str(e)}")
        
        # 按建立時間排序（使用原始 timestamp 排序）
        fw_versions.sort(
            key=lambda x: self._get_timestamp(x.get('created_at_raw')),
            reverse=True
        )
        
        return fw_versions
    
    def _get_fw_version_info(self, project: Dict) -> Optional[Dict]:
        """
        獲取 FW 版本的統計資訊
        
        注意: SAF 資料結構
        - 每個 FW 版本是獨立的頂層專案
        - FW 版本名稱存放在 `fw` 欄位
        - projectName 欄位是專案名稱（通常相同）
        """
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
                    'fw': fw_version,  # 別名方便訪問
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
                # 沒有 firmware-summary，返回基本資訊
                return {
                    'fw_version': fw_version,
                    'fw': fw_version,  # 別名方便訪問
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
            logger.warning(f"獲取 FW {project.get('fw', project.get('projectName'))} 統計失敗: {str(e)}")
            return None
    
    def _format_response(self, project_name: str, 
                        fw_versions: List[Dict],
                        total_versions: int,
                        max_versions: int,
                        include_stats: bool) -> str:
        """
        格式化回應訊息
        """
        lines = [
            f"## 📋 {project_name} 專案 FW 版本列表",
            ""
        ]
        
        # 顯示數量資訊
        if total_versions > len(fw_versions):
            lines.append(f"顯示最新 **{len(fw_versions)}** 個版本（共 {total_versions} 個）：")
        else:
            lines.append(f"共找到 **{len(fw_versions)}** 個 FW 版本：")
        
        lines.append("")
        
        # 根據是否有統計資訊選擇表格格式
        if include_stats and fw_versions and fw_versions[0].get('has_stats'):
            # 詳細統計表格
            lines.extend([
                "| # | FW 版本 | 完成率 | Pass | Fail | 樣本使用 |",
                "|---|---------|--------|------|------|----------|"
            ])
            
            for i, fw in enumerate(fw_versions, 1):
                version = fw.get('fw_version', 'N/A')
                completion_rate = fw.get('completion_rate', 0)
                pass_count = fw.get('pass', 0)
                fail_count = fw.get('fail', 0)
                samples = fw.get('samples_used', 0)
                total_samples = fw.get('total_samples', 0)
                
                # 格式化樣本使用
                if total_samples > 0:
                    sample_str = f"{samples}/{total_samples}"
                else:
                    sample_str = "-"
                
                lines.append(
                    f"| {i} | **{version}** | {completion_rate:.1f}% | {pass_count} | {fail_count} | {sample_str} |"
                )
        else:
            # 簡單表格（無統計資訊）
            lines.extend([
                "| # | FW 版本 | 建立時間 |",
                "|---|---------|----------|"
            ])
            
            for i, fw in enumerate(fw_versions, 1):
                version = fw.get('fw_version', 'N/A')
                created_at = fw.get('created_at', 'N/A')
                
                # 格式化時間（只顯示日期部分）
                if created_at and 'T' in created_at:
                    created_at = created_at.split('T')[0]
                
                lines.append(f"| {i} | **{version}** | {created_at} |")
        
        # 添加提示
        lines.extend([
            "",
            "---",
            "",
            "💡 **提示**：",
        ])
        
        if len(fw_versions) >= 2:
            v1 = fw_versions[0].get('fw_version')
            v2 = fw_versions[1].get('fw_version')
            lines.append(
                f"- 您可以問「比較 {project_name} 的 {v1} 和 {v2}」"
            )
            lines.append(
                f"- 或問「{project_name} 最新 FW 比較」自動比較最新兩版本"
            )
        elif len(fw_versions) == 1:
            v1 = fw_versions[0].get('fw_version')
            lines.append(
                f"- 目前只有一個版本 {v1}，無法進行比較"
            )
        
        # 如果還有更多版本，提示用戶
        if total_versions > len(fw_versions):
            lines.append(
                f"- 如需查看更多版本，請問「列出 {project_name} 全部 FW 版本」"
            )
        
        # 如果沒有顯示統計，提示用戶
        if not include_stats:
            lines.append(
                f"- 如需查看詳細統計，請問「列出 {project_name} FW 版本統計」"
            )
        
        return "\n".join(lines)
