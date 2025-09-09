# Frontend Development Guide (React)

## 🚀 概述

AI Platform 前端使用 React 18 建構，提供現代化的 Web 界面，與 Django 後端 API 完全整合。

## 📁 專案結構

```
frontend/
├── src/
│   ├── App.js          # 主要應用程式組件
│   ├── App.css         # 主要樣式檔案
│   ├── index.js        # 應用程式入口點
│   └── index.css       # 全域樣式
├── public/
│   ├── index.html      # HTML 模板
│   └── favicon.ico     # 網站圖示
├── package.json        # 套件依賴管理
└── Dockerfile          # 容器建構檔案
```

## 🔧 技術架構

### 核心技術
- **React 18.2.0**: 前端框架
- **Axios 1.4.0**: HTTP 客戶端
- **React Router DOM 6.11.0**: 路由管理
- **React Scripts 5.0.1**: 建構工具

### 開發工具
- **Docker**: 容器化部署
- **Nginx**: 反向代理
- **Hot Reload**: 即時程式碼更新

## 🌐 API 整合

### API 基礎設定
前端透過 Nginx 反向代理與 Django API 通信：

```javascript
// 相對路徑調用 API (推薦)
axios.get('/api/users/')
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

### 環境變數配置
```bash
# 在 docker-compose.yml 中設定
REACT_APP_API_URL=http://localhost:8000
CHOKIDAR_USEPOLLING=true  # Docker 環境熱重載
```

## 📊 組件架構

### 主要組件 (App.js)
```javascript
import React, { useState, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [apiStatus, setApiStatus] = useState('Loading...');
  const [apiData, setApiData] = useState(null);

  useEffect(() => {
    // 測試 API 連接
    const testAPI = async () => {
      try {
        const response = await axios.get('/api/');
        setApiStatus('Connected');
        setApiData(response.data);
      } catch (error) {
        // 處理錯誤狀態
        handleApiError(error);
      }
    };
    
    testAPI();
  }, []);

  return (
    <div className="App">
      {/* 組件內容 */}
    </div>
  );
}
```

### 錯誤處理策略
```javascript
const handleApiError = (error) => {
  if (error.response?.status === 403) {
    setApiStatus('API Available (Authentication Required)');
  } else if (error.response?.status === 401) {
    setApiStatus('API Available (Unauthorized)');
  } else {
    setApiStatus('Connection Failed');
  }
};
```

## 🎨 樣式系統

### CSS 架構
```css
/* App.css - 主要樣式 */
.App {
  text-align: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  color: white;
}

.status-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 20px;
  margin: 20px auto;
  max-width: 800px;
}
```

### 響應式設計
- 支援桌面、平板、手機
- CSS Grid 和 Flexbox 佈局
- 流暢的動畫效果

## 🔄 開發工作流程

### 1. 本地開發
```bash
# 進入容器
docker exec -it ai-react bash

# 安裝新套件
npm install package-name

# 檢查日誌
docker logs ai-react --follow
```

### 2. 程式碼結構建議
```
src/
├── components/         # 可重用組件
│   ├── Header.js
│   ├── StatusCard.js
│   └── ServiceLink.js
├── pages/             # 頁面組件
│   ├── Dashboard.js
│   └── Settings.js
├── services/          # API 服務
│   └── apiService.js
├── hooks/             # 自定義 Hook
│   └── useApi.js
└── utils/             # 工具函數
    └── helpers.js
```

### 3. API 服務封裝
```javascript
// services/apiService.js
import axios from 'axios';

const API_BASE = '/api';

export const apiService = {
  // 用戶相關
  getUsers: () => axios.get(`${API_BASE}/users/`),
  createUser: (data) => axios.post(`${API_BASE}/users/`, data),
  
  // 專案相關
  getProjects: () => axios.get(`${API_BASE}/projects/`),
  createProject: (data) => axios.post(`${API_BASE}/projects/`, data),
};
```

## 🔒 認證與權限

### Token 管理
```javascript
// 設定 axios 預設 header
axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;

// 或在請求中單獨設定
axios.get('/api/users/', {
  headers: { Authorization: `Bearer ${token}` }
});
```

### 登入狀態管理
```javascript
const [isAuthenticated, setIsAuthenticated] = useState(false);
const [user, setUser] = useState(null);

// 檢查登入狀態
useEffect(() => {
  const token = localStorage.getItem('token');
  if (token) {
    // 驗證 token 並設定用戶狀態
    verifyToken(token);
  }
}, []);
```

## 📦 建構與部署

### 開發環境
```bash
# 啟動開發服務器
docker compose up react

# 檢查容器狀態
docker compose ps
```

### 生產環境建構
```bash
# 建構生產版本
npm run build

# 建構 Docker 映像
docker compose build react
```

### 性能優化
- **Code Splitting**: 動態載入組件
- **Lazy Loading**: 延遲載入資源
- **Memoization**: 避免不必要的重新渲染

```javascript
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./pages/Dashboard'));

function App() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <Dashboard />
    </Suspense>
  );
}
```

## 🛠️ 除錯與測試

### 常見問題排解
1. **API 連接失敗**
   - 檢查 Nginx 配置
   - 確認 Django 服務狀態
   - 驗證 CORS 設定

2. **熱重載不工作**
   - 確認 `CHOKIDAR_USEPOLLING=true`
   - 檢查 volume 掛載

3. **套件安裝失敗**
   - 清除 node_modules volume
   - 重新建構容器

### 開發工具
```javascript
// React Developer Tools
// Redux DevTools (如使用 Redux)
// 瀏覽器開發者工具

// 日誌除錯
console.log('API Response:', response.data);
console.error('API Error:', error);
```

## 📊 監控與日誌

### 性能監控
```javascript
// 效能測量
const startTime = performance.now();
// ... API 調用 ...
const endTime = performance.now();
console.log(`API 回應時間: ${endTime - startTime}ms`);
```

### 錯誤追蹤
```javascript
window.addEventListener('error', (event) => {
  console.error('全域錯誤:', event.error);
});

// API 錯誤統一處理
axios.interceptors.response.use(
  response => response,
  error => {
    console.error('API 錯誤:', error);
    return Promise.reject(error);
  }
);
```

## 🔮 後續擴展建議

1. **狀態管理**: 考慮引入 Redux 或 Zustand
2. **UI 框架**: 整合 Material-UI 或 Ant Design
3. **測試框架**: 添加 Jest 和 React Testing Library
4. **PWA 支援**: 實現離線功能
5. **國際化**: 支援多語言介面

## 📚 相關文件

- [Backend Development Guide](./backend-development.md)
- [API Integration Guide](./api-integration.md)
- [Docker Deployment Guide](./docker-deployment.md)
- [Security Best Practices](./security-guide.md)

---

**建立時間**: 2025-09-08  
**最後更新**: 2025-09-08  
**維護者**: AI Platform Team