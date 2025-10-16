"""
Protocol Guide Library - Protocol Assistant 知識庫
===============================================

這是使用通用基礎架構創建的示例知識庫，展示如何快速創建新知識庫系統。

使用的基礎架構：library/common/knowledge_base/

創建時間：約 15 分鐘
代碼量：約 70 行（對比原始方式的 1000+ 行）
"""

from .api_handlers import ProtocolGuideAPIHandler
from .viewset_manager import ProtocolGuideViewSetManager
from .search_service import ProtocolGuideSearchService
from .vector_service import ProtocolGuideVectorService

__all__ = [
    'ProtocolGuideAPIHandler',
    'ProtocolGuideViewSetManager',
    'ProtocolGuideSearchService',
    'ProtocolGuideVectorService',
]

__version__ = '1.0.0'
