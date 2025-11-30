from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'know-issues', views.KnowIssueViewSet)
router.register(r'test-classes', views.TestClassViewSet)
router.register(r'ocr-test-classes', views.OCRTestClassViewSet)
router.register(r'ocr-storage-benchmarks', views.OCRStorageBenchmarkViewSet)
router.register(r'rvt-guides', views.RVTGuideViewSet)
router.register(r'protocol-guides', views.ProtocolGuideViewSet)
router.register(r'protocol-assistant', views.ProtocolAssistantViewSet, basename='protocol-assistant')
router.register(r'content-images', views.ContentImageViewSet)
router.register(r'threshold-settings', views.SearchThresholdViewSet)
router.register(r'search-threshold-settings', views.SearchThresholdSettingViewSet, basename='search-threshold-setting')

# Benchmark Testing System (舊版 - Protocol Search Benchmark)
router.register(r"benchmark/test-cases", views.BenchmarkTestCaseViewSet, basename="benchmark-test-case")
router.register(r"benchmark/test-runs", views.BenchmarkTestRunViewSet, basename="benchmark-test-run")
router.register(r"benchmark/test-results", views.BenchmarkTestResultViewSet, basename="benchmark-test-result")
router.register(r"benchmark/versions", views.SearchAlgorithmVersionViewSet, basename="benchmark-version")

# Dify Benchmark System (新版 - Dify Config Benchmark)
router.register(r"dify-benchmark/versions", views.DifyConfigVersionViewSet, basename="dify-benchmark-version")
router.register(r"dify-benchmark/test-cases", views.DifyBenchmarkTestCaseViewSet, basename="dify-benchmark-test-case")
router.register(r"dify-benchmark/test-runs", views.DifyTestRunViewSet, basename="dify-benchmark-test-run")

# Unified Benchmark System (統一測試案例系統 - 整合 Protocol 和 VSA)
router.register(r"unified-benchmark/test-cases", views.UnifiedBenchmarkTestCaseViewSet, basename="unified-benchmark-test-case")

urlpatterns = [
    path('', include(router.urls)),
    
    # 用戶認證 API (放在 rest_framework.urls 之前) - 統一使用 function-based views
    path('auth/login/', views.user_login_api, name='user_login'),
    path('auth/register/', views.user_register, name='user_register'),
    path('auth/logout/', views.user_logout, name='user_logout'),
    path('auth/user/', views.user_info, name='user_info'),
    path('auth/change-password/', views.change_password, name='change_password'),
    
    # Django REST framework 認證頁面（使用不同路徑）
    path('auth/drf/', include('rest_framework.urls')),
    
    # Dify 外部知識庫 API - 分離不同應用的端點
    
    # Protocol RAG (Know Issue) 知識庫
    path('dify/protocol/knowledge/retrieval', views.dify_know_issue_search, name='dify_protocol_knowledge_no_slash'),
    path('dify/protocol/knowledge/retrieval/', views.dify_know_issue_search, name='dify_protocol_knowledge'),
    
    # AI OCR Storage Benchmark 知識庫
    path('dify/ocr/knowledge/retrieval', views.dify_ocr_storage_benchmark_search, name='dify_ocr_knowledge_no_slash'),
    path('dify/ocr/knowledge/retrieval/', views.dify_ocr_storage_benchmark_search, name='dify_ocr_knowledge'),
    
    # RVT Guide 知識庫
    path('dify/rvt/knowledge/retrieval', views.dify_rvt_guide_search, name='dify_rvt_knowledge_no_slash'),
    path('dify/rvt/knowledge/retrieval/', views.dify_rvt_guide_search, name='dify_rvt_knowledge'),
    
    # 通用知識庫端點（向後兼容，通過 knowledge_id 路由）
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
    path('dify/knowledge/', views.dify_knowledge_search, name='dify_knowledge_auto_retrieval'),
    path('dify/knowledge', views.dify_knowledge_search, name='dify_knowledge_base'),
    
    # 相容舊的特定知識庫端點（向後兼容）
    path('dify/know-issue/retrieval', views.dify_knowledge_search, name='dify_know_issue_compat_no_slash'),
    path('dify/know-issue/retrieval/', views.dify_knowledge_search, name='dify_know_issue_compat'),
    path('dify/rvt-guide/retrieval', views.dify_knowledge_search, name='dify_rvt_guide_compat_no_slash'),
    path('dify/rvt-guide/retrieval/', views.dify_knowledge_search, name='dify_rvt_guide_compat'),
    
    # Dify Chat API
    path('dify/chat/', views.dify_chat, name='dify_chat'),
    path('dify/chat-with-file/', views.dify_chat_with_file, name='dify_chat_with_file'),
    path('dify/config/', views.dify_config_info, name='dify_config_info'),
    
    # Dify Baseline 版本管理 API
    path('dify/versions/<int:version_id>/set_baseline/', views.set_baseline_version, name='set_baseline_version'),
    path('dify/versions/baseline/', views.get_baseline_version_info, name='get_baseline_version_info'),
    
    # Dify OCR Chat API - 專門用於 AI OCR 系統
    path('dify/ocr/chat/', views.dify_ocr_chat, name='dify_ocr_chat'),
    
    # OCR 圖片分析 API - 供 Assistant 檔案上傳功能使用
    path('ocr/analyze/', views.OCRAnalyzeView.as_view(), name='ocr_analyze'),
    
    # RVT Guide Chat API
    path('rvt-guide/chat/', views.rvt_guide_chat, name='rvt_guide_chat'),
    path('rvt-guide/config/', views.rvt_guide_config, name='rvt_guide_config'),
    
    # Protocol Guide API
    path('dify/protocol-guide/knowledge/retrieval', views.dify_protocol_guide_search, name='dify_protocol_guide_knowledge_no_slash'),
    path('dify/protocol-guide/knowledge/retrieval/', views.dify_protocol_guide_search, name='dify_protocol_guide_knowledge'),
    path('protocol-guide/chat/', views.protocol_guide_chat, name='protocol_guide_chat'),
    path('protocol-guide/config/', views.protocol_guide_config, name='protocol_guide_config'),
    
    # Chat Usage Statistics API
    path('chat/statistics/', views.chat_usage_statistics, name='chat_usage_statistics'),
    path('chat/record-usage/', views.record_chat_usage, name='record_chat_usage'),
    
    # 系統狀態監控 API
    path('system/simple-status/', views.simple_system_status, name='simple_system_status'),
    path('system/basic-status/', views.basic_system_status, name='basic_system_status'),
    path('system/logs/', views.system_logs, name='system_logs'),
    
    # 日誌查看器 API
    path('system/logs/list/', views.list_log_files, name='list_log_files'),
    path('system/logs/view/', views.view_log_file, name='view_log_file'),
    path('system/logs/download/', views.download_log_file, name='download_log_file'),
    path('system/logs/search/', views.search_log_file, name='search_log_file'),
    path('system/logs/stats/', views.log_file_stats, name='log_file_stats'),
    
    # 對話管理 API - Conversation Management
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/record/', views.record_conversation, name='record_conversation'),
    path('conversations/sessions/<str:session_id>/', views.update_conversation_session, name='update_conversation_session'),
    path('conversations/stats/', views.conversation_stats, name='conversation_stats'),
    
    # RVT Analytics API - RVT Assistant 分析功能
    path('rvt-analytics/feedback/', views.rvt_analytics_feedback, name='rvt_analytics_feedback'),
    path('rvt-analytics/overview/', views.rvt_analytics_overview, name='rvt_analytics_overview'),
    path('rvt-analytics/questions/', views.rvt_analytics_questions, name='rvt_analytics_questions'),
    path('rvt-analytics/satisfaction/', views.rvt_analytics_satisfaction, name='rvt_analytics_satisfaction'),
    path('rvt-analytics/question-history/', views.rvt_question_history, name='rvt_question_history'),
    
    # Protocol Analytics API - Protocol Assistant 分析功能
    path('protocol-analytics/overview/', views.protocol_analytics_overview, name='protocol_analytics_overview'),
    path('protocol-analytics/questions/', views.protocol_analytics_questions, name='protocol_analytics_questions'),
    path('protocol-analytics/satisfaction/', views.protocol_analytics_satisfaction, name='protocol_analytics_satisfaction'),
    path('protocol-analytics/trends/', views.protocol_analytics_trends, name='protocol_analytics_trends'),
    path('protocol-analytics/question-history/', views.protocol_question_history, name='protocol_question_history'),
    
    # 聊天向量化和聚類分析 API
    path('chat-vectors/search/', views.chat_vector_search, name='chat_vector_search'),
    path('chat-clustering/analysis/', views.chat_clustering_analysis, name='chat_clustering_analysis'),
    path('chat-clustering/stats/', views.chat_clustering_stats, name='chat_clustering_stats'),
    path('chat-vectors/vectorize/', views.vectorize_chat_message, name='vectorize_chat_message'),
    path('chat-classification/intelligent/', views.intelligent_question_classify, name='intelligent_question_classify'),
]