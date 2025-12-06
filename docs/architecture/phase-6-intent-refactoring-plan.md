# Phase 6: 意圖系統重構規劃

## 📋 概述

根據 SAF API Server 新增的 API 端點，需要重新規劃「指定專案 + 指定 FW 版本」相關的意圖和 API 對應關係。

### 當前問題

1. **API 端點對應不清晰**：現有意圖沒有明確對應到新的 API 端點
2. **階層結構混淆**：Project → FW Version 的階層關係在意圖中沒有清楚表達
3. **缺少新 API 支援**：以下新 API 尚未整合：
   - `GET /api/v1/projects/{project_uid}/firmware-summary` (Firmware 詳細摘要)
   - `GET /api/v1/projects/{project_id}/firmwares` (專案 Firmware 列表)
   - `GET /api/v1/projects/{project_uid}/full-summary` (完整專案摘要)

---

## 🔍 SAF API 端點分析

### API 端點清單

| # | API 端點 | 路徑參數 | 用途 | 狀態 |
|---|----------|----------|------|------|
| 1 | `GET /api/v1/projects` | - | 取得專案列表（含 children） | ✅ 已實現 |
| 2 | `GET /api/v1/projects/summary` | - | 專案統計摘要 | ✅ 已實現 |
| 3 | `GET /api/v1/projects/{project_uid}/test-summary` | project_uid | 測試結果摘要（按類別和容量） | ✅ 已實現 |
| 4 | `GET /api/v1/projects/{project_uid}/firmware-summary` | project_uid | **🆕 Firmware 詳細摘要** | ❌ 待實現 |
| 5 | `GET /api/v1/projects/{project_id}/firmwares` | project_id | **🆕 專案 Firmware 列表** | ❌ 待實現 |
| 6 | `GET /api/v1/projects/{project_uid}/full-summary` | project_uid | **🆕 完整專案摘要** | ❌ 待實現 |

### 關鍵概念釐清

#### 1. `project_uid` vs `project_id` vs `projectName`

```
SAF 資料結構：
├── projectId (專案 ID，同一專案不同 FW 版本共用)
│   ├── projectUid_1 (FW 版本 1 的唯一 ID)
│   ├── projectUid_2 (FW 版本 2 的唯一 ID)
│   └── projectUid_3 (FW 版本 3 的唯一 ID)
└── projectName (專案名稱，如 "Springsteen"、"DEMETER")
```

| 欄位 | 說明 | 範例 | 用途 |
|------|------|------|------|
| `projectName` | 專案名稱 | "Springsteen" | 用戶查詢時使用 |
| `projectId` | 專案 ID | "8e9fe3fa43694a2c8a7cef9e42620f60" | 取得 FW 列表用 |
| `projectUid` | 專案實例 UID | "00e11fc25a3f454e9e3860ff67dd2c07" | 取得測試結果用 |
| `fw` | FW 版本名稱 | "G200X6EC" | 用戶查詢時使用 |

#### 2. API 呼叫流程

```
用戶查詢: "Springsteen G200X6EC 測試結果"
          ↓
Step 1: GET /api/v1/projects → 找到 projectName="Springsteen" + fw="G200X6EC" 的記錄
          ↓
Step 2: 取得 projectUid="00e11fc25a3f454e9e3860ff67dd2c07"
          ↓
Step 3: GET /api/v1/projects/{projectUid}/test-summary
          ↓
Step 4: 返回測試結果
```

---

## 🎯 意圖系統重新設計

### 現有意圖 vs 新意圖規劃

#### 保留的意圖（Phase 1-5 已實現）

| 意圖 | 說明 | 對應 API | 狀態 |
|------|------|----------|------|
| `query_projects_by_customer` | 按客戶查詢專案 | projects | ✅ |
| `query_projects_by_controller` | 按控制器查詢專案 | projects | ✅ |
| `query_project_detail` | 查詢專案詳情 | projects | ✅ |
| `query_project_test_summary` | 查詢專案測試摘要 | test-summary | ✅ |
| `query_project_test_summary_by_fw` | 按 FW 版本查詢測試摘要 | test-summary | ✅ |
| `compare_fw_versions` | 比較兩個 FW 版本 | test-summary x2 | ✅ |
| `count_projects` | 統計專案數量 | projects | ✅ |
| `list_all_customers` | 列出所有客戶 | projects | ✅ |
| `list_all_controllers` | 列出所有控制器 | projects | ✅ |

#### 🆕 新增意圖（Phase 6）

| 意圖 | 說明 | 對應 API | 優先級 |
|------|------|----------|--------|
| `query_fw_detail_summary` | 查詢單一 FW 詳細摘要 | firmware-summary | 🔴 高 |
| `list_project_firmwares` | 列出專案所有 FW 版本 | firmwares | 🔴 高 |
| `query_project_full_summary` | 查詢專案完整摘要（含所有 FW） | full-summary | 🟡 中 |

---

## 📊 新意圖詳細設計

### 1. `query_fw_detail_summary` - 查詢 FW 詳細摘要

**用途**：取得單一 Firmware 的詳細測試統計（包含樣本統計、測試項目統計等）

**對應 API**：`GET /api/v1/projects/{project_uid}/firmware-summary`

**必要參數**：
- `project_name`: 專案名稱
- `fw_version`: FW 版本

**自然語言範例**：
```
✅ "Springsteen G200X6EC 的詳細測試統計"
✅ "查詢 DEMETER Y1114B 的樣本使用率"
✅ "G200X8CA firmware 詳細摘要"
✅ "Springsteen G200X85A 測試項目失敗率是多少"
✅ "查看 Channel 82CBW5QF 的完成率"
```

**回應內容**：
```json
{
  "fw_name": "G200X85A_OPAL",
  "overview": {
    "total_test_items": 61,
    "passed": 44,
    "failed": 16,
    "completion_rate": 100.0,
    "pass_rate": 73.33
  },
  "sample_stats": {
    "total_samples": 140,
    "samples_used": 0,
    "utilization_rate": 0.0
  },
  "test_item_stats": {
    "total_items": 39,
    "passed_items": 25,
    "failed_items": 14,
    "fail_rate": 36.0
  }
}
```

**與現有 `query_project_test_summary_by_fw` 的差異**：

| 項目 | test-summary (現有) | firmware-summary (新增) |
|------|---------------------|-------------------------|
| API | `/test-summary` | `/firmware-summary` |
| 資料維度 | 按類別 + 容量 | 整體統計 + 樣本 + 測試項目 |
| 適用場景 | 查看不同測試類別的結果 | 查看整體效能指標 |
| 回應重點 | 各類別 Pass/Fail 明細 | 完成率、樣本使用率、失敗率 |

---

### 2. `list_project_firmwares` - 列出專案 FW 列表

**用途**：列出特定專案下所有的 Firmware 版本

**對應 API**：`GET /api/v1/projects/{project_id}/firmwares`

**必要參數**：
- `project_name`: 專案名稱

**自然語言範例**：
```
✅ "Springsteen 有哪些 FW 版本"
✅ "列出 DEMETER 所有 firmware"
✅ "Channel 有幾個 FW 版本"
✅ "查詢 Bennington 的 firmware 列表"
✅ "Springsteen 目前有哪些版本可以查"
```

**回應內容**：
```json
{
  "project_name": "Springsteen",
  "total_firmwares": 447,
  "firmwares": [
    {"fw": "G200X6EC", "subVersion": "AA", "projectUid": "xxx"},
    {"fw": "G200X8CA", "subVersion": "AA", "projectUid": "yyy"},
    ...
  ]
}
```

**注意事項**：
- 需要先從 `projects` API 取得 `projectId`
- 再用 `projectId` 呼叫 `/firmwares` API

---

### 3. `query_project_full_summary` - 查詢專案完整摘要

**用途**：取得專案的完整摘要，包含所有 Firmware 的統計資訊與聚合統計

**對應 API**：`GET /api/v1/projects/{project_uid}/full-summary`

**必要參數**：
- `project_name`: 專案名稱

**可選參數**：
- `fw_version`: 如果指定，只顯示該 FW 的詳情（否則顯示所有 FW）

**自然語言範例**：
```
✅ "Springsteen 專案的完整測試報告"
✅ "查詢 DEMETER 所有 FW 的整體通過率"
✅ "Springsteen 專案總共跑了多少測試"
✅ "Channel 專案的整體測試狀況"
✅ "給我 Bennington 的完整摘要"
```

**回應內容**：
```json
{
  "project_name": "Springsteen",
  "total_firmwares": 2,
  "firmwares": [...],
  "aggregated_stats": {
    "total_test_items": 122,
    "total_passed": 88,
    "total_failed": 32,
    "overall_pass_rate": 73.33
  }
}
```

---

## 🔄 意圖識別決策樹

```
用戶查詢解析
    │
    ├─ 包含專案名稱？
    │   │
    │   ├─ 否 → 全域查詢意圖
    │   │       ├─ "有幾個專案" → count_projects
    │   │       ├─ "所有客戶" → list_all_customers
    │   │       └─ "所有控制器" → list_all_controllers
    │   │
    │   └─ 是 → 專案相關意圖
    │           │
    │           ├─ 包含 FW 版本？
    │           │   │
    │           │   ├─ 否 → 專案級查詢
    │           │   │       ├─ "FW 列表/有哪些版本" → list_project_firmwares 🆕
    │           │   │       ├─ "完整摘要/整體報告" → query_project_full_summary 🆕
    │           │   │       ├─ "測試摘要/結果" → query_project_test_summary
    │           │   │       └─ "專案資訊/詳情" → query_project_detail
    │           │   │
    │           │   └─ 是 → FW 級查詢
    │           │           │
    │           │           ├─ 包含第二個 FW 版本？
    │           │           │   │
    │           │           │   ├─ 是 → compare_fw_versions
    │           │           │   │
    │           │           │   └─ 否 → 單一 FW 查詢
    │           │           │           ├─ "詳細統計/樣本/完成率" → query_fw_detail_summary 🆕
    │           │           │           └─ "測試結果/Pass/Fail" → query_project_test_summary_by_fw
    │           │           │
    │           │           └─ ...
    │           │
    │           └─ ...
    │
    └─ 按客戶/控制器過濾？
            ├─ "客戶 XXX" → query_projects_by_customer
            └─ "控制器 XXX" → query_projects_by_controller
```

---

## 🔧 API 處理流程

### 流程 A: `list_project_firmwares`

```
1. 用戶: "Springsteen 有哪些 FW 版本"
   │
2. 意圖分析: list_project_firmwares {project_name: "Springsteen"}
   │
3. Handler 執行:
   ├── Step 1: GET /api/v1/projects (flatten=True)
   │           → 找到 projectName="Springsteen" 的第一筆記錄
   │           → 取得 projectId
   │
   ├── Step 2: GET /api/v1/projects/{projectId}/firmwares
   │           → 取得所有 FW 列表
   │
   └── Step 3: 格式化回應
               → "Springsteen 共有 447 個 FW 版本: G200X6EC, G200X8CA, ..."
```

### 流程 B: `query_fw_detail_summary`

```
1. 用戶: "Springsteen G200X6EC 的詳細測試統計"
   │
2. 意圖分析: query_fw_detail_summary {project_name: "Springsteen", fw_version: "G200X6EC"}
   │
3. Handler 執行:
   ├── Step 1: GET /api/v1/projects (flatten=True)
   │           → 找到 projectName="Springsteen" + fw 包含 "G200X6EC"
   │           → 取得 projectUid
   │
   ├── Step 2: GET /api/v1/projects/{projectUid}/firmware-summary
   │           → 取得 FW 詳細摘要
   │
   └── Step 3: 格式化回應
               → "G200X6EC 測試完成率: 100%, 通過率: 73.33%..."
```

### 流程 C: `query_project_full_summary`

```
1. 用戶: "Springsteen 專案的完整測試報告"
   │
2. 意圖分析: query_project_full_summary {project_name: "Springsteen"}
   │
3. Handler 執行:
   ├── Step 1: GET /api/v1/projects (flatten=True)
   │           → 找到 projectName="Springsteen" 的第一筆記錄
   │           → 取得 projectUid
   │
   ├── Step 2: GET /api/v1/projects/{projectUid}/full-summary
   │           → 取得完整摘要（含所有 FW）
   │
   └── Step 3: 格式化回應
               → "Springsteen 共有 2 個 FW 版本，整體通過率: 73.33%..."
```

---

## 📁 實作檔案清單

### 1. 意圖定義更新

```python
# library/saf_integration/smart_query/intent_types.py

class IntentType(Enum):
    # ... 現有意圖 ...
    
    # 🆕 Phase 6: 新增意圖
    QUERY_FW_DETAIL_SUMMARY = "query_fw_detail_summary"
    LIST_PROJECT_FIRMWARES = "list_project_firmwares"
    QUERY_PROJECT_FULL_SUMMARY = "query_project_full_summary"
```

### 2. API 端點註冊

```python
# library/saf_integration/endpoint_registry.py

SAF_ENDPOINTS = {
    # ... 現有端點 ...
    
    # 🆕 Phase 6: 新增端點
    "firmware_summary": {
        "path": "/api/v1/projects/{project_uid}/firmware-summary",
        "method": "GET",
        "description": "查詢單一 Firmware 的詳細統計",
        "path_params": ["project_uid"],
        "enabled": True
    },
    "project_firmwares": {
        "path": "/api/v1/projects/{project_id}/firmwares",
        "method": "GET",
        "description": "取得專案的 Firmware 列表",
        "path_params": ["project_id"],
        "enabled": True
    },
    "full_summary": {
        "path": "/api/v1/projects/{project_uid}/full-summary",
        "method": "GET",
        "description": "查詢專案完整摘要",
        "path_params": ["project_uid"],
        "enabled": True
    }
}
```

### 3. API Client 新增方法

```python
# library/saf_integration/api_client.py

class SAFAPIClient:
    # ... 現有方法 ...
    
    def get_firmware_summary(self, project_uid: str) -> Optional[Dict]:
        """取得 Firmware 詳細摘要"""
        pass
    
    def get_project_firmwares(self, project_id: str) -> List[Dict]:
        """取得專案的 Firmware 列表"""
        pass
    
    def get_full_summary(self, project_uid: str) -> Optional[Dict]:
        """取得專案完整摘要"""
        pass
```

### 4. 新增 Handler

```
library/saf_integration/smart_query/query_handlers/
├── fw_detail_summary_handler.py      # 🆕 query_fw_detail_summary
├── list_project_firmwares_handler.py # 🆕 list_project_firmwares
└── full_summary_handler.py           # 🆕 query_project_full_summary
```

### 5. 意圖分析器更新

```python
# library/saf_integration/smart_query/intent_analyzer.py

# 新增 Phase 6 意圖描述和範例
PHASE_6_INTENTS = """
12. query_fw_detail_summary: 查詢單一 FW 的詳細統計
    - 常見說法：詳細統計、樣本使用率、完成率、測試項目統計
    - 必要參數：project_name, fw_version
    
13. list_project_firmwares: 列出專案的所有 FW 版本
    - 常見說法：有哪些 FW、FW 列表、版本列表、有幾個版本
    - 必要參數：project_name
    
14. query_project_full_summary: 查詢專案完整摘要
    - 常見說法：完整報告、整體摘要、所有 FW 統計
    - 必要參數：project_name
"""
```

---

## 📋 實作優先順序

### Phase 6.1 - 列出 FW 版本 (🔴 高優先)

**目標**：讓用戶可以查詢專案有哪些 FW 版本可查

| 任務 | 說明 | 預估時間 |
|------|------|----------|
| 6.1.1 | 新增 `list_project_firmwares` 意圖定義 | 15 min |
| 6.1.2 | 新增 `get_project_firmwares()` API Client 方法 | 30 min |
| 6.1.3 | 實作 `ListProjectFirmwaresHandler` | 45 min |
| 6.1.4 | 更新意圖分析 Prompt | 20 min |
| 6.1.5 | 測試案例撰寫 | 30 min |

### Phase 6.2 - FW 詳細摘要 (🔴 高優先)

**目標**：提供比 test-summary 更詳細的 FW 統計資訊

| 任務 | 說明 | 預估時間 |
|------|------|----------|
| 6.2.1 | 新增 `query_fw_detail_summary` 意圖定義 | 15 min |
| 6.2.2 | 新增 `get_firmware_summary()` API Client 方法 | 30 min |
| 6.2.3 | 實作 `FWDetailSummaryHandler` | 45 min |
| 6.2.4 | 更新意圖分析 Prompt | 20 min |
| 6.2.5 | 測試案例撰寫 | 30 min |

### Phase 6.3 - 完整專案摘要 (🟡 中優先)

**目標**：一次取得專案所有 FW 的聚合統計

| 任務 | 說明 | 預估時間 |
|------|------|----------|
| 6.3.1 | 新增 `query_project_full_summary` 意圖定義 | 15 min |
| 6.3.2 | 新增 `get_full_summary()` API Client 方法 | 30 min |
| 6.3.3 | 實作 `FullSummaryHandler` | 45 min |
| 6.3.4 | 更新意圖分析 Prompt | 20 min |
| 6.3.5 | 測試案例撰寫 | 30 min |

---

## ⚠️ 注意事項

### 1. API 路徑參數差異

```
⚠️ 注意：不同 API 使用不同的 ID 參數！

/firmwares API → 使用 project_id (專案 ID)
/firmware-summary API → 使用 project_uid (專案實例 UID)
/full-summary API → 使用 project_uid (專案實例 UID)
/test-summary API → 使用 project_uid (專案實例 UID)
```

### 2. ID 轉換邏輯

```python
# 從 projects API 取得的資料結構：
{
    "projectId": "8e9fe3fa43694a2c8a7cef9e42620f60",    # 用於 /firmwares
    "projectUid": "00e11fc25a3f454e9e3860ff67dd2c07",   # 用於其他 API
    "projectName": "Springsteen",
    "fw": "G200X6EC",
    ...
}

# Handler 需要根據目標 API 選擇正確的 ID
```

### 3. 快取考量

- `list_project_firmwares` 結果可以快取（FW 列表相對穩定）
- `firmware-summary` 結果需要較短的 TTL（測試結果會更新）
- `full-summary` 包含聚合統計，可以適度快取

---

## 📊 預期效益

| 效益 | 說明 |
|------|------|
| 🎯 查詢精確度 | 用戶可以更精確地查詢不同層級的資訊 |
| 📊 資訊完整度 | 提供樣本統計、測試項目統計等詳細資訊 |
| 🔍 探索性查詢 | 用戶可以先列出 FW 列表，再深入查詢 |
| ⚡ 效能優化 | full-summary 一次取得所有 FW 統計，減少多次查詢 |

---

## 📝 文件版本

| 版本 | 日期 | 說明 |
|------|------|------|
| v1.0 | 2025-12-07 | 初始規劃文件 |

---

**下一步**：確認規劃內容後，開始執行 Phase 6.1
