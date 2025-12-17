"""
CompareTestJobsHandler - FW 版本測試項目比較
============================================

處理 Phase 17 意圖：比較兩個 FW 版本的測試項目結果差異
- 找出狀態變化的項目（Pass→Fail 或 Fail→Pass）
- 找出新增/移除的測試項目
- 統計差異數據

API 端點：POST /api/v1/projects/test-jobs

用戶問法範例：
- 比較 Springsteen PH10YC3H_Pyrite_4K 和 GD10YBJD 的測項結果
- 對比 PM9M1 HHB0YBC1 與 HHB0YBC2 測試項目差異
- Springsteen FW 版本 PH10YC3H_Pyrite_4K 與 PH10YC3H_Pyrite_2K 的測試差異

作者：AI Platform Team
創建日期：2025-12-17
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class CompareTestJobsHandler(BaseHandler):
    """
    FW 版本測試項目比較處理器
    
    支援的意圖：
    - compare_fw_test_jobs: 比較兩個 FW 版本的測試項目結果差異
    
    輸出：
    - 統計摘要（總測試項目、Pass/Fail 數量、通過率變化）
    - 狀態變化項目（Pass→Fail 或 Fail→Pass）
    - 新增的測試項目
    - 移除的測試項目
    """
    
    handler_name = "compare_test_jobs_handler"
    supported_intent = "compare_fw_test_jobs"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行測試項目比較
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "fw_version_1": "PH10YC3H_Pyrite_4K",
                "fw_version_2": "GD10YBJD",
                # 或 Dify 格式：
                "fw_versions": ["PH10YC3H_Pyrite_4K", "GD10YBJD"],
                "test_category": "" (optional) - 篩選特定測試類別
                "show_only_diff": True (optional) - 只顯示差異項目
            }
            
        Returns:
            QueryResult: 包含比較結果
        """
        self._log_query(parameters)
        
        # ★ 處理 Dify 返回的 fw_versions 陣列格式
        # Dify 可能返回 {"fw_versions": ["FW1", "FW2"]} 而非 {"fw_version_1": "FW1", "fw_version_2": "FW2"}
        if 'fw_versions' in parameters and isinstance(parameters['fw_versions'], list):
            fw_versions = parameters['fw_versions']
            if len(fw_versions) >= 2:
                parameters['fw_version_1'] = fw_versions[0]
                parameters['fw_version_2'] = fw_versions[1]
                logger.info(f"轉換 fw_versions 格式: {fw_versions} -> fw_version_1={fw_versions[0]}, fw_version_2={fw_versions[1]}")
            elif len(fw_versions) == 1:
                return QueryResult.error(
                    f"只提供了一個 FW 版本 '{fw_versions[0]}'，比較需要兩個版本",
                    self.handler_name,
                    parameters
                )
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name', 'fw_version_1', 'fw_version_2']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        fw_version_1 = parameters.get('fw_version_1')
        fw_version_2 = parameters.get('fw_version_2')
        test_category = parameters.get('test_category', '')
        show_only_diff = parameters.get('show_only_diff', True)
        
        try:
            # Step 1: 獲取兩個 FW 版本的測試結果
            result_1, project_1 = self._get_test_jobs_for_fw(project_name, fw_version_1)
            result_2, project_2 = self._get_test_jobs_for_fw(project_name, fw_version_2)
            
            if result_1 is None:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 '{project_name}' 的 FW 版本 '{fw_version_1}'"
                )
            
            if result_2 is None:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案 '{project_name}' 的 FW 版本 '{fw_version_2}'"
                )
            
            # Step 2: 比較兩組測試結果
            comparison = self._compare_test_jobs(
                jobs_1=result_1.get('test_jobs', []),
                jobs_2=result_2.get('test_jobs', []),
                fw_1=project_1.get('fw', fw_version_1),
                fw_2=project_2.get('fw', fw_version_2),
                test_category=test_category
            )
            
            # Step 3: 生成回應訊息
            message = self._build_comparison_message(
                project_name=project_name,
                fw_1=project_1.get('fw', fw_version_1),
                fw_2=project_2.get('fw', fw_version_2),
                comparison=comparison,
                show_only_diff=show_only_diff
            )
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'fw_version_1': project_1.get('fw', fw_version_1),
                    'fw_version_2': project_2.get('fw', fw_version_2),
                    'comparison': comparison
                },
                count=comparison['total_changes'],
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': project_1.get('projectName', project_name),
                    'customer': project_1.get('customer', ''),
                    'controller': project_1.get('controller', ''),
                    'intent': 'compare_fw_test_jobs'
                }
            )
            
        except Exception as e:
            logger.error(f"FW 版本測試項目比較錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _get_test_jobs_for_fw(
        self, 
        project_name: str, 
        fw_version: str
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        獲取特定 FW 版本的測試結果
        
        Returns:
            Tuple[test_jobs_result, matched_project] 或 (None, None)
        """
        # 找到符合的專案
        matched_project = self.api_client.find_project_uid_by_name_and_fw(project_name, fw_version)
        
        if not matched_project:
            return None, None
        
        project_id = matched_project.get('projectId')
        
        # 調用 Test Jobs API
        test_jobs_result = self.api_client.get_project_test_jobs(
            project_ids=[project_id],
            test_tool_key=''
        )
        
        return test_jobs_result, matched_project
    
    def _compare_test_jobs(
        self,
        jobs_1: List[Dict],
        jobs_2: List[Dict],
        fw_1: str,
        fw_2: str,
        test_category: str = ''
    ) -> Dict[str, Any]:
        """
        比較兩組測試結果
        
        Args:
            jobs_1: 第一個 FW 版本的測試項目
            jobs_2: 第二個 FW 版本的測試項目
            fw_1: 第一個 FW 版本名稱
            fw_2: 第二個 FW 版本名稱
            test_category: 篩選的測試類別（可選）
            
        Returns:
            比較結果字典
        """
        # 篩選測試類別（如果指定）
        if test_category:
            jobs_1 = [j for j in jobs_1 if j.get('test_category_name', '').lower() == test_category.lower()]
            jobs_2 = [j for j in jobs_2 if j.get('test_category_name', '').lower() == test_category.lower()]
        
        # 建立測試項目索引（使用 test_item_name + capacity 作為唯一 key）
        def make_key(job: Dict) -> str:
            return f"{job.get('test_item_name', '')}||{job.get('capacity', '')}"
        
        jobs_1_map = {make_key(j): j for j in jobs_1}
        jobs_2_map = {make_key(j): j for j in jobs_2}
        
        keys_1 = set(jobs_1_map.keys())
        keys_2 = set(jobs_2_map.keys())
        
        # 找出差異
        added_keys = keys_2 - keys_1  # v2 新增的
        removed_keys = keys_1 - keys_2  # v2 移除的
        common_keys = keys_1 & keys_2  # 兩者都有的
        
        # 分析狀態變化
        pass_to_fail = []  # Pass → Fail（退步）
        fail_to_pass = []  # Fail → Pass（進步）
        unchanged = []
        
        for key in common_keys:
            job_1 = jobs_1_map[key]
            job_2 = jobs_2_map[key]
            
            status_1 = job_1.get('test_status', '')
            status_2 = job_2.get('test_status', '')
            
            if status_1 == 'Pass' and status_2 == 'Fail':
                pass_to_fail.append({
                    'test_item': job_1.get('test_item_name', ''),
                    'category': job_1.get('test_category_name', ''),
                    'capacity': job_1.get('capacity', ''),
                    'status_v1': status_1,
                    'status_v2': status_2
                })
            elif status_1 == 'Fail' and status_2 == 'Pass':
                fail_to_pass.append({
                    'test_item': job_1.get('test_item_name', ''),
                    'category': job_1.get('test_category_name', ''),
                    'capacity': job_1.get('capacity', ''),
                    'status_v1': status_1,
                    'status_v2': status_2
                })
            else:
                unchanged.append(job_1)
        
        # 統計 v1
        v1_pass = sum(1 for j in jobs_1 if j.get('test_status') == 'Pass')
        v1_fail = sum(1 for j in jobs_1 if j.get('test_status') == 'Fail')
        v1_total = len(jobs_1)
        v1_pass_rate = (v1_pass / v1_total * 100) if v1_total > 0 else 0
        
        # 統計 v2
        v2_pass = sum(1 for j in jobs_2 if j.get('test_status') == 'Pass')
        v2_fail = sum(1 for j in jobs_2 if j.get('test_status') == 'Fail')
        v2_total = len(jobs_2)
        v2_pass_rate = (v2_pass / v2_total * 100) if v2_total > 0 else 0
        
        # 新增項目詳情
        added_items = [
            {
                'test_item': jobs_2_map[k].get('test_item_name', ''),
                'category': jobs_2_map[k].get('test_category_name', ''),
                'capacity': jobs_2_map[k].get('capacity', ''),
                'status': jobs_2_map[k].get('test_status', '')
            }
            for k in added_keys
        ]
        
        # 移除項目詳情
        removed_items = [
            {
                'test_item': jobs_1_map[k].get('test_item_name', ''),
                'category': jobs_1_map[k].get('test_category_name', ''),
                'capacity': jobs_1_map[k].get('capacity', ''),
                'status': jobs_1_map[k].get('test_status', '')
            }
            for k in removed_keys
        ]
        
        # 構建所有測試項目（按 category 分組），用於「無差異」時顯示
        # 需要同時記錄兩個 FW 版本的狀態
        all_items_by_category = {}
        for key in common_keys:
            job_1 = jobs_1_map[key]
            job_2 = jobs_2_map[key]
            category = job_1.get('test_category_name', '未分類')
            if category not in all_items_by_category:
                all_items_by_category[category] = []
            all_items_by_category[category].append({
                'test_item': job_1.get('test_item_name', ''),
                'capacity': job_1.get('capacity', ''),
                'status_v1': job_1.get('test_status', ''),
                'status_v2': job_2.get('test_status', '')
            })
        
        return {
            'summary': {
                'v1': {
                    'fw': fw_1,
                    'total': v1_total,
                    'pass': v1_pass,
                    'fail': v1_fail,
                    'pass_rate': v1_pass_rate
                },
                'v2': {
                    'fw': fw_2,
                    'total': v2_total,
                    'pass': v2_pass,
                    'fail': v2_fail,
                    'pass_rate': v2_pass_rate
                },
                'diff': {
                    'total': v2_total - v1_total,
                    'pass': v2_pass - v1_pass,
                    'fail': v2_fail - v1_fail,
                    'pass_rate': v2_pass_rate - v1_pass_rate
                }
            },
            'pass_to_fail': pass_to_fail,
            'fail_to_pass': fail_to_pass,
            'added_items': added_items,
            'removed_items': removed_items,
            'all_items': all_items_by_category,  # 新增：所有測試項目（按分類）
            'total_changes': len(pass_to_fail) + len(fail_to_pass) + len(added_items) + len(removed_items)
        }
    
    def _build_comparison_message(
        self,
        project_name: str,
        fw_1: str,
        fw_2: str,
        comparison: Dict[str, Any],
        show_only_diff: bool = True
    ) -> str:
        """
        構建比較結果的 Markdown 訊息
        """
        summary = comparison['summary']
        pass_to_fail = comparison['pass_to_fail']
        fail_to_pass = comparison['fail_to_pass']
        added_items = comparison['added_items']
        removed_items = comparison['removed_items']
        
        lines = [
            f"## 🔄 {project_name} FW 版本測試項目比較",
            "",
            f"**比較版本**: {fw_1} ↔ {fw_2}",
            "",
            "### 📊 整體統計",
            "",
            f"| 指標 | {fw_1} | {fw_2} | 變化 |",
            "|------|--------|--------|------|",
        ]
        
        # 總測試項目
        diff_total = summary['diff']['total']
        diff_total_str = f"+{diff_total}" if diff_total > 0 else str(diff_total)
        lines.append(f"| 總測試項目 | {summary['v1']['total']} | {summary['v2']['total']} | {diff_total_str} |")
        
        # Pass 數量
        diff_pass = summary['diff']['pass']
        diff_pass_str = f"+{diff_pass}" if diff_pass > 0 else str(diff_pass)
        pass_icon = "✅" if diff_pass > 0 else ("⚠️" if diff_pass < 0 else "")
        lines.append(f"| Pass | {summary['v1']['pass']} | {summary['v2']['pass']} | {diff_pass_str} {pass_icon} |")
        
        # Fail 數量
        diff_fail = summary['diff']['fail']
        diff_fail_str = f"+{diff_fail}" if diff_fail > 0 else str(diff_fail)
        fail_icon = "✅" if diff_fail < 0 else ("⚠️" if diff_fail > 0 else "")
        lines.append(f"| Fail | {summary['v1']['fail']} | {summary['v2']['fail']} | {diff_fail_str} {fail_icon} |")
        
        # 通過率
        diff_rate = summary['diff']['pass_rate']
        diff_rate_str = f"+{diff_rate:.1f}%" if diff_rate > 0 else f"{diff_rate:.1f}%"
        rate_icon = "✅" if diff_rate > 0 else ("⚠️" if diff_rate < 0 else "")
        lines.append(f"| 通過率 | {summary['v1']['pass_rate']:.1f}% | {summary['v2']['pass_rate']:.1f}% | {diff_rate_str} {rate_icon} |")
        
        lines.append("")
        
        # 狀態變化項目
        total_status_changes = len(pass_to_fail) + len(fail_to_pass)
        if total_status_changes > 0:
            lines.append(f"### ⚠️ 狀態變化項目（{total_status_changes} 項）")
            lines.append("")
            
            # Fail → Pass（進步）
            if fail_to_pass:
                lines.append("<details>")
                lines.append(f"<summary>❌→✅ Fail 轉 Pass（{len(fail_to_pass)} 項）- 已修復</summary>")
                lines.append("")
                lines.append("| Category | Test Item | Capacity | v1 狀態 | v2 狀態 |")
                lines.append("|----------|-----------|----------|---------|---------|")
                for item in fail_to_pass[:20]:  # 限制顯示數量
                    test_item = item['test_item']
                    if len(test_item) > 40:
                        test_item = test_item[:37] + "..."
                    lines.append(f"| {item['category']} | {test_item} | {item['capacity']} | ❌ | ✅ |")
                if len(fail_to_pass) > 20:
                    lines.append(f"| ... | 還有 {len(fail_to_pass) - 20} 項 | ... | ... | ... |")
                lines.append("")
                lines.append("</details>")
                lines.append("")
            
            # Pass → Fail（退步）
            if pass_to_fail:
                lines.append("<details>")
                lines.append(f"<summary>✅→❌ Pass 轉 Fail（{len(pass_to_fail)} 項）- ⚠️ 需關注</summary>")
                lines.append("")
                lines.append("| Category | Test Item | Capacity | v1 狀態 | v2 狀態 |")
                lines.append("|----------|-----------|----------|---------|---------|")
                for item in pass_to_fail[:20]:
                    test_item = item['test_item']
                    if len(test_item) > 40:
                        test_item = test_item[:37] + "..."
                    lines.append(f"| {item['category']} | {test_item} | {item['capacity']} | ✅ | ❌ |")
                if len(pass_to_fail) > 20:
                    lines.append(f"| ... | 還有 {len(pass_to_fail) - 20} 項 | ... | ... | ... |")
                lines.append("")
                lines.append("</details>")
                lines.append("")
        
        # 新增測試項目
        if added_items:
            lines.append(f"### 🆕 新增測試項目（{len(added_items)} 項）")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>點擊展開</summary>")
            lines.append("")
            lines.append("| Category | Test Item | Capacity | 狀態 |")
            lines.append("|----------|-----------|----------|------|")
            for item in added_items[:20]:
                test_item = item['test_item']
                if len(test_item) > 40:
                    test_item = test_item[:37] + "..."
                status_icon = "✅" if item['status'] == 'Pass' else "❌"
                lines.append(f"| {item['category']} | {test_item} | {item['capacity']} | {status_icon} |")
            if len(added_items) > 20:
                lines.append(f"| ... | 還有 {len(added_items) - 20} 項 | ... | ... |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # 移除測試項目
        if removed_items:
            lines.append(f"### 🗑️ 移除測試項目（{len(removed_items)} 項）")
            lines.append("")
            lines.append("<details>")
            lines.append("<summary>點擊展開</summary>")
            lines.append("")
            lines.append("| Category | Test Item | Capacity | 原狀態 |")
            lines.append("|----------|-----------|----------|--------|")
            for item in removed_items[:20]:
                test_item = item['test_item']
                if len(test_item) > 40:
                    test_item = test_item[:37] + "..."
                status_icon = "✅" if item['status'] == 'Pass' else "❌"
                lines.append(f"| {item['category']} | {test_item} | {item['capacity']} | {status_icon} |")
            if len(removed_items) > 20:
                lines.append(f"| ... | 還有 {len(removed_items) - 20} 項 | ... | ... |")
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        # 沒有變化的情況 - 也要列出所有測試項目
        if total_status_changes == 0 and not added_items and not removed_items:
            lines.append("### ✅ 無差異")
            lines.append("")
            lines.append("兩個 FW 版本的測試項目結果完全相同。")
            lines.append("")
            
            # 列出所有測試項目（按類別分組）
            all_items = comparison.get('all_items', {})
            if all_items:
                lines.append("### 📋 所有測試項目")
                lines.append("")
                
                for category, items in sorted(all_items.items()):
                    # 統計 Pass 數量（以 v1 狀態為準，因為無差異情況下 v1 == v2）
                    pass_count = sum(1 for item in items if item.get('status_v1') == 'Pass')
                    fail_count = sum(1 for item in items if item.get('status_v1') == 'Fail')
                    other_count = len(items) - pass_count - fail_count
                    
                    lines.append("<details>")
                    lines.append(f"<summary>📁 {category}（{len(items)} 項，✅ {pass_count} / ❌ {fail_count}）</summary>")
                    lines.append("")
                    # 顯示兩個 FW 版本的狀態欄位
                    lines.append(f"| Test Item | Capacity | {fw_1} | {fw_2} |")
                    lines.append("|-----------|----------|--------|--------|")
                    
                    for item in items[:50]:  # 每個類別最多顯示 50 項
                        test_item = item.get('test_item', '')
                        if len(test_item) > 50:
                            test_item = test_item[:47] + "..."
                        capacity = item.get('capacity', '')
                        status_v1 = item.get('status_v1', '')
                        status_v2 = item.get('status_v2', '')
                        icon_v1 = "✅" if status_v1 == 'Pass' else "❌" if status_v1 == 'Fail' else "⏳"
                        icon_v2 = "✅" if status_v2 == 'Pass' else "❌" if status_v2 == 'Fail' else "⏳"
                        lines.append(f"| {test_item} | {capacity} | {icon_v1} | {icon_v2} |")
                    
                    if len(items) > 50:
                        lines.append(f"| ... | 還有 {len(items) - 50} 項 | ... | ... |")
                    
                    lines.append("")
                    lines.append("</details>")
                    lines.append("")
        
        return "\n".join(lines)
