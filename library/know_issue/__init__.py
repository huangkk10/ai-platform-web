"""
Know Issue Library - 問題知識庫統一管理
=====================================

提供所有 Know Issue 相關的功能：
- KnowIssueProcessor: 資料處理器
- KnowIssueViewSetManager: ViewSet 管理器  
- KnowIssueAPIHandler: API 處理器

使用方式：
```python
from library.know_issue import KnowIssueViewSetManager, process_know_issue_create

# ViewSet 管理器
manager = KnowIssueViewSetManager()
result = manager.handle_create(request, serializer)

# 便利函數
response = process_know_issue_create(request, serializer)
```
"""

import logging

# 設置 logger
logger = logging.getLogger(__name__)

# 核心組件導入
try:
    # 從各個模組導入主要組件
    from .processors import KnowIssueProcessor
    from .viewset_manager import KnowIssueViewSetManager  
    from .api_handlers import KnowIssueAPIHandler
    from .convenience_functions import (
        process_know_issue_create,
        process_know_issue_update,
        handle_dify_know_issue_search_api,
        create_know_issue_processor,
        create_know_issue_viewset_manager,
        create_know_issue_api_handler
    )
    
    # 備用組件導入
    from .fallback_handlers import (
        FallbackKnowIssueProcessor,
        fallback_know_issue_create,
        fallback_know_issue_update,
        fallback_dify_know_issue_search,
        fallback_know_issue_queryset_filter
    )
    
    KNOW_ISSUE_LIBRARY_AVAILABLE = True
    logger.info("✅ Know Issue Library 所有組件導入成功")
    
except ImportError as e:
    logger.warning(f"Know Issue library 組件導入失敗: {e}")
    
    # 設定所有組件為 None
    KnowIssueProcessor = None
    KnowIssueViewSetManager = None
    KnowIssueAPIHandler = None
    process_know_issue_create = None
    process_know_issue_update = None
    handle_dify_know_issue_search_api = None
    create_know_issue_processor = None
    create_know_issue_viewset_manager = None
    create_know_issue_api_handler = None
    
    # 備用組件
    FallbackKnowIssueProcessor = None
    fallback_know_issue_create = None
    fallback_know_issue_update = None
    fallback_dify_know_issue_search = None
    fallback_know_issue_queryset_filter = None
    
    KNOW_ISSUE_LIBRARY_AVAILABLE = False


def get_know_issue_library_status():
    """獲取 Know Issue library 狀態"""
    return {
        'available': KNOW_ISSUE_LIBRARY_AVAILABLE,
        'components': {
            'processor': KnowIssueProcessor is not None,
            'viewset_manager': KnowIssueViewSetManager is not None,
            'api_handler': KnowIssueAPIHandler is not None,
            'convenience_functions': process_know_issue_create is not None,
            'fallback_processor': FallbackKnowIssueProcessor is not None
        },
        'modules': [
            'processors.py - 資料處理器',
            'viewset_manager.py - ViewSet 管理器',
            'api_handlers.py - API 處理器',
            'convenience_functions.py - 便利函數',
            'fallback_handlers.py - 備用處理器'
        ]
    }


# 導出所有組件
__all__ = [
    # 核心組件
    'KnowIssueProcessor',
    'KnowIssueViewSetManager', 
    'KnowIssueAPIHandler',
    
    # 便利函數
    'process_know_issue_create',
    'process_know_issue_update', 
    'handle_dify_know_issue_search_api',
    'create_know_issue_processor',
    'create_know_issue_viewset_manager',
    'create_know_issue_api_handler',
    
    # 備用組件
    'FallbackKnowIssueProcessor',
    'fallback_know_issue_create',
    'fallback_know_issue_update',
    'fallback_dify_know_issue_search',
    'fallback_know_issue_queryset_filter',
    
    # 狀態和工具
    'KNOW_ISSUE_LIBRARY_AVAILABLE',
    'get_know_issue_library_status'
]