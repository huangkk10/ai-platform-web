"""
系統監控模組

提供系統狀態檢查、服務健康監控和基本統計信息收集功能。
適用於 Django Web 應用的系統監控需求。
"""

from .service_monitor import ServiceMonitor, ServiceStatus, create_service_monitor
from .system_stats import SystemStatsCollector, create_stats_collector  
from .health_checker import HealthChecker, create_health_checker
from .resource_monitor import SystemResourceMonitor, create_resource_monitor
from .admin_monitor import AdminSystemMonitor, create_admin_monitor
from .remote_db_monitor import RemoteDatabaseMonitor, create_remote_db_monitor, HostDiskInfo
from .fallback_monitor import (
    FallbackSystemMonitor, 
    create_fallback_monitor,
    get_minimal_fallback_status_dict,
    get_basic_fallback_status_dict
)

# 日誌管理功能
LOG_MANAGEMENT_AVAILABLE = True
try:
    from .log_reader import LogFileReader
    from .log_parser import LogLineParser
except ImportError as e:
    LOG_MANAGEMENT_AVAILABLE = False
    LogFileReader = None
    LogLineParser = None

__all__ = [
    'ServiceMonitor',
    'ServiceStatus', 
    'SystemStatsCollector',
    'HealthChecker',
    'SystemResourceMonitor',
    'AdminSystemMonitor',
    'RemoteDatabaseMonitor',
    'FallbackSystemMonitor',
    'create_service_monitor',
    'create_stats_collector',
    'create_health_checker',
    'create_resource_monitor',
    'create_admin_monitor',
    'create_remote_db_monitor',
    'create_fallback_monitor',
    'get_minimal_fallback_status_dict',
    'get_basic_fallback_status_dict',
    # 日誌管理
    'LOG_MANAGEMENT_AVAILABLE',
    'LogFileReader',
    'LogLineParser',
]