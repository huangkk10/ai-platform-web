# 關鍵字搜尋失敗診斷報告
**日期**: 2025-11-27  
**問題**: v1.2.2 測試中關鍵字搜尋回傳 0 結果  
**嚴重程度**: 🔴 致命（導致混合搜尋失效）

---

## 🔍 問題現象

### 測試結果
- **總通過率**: 70% ❌（目標 90%）
- **精確關鍵字**: 66.7% ❌（目標 85%+）
- **長尾查詢**: 0% ❌（目標 75%+）

### 日誌證據
所有測試案例的關鍵字搜尋都返回 0 結果：

```log
[INFO] 🔍 英文全文搜尋: 'IOL 密碼' → 0 個結果
[INFO] 🔍 中文模糊搜尋: 'IOL 密碼' → 0 個結果
[INFO] 🔍 關鍵字搜尋完成: 'IOL 密碼' → 0 個結果（英文 + 中文融合）
```

**影響範圍**：
- ❌ 混合搜尋退化為純向量搜尋
- ❌ RRF 融合功能形同虛設（只融合向量結果）
- ❌ 精確關鍵字匹配能力完全喪失

---

## 🧪 診斷過程

### 步驟 1：檢查 GIN 索引狀態

**結論**: ✅ GIN 索引存在且正常

```sql
-- 索引定義
CREATE INDEX idx_section_fulltext_search 
ON public.document_section_embeddings 
USING gin (
    to_tsvector('simple'::regconfig, 
        (((COALESCE(heading_text, '') || ' ') || COALESCE(document_title, '')) || ' ') || COALESCE(content, '')
    )
);
```

### 步驟 2：檢查資料是否存在

**結論**: ✅ 資料存在

```sql
-- 查詢結果
SELECT * FROM document_section_embeddings 
WHERE content LIKE '%密碼%' 
LIMIT 1;

-- 結果：source_id = 10, title = '3.2 執行指令', content 包含「密碼為1」
```

### 步驟 3：測試 PostgreSQL 全文搜尋查詢

**結論**: ❌ 查詢失敗（0 結果）

```sql
-- 測試查詢（與程式碼完全相同）
SELECT source_id, title 
FROM document_section_embeddings 
WHERE source_table = 'protocol_guide'
  AND to_tsvector('simple', COALESCE(heading_text, '') || ' ' || ...) 
      @@ plainto_tsquery('simple', 'IOL 密碼')
ORDER BY ts_rank(...) DESC;

-- 結果：0 rows
```

### 步驟 4：分析 `plainto_tsquery` 行為

**結論**: ⚠️ `simple` 分詞器對中英文混合查詢支援不佳

```sql
-- 測試分詞結果
SELECT plainto_tsquery('simple', 'IOL 密碼');
-- 結果：'iol' & '密碼'  （AND 關係，必須同時匹配）

SELECT plainto_tsquery('simple', '密碼');
-- 結果：'密碼'  （能找到 2 筆，但不包含我們期望的 source_id=10）
```

### 步驟 5：發現根本原因

**核心問題**：`@@ plainto_tsquery` 運算符太嚴格，導致：

1. **中英文混合查詢失效**：
   - 查詢「IOL 密碼」 → `'iol' & '密碼'` （必須同時包含）
   - 但文本中是「密碼為1」，`iol` 可能在其他位置
   - 無法匹配成功

2. **單獨中文查詢也失效**：
   - 查詢「密碼」 → 只找到 2 筆不相關的結果
   - 我們期望的 source_id=10 居然沒有被匹配

3. **`simple` 分詞器的問題**：
   - `simple` 分詞器將整個中文詞組視為單個 token
   - 但實際文本中的分詞可能不同（如「密碼為1」可能被分為「密碼」「為」「1」）
   - 導致匹配失敗

---

## 🔧 根本原因總結

### 原因 1：PostgreSQL 全文搜尋配置錯誤

**問題點**：
- 使用 `simple` 分詞器，不支援中文智能分詞
- `plainto_tsquery` 的 `@@` 運算符要求精確匹配
- 中文詞組的分詞不一致

### 原因 2：中文模糊搜尋邏輯問題

查看代碼發現中文模糊搜尋有條件判斷：

```python
has_chinese = any('\u4e00' <= char <= '\u9fff' for char in query)

if has_chinese:
    # 執行中文模糊搜尋
```

但對於「IOL 密碼」這樣的混合查詢，雖然 `has_chinese=True`，但 LIKE 查詢可能也失敗了。

### 原因 3：PostgreSQL 中文全文搜尋的固有限制

PostgreSQL 內建的全文搜尋對中文支援不佳：
- `simple` 分詞器：不分詞，整個詞組作為一個 token
- `english` 分詞器：只支援英文
- **沒有內建的中文分詞器**

標準做法應該是：
- 英文查詢 → 使用 `ts_vector` + GIN 索引
- 中文查詢 → 使用 `LIKE` 或外部中文分詞器（如 zhparser）

---

## 💡 修復方案

### 方案 1：改用 LIKE 模糊匹配（推薦，快速）

**優點**：
- ✅ 實作簡單（5 分鐘）
- ✅ 支援中英文混合查詢
- ✅ 不需要安裝額外插件

**缺點**：
- ⚠️ 效能較差（無法使用 GIN 索引）
- ⚠️ 大表會較慢（但段落表只有幾千筆，可接受）

**實作**：
```python
def _keyword_search(self, query: str, limit: int = 10, source_table: str = None) -> list:
    """關鍵字搜尋（使用 LIKE 模糊匹配）"""
    
    keywords = query.split()  # 拆分為單詞
    
    # 構建 WHERE 條件
    like_conditions = []
    params = [source_table]
    
    for keyword in keywords:
        like_conditions.append("""
            (heading_text ILIKE %s OR 
             document_title ILIKE %s OR 
             content ILIKE %s)
        """)
        like_pattern = f'%{keyword}%'
        params.extend([like_pattern, like_pattern, like_pattern])
    
    where_clause = " AND ".join(like_conditions)  # 所有關鍵字都要匹配
    
    cursor.execute(f"""
        SELECT 
            source_id,
            COALESCE(heading_text, document_title) as title,
            content,
            document_id,
            document_title,
            1.0 as rank
        FROM document_section_embeddings
        WHERE source_table = %s
            AND {where_clause}
        LIMIT %s
    """, params + [limit])
```

**測試驗證**：
```sql
-- 測試「IOL 密碼」
SELECT * FROM document_section_embeddings 
WHERE source_table = 'protocol_guide'
  AND (heading_text ILIKE '%IOL%' OR document_title ILIKE '%IOL%' OR content ILIKE '%IOL%')
  AND (heading_text ILIKE '%密碼%' OR document_title ILIKE '%密碼%' OR content ILIKE '%密碼%')
LIMIT 5;

-- 預期結果：應該能找到 source_id=10（3.2 執行指令）
```

---

### 方案 2：安裝 zhparser 中文分詞插件（長期，推薦）

**優點**：
- ✅ 智能中文分詞
- ✅ 可使用 GIN 索引（效能優異）
- ✅ 支援中英文混合查詢

**缺點**：
- ❌ 需要安裝 PostgreSQL 插件（需要 DBA 權限）
- ❌ 實作時間較長（1-2 小時）

**實作步驟**：
```bash
# 1. 安裝 zhparser 插件
docker exec postgres_db apt-get update
docker exec postgres_db apt-get install -y postgresql-<version>-zhparser

# 2. 創建中文分詞配置
docker exec postgres_db psql -U postgres -d ai_platform -c "
CREATE TEXT SEARCH CONFIGURATION chinese_zh (PARSER = zhparser);
ALTER TEXT SEARCH CONFIGURATION chinese_zh ADD MAPPING FOR n,v,a,i,e,l WITH simple;
"

# 3. 重建 GIN 索引
CREATE INDEX idx_section_fulltext_chinese 
ON document_section_embeddings 
USING gin (
    to_tsvector('chinese_zh', COALESCE(heading_text, '') || ' ' || ...)
);
```

---

### 方案 3：混合策略（折衷）

**策略**：
- 英文查詢 → 使用 PostgreSQL 全文搜尋（保留現有邏輯）
- 中文查詢 → 使用 LIKE 模糊匹配
- 混合查詢 → 分離中英文分別查詢，再融合結果

**實作**：
```python
def _keyword_search(self, query: str, limit: int = 10, source_table: str = None) -> list:
    # 分離中英文
    chinese_chars = ''.join(c for c in query if '\u4e00' <= c <= '\u9fff')
    english_words = ' '.join(c for c in query.split() if not any('\u4e00' <= ch <= '\u9fff' for ch in c))
    
    all_results = {}
    
    # 英文部分：使用 PostgreSQL 全文搜尋
    if english_words:
        # ... 現有邏輯
    
    # 中文部分：使用 LIKE 模糊匹配
    if chinese_chars:
        # ... LIKE 查詢
    
    # 融合結果
    return list(all_results.values())
```

---

## 📋 推薦實施計劃

### 立即行動（方案 1）：
1. **修改 `_keyword_search()` 方法** → 改用 LIKE 模糊匹配
2. **重新執行測試** → 驗證修復效果
3. **時間估計** → 5-10 分鐘

### 中期優化（方案 3）：
1. **實作混合策略** → 英文用全文搜尋，中文用 LIKE
2. **效能測試** → 確認延遲可接受
3. **時間估計** → 1-2 小時

### 長期優化（方案 2）：
1. **安裝 zhparser 插件** → 需要 DBA 協助
2. **重建 GIN 索引** → 支援中文智能分詞
3. **時間估計** → 1-2 天（含測試）

---

## ✅ 驗收標準

修復後應滿足：
- [ ] 「IOL 密碼」查詢能找到 source_id=10（3.2 執行指令）
- [ ] 關鍵字搜尋不再返回 0 結果
- [ ] 測試通過率提升至 90%+
- [ ] RRF 融合功能正常工作（向量 + 關鍵字融合）

---

**下一步**：立即實施方案 1（LIKE 模糊匹配）
