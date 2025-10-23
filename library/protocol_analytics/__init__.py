"""
Protocol Analytics Library - Protocol Assistant 分析功能模組

此模組提供 Protocol Assistant 的深度分析功能，包括：
- 問題分類與統計
- 用戶滿意度分析
- 對話品質評估
- 趨勢分析與報告

主要組件：
- question_classifier.py: 問題智能分類器
- satisfaction_analyzer.py: 滿意度分析器
- statistics_manager.py: 統計數據管理器
- api_handlers.py: API 處理器

基於 Common Analytics 基礎設施，複用 BaseStatisticsManager
"""

# 版本信息
__version__ = '1.0.0'
__author__ = 'AI Platform Team'

# 檢查依賴可用性
try:
    from django.db import models
    from django.utils import timezone
    DJANGO_AVAILABLE = True
except ImportError:
    DJANGO_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# 庫可用性標誌
PROTOCOL_ANALYTICS_AVAILABLE = DJANGO_AVAILABLE

# 導入主要組件
if PROTOCOL_ANALYTICS_AVAILABLE:
    try:
        from .question_classifier import (
            ProtocolQuestionClassifier,
            classify_protocol_question,
            get_protocol_categories
        )
        from .statistics_manager import (
            ProtocolStatisticsManager,
            get_protocol_analytics_stats
        )
        from .api_handlers import (
            ProtocolAnalyticsAPIHandler,
            handle_protocol_feedback_api,
            handle_protocol_analytics_api
        )
        
        # 複用 RVT Analytics 的滿意度分析器
        from library.rvt_analytics.satisfaction_analyzer import (
            SatisfactionAnalyzer,
            analyze_user_satisfaction,
            get_satisfaction_trends
        )
        
        QUESTION_CLASSIFIER_AVAILABLE = True
        SATISFACTION_ANALYZER_AVAILABLE = True
        STATISTICS_MANAGER_AVAILABLE = True
        API_HANDLERS_AVAILABLE = True
        
    except ImportError as e:
        print(f"Protocol Analytics 部分組件導入失敗: {e}")
        
        # 設置備用標誌
        QUESTION_CLASSIFIER_AVAILABLE = False
        SATISFACTION_ANALYZER_AVAILABLE = False
        STATISTICS_MANAGER_AVAILABLE = False
        API_HANDLERS_AVAILABLE = False
        
        # 提供備用函數
        def classify_protocol_question(*args, **kwargs):
            return 'unknown'
            
        def analyze_user_satisfaction(*args, **kwargs):
            return {'satisfaction': 'unknown'}
            
        def get_protocol_analytics_stats(*args, **kwargs):
            return {'error': 'Analytics not available'}
            
        def handle_protocol_feedback_api(*args, **kwargs):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Analytics API not available'}, status=503)
            
        def handle_protocol_analytics_api(*args, **kwargs):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Analytics API not available'}, status=503)

else:
    # Django 不可用時的備用實現
    QUESTION_CLASSIFIER_AVAILABLE = False
    SATISFACTION_ANALYZER_AVAILABLE = False
    STATISTICS_MANAGER_AVAILABLE = False
    API_HANDLERS_AVAILABLE = False
    
    def classify_protocol_question(*args, **kwargs):
        return 'unknown'
        
    def analyze_user_satisfaction(*args, **kwargs):
        return {'satisfaction': 'unknown'}
        
    def get_protocol_analytics_stats(*args, **kwargs):
        return {'error': 'Django not available'}
        
    def handle_protocol_feedback_api(*args, **kwargs):
        return {'error': 'Django not available'}
        
    def handle_protocol_analytics_api(*args, **kwargs):
        return {'error': 'Django not available'}

# 便利函數導出
__all__ = [
    # 可用性標誌
    'PROTOCOL_ANALYTICS_AVAILABLE',
    'QUESTION_CLASSIFIER_AVAILABLE',
    'SATISFACTION_ANALYZER_AVAILABLE',
    'STATISTICS_MANAGER_AVAILABLE',
    'API_HANDLERS_AVAILABLE',
    
    # 主要功能函數
    'classify_protocol_question', 
    'analyze_user_satisfaction',
    'get_protocol_analytics_stats',
    'handle_protocol_feedback_api',
    'handle_protocol_analytics_api',
    
    # 類別導出 (如果可用)
    'ProtocolQuestionClassifier',
    'SatisfactionAnalyzer',
    'ProtocolStatisticsManager',
    'ProtocolAnalyticsAPIHandler'
]

# 版本檢查和兼容性信息
def get_library_info():
    """獲取 Protocol Analytics Library 資訊"""
    return {
        'version': __version__,
        'available': PROTOCOL_ANALYTICS_AVAILABLE,
        'components': {
            'question_classifier': QUESTION_CLASSIFIER_AVAILABLE,
            'satisfaction_analyzer': SATISFACTION_ANALYZER_AVAILABLE,
            'statistics_manager': STATISTICS_MANAGER_AVAILABLE,
            'api_handlers': API_HANDLERS_AVAILABLE
        },
        'dependencies': {
            'django': DJANGO_AVAILABLE,
            'numpy': NUMPY_AVAILABLE
        }
    }

# 初始化日誌
if PROTOCOL_ANALYTICS_AVAILABLE:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Protocol Analytics Library v{__version__} 初始化完成")
    logger.info(f"可用組件: {sum(1 for k, v in get_library_info()['components'].items() if v)}/4")
else:
    print(f"Protocol Analytics Library v{__version__} - Django 不可用，使用備用模式")
