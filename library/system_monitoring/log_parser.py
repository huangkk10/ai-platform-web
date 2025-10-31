"""
日誌解析器 (Log Parser)
解析 Django 日誌格式並提供過濾功能

支援的日誌格式：
[LEVEL] TIMESTAM        # 先嘗試用正則表達式匹配標準日誌格式
        match = cls.LOG_PATTERN.match(line)
        
        # 如果不匹配標準格式，則視為延續行（不顯示 level 標籤）
        if not match:
            return {
                'line_number': line_number,
                'level': None,  # 不顯示 level 標籤
                'timestamp': None,
                'module': None,
                'function': None,
                'source_line': None,
                'message': line,
                'raw_line': line,
                'is_continuation': True,
                'is_unknown': False
            }TION | Line NUMBER | MESSAGE
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LogLineParser:
    """日誌行解析器"""
    
    # Django 日誌格式正則表達式
    LOG_PATTERN = re.compile(
        r'\[(?P<level>\w+)\]\s+'
        r'(?P<timestamp>[\d\-:\.,\s]+)\s+'
        r'(?P<module>[\w\.]+)\s+'
        r'(?P<message>.+)'
    )
    
    # 簡化格式（部分日誌可能沒有完整結構）
    SIMPLE_PATTERN = re.compile(
        r'\[(?P<level>\w+)\]\s+'
        r'(?P<timestamp>[\d\-:\.,\s]+)\s+'
        r'(?P<message>.+)'
    )
    
    # 日誌級別顏色映射
    LEVEL_COLORS = {
        'DEBUG': 'gray',
        'INFO': 'blue',
        'WARNING': 'orange',
        'ERROR': 'red',
        'CRITICAL': 'purple',
        'CONTINUATION': 'cyan',  # 多行日誌的延續行
        'UNKNOWN': 'default'
    }
    
    @classmethod
    def parse_line(cls, line: str, line_number: int) -> dict:
        """
        解析單行日誌，返回結構化數據
        
        Args:
            line: 日誌行內容
            line_number: 行號
            
        Returns:
            包含解析結果的字典
        """
        if not line.strip():
            return {
                'line_number': line_number,
                'level': None,  # 空行不顯示 level
                'timestamp': None,
                'module': None,
                'function': None,
                'source_line': None,
                'message': '',
                'raw_line': line,
                'is_continuation': False,
                'is_unknown': False
            }
        
        # 嘗試匹配完整格式：[LEVEL] TIMESTAMP | MODULE | ...
        match = cls.LOG_PATTERN.match(line)
        if match:
            return {
                'line_number': line_number,
                'level': match.group('level'),
                'timestamp': match.group('timestamp').strip(),
                'module': match.group('module'),
                'function': None,
                'source_line': None,
                'message': match.group('message').strip(),
                'raw_line': line,
                'is_continuation': False,
                'is_unknown': False
            }
        
        # 嘗試匹配簡化格式：[LEVEL] TIMESTAMP MESSAGE
        simple_match = cls.SIMPLE_PATTERN.match(line)
        if simple_match:
            return {
                'line_number': line_number,
                'level': simple_match.group('level'),
                'timestamp': simple_match.group('timestamp').strip(),
                'module': None,
                'function': None,
                'source_line': None,
                'message': simple_match.group('message').strip(),
                'raw_line': line,
                'is_continuation': False,
                'is_unknown': False
            }
        
        # 如果都不匹配，視為延續行（不顯示 level 標籤）
        # 這包括：多行日誌的後續行、異常堆疊、以及任何非標準格式的行
        return {
            'line_number': line_number,
            'level': None,  # 不顯示 level 標籤
            'timestamp': None,
            'module': None,
            'function': None,
            'source_line': None,
            'message': line,
            'raw_line': line,
            'is_continuation': True,
            'is_unknown': False
        }
    
    @classmethod
    def parse_lines(cls, lines: List[str], start_line: int = 1) -> List[Dict]:
        """批量解析日誌行"""
        parsed_lines = []
        
        for i, line in enumerate(lines, start=start_line):
            parsed = cls.parse_line(line, i)
            if parsed:
                parsed_lines.append(parsed)
        
        return parsed_lines
    
    @classmethod
    def filter_by_level(cls, parsed_lines: List[Dict], level: str) -> List[Dict]:
        """按日誌級別過濾"""
        if not level or level.upper() == 'ALL':
            return parsed_lines
        
        return [
            line for line in parsed_lines 
            if line.get('level') and line['level'].upper() == level.upper()
        ]
    
    @classmethod
    def filter_by_keyword(cls, parsed_lines: List[Dict], keyword: str) -> List[Dict]:
        """按關鍵字過濾"""
        if not keyword:
            return parsed_lines
        
        keyword_lower = keyword.lower()
        return [
            line for line in parsed_lines 
            if keyword_lower in (line.get('message') or '').lower() 
            or keyword_lower in (line.get('module') or '').lower()
        ]
    
    @classmethod
    def filter_by_date_range(cls, parsed_lines: List[Dict], 
                           start_date: Optional[str] = None,
                           end_date: Optional[str] = None) -> List[Dict]:
        """按日期範圍過濾"""
        if not start_date and not end_date:
            return parsed_lines
        
        filtered = []
        for line in parsed_lines:
            try:
                # 嘗試解析時間戳
                timestamp_str = line['timestamp'].strip()
                if not timestamp_str:
                    continue
                
                # 簡單的日期比較（可根據實際格式調整）
                if start_date and timestamp_str < start_date:
                    continue
                if end_date and timestamp_str > end_date:
                    continue
                
                filtered.append(line)
            except Exception:
                # 無法解析時間戳則跳過
                continue
        
        return filtered
    
    @classmethod
    def get_level_statistics(cls, parsed_lines: List[Dict]) -> Dict:
        """統計各級別日誌數量"""
        stats = {
            'DEBUG': 0,
            'INFO': 0,
            'WARNING': 0,
            'ERROR': 0,
            'CRITICAL': 0,
            'UNKNOWN': 0
        }
        
        for line in parsed_lines:
            level = line.get('level')
            
            # 跳過沒有 level 的行（如延續行、空行）
            if level is None:
                continue
            
            level_upper = level.upper()
            if level_upper in stats:
                stats[level_upper] += 1
            else:
                stats['UNKNOWN'] += 1
        
        return stats
