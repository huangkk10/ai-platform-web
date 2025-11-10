# Protocol Assistant "Cup顏色全文" 查詢問題分析與修復

**問題報告日期**：2025-11-11  
**問題類型**：完整文檔展開功能失敗  
**嚴重程度**：高（影響所有文檔級關鍵字查詢）

---

## 🎯 問題描述

**用戶查詢**：`"Cup顏色全文"`

**期望行為**：
- 檢測到關鍵字 `'全文'`
- 返回 **Cup 的完整文檔內容**（包含所有段落）

**實際行為**：
- ✅ 關鍵字檢測成功（`'全文'` 被識別）
- ✅ 查詢清理成功（清理為 `'Cup顏色'`）
- ❌ **完整文檔展開失敗**
- ❌ 返回的是 **Section 級結果**，而非完整文檔

---

## 🔍 根本原因分析

### 問題 1：`document_id` 和 `document_title` 欄位缺失 ⚠️

**診斷日誌**：
```log
[INFO] 🎯 文檔級查詢檢測:
[INFO]    原始查詢: 'Cup顏色全文'
[INFO]    檢測關鍵字: ['全文']
[INFO]    清理後查詢: 'Cup顏色' (用於向量搜尋)
[INFO] 🔄 將 2 個 section 結果擴展為完整文檔
[WARNING] ⚠️  無法從 source_ids {20, 21} 找到對應的 document_id  ← 問題在這裡！
```

**資料庫檢查**：
```sql
SELECT document_id, document_title FROM document_section_embeddings 
WHERE source_table = 'protocol_guide' AND source_id = 20;

-- 結果：所有記錄的 document_id 和 document_title 都是 NULL
```

**根因**：
- `SectionVectorizationService._store_section_embedding()` 方法 **沒有** 寫入 `document_id` 和 `document_title` 欄位
- INSERT 語句中缺少這兩個欄位
- `_expand_to_full_document()` 依賴 `document_id` 來查找完整文檔
- 結果：即使檢測到關鍵字，也無法展開為完整文檔

---

## ✅ 修復方案

### 修復 1：添加 `document_id` 和 `document_title` 欄位到 INSERT 語句

**修改檔案**：`library/common/knowledge_base/section_vectorization_service.py`

#### 1.1 更新方法簽名
```python
def _store_section_embedding(
    self,
    source_table: str,
    source_id: int,
    section: MarkdownSection,
    full_context: str,
    document_title: str = ""  # ✅ 添加文檔標題參數
) -> bool:
```

#### 1.2 生成 `document_id`
```python
# 🔧 生成 document_id（使用 source_table + source_id 的組合）
# 格式：protocol_guide_20, rvt_guide_15 等
document_id = f"{source_table}_{source_id}"
```

#### 1.3 更新 INSERT 語句
```python
INSERT INTO document_section_embeddings (
    source_table, source_id, section_id,
    document_id, document_title,  # ✅ 新增欄位
    heading_level, heading_text, section_path, parent_section_id,
    content, full_context, 
    embedding, title_embedding, content_embedding,
    word_count, has_code, has_images,
    created_at, updated_at
) VALUES (
    %s, %s, %s,
    %s, %s,  # ✅ 新增參數
    %s, %s, %s, %s,
    %s, %s, 
    %s::vector, %s::vector, %s::vector,
    %s, %s, %s,
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
)
```

#### 1.4 更新 ON CONFLICT 子句
```python
ON CONFLICT (source_table, source_id, section_id)
DO UPDATE SET
    document_id = EXCLUDED.document_id,        # ✅ 新增
    document_title = EXCLUDED.document_title,  # ✅ 新增
    heading_level = EXCLUDED.heading_level,
    -- ... 其他欄位
```

#### 1.5 傳遞 `document_title` 參數
```python
# 在 vectorize_document_sections() 方法中
success = self._store_section_embedding(
    source_table=source_table,
    source_id=source_id,
    section=section,
    full_context=full_context,
    document_title=document_title  # ✅ 傳遞文檔標題
)
```

---

### 修復 2：批量更新現有記錄

**執行腳本**：`fix_document_ids.py`

#### 修復邏輯
```python
# 對於 protocol_guide
UPDATE document_section_embeddings dse
SET 
    document_id = CONCAT('protocol_guide_', dse.source_id::text),
    document_title = pg.title
FROM protocol_guide pg
WHERE dse.source_table = 'protocol_guide'
    AND dse.source_id = pg.id
    AND (dse.document_id IS NULL OR dse.document_id = '');
```

#### 修復結果
```
修復前：
  - protocol_guide: 9 筆記錄缺少 document_id
  - rvt_guide: 53 筆記錄缺少 document_id
  總計: 62 筆

修復後：
  ✅ protocol_guide: 56 筆 (100.0% 有 document_id 和 document_title)
  ✅ rvt_guide: 53 筆 (100.0% 有 document_id 和 document_title)
```

---

## 🧪 測試驗證

### 測試 1：資料庫驗證
```sql
SELECT 
    source_id, section_id, heading_text,
    document_id, document_title
FROM document_section_embeddings
WHERE source_table = 'protocol_guide' AND source_id = 20;
```

**結果**：
```
source_id | section_id | heading_text | document_id       | document_title
----------|------------|--------------|-------------------|--------------
20        | sec_1      | 顏色顏色...  | protocol_guide_20 | Cup
20        | sec_2      | 圖案         | protocol_guide_20 | Cup
20        | sec_3      | 歷史         | protocol_guide_20 | Cup
20        | sec_4      | 化學         | protocol_guide_20 | Cup
20        | sec_5      | 國語         | protocol_guide_20 | Cup
20        | sec_6      | 數學         | protocol_guide_20 | Cup
```
✅ **通過**：所有記錄都有正確的 `document_id` 和 `document_title`

---

### 測試 2：完整文檔展開功能
```
查詢: "Cup顏色全文"

結果 1:
  標題: 測試多向量生成
  分數: 0.8551
  類型: ✅ 完整文檔
  Document ID: protocol_guide_21
  包含段落數: 3
  內容長度: 96 字元

結果 2:
  標題: Cup
  分數: 0.8551
  類型: ✅ 完整文檔
  Document ID: protocol_guide_20
  包含段落數: 6
  內容長度: 71 字元
```

**日誌驗證**：
```log
[INFO] 🎯 文檔級查詢檢測:
[INFO]    原始查詢: 'Cup顏色全文'
[INFO]    檢測關鍵字: ['全文']
[INFO]    清理後查詢: 'Cup顏色' (用於向量搜尋)
[INFO] 🔄 將 2 個 section 結果擴展為完整文檔
[INFO] 📄 擴展為完整文檔，涉及 2 個文檔 (來自 2 個 source_ids)
[INFO] ✅ 組裝完成: 測試多向量生成, 包含 3 個 sections
[INFO] ✅ 組裝完成: Cup, 包含 6 個 sections
```

✅ **通過**：
- 關鍵字檢測成功
- 查詢清理成功
- **完整文檔展開成功**（之前失敗）
- 返回類型正確：`is_full_document: True`

---

### 測試 3：對比測試（關鍵字 vs 無關鍵字）

#### 測試 3.1：含關鍵字查詢
```
查詢: "Cup顏色全文"
結果類型: ✅ 完整文檔
包含段落: 6 個
內容長度: 71 字元
```

#### 測試 3.2：無關鍵字查詢
```
查詢: "Cup 如何使用"
結果類型: ❌ Section 級
返回: 單一段落內容
```

✅ **通過**：關鍵字正確觸發完整文檔模式

---

## 📊 影響評估

### 受影響範圍
- ✅ **Protocol Assistant**：主要影響
- ✅ **RVT Assistant**：同樣修復（53 筆記錄）
- ⚠️ **其他 Assistant**：如果使用 Section Search，也受益

### 修復效果
| 功能 | 修復前 | 修復後 |
|------|--------|--------|
| 關鍵字檢測 | ✅ 正常 | ✅ 正常 |
| 查詢清理 | ✅ 正常 | ✅ 正常 |
| 完整文檔展開 | ❌ 失敗 | ✅ 成功 |
| 文檔完整性 | ❌ Section 級 | ✅ 完整文檔 |
| 用戶體驗 | ❌ 片段回答 | ✅ 完整回答 |

---

## 🎓 經驗教訓

### 1. 資料庫欄位與功能的依賴關係
**問題**：
- 新增功能（完整文檔展開）依賴特定欄位（`document_id`）
- 但向量生成邏輯沒有填充這些欄位
- 導致功能無法運作，但沒有明顯的錯誤訊息

**教訓**：
- 新增功能時，必須檢查資料庫欄位是否完整
- 向量生成邏輯應該是**唯一**填充這些欄位的地方
- 需要完整的端到端測試（資料生成 → 搜尋 → 展開）

---

### 2. 代碼審查的盲點
**問題**：
- 之前的 Bug 修復專注於 `title_embedding` 和 `content_embedding`
- 忽略了其他重要欄位（`document_id`, `document_title`）
- 假設這些欄位已經存在

**教訓**：
- 資料表結構審查應該是**全面性**的
- 不要只修復當前的錯誤，要檢查整個欄位列表
- 使用 `SELECT *` 查詢檢查所有欄位狀態

---

### 3. 日誌的重要性
**優點**：
- 日誌明確指出 `⚠️ 無法從 source_ids {20, 21} 找到對應的 document_id`
- 讓我們快速定位問題

**改進**：
- 應該將這個 WARNING 升級為 ERROR
- 在開發環境中應該拋出異常（而非僅記錄）

---

## ✅ 修復狀態總結

| 項目 | 狀態 | 備註 |
|------|------|------|
| 識別問題根因 | ✅ 完成 | `document_id` 欄位缺失 |
| 修改向量生成邏輯 | ✅ 完成 | 添加 `document_id` 和 `document_title` |
| 批量修復現有記錄 | ✅ 完成 | 62 筆記錄已修復 |
| Django 服務重啟 | ✅ 完成 | 新代碼已載入 |
| 功能驗證測試 | ✅ 通過 | 完整文檔展開正常 |
| 日誌驗證 | ✅ 通過 | 無警告訊息 |
| 文檔更新 | ✅ 完成 | 本報告 |

---

## 🆕 相關修復記錄

### 相關 Bug
1. **多向量生成 Bug**（2025-11-11）：
   - 問題：只生成 `embedding`，缺少 `title_embedding` 和 `content_embedding`
   - 狀態：✅ 已修復
   
2. **document_id 欄位缺失**（2025-11-11 - 本次）：
   - 問題：缺少 `document_id` 和 `document_title` 欄位
   - 狀態：✅ 已修復

### 相關功能
1. **關鍵字清理功能**（2025-11-11）：
   - 功能：移除查詢中的指令性關鍵字
   - 狀態：✅ 正常運作
   
2. **完整文檔展開功能**（2025-11-11）：
   - 功能：將 section 結果組裝為完整文檔
   - 狀態：✅ 現已修復並運作

---

## 📚 相關文檔

- **Bug 修復總結**：`/docs/debugging/PROTOCOL_VECTOR_BUG_FIX_SUMMARY.md`
- **關鍵字清理實作報告**：`/docs/features/protocol-keyword-cleaning-implementation.md`
- **向量系統架構**：`/docs/architecture/rvt-assistant-database-vector-architecture.md`

---

**修復日期**：2025-11-11  
**修復者**：AI Assistant  
**審核狀態**：✅ 已修復並測試通過  
**生產狀態**：✅ 可部署至生產環境

**最後更新**：2025-11-11 04:40
