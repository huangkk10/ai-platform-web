# SAF Assistant 專案測試查詢功能規劃

> **文件狀態**：✅ Phase 0 確認完成 | ✅ Intent 1 已實作 | ✅ Intent 5 已實作（改用 test-details API）| ✅ Intent 6, 7 已實作  
> **建立日期**：2024-12-09  
> **更新日期**：2024-12-10  
> **負責人**：AI Platform Team  
> **版本**：v1.7

---

## 📋 功能概述

### 背景說明
SAF Assistant 目前需要新增「專案測試查詢」相關意圖，讓用戶能夠透過自然語言查詢：
- 哪些專案有執行過特定類型的測試
- 特定專案的測試結果摘要
- 專案的 Firmware 資訊
- 專案的完整測試概況
- **特定專案 + Firmware 的測試類別和測項明細**
- **根據測試狀態（Pass/Fail）篩選專案**

### 可用 API 資源

| API 端點 | HTTP 方法 | 功能說明 | 回傳內容 |
|---------|----------|---------|---------|
| `/api/v1/projects/{project_uid}/test-summary` | GET | 取得專案測試摘要 | 依 category 彙整的測試結果 |
| `/api/v1/projects/{project_uid}/firmware-summary` | GET | 取得 Firmware 詳細摘要 | Firmware 版本與狀態資訊 |
| `/api/v1/projects/{project_uid}/full-summary` | GET | 取得完整專案摘要 | 包含所有 firmware 的完整資訊 |
| **`/api/v1/projects/{project_uid}/test-details`** | **GET** | **取得完整測試詳細資料** | **含所有 test items 明細、各狀態統計** |

### 測試狀態定義

根據系統定義，測試狀態（Test Status）包含以下類型：

| 狀態 | 說明 | 圖示 |
|------|------|------|
| **Ongoing** | 測試進行中 | 🔄 |
| **Passed** | 測試通過 | ✅ |
| **Conditional Passed** | 有條件通過 | ⚠️ |
| **Failed** | 測試失敗 | ❌ |
| **Interrupted** | 測試中斷 | 🛑 |

### 測試結果數值格式

#### test-summary API 欄位（舊版）

| 欄位 | 說明 | 範例值 |
|------|------|-------|
| `pass` | 測試通過數 | 68 |
| `fail` | 測試失敗數 | 3 |
| `ongoing` | 進行中數量 | 0 |
| `cancel` | 取消數量 | 1 |
| `check` | 需檢查數量 (Conditional Passed) | 0 |
| `total` | 總計 | 72 |
| `pass_rate` | 通過率 (%) | 95.77 |

#### test-details API 欄位（新版，建議使用）✅

| 欄位 | 說明 | 範例值 |
|------|------|-------|
| `ongoing` | 測試進行中 | 0 |
| `passed` | 測試通過數 | 226 |
| `conditional_passed` | 有條件通過 | 34 |
| `failed` | 測試失敗數 | 6 |
| `interrupted` | 測試中斷 | 6 |
| `total` | 總計 | 272 |
| `pass_rate` | 通過率 (%) | 97.41 |

**欄位順序**：`Ongoing / Passed / Conditional Passed / Failed / Interrupted`

### 測試資料結構

根據截圖，資料結構如下：

```
Project
└── Firmware (512GB, 1024GB, 2048GB, 4096GB, ...)
    └── Category (Compatibility, Functionality, MANDi, NVMe_Validation_Tool, ...)
        └── Test Items (Host compatibility, OS compatibility, MANDi BAT, ...)
            └── 測試SAMPLE要求數 (anySample(1), 512GB(1),1024GB(1),2048GB(1), ...)
                └── 測試結果 (X/Y/Z/W/V 格式)
```

---

## 🆕 test-details API 說明

### API 端點
```
GET /api/v1/projects/{project_uid}/test-details
```

### 必要 Headers
| Header | 說明 | 範例 |
|--------|------|------|
| `Authorization` | 使用者 ID | `150` |
| `Authorization-Name` | 使用者名稱 | `huangkk` |

### 回傳資料結構
```json
{
  "success": true,
  "data": {
    "project_uid": "bcd1b61fd256475a9d05e986f8e6cfd8",
    "project_name": "Client_PCIe_Micron_Springsteen_SM2508_Micron B68S TLC",
    "fw_name": "PH10YC3H_Pyrite_512Byte",
    "sub_version": "AC",
    "capacities": ["512GB", "1024GB", "2048GB", "4096GB"],
    "total_items": 95,
    "details": [
      {
        "category_name": "Compatibility",
        "test_item_name": "Host compatibility",
        "size_results": [
          {
            "size": "512GB",
            "result": {
              "ongoing": 0,
              "passed": 6,
              "conditional_passed": 0,
              "failed": 0,
              "interrupted": 0,
              "total": 6
            }
          }
        ],
        "total": {
          "ongoing": 0,
          "passed": 20,
          "conditional_passed": 0,
          "failed": 0,
          "interrupted": 0,
          "total": 20
        },
        "sample_capacity": "anySample(1)",
        "note": "測試說明..."
      }
    ],
    "summary": {
      "total_ongoing": 0,
      "total_passed": 226,
      "total_conditional_passed": 34,
      "total_failed": 6,
      "total_interrupted": 6,
      "overall_total": 272,
      "pass_rate": 97.41
    }
  }
}
```

### API 對比

| 項目 | test-summary | test-details |
|------|-------------|--------------|
| **詳細程度** | 只有 Category 統計 | 有 Category + Test Item 明細 |
| **欄位命名** | `pass`, `fail`, `check`, `cancel` | `passed`, `failed`, `conditional_passed`, `interrupted` |
| **包含 Note** | ❌ 無 | ✅ 有測試說明 |
| **包含 Sample 資訊** | ❌ 無 | ✅ 有 `sample_capacity` |
| **Summary** | 無整體統計 | ✅ 有 `summary` 欄位 |

---

## ✅ Phase 0 API 確認結果

### 專案列表 API

**確認狀態**：✅ 已存在並可用

- **方法**: `SAFAPIClient.get_all_projects()` - 獲取所有專案列表
- **方法**: `SAFAPIClient.get_project_uid_by_name(project_name)` - 專案名稱轉 UID（支援精確/模糊匹配）
- **方法**: `SAFAPIClient.get_project_test_details(project_uid)` - 獲取完整測試詳細資料 ✅ **新增**
- **專案總數**: 約 5,374 個（含子專案）

### test-summary API 回應結構

```json
{
  "project_uid": "21c6db80a556449f8b026649b28858c9",
  "project_name": "Automotive_PCIe_WD_DEMETER_SM2264XT_WDC BiCs5 TLC",
  "capacities": ["256GB", "512GB", "1024GB"],
  "categories": [
    {
      "name": "NVMe_Validation_Tool",
      "results_by_capacity": {
        "256GB": {
          "pass": 0, "fail": 1, "ongoing": 0, 
          "cancel": 1, "check": 0, "total": 2, "pass_rate": 0.0
        },
        "512GB": {"pass": 0, "fail": 0, ...},
        "1024GB": {"pass": 0, "fail": 0, ...}
      },
      "total": {
        "pass": 0, "fail": 1, "ongoing": 0, 
        "cancel": 1, "check": 0, "total": 2, "pass_rate": 0.0
      }
    },
    {"name": "Performance", ...},
    {"name": "OAKGATE", ...}
  ]
}
```

### firmware-summary API 回應結構

```json
{
  "project_uid": "21c6db80a556449f8b026649b28858c9",
  "fw_name": "[MR1.2][Y1114B_629fa1a_Y1114A_8572096]_128GB",
  "sub_version": "AC",
  "task_name": "[SM2264AUTO-4810][WD][DEMETER][SM2264XT][AC][WDC BiCS5 TLC]",
  "overview": {
    "total_test_items": 72,
    "passed": 68,
    "failed": 3,
    "conditional_passed": 0,
    "completion_rate": 99.0,
    "pass_rate": 95.77
  },
  "sample_stats": {
    "total_samples": 0,
    "samples_used": 0,
    "utilization_rate": 0.0
  },
  "test_item_stats": {
    "total_items": 72,
    "passed_items": 68,
    "failed_items": 3,
    "execution_rate": 99.0,
    "fail_rate": 4.0
  }
}
```

### 現有程式碼資源

| 資源 | 路徑 | 說明 |
|------|------|------|
| SAF API Client | `library/saf_integration/api_client.py` | 已有 `get_project_test_summary()`, `get_firmware_summary()` |
| Endpoint 配置 | `library/saf_integration/endpoint_registry.py` | 已有 `project_test_summary` 端點定義 |
| Test Summary Handler | `library/saf_integration/smart_query/query_handlers/test_summary_handler.py` | 已有測試摘要處理器 |
| Dify 配置 | `library/config/dify_config_manager.py` | SAF Intent Analyzer, SAF Analyzer 配置 |

---

## 🎯 新增意圖設計

### 意圖總覽

| # | 意圖名稱 | 說明 | 複雜度 | 狀態 |
|---|---------|------|-------|------|
| 1 | 專案測試類別查詢 | 哪些案子有測試過 XX？ | 中 | ✅ 已實作 |
| 2 | 專案測試結果查詢 | XX 專案的測試結果如何？ | 低 | ✅ 已存在 |
| 3 | Firmware 版本查詢 | XX 專案的 FW 資訊？ | 低 | ✅ 已存在 |
| 4 | 專案完整概況查詢 | 給我 XX 專案的完整報告 | 低 | ✅ 已存在 |
| **5** | **專案 FW 測試類別查詢** | **某 Project FW 有哪些測試類別？** | **中** | ✅ 已實作 |
| **6** | **專案 FW 類別測項查詢** | **某 Project FW 的 XX 類別有哪些測項？** | **中** | ✅ 已實作 |
| **7** | **專案 FW 全部測項查詢** | **某 Project FW 有哪些測項？** | **中** | ✅ 已實作 |
| **8** | **測試狀態專案篩選** | **PCIe CV5 有 PASS/FAIL 的案子有哪些？** | **高** | ⏳ 待開發 |

---

### 意圖 1：專案測試類別查詢 (Project Test Category Search) ✅ 已實作

> **實作狀態**：✅ 完成  
> **實作日期**：2024-12-09  
> **實作方式**：`TestCategorySearchHandler` + Intent Analyzer Prompt 更新

**意圖識別關鍵字**：
- 「哪些案子」、「哪些專案」、「哪些產品」
- 「有測試過」、「做過」、「跑過」、「執行過」
- 測試類別名稱（PCIe CV5, USB4 CV, NVMe, SATA CV, CrystalDiskMark 等）

**用戶問法範例**：
```
- 哪些案子有測試過 PCIe CV5？
- 有做過 USB4 CV 測試的專案有哪些？
- 找出所有測試過 NVMe 的專案
- 哪些產品有跑過 CrystalDiskMark？
- 列出有 SATA CV 測試的案子
- 哪些專案完成了 PCIe 認證測試？
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案測試類別查詢」
2. 實體提取 → 提取測試類別名稱（如 "PCIe CV5"）
3. 專案列表獲取 → 呼叫 `get_all_projects()` API
4. 迴圈查詢 → 對每個專案呼叫 test-summary API
5. 條件篩選 → 篩選出包含該測試類別的專案
6. 結果彙整 → 格式化輸出符合條件的專案列表
```

**實作細節**：
```
Handler: TestCategorySearchHandler
- 位置: library/saf_integration/smart_query/query_handlers/test_category_search_handler.py
- 功能: 並行搜尋 (10 workers)，類別標準化，客戶篩選，狀態篩選
- 搜尋範圍: 前 100 個專案（避免過長等待時間）

測試結果 (2024-12-09):
- 查詢: "哪些案子有測試過 Performance"
- 意圖識別: query_projects_by_test_category (信心度 95%)
- 結果: 找到 69 個專案包含 Performance 測試
```

**回應格式範例**：
```
根據系統資料，以下專案有進行過 PCIe CV5 測試：

1. **Project Alpha** (SAF-2024-001)
   - 測試狀態：✅ 通過
   - 測試日期：2024-11-15
   
2. **Project Beta** (SAF-2024-003)
   - 測試狀態：⚠️ 部分通過 (85%)
   - 測試日期：2024-12-01

3. **Project Gamma** (SAF-2024-007)
   - 測試狀態：🔄 進行中
   - 測試日期：2024-12-05

共找到 3 個專案。需要查看任一專案的詳細測試結果嗎？
```

---

### 意圖 2：專案測試結果查詢 (Project Test Result Query)

**意圖識別關鍵字**：
- 專案名稱或 UID
- 「測試結果」、「測試摘要」、「測試報告」
- 「做過哪些測試」、「測試狀態」

**用戶問法範例**：
```
- XX 專案的測試結果如何？
- Project ABC 有做過哪些測試？
- 這個案子的測試摘要是什麼？
- XX 產品的 PCIe 測試通過了嗎？
- SAF-2024-001 的測試進度如何？
- 給我 XX 專案的測試報告
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案測試結果查詢」
2. 實體提取 → 提取專案名稱或 project_uid
3. 名稱解析 → 如果是名稱，轉換為 project_uid（需對應表）
4. API 呼叫 → GET /api/v1/projects/{project_uid}/test-summary
5. 結果格式化 → 依類別彙整測試結果
```

**回應格式範例**：
```
**Project Alpha (SAF-2024-001) 測試摘要**

📊 測試概況：
- 總測試項目：45 項
- 通過：42 項 (93.3%)
- 失敗：2 項
- 進行中：1 項

📋 依類別分類：
| 類別 | 通過/總數 | 狀態 |
|------|----------|------|
| PCIe CV5 | 15/15 | ✅ |
| NVMe | 12/13 | ⚠️ |
| SATA | 10/10 | ✅ |
| 效能測試 | 5/7 | ⚠️ |

需要查看失敗項目的詳細資訊嗎？
```

---

### 意圖 3：Firmware 版本查詢 (Firmware Version Query)

**意圖識別關鍵字**：
- 「Firmware」、「FW」、「韌體」
- 「版本」、「資訊」、「狀態」
- 專案名稱或 UID

**用戶問法範例**：
```
- XX 專案用的是哪個 Firmware 版本？
- 這個案子的 FW 資訊是什麼？
- Project ABC 有幾個 Firmware 版本？
- 最新的 Firmware 測試狀態如何？
- SAF-2024-001 的韌體版本清單
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「Firmware 版本查詢」
2. 實體提取 → 提取專案名稱或 project_uid
3. 名稱解析 → 如果是名稱，轉換為 project_uid
4. API 呼叫 → GET /api/v1/projects/{project_uid}/firmware-summary
5. 結果格式化 → 格式化 Firmware 資訊
```

**回應格式範例**：
```
**Project Alpha (SAF-2024-001) Firmware 摘要**

📦 Firmware 版本列表：
| 版本 | 發布日期 | 測試狀態 | 備註 |
|------|---------|---------|------|
| FW v2.1.0 | 2024-12-01 | ✅ 通過 | 最新版本 |
| FW v2.0.5 | 2024-11-15 | ✅ 通過 | 穩定版本 |
| FW v2.0.0 | 2024-10-20 | ⚠️ 部分通過 | 已棄用 |

目前使用版本：FW v2.1.0
```

---

### 意圖 4：專案完整概況查詢 (Project Full Summary Query)

**意圖識別關鍵字**：
- 「完整」、「全部」、「整體」、「詳細」
- 「報告」、「概況」、「摘要」、「資訊」
- 專案名稱或 UID

**用戶問法範例**：
```
- 給我 XX 專案的完整報告
- Project ABC 的全部資訊是什麼？
- 這個案子的整體測試概況？
- XX 產品的測試和 Firmware 完整摘要
- 我想看 SAF-2024-001 的詳細資料
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案完整概況查詢」
2. 實體提取 → 提取專案名稱或 project_uid
3. 名稱解析 → 如果是名稱，轉換為 project_uid
4. API 呼叫 → GET /api/v1/projects/{project_uid}/full-summary
5. 結果格式化 → 格式化完整專案摘要
```

**回應格式範例**：
```
**Project Alpha (SAF-2024-001) 完整概況**

📌 基本資訊：
- 專案名稱：Project Alpha
- 專案代號：SAF-2024-001
- 建立日期：2024-09-01
- 狀態：進行中

📊 測試概況：
- 總測試項目：45 項
- 通過率：93.3%
- 最近測試：2024-12-05

📦 Firmware 概況：
- 版本數量：3 個
- 目前版本：FW v2.1.0
- 最新測試：2024-12-01

📋 測試類別明細：
[詳細測試類別表格...]

需要查看特定類別的詳細資訊嗎？
```

---

### 意圖 5：專案 FW 測試類別查詢 (Project FW Test Categories Query) ✅ 已實作

> **實作狀態**：✅ 完成  
> **實作日期**：2024-12-10  
> **實作方式**：`FWTestCategoriesHandler` + Intent Analyzer Prompt 更新

**意圖識別關鍵字**：
- 專案名稱 + Firmware 版本
- 「有哪些測試類別」、「測試類別」、「Category」
- 「包含哪些測試」

**用戶問法範例**：
```
- Project Alpha 的 512GB FW 有哪些測試類別？
- SAF-2024-001 的 1024GB 版本包含哪些測試？
- 這個案子的 2048GB FW 有什麼測試類別？
- XX 專案 FW v2.1 有哪些 Category？
- DEMETER 的 Y1114B 有什麼測試類別？
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案 FW 測試類別查詢」
2. 實體提取 → 提取專案名稱 + Firmware 版本
3. 專案匹配 → 使用 FW 版本模糊匹配找到對應的 project_uid
4. API 呼叫 → GET /api/v1/projects/{project_uid}/test-summary
5. 結果彙整 → 列出該 FW 的所有測試類別及統計數據
```

**實際回應格式**：
```
**專案 'DEMETER' FW '[MR1.2][Y1114B_629fa1a_Y1114A_8572096]' 測試類別**
📋 共 10 個測試類別：
1. Chamber Tempeture Test ❌ (Pass: 0, Fail: 7, Ongoing: 0)
2. Compatibility ❌ (Pass: 0, Fail: 1, Ongoing: 0)
3. NVMe_Validation_Tool ❌ (Pass: 0, Fail: 45, Ongoing: 0)
4. OAKGATE ⚪ (Pass: 0, Fail: 0, Ongoing: 0)
5. Performance ⚪ (Pass: 0, Fail: 0, Ongoing: 0)
6. Power Consumption ✅ (Pass: 9, Fail: 0, Ongoing: 0)
7. Protocol 🔄 (Pass: 0, Fail: 7, Ongoing: 1)
8. Reliability and Power Cycle ❌ (Pass: 0, Fail: 46, Ongoing: 0)
9. Security ❌ (Pass: 0, Fail: 1, Ongoing: 0)
10. Wear Leveling ❌ (Pass: 0, Fail: 3, Ongoing: 0)
💡 可用容量: 256GB, 512GB, 1024GB
```

---

### 意圖 6：專案 FW 類別測項查詢 (Project FW Category Test Items Query) ✅ 已實作

> **實作狀態**：✅ 完成  
> **實作日期**：2024-12-10  
> **實作方式**：`FWCategoryTestItemsHandler` + 使用 test-details API

**意圖識別關鍵字**：
- 專案名稱 + Firmware 版本 + 測試類別
- 「有哪些測項」、「測試項目」、「Test Items」
- 特定類別名稱（Compatibility, NVMe_Validation_Tool, MANDi 等）

**用戶問法範例**：
```
- Springsteen 的 GD10YBJD_Opal Functionality 類別有哪些測項？
- DEMETER 的 Y1114B 的 NVMe_Validation_Tool 有什麼測試項目？
- 這個案子 1024GB 的 MANDi 測試包含哪些項目？
- XX 專案 FW v2.1 的 Functionality 測試有哪些？
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案 FW 類別測項查詢」
2. 實體提取 → 提取專案名稱 + Firmware 版本 + 測試類別
3. 專案匹配 → 使用 FW 版本模糊匹配找到對應的 project_uid
4. API 呼叫 → GET /api/v1/projects/{project_uid}/test-details
5. 資料篩選 → 從 details 篩選指定類別的 test items
6. 結果彙整 → 列出該類別下的所有測試項目及統計
```

**回應格式範例**：
```
**專案 'Springsteen' FW 'GD10YBJD_Opal' - Functionality 測項**

📋 共 4 個測試項目：

| # | 測試項目 | 狀態 | Ongoing | Passed | Cond.Pass | Failed | Interrupted |
|---|----------|------|---------|--------|-----------|--------|-------------|
| 1 | TCG Test | ✅ | 0 | 4 | 0 | 0 | 0 |
| 2 | Hot-plug Test | ✅ | 0 | 2 | 0 | 0 | 0 |
| ...

📊 **總計**: Ongoing: 0, Passed: 8, Cond.Pass: 0, Failed: 0, Interrupted: 0
```

**實作細節**：
```
Handler: FWCategoryTestItemsHandler
- 位置: library/saf_integration/smart_query/query_handlers/fw_category_test_items_handler.py
- 功能: 從 test-details API 的 details 篩選特定類別測項
- 支援類別名稱模糊匹配
```

📋 測試項目清單：

| # | Test Item | SAMPLE 要求 | 測試結果 |
|---|-----------|------------|---------|
| 1 | NVMe_Validation_Tool_2(Boot_Partition_Write_Protection_Technical_Proposals_TP4170) | 512GB(1),1024GB(1),2048GB(1) | 0/16/**5**/1/0 |
| 2 | NVMe_Validation_Tool_2(SMBus_MI1.2) | anySample(1) | 0/1/**5**/0/3 |
| 3 | NVMe_Validation_Tool_2_Standard_Test_v2_0_(Advanced) | 512GB(1),1024GB(1),2048GB(1) | 0/1/**5**/0/0 |

📊 狀態說明：`Passed/Ongoing/Conditional/Failed/Interrupted`

共 3 個測試項目。
```

---

### 意圖 7：專案 FW 全部測項查詢 (Project FW All Test Items Query) ✅ 已實作

> **實作狀態**：✅ 完成  
> **實作日期**：2024-12-10  
> **實作方式**：`FWAllTestItemsHandler` + 使用 test-details API

**意圖識別關鍵字**：
- 專案名稱 + Firmware 版本
- 「所有測項」、「全部測試項目」、「有哪些測項」
- 不指定特定類別

**用戶問法範例**：
```
- Springsteen 的 GD10YBJD_Opal 有哪些測項？
- DEMETER 的 Y1114B 所有測試項目？
- 列出這個案子 512GB 的全部測試項目
- XX 專案 FW v2.1 的測試項目清單
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「專案 FW 全部測項查詢」
2. 實體提取 → 提取專案名稱 + Firmware 版本
3. 專案匹配 → 使用 FW 版本模糊匹配找到對應的 project_uid
4. API 呼叫 → GET /api/v1/projects/{project_uid}/test-details
5. 資料彙整 → 按類別分組列出所有測試項目
```

**回應格式範例**：
```
**專案 'Springsteen' FW 'GD10YBJD_Opal' 全部測項**

📋 共 9 個類別，29 個測試項目：

### ✅ **Functionality** (4 項)

| # | 測試項目 | 狀態 | Ongoing | Passed | Cond.Pass | Failed | Interrupted |
|---|----------|------|---------|--------|-----------|--------|-------------|
| 1 | TCG Test | ✅ | 0 | 4 | 0 | 0 | 0 |
| 2 | Hot-plug Test | ✅ | 0 | 2 | 0 | 0 | 0 |
...

### ❌ **L & L** (1 項)

| # | 測試項目 | 狀態 | Ongoing | Passed | Cond.Pass | Failed | Interrupted |
|---|----------|------|---------|--------|-----------|--------|-------------|
| 1 | L & L Test | ❌ | 0 | 0 | 0 | 1 | 0 |

...

---
� **總計**: 29 測項 | Ongoing: 0, Passed: 32, Cond.Pass: 10, Failed: 1, Interrupted: 0
� 可用容量: 512GB, 1024GB, 2048GB, 4096GB
```

**實作細節**：
```
Handler: FWAllTestItemsHandler
- 位置: library/saf_integration/smart_query/query_handlers/fw_all_test_items_handler.py
- 功能: 從 test-details API 獲取所有測項並按類別分組顯示
- 輸出格式: 按類別分組的表格，包含每個類別的狀態摘要
```

---

### 意圖 8：測試狀態專案篩選 (Test Status Project Filter) 🆕

**意圖識別關鍵字**：
- 測試類別名稱 + 測試狀態
- 「有 PASS 的」、「有 FAIL 的」、「已通過」、「失敗」
- 「哪些案子」、「哪些專案」

**用戶問法範例**：
```
- PCIe CV5 目前廠內有 PASS 的案子有哪些？
- 哪些專案的 NVMe 測試有 FAIL？
- MANDi 測試有通過的案子？
- 列出 USB4 CV 測試失敗的專案
- 有哪些案子的 Compatibility 測試是 Conditional Passed？
- NVMe_Validation_Tool 有中斷(Interrupted)的專案？
```

**處理邏輯**：
```
1. 意圖識別 → 判斷為「測試狀態專案篩選」
2. 實體提取 → 提取測試類別 + 目標狀態 (Passed/Failed/Conditional/Ongoing/Interrupted)
3. 專案列表獲取 → 使用 `get_all_projects()` API
4. 迴圈查詢 → 對每個專案呼叫 test-summary/full-summary API
5. 條件篩選 → 篩選出該類別有指定狀態的專案
6. 結果彙整 → 格式化輸出符合條件的專案列表
```

**回應格式範例**：
```
**NVMe_Validation_Tool 測試有 PASS 的專案**

根據系統資料，以下專案的 NVMe_Validation_Tool 測試有 Passed 狀態：

| # | 專案名稱 | 專案代號 | Passed 數量 | 整體狀態 |
|---|---------|---------|------------|---------|
| 1 | Project Alpha | SAF-2024-001 | 18 項 | ⚠️ 18 Passed, 15 Conditional |
| 2 | Project Beta | SAF-2024-003 | 45 項 | ✅ 全部 Passed |
| 3 | Project Gamma | SAF-2024-007 | 12 項 | 🔄 12 Passed, 8 Ongoing |

共找到 3 個專案。

需要查看特定專案的詳細測試結果嗎？
```

**狀態篩選對應表**：

| 用戶說法 | 對應狀態 |
|---------|---------|
| PASS、通過、已通過 | Passed |
| FAIL、失敗、未通過 | Failed |
| 有條件通過、Conditional | Conditional Passed |
| 進行中、Ongoing、測試中 | Ongoing |
| 中斷、Interrupted | Interrupted |

---

## 🏗️ 技術實作方案

### 方案 A：純 Dify 工作流程（推薦用於快速驗證）

**架構圖**：
```
用戶提問
    ↓
┌─────────────────┐
│  意圖分類節點    │ ← LLM 判斷意圖類型
│  (LLM Node)     │
└────────┬────────┘
         ↓
┌─────────────────┐
│  條件分支節點    │ ← 根據意圖類型分流
│  (IF/ELSE)      │
└────────┬────────┘
         ↓
    ┌────┴────┬────────┬────────┐
    ↓         ↓        ↓        ↓
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│意圖 1 │ │意圖 2 │ │意圖 3 │ │意圖 4 │
│類別查詢│ │結果查詢│ │FW查詢 │ │完整概況│
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    ↓         ↓        ↓        ↓
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│HTTP   │ │HTTP   │ │HTTP   │ │HTTP   │
│Request│ │Request│ │Request│ │Request│
└───┬───┘ └───┬───┘ └───┬───┘ └───┬───┘
    ↓         ↓        ↓        ↓
    └────┬────┴────────┴────────┘
         ↓
┌─────────────────┐
│  回應生成節點    │ ← LLM 格式化輸出
│  (LLM Node)     │
└─────────────────┘
         ↓
      用戶回應
```

**優點**：
- ✅ 快速實作和驗證
- ✅ 不需要修改 Django 後端
- ✅ 容易調整和迭代

**缺點**：
- ⚠️ 意圖 1 需要遍歷專案，效能可能較差
- ⚠️ Dify 工作流程複雜度較高
- ⚠️ 錯誤處理較不靈活

---

### 方案 B：Django 後端 + Dify 整合（推薦用於生產環境）

**新增 Django API**：

```python
# backend/api/views/saf_assistant_views.py

class SAFProjectSearchViewSet(viewsets.ViewSet):
    """SAF Assistant 專案搜尋 API"""
    
    @action(detail=False, methods=['post'])
    def search_by_test_category(self, request):
        """
        根據測試類別搜尋專案
        
        POST /api/saf-assistant/search-by-test-category/
        {
            "test_category": "PCIe CV5",
            "status_filter": "passed"  // optional: passed, failed, in_progress, all
        }
        """
        pass
    
    @action(detail=False, methods=['get'])
    def project_test_summary(self, request):
        """
        獲取專案測試摘要（支援名稱或 UID 查詢）
        
        GET /api/saf-assistant/project-test-summary/?project=Project Alpha
        GET /api/saf-assistant/project-test-summary/?project_uid=SAF-2024-001
        """
        pass
    
    @action(detail=False, methods=['get'])
    def project_firmware_summary(self, request):
        """
        獲取專案 Firmware 摘要
        
        GET /api/saf-assistant/project-firmware-summary/?project=Project Alpha
        """
        pass
    
    @action(detail=False, methods=['get'])
    def project_full_summary(self, request):
        """
        獲取專案完整摘要
        
        GET /api/saf-assistant/project-full-summary/?project=Project Alpha
        """
        pass
```

**URL 路由**：
```python
# backend/api/urls.py
router.register(r'saf-assistant', SAFProjectSearchViewSet, basename='saf-assistant')
```

**優點**：
- ✅ 效能優化（後端批次處理）
- ✅ 複雜邏輯集中管理
- ✅ 更好的錯誤處理
- ✅ 支援專案名稱到 UID 的轉換

**缺點**：
- ⚠️ 需要額外開發時間
- ⚠️ 需要了解 SAF 系統的資料結構

---

## 📝 Dify 提示詞設計

### 意圖分類提示詞

```
你是一個意圖分類器，負責判斷用戶的問題屬於哪種類型。

## 意圖類型

1. **PROJECT_TEST_CATEGORY_SEARCH** - 專案測試類別查詢
   - 用戶想知道哪些專案有執行過特定類型的測試
   - 關鍵詞：哪些案子、哪些專案、有測試過、做過、跑過
   - 範例：「哪些案子有測試過 PCIe CV5？」

2. **PROJECT_TEST_RESULT** - 專案測試結果查詢
   - 用戶想知道特定專案的測試結果或摘要
   - 關鍵詞：測試結果、測試摘要、做過哪些測試
   - 範例：「Project Alpha 的測試結果如何？」

3. **PROJECT_FIRMWARE** - Firmware 版本查詢
   - 用戶想知道專案的 Firmware 相關資訊
   - 關鍵詞：Firmware、FW、韌體、版本
   - 範例：「這個案子的 FW 版本是什麼？」

4. **PROJECT_FULL_SUMMARY** - 專案完整概況查詢
   - 用戶想要專案的完整資訊
   - 關鍵詞：完整、全部、整體、詳細報告
   - 範例：「給我 XX 專案的完整報告」

5. **OTHER** - 其他問題
   - 不屬於上述任何類型

## 輸出格式

請以 JSON 格式輸出：
{
    "intent": "意圖類型",
    "confidence": 0.95,
    "entities": {
        "project_name": "專案名稱（如果有）",
        "project_uid": "專案 UID（如果有）",
        "test_category": "測試類別（如果有）"
    }
}
```

### 回應生成提示詞

```
你是 SAF Assistant，負責回答關於專案測試的問題。

## 回應原則

1. **結構清晰**：使用表格、列表等格式呈現資訊
2. **狀態圖示**：
   - ✅ 通過
   - ❌ 失敗
   - ⚠️ 部分通過
   - 🔄 進行中
3. **數據準確**：直接引用 API 回傳的數據
4. **追問引導**：在回答末尾提供相關追問建議

## API 資料

{api_response}

## 用戶問題

{user_query}

請根據 API 資料回答用戶問題。
```

---

## ⚡ 實作優先順序

| 優先級 | 功能 | 預估工時 | 難度 | 價值 | 備註 |
|-------|------|---------|------|------|------|
| 🥇 P0 | 意圖 2：專案測試結果查詢 | 4h | 低 | 高 ⭐⭐⭐ | 基礎功能 |
| 🥇 P0 | 意圖 5：專案 FW 測試類別查詢 | 4h | 中 | 高 ⭐⭐⭐ | 🆕 核心功能 |
| 🥇 P0 | 意圖 6：專案 FW 類別測項查詢 | 4h | 中 | 高 ⭐⭐⭐ | 🆕 核心功能 |
| 🥈 P1 | 意圖 7：專案 FW 全部測項查詢 | 4h | 中 | 中 ⭐⭐ | 🆕 擴展功能 |
| 🥈 P1 | 意圖 8：測試狀態專案篩選 | 8h | 高 | 高 ⭐⭐⭐ | 🆕 進階功能 |
| 🥈 P1 | 意圖 1：專案測試類別查詢 | 8h | 中 | 中 ⭐⭐ | 需遍歷專案 |
| 🥉 P2 | 意圖 4：專案完整概況查詢 | 4h | 低 | 中 ⭐⭐ | 擴展功能 |
| � P2 | 意圖 3：Firmware 版本查詢 | 4h | 低 | 低 ⭐ | 擴展功能 |

**建議實作順序**：
1. **Phase 1**：先完成意圖 2、5、6（單專案 + FW 層級查詢，最常用）
2. **Phase 2**：完成意圖 7、8（全測項查詢 + 狀態篩選）
3. **Phase 3**：完成意圖 1、3、4（跨專案搜尋和完整報告）

---

## ✅ 確認事項（已完成 Phase 0 確認）

### 必須確認（阻塞項）- 已完成

| # | 問題 | 重要性 | 狀態 | 確認結果 |
|---|------|-------|------|----------|
| 1 | **專案列表 API** | 🔴 高 | ✅ 已確認 | `SAFAPIClient.get_all_projects()` - 約 5,374 個專案 |
| 2 | **專案名稱對應** | 🔴 高 | ✅ 已確認 | `SAFAPIClient.get_project_uid_by_name()` - 支援精確/模糊匹配 |
| 3 | **API 認證方式** | 🔴 高 | ✅ 已確認 | `auth_manager.get_auth_headers()` - 已有完整認證機制 |
| 4 | **測試結果數值格式** | 🔴 高 | ✅ 已確認 | `pass/fail/ongoing/cancel/check/total/pass_rate` |

### 建議確認（優化項）- 已完成

| # | 問題 | 重要性 | 狀態 | 確認結果 |
|---|------|-------|------|----------|
| 5 | **測試類別清單** | 🟡 中 | ✅ 已確認 | `NVMe_Validation_Tool`, `OAKGATE`, `Performance`, `Compatibility`, `Functionality`, `MANDi` 等 |
| 6 | **API 回應格式** | 🟡 中 | ✅ 已確認 | 見上方「Phase 0 API 確認結果」章節 |
| 7 | **效能考量** | 🟡 中 | ✅ 已確認 | 約 5,374 個專案，API 已有分頁（size=100）和快取機制 |
| 8 | **Firmware 版本格式** | 🟡 中 | ✅ 已確認 | 由 `fw_name` 表示，如 `[MR1.2][Y1114B_629fa1a_Y1114A_8572096]_128GB` |

---

## 📊 測試案例設計

### 意圖 1 測試案例

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC1-1 | 哪些案子有測試過 PCIe CV5？ | PROJECT_TEST_CATEGORY_SEARCH | test_category: "PCIe CV5" |
| TC1-2 | 有做過 USB4 CV 測試的專案 | PROJECT_TEST_CATEGORY_SEARCH | test_category: "USB4 CV" |
| TC1-3 | 找出所有測試過 NVMe 的專案 | PROJECT_TEST_CATEGORY_SEARCH | test_category: "NVMe" |
| TC1-4 | 列出有 SATA 測試的案子 | PROJECT_TEST_CATEGORY_SEARCH | test_category: "SATA" |

### 意圖 2 測試案例

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC2-1 | Project Alpha 的測試結果如何？ | PROJECT_TEST_RESULT | project_name: "Project Alpha" |
| TC2-2 | SAF-2024-001 有做過哪些測試？ | PROJECT_TEST_RESULT | project_uid: "SAF-2024-001" |
| TC2-3 | 這個案子的測試摘要 | PROJECT_TEST_RESULT | （需從上下文取得） |

### 意圖 5 測試案例 🆕

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC5-1 | Project Alpha 的 512GB FW 有哪些測試類別？ | PROJECT_FW_CATEGORIES | project: "Project Alpha", fw: "512GB" |
| TC5-2 | SAF-2024-001 的 1024GB 版本包含哪些測試？ | PROJECT_FW_CATEGORIES | project_uid: "SAF-2024-001", fw: "1024GB" |
| TC5-3 | 這個案子的 2048GB FW 有什麼 Category？ | PROJECT_FW_CATEGORIES | fw: "2048GB" |

### 意圖 6 測試案例 🆕

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC6-1 | Project Alpha 的 512GB 的 Compatibility 有哪些測項？ | PROJECT_FW_CATEGORY_ITEMS | project: "Project Alpha", fw: "512GB", category: "Compatibility" |
| TC6-2 | SAF-2024-001 的 NVMe_Validation_Tool 有什麼測試項目？ | PROJECT_FW_CATEGORY_ITEMS | project_uid: "SAF-2024-001", category: "NVMe_Validation_Tool" |
| TC6-3 | 這個案子 1024GB 的 MANDi 測試包含哪些項目？ | PROJECT_FW_CATEGORY_ITEMS | fw: "1024GB", category: "MANDi" |

### 意圖 7 測試案例 🆕

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC7-1 | Project Alpha 的 512GB FW 有哪些測項？ | PROJECT_FW_ALL_ITEMS | project: "Project Alpha", fw: "512GB" |
| TC7-2 | SAF-2024-001 的 1024GB 版本所有測試項目？ | PROJECT_FW_ALL_ITEMS | project_uid: "SAF-2024-001", fw: "1024GB" |
| TC7-3 | 列出這個案子 2048GB 的全部測試項目 | PROJECT_FW_ALL_ITEMS | fw: "2048GB" |

### 意圖 8 測試案例 🆕

| 測試案例 | 輸入 | 預期意圖 | 預期提取實體 |
|---------|------|---------|-------------|
| TC8-1 | PCIe CV5 目前廠內有 PASS 的案子有哪些？ | TEST_STATUS_PROJECT_FILTER | category: "PCIe CV5", status: "Passed" |
| TC8-2 | 哪些專案的 NVMe 測試有 FAIL？ | TEST_STATUS_PROJECT_FILTER | category: "NVMe", status: "Failed" |
| TC8-3 | MANDi 測試有通過的案子？ | TEST_STATUS_PROJECT_FILTER | category: "MANDi", status: "Passed" |
| TC8-4 | NVMe_Validation_Tool 有 Conditional Passed 的專案？ | TEST_STATUS_PROJECT_FILTER | category: "NVMe_Validation_Tool", status: "Conditional" |
| TC8-5 | 有哪些案子的 Compatibility 測試中斷了？ | TEST_STATUS_PROJECT_FILTER | category: "Compatibility", status: "Interrupted" |

---

## 📅 里程碑規劃

### 🎯 分階段實作總覽

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SAF Assistant 專案測試查詢                         │
├─────────────────────────────────────────────────────────────────────────┤
│  Phase 0   │  Phase 1   │  Phase 2   │  Phase 3   │  Phase 4   │ Phase 5│
│  準備工作   │  單專案查詢 │  FW層級查詢 │  狀態篩選   │  跨專案搜尋 │  優化   │
│  (1-2天)   │  (1-2天)   │  (2-3天)   │  (2-3天)   │  (2天)     │ (1天)  │
├────────────┼────────────┼────────────┼────────────┼────────────┼────────┤
│ ✓ 確認API  │ ✓ 意圖2    │ ✓ 意圖5    │ ✓ 意圖7    │ ✓ 意圖1    │ ✓ 調優 │
│ ✓ 確認格式 │            │ ✓ 意圖6    │ ✓ 意圖8    │ ✓ 意圖3    │ ✓ 測試 │
│ ✓ 建立基礎 │            │            │            │ ✓ 意圖4    │        │
└────────────┴────────────┴────────────┴────────────┴────────────┴────────┘
                              總預估：9-13 天
```

---

### 📋 Phase 0：準備工作（1-2 天）

**目標**：確認所有前置條件，建立開發基礎

| 任務 | 說明 | 負責人 | 狀態 |
|------|------|-------|------|
| 0.1 | 確認 API 認證方式（Token/Session） | | ⏳ |
| 0.2 | 確認測試結果數值格式 `X/Y/Z/W/V` 的對應意義 | | ⏳ |
| 0.3 | 確認專案列表 API 是否存在 | | ⏳ |
| 0.4 | 確認專案名稱到 UID 的對應方式 | | ⏳ |
| 0.5 | 取得 3 個 API 的完整回應格式（JSON Sample） | | ⏳ |
| 0.6 | 確認 Firmware 版本表示方式（容量/版本號） | | ⏳ |
| 0.7 | 在 Dify 建立 SAF Assistant 應用基礎框架 | | ⏳ |

**產出物**：
- [ ] API 規格確認文件
- [ ] Dify 應用基礎框架
- [ ] 測試用專案資料（至少 2-3 個專案）

**驗收標準**：
- ✅ 所有待確認事項已確認
- ✅ 可成功呼叫 3 個 API 並取得回應
- ✅ Dify 應用可正常運作

---

### 📋 Phase 1：單專案查詢（1-2 天）

**目標**：實作最基本的專案查詢功能

**實作內容**：

| 意圖 | 功能 | 優先級 | 預估工時 |
|------|------|-------|---------|
| 意圖 2 | 專案測試結果查詢 | P0 | 4h |

**詳細步驟**：

```
Day 1：
├── 1.1 建立意圖分類節點（簡化版，只處理意圖 2）
├── 1.2 實作 HTTP Request 節點（呼叫 test-summary API）
├── 1.3 實作回應生成節點（格式化測試結果）
└── 1.4 基本功能測試

Day 2：
├── 1.5 處理專案名稱到 UID 的轉換
├── 1.6 錯誤處理（專案不存在、API 錯誤）
└── 1.7 整合測試
```

**測試案例**：
```
✓ "SAF-2024-001 的測試結果如何？"
✓ "Project Alpha 有做過哪些測試？"
✓ "這個案子的測試摘要是什麼？"
```

**驗收標準**：
- ✅ 可透過 project_uid 查詢測試結果
- ✅ 可透過專案名稱查詢測試結果
- ✅ 回應格式清晰，包含狀態圖示
- ✅ 錯誤情況有適當處理

---

### 📋 Phase 2：FW 層級查詢（2-3 天）

**目標**：實作 Firmware 層級的測試查詢

**實作內容**：

| 意圖 | 功能 | 優先級 | 預估工時 |
|------|------|-------|---------|
| 意圖 5 | 專案 FW 測試類別查詢 | P0 | 4h |
| 意圖 6 | 專案 FW 類別測項查詢 | P0 | 4h |

**詳細步驟**：

```
Day 1：
├── 2.1 擴展意圖分類節點（新增意圖 5、6）
├── 2.2 實作實體提取（專案 + FW 版本 + Category）
└── 2.3 實作意圖 5：FW 測試類別查詢

Day 2：
├── 2.4 實作意圖 6：FW 類別測項查詢
├── 2.5 資料篩選邏輯（根據 FW 版本過濾）
└── 2.6 回應格式化（表格呈現）

Day 3：
├── 2.7 整合測試
├── 2.8 邊界情況處理
└── 2.9 優化回應格式
```

**測試案例**：
```
✓ "Project Alpha 的 512GB FW 有哪些測試類別？"
✓ "SAF-2024-001 的 1024GB 版本包含哪些測試？"
✓ "這個案子 512GB 的 NVMe_Validation_Tool 有哪些測項？"
✓ "Project Alpha 的 Compatibility 測試有什麼項目？"
```

**驗收標準**：
- ✅ 可查詢特定 FW 的測試類別清單
- ✅ 可查詢特定 FW + Category 的測項明細
- ✅ 支援不同的 FW 版本格式（512GB, 1024GB 等）
- ✅ 回應包含測試結果狀態

---

### 📋 Phase 3：狀態篩選（2-3 天）

**目標**：實作進階的測試狀態篩選和全測項查詢

**實作內容**：

| 意圖 | 功能 | 優先級 | 預估工時 |
|------|------|-------|---------|
| 意圖 7 | 專案 FW 全部測項查詢 | P1 | 4h |
| 意圖 8 | 測試狀態專案篩選 | P1 | 8h |

**詳細步驟**：

```
Day 1：
├── 3.1 擴展意圖分類節點（新增意圖 7、8）
├── 3.2 實作意圖 7：全部測項查詢
└── 3.3 回應格式化（依類別分組）

Day 2：
├── 3.4 實作意圖 8：狀態篩選基礎
├── 3.5 狀態關鍵字對應（PASS/FAIL/Conditional 等）
└── 3.6 專案遍歷邏輯（如有專案列表 API）

Day 3：
├── 3.7 整合測試
├── 3.8 效能優化（減少 API 呼叫）
└── 3.9 錯誤處理完善
```

**測試案例**：
```
✓ "Project Alpha 的 512GB FW 有哪些測項？"
✓ "列出這個案子 1024GB 的全部測試項目"
✓ "NVMe_Validation_Tool 目前有 PASS 的案子有哪些？"
✓ "哪些專案的 Compatibility 測試有 FAIL？"
✓ "MANDi 測試有 Conditional Passed 的專案？"
```

**驗收標準**：
- ✅ 可查詢特定 FW 的所有測項（依類別分組）
- ✅ 可根據測試狀態篩選專案
- ✅ 支援多種狀態關鍵字識別
- ✅ 效能可接受（< 10 秒回應）

---

### 📋 Phase 4：跨專案搜尋（2 天）

**目標**：實作跨專案的搜尋和完整報告功能

**實作內容**：

| 意圖 | 功能 | 優先級 | 預估工時 |
|------|------|-------|---------|
| 意圖 1 | 專案測試類別查詢 | P1 | 8h |
| 意圖 3 | Firmware 版本查詢 | P2 | 4h |
| 意圖 4 | 專案完整概況查詢 | P2 | 4h |

**詳細步驟**：

```
Day 1：
├── 4.1 實作意圖 1：跨專案測試類別搜尋
├── 4.2 專案列表獲取和遍歷
└── 4.3 結果彙整和排序

Day 2：
├── 4.4 實作意圖 3：Firmware 版本查詢
├── 4.5 實作意圖 4：完整概況查詢
├── 4.6 整合測試
└── 4.7 效能優化
```

**測試案例**：
```
✓ "哪些案子有測試過 PCIe CV5？"
✓ "有做過 NVMe 測試的專案有哪些？"
✓ "Project Alpha 的 FW 版本有哪些？"
✓ "給我 SAF-2024-001 的完整報告"
```

**驗收標準**：
- ✅ 可搜尋所有有特定測試類別的專案
- ✅ 可查詢專案的 Firmware 版本清單
- ✅ 可取得專案的完整測試概況

---

### 📋 Phase 5：優化調整（1 天）

**目標**：優化整體體驗，處理邊界情況

**實作內容**：

```
├── 5.1 提示詞調優
│   ├── 改善意圖識別準確度
│   ├── 優化回應格式和用語
│   └── 處理模糊查詢
│
├── 5.2 錯誤處理完善
│   ├── API 超時處理
│   ├── 資料不存在處理
│   └── 友善錯誤訊息
│
├── 5.3 效能優化
│   ├── 減少不必要的 API 呼叫
│   ├── 快取常用資料
│   └── 回應時間監控
│
└── 5.4 用戶測試
    ├── 收集回饋
    └── 迭代改進
```

**驗收標準**：
- ✅ 意圖識別準確率 > 90%
- ✅ 平均回應時間 < 5 秒
- ✅ 錯誤情況有友善提示
- ✅ 用戶滿意度回饋正面

---

### 📊 分階段交付里程碑

```
Week 1
├── Phase 0 完成：準備工作 ✓
└── Phase 1 完成：單專案查詢可用 ✓
    → 🎯 里程碑 1：MVP 可展示

Week 2
├── Phase 2 完成：FW 層級查詢可用 ✓
└── Phase 3 開始：狀態篩選
    → 🎯 里程碑 2：核心功能完成

Week 3
├── Phase 3 完成：狀態篩選可用 ✓
├── Phase 4 完成：跨專案搜尋可用 ✓
└── Phase 5 完成：優化調整 ✓
    → 🎯 里程碑 3：全功能上線
```

---

### 🚀 快速啟動建議

**如果時間有限，建議最小可行版本 (MVP)**：

| 階段 | 內容 | 時間 | 可回答的問題 |
|------|------|------|-------------|
| **MVP v0.1** | Phase 0 + Phase 1 | 3 天 | 單專案測試結果查詢 |
| **MVP v0.2** | + Phase 2 | +3 天 | FW 層級測試查詢 |
| **MVP v0.3** | + Phase 3 | +3 天 | 狀態篩選查詢 |
| **Full** | + Phase 4 + 5 | +3 天 | 完整功能 |

**MVP v0.1 可回答**：
- ✅ "SAF-2024-001 的測試結果如何？"
- ✅ "Project Alpha 有做過哪些測試？"

**MVP v0.2 可回答**：
- ✅ "Project Alpha 的 512GB FW 有哪些測試類別？"
- ✅ "這個案子 512GB 的 NVMe_Validation_Tool 有哪些測項？"

**MVP v0.3 可回答**：
- ✅ "NVMe_Validation_Tool 有 PASS 的案子有哪些？"
- ✅ "列出這個案子 512GB 的全部測試項目"

---

## 📚 相關文檔

- SAF Assistant 現有架構文檔（待補充）
- Dify 工作流程開發指南
- Django API 開發規範

---

## 📝 更新記錄

| 日期 | 版本 | 更新內容 | 更新者 |
|------|------|---------|-------|
| 2024-12-09 | v1.0 | 初始規劃文件建立 | AI Platform Team |
| 2024-12-09 | v1.1 | 新增意圖 5-8（FW 層級查詢、狀態篩選）<br>新增測試狀態定義<br>更新實作優先順序<br>新增測試案例 | AI Platform Team |
| 2024-12-09 | v1.2 | 新增詳細分階段實作計劃<br>新增 Phase 0-5 詳細步驟<br>新增 MVP 快速啟動建議<br>新增里程碑交付時程 | AI Platform Team |
| 2024-12-09 | v1.3 | Phase 0 API 確認完成<br>確認測試結果格式<br>確認專案列表和 FW 版本格式 | AI Platform Team |
| 2024-12-09 | v1.4 | Phase 1 Intent 1 實作完成<br>新增 TestCategorySearchHandler<br>更新 Intent Analyzer prompt | AI Platform Team |
| 2024-12-10 | v1.5 | Phase 2 Intent 5 實作完成<br>新增 FWTestCategoriesHandler<br>標記 Intent 6-7 暫緩（API 不支援 test items） | AI Platform Team |

---

**🎯 下一步行動**：
1. **Phase 3**：實作 Intent 8（測試狀態專案篩選）
2. **需要確認**：
   - 是否有其他 API 端點提供 test items 詳細資料
   - Intent 6-7 待 API 支援後再實作
3. **已完成**：
   - ✅ Intent 1：跨專案測試類別查詢
   - ✅ Intent 5：專案 FW 測試類別查詢
