"""
TestJobsHandler - 專案 FW 測試工作結果查詢
==========================================

處理 Phase 16 意圖：專案 FW 測試工作結果查詢
- 查詢特定專案特定 FW 版本的完整測試結果

API 端點：POST /api/v1/projects/test-status/search (Phase 19.1 更新)
- 原先使用 /api/v1/projects/test-jobs（舊 API，類別不完整）
- 現改用 /api/v1/projects/test-status/search（新 API，類別完整含 Performance）

特點：
- 支援簡短專案名稱（如 PM9M1）自動對應到完整專案 ID
- 返回完整測試項目列表（含 Category、Item、Status、Capacity 等）
- 包含完整的測試類別（含 Performance (Secondary)）
- 按類別分組統計 Pass/Fail 數量

作者：AI Platform Team
創建日期：2025-12-17
更新日期：2025-12-18 - Phase 19.1: 改用 test-status/search API
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class TestJobsHandler(BaseHandler):
    """
    專案 FW 測試工作結果查詢處理器
    
    支援的意圖：
    - query_project_fw_test_jobs: 查詢專案 FW 的完整測試結果
    
    用戶問法範例：
    - PM9M1 的 HHB0YBC1 測項結果
    - PM9M1 HHB0YBC1 的測試項目結果
    - 查詢 Springsteen GD10YBJD 的測試結果
    """
    
    handler_name = "test_jobs_handler"
    supported_intent = "query_project_fw_test_jobs"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行測試工作結果查詢
        
        Args:
            parameters: {
                "project_name": "PM9M1",
                "fw_version": "HHB0YBC1",
                "test_tool_key": "" (optional)
            }
            
        Returns:
            QueryResult: 包含測試工作結果列表
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
        test_tool_key = parameters.get('test_tool_key', '')
        
        try:
            # Step 1: 找到符合的專案（透過 FW 版本匹配）
            matched_project = self._find_project_by_fw(project_name, fw_version)
            
            if not matched_project:
                return self._handle_project_not_found(project_name, fw_version, parameters)
            
            # 🔑 重要：Test Jobs API 需要使用 projectId（父專案 ID），不是 projectUid
            # SAF 專案結構：
            # - 父專案（如 PM9M1）有 projectId 和 projectUid
            # - 子專案（每個 FW 版本）的 projectId 與父專案相同
            # - Test Jobs API 使用 projectId 來查詢該專案下所有 FW 版本的測試結果
            project_id = matched_project.get('projectId')
            project_uid = matched_project.get('projectUid')  # 保留用於 logging
            matched_fw = matched_project.get('fw', '')
            full_project_name = matched_project.get('projectName', '')
            
            logger.info(
                f"Test Jobs 查詢 - 版本匹配成功: {project_name} + {fw_version} "
                f"-> {full_project_name} / {matched_fw} "
                f"(projectId: {project_id}, projectUid: {project_uid})"
            )
            
            # Step 2: 調用 test-status/search API（Phase 19.1 更新）
            # 改用新 API 以獲取完整的測試類別（包含 Performance）
            test_status_result = self.api_client.search_test_status_by_project_fw(
                project_name=full_project_name,
                fw_version=matched_fw,
                fetch_all=True
            )
            
            if not test_status_result:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試結果"
                )
            
            # 轉換為相容格式
            test_jobs_result = self._convert_test_status_to_jobs(test_status_result)
            
            # Step 3: 格式化回應
            return self._format_test_jobs_response(
                test_jobs=test_jobs_result,
                project_name=project_name,
                fw_version=matched_fw,
                full_project_name=full_project_name,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"Test Jobs 查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _find_project_by_fw(
        self, 
        project_name: str, 
        fw_version: str
    ) -> Optional[Dict[str, Any]]:
        """
        根據專案名稱和 FW 版本找到對應的專案
        
        匹配邏輯：
        1. 專案名稱包含用戶輸入的專案名稱（不區分大小寫）
        2. FW 版本完全匹配（不區分大小寫）
        
        Args:
            project_name: 專案名稱片段（如 PM9M1）
            fw_version: FW 版本（如 HHB0YBC1）
            
        Returns:
            符合條件的專案資訊，如果找不到則返回 None
        """
        # 使用 API client 的輔助方法
        return self.api_client.find_project_uid_by_name_and_fw(project_name, fw_version)
    
    def _get_all_fw_versions(self, project_name: str) -> List[str]:
        """獲取指定專案的所有 FW 版本列表"""
        return self.api_client.get_all_fw_versions_for_project(project_name)
    
    def _convert_test_status_to_jobs(self, test_status_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 test-status/search API 回應轉換為舊 API 相容格式
        
        Phase 19.1 新增：統一資料格式以相容現有的回應生成邏輯
        
        Args:
            test_status_result: 新 API 的回應 {'items': [...], 'total': int, ...}
            
        Returns:
            轉換後的資料 {'test_jobs': [...], 'total': int}
        """
        items = test_status_result.get('items', [])
        test_jobs = []
        
        for item in items:
            # 將 test_status (PASS/FAIL/ONGOING...) 轉換為舊格式 (Pass/Fail)
            status = item.get('test_status', '')
            normalized_status = 'Pass' if status == 'PASS' else ('Fail' if status == 'FAIL' else status)
            
            test_jobs.append({
                'test_job_id': item.get('test_job_id', ''),
                'test_item_name': item.get('test_item', ''),
                'test_category_name': item.get('test_category_name', ''),
                'test_plan_name': item.get('test_plan_name', ''),
                'test_status': normalized_status,
                'sample_id': item.get('sample_id', ''),
                'capacity': item.get('capacity', ''),
                'fw': item.get('fw', ''),
                'platform': item.get('platform', ''),
                'root_id': item.get('root_id', ''),
                # 新 API 特有的欄位
                'start_time': item.get('start_time', ''),
                'end_time': item.get('end_time', ''),
                'duration': item.get('duration', ''),
                'user': item.get('user', ''),
                'os_name': item.get('os_name', ''),
            })
        
        converted_result = {
            'test_jobs': test_jobs,
            'total': len(test_jobs)
        }
        
        logger.info(f"test-status/search API 轉換完成: {len(test_jobs)} 筆測試項目")
        
        return converted_result
    
    def _format_test_jobs_response(
        self,
        test_jobs: Dict[str, Any],
        project_name: str,
        fw_version: str,
        full_project_name: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化測試工作結果回應
        """
        jobs = test_jobs.get('test_jobs', [])
        total = test_jobs.get('total', len(jobs))
        
        if not jobs:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 {project_name} FW {fw_version} 沒有測試結果資料"
            )
        
        # 統計資訊（排除沒有 Category 的資料）
        # Phase 19.1: 過濾空 Category，不納入統計和顯示
        valid_jobs = [j for j in jobs if j.get('test_category_name', '').strip()]
        filtered_count = len(jobs) - len(valid_jobs)
        if filtered_count > 0:
            logger.info(f"過濾 {filtered_count} 筆沒有 Category 的測試項目")
        
        total = len(valid_jobs)
        pass_count = sum(1 for j in valid_jobs if j.get('test_status') == 'Pass')
        fail_count = sum(1 for j in valid_jobs if j.get('test_status') == 'Fail')
        other_count = total - pass_count - fail_count
        
        # 按 Test Category 分組（只處理有 Category 的資料）
        categories = {}
        for job in valid_jobs:
            cat = job.get('test_category_name', '')
            if cat not in categories:
                categories[cat] = {'pass': 0, 'fail': 0, 'other': 0, 'items': []}
            categories[cat]['items'].append(job)
            status = job.get('test_status', '')
            if status == 'Pass':
                categories[cat]['pass'] += 1
            elif status == 'Fail':
                categories[cat]['fail'] += 1
            else:
                categories[cat]['other'] += 1
        
        # 格式化訊息（使用過濾後的 valid_jobs）
        message = self._build_response_message(
            project_name=project_name,
            fw_version=fw_version,
            total=total,
            pass_count=pass_count,
            fail_count=fail_count,
            other_count=other_count,
            categories=categories,
            jobs=valid_jobs
        )
        
        # 構建表格資料（前端可用）
        table_data = [
            {
                'root_id': job.get('root_id', ''),
                'test_category': job.get('test_category_name', ''),
                'test_item': job.get('test_item_name', ''),
                'fw': job.get('fw', ''),
                'capacity': job.get('capacity', ''),
                'sample_id': job.get('sample_id', ''),
                'platform': job.get('platform', ''),
                'test_status': job.get('test_status', ''),
                'tool': ', '.join(job.get('test_tool_key_list', []))
            }
            for job in jobs
        ]
        
        return QueryResult.success(
            data={
                'project_name': project_name,
                'full_project_name': full_project_name,
                'fw_version': fw_version,
                'test_jobs': jobs,
                'total': total,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'other_count': other_count,
                'categories': categories,
                'table': table_data
            },
            count=total,
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'project_name': full_project_name,
                'customer': project.get('customer', ''),
                'controller': project.get('controller', ''),
                'fw': fw_version,
                'intent': 'query_project_fw_test_jobs'
            }
        )
    
    def _build_response_message(
        self,
        project_name: str,
        fw_version: str,
        total: int,
        pass_count: int,
        fail_count: int,
        other_count: int,
        categories: Dict,
        jobs: List[Dict]
    ) -> str:
        """
        構建回應訊息（Markdown + HTML details 摺疊格式）
        
        優化版本：
        - 按 Category 摺疊顯示
        - Capacity 拉平成欄位
        - 移除 Sample 欄位
        """
        
        pass_rate = (pass_count / total * 100) if total > 0 else 0
        
        # 獲取所有 Capacity（動態欄位）
        all_capacities = self._get_all_capacities(jobs)
        
        lines = [
            f"## 🧪 專案 {project_name} - FW {fw_version} 測試結果",
            "",
            f"**總測試項目**: {total} 個  ",
            f"**Pass**: {pass_count} ✅ | **Fail**: {fail_count} ❌ | **其他**: {other_count} | **通過率**: {pass_rate:.1f}%",
            "",
            "---",
            ""
        ]
        
        # 按 Category 生成摺疊區塊
        for cat_name in sorted(categories.keys()):
            cat_data = categories[cat_name]
            cat_total = cat_data['pass'] + cat_data['fail'] + cat_data['other']
            
            # 生成該 Category 的摺疊區塊
            category_block = self._format_category_details(
                category_name=cat_name,
                category_data=cat_data,
                cat_total=cat_total,
                all_capacities=all_capacities
            )
            lines.append(category_block)
        
        return "\n".join(lines)
    
    def _get_all_capacities(self, jobs: List[Dict]) -> List[str]:
        """
        獲取所有出現的 Capacity，按數值排序
        
        Returns:
            排序後的 Capacity 列表，如 ['512GB', '1024GB', '2048GB']
        """
        capacities = set()
        for job in jobs:
            cap = job.get('capacity', '')
            if cap:
                capacities.add(cap)
        
        # 按數值排序（處理 GB 和 TB）
        def sort_key(cap_str: str) -> int:
            try:
                if 'TB' in cap_str.upper():
                    return int(cap_str.upper().replace('TB', '').strip()) * 1000
                else:
                    return int(cap_str.upper().replace('GB', '').strip())
            except:
                return 0
        
        return sorted(capacities, key=sort_key)
    
    def _group_by_test_item(self, jobs: List[Dict]) -> List[Dict]:
        """
        將同一 Test Item 的不同 Capacity 結果合併為一行
        
        Args:
            jobs: 原始測試工作列表
            
        Returns:
            合併後的列表，每個 Test Item 只有一個條目，包含所有 Capacity 的狀態
        """
        grouped = {}
        
        for job in jobs:
            root_id = job.get('root_id', '')
            test_item = job.get('test_item_name', '')
            key = (root_id, test_item)
            
            if key not in grouped:
                grouped[key] = {
                    'root_id': root_id,
                    'test_item': test_item,
                    'capacities': {},
                    'has_fail': False  # 用於排序，Fail 優先
                }
            
            capacity = job.get('capacity', 'Unknown')
            status = job.get('test_status', '')
            grouped[key]['capacities'][capacity] = status
            
            if status == 'Fail':
                grouped[key]['has_fail'] = True
        
        # 轉換為列表並排序（Fail 優先）
        result = list(grouped.values())
        result.sort(key=lambda x: (not x['has_fail'], x['root_id'], x['test_item']))
        
        return result
    
    def _format_category_details(
        self,
        category_name: str,
        category_data: Dict,
        cat_total: int,
        all_capacities: List[str]
    ) -> str:
        """
        生成單個 Category 的 HTML details 摺疊區塊
        
        Args:
            category_name: Category 名稱
            category_data: 包含 pass, fail, other, items 的字典
            cat_total: 該 Category 的總項目數
            all_capacities: 所有 Capacity 列表（用於表格欄位）
            
        Returns:
            HTML details 區塊字串
        """
        cat_pass = category_data['pass']
        cat_fail = category_data['fail']
        cat_other = category_data['other']
        items = category_data['items']
        
        # 將 items 按 Test Item 分組（Capacity 拉平）
        grouped_items = self._group_by_test_item(items)
        
        # 構建 details 區塊
        # Phase 19.1: 增加「其他」狀態顯示，讓 Total 數字更清晰
        if cat_other > 0:
            summary_line = f"<summary>📁 <b>{category_name}</b> — ✅ {cat_pass} | ❌ {cat_fail} | ➖ {cat_other} | Total: {cat_total}</summary>"
        else:
            summary_line = f"<summary>📁 <b>{category_name}</b> — ✅ {cat_pass} | ❌ {cat_fail} | Total: {cat_total}</summary>"
        
        lines = [
            "<details>",
            summary_line,
            ""
        ]
        
        # 表格標題（動態 Capacity 欄位）
        capacity_headers = " | ".join(all_capacities)
        capacity_separators = " | ".join([":-----:" for _ in all_capacities])
        
        lines.extend([
            f"| Test Item | {capacity_headers} |",
            f"|-----------|{capacity_separators}|"
        ])
        
        # 表格內容
        for item in grouped_items:
            test_item = item['test_item']
            
            # 截斷過長的 Test Item 名稱
            if len(test_item) > 50:
                test_item_display = test_item[:47] + "..."
            else:
                test_item_display = test_item
            
            # 生成每個 Capacity 的狀態符號
            status_cells = []
            for cap in all_capacities:
                status = item['capacities'].get(cap, '')
                if status == 'Pass':
                    status_cells.append("✅")
                elif status == 'Fail':
                    status_cells.append("❌")
                else:
                    status_cells.append("-")
            
            status_str = " | ".join(status_cells)
            lines.append(f"| {test_item_display} | {status_str} |")
        
        lines.extend([
            "",
            "</details>",
            ""
        ])
        
        return "\n".join(lines)
    
    def _handle_project_not_found(
        self, 
        project_name: str, 
        fw_version: str,
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """處理找不到專案的情況"""
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
