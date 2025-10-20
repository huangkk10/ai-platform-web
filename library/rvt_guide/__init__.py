"""
RVT Guide Library - 統一管理 RVT Guide 相關功能

這個模組提供完整的 RVT Guide 功能，包括：
- API 處理器 (api_handlers.py)
- ViewSet 管理器 (viewset_manager.py) 
- 搜索服務 (search_service.py)
- 向量處理 (vector_service.py)
- 備用實現 (fallback_handlers.py)

目標：減少 backend/api/views.py 中的程式碼量，提高可維護性
"""

from .api_handlers import RVTGuideAPIHandler
from .viewset_manager import RVTGuideViewSetManager
from .search_service import RVTGuideSearchService
from .vector_service import RVTGuideVectorService
from .fallback_handlers import (
    RVTGuideFallbackHandler,
    FallbackViewSetManager,
    FallbackSearchService,
    fallback_dify_rvt_guide_search,
    fallback_rvt_guide_chat,
    fallback_rvt_guide_config
)

# ✅ 啟用 RVT Guide Library
RVT_GUIDE_LIBRARY_AVAILABLE = True

__all__ = [
    'RVTGuideAPIHandler',
    'RVTGuideViewSetManager', 
    'RVTGuideSearchService',
    'RVTGuideVectorService',
    'RVTGuideFallbackHandler',
    'FallbackViewSetManager',
    'FallbackSearchService',
    'fallback_dify_rvt_guide_search',
    'fallback_rvt_guide_chat',
    'fallback_rvt_guide_config',
    'RVT_GUIDE_LIBRARY_AVAILABLE'  # 導出標誌
]