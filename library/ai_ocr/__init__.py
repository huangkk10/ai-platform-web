"""
AI OCR Library - 統一導入模組

提供所有 AI OCR 相關組件的統一導入點：
- API 處理器
- ViewSet 管理器
- 聊天服務
- 搜索服務
- 備用處理器

使用方式：
    from library.ai_ocr import AIOCRAPIHandler, OCRStorageBenchmarkViewSetManager
"""

# 核心組件導入
try:
    from .api_handlers import (
        AIOCRAPIHandler,
        dify_ocr_chat_api,
        dify_chat_with_file_api,
        dify_ocr_storage_benchmark_search_api
    )
    from .viewset_manager import (
        OCRTestClassViewSetManager,
        OCRStorageBenchmarkViewSetManager,
        create_ocr_test_class_viewset_manager,
        create_ocr_storage_benchmark_viewset_manager
    )
    from .chat_service import (
        AIOCRChatService,
        AIOCRChatServiceFallback,
        create_ai_ocr_chat_service
    )
    from .search_service import (
        AIOCRSearchService,
        AIOCRSearchServiceFallback,
        create_ai_ocr_search_service,
        search_ocr_storage_benchmark_unified
    )
    from .fallback_handlers import (
        AIOCRFallbackHandler,
        FallbackViewSetManager,
        FallbackChatService,
        FallbackSearchService,
        fallback_dify_ocr_chat,
        fallback_dify_chat_with_file,
        fallback_dify_ocr_storage_benchmark_search,
        handle_dify_ocr_storage_benchmark_search_fallback,
        create_fallback_ocr_test_class_viewset_manager,
        create_fallback_ocr_storage_benchmark_viewset_manager,
        create_fallback_ai_ocr_chat_service,
        create_fallback_ai_ocr_search_service,
        handle_upload_image_fallback
    )
    
    AI_OCR_LIBRARY_AVAILABLE = True
    
except ImportError as e:
    # 如果有任何導入失敗，提供備用
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"AI OCR library 組件導入失敗: {e}")
    
    # 設定所有組件為 None
    AIOCRAPIHandler = None
    dify_ocr_chat_api = None
    dify_chat_with_file_api = None
    dify_ocr_storage_benchmark_search_api = None
    OCRTestClassViewSetManager = None
    OCRStorageBenchmarkViewSetManager = None
    AIOCRChatService = None
    AIOCRSearchService = None
    AIOCRFallbackHandler = None
    
    # 便利函數也設為 None
    create_ocr_test_class_viewset_manager = None
    create_ocr_storage_benchmark_viewset_manager = None
    create_ai_ocr_chat_service = None
    create_ai_ocr_search_service = None
    
    # 備用函數設為 None
    fallback_dify_ocr_chat = None
    fallback_dify_chat_with_file = None
    fallback_dify_ocr_storage_benchmark_search = None
    handle_dify_ocr_storage_benchmark_search_fallback = None
    
    AI_OCR_LIBRARY_AVAILABLE = False


# 便利函數：統一創建服務
def create_ai_ocr_api_handler():
    """創建 AI OCR API 處理器"""
    if AI_OCR_LIBRARY_AVAILABLE and AIOCRAPIHandler:
        return AIOCRAPIHandler()
    else:
        return None


def get_ai_ocr_library_status():
    """獲取 AI OCR library 狀態"""
    return {
        'available': AI_OCR_LIBRARY_AVAILABLE,
        'components': {
            'api_handler': AIOCRAPIHandler is not None,
            'viewset_managers': OCRTestClassViewSetManager is not None,
            'chat_service': AIOCRChatService is not None,
            'search_service': AIOCRSearchService is not None,
            'fallback_handler': AIOCRFallbackHandler is not None
        }
    }


# 導出所有主要組件
__all__ = [
    # 核心組件
    'AIOCRAPIHandler',
    'dify_ocr_chat_api',
    'dify_chat_with_file_api', 
    'dify_ocr_storage_benchmark_search_api',
    'OCRTestClassViewSetManager',
    'OCRStorageBenchmarkViewSetManager',
    'AIOCRChatService',
    'AIOCRSearchService',
    
    # 備用組件
    'AIOCRFallbackHandler',
    'FallbackViewSetManager',
    'FallbackChatService',
    'FallbackSearchService',
    
    # 便利函數
    'create_ocr_test_class_viewset_manager',
    'create_ocr_storage_benchmark_viewset_manager',
    'create_ai_ocr_chat_service',
    'create_ai_ocr_search_service',
    'create_ai_ocr_api_handler',
    'search_ocr_storage_benchmark_unified',
    
    # 備用函數
    'fallback_dify_ocr_chat',
    'fallback_dify_chat_with_file',
    'fallback_dify_ocr_storage_benchmark_search',
    'handle_dify_ocr_storage_benchmark_search_fallback',
    'create_fallback_ocr_test_class_viewset_manager',
    'create_fallback_ocr_storage_benchmark_viewset_manager',
    'create_fallback_ai_ocr_chat_service',
    'create_fallback_ai_ocr_search_service',
    'handle_upload_image_fallback',
    
    # 狀態
    'AI_OCR_LIBRARY_AVAILABLE',
    'get_ai_ocr_library_status'
]