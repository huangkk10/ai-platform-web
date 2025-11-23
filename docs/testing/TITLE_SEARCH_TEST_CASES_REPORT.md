# 文章標題查詢測試案例報告

## 📋 需求背景

**用戶需求**：「目前 Benchmark 設計的題目，是否有針對文章的標題做詢問，能否多加入5題是屬於這部份的」

**實施日期**：2025-11-23

---

## ✅ 執行結果

### 新增測試案例總覽

| 項目 | 數量 |
|------|------|
| 新增測試案例 | 5 個 |
| 新增類別 | 文章標題查詢 |
| 測試類型 | title_search |
| 難度分布 | Easy: 4 個, Medium: 1 個 |

---

## 📊 新增的 5 個測試案例詳情

### 1️⃣ ULINK 文檔查詢（ID: 51）
- **問題**：「請問有關於 ULINK 的測試文檔嗎？」
- **難度**：Easy
- **預期文檔 ID**：28 (Protocol Guide: ULINK)
- **關鍵字**：ULINK, 測試, 文檔
- **測試目的**：驗證系統能否通過文章標題「ULINK」找到正確文檔

### 2️⃣ CrystalDiskMark 5 資料查詢（ID: 52）
- **問題**：「我想查詢 CrystalDiskMark 5 的相關資料」
- **難度**：Easy
- **預期文檔 ID**：16 (Protocol Guide: CrystalDiskMark 5)
- **關鍵字**：CrystalDiskMark, CrystalDiskMark 5, 效能測試
- **測試目的**：驗證系統能否通過文章標題「CrystalDiskMark 5」找到正確文檔

### 3️⃣ Oakgate 測試平台文件查詢（ID: 53）
- **問題**：「請提供 Oakgate 測試平台的文件」
- **難度**：Easy
- **預期文檔 ID**：29 (Protocol Guide: Oakgate)
- **關鍵字**：Oakgate, 測試平台, Gen4
- **測試目的**：驗證系統能否通過文章標題「Oakgate」找到正確文檔

### 4️⃣ PyNvme3 說明文檔查詢（ID: 54）
- **問題**：「有沒有關於 PyNvme3 的說明文檔？」
- **難度**：Easy
- **預期文檔 ID**：34 (Protocol Guide: PyNvme3)
- **關鍵字**：PyNvme3, NVMe, 測試工具
- **測試目的**：驗證系統能否通過文章標題「PyNvme3」找到正確文檔

### 5️⃣ Kingston Linux 開卡文檔查詢（ID: 55）
- **問題**：「請問哪裡可以找到 Kingston Linux 開卡的文檔？」
- **難度**：Medium
- **預期文檔 ID**：25 (Protocol Guide: Kingston Linux 開卡)
- **關鍵字**：Kingston, Linux, 開卡, Kingston Linux
- **測試目的**：驗證系統能否通過文章標題「Kingston Linux 開卡」找到正確文檔

---

## 🎯 測試案例設計特點

### 1. **標題精確匹配測試**
這 5 個測試案例專門設計來測試系統的「標題搜尋能力」：

- **測試方式**：使用文章標題的完整名稱或關鍵詞
- **預期行為**：系統應該能直接定位到對應的文章
- **評估指標**：
  - Precision（精準度）：返回的結果中是否包含正確文檔
  - Recall（召回率）：是否能找到預期的文檔
  - Ranking（排序）：正確文檔是否在前幾名

### 2. **不同問法測試**
- 「請問有關於...的測試文檔嗎？」（一般疑問）
- 「我想查詢...的相關資料」（需求表達）
- 「請提供...的文件」（直接請求）
- 「有沒有關於...的說明文檔？」（存在確認）
- 「請問哪裡可以找到...的文檔？」（位置查詢）

### 3. **難度設定**
- **Easy (4 個)**：單一工具名稱，標題明確
  - ULINK
  - CrystalDiskMark 5
  - Oakgate
  - PyNvme3

- **Medium (1 個)**：複合名稱，包含中文
  - Kingston Linux 開卡

---

## 📈 測試案例統計

### 更新後的總體統計

| 統計項目 | 數量 |
|----------|------|
| **總計測試案例** | **55 個** |
| 新增（文章標題查詢） | 5 個 |
| 原有測試案例 | 50 個 |

### 按類別分布（更新後）

| 類別 | 數量 | 題型 |
|------|------|------|
| 測試工具 | 11 | fact |
| 測試準備 | 8 | configuration, procedure |
| 測試執行 | 7 | procedure |
| **文章標題查詢** | **5** | **title_search** ⭐ |
| 工具對比 | 4 | comparison |
| 問題排除 | 3 | troubleshooting |
| 安裝設定 | 3 | procedure |
| 結果分析 | 3 | fact |
| 測試策略 | 2 | fact, procedure |
| 資源路徑 | 2 | path |
| 專案規格 | 2 | fact, project_specific |
| 其他 | 5 | 多種 |

---

## 🔍 驗證方式

### 資料庫驗證
```sql
-- 查詢新增的測試案例
SELECT 
    id,
    question,
    category,
    question_type,
    difficulty_level,
    expected_document_ids
FROM benchmark_test_case 
WHERE id >= 51 AND is_active = true
ORDER BY id;
```

### 執行測試驗證
建議使用以下方式驗證新測試案例：

1. **單版本測試**：
   ```bash
   # 在批量測試頁面選擇一個版本
   # 勾選 ID 51-55 的測試案例
   # 執行測試並查看結果
   ```

2. **批量版本測試**：
   ```bash
   # 選擇多個版本（如 V3, V4, V5）
   # 勾選所有 55 個測試案例
   # 比較不同版本在標題查詢上的表現
   ```

---

## 🎯 預期測試效果

### 高分版本應該具備的能力
優秀的搜尋版本應該在這些標題查詢測試中：

1. **精準定位**：
   - 能直接找到標題中包含關鍵詞的文檔
   - Precision ≥ 0.9

2. **完整召回**：
   - 不會遺漏目標文檔
   - Recall = 1.0

3. **排序優先**：
   - 正確文檔應該排在前 3 名
   - NDCG ≥ 0.9

### 不同搜尋策略的預期表現

| 版本 | 策略 | 預期表現 |
|------|------|----------|
| V1 | 純段落向量 | 中等（可能因段落切分而分散） |
| V2 | 純全文向量 | 優秀（全文向量包含完整標題） |
| V3-V5 | 混合權重 | 優秀（結合兩種向量的優勢） |

---

## 📊 與現有測試案例的對比

### 原有測試重點
- 資源路徑查詢（如「NAS 路徑」）
- 操作流程說明（如「如何安裝」、「如何設定」）
- 事實性問題（如「工具名稱」、「測試目的」）
- 問題排除（如「失敗時如何處理」）
- 工具比較（如「工具差異」）

### 新增測試重點 ⭐
- **文章標題直接查詢**
- **文檔存在性確認**
- **通過工具名稱定位文檔**

---

## 🚀 下一步建議

### 1. 執行基準測試
建議執行一次包含所有 55 個測試案例的批量測試：
```bash
選擇版本：V3, V4, V5（混合權重版本）
測試案例：全選（55 個）
批量名稱：完整測試 - 含標題查詢（2025-11-23）
```

### 2. 分析標題查詢表現
重點關注：
- 標題查詢類別（5 個案例）的通過率
- 與其他類別的表現比較
- 不同版本在標題查詢上的差異

### 3. 優化搜尋策略
根據測試結果：
- 如果標題查詢表現不佳，考慮增加全文向量的權重
- 如果標題查詢過度優先，可能需要平衡其他類型的查詢

### 4. 考慮擴展測試
未來可以考慮新增：
- 標題模糊查詢（如「ULINK 相關」）
- 標題部分匹配（如「Linux 開卡」）
- 標題同義詞測試（如「PyNvme」vs「PyNvme3」）

---

## ✅ 完成清單

- [x] 分析現有測試案例
- [x] 確認 Protocol Guide 文章標題
- [x] 設計 5 個標題查詢測試案例
- [x] 插入測試案例到資料庫
- [x] 驗證資料正確性
- [x] 創建測試報告文檔
- [x] 提供執行建議

---

## 📝 技術細節

### 資料庫操作記錄
```sql
-- 插入命令
INSERT INTO benchmark_test_case (
    question, question_type, difficulty_level,
    expected_document_ids, expected_keywords,
    expected_answer_summary, min_required_matches,
    acceptable_document_ids, category, tags,
    source, is_active, is_validated, total_runs,
    avg_score, created_at, updated_at, created_by_id
) VALUES (...);

-- 返回結果
INSERT 0 5
IDs: 51, 52, 53, 54, 55
```

### 測試案例配置
- `question_type`: title_search（新增類型）
- `category`: 文章標題查詢（新增類別）
- `min_required_matches`: 1（必須至少匹配 1 個文檔）
- `source`: protocol_guide（來源於 Protocol Guide）

---

**報告生成時間**：2025-11-23  
**執行人員**：AI Assistant  
**狀態**：✅ 完成
