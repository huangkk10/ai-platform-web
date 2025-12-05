"""
SAF 查詢處理器基類
==================

定義所有查詢處理器的基本介面和通用功能。

作者：AI Platform Team
創建日期：2025-12-05
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class QueryStatus(Enum):
    """查詢狀態枚舉"""
    SUCCESS = "success"
    NO_RESULTS = "no_results"
    ERROR = "error"
    PARTIAL = "partial"


@dataclass
class QueryResult:
    """
    查詢結果數據類
    
    Attributes:
        status: 查詢狀態
        data: 查詢結果資料
        count: 結果數量
        query_type: 查詢類型
        parameters: 查詢參數
        message: 附加訊息
        error_message: 錯誤訊息（如果有）
        metadata: 額外的元數據
    """
    status: QueryStatus
    data: Any = None
    count: int = 0
    query_type: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    message: str = ""
    error_message: Optional[str] = None  # 重命名以避免與 classmethod 衝突
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """檢查查詢是否成功"""
        return self.status == QueryStatus.SUCCESS
    
    def has_data(self) -> bool:
        """檢查是否有資料"""
        if self.data is None:
            return False
        if isinstance(self.data, (list, dict)):
            return len(self.data) > 0
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'status': self.status.value,
            'data': self.data,
            'count': self.count,
            'query_type': self.query_type,
            'parameters': self.parameters,
            'message': self.message,
            'error': self.error_message,  # 使用 error_message 欄位
            'metadata': self.metadata
        }
    
    @classmethod
    def success(cls, data: Any, count: int = None, query_type: str = "",
                parameters: Dict[str, Any] = None, message: str = "",
                metadata: Dict[str, Any] = None) -> 'QueryResult':
        """創建成功的查詢結果"""
        if count is None:
            if isinstance(data, list):
                count = len(data)
            elif isinstance(data, dict):
                count = 1
            else:
                count = 1 if data else 0
        
        return cls(
            status=QueryStatus.SUCCESS,
            data=data,
            count=count,
            query_type=query_type,
            parameters=parameters or {},
            message=message,
            metadata=metadata or {}
        )
    
    @classmethod
    def no_results(cls, query_type: str = "", parameters: Dict[str, Any] = None,
                   message: str = "未找到符合條件的資料") -> 'QueryResult':
        """創建無結果的查詢結果"""
        return cls(
            status=QueryStatus.NO_RESULTS,
            data=[],
            count=0,
            query_type=query_type,
            parameters=parameters or {},
            message=message
        )
    
    @classmethod
    def error(cls, error_msg: str, query_type: str = "",
              parameters: Dict[str, Any] = None) -> 'QueryResult':
        """創建錯誤的查詢結果"""
        return cls(
            status=QueryStatus.ERROR,
            data=None,
            count=0,
            query_type=query_type,
            parameters=parameters or {},
            error_message=error_msg  # 使用新欄位名
        )


class BaseHandler(ABC):
    """
    查詢處理器基類
    
    所有具體的處理器都應繼承此類並實作 execute 方法。
    """
    
    # 子類應覆寫這些屬性
    handler_name: str = "base"
    supported_intent: str = ""
    
    def __init__(self):
        """初始化處理器"""
        # 延遲導入 SAF API 客戶端
        self._api_client = None
    
    @property
    def api_client(self):
        """
        獲取 SAF API 客戶端（延遲初始化）
        """
        if self._api_client is None:
            from library.saf_integration.api_client import SAFAPIClient
            self._api_client = SAFAPIClient()
        return self._api_client
    
    @abstractmethod
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行查詢
        
        Args:
            parameters: 查詢參數
            
        Returns:
            QueryResult: 查詢結果
        """
        pass
    
    def validate_parameters(self, parameters: Dict[str, Any], 
                           required: List[str] = None) -> Optional[str]:
        """
        驗證參數
        
        Args:
            parameters: 要驗證的參數
            required: 必要參數列表
            
        Returns:
            Optional[str]: 錯誤訊息，如果驗證通過則為 None
        """
        if required is None:
            required = []
        
        for param in required:
            if param not in parameters or not parameters[param]:
                return f"缺少必要參數: {param}"
        
        return None
    
    def _log_query(self, parameters: Dict[str, Any]):
        """記錄查詢日誌"""
        logger.info(f"[{self.handler_name}] 執行查詢: {parameters}")
    
    def _log_result(self, result: QueryResult):
        """記錄結果日誌"""
        logger.info(
            f"[{self.handler_name}] 查詢完成: "
            f"status={result.status.value}, count={result.count}"
        )
    
    def _handle_api_error(self, error: Exception, 
                         parameters: Dict[str, Any]) -> QueryResult:
        """
        處理 API 錯誤
        
        Args:
            error: 異常對象
            parameters: 查詢參數
            
        Returns:
            QueryResult: 錯誤結果
        """
        error_message = f"API 調用失敗: {str(error)}"
        logger.error(f"[{self.handler_name}] {error_message}")
        
        return QueryResult.error(
            error_message,  # 使用位置參數而非命名參數
            query_type=self.handler_name,
            parameters=parameters
        )
    
    def _filter_projects(self, projects: List[Dict], 
                        field: str, value: str) -> List[Dict]:
        """
        過濾專案列表
        
        Args:
            projects: 專案列表
            field: 過濾欄位
            value: 過濾值
            
        Returns:
            List[Dict]: 過濾後的專案列表
        """
        if not projects or not value:
            return projects
        
        value_lower = value.lower()
        filtered = []
        
        for project in projects:
            field_value = project.get(field, '')
            if field_value and value_lower in str(field_value).lower():
                filtered.append(project)
        
        return filtered
    
    def _extract_unique_values(self, projects: List[Dict], 
                               field: str) -> List[str]:
        """
        從專案列表中提取唯一值
        
        Args:
            projects: 專案列表
            field: 欄位名稱
            
        Returns:
            List[str]: 唯一值列表
        """
        values = set()
        for project in projects:
            value = project.get(field)
            if value:
                values.add(str(value))
        
        return sorted(list(values))
    
    def _format_project_data(self, project: Dict) -> Dict[str, Any]:
        """
        格式化單個專案資料
        
        Args:
            project: 原始專案資料
            
        Returns:
            Dict: 格式化後的專案資料
        """
        return {
            'projectName': project.get('projectName', ''),
            'customer': project.get('customer', ''),
            'controller': project.get('controller', ''),
            'nand': project.get('nand', ''),
            'pl': project.get('pl', ''),
            'status': project.get('status', ''),
            'createDate': project.get('createDate', ''),
        }
