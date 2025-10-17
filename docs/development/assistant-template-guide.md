# 🎯 AI Assistant 標準範本開發指南

## 📘 文檔目的
本文檔說明如何使用 **RVT Assistant** 作為標準範本，快速開發新的 AI Assistant 功能模組。

## 🌟 為什麼選擇 RVT Assistant 作為範本？

RVT Assistant 是專案中第一個完整實現的 AI Assistant 系統，包含：
- ✅ 完整的前後端分離架構
- ✅ 配置驅動的開發模式
- ✅ Library 模組化設計
- ✅ Mixins 可重用架構
- ✅ 向量搜尋整合
- ✅ Dify AI 整合
- ✅ 完整的分析系統
- ✅ 統一的 UI/UX 標準

## 🎯 RVT Assistant 架構全景圖

```
┌─────────────────────────────────────────────────────────────────┐
│                     RVT Assistant 完整架構                        │
└─────────────────────────────────────────────────────────────────┘

📱 前端層 (React + Ant Design)
├── 🗨️ RvtAssistantChatPage.js         聊天互動介面
├── 📚 RvtGuidePage/index.js            知識庫管理（配置驅動）
├── 📊 RVTAnalyticsPage.js              分析儀表板
├── 🎣 hooks/
│   ├── useRvtChat.js                   聊天邏輯
│   ├── useRvtGuideData.js              資料管理
│   └── useRvtGuideList.js              列表操作
└── ⚙️ config/knowledgeBaseConfig.js    配置中心

🔌 API 層 (Django REST Framework)
├── 📡 /api/rvt-guides/                 RESTful CRUD
├── 💬 /api/rvt-guide/chat/             聊天端點
├── ⚙️ /api/rvt-guide/config/           配置端點
├── 🖼️ /api/rvt-guide/upload_image/     圖片上傳
└── 📈 /api/rvt-analytics/*             分析端點

🧩 Library 層 (業務邏輯模組化)
├── 📦 library/rvt_guide/
│   ├── viewset_manager.py              ViewSet 管理器
│   ├── api_handlers.py                 API 處理邏輯
│   ├── fallback_handlers.py            降級處理
│   ├── search_service.py               搜尋服務
│   └── vector_service.py               向量服務
├── 📊 library/rvt_analytics/
│   ├── question_classifier.py          問題分類
│   ├── satisfaction_analyzer.py        滿意度分析
│   └── statistics_manager.py           統計管理
├── 💬 library/conversation_management/  對話管理（共用）
└── 🤖 library/dify_integration/         AI 整合（共用）

🗄️ 資料庫層 (PostgreSQL + pgvector)
├── 📄 rvt_guide                        知識庫主表
├── 🖼️ content_images                   關聯圖片
├── 💬 chat_conversations               對話記錄
├── 📝 chat_messages                    訊息記錄
└── 🔍 document_embeddings_1024         向量嵌入（RAG）

🤖 AI 層 (Dify Integration)
├── 📡 Dify API Integration             AI 推理服務
├── 🔍 RAG (Retrieval-Augmented)        知識檢索增強
└── 📊 Analytics & Feedback             分析與反饋
```

## 🚀 快速開始：創建新 Assistant（5 步驟）

### 範例：創建 Protocol Assistant

#### 步驟 1：配置設定（5 分鐘）
```javascript
// frontend/src/config/knowledgeBaseConfig.js
export const knowledgeBaseConfigs = {
  // ... 保留 rvt-assistant 配置
  
  'protocol-assistant': {
    apiEndpoint: '/api/protocol-guides/',
    pageSize: 100,
    routes: {
      list: '/knowledge/protocol-log',
      create: '/knowledge/protocol-guide/markdown-create',
      edit: '/knowledge/protocol-guide/markdown-edit/:id',
      preview: '/knowledge/protocol-guide/preview/:id',
      getEditPath: (id) => `/knowledge/protocol-guide/markdown-edit/${id}`,
      getPreviewPath: (id) => `/knowledge/protocol-guide/preview/${id}`,
    },
    events: {
      reload: 'protocol-guide-reload',
    },
    labels: {
      pageTitle: 'Protocol Assistant 知識庫',
      createButton: '新增 Protocol Guide',
      reloadButton: '重新整理',
      editTitle: '編輯 Protocol Guide',
      createTitle: '新建 Protocol Guide',
      deleteConfirmTitle: '確認刪除',
      deleteConfirmContent: (title) => `確定要刪除協議文檔 "${title}" 嗎？`,
      deleteSuccess: '刪除成功',
      deleteFailed: '刪除失敗',
    },
    columns: {
      primaryField: 'title',
      dateField: 'created_at',
      sortField: 'created_at',
      sortOrder: 'descend',
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
      },
    },
  },
};
```

#### 步驟 2：前端頁面（2 分鐘，20 行代碼）
```javascript
// frontend/src/pages/ProtocolGuidePage/index.js
import React from 'react';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';
import GuideDetailModal from '../../components/GuideDetailModal';

/**
 * Protocol Assistant 知識庫頁面
 * 使用配置驅動架構，參考 RVT Assistant 範本
 */
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

#### 步驟 3：Django Model（5 分鐘）
```python
# backend/api/models.py

class ProtocolGuide(models.Model):
    """Protocol Assistant 知識庫（參考 RVTGuide）"""
    title = models.CharField(max_length=500, verbose_name='標題')
    content = models.TextField(verbose_name='內容')
    category = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        verbose_name='分類'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='創建時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='創建者'
    )
    
    class Meta:
        db_table = 'protocol_guide'
        ordering = ['-created_at']
        verbose_name = 'Protocol Guide'
        verbose_name_plural = 'Protocol Guides'
    
    def __str__(self):
        return self.title
```

#### 步驟 4：Library 模組（30 分鐘）
```python
# backend/library/protocol_guide/__init__.py
"""
Protocol Assistant Library
參考 RVT Guide 結構實現
"""

from .viewset_manager import ProtocolGuideViewSetManager
from .api_handlers import ProtocolGuideAPIHandler
from .search_service import ProtocolGuideSearchService
from .vector_service import ProtocolGuideVectorService
from .fallback_handlers import ProtocolGuideFallbackHandler

PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True

__all__ = [
    'ProtocolGuideViewSetManager',
    'ProtocolGuideAPIHandler',
    'ProtocolGuideSearchService',
    'ProtocolGuideVectorService',
    'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
]
```

```python
# backend/library/protocol_guide/viewset_manager.py
"""
ViewSet 管理器 - 複製自 rvt_guide/viewset_manager.py 並調整
"""

class ProtocolGuideViewSetManager:
    """Protocol Guide ViewSet 管理器"""
    
    def __init__(self):
        self.api_handler = ProtocolGuideAPIHandler()
        self.search_service = ProtocolGuideSearchService()
        self.vector_service = ProtocolGuideVectorService()
    
    def handle_chat_request(self, request):
        """處理聊天請求（參考 RVT 實現）"""
        return self.api_handler.process_chat(request)
    
    def handle_search_request(self, request):
        """處理搜尋請求"""
        return self.search_service.search(request)
    
    # ... 其他方法參考 RVT 實現
```

#### 步驟 5：ViewSet（10 分鐘）
```python
# backend/api/views/viewsets/knowledge_viewsets.py

from library.protocol_guide import (
    ProtocolGuideViewSetManager,
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE
)

class ProtocolGuideViewSet(
    LibraryManagerMixin,
    FallbackLogicMixin,
    VectorManagementMixin,
    viewsets.ModelViewSet
):
    """Protocol Assistant 知識庫 ViewSet（參考 RVTGuideViewSet）"""
    
    queryset = ProtocolGuide.objects.all()
    serializer_class = ProtocolGuideSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    # 配置 Manager
    manager_config = {
        'library_available_flag': 'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
        'manager_class': 'ProtocolGuideViewSetManager',
    }
    
    def get_serializer_class(self):
        """根據 action 選擇序列化器"""
        if self.action == 'list':
            return ProtocolGuideListSerializer
        elif self.action == 'retrieve':
            return ProtocolGuideWithImagesSerializer
        return ProtocolGuideSerializer
    
    @action(detail=False, methods=['post'])
    @method_decorator(csrf_exempt)
    def chat(self, request):
        """聊天 API（複製 RVT 邏輯）"""
        return self._execute_with_library(
            'handle_chat_request',
            request,
            fallback_method='_fallback_chat'
        )
    
    @action(detail=False, methods=['get'])
    def config(self, request):
        """配置 API"""
        return Response({
            'success': True,
            'config': {
                'app_name': 'Protocol Known Issue System',
                'system_type': 'protocol_assistant'
            }
        })
    
    def _fallback_chat(self, request):
        """降級處理（當 Library 不可用時）"""
        return Response({
            'success': False,
            'error': 'Protocol Assistant service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
```

#### 註冊路由
```python
# backend/api/urls.py
router.register(r'protocol-guides', views.ProtocolGuideViewSet)
```

## 📋 完整開發檢查清單

### 前端開發
- [ ] 在 `knowledgeBaseConfig.js` 添加配置
- [ ] 創建知識庫頁面（使用 KnowledgeBasePage）
- [ ] 創建聊天頁面（參考 RvtAssistantChatPage）
- [ ] 創建分析頁面（參考 RVTAnalyticsPage）
- [ ] 開發自定義 Hooks（useProtocolChat, useProtocolGuideData）
- [ ] 添加路由配置
- [ ] 更新導航選單

### 後端開發
- [ ] 創建 Django Model
- [ ] 創建 Serializers
- [ ] 建立 Library 模組結構
- [ ] 實現 ViewSet Manager
- [ ] 實現 API Handlers
- [ ] 實現 Search Service
- [ ] 實現 Vector Service
- [ ] 實現 Fallback Handlers
- [ ] 註冊 URL 路由
- [ ] 執行數據庫遷移

### AI 整合
- [ ] 配置 Dify 應用
- [ ] 設定 RAG 知識庫
- [ ] 配置提示詞模板
- [ ] 測試 AI 回應品質
- [ ] 配置錯誤處理

### 分析系統
- [ ] 實現問題分類器
- [ ] 實現滿意度分析
- [ ] 實現統計管理
- [ ] 創建分析 API
- [ ] 開發前端圖表

### 測試
- [ ] API 端點測試
- [ ] 前端功能測試
- [ ] AI 回應測試
- [ ] 效能測試
- [ ] 用戶體驗測試

## 🎨 UI/UX 標準（遵循 Ant Design）

### 必須使用的組件
```javascript
import {
  Card, Table, Button, Space, Typography, Tag, message,
  Input, Select, Row, Col, Modal, Form, Tooltip, Drawer,
  notification
} from 'antd';
```

### 配色標準
```javascript
const colors = {
  primary: '#1890ff',      // 主色調
  success: '#52c41a',      // 成功狀態
  warning: '#faad14',      // 警告狀態
  error: '#ff4d4f',        // 錯誤狀態
  info: '#1890ff',         // 資訊狀態
};
```

### 間距標準
- 頁面邊距：`24px`
- 組件間距：`16px`
- 卡片內邊距：`24px`
- 表單項間距：`16px`

## 📊 資料庫設計標準

### 知識庫主表
```sql
CREATE TABLE [assistant_name]_guide (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id)
);
```

### 圖片關聯表（如需要）
```sql
CREATE TABLE [assistant_name]_images (
    id SERIAL PRIMARY KEY,
    guide_id INTEGER REFERENCES [assistant_name]_guide(id) ON DELETE CASCADE,
    image BYTEA,
    filename VARCHAR(255),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 對話記錄（共用表）
```sql
-- chat_conversations 表已存在，只需指定 system_type
system_type = 'protocol_assistant'  -- 或其他 assistant 類型
```

### 向量嵌入（共用表）
```sql
-- document_embeddings_1024 表已存在，使用 source_type 區分
source_type = 'protocol_guide'  -- 對應的知識庫類型
```

## 🔧 Dify 配置標準

### 配置文件位置
```python
# library/config/dify_app_configs.py

DIFY_APPS['protocol-assistant'] = DifyAppConfig(
    app_name="Protocol Known Issue System",
    api_key="app-xxxxxxxxxxxxx",           # 從 Dify 獲取
    api_url="http://10.10.172.37/v1/chat-messages",
    knowledge_base_id="protocol_database",  # 對應的知識庫 ID
    system_type="protocol_assistant",
    description="Protocol Assistant for debugging protocol issues",
    max_tokens=2000,
    temperature=0.7,
)
```

### 創建配置輔助函數
```python
# library/config/dify_app_configs.py

def create_protocol_chat_client():
    """創建 Protocol Assistant 聊天客戶端"""
    config = DIFY_APPS.get('protocol-assistant')
    if not config:
        raise ValueError("Protocol Assistant 配置不存在")
    
    return DifyRequestManager(
        api_key=config.api_key,
        api_url=config.api_url,
        app_name=config.app_name
    )
```

## 📈 效能優化建議

### 前端優化
1. **使用 React.memo** 避免不必要的重新渲染
2. **使用 useMemo 和 useCallback** 優化 Hooks
3. **列表虛擬化** 使用 `rc-virtual-list` 處理大列表
4. **圖片懶加載** 優化圖片載入

### 後端優化
1. **查詢優化** 使用 `select_related` 和 `prefetch_related`
2. **向量索引** 確保 pgvector 索引正確建立
3. **快取機制** 使用 Django Cache Framework
4. **批次處理** 大量資料處理使用批次操作

### 資料庫優化
1. **建立適當索引**
   ```sql
   CREATE INDEX idx_title ON protocol_guide(title);
   CREATE INDEX idx_created_at ON protocol_guide(created_at DESC);
   ```
2. **向量索引優化**
   ```sql
   CREATE INDEX ON document_embeddings_1024 
   USING ivfflat (embedding vector_cosine_ops)
   WITH (lists = 100);
   ```

## 🔍 故障排查指南

### 常見問題

#### 1. Library 載入失敗
```python
# 檢查 __init__.py 是否正確導出
PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True

# 檢查 ViewSet 配置
manager_config = {
    'library_available_flag': 'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
    'manager_class': 'ProtocolGuideViewSetManager',
}
```

#### 2. 前端配置未生效
```javascript
// 確認配置鍵名稱一致
const config = knowledgeBaseConfigs['protocol-assistant'];

// 檢查配置物件是否完整
console.log('Config:', config);
```

#### 3. API 403 錯誤
```python
# 檢查權限設定
permission_classes = [permissions.IsAuthenticated]

# 檢查 CSRF 豁免（聊天 API）
@method_decorator(csrf_exempt)
def chat(self, request):
    pass
```

#### 4. 向量搜尋無結果
```python
# 確認向量已生成
python manage.py generate_protocol_embeddings

# 檢查向量維度一致性
embedding_dim = 1024  # 確保與模型一致
```

## 📚 參考資源

### 核心檔案參考
- **前端範例**：
  - `frontend/src/pages/RvtAssistantChatPage.js`
  - `frontend/src/pages/RvtGuidePage/index.js`
  - `frontend/src/config/knowledgeBaseConfig.js`
  
- **後端範例**：
  - `backend/api/views/viewsets/knowledge_viewsets.py`
  - `backend/library/rvt_guide/`
  - `backend/api/models.py`

### 文檔參考
- `/docs/development/ui-component-guidelines.md` - UI 規範
- `/docs/architecture/rvt-assistant-database-vector-architecture.md` - 資料庫架構
- `/docs/ai-integration/dify-app-config-usage.md` - Dify 配置

### 測試工具
- `tests/rvt_assistant_diagnostic.py` - 診斷工具範例
- `tests/test_dify_integration/` - Dify 整合測試

## 🎯 成功標準

一個完整的 Assistant 應該包含：

✅ **前端完整性**
- 聊天介面流暢，支援即時回應
- 知識庫管理功能完善
- 分析儀表板數據準確
- UI/UX 符合 Ant Design 規範

✅ **後端完整性**
- RESTful API 完整實現
- Library 模組化設計清晰
- 錯誤處理和降級機制完善
- 向量搜尋功能正常

✅ **AI 整合**
- Dify 整合配置正確
- RAG 檢索效果良好
- 回應品質符合預期

✅ **分析功能**
- 問題分類準確
- 統計數據完整
- 趨勢分析有意義

✅ **效能表現**
- 回應時間 < 3 秒
- 列表載入 < 1 秒
- 向量搜尋 < 500ms

## 🚀 快速命令參考

```bash
# 建立資料庫遷移
python manage.py makemigrations

# 執行遷移
python manage.py migrate

# 生成向量嵌入
python manage.py generate_protocol_embeddings

# 測試 API
curl -X POST http://localhost/api/protocol-guides/chat/ \
  -H "Content-Type: application/json" \
  -d '{"message": "測試訊息"}'

# 檢查 Library 載入狀態
docker exec ai-django python manage.py shell -c \
  "from library.protocol_guide import PROTOCOL_GUIDE_LIBRARY_AVAILABLE; \
   print(f'Library Available: {PROTOCOL_GUIDE_LIBRARY_AVAILABLE}')"
```

## 💡 最佳實踐

1. **先配置，後編碼** - 充分利用配置驅動架構
2. **複製參考，逐步調整** - 不要從零開始
3. **測試驅動** - 每完成一個功能就測試
4. **文檔同步** - 開發過程中同步更新文檔
5. **權限優先** - 先考慮權限和安全性
6. **效能意識** - 從一開始就考慮效能優化
7. **錯誤處理** - 完善的錯誤處理和用戶提示

---

**🎉 使用本指南，您可以在 1-2 天內完成一個功能完整的 AI Assistant！**

**建立日期**: 2025-10-18  
**維護者**: AI Platform Team  
**版本**: v1.0
