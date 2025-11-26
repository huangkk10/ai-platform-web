# Stage 2 向量搜索 NoneType 錯誤修復報告

**日期**: 2025-11-26  
**問題**: "iol 密碼" 查詢無法返回 UNH-IOL 文檔  
**根因**: Stage 2 文檔搜索的 SQL 查詢未過濾 NULL 向量，導致 NoneType 比較錯誤  
**修復者**: AI Assistant  

---

## 📋 問題描述

### 用戶報告
用戶查詢 **"iol 密碼"** 時，期望返回 **UNH-IOL** 文檔（包含密碼資訊），但系統返回 0 個結果。

### 症狀
- ✅ **Stage 1 (段落搜索)**: 正常運作，找到相關段落（85-89% 相似度）
- ❌ **Stage 2 (文檔搜索)**: 崩潰，錯誤訊息：
  ```
  [ERROR] 多向量搜索失敗: '>=' not supported between instances of 'NoneType' and 'float'
  ```
- ❌ **最終結果**: 系統返回 0 個結果給用戶

---

## 🔍 根因分析

### 錯誤位置
- **檔案**: `backend/api/services/embedding_service.py`
- **方法 1**: `search_similar_documents_multi()` (Line 383-492)
- **方法 2**: `search_similar_documents()` (Line 242-313)
- **錯誤行**: Line 463, Line 297

### 問題根源

#### SQL 查詢缺少 NULL 過濾
```python
# ❌ 錯誤的 SQL (修復前)
sql = f"""
    SELECT 
        de.source_table,
        de.source_id,
        1 - (de.title_embedding <=> %s::vector) as title_score,
        1 - (de.content_embedding <=> %s::vector) as content_score,
        (%s * (1 - (de.title_embedding <=> %s::vector))) + 
        (%s * (1 - (de.content_embedding <=> %s::vector))) as final_score
    FROM document_embeddings de
    WHERE de.source_table = %s
    ORDER BY final_score DESC
    LIMIT %s
"""
```

#### 問題鏈
1. **資料庫中存在 NULL 向量**（某些文檔的 title_embedding 或 content_embedding 為 NULL）
2. **向量計算失敗**：
   - `1 - (NULL <=> vector)` → **NULL**
   - `(0.1 * NULL) + (0.9 * NULL)` → **NULL**
3. **final_score 變成 NULL**
4. **Python 比較失敗**：
   ```python
   if None >= 0.8:  # TypeError!
   ```

---

## ✅ 修復內容

### 方法 1: `search_similar_documents_multi()` (多向量搜索)

**修復位置**: Line 410-438

```python
# ✅ 修復後的 SQL
# 構建 SQL 查詢
sql_parts = []
params = []

# ✅ 修正：添加 NOT NULL 過濾，避免 NoneType 比較錯誤
base_conditions = ["de.title_embedding IS NOT NULL", "de.content_embedding IS NOT NULL"]

if source_table:
    base_conditions.append("de.source_table = %s")
    params.append(source_table)

sql_parts_str = " AND ".join(base_conditions)

sql = f"""
    SELECT 
        de.source_table,
        de.source_id,
        -- 標題相似度
        1 - (de.title_embedding <=> %s::vector) as title_score,
        -- 內容相似度
        1 - (de.content_embedding <=> %s::vector) as content_score,
        -- 加權最終分數
        (%s * (1 - (de.title_embedding <=> %s::vector))) + 
        (%s * (1 - (de.content_embedding <=> %s::vector))) as final_score,
        de.created_at,
        de.updated_at
    FROM document_embeddings de
    WHERE {sql_parts_str}
    ORDER BY final_score DESC
    LIMIT %s
"""
```

**關鍵改變**:
- 添加 `WHERE de.title_embedding IS NOT NULL AND de.content_embedding IS NOT NULL`
- 確保所有參與計算的向量都存在

---

### 方法 2: `search_similar_documents()` (單向量搜索)

**修復位置**: Line 267-289

```python
# ✅ 修復後的 SQL
# 構建 SQL 查詢
sql_parts = []
params = []

# ✅ 修正：添加 NOT NULL 過濾，避免 NoneType 比較錯誤
base_conditions = ["de.embedding IS NOT NULL"]

if source_table:
    base_conditions.append("de.source_table = %s")
    params.append(source_table)

sql_parts_str = " AND ".join(base_conditions)

sql = f"""
    SELECT 
        de.source_table,
        de.source_id,
        1 - (de.embedding <=> %s) as similarity_score,
        de.created_at,
        de.updated_at
    FROM {target_table} de
    WHERE {sql_parts_str}
    ORDER BY de.embedding <=> %s
    LIMIT %s
"""
```

**關鍵改變**:
- 添加 `WHERE de.embedding IS NOT NULL`
- 確保向量存在後才進行相似度計算

---

## 📊 測試驗證

### 測試 1: Stage 2 多向量搜索（直接測試）

**測試代碼**:
```python
from api.services.embedding_service import get_embedding_service

service = get_embedding_service()

results = service.search_similar_documents_multi(
    query='IOL 密碼',
    source_table='protocol_guide',
    limit=5,
    threshold=0.7,
    title_weight=0.1,  # Stage 2: 10% 標題
    content_weight=0.9  # Stage 2: 90% 內容
)
```

**測試結果**:
```
✅ 修復前: ERROR (NoneType comparison)
✅ 修復後: 返回 5 個結果

1. ID=10 (UNH-IOL)
   Final Score: 84.36%
   Title Score: 85.36%
   Content Score: 84.25%
   Match Type: balanced

2. ID=18, Final Score: 84.30%
3. ID=25, Final Score: 82.98%
4. ID=31, Final Score: 81.90%
5. ID=35, Final Score: 81.50%
```

---

### 測試 2: Stage 2 完整流程（Dify API）

**測試請求**:
```bash
curl -X POST "http://localhost/api/dify/knowledge/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "iol 密碼 __FULL_SEARCH__",
    "retrieval_setting": {
      "top_k": 1,
      "score_threshold": 0.8,
      "search_mode": "document_only",
      "stage": 2
    }
  }'
```

**測試結果**:
```json
{
    "records": [
        {
            "content": "UNH-IOL # 1. IOL 執行檔&文件 ...密碼為1...",
            "score": 0.8436237156391144,
            "title": "UNH-IOL",
            "metadata": {
                "id": 10,
                "created_at": "2025-10-20T11:24:32.710236",
                "updated_at": "2025-11-07T18:18:06.900408"
            }
        }
    ]
}
```

**驗證結果**:
- ✅ 返回正確文檔 (UNH-IOL)
- ✅ 分數超過閾值 (0.844 > 0.8)
- ✅ 包含密碼資訊 ("密碼為1")
- ✅ 無 NoneType 錯誤

---

### 測試 3: 兩階段搜索完整流程

**查詢**: "iol 密碼"

**流程**:
1. **Stage 1 (段落搜索)**: 
   - 權重: 95% 標題 / 5% 內容
   - 結果: 找到 `sec_8 "IOL 安裝需求"` (89% 相似度)
   - AI 回應: 包含不確定關鍵字 ("不知道")

2. **自動升級 Stage 2**:
   - 觸發條件: AI 不確定
   - 搜索模式: `document_only`
   - 權重: 10% 標題 / 90% 內容
   - 閾值: 0.8

3. **Stage 2 (文檔搜索)**:
   - ✅ **修復前**: ERROR (NoneType comparison)
   - ✅ **修復後**: 找到 `UNH-IOL` (84.36% 相似度)

4. **最終結果**:
   - ✅ 返回完整 UNH-IOL 文檔給用戶
   - ✅ 包含密碼資訊

---

## 🎯 修復影響範圍

### 直接影響
- ✅ **Protocol Assistant Stage 2 搜索** - 現在正常運作
- ✅ **RVT Assistant Stage 2 搜索** - 使用相同方法，同時修復
- ✅ **所有兩階段搜索系統** - 不再因 NULL 向量崩潰

### 間接影響
- ✅ **提升用戶體驗**: "iol 密碼" 等查詢現在返回正確結果
- ✅ **系統穩定性**: 消除所有知識庫的 Stage 2 崩潰風險
- ✅ **一致性**: Stage 1 和 Stage 2 現在都有 NULL 過濾

---

## 🔄 與前次修復的關聯

### 前次修復 (2025-11-25)
- **問題**: "CrystalDiskMark 是什麼？" 搜索失敗
- **根因**: Stage 1 段落搜索的標點符號清理問題
- **位置**: `library/protocol_guide/search_service.py` Line 135-138
- **修復**: 添加 `'？', '！', '。', '，'` 到清理邏輯

### 本次修復 (2025-11-26)
- **問題**: "iol 密碼" 觸發 Stage 2 後崩潰
- **根因**: Stage 2 文檔搜索的 NULL 向量處理問題
- **位置**: `backend/api/services/embedding_service.py` Line 410, 267
- **修復**: 添加 `IS NOT NULL` WHERE 條件

### 共同點
- **模式**: 兩次都是向量搜索的邊界條件處理問題
- **分散性**: 修復邏輯分散在不同檔案（search_service vs embedding_service）
- **缺乏統一**: 沒有集中的查詢驗證和向量檢查機制

---

## 📋 後續建議

### 短期改進
1. **統一驗證層**
   - 在 `embedding_service.py` 添加統一的向量檢查方法
   - 在所有 SQL 查詢中標準化 NOT NULL 過濾

2. **監控與警告**
   - 添加向量完整性監控（Celery 定時任務）
   - 發現 NULL 向量時記錄警告日誌

3. **文檔更新**
   - 更新向量搜索最佳實踐文檔
   - 添加 NULL 處理到標準 SQL 範本

### 長期改進
1. **向量生成完整性**
   - 確保所有文檔在創建/更新時生成向量
   - 添加向量生成失敗的重試機制

2. **查詢處理統一化**
   - 實現 Phase 1 建議的 `QueryCleaner` 統一類
   - 集中處理所有查詢清理和驗證邏輯

3. **測試覆蓋**
   - 添加 NULL 向量場景的單元測試
   - 添加兩階段搜索的集成測試

---

## 📚 相關文檔

- **查詢清理審計報告**: `/docs/development/query-cleaning-audit-report.md`
- **向量搜索指南**: `/docs/vector-search/vector-search-guide.md`
- **AI 助手範本指南**: `/docs/development/assistant-template-guide.md`

---

## ✅ 修復確認

- [x] 修復 `search_similar_documents_multi()` 方法
- [x] 修復 `search_similar_documents()` 方法
- [x] 重啟 Django 服務應用修復
- [x] 測試 Stage 2 多向量搜索
- [x] 測試 Stage 2 完整流程（Dify API）
- [x] 驗證 "iol 密碼" 查詢返回正確結果
- [x] 創建修復報告文檔

**修復完成時間**: 2025-11-26 09:15:00  
**測試驗證**: ✅ 通過  
**生產環境**: ✅ 已部署  
