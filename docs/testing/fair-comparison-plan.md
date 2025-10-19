# Protocol Assistant 向量搜尋公平對比測試方案

**日期**: 2025-10-20  
**問題**: 當前測試不公平（新系統向量搜尋 vs 舊系統關鍵字搜尋）  
**目標**: 進行公平的「段落向量 vs 整篇向量」對比

---

## 🔍 問題分析

### 當前測試的問題

```
測試結果: 新系統 95% 勝率
但實際上：
  新系統 = 段落向量搜尋（正常運作）
  舊系統 = 關鍵字搜尋（向量表缺失，被迫降級）
  
結論: ❌ 這不是公平的對比！
```

### 為何不公平？

1. **技術層級不同**
   - 新系統：使用 AI Embedding 向量（語義理解）
   - 舊系統：使用 PostgreSQL 全文搜尋（關鍵字匹配）
   - 就像比較「GPS 導航 vs 看路標」

2. **舊系統並未正常運作**
   - 缺少 `document_embeddings_1024` 表
   - 向量搜尋功能完全失效
   - 降級到備用方案（關鍵字搜尋）

3. **無法回答核心問題**
   - 我們想知道：**段落級別向量** vs **整篇文檔向量**，誰更好？
   - 實際測試：段落向量 vs 關鍵字搜尋（完全不同的東西）

---

## 🎯 公平對比方案

### 方案 A：修復舊系統，進行真實對比 ⭐ **推薦**

#### Step 1: 檢查現有向量表狀態

```sql
-- 檢查所有 embedding 相關的表
SELECT 
    tablename,
    schemaname
FROM pg_catalog.pg_tables 
WHERE tablename LIKE '%embedding%';

-- 檢查 document_embeddings 的結構
\d document_embeddings
```

#### Step 2: 決定是否需要創建 1024 維表

**選項 2a**: 創建新的 1024 維表（如果不存在）

```sql
-- 創建 document_embeddings_1024 表
CREATE TABLE document_embeddings_1024 (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100) NOT NULL,
    source_id INTEGER NOT NULL,
    text_content TEXT,
    content_hash VARCHAR(64),
    embedding vector(1024),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_table, source_id)
);

-- 創建索引
CREATE INDEX idx_embeddings_1024_source 
    ON document_embeddings_1024(source_table, source_id);

CREATE INDEX idx_embeddings_1024_vector 
    ON document_embeddings_1024 
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**選項 2b**: 修改舊系統代碼使用現有的 `document_embeddings` 表

```python
# 修改 library/protocol_guide/search_service.py
# 將所有 document_embeddings_1024 改為 document_embeddings
```

#### Step 3: 生成整篇文檔的 1024 維向量

```python
# 在 Django shell 中執行
from api.services.embedding_service import get_embedding_service
from api.models import ProtocolGuide

service = get_embedding_service('ultra_high')  # 1024 維模型

# 為每篇 Protocol Guide 生成向量
for guide in ProtocolGuide.objects.all():
    # 組合完整內容
    full_content = f"Title: {guide.title}\n\nContent:\n{guide.content}"
    
    # 生成並儲存向量
    service.store_document_embedding(
        source_table='protocol_guide',
        source_id=guide.id,
        content=full_content,
        use_1024_table=True  # 使用 1024 維表
    )
    
    print(f"✅ Guide {guide.id} - 向量生成完成")
```

**預估時間**：
- 檢查表狀態：5 分鐘
- 創建 1024 維表：5 分鐘
- 生成向量（假設 50 篇文檔）：15-20 分鐘
- **總計：30 分鐘**

#### Step 4: 重新執行對比測試

```bash
# 重新執行測試
docker exec ai-django python /app/tests/test_vector_search/test_section_search_comparison.py
```

這次的對比將是：
```
新系統（段落向量） vs 舊系統（整篇向量）
      ↓                    ↓
  ✅ 公平對比！兩者都使用向量搜尋
```

---

### 方案 B：檢查舊系統是否有其他表名

可能舊系統使用不同的表名或維度：

```sql
-- 檢查所有可能的表
SELECT 
    tablename,
    schemaname,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_catalog.pg_tables 
WHERE tablename LIKE '%embed%' OR tablename LIKE '%vector%';

-- 如果找到其他表，檢查其結構
-- \d <table_name>
```

**預估時間**：10-15 分鐘

---

### 方案 C：基於現有數據做出決策（快速但不完美）

如果時間緊迫，我們可以基於以下邏輯做出決策：

#### 理論分析：段落級別應該更好

**段落向量搜尋的優勢**：
1. ✅ **精準度更高**
   - 問題通常只涉及文檔的一部分
   - 段落向量可以精準匹配相關段落
   - 整篇向量會被不相關內容「稀釋」

2. ✅ **回應內容更精簡**
   - 只返回相關段落，不是整篇文檔
   - 減少 AI 需要處理的 token 數量
   - 降低 API 成本

3. ✅ **多個段落組合**
   - 可以從不同文檔提取相關段落
   - 整篇搜尋只能返回整篇文檔

**整篇向量搜尋的劣勢**：
1. ❌ **精準度降低**
   - 一篇文檔可能涵蓋多個主題
   - 向量會被平均稀釋
   - 難以精準匹配問題

2. ❌ **內容過長**
   - 返回整篇文檔（可能 5000+ 字元）
   - 增加 AI 處理成本
   - 用戶閱讀負擔重

#### 業界最佳實踐

參考主流 RAG 系統：
- **Pinecone, Weaviate, Qdrant** - 都推薦段落級別（Chunking）
- **LangChain, LlamaIndex** - 預設使用 Chunking
- **OpenAI 官方文檔** - 建議將長文檔分割成小段

**結論**：即使沒有測試數據，**段落級別在理論和實務上都更優**

---

## 💡 我的建議

### 推薦順序

1. **方案 A（30 分鐘）** - 修復舊系統並重新測試 ⭐ **最推薦**
   - **理由**：獲得真實的對比數據
   - **優點**：決策基於事實，而非假設
   - **缺點**：需要 30 分鐘

2. **方案 B（15 分鐘）** - 檢查是否有其他表
   - **理由**：可能舊系統使用不同的表名
   - **優點**：快速驗證
   - **缺點**：不一定能找到

3. **方案 C（立即）** - 基於理論分析決策
   - **理由**：理論和業界實踐都支持段落級別
   - **優點**：立即決策
   - **缺點**：缺少實際測試數據

### 如果選擇方案 A，執行步驟

```bash
# Step 1: 進入 Django shell
docker exec -it ai-django python manage.py shell

# Step 2: 檢查表狀態（在 shell 中）
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT tablename 
        FROM pg_catalog.pg_tables 
        WHERE tablename LIKE '%embed%'
    """)
    print(cursor.fetchall())

# Step 3: 決定下一步
# - 如果沒有 document_embeddings_1024，創建它
# - 如果有其他表，檢查結構
# - 如果有 document_embeddings，檢查維度

# Step 4: 生成向量（根據上面的 Step 3 腳本）

# Step 5: 重新測試
exit()  # 退出 shell
python /app/tests/test_vector_search/test_section_search_comparison.py
```

---

## 🎯 決策建議

### 如果你想要「確定」的答案
→ **選擇方案 A**（30 分鐘）

### 如果你想要「快速」的決策
→ **選擇方案 C**（基於理論 + 新系統表現良好）

### 如果你想要「折衷」方案
→ **選擇方案 B → A**（先快速檢查，再決定是否修復）

---

## ❓ 需要回答的問題

請回答以下問題，我會據此提供具體執行步驟：

1. **你想要多準確的對比結果？**
   - A. 非常準確（願意花 30 分鐘修復舊系統）
   - B. 快速決策（基於理論和新系統表現）
   - C. 先檢查看看（15 分鐘檢查表狀態）

2. **舊系統（整篇向量搜尋）在生產環境中還在使用嗎？**
   - 如果不再使用 → 可以直接切換到新系統
   - 如果仍在使用 → 需要謹慎對比

3. **Protocol Guide 目前有多少篇文檔？**
   - 這決定生成向量需要多久
   - 50 篇以下：15 分鐘
   - 100 篇以下：30 分鐘

---

**總結**：你的觀察非常正確！當前測試確實不公平。我建議先花 30 分鐘修復舊系統，進行公平對比，這樣才能做出有信心的決策。

你想選擇哪個方案？
