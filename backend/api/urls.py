from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'employees', views.EmployeeViewSet)
router.register(r'know-issues', views.KnowIssueViewSet)

urlpatterns = [
    path('', include(router.urls)),
    
    # 用戶認證 API (放在 rest_framework.urls 之前)
    path('auth/login/', views.UserLoginView.as_view(), name='user_login'),
    path('auth/logout/', views.user_logout, name='user_logout'),
    path('auth/user/', views.user_info, name='user_info'),
    
    # Django REST framework 認證頁面（使用不同路徑）
    path('auth/drf/', include('rest_framework.urls')),
    
    # Dify 外部知識 API - 同時支援有斜槓和無斜槓的版本
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
    # 相容舊路徑
    path('dify/knowledge/search/', views.dify_knowledge_search, name='dify_knowledge_search_legacy'),
    path('dify/knowledge/search/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search_official'),
]