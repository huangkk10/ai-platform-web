# RVT Assistant — 檔案對照表

## 核心檔案（修改最多）

| 檔案路徑 | 類別/函數 | 職責 |
|---------|----------|------|
| `library/rvt_guide/smart_search_router.py` | `SmartSearchRouter` | 路由入口，決定 Mode A/B |
| `library/rvt_guide/keyword_triggered_handler.py` | `KeywordTriggeredSearchHandler` | Mode A 全文搜尋 |
| `library/rvt_guide/two_tier_handler.py` | `TwoTierSearchHandler` | Mode B 兩階段搜尋 |
| `library/rvt_guide/api_handlers.py` | `RVTGuideAPIHandler` | 聊天 API 入口，覆寫 handle_chat_api |
| `library/common/query_analysis/keyword_detector.py` | `FULL_DOCUMENT_KEYWORDS` | Mode A 觸發關鍵字列表（~50 個） |
| `library/common/ai_response/uncertainty_detector.py` | `UNCERTAINTY_KEYWORDS` | Fallback 判斷關鍵字 |

## Django 後端

| 檔案路徑 | 職責 |
|---------|------|
| `backend/api/views/split_views.py` | `rvt_guide_chat` / `rvt_guide_config` view 函數入口 |
| `backend/api/views/dify_knowledge_views.py` | Dify callback，`dify_rvt_guide_search()` + `dify_knowledge_search()` |
| `backend/api/models.py` → `class RVTGuide` (line ~635) | RVT 文件 DB model（table: `rvt_guide`） |
| `backend/api/models.py` → `class ContentImage` (line ~819) | 圖片 DB model，`rvt_guide` FK |
| `backend/api/models.py` → `class UserPermission` (line ~43) | `web_rvt_assistant` 存取權限欄位 |
| `backend/api/urls.py` | URL routing |

## 設定/配置

| 檔案路徑 | 職責 |
|---------|------|
| `library/config/dify_config_manager.py` | RVT Dify API Key、環境（dev/prod）管理 |
| `library/config/dify_config.py` | Dify base URL、AI PC IP |
| `config/settings.yaml` | `ai_pc_ip`（`10.253.43.244`） |
| `docker-compose.yml` | `DIFY_ENV=development/production` |

## 搜尋/向量

| 檔案路徑 | 類別 | 職責 |
|---------|------|------|
| `library/rvt_guide/search_service.py` | `RVTGuideSearchService` | 向量搜尋主服務（繼承 Base） |
| `library/rvt_guide/vector_service.py` | `RVTGuideVectorService` | 向量產生/儲存 |
| `library/common/knowledge_base/base_search_service.py` | `BaseKnowledgeBaseSearchService` | [IMG:N] 提取、共用搜尋邏輯 |
| `library/common/knowledge_base/section_search_service.py` | `SectionSearchService` | 段落搜尋（多向量權重 70%/30%） |
| `library/dify_knowledge/__init__.py` | `DifyKnowledgeSearchHandler` | knowledge_id 標準化、搜尋路由 |

## Dify 整合

| 檔案路徑 | 職責 |
|---------|------|
| `library/dify_integration/chat_client.py` | `DifyChatClient.chat()` 發送請求到 Dify |
| `library/dify_integration/request_manager.py` | `DifyRequestManager`（feedback 等） |

## 序列化器（RVT 特有模組化設計）

| 檔案路徑 | 類別 | 用途 |
|---------|------|------|
| `library/rvt_guide/serializers/base.py` | `RVTGuideSerializer` | 完整欄位，用於 create/update/retrieve |
| `library/rvt_guide/serializers/list.py` | `RVTGuideListSerializer` | 輕量，僅 id/title/timestamps，用於 list |
| `library/rvt_guide/serializers/with_images.py` | `RVTGuideWithImagesSerializer` | 含 ContentImage 嵌套資料 |
| `library/common/serializers.py` | `ContentImageSerializer` | 圖片序列化（共用） |

## 降級/備用

| 檔案路徑 | 類別 | 用途 |
|---------|------|------|
| `library/rvt_guide/fallback_handlers.py` | `RVTGuideFallbackHandler` | library 初始化失敗時的降級實作 |

## 對話記錄

| 檔案路徑 | 職責 |
|---------|------|
| `library/rvt_guide/api_handlers.py` | `_save_conversation_to_db()` 靜態方法 |
| `backend/api/models.py` → `ConversationSession` | `chat_type='rvt_assistant_chat'` |
| `backend/api/models.py` → `ChatMessage` | 儲存 user/assistant 訊息 |

## 基礎類別（通用框架）

| 基礎類別 | RVT 子類別 | 所在檔案 |
|---------|-----------|---------|
| `BaseKnowledgeBaseAPIHandler` | `RVTGuideAPIHandler` | `library/rvt_guide/api_handlers.py` |
| `BaseKnowledgeBaseSearchService` | `RVTGuideSearchService` | `library/rvt_guide/search_service.py` |
| `BaseKnowledgeBaseVectorService` | `RVTGuideVectorService` | `library/rvt_guide/vector_service.py` |
| `BaseViewSetManager` | `RVTGuideViewSetManager` | `library/rvt_guide/viewset_manager.py` |

## URL 對照

| URL | 方法 | 視圖函數 | 用途 |
|-----|------|---------|------|
| `/api/rvt-guide/chat/` | POST | `rvt_guide_chat` | 前端聊天入口 |
| `/api/rvt-guide/config/` | GET | `rvt_guide_config` | 取得 Dify 設定資訊 |
| `/api/dify/knowledge/retrieval/` | POST | `dify_knowledge_search` | Dify 外部知識庫 callback（通用） |
| `/api/dify/rvt/knowledge/retrieval/` | POST | `dify_rvt_guide_search` | RVT 專用 callback |
| `/api/dify/rvt-guide/retrieval/` | POST | `dify_knowledge_search` | 舊版相容 callback |
| `/api/rvt-guides/` | GET/POST | `RVTGuideViewSet` | CRUD 管理文件 |
| `/api/rvt-analytics/overview/` | GET | — | 使用統計 |

## 管理指令

| 指令檔案 | 用途 |
|---------|------|
| `backend/api/management/commands/create_rvt_guide_data.py` | 建立測試資料 |
| `backend/api/management/commands/generate_rvt_embeddings.py` | 產生向量 embeddings |
| `backend/api/management/commands/generate_rvt_embeddings_1536.py` | 1536 維向量版本 |
