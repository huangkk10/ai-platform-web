"""
CompareLatestFWHandler - 自動比較最新兩個 FW 版本
================================================

處理 Phase 5.2.1 自動比較最新版本意圖：
- compare_latest_fw: 自動選擇最新兩個 FW 版本進行比較

功能：
- 獲取專案下所有子專案（FW 版本）
- 自動選擇最新兩個版本
- 複用 CompareFWVersionsHandler 進行比較

作者：AI Platform Team
創建日期：2025-12-07
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult
from .compare_fw_versions_handler import CompareFWVersionsHandler
from .list_fw_versions_handler import ListFWVersionsHandler

logger = logging.getLogger(__name__)


class CompareLatestFWHandler(BaseHandler):
    """
    自動比較最新 FW 版本處理器
    
    支援的意圖：
    - compare_latest_fw: 自動比較最新兩個 FW 版本
    
    功能：
    1. 獲取專案下所有 FW 版本（複用 ListFWVersionsHandler）
    2. 按完成率/建立時間排序，選擇最新兩個
    3. 複用 CompareFWVersionsHandler 進行比較
    """
    
    handler_name = "compare_latest_fw_handler"
    supported_intent = "compare_latest_fw"
    
    def __init__(self):
        """初始化 Handler"""
        super().__init__()
        # 複用 ListFWVersionsHandler 獲取版本列表
        self.list_handler = ListFWVersionsHandler()
        # 複用 CompareFWVersionsHandler 進行比較
        self.compare_handler = CompareFWVersionsHandler()
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行自動比較最新 FW 版本
        
        Args:
            parameters: {
                "project_name": "DEMETER"
            }
            
        Returns:
            QueryResult: 包含比較結果
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
            # Step 1: 獲取 FW 版本列表（使用 max_versions=10 獲取最新 10 個版本）
            # 快速模式不包含統計資訊，但我們只需要版本名稱
            list_result = self.list_handler.execute({
                'project_name': project_name,
                'max_versions': 10,  # 只需要最新的 10 個版本
                'include_stats': False  # 快速模式
            })
            
            if not list_result.is_success():
                return QueryResult.error(
                    f"無法獲取 {project_name} 的 FW 版本列表：{list_result.error_message}",
                    self.handler_name,
                    parameters
                )
            
            fw_versions = list_result.data.get('fw_versions', [])
            total_versions = list_result.data.get('total_versions', 0)
            
            # Step 2: 檢查是否有足夠版本進行比較
            if len(fw_versions) < 2:
                return self._handle_insufficient_versions(project_name, fw_versions, parameters)
            
            # Step 3: 選擇最新兩個版本（版本已按建立時間排序）
            selected = self._select_latest_versions(fw_versions)
            
            fw_version_1 = selected[0].get('fw_version')
            fw_version_2 = selected[1].get('fw_version')
            
            # Step 4: 執行比較
            compare_result = self.compare_handler.execute({
                'project_name': project_name,
                'fw_version_1': fw_version_1,
                'fw_version_2': fw_version_2
            })
            
            # Step 5: 在回應中加入自動選擇的說明
            if compare_result.is_success():
                original_message = compare_result.message
                selection_note = self._format_selection_note(
                    fw_version_1, fw_version_2, 
                    selected[0], selected[1],
                    total_versions
                )
                compare_result.message = selection_note + "\n\n" + original_message
                
                # 更新 metadata
                compare_result.metadata['auto_selected'] = True
                compare_result.metadata['total_versions'] = total_versions
                compare_result.metadata['selection_method'] = 'latest_two'
            
            return compare_result
            
        except Exception as e:
            logger.error(f"自動比較最新 FW 版本錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _select_latest_versions(self, fw_versions: List[Dict]) -> List[Dict]:
        """
        選擇最新的兩個版本
        
        選擇策略：
        - 版本已按建立時間降序排列（最新的在前）
        - 直接取前兩個版本
        
        Args:
            fw_versions: 已按建立時間降序排列的版本列表
            
        Returns:
            最新的兩個版本
        """
        # 版本已按建立時間排序，直接取前兩個
        return fw_versions[:2]
    
    def _handle_insufficient_versions(self, project_name: str, 
                                       fw_versions: List[Dict],
                                       parameters: Dict) -> QueryResult:
        """
        處理版本數量不足的情況
        """
        if len(fw_versions) == 0:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 **{project_name}** 目前沒有任何 FW 版本，無法進行比較。"
            )
        
        # 只有一個版本
        version = fw_versions[0]
        message_lines = [
            f"## ⚠️ 無法比較",
            "",
            f"專案 **{project_name}** 目前只有 **1** 個 FW 版本：",
            "",
            f"| FW 版本 | 建立時間 |",
            f"|---------|----------|",
            f"| {version.get('fw_version')} | {version.get('created_at', 'N/A')} |",
            "",
            "需要至少兩個 FW 版本才能進行比較。"
        ]
        
        return QueryResult.no_results(
            query_type=self.handler_name,
            parameters=parameters,
            message="\n".join(message_lines)
        )
    
    def _format_selection_note(self, fw_version_1: str, fw_version_2: str,
                               info_1: Dict, info_2: Dict,
                               total_versions: int) -> str:
        """
        格式化自動選擇的說明
        """
        lines = [
            f"🤖 **自動選擇比較**：從 {total_versions} 個 FW 版本中，"
            f"選擇了最新的兩個版本進行比較：",
            "",
            f"- **{fw_version_1}**：建立於 {info_1.get('created_at', 'N/A')}",
            f"- **{fw_version_2}**：建立於 {info_2.get('created_at', 'N/A')}",
            "",
            "---"
        ]
        return "\n".join(lines)
