"""
CompareMultipleFWHandler - 多版本 FW 趨勢比較
=============================================

處理 Phase 5.4 多版本趨勢分析意圖：
- compare_multiple_fw: 比較 3 個或更多 FW 版本的趨勢

功能：
- 支援指定多個 FW 版本名稱進行比較
- 支援自動選擇最近 N 個版本
- 計算趨勢（上升/下降/波動）
- 按類別和容量分組比較
- 輸出圖表用 JSON 資料
- 📊 支援圖表視覺化

作者：AI Platform Team
創建日期：2025-12-08
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from .base_handler import BaseHandler, QueryResult
from .list_fw_versions_handler import ListFWVersionsHandler
from .test_summary_by_fw_handler import TestSummaryByFWHandler
from library.common.chart_formatter import ChartFormatter

logger = logging.getLogger(__name__)

# 配置
MAX_VERSIONS = 10  # 最多比較版本數
DEFAULT_LATEST_COUNT = 3  # 預設比較最近幾個版本
MAX_PARALLEL_REQUESTS = 5  # 並行 API 請求數


class CompareMultipleFWHandler(BaseHandler):
    """
    多版本 FW 趨勢比較處理器
    
    支援的意圖：
    - compare_multiple_fw: 比較多個 FW 版本趨勢
    
    功能：
    1. 支援指定多個 FW 版本名稱
    2. 支援自動選擇最近 N 個版本
    3. 計算各指標趨勢
    4. 按類別分組比較
    5. 輸出圖表 JSON 資料
    """
    
    handler_name = "compare_multiple_fw_handler"
    supported_intent = "compare_multiple_fw"
    
    def __init__(self):
        """初始化 Handler"""
        super().__init__()
        self.list_handler = ListFWVersionsHandler()
        self.summary_handler = TestSummaryByFWHandler()
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行多版本 FW 趨勢比較
        
        Args:
            parameters: {
                "project_name": "Springsteen",
                # 方式 A：指定版本列表
                "fw_versions": ["FW1", "FW2", "FW3"],
                # 方式 B：自動選擇最近 N 個
                "latest_count": 3,
                # 可選：SubVersion 過濾（如 AA、AB、AC）
                "sub_version": "AA",
                # 可選：是否包含圖表資料
                "include_chart_data": True
            }
            
        Returns:
            QueryResult: 包含多版本比較結果和趨勢分析
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
        fw_versions = parameters.get('fw_versions', [])
        latest_count = parameters.get('latest_count', 0)
        sub_version = parameters.get('sub_version')  # 新增：SubVersion 過濾
        include_chart_data = parameters.get('include_chart_data', True)
        
        # 如果沒有指定版本也沒有指定 latest_count，預設取最近 3 個
        if not fw_versions and not latest_count:
            latest_count = DEFAULT_LATEST_COUNT
        
        try:
            # Step 1: 確定要比較的版本列表
            versions_to_compare, all_versions_info = self._resolve_versions(
                project_name, fw_versions, latest_count, sub_version
            )
            
            if not versions_to_compare:
                return QueryResult.error(
                    f"無法確定要比較的 FW 版本",
                    self.handler_name,
                    parameters
                )
            
            if len(versions_to_compare) < 2:
                return QueryResult.error(
                    f"至少需要 2 個 FW 版本才能進行趨勢比較，目前只有 {len(versions_to_compare)} 個",
                    self.handler_name,
                    parameters
                )
            
            if len(versions_to_compare) > MAX_VERSIONS:
                versions_to_compare = versions_to_compare[:MAX_VERSIONS]
                logger.warning(f"版本數量超過上限，只比較前 {MAX_VERSIONS} 個")
            
            # Step 2: 獲取各版本的測試統計資料
            versions_data = self._get_versions_data(project_name, versions_to_compare)
            
            if not versions_data:
                return QueryResult.error(
                    f"無法獲取 FW 版本的測試資料",
                    self.handler_name,
                    parameters
                )
            
            # Step 3: 計算趨勢
            trends = self._calculate_trends(versions_data)
            
            # Step 4: 格式化回應
            message = self._format_response(
                project_name, 
                versions_data, 
                trends,
                all_versions_info,
                sub_version
            )
            
            # Step 5: 生成圖表資料（如果需要）
            chart_data = None
            if include_chart_data:
                chart_data = self._generate_chart_data(project_name, versions_data, trends)
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'versions_compared': [v['fw_version'] for v in versions_data],
                    'versions_count': len(versions_data),
                    'versions_data': versions_data,
                    'trends': trends,
                    'chart_data': chart_data
                },
                count=len(versions_data),
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': project_name,
                    'comparison_type': 'multiple_fw_trend',
                    'total_available_versions': len(all_versions_info) if all_versions_info else 0
                }
            )
            
        except Exception as e:
            logger.error(f"多版本趨勢比較錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _resolve_versions(self, project_name: str, 
                         fw_versions: List[str],
                         latest_count: int,
                         sub_version: str = None) -> Tuple[List[str], List[Dict]]:
        """
        解析要比較的版本列表
        
        Args:
            project_name: 專案名稱
            fw_versions: 用戶指定的版本列表
            latest_count: 要比較的最近版本數量
            sub_version: SubVersion 過濾（如 AA、AB、AC）
            
        Returns:
            Tuple[List[str], List[Dict]]: (版本名稱列表, 所有版本資訊)
        """
        # 如果用戶指定了具體版本，直接從全部專案中搜尋（不受 max_versions 限制）
        if fw_versions:
            return self._resolve_specified_versions(project_name, fw_versions, sub_version)
        
        # 獲取專案最新 FW 版本（用於 latest_count 場景）
        # 如果有 sub_version，需要過濾後再取最近 N 個
        if sub_version:
            return self._resolve_latest_versions_with_subversion(
                project_name, latest_count, sub_version
            )
        
        list_result = self.list_handler.execute({
            'project_name': project_name,
            'max_versions': max(latest_count * 2, 50),  # 獲取足夠多的版本
            'include_stats': False
        })
        
        if not list_result.is_success():
            logger.error(f"無法獲取版本列表: {list_result.error_message}")
            return [], []
        
        all_versions = list_result.data.get('fw_versions', [])
        
        if not all_versions:
            return [], []
        
        # 如果指定了 latest_count，取最近的 N 個版本
        if latest_count > 0:
            # 版本已按建立時間排序（最新在前）
            latest_versions = [v['fw_version'] for v in all_versions[:latest_count]]
            return latest_versions, all_versions
        
        return [], all_versions
    
    def _resolve_latest_versions_with_subversion(self, project_name: str,
                                                  latest_count: int,
                                                  sub_version: str) -> Tuple[List[str], List[Dict]]:
        """
        獲取特定 SubVersion 的最近 N 個版本
        
        Args:
            project_name: 專案名稱
            latest_count: 要獲取的版本數量
            sub_version: SubVersion 過濾（如 AA、AB、AC）
            
        Returns:
            Tuple[List[str], List[Dict]]: (版本名稱列表, 版本資訊列表)
        """
        # 直接從 API 獲取所有專案
        all_projects = self.api_client.get_all_projects(flatten=True)
        
        if not all_projects:
            logger.error("無法獲取專案列表")
            return [], []
        
        # 找到所有匹配專案名稱和 SubVersion 的專案
        project_name_lower = project_name.lower()
        sub_version_upper = sub_version.upper() if sub_version else None
        
        matching_projects = [
            p for p in all_projects
            if project_name_lower in p.get('projectName', '').lower()
            and (not sub_version_upper or p.get('subVersion', '').upper() == sub_version_upper)
        ]
        
        if not matching_projects:
            logger.warning(f"找不到 SubVersion={sub_version} 的專案: {project_name}")
            return [], []
        
        # 建立 FW 版本映射（去重）
        seen_fw = set()
        all_versions = []
        for p in matching_projects:
            fw = p.get('fw', '')
            if fw and fw.lower() not in seen_fw:
                seen_fw.add(fw.lower())
                # 處理 createdAt 可能是字典或字符串的情況
                created_at = p.get('createdAt', '')
                if isinstance(created_at, dict):
                    # 如果是字典格式（如 {'seconds': {'low': xxx}}）
                    seconds = created_at.get('seconds', {})
                    if isinstance(seconds, dict):
                        created_at_value = seconds.get('low', 0)
                    else:
                        created_at_value = seconds
                else:
                    created_at_value = created_at
                    
                all_versions.append({
                    'fw_version': fw,
                    'project_uid': p.get('projectUid'),
                    'sub_version': p.get('subVersion'),
                    'nand': p.get('nand'),
                    'created_at': created_at_value
                })
        
        # 按創建時間排序（最新在前）
        all_versions.sort(key=lambda x: x.get('created_at', 0) if isinstance(x.get('created_at', 0), (int, float)) else 0, reverse=True)
        
        logger.info(f"專案 {project_name} SubVersion={sub_version} 共有 {len(all_versions)} 個 FW 版本")
        
        # 取最近 N 個版本
        latest_versions = [v['fw_version'] for v in all_versions[:latest_count]]
        
        return latest_versions, all_versions
    
    def _resolve_specified_versions(self, project_name: str, 
                                   fw_versions: List[str],
                                   sub_version: str = None) -> Tuple[List[str], List[Dict]]:
        """
        解析用戶指定的 FW 版本（從全部專案中搜尋）
        
        Args:
            project_name: 專案名稱
            fw_versions: 用戶指定的版本列表
            sub_version: SubVersion 過濾（如 AA、AB、AC）
            
        Returns:
            Tuple[List[str], List[Dict]]: (找到的版本名稱列表, 版本資訊列表)
        """
        # 直接從 API 獲取所有專案（不受 ListFWVersionsHandler 的 max_versions 限制）
        all_projects = self.api_client.get_all_projects(flatten=True)
        
        if not all_projects:
            logger.error("無法獲取專案列表")
            return [], []
        
        # 找到所有匹配專案名稱的專案
        project_name_lower = project_name.lower()
        sub_version_upper = sub_version.upper() if sub_version else None
        
        matching_projects = [
            p for p in all_projects
            if project_name_lower in p.get('projectName', '').lower()
        ]
        
        if not matching_projects:
            logger.error(f"找不到專案: {project_name}")
            return [], []
        
        # 如果指定了 sub_version，進一步過濾
        if sub_version_upper:
            filtered_projects = [
                p for p in matching_projects
                if p.get('subVersion', '').upper() == sub_version_upper
            ]
            if filtered_projects:
                matching_projects = filtered_projects
                logger.info(f"已過濾 SubVersion={sub_version}，剩餘 {len(matching_projects)} 個專案")
            else:
                logger.warning(f"找不到 SubVersion={sub_version} 的專案，使用所有專案")
        
        # 建立 FW 版本映射（大小寫不敏感）
        available_versions = {}
        for p in matching_projects:
            fw = p.get('fw', '')
            if fw:
                available_versions[fw.lower()] = {
                    'fw_version': fw,
                    'project_uid': p.get('projectUid'),
                    'sub_version': p.get('subVersion'),
                    'nand': p.get('nand')
                }
        
        logger.info(f"專案 {project_name} 共有 {len(available_versions)} 個不同的 FW 版本")
        
        # 解析用戶指定的版本
        resolved_versions = []
        resolved_infos = []
        
        for fw in fw_versions:
            fw_lower = fw.lower()
            
            # 嘗試精確匹配
            if fw_lower in available_versions:
                info = available_versions[fw_lower]
                resolved_versions.append(info['fw_version'])
                resolved_infos.append(info)
                logger.info(f"找到 FW 版本: {fw} -> {info['fw_version']}")
            else:
                # 嘗試模糊匹配
                matched = None
                for key, info in available_versions.items():
                    if fw_lower in key or key in fw_lower:
                        matched = info
                        break
                
                if matched:
                    resolved_versions.append(matched['fw_version'])
                    resolved_infos.append(matched)
                    logger.info(f"模糊匹配 FW 版本: {fw} -> {matched['fw_version']}")
                else:
                    logger.warning(f"找不到 FW 版本: {fw}")
        
        return resolved_versions, resolved_infos
    
    def _get_versions_data(self, project_name: str, 
                           fw_versions: List[str]) -> List[Dict]:
        """
        獲取多個版本的測試統計資料（並行獲取）
        
        Args:
            project_name: 專案名稱
            fw_versions: FW 版本列表
            
        Returns:
            List[Dict]: 各版本的統計資料列表
        """
        versions_data = []
        
        # 使用 ThreadPoolExecutor 並行獲取
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_REQUESTS) as executor:
            # 提交所有任務
            future_to_version = {
                executor.submit(
                    self._get_single_version_data, 
                    project_name, 
                    fw_version
                ): fw_version
                for fw_version in fw_versions
            }
            
            # 收集結果
            for future in as_completed(future_to_version):
                fw_version = future_to_version[future]
                try:
                    data = future.result()
                    if data:
                        versions_data.append(data)
                except Exception as e:
                    logger.warning(f"獲取 FW {fw_version} 資料失敗: {str(e)}")
        
        # 按版本在原始列表中的順序排序
        version_order = {v: i for i, v in enumerate(fw_versions)}
        versions_data.sort(key=lambda x: version_order.get(x['fw_version'], 999))
        
        return versions_data
    
    def _get_single_version_data(self, project_name: str, 
                                  fw_version: str) -> Optional[Dict]:
        """
        獲取單個版本的測試統計資料
        
        Args:
            project_name: 專案名稱
            fw_version: FW 版本名稱
            
        Returns:
            Dict: 版本統計資料
        """
        try:
            result = self.summary_handler.execute({
                'project_name': project_name,
                'fw_version': fw_version
            })
            
            if result.is_success() and result.data:
                summary = result.data.get('summary', {})
                categories = result.data.get('categories', [])
                capacities = result.data.get('capacities', [])
                
                # 從 summary 取得正確的 key（pass/fail 不是 total_pass/total_fail）
                total_pass = summary.get('pass', 0)
                total_fail = summary.get('fail', 0)
                total = summary.get('total', 0)
                
                # pass_rate 可能是字串 "0.0%" 或數字
                pass_rate_raw = summary.get('passRate', '0.0%')
                if isinstance(pass_rate_raw, str):
                    pass_rate = float(pass_rate_raw.replace('%', '')) if pass_rate_raw else 0.0
                else:
                    pass_rate = float(pass_rate_raw) if pass_rate_raw else 0.0
                
                # 計算完成率（如果 metadata 有的話）
                completion_rate = 0
                if result.metadata:
                    completion_rate = result.metadata.get('completion_rate', 0)
                
                return {
                    'fw_version': fw_version,
                    'project_uid': result.metadata.get('project_uid', '') if result.metadata else '',
                    'pass': total_pass,
                    'fail': total_fail,
                    'total': total,
                    'pass_rate': pass_rate,
                    'completion_rate': completion_rate,
                    'categories': categories,
                    'capacities': capacities,
                    'created_at': result.metadata.get('created_at', '') if result.metadata else ''
                }
            
            return None
            
        except Exception as e:
            logger.warning(f"獲取 FW {fw_version} 統計失敗: {str(e)}")
            return None
    
    def _calculate_trends(self, versions_data: List[Dict]) -> Dict[str, Any]:
        """
        計算各指標的趨勢
        
        趨勢類型：
        - increasing: 持續上升
        - decreasing: 持續下降
        - fluctuating: 波動
        - stable: 穩定
        
        Args:
            versions_data: 各版本的統計資料
            
        Returns:
            Dict: 趨勢分析結果
        """
        if len(versions_data) < 2:
            return {}
        
        def calculate_single_trend(values: List[float]) -> str:
            """計算單一指標的趨勢"""
            if len(values) < 2:
                return "stable"
            
            # 計算變化方向
            changes = []
            for i in range(1, len(values)):
                if values[i] > values[i-1]:
                    changes.append(1)  # 上升
                elif values[i] < values[i-1]:
                    changes.append(-1)  # 下降
                else:
                    changes.append(0)  # 持平
            
            # 判斷趨勢
            if all(c >= 0 for c in changes) and any(c > 0 for c in changes):
                return "increasing"
            elif all(c <= 0 for c in changes) and any(c < 0 for c in changes):
                return "decreasing"
            elif all(c == 0 for c in changes):
                return "stable"
            else:
                return "fluctuating"
        
        def get_trend_icon(trend: str) -> str:
            """獲取趨勢圖示"""
            icons = {
                "increasing": "📈",
                "decreasing": "📉",
                "fluctuating": "📊",
                "stable": "➡️"
            }
            return icons.get(trend, "")
        
        # 提取各指標數值
        pass_values = [v.get('pass', 0) for v in versions_data]
        fail_values = [v.get('fail', 0) for v in versions_data]
        pass_rate_values = [v.get('pass_rate', 0) for v in versions_data]
        completion_rate_values = [v.get('completion_rate', 0) for v in versions_data]
        
        # 計算整體趨勢
        trends = {
            'pass': {
                'trend': calculate_single_trend(pass_values),
                'values': pass_values,
                'first': pass_values[0],
                'last': pass_values[-1],
                'change': pass_values[-1] - pass_values[0]
            },
            'fail': {
                'trend': calculate_single_trend(fail_values),
                'values': fail_values,
                'first': fail_values[0],
                'last': fail_values[-1],
                'change': fail_values[-1] - fail_values[0]
            },
            'pass_rate': {
                'trend': calculate_single_trend(pass_rate_values),
                'values': pass_rate_values,
                'first': pass_rate_values[0],
                'last': pass_rate_values[-1],
                'change': pass_rate_values[-1] - pass_rate_values[0]
            },
            'completion_rate': {
                'trend': calculate_single_trend(completion_rate_values),
                'values': completion_rate_values,
                'first': completion_rate_values[0],
                'last': completion_rate_values[-1],
                'change': completion_rate_values[-1] - completion_rate_values[0]
            }
        }
        
        # 添加圖示
        for key in trends:
            trends[key]['icon'] = get_trend_icon(trends[key]['trend'])
        
        # 計算按類別的趨勢
        category_trends = self._calculate_category_trends(versions_data)
        trends['by_category'] = category_trends
        
        return trends
    
    def _calculate_category_trends(self, versions_data: List[Dict]) -> Dict[str, Dict]:
        """
        計算各類別的趨勢
        
        Args:
            versions_data: 各版本的統計資料
            
        Returns:
            Dict: 按類別的趨勢分析
        """
        # 收集所有類別
        all_categories = set()
        for v in versions_data:
            by_category = v.get('by_category', {})
            all_categories.update(by_category.keys())
        
        category_trends = {}
        
        for category in all_categories:
            pass_values = []
            fail_values = []
            
            for v in versions_data:
                by_category = v.get('by_category', {})
                cat_data = by_category.get(category, {})
                pass_values.append(cat_data.get('pass', 0))
                fail_values.append(cat_data.get('fail', 0))
            
            # 計算變化
            pass_change = pass_values[-1] - pass_values[0] if pass_values else 0
            fail_change = fail_values[-1] - fail_values[0] if fail_values else 0
            
            category_trends[category] = {
                'pass_values': pass_values,
                'fail_values': fail_values,
                'pass_change': pass_change,
                'fail_change': fail_change,
                'pass_trend_icon': "📈" if pass_change > 0 else ("📉" if pass_change < 0 else "➡️"),
                'fail_trend_icon': "📈" if fail_change > 0 else ("📉" if fail_change < 0 else "➡️"),
                'needs_attention': fail_change > 0 and (fail_change >= 3 or (fail_values[0] > 0 and fail_change / fail_values[0] >= 0.5))
            }
        
        return category_trends
    
    def _format_response(self, project_name: str,
                        versions_data: List[Dict],
                        trends: Dict[str, Any],
                        all_versions_info: List[Dict],
                        sub_version: str = None) -> str:
        """
        格式化回應訊息（增強版）
        
        Args:
            project_name: 專案名稱
            versions_data: 各版本統計資料
            trends: 趨勢分析結果
            all_versions_info: 所有可用版本資訊
            sub_version: SubVersion 過濾（如 AA、AB、AC）
            
        Returns:
            str: Markdown 格式的回應
        """
        version_names = [v['fw_version'] for v in versions_data]
        
        # 構建標題（包含 SubVersion 資訊）
        title_suffix = f" (SubVersion: {sub_version})" if sub_version else ""
        
        lines = [
            f"## 📊 {project_name}{title_suffix} 多版本趨勢比較",
            "",
            f"比較版本（{len(versions_data)} 個）：**{'** → **'.join(version_names)}**",
            ""
        ]
        
        # ===== Section 1: 整體指標趨勢表格 =====
        lines.extend([
            "### 📈 整體指標趨勢",
            "",
            "| 指標 | " + " | ".join(version_names) + " | 變化 | 趨勢 |",
            "|------|" + "|".join(["------"] * len(version_names)) + "|------|------|"
        ])
        
        # Pass
        pass_trend = trends.get('pass', {})
        pass_values = [v.get('pass', 0) for v in versions_data]
        pass_change = pass_trend.get('change', 0)
        pass_change_str = f"+{pass_change}" if pass_change > 0 else str(pass_change)
        lines.append(f"| Pass | {' | '.join(str(v) for v in pass_values)} | {pass_change_str} | {pass_trend.get('icon', '')} |")
        
        # Fail
        fail_trend = trends.get('fail', {})
        fail_values = [v.get('fail', 0) for v in versions_data]
        fail_change = fail_trend.get('change', 0)
        fail_change_str = f"+{fail_change}" if fail_change > 0 else str(fail_change)
        lines.append(f"| Fail | {' | '.join(str(v) for v in fail_values)} | {fail_change_str} | {fail_trend.get('icon', '')} |")
        
        # Total
        total_values = [v.get('total', 0) for v in versions_data]
        first_total = versions_data[0].get('total', 0)
        last_total = versions_data[-1].get('total', 0)
        total_change = last_total - first_total
        total_change_str = f"+{total_change}" if total_change > 0 else str(total_change)
        lines.append(f"| Total | {' | '.join(str(v) for v in total_values)} | {total_change_str} | |")
        
        # 通過率
        pass_rate_trend = trends.get('pass_rate', {})
        pass_rate_values = [v.get('pass_rate', 0) for v in versions_data]
        pass_rate_change = pass_rate_trend.get('change', 0)
        pass_rate_change_str = f"+{pass_rate_change:.1f}%" if pass_rate_change > 0 else f"{pass_rate_change:.1f}%"
        lines.append(f"| 通過率 | {' | '.join(f'{v:.1f}%' for v in pass_rate_values)} | {pass_rate_change_str} | {pass_rate_trend.get('icon', '')} |")
        
        # 完成率
        completion_trend = trends.get('completion_rate', {})
        completion_values = [v.get('completion_rate', 0) for v in versions_data]
        completion_change = completion_trend.get('change', 0)
        completion_change_str = f"+{completion_change:.1f}%" if completion_change > 0 else f"{completion_change:.1f}%"
        lines.append(f"| 完成率 | {' | '.join(f'{v:.1f}%' for v in completion_values)} | {completion_change_str} | {completion_trend.get('icon', '')} |")
        
        lines.append("")
        
        # ===== Section 2: 統計摘要 =====
        lines.extend(self._format_statistics_summary(versions_data, pass_values, fail_values, total_values))
        
        # ===== Section 3: 按類別詳細比較 =====
        lines.extend(self._format_category_comparison(versions_data, version_names, trends))
        
        # ===== Section 4: 趨勢分析摘要 =====
        lines.extend([
            "### 🔍 趨勢分析摘要",
            ""
        ])
        
        # 整體趨勢說明
        pass_trend_text = self._get_trend_description('Pass', pass_trend)
        fail_trend_text = self._get_trend_description('Fail', fail_trend)
        
        lines.append(f"**整體趨勢**：")
        lines.append(f"- {pass_trend_text}")
        lines.append(f"- {fail_trend_text}")
        lines.append("")
        
        # 獲取類別趨勢資料
        category_trends = trends.get('by_category', {})
        
        # 需要關注的類別
        attention_categories = [
            cat for cat, data in category_trends.items() 
            if data.get('needs_attention')
        ]
        
        if attention_categories:
            lines.append("**⚠️ 需要關注的類別**：")
            for cat in attention_categories:
                cat_data = category_trends[cat]
                fail_change = cat_data.get('fail_change', 0)
                lines.append(f"- **{cat}**：Fail 增加 {fail_change}")
            lines.append("")
        
        # 改善的類別
        improved_categories = [
            cat for cat, data in category_trends.items()
            if data.get('fail_change', 0) < 0
        ]
        
        if improved_categories:
            lines.append("**✅ 改善的類別**：")
            for cat in improved_categories:
                cat_data = category_trends[cat]
                fail_change = cat_data.get('fail_change', 0)
                lines.append(f"- **{cat}**：Fail 減少 {abs(fail_change)}")
            lines.append("")
        
        # ===== Section 5: 版本間差異分析 =====
        lines.extend(self._format_version_diff_analysis(versions_data, version_names))
        
        # 提示
        total_versions = len(all_versions_info) if all_versions_info else 0
        if total_versions > len(versions_data):
            lines.extend([
                "---",
                "",
                "💡 **提示**：",
                f"- 此專案共有 {total_versions} 個 FW 版本，目前顯示 {len(versions_data)} 個",
                f"- 您可以指定其他版本進行比較"
            ])
        
        # ===== Section 6: 圖表視覺化 =====
        lines.extend(self._generate_trend_chart(project_name, versions_data, version_names, sub_version))
        
        return "\n".join(lines)
    
    def _generate_trend_chart(self, project_name: str, 
                               versions_data: List[Dict],
                               version_names: List[str],
                               sub_version: str = None) -> List[str]:
        """
        📊 生成趨勢視覺化圖表
        
        包含：
        0. 測試類別雷達圖（各類別 Pass 數量分佈對比）
        1. 測試結果分組長條圖（Pass/Fail 對比）
        2. 測試結果趨勢折線圖（Pass/Fail/Total 趨勢）
        3. 整體指標折線圖（完成率/執行率/失敗率趨勢）
        
        Args:
            project_name: 專案名稱
            versions_data: 各版本統計資料
            version_names: 版本名稱列表
            sub_version: SubVersion 過濾（如 AA、AB、AC）
            
        Returns:
            List[str]: 包含圖表標記的 Markdown 行列表
        """
        lines = [
            "",
            "### 📊 趨勢視覺化",
            ""
        ]
        
        try:
            # 構建標題後綴
            title_suffix = f" ({sub_version})" if sub_version else ""
            
            # ===== 圖表 0: 測試類別熱力圖 =====
            heatmap_chart = self._generate_category_heatmap(
                project_name, versions_data, version_names, sub_version
            )
            if heatmap_chart:
                lines.append(heatmap_chart)
                lines.append("")
            
            # 準備圖表資料
            pass_values = [v.get('pass', 0) for v in versions_data]
            fail_values = [v.get('fail', 0) for v in versions_data]
            total_values = [v.get('total', 0) for v in versions_data]
            pass_rate_values = [v.get('pass_rate', 0) for v in versions_data]
            completion_rate_values = [v.get('completion_rate', 0) for v in versions_data]
            
            # ===== 圖表 1: 測試結果分組長條圖 =====
            bar_chart_title = f"{project_name}{title_suffix} 測試結果比較"
            
            bar_chart_md = ChartFormatter.fw_test_results_bar(
                title=bar_chart_title,
                fw_versions=version_names,
                pass_counts=pass_values,
                fail_counts=fail_values
            )
            
            lines.append(bar_chart_md)
            lines.append("")
            
            # ===== 圖表 2: 測試結果趨勢折線圖 =====
            line_chart_title = f"{project_name}{title_suffix} 測試結果趨勢"
            
            line_chart_md = ChartFormatter.line_chart(
                title=line_chart_title,
                labels=version_names,
                datasets=[
                    {
                        "name": "Pass",
                        "data": pass_values,
                        "color": "#52c41a"  # 綠色
                    },
                    {
                        "name": "Fail", 
                        "data": fail_values,
                        "color": "#ff4d4f"  # 紅色
                    },
                    {
                        "name": "Total",
                        "data": total_values,
                        "color": "#1890ff"  # 藍色
                    }
                ],
                description=f"顯示 {len(version_names)} 個 FW 版本的測試結果變化趨勢",
                options={
                    "showGrid": True,
                    "showLegend": True,
                    "showDots": True,
                    "height": 320
                }
            )
            
            lines.append(line_chart_md)
            lines.append("")
            
            # ===== 圖表 3: 整體指標折線圖 =====
            # 準備整體指標資料（完成率、通過率）
            metrics_data = {
                "完成率": completion_rate_values,
                "通過率": pass_rate_values
            }
            
            # 如果有任何有效的整體指標數據，則生成圖表
            has_metrics = any(
                any(v > 0 for v in values) 
                for values in metrics_data.values()
            )
            
            if has_metrics:
                metrics_chart_title = f"{project_name}{title_suffix} 整體指標趨勢"
                
                metrics_chart_md = ChartFormatter.fw_overall_metrics_line(
                    title=metrics_chart_title,
                    fw_versions=version_names,
                    metrics_data=metrics_data
                )
                
                lines.append(metrics_chart_md)
                lines.append("")
            
            logger.info(f"📊 已生成趨勢圖表：{bar_chart_title}, {line_chart_title}")
            
        except Exception as e:
            logger.error(f"生成圖表時發生錯誤: {str(e)}")
            lines.append(f"*（圖表生成失敗：{str(e)}）*")
        
        return lines
    
    def _generate_category_radar_chart(
        self,
        project_name: str,
        versions_data: List[Dict],
        version_names: List[str],
        sub_version: str = None
    ) -> Optional[str]:
        """
        生成測試類別雷達圖（多版本支援）
        
        Args:
            project_name: 專案名稱
            versions_data: 各版本統計資料
            version_names: 版本名稱列表
            sub_version: SubVersion 過濾
            
        Returns:
            雷達圖的 Markdown 標記，失敗返回 None
        """
        try:
            # 收集所有類別
            all_categories = set()
            for v in versions_data:
                for cat in v.get('categories', []):
                    cat_name = cat.get('name', '')
                    if cat_name:
                        all_categories.add(cat_name)
            
            # 雷達圖需要至少 3 個維度
            if len(all_categories) < 3:
                logger.debug(f"類別數量不足 ({len(all_categories)} < 3)，跳過雷達圖生成")
                return None
            
            # 排序類別名稱（保持一致性）
            sorted_categories = sorted(all_categories)
            
            # 限制最多顯示 12 個類別（避免雷達圖過於擁擠）
            if len(sorted_categories) > 12:
                # 優先選取有最多 Pass 的類別
                category_totals = {}
                for v in versions_data:
                    for cat in v.get('categories', []):
                        cat_name = cat.get('name', '')
                        if cat_name:
                            category_totals[cat_name] = category_totals.get(cat_name, 0) + cat.get('pass', 0)
                
                sorted_categories = sorted(
                    category_totals.keys(),
                    key=lambda x: category_totals[x],
                    reverse=True
                )[:12]
            
            # 準備雷達圖數據
            fw_versions_data = []
            for i, version_name in enumerate(version_names):
                if i >= len(versions_data):
                    break
                    
                v = versions_data[i]
                
                # 建立類別映射
                cat_map = {cat.get('name', ''): cat for cat in v.get('categories', [])}
                
                # 獲取每個類別的 Pass 數量
                pass_counts = [
                    cat_map.get(cat, {}).get('pass', 0)
                    for cat in sorted_categories
                ]
                
                fw_versions_data.append({
                    'name': version_name,
                    'pass_counts': pass_counts
                })
            
            # 構建標題
            title_suffix = f" ({sub_version})" if sub_version else ""
            chart_title = f"🕸️ {project_name}{title_suffix} 測試類別分佈對比"
            
            # 生成雷達圖
            radar_chart = ChartFormatter.fw_category_comparison_radar(
                title=chart_title,
                categories=sorted_categories,
                fw_versions=fw_versions_data
            )
            
            logger.info(f"📊 已生成雷達圖：{len(sorted_categories)} 個類別, {len(fw_versions_data)} 個版本")
            return radar_chart
            
        except Exception as e:
            logger.warning(f"生成測試類別雷達圖失敗: {str(e)}")
            return None

    def _generate_category_heatmap(
        self,
        project_name: str,
        versions_data: List[Dict],
        version_names: List[str],
        sub_version: str = None
    ) -> Optional[str]:
        """
        生成測試類別 Fail 數量熱力圖
        
        Args:
            project_name: 專案名稱
            versions_data: 各版本統計資料
            version_names: 版本名稱列表
            sub_version: SubVersion 過濾
            
        Returns:
            熱力圖的 Markdown 標記，失敗返回 None
        """
        try:
            # 收集所有類別
            all_categories = set()
            for v in versions_data:
                for cat in v.get('categories', []):
                    cat_name = cat.get('name', '')
                    if cat_name:
                        all_categories.add(cat_name)
            
            # 需要至少有類別資料
            if len(all_categories) < 2:
                logger.debug(f"類別數量不足 ({len(all_categories)} < 2)，跳過熱力圖生成")
                return None
            
            # 排序類別名稱
            sorted_categories = sorted(all_categories)
            
            # 準備熱力圖數據：二維陣列 [category][version]
            fail_data = []
            for category in sorted_categories:
                row = []
                for i, version_name in enumerate(version_names):
                    if i >= len(versions_data):
                        row.append(0)
                        continue
                    
                    v = versions_data[i]
                    cat_map = {cat.get('name', ''): cat for cat in v.get('categories', [])}
                    fail_count = cat_map.get(category, {}).get('fail', 0)
                    row.append(fail_count)
                
                fail_data.append(row)
            
            # 構建標題
            title_suffix = f" ({sub_version})" if sub_version else ""
            chart_title = f"🔥 {project_name}{title_suffix} 測試類別 Fail 分佈熱力圖"
            
            # 生成熱力圖
            heatmap_chart = ChartFormatter.category_fail_heatmap(
                title=chart_title,
                categories=sorted_categories,
                fw_versions=version_names,
                fail_counts=fail_data,
                description=f"顯示 {len(sorted_categories)} 個測試類別在 {len(version_names)} 個 FW 版本的 Fail 分佈（綠色=無 Fail）"
            )
            
            logger.info(f"📊 已生成熱力圖：{len(sorted_categories)} 個類別, {len(version_names)} 個版本")
            return heatmap_chart
            
        except Exception as e:
            logger.warning(f"生成測試類別熱力圖失敗: {str(e)}")
            return None

    def _format_statistics_summary(self, versions_data: List[Dict],
                                   pass_values: List[int],
                                   fail_values: List[int],
                                   total_values: List[int]) -> List[str]:
        """
        格式化統計摘要
        
        Args:
            versions_data: 各版本統計資料
            pass_values: Pass 數值列表
            fail_values: Fail 數值列表
            total_values: Total 數值列表
            
        Returns:
            List[str]: Markdown 行列表
        """
        lines = [
            "### 📋 統計摘要",
            ""
        ]
        
        # 計算統計值
        if pass_values:
            avg_pass = sum(pass_values) / len(pass_values)
            max_pass = max(pass_values)
            min_pass = min(pass_values)
            max_pass_idx = pass_values.index(max_pass)
            min_pass_idx = pass_values.index(min_pass)
        else:
            avg_pass = max_pass = min_pass = 0
            max_pass_idx = min_pass_idx = 0
        
        if fail_values:
            avg_fail = sum(fail_values) / len(fail_values)
            max_fail = max(fail_values)
            min_fail = min(fail_values)
            max_fail_idx = fail_values.index(max_fail)
            min_fail_idx = fail_values.index(min_fail)
        else:
            avg_fail = max_fail = min_fail = 0
            max_fail_idx = min_fail_idx = 0
        
        if total_values:
            total_sum = sum(total_values)
            avg_total = total_sum / len(total_values)
        else:
            total_sum = avg_total = 0
        
        # 統計表格
        lines.extend([
            "| 統計項目 | Pass | Fail | Total |",
            "|---------|------|------|-------|",
            f"| 平均值 | {avg_pass:.1f} | {avg_fail:.1f} | {avg_total:.1f} |",
            f"| 最大值 | {max_pass} ({versions_data[max_pass_idx]['fw_version'] if versions_data else '-'}) | "
            f"{max_fail} ({versions_data[max_fail_idx]['fw_version'] if versions_data else '-'}) | {max(total_values) if total_values else 0} |",
            f"| 最小值 | {min_pass} ({versions_data[min_pass_idx]['fw_version'] if versions_data else '-'}) | "
            f"{min_fail} ({versions_data[min_fail_idx]['fw_version'] if versions_data else '-'}) | {min(total_values) if total_values else 0} |",
            ""
        ])
        
        # 版本測試數量變化趨勢
        if len(total_values) >= 2:
            total_change_pct = ((total_values[-1] - total_values[0]) / total_values[0] * 100) if total_values[0] > 0 else 0
            lines.append(f"📊 **測試規模變化**：從 {total_values[0]} 項增加到 {total_values[-1]} 項 ({total_change_pct:+.1f}%)")
            lines.append("")
        
        return lines
    
    def _format_category_comparison(self, versions_data: List[Dict],
                                    version_names: List[str],
                                    trends: Dict[str, Any]) -> List[str]:
        """
        格式化按類別詳細比較
        
        Args:
            versions_data: 各版本統計資料
            version_names: 版本名稱列表
            trends: 趨勢分析結果
            
        Returns:
            List[str]: Markdown 行列表
        """
        lines = []
        
        # 收集所有類別的數據
        all_categories = {}
        for v in versions_data:
            for cat in v.get('categories', []):
                cat_name = cat.get('name', '')
                if cat_name not in all_categories:
                    all_categories[cat_name] = []
                all_categories[cat_name].append({
                    'pass': cat.get('pass', 0),
                    'fail': cat.get('fail', 0),
                    'total': cat.get('total', 0)
                })
        
        if not all_categories:
            return lines
        
        lines.extend([
            "### 📁 按類別詳細比較",
            "",
            "| 類別 | " + " | ".join([f"{v} (P/F/T)" for v in version_names]) + " | Fail 變化 | 狀態 |",
            "|------|" + "|".join(["------"] * len(version_names)) + "|------|------|"
        ])
        
        # 按類別名稱排序
        for category in sorted(all_categories.keys()):
            cat_data_list = all_categories[category]
            
            # 確保每個版本都有資料（補 0）
            while len(cat_data_list) < len(version_names):
                cat_data_list.append({'pass': 0, 'fail': 0, 'total': 0})
            
            # 各版本的 Pass/Fail/Total
            pft_values = []
            for cat_data in cat_data_list:
                p = cat_data.get('pass', 0)
                f = cat_data.get('fail', 0)
                t = cat_data.get('total', 0)
                pft_values.append(f"{p}/{f}/{t}")
            
            # 計算 Fail 變化
            first_fail = cat_data_list[0].get('fail', 0)
            last_fail = cat_data_list[-1].get('fail', 0)
            fail_change = last_fail - first_fail
            fail_str = f"+{fail_change}" if fail_change > 0 else str(fail_change)
            
            # 狀態圖標
            if fail_change > 0:
                status = "🔴 退步"
            elif fail_change < 0:
                status = "🟢 改善"
            elif last_fail == 0:
                status = "✅ 無 Fail"
            else:
                status = "⚪ 持平"
            
            lines.append(f"| {category} | {' | '.join(pft_values)} | {fail_str} | {status} |")
        
        lines.append("")
        
        # 類別摘要統計
        total_categories = len(all_categories)
        improved = sum(1 for cat in all_categories.values() 
                      if len(cat) >= 2 and cat[-1].get('fail', 0) < cat[0].get('fail', 0))
        degraded = sum(1 for cat in all_categories.values() 
                      if len(cat) >= 2 and cat[-1].get('fail', 0) > cat[0].get('fail', 0))
        no_fail = sum(1 for cat in all_categories.values() 
                     if cat[-1].get('fail', 0) == 0)
        
        lines.extend([
            f"📊 **類別統計**：共 {total_categories} 個類別",
            f"- 🟢 改善：{improved} 個類別",
            f"- 🔴 退步：{degraded} 個類別",
            f"- ✅ 無 Fail：{no_fail} 個類別",
            ""
        ])
        
        return lines
    
    def _format_version_diff_analysis(self, versions_data: List[Dict],
                                      version_names: List[str]) -> List[str]:
        """
        格式化版本間差異分析
        
        Args:
            versions_data: 各版本統計資料
            version_names: 版本名稱列表
            
        Returns:
            List[str]: Markdown 行列表
        """
        if len(versions_data) < 2:
            return []
        
        lines = [
            "### 🔄 版本間變化分析",
            ""
        ]
        
        # 計算相鄰版本間的變化
        for i in range(1, len(versions_data)):
            prev = versions_data[i-1]
            curr = versions_data[i]
            
            prev_name = version_names[i-1]
            curr_name = version_names[i]
            
            pass_diff = curr.get('pass', 0) - prev.get('pass', 0)
            fail_diff = curr.get('fail', 0) - prev.get('fail', 0)
            total_diff = curr.get('total', 0) - prev.get('total', 0)
            
            pass_diff_str = f"+{pass_diff}" if pass_diff > 0 else str(pass_diff)
            fail_diff_str = f"+{fail_diff}" if fail_diff > 0 else str(fail_diff)
            total_diff_str = f"+{total_diff}" if total_diff > 0 else str(total_diff)
            
            # 判斷整體趨勢
            if fail_diff < 0 and pass_diff >= 0:
                overall = "✅ 改善"
            elif fail_diff > 0:
                overall = "⚠️ 需關注"
            else:
                overall = "➡️ 持平"
            
            lines.append(f"**{prev_name} → {curr_name}**：Pass {pass_diff_str}, Fail {fail_diff_str}, Total {total_diff_str} {overall}")
        
        lines.append("")
        
        # 首尾版本比較摘要
        first = versions_data[0]
        last = versions_data[-1]
        
        total_pass_change = last.get('pass', 0) - first.get('pass', 0)
        total_fail_change = last.get('fail', 0) - first.get('fail', 0)
        
        lines.extend([
            f"**📈 整體變化（{version_names[0]} → {version_names[-1]}）**：",
            f"- Pass：{first.get('pass', 0)} → {last.get('pass', 0)} ({'+' if total_pass_change >= 0 else ''}{total_pass_change})",
            f"- Fail：{first.get('fail', 0)} → {last.get('fail', 0)} ({'+' if total_fail_change >= 0 else ''}{total_fail_change})",
            ""
        ])
        
        return lines
    
    def _get_trend_description(self, metric_name: str, trend_data: Dict) -> str:
        """
        獲取趨勢描述文字
        
        Args:
            metric_name: 指標名稱
            trend_data: 趨勢資料
            
        Returns:
            str: 描述文字
        """
        trend = trend_data.get('trend', 'stable')
        change = trend_data.get('change', 0)
        icon = trend_data.get('icon', '')
        
        descriptions = {
            'increasing': f"{metric_name} 持續上升（變化：+{change}）{icon}",
            'decreasing': f"{metric_name} 持續下降（變化：{change}）{icon}",
            'fluctuating': f"{metric_name} 波動變化（總變化：{'+' if change > 0 else ''}{change}）{icon}",
            'stable': f"{metric_name} 保持穩定 {icon}"
        }
        
        return descriptions.get(trend, f"{metric_name} 變化：{change}")
    
    def _generate_chart_data(self, project_name: str,
                            versions_data: List[Dict],
                            trends: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成前端圖表用的 JSON 資料
        
        Args:
            project_name: 專案名稱
            versions_data: 各版本統計資料
            trends: 趨勢分析結果
            
        Returns:
            Dict: 圖表資料
        """
        version_names = [v['fw_version'] for v in versions_data]
        created_dates = [v.get('created_at', '') for v in versions_data]
        
        # 主要指標資料
        metrics = {
            'pass': [v.get('pass', 0) for v in versions_data],
            'fail': [v.get('fail', 0) for v in versions_data],
            'pass_rate': [v.get('pass_rate', 0) for v in versions_data],
            'completion_rate': [v.get('completion_rate', 0) for v in versions_data]
        }
        
        # 按類別資料
        by_category = {}
        category_trends = trends.get('by_category', {})
        for category, cat_data in category_trends.items():
            by_category[category] = {
                'pass': cat_data.get('pass_values', []),
                'fail': cat_data.get('fail_values', [])
            }
        
        # 趨勢摘要
        trend_summary = {
            'pass': trends.get('pass', {}).get('trend', 'stable'),
            'fail': trends.get('fail', {}).get('trend', 'stable'),
            'pass_rate': trends.get('pass_rate', {}).get('trend', 'stable'),
            'completion_rate': trends.get('completion_rate', {}).get('trend', 'stable')
        }
        
        return {
            'chart_type': 'multi_version_trend',
            'project_name': project_name,
            'versions': version_names,
            'created_dates': created_dates,
            'metrics': metrics,
            'by_category': by_category,
            'trends': trend_summary,
            'version_count': len(versions_data)
        }
