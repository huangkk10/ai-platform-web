"""
CompareTestJobsHandler - FW 版本測試項目比較
============================================

處理 Phase 17/18 意圖：比較多個 FW 版本的測試項目結果差異
- 支援 2-10 個 FW 版本同時比較
- 找出狀態變化的項目（Pass→Fail 或 Fail→Pass）
- 找出新增/移除的測試項目
- 統計差異數據

API 端點：POST /api/v1/projects/test-jobs

用戶問法範例：
- 比較 Springsteen PH10YC3H_Pyrite_4K 和 GD10YBJD 的測項結果
- 對比 PM9M1 HHB0YBC1 與 HHB0YBC2 測試項目差異
- 比較 springsteen 幾版 FW 的測試項目結果 GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal

作者：AI Platform Team
創建日期：2025-12-17
更新日期：2025-12-17 - Phase 18: 支援多版本比較
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class CompareTestJobsHandler(BaseHandler):
    """
    FW 版本測試項目比較處理器
    
    支援的意圖：
    - compare_fw_test_jobs: 比較多個 FW 版本的測試項目結果差異
    
    Phase 18 更新：
    - 支援 2-10 個 FW 版本同時比較
    - 使用 fw_versions 陣列參數
    - 動態生成多欄表格
    
    輸出：
    - 統計摘要（各版本的總測試項目、Pass/Fail 數量、通過率）
    - 有差異的測試項目（任意兩個版本狀態不同）
    - 所有測試項目（按類別分組）
    """
    
    handler_name = "compare_test_jobs_handler"
    supported_intent = "compare_fw_test_jobs"
    
    # 版本數量限制
    MIN_VERSIONS = 2
    MAX_VERSIONS = 10
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行測試項目比較（Phase 18: 支援多版本）
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                "fw_versions": ["PH10YC3H_Pyrite_4K", "GD10YBJD", ...],  # 2-10 個版本
                # 或舊格式（向後相容）：
                "fw_version_1": "PH10YC3H_Pyrite_4K",
                "fw_version_2": "GD10YBJD",
                "test_category": "" (optional) - 篩選特定測試類別
            }
            
        Returns:
            QueryResult: 包含比較結果
        """
        self._log_query(parameters)
        
        # Step 1: 統一轉換為 fw_versions 陣列格式
        fw_versions = self._normalize_fw_versions(parameters)
        
        # Step 2: 驗證版本數量
        if len(fw_versions) < self.MIN_VERSIONS:
            return QueryResult.error(
                f"至少需要 {self.MIN_VERSIONS} 個 FW 版本才能進行比較，"
                f"目前只有 {len(fw_versions)} 個",
                self.handler_name,
                parameters
            )
        
        if len(fw_versions) > self.MAX_VERSIONS:
            return QueryResult.error(
                f"最多支援比較 {self.MAX_VERSIONS} 個版本，"
                f"您提供了 {len(fw_versions)} 個。請減少版本數量或分批比較。",
                self.handler_name,
                parameters
            )
        
        # Step 3: 驗證必要參數
        project_name = parameters.get('project_name')
        if not project_name:
            return QueryResult.error(
                "缺少專案名稱 (project_name)",
                self.handler_name,
                parameters
            )
        
        test_category = parameters.get('test_category', '')
        
        try:
            # Step 4: 獲取所有版本的測試結果
            results = {}
            not_found_versions = []
            actual_fw_names = {}  # 儲存實際 FW 名稱
            
            for fw_version in fw_versions:
                result, project = self._get_test_jobs_for_fw(project_name, fw_version)
                if result:
                    actual_fw = project.get('fw', fw_version)
                    results[fw_version] = {
                        'data': result,
                        'project': project
                    }
                    actual_fw_names[fw_version] = actual_fw
                else:
                    not_found_versions.append(fw_version)
            
            # Step 5: 檢查是否有足夠版本可比較
            if len(results) < self.MIN_VERSIONS:
                found_list = list(results.keys())
                return QueryResult.error(
                    f"找不到足夠的 FW 版本資料進行比較。\n"
                    f"找到: {found_list if found_list else '無'}\n"
                    f"未找到: {not_found_versions}",
                    self.handler_name,
                    parameters
                )
            
            # 使用實際找到的版本（按原始順序）
            found_versions = [v for v in fw_versions if v in results]
            
            # Step 6: 執行多版本比較
            comparison = self._compare_multi_test_jobs(
                results=results,
                fw_versions=found_versions,
                actual_fw_names=actual_fw_names,
                test_category=test_category
            )
            
            # Step 7: 添加警告訊息（如果有版本未找到）
            warnings = []
            if not_found_versions:
                warnings.append(
                    f"以下版本未找到資料，已從比較中排除: {', '.join(not_found_versions)}"
                )
            
            # Step 8: 生成回應訊息
            message = self._build_multi_comparison_message(
                project_name=project_name,
                comparison=comparison,
                warnings=warnings
            )
            
            # 獲取第一個專案的元資料
            first_project = results[found_versions[0]]['project']
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'fw_versions': comparison['fw_versions'],
                    'version_count': comparison['version_count'],
                    'comparison': comparison,
                    'warnings': warnings
                },
                count=comparison['diff_count'],
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': first_project.get('projectName', project_name),
                    'customer': first_project.get('customer', ''),
                    'controller': first_project.get('controller', ''),
                    'intent': 'compare_fw_test_jobs',
                    'version_count': comparison['version_count']
                }
            )
            
        except Exception as e:
            logger.error(f"FW 版本測試項目比較錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _normalize_fw_versions(self, parameters: Dict[str, Any]) -> List[str]:
        """
        統一轉換為 fw_versions 陣列格式（向後相容）
        
        支援三種輸入格式:
        1. fw_versions: ["FW1", "FW2", ...]     → 直接使用
        2. fw_version_1 + fw_version_2          → 轉換為陣列
        3. 混合格式                              → 合併處理
        
        Args:
            parameters: 原始參數字典
            
        Returns:
            List[str]: FW 版本陣列（已去重）
        """
        fw_versions = []
        
        # 格式 1: 新的陣列格式
        if 'fw_versions' in parameters:
            versions = parameters['fw_versions']
            if isinstance(versions, list):
                fw_versions.extend(versions)
            elif isinstance(versions, str):
                fw_versions.append(versions)
        
        # 格式 2: 舊的個別參數格式（向後相容）
        if 'fw_version_1' in parameters:
            v1 = parameters['fw_version_1']
            if v1 and v1 not in fw_versions:
                fw_versions.insert(0, v1)
        if 'fw_version_2' in parameters:
            v2 = parameters['fw_version_2']
            if v2 and v2 not in fw_versions:
                # 如果有 v1，v2 放在 v1 後面
                if 'fw_version_1' in parameters and parameters['fw_version_1'] in fw_versions:
                    idx = fw_versions.index(parameters['fw_version_1'])
                    fw_versions.insert(idx + 1, v2)
                else:
                    fw_versions.append(v2)
        
        # 去重並保持順序
        seen = set()
        unique_versions = []
        for v in fw_versions:
            if v and v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        logger.info(f"正規化 FW 版本: {parameters} -> {unique_versions}")
        return unique_versions
    
    def _get_test_jobs_for_fw(
        self, 
        project_name: str, 
        fw_version: str
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        獲取特定 FW 版本的測試結果
        
        Phase 19 更新：改用 test-status/search API，提供更豐富的測試類別資訊
        
        Returns:
            Tuple[test_jobs_result, matched_project] 或 (None, None)
        """
        # 找到符合的專案（用於獲取專案元資料）
        matched_project = self.api_client.find_project_uid_by_name_and_fw(project_name, fw_version)
        
        if not matched_project:
            return None, None
        
        # 使用新的 test-status/search API
        actual_project_name = matched_project.get('projectName', project_name)
        actual_fw = matched_project.get('fw', fw_version)
        
        test_status_result = self.api_client.search_test_status_by_project_fw(
            project_name=actual_project_name,
            fw_version=actual_fw,
            fetch_all=True
        )
        
        if not test_status_result:
            logger.warning(f"test-status/search API 無資料: {actual_project_name} + {actual_fw}")
            return None, matched_project
        
        # 轉換為舊 API 相容的格式
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
        
        return converted_result, matched_project
    
    def _compare_multi_test_jobs(
        self,
        results: Dict[str, Dict[str, Any]],
        fw_versions: List[str],
        actual_fw_names: Dict[str, str],
        test_category: str = ''
    ) -> Dict[str, Any]:
        """
        比較多個 FW 版本的測試結果（Phase 18 新增）
        
        Args:
            results: {fw_version: {'data': test_jobs_data, 'project': project_info}}
            fw_versions: 要比較的版本列表（按順序）
            actual_fw_names: {input_fw: actual_fw_name}
            test_category: 可選的測試類別過濾
            
        Returns:
            comparison: {
                'project_name': str,
                'fw_versions': List[str],
                'version_count': int,
                'summary': {fw_version: {'total': int, 'pass': int, 'fail': int, 'pass_rate': float}},
                'differences': List[Dict],
                'all_items_by_category': Dict[str, List[Dict]],
                'has_differences': bool,
                'diff_count': int,
                'total_items': int
            }
        """
        # 取得專案名稱
        first_version = fw_versions[0]
        project_name = results[first_version]['project'].get('projectName', 'Unknown')
        
        # 使用實際 FW 名稱
        display_fw_versions = [actual_fw_names.get(v, v) for v in fw_versions]
        
        # 建立測試項目索引（使用 test_item_name + capacity 作為唯一 key）
        def make_key(job: Dict) -> str:
            return f"{job.get('test_item_name', '')}||{job.get('capacity', '')}"
        
        # 建立測試項目對照表: {key: {fw_version: status}}
        item_status_map = {}  # {key: {fw_version: status}}
        item_category_map = {}  # {key: category}
        item_info_map = {}  # {key: {'test_item': ..., 'capacity': ...}}
        
        for fw_version in fw_versions:
            test_jobs = results[fw_version]['data'].get('test_jobs', [])
            display_fw = actual_fw_names.get(fw_version, fw_version)
            
            # 可選: 按類別過濾
            if test_category:
                test_jobs = [j for j in test_jobs 
                            if j.get('test_category_name', '').lower() == test_category.lower()]
            
            for job in test_jobs:
                key = make_key(job)
                status = job.get('test_status', 'Unknown')
                
                if key not in item_status_map:
                    item_status_map[key] = {}
                item_status_map[key][display_fw] = status
                
                # 只記錄一次
                if key not in item_category_map:
                    item_category_map[key] = job.get('test_category_name', '未分類')
                    item_info_map[key] = {
                        'test_item': job.get('test_item_name', ''),
                        'capacity': job.get('capacity', '')
                    }
        
        # 分析差異
        differences = []
        all_items_by_category = {}
        
        for key, statuses in item_status_map.items():
            category = item_category_map.get(key, '未分類')
            info = item_info_map.get(key, {})
            
            # 為所有版本填充狀態（如果某版本沒有這個測試項，標記為 N/A）
            full_statuses = {}
            for fw in display_fw_versions:
                full_statuses[fw] = statuses.get(fw, 'N/A')
            
            # 檢查是否有差異（任意兩個版本狀態不同，排除 N/A）
            valid_statuses = [s for s in full_statuses.values() if s != 'N/A']
            has_diff = len(set(valid_statuses)) > 1 if len(valid_statuses) > 1 else False
            
            item_data = {
                'test_item': info.get('test_item', ''),
                'capacity': info.get('capacity', ''),
                'category': category,
                'statuses': full_statuses,
                'has_diff': has_diff
            }
            
            # 按類別分組
            if category not in all_items_by_category:
                all_items_by_category[category] = []
            all_items_by_category[category].append(item_data)
            
            if has_diff:
                differences.append(item_data)
        
        # 計算各版本統計
        summary = {}
        for fw_version in fw_versions:
            display_fw = actual_fw_names.get(fw_version, fw_version)
            test_jobs = results[fw_version]['data'].get('test_jobs', [])
            
            # 如果有類別過濾
            if test_category:
                test_jobs = [j for j in test_jobs 
                            if j.get('test_category_name', '').lower() == test_category.lower()]
            
            total = len(test_jobs)
            pass_count = sum(1 for j in test_jobs if j.get('test_status') == 'Pass')
            fail_count = sum(1 for j in test_jobs if j.get('test_status') == 'Fail')
            pass_rate = (pass_count / total * 100) if total > 0 else 0
            
            summary[display_fw] = {
                'total': total,
                'pass': pass_count,
                'fail': fail_count,
                'pass_rate': round(pass_rate, 1)
            }
        
        # 排序類別內的項目
        for category in all_items_by_category:
            all_items_by_category[category].sort(key=lambda x: (x['test_item'], x['capacity']))
        
        return {
            'project_name': project_name,
            'fw_versions': display_fw_versions,
            'version_count': len(display_fw_versions),
            'summary': summary,
            'differences': differences,
            'all_items_by_category': all_items_by_category,
            'has_differences': len(differences) > 0,
            'diff_count': len(differences),
            'total_items': len(item_status_map)
        }
    
    def _build_multi_comparison_message(
        self,
        project_name: str,
        comparison: Dict[str, Any],
        warnings: List[str] = None
    ) -> str:
        """
        構建多版本比較結果的 Markdown 訊息（Phase 18 新增）
        
        Args:
            project_name: 專案名稱
            comparison: 比較結果
            warnings: 警告訊息列表
        """
        fw_versions = comparison['fw_versions']
        version_count = comparison['version_count']
        summary = comparison['summary']
        differences = comparison['differences']
        all_items_by_category = comparison['all_items_by_category']
        has_differences = comparison['has_differences']
        
        lines = [
            f"## 🔄 {project_name} FW 版本測試項目比較",
            "",
            f"**比較版本**（{version_count} 個）: {' ↔ '.join(fw_versions)}",
            ""
        ]
        
        # 警告訊息
        if warnings:
            lines.append("### ⚠️ 注意")
            for warning in warnings:
                lines.append(f"- {warning}")
            lines.append("")
        
        # === 整體統計表 ===
        lines.append("### 📊 整體統計")
        lines.append("")
        
        # 根據版本數量動態調整欄位寬度
        if version_count <= 2:
            stat_max_len = 22  # 2 版本：最寬
        elif version_count <= 3:
            stat_max_len = 20  # 3 版本：寬
        elif version_count <= 5:
            stat_max_len = 18  # 4-5 版本：中等
        else:
            stat_max_len = 15  # 6+ 版本：較窄
        
        # 動態生成表頭
        header = "| 指標 |"
        separator = "|------|"
        for fw in fw_versions:
            short_name = self._shorten_fw_name(fw, max_len=stat_max_len)
            header += f" {short_name} |"
            separator += "----------|"
        
        # 如果只有 2 個版本，加上「變化」欄
        if version_count == 2:
            header += " 變化 |"
            separator += "------|"
        
        lines.append(header)
        lines.append(separator)
        
        # 統計資料列
        metrics = [
            ('總測試項目', 'total'),
            ('Pass', 'pass'),
            ('Fail', 'fail'),
            ('通過率', 'pass_rate')
        ]
        
        for label, key in metrics:
            row = f"| {label} |"
            values = []
            for fw in fw_versions:
                value = summary.get(fw, {}).get(key, 'N/A')
                if key == 'pass_rate':
                    value = f"{value}%"
                row += f" {value} |"
                values.append(summary.get(fw, {}).get(key, 0))
            
            # 如果只有 2 個版本，計算變化
            if version_count == 2 and len(values) == 2:
                diff = values[1] - values[0]
                if key == 'pass_rate':
                    diff_str = f"+{diff:.1f}%" if diff > 0 else f"{diff:.1f}%"
                else:
                    diff_str = f"+{diff}" if diff > 0 else str(diff)
                
                # 選擇適當的 icon
                if key in ['pass', 'pass_rate']:
                    icon = "✅" if diff > 0 else ("⚠️" if diff < 0 else "")
                elif key == 'fail':
                    icon = "✅" if diff < 0 else ("⚠️" if diff > 0 else "")
                else:
                    icon = ""
                row += f" {diff_str} {icon} |"
            
            lines.append(row)
        
        lines.append("")
        
        # === 差異區塊 ===
        if has_differences:
            diff_count = comparison['diff_count']
            lines.append(f"### ❌ 有差異的測試項目（{diff_count} 項）")
            lines.append("")
            lines.append(self._build_multi_version_table(differences, fw_versions, limit=30))
        else:
            lines.append("### ✅ 無差異")
            lines.append("")
            lines.append("所有 FW 版本的測試項目結果完全相同。")
        
        lines.append("")
        
        # === 所有測試項目區塊 ===
        lines.append("### 📋 所有測試項目")
        lines.append("")
        
        # 定義無意義的狀態（不計入有效結果）
        invalid_statuses = {'N/A', 'CANCEL', 'Cancel', ''}
        
        for category, items in sorted(all_items_by_category.items()):
            # 先過濾出有效項目（至少一個版本有有意義的結果）
            valid_items = [
                item for item in items 
                if any(
                    item['statuses'].get(fw, 'N/A') not in invalid_statuses 
                    for fw in fw_versions
                )
            ]
            
            # 如果過濾後沒有有效項目，跳過這個類別
            if not valid_items:
                continue
            
            # 統計：所有版本都 Pass 的項目數（只統計有有意義結果的版本）
            all_pass_count = sum(1 for item in valid_items if all(
                item['statuses'].get(fw) == 'Pass' 
                for fw in fw_versions 
                if item['statuses'].get(fw, 'N/A') not in invalid_statuses
            ))
            # 任一版本 Fail 的項目數
            any_fail_count = sum(1 for item in valid_items if any(
                item['statuses'].get(fw) == 'Fail' for fw in fw_versions
            ))
            
            lines.append("<details>")
            lines.append(f"<summary>📁 {category}（{len(valid_items)} 項，✅ {all_pass_count} / ❌ {any_fail_count}）</summary>")
            lines.append("")
            lines.append(self._build_multi_version_table(items, fw_versions, limit=50))
            lines.append("")
            lines.append("</details>")
            lines.append("")
        
        return "\n".join(lines)
    
    def _build_multi_version_table(
        self, 
        items: List[Dict], 
        fw_versions: List[str],
        limit: int = 50
    ) -> str:
        """
        建立多版本比較表格（Phase 18 新增）
        
        Args:
            items: 測試項目列表
            fw_versions: FW 版本列表
            limit: 最多顯示項目數
            
        Returns:
            Markdown 表格字串
        """
        if not items:
            return "_沒有資料_"
        
        lines = []
        
        # 根據版本數量動態調整欄位寬度
        # 版本越多，每欄越窄；版本越少，每欄越寬
        version_count = len(fw_versions)
        if version_count <= 2:
            fw_max_len = 20  # 2 版本：較寬
        elif version_count <= 3:
            fw_max_len = 18  # 3 版本：中等
        elif version_count <= 5:
            fw_max_len = 15  # 4-5 版本：較窄
        else:
            fw_max_len = 12  # 6+ 版本：最窄
        
        # 表頭
        header = "| Test Item | Capacity |"
        separator = "|-----------|----------|"
        
        for fw in fw_versions:
            short_name = self._shorten_fw_name(fw, max_len=fw_max_len)
            header += f" {short_name} |"
            separator += "--------|"
        
        lines.append(header)
        lines.append(separator)
        
        # 過濾掉所有 FW 版本都沒有有效測試結果的項目
        # 「無意義狀態」：N/A（不存在）、CANCEL（取消）、空值
        # 這些項目沒有任何實際測試結果，不需要顯示
        invalid_statuses = {'N/A', 'CANCEL', 'Cancel', ''}
        valid_items = []
        for item in items:
            statuses = item.get('statuses', {})
            # 檢查是否至少有一個版本有有效狀態（Pass/Fail/ONGOING 等）
            has_valid_status = any(
                statuses.get(fw, 'N/A') not in invalid_statuses
                for fw in fw_versions
            )
            if has_valid_status:
                valid_items.append(item)
        
        # 如果過濾後沒有項目，返回提示訊息
        if not valid_items:
            return "_此類別在選定的 FW 版本中沒有測試項目_"
        
        # 資料列
        for item in valid_items[:limit]:
            test_item = item.get('test_item', '')
            capacity = item.get('capacity', '')
            statuses = item.get('statuses', {})
            
            # 截斷過長的測試項目名稱
            display_name = test_item[:45] + "..." if len(test_item) > 45 else test_item
            
            row = f"| {display_name} | {capacity} |"
            
            for fw in fw_versions:
                status = statuses.get(fw, 'N/A')
                icon = self._get_status_icon(status)
                row += f" {icon} |"
            
            lines.append(row)
        
        # 如果超過限制（使用過濾後的 valid_items）
        if len(valid_items) > limit:
            remaining = len(valid_items) - limit
            row = f"| ... 還有 {remaining} 項 | ... |"
            for _ in fw_versions:
                row += " ... |"
            lines.append(row)
        
        return "\n".join(lines)
    
    def _shorten_fw_name(self, fw_name: str, max_len: int = 15) -> str:
        """
        縮短 FW 版本名稱以適應表格
        
        策略:
        1. 如果小於 max_len，直接返回
        2. 嘗試保留前綴和後綴，中間用 ... 替代
        3. 後綴保留更多字元以便區分版本
        """
        if len(fw_name) <= max_len:
            return fw_name
        
        # 根據 max_len 調整後綴長度
        # 較長的 max_len 保留更多後綴
        if max_len >= 18:
            suffix_len = 8  # 如 "_Pyrite_4K"
        elif max_len >= 15:
            suffix_len = 6  # 如 "_Opal"
        else:
            suffix_len = 4  # 如 "_4K"
        
        # 前綴長度 = max_len - 3(...) - suffix_len
        prefix_len = max_len - 3 - suffix_len
        
        if prefix_len < 4:
            # 如果前綴太短，改為只截取前面
            return f"{fw_name[:max_len-3]}..."
        
        return f"{fw_name[:prefix_len]}...{fw_name[-suffix_len:]}"
    
    def _get_status_icon(self, status: str) -> str:
        """獲取狀態對應的 icon"""
        status_icons = {
            # 主要狀態
            'Pass': '✅',
            'PASS': '✅',
            'Fail': '❌',
            'FAIL': '❌',
            # 進行中/未完成狀態
            'ONGOING': '🔄',           # 進行中
            'Ongoing': '🔄',
            # 取消/中斷狀態
            'CANCEL': '🚫',            # 取消
            'Cancel': '🚫',
            'INTERRUPT': '⏸️',         # 中斷
            'Interrupt': '⏸️',
            # 條件通過
            'CONDITIONAL PASS': '⚠️',  # 條件通過
            'Conditional Pass': '⚠️',
            'CONDITIONAL_PASS': '⚠️',
            # 其他狀態
            'Skip': '⏭️',
            'SKIP': '⏭️',
            'Error': '🔴',
            'ERROR': '🔴',
            'N/A': '➖',
            'Unknown': '❓'
        }
        return status_icons.get(status, '❓')

    # ==================== 以下為舊版兩版本比較方法（保留向後相容）====================
    
    def _compare_test_jobs(
        self,
        jobs_1: List[Dict],
        jobs_2: List[Dict],
        fw_1: str,
        fw_2: str,
        test_category: str = ''
    ) -> Dict[str, Any]:
        """
        比較兩組測試結果（舊版方法，保留向後相容）
        
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
