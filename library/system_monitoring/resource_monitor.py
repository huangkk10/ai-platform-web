"""
系統資源監控器

提供系統硬體資源監控功能，包括：
- CPU 使用率監控
- 記憶體使用率監控
- 磁碟空間使用率監控
- 系統資源警報生成
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SystemResource:
    """系統資源資料類別"""
    cpu_percent: float
    memory_total_gb: float
    memory_used_gb: float
    memory_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_percent: float
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'cpu_percent': round(self.cpu_percent, 1),
            'memory': {
                'total': round(self.memory_total_gb, 2),
                'used': round(self.memory_used_gb, 2),
                'percent': round(self.memory_percent, 1)
            },
            'disk': {
                'total': round(self.disk_total_gb, 2),
                'used': round(self.disk_used_gb, 2),
                'percent': round(self.disk_percent, 1)
            }
        }


@dataclass
class ResourceThresholds:
    """資源閾值配置"""
    cpu_warning: float = 80.0
    cpu_critical: float = 90.0
    memory_warning: float = 80.0
    memory_critical: float = 90.0
    disk_warning: float = 85.0
    disk_critical: float = 95.0


class SystemResourceMonitor:
    """系統資源監控器"""
    
    def __init__(self, thresholds: Optional[ResourceThresholds] = None):
        self.logger = logging.getLogger(__name__)
        self.thresholds = thresholds or ResourceThresholds()
    
    def get_system_resources(self) -> Optional[SystemResource]:
        """
        獲取系統資源使用情況
        
        Returns:
            SystemResource: 系統資源數據，如果獲取失敗則返回 None
        """
        try:
            import psutil
            
            # CPU 使用率（等待 1 秒獲取準確值）
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 記憶體使用情況
            memory = psutil.virtual_memory()
            memory_total_gb = memory.total / (1024**3)
            memory_used_gb = memory.used / (1024**3)
            memory_percent = memory.percent
            
            # 磁碟使用情況
            disk = psutil.disk_usage('/')
            disk_total_gb = disk.total / (1024**3)
            disk_used_gb = disk.used / (1024**3)
            disk_percent = (disk.used / disk.total) * 100
            
            resource = SystemResource(
                cpu_percent=cpu_percent,
                memory_total_gb=memory_total_gb,
                memory_used_gb=memory_used_gb,
                memory_percent=memory_percent,
                disk_total_gb=disk_total_gb,
                disk_used_gb=disk_used_gb,
                disk_percent=disk_percent
            )
            
            self.logger.info(
                f"系統資源: CPU={cpu_percent:.1f}%, "
                f"記憶體={memory_percent:.1f}%, "
                f"磁碟={disk_percent:.1f}%"
            )
            
            return resource
            
        except ImportError:
            self.logger.error("psutil 模組不可用，無法獲取系統資源")
            return None
        except Exception as e:
            self.logger.error(f"獲取系統資源失敗: {str(e)}")
            return None
    
    def generate_resource_alerts(self, resource: SystemResource) -> List[str]:
        """
        根據系統資源使用情況生成警報
        
        Args:
            resource: 系統資源數據
            
        Returns:
            List[str]: 警報訊息列表
        """
        alerts = []
        
        # CPU 警報
        if resource.cpu_percent >= self.thresholds.cpu_critical:
            alerts.append(f'CPU 使用率極高 ({resource.cpu_percent:.1f}%)')
        elif resource.cpu_percent >= self.thresholds.cpu_warning:
            alerts.append(f'CPU 使用率過高 ({resource.cpu_percent:.1f}%)')
        
        # 記憶體警報
        if resource.memory_percent >= self.thresholds.memory_critical:
            alerts.append(f'記憶體使用率極高 ({resource.memory_percent:.1f}%)')
        elif resource.memory_percent >= self.thresholds.memory_warning:
            alerts.append(f'記憶體使用率過高 ({resource.memory_percent:.1f}%)')
        
        # 磁碟警報
        if resource.disk_percent >= self.thresholds.disk_critical:
            alerts.append(f'磁碟空間嚴重不足 ({resource.disk_percent:.1f}%)')
        elif resource.disk_percent >= self.thresholds.disk_warning:
            alerts.append(f'磁碟空間不足 ({resource.disk_percent:.1f}%)')
        
        return alerts
    
    def get_resource_status(self, resource: SystemResource) -> str:
        """
        根據系統資源使用情況確定整體狀態
        
        Args:
            resource: 系統資源數據
            
        Returns:
            str: 系統狀態 ('healthy', 'warning', 'critical')
        """
        # 檢查是否有關鍵警報
        if (resource.cpu_percent >= self.thresholds.cpu_critical or
            resource.memory_percent >= self.thresholds.memory_critical or
            resource.disk_percent >= self.thresholds.disk_critical):
            return 'critical'
        
        # 檢查是否有警告
        if (resource.cpu_percent >= self.thresholds.cpu_warning or
            resource.memory_percent >= self.thresholds.memory_warning or
            resource.disk_percent >= self.thresholds.disk_warning):
            return 'warning'
        
        return 'healthy'
    
    def get_detailed_system_info(self) -> Dict[str, Any]:
        """
        獲取詳細的系統資源信息
        
        Returns:
            Dict[str, Any]: 包含資源數據、警報和狀態的完整信息
        """
        try:
            import psutil
            
            resource = self.get_system_resources()
            if not resource:
                return {
                    'status': 'error',
                    'error': '無法獲取系統資源數據',
                    'system': {},
                    'alerts': ['系統資源監控不可用']
                }
            
            alerts = self.generate_resource_alerts(resource)
            status = self.get_resource_status(resource)
            
            # 額外的系統信息
            try:
                boot_time = psutil.boot_time()
                uptime_seconds = psutil.time.time() - boot_time
                uptime_hours = uptime_seconds / 3600
                
                cpu_count = psutil.cpu_count()
                cpu_freq = psutil.cpu_freq()
                
                additional_info = {
                    'uptime_hours': round(uptime_hours, 1),
                    'cpu_count': cpu_count,
                    'cpu_freq_mhz': round(cpu_freq.current, 0) if cpu_freq else None,
                }
            except Exception as e:
                self.logger.warning(f"無法獲取額外系統信息: {str(e)}")
                additional_info = {}
            
            return {
                'status': status,
                'system': {**resource.to_dict(), **additional_info},
                'alerts': alerts,
                'thresholds': asdict(self.thresholds)
            }
            
        except Exception as e:
            self.logger.error(f"獲取詳細系統信息失敗: {str(e)}")
            return {
                'status': 'error',
                'error': f'系統信息獲取失敗: {str(e)}',
                'system': {},
                'alerts': [f'系統監控錯誤: {str(e)}']
            }


def create_resource_monitor(
    cpu_warning: float = 80.0,
    memory_warning: float = 80.0,
    disk_warning: float = 85.0
) -> SystemResourceMonitor:
    """
    創建系統資源監控器實例
    
    Args:
        cpu_warning: CPU 使用率警告閾值
        memory_warning: 記憶體使用率警告閾值
        disk_warning: 磁碟使用率警告閾值
        
    Returns:
        SystemResourceMonitor: 資源監控器實例
    """
    thresholds = ResourceThresholds(
        cpu_warning=cpu_warning,
        memory_warning=memory_warning,
        disk_warning=disk_warning
    )
    return SystemResourceMonitor(thresholds)