# 段落搜尋架構問題：標題權重的語義不符

**日期**：2025-11-06  
**嚴重程度**：🔴 高（設計概念錯誤）

---

## 🎯 **問題核心**

### 用戶期望 vs 實際實現

| 項目 | 用戶理解 | 實際實現 | 結果 |
|------|---------|---------|------|
| **「標題權重」的意義** | 文件標題（document.title）的權重 | 段落標題（section.heading_text）的權重 | ❌ 語義不符 |
| **搜尋 "CrystalDiskMark 5"** | 期望找到標題為 "CrystalDiskMark 5" 的文件 | 實際比對段落標題 "2.When boot into system." | ❌ 完全不匹配 |
| **100% 標題權重** | 期望：完全基於文件標題搜尋 | 實際：完全基於段落標題搜尋 | ❌ 概念錯誤 |

---

## 📊 **當前架構分析**

### 段落向量結構（document_section_embeddings 表）

```sql
-- 當前的段落向量欄位
CREATE TABLE document_section_embeddings (
    id SERIAL PRIMARY KEY,
    source_table VARCHAR(100),
    source_id INTEGER,  -- 關聯到 protocol_guide.id
    section_id VARCHAR(50),
    
    -- 段落資訊
    heading_text TEXT,  -- ⚠️ 段落標題（不是文件標題）
    content TEXT,       -- 段落內容
    
    -- 多向量
    title_embedding vector(1024),    -- ⚠️ 基於 heading_text
    content_embedding vector(1024),  -- ✅ 基於 content
    
    -- 舊的單向量（已不使用）
    embedding vector(1024)
);
```

### 多向量生成邏輯

**檔案**：`backend/regenerate_section_multi_vectors.py`（第 50-54 行）

```python
# 生成標題向量
title_text = heading_text or ""  # ⚠️ 使用段落標題
title_embedding = embedding_service.generate_embedding(title_text)

# 生成內容向量
content_text = content or ""
content_embedding = embedding_service.generate_embedding(content_text)
```

**問題**：
- `title_embedding` 是基於 `heading_text`（段落標題）
- **不是**基於 `document.title`（文件標題）

---

## 🔍 **實際案例證明**

### CrystalDiskMark 5 文件的段落

**文件標題**：`"CrystalDiskMark 5"` ✅（這是用戶想搜尋的）

**段落 1**：
```python
heading_text = "1.Test Platform model and sample setup please by case required."
title_embedding = encode("1.Test Platform model and sample setup...")
# ⚠️ 完全不包含 "CrystalDiskMark" 或 "5"
```

**段落 2**：
```python
heading_text = "2.When boot into system."
title_embedding = encode("2.When boot into system.")
# ⚠️ 完全不包含 "CrystalDiskMark" 或 "5"
```

**搜尋 "crystaldiskmark 5" 時**：
```python
query_embedding = encode("crystaldiskmark 5")

# 與段落 1 的 title_embedding 比對
similarity = cosine(query_embedding, encode("1.Test Platform model..."))
# 結果：0.78（低，因為語義不相關）

# 與段落 2 的 title_embedding 比對
similarity = cosine(query_embedding, encode("2.When boot into system."))
# 結果：0.81（低，因為語義不相關）
```

**結論**：即使設定 100% 標題權重，仍然找不到 CrystalDiskMark 5！

---

## 🎯 **問題分析**

### 為什麼 UNH-IOL 分數更高？

**UNH-IOL 的段落**：
```python
heading_text = "5.IOL 安裝需求"
title_embedding = encode("5.IOL 安裝需求")

# 與查詢 "crystaldiskmark 5" 比對
similarity = cosine(encode("crystaldiskmark 5"), encode("5.IOL 安裝需求"))
# 結果：0.85（較高）
```

**為什麼分數高？**
1. **有數字 "5"**：與查詢中的 "5" 匹配 ✅
2. **"IOL" vs "crystaldiskmark"**：都是技術工具名稱，語義相似 ✅
3. **"安裝需求"**：技術文檔常見操作詞彙 ✅

**向量模型的理解**：
- `"crystaldiskmark 5"` → 某個技術工具的版本 5
- `"5.IOL 安裝需求"` → 第 5 點，關於 IOL 工具的安裝需求
- **語義模式相似**：「技術工具 + 數字 + 操作」

---

## 💡 **根本問題**

### 概念錯誤：段落向量不應該只用段落標題

**當前設計**：
```python
# 段落的 title_embedding
title_embedding = encode(section.heading_text)
# 問題：段落標題通常是：
#   - "1.xxx"
#   - "步驟 2：xxx"
#   - "2.When boot into system."
# 這些標題不包含文件標題，導致無法透過文件名搜尋到段落
```

**應該的設計**：
```python
# 段落的 title_embedding 應該包含文件標題
title_embedding = encode(f"{document.title} - {section.heading_text}")
# 範例：
#   - "CrystalDiskMark 5 - 2.When boot into system."
#   - "UNH-IOL - 5.IOL 安裝需求"
# 這樣才能透過文件標題找到段落
```

---

## 🔄 **需要修改的地方**

### 1. 段落多向量生成邏輯

**檔案**：`backend/regenerate_section_multi_vectors.py`

**當前邏輯**（第 26-40 行）：
```python
cursor.execute("""
    SELECT id, source_table, source_id, section_id, 
           heading_text, content
    FROM document_section_embeddings
    ORDER BY source_table, source_id, id;
""")

# ... 後續處理
title_text = heading_text or ""  # ⚠️ 只用段落標題
title_embedding = embedding_service.generate_embedding(title_text)
```

**需要修改為**：
```python
cursor.execute("""
    SELECT 
        dse.id, dse.source_table, dse.source_id, dse.section_id, 
        dse.heading_text, dse.content,
        -- ✨ 加入文件標題
        CASE 
            WHEN dse.source_table = 'protocol_guide' 
            THEN pg.title
            WHEN dse.source_table = 'rvt_guide' 
            THEN rg.title
        END as document_title
    FROM document_section_embeddings dse
    LEFT JOIN protocol_guide pg ON dse.source_table = 'protocol_guide' AND dse.source_id = pg.id
    LEFT JOIN rvt_guide rg ON dse.source_table = 'rvt_guide' AND dse.source_id = rg.id
    ORDER BY dse.source_table, dse.source_id, dse.id;
""")

# ... 後續處理
# ✨ 組合文件標題和段落標題
title_text = f"{document_title} - {heading_text}" if document_title and heading_text else (heading_text or "")
title_embedding = embedding_service.generate_embedding(title_text)
```

### 2. 段落向量化服務

**檔案**：`library/common/knowledge_base/section_vectorization_service.py`

需要修改 `_store_section_embedding()` 方法（如果使用），或者在生成時就傳入文件標題。

### 3. 未來新增段落時

確保任何生成段落向量的邏輯都：
1. 能存取到文件標題（document.title）
2. 將文件標題和段落標題組合
3. 用組合後的標題生成 title_embedding

---

## 📊 **預期效果**

### 修改前（當前）

**查詢**：`"crystaldiskmark 5"`

**結果**：
```
1. UNH-IOL - 5.IOL 安裝需求 (0.85)  ⚠️ 不相關但分數高
2. Burn in Test - 5.Install BurnIn Test Pro (0.83)  ⚠️ 不相關
...
8. CrystalDiskMark 5 - 2.When boot into system. (0.81)  ❌ 相關但排名低
```

### 修改後（預期）

**段落向量**：
```python
# CrystalDiskMark 5 的段落 1
title_embedding = encode("CrystalDiskMark 5 - 1.Test Platform model...")
# ✅ 包含 "CrystalDiskMark 5"

# CrystalDiskMark 5 的段落 2
title_embedding = encode("CrystalDiskMark 5 - 2.When boot into system.")
# ✅ 包含 "CrystalDiskMark 5"
```

**查詢**：`"crystaldiskmark 5"`

**預期結果**：
```
1. CrystalDiskMark 5 - 1.Test Platform model... (0.94)  ✅ 完全匹配
2. CrystalDiskMark 5 - 2.When boot into system. (0.92)  ✅ 完全匹配
3. CrystalDiskMark 5 - 3.Perform cmd line... (0.93)  ✅ 完全匹配
4. UNH-IOL - 5.IOL 安裝需求 (0.85)  ⚠️ 排名下降
```

**改善**：
- ✅ CrystalDiskMark 5 的所有段落都排在前面
- ✅ 分數從 0.81 提升到 0.92+
- ✅ 符合用戶期望：搜尋文件名找到該文件

---

## 🎯 **核心結論**

### 問題定義

**不是**多向量方法（方案 A）的問題，而是：

❌ **段落的 title_embedding 不應該只用段落標題（heading_text）**  
✅ **應該組合文件標題 + 段落標題**

### 用戶的「標題權重」語義

```
用戶說的：「標題權重 100%」
期望意義：「完全基於【文件標題】搜尋」
           → document.title = "CrystalDiskMark 5"

實際實現：「完全基於【段落標題】搜尋」
           → section.heading_text = "2.When boot into system."

結果：語義不符，無法達到用戶預期 ❌
```

### 正確的設計

**段落的 title_embedding 應該包含文件標題**：

```python
# ✅ 正確設計
title_embedding = encode(f"{document.title} - {section.heading_text}")

# 範例：
# "CrystalDiskMark 5 - 2.When boot into system."
# "UNH-IOL - 5.IOL 安裝需求"
# "Burn in Test - 1. Prepare SSD sample."
```

**好處**：
1. ✅ 段落繼承文件標題的語義
2. ✅ 搜尋文件名能找到所有相關段落
3. ✅ 符合用戶對「標題權重」的直覺理解
4. ✅ 不需要改變多向量架構，只需調整 title_embedding 的生成內容

---

## 📋 **修改範圍**

### 受影響的檔案

| 檔案 | 修改內容 | 優先級 |
|------|---------|--------|
| `regenerate_section_multi_vectors.py` | 修改 SQL 查詢，加入文件標題；修改 title_text 組合邏輯 | 🔴 高 |
| `section_vectorization_service.py` | 確保未來新增段落時也組合文件標題 | 🔴 高 |
| `generate_all_protocol_sections.py` | 如果還在使用，需要同步修改 | 🟡 中 |

### 資料遷移

**需要重新生成所有段落的 title_embedding**：
- Protocol Guide：42 個段落
- RVT Guide：53 個段落
- 總計：95 個段落

**預估時間**：~5 分鐘（只需重新生成 title_embedding）

---

## 🎯 **解決方案總結**

### 方案：修改段落 title_embedding 的生成邏輯

**不需要**：
- ❌ 改變多向量架構
- ❌ 修改資料庫結構
- ❌ 修改搜尋邏輯
- ❌ 修改權重配置

**只需要**：
- ✅ 修改段落向量生成邏輯（組合文件標題）
- ✅ 重新生成所有段落的 title_embedding（~5 分鐘）
- ✅ 驗證搜尋結果改善

**影響範圍**：
- Protocol Guide：所有段落
- RVT Guide：所有段落
- 其他使用段落搜尋的 Assistant

**優點**：
- ✅ 簡單快速（不需要大規模重構）
- ✅ 符合用戶期望（標題權重 = 文件標題權重）
- ✅ 不影響現有架構
- ✅ 立即見效

---

**建議**：立即實施此修改，這是設計概念的修正，而非架構問題。
