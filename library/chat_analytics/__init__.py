"""
Chat Analytics Library - 聊天分析統一管理
==========================================

提供聊天使用統計和記錄相關功能：
- ChatUsageStatisticsHandler: 統計分析處理器
- ChatUsageRecorder: 聊天記錄處理器  
- ChatAnalyticsAPIHandler: API 處理器

使用方式：
```python
from library.chat_analytics import (
    handle_chat_usage_statistics_api,
    handle_record_chat_usage_api,
    ChatUsageStatisticsHandler
)

# API 處理
response = handle_chat_usage_statistics_api(request)
response = handle_record_chat_usage_api(request)

# 程式化使用
handler = ChatUsageStatisticsHandler()
stats = handler.get_statistics(days=30)
```
"""

import logging

# 設置 logger
logger = logging.getLogger(__name__)

# 聊天類型映射和常數
CHAT_TYPE_DISPLAY_MAP = {
    'know_issue_chat': 'Protocol RAG',
    'log_analyze_chat': 'AI OCR', 
    'rvt_assistant_chat': 'RVT Assistant'
}

VALID_CHAT_TYPES = ['know_issue_chat', 'log_analyze_chat', 'rvt_assistant_chat']

# 核心組件導入
try:
    # 從各個模組導入主要組件
    from .statistics_handler import ChatUsageStatisticsHandler
    from .usage_recorder import ChatUsageRecorder
    from .api_handler import ChatAnalyticsAPIHandler
    from .convenience_functions import (
        handle_chat_usage_statistics_api,
        handle_record_chat_usage_api,
        create_chat_statistics_handler,
        create_chat_usage_recorder,
        create_chat_analytics_api_handler,
        get_statistics_for_days
    )
    
    # 備用組件導入
    from .fallback_handlers import (
        FallbackChatAnalyticsHandler,
        fallback_chat_usage_statistics_api,
        fallback_record_chat_usage_api,
        get_fallback_analytics_status
    )
    
    CHAT_ANALYTICS_LIBRARY_AVAILABLE = True
    logger.info("✅ Chat Analytics Library 所有組件導入成功")
    
except ImportError as e:
    logger.warning(f"Chat Analytics library 組件導入失敗: {e}")
    
    # 設定所有組件為 None
    ChatUsageStatisticsHandler = None
    ChatUsageRecorder = None
    ChatAnalyticsAPIHandler = None
    handle_chat_usage_statistics_api = None
    handle_record_chat_usage_api = None
    create_chat_statistics_handler = None
    create_chat_usage_recorder = None
    create_chat_analytics_api_handler = None
    get_statistics_for_days = None
    
    # 備用組件
    FallbackChatAnalyticsHandler = None
    fallback_chat_usage_statistics_api = None
    fallback_record_chat_usage_api = None
    get_fallback_analytics_status = None
    
    CHAT_ANALYTICS_LIBRARY_AVAILABLE = False


def get_chat_analytics_library_status():
    """獲取 Chat Analytics Library 狀態"""
    try:
        return {
            'available': CHAT_ANALYTICS_LIBRARY_AVAILABLE,
            'valid_chat_types': VALID_CHAT_TYPES,
            'chat_type_mapping': CHAT_TYPE_DISPLAY_MAP,
            'components': {
                'statistics_handler': ChatUsageStatisticsHandler is not None,
                'usage_recorder': ChatUsageRecorder is not None,
                'api_handler': ChatAnalyticsAPIHandler is not None,
                'convenience_functions': handle_chat_usage_statistics_api is not None,
                'fallback_handler': FallbackChatAnalyticsHandler is not None
            },
            'modules': [
                'statistics_handler.py - 統計分析處理器',
                'usage_recorder.py - 聊天記錄處理器',
                'api_handler.py - API 處理器',
                'convenience_functions.py - 便利函數',
                'fallback_handlers.py - 備用處理器'
            ]
        }
    except Exception as e:
        logger.error(f"Get library status failed: {e}")
        return {
            'available': False,
            'error': str(e),
            'components': {}
        }


# 導出主要組件
__all__ = [
    # 核心組件
    'ChatUsageStatisticsHandler',
    'ChatUsageRecorder',
    'ChatAnalyticsAPIHandler',
    
    # 便利函數
    'handle_chat_usage_statistics_api',
    'handle_record_chat_usage_api',
    'get_statistics_for_days',
    
    # 創建函數
    'create_chat_statistics_handler',
    'create_chat_usage_recorder',
    'create_chat_analytics_api_handler',
    
    # 備用組件
    'FallbackChatAnalyticsHandler',
    'fallback_chat_usage_statistics_api',
    'fallback_record_chat_usage_api',
    'get_fallback_analytics_status',
    
    # 狀態和常數
    'get_chat_analytics_library_status',
    'CHAT_ANALYTICS_LIBRARY_AVAILABLE',
    'VALID_CHAT_TYPES',
    'CHAT_TYPE_DISPLAY_MAP'
]