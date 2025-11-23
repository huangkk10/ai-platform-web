# Batch ID 未保存到資料庫問題修復報告

## 📋 問題描述

### 用戶報告
用戶在批量測試執行頁面看到警告訊息：
```
⚠️ 找不到對應的批量測試記錄 (batch_id: 20251123_103552)
```

### 問題現象
- 批量測試成功執行，生成了 test runs
- 但前端無法透過 batch_id 查詢到相關的測試記錄
- 批量測試歷史頁面無法顯示測試記錄

### 截圖
![問題截圖](../screenshots/batch_id_not_found.png)

---

## 🔍 問題診斷

### 步驟 1：檢查資料庫
```sql
SELECT id, run_name, notes, created_at
FROM benchmark_test_run 
WHERE run_type = 'batch_comparison' 
ORDER BY created_at DESC 
LIMIT 5;
```

**發現**：`notes` 欄位為**空值**！

```
 id  | run_name                              | notes |  created_at
-----+---------------------------------------+-------+------------------
 111 | 批量測試 2025/11/23 上午10:35:46 - V1 |       | 2025-11-23 10:36
 110 | 批量測試 2025/11/23 上午10:35:46 - V2 |       | 2025-11-23 10:36
```

### 步驟 2：檢查 batch_version_tester.py

```python
def _run_single_version_test(self, version, test_cases, batch_id, batch_name, notes):
    from library.benchmark.test_runner import BenchmarkTestRunner
    runner = BenchmarkTestRunner(version_id=version.id, verbose=self.verbose)
    
    # ✅ 代碼正確：組合了 batch_notes
    batch_notes = "批次 ID: " + batch_id
    if notes:
        batch_notes = batch_notes + "\n" + notes
    
    return runner.run_batch_tests(
        test_cases=test_cases, 
        run_name=batch_name + " - " + version.version_name,
        run_type="batch_comparison", 
        notes=batch_notes  # ✅ 有傳遞 notes 參數
    )
```

### 步驟 3：檢查 test_runner.py

```python
def run_batch_tests(self, test_cases, run_name, run_type='manual', notes=''):
    self._log(f"開始測試: {run_name}")
    
    # ❌ 問題：沒有使用 notes 參數！
    test_run = BenchmarkTestRun.objects.create(
        version=self.version, 
        run_name=run_name, 
        run_type=run_type,
        # notes=notes,  ← 遺漏這一行！
        total_test_cases=len(test_cases), 
        status='running', 
        started_at=timezone.now()
    )
```

**根本原因**：`run_batch_tests` 方法雖然接收了 `notes` 參數，但在創建 `BenchmarkTestRun` 時**忘記使用**這個參數！

---

## 🛠️ 修復方案

### 修復代碼
在 `backend/library/benchmark/test_runner.py` 的 `run_batch_tests` 方法中：

**修改前**：
```python
test_run = BenchmarkTestRun.objects.create(
    version=self.version, run_name=run_name, run_type=run_type,
    total_test_cases=len(test_cases), status='running', started_at=timezone.now())
```

**修改後**：
```python
test_run = BenchmarkTestRun.objects.create(
    version=self.version, run_name=run_name, run_type=run_type, notes=notes,
    total_test_cases=len(test_cases), status='running', started_at=timezone.now())
```

### 修復指令
```bash
docker exec ai-django bash -c "
python3 << 'PYEOF'
with open('/app/library/benchmark/test_runner.py', 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'test_run = BenchmarkTestRun.objects.create(' in line:
        if i+1 < len(lines) and 'version=self.version' in lines[i+1]:
            old_line = lines[i+1]
            new_line = old_line.replace('run_type=run_type,', 'run_type=run_type, notes=notes,')
            if old_line != new_line:
                lines[i+1] = new_line
                break

with open('/app/library/benchmark/test_runner.py', 'w') as f:
    f.writelines(lines)
PYEOF
"

# 重啟 Django
docker compose restart django
```

---

## ✅ 驗證測試

### 測試執行
```python
from library.benchmark.batch_version_tester import BatchVersionTester

tester = BatchVersionTester(verbose=False)
result = tester.run_batch_test(
    version_ids=[3, 4],
    test_case_ids=[1, 2],
    batch_name='修復測試',
    notes='這是用戶備註',
    force_retest=False
)
```

### 測試結果
```
✅ 批量測試成功
Batch ID: 20251123_104240
Test Run IDs: [112, 113]

Test Run 112:
  Run Name: 修復測試 - Baseline Test
  Notes: 批次 ID: 20251123_104240
這是用戶備註
  ✅ Batch ID 已正確保存在 notes 中

Test Run 113:
  Run Name: 修復測試 - Baseline Version
  Notes: 批次 ID: 20251123_104240
這是用戶備註
  ✅ Batch ID 已正確保存在 notes 中
```

### 資料庫驗證
```sql
SELECT id, run_name, notes
FROM benchmark_test_run 
WHERE id IN (112, 113);
```

結果：
```
 id  | run_name                     | notes
-----+------------------------------+----------------------------------
 112 | 修復測試 - Baseline Test     | 批次 ID: 20251123_104240\n這是用戶備註
 113 | 修復測試 - Baseline Version  | 批次 ID: 20251123_104240\n這是用戶備註
```

✅ **確認**：batch_id 已正確保存到 notes 欄位！

---

## 📊 影響範圍

### 影響的功能
1. ✅ **批量測試執行** - 現在可以正確保存 batch_id
2. ✅ **批量測試歷史** - 可以透過 batch_id 查詢測試記錄
3. ✅ **批量對比頁面** - 可以正確獲取測試結果

### 不影響的功能
- ❌ **舊的測試記錄** - 已執行的批量測試無法追溯修復（notes 為空）
- ✅ **單一測試執行** - 不受影響（不使用 batch_id）

---

## 🎯 解決方案總結

| 項目 | 說明 |
|------|------|
| **問題** | `run_batch_tests` 方法沒有使用 `notes` 參數 |
| **原因** | 代碼遺漏：`BenchmarkTestRun.objects.create(...)` 沒有傳入 `notes=notes` |
| **修復** | 在 `test_runner.py` 第 54 行添加 `notes=notes` 參數 |
| **測試** | ✅ 新的批量測試可以正確保存 batch_id |
| **狀態** | ✅ 已完成並驗證 |

---

## 📝 建議改進

### 1. 程式碼品質改進
```python
# 建議：使用明確的參數傳遞
def run_batch_tests(self, test_cases, run_name, run_type='manual', notes=''):
    """
    執行批量測試
    
    Args:
        notes: 測試備註，批量測試時包含 batch_id
    """
    test_run = BenchmarkTestRun.objects.create(
        version=self.version,
        run_name=run_name,
        run_type=run_type,
        notes=notes,  # ← 明確傳入
        ...
    )
```

### 2. 單元測試建議
```python
def test_batch_test_saves_notes():
    """測試批量測試是否正確保存 notes"""
    result = tester.run_batch_test(
        version_ids=[1],
        test_case_ids=[1],
        notes="測試備註"
    )
    
    test_run = BenchmarkTestRun.objects.get(id=result['test_run_ids'][0])
    assert result['batch_id'] in test_run.notes
    assert "測試備註" in test_run.notes
```

### 3. 資料驗證建議
- 在 `BatchVersionTester.run_batch_test` 返回結果前，驗證 notes 是否保存成功
- 如果保存失敗，記錄警告日誌

---

## 📅 修復記錄

- **日期**：2025-11-23
- **版本**：v1.0.0
- **修復人員**：AI Assistant
- **測試狀態**：✅ 通過
- **部署狀態**：✅ 已部署到 Django 容器

---

## 🔄 後續工作

### 立即行動
- [x] 修復 test_runner.py 代碼
- [x] 重啟 Django 容器
- [x] 驗證新批量測試正常運作
- [x] 通知用戶測試

### 未來改進
- [ ] 為舊測試記錄添加 batch_id（如果需要）
- [ ] 添加單元測試覆蓋此場景
- [ ] 考慮在 Model 層面添加驗證

---

**修復狀態**：✅ **已完成**

用戶現在可以：
1. 刷新瀏覽器頁面（Ctrl+Shift+R 或 F5）
2. 執行新的批量測試
3. 正常查看批量測試歷史記錄
4. 順利進入批量對比頁面

所有新的批量測試都會正確保存 batch_id 到 notes 欄位中！🎉
