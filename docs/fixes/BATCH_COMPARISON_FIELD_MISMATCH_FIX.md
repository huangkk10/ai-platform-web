# 批量測試對比頁面欄位名稱不匹配修復報告

**日期**: 2025-11-23  
**問題 ID**: Field Mismatch in Batch Comparison  
**嚴重程度**: 高（資料正確但前端顯示為 0）

---

## 📋 問題描述

用戶反映批量測試對比頁面中，所有版本的 Precision、Recall、F1 Score 都顯示為 **0.0%**，即使綜合分數有差異（47分左右）。

**症狀**：
- ✅ 資料庫中有正確的數值（例如：precision=0.1988, recall=0.7273）
- ❌ 前端對比頁面顯示：Precision=0.0%, Recall=0.0%, F1=0.0%
- ✅ Overall Score 顯示正常（47分左右）

---

## 🔍 根本原因

### 問題 1：前端欄位名稱錯誤

**檔案**: `frontend/src/pages/benchmark/BatchComparisonPage.js`

**錯誤代碼**（第 116-118 行）：
```javascript
precision: parseFloat(run.precision) || 0,      // ❌ 欄位不存在
recall: parseFloat(run.recall) || 0,            // ❌ 欄位不存在
f1_score: parseFloat(run.f1_score) || 0,        // ❌ 欄位不存在
```

**問題**：
- 前端嘗試讀取 `run.precision`、`run.recall`、`run.f1_score`
- 但 API 返回的欄位名稱是 `run.avg_precision`、`run.avg_recall`、`run.avg_f1_score`
- 結果：`parseFloat(undefined) || 0` = `0`

### 問題 2：數值單位不一致

**資料庫儲存**：
- `avg_precision`: 0.1988（0-1 範圍）
- `avg_recall`: 0.7273（0-1 範圍）
- `avg_f1_score`: 0.3061（0-1 範圍）

**前端顯示**：需要轉換為百分比（0-100 範圍）

---

## 🛠️ 修復方案

### 修復 1：BatchComparisonPage.js 欄位名稱與單位

**檔案**: `frontend/src/pages/benchmark/BatchComparisonPage.js`

**修改前**（錯誤）：
```javascript
precision: parseFloat(run.precision) || 0,
recall: parseFloat(run.recall) || 0,
f1_score: parseFloat(run.f1_score) || 0,
```

**修改後**（正確）：
```javascript
precision: (parseFloat(run.avg_precision) || 0) * 100,  // ✅ 修正欄位名稱並轉為百分比
recall: (parseFloat(run.avg_recall) || 0) * 100,        // ✅ 修正欄位名稱並轉為百分比
f1_score: (parseFloat(run.avg_f1_score) || 0) * 100,    // ✅ 修正欄位名稱並轉為百分比
```

**改進**：
1. 使用正確的欄位名稱（`avg_precision` 而非 `precision`）
2. 乘以 100 轉換為百分比格式（19.88% 而非 0.1988）

### 修復 2：batch_version_tester.py 百分比轉換

**檔案**: `backend/library/benchmark/batch_version_tester.py`

**修改前**（缺少百分比轉換）：
```python
"precision": float(t.avg_precision or 0),
"recall": float(t.avg_recall or 0),
"f1_score": float(t.avg_f1_score or 0)
```

**修改後**（加入百分比轉換）：
```python
"precision": float(t.avg_precision or 0) * 100,  # 轉為百分比
"recall": float(t.avg_recall or 0) * 100,        # 轉為百分比
"f1_score": float(t.avg_f1_score or 0) * 100     # 轉為百分比
```

---

## ✅ 修復驗證

### 測試案例：Batch ID 20251123_110225

**資料庫數值**：
```
Test Run 121 (V5): 
  avg_precision = 0.1988
  avg_recall = 0.7273
  avg_f1_score = 0.3061
  overall_score = 46.91

Test Run 125 (V1):
  avg_precision = 0.1988
  avg_recall = 0.7273
  avg_f1_score = 0.3061
  overall_score = 47.09
```

**預期前端顯示**（修復後）：
- Precision: **19.88%**
- Recall: **72.73%**
- F1 Score: **30.61%**
- Overall Score: 46.91 - 47.09

---

## 📊 欄位名稱對照表

| 資料庫 Model 欄位 | API Serializer 返回 | 前端應該讀取 | 數值範圍 | 顯示格式 |
|-----------------|-------------------|------------|---------|---------|
| `avg_precision` | `avg_precision` | `run.avg_precision` | 0-1 | × 100 = % |
| `avg_recall` | `avg_recall` | `run.avg_recall` | 0-1 | × 100 = % |
| `avg_f1_score` | `avg_f1_score` | `run.avg_f1_score` | 0-1 | × 100 = % |
| `avg_response_time` | `avg_response_time` | `run.avg_response_time` | ms | 直接顯示 |
| `overall_score` | `overall_score` | `run.overall_score` | 0-100 | 直接顯示 |

---

## 🔄 相關修復記錄

本次修復是 **第二次欄位名稱不匹配問題**：

1. **第一次**（2025-11-23 上午）：
   - **檔案**: `test_runner.py`
   - **問題**: 使用 `precision_pct` 而非 `avg_precision`
   - **結果**: 資料無法儲存到資料庫
   - **修復**: [BATCH_ID_NOT_SAVED_FIX.md](./BATCH_ID_NOT_SAVED_FIX.md)

2. **第二次**（2025-11-23 下午）：
   - **檔案**: `BatchComparisonPage.js`、`batch_version_tester.py`
   - **問題**: 前端讀取 `precision` 而非 `avg_precision`
   - **結果**: 資料正確但前端顯示為 0
   - **修復**: 本文件

---

## 💡 預防措施建議

### 1. 統一命名規範文檔
創建 `/docs/development/API_FIELD_NAMING_CONVENTION.md`：
- 定義所有 API 欄位的標準命名
- Model 欄位 → Serializer 欄位 → 前端變數名稱的對照表

### 2. 前端 TypeScript 轉換
使用 TypeScript 定義 API 回應的介面：
```typescript
interface BenchmarkTestRun {
  id: number;
  overall_score: number;
  avg_precision: number;  // ✅ 明確定義欄位名稱
  avg_recall: number;
  avg_f1_score: number;
  avg_response_time: number;
  // ... 其他欄位
}
```

### 3. 單元測試覆蓋
為資料轉換邏輯添加單元測試：
```javascript
describe('generateRealComparison', () => {
  it('should correctly extract avg_precision from test run', () => {
    const run = { avg_precision: 0.1988 };
    const result = generateRealComparison([run]);
    expect(result.versions[0].precision).toBe(19.88);
  });
});
```

### 4. API 回應驗證
在開發環境中添加 API 回應驗證：
```javascript
if (process.env.NODE_ENV === 'development') {
  if (!run.avg_precision && run.precision) {
    console.warn('⚠️ API 欄位名稱可能錯誤：使用 precision 而非 avg_precision');
  }
}
```

---

## 📝 操作步驟記錄

```bash
# 1. 修改前端欄位名稱
# 檔案：frontend/src/pages/benchmark/BatchComparisonPage.js
# 修改：run.precision → run.avg_precision（並 × 100）

# 2. 修改後端百分比轉換
docker exec ai-django bash -c "
  cd /app/library/benchmark
  # 修改 batch_version_tester.py 的 _generate_comparison 方法
  # 加入 * 100 轉換為百分比
"

# 3. 重啟服務
docker compose restart django react

# 4. 測試驗證
# 訪問：http://10.10.172.127/benchmark/comparison/20251123_110225
# 預期看到：Precision=19.88%, Recall=72.73%, F1=30.61%
```

---

## ✅ 修復狀態

- **前端修復**: ✅ 完成（BatchComparisonPage.js）
- **後端修復**: ✅ 完成（batch_version_tester.py）
- **服務重啟**: ✅ 完成（Django + React）
- **測試驗證**: ⏳ 等待用戶確認

---

## 🎯 用戶操作指南

**請按以下步驟驗證修復**：

1. **刷新瀏覽器**
   - 按 `Ctrl + Shift + R`（強制刷新，清除快取）

2. **重新查看對比頁面**
   - 訪問：批量測試對比頁面（Batch ID: 20251123_110225）

3. **預期結果**
   - ✅ Precision 應顯示：**19.88%**（而非 0.0%）
   - ✅ Recall 應顯示：**72.73%**（而非 0.0%）
   - ✅ F1 Score 應顯示：**30.61%**（而非 0.0%）
   - ✅ Overall Score 應顯示：**46.91 - 47.09**

4. **如果仍然顯示 0.0%**
   - 檢查瀏覽器開發者工具（F12 → Network）
   - 查看 API 回應是否包含 `avg_precision` 欄位
   - 確認前端 JavaScript 沒有快取問題

---

**修復完成時間**: 2025-11-23 下午  
**影響範圍**: 批量測試對比頁面的 Precision/Recall/F1 Score 顯示  
**修復者**: AI Assistant  
**審核者**: 待用戶確認
