# Protocol Assistant 引用來源缺失問題 - 正確分析報告

**報告日期**：2025-11-10  
**分析者**：AI Platform Team  
**狀態**：✅ 問題已正確診斷

---

## 🔍 問題重述

用戶詢問「Cup」檔案相關問題，AI 找到並引用了其他檔案（ISC 進階問題 82%, Burn in Test 81%），但引用來源中沒有顯示 "Cup" 這份檔案。

---

## ✅ 正確的診斷結果

### 系統整體狀態：**健康** 🟢

```
總檔案數：   6 個
完全健康：   5 個 (83.3%) ✅
有問題：     1 個 (16.7%) ⚠️
系統健康度： 83.3% 🟡 良好
```

### 詳細向量狀態

| ID | 標題 | 長度 | 整篇向量 | Section 向量 | Section 數 | 狀態 |
|----|------|------|----------|--------------|-----------|------|
| 10 | UNH-IOL | 1219 | ✅ | ✅ | 11 | 健康 |
| 15 | Burn in Test | 1139 | ✅ | ✅ | 6 | 健康 |
| 16 | CrystalDiskMark 5 | 784 | ✅ | ✅ | 4 | 健康 |
| 17 | 阿呆 | 147 | ✅ | ✅ | 2 | 健康 |
| 18 | I3C 相關說明 | 3586 | ✅ | ✅ | 24 | 健康 |
| 19 | **Cup** | **1** | ✅ | **❌** | **0** | **問題** |

---

## 🎯 核心問題

**只有 "Cup" 檔案有問題！**

### 問題原因

1. **內容過短**：只有 1 個字元 "a"
2. **缺少結構**：沒有任何 Markdown 標題（# ## ###）
3. **無法分割**：Section 分割器無法識別段落
4. **向量缺失**：`document_section_embeddings` 表中沒有記錄

### 為什麼其他檔案正常？

所有其他檔案都有完整的 Markdown 結構：

- **UNH-IOL**: 11 個 sections ✅（內容 1219 字元）
- **Burn in Test**: 6 個 sections ✅（內容 1139 字元）
- **CrystalDiskMark 5**: 4 個 sections ✅（內容 784 字元）
- **阿呆**: 2 個 sections ✅（內容只有 147 字元，但有標題結構！）
- **I3C 相關說明**: 24 個 sections ✅（內容 3586 字元）

**關鍵發現**：即使「阿呆」檔案只有 147 字元，因為有 `# 個人介紹` 等標題，仍能正常生成 section 向量！

---

## 💡 為什麼用戶之前能正常使用？

**完全正確！** 因為：

1. ✅ 其他 5 個檔案都有完整結構
2. ✅ Section 向量正常生成
3. ✅ 搜尋系統運作正常
4. ✅ 引用來源正確顯示

**只有 "Cup" 是特例**，因為它只是一個測試檔案（內容只有 "a"）。

---

## 🔧 解決方案

### 方案 1：編輯檔案（推薦）⭐

**步驟**：
1. 訪問編輯頁面：
   ```
   http://localhost/knowledge/protocol-guide/markdown-edit/19
   ```

2. 添加 Markdown 結構，例如：
   ```markdown
   # Cup 介紹
   
   ## 基本說明
   Cup 是一個...
   
   ## 用途
   主要用於...
   
   ## 注意事項
   - 注意點 1
   - 注意點 2
   ```

3. 儲存後，系統會自動：
   - ✅ 生成 section 向量
   - ✅ "Cup" 立即可被搜尋到
   - ✅ 會出現在引用來源中

### 方案 2：手動生成向量（備用）

如果編輯後向量仍未生成，可手動執行：

```python
# 進入 Django shell
docker exec -it ai-django python manage.py shell

# 執行以下代碼
from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService

cup = ProtocolGuide.objects.get(id=19)
service = SectionVectorizationService()

result = service.vectorize_document_sections(
    source_table='protocol_guide',
    source_id=19,
    markdown_content=cup.content,
    metadata={'title': cup.title}
)

print(f"✅ 生成 {result} 個 sections")
```

---

## 🧪 驗證方法

### 1. 使用檢查腳本（推薦）

```bash
./check_all_guides_fixed.sh
```

**預期結果**（修復後）：
```
ID: 19  | Cup  | 長度: 200+  | 整篇向量: ✅ | Section: ✅ (3+ 個) | ✅ 健康

系統健康度： 100.0% 🟢 優秀
```

### 2. 直接查詢資料庫

```bash
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
    COUNT(*) as section_count
FROM document_section_embeddings
WHERE source_table='protocol_guide' 
    AND document_id='doc_19';
"
```

**預期結果**（修復後）：
```
section_count
-------------
          3+
```

### 3. 測試搜尋功能

```bash
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "Cup",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**預期結果**（修復後）：
應該能找到 "Cup" 檔案並返回內容。

---

## ❌ 之前分析的錯誤

### 我的錯誤

1. **檢查腳本 Bug**：
   - ❌ 沒有正確處理 `document_section_embeddings.document_id` 的字串格式（`doc_10`）
   - ❌ 直接用數字 ID 比對，導致找不到資料
   - ❌ 誤判為「所有檔案都沒有 section 向量」

2. **錯誤結論**：
   - ❌ 誤報系統健康度為 0%
   - ❌ 誤報需要修復 6 個檔案
   - ❌ 提供了不必要的「大規模修復方案」

### 正確的事實

| 項目 | 錯誤分析 | 正確分析 |
|------|----------|----------|
| 系統健康度 | 0% 🔴 | 83.3% 🟡 |
| 需要修復 | 6 個檔案 | 1 個檔案 |
| 問題範圍 | 全系統 | 只有 Cup |
| 用戶體驗 | 無法使用 | 正常使用 ✅ |

---

## 📊 技術細節：document_id 格式

### 資料庫欄位格式差異

```sql
-- protocol_guide 表
id: INTEGER (10, 15, 16, 17, 18, 19)

-- document_embeddings 表
source_id: INTEGER (10, 15, 16, 17, 18, 19)

-- document_section_embeddings 表
document_id: VARCHAR ("doc_10", "doc_15", "doc_16", ...)
```

### 正確的查詢方法

```sql
-- ❌ 錯誤（會找不到資料）
SELECT * FROM document_section_embeddings 
WHERE source_table='protocol_guide' AND document_id = 10;

-- ✅ 正確（使用字串格式）
SELECT * FROM document_section_embeddings 
WHERE source_table='protocol_guide' AND document_id = 'doc_10';

-- ✅ 正確（動態組合）
SELECT * 
FROM protocol_guide pg
LEFT JOIN document_section_embeddings dse 
    ON dse.source_table='protocol_guide' 
    AND dse.document_id = ('doc_' || pg.id);
```

---

## 🎯 總結

### 實際問題

- **範圍**：只有 1 個檔案（Cup）
- **原因**：內容太短且無結構（只有 "a"）
- **影響**：不影響其他檔案的正常使用
- **嚴重度**：低（測試檔案）

### 系統狀態

- **整體健康度**：83.3% 🟡 良好
- **可用檔案**：5/6 (83.3%) ✅
- **向量生成機制**：正常運作 ✅
- **搜尋系統**：正常運作 ✅

### 用戶體驗

- ✅ 其他 5 個檔案都能正常搜尋
- ✅ 引用來源正確顯示
- ✅ AI 回答準確
- ❌ 只有 "Cup" 無法被搜尋到（因為內容不完整）

### 修復建議

**優先度**：低（如果 Cup 只是測試檔案）

**修復方法**：
1. 編輯 Cup 檔案，添加 Markdown 結構
2. 儲存後自動生成向量
3. 健康度立即達到 100% ✅

**預防措施**：
- 創建檔案時確保包含至少 2-3 個 Markdown 標題
- 內容長度建議 > 100 字元
- 可參考「阿呆」檔案（147 字元但有結構，正常運作）

---

## 📚 相關文檔

- **診斷工具**：`./check_all_guides_fixed.sh`（修正版）
- **單檔診斷**：`./diagnose_cup_missing.sh <id>`
- **向量生成說明**：`/docs/vector-search/protocol-guide-vector-auto-generation.md`
- **內容創建規範**：`/docs/features/protocol-guide-content-validation-guide.md`

---

## 🙏 致歉說明

**對於之前的誤判，我深表歉意！**

**錯誤**：
- 檢查腳本沒有正確處理 document_id 格式
- 導致誤報所有檔案都缺少向量
- 給了不必要的「大規模修復方案」

**事實**：
- 您的系統非常健康（83.3%）
- 您的使用經驗完全正確
- 只有 1 個測試檔案需要修復
- 不需要大規模改動

**改進**：
- 已修正檢查腳本（`check_all_guides_fixed.sh`）
- 更新了所有相關文檔
- 確保未來不會再發生類似錯誤

---

**報告者**：AI Platform Team  
**更新日期**：2025-11-10  
**版本**：v2.0（修正版）  
**狀態**：✅ 已確認正確
