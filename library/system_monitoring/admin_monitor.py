"""
管理員級別系統監控器

提供管理員專用的系統監控功能，包括：
- 完整的系統資源監控
- 資料庫表統計
- 系統服務狀態檢查
- 綜合系統健康報告
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from .resource_monitor import SystemResourceMonitor, create_resource_monitor
from .service_monitor import ServiceMonitor, create_service_monitor
from .system_stats import SystemStatsCollector, create_stats_collector

logger = logging.getLogger(__name__)


@dataclass
class DatabaseTableStats:
    """資料庫表統計資料類別"""
    table_name: str
    display_name: str
    count: int
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        result = {
            'table': self.table_name,
            'name': self.display_name,
            'count': self.count
        }
        if self.error:
            result['error'] = self.error
        return result


@dataclass
class AdminHealthReport:
    """管理員健康檢查報告"""
    overall_status: str
    timestamp: str
    server_time: str
    system_resources: Dict[str, Any]
    database_status: str
    database_stats: Dict[str, Any]
    services_status: Dict[str, Any]
    alerts: List[str]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)


class AdminSystemMonitor:
    """管理員級別系統監控器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.resource_monitor = create_resource_monitor()
        self.service_monitor = create_service_monitor()
        self.stats_collector = create_stats_collector()
        
        # 預定義的資料庫表映射 (顯示名稱, 實際表名, 中文描述)
        self.database_tables = [
            ('users', 'auth_user', '用戶'),
            ('know_issues', 'know_issue', 'Know Issue'),
            ('projects', 'api_project', '專案'),
            ('rvt_guides', 'rvt_guide', 'RVT 指南'),
            ('ocr_benchmarks', 'ocr_storage_benchmark', 'OCR 基準測試'),
            ('test_classes', 'protocol_test_class', '測試類別'),
            ('employee', 'employee', '員工'),
            ('user_profiles', 'api_userprofile', '用戶檔案'),
            ('chat_usage', 'chat_usage', '聊天使用記錄'),
        ]
    
    def get_database_table_stats(self, connection=None) -> List[DatabaseTableStats]:
        """
        獲取資料庫表統計信息
        
        Args:
            connection: Django database connection object
            
        Returns:
            List[DatabaseTableStats]: 資料庫表統計列表
        """
        stats = []
        
        try:
            if connection is None:
                from django.db import connection
            
            with connection.cursor() as cursor:
                for display_name, table_name, description in self.database_tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                        count = cursor.fetchone()[0]
                        
                        stats.append(DatabaseTableStats(
                            table_name=table_name,
                            display_name=f"{description}數量",
                            count=count
                        ))
                        
                    except Exception as table_error:
                        self.logger.warning(f"無法統計表 {table_name}: {str(table_error)}")
                        stats.append(DatabaseTableStats(
                            table_name=table_name,
                            display_name=f"{description}數量",
                            count=0,
                            error=f"表不存在或無權限: {str(table_error)}"
                        ))
                        
        except Exception as e:
            self.logger.error(f"資料庫表統計失敗: {str(e)}")
            stats.append(DatabaseTableStats(
                table_name="error",
                display_name="資料庫錯誤",
                count=0,
                error=str(e)
            ))
            
        return stats
    
    def get_database_health_info(self, connection=None) -> Dict[str, Any]:
        """
        獲取資料庫健康信息
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 資料庫健康信息
        """
        try:
            if connection is None:
                from django.db import connection
            
            with connection.cursor() as cursor:
                # 基本連接測試
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                # 獲取資料庫版本
                try:
                    cursor.execute("SELECT version()")
                    db_version = cursor.fetchone()[0].split(' ')[0]
                except Exception:
                    db_version = "未知版本"
                
                # 獲取活躍連接數
                try:
                    cursor.execute("SELECT COUNT(*) FROM django_session WHERE expire_date > NOW()")
                    active_sessions = cursor.fetchone()[0]
                except Exception:
                    active_sessions = 0
                
                # 獲取資料庫大小（PostgreSQL）
                try:
                    cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()))")
                    db_size = cursor.fetchone()[0]
                except Exception:
                    db_size = "未知"
                
                return {
                    'status': 'healthy',
                    'version': db_version,
                    'active_sessions': active_sessions,
                    'database_size': db_size,
                    'connection_status': '正常'
                }
                
        except Exception as e:
            self.logger.error(f"資料庫健康檢查失敗: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'connection_status': '連接失敗'
            }
    
    def generate_system_recommendations(self, resource_info: Dict[str, Any], 
                                      db_stats: List[DatabaseTableStats]) -> List[str]:
        """
        根據系統狀態生成改善建議
        
        Args:
            resource_info: 系統資源信息
            db_stats: 資料庫表統計
            
        Returns:
            List[str]: 改善建議列表
        """
        recommendations = []
        
        # 系統資源建議
        if resource_info.get('status') == 'critical':
            recommendations.append('🔴 系統資源使用率極高，建議立即檢查和優化')
        elif resource_info.get('status') == 'warning':
            recommendations.append('🟡 系統資源使用率偏高，建議監控和優化')
        
        system = resource_info.get('system', {})
        
        # CPU 建議
        cpu_percent = system.get('cpu_percent', 0)
        if cpu_percent > 90:
            recommendations.append('💾 CPU 使用率極高，建議檢查後台進程和優化代碼')
        elif cpu_percent > 80:
            recommendations.append('⚡ CPU 使用率較高，建議關注系統負載')
        
        # 記憶體建議
        memory = system.get('memory', {})
        memory_percent = memory.get('percent', 0)
        if memory_percent > 90:
            recommendations.append('🧠 記憶體使用率極高，建議增加記憶體或優化程序')
        elif memory_percent > 80:
            recommendations.append('📊 記憶體使用率較高，建議監控記憶體洩漏')
        
        # 磁碟建議
        disk = system.get('disk', {})
        disk_percent = disk.get('percent', 0)
        if disk_percent > 95:
            recommendations.append('💽 磁碟空間極度不足，請立即清理空間')
        elif disk_percent > 85:
            recommendations.append('📁 磁碟空間不足，建議清理日誌和臨時文件')
        
        # 資料庫建議
        total_records = sum(stat.count for stat in db_stats if not stat.error)
        if total_records > 100000:
            recommendations.append('🗃️ 資料庫記錄較多，建議定期清理和優化索引')
        
        # 如果沒有問題，給予正面建議
        if not recommendations:
            recommendations.append('✅ 系統運行良好，建議繼續保持定期監控')
        
        return recommendations
    
    def perform_admin_health_check(self, connection=None) -> AdminHealthReport:
        """
        執行管理員級別的完整健康檢查
        
        Args:
            connection: Django database connection object
            
        Returns:
            AdminHealthReport: 完整的健康檢查報告
        """
        try:
            # 獲取當前時間
            from django.utils import timezone
            now = timezone.now()
            timestamp = now.isoformat()
            server_time = now.strftime('%Y-%m-%d %H:%M:%S')
        except ImportError:
            from datetime import datetime
            now = datetime.now()
            timestamp = now.isoformat()
            server_time = now.strftime('%Y-%m-%d %H:%M:%S')
        
        # 1. 系統資源檢查
        resource_info = self.resource_monitor.get_detailed_system_info()
        
        # 2. 資料庫健康檢查
        db_health = self.get_database_health_info(connection)
        db_table_stats = self.get_database_table_stats(connection)
        
        # 3. 服務狀態檢查
        services_status = self.service_monitor.get_services_status_dict(connection)
        
        # 4. 收集警報
        alerts = []
        alerts.extend(resource_info.get('alerts', []))
        
        if db_health.get('status') == 'error':
            alerts.append(f"資料庫連接異常: {db_health.get('error', '未知錯誤')}")
        
        # 檢查服務警報
        for service_name, service_info in services_status.items():
            if service_info.get('status') == 'error':
                alerts.append(f"{service_name} 服務異常")
            elif service_info.get('status') == 'stopped':
                alerts.append(f"{service_name} 服務已停止")
        
        # 5. 生成改善建議
        recommendations = self.generate_system_recommendations(resource_info, db_table_stats)
        
        # 6. 確定整體狀態
        overall_status = 'healthy'
        if resource_info.get('status') == 'critical' or db_health.get('status') == 'error':
            overall_status = 'critical'
        elif (resource_info.get('status') == 'warning' or 
              any(service.get('status') in ['stopped', 'unknown'] 
                  for service in services_status.values())):
            overall_status = 'warning'
        
        # 7. 整理資料庫統計
        database_stats = {
            'health': db_health,
            'tables': {stat.display_name: stat.to_dict() for stat in db_table_stats}
        }
        
        return AdminHealthReport(
            overall_status=overall_status,
            timestamp=timestamp,
            server_time=server_time,
            system_resources=resource_info,
            database_status=db_health.get('status', 'unknown'),
            database_stats=database_stats,
            services_status=services_status,
            alerts=alerts,
            recommendations=recommendations
        )
    
    def get_simple_status_dict(self, connection=None) -> Dict[str, Any]:
        """
        獲取簡化的系統狀態（類似於原本的 simple_system_status 函數）
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, Any]: 簡化的系統狀態字典
        """
        # 執行完整檢查
        full_report = self.perform_admin_health_check(connection)
        
        # 簡化輸出格式
        system_resources = full_report.system_resources.get('system', {})
        
        # 從完整報告中提取統計數據並轉換為前端期望的格式
        db_tables = full_report.database_stats.get('tables', {})
        
        # 建立前端期望的資料庫統計格式
        database_stats = {}
        
        # 映射中文名稱到英文鍵名
        key_mapping = {
            '用戶數量': 'users',
            'Know Issue數量': 'know_issues',
            '專案數量': 'projects',
            'RVT 指南數量': 'rvt_guides',
            'OCR 基準測試數量': 'ocr_benchmarks',
            '測試類別數量': 'test_classes',
            '員工數量': 'employees',
            '用戶檔案數量': 'user_profiles',
            '聊天使用記錄數量': 'chat_usage'
        }
        
        # 轉換統計數據格式
        for chinese_name, table_data in db_tables.items():
            if 'error' not in table_data and chinese_name in key_mapping:
                english_key = key_mapping[chinese_name]
                database_stats[english_key] = table_data['count']
        
        return {
            'status': full_report.overall_status,
            'timestamp': full_report.timestamp,
            'server_time': full_report.server_time,
            'system': {
                'cpu_percent': system_resources.get('cpu_percent', 0),
                'memory': system_resources.get('memory', {}),
                'disk': system_resources.get('disk', {})
            },
            'services': {
                'django': {'status': 'running'},
                'database': {'status': full_report.database_status}
            },
            'database_stats': database_stats,
            'alerts': full_report.alerts
        }


def create_admin_monitor() -> AdminSystemMonitor:
    """
    創建管理員系統監控器實例
    
    Returns:
        AdminSystemMonitor: 管理員監控器實例
    """
    return AdminSystemMonitor()