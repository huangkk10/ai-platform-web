"""
系統監控備用實現

當主要的系統監控 library 不可用時，提供最小化的備用監控功能。
這個模組確保即使在最壞的情況下，系統仍然能提供基本的狀態信息。
"""

import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class FallbackSystemMonitor:
    """
    備用系統監控器 - 提供最基本的系統狀態檢查
    
    當主要的監控組件不可用時使用此類作為最後的備用方案。
    只提供最關鍵的功能：Django 運行狀態和資料庫連接檢查。
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def get_minimal_system_status(self, connection=None) -> Dict[str, Any]:
        """
        獲取最小化的系統狀態
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 最小化系統狀態字典
        """
        try:
            # 動態導入避免循環依賴
            if connection is None:
                from django.db import connection
            
            from django.utils import timezone
            
            # 檢查資料庫連接
            db_status = self._check_database_connection(connection)
            
            # 構建最小化響應
            status_dict = {
                'status': db_status['overall_status'],
                'timestamp': timezone.now().isoformat(),
                'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'services': {
                    'django': {'status': 'running'},
                    'database': {'status': db_status['database_status']}
                },
                'message': '使用簡化狀態檢查（library 不可用）',
                'fallback_mode': True
            }
            
            # 如果有錯誤信息，添加到響應中
            if 'error' in db_status:
                status_dict['database_error'] = db_status['error']
                
            return status_dict
            
        except Exception as e:
            self.logger.error(f"Fallback status check failed: {e}")
            
            # 最終的錯誤備用響應
            try:
                from django.utils import timezone
                timestamp = timezone.now().isoformat()
                server_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            except ImportError:
                timestamp = datetime.now().isoformat()
                server_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            return {
                'status': 'error',
                'timestamp': timestamp,
                'server_time': server_time,
                'error': f'備用狀態檢查失敗: {str(e)}',
                'fallback_mode': True,
                'services': {
                    'django': {'status': 'running'},  # 如果能執行到這裡，Django 肯定在運行
                    'database': {'status': 'error'}
                }
            }
    
    def _check_database_connection(self, connection) -> Dict[str, Any]:
        """
        檢查資料庫連接狀態
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 資料庫檢查結果
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            return {
                'database_status': 'healthy',
                'overall_status': 'healthy'
            }
            
        except Exception as e:
            self.logger.error(f"Database connection check failed: {str(e)}")
            return {
                'database_status': 'error',
                'overall_status': 'error',
                'error': str(e)
            }
    
    def get_basic_fallback_status(self, connection=None) -> Dict[str, Any]:
        """
        獲取基本備用狀態（用於 basic_system_status）
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 基本系統狀態字典
        """
        try:
            if connection is None:
                from django.db import connection
            
            from django.utils import timezone
            
            # 檢查資料庫
            db_check = self._check_database_connection(connection)
            
            # 獲取基本統計
            basic_stats = self._get_basic_statistics(connection)
            
            return {
                'status': db_check['overall_status'],
                'timestamp': timezone.now().isoformat(),
                'server_time': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'services': {
                    'django': {
                        'status': 'running',
                        'message': 'Django API 正常運行'
                    },
                    'database': {
                        'status': db_check['database_status'],
                        'message': '資料庫連接正常' if db_check['database_status'] == 'healthy' 
                                 else f"資料庫連接失敗: {db_check.get('error', '未知錯誤')}"
                    }
                },
                'statistics': basic_stats,
                'user_level': 'basic',
                'alerts': [] if db_check['database_status'] == 'healthy' else ['資料庫連接異常'],
                'fallback_mode': True
            }
            
        except Exception as e:
            self.logger.error(f"Basic fallback status failed: {str(e)}")
            return {
                'status': 'error',
                'error': f'獲取基本系統狀態失敗: {str(e)}',
                'fallback_mode': True
            }
    
    def _get_basic_statistics(self, connection) -> Dict[str, Any]:
        """
        獲取基本統計信息
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 基本統計信息
        """
        stats = {}
        
        try:
            with connection.cursor() as cursor:
                # 活躍用戶數
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_active = true")
                active_users = cursor.fetchone()[0]
                
                stats['active_users'] = {
                    'count': active_users,
                    'description': '系統中的活躍用戶數量'
                }
                
        except Exception as e:
            self.logger.warning(f"Failed to get basic statistics: {str(e)}")
            stats['error'] = f'統計數據獲取失敗: {str(e)}'
            
        return stats


def create_fallback_monitor() -> FallbackSystemMonitor:
    """
    創建備用系統監控器實例
    
    Returns:
        FallbackSystemMonitor: 備用監控器實例
    """
    return FallbackSystemMonitor()


# 便利函數 - 直接獲取最小化狀態（與原來的 _get_minimal_fallback_status 相容）
def get_minimal_fallback_status_dict(connection=None) -> Dict[str, Any]:
    """
    獲取最小化備用狀態字典 - 與原 views.py 中的函數相容
    
    Args:
        connection: Django database connection object
        
    Returns:
        Dict[str, Any]: 最小化系統狀態字典
    """
    monitor = create_fallback_monitor()
    return monitor.get_minimal_system_status(connection)


def get_basic_fallback_status_dict(connection=None) -> Dict[str, Any]:
    """
    獲取基本備用狀態字典 - 用於 basic_system_status
    
    Args:
        connection: Django database connection object
        
    Returns:
        Dict[str, Any]: 基本系統狀態字典
    """
    monitor = create_fallback_monitor()
    return monitor.get_basic_fallback_status(connection)