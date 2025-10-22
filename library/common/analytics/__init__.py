"""
Common Analytics Library - 共用分析基礎設施

提供所有 Assistant 分析功能的共用基礎類別和工具。

Architecture:
- BaseStatisticsManager: 統計數據管理基礎類別
- BaseQuestionAnalyzer: 問題分析基礎類別
- BaseSatisfactionAnalyzer: 滿意度分析基礎類別
- BaseAPIHandler: API 處理器基礎類別

Usage:
    from library.common.analytics.base_statistics_manager import BaseStatisticsManager
    
    class RVTStatisticsManager(BaseStatisticsManager):
        def get_assistant_type(self):
            return 'rvt_assistant'
"""

__version__ = '1.0.0'
__author__ = 'AI Platform Team'

# 檢查 Django 可用性
DJANGO_AVAILABLE = False
try:
    import django
    DJANGO_AVAILABLE = True
except ImportError:
    pass

COMMON_ANALYTICS_AVAILABLE = DJANGO_AVAILABLE

if COMMON_ANALYTICS_AVAILABLE:
    try:
        from .base_statistics_manager import BaseStatisticsManager
        from .base_question_analyzer import BaseQuestionAnalyzer
        from .base_satisfaction_analyzer import BaseSatisfactionAnalyzer
        from .base_api_handler import BaseAPIHandler
        
        __all__ = [
            'BaseStatisticsManager',
            'BaseQuestionAnalyzer',
            'BaseSatisfactionAnalyzer',
            'BaseAPIHandler',
            'COMMON_ANALYTICS_AVAILABLE',
        ]
    except ImportError as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Common Analytics 模組載入失敗: {e}")
        
        COMMON_ANALYTICS_AVAILABLE = False
        
        # 提供降級版本
        class BaseStatisticsManager:
            def __init__(self):
                raise ImportError("Common Analytics not available")
        
        class BaseQuestionAnalyzer:
            def __init__(self):
                raise ImportError("Common Analytics not available")
        
        class BaseSatisfactionAnalyzer:
            def __init__(self):
                raise ImportError("Common Analytics not available")
        
        class BaseAPIHandler:
            def __init__(self):
                raise ImportError("Common Analytics not available")
        
        __all__ = [
            'COMMON_ANALYTICS_AVAILABLE',
        ]
else:
    # Django 不可用時的降級處理
    class BaseStatisticsManager:
        def __init__(self):
            raise ImportError("Django is required for Common Analytics")
    
    class BaseQuestionAnalyzer:
        def __init__(self):
            raise ImportError("Django is required for Common Analytics")
    
    class BaseSatisfactionAnalyzer:
        def __init__(self):
            raise ImportError("Django is required for Common Analytics")
    
    class BaseAPIHandler:
        def __init__(self):
            raise ImportError("Django is required for Common Analytics")
    
    __all__ = [
        'COMMON_ANALYTICS_AVAILABLE',
    ]


def get_library_info():
    """獲取 Library 資訊"""
    return {
        'name': 'Common Analytics Library',
        'version': __version__,
        'available': COMMON_ANALYTICS_AVAILABLE,
        'django_available': DJANGO_AVAILABLE,
        'description': '提供所有 Assistant 分析功能的共用基礎設施'
    }
