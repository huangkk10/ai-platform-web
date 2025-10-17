# Frontend-Backend Integration Guide

## 🔗 概述

本文件詳細說明 AI Platform 前後端整合的架構、流程與最佳實踐，確保 React 前端與 Django 後端的無縫協作。

## 🏗️ 系統架構

### 整體架構圖
```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│   瀏覽器客戶端    │    │    Nginx     │    │  React Frontend │    │   Django     │
│                 │◄──►│  Port 80/443 │◄──►│   Port 3000     │◄──►│  Backend     │
│   User Interface│    │ Reverse Proxy│    │  Development    │    │  Port 8000   │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────┘
                                                                           │
                                                                           ▼
                                                                   ┌──────────────┐
                                                                   │ PostgreSQL   │
                                                                   │   Port 5432  │
                                                                   └──────────────┘
```

### 容器網路架構
```
Docker Network: custom_network
├── ai-nginx (Nginx Proxy)
├── ai-react (React Dev Server)  
├── ai-django (Django API)
└── postgres_db (PostgreSQL)
```

## 📡 API 通信協定

### HTTP 請求流程
1. **用戶操作** → React 組件觸發 API 調用
2. **前端請求** → Axios 發送 HTTP 請求到相對路徑
3. **代理轉發** → Nginx 根據路由規則轉發請求
4. **後端處理** → Django 處理請求並操作資料庫
5. **回應傳遞** → 資料經由相同路徑回傳到前端
6. **界面更新** → React 更新 UI 顯示結果

### API 端點規範
```javascript
// 基礎 API 結構
const API_ENDPOINTS = {
  // 認證相關
  auth: {
    login: '/api/auth/login/',
    logout: '/api/auth/logout/',
    refresh: '/api/auth/refresh/',
  },
  
  // 用戶管理
  users: {
    list: '/api/users/',
    detail: '/api/users/{id}/',
    profile: '/api/profiles/me/',
  },
  
  // 專案管理
  projects: {
    list: '/api/projects/',
    detail: '/api/projects/{id}/',
    addMember: '/api/projects/{id}/add-member/',
    removeMember: '/api/projects/{id}/remove-member/',
  },
  
  // 任務管理
  tasks: {
    list: '/api/tasks/',
    detail: '/api/tasks/{id}/',
    assign: '/api/tasks/{id}/assign/',
    changeStatus: '/api/tasks/{id}/change-status/',
  }
};
```

## 🔄 資料流範例

### 1. 用戶登入流程
```javascript
// Frontend: 登入請求
const loginUser = async (credentials) => {
  try {
    const response = await axios.post('/api/auth/login/', credentials);
    const { token, user } = response.data;
    
    // 儲存 token
    localStorage.setItem('authToken', token);
    
    // 設定後續請求的認證標頭
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
    
    return { success: true, user };
  } catch (error) {
    return { success: false, error: error.response.data };
  }
};
```

```python
# Backend: 登入視圖
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                          context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'token': token.key,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
            }
        })
```

### 2. 專案建立流程
```javascript
// Frontend: 建立專案
const createProject = async (projectData) => {
  try {
    const response = await axios.post('/api/projects/', projectData);
    return { success: true, project: response.data };
  } catch (error) {
    return { 
      success: false, 
      errors: error.response.data 
    };
  }
};

// React 組件中使用
const ProjectForm = () => {
  const [formData, setFormData] = useState({
    name: '',
    description: ''
  });
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    const result = await createProject(formData);
    
    if (result.success) {
      // 更新項目列表
      setProjects(prev => [...prev, result.project]);
      // 清空表單
      setFormData({ name: '', description: '' });
    } else {
      // 顯示錯誤訊息
      setErrors(result.errors);
    }
  };
  
  // ... JSX 返回
};
```

```python
# Backend: 專案建立視圖
class ProjectViewSet(viewsets.ModelViewSet):
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        # 自動設定專案擁有者為當前用戶
        serializer.save(owner=self.request.user)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # 執行建立
        self.perform_create(serializer)
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            serializer.data, 
            status=status.HTTP_201_CREATED, 
            headers=headers
        )
```

## 🔒 認證與授權整合

### Token 認證流程
```javascript
// Frontend: 認證攔截器
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 回應攔截器處理認證失效
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token 過期，清除本地儲存並重定向到登入頁
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

### 權限檢查機制
```javascript
// Frontend: 權限檢查 Hook
const usePermissions = () => {
  const [user, setUser] = useState(null);
  
  const hasPermission = (permission) => {
    if (!user) return false;
    return user.permissions?.includes(permission) || user.is_staff;
  };
  
  const canEditProject = (project) => {
    if (!user) return false;
    return project.owner.id === user.id || user.is_staff;
  };
  
  return { user, hasPermission, canEditProject };
};

// 組件中使用權限檢查
const ProjectCard = ({ project }) => {
  const { canEditProject } = usePermissions();
  
  return (
    <div className="project-card">
      <h3>{project.name}</h3>
      <p>{project.description}</p>
      
      {canEditProject(project) && (
        <div className="project-actions">
          <button onClick={() => editProject(project.id)}>編輯</button>
          <button onClick={() => deleteProject(project.id)}>刪除</button>
        </div>
      )}
    </div>
  );
};
```

## 🌐 CORS 與代理設定

### Nginx 代理配置
```nginx
# nginx/nginx.conf
upstream react_frontend {
    server react:3000;
}

upstream django_backend {
    server django:8000;
}

server {
    listen 80;
    
    # API 請求轉發到 Django
    location /api/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Django Admin 轉發
    location /admin/ {
        proxy_pass http://django_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # 前端應用轉發到 React
    location / {
        proxy_pass http://react_frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket 支援 (React Hot Reload)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Django CORS 設定
```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://10.10.173.12",  # 外部訪問 IP
]

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
```

## 📊 錯誤處理與狀態管理

### 統一錯誤處理
```javascript
// Frontend: 錯誤處理工具
class APIError extends Error {
  constructor(message, status, details) {
    super(message);
    this.status = status;
    this.details = details;
  }
}

const handleAPIError = (error) => {
  if (error.response) {
    // 服務器回應錯誤
    const { status, data } = error.response;
    
    switch (status) {
      case 400:
        return new APIError('請求參數錯誤', status, data);
      case 401:
        return new APIError('身份驗證失敗', status, data);
      case 403:
        return new APIError('權限不足', status, data);
      case 404:
        return new APIError('資源不存在', status, data);
      case 500:
        return new APIError('服務器內部錯誤', status, data);
      default:
        return new APIError('未知錯誤', status, data);
    }
  } else if (error.request) {
    // 網路錯誤
    return new APIError('網路連接失敗', 0, null);
  } else {
    // 其他錯誤
    return new APIError('請求設定錯誤', -1, error.message);
  }
};
```

### 狀態管理範例
```javascript
// Frontend: 全域狀態管理
import React, { createContext, useContext, useReducer } from 'react';

const AppContext = createContext();

const initialState = {
  user: null,
  projects: [],
  tasks: [],
  loading: false,
  error: null,
};

const appReducer = (state, action) => {
  switch (action.type) {
    case 'SET_USER':
      return { ...state, user: action.payload };
    
    case 'SET_PROJECTS':
      return { ...state, projects: action.payload };
    
    case 'ADD_PROJECT':
      return { 
        ...state, 
        projects: [...state.projects, action.payload] 
      };
    
    case 'UPDATE_PROJECT':
      return {
        ...state,
        projects: state.projects.map(p => 
          p.id === action.payload.id ? action.payload : p
        )
      };
    
    case 'SET_LOADING':
      return { ...state, loading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    
    default:
      return state;
  }
};

export const AppProvider = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);
  
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};
```

## 🔄 實時通信 (可選)

### WebSocket 整合
```javascript
// Frontend: WebSocket 連接
class WebSocketService {
  constructor() {
    this.ws = null;
    this.reconnectInterval = 5000;
    this.maxReconnectAttempts = 5;
    this.reconnectAttempts = 0;
  }
  
  connect(token) {
    const wsUrl = `ws://localhost:8000/ws/?token=${token}`;
    this.ws = new WebSocket(wsUrl);
    
    this.ws.onopen = () => {
      console.log('WebSocket 已連接');
      this.reconnectAttempts = 0;
    };
    
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };
    
    this.ws.onclose = () => {
      console.log('WebSocket 已斷開');
      this.reconnect();
    };
  }
  
  handleMessage(data) {
    switch (data.type) {
      case 'task_update':
        // 處理任務更新
        break;
      case 'project_notification':
        // 處理專案通知
        break;
    }
  }
  
  reconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      setTimeout(() => {
        this.reconnectAttempts++;
        this.connect();
      }, this.reconnectInterval);
    }
  }
}
```

## 📈 性能優化

### 前端優化策略
```javascript
// 1. API 請求去重
const requestCache = new Map();

const cacheAPI = (url, config = {}) => {
  const key = JSON.stringify({ url, ...config });
  
  if (requestCache.has(key)) {
    return requestCache.get(key);
  }
  
  const promise = axios.get(url, config);
  requestCache.set(key, promise);
  
  // 清除過期快取
  setTimeout(() => {
    requestCache.delete(key);
  }, 30000); // 30秒後清除
  
  return promise;
};

// 2. 分頁載入
const usePagination = (apiEndpoint) => {
  const [data, setData] = useState([]);
  const [hasMore, setHasMore] = useState(true);
  const [page, setPage] = useState(1);
  
  const loadMore = async () => {
    try {
      const response = await axios.get(`${apiEndpoint}?page=${page}`);
      const newData = response.data.results;
      
      setData(prev => [...prev, ...newData]);
      setHasMore(!!response.data.next);
      setPage(prev => prev + 1);
    } catch (error) {
      console.error('載入失敗:', error);
    }
  };
  
  return { data, hasMore, loadMore };
};
```

### 後端優化策略
```python
# Django 優化
from django.core.cache import cache
from django.views.decorators.cache import cache_page

# 1. 查詢優化
class ProjectViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return Project.objects.select_related('owner').prefetch_related(
            'members', 'tasks'
        ).filter(
            Q(owner=self.request.user) | Q(members=self.request.user)
        ).distinct()

# 2. 快取機制
@cache_page(60 * 15)  # 快取 15 分鐘
def get_project_stats(request):
    stats = cache.get('project_stats')
    if not stats:
        stats = {
            'total_projects': Project.objects.count(),
            'active_projects': Project.objects.filter(status='active').count(),
            'total_tasks': Task.objects.count(),
        }
        cache.set('project_stats', stats, 60 * 15)
    
    return JsonResponse(stats)

# 3. 分頁最佳化
class CustomPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
```

## 🛠️ 開發與除錯工具

### 前端除錯
```javascript
// API 除錯工具
if (process.env.NODE_ENV === 'development') {
  axios.interceptors.request.use(request => {
    console.log('🚀 API Request:', request);
    return request;
  });
  
  axios.interceptors.response.use(
    response => {
      console.log('✅ API Response:', response);
      return response;
    },
    error => {
      console.error('❌ API Error:', error);
      return Promise.reject(error);
    }
  );
}
```

### 後端除錯
```python
# Django 日誌設定
import logging

logger = logging.getLogger(__name__)

class ProjectViewSet(viewsets.ModelViewSet):
    def create(self, request, *args, **kwargs):
        logger.info(f'Creating project: {request.data}')
        
        try:
            response = super().create(request, *args, **kwargs)
            logger.info(f'Project created successfully: {response.data}')
            return response
        except Exception as e:
            logger.error(f'Project creation failed: {str(e)}')
            raise
```

## 📚 相關文件

- [Frontend Development Guide](./frontend-development.md)
- [Backend Development Guide](./backend-development.md)
- [API Documentation](./api-documentation.md)
- [Security Best Practices](./security-guide.md)
- [Deployment Guide](./deployment-guide.md)

---

**建立時間**: 2025-09-08  
**最後更新**: 2025-09-08  
**維護者**: AI Platform Team