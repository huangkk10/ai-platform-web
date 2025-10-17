# 🎯 AI Assistant 標準範本快速參考

## 📘 一句話總結
**使用 RVT Assistant 作為標準範本，通過配置驅動模式快速創建新的 AI Assistant 功能。**

## 🚀 5 分鐘快速開始

### 1. 添加配置（2 分鐘）
```javascript
// frontend/src/config/knowledgeBaseConfig.js
'your-assistant': {
  apiEndpoint: '/api/your-guides/',
  routes: { list, create, edit },
  labels: { pageTitle, createButton, ... },
  permissions: { canDelete, canEdit, canView }
}
```

### 2. 創建前端頁面（1 分鐘）
```javascript
// frontend/src/pages/YourGuidePage/index.js
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import KnowledgeBasePage from '../../components/KnowledgeBase/KnowledgeBasePage';

const YourGuidePage = () => (
  <KnowledgeBasePage config={knowledgeBaseConfigs['your-assistant']} />
);
```

### 3. 創建 Model（1 分鐘）
```python
# backend/api/models.py
class YourGuide(models.Model):
    title = models.CharField(max_length=500)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    # ... 參考 RVTGuide
```

### 4. 創建 ViewSet（1 分鐘）
```python
# backend/api/views/viewsets/knowledge_viewsets.py
class YourGuideViewSet(LibraryManagerMixin, viewsets.ModelViewSet):
    queryset = YourGuide.objects.all()
    # ... 複製 RVTGuideViewSet 結構
```

### 5. 註冊路由（30 秒）
```python
# backend/api/urls.py
router.register(r'your-guides', views.YourGuideViewSet)
```

## 📋 核心文件清單

### 必讀文檔
- **完整指南**: `/docs/development/assistant-template-guide.md`
- **架構說明**: `.github/chatmodes/ai_web.chatmode.md`（搜尋「AI Assistant 標準範本架構」）

### 參考代碼
**前端**：
- `frontend/src/pages/RvtAssistantChatPage.js` - 聊天頁面
- `frontend/src/pages/RvtGuidePage/index.js` - 知識庫頁面（20 行實現）
- `frontend/src/config/knowledgeBaseConfig.js` - 配置中心

**後端**：
- `backend/api/views/viewsets/knowledge_viewsets.py` - ViewSet 範例
- `backend/library/rvt_guide/` - Library 模組結構
- `backend/api/models.py` - Model 定義

## 🎯 架構全景（簡化版）

```
前端 (React)
├── 配置 → knowledgeBaseConfig.js
├── 頁面 → YourGuidePage/index.js (20 行)
└── Hook → useYourChat.js (可選)

後端 (Django)
├── Model → YourGuide
├── ViewSet → YourGuideViewSet (使用 Mixins)
├── Library → library/your_guide/ (模組化邏輯)
└── 路由 → api/urls.py

資料庫 (PostgreSQL)
├── your_guide (主表)
├── content_images (圖片，可選)
└── document_embeddings_1024 (向量)

AI 整合 (Dify)
└── 配置 → library/config/dify_app_configs.py
```

## ✅ 功能檢查清單

### 基礎功能（必需）
- [ ] 知識庫 CRUD
- [ ] 配置驅動頁面
- [ ] 前後端 API 整合
- [ ] 權限控制

### 進階功能（推薦）
- [ ] AI 聊天介面
- [ ] 向量搜尋
- [ ] 分析儀表板
- [ ] 圖片上傳

### 優化功能（可選）
- [ ] 快取機制
- [ ] 批次操作
- [ ] 導出功能
- [ ] 高級篩選

## 🔧 常用命令

```bash
# 資料庫遷移
python manage.py makemigrations
python manage.py migrate

# 生成向量
python manage.py generate_your_embeddings

# 檢查 Library
docker exec ai-django python manage.py shell -c \
  "from library.your_guide import YOUR_GUIDE_LIBRARY_AVAILABLE; \
   print(YOUR_GUIDE_LIBRARY_AVAILABLE)"

# 測試 API
curl -X GET http://localhost/api/your-guides/ \
  -H "Content-Type: application/json"
```

## 💡 關鍵技巧

1. **配置優先** - 80% 的工作通過配置完成
2. **複製調整** - 複製 RVT Assistant 代碼並調整名稱
3. **Mixins 架構** - 使用 Mixins 實現可重用邏輯
4. **測試驅動** - 每完成一個功能就測試
5. **文檔同步** - 開發過程中同步更新文檔

## 🆘 故障排查

### 前端配置未生效
```javascript
// 檢查配置鍵名稱
console.log(knowledgeBaseConfigs['your-assistant']);
```

### Library 載入失敗
```python
# 檢查 __init__.py
YOUR_GUIDE_LIBRARY_AVAILABLE = True
```

### API 403 錯誤
```python
# 檢查權限
permission_classes = [permissions.IsAuthenticated]
```

## 📞 獲取幫助

- **完整指南**: `/docs/development/assistant-template-guide.md`
- **架構文檔**: `/docs/architecture/rvt-assistant-database-vector-architecture.md`
- **配置指南**: `/docs/ai-integration/dify-app-config-usage.md`

---

**⏱️ 預估開發時間**：
- 基礎功能：4-6 小時
- 完整功能：1-2 天
- 優化完善：額外 1-2 天

**🎉 祝您開發順利！**
