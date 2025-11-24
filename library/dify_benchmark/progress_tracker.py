"""
批量測試進度追蹤器

提供線程安全的進度追蹤機制，用於追蹤批量測試的執行進度。
支援多個批次同時執行，每個批次獨立追蹤進度。

作者: AI Platform Team
日期: 2025-11-24
"""

import threading
import time
import sys
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# 配置日誌
logger = logging.getLogger(__name__)

def _log_and_flush(level, message):
    """
    記錄日誌並強制刷新輸出緩衝
    
    解決 Python 日誌緩衝問題，確保日誌即時輸出
    """
    if level == 'info':
        logger.info(message)
    elif level == 'warning':
        logger.warning(message)
    elif level == 'error':
        logger.error(message)
    elif level == 'debug':
        logger.debug(message)
    
    # 強制刷新標準輸出和錯誤輸出
    sys.stdout.flush()
    sys.stderr.flush()


class BatchTestProgressTracker:
    """
    批量測試進度追蹤器 (Singleton)
    
    使用線程鎖確保多線程環境下的資料安全。
    追蹤資訊包括：
    - 整體進度（已完成/總數）
    - 當前執行的版本和測試案例
    - 每個版本的詳細進度
    - 預估剩餘時間
    - 執行狀態（running, completed, error）
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton 模式實作"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化進度追蹤器"""
        if self._initialized:
            return
        
        self._progress_data: Dict[str, Dict[str, Any]] = {}
        self._data_lock = threading.Lock()
        self._initialized = True
    
    def initialize_batch(
        self,
        batch_id: str,
        total_tests: int,
        versions: List[Dict[str, Any]],
        batch_name: str = None
    ) -> None:
        """
        初始化批次進度追蹤
        
        Args:
            batch_id: 批次唯一識別碼
            total_tests: 總測試數量
            versions: 版本列表 [{'id': 1, 'name': 'v1.0', 'test_count': 10}, ...]
            batch_name: 批次名稱
        """
        logger.info(
            f"📝 [ProgressTracker] 初始化批次追蹤: "
            f"batch_id={batch_id}, "
            f"total_tests={total_tests}, "
            f"versions={len(versions)}, "
            f"batch_name='{batch_name}'"
        )
        sys.stdout.flush()
        sys.stderr.flush()
        
        with self._data_lock:
            self._progress_data[batch_id] = {
                'batch_id': batch_id,
                'batch_name': batch_name or f'Batch {batch_id}',
                'status': 'running',
                'total_tests': total_tests,
                'completed_tests': 0,
                'failed_tests': 0,
                'current_version': None,
                'current_version_name': None,
                'current_test_case': None,
                'start_time': datetime.now().isoformat(),
                'end_time': None,
                'estimated_remaining_time': None,
                'versions': {
                    v['id']: {
                        'version_id': v['id'],
                        'version_name': v['name'],
                        'total_tests': v['test_count'],
                        'completed_tests': 0,
                        'failed_tests': 0,
                        'status': 'pending',  # pending, running, completed, error
                        'start_time': None,
                        'end_time': None,
                        'average_score': None,
                        'pass_rate': None
                    }
                    for v in versions
                },
                'error_message': None,
                'last_update': datetime.now().isoformat()
            }
            
            logger.info(
                f"✅ [ProgressTracker] 批次初始化完成: batch_id={batch_id}, "
                f"versions={list(self._progress_data[batch_id]['versions'].keys())}"
            )
            sys.stdout.flush()
            sys.stderr.flush()
    
    def update_progress(
        self,
        batch_id: str,
        completed_tests: int = None,
        failed_tests: int = None,
        current_version: int = None,
        current_version_name: str = None,
        current_test_case: str = None
    ) -> None:
        """
        更新整體進度
        
        Args:
            batch_id: 批次識別碼
            completed_tests: 已完成測試數（增量）
            failed_tests: 失敗測試數（增量）
            current_version: 當前執行版本 ID
            current_version_name: 當前版本名稱
            current_test_case: 當前測試案例名稱
        """
        with self._data_lock:
            if batch_id not in self._progress_data:
                logger.warning(f"⚠️ [ProgressTracker] 嘗試更新不存在的批次: {batch_id}")
                return
            
            progress = self._progress_data[batch_id]
            
            # 記錄更新前的數量
            old_completed = progress['completed_tests']
            
            # 更新計數
            if completed_tests is not None:
                progress['completed_tests'] += completed_tests
            if failed_tests is not None:
                progress['failed_tests'] += failed_tests
            
            # 更新當前執行資訊
            if current_version is not None:
                progress['current_version'] = current_version
            if current_version_name is not None:
                progress['current_version_name'] = current_version_name
            if current_test_case is not None:
                progress['current_test_case'] = current_test_case
            
            # 更新時間戳
            progress['last_update'] = datetime.now().isoformat()
            
            # 計算進度百分比
            progress_pct = (progress['completed_tests'] / progress['total_tests'] * 100) if progress['total_tests'] > 0 else 0
            
            # 只在測試完成數有變化時記錄日誌（避免過多日誌）
            if completed_tests is not None and completed_tests > 0:
                logger.info(
                    f"📊 [ProgressTracker] 進度更新: "
                    f"batch_id={batch_id}, "
                    f"progress={progress_pct:.1f}%, "
                    f"completed={progress['completed_tests']}/{progress['total_tests']}, "
                    f"failed={progress['failed_tests']}, "
                    f"current_version='{progress['current_version_name']}', "
                    f"current_test='{progress['current_test_case'][:50] if progress['current_test_case'] else None}...'"
                )
                sys.stdout.flush()
                sys.stderr.flush()
                progress['current_version'] = current_version
            if current_version_name is not None:
                progress['current_version_name'] = current_version_name
            if current_test_case is not None:
                progress['current_test_case'] = current_test_case
            
            # 計算預估剩餘時間
            if progress['completed_tests'] > 0:
                start_time = datetime.fromisoformat(progress['start_time'])
                elapsed_seconds = (datetime.now() - start_time).total_seconds()
                avg_time_per_test = elapsed_seconds / progress['completed_tests']
                remaining_tests = progress['total_tests'] - progress['completed_tests']
                progress['estimated_remaining_time'] = int(avg_time_per_test * remaining_tests)
            
            progress['last_update'] = datetime.now().isoformat()
    
    def update_version_progress(
        self,
        batch_id: str,
        version_id: int,
        completed_tests: int = None,
        failed_tests: int = None,
        status: str = None,
        average_score: float = None,
        pass_rate: float = None
    ) -> None:
        """
        更新特定版本的進度
        
        Args:
            batch_id: 批次識別碼
            version_id: 版本 ID
            completed_tests: 已完成測試數（增量）
            failed_tests: 失敗測試數（增量）
            status: 狀態 (pending, running, completed, error)
            average_score: 平均分數
            pass_rate: 通過率
        """
        with self._data_lock:
            if batch_id not in self._progress_data:
                return
            
            progress = self._progress_data[batch_id]
            if version_id not in progress['versions']:
                return
            
            version_progress = progress['versions'][version_id]
            
            # 更新計數
            if completed_tests is not None:
                version_progress['completed_tests'] += completed_tests
            if failed_tests is not None:
                version_progress['failed_tests'] += failed_tests
            
            # 更新狀態
            if status is not None:
                version_progress['status'] = status
                if status == 'running' and version_progress['start_time'] is None:
                    version_progress['start_time'] = datetime.now().isoformat()
                elif status in ['completed', 'error']:
                    version_progress['end_time'] = datetime.now().isoformat()
            
            # 更新測試結果
            if average_score is not None:
                version_progress['average_score'] = round(average_score, 2)
            if pass_rate is not None:
                version_progress['pass_rate'] = round(pass_rate, 2)
            
            progress['last_update'] = datetime.now().isoformat()
    
    def mark_completed(
        self,
        batch_id: str,
        success: bool = True,
        error_message: str = None
    ) -> None:
        """
        標記批次完成
        
        Args:
            batch_id: 批次識別碼
            success: 是否成功完成
            error_message: 錯誤訊息（如果失敗）
        """
        with self._data_lock:
            if batch_id not in self._progress_data:
                return
            
            progress = self._progress_data[batch_id]
            progress['status'] = 'completed' if success else 'error'
            progress['end_time'] = datetime.now().isoformat()
            progress['estimated_remaining_time'] = 0
            
            if error_message:
                progress['error_message'] = error_message
            
            progress['last_update'] = datetime.now().isoformat()
    
    def get_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取批次進度資料
        
        Args:
            batch_id: 批次識別碼
            
        Returns:
            進度資料字典，如果不存在則返回 None
        """
        with self._data_lock:
            if batch_id not in self._progress_data:
                return None
            
            # 返回深拷貝，避免外部修改
            import copy
            return copy.deepcopy(self._progress_data[batch_id])
    
    def cleanup_batch(self, batch_id: str) -> None:
        """
        清理批次資料（測試完成後呼叫）
        
        Args:
            batch_id: 批次識別碼
        """
        with self._data_lock:
            if batch_id in self._progress_data:
                del self._progress_data[batch_id]
    
    def get_all_active_batches(self) -> List[str]:
        """
        獲取所有執行中的批次 ID
        
        Returns:
            批次 ID 列表
        """
        with self._data_lock:
            return [
                batch_id 
                for batch_id, data in self._progress_data.items()
                if data['status'] == 'running'
            ]


# 全局單例實例
progress_tracker = BatchTestProgressTracker()
