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
    
    # Dify 外部知識 API - 同時支援有斜槓和無斜槓的版本
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
    # Dify 自動附加 /retrieval 的基礎路由
    path('dify/knowledge/', views.dify_knowledge_search, name='dify_knowledge_auto_retrieval'),
    # 相容舊路徑
    path('dify/knowledge/search/', views.dify_knowledge_search, name='dify_knowledge_search_legacy'),
    path('dify/knowledge/search/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search_official'),
    
    # Dify Know Issue 外部知識庫 API
    path('dify/know-issue/retrieval', views.dify_know_issue_search, name='dify_know_issue_search_no_slash'),
    path('dify/know-issue/retrieval/', views.dify_know_issue_search, name='dify_know_issue_search'),
    # Dify 自動附加 /retrieval 的路由 (支援有斜槓和無斜槓)
    path('dify/know-issue/', views.dify_know_issue_search, name='dify_know_issue_auto_retrieval_slash'),
    path('dify/know-issue', views.dify_know_issue_search, name='dify_know_issue_auto_retrieval_no_slash'),
]