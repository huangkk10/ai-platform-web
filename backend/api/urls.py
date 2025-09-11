from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)
router.register(r'employees', views.EmployeeViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
    # Dify 外部知識 API - 同時支援有斜槓和無斜槓的版本
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
    # 相容舊路徑
    path('dify/knowledge/search/', views.dify_knowledge_search, name='dify_knowledge_search_legacy'),
    path('dify/knowledge/search/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search_official'),
]