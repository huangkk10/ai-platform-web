---
name: rvt-assistant
description: 'RVT Assistant 功能架構與實作知識。Use when: modifying RVT Assistant chat flow, search routing, Dify integration, uncertainty detection, keyword detection, search modes (mode A / mode B), two-tier search, fallback logic, external knowledge base API, RVTGuide model, ContentImage model, image system [IMG:N], vector search, ThresholdManager, or any RVT Assistant related feature.'
argument-hint: 'What do you want to understand or modify? (e.g., search routing, Dify config, image system, fallback, threshold)'
---

# RVT Assistant Agent Skill

## 適用情境

修改 RVT Assistant 相關功能時使用此 skill，包含：
- 聊天流程、搜尋路由（Mode A / Mode B）
- Dify 整合、外部知識庫 API
- 關鍵字偵測、不確定性偵測
- 搜尋參數調整、知識庫文件管理
- 圖片支援（[IMG:N] 格式）
- 測試與診斷

## 參考文件

| 文件 | 內容 |
|------|------|
| [references/architecture.md](references/architecture.md) | 系統架構、DB model、Dify 設定、圖片系統 |
| [references/flow.md](references/flow.md) | Mode A / Mode B 完整流程、external KB API |
| [references/files-map.md](references/files-map.md) | 每個檔案的職責對照表、URL 路由 |
| [references/common-tasks.md](references/common-tasks.md) | 常見修改操作（參數調整、新增文件、疑難排解） |

## 快速查閱

### 服務 IP / Dify App

| 環境 | Dify App | API Key |
|------|----------|---------|
| Dev (`DIFY_ENV=development`) | RVT_Guide_dev | `app-xDXNUVPnPkP1We12RonI6Jk6` |
| Prod (`DIFY_ENV=production`) | RVT_Guide | `app-Lp4mlfIWHqMWPHTlzF9ywT4F` |

- Dify IP: `10.253.43.244`
- Web Server: `10.10.172.127`
- 外部知識庫 URL: `http://10.10.172.127/api/dify/knowledge/retrieval/`

### RVT vs Protocol Assistant 的差異

| 項目 | RVT Assistant | Protocol Assistant |
|------|---------------|--------------------|
| 聊天 URL | `/api/rvt-guide/chat/` | `/api/protocol-assistant/chat/` |
| library 目錄 | `library/rvt_guide/` | `library/protocol_guide/` |
| DB model | `RVTGuide` (`rvt_guide`) | `ProtocolGuide` (`protocol_guide`) |
| knowledge_id | `rvt_guide_db` / `rvt_guide_db_dev` | `protocol_guide_database` |
| 圖片支援 | ✅ `ContentImage` model + `[IMG:N]` | ❌（無圖片） |
| 外部 KB knowledge ID | `rvt_guide_db_dev` (dev) | `protocol_guide_database` |

### 關鍵數字

- Mode A 觸發: 查詢含 `FULL_DOCUMENT_KEYWORDS` 關鍵字（共 ~50 個）
- `__FULL_SEARCH__` marker: Mode A 在 query 前加此前綴傳給 Dify
- Fallback 觸發: `is_uncertain_response()` = True 或 answer 長度 < 20
- Stage 1 threshold: `0.8`（`rvt_assistant`，由 ThresholdManager 管理）
- 向量搜尋錯誤: `search_rvt_guide_with_vectors() got an unexpected keyword argument 'stage'`（不影響功能，自動回退到 search_service）
