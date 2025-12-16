"""
DateHandler - 按日期/月份查詢專案
================================

處理 query_projects_by_date 和 query_projects_by_month 意圖。

支援的查詢：
- 「2025年12月有哪些專案」
- 「本月轉進的案子」
- 「上個月新增的專案」
- 「12月的案子」

作者：AI Platform Team
創建日期：2025-12-08
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class DateHandler(BaseHandler):
    """
    日期查詢處理器
    
    處理按日期或月份查詢專案的請求。
    """
    
    handler_name = "date_handler"
    supported_intent = "query_projects_by_date"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按日期查詢專案
        
        Args:
            parameters: {
                "year": 2025,           # 可選
                "month": 12,            # 可選
                "date": "2025-12-01",   # 可選，指定日期
                "date_range": "this_month" | "last_month" | "this_year",  # 可選
            }
            
        Returns:
            QueryResult: 包含符合日期條件的所有專案
        """
        self._log_query(parameters)
        
        try:
            # 解析日期範圍
            start_date, end_date, date_description = self._parse_date_parameters(parameters)
            
            if start_date is None or end_date is None:
                return QueryResult.error(
                    "無法解析日期參數，請指定年月或日期範圍",
                    self.handler_name,
                    parameters
                )
            
            logger.info(f"查詢日期範圍: {start_date} ~ {end_date} ({date_description})")
            
            # 獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message="無法獲取專案列表"
                )
            
            # 按日期過濾專案
            filtered_projects = self._filter_projects_by_date(
                projects_list, start_date, end_date
            )
            
            # 去重
            unique_projects = self._deduplicate_projects_by_name(filtered_projects)
            
            if not unique_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"{date_description}沒有新增的專案"
                )
            
            # 按日期排序（最新的在前）
            sorted_projects = sorted(
                unique_projects,
                key=lambda x: self._get_project_timestamp(x),
                reverse=True
            )
            
            # 格式化專案資料
            formatted_projects = [
                self._format_project_with_date(p) for p in sorted_projects
            ]
            
            # 按月份分組統計
            monthly_stats = self._group_by_month(sorted_projects)
            
            result_data = {
                'projects': formatted_projects,
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d'),
                    'description': date_description
                },
                'monthly_stats': monthly_stats,
                'total_count': len(formatted_projects)
            }
            
            result = QueryResult.success(
                data=result_data,
                count=len(formatted_projects),
                query_type=self.handler_name,
                parameters=parameters,
                message=f"{date_description}共有 {len(formatted_projects)} 個專案"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _parse_date_parameters(self, parameters: Dict[str, Any]) -> Tuple[Optional[datetime], Optional[datetime], str]:
        """
        解析日期參數，返回開始和結束日期
        
        Args:
            parameters: 查詢參數
            
        Returns:
            Tuple[start_date, end_date, description]: 日期範圍和描述
        """
        now = datetime.now()
        
        # 優先處理 date_range
        date_range = parameters.get('date_range', '').lower()
        
        if date_range == 'this_month' or date_range == '本月':
            start_date = datetime(now.year, now.month, 1)
            # 計算本月最後一天
            if now.month == 12:
                end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
            return start_date, end_date, "本月"
        
        elif date_range == 'last_month' or date_range == '上月' or date_range == '上個月':
            # 上個月（特指上一個完整的月份）
            if now.month == 1:
                start_date = datetime(now.year - 1, 12, 1)
                end_date = datetime(now.year, 1, 1) - timedelta(days=1)
            else:
                start_date = datetime(now.year, now.month - 1, 1)
                end_date = datetime(now.year, now.month, 1) - timedelta(days=1)
            return start_date, end_date, "上個月"
        
        elif date_range in ('recent_month', '近一個月', '最近一個月', '近30天', '近一月'):
            # 近一個月（從今天往回推 30 天）- 注意：這不是「上個月」！
            start_date = now - timedelta(days=30)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "近一個月"
        
        elif date_range in ('recent', '最近', '近期'):
            # 最近（30 天）
            start_date = now - timedelta(days=30)
            start_date = datetime(start_date.year, start_date.month, start_date.day)
            end_date = now
            return start_date, end_date, "最近 30 天"
        
        elif date_range == 'this_year' or date_range == '今年':
            start_date = datetime(now.year, 1, 1)
            end_date = datetime(now.year, 12, 31)
            return start_date, end_date, f"{now.year}年"
        
        # 處理年月參數
        year = parameters.get('year')
        month = parameters.get('month')
        
        if year and month:
            year = int(year)
            month = int(month)
            start_date = datetime(year, month, 1)
            
            # 計算該月最後一天
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            return start_date, end_date, f"{year}年{month}月"
        
        elif month:
            # 只有月份，假設是今年
            month = int(month)
            year = now.year
            
            # 如果指定月份大於當前月份，可能是指去年
            if month > now.month:
                year = now.year - 1
            
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            return start_date, end_date, f"{year}年{month}月"
        
        elif year:
            # 只有年份
            year = int(year)
            start_date = datetime(year, 1, 1)
            end_date = datetime(year, 12, 31)
            return start_date, end_date, f"{year}年"
        
        # 處理具體日期字串
        date_str = parameters.get('date')
        if date_str:
            try:
                # 嘗試多種日期格式
                for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d']:
                    try:
                        target_date = datetime.strptime(date_str, fmt)
                        return target_date, target_date, target_date.strftime('%Y年%m月%d日')
                    except ValueError:
                        continue
            except Exception:
                pass
        
        # 預設返回本月
        logger.warning("無法解析日期參數，使用預設值（本月）")
        start_date = datetime(now.year, now.month, 1)
        if now.month == 12:
            end_date = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
        return start_date, end_date, "本月"
    
    def _filter_projects_by_date(self, projects: List[Dict], 
                                  start_date: datetime, 
                                  end_date: datetime) -> List[Dict]:
        """
        按日期過濾專案
        
        Args:
            projects: 專案列表
            start_date: 開始日期
            end_date: 結束日期
            
        Returns:
            List[Dict]: 過濾後的專案列表
        """
        filtered = []
        
        # 轉換為 timestamp 範圍（含時間邊界）
        start_ts = start_date.timestamp()
        end_ts = (end_date + timedelta(days=1)).timestamp()  # 結束日期的次日開始
        
        for project in projects:
            created_at = project.get('createdAt', {})
            
            # 處理 SAF API 的時間戳格式
            # 格式: {'seconds': {'low': 1764269009, 'high': 0, 'unsigned': False}}
            if isinstance(created_at, dict):
                seconds = created_at.get('seconds', {})
                if isinstance(seconds, dict):
                    timestamp = seconds.get('low', 0)
                else:
                    timestamp = seconds if isinstance(seconds, (int, float)) else 0
            elif isinstance(created_at, (int, float)):
                timestamp = created_at
            else:
                continue
            
            # 檢查是否在範圍內
            if start_ts <= timestamp < end_ts:
                filtered.append(project)
        
        logger.info(f"日期過濾: {len(projects)} -> {len(filtered)} 個專案")
        return filtered
    
    def _get_project_timestamp(self, project: Dict) -> int:
        """
        獲取專案的創建時間戳
        
        Args:
            project: 專案資料
            
        Returns:
            int: Unix timestamp
        """
        created_at = project.get('createdAt', {})
        
        if isinstance(created_at, dict):
            seconds = created_at.get('seconds', {})
            if isinstance(seconds, dict):
                return seconds.get('low', 0)
            return seconds if isinstance(seconds, (int, float)) else 0
        elif isinstance(created_at, (int, float)):
            return int(created_at)
        
        return 0
    
    def _format_project_with_date(self, project: Dict) -> Dict[str, Any]:
        """
        格式化專案資料，包含日期資訊
        
        Args:
            project: 原始專案資料
            
        Returns:
            Dict: 格式化後的專案資料
        """
        timestamp = self._get_project_timestamp(project)
        created_date = ""
        
        if timestamp:
            try:
                dt = datetime.fromtimestamp(timestamp)
                created_date = dt.strftime('%Y-%m-%d')
            except Exception:
                pass
        
        return {
            'projectName': project.get('projectName', ''),
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'nand': project.get('nand', ''),
            'pl': project.get('pl', ''),
            'status': project.get('status', ''),
            'createdDate': created_date,  # 日期字串格式
            'createdAt': created_date,    # 保留舊的 key 以保持相容性
            'fw': project.get('fw', ''),
        }
    
    def _group_by_month(self, projects: List[Dict]) -> Dict[str, int]:
        """
        按月份分組統計專案數量
        
        Args:
            projects: 專案列表
            
        Returns:
            Dict: 月份 -> 專案數量
        """
        monthly = {}
        
        for project in projects:
            timestamp = self._get_project_timestamp(project)
            if timestamp:
                try:
                    dt = datetime.fromtimestamp(timestamp)
                    month_key = dt.strftime('%Y-%m')
                    monthly[month_key] = monthly.get(month_key, 0) + 1
                except Exception:
                    pass
        
        # 按月份排序
        return dict(sorted(monthly.items(), reverse=True))
