# Backend Development Guide (Django)

## 🚀 概述

AI Platform 後端使用 Django 4.2 + Django REST Framework 建構，提供 RESTful API 服務，與 PostgreSQL 資料庫整合。

## 📁 專案結構

```
backend/
├── ai_platform/           # 主專案設定
│   ├── __init__.py
│   ├── settings.py        # 主要設定檔案
│   ├── urls.py           # 主要 URL 路由
│   ├── wsgi.py           # WSGI 應用程式
│   └── asgi.py           # ASGI 應用程式 (異步)
├── api/                  # API 應用程式
│   ├── models.py         # 資料模型
│   ├── serializers.py    # 序列化器
│   ├── views.py          # 視圖邏輯
│   ├── urls.py           # API 路由
│   └── apps.py           # 應用程式設定
├── manage.py             # Django 管理工具
├── requirements.txt      # Python 依賴套件
└── Dockerfile           # 容器建構檔案
```

## 🔧 技術架構

### 核心技術
- **Django 4.2**: Web 框架
- **Django REST Framework 3.14**: API 框架
- **PostgreSQL 15**: 主要資料庫
- **psycopg2-binary**: PostgreSQL 驅動
- **python-decouple**: 環境變數管理

### 中介軟體
- **CORS Headers**: 跨域請求支援
- **WhiteNoise**: 靜態檔案服務
- **Authentication**: Token/Session 認證

## 🗄️ 資料庫設定

### PostgreSQL 連接
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'NAME': config('DB_NAME', default='ai_platform'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres123'),
    }
}
```

### 資料模型範例
```python
# api/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"

class Project(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    members = models.ManyToManyField(User, related_name='projects', blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title
```

## 📡 API 設計

### 序列化器 (Serializers)
```python
# api/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = ['id', 'user', 'bio', 'location', 'birth_date', 'avatar', 'created_at', 'updated_at']

class ProjectSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    members = UserSerializer(many=True, read_only=True)
    tasks_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'owner', 'members', 'status', 'tasks_count', 'created_at', 'updated_at']
    
    def get_tasks_count(self, obj):
        return obj.tasks.count()

class TaskSerializer(serializers.ModelSerializer):
    project = ProjectSerializer(read_only=True)
    assigned_to = UserSerializer(read_only=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'project', 'assigned_to', 'priority', 'completed', 'due_date', 'created_at', 'updated_at']
```

### 視圖 (Views)
```python
# api/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import UserProfile, Project, Task
from .serializers import UserSerializer, UserProfileSerializer, ProjectSerializer, TaskSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只返回當前用戶可以看到的用戶
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class UserProfileViewSet(viewsets.ModelViewSet):
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @action(detail=False, methods=['get', 'put'])
    def me(self, request):
        """獲取或更新當前用戶的個人資料"""
        try:
            profile = UserProfile.objects.get(user=request.user)
        except UserProfile.DoesNotExist:
            profile = UserProfile.objects.create(user=request.user)
        
        if request.method == 'GET':
            serializer = self.get_serializer(profile)
            return Response(serializer.data)
        elif request.method == 'PUT':
            serializer = self.get_serializer(profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只返回用戶擁有或參與的專案
        return Project.objects.filter(
            models.Q(owner=self.request.user) | 
            models.Q(members=self.request.user)
        ).distinct()
    
    def perform_create(self, serializer):
        # 設定專案擁有者為當前用戶
        serializer.save(owner=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_member(self, request, pk=None):
        """新增專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.add(user)
            return Response({'message': f'User {user.username} added to project'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def remove_member(self, request, pk=None):
        """移除專案成員"""
        project = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            project.members.remove(user)
            return Response({'message': f'User {user.username} removed from project'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # 只返回用戶相關的任務
        return Task.objects.filter(
            models.Q(project__owner=self.request.user) |
            models.Q(project__members=self.request.user) |
            models.Q(assigned_to=self.request.user)
        ).distinct()
    
    @action(detail=True, methods=['post'])
    def assign_task(self, request, pk=None):
        """指派任務給用戶"""
        task = self.get_object()
        user_id = request.data.get('user_id')
        
        try:
            user = User.objects.get(id=user_id)
            task.assigned_to = user
            task.save()
            return Response({'message': f'Task assigned to {user.username}'})
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """變更任務完成狀態"""
        task = self.get_object()
        completed = request.data.get('completed', False)
        task.completed = completed
        task.save()
        
        status_text = 'completed' if completed else 'reopened'
        return Response({'message': f'Task {status_text}'})
```

### URL 路由
```python
# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'profiles', views.UserProfileViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'tasks', views.TaskViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),  # DRF 認證 URLs
]
```

```python
# ai_platform/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(['GET'])
def api_root(request):
    return Response({
        'message': 'Welcome to AI Platform API',
        'version': '1.0.0',
        'endpoints': {
            'users': '/api/users/',
            'profiles': '/api/profiles/',
            'projects': '/api/projects/',
            'tasks': '/api/tasks/',
            'admin': '/admin/',
        }
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]

# 靜態檔案服務 (開發環境)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
```

## 🔒 認證與權限

### REST Framework 設定
```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
```

### Token 認證設定
```python
# 在 INSTALLED_APPS 中加入
INSTALLED_APPS = [
    # ...
    'rest_framework.authtoken',
]

# 建立 Token
from rest_framework.authtoken.models import Token
from django.contrib.auth.models import User

user = User.objects.get(username='your_username')
token, created = Token.objects.get_or_create(user=user)
print(f'Token: {token.key}')
```

### 自定義權限
```python
# api/permissions.py
from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """只有擁有者可以編輯，其他人只能讀取"""
    
    def has_object_permission(self, request, view, obj):
        # 讀取權限給所有請求
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 寫入權限只給擁有者
        return obj.owner == request.user

class IsProjectMember(permissions.BasePermission):
    """只有專案成員可以存取"""
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'project'):
            # 對於任務等與專案相關的物件
            project = obj.project
        else:
            # 對於專案本身
            project = obj
        
        return (project.owner == request.user or 
                request.user in project.members.all())
```

## 🔧 開發工具與指令

### 常用 Django 指令
```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 建立遷移檔案
python manage.py makemigrations

# 執行資料庫遷移
python manage.py migrate

# 建立超級用戶
python manage.py createsuperuser

# 收集靜態檔案
python manage.py collectstatic

# 啟動 Django shell
python manage.py shell

# 執行測試
python manage.py test
```

### 資料庫管理
```bash
# 重置資料庫
python manage.py flush

# 載入初始資料
python manage.py loaddata fixtures/initial_data.json

# 匯出資料
python manage.py dumpdata api --indent 2 > backup.json

# 檢查資料庫
python manage.py dbshell
```

## 📊 測試與除錯

### 單元測試
```python
# api/tests.py
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Project, Task

class ProjectAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        
    def test_create_project(self):
        data = {
            'name': 'Test Project',
            'description': 'A test project'
        }
        response = self.client.post('/api/projects/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)
        
    def test_get_projects(self):
        Project.objects.create(
            name='Test Project',
            description='A test project',
            owner=self.user
        )
        response = self.client.get('/api/projects/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
```

### 日誌設定
```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/app/logs/django.log',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'api': {
            'handlers': ['file', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 🚀 部署與優化

### 生產環境設定
```python
# settings/production.py
from .base import *

DEBUG = False
ALLOWED_HOSTS = ['your-domain.com', 'www.your-domain.com']

# 資料庫優化
DATABASES['default']['CONN_MAX_AGE'] = 60

# 快取設定
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}

# 安全性設定
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 效能優化
```python
# 查詢優化
from django.db import models

# 使用 select_related 減少查詢次數
projects = Project.objects.select_related('owner').all()

# 使用 prefetch_related 優化多對多關係
projects = Project.objects.prefetch_related('members', 'tasks').all()

# 資料庫索引
class Project(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    status = models.CharField(max_length=20, db_index=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['created_at']),
        ]
```

## 📚 相關文件

- [Frontend Development Guide](./frontend-development.md)
- [API Integration Guide](./api-integration.md)
- [Database Schema](./database-schema.md)
- [Security Best Practices](./security-guide.md)

---

**建立時間**: 2025-09-08  
**最後更新**: 2025-09-08  
**維護者**: AI Platform Team