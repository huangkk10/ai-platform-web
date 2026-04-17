# RVT Assistant — 系統架構

## 整體架構（7 層）

```
前端 React
    ↓  POST /api/rvt-guide/chat/
Django View (split_views.py → rvt_guide_chat)
    ↓
RVTGuideAPIHandler.handle_chat_api()
    ↓
SmartSearchRouter.handle_smart_search()
    ↓
  [Mode A] KeywordTriggeredSearchHandler     [Mode B] TwoTierSearchHandler
      ↓                                             ↓  Stage 1
  DifyChatClient.chat()                      DifyChatClient.chat()
      ↓ Dify callback                              ↓ Dify callback(若需 Stage 2 也會再呼叫)
  POST /api/dify/knowledge/retrieval/        POST /api/dify/knowledge/retrieval/
      ↓                                             ↓
  DifyKnowledgeSearchHandler                 DifyKnowledgeSearchHandler
      ↓  knowledge_id='rvt_guide_db_dev'
  RVTGuideSearchService (pgvector)
      ↓ 返回 2 筆結果
  Dify LLM 生成回答
      ↓ 回到 Django
  is_uncertain_response() 判斷
      ↓
  Response + 儲存 ConversationSession
```

## DB Models

### `RVTGuide` (`backend/api/models.py` line ~635)
```python
class RVTGuide(models.Model):
    title   = CharField(max_length=300)   # 文件標題
    content = TextField()                  # 文件內容（含 [IMG:N] 標記）
    created_at, updated_at                 # 時間戳
    # db_table = 'rvt_guide'
    
    def get_active_images()    # 取得啟用圖片
    def get_primary_image()    # 取得主要圖片
```

### `ContentImage` (`backend/api/models.py` line ~819)
**RVT 獨有** — Protocol Assistant 沒有此功能

```python
class ContentImage(models.Model):
    rvt_guide      = ForeignKey(RVTGuide, related_name='images')  # 直接關聯
    content_type   = ForeignKey(ContentType)  # GenericForeignKey 支援
    object_id      = PositiveIntegerField()
    
    # 圖片檔案
    filename           = CharField(max_length=255)
    content_type_mime  = CharField(max_length=100)  # MIME type
    file_size          = IntegerField()
    image_data         = BinaryField()              # 圖片二進位資料存 DB
    
    # 排序
    display_order = IntegerField(default=1)
    is_primary    = BooleanField(default=False)
    is_active     = BooleanField(default=True)
```

### 圖片在 content 中的格式
文件內容中使用 `[IMG:N]` 做圖片佔位符，N 為 ContentImage.id：
```
使用者可透過此功能查看板數量，如下圖：[IMG:14] board_count.png
```
前端收到後依 ID 從 `/api/rvt-guides/{id}/images/{img_id}/` 取得圖片。

### `UserPermission` (`backend/api/models.py` line ~43)
```python
web_rvt_assistant = BooleanField(default=False)  # Web RVT Assistant 存取權
kb_rvt_assistant  = BooleanField(default=False)  # KB RVT Assistant 存取權
```

### `ConversationSession` + `ChatMessage`
對話記錄模型，`chat_type='rvt_assistant_chat'`

---

## Dify 設定

| 環境 | App 名稱 | API Key | knowledge_id |
|------|----------|---------|--------------|
| Development | RVT_Guide_dev | `app-xDXNUVPnPkP1We12RonI6Jk6` | `rvt_guide_db_dev` |
| Production | RVT_Guide | `app-Lp4mlfIWHqMWPHTlzF9ywT4F` | `rvt_guide_db` |

- 切換依據：`docker-compose.yml` 的 `DIFY_ENV=development/production`
- 設定位置：`library/config/dify_config_manager.py`
- **重要**：兩個 app 都必須關閉 Reranking（否則 HTTP 400 錯誤）
- 外部知識庫 URL：`http://10.10.172.127/api/dify/knowledge/retrieval/`

---

## 搜尋系統

### `SmartSearchConfig`（與 Protocol 共用設定，在 ThresholdManager 中管理）

RVT 使用 `rvt_assistant` 作為 assistant_type，搜尋參數由 `ThresholdManager` 動態管理：

- Stage 1 threshold: `0.8`
- Stage 1 top_k: `3`
- 搜尋模式: `auto`（優先段落搜尋）

### 向量搜尋系統

`RVTGuideSearchService` 繼承 `BaseKnowledgeBaseSearchService`：
- 使用 pgvector 進行語意搜尋
- `SectionSearchService` 支援段落級搜尋（多向量）
- Stage 1 段落搜尋權重：標題 70% / 內容 30%
- 備用（向量失敗時）：關鍵字搜尋

### knowledge_id 標準化（`library/dify_knowledge/__init__.py`）
```python
'rvt_guide_db'      → 'rvt_guide'
'rvt_guide_db_dev'  → 'rvt_guide'   # Dev 環境
'rvt_guide_db_prod' → 'rvt_guide'   # Prod 環境
'rvt_guide'         → 'rvt_guide'
'rvt-guide'         → 'rvt_guide'
'rvt_user_guide'    → 'rvt_guide'
'rvt_assistant_dev' → 'rvt_guide'
```

---

## 模組依賴圖

```
library/rvt_guide/
├── api_handlers.py           ← 主入口（繼承 BaseKnowledgeBaseAPIHandler）
├── smart_search_router.py    ← 路由器（Mode A/B 決策）
├── keyword_triggered_handler.py  ← Mode A
├── two_tier_handler.py       ← Mode B
├── search_service.py         ← 向量搜尋（繼承 Base）
├── vector_service.py         ← 向量產生/儲存
├── viewset_manager.py        ← CRUD 管理
├── fallback_handlers.py      ← 降級備用實作
└── serializers/
    ├── base.py               ← 完整欄位序列化
    ├── list.py               ← 輕量列表序列化
    └── with_images.py        ← 含 ContentImage 序列化

library/common/               ← 共用模組（RVT & Protocol 共用）
├── knowledge_base/
│   ├── base_api_handler.py
│   ├── base_search_service.py    ← [IMG:N] 提取邏輯在此
│   └── section_search_service.py
├── query_analysis/
│   └── keyword_detector.py   ← FULL_DOCUMENT_KEYWORDS
└── ai_response/
    └── uncertainty_detector.py ← is_uncertain_response()
```

---

## 與 Protocol Assistant 的架構差異

| 特性 | RVT Assistant | Protocol Assistant |
|------|---------------|--------------------|
| 圖片系統 | ✅ ContentImage + [IMG:N] | ❌ 無 |
| serializers | 獨立模組化（3 個序列化器） | 單一序列化器 |
| fallback_handlers | 有獨立降級實作 | 無（直接錯誤） |
| 搜尋 config | ThresholdManager 動態管理 | SmartSearchConfig dataclass |
| 外部 KB knowledge_id | `rvt_guide_db_dev` / `rvt_guide_db` | `protocol_guide_database` |
| content 欄位差異 | 含 [IMG:N] 佔位符 | 純文字 |
