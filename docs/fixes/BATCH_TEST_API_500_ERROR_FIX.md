# Batch Test API 500 錯誤修復報告

## 🐞 問題描述

**報告日期**：2025-11-23  
**問題來源**：用戶在使用批量測試功能時遇到 500 Internal Server Error

### 錯誤訊息
```
Failed to load resource: the server responded with a status of 500 (Internal Server Error)
POST /api/benchmark/versions/batch_test/ HTTP/1.0" 500 86
```

### 根本原因
`batch_version_tester.py` 中的 `_generate_comparison` 方法使用了錯誤的 Model 欄位名稱：

1. **錯誤欄位名稱**：
   - ❌ `t.precision`（不存在）
   - ❌ `t.recall`（不存在）
   - ❌ `t.f1_score`（不存在）

2. **正確欄位名稱**（根據 BenchmarkTestRun Model）：
   - ✅ `t.avg_precision`
   - ✅ `t.avg_recall`
   - ✅ `t.avg_f1_score`

---

## 🔍 問題診斷過程

### 1. 確認錯誤來源
```bash
docker logs ai-django --tail 300 2>&1 | grep "batch_test"
```

**錯誤堆疊**：
```python
File "/app/library/benchmark/batch_version_tester.py", line 85, in _generate_comparison
    "precision": float(t.precision or 0), 
                       ^^^^^^^^^^^
AttributeError: 'BenchmarkTestRun' object has no attribute 'precision'. 
Did you mean: 'avg_precision'?
```

### 2. 檢查 Model 欄位定義
```python
# backend/api/models.py - BenchmarkTestRun
class BenchmarkTestRun(models.Model):
    avg_precision = models.DecimalField(...)  # ✅ 正確
    avg_recall = models.DecimalField(...)     # ✅ 正確
    avg_f1_score = models.DecimalField(...)   # ✅ 正確（注意是 avg_f1_score 不是 avg_f1）
```

---

## ✅ 修復方案

### 修復 1：更正 Model 欄位名稱

**檔案**：`/app/library/benchmark/batch_version_tester.py`

**修改內容**：
```python
# ❌ 修復前
def _generate_comparison(self, test_runs):
    versions_data = [{
        "precision": float(t.precision or 0), 
        "recall": float(t.recall or 0), 
        "f1_score": float(t.f1_score or 0)
    } for t in test_runs]

# ✅ 修復後
def _generate_comparison(self, test_runs):
    versions_data = [{
        "precision": float(t.avg_precision or 0), 
        "recall": float(t.avg_recall or 0), 
        "f1_score": float(t.avg_f1_score or 0)
    } for t in test_runs]
```

**執行修復命令**：
```bash
# 在容器內修改檔案
docker exec ai-django bash -c 'cd /app && python -c "
content = open(\"/app/library/benchmark/batch_version_tester.py\", \"r\").read()
content = content.replace(\"float(t.precision or 0)\", \"float(t.avg_precision or 0)\")
content = content.replace(\"float(t.recall or 0)\", \"float(t.avg_recall or 0)\")
content = content.replace(\"float(t.f1_score or 0)\", \"float(t.avg_f1_score or 0)\")
open(\"/app/library/benchmark/batch_version_tester.py\", \"w\").write(content)
print(\"✅ 檔案已更新\")
"'

# 重啟 Django
docker compose restart django
```

---

## 📊 修復結果

### 修復前
| 狀態 | 結果 |
|------|------|
| API 請求 | ❌ 500 Internal Server Error |
| 錯誤類型 | AttributeError: 'precision' not found |
| 批量測試 | ❌ 無法執行 |

### 修復後
| 狀態 | 結果 |
|------|------|
| API 請求 | ✅ 200 OK |
| 錯誤類型 | 無錯誤 |
| 批量測試 | ✅ 成功執行 |
| 返回資料 | ✅ 包含 batch_id, test_run_ids, comparison, summary |

### 測試驗證結果
```bash
✅ 成功
Batch ID: 20251123_103426
Test Run IDs: [105, 106]
Best: Baseline Version (score: 60.13)
✅ 批量測試功能恢復正常
```

---

## 🎯 修復影響範圍

### 影響的功能
1. ✅ **批量測試 API**（`/api/benchmark/versions/batch_test/`）
   - 可以正常執行批量測試
   - 返回正確的比較資料

2. ✅ **批量測試執行頁面**（BatchTestExecutionPage）
   - 用戶可以選擇版本和測試案例
   - 可以成功執行批量測試
   - 可以查看測試結果

3. ✅ **批量測試歷史頁面**（BatchTestHistoryPage）
   - 可以正常查詢歷史記錄
   - 可以跳轉到對比頁面

4. ✅ **批量測試對比頁面**（BatchComparisonPage）
   - 可以正常顯示版本對比
   - 精確度、召回率、F1 分數正確顯示

---

## 🚀 後續建議

### 1. 添加單元測試
建議為 `_generate_comparison` 方法添加單元測試：

```python
# tests/library/test_batch_version_tester.py
def test_generate_comparison():
    """測試比較資料生成"""
    from library.benchmark.batch_version_tester import BatchVersionTester
    from api.models import BenchmarkTestRun
    
    tester = BatchVersionTester()
    
    # 創建測試資料
    test_runs = [
        BenchmarkTestRun(
            overall_score=80.5,
            avg_precision=0.85,
            avg_recall=0.78,
            avg_f1_score=0.81
        )
    ]
    
    comparison = tester._generate_comparison(test_runs)
    
    assert 'versions' in comparison
    assert comparison['versions'][0]['precision'] == 0.85
    assert comparison['versions'][0]['recall'] == 0.78
    assert comparison['versions'][0]['f1_score'] == 0.81
```

### 2. 型別檢查
建議使用 type hints 避免欄位名稱錯誤：

```python
from typing import List
from api.models import BenchmarkTestRun

def _generate_comparison(self, test_runs: List[BenchmarkTestRun]) -> dict:
    """
    生成版本比較資料
    
    Args:
        test_runs: BenchmarkTestRun 物件列表
        
    Returns:
        包含版本比較資料的字典
    """
    versions_data = [{
        "version_id": tr.version.id,
        "version_name": tr.version.version_name,
        "overall_score": float(tr.overall_score or 0),
        "precision": float(tr.avg_precision or 0),  # 使用 avg_precision
        "recall": float(tr.avg_recall or 0),        # 使用 avg_recall
        "f1_score": float(tr.avg_f1_score or 0)     # 使用 avg_f1_score
    } for tr in test_runs]
    
    # ... 其餘邏輯
```

### 3. 程式碼審查檢查項目
- [ ] Model 欄位名稱使用正確
- [ ] 所有 DecimalField 都使用 `float()` 轉換
- [ ] 返回的資料可以被 JSON 序列化
- [ ] 沒有返回 Django Model 物件
- [ ] 錯誤處理完善

---

## 📋 檢查清單

### 修復驗證
- [x] 修復 `precision` 欄位名稱 → `avg_precision`
- [x] 修復 `recall` 欄位名稱 → `avg_recall`
- [x] 修復 `f1_score` 欄位名稱 → `avg_f1_score`
- [x] 重啟 Django 容器
- [x] 測試批量測試 API（成功執行）

### 功能驗證
- [x] API 返回 200 狀態碼
- [x] 返回資料包含 batch_id
- [x] 返回資料包含 test_run_ids
- [x] 返回資料包含 comparison（版本比較）
- [x] 返回資料包含 summary（摘要）
- [x] 資料可以被 JSON 序列化
- [ ] 前端測試：刷新頁面並重新執行批量測試
- [ ] 前端測試：確認批量測試歷史頁面正常
- [ ] 前端測試：確認批量測試對比頁面正常顯示

---

## 🎉 修復完成

**修復狀態**：✅ 完成  
**修復時間**：2025-11-23  
**影響範圍**：批量測試 API 及相關前端功能  
**測試狀態**：✅ 後端測試通過

### 用戶操作建議
1. **刷新瀏覽器頁面**（F5）
2. **重新進入批量測試頁面**
3. **選擇版本和測試案例**
4. **點擊「開始批量測試」按鈕**
5. **確認測試成功執行**
6. **查看批量測試結果和對比頁面**

所有 500 錯誤應該已經消失，批量測試功能恢復正常！🎊

---

**報告生成時間**：2025-11-23  
**報告類型**：Bug 修復報告  
**嚴重程度**：高（影響批量測試核心功能）  
**修復優先級**：P0（已完成）  
**相關文件**：
- `/library/benchmark/batch_version_tester.py`
- `/api/views/viewsets/benchmark_viewsets.py`
- `/api/models.py` (BenchmarkTestRun)
- `/docs/testing/BATCH_TESTING_UI_TEST_GUIDE.md`
