"""
通用知識庫基礎架構
==================

這個模組提供所有知識庫系統的抽象基礎類別，用於減少代碼重複，
統一知識庫的開發模式。

主要組件：
- BaseKnowledgeBaseAPIHandler: API 端點處理基礎類別
- BaseKnowledgeBaseViewSetManager: ViewSet 管理基礎類別
- BaseKnowledgeBaseSearchService: 搜索服務基礎類別
- BaseKnowledgeBaseVectorService: 向量服務基礎類別

使用方式：
```python
from library.common.knowledge_base import BaseKnowledgeBaseViewSetManager

class ProtocolGuideViewSetManager(BaseKnowledgeBaseViewSetManager):
    model_class = ProtocolGuide
    serializer_class = ProtocolGuideSerializer
    list_serializer_class = ProtocolGuideListSerializer
    
    # 只需覆寫特殊邏輯
    def perform_create(self, serializer):
        # 自定義創建邏輯
        pass
```

優點：
- 新增知識庫只需 10-20 行代碼
- 修改基礎類別自動應用所有知識庫
- 統一維護，減少 bug
- 強制統一的 API 設計模式
"""

from .base_api_handler import BaseKnowledgeBaseAPIHandler
from .base_viewset_manager import BaseKnowledgeBaseViewSetManager
from .base_search_service import BaseKnowledgeBaseSearchService
from .base_vector_service import BaseKnowledgeBaseVectorService

__all__ = [
    'BaseKnowledgeBaseAPIHandler',
    'BaseKnowledgeBaseViewSetManager',
    'BaseKnowledgeBaseSearchService',
    'BaseKnowledgeBaseVectorService',
]

__version__ = '1.0.0'
