# 🤖 AI 助手專用：創建新 Assistant 的指引

> **目標受眾**: GitHub Copilot、AI 編碼助手  
> **目的**: 提供清晰的步驟指引，協助 AI 快速理解並創建新的 Assistant 模組

## 🎯 核心概念

**RVT Assistant = 標準範本**

所有新的 AI Assistant（如 Protocol Assistant、QA Assistant）都應該：
1. 複製 RVT Assistant 的架構
2. 調整名稱和配置
3. 保持相同的模組化結構

## 📂 關鍵檔案位置地圖

```
必讀文檔：
├── /docs/development/assistant-template-guide.md        ← 完整開發指南
├── /docs/development/assistant-template-quick-start.md  ← 快速開始
└── /.github/chatmodes/ai_web.chatmode.md                ← AI 指令（搜尋「AI Assistant」）

參考代碼：
├── 前端
│   ├── /frontend/src/pages/RvtAssistantChatPage.js      ← 聊天頁面範例
│   ├── /frontend/src/pages/RvtGuidePage/index.js        ← 知識庫頁面範例（僅 20 行）
│   ├── /frontend/src/config/knowledgeBaseConfig.js      ← 配置中心
│   └── /frontend/src/hooks/useRvtChat.js                ← API 通訊 Hook
│
├── 後端
│   ├── /backend/api/models.py                           ← Model 定義（搜尋 RVTGuide）
│   ├── /backend/api/views/viewsets/knowledge_viewsets.py ← ViewSet 範例
│   ├── /backend/library/rvt_guide/                      ← Library 模組結構
│   │   ├── __init__.py
│   │   ├── viewset_manager.py
│   │   ├── api_handlers.py
│   │   └── ...
│   └── /backend/api/urls.py                             ← 路由註冊
│
└── 配置
    └── /library/config/dify_app_configs.py              ← Dify AI 配置
```

## 🚀 AI 創建新 Assistant 的步驟模板

### 假設需求：創建 "Protocol Assistant"

#### 步驟 1: 前端配置（必需）
**檔案**: `frontend/src/config/knowledgeBaseConfig.js`
**操作**: 添加新配置
```javascript
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
  events: { reload: 'protocol-guide-reload' },
  labels: {
    pageTitle: 'Protocol Assistant 知識庫',
    createButton: '新增 Protocol Guide',
    // ... 複製 rvt-assistant 的其他 labels
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
}
```

#### 步驟 2: 前端頁面（必需）
**檔案**: `frontend/src/pages/ProtocolGuidePage/index.js`
**操作**: 創建新文件（直接複製 RvtGuidePage，僅改名稱）
```javascript
import React from 'react';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';
import GuideDetailModal from '../../components/GuideDetailModal';

const ProtocolGuidePage = () => {
  const config = knowledgeBaseConfigs['protocol-assistant'];
  return (
    <KnowledgeBasePage config={config} DetailModal={GuideDetailModal} />
  );
};

export default ProtocolGuidePage;
```

#### 步驟 3: Django Model（必需）
**檔案**: `backend/api/models.py`
**操作**: 添加新 Model（複製 RVTGuide 結構）
```python
class ProtocolGuide(models.Model):
    """Protocol Assistant 知識庫"""
    title = models.CharField(max_length=500, verbose_name='標題')
    content = models.TextField(verbose_name='內容')
    category = models.CharField(max_length=100, blank=True, null=True, verbose_name='分類')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='創建時間')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新時間')
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
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

#### 步驟 4: Serializer（必需）
**檔案**: `backend/api/serializers.py`
**操作**: 添加序列化器（複製 RVTGuide 序列化器）
```python
class ProtocolGuideSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ProtocolGuide
        fields = ['id', 'title', 'content', 'category', 'created_at', 
                  'updated_at', 'created_by', 'created_by_username']
        read_only_fields = ['created_at', 'updated_at']

class ProtocolGuideListSerializer(serializers.ModelSerializer):
    """列表用簡化序列化器"""
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = ProtocolGuide
        fields = ['id', 'title', 'category', 'created_at', 'created_by_username']
```

#### 步驟 5: ViewSet（必需）
**檔案**: `backend/api/views/viewsets/knowledge_viewsets.py`
**操作**: 添加 ViewSet（複製 RVTGuideViewSet 結構）
```python
# 先導入 Library（如果已建立）
try:
    from library.protocol_guide import (
        ProtocolGuideViewSetManager,
        PROTOCOL_GUIDE_LIBRARY_AVAILABLE
    )
except ImportError:
    ProtocolGuideViewSetManager = None
    PROTOCOL_GUIDE_LIBRARY_AVAILABLE = False

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
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProtocolGuideListSerializer
        return ProtocolGuideSerializer
    
    @action(detail=False, methods=['post'])
    @method_decorator(csrf_exempt)
    def chat(self, request):
        """聊天 API"""
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
        """降級處理"""
        return Response({
            'success': False,
            'error': 'Protocol Assistant service temporarily unavailable'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
```

#### 步驟 6: 路由註冊（必需）
**檔案**: `backend/api/urls.py`
**操作**: 註冊路由
```python
# 在 router 註冊部分添加
router.register(r'protocol-guides', views.ProtocolGuideViewSet)
```

#### 步驟 7: Library 模組（可選，進階功能需要）
**目錄**: `backend/library/protocol_guide/`
**操作**: 創建目錄結構（完全複製 rvt_guide 結構）
```
protocol_guide/
├── __init__.py                 # 導出接口
├── viewset_manager.py          # ViewSet 管理器
├── api_handlers.py             # API 處理邏輯
├── fallback_handlers.py        # 降級處理
├── search_service.py           # 搜尋服務
└── vector_service.py           # 向量服務
```

**檔案**: `backend/library/protocol_guide/__init__.py`
```python
"""Protocol Assistant Library"""

from .viewset_manager import ProtocolGuideViewSetManager
from .api_handlers import ProtocolGuideAPIHandler

PROTOCOL_GUIDE_LIBRARY_AVAILABLE = True

__all__ = [
    'ProtocolGuideViewSetManager',
    'ProtocolGuideAPIHandler',
    'PROTOCOL_GUIDE_LIBRARY_AVAILABLE',
]
```

#### 步驟 8: 資料庫遷移（必需）
**操作**: 執行遷移命令
```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 創建遷移
python manage.py makemigrations

# 執行遷移
python manage.py migrate
```

#### 步驟 9: Dify 配置（可選，AI 整合需要）
**檔案**: `library/config/dify_app_configs.py`
**操作**: 添加 Dify 應用配置
```python
DIFY_APPS['protocol-assistant'] = DifyAppConfig(
    app_name="Protocol Known Issue System",
    api_key="app-xxxxxxxxxxxxx",  # 需從 Dify 獲取
    api_url="http://10.10.172.37/v1/chat-messages",
    knowledge_base_id="protocol_database",
    system_type="protocol_assistant",
    description="Protocol Assistant for debugging protocol issues",
    max_tokens=2000,
    temperature=0.7,
)

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

## 🔍 AI 檢查清單

創建新 Assistant 時，AI 應該檢查：

### 必需檔案
- [ ] `frontend/src/config/knowledgeBaseConfig.js` - 添加配置
- [ ] `frontend/src/pages/[Name]GuidePage/index.js` - 創建頁面
- [ ] `backend/api/models.py` - 添加 Model
- [ ] `backend/api/serializers.py` - 添加 Serializer
- [ ] `backend/api/views/viewsets/knowledge_viewsets.py` - 添加 ViewSet
- [ ] `backend/api/urls.py` - 註冊路由

### 可選檔案（進階功能）
- [ ] `backend/library/[name]_guide/` - Library 模組
- [ ] `library/config/dify_app_configs.py` - Dify 配置
- [ ] `frontend/src/pages/[Name]AssistantChatPage.js` - 聊天頁面
- [ ] `frontend/src/hooks/use[Name]Chat.js` - 聊天 Hook

### 命名規則
- Model 名稱: `[Name]Guide`（如 `ProtocolGuide`）
- ViewSet 名稱: `[Name]GuideViewSet`
- Library 目錄: `library/[name]_guide/`（小寫加底線）
- 配置鍵: `'[name]-assistant'`（小寫加連字號）
- 路由: `r'[name]-guides'`
- API 端點: `/api/[name]-guides/`

### 資料庫表名
- 主表: `[name]_guide`（如 `protocol_guide`）
- 圖片表: 使用共用的 `content_images` 表
- 對話表: 使用共用的 `chat_conversations` 表

## 💡 AI 提示詞建議

當用戶要求創建新 Assistant 時，AI 可以使用：

```
我將幫您創建 [Name] Assistant，參考 RVT Assistant 的標準架構。

我將執行以下步驟：
1. 添加前端配置到 knowledgeBaseConfig.js
2. 創建前端頁面 [Name]GuidePage/index.js
3. 創建 Django Model [Name]Guide
4. 創建對應的 Serializer
5. 創建 ViewSet [Name]GuideViewSet
6. 註冊 API 路由
7. 生成資料庫遷移指令

請確認是否需要以下進階功能：
- [ ] AI 聊天功能（需要 Dify 配置）
- [ ] 向量搜尋（需要 pgvector）
- [ ] 分析儀表板
- [ ] 圖片上傳功能
```

## 🎯 成功標準

AI 完成創建後，應該能夠：
- [ ] 前端可以訪問知識庫列表頁面
- [ ] 可以創建、編輯、刪除記錄
- [ ] API 端點正常回應
- [ ] 權限控制正確
- [ ] 無明顯錯誤或警告

## 📚 快速參考連結

**立即開始**: `/docs/development/assistant-template-quick-start.md`  
**完整指南**: `/docs/development/assistant-template-guide.md`  
**架構說明**: `/.github/chatmodes/ai_web.chatmode.md`（搜尋「AI Assistant」）

---

**🎉 使用此指引，AI 可以在 10-15 分鐘內生成完整的 Assistant 基礎代碼！**

**維護日期**: 2025-10-18  
**目標用戶**: GitHub Copilot, AI Coding Assistants  
**版本**: v1.0
