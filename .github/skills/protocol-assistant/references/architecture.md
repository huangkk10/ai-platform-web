# Protocol Assistant — 系統架構

## 整體架構圖

```
[前端 React]
  POST /api/protocol-assistant/chat/
      ↓
[Django ViewSet]
  backend/api/views/viewsets/protocol_assistant_viewset.py
  class ProtocolAssistantViewSet
      ↓
[API Handler]
  library/protocol_guide/api_handlers.py
  class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler)
  → handle_chat_api(request)
      ↓
[智能搜尋路由器]
  library/protocol_guide/smart_search_router.py
  class SmartSearchRouter
  → handle_smart_search(user_query, conversation_id, user_id)
      ↓
  ┌─────────────────────────────────────────────┐
  │ contains_full_document_keywords(query)?      │
  │ library/common/query_analysis/               │
  │   keyword_detector.py                        │
  └─────────┬───────────────────────┬───────────┘
            │ True (含關鍵字)        │ False (一般問題)
            ↓                       ↓
       [Mode A]                 [Mode B]
  keyword_triggered_handler   two_tier_handler.py
  .py                        class TwoTierSearchHandler
  class ProtocolGuide         → Stage 1: 段落搜尋
  KeywordTriggeredHandler     → Stage 2: 全文搜尋(+__FULL_SEARCH__)
            ↓                       ↓
       [Dify Chat API]        [Dify Chat API]
  http://10.253.43.244/       http://10.253.43.244/
  v1/chat-messages            v1/chat-messages
            ↓                       ↓
       [Dify 外部知識庫回調]
  POST /api/dify/knowledge/retrieval/
  backend/api/views/dify_knowledge_views.py
  → dify_knowledge_search()
  → knowledge_id='protocol_guide_database' → DB table 'protocol_guide'
  → __FULL_SEARCH__ in query → search_mode='document_only'(Stage2)
            ↓
       [向量搜尋]
  library/protocol_guide/search_service.py
  class ProtocolGuideSearchService
  → PostgreSQL + pgvector
            ↓
       [回傳結果給 Dify → Dify 生成回答 → 回傳 answer]
            ↓
  is_uncertain_response(answer)?
  library/common/ai_response/uncertainty_detector.py
  → True: fallback（原始回答 + 提示語）
  → False: 正常回傳
            ↓
  _record_conversation()
  library/conversation_management/
            ↓
[前端顯示回答]
```

---

## 分層說明

### Layer 1 — Django API 入口
**檔案**: `backend/api/views/viewsets/protocol_assistant_viewset.py`

- URL: `POST /api/protocol-assistant/chat/`
- 權限: `AllowAny`（允許未登入）
- 呼叫 `ProtocolGuideAPIHandler.handle_chat_api(request)`

---

### Layer 2 — API Handler（繼承 Base）
**檔案**: `library/protocol_guide/api_handlers.py`

```python
class ProtocolGuideAPIHandler(BaseKnowledgeBaseAPIHandler):
    knowledge_id = 'protocol_guide_db'
    config_key = 'protocol_guide'
    source_table = 'protocol_guide'
    model_class = ProtocolGuide
```

覆寫 `handle_chat_api()` → 使用 `SmartSearchRouter`

---

### Layer 3 — 智能搜尋路由器
**檔案**: `library/protocol_guide/smart_search_router.py`

- 偵測關鍵字 → 路由到 Mode A 或 Mode B
- 呼叫對應 handler
- 呼叫 `_record_conversation()` 記錄對話到 DB

---

### Layer 4 — 搜尋模式處理器

| 模式 | 檔案 | 觸發條件 |
|------|------|---------|
| Mode A | `keyword_triggered_handler.py` | 問題含全文關鍵字 |
| Mode B Stage 1 | `two_tier_handler.py` | 一般問題，先段落搜尋 |
| Mode B Stage 2 | `two_tier_handler.py` | Stage 1 不確定，加 `__FULL_SEARCH__` 重試 |
| Fallback | `two_tier_handler.py` | Stage 2 仍不確定，回傳提示語 |

---

### Layer 5 — Dify 整合
**檔案**: `library/dify_integration/chat_client.py`

- `DifyChatClient.chat()` → POST `http://10.253.43.244/v1/chat-messages`
- Dify 接收查詢後，callback → Django 外部知識庫 API
- Django 做向量搜尋，回傳 records → Dify 生成回答

---

### Layer 6 — 外部知識庫 API（Dify Callback）
**檔案**: `backend/api/views/dify_knowledge_views.py`

- URL: `POST /api/dify/knowledge/retrieval/`
- 接收 Dify 傳來的 `knowledge_id`, `query`, `retrieval_setting`
- `knowledge_id='protocol_guide_database'` → 搜尋 `protocol_guide` table
- 偵測 `__FULL_SEARCH__` → `search_mode='document_only'`（全文）

---

### Layer 7 — 向量搜尋
**檔案**: `library/protocol_guide/search_service.py`

- 繼承 `BaseKnowledgeBaseSearchService`
- PostgreSQL + pgvector 向量相似度搜尋
- DB table: `protocol_guide`（model: `backend/api/models.py ProtocolGuide`）

---

## ProtocolGuide DB Model

```python
class ProtocolGuide(models.Model):
    title   = CharField(max_length=300)   # 文檔標題
    content = TextField()                  # 文檔內容（Markdown）
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'protocol_guide'
```

---

## Dify 設定

| 項目 | Dev | Prod |
|------|-----|------|
| API Key | `app-4TbH1O7NkpOFsnxGEF3FLyqd` | `app-MgZZOhADkEmdUrj2DtQLJ23G` |
| Dify App Name | `Protocol_Guide_dev` | `Protocol_Guide` |
| 知識庫名稱 | `protocol_guide_knowledge_database_dev` | `protocol_guide_knowledge_database` |
| 知識庫類型 | 外部（External） | 外部（External） |
| 外部 API URL | `http://10.10.172.127/api/dify/knowledge/retrieval/` | `http://10.10.172.127/api/dify/knowledge/retrieval/` |
| Reranking | 關閉 | 關閉 |
| LLM | gemma3:27b | gemma3:27b |

環境切換設定（`docker-compose.yml`）：
```yaml
DIFY_ENV=development   # → 使用 DEV_API_KEYS
DIFY_ENV=production    # → 使用 PROD_API_KEYS
```
