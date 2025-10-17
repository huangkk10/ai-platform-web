"""
API Views 統一導出接口
========================================

本模組提供統一的 views 導出接口，保持向後兼容性。

重構說明：
- 原有的 views.py 已拆分為：
  - dify_knowledge_views.py: Dify 外部知識庫 API
  - legacy_views.py: 其他所有 API 和 ViewSets
- 通過此 __init__.py 統一導出，確保現有代碼無需修改
- 依賴注入模式消除了循環依賴風險

使用方式（完全向後兼容）：
    # 方式 1：傳統導入（仍然可用）
    from api import views
    views.dify_knowledge_search(request)
    views.UserViewSet
    
    # 方式 2：直接導入（推薦）
    from api.views import dify_knowledge_search, UserViewSet
    
    # 方式 3：從子模組導入（最明確）
    from api.views.dify_knowledge_views import dify_knowledge_search
    from api.views.legacy_views import UserViewSet

Created: 2025-10-17
Author: AI Platform Team
"""

# ============= Dify 知識庫 API 導出 =============

from .dify_knowledge_views import (
    # 搜索輔助函數（向後兼容）
    search_know_issue_knowledge,
    search_rvt_guide_knowledge,
    search_protocol_guide_knowledge,
    search_ocr_storage_benchmark,
    
    # Dify 外部知識庫 API 端點
    dify_knowledge_search,           # 🌟 統一入口（推薦使用）
    dify_know_issue_search,          # 舊版 API（向後兼容）
    dify_ocr_storage_benchmark_search,  # 舊版 API（向後兼容）
    dify_rvt_guide_search,           # 舊版 API（向後兼容）
    dify_protocol_guide_search,      # 舊版 API（向後兼容）
    
    # 依賴注入工具（高級用法）
    get_search_functions_registry,
    create_dify_search_handler,
)


# ============= 其他所有 Views 導出 =============

from .legacy_views import (
    # 認證相關 API
    user_login_api,
    user_register,
    user_logout,
    user_info,
    change_password,
    
    # ViewSet 類別
    UserViewSet,
    UserProfileViewSet,
    ProjectViewSet,
    TaskViewSet,
    KnowIssueViewSet,
    TestClassViewSet,
    OCRTestClassViewSet,
    OCRStorageBenchmarkViewSet,
    RVTGuideViewSet,
    ProtocolGuideViewSet,
    ContentImageViewSet,
    
    # Dify Chat API
    dify_chat,
    dify_chat_with_file,
    dify_config_info,
    dify_ocr_chat,
    
    # RVT Guide Chat API
    rvt_guide_chat,
    rvt_guide_config,
    
    # Protocol Guide Chat API
    protocol_guide_chat,
    protocol_guide_config,
    
    # Chat 使用統計 API
    chat_usage_statistics,
    record_chat_usage,
    
    # 系統監控 API
    simple_system_status,
    basic_system_status,
    system_logs,
    
    # 對話管理 API
    conversation_list,
    conversation_detail,
    record_conversation,
    update_conversation_session,
    conversation_stats,
    
    # RVT Analytics API
    rvt_analytics_feedback,
    rvt_analytics_overview,
    rvt_analytics_questions,
    rvt_analytics_satisfaction,
    
    # 聊天向量化和聚類 API
    chat_vector_search,
    chat_clustering_analysis,
    chat_clustering_stats,
    vectorize_chat_message,
    intelligent_question_classify,
)


# ============= __all__ 定義（可選但推薦） =============

__all__ = [
    # Dify 知識庫 API
    'search_know_issue_knowledge',
    'search_rvt_guide_knowledge',
    'search_protocol_guide_knowledge',
    'search_ocr_storage_benchmark',
    'dify_knowledge_search',
    'dify_know_issue_search',
    'dify_ocr_storage_benchmark_search',
    'dify_rvt_guide_search',
    'dify_protocol_guide_search',
    'get_search_functions_registry',
    'create_dify_search_handler',
    
    # 認證 API
    'user_login_api',
    'user_register',
    'user_logout',
    'user_info',
    'change_password',
    
    # ViewSets
    'UserViewSet',
    'UserProfileViewSet',
    'ProjectViewSet',
    'TaskViewSet',
    'KnowIssueViewSet',
    'TestClassViewSet',
    'OCRTestClassViewSet',
    'OCRStorageBenchmarkViewSet',
    'RVTGuideViewSet',
    'ProtocolGuideViewSet',
    'ContentImageViewSet',
    
    # Chat APIs
    'dify_chat',
    'dify_chat_with_file',
    'dify_config_info',
    'dify_ocr_chat',
    'rvt_guide_chat',
    'rvt_guide_config',
    'protocol_guide_chat',
    'protocol_guide_config',
    
    # Statistics
    'chat_usage_statistics',
    'record_chat_usage',
    
    # System Monitoring
    'simple_system_status',
    'basic_system_status',
    'system_logs',
    
    # Conversation Management
    'conversation_list',
    'conversation_detail',
    'record_conversation',
    'update_conversation_session',
    'conversation_stats',
    
    # RVT Analytics
    'rvt_analytics_feedback',
    'rvt_analytics_overview',
    'rvt_analytics_questions',
    'rvt_analytics_satisfaction',
    
    # Chat Vector & Clustering
    'chat_vector_search',
    'chat_clustering_analysis',
    'chat_clustering_stats',
    'vectorize_chat_message',
    'intelligent_question_classify',
]


# ============= 版本資訊 =============

__version__ = '2.0.0'
__refactor_date__ = '2025-10-17'
__description__ = 'Modular views with dependency injection pattern'
