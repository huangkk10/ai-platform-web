# Test Jobs 顯示優化計畫

## 📋 文件資訊
- **建立日期**: 2025-12-17
- **狀態**: 規劃中
- **相關功能**: SAF Assistant - Test Jobs Query (Phase 16)
- **相關檔案**: `library/saf_integration/smart_query/query_handlers/test_jobs_handler.py`

---

## 🎯 優化目標

改善 Test Jobs 查詢結果的顯示方式，提升用戶體驗和資訊可讀性。

---

## 📊 改動項目總覽

| 項目 | 原本 | 改成 | 優先級 |
|------|------|------|--------|
| **結構** | Pass/Fail 分開兩個表格 | 按 Category 摺疊，展開顯示 Test Items | P1 |
| **Capacity** | 每個容量一行（多行重複） | 拉平成欄位（512GB / 1024GB / 2048GB） | P1 |
| **Sample 欄位** | 顯示 | 移除 | P1 |
| **空欄位問題** | 有多餘空欄位 | 修復 | P1 |

---

## 🖼️ 顯示效果對比

### 原本的顯示方式

```markdown
## 🧪 專案 PM9M1 - FW HHB0YBC1 測試結果

總測試項目: 983 個
Pass: 632 ✅ | Fail: 181 ❌ | 其他: 170 | 通過率: 64.3%

### 📊 按類別統計

| Test Category | Pass | Fail | Other | Total |
|---------------|------|------|-------|-------|
| NVMe_Validation_Tool | 122 | 42 | 0 | 164 |
| Protocol | 20 | 65 | 24 | 109 |
...

### ❌ 失敗的測試項目

| Root ID | Test Category | Test Item | Capacity | Sample | Status |
|---------|---------------|-----------|----------|--------|--------|
| STC-4337 | NVMe_Validation_Tool | NVMe_Validation_Tool_2... | 1024GB | SSD-Y-15767 | ❌ Fail |
| STC-4337 | NVMe_Validation_Tool | NVMe_Validation_Tool_2... | 2048GB | SSD-Y-16092 | ❌ Fail |
| STC-5025 | Protocol | SMI PyNVMe Verification Tool (SPVT) | 512GB | SSD-Y-11637 | ❌ Fail |
| STC-5025 | Protocol | SMI PyNVMe Verification Tool (SPVT) | 1024GB | SSD-Y-08750 | ❌ Fail |
...（同一 Test Item 重複多行，只是 Capacity 不同）

### ✅ 通過的測試項目

| Root ID | Test Category | Test Item | Capacity | Sample | Status |
|---------|---------------|-----------|----------|--------|--------|
| STC-442 | Protocol | SANBlaze_Section1_NVMe... | 512GB | SSD-Y-11640 | ✅ Pass |
...

| 項目 | 內容 |
（空欄位問題）
```

**問題**：
1. ❌ 同一 Test Item 因不同 Capacity 重複多行，表格冗長
2. ❌ Sample 欄位對用戶意義不大，佔用空間
3. ❌ Pass/Fail 分開，無法直接對比同一 Test Item 的狀態
4. ❌ 結尾有空欄位

---

### 優化後的顯示方式

```html
## 🧪 專案 PM9M1 - FW HHB0YBC1 測試結果

**總測試項目**: 983 個  
**Pass**: 632 ✅ | **Fail**: 181 ❌ | **其他**: 170 | **通過率**: 64.3%

---

<details>
<summary>📁 <b>NVMe_Validation_Tool</b> — ✅ 122 | ❌ 42 | Total: 164</summary>

| Root ID | Test Item | 512GB | 1024GB | 2048GB |
|---------|-----------|:-----:|:------:|:------:|
| STC-4337 | NVMe_Validation_Tool_2(oem_hp_test_v1_4_hp) | ❌ | ❌ | ❌ |
| STC-4338 | NVMe_Validation_Tool_3(oem_dell_test) | ✅ | ✅ | - |
| STC-4339 | NVMe_Validation_Tool_4(basic_test) | ✅ | ✅ | ✅ |

</details>

<details>
<summary>📁 <b>Protocol</b> — ✅ 20 | ❌ 65 | Total: 109</summary>

| Root ID | Test Item | 512GB | 1024GB | 2048GB |
|---------|-----------|:-----:|:------:|:------:|
| STC-5025 | SMI PyNVMe Verification Tool (SPVT) | ❌ | ❌ | ❌ |
| STC-442 | SANBlaze_Section1_NVMe Generic I/O Commands | ✅ | ✅ | ✅ |
| STC-443 | SANBlaze_Section2_NVMe I/O Tests | ✅ | - | - |
| STC-444 | SANBlaze_Section3_NVMe_Reset-All supported | ✅ | - | - |

</details>

<details>
<summary>📁 <b>Power Cycling</b> — ✅ 240 | ❌ 35 | Total: 337</summary>

| Root ID | Test Item | 512GB | 1024GB | 2048GB |
|---------|-----------|:-----:|:------:|:------:|
| STC-1001 | Power_Cycle_Basic_Test | ✅ | ✅ | ✅ |
| STC-1002 | Power_Cycle_Stress_Test | ❌ | ✅ | ✅ |

</details>

<details>
<summary>📁 <b>Reliability</b> — ✅ 156 | ❌ 39 | Total: 238</summary>

...

</details>

<details>
<summary>📁 <b>Security</b> — ✅ 94 | ❌ 0 | Total: 135</summary>

...

</details>
```

**改善**：
1. ✅ 按 Category 摺疊，預設收合，點擊展開
2. ✅ Capacity 拉平成欄位，同一 Test Item 只佔一行
3. ✅ 移除 Sample 欄位
4. ✅ 修復空欄位問題
5. ✅ 使用 ✅/❌/- 符號簡潔顯示狀態

---

## 🔧 技術實作方案

### 1. HTML `<details>` 摺疊

使用 HTML5 原生的 `<details>` + `<summary>` 標籤實現摺疊效果：

```html
<details>
<summary>摺疊時顯示的標題</summary>

展開後顯示的內容（支援 Markdown 表格）

</details>
```

**相容性**：
- ✅ 大多數現代瀏覽器原生支援
- ✅ GitHub/GitLab Markdown 支援
- ⚠️ 需確認前端 Chat 組件的 Markdown 渲染器支援 HTML

### 2. Capacity 拉平邏輯

**資料轉換流程**：

```
原始資料（多行）:
[
  {root_id: "STC-5025", test_item: "SPVT", capacity: "512GB", status: "Fail"},
  {root_id: "STC-5025", test_item: "SPVT", capacity: "1024GB", status: "Fail"},
  {root_id: "STC-5025", test_item: "SPVT", capacity: "2048GB", status: "Fail"},
]

轉換後（單行）:
{
  root_id: "STC-5025",
  test_item: "SPVT",
  capacities: {
    "512GB": "Fail",
    "1024GB": "Fail", 
    "2048GB": "Fail"
  }
}
```

**Python 實作概念**：

```python
def _group_by_test_item(self, jobs: List[Dict]) -> List[Dict]:
    """
    將同一 Test Item 的不同 Capacity 結果合併為一行
    """
    grouped = {}
    
    for job in jobs:
        key = (job.get('root_id'), job.get('test_item_name'))
        if key not in grouped:
            grouped[key] = {
                'root_id': job.get('root_id'),
                'test_item': job.get('test_item_name'),
                'capacities': {}
            }
        
        capacity = job.get('capacity', 'Unknown')
        status = job.get('test_status', '')
        grouped[key]['capacities'][capacity] = status
    
    return list(grouped.values())
```

### 3. 動態 Capacity 欄位

不同專案可能有不同的 Capacity 組合，需動態生成欄位：

```python
def _get_all_capacities(self, jobs: List[Dict]) -> List[str]:
    """獲取所有出現的 Capacity，排序後返回"""
    capacities = set()
    for job in jobs:
        cap = job.get('capacity', '')
        if cap:
            capacities.add(cap)
    
    # 按數值排序（512GB < 1024GB < 2048GB）
    return sorted(capacities, key=lambda x: int(x.replace('GB', '').replace('TB', '000')))
```

---

## 📝 修改檔案清單

| 檔案 | 修改內容 |
|------|----------|
| `test_jobs_handler.py` | 重構 `_build_response_message()` 方法 |
| `test_jobs_handler.py` | 新增 `_group_by_test_item()` 方法 |
| `test_jobs_handler.py` | 新增 `_get_all_capacities()` 方法 |
| `test_jobs_handler.py` | 新增 `_format_category_details()` 方法 |

---

## ✅ 驗收標準

1. **摺疊功能**
   - [x] 每個 Test Category 顯示為可摺疊區塊
   - [x] 摺疊時顯示 Category 名稱 + Pass/Fail 統計
   - [x] 展開時顯示該 Category 的所有 Test Items

2. **Capacity 拉平**
   - [x] 同一 Test Item 只顯示一行
   - [x] 不同 Capacity 顯示為獨立欄位
   - [x] 沒有測試的 Capacity 顯示 `-`

3. **欄位優化**
   - [x] 移除 Sample 欄位
   - [x] 移除 Test Category 欄位（已在摺疊標題顯示）
   - [x] 狀態使用 ✅/❌/- 符號

4. **格式修復**
   - [x] 無多餘空欄位
   - [x] Markdown 表格正確渲染

---

## 🧪 測試計畫

### 測試案例

1. **PM9M1 HHB0YBC1**（983 筆，5 個 Category）
   - 驗證摺疊功能
   - 驗證 Capacity 拉平（512GB/1024GB/2048GB）

2. **其他專案**
   - 測試不同 Capacity 組合
   - 測試單一 Capacity 情況

### 測試指令

```bash
# 單元測試
docker exec ai-django python -c "
from library.saf_integration.smart_query.query_handlers.test_jobs_handler import TestJobsHandler
handler = TestJobsHandler()
result = handler.execute({
    'project_name': 'PM9M1',
    'fw_version': 'HHB0YBC1'
})
print(result.message)
"
```

---

## 📅 時程估計

| 階段 | 工作內容 | 預估時間 |
|------|----------|----------|
| 1 | 新增資料分組方法 | 15 分鐘 |
| 2 | 重構訊息建構方法 | 30 分鐘 |
| 3 | 測試與調整 | 15 分鐘 |
| **總計** | | **~1 小時** |

---

## 📚 參考資料

- [HTML `<details>` 標籤](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details)
- [GitHub Markdown 支援的 HTML](https://docs.github.com/en/get-started/writing-on-github)

---

## 📝 更新紀錄

| 日期 | 版本 | 變更內容 |
|------|------|----------|
| 2025-12-17 | v1.0 | 初版計畫建立 |
| 2025-12-17 | v1.1 | ✅ 實作完成，所有驗收標準通過 |
