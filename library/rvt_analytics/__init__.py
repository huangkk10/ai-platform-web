"""
RVT Analytics Library - RVT Assistant 分析功能模組

此模組提供 RVT Assistant 的深度分析功能，包括：
- 問題分類與統計
- 用戶滿意度分析
- 對話品質評估
- 趨勢分析與報告

主要組件：
- question_classifier.py: 問題智能分類器
- satisfaction_analyzer.py: 滿意度分析器
- statistics_manager.py: 統計數據管理器
- api_handlers.py: API 處理器
- report_generator.py: 報告生成器
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
RVT_ANALYTICS_AVAILABLE = DJANGO_AVAILABLE

# 導入主要組件
if RVT_ANALYTICS_AVAILABLE:
    try:
        from .message_feedback import (
            MessageFeedbackHandler,
            record_message_feedback,
            get_message_feedback_stats
        )
        from .question_classifier import (
            QuestionClassifier,
            classify_question,
            get_question_categories
        )
        from .satisfaction_analyzer import (
            SatisfactionAnalyzer,
            analyze_user_satisfaction,
            get_satisfaction_trends
        )
        from .statistics_manager import (
            StatisticsManager,
            get_rvt_analytics_stats
        )
        from .api_handlers import (
            RVTAnalyticsAPIHandler,
            handle_feedback_api,
            handle_analytics_api
        )
        
        MESSAGE_FEEDBACK_AVAILABLE = True
        QUESTION_CLASSIFIER_AVAILABLE = True
        SATISFACTION_ANALYZER_AVAILABLE = True
        STATISTICS_MANAGER_AVAILABLE = True
        API_HANDLERS_AVAILABLE = True
        
    except ImportError as e:
        print(f"RVT Analytics 部分組件導入失敗: {e}")
        
        # 設置備用標誌
        MESSAGE_FEEDBACK_AVAILABLE = False
        QUESTION_CLASSIFIER_AVAILABLE = False
        SATISFACTION_ANALYZER_AVAILABLE = False
        STATISTICS_MANAGER_AVAILABLE = False
        API_HANDLERS_AVAILABLE = False
        
        # 提供備用函數
        def record_message_feedback(*args, **kwargs):
            return {'success': False, 'error': 'RVT Analytics library not available'}
            
        def classify_question(*args, **kwargs):
            return 'unknown'
            
        def analyze_user_satisfaction(*args, **kwargs):
            return {'satisfaction': 'unknown'}
            
        def get_rvt_analytics_stats(*args, **kwargs):
            return {'error': 'Analytics not available'}
            
        def handle_feedback_api(*args, **kwargs):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Analytics API not available'}, status=503)
            
        def handle_analytics_api(*args, **kwargs):
            from django.http import JsonResponse
            return JsonResponse({'error': 'Analytics API not available'}, status=503)

else:
    # Django 不可用時的備用實現
    MESSAGE_FEEDBACK_AVAILABLE = False
    QUESTION_CLASSIFIER_AVAILABLE = False
    SATISFACTION_ANALYZER_AVAILABLE = False
    STATISTICS_MANAGER_AVAILABLE = False
    API_HANDLERS_AVAILABLE = False
    
    def record_message_feedback(*args, **kwargs):
        return {'success': False, 'error': 'Django not available'}
        
    def classify_question(*args, **kwargs):
        return 'unknown'
        
    def analyze_user_satisfaction(*args, **kwargs):
        return {'satisfaction': 'unknown'}
        
    def get_rvt_analytics_stats(*args, **kwargs):
        return {'error': 'Django not available'}
        
    def handle_feedback_api(*args, **kwargs):
        return {'error': 'Django not available'}
        
    def handle_analytics_api(*args, **kwargs):
        return {'error': 'Django not available'}

# 便利函數導出
__all__ = [
    # 可用性標誌
    'RVT_ANALYTICS_AVAILABLE',
    'MESSAGE_FEEDBACK_AVAILABLE',
    'QUESTION_CLASSIFIER_AVAILABLE',
    'SATISFACTION_ANALYZER_AVAILABLE',
    'STATISTICS_MANAGER_AVAILABLE',
    'API_HANDLERS_AVAILABLE',
    
    # 主要功能函數
    'record_message_feedback',
    'classify_question', 
    'analyze_user_satisfaction',
    'get_rvt_analytics_stats',
    'handle_feedback_api',
    'handle_analytics_api',
    
    # 類別導出 (如果可用)
    'MessageFeedbackHandler',
    'QuestionClassifier',
    'SatisfactionAnalyzer',
    'StatisticsManager',
    'RVTAnalyticsAPIHandler'
]

# 版本檢查和兼容性信息
def get_library_info():
    """獲取 RVT Analytics Library 資訊"""
    return {
        'version': __version__,
        'available': RVT_ANALYTICS_AVAILABLE,
        'components': {
            'message_feedback': MESSAGE_FEEDBACK_AVAILABLE,
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
if RVT_ANALYTICS_AVAILABLE:
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"RVT Analytics Library v{__version__} 初始化完成")
    logger.info(f"可用組件: {sum(1 for k, v in get_library_info()['components'].items() if v)}/5")
else:
    print(f"RVT Analytics Library v{__version__} - Django 不可用，使用備用模式")