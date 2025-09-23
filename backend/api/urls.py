from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'dify-employees', views.DifyEmployeeViewSet)
router.register(r'know-issues', views.KnowIssueViewSet)
router.register(r'test-classes', views.TestClassViewSet)
router.register(r'ocr-test-classes', views.OCRTestClassViewSet)
router.register(r'ocr-storage-benchmarks', views.OCRStorageBenchmarkViewSet)
router.register(r'rvt-guides', views.RVTGuideViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # 用戶認證 API (放在 rest_framework.urls 之前)
    path('auth/login/', views.UserLoginView.as_view(), name='user_login'),
    path('auth/register/', views.user_register, name='user_register'),
    path('auth/logout/', views.user_logout, name='user_logout'),
    path('auth/user/', views.user_info, name='user_info'),
    path('auth/change-password/', views.change_password, name='change_password'),
    
    # Django REST framework 認證頁面（使用不同路徑）
    path('auth/drf/', include('rest_framework.urls')),
    
    # Dify 統一外部知識 API - 通過 knowledge_id 參數區分不同知識庫
    # 主要端點（Dify 會自動添加 /retrieval）
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
    
    # RVT Guide Chat API
    path('rvt-guide/chat/', views.rvt_guide_chat, name='rvt_guide_chat'),
    path('rvt-guide/config/', views.rvt_guide_config, name='rvt_guide_config'),
    
    # Chat Usage Statistics API
    path('chat/statistics/', views.chat_usage_statistics, name='chat_usage_statistics'),
    path('chat/record-usage/', views.record_chat_usage, name='record_chat_usage'),
    
    # 系統狀態監控 API
    path('system/status/', views.system_status, name='system_status'),
    path('system/simple-status/', views.simple_system_status, name='simple_system_status'),
    path('system/basic-status/', views.basic_system_status, name='basic_system_status'),
    path('system/logs/', views.system_logs, name='system_logs'),
]