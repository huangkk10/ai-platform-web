"""
API Views 統一導出接口
========================================

本模組提供統一的 views 導出接口，保持向後兼容性。

重構說明：
- 原有的 views.py 已拆分為：
  - dify_knowledge_views.py: Dify 外部知識庫 API
  - auth_views.py: 用戶認證相關 API ✅ 新增
  - legacy_views.py: 其他所有 API 和 ViewSets
- 通過此 __init__.py 統一導出，確保現有代碼無需修改
- 依賴注入模式消除了循環依賴風險

使用方式（完全向後兼容）：
    # 方式 1：傳統導入（仍然可用）
    from api import views
    views.dify_knowledge_search(request)
    views.user_login_api(request)
    views.UserViewSet
    
    # 方式 2：直接導入（推薦）
    from api.views import dify_knowledge_search, user_login_api, UserViewSet
    
    # 方式 3：從子模組導入（最明確）
    from api.views.dify_knowledge_views import dify_knowledge_search
    from api.views.auth_views import user_login_api
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


# ============= 認證 API 導出 =============

from .auth_views import (
    user_login_api,
    user_register,
    user_logout,
    change_password,
    user_info,
)


# ============= Dify Chat API 導出 =============

from .dify_chat_views import (
    # Chat APIs
    dify_chat,
    dify_chat_with_file,
    dify_ocr_chat,
    rvt_guide_chat,
    protocol_guide_chat,
    
    # Chat 使用統計 API
    chat_usage_statistics,
    record_chat_usage,
)


# ============= Dify Config API 導出 =============

from .dify_config_views import (
    dify_config_info,
    rvt_guide_config,
    protocol_guide_config,
)


# ============= Analytics API 導出 =============

from .analytics_views import (
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


# ============= ViewSets 導出 =============

from .viewsets import (
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
)


# ============= System Monitoring API 導出 =============

from .system_monitoring_views import (
    system_logs,
    simple_system_status,
    basic_system_status,
)


# ============= 清理完成 =============
# legacy_views.py 已被完全拆分為以下模組：
# - dify_knowledge_views.py: Dify 知識庫 API (10 個函數)
# - auth_views.py: 用戶認證 API (5 個函數)
# - dify_chat_views.py: Dify 聊天 API (7 個函數)
# - dify_config_views.py: Dify 配置 API (3 個函數)
# - analytics_views.py: 分析統計 API (14 個函數)
# - viewsets.py: 所有 ViewSet 類別 (11 個類別)
# - system_monitoring_views.py: 系統監控 API (3 個函數)
# 總計: 53 個 API 端點，完全模組化


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
