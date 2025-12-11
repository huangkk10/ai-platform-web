"""
遠端資料庫主機監控器

透過 PostgreSQL 連線獲取資料庫主機的磁碟使用資訊
由於資料庫已遷移到獨立主機 (10.10.173.29)，需要監控該主機的資源狀態

功能：
- 獲取資料庫大小
- 獲取各表空間大小
- 獲取資料目錄資訊
- 透過 SSH 獲取主機磁碟使用率
"""

import logging
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class HostDiskInfo:
    """主機磁碟資訊（透過 SSH 獲取）"""
    total_size: str       # 總容量 (如 "17T")
    used_size: str        # 已使用 (如 "13G")  
    available_size: str   # 可用空間 (如 "16T")
    use_percent: float    # 使用率百分比 (如 1.0)
    mount_point: str      # 掛載點 (如 "/")
    filesystem: str       # 檔案系統 (如 "/dev/sda2")
    status: str           # 'healthy', 'warning', 'critical', 'error'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            'total_size': self.total_size,
            'used_size': self.used_size,
            'available_size': self.available_size,
            'use_percent': self.use_percent,
            'mount_point': self.mount_point,
            'filesystem': self.filesystem,
            'status': self.status
        }
        if self.error_message:
            result['error_message'] = self.error_message
        return result


@dataclass
class RemoteDatabaseDiskInfo:
    """遠端資料庫磁碟資訊"""
    host: str
    database_size: str  # 人類可讀格式 (如 "45 MB")
    database_size_bytes: int  # 原始位元組數
    total_databases_size: str
    total_databases_size_bytes: int
    data_directory: str
    status: str  # 'healthy', 'warning', 'error'
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            'host': self.host,
            'database_size': self.database_size,
            'database_size_bytes': self.database_size_bytes,
            'total_databases_size': self.total_databases_size,
            'total_databases_size_bytes': self.total_databases_size_bytes,
            'data_directory': self.data_directory,
            'status': self.status
        }
        if self.error_message:
            result['error_message'] = self.error_message
        return result


@dataclass 
class TablespaceInfo:
    """表空間資訊"""
    name: str
    size: str
    size_bytes: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'size': self.size,
            'size_bytes': self.size_bytes
        }


class RemoteDatabaseMonitor:
    """遠端資料庫監控器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or self._load_default_config()
        
        # SSH 連線設定（從環境變數或配置載入）
        self.ssh_config = {
            'host': self.config.get('host', '10.10.173.29'),
            'username': os.environ.get('DB_HOST_SSH_USER', 'svd-ai'),
            'password': os.environ.get('DB_HOST_SSH_PASSWORD', '1'),
            'port': 22,
            'timeout': 5
        }
        
    def _load_default_config(self) -> Dict[str, Any]:
        """載入預設配置"""
        try:
            from library.config.config_loader import ConfigLoader
            config_loader = ConfigLoader()
            full_config = config_loader.get_config()
            return full_config.get('database_server', {})
        except Exception as e:
            self.logger.warning(f"載入配置失敗，使用預設值: {str(e)}")
            return {
                'host': '10.10.173.29',
                'port': 5432,
                'database': 'ai_platform'
            }
    
    def get_database_host(self) -> str:
        """獲取資料庫主機 IP"""
        return self.config.get('host', '10.10.173.29')
    
    def get_database_disk_info(self, connection=None) -> RemoteDatabaseDiskInfo:
        """
        獲取資料庫主機的磁碟使用資訊
        
        透過 PostgreSQL 查詢獲取：
        - 當前資料庫大小
        - 所有資料庫總大小
        - 資料目錄位置
        
        Args:
            connection: Django database connection object
            
        Returns:
            RemoteDatabaseDiskInfo: 資料庫磁碟資訊
        """
        host = self.get_database_host()
        
        try:
            if connection is None:
                from django.db import connection
            
            with connection.cursor() as cursor:
                # 獲取當前資料庫大小
                cursor.execute("SELECT pg_database_size(current_database())")
                db_size_bytes = cursor.fetchone()[0]
                
                cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                db_size_pretty = cursor.fetchone()[0]
                
                # 獲取所有資料庫總大小
                cursor.execute("""
                    SELECT COALESCE(SUM(pg_database_size(datname)), 0)
                    FROM pg_database 
                    WHERE datistemplate = false
                """)
                total_size_bytes = cursor.fetchone()[0]
                
                cursor.execute("""
                    SELECT pg_size_pretty(COALESCE(SUM(pg_database_size(datname)), 0))
                    FROM pg_database 
                    WHERE datistemplate = false
                """)
                total_size_pretty = cursor.fetchone()[0]
                
                # 獲取資料目錄
                cursor.execute("SHOW data_directory")
                data_directory = cursor.fetchone()[0]
                
                self.logger.info(
                    f"遠端資料庫 ({host}) 磁碟資訊: "
                    f"當前DB={db_size_pretty}, 總計={total_size_pretty}"
                )
                
                return RemoteDatabaseDiskInfo(
                    host=host,
                    database_size=db_size_pretty,
                    database_size_bytes=db_size_bytes,
                    total_databases_size=total_size_pretty,
                    total_databases_size_bytes=total_size_bytes,
                    data_directory=data_directory,
                    status='healthy'
                )
                
        except Exception as e:
            self.logger.error(f"獲取遠端資料庫磁碟資訊失敗: {str(e)}")
            return RemoteDatabaseDiskInfo(
                host=host,
                database_size="未知",
                database_size_bytes=0,
                total_databases_size="未知",
                total_databases_size_bytes=0,
                data_directory="未知",
                status='error',
                error_message=str(e)
            )
    
    def get_tablespace_sizes(self, connection=None) -> List[TablespaceInfo]:
        """
        獲取各表空間的大小
        
        Args:
            connection: Django database connection object
            
        Returns:
            List[TablespaceInfo]: 表空間資訊列表
        """
        tablespaces = []
        
        try:
            if connection is None:
                from django.db import connection
            
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        spcname,
                        pg_size_pretty(pg_tablespace_size(spcname)) as size_pretty,
                        pg_tablespace_size(spcname) as size_bytes
                    FROM pg_tablespace
                    ORDER BY pg_tablespace_size(spcname) DESC
                """)
                
                for row in cursor.fetchall():
                    tablespaces.append(TablespaceInfo(
                        name=row[0],
                        size=row[1],
                        size_bytes=row[2]
                    ))
                    
        except Exception as e:
            self.logger.error(f"獲取表空間資訊失敗: {str(e)}")
            
        return tablespaces
    
    def get_database_connection_info(self, connection=None) -> Dict[str, Any]:
        """
        獲取資料庫連接資訊
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 連接資訊
        """
        try:
            if connection is None:
                from django.db import connection
            
            with connection.cursor() as cursor:
                # 獲取 PostgreSQL 版本
                cursor.execute("SELECT version()")
                version_row = cursor.fetchone()
                full_version = version_row[0] if version_row else "未知"
                
                # 獲取當前連接數
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_stat_activity 
                    WHERE datname = current_database()
                """)
                active_connections = cursor.fetchone()[0]
                
                # 獲取最大連接數
                cursor.execute("SHOW max_connections")
                max_connections = int(cursor.fetchone()[0])
                
                return {
                    'version': full_version.split(',')[0] if full_version else "未知",
                    'active_connections': active_connections,
                    'max_connections': max_connections,
                    'connection_usage_percent': round((active_connections / max_connections) * 100, 1) if max_connections > 0 else 0
                }
                
        except Exception as e:
            self.logger.error(f"獲取資料庫連接資訊失敗: {str(e)}")
            return {
                'version': "未知",
                'active_connections': 0,
                'max_connections': 0,
                'connection_usage_percent': 0,
                'error': str(e)
            }
    
    def get_host_disk_info_via_ssh(self) -> HostDiskInfo:
        """
        透過 SSH 獲取主機磁碟使用資訊
        
        執行 df -h / 命令獲取根分區磁碟狀態
        
        Returns:
            HostDiskInfo: 主機磁碟資訊
        """
        try:
            import paramiko
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                hostname=self.ssh_config['host'],
                username=self.ssh_config['username'],
                password=self.ssh_config['password'],
                port=self.ssh_config['port'],
                timeout=self.ssh_config['timeout']
            )
            
            # 執行 df -h / 命令獲取根分區資訊
            stdin, stdout, stderr = ssh.exec_command('df -h /')
            output = stdout.read().decode().strip()
            error_output = stderr.read().decode().strip()
            
            ssh.close()
            
            if error_output:
                self.logger.warning(f"SSH 命令有錯誤輸出: {error_output}")
            
            # 解析 df 輸出
            # Filesystem      Size  Used Avail Use% Mounted on
            # /dev/sda2        17T   13G   16T   1% /
            lines = output.split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                if len(parts) >= 6:
                    filesystem = parts[0]
                    total_size = parts[1]
                    used_size = parts[2]
                    available_size = parts[3]
                    use_percent_str = parts[4].replace('%', '')
                    mount_point = parts[5]
                    
                    try:
                        use_percent = float(use_percent_str)
                    except ValueError:
                        use_percent = 0.0
                    
                    # 根據使用率判斷狀態
                    if use_percent >= 95:
                        status = 'critical'
                    elif use_percent >= 85:
                        status = 'warning'
                    else:
                        status = 'healthy'
                    
                    self.logger.info(
                        f"SSH 獲取主機 ({self.ssh_config['host']}) 磁碟資訊: "
                        f"總容量={total_size}, 已用={used_size} ({use_percent}%)"
                    )
                    
                    return HostDiskInfo(
                        total_size=total_size,
                        used_size=used_size,
                        available_size=available_size,
                        use_percent=use_percent,
                        mount_point=mount_point,
                        filesystem=filesystem,
                        status=status
                    )
            
            # 解析失敗
            raise ValueError(f"無法解析 df 輸出: {output}")
            
        except ImportError:
            self.logger.error("paramiko 未安裝，無法透過 SSH 獲取主機磁碟資訊")
            return HostDiskInfo(
                total_size="未知",
                used_size="未知",
                available_size="未知",
                use_percent=0.0,
                mount_point="/",
                filesystem="未知",
                status='error',
                error_message="paramiko 未安裝"
            )
        except Exception as e:
            self.logger.error(f"SSH 獲取主機磁碟資訊失敗: {str(e)}")
            return HostDiskInfo(
                total_size="未知",
                used_size="未知",
                available_size="未知",
                use_percent=0.0,
                mount_point="/",
                filesystem="未知",
                status='error',
                error_message=str(e)
            )
    
    def get_full_remote_database_status(self, connection=None) -> Dict[str, Any]:
        """
        獲取完整的遠端資料庫狀態
        
        整合所有監控資訊
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 完整的遠端資料庫狀態
        """
        disk_info = self.get_database_disk_info(connection)
        connection_info = self.get_database_connection_info(connection)
        tablespaces = self.get_tablespace_sizes(connection)
        host_disk = self.get_host_disk_info_via_ssh()  # 新增：主機磁碟資訊
        
        return {
            'host': disk_info.host,
            'status': disk_info.status,
            'disk': disk_info.to_dict(),
            'host_disk': host_disk.to_dict(),  # 新增：主機磁碟資訊
            'connection': connection_info,
            'tablespaces': [ts.to_dict() for ts in tablespaces]
        }


def create_remote_db_monitor(config: Optional[Dict[str, Any]] = None) -> RemoteDatabaseMonitor:
    """
    工廠函數：創建遠端資料庫監控器實例
    
    Args:
        config: 配置字典
        
    Returns:
        RemoteDatabaseMonitor: 監控器實例
    """
    return RemoteDatabaseMonitor(config)
