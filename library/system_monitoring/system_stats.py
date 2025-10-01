"""
系統統計信息收集器

提供系統基本統計信息收集功能，包括：
- 用戶統計
- 數據統計 
- 應用統計
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class StatItem:
    """統計項目資料類別"""
    count: int
    description: str
    category: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return asdict(self)


class SystemStatsCollector:
    """系統統計信息收集器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def get_user_statistics(self, connection=None) -> Dict[str, StatItem]:
        """
        獲取用戶相關統計
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, StatItem]: 用戶統計信息
        """
        stats = {}
        
        try:
            if connection is None:
                from django.db import connection
                
            with connection.cursor() as cursor:
                # 活躍用戶數量
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_active = true")
                active_users = cursor.fetchone()[0]
                stats['active_users'] = StatItem(
                    count=active_users,
                    description='系統中的活躍用戶數量',
                    category='users'
                )
                
                # 總用戶數量
                cursor.execute("SELECT COUNT(*) FROM auth_user")
                total_users = cursor.fetchone()[0]
                stats['total_users'] = StatItem(
                    count=total_users,
                    description='系統中的總用戶數量',
                    category='users'
                )
                
                # 管理員用戶數量
                cursor.execute("SELECT COUNT(*) FROM auth_user WHERE is_staff = true")
                admin_users = cursor.fetchone()[0]
                stats['admin_users'] = StatItem(
                    count=admin_users,
                    description='系統中的管理員用戶數量',
                    category='users'
                )
                
        except Exception as e:
            self.logger.error(f"Failed to collect user statistics: {str(e)}")
            stats['error'] = StatItem(
                count=0,
                description=f'用戶統計獲取失敗: {str(e)}',
                category='error'
            )
            
        return stats
    
    def get_knowledge_statistics(self, connection=None) -> Dict[str, StatItem]:
        """
        獲取知識庫相關統計
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, StatItem]: 知識庫統計信息
        """
        stats = {}
        
        try:
            if connection is None:
                from django.db import connection
                
            with connection.cursor() as cursor:
                # Know Issue 數量
                cursor.execute("SELECT COUNT(*) FROM know_issue")
                total_issues = cursor.fetchone()[0]
                stats['total_know_issues'] = StatItem(
                    count=total_issues,
                    description='知識庫中的問題記錄數量',
                    category='knowledge'
                )
                
                # RVT Guide 數量
                try:
                    cursor.execute("SELECT COUNT(*) FROM rvt_guide")
                    total_guides = cursor.fetchone()[0]
                    stats['total_rvt_guides'] = StatItem(
                        count=total_guides,
                        description='RVT 使用指南記錄數量',
                        category='knowledge'
                    )
                except Exception:
                    # 如果 RVT Guide 表不存在，跳過
                    pass
                
                # OCR 測試記錄數量
                try:
                    cursor.execute("SELECT COUNT(*) FROM ocr_storage_benchmark")
                    total_ocr = cursor.fetchone()[0]
                    stats['total_ocr_benchmarks'] = StatItem(
                        count=total_ocr,
                        description='OCR 存儲基準測試記錄數量',
                        category='knowledge'
                    )
                except Exception:
                    # 如果 OCR 表不存在，跳過
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to collect knowledge statistics: {str(e)}")
            stats['error'] = StatItem(
                count=0,
                description=f'知識庫統計獲取失敗: {str(e)}',
                category='error'
            )
            
        return stats
    
    def get_project_statistics(self, connection=None) -> Dict[str, StatItem]:
        """
        獲取專案相關統計
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, StatItem]: 專案統計信息
        """
        stats = {}
        
        try:
            if connection is None:
                from django.db import connection
                
            with connection.cursor() as cursor:
                # 專案數量
                try:
                    cursor.execute("SELECT COUNT(*) FROM project")
                    total_projects = cursor.fetchone()[0]
                    stats['total_projects'] = StatItem(
                        count=total_projects,
                        description='系統中的專案數量',
                        category='projects'
                    )
                except Exception:
                    # 如果 Project 表不存在，跳過
                    pass
                
                # 任務數量
                try:
                    cursor.execute("SELECT COUNT(*) FROM task")
                    total_tasks = cursor.fetchone()[0]
                    stats['total_tasks'] = StatItem(
                        count=total_tasks,
                        description='系統中的任務數量',
                        category='projects'
                    )
                except Exception:
                    # 如果 Task 表不存在，跳過
                    pass
                    
        except Exception as e:
            self.logger.error(f"Failed to collect project statistics: {str(e)}")
            stats['error'] = StatItem(
                count=0,
                description=f'專案統計獲取失敗: {str(e)}',
                category='error'
            )
            
        return stats
    
    def get_basic_statistics(self, connection=None) -> Dict[str, StatItem]:
        """
        獲取基本統計信息（僅包含公開的、非敏感信息）
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, StatItem]: 基本統計信息
        """
        stats = {}
        
        # 合併各類統計
        user_stats = self.get_user_statistics(connection)
        knowledge_stats = self.get_knowledge_statistics(connection)
        
        # 只返回基本的統計項目
        if 'active_users' in user_stats:
            stats['active_users'] = user_stats['active_users']
        
        if 'total_know_issues' in knowledge_stats:
            stats['total_know_issues'] = knowledge_stats['total_know_issues']
            
        # 如果有錯誤，也包含錯誤信息
        for stat_dict in [user_stats, knowledge_stats]:
            if 'error' in stat_dict:
                stats['error'] = stat_dict['error']
                break
                
        return stats
    
    def get_all_statistics(self, connection=None) -> Dict[str, StatItem]:
        """
        獲取完整統計信息
        
        Args:
            connection: Django database connection object
            
        Returns:
            Dict[str, StatItem]: 完整統計信息
        """
        stats = {}
        
        # 合併所有統計類別
        stats.update(self.get_user_statistics(connection))
        stats.update(self.get_knowledge_statistics(connection))
        stats.update(self.get_project_statistics(connection))
        
        return stats
    
    def get_statistics_dict(self, include_all: bool = False, connection=None) -> Dict[str, Dict[str, Any]]:
        """
        獲取統計信息的字典格式
        
        Args:
            include_all: 是否包含所有統計信息
            connection: Django database connection object
            
        Returns:
            Dict[str, Dict[str, Any]]: 字典格式的統計信息
        """
        if include_all:
            stats = self.get_all_statistics(connection)
        else:
            stats = self.get_basic_statistics(connection)
            
        return {name: stat.to_dict() for name, stat in stats.items()}


def create_stats_collector() -> SystemStatsCollector:
    """
    創建系統統計收集器實例
    
    Returns:
        SystemStatsCollector: 統計收集器實例
    """
    return SystemStatsCollector()