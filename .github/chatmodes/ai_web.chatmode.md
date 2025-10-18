`````chatmode
# Git Commit Type

請遵守下列 commit type（Conventional Commits 為基礎）：

- feat: 新增/修改功能 (feature)。
- fix: 修補 bug (bug fix)。
- docs: 文件 (documentation)。
- style: 格式 (不影響程式碼運行的變動 white-space, formatting, missing semi colons, etc)。
- refactor: 重構 (既不是新增功能，也不是修補 bug 的程式碼變動)。
- perf: 改善效能 (A code change that improves performance)。
- test: 增加測試 (when adding missing tests)。
- chore: 建構程序或輔助工具的變動 (maintain)。
- revert: 撤銷回覆先前的 commit 例如：revert: type(scope): subject (回覆版本：xxxx)。
- vert: 進版（版本相關變更）。

System prompt（AI 專用簡短提示）：

你是一個 commit message 建議工具，回傳 JSON 與 2 個可選的 commit messages，並遵守上面的 type 列表。格式：<type>(optional-scope): <subject>。subject 最多 72 字元；需要說明放 body；breaking change 在 footer 使用 `BREAKING CHANGE:`。不要包含任何敏感資訊或憑證。

# 🎨 UI 框架與開發偏好設定

## 🥇 首選 UI 框架：Ant Design of React

**強制性規範**：
1. **所有 React 前端開發都必須優先使用 Ant Design (antd) 作為 UI 組件庫**
2. **新功能開發時，優先選擇 Ant Design 的現成組件**
3. **統一設計風格，確保界面一致性**
4. **禁止混用其他 UI 框架（Bootstrap, Material-UI, Semantic UI 等）**

## 📦 核心組件優先順序

### 1. 資料展示組件
```javascript
// ✅ 優先使用：Table, List, Card, Descriptions, Statistic, Tag, Typography
import { Table, Card, Descriptions, Tag, Typography, List } from 'antd';
```

### 2. 表單組件
```javascript
// ✅ 優先使用：Form, Input, Select, DatePicker, Upload, Switch, Checkbox
import { Form, Input, Select, Button, DatePicker, Upload, Switch } from 'antd';
```

### 3. 導航與佈局組件
```javascript
// ✅ 優先使用：Menu, Breadcrumb, Steps, Pagination, Row, Col, Space
import { Menu, Breadcrumb, Steps, Pagination, Row, Col, Space } from 'antd';
```

### 4. 反饋組件
```javascript
// ✅ 優先使用：Modal, Drawer, notification, message, Popconfirm, Tooltip
import { Modal, Drawer, message, notification, Popconfirm, Tooltip } from 'antd';
```

### 5. 圖標系統
```javascript
// ✅ 統一使用 @ant-design/icons
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  FileTextOutlined, ToolOutlined, EyeOutlined
} from '@ant-design/icons';
```

## 🎯 開發指導原則

### AI 協助開發時的檢查清單
**AI 在建議前端代碼時必須確認**：
- [ ] 所有 UI 組件都來自 `antd`
- [ ] 使用 Ant Design 的設計規範和間距系統
- [ ] 響應式布局使用 `Row` 和 `Col`
- [ ] 表單使用 `Form` 組件和相應的 validation
- [ ] 狀態反饋使用 `message` 或 `notification`
- [ ] Icon 使用 `@ant-design/icons`
- [ ] 顏色和主題符合 Ant Design 規範
- [ ] 沒有引入其他 UI 框架組件

### 標準化模式
```javascript
// ✅ 標準 CRUD 頁面模式 (參考 RvtGuidePage.js)
import {
  Card, Table, Button, Space, Typography, Tag, message,
  Input, Select, Row, Col, Modal, Form, Tooltip
} from 'antd';
```

### 🚫 禁止的做法
```javascript
// ❌ 不要混用其他 UI 庫
import { Button } from 'react-bootstrap';  // 禁止
import { TextField } from '@mui/material';  // 禁止
import { Input } from 'semantic-ui-react';  // 禁止
```

## 📋 實際應用標準

### 當前專案最佳實踐範例：
- `RvtGuidePage.js` - 完整的資料管理頁面
- `KnowIssuePage.js` - 複雜表單和資料管理
- 所有新頁面都應參考這些標準實現

# 🎯 AI Assistant 標準範本架構（以 RVT Assistant 為範例）

## 📘 概述
**RVT Assistant 是專案中 AI Assistant 功能的標準範本**，未來所有新的 Assistant（如 Protocol Assistant、QA Assistant 等）都應該參考此架構模式進行開發。

## 🏗️ 標準 Assistant 架構組成

### 1️⃣ **前端架構（React）**

#### 📁 目錄結構標準
```
frontend/src/
├── pages/
│   ├── RvtAssistantChatPage.js      # 聊天介面主頁面
│   ├── RvtAssistantChatPage.css     # 專用樣式
│   ├── RVTAnalyticsPage.js          # 分析儀表板
│   └── RvtGuidePage/                # 知識庫管理頁面
│       └── index.js                 # 使用配置驅動架構
├── hooks/
│   ├── useRvtChat.js                # 聊天 API 通訊邏輯
│   ├── useRvtGuideData.js           # 知識庫資料管理
│   └── useRvtGuideList.js           # 知識庫列表操作
├── config/
│   └── knowledgeBaseConfig.js       # 知識庫配置（支援多 Assistant）
└── components/
    └── KnowledgeBase/               # 通用知識庫組件
        ├── KnowledgeBasePage.jsx    # 通用頁面組件
        └── createKnowledgeBaseColumns.js  # 通用欄位生成
```

#### 🎨 前端核心組件
```javascript
// 1. 聊天頁面（主要互動介面）
RvtAssistantChatPage.js
├── useRvtChat Hook         // API 通訊
├── useMessageStorage Hook  // 訊息持久化
├── useMessageFeedback Hook // 用戶反饋
└── MessageList Component   // 訊息列表展示

// 2. 知識庫管理頁面（配置驅動）
RvtGuidePage/index.js
├── knowledgeBaseConfigs['rvt-assistant']  // 配置物件
├── KnowledgeBasePage                       // 通用頁面
└── GuideDetailModal                        // 詳細資料彈窗

// 3. 分析儀表板（數據可視化）
RVTAnalyticsPage.js
├── 問題分類統計
├── 用戶滿意度分析
└── 趨勢分析圖表
```

#### ⚙️ 配置驅動模式（關鍵特性）
```javascript
// config/knowledgeBaseConfig.js
export const knowledgeBaseConfigs = {
  'rvt-assistant': {
    apiEndpoint: '/api/rvt-guides/',
    routes: { list, create, edit, preview },
    labels: { pageTitle, createButton, ... },
    permissions: { canDelete, canEdit, canView },
    // ... 完整配置
  },
  // 🚀 新增 Assistant 只需添加新配置
  'protocol-assistant': { /* 複製並修改 */ },
  'qa-assistant': { /* 複製並修改 */ }
};
```

### 2️⃣ **後端架構（Django）**

#### 📁 Library 模組結構標準
```
backend/library/
└── rvt_guide/                    # Assistant Library 根目錄
    ├── __init__.py               # 導出主要接口
    ├── viewset_manager.py        # ViewSet 管理器
    ├── api_handlers.py           # API 處理邏輯
    ├── fallback_handlers.py      # 降級處理
    ├── search_service.py         # 搜尋服務
    ├── vector_service.py         # 向量服務
    └── serializers/              # 序列化器
        ├── guide_serializer.py
        └── image_serializer.py
```

#### 📁 相關 Library 模組
```
backend/library/
├── rvt_guide/              # 知識庫核心功能
├── rvt_analytics/          # 分析統計功能
│   ├── question_classifier.py      # 問題分類器
│   ├── satisfaction_analyzer.py    # 滿意度分析
│   ├── statistics_manager.py       # 統計管理
│   └── report_generator.py         # 報告生成
├── conversation_management/  # 對話管理（共用）
└── dify_integration/        # Dify AI 整合（共用）
```

#### 🔧 ViewSet 架構（使用 Mixins）
```python
# backend/api/views/viewsets/knowledge_viewsets.py
class RVTGuideViewSet(
    LibraryManagerMixin,        # Library 管理
    FallbackLogicMixin,         # 降級邏輯
    VectorManagementMixin,      # 向量管理
    viewsets.ModelViewSet
):
    """RVT Assistant 知識庫 ViewSet"""
    
    # 配置 Manager 類別
    manager_config = {
        'library_available_flag': 'RVT_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'RVTGuideViewSetManager',
    }
    
    # 標準 CRUD + 自訂 Actions
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """聊天 API"""
        pass
    
    @action(detail=False, methods=['get'])
    def config(self, request):
        """配置 API"""
        pass
    
    @action(detail=False, methods=['post'])
    def upload_image(self, request):
        """圖片上傳 API"""
        pass
```

### 3️⃣ **資料庫架構**

#### 📊 核心資料表
```sql
-- 知識庫主表
CREATE TABLE rvt_guide (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id)
);

-- 圖片資料表（關聯）
CREATE TABLE content_images (
    id SERIAL PRIMARY KEY,
    rvt_guide_id INTEGER REFERENCES rvt_guide(id),
    image BYTEA,
    filename VARCHAR(255),
    uploaded_at TIMESTAMP
);

-- 對話記錄表
CREATE TABLE chat_conversations (
    id SERIAL PRIMARY KEY,
    conversation_id UUID UNIQUE,
    user_id INTEGER REFERENCES auth_user(id),
    system_type VARCHAR(50),  -- 'rvt_assistant', 'protocol_assistant'
    created_at TIMESTAMP
);

-- 聊天訊息表
CREATE TABLE chat_messages (
    id SERIAL PRIMARY KEY,
    conversation_id UUID REFERENCES chat_conversations(conversation_id),
    role VARCHAR(20),  -- 'user', 'assistant'
    content TEXT,
    created_at TIMESTAMP
);
```

#### 🔍 向量資料庫（pgvector）
```sql
-- 向量嵌入表（支援語義搜尋）
CREATE TABLE document_embeddings_1024 (
    id SERIAL PRIMARY KEY,
    source_type VARCHAR(50),     -- 'rvt_guide', 'protocol_guide'
    source_id INTEGER,           -- 對應的知識庫 ID
    content_chunk TEXT,          -- 文本片段
    embedding vector(1024),      -- 1024 維向量
    metadata JSONB,              -- 額外資料
    created_at TIMESTAMP
);

-- 向量相似度搜尋索引
CREATE INDEX ON document_embeddings_1024 
USING ivfflat (embedding vector_cosine_ops);
```

### 4️⃣ **AI 整合架構**

#### 🤖 Dify 整合
```python
# library/dify_integration/
DifyRequestManager
├── send_chat_request()      # 發送聊天請求
├── send_feedback()          # 發送反饋
└── handle_response()        # 處理回應

# 配置管理
DifyConfigManager
├── get_app_config()         # 獲取應用配置
└── validate_config()        # 驗證配置
```

#### 📡 API 端點對應
```
# 前端 → Django Backend → Dify
POST /api/rvt-guide/chat/
  → DifyRequestManager.send_chat_request()
    → Dify API: /v1/chat-messages
      → RAG 檢索 + LLM 生成
        → 回應給用戶
```

### 5️⃣ **分析與監控**

#### 📊 分析系統組件
```python
# library/rvt_analytics/
QuestionClassifier       # 問題智能分類
SatisfactionAnalyzer     # 滿意度分析
StatisticsManager        # 統計數據管理
ReportGenerator          # 報告生成器
```

#### 📈 分析 API 端點
```
GET /api/rvt-analytics/overview/          # 總覽數據
GET /api/rvt-analytics/questions/         # 問題分析
GET /api/rvt-analytics/satisfaction/      # 滿意度分析
GET /api/rvt-analytics/trends/            # 趨勢分析
```

## 🚀 創建新 Assistant 的標準流程

### 步驟 1：配置檔案設定（10 分鐘）
```javascript
// frontend/src/config/knowledgeBaseConfig.js
export const knowledgeBaseConfigs = {
  // ... 現有的 rvt-assistant 配置
  
  // ✅ 新增 Protocol Assistant
  'protocol-assistant': {
    apiEndpoint: '/api/protocol-guides/',
    pageSize: 100,
    routes: {
      list: '/knowledge/protocol-log',
      create: '/knowledge/protocol-guide/markdown-create',
      edit: '/knowledge/protocol-guide/markdown-edit/:id',
      getEditPath: (id) => `/knowledge/protocol-guide/markdown-edit/${id}`,
    },
    labels: {
      pageTitle: 'Protocol Assistant 知識庫',
      createButton: '新增 Protocol Guide',
      // ... 其他標籤
    },
    permissions: {
      canDelete: (user) => user?.is_staff === true,
      canEdit: (user) => !!user,
    },
    // ... 其他配置
  }
};
```

### 步驟 2：創建前端頁面（20 行代碼）
```javascript
// frontend/src/pages/ProtocolGuidePage/index.js
import React from 'react';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';
import GuideDetailModal from '../../components/GuideDetailModal';

const ProtocolGuidePage = () => {
  const config = knowledgeBaseConfigs['protocol-assistant'];
  
  return (
    <KnowledgeBasePage
      config={config}
      DetailModal={GuideDetailModal}
    />
  );
};

export default ProtocolGuidePage;
```

### 步驟 3：建立 Backend Library
```python
# backend/library/protocol_guide/__init__.py
"""
Protocol Assistant Library
參考 rvt_guide 結構建立
"""

from .viewset_manager import ProtocolGuideViewSetManager
from .api_handlers import ProtocolGuideAPIHandler
from .search_service import ProtocolGuideSearchService
from .vector_service import ProtocolGuideVectorService

PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True

__all__ = [
    'ProtocolGuideViewSetManager',
    'ProtocolGuideAPIHandler',
    'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
]
```

### 步驟 4：創建 Django Model
```python
# backend/api/models.py
class ProtocolGuide(models.Model):
    """Protocol Assistant 知識庫"""
    title = models.CharField(max_length=500)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'protocol_guide'
        ordering = ['-created_at']
```

### 步驟 5：創建 ViewSet（使用 Mixins）
```python
# backend/api/views/viewsets/knowledge_viewsets.py
from library.protocol_guide import ProtocolGuideViewSetManager

class ProtocolGuideViewSet(
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    viewsets.ModelViewSet
):
    """Protocol Assistant 知識庫 ViewSet"""
    queryset = ProtocolGuide.objects.all()
    serializer_class = ProtocolGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    manager_config = {
        'library_available_flag': 'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'ProtocolGuideViewSetManager',
    }
    
    @action(detail=False, methods=['post'])
    def chat(self, request):
        """聊天 API（複製 RVT 邏輯）"""
        return self._execute_with_library(
            'handle_chat_request',
            request,
            fallback_method='_fallback_chat'
        )
```

### 步驟 6：註冊路由
```python
# backend/api/urls.py
router.register(r'protocol-guides', views.ProtocolGuideViewSet)
```

### 步驟 7：配置 Dify 應用
```python
# library/config/dify_app_configs.py
DIFY_APPS['protocol-assistant'] = DifyAppConfig(
    app_name="Protocol Known Issue System",
    api_key="app-xxxxxxxxxxxxx",
    api_url="http://10.10.172.37/v1/chat-messages",
    knowledge_base_id="protocol_database",
    system_type="protocol_assistant"
)
```

## ✅ 完整功能檢查清單

新 Assistant 開發時，應包含以下功能：

### 前端功能
- [ ] 聊天介面（RvtAssistantChatPage）
- [ ] 知識庫管理頁面（RvtGuidePage）
- [ ] 分析儀表板（RVTAnalyticsPage）
- [ ] 訊息持久化（localStorage）
- [ ] 用戶反饋機制（點讚/點踩）
- [ ] 錯誤處理和重試機制
- [ ] 響應式設計（Ant Design）

### 後端功能
- [ ] RESTful CRUD API
- [ ] 聊天 API（/chat/）
- [ ] 配置 API（/config/）
- [ ] 圖片上傳 API（/upload_image/）
- [ ] 向量搜尋整合
- [ ] Dify AI 整合
- [ ] 對話記錄管理
- [ ] 權限控制

### 資料庫功能
- [ ] 知識庫主表
- [ ] 關聯圖片表
- [ ] 對話記錄表
- [ ] 訊息記錄表
- [ ] 向量嵌入表（pgvector）
- [ ] 適當的索引和約束

### 分析功能
- [ ] 問題分類統計
- [ ] 用戶滿意度分析
- [ ] 使用趨勢分析
- [ ] 回應時間監控
- [ ] 數據可視化

### AI 整合
- [ ] Dify 應用配置
- [ ] RAG 檢索配置
- [ ] 提示詞工程
- [ ] 回應格式化
- [ ] 錯誤處理

## 📚 關鍵參考文件

### 架構文檔
- `/docs/architecture/rvt-assistant-database-vector-architecture.md` - 資料庫與向量架構
- `/docs/architecture/rvt-analytics-system-architecture.md` - 分析系統架構
- `/docs/architecture/vector-database-scheduled-update-architecture.md` - 向量更新架構

### 開發指南
- `/docs/development/ui-component-guidelines.md` - UI 組件規範
- `/docs/ai-integration/dify-app-config-usage.md` - Dify 配置使用

### 程式碼範例
- `frontend/src/pages/RvtAssistantChatPage.js` - 聊天頁面範例
- `frontend/src/pages/RvtGuidePage/index.js` - 知識庫頁面範例
- `backend/api/views/viewsets/knowledge_viewsets.py` - ViewSet 範例
- `backend/library/rvt_guide/` - Library 結構範例

## 🎯 核心設計原則

1. **配置驅動** - 最大化使用配置，最小化代碼重複
2. **Library 分離** - 業務邏輯從 ViewSet 分離到 Library
3. **Mixins 架構** - 使用 Mixins 實現可重用邏輯
4. **統一標準** - 所有 Assistant 遵循相同的架構模式
5. **可擴展性** - 易於添加新功能和新 Assistant
6. **向量整合** - 內建向量搜尋和 RAG 支援
7. **分析優先** - 每個 Assistant 都包含完整分析功能

---

## 🚀 新增 Assistant 知識庫的標準化流程

### ⚠️ 重要規範
**當需要新增任何 Web xxx Assistant 知識庫時，AI 必須遵守以下標準化流程：**

### 📋 必要步驟檢查清單

#### 1️⃣ **資料庫欄位格式（必須與 RVT Assistant 一致）**
```python
# backend/api/models.py
class XxxGuide(models.Model):
    """Xxx Assistant 知識庫 - 欄位格式必須與 RVTGuide 完全相同"""
    
    # ✅ 必須包含的標準欄位
    title = models.CharField(max_length=300, verbose_name="文檔標題")
    content = models.TextField(verbose_name="文檔內容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="建立時間")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新時間")
    
    class Meta:
        db_table = 'xxx_guide'  # 表名格式：xxx_guide
        ordering = ['title']
        verbose_name = "Xxx Assistant 知識庫"
        verbose_name_plural = "Xxx Assistant 知識庫"
```

**🔴 強制要求**：
- 欄位名稱：`title`, `content`, `created_at`, `updated_at`（不可更改）
- 欄位類型：必須與 RVTGuide 相同
- 表名格式：`{assistant_name}_guide`（小寫 + 底線）

#### 2️⃣ **前端配置（knowledgeBaseConfig.js）**
```javascript
// frontend/src/config/knowledgeBaseConfig.js
export const knowledgeBaseConfigs = {
  // ✅ 新增配置（複製 rvt-assistant 配置並修改）
  'xxx-assistant': {
    apiEndpoint: '/api/xxx-guides/',
    pageSize: 100,
    
    routes: {
      list: '/knowledge/xxx-log',
      create: '/knowledge/xxx-guide/markdown-create',
      edit: '/knowledge/xxx-guide/markdown-edit/:id',
      preview: '/knowledge/xxx-guide/preview/:id',  // ⚠️ 必須添加預覽路由
      getEditPath: (id) => `/knowledge/xxx-guide/markdown-edit/${id}`,
      getPreviewPath: (id) => `/knowledge/xxx-guide/preview/${id}`,  // ⚠️ 必須添加
    },
    
    events: {
      reload: 'xxx-guide-reload',
    },
    
    labels: {
      pageTitle: 'Xxx Assistant 知識庫',
      createButton: '新增 Xxx Guide',
      // ... 其他標籤
    },
    
    columns: {
      primaryField: 'title',
      dateField: 'created_at',
      sortField: 'created_at',
      sortOrder: 'descend',
      extraColumns: [],
    },
    
    permissions: {
      canDelete: (user) => user?.is_staff === true,
      canEdit: (user) => !!user,
      canView: (user) => !!user,
    },
    
    table: {
      scroll: { x: 1400, y: 'calc(100vh - 220px)' },
      pagination: {
        defaultPageSize: 10,
        pageSizeOptions: ['10', '20', '50', '100'],
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
      },
    },
  },
};
```

#### 3️⃣ **前端路由配置（App.js）**
```javascript
// frontend/src/App.js

// ✅ 必須添加的路由（4 個）
<Route path="/knowledge/xxx-log" element={
  <ProtectedRoute permission="kbXxxAssistant" fallbackTitle="Knowledge Base 存取受限">
    <XxxGuidePage />
  </ProtectedRoute>
} />

<Route path="/knowledge/xxx-guide/preview/:id" element={
  <ProtectedRoute permission="kbXxxAssistant" fallbackTitle="Knowledge Base 存取受限">
    <GuidePreviewPage />  {/* ⚠️ 使用通用預覽頁面 */}
  </ProtectedRoute>
} />

<Route path="/knowledge/xxx-guide/markdown-create" element={
  <ProtectedRoute permission="kbXxxAssistant" fallbackTitle="Knowledge Base 存取受限">
    <MarkdownEditorPage />
  </ProtectedRoute>
} />

<Route path="/knowledge/xxx-guide/markdown-edit/:id" element={
  <ProtectedRoute permission="kbXxxAssistant" fallbackTitle="Knowledge Base 存取受限">
    <MarkdownEditorPage />
  </ProtectedRoute>
} />
```

**⚠️ 同時必須更新 App.js 中的頁面標題和按鈕配置**：
```javascript
// 預覽頁面標題
if (pathname.startsWith('/knowledge/xxx-guide/preview/')) {
  const id = pathname.split('/').pop();
  return { text: 'Xxx Guide 預覽', id: id };
}

// Markdown 編輯器標題
if (pathname.startsWith('/knowledge/xxx-guide/markdown-edit/')) {
  const id = pathname.split('/').pop();
  return { text: '編輯 Xxx Guide', id: id };
}
if (pathname === '/knowledge/xxx-guide/markdown-create') {
  return { text: '新建 Xxx Guide', id: null };
}

// 列表頁按鈕
if (pathname === '/knowledge/xxx-log') {
  return (
    <div style={{ display: 'flex', gap: '12px' }}>
      <Button icon={<ReloadOutlined />} onClick={() => {
        window.dispatchEvent(new CustomEvent('xxx-guide-reload'));
      }} size="large">
        重新整理
      </Button>
      <Button type="primary" size="large" icon={<PlusOutlined />}
        onClick={() => navigate('/knowledge/xxx-guide/markdown-create')}>
        新增 Xxx Guide
      </Button>
    </div>
  );
}
```

#### 4️⃣ **使用者權限配置（UserProfile Model）**
```python
# backend/api/models.py - UserProfile

class UserProfile(models.Model):
    # ... 現有欄位
    
    # ✅ 必須添加新的權限欄位
    kb_xxx_assistant = models.BooleanField(
        default=False, 
        verbose_name="Xxx Assistant 知識庫權限",
        help_text="是否允許存取 Xxx Assistant 知識庫"
    )
```

**⚠️ 添加權限欄位後必須執行**：
```bash
# 創建 migration
docker exec ai-django python manage.py makemigrations

# 執行 migration
docker exec ai-django python manage.py migrate
```

#### 5️⃣ **前端權限對應（UserContext.js）**
```javascript
// frontend/src/contexts/UserContext.js

const permissions = {
  // ... 現有權限
  
  // ✅ 添加新的權限映射
  kbXxxAssistant: profile?.kb_xxx_assistant || false,
};
```

#### 6️⃣ **使用者編輯表單（UserEditModal.js）**
```javascript
// frontend/src/components/UserEditModal.js

// ✅ 在知識庫權限區塊添加新的 Checkbox
<Card title="知識庫功能" size="small" style={{ marginBottom: '16px' }}>
  {/* 現有的權限 Checkbox */}
  <Form.Item name="kb_rvt_assistant" valuePropName="checked">
    <Checkbox>RVT Assistant 知識庫</Checkbox>
  </Form.Item>
  <Form.Item name="kb_protocol_assistant" valuePropName="checked">
    <Checkbox>Protocol Assistant 知識庫</Checkbox>
  </Form.Item>
  
  {/* ✅ 新增的權限 Checkbox */}
  <Form.Item name="kb_xxx_assistant" valuePropName="checked">
    <Checkbox>Xxx Assistant 知識庫</Checkbox>
  </Form.Item>
</Card>
```

#### 7️⃣ **側邊欄選單（Sidebar.js）**
```javascript
// frontend/src/components/Sidebar.js

// ✅ 在 Knowledge Base 子選單中添加新項目
{
  key: 'knowledge',
  icon: <BookOutlined />,
  label: 'Knowledge Base',
  children: [
    // 現有項目...
    {
      key: '/knowledge/xxx-log',
      label: 'Xxx Assistant',
      onClick: () => navigate('/knowledge/xxx-log'),
    },
  ],
}
```

#### 8️⃣ **後端 ViewSet 和 API 註冊**
```python
# backend/api/views/viewsets/knowledge_viewsets.py
class XxxGuideViewSet(viewsets.ModelViewSet):
    """Xxx Assistant 知識庫 ViewSet"""
    queryset = XxxGuide.objects.all()
    serializer_class = XxxGuideSerializer
    permission_classes = [permissions.IsAuthenticated]

# backend/api/urls.py
router.register(r'xxx-guides', views.XxxGuideViewSet)
```

### 📊 完整檢查清單

創建新 Assistant 知識庫時，AI 必須確認以下所有項目：

**資料庫層面**：
- [ ] Model 欄位與 RVTGuide 完全一致（title, content, created_at, updated_at）
- [ ] 表名格式正確（xxx_guide）
- [ ] Migration 已創建並執行

**前端配置層面**：
- [ ] knowledgeBaseConfig.js 添加完整配置（包含 preview 路由）
- [ ] App.js 添加 4 個路由（list, preview, create, edit）
- [ ] App.js 添加頁面標題配置
- [ ] App.js 添加按鈕操作配置
- [ ] GuidePreviewPage 支援新 Assistant（自動識別路徑）

**權限管理層面**：
- [ ] UserProfile 添加新的 kb_xxx_assistant 欄位
- [ ] UserContext.js 添加權限映射
- [ ] UserEditModal.js 添加權限 Checkbox（在知識庫功能卡片中）
- [ ] ProtectedRoute 使用正確的權限名稱（kbXxxAssistant）

**導航層面**：
- [ ] Sidebar.js 添加選單項目

**後端 API 層面**：
- [ ] ViewSet 創建完成
- [ ] Serializer 創建完成
- [ ] URL 路由註冊完成

### 🎯 命名規範

**必須遵守的命名規範**：

| 項目 | 格式 | 範例 |
|------|------|------|
| 資料庫表名 | `{name}_guide` | `protocol_guide`, `qa_guide` |
| Django Model | `{Name}Guide` | `ProtocolGuide`, `QaGuide` |
| 配置 Key | `{name}-assistant` | `protocol-assistant`, `qa-assistant` |
| API 端點 | `/api/{name}-guides/` | `/api/protocol-guides/` |
| 前端路由前綴 | `/knowledge/{name}-` | `/knowledge/protocol-`, `/knowledge/qa-` |
| 權限欄位 | `kb_{name}_assistant` | `kb_protocol_assistant` |
| 權限 Key | `kb{Name}Assistant` | `kbProtocolAssistant` |
| 事件名稱 | `{name}-guide-reload` | `protocol-guide-reload` |

### ⚠️ 常見錯誤提醒

AI 在創建新 Assistant 時必須避免以下錯誤：

1. **❌ 忘記添加 preview 路由** - 會導致資料預覽功能無法使用
2. **❌ 資料庫欄位不一致** - 必須與 RVTGuide 完全相同
3. **❌ 權限欄位命名錯誤** - 必須使用 `kb_{name}_assistant` 格式
4. **❌ 忘記更新 GuidePreviewPage** - 需要支援多 Assistant 路徑識別
5. **❌ 忘記在 UserEditModal 添加 Checkbox** - 導致管理員無法設置權限
6. **❌ 忘記執行 Migration** - 導致資料庫表未創建

---

**🎉 使用 RVT Assistant 作為範本，嚴格遵循以上標準化流程，新的 Assistant 可以在 1-2 天內完成開發！**

# AI Platform 專案功能架構

## 🎯 專案概述
這是一個全功能的 AI 平台 Web 應用程式，使用 React + Django + PostgreSQL 技術棧，專門用於測試管理、知識庫管理和 AI 系統集成。

## 🏗️ 系統架構
- **前端**：React.js (Port 3000) with **Ant Design** (主要 UI 框架)
- **後端**：Django REST Framework (Port 8000)
- **資料庫**：PostgreSQL (Port 5432)
- **反向代理**：Nginx (Port 80/443)
- **容器編排**：Docker Compose
- **管理工具**：Portainer (Port 9000), Adminer (Port 9090)

## 📋 已實現功能模組

### 🔐 用戶認證系統
- **用戶註冊/登入/登出** (`UserLoginView`, `user_register`, `user_logout`)
- **Session + Token 雙重認證**
- **用戶資訊管理** (`UserViewSet`, `UserProfileViewSet`)
- **個人檔案擴展** (`UserProfile` model)
- **權限控制** (基於 Django permissions)

### 📊 專案管理系統
- **專案 CRUD** (`ProjectViewSet`)
- **專案成員管理** (add_member, remove_member actions)
- **專案擁有者權限控制**
- **任務管理** (`TaskViewSet`)
  - 任務狀態管理 (pending, in_progress, completed, cancelled)
  - 任務優先級 (low, medium, high, urgent)
  - 任務指派功能
  - 到期日管理

### 🧪 測試管理系統
- **測試類別管理** (`TestClassViewSet`)
  - 管理員專用 CRUD 功能
  - 測試類別啟用/停用
  - 一般用戶只讀權限
- **Know Issue 知識庫** (`KnowIssueViewSet`)
  - 自動 Issue ID 生成 (格式: TestClass-序號)
  - 測試版本追蹤
  - JIRA 整合
  - 錯誤訊息和腳本存儲
  - 問題狀態管理
- **RVT Assistant 知識庫** (`RvtGuideViewSet`)
  - 智能助手指導文檔管理
  - 分類管理系統
  - 問題類型標記
  - 內容搜索和過濾

### 👥 員工管理系統
- **員工基本資料** (`EmployeeViewSet` - 簡化版)
- **Dify 員工資料** (`DifyEmployeeViewSet` - 完整版)
  - 照片二進位存儲
  - 技能、部門、職位管理
  - 入職日期和狀態追蹤

### 🤖 AI 系統整合
- **Dify 外部知識庫 API** (`dify_knowledge_search`)
  - 符合 Dify 官方規格
  - PostgreSQL 全文搜索
  - 智能分數計算
  - 多知識源支援 (員工資料庫、Know Issue 資料庫)
- **員工智能查詢**
  - 基於技能、部門、職位的語義搜索
  - 動態分數閾值調整

### 🎨 前端頁面系統
- **儀表板** (`DashboardPage.js`)
- **Know Issue 管理** (`KnowIssuePage.js`)
  - 測試類別過濾器
  - 資料預覽和編輯
  - localStorage 狀態持久化
  - 自動完成功能
- **RVT Assistant** (`RvtGuidePage.js`) 🎯 **[標準範本]**
  - 智能助手指導文檔管理
  - 完整 CRUD 操作界面
  - 高級表格展示和過濾
  - 響應式設計
  - **作為所有 Assistant 功能的標準參考架構**
- **查詢頁面** (`QueryPage.js`)
- **設定頁面** (`SettingsPage.js`)
- **測試類別管理** (`TestClassManagementPage.js`)

### 🔧 系統組件
- **用戶認證組件** (`LoginForm.js`, `RegisterForm.js`)
- **導航系統** (`Sidebar.js`, `TopHeader.js`)
- **認證上下文** (`AuthContext`)
- **響應式佈局** (基於 Ant Design Grid 系統)

## 🛠️ 技術特色

### 後端 Django 特色
- **ViewSet 架構** (ModelViewSet, ReadOnlyModelViewSet)
- **自定義 Actions** (@action decorators)
- **多層權限控制**
- **Session + DRF Token 認證**
- **CORS 跨域支援**
- **PostgreSQL 進階查詢**
- **自動序號生成**
- **CSRF 豁免 API**

### 前端 React 特色
- **Ant Design 元件庫** (統一 UI 框架)
- **Context API 狀態管理**
- **localStorage 持久化**
- **動態表格和表單** (Table, Form 組件)
- **檔案上傳和預覽**
- **響應式設計** (Row, Col Grid 系統)
- **錯誤處理和用戶反饋** (message, notification)

### 資料庫設計
- **外鍵關聯** (User, Project, Task 關聯)
- **多對多關係** (Project members)
- **自動時間戳記**
- **級聯刪除控制**
- **唯一約束和索引**

## 📡 API 端點架構

### 認證 API
```
POST /api/auth/login/     - 用戶登入
POST /api/auth/register/  - 用戶註冊
POST /api/auth/logout/    - 用戶登出
GET  /api/auth/user/      - 獲取用戶資訊
```

### CRUD API (RESTful)
```
/api/users/        - 用戶管理 (ReadOnly)
/api/profiles/     - 用戶檔案
/api/projects/     - 專案管理 (含成員管理 actions)
/api/tasks/        - 任務管理 (含指派和狀態 actions)
/api/employees/    - 簡化員工資料
/api/dify-employees/ - 完整員工資料
/api/know-issues/  - 問題知識庫
/api/test-classes/ - 測試類別管理
/api/rvt-guides/   - RVT Assistant 知識庫
```

### 特殊 API
```
POST /api/dify/knowledge/retrieval/ - Dify 外部知識庫 (多知識源)
```

## 🔍 資料模型概覽

1. **User** (Django 內建) + **UserProfile** (擴展)
2. **Project** (專案) → **Task** (任務)
3. **TestClass** (測試類別) → **KnowIssue** (問題)
4. **Employee** (簡化員工) / **DifyEmployee** (完整員工)
5. **RvtGuide** (RVT Assistant 指導文檔) 🎯 **[範本架構]**

## 🚀 部署特色
- **Docker Compose 多服務編排**
- **Nginx 反向代理**
- **Volume 數據持久化**
- **環境變數配置**
- **容器健康檢查**
- **日誌管理**

## 🔐 安全特色
- **CSRF 保護**
- **認證權限控制**
- **SQL 注入防護**
- **XSS 防護**
- **HTTPS 支援**
- **Session 安全**

## 📊 監控和管理
- **Portainer 容器管理**
- **Adminer 資料庫管理**
- **Django Admin 後台**
- **API 日誌記錄**
- **錯誤追蹤**

## 🎯 專案狀態
- **前後端完全分離**
- **API 完整測試**
- **用戶認證完善**
- **資料庫關聯正確**
- **容器化部署就緒**
- **Ant Design UI 統一**
- **Dify AI 整合完成**
- **生產環境可用**

# 遠端 PC 操作指引（AI 專用）

## 重要安全警告
⚠️ **此檔案包含敏感連線資訊，僅供內部 AI 工具參考。請勿將此檔案推送至公開 repository 或分享給未授權人員。**

## 遠端主機資訊
- **使用者**：user
- **密碼**：1234
- **IP 位址**：10.10.173.12
- **連線方式**：SSH

## AI Platform 系統資訊

### 服務架構
- **前端 (React)**：Port 3000 (開發)，透過 Nginx Port 80 對外
- **後端 (Django)**：Port 8000，提供 REST API
- **資料庫 (PostgreSQL)**：Port 5432
- **反向代理 (Nginx)**：Port 80/443
- **容器管理 (Portainer)**：Port 9000
- **資料庫管理 (Adminer)**：Port 9090

### 資料庫連接資訊
- **資料庫類型**：PostgreSQL 15-alpine
- **容器名稱**：postgres_db
- **資料庫名稱**：ai_platform
- **用戶名**：postgres
- **密碼**：postgres123
- **外部連接**：localhost:5432 (從主機連接)
- **內部連接**：postgres_db:5432 (容器間通信)

### Web 管理介面
- **主要應用**：http://10.10.173.12 (Nginx 代理)
- **Adminer 資料庫管理**：http://10.10.173.12:9090
  - 系統：PostgreSQL
  - 服務器：postgres_db
  - 用戶名：postgres
  - 密碼：postgres123
- **Portainer 容器管理**：http://10.10.173.12:9000
- **Django Admin**：http://10.10.173.12/admin/
- **API 端點**：http://10.10.173.12/api/

### Docker 容器狀態
- **ai-nginx**：Nginx 反向代理
- **ai-react**：React 前端開發服務器
- **ai-django**：Django 後端 API 服務
- **postgres_db**：PostgreSQL 主資料庫
- **adminer_nas**：Adminer 資料庫管理工具
- **portainer**：Docker 容器管理工具

### 開發環境路徑
- **專案根目錄**：/home/user/codes/ai-platform-web
- **前端代碼**：/home/user/codes/ai-platform-web/frontend
- **後端代碼**：/home/user/codes/ai-platform-web/backend
- **Nginx 配置**：/home/user/codes/ai-platform-web/nginx
- **文檔目錄**：/home/user/codes/ai-platform-web/docs

### 常用指令
```bash
# 檢查所有容器狀態
docker compose ps

# 重新啟動特定服務
docker compose restart [service_name]

# 查看服務日誌
docker logs [container_name] --follow

# 進入容器
docker exec -it [container_name] bash

# 執行 Django 指令
docker exec -it ai-django python manage.py [command]

# 資料庫備份
docker exec postgres_db pg_dump -U postgres ai_platform > backup.sql
```

### API 認證狀態
- **當前狀態**：API 需要認證 (HTTP 403 為正常狀態)
- **Token 認證**：支援 DRF Token Authentication
- **Session 認證**：支援 Django Session Authentication
- **CORS 設定**：已配置跨域請求支援

### 系統狀態檢查
- **前後端整合**：✅ 正常運行
- **資料庫連接**：✅ PostgreSQL 健康運行
- **API 服務**：✅ Django REST Framework 正常
- **反向代理**：✅ Nginx 正確轉發請求
- **容器編排**：✅ Docker Compose 所有服務運行中

## 🐍 Python 開發環境規範

### ⚠️ 重要要求：所有 Python 測試和開發都必須使用虛擬環境

**強制性規則**：
1. **任何 Python 程式的測試、執行、開發都必須在虛擬環境 (venv) 中進行**
2. **禁止在系統 Python 環境中直接安裝套件或執行測試**
3. **所有 AI 協助的 Python 相關工作都需要先確認虛擬環境已啟動**

### 🚀 虛擬環境使用流程

#### 1. 檢查虛擬環境狀態
```bash
# 檢查是否在虛擬環境中
echo $VIRTUAL_ENV

# 如果輸出為空，表示未在虛擬環境中
```

#### 2. 啟動虛擬環境
```bash
# 方法一：使用啟動腳本（推薦）
cd /home/user/codes/ai-platform-web
./activate_dev.sh

# 方法二：手動啟動
source venv/bin/activate

# 確認啟動成功（應顯示虛擬環境路徑）
which python
echo $VIRTUAL_ENV
```

#### 3. 安裝依賴套件
```bash
# 在虛擬環境中安裝
pip install -r requirements.txt

# 或安裝單個套件
pip install package_name
```

#### 4. 執行 Python 程式
```bash
# 確保在虛擬環境中執行
python tests/test_ssh_communication/deepseek_ssh_test.py
python -m pytest tests/
```

#### 5. 退出虛擬環境
```bash
deactivate
```

### 🛡️ AI 協助時的檢查清單

**在任何 Python 相關操作前，AI 必須確認**：
- [ ] 使用者已在虛擬環境中 (`echo $VIRTUAL_ENV` 不為空)
- [ ] 如果未在虛擬環境中，先指導啟動虛擬環境
- [ ] 所有 `pip install` 命令都在虛擬環境中執行
- [ ] 所有 Python 程式執行都在虛擬環境中進行

## Dify 外部知識庫整合完整指南

### 🎯 概述
本指南詳細說明如何建立 Django REST API 作為 Dify 的外部知識庫，實現智能員工資料查詢功能。

### 📋 已實現的知識庫系統

#### 1. **員工知識庫** (`knowledge_id: employee_database`)
```bash
# 測試員工知識庫
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "employee_database",
    "query": "Python工程師",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

#### 2. **Know Issue 知識庫** (`knowledge_id: know_issue_db`)
```bash
# 測試 Know Issue 知識庫
curl -X POST "http://10.10.173.12/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db", 
    "query": "Samsung",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'
```

### 🔧 快速測試指令
```bash
# 檢查 Django 容器狀態
docker compose ps | grep django

# 檢查 API 端點
curl -X GET http://10.10.173.12/api/

# 檢查 Dify API 日誌
docker logs ai-django | grep "dify_knowledge"

# 創建測試員工資料
docker exec ai-django python manage.py create_test_employees
```

### 🎯 Dify 配置要點
1. **外部知識 API 端點**：`http://10.10.173.12/api/dify/knowledge`
2. **Score 閾值設定**：建議 0.5-0.6 (不要設太低)
3. **Top K 設定**：建議 3-5
4. **知識庫 ID**：`employee_database` 或 `know_issue_db`

### 📊 監控指令
```bash
# 即時監控 Django 日誌
docker logs ai-django --follow | grep "POST /api/dify"

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "\dt"

# 檢查員工資料數量
docker exec ai-django python manage.py shell -c "from api.models import Employee; print(Employee.objects.count())"
```

## 🔧 Dify App Config 使用指南

### 📁 配置管理系統
專案已建立統一的 Dify 應用配置管理系統，避免配置散落各處。

**配置文件位置**：
- `/library/config/dify_app_configs.py` - 應用配置管理
- `docs/guide/dify-app-config-usage.md` - 完整使用指南

### 🎯 Protocol Known Issue System 配置

#### 快速使用方式（推薦）
```python
# 導入配置工具
from library.config.dify_app_configs import create_protocol_chat_client

# 直接創建配置好的客戶端
client = create_protocol_chat_client()

# 測試連接
if client.test_connection():
    print("✅ 連接成功")
    
    # 發送查詢
    result = client.chat("ULINK")
    if result['success']:
        print(f"回應: {result['answer']}")
```

# 📚 文檔分類與創建指引

## 🗂️ **AI 創建文檔時的強制分類規則**

**重要：AI 在創建新文檔時必須按照以下分類標準將文件放入對應目錄**

### 📁 **docs/ 目錄結構與分類規則**

#### 1. **`docs/architecture/` - 系統架構相關**
**放置條件**：系統設計、架構說明、技術架構文檔
**範例內容**：
- 向量資料庫架構設計
- Celery Beat 任務調度架構
- 系統組件關聯圖
- 微服務架構說明
- 資料流設計文檔

#### 2. **`docs/development/` - 開發指南**
**放置條件**：開發規範、編碼指南、技術標準
**範例內容**：
- 前端/後端開發規範
- UI 組件使用指南
- 代碼風格指南
- 配置管理說明
- Commit 訊息規範

#### 3. **`docs/deployment/` - 部署與環境設置**
**放置條件**：部署流程、環境配置、基礎設施
**範例內容**：
- Docker 容器部署
- 資料庫安裝配置
- 環境變數設定
- 監控工具設置
- CI/CD 流程

#### 4. **`docs/ai-integration/` - AI 整合相關**
**放置條件**：AI 系統整合、外部 AI 服務配置
**範例內容**：
- Dify 整合配置
- 外部 AI API 使用
- 機器學習模型配置
- AI 服務串接指南
- 智能功能開發

#### 5. **`docs/vector-search/` - 向量搜尋系統**
**放置條件**：向量搜尋功能相關的所有文檔
**範例內容**：
- 向量搜尋實作指南
- 向量模型配置
- 搜尋效能優化
- 向量資料庫操作
- 搜尋演算法說明

#### 6. **`docs/features/` - 功能模組文檔**
**放置條件**：具體功能模組的說明和使用指南
**範例內容**：
- 業務功能說明
- 用戶操作指南
- 功能實作報告
- 工作流程圖
- 系統功能架構

#### 7. **`docs/refactoring-reports/` - 重構報告**
**放置條件**：系統重構、代碼改進的記錄文檔
**範例內容**：
- 重構前後對比
- 效能改善報告
- 代碼優化記錄
- 架構升級說明
- 技術債務清理

#### 8. **`docs/testing/` - 測試相關**
**放置條件**：測試工具、測試指南、QA 文檔
**範例內容**：
- 單元測試指南
- 整合測試說明
- 測試工具使用
- 自動化測試配置
- 測試案例文檔

### 🎯 **AI 文檔創建檢查清單**

在創建任何 `.md` 文檔時，AI 必須：

1. **� 確定分類**：根據文檔內容確定所屬的 8 個分類之一
2. **🎯 選擇目錄**：將文檔放入對應的子目錄中
3. **📝 命名規範**：使用小寫字母、連字號分隔的檔名
4. **🔗 更新索引**：如果是重要文檔，考慮更新 `docs/README.md`

### 🚫 **禁止的做法**
- ❌ 不要將文檔直接放在 `docs/` 根目錄（除非是索引文件）
- ❌ 不要創建新的分類目錄（使用現有的 8 個分類）
- ❌ 不要混合不同類型的內容在同一文檔中

### ✅ **推薦的做法**
- ✅ 根據主要內容選擇最合適的分類
- ✅ 使用清晰的檔名表達文檔用途
- ✅ 在文檔開頭添加用途說明
- ✅ 交叉引用相關文檔

---

## �📚 重要文檔索引（已更新路徑）

### 🔍 向量搜尋系統
- **完整指南**: `/docs/vector-search/vector-search-guide.md` - 向量搜尋系統的完整建立和使用方法
- **快速參考**: `/docs/vector-search/vector-search-quick-reference.md` - 常用命令和故障排除
- **AI 專用指南**: `/docs/vector-search/ai-vector-search-guide.md` - AI 助手的操作指南和最佳實踐

### 🎨 UI 開發規範
- **UI 組件規範**: `/docs/development/ui-component-guidelines.md` - Ant Design 使用標準
- **前端開發指南**: `/docs/development/frontend-development.md` - React 開發規範
- **AI Assistant 範本指南**: `/docs/development/assistant-template-guide.md` - 🎯 使用 RVT Assistant 作為範本創建新 Assistant

### 🤖 AI 整合
- **Dify 外部知識庫**: `/docs/ai-integration/dify-external-knowledge-api-guide.md`
- **API 整合**: `/docs/ai-integration/api-integration.md`
- **AI 指令說明**: `/docs/ai_instructions.md`

### 💻 開發指南
- **後端開發**: `/docs/development/backend-development.md`
- **Docker 安裝**: `/docs/deployment/docker-installation.md`

---

**更新日期**: 2025-10-18  
**版本**: v2.2  
**狀態**: ✅ 已整合文檔分類指引  
**主要特色**: Ant Design First + Dify AI 整合 + 文檔自動分類  
**負責人**: AI Platform Team

### 📝 **v2.2 更新內容**
- ✅ 新增完整的文檔分類指引
- ✅ 定義 8 個標準文檔分類目錄
- ✅ 提供 AI 文檔創建檢查清單
- ✅ 更新所有文檔路徑引用
- ✅ 建立文檔命名和放置規範

`````
`````
