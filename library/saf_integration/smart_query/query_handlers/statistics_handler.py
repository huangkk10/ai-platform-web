"""
StatisticsHandler - 統計查詢處理器
==================================

處理以下意圖：
- count_projects: 統計專案數量
- list_all_customers: 列出所有客戶
- list_all_controllers: 列出所有控制器

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from typing import Dict, Any, List

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class StatisticsHandler(BaseHandler):
    """
    統計查詢處理器
    
    處理各種統計類型的查詢請求。
    """
    
    handler_name = "statistics_handler"
    supported_intent = "statistics"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行統計查詢
        
        Args:
            parameters: {
                "query_type": "count_projects" | "list_customers" | "list_controllers" | "list_pls",
                "customer": "WD" (可選，用於 count_projects)
            }
            
        Returns:
            QueryResult: 統計結果
        """
        self._log_query(parameters)
        
        query_type = parameters.get('query_type', 'count_projects')
        
        try:
            if query_type == 'count_projects':
                return self._count_projects(parameters)
            elif query_type == 'list_customers':
                return self._list_all_customers(parameters)
            elif query_type == 'list_controllers':
                return self._list_all_controllers(parameters)
            elif query_type == 'list_pls':
                return self._list_all_pls(parameters)
            else:
                return QueryResult.error(
                    f"不支援的統計類型: {query_type}",
                    self.handler_name,
                    parameters
                )
                
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def count_projects(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        統計專案數量（公開方法）
        
        Args:
            parameters: {"customer": "WD"} (可選)
            
        Returns:
            QueryResult: 專案數量統計
        """
        return self._count_projects(parameters)
    
    def list_customers(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有客戶（公開方法）
        
        Returns:
            QueryResult: 客戶列表
        """
        return self._list_all_customers(parameters)
    
    def list_controllers(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有控制器（公開方法）
        
        Returns:
            QueryResult: 控制器列表
        """
        return self._list_all_controllers(parameters)
    
    def _count_projects(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        統計專案數量
        
        Args:
            parameters: {"customer": "WD"} (可選)
            
        Returns:
            QueryResult: 專案數量統計
        """
        customer = parameters.get('customer')
        
        # 使用正確的 API 方法獲取所有專案
        projects_list = self.api_client.get_all_projects()
        
        if not projects_list:
            return QueryResult.error(
                "無法獲取專案列表",
                self.handler_name,
                parameters
            )
        
        all_projects_list = projects_list  # 保存完整列表用於分組統計
        
        # 如果指定了客戶，則過濾
        if customer:
            projects_list = self._filter_projects(projects_list, 'customer', customer)
        
        # 去重：根據 projectName 去除重複的專案
        # SAF API 可能返回多個子專案（同一個專案名稱多個記錄）
        original_count = len(projects_list)
        unique_projects = self._deduplicate_projects_by_name(projects_list)
        count = len(unique_projects)
        
        # 構建統計資料
        stats_data = {
            'total_count': count,
            'original_count': original_count,  # 原始記錄數（含重複）
            'customer': customer if customer else '全部',
        }
        
        # 如果沒有指定客戶，添加按客戶分組的統計
        if not customer:
            customer_stats = self._group_by_customer(all_projects_list)
            stats_data['by_customer'] = customer_stats
        
        message = (
            f"{'客戶 ' + customer if customer else '總共'}有 {count} 個專案"
        )
        
        result = QueryResult.success(
            data=stats_data,
            count=count,
            query_type="count_projects",
            parameters=parameters,
            message=message
        )
        
        self._log_result(result)
        return result
    
    def _list_all_customers(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有客戶
        
        Returns:
            QueryResult: 客戶列表
        """
        # 使用正確的 API 方法獲取所有專案
        projects_list = self.api_client.get_all_projects()
        
        if not projects_list:
            return QueryResult.error(
                "無法獲取專案列表",
                self.handler_name,
                parameters
            )
        
        # 提取唯一客戶
        customers = self._extract_unique_values(projects_list, 'customer')
        
        # 統計每個客戶的專案數
        customer_stats = self._group_by_customer(projects_list)
        
        result = QueryResult.success(
            data={
                'customers': customers,
                'customer_count': len(customers),
                'customer_stats': customer_stats
            },
            count=len(customers),
            query_type="list_customers",
            parameters=parameters,
            message=f"共有 {len(customers)} 個客戶"
        )
        
        self._log_result(result)
        return result
    
    def _list_all_controllers(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有控制器
        
        Returns:
            QueryResult: 控制器列表
        """
        # 使用正確的 API 方法獲取所有專案
        projects_list = self.api_client.get_all_projects()
        
        if not projects_list:
            return QueryResult.error(
                "無法獲取專案列表",
                self.handler_name,
                parameters
            )
        
        # 提取唯一控制器
        controllers = self._extract_unique_values(projects_list, 'controller')
        
        # 統計每個控制器的專案數
        controller_stats = self._group_by_field(projects_list, 'controller')
        
        result = QueryResult.success(
            data={
                'controllers': controllers,
                'controller_count': len(controllers),
                'controller_stats': controller_stats
            },
            count=len(controllers),
            query_type="list_controllers",
            parameters=parameters,
            message=f"共有 {len(controllers)} 種控制器"
        )
        
        self._log_result(result)
        return result
    
    def _list_all_pls(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有專案負責人 (PL)
        
        Returns:
            QueryResult: PL 列表及其負責的專案數量
        """
        # 獲取所有專案
        projects_list = self.api_client.get_all_projects()
        
        if not projects_list:
            return QueryResult.error(
                "無法獲取專案列表",
                self.handler_name,
                parameters
            )
        
        # 去重專案（按 projectName）
        unique_projects = self._deduplicate_projects_by_name(projects_list)
        
        # 提取唯一 PL
        pls = self._extract_unique_values(unique_projects, 'pl')
        
        # 統計每個 PL 的專案數
        pl_stats = self._group_by_field(unique_projects, 'pl')
        
        result = QueryResult.success(
            data={
                'pls': pls,
                'pl_count': len(pls),
                'pl_stats': pl_stats
            },
            count=len(pls),
            query_type="list_pls",
            parameters=parameters,
            message=f"共有 {len(pls)} 位專案負責人"
        )
        
        self._log_result(result)
        return result
    
    def list_pls(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        列出所有專案負責人（公開方法）
        
        Returns:
            QueryResult: PL 列表
        """
        return self._list_all_pls(parameters)
    
    def _group_by_customer(self, projects: List[Dict]) -> Dict[str, int]:
        """
        按客戶分組統計專案數量
        
        Args:
            projects: 專案列表
            
        Returns:
            Dict: 客戶 -> 專案數量
        """
        return self._group_by_field(projects, 'customer')
    
    def _group_by_field(self, projects: List[Dict], field: str) -> Dict[str, int]:
        """
        按指定欄位分組統計
        
        Args:
            projects: 專案列表
            field: 分組欄位
            
        Returns:
            Dict: 欄位值 -> 數量
        """
        stats = {}
        for project in projects:
            value = project.get(field, 'Unknown')
            if value:
                stats[value] = stats.get(value, 0) + 1
        
        # 按數量排序
        return dict(sorted(stats.items(), key=lambda x: x[1], reverse=True))
