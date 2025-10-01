"""
服務監控器

提供各種服務狀態檢查功能，包括：
- 資料庫連接檢查
- 網路端口檢查  
- 服務健康狀態監控
"""

import socket
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """服務狀態枚舉"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    UNKNOWN = "unknown"
    HEALTHY = "healthy"


@dataclass
class ServiceInfo:
    """服務信息資料類別"""
    name: str
    status: ServiceStatus
    message: str
    port: Optional[int] = None
    host: Optional[str] = None
    service_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = asdict(self)
        result['status'] = self.status.value
        return result


class ServiceMonitor:
    """服務監控器類別"""
    
    def __init__(self, config=None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._load_default_config()
        
    def _load_default_config(self) -> Dict[str, Any]:
        """載入預設配置或從配置文件載入"""
        try:
            # 嘗試載入配置文件
            from library.config.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            full_config = config_loader.get_config()
            return full_config.get('system_monitoring', {}).get('services', {})
        except ImportError:
            # 如果配置載入器不可用，使用預設配置
            self.logger.warning("ConfigLoader 不可用，使用預設服務配置")
            return {
                'django': {'enabled': True, 'port': 8000},
                'database': {'enabled': True, 'type': 'PostgreSQL'},
                'frontend': {'enabled': True, 'host': 'ai-react', 'port': 3000, 'timeout': 3},
                'nginx': {'enabled': True, 'host': 'ai-nginx', 'port': 80, 'timeout': 3}
            }
        except Exception as e:
            self.logger.warning(f"載入配置失敗，使用預設配置: {str(e)}")
            return {
                'django': {'enabled': True, 'port': 8000},
                'database': {'enabled': True, 'type': 'PostgreSQL'},
                'frontend': {'enabled': True, 'host': 'ai-react', 'port': 3000, 'timeout': 3},
                'nginx': {'enabled': True, 'host': 'ai-nginx', 'port': 80, 'timeout': 3}
            }
        
    def check_database_connection(self, connection=None) -> ServiceInfo:
        """
        檢查資料庫連接狀態
        
        Args:
            connection: Django database connection object
            
        Returns:
            ServiceInfo: 資料庫服務信息
        """
        try:
            if connection is None:
                # 動態導入避免循環依賴
                from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
            return ServiceInfo(
                name="database",
                status=ServiceStatus.HEALTHY,
                message="資料庫連接正常",
                service_type="PostgreSQL"
            )
            
        except Exception as e:
            self.logger.error(f"Database connection check failed: {str(e)}")
            return ServiceInfo(
                name="database",
                status=ServiceStatus.ERROR,
                message=f"資料庫連接失敗: {str(e)}",
                service_type="PostgreSQL"
            )
    
    def check_port_connectivity(self, host: str, port: int, service_name: str) -> ServiceInfo:
        """
        檢查端口連接狀態
        
        Args:
            host: 主機地址
            port: 端口號
            service_name: 服務名稱
            
        Returns:
            ServiceInfo: 端口連接服務信息
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)  # 3秒超時
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                return ServiceInfo(
                    name=service_name,
                    status=ServiceStatus.RUNNING,
                    message=f"{service_name} 服務正常運行",
                    host=host,
                    port=port
                )
            else:
                return ServiceInfo(
                    name=service_name,
                    status=ServiceStatus.STOPPED,
                    message=f"{service_name} 服務未運行",
                    host=host,
                    port=port
                )
                
        except Exception as e:
            self.logger.warning(f"Port connectivity check failed for {service_name}:{port} - {str(e)}")
            return ServiceInfo(
                name=service_name,
                status=ServiceStatus.UNKNOWN,
                message=f"無法檢查 {service_name} 服務狀態",
                host=host,
                port=port
            )
    
    def check_django_service(self) -> ServiceInfo:
        """
        檢查 Django 服務狀態
        
        Returns:
            ServiceInfo: Django 服務信息
        """
        return ServiceInfo(
            name="django",
            status=ServiceStatus.RUNNING,
            message="Django REST API 正常運行",
            port=8000,
            service_type="Web Framework"
        )
    
    def check_frontend_service(self, host: str = None, port: int = None) -> ServiceInfo:
        """
        檢查前端服務狀態 - 使用配置文件中的設定
        
        Args:
            host: 主機地址，如果為 None 則使用配置文件設定
            port: 端口號，如果為 None 則使用配置文件設定
            
        Returns:
            ServiceInfo: 前端服務信息
        """
        frontend_config = self.config.get('frontend', {})
        
        if not frontend_config.get('enabled', True):
            return ServiceInfo(
                name="frontend",
                status=ServiceStatus.UNKNOWN,
                message="前端服務監控已停用"
            )
        
        actual_host = host or frontend_config.get('host', 'ai-react')
        actual_port = port or frontend_config.get('port', 3000)
        
        return self.check_port_connectivity(actual_host, actual_port, "frontend")
    
    def check_nginx_service(self, host: str = None, port: int = None) -> ServiceInfo:
        """
        檢查 Nginx 服務狀態 - 使用配置文件中的設定
        
        Args:
            host: 主機地址，如果為 None 則使用配置文件設定
            port: 端口號，如果為 None 則使用配置文件設定
            
        Returns:
            ServiceInfo: Nginx 服務信息
        """
        nginx_config = self.config.get('nginx', {})
        
        if not nginx_config.get('enabled', True):
            return ServiceInfo(
                name="nginx",
                status=ServiceStatus.UNKNOWN,
                message="Nginx 服務監控已停用"
            )
        
        actual_host = host or nginx_config.get('host', 'ai-nginx')
        actual_port = port or nginx_config.get('port', 80)
        
        return self.check_port_connectivity(actual_host, actual_port, "nginx")
    
    def get_all_services_status(self, connection=None) -> Dict[str, ServiceInfo]:
        """
        獲取所有服務狀態 - 根據配置文件決定檢查哪些服務
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, ServiceInfo]: 所有服務狀態字典
        """
        services = {}
        
        # Django 服務 (總是運行中，因為正在執行此代碼)
        django_config = self.config.get('django', {})
        if django_config.get('enabled', True):
            services['django'] = self.check_django_service()
        
        # 資料庫服務
        database_config = self.config.get('database', {})
        if database_config.get('enabled', True):
            services['database'] = self.check_database_connection(connection)
        
        # 前端服務
        frontend_config = self.config.get('frontend', {})
        if frontend_config.get('enabled', True):
            services['frontend'] = self.check_frontend_service()
        
        # Nginx 服務
        nginx_config = self.config.get('nginx', {})
        if nginx_config.get('enabled', True):
            services['nginx'] = self.check_nginx_service()
        
        # 未來可以根據配置添加其他服務
        # 例如 Redis, Elasticsearch 等
        
        return services
    
    def get_services_status_dict(self, connection=None) -> Dict[str, Dict[str, Any]]:
        """
        獲取所有服務狀態的字典格式
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Dict[str, Any]]: 字典格式的服務狀態
        """
        services = self.get_all_services_status(connection)
        return {name: service.to_dict() for name, service in services.items()}


def create_service_monitor(config=None) -> ServiceMonitor:
    """
    創建服務監控器實例
    
    Args:
        config: 可選的配置字典，如果為 None 則從配置文件載入
    
    Returns:
        ServiceMonitor: 服務監控器實例
    """
    return ServiceMonitor(config)