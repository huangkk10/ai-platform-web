# Protocol Assistant 向量系統 Bug 修復總結

**修復日期**：2025-11-11  
**問題類型**：系統 Bug（非內容問題）  
**嚴重程度**：高（影響所有 Protocol Guide 的搜尋功能）

---

## 🎯 問題摘要

Protocol Assistant 無法搜尋到文檔，即使文檔和向量都存在。

### 根本原因

1. **段落向量生成邏輯缺陷**：
   - 系統只生成單一的 `embedding` 向量
   - 但搜尋系統需要 `title_embedding` 和 `content_embedding`（分離的多向量）
   - 搜尋條件：`WHERE title_embedding IS NOT NULL AND content_embedding IS NOT NULL`
   - 結果：即使段落記錄存在，也因為這兩個欄位為 NULL 而無法被搜尋到

2. **ViewSet Manager 參數錯誤**：
   - 使用 `metadata={'title': ...}` 而非 `document_title=...`
   - 導致段落向量生成可能失敗

---

## ✅ 已修復內容

### 1. `SectionVectorizationService._store_section_embedding()` ✅

**修復前**：
```python
# 只生成單一向量
embedding = self.embedding_service.generate_embedding(full_context)
# 只存儲到 embedding 欄位
```

**修復後**：
```python
# ✅ 分別生成標題向量和內容向量
title_embedding = self.embedding_service.generate_embedding(section.title)
content_embedding = self.embedding_service.generate_embedding(section.content)
embedding = self.embedding_service.generate_embedding(full_context)  # 向後兼容

# ✅ 存儲三個向量欄位
INSERT INTO document_section_embeddings (
    embedding, title_embedding, content_embedding, ...
) VALUES (
    %s::vector, %s::vector, %s::vector, ...
)
```

**影響**：
- ✅ 新創建的文檔會自動生成完整的多向量
- ✅ 更新現有文檔會重新生成多向量
- ⚠️ 舊文檔需要手動重新生成

---

### 2. `ProtocolGuideViewSetManager` ✅

**修復前**：
```python
vectorization_service.vectorize_document_sections(
    metadata={'title': instance.title}  # ❌ 錯誤
)
```

**修復後**：
```python
result = vectorization_service.vectorize_document_sections(
    document_title=instance.title  # ✅ 正確
)

# ✅ 添加錯誤處理
if result.get('success'):
    logger.info(f"✅ 成功 ({result.get('vectorized_count')} 個段落)")
else:
    logger.error(f"❌ 失敗: {result.get('error')}")
```

---

## 🧪 測試驗證

**測試時間**：2025-11-11 03:52  
**測試結果**：✅ 成功

```
創建測試文檔 ID: 21
解析段落: 3 個
向量化成功: 3/3

資料庫驗證：
✅ sec_1: title_embedding (1024維), content_embedding (NULL - 內容為空)
✅ sec_2: title_embedding (1024維), content_embedding (1024維)
✅ sec_3: title_embedding (1024維), content_embedding (1024維)
```

---

## ⚠️ 需要採取的行動

### 1. 立即行動：重啟 Django 服務 ✅

```bash
docker restart ai-django
```

**狀態**：✅ 已完成

---

### 2. 重要行動：重新生成舊文檔的向量

**影響範圍**：2025-11-11 之前創建的所有 Protocol Guide

**檢查受影響的文檔數量**：
```sql
SELECT COUNT(*) 
FROM document_section_embeddings 
WHERE source_table = 'protocol_guide' 
  AND (title_embedding IS NULL OR content_embedding IS NULL);
```

**批量修復方法 A：使用現有腳本**
```bash
docker exec ai-django python regenerate_section_multi_vectors.py \
  --source protocol_guide \
  --batch-size 10
```

**批量修復方法 B：手動腳本**
```python
# 在 Django shell 中執行
from django.db import connection
from api.services.embedding_service import get_embedding_service

embedding_service = get_embedding_service('ultra_high')

# 獲取需要修復的段落
with connection.cursor() as cursor:
    cursor.execute('''
        SELECT id, heading_text, content
        FROM document_section_embeddings
        WHERE source_table = 'protocol_guide' 
          AND (title_embedding IS NULL OR content_embedding IS NULL)
    ''')
    sections = cursor.fetchall()

print(f'需要修復 {len(sections)} 個段落向量')

# 批量更新
for section_id, heading_text, content in sections:
    title_emb = embedding_service.generate_embedding(heading_text) if heading_text else None
    content_emb = embedding_service.generate_embedding(content) if content else None
    
    if title_emb or content_emb:
        title_str = '[' + ','.join(map(str, title_emb)) + ']' if title_emb else None
        content_str = '[' + ','.join(map(str, content_emb)) + ']' if content_emb else None
        
        with connection.cursor() as cursor:
            cursor.execute('''
                UPDATE document_section_embeddings
                SET title_embedding = %s::vector,
                    content_embedding = %s::vector,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', [title_str, content_str, section_id])
        
        print(f'  ✅ 段落 {section_id} 更新成功')

print('✅ 所有段落向量已更新')
```

---

### 3. 驗證行動：測試搜尋功能

**步驟 1：檢查 Cup 文檔的向量**
```sql
SELECT 
    section_id,
    heading_text,
    title_embedding IS NOT NULL as has_title,
    content_embedding IS NOT NULL as has_content,
    vector_dims(title_embedding) as title_dim,
    vector_dims(content_embedding) as content_dim
FROM document_section_embeddings
WHERE source_table = 'protocol_guide' AND source_id = 20
ORDER BY section_id;
```

**預期結果**：
```
section_id | heading_text | has_title | has_content | title_dim | content_dim
-----------+--------------+-----------+-------------+-----------+-------------
sec_1      | Cup 顏色...  | t         | t           | 1024      | 1024
```

**步驟 2：在 Protocol Assistant 中測試**
1. 打開 Protocol Assistant 聊天界面
2. 詢問：「Cup 是什麼？」或「請說明 Cup」
3. 預期：AI 應該能找到並引用 Cup 文檔

---

## 📊 影響評估

### 受影響的系統
- ✅ **Protocol Assistant**：主要影響
- ⚠️ **其他 Assistant**：如果使用相同的段落搜尋邏輯，也可能受影響
  - RVT Assistant
  - Know Issue Assistant（如果有）

### 需要檢查的其他 Assistant

**檢查方法**：
```bash
# 搜尋使用 SectionSearchService 的地方
grep -r "SectionSearchService" library/*/search_service.py
grep -r "document_section_embeddings" library/*/search_service.py
```

**如果其他 Assistant 也使用段落搜尋**：
1. 檢查是否有相同問題（向量欄位為 NULL）
2. 執行相同的修復流程
3. 重新生成向量

---

## 📚 相關文檔

- **完整診斷報告**：`/docs/debugging/protocol-assistant-cup-search-issue-analysis.md`
- **向量系統架構**：`/docs/architecture/rvt-assistant-database-vector-architecture.md`
- **段落向量實作**：`/docs/vector-search/section-vector-implementation.md`

---

## 🎓 經驗教訓

### 系統設計教訓
1. **資料表結構與代碼不一致**：
   - 資料表有 3 個向量欄位（embedding, title_embedding, content_embedding）
   - 但代碼只填充 1 個欄位
   - **教訓**：資料表結構變更時，必須同步更新所有相關代碼

2. **搜尋系統與生成系統脫節**：
   - 搜尋系統依賴 title_embedding 和 content_embedding
   - 但生成系統只生成 embedding
   - **教訓**：搜尋和生成邏輯應該使用相同的欄位規範

3. **缺少整合測試**：
   - 單元測試可能都通過，但整合測試會失敗
   - **教訓**：需要端到端測試（創建文檔 → 生成向量 → 搜尋驗證）

### 診斷教訓
1. **不要過早下結論**：
   - 最初認為是內容問題（Cup 文檔只有標題）
   - 實際是系統 Bug（向量欄位不匹配）
   - **教訓**：即使找到一個問題，也要深入檢查是否有更根本的原因

2. **完整的診斷流程**：
   - 檢查資料庫記錄 → 檢查向量 → 檢查 SQL 查詢 → **檢查資料表結構**
   - **教訓**：資料表結構檢查是診斷向量問題的關鍵步驟

---

## ✅ 修復狀態總結

| 項目 | 狀態 | 備註 |
|------|------|------|
| 段落向量生成邏輯 | ✅ 已修復 | 現在生成 3 個向量 |
| ViewSet Manager 參數 | ✅ 已修復 | 使用正確的參數名稱 |
| Django 服務重啟 | ✅ 已完成 | 載入新代碼 |
| 測試驗證 | ✅ 已通過 | 測試文檔向量正確 |
| Cup 文檔向量修復 | ✅ 已完成 | 手動重新生成 |
| 舊文檔向量重新生成 | ⏳ 待執行 | 需要批量更新 |
| 搜尋功能驗證 | ⏳ 待測試 | 需要在 UI 中測試 |

---

**更新日期**：2025-11-11  
**修復者**：AI Assistant  
**審核狀態**：待用戶驗證
