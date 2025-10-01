"""
健康檢查器

提供系統整體健康狀態檢查功能，整合各種監控組件。
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

from .service_monitor import ServiceMonitor, ServiceStatus, ServiceInfo
from .system_stats import SystemStatsCollector, StatItem

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康狀態枚舉"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康檢查結果資料類別"""
    status: HealthStatus
    timestamp: str
    server_time: str
    services: Dict[str, Dict[str, Any]]
    statistics: Dict[str, Dict[str, Any]]
    user_level: str = "basic"
    alerts: Optional[list] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        return result


class HealthChecker:
    """健康檢查器類別"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.service_monitor = ServiceMonitor()
        self.stats_collector = SystemStatsCollector()
    
    def _determine_overall_status(self, services: Dict[str, ServiceInfo]) -> HealthStatus:
        """
        根據服務狀態確定整體健康狀態
        
        Args:
            services: 服務狀態字典
            
        Returns:
            HealthStatus: 整體健康狀態
        """
        # 檢查關鍵服務狀態
        critical_services = ['database', 'django']
        
        for service_name in critical_services:
            if service_name in services:
                service = services[service_name]
                if service.status in [ServiceStatus.ERROR]:
                    return HealthStatus.ERROR
                elif service.status in [ServiceStatus.UNKNOWN, ServiceStatus.STOPPED]:
                    return HealthStatus.WARNING
        
        # 如果所有關鍵服務都正常，檢查其他服務
        warning_count = 0
        for service in services.values():
            if service.status in [ServiceStatus.STOPPED, ServiceStatus.UNKNOWN]:
                warning_count += 1
                
        # 如果有警告但不影響核心功能，返回健康狀態
        if warning_count > 0:
            return HealthStatus.WARNING
            
        return HealthStatus.HEALTHY
    
    def _get_current_timestamps(self) -> tuple[str, str]:
        """
        獲取當前時間戳
        
        Returns:
            tuple[str, str]: ISO格式時間戳和格式化時間
        """
        try:
            from django.utils import timezone
            now = timezone.now()
            iso_timestamp = now.isoformat()
            formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
            return iso_timestamp, formatted_time
        except ImportError:
            # 如果 Django 不可用，使用標準 datetime
            now = datetime.now()
            iso_timestamp = now.isoformat()
            formatted_time = now.strftime('%Y-%m-%d %H:%M:%S')
            return iso_timestamp, formatted_time
    
    def perform_basic_health_check(self, connection=None) -> HealthCheckResult:
        """
        執行基本健康檢查
        
        Args:
            connection: Django database connection object
            
        Returns:
            HealthCheckResult: 健康檢查結果
        """
        try:
            # 獲取時間戳
            iso_timestamp, formatted_time = self._get_current_timestamps()
            
            # 檢查服務狀態
            services = self.service_monitor.get_all_services_status(connection)
            services_dict = {name: service.to_dict() for name, service in services.items()}
            
            # 收集基本統計信息
            stats_dict = self.stats_collector.get_statistics_dict(
                include_all=False, 
                connection=connection
            )
            
            # 確定整體健康狀態
            overall_status = self._determine_overall_status(services)
            
            # 創建健康檢查結果
            result = HealthCheckResult(
                status=overall_status,
                timestamp=iso_timestamp,
                server_time=formatted_time,
                services=services_dict,
                statistics=stats_dict,
                user_level="basic"
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Basic health check failed: {str(e)}")
            iso_timestamp, formatted_time = self._get_current_timestamps()
            
            return HealthCheckResult(
                status=HealthStatus.ERROR,
                timestamp=iso_timestamp,
                server_time=formatted_time,
                services={},
                statistics={'error': {'count': 0, 'description': f'健康檢查失敗: {str(e)}'}},
                user_level="basic"
            )
    
    def perform_full_health_check(self, connection=None) -> HealthCheckResult:
        """
        執行完整健康檢查
        
        Args:
            connection: Django database connection object
            
        Returns:
            HealthCheckResult: 完整健康檢查結果
        """
        try:
            # 獲取時間戳
            iso_timestamp, formatted_time = self._get_current_timestamps()
            
            # 檢查服務狀態
            services = self.service_monitor.get_all_services_status(connection)
            services_dict = {name: service.to_dict() for name, service in services.items()}
            
            # 收集完整統計信息
            stats_dict = self.stats_collector.get_statistics_dict(
                include_all=True,
                connection=connection
            )
            
            # 確定整體健康狀態
            overall_status = self._determine_overall_status(services)
            
            # 生成警報信息
            alerts = self._generate_alerts(services, stats_dict)
            
            # 創建健康檢查結果
            result = HealthCheckResult(
                status=overall_status,
                timestamp=iso_timestamp,
                server_time=formatted_time,
                services=services_dict,
                statistics=stats_dict,
                user_level="full",
                alerts=alerts
            )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Full health check failed: {str(e)}")
            iso_timestamp, formatted_time = self._get_current_timestamps()
            
            return HealthCheckResult(
                status=HealthStatus.ERROR,
                timestamp=iso_timestamp,
                server_time=formatted_time,
                services={},
                statistics={'error': {'count': 0, 'description': f'健康檢查失敗: {str(e)}'}},
                user_level="full",
                alerts=[f"系統健康檢查失敗: {str(e)}"]
            )
    
    def _generate_alerts(self, services: Dict[str, ServiceInfo], stats: Dict[str, Dict[str, Any]]) -> list:
        """
        根據服務狀態和統計信息生成警報
        
        Args:
            services: 服務狀態字典
            stats: 統計信息字典
            
        Returns:
            list: 警報信息列表
        """
        alerts = []
        
        # 檢查服務警報
        for service_name, service in services.items():
            if service.status == ServiceStatus.ERROR:
                alerts.append(f"{service_name} 服務發生錯誤: {service.message}")
            elif service.status == ServiceStatus.STOPPED:
                alerts.append(f"{service_name} 服務已停止")
        
        # 檢查統計數據警報
        if 'error' in stats:
            alerts.append(f"統計數據收集異常: {stats['error']['description']}")
        
        return alerts


def create_health_checker() -> HealthChecker:
    """
    創建健康檢查器實例
    
    Returns:
        HealthChecker: 健康檢查器實例
    """
    return HealthChecker()