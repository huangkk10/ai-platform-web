# Test Summary vs Firmware Summary 意圖設計規劃

## 📋 概述

本文件規劃 `/test-summary` 和 `/firmware-summary` 兩個 API 的意圖區分設計，確保系統能根據用戶查詢準確選擇對應的 API，並提供適當的回應格式。

---

## 🔍 API 資料結構對比

### `/test-summary` API

**用途**：提供按「測試類別」和「容量」分組的測試結果明細

**資料結構**：
```json
{
  "project_uid": "00e11fc25a3f454e9e3860ff67dd2c07",
  "project_name": "Client_PCIe_Micron_Springsteen_SM2508_Micron B58R TLC",
  "capacities": ["512GB", "1024GB", "2048GB", "4096GB"],
  "categories": [
    {
      "name": "Certification",
      "results_by_capacity": {
        "512GB": {"pass": 0, "fail": 0, "ongoing": 0, "cancel": 0, "total": 0, "pass_rate": 0.0},
        "1024GB": {"pass": 0, "fail": 0, "ongoing": 0, "cancel": 1, "total": 1, "pass_rate": 0.0},
        ...
      },
      "total": {"pass": 0, "fail": 0, "ongoing": 0, "cancel": 1, "total": 1, "pass_rate": 0.0}
    },
    ...
  ]
}
```

**提供的資訊維度**：
| 維度 | 說明 | 範例值 |
|------|------|--------|
| 測試類別 | 12 種測試類別 | Certification, Compatibility, MANDi, Protocol, Security... |
| 容量分類 | 4 種容量 | 512GB, 1024GB, 2048GB, 4096GB |
| 測試狀態 | 5 種狀態 | pass, fail, ongoing, cancel, check |
| 通過率 | 按類別計算 | pass_rate: 0.0 ~ 100.0 |

**測試類別清單**：
1. Certification
2. Compatibility
3. MANDi
4. NVMe_Validation_Tool
5. Performance (Primary)
6. Performance (Secondary)
7. Power Consumption (Secondary)
8. Power Cycling
9. Protocol
10. Reliability
11. Security
12. UNITest

---

### `/firmware-summary` API

**用途**：提供單一 Firmware 的整體測試統計和效能指標

**資料結構**：
```json
{
  "project_uid": "00e11fc25a3f454e9e3860ff67dd2c07",
  "fw_name": "G200X6EC",
  "sub_version": "AA",
  "task_name": "[SVDFWV-31829][Micron][Springsteen][SM2508][AA][Micron B58R TLC]",
  "overview": {
    "total_test_items": 183,
    "passed": 58,
    "failed": 45,
    "conditional_passed": 0,
    "completion_rate": 56.0,
    "pass_rate": 56.31
  },
  "sample_stats": {
    "total_samples": 231,
    "samples_used": 0,
    "utilization_rate": 0.0
  },
  "test_item_stats": {
    "total_items": 113,
    "passed_items": 20,
    "failed_items": 28,
    "execution_rate": 42.0,
    "fail_rate": 25.0
  }
}
```

**提供的資訊維度**：
| 維度 | 說明 | 範例值 |
|------|------|--------|
| 整體概覽 | 總測試項目、Pass/Fail 數量 | total_test_items: 183, passed: 58, failed: 45 |
| 完成率 | 測試完成百分比 | completion_rate: 56.0% |
| 通過率 | 測試通過百分比 | pass_rate: 56.31% |
| 樣本統計 | 樣本總數、已使用、使用率 | total_samples: 231, utilization_rate: 0.0% |
| 測試項目統計 | 項目數、執行率、失敗率 | total_items: 113, fail_rate: 25.0% |

---

## 🎯 意圖設計

### 意圖 1: `query_project_test_summary_by_fw` (現有 - 使用 `/test-summary`)

**用途**：查詢特定 FW 版本的測試結果，按類別和容量分組

**觸發關鍵字**：
```
✅ 主要關鍵字：
- "測試結果"、"測試狀態"
- "Pass/Fail"、"通過/失敗"
- "各類別"、"類別測試"
- "容量測試"、"512GB/1024GB 測試"
- "Compatibility 測試"、"Security 測試" (特定類別)

❌ 不應觸發的說法：
- "完成率"、"進度"
- "樣本"、"樣本使用"
- "整體統計"、"總覽"
```

**自然語言範例**：
```
✅ 應該觸發此意圖：
1. "Springsteen G200X6EC 測試結果"
2. "Springsteen G200X6EC 的 Pass/Fail 狀況"
3. "查詢 G200X6EC 各類別測試結果"
4. "Springsteen G200X6EC Compatibility 測試怎樣"
5. "G200X6EC 的 Security 測試有幾個 Fail"
6. "Springsteen G200X6EC 1024GB 測試結果"
7. "G200X6EC 各容量的測試狀態"
8. "Springsteen G200X6EC Protocol 測試 Pass 了嗎"
9. "查看 G200X6EC 的 Performance 測試"
10. "Springsteen G200X6EC 哪些測試 Fail 了"
```

**回應格式設計**：

```markdown
## 📊 Springsteen G200X6EC 測試結果

### 測試概覽
- **專案**: Springsteen
- **FW 版本**: G200X6EC
- **容量**: 512GB, 1024GB, 2048GB, 4096GB

### 各類別測試結果

| 類別 | Pass | Fail | Ongoing | Cancel | Total | 通過率 |
|------|------|------|---------|--------|-------|--------|
| Certification | 0 | 0 | 0 | 1 | 1 | 0.0% |
| Compatibility | 0 | 3 | 0 | 3 | 6 | 0.0% |
| MANDi | 0 | 0 | 0 | 9 | 9 | 0.0% |
| Protocol | 0 | 2 | 0 | 4 | 6 | 0.0% |
| Security | 0 | 6 | 0 | 1 | 7 | 0.0% |
| ... | ... | ... | ... | ... | ... | ... |

### 容量分布 (以 Compatibility 為例)
| 容量 | Pass | Fail | Total |
|------|------|------|-------|
| 512GB | 0 | 0 | 2 |
| 1024GB | 0 | 1 | 2 |
| 2048GB | 0 | 2 | 2 |
| 4096GB | 0 | 0 | 0 |

### 問題摘要
⚠️ 失敗測試類別：Compatibility (3), Performance Primary (5), Security (6)...
```

---

### 意圖 2: `query_fw_detail_summary` (🆕 新增 - 使用 `/firmware-summary`)

**用途**：查詢特定 FW 版本的整體統計指標（完成率、樣本使用率等）

**觸發關鍵字**：
```
✅ 主要關鍵字：
- "詳細統計"、"統計資訊"
- "完成率"、"測試進度"
- "通過率"、"整體通過率"
- "樣本"、"樣本使用率"、"樣本狀況"
- "執行率"、"失敗率"
- "測試項目數"、"總共幾個測試"
- "概覽"、"總覽"、"Overview"

❌ 不應觸發的說法：
- "各類別"、"類別測試"
- "Compatibility"、"Security" (特定類別名稱)
- "容量測試"、"512GB"
- "哪些 Fail"、"哪些 Pass"
```

**自然語言範例**：
```
✅ 應該觸發此意圖：
1. "Springsteen G200X6EC 的詳細統計"
2. "查詢 G200X6EC 完成率"
3. "Springsteen G200X6EC 測試進度多少"
4. "G200X6EC 的整體通過率是多少"
5. "Springsteen G200X6EC 樣本使用狀況"
6. "查看 G200X6EC 樣本使用率"
7. "Springsteen G200X6EC 還有多少樣本"
8. "G200X6EC 測試執行率多少"
9. "Springsteen G200X6EC 失敗率"
10. "G200X6EC 總共有幾個測試項目"
11. "Springsteen G200X6EC 測試概覽"
12. "給我 G200X6EC 的統計資訊"
```

**回應格式設計**：

```markdown
## 📈 Springsteen G200X6EC 詳細統計

### 基本資訊
- **專案**: Springsteen
- **FW 版本**: G200X6EC
- **Sub Version**: AA
- **Task**: [SVDFWV-31829][Micron][Springsteen][SM2508][AA][Micron B58R TLC]

### 📊 測試概覽 (Overview)
| 指標 | 數值 |
|------|------|
| 總測試項目 | 183 |
| 已通過 | 58 |
| 已失敗 | 45 |
| 條件通過 | 0 |
| **完成率** | 56.0% |
| **通過率** | 56.31% |

### 🧪 樣本統計 (Sample Stats)
| 指標 | 數值 |
|------|------|
| 總樣本數 | 231 |
| 已使用樣本 | 0 |
| **使用率** | 0.0% |

### 📋 測試項目統計 (Test Item Stats)
| 指標 | 數值 |
|------|------|
| 總項目數 | 113 |
| 通過項目 | 20 |
| 失敗項目 | 28 |
| **執行率** | 42.0% |
| **失敗率** | 25.0% |

### 狀態摘要
- ⏳ **測試進度**: 56% 完成
- ✅ **測試品質**: 56.31% 通過率
- ⚠️ **待關注**: 28 個測試項目失敗 (失敗率 25%)
```

---

## 🔄 意圖識別決策樹

```
用戶查詢: "Springsteen G200X6EC ..."
    │
    ├─ 包含以下關鍵字？
    │   │
    │   ├─ 類別相關：
    │   │   ├─ "類別"、"各類別" → query_project_test_summary_by_fw
    │   │   ├─ 具體類別名稱 (Compatibility, Security, Protocol...) → query_project_test_summary_by_fw
    │   │   └─ "容量"、"512GB"、"1024GB" → query_project_test_summary_by_fw
    │   │
    │   ├─ 統計相關：
    │   │   ├─ "完成率"、"進度" → query_fw_detail_summary
    │   │   ├─ "樣本"、"使用率" → query_fw_detail_summary
    │   │   ├─ "執行率"、"失敗率" → query_fw_detail_summary
    │   │   ├─ "統計"、"概覽"、"總覽" → query_fw_detail_summary
    │   │   └─ "整體通過率" → query_fw_detail_summary
    │   │
    │   └─ 通用關鍵字：
    │       ├─ "測試結果"、"Pass/Fail" → query_project_test_summary_by_fw (預設)
    │       └─ "哪些 Fail"、"哪些 Pass" → query_project_test_summary_by_fw
    │
    └─ 無明確關鍵字 → query_project_test_summary_by_fw (預設)
```

---

## 📝 關鍵字映射表

### `/test-summary` 觸發關鍵字

| 類別 | 關鍵字 |
|------|--------|
| 測試結果 | 測試結果、測試狀態、測試情況、Pass/Fail、通過/失敗 |
| 類別相關 | 各類別、類別測試、Certification、Compatibility、MANDi、Protocol、Security、Performance、Reliability、UNITest |
| 容量相關 | 容量測試、512GB、1024GB、2048GB、4096GB、各容量 |
| 明細查詢 | 哪些 Fail、哪些 Pass、失敗的測試、通過的測試 |

### `/firmware-summary` 觸發關鍵字

| 類別 | 關鍵字 |
|------|--------|
| 完成度 | 完成率、測試進度、進度多少、完成多少 |
| 通過率 | 整體通過率、總體通過率、通過率多少 |
| 樣本 | 樣本、樣本使用率、樣本狀況、還有多少樣本、樣本數 |
| 項目統計 | 執行率、失敗率、測試項目數、總共幾個測試 |
| 整體 | 詳細統計、統計資訊、概覽、總覽、Overview |

---

## 🔧 LLM Prompt 設計

### 意圖識別 Prompt 片段

```
## FW 版本相關查詢 (需要 project_name + fw_version)

### query_project_test_summary_by_fw (測試結果)
查詢特定 FW 版本的測試結果，按類別和容量分組
- **觸發條件**: 用戶想知道各測試類別的 Pass/Fail 狀態
- **關鍵字**: 測試結果、Pass/Fail、各類別、類別測試、容量測試
- **特定類別名稱**: Certification, Compatibility, MANDi, Protocol, Security, Performance, Reliability, UNITest
- **範例**:
  - "Springsteen G200X6EC 測試結果"
  - "G200X6EC Compatibility 測試怎樣"
  - "Springsteen G200X6EC 哪些測試 Fail"
  - "G200X6EC 1024GB 測試結果"

### query_fw_detail_summary (詳細統計) 🆕
查詢特定 FW 版本的整體統計指標
- **觸發條件**: 用戶想知道完成率、樣本使用率、執行率等整體指標
- **關鍵字**: 詳細統計、完成率、進度、樣本、使用率、執行率、失敗率、概覽
- **範例**:
  - "Springsteen G200X6EC 詳細統計"
  - "G200X6EC 完成率多少"
  - "Springsteen G200X6EC 樣本使用狀況"
  - "G200X6EC 測試進度"
  - "Springsteen G200X6EC 失敗率"
```

---

## 📊 回應對比表

| 用戶問題 | 意圖 | API | 回應重點 |
|----------|------|-----|----------|
| "G200X6EC 測試結果" | test_summary_by_fw | /test-summary | 12 個類別的 Pass/Fail 表格 |
| "G200X6EC 詳細統計" | fw_detail_summary | /firmware-summary | 完成率、樣本、執行率 |
| "G200X6EC Compatibility 測試" | test_summary_by_fw | /test-summary | 只顯示 Compatibility 類別 |
| "G200X6EC 完成率" | fw_detail_summary | /firmware-summary | 56% 完成率 + 進度說明 |
| "G200X6EC 哪些 Fail" | test_summary_by_fw | /test-summary | 列出失敗的測試類別 |
| "G200X6EC 樣本使用" | fw_detail_summary | /firmware-summary | 231 樣本，0% 使用率 |
| "G200X6EC 1024GB 測試" | test_summary_by_fw | /test-summary | 只顯示 1024GB 容量結果 |
| "G200X6EC 失敗率" | fw_detail_summary | /firmware-summary | 25% 失敗率 + 項目統計 |

---

## 🧪 測試案例設計

### Test Case 1: 意圖識別正確性

```python
test_cases = [
    # test-summary 意圖
    ("Springsteen G200X6EC 測試結果", "query_project_test_summary_by_fw"),
    ("G200X6EC 的 Pass/Fail 狀況", "query_project_test_summary_by_fw"),
    ("Springsteen G200X6EC Compatibility 測試", "query_project_test_summary_by_fw"),
    ("G200X6EC 哪些測試 Fail 了", "query_project_test_summary_by_fw"),
    ("Springsteen G200X6EC 各類別測試結果", "query_project_test_summary_by_fw"),
    ("G200X6EC 1024GB 測試結果", "query_project_test_summary_by_fw"),
    
    # firmware-summary 意圖
    ("Springsteen G200X6EC 詳細統計", "query_fw_detail_summary"),
    ("G200X6EC 完成率多少", "query_fw_detail_summary"),
    ("Springsteen G200X6EC 樣本使用狀況", "query_fw_detail_summary"),
    ("G200X6EC 測試進度", "query_fw_detail_summary"),
    ("Springsteen G200X6EC 失敗率", "query_fw_detail_summary"),
    ("G200X6EC 整體通過率", "query_fw_detail_summary"),
    ("Springsteen G200X6EC 測試概覽", "query_fw_detail_summary"),
    ("G200X6EC 還有多少樣本", "query_fw_detail_summary"),
]
```

### Test Case 2: 邊界測試

```python
edge_cases = [
    # 模糊語句 - 應該用 test-summary (預設)
    ("Springsteen G200X6EC 測試怎樣", "query_project_test_summary_by_fw"),
    ("G200X6EC 測試狀況", "query_project_test_summary_by_fw"),
    
    # 混合語句 - 根據主要意圖判斷
    ("G200X6EC Compatibility 完成率", "query_fw_detail_summary"),  # 完成率優先
    ("G200X6EC 測試結果和進度", "query_project_test_summary_by_fw"),  # 測試結果優先
]
```

---

## 📋 實作檢查清單

### Phase 6.2: query_fw_detail_summary

- [ ] 6.2.1 新增意圖定義到 `intent_types.py`
- [ ] 6.2.2 新增 `get_firmware_summary()` 到 `api_client.py`
- [ ] 6.2.3 建立 `FWDetailSummaryHandler` 處理器
- [ ] 6.2.4 更新意圖分析 Prompt（加入關鍵字區分）
- [ ] 6.2.5 實作回應格式化
- [ ] 6.2.6 撰寫測試案例
- [ ] 6.2.7 進行意圖識別測試

### 現有意圖優化: query_project_test_summary_by_fw

- [ ] 優化回應格式（加入表格顯示）
- [ ] 支援特定類別過濾（如只查 Compatibility）
- [ ] 支援特定容量過濾（如只查 1024GB）

---

## 📝 文件版本

| 版本 | 日期 | 說明 |
|------|------|------|
| v1.0 | 2025-12-07 | 初始版本 - test-summary vs firmware-summary 意圖設計 |

---

## 🔗 相關文件

- [Phase 6 意圖系統重構規劃](./phase-6-intent-refactoring-plan.md)
- [LLM Smart API Router 設計](./llm-smart-api-router-design.md)

---

**下一步**：確認設計後，開始實作 Phase 6.2 `query_fw_detail_summary` 意圖
