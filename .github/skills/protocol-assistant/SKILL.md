---
name: protocol-assistant
description: 'Protocol Assistant 功能架構與實作知識。Use when: modifying Protocol Assistant chat flow, search routing, Dify integration, uncertainty detection, keyword detection, search modes (mode A / mode B), two-tier search, fallback logic, external knowledge base API, ProtocolGuide model, vector search, vector database, pgvector, embeddings, document_embeddings, document_section_embeddings, SearchThresholdSetting, SectionSearchService, embedding model, multilingual-e5-large, cosine similarity, threshold, smart search router, or any Protocol Assistant related feature.'
argument-hint: 'What do you want to understand or modify? (e.g., search routing, Dify call, fallback, keyword detection)'
---

# Protocol Assistant — 架構與實作 Skill

## 快速定位

| 想改什麼 | 看哪個文件 |
|---------|-----------|
| 搜尋模式路由邏輯 | [architecture.md](./references/architecture.md) |
| 完整呼叫流程圖 | [flow.md](./references/flow.md) |
| 所有檔案對應表 | [files-map.md](./references/files-map.md) |
| 常見修改任務 | [common-tasks.md](./references/common-tasks.md) |
| 向量資料庫架構與原理 | [vector-database.md](./references/vector-database.md) |

## 核心概念（必讀）

Protocol Assistant 使用**智能搜尋路由**，根據用戶問題自動選擇搜尋模式：

- **Mode A**：問題含「完整/教學/SOP/詳細...」等關鍵字 → 直接全文搜尋
- **Mode B**：一般問題 → 兩階段搜尋（段落 → 全文 → fallback）

## 關鍵數字

- Dify App (dev): `app-4TbH1O7NkpOFsnxGEF3FLyqd`（`Protocol_Guide_dev`）
- Dify App (prod): `app-MgZZOhADkEmdUrj2DtQLJ23G`（`Protocol_Guide`）
- 外部知識庫 API: `http://10.10.172.127/api/dify/knowledge/retrieval/`
- knowledge_id: `protocol_guide_database`（Dify 傳來）→ 對應 DB table `protocol_guide`
- 全文搜尋標記: 查詢字串加 `__FULL_SEARCH__` 觸發 Stage 2
- 環境切換: `DIFY_ENV=development`（dev）/ `production`（prod）
