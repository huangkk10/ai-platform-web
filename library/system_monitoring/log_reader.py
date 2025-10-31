"""
日誌檔案讀取器 (Log File Reader)
提供高效的日誌檔案讀取功能

功能：
- 列出所有可用的日誌檔案
- 從檔案尾部讀取指定行數（tail）
- 讀取完整檔案內容
- 檔案統計資訊
- 安全性驗證（防止路徑遍歷攻擊）
"""

import os
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class LogFileReader:
    """高效的日誌檔案讀取器"""
    
    # 日誌檔案目錄
    LOG_DIR = Path('/app/logs')
    
    # 允許訪問的日誌檔案列表（白名單機制）
    ALLOWED_LOG_FILES = {
        'django.log': 'general',
        'django_error.log': 'error',
        'dify_requests.log': 'dify',
        'rvt_analytics.log': 'analytics',
        'vector_operations.log': 'vector',
        'api_access.log': 'access',
        'celery.log': 'celery',
        'protocol_analytics.log': 'analytics',
    }
    
    @classmethod
    def list_log_files(cls) -> List[Dict]:
        """列出所有可用的日誌檔案"""
        files = []
        
        for filename, file_type in cls.ALLOWED_LOG_FILES.items():
            try:
                filepath = cls.LOG_DIR / filename
                
                if filepath.exists():
                    stat = filepath.stat()
                    
                    files.append({
                        'name': filename,
                        'path': str(filepath),
                        'size': stat.st_size,
                        'size_human': cls._format_size(stat.st_size),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'line_count': cls._count_lines(filepath),
                        'type': file_type
                    })
            except Exception as e:
                logger.warning(f"讀取日誌檔案資訊失敗 {filename}: {str(e)}")
        
        return files
    
    @classmethod
    def read_tail(cls, filename: str, lines: int = 100) -> List[str]:
        """從檔案尾部讀取指定行數"""
        filepath = cls._validate_and_get_path(filename)
        
        try:
            with open(filepath, 'rb') as f:
                f.seek(0, os.SEEK_END)
                file_size = f.tell()
                
                if file_size == 0:
                    return []
                
                buffer_size = 8192
                lines_found = []
                buffer = b''
                
                for offset in range(file_size, 0, -buffer_size):
                    read_size = min(buffer_size, offset)
                    f.seek(max(0, offset - buffer_size))
                    chunk = f.read(read_size)
                    
                    buffer = chunk + buffer
                    lines_in_buffer = buffer.split(b'\n')
                    
                    if len(lines_in_buffer) > 1:
                        lines_found = lines_in_buffer[1:] + lines_found
                        if len(lines_found) >= lines:
                            break
                        buffer = lines_in_buffer[0]
                
                result_lines = [
                    line.decode('utf-8', errors='ignore').strip() 
                    for line in lines_found[-lines:] 
                    if line.strip()
                ]
                
                return result_lines
                
        except Exception as e:
            logger.error(f"讀取日誌檔案失敗 {filename}: {str(e)}")
            raise
    
    @classmethod
    def read_all(cls, filename: str, max_lines: Optional[int] = None) -> List[str]:
        """讀取完整檔案內容"""
        filepath = cls._validate_and_get_path(filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = []
                for i, line in enumerate(f):
                    if max_lines and i >= max_lines:
                        break
                    line = line.strip()
                    if line:
                        lines.append(line)
                
                return lines
                
        except Exception as e:
            logger.error(f"讀取日誌檔案失敗 {filename}: {str(e)}")
            raise
    
    @classmethod
    def get_file_stats(cls, filename: str) -> Dict:
        """獲取日誌檔案統計資訊"""
        filepath = cls._validate_and_get_path(filename)
        
        try:
            stat = filepath.stat()
            
            return {
                'name': filename,
                'size': stat.st_size,
                'size_human': cls._format_size(stat.st_size),
                'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'line_count': cls._count_lines(filepath),
                'encoding': 'utf-8'
            }
        except Exception as e:
            logger.error(f"獲取檔案統計失敗 {filename}: {str(e)}")
            raise
    
    @classmethod
    def _validate_and_get_path(cls, filename: str) -> Path:
        """驗證檔案名並返回完整路徑"""
        if filename not in cls.ALLOWED_LOG_FILES:
            raise ValueError(f"Invalid log file: {filename}")
        
        filepath = (cls.LOG_DIR / filename).resolve()
        
        if not str(filepath).startswith(str(cls.LOG_DIR.resolve())):
            raise ValueError("Path traversal attempt detected")
        
        if not filepath.exists():
            raise FileNotFoundError(f"Log file not found: {filename}")
        
        return filepath
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """格式化檔案大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def _count_lines(filepath: Path) -> int:
        """計算檔案行數"""
        try:
            with open(filepath, 'rb') as f:
                count = sum(1 for _ in f)
            return count
        except Exception:
            return 0
