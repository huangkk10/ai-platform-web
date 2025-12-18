"""
ListFWByDateRangeHandler - 按日期範圍列出專案的 FW 版本
======================================================

處理 Phase 13 按日期範圍查詢專案 FW 版本意圖：
- list_fw_by_date_range: 查詢專案在指定日期範圍內有哪些 FW 版本

功能：
- 支援年月查詢：「Springsteen 12月有哪些 FW」
- 支援月份範圍：「Springsteen 2025年10月到12月的 FW」
- 支援相對時間：「Springsteen 本月的 FW」、「Springsteen 上個月的 FW」
- 支援最近查詢：「Springsteen 最近一週的 FW」

優化策略：
- 複用 ListFWVersionsHandler 的 FW 版本獲取邏輯
- 基於創建時間進行日期過濾
- 按日期排序（最新的在前）

作者：AI Platform Team
創建日期：2025-01-20
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class ListFWByDateRangeHandler(BaseHandler):
    """
    按日期範圍列出專案 FW 版本處理器
    
    支援的意圖：
    - list_fw_by_date_range: 查詢專案在指定日期範圍內有哪些 FW 版本
    
    功能：
    1. 解析日期範圍參數（年月、相對時間等）
    2. 獲取專案所有 FW 版本
    3. 按日期過濾 FW 版本
    4. 格式化輸出
    """
    
    handler_name = "list_fw_by_date_range_handler"
    supported_intent = "list_fw_by_date_range"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按日期範圍查詢專案 FW 版本
        
        Args:
            parameters: {
                "project_name": "Springsteen",    # 必須
                "year": 2025,                     # 可選
                "month": 12,                      # 可選
                "start_month": 10,                # 可選（範圍查詢）
                "end_month": 12,                  # 可選（範圍查詢）
                "date_range": "this_month" | "last_month" | "this_week" | "last_week",  # 可選
            }
            
        Returns:
            QueryResult: 包含符合日期條件的 FW 版本列表
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['project_name'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        
        try:
            # Step 1: 解析日期範圍
            start_date, end_date, date_description = self._parse_date_parameters(parameters)
            
            if start_date is None or end_date is None:
                return QueryResult.error(
                    "無法解析日期參數，請指定年月或日期範圍",
                    self.handler_name,
                    parameters
                )
            
            logger.info(f"查詢專案 {project_name} 的 FW 版本，日期範圍: {start_date} ~ {end_date} ({date_description})")
            
            # Step 2: 獲取所有專案列表
            all_projects = self.api_client.get_all_projects(flatten=True)
            
            if not all_projects:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # Step 3: 找到所有匹配專案名稱的專案（作為 FW 版本）
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
            
            # Step 3.5: 按 Sub Version 過濾（如果有指定）
            sub_version = parameters.get('sub_version')
            if sub_version:
                sub_version_upper = sub_version.upper()
                matching_projects = self._filter_by_sub_version(
                    matching_projects, sub_version_upper
                )
                
                if not matching_projects:
                    return QueryResult.error(
                        f"找不到專案 {project_name} 的 {sub_version} 版本",
                        self.handler_name,
                        parameters
                    )
                
                logger.info(f"Sub Version 過濾後: {len(matching_projects)} 個 FW 版本")
            
            # Step 4: 按日期過濾
            filtered_projects = self._filter_by_date(
                matching_projects, start_date, end_date
            )
            
            # Step 5: 按建立時間排序（最新的在前）
            filtered_projects.sort(
                key=lambda x: self._get_timestamp(x.get('createdAt')),
                reverse=True
            )
            
            # Step 6: 格式化 FW 版本資訊
            fw_versions = self._format_fw_versions(filtered_projects)
            
            if not fw_versions:
                sub_version_desc = f" {sub_version} 版本" if sub_version else ""
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"專案 {project_name}{sub_version_desc} 在 {date_description} 沒有任何 FW 版本"
                )
            
            # Step 7: 生成回應訊息
            message = self._format_response(
                project_name,
                fw_versions,
                date_description,
                start_date,
                end_date,
                len(matching_projects),
                sub_version=sub_version
            )
            
            # 提取第一個專案的基本資訊作為代表
            first_project = filtered_projects[0] if filtered_projects else matching_projects[0]
            
            return QueryResult.success(
                data={
                    'project_name': project_name,
                    'sub_version': sub_version,
                    'fw_versions': fw_versions,
                    'date_range': {
                        'start': start_date.strftime('%Y-%m-%d'),
                        'end': end_date.strftime('%Y-%m-%d'),
                        'description': date_description
                    },
                    'total_in_range': len(fw_versions),
                    'total_all_versions': len(matching_projects)
                },
                count=len(fw_versions),
                query_type=self.handler_name,
                parameters=parameters,
                message=message,
                metadata={
                    'project_name': first_project.get('projectName'),
                    'customer': first_project.get('customer'),
                    'controller': first_project.get('controller'),
                    'date_description': date_description,
                    'sub_version': sub_version
                }
            )
            
        except Exception as e:
            logger.error(f"按日期查詢 FW 版本錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _parse_date_parameters(self, parameters: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """
        解析日期參數，返回開始和結束日期
        
        支援的參數格式：
        1. date_range: "this_month", "last_month", "this_week", "last_week"
        2. year + month: 指定年月
        3. year + start_month + end_month: 指定月份範圍
        4. month: 只有月份（假設是今年）
        
        Args:
            parameters: 查詢參數
            
        Returns:
            Tuple[start_date, end_date, description]: 日期範圍和描述
        """
        now = datetime.now()
        
        # 優先處理 date_range
        date_range = parameters.get('date_range', '').lower()
        
        if date_range in ('this_month', '本月'):
            start_date = datetime(now.year, now.month, 1)
            end_date = self._get_month_end(now.year, now.month)
            return start_date, end_date, "本月"
        
        elif date_range in ('last_month', '上月', '上個月'):
            if now.month == 1:
                start_date = datetime(now.year - 1, 12, 1)
                end_date = self._get_month_end(now.year - 1, 12)
            else:
                start_date = datetime(now.year, now.month - 1, 1)
                end_date = self._get_month_end(now.year, now.month - 1)
            return start_date, end_date, "上個月"
        
        elif date_range in ('this_week', '本週', '本周'):
            # 本週一到今天
            start_of_week = now - timedelta(days=now.weekday())
            start_date = datetime(start_of_week.year, start_of_week.month, start_of_week.day)
            end_date = now
            return start_date, end_date, "本週"
        
        elif date_range in ('last_week', '上週', '上周'):
            # 上週一到上週日
            start_of_this_week = now - timedelta(days=now.weekday())
            end_date = start_of_this_week - timedelta(days=1)
            start_date = end_date - timedelta(days=6)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            return start_date, end_date, "上週"
        
        elif date_range in ('this_year', '今年'):
            # 今年
            start_date = datetime(now.year, 1, 1)
            end_date = datetime(now.year, 12, 31, 23, 59, 59)
            return start_date, end_date, "今年"
        
        elif date_range in ('last_year', '去年'):
            # 去年
            start_date = datetime(now.year - 1, 1, 1)
            end_date = datetime(now.year - 1, 12, 31, 23, 59, 59)
            return start_date, end_date, "去年"
        
        elif date_range in ('recent', '最近', '近期'):
            # 最近一個月（30 天）
            start_date = now - timedelta(days=30)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "最近 30 天"
        
        elif date_range in ('recent_month', '近一個月', '最近一個月', '近30天', '近一月'):
            # 近一個月（從今天往回推 30 天）- 注意：這不是「上個月」！
            start_date = now - timedelta(days=30)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "近一個月"
        
        elif date_range in ('last_2_months', '近2個月', '近兩個月', '最近2個月', '最近兩個月', '近二個月'):
            # 近兩個月（從今天往回推 60 天）
            start_date = now - timedelta(days=60)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "近 2 個月"
        
        elif date_range in ('last_3_months', '近3個月', '近三個月', '最近3個月', '最近三個月'):
            # 近三個月（從今天往回推 90 天）
            start_date = now - timedelta(days=90)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "近 3 個月"
        
        elif date_range in ('last_6_months', '近6個月', '近半年', '最近6個月', '最近半年'):
            # 近半年（從今天往回推 180 天）
            start_date = now - timedelta(days=180)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "近半年"
        
        # 處理年月範圍參數
        year = parameters.get('year')
        month = parameters.get('month')
        start_month = parameters.get('start_month')
        end_month = parameters.get('end_month')
        
        # 處理月份範圍 (start_month + end_month，可選 year)
        if start_month and end_month:
            start_month = int(start_month)
            end_month = int(end_month)
            
            # 如果沒有指定年份，使用智能推斷
            if year:
                inferred_year = int(year)
            else:
                # 智能推斷年份：
                # 1. 如果結束月份 > 當前月份，可能是去年
                # 2. 否則使用今年
                if end_month > now.month:
                    inferred_year = now.year - 1
                else:
                    inferred_year = now.year
            
            start_date = datetime(inferred_year, start_month, 1)
            end_date = self._get_month_end(inferred_year, end_month)
            return start_date, end_date, f"{inferred_year}年{start_month}月到{end_month}月"
        
        # 處理單一年月參數 (year + month)
        if year and month:
            year = int(year)
            month = int(month)
            start_date = datetime(year, month, 1)
            end_date = self._get_month_end(year, month)
            return start_date, end_date, f"{year}年{month}月"
        
        # 只有月份（假設是今年，但如果月份大於當前月份則是去年）
        if month:
            month = int(month)
            year = now.year
            # 如果指定月份大於當前月份，可能是指去年
            if month > now.month:
                year = now.year - 1
            start_date = datetime(year, month, 1)
            end_date = self._get_month_end(year, month)
            return start_date, end_date, f"{year}年{month}月"
        
        # 只有年份
        if year:
            year = int(year)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31, 23, 59, 59)
            return start_date, end_date, f"{year}年"
        
        # 預設返回本月
        logger.warning("無法解析日期參數，使用預設值（本月）")
        start_date = datetime(now.year, now.month, 1)
        end_date = self._get_month_end(now.year, now.month)
        return start_date, end_date, "本月"
    
    def _get_month_end(self, year: int, month: int) -> datetime:
        """獲取指定月份的最後一天"""
        if month == 12:
            return datetime(year + 1, 1, 1) - timedelta(seconds=1)
        else:
            return datetime(year, month + 1, 1) - timedelta(seconds=1)
    
    def _filter_by_date(self, projects: List[Dict],
                        start_date: datetime,
                        end_date: datetime) -> List[Dict]:
        """
        按日期過濾專案列表
        
        Args:
            projects: 專案列表
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            List[Dict]: 過濾後的專案列表
        """
        filtered = []
        
        start_ts = start_date.timestamp()
        end_ts = end_date.timestamp()
        
        for project in projects:
            timestamp = self._get_timestamp(project.get('createdAt'))
            if timestamp and start_ts <= timestamp <= end_ts:
                filtered.append(project)
        
        logger.info(f"日期過濾: {len(projects)} -> {len(filtered)} 個 FW 版本")
        return filtered
    
    def _filter_by_sub_version(self, projects: List[Dict], 
                                sub_version: str) -> List[Dict]:
        """
        按 Sub Version 過濾 FW 版本
        
        Sub Version 是 FW 版本中的一個標識碼，通常表示容量版本：
        - AA: 512GB
        - AB: 1024GB/1TB
        - AC: 2048GB/2TB
        - AD: 4096GB/4TB
        
        過濾邏輯：
        1. 檢查 FW 欄位中是否包含 _SubVersion（如 _AC, _AA）
        2. 檢查 SubVersion 欄位（如果存在）
        
        Args:
            projects: 專案列表
            sub_version: Sub Version 代碼（如 AA、AB、AC、AD）
            
        Returns:
            List[Dict]: 過濾後的專案列表
        """
        if not sub_version:
            return projects
        
        filtered = []
        sub_version_upper = sub_version.upper()
        
        for project in projects:
            fw = project.get('fw', '')
            project_sub_version = project.get('subVersion', '')
            
            # 方法 1：檢查 FW 欄位中是否包含 _SubVersion
            # 例如：PH10YC3H_Pyrite_4K 中的 Pyrite 代表 AC
            # 或者 GD10YBJD_Opal 中的 Opal 代表 AC
            # 或直接包含 _AC、_AA 等
            if f'_{sub_version_upper}' in fw.upper():
                filtered.append(project)
                continue
            
            # 方法 2：檢查 subVersion 欄位（如果存在）
            if project_sub_version and project_sub_version.upper() == sub_version_upper:
                filtered.append(project)
                continue
            
            # 方法 3：特殊映射（容量名稱到 Sub Version 代碼）
            # Opal/Pyrite 等通常代表不同的容量版本
            capacity_mapping = {
                'OPAL': 'AC',      # Opal 通常是 AC (2TB)
                'PYRITE': 'AC',   # Pyrite 通常是 AC
                '512': 'AA',
                '512GB': 'AA',
                '1024': 'AB',
                '1TB': 'AB',
                '2048': 'AC',
                '2TB': 'AC',
                '4096': 'AD',
                '4TB': 'AD',
            }
            
            for keyword, mapped_sv in capacity_mapping.items():
                if keyword in fw.upper() and mapped_sv == sub_version_upper:
                    filtered.append(project)
                    break
        
        return filtered
    
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
                seconds = created_at.get('seconds', {})
                if isinstance(seconds, dict):
                    return seconds.get('low', 0)
                elif isinstance(seconds, int):
                    return seconds
                return 0
            elif isinstance(created_at, str):
                from datetime import datetime as dt
                d = dt.fromisoformat(created_at.replace('Z', '+00:00'))
                return int(d.timestamp())
            elif isinstance(created_at, (int, float)):
                return int(created_at)
            else:
                return 0
        except Exception:
            return 0
    
    # 狀態碼對應表（SAF 系統定義）
    STATUS_MAPPING = {
        0: '進行中',      # In Progress
        1: '待處理',      # Pending (reserved)
        2: '已暫停',      # Paused
        3: '已完成',      # Completed
    }
    
    def _get_status_text(self, status_code: Any) -> str:
        """
        將狀態碼轉換為可讀文字
        
        Args:
            status_code: 狀態碼
            
        Returns:
            狀態文字描述
        """
        try:
            status_int = int(status_code) if status_code is not None else 0
            return self.STATUS_MAPPING.get(status_int, f'未知({status_code})')
        except (ValueError, TypeError):
            return f'未知({status_code})'
    
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
                dt = datetime.fromtimestamp(timestamp)
                return dt.strftime('%Y-%m-%d')
            return 'N/A'
        except Exception:
            return 'N/A'
    
    def _format_fw_versions(self, projects: List[Dict]) -> List[Dict]:
        """
        格式化 FW 版本資訊
        
        Args:
            projects: 專案列表
            
        Returns:
            FW 版本資訊列表
        """
        fw_versions = []
        
        for project in projects:
            fw_version = project.get('fw', project.get('projectName', 'N/A'))
            created_at_raw = project.get('createdAt', '')
            created_date = self._format_timestamp(created_at_raw)
            
            # 轉換狀態碼為可讀文字
            status_code = project.get('status', 0)
            status_text = self._get_status_text(status_code)
            
            # 提取 Sub-Version（多種可能的欄位名稱或從 FW 版本中提取）
            sub_version = (
                project.get('subVersion') or 
                project.get('sub_version') or 
                self._extract_sub_version_from_fw(fw_version) or
                'N/A'
            )
            
            fw_info = {
                'fw_version': fw_version,
                'fw': fw_version,
                'project_uid': project.get('projectUid'),
                'project_name': project.get('projectName', ''),
                'customer': project.get('customer', ''),
                'controller': project.get('controller', 'N/A'),
                'sub_version': sub_version,
                'created_date': created_date,
                'status': status_text,
                'status_code': status_code,
            }
            fw_versions.append(fw_info)
        
        return fw_versions
    
    def _extract_sub_version_from_fw(self, fw_version: str) -> Optional[str]:
        """
        從 FW 版本字串中提取 Sub-Version
        
        例如：
        - "G200X6EC_AA" -> "AA"
        - "Y1114B_AC" -> "AC"
        - "PH10YC3H_Opal_4K" -> "Opal"
        - "HHB0YBC1" -> None
        """
        import re
        if not fw_version or '_' not in fw_version:
            return None
        
        # 匹配 _AA, _AB, _AC, _AD 等常見 Sub-Version 格式
        match = re.search(r'_([A-Z]{2})(?:_|$)', fw_version)
        if match:
            return match.group(1)
        
        # 匹配 _Opal, _Pyrite 等格式
        parts = fw_version.split('_')
        if len(parts) >= 2:
            # 返回第二部分（通常是 Sub-Version 或類型）
            return parts[1] if parts[1] else None
        
        return None
    
    def _format_response(self, project_name: str,
                         fw_versions: List[Dict],
                         date_description: str,
                         start_date: datetime,
                         end_date: datetime,
                         total_versions: int,
                         sub_version: str = None) -> str:
        """
        格式化回應訊息
        
        Args:
            project_name: 專案名稱
            fw_versions: FW 版本列表
            date_description: 日期描述
            start_date: 開始日期
            end_date: 結束日期
            total_versions: 專案總 FW 版本數
            sub_version: Sub Version 代碼（可選）
            
        Returns:
            格式化的回應訊息
        """
        lines = []
        
        # 標題（包含 Sub Version 如果有的話）
        sub_version_text = f" {sub_version}" if sub_version else ""
        lines.append(f"## 📅 專案 {project_name}{sub_version_text} - {date_description} 的 FW 版本")
        lines.append("")
        
        # 日期範圍資訊
        lines.append(f"**查詢日期範圍**: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
        if sub_version:
            lines.append(f"**Sub Version**: {sub_version}")
        lines.append(f"**符合條件**: {len(fw_versions)} 個版本（專案共有 {total_versions} 個版本）")
        lines.append("")
        
        # FW 版本列表
        if fw_versions:
            lines.append("### FW 版本列表")
            lines.append("")
            lines.append("| # | FW 版本 | Sub-Version | Controller | 建立日期 | 狀態 |")
            lines.append("|---|---------|-------------|------------|----------|------|")
            
            for i, fw in enumerate(fw_versions, 1):
                fw_version = fw.get('fw_version', 'N/A')
                sub_ver = fw.get('sub_version', 'N/A')
                controller = fw.get('controller', 'N/A')
                created_date = fw.get('created_date', 'N/A')
                status = fw.get('status', 'N/A')
                lines.append(f"| {i} | {fw_version} | {sub_ver} | {controller} | {created_date} | {status} |")
            
            lines.append("")
            
            # 提供後續查詢建議
            lines.append("### 💡 後續查詢建議")
            lines.append("")
            if len(fw_versions) >= 2:
                fw1 = fw_versions[0].get('fw_version', '')
                fw2 = fw_versions[1].get('fw_version', '')
                lines.append(f"- 「{project_name} {fw1} 和 {fw2} 的差異」- 比較兩個版本")
            if len(fw_versions) >= 1:
                fw1 = fw_versions[0].get('fw_version', '')
                lines.append(f"- 「{project_name} {fw1} 的測試結果」- 查看測試狀態")
                lines.append(f"- 「{project_name} {fw1} 的詳細統計」- 查看完成率和樣本數")
        
        return "\n".join(lines)
