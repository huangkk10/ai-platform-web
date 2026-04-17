# Protocol Assistant — 向量資料庫架構與運作原理

## 角色定位

向量資料庫是 Protocol Assistant 的**知識檢索核心**。

完整流程：
```
用戶提問
  ↓ [embedding_service] 將問題轉成 1024 維向量
  ↓ [pgvector] 餘弦相似度搜尋 document_section_embeddings
  ↓ 找到相關段落（score >= 0.9, top 3）
  ↓ 傳給 Dify 外部知識庫 callback → LLM 生成回答
```

沒有向量資料，Dify 無法找到任何內容，回答會退化為空白或 fallback。

---

## Embedding 模型

**模型**：`intfloat/multilingual-e5-large`（Sentence Transformers）
- 維度：**1024 維**
- 特性：多語言（繁中、英文、日文等），本地推論不需呼叫外部 API
- 服務類別：`backend/api/services/embedding_service.py` → `OpenSourceEmbeddingService`
- 預設 model_type：`ultra_high`（1024 維）

```python
# 取得 embedding service 的標準方法
from api.services.embedding_service import get_embedding_service
service = get_embedding_service('ultra_high')
embedding = service.generate_embedding("ucc 如何使用")  # 返回 List[float] 長度 1024
```

---

## 資料庫表結構

系統有**兩層**向量儲存，各有職責：

### 1. `document_embeddings`（文件層）

存整份文件的向量（每份文件 1 筆）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `source_table` | varchar(100) | 來源表，如 `protocol_guide` |
| `source_id` | integer | 對應 ProtocolGuide.id |
| `text_content` | text | 前 10,000 字元（用於備查） |
| `content_hash` | varchar(64) | SHA-256，用於偵測內容變更 |
| `embedding` | vector(1024) | 向後兼容用（與 title_embedding 相同） |
| `title_embedding` | vector(1024) | **標題**的 1024 維向量 |
| `content_embedding` | vector(1024) | **內容**的 1024 維向量 |

目前 protocol_guide 有：**18 筆**

### 2. `document_section_embeddings`（段落層）⭐ 主要搜尋對象

按 Markdown heading 切分的段落向量（每份文件多筆）：

| 欄位 | 類型 | 說明 |
|------|------|------|
| `source_table` | varchar(100) | `protocol_guide` |
| `source_id` | integer | 對應文件 ID |
| `section_id` | varchar(50) | 如 `sec_1`, `sec_2`, `doc_42`（文件標題特殊段落） |
| `heading_level` | integer | 0=文件標題, 1=H1, 2=H2, ... 6=H6 |
| `heading_text` | varchar(500) | 段落標題文字 |
| `section_path` | text | 完整路徑，如 `Doc Title > H1 > H2` |
| `content` | text | 段落內容 |
| `full_context` | text | `section_path + \n\n + content` |
| `title_embedding` | vector(1024) | 標題向量 |
| `content_embedding` | vector(1024) | 內容向量 |
| `embedding` | vector(1024) | 舊版單向量（向後兼容） |
| `word_count` | integer | 字數統計 |
| `has_code` | boolean | 是否含程式碼 |
| `has_images` | boolean | 是否含圖片 |
| `is_document_title` | boolean | 是否為文件標題特殊段落 |

目前 protocol_guide 有：**345 筆**

---

## 多向量搜尋機制（核心設計）

每個文件/段落都有**兩個獨立向量**：標題向量 + 內容向量。

搜尋時用加權公式計算最終分數：

```
final_score = title_weight × title_similarity + content_weight × content_similarity
```

**PostgreSQL 執行的 SQL（核心）**：
```sql
SELECT 
    dse.source_id,
    dse.heading_text,
    dse.section_path,
    dse.content,
    -- 加權分數
    (0.25 * (1 - (dse.title_embedding <=> $1::vector))) + 
    (0.75 * (1 - (dse.content_embedding <=> $1::vector))) AS similarity,
    (1 - (dse.title_embedding <=> $1::vector)) AS title_score,
    (1 - (dse.content_embedding <=> $1::vector)) AS content_score
FROM document_section_embeddings dse
WHERE dse.source_table = 'protocol_guide'
  AND dse.title_embedding IS NOT NULL
  AND dse.content_embedding IS NOT NULL
ORDER BY similarity DESC
LIMIT 3
```

`<=>` 是 pgvector 的**餘弦距離**運算子（cosine distance）。
`1 - distance` 轉換為**餘弦相似度**（0~1，越接近 1 越相似）。

---

## 搜尋權重設定（SearchThresholdSetting）

Protocol Assistant 的搜尋參數儲存在 DB 的 `SearchThresholdSetting` 中，**可透過 Admin 動態調整**：

| 參數 | 目前值 | 說明 |
|------|--------|------|
| `stage1_title_weight` | **25%** | Stage 1 標題權重 |
| `stage1_content_weight` | **75%** | Stage 1 內容權重 |
| `stage1_threshold` | **0.90** | Stage 1 搜尋後 Dify score threshold |
| `stage1_post_boost_threshold` | **0.70** | Title Boost 後的 threshold |
| `stage2_title_weight` | 10% | Stage 2 標題權重 |
| `stage2_content_weight` | 90% | Stage 2 內容權重 |
| `stage2_threshold` | 0.85 | Stage 2 score threshold |
| `use_unified_weights` | False | 是否 Stage 1/2 共用同一組權重 |

> `assistant_type = 'protocol_assistant'`，從 `SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')` 讀取。

---

## 內容如何切分成段落（Markdown Parser）

**檔案**：`library/common/knowledge_base/markdown_parser.py` → `MarkdownStructureParser`

解析規則：
1. 用正則 `^(#{1,6})\s+(.+)$` 找所有 Markdown heading
2. 每個 heading 到下一個 heading 之間的文字 = 一個段落
3. 自動建立父子關係（`parent_section_id`）
4. 建立完整路徑（`section_path`）

**額外特殊段落**：每份文件都有一個 `section_id=doc_{id}`, `heading_level=0` 的特殊段落，存放文件標題 + 前 500 字元。這讓搜尋時能匹配到文件標題本身。

```
文件「CrystalDiskMark 測試 SOP」
  ├── doc_42  (level=0, is_document_title=True, content=前500字)
  ├── sec_1   (level=1, heading=環境需求, content=...)
  ├── sec_2   (level=2, heading=安裝步驟, content=...)
  └── sec_3   (level=2, heading=常見問題, content=...)
```

---

## 向量生成流程（寫入路徑）

```
ProtocolGuide 文件建立/更新（Django signal 或手動觸發）
  ↓
ProtocolGuideVectorService.generate_and_store_vector(instance)
  ↓ (繼承自 BaseKnowledgeBaseVectorService)
OpenSourceEmbeddingService.store_document_embeddings_multi()
  ├── generate_embedding(title)   → title_embedding (1024維)
  ├── generate_embedding(content) → content_embedding (1024維)
  └── INSERT/UPDATE document_embeddings (ON CONFLICT DO UPDATE)

SectionVectorizationService.vectorize_document_sections()
  ├── MarkdownStructureParser.parse(markdown_content) → List[MarkdownSection]
  ├── 為每個 section: generate_embedding(heading_text) → title_embedding
  ├── 為每個 section: generate_embedding(content) → content_embedding
  └── UPSERT document_section_embeddings
```

---

## 批量重新產生向量（管理指令）

```bash
# 重新產生 Protocol Guide 向量
docker exec ai-django python manage.py generate_protocol_embeddings

# 強制重新產生（即使內容未變）
docker exec ai-django python manage.py generate_protocol_embeddings --force

# 重新產生段落多向量 (v2)
docker exec ai-django python backend/regenerate_section_multi_vectors_v2.py
```

---

## 向量搜尋在 Protocol Assistant 的角色圖

```
[搜尋查詢] "CrystalDiskMark 完整測試流程"
      ↓
[1] SmartSearchRouter 判斷 → Mode A（含「完整」關鍵字）
      ↓
[2] KeywordTriggeredHandler 加上 __FULL_SEARCH__ 前綴
      ↓  
[3] DifyChatClient 送給 Dify → Dify 呼叫外部 KB callback
      ↓
[4] dify_knowledge_views.dify_knowledge_search()
    偵測 __FULL_SEARCH__ → top_k=50 大量搜尋
      ↓
[5] DifyKnowledgeSearchHandler.search()
    knowledge_id='protocol_guide_database' → source_table='protocol_guide'
      ↓
[6] BaseKnowledgeBaseSearchService → SectionSearchService.search_sections()
    生成 query embedding → pgvector <=> 計算相似度 → 過濾 score >= 0.9
      ↓
[7] 返回 top-N 段落內容（title + content）給 Dify
      ↓
[8] Dify LLM 根據段落生成回答
```

---

## 常見向量問題診斷

### 問題：搜尋無結果

```bash
# 確認向量已產生
docker exec ai-django python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT COUNT(*) FROM document_section_embeddings WHERE source_table=%s', ['protocol_guide'])
    print('sections:', c.fetchone()[0])
    c.execute('SELECT COUNT(*) FROM document_embeddings WHERE source_table=%s', ['protocol_guide'])
    print('documents:', c.fetchone()[0])
"
```

### 問題：threshold 太高導致無結果

修改 Admin：`http://10.10.172.127/admin/api/searchthresholdsetting/`
- 降低 `stage1_threshold`（目前 0.90，試試 0.75）
- 降低 `stage1_post_boost_threshold`（目前 0.70）

### 問題：新增文件後搜尋不到

需要手動觸發向量生成：
```bash
docker exec ai-django python manage.py generate_protocol_embeddings
```

### 問題：確認向量維度正確

```bash
docker exec ai-django python manage.py shell -c "
from django.db import connection
with connection.cursor() as c:
    c.execute('SELECT vector_dims(title_embedding) FROM document_section_embeddings WHERE source_table=%s LIMIT 1', ['protocol_guide'])
    print('dims:', c.fetchone())
"
# 應輸出 (1024,)
```
