# Protocol Assistant — 檔案對照表

## 核心檔案（修改最多）

| 檔案路徑 | 類別/函數 | 職責 |
|---------|----------|------|
| `library/protocol_guide/smart_search_router.py` | `SmartSearchRouter` | 路由入口，決定 Mode A/B |
| `library/protocol_guide/keyword_triggered_handler.py` | `ProtocolGuideKeywordTriggeredHandler` | Mode A 全文搜尋 |
| `library/protocol_guide/two_tier_handler.py` | `TwoTierSearchHandler` | Mode B 兩階段搜尋 |
| `library/protocol_guide/api_handlers.py` | `ProtocolGuideAPIHandler` | API 處理（覆寫 handle_chat_api） |
| `library/common/query_analysis/keyword_detector.py` | `FULL_DOCUMENT_KEYWORDS` | 關鍵字列表（Mode A 觸發條件） |
| `library/common/ai_response/uncertainty_detector.py` | `UNCERTAINTY_KEYWORDS` | 不確定偵測關鍵字 |
| `library/protocol_guide/smart_search_config.py` | `SmartSearchConfig` | 搜尋參數設定（top_k, threshold...） |

## Django 後端

| 檔案路徑 | 職責 |
|---------|------|
| `backend/api/views/viewsets/protocol_assistant_viewset.py` | URL 入口 ViewSet |
| `backend/api/views/dify_knowledge_views.py` | Dify callback API，knowledge_id 路由 |
| `backend/api/models.py` → `class ProtocolGuide` | DB model（table: `protocol_guide`） |
| `backend/api/urls.py` | URL routing 設定 |

## 設定/配置

| 檔案路徑 | 職責 |
|---------|------|
| `library/config/dify_config_manager.py` | Dify API Key、環境（dev/prod）管理 |
| `library/config/dify_config.py` | Dify base URL、AI PC IP |
| `config/settings.yaml` | `ai_pc_ip`（Dify IP）設定 |
| `docker-compose.yml` | `DIFY_ENV=development/production` |

## 搜尋/向量

| 檔案路徑 | 類別 | 職責 |
|---------|------|------|
| `library/protocol_guide/search_service.py` | `ProtocolGuideSearchService` | 向量搜尋（繼承 Base） |
| `library/protocol_guide/vector_service.py` | `ProtocolGuideVectorService` | 向量生成/儲存 |
| `library/common/knowledge_base/base_search_service.py` | `BaseKnowledgeBaseSearchService` | 向量搜尋基類 |
| `library/common/knowledge_base/vector_search_helper.py` | — | pgvector 搜尋工具 |

## Dify 整合

| 檔案路徑 | 職責 |
|---------|------|
| `library/dify_integration/chat_client.py` | `DifyChatClient.chat()` 發送聊天請求 |
| `library/dify_integration/request_manager.py` | `DifyRequestManager`（feedback 等） |
| `library/dify_knowledge/__init__.py` | knowledge_id → search function 映射 |

## 對話管理

| 檔案路徑 | 職責 |
|---------|------|
| `library/conversation_management/conversation_recorder.py` | 記錄對話到 DB |
| `library/conversation_management/convenience_functions.py` | `record_complete_exchange()` |

## 基礎類別（通用框架）

| 檔案路徑 | 類別 | Protocol Guide 子類別 |
|---------|------|-------------------| 
| `library/common/knowledge_base/base_api_handler.py` | `BaseKnowledgeBaseAPIHandler` | `ProtocolGuideAPIHandler` |
| `library/common/knowledge_base/base_search_service.py` | `BaseKnowledgeBaseSearchService` | `ProtocolGuideSearchService` |
| `library/common/knowledge_base/base_vector_service.py` | `BaseKnowledgeBaseVectorService` | `ProtocolGuideVectorService` |
| `library/common/knowledge_base/base_viewset_manager.py` | `BaseViewSetManager` | `ProtocolGuideViewSetManager` |

## URL 對照

| URL | 方法 | 檔案 | 用途 |
|-----|------|------|------|
| `/api/protocol-assistant/chat/` | POST | `protocol_assistant_viewset.py` | 前端聊天入口 |
| `/api/dify/knowledge/retrieval/` | POST | `dify_knowledge_views.py` | Dify callback（外部知識庫） |
| `/api/protocol-guide/chat/` | POST | `split_views.py` | 舊版聊天入口 |
| `/api/protocol-guide/knowledge/retrieval/` | POST | `dify_knowledge_views.py` | 舊版 Dify callback |
| `/api/protocol-analytics/overview/` | GET | — | 使用統計 |

## 測試檔案

| 檔案路徑 | 測試項目 |
|---------|---------|
| `library/protocol_guide/test_smart_router.py` | SmartSearchRouter 單元測試 |
| `library/protocol_guide/test_api_integration.py` | API 整合測試 |
| `library/protocol_guide/test_phase3_dify_integration.py` | Dify 整合測試 |
| `backend/test_crystaldiskmark_search.py` | 搜尋結果驗證 |
