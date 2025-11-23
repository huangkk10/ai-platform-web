"""
基礎搜尋策略抽象類
==================

所有具體搜尋策略都必須繼承此類並實現 execute() 方法。

⚠️ 重要：此策略系統與現有 ProtocolGuideSearchService 完全獨立
- Protocol Assistant 繼續使用原有 search_knowledge()
- Benchmark 系統使用這個新的策略系統
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseSearchStrategy(ABC):
    """
    搜尋策略基礎類
    
    所有具體搜尋策略都必須繼承此類並實現 execute() 方法
    """
    
    def __init__(
        self,
        search_service,
        name: str,
        description: str,
        **default_params
    ):
        """
        初始化策略
        
        Args:
            search_service: ProtocolGuideSearchService 實例
            name: 策略名稱（如 'section_only', 'hybrid_weighted'）
            description: 策略描述（用於日誌）
            **default_params: 預設參數
        """
        self.search_service = search_service
        self.name = name
        self.description = description
        self.default_params = default_params
    
    @abstractmethod
    def execute(
        self,
        query: str,
        limit: int = 10,
        **params
    ) -> List[Dict[str, Any]]:
        """
        執行搜尋策略
        
        子類必須實現此方法
        
        Args:
            query: 搜尋查詢
            limit: 返回結果數量
            **params: 策略特定參數
            
        Returns:
            List[Dict]: 搜尋結果列表
                [
                    {
                        'id': 文檔 ID,
                        'score': 相似度分數,
                        'title': 標題,
                        'content': 內容,
                        'metadata': {...},
                        'source': 'section' | 'document' | 'keyword',
                        'weight_applied': 權重（如果有）
                    },
                    ...
                ]
        """
        pass
    
    def _log(self, message: str, level: str = 'info'):
        """統一日誌格式"""
        log_func = getattr(logger, level, logger.info)
        log_func(f"[Strategy:{self.name}] {message}")
    
    def get_params(self, **override_params):
        """合併預設參數和覆蓋參數"""
        params = self.default_params.copy()
        params.update(override_params)
        return params
    
    def _format_result_metadata(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        標準化結果格式
        
        確保所有策略返回的結果格式一致
        """
        # 確保有 metadata
        if 'metadata' not in result:
            result['metadata'] = {}
        
        # 確保 metadata 中有 id
        if 'id' not in result['metadata'] and 'id' in result:
            result['metadata']['id'] = result['id']
        
        # 添加策略標記
        result['strategy'] = self.name
        
        return result
