# SAF Assistant - Test Jobs 查詢功能開發計畫

## 📋 文件資訊
- **建立日期**: 2025-12-17
- **功能名稱**: 專案 FW 測項結果查詢 (Test Jobs Query)
- **狀態**: ⚠️ Django 端實作完成，等待 SAF API 端點實作
- **更新日期**: 2025-12-17

---

## � 實作進度

| 階段 | 狀態 | 說明 |
|------|------|------|
| Phase 1: API Client 擴展 | ✅ 完成 | endpoint_registry.py, api_client.py |
| Phase 2: Intent 定義 | ✅ 完成 | intent_types.py, intent_analyzer.py |
| Phase 3: Handler 實作 | ✅ 完成 | test_jobs_handler.py |
| Phase 4: Router 整合 | ✅ 完成 | query_router.py |
| Phase 5: 測試驗證 | ⚠️ 部分完成 | 意圖識別成功，SAF API 尚未實作 |

### 測試結果 (2025-12-17)

**意圖識別測試**：✅ 成功
```bash
# 測試查詢
curl -X POST "http://localhost/api/saf/smart-query/" \
  -H "Content-Type: application/json" \
  -d '{"query": "Springsteen 的 A222X4CA 測項結果"}'

# 結果
{
  "intent": {
    "type": "query_project_fw_test_jobs",  # ✅ 正確識別
    "parameters": {
      "project_name": "Springsteen",
      "fw_version": "A222X4CA"
    },
    "confidence": 0.95  # ✅ 高信心度
  }
}
```

**SAF API 端點測試**：❌ API 尚未實作
```bash
# 直接測試 SAF API
curl -X POST "http://10.252.170.171:8080/api/v1/projects/test-jobs" \
  -H "Authorization: 0" \
  -H "Authorization-Name: test" \
  -d '{"project_ids": ["8e9fe3fa43694a2c8a7cef9e42620f60"]}'

# 結果
{"detail":"Not Found"}  # ❌ API 端點不存在
```

### ⚠️ 待 SAF 團隊完成

1. **實作 API 端點**: `POST /api/v1/projects/test-jobs`
2. **Response 格式**: 需返回 test_jobs 列表和 total 欄位
3. **測試**: 完成後通知我們進行整合測試

---

## 🎯 功能目標

讓使用者能夠透過自然語言查詢特定專案、特定 FW 的測試項目結果，包括：
- Test Category（測試類別）
- Test Item（測試項目名稱）
- Capacity（容量）
- Test Status（測試狀態 Pass/Fail）
- Sample ID、Platform、Tool 等詳細資訊

### 使用情境範例
```
用戶問：「PM9M1 的 HHB0YBC1 測項結果」
用戶問：「PM9M1 HHB0YBC1 的測試項目結果」
用戶問：「查詢 PM9M1 FW HHB0YBC1 的所有測試結果」
```

---

## 🔍 新 API 說明

### API 端點
```
POST /api/v1/projects/test-jobs
```

### Request Headers
| Header | 值 | 說明 |
|--------|---|------|
| Content-Type | application/json | |
| Authorization | 使用者 ID (如 150) | SAF 使用者 ID |
| Authorization-Name | 使用者名稱 (如 test) | SAF 使用者名稱 |

### Request Body
```json
{
  "project_ids": ["專案ID1", "專案ID2"],
  "test_tool_key": ""
}
```

| 欄位 | 類型 | 必填 | 說明 |
|------|------|------|------|
| project_ids | string[] | 是 | 專案 ID 列表 |
| test_tool_key | string | 否 | 測試工具 Key（用於篩選，可為空字串）|

### Response 結構
```json
{
  "success": true,
  "data": {
    "test_jobs": [
      {
        "test_job_id": "1d291784c06111f0b40c0242ac280004",
        "fw": "HHB0YBC1",
        "test_plan_name": "Client_PCIe_Standard",
        "test_category_name": "NVMe_Validation_Tool",
        "root_id": "STC-4337",
        "test_item_name": "NVMe_Validation_Tool_2(oem_hp_test_v1_4_hp)",
        "test_status": "Fail",
        "sample_id": "SSD-Y-15767",
        "capacity": "1024GB",
        "platform": "PC-SSD-5836",
        "test_tool_key_list": ["snvt2"]
      }
    ],
    "total": 982
  }
}
```

### Response 欄位說明
| 欄位 | 說明 |
|------|------|
| test_job_id | 測試工作 ID |
| fw | 韌體版本 |
| test_plan_name | 測試計畫名稱 |
| test_category_name | 測試類別名稱 |
| root_id | Root ID |
| test_item_name | 測試項目名稱 |
| test_status | 測試狀態 (Pass / Fail) |
| sample_id | 樣品 ID |
| capacity | 容量 (如 1024GB) |
| platform | 測試平台 |
| test_tool_key_list | 測試工具 Key 列表 |

---

## 🏗️ 系統架構設計

### 專案名稱對應邏輯

**關鍵問題**：用戶可能只說「PM9M1」，但 API 需要的是完整專案名稱的 ID（如 `Client_PCIe_Samsung_PM9M1_SM2504XT_Samsung V9 TLC`）

**解決方案**：
1. 先透過現有的 `/api/v1/projects` API 獲取所有專案列表
2. 用戶輸入的專案名稱（如 `PM9M1`）進行模糊匹配
3. 找到符合的**父專案**（如 `Client_PCIe_Samsung_PM9M1_SM2504XT_Samsung V9 TLC`）
4. 獲取該父專案的 `projectUid` 作為 `project_ids` 參數

### 專案階層示意
```
Client_PCIe_Samsung_PM9M1_SM2504XT_Samsung V9 TLC  (父專案，用這個 ID)
├── PM9M1_HHB0YBC1   (子專案/FW版本)
├── PM9M1_HHB0YC2H   (子專案/FW版本)
└── PM9M1_HHB0YBC1   (子專案/FW版本)
```

---

## 📝 實作步驟

### Phase 1: API Client 擴展

#### 1.1 新增 Endpoint 配置
**檔案**: `/library/saf_integration/endpoint_registry.py`

```python
# 新增 test-jobs endpoint
"project_test_jobs": {
    "path": "/api/v1/projects/test-jobs",
    "method": "POST",
    "description": "查詢專案測試工作結果（含所有測項詳細資訊）",
    "params": {},
    "body_params": ["project_ids", "test_tool_key"],
    "transformer": "test_jobs_to_response",
    "enabled": True,
    "requires_auth": True
}
```

#### 1.2 API Client 新增方法
**檔案**: `/library/saf_integration/api_client.py`

```python
def get_project_test_jobs(
    self, 
    project_ids: List[str], 
    test_tool_key: str = ""
) -> Optional[Dict[str, Any]]:
    """
    獲取專案測試工作結果
    
    Args:
        project_ids: 專案 ID 列表
        test_tool_key: 測試工具 Key（可選篩選）
        
    Returns:
        測試工作結果資料
    """
    # 實作 POST 請求邏輯
    pass

def find_parent_project_id(self, project_name: str) -> Optional[str]:
    """
    根據專案名稱片段找到父專案 ID
    
    例如：輸入 "PM9M1" 
    找到 "Client_PCIe_Samsung_PM9M1_SM2504XT_Samsung V9 TLC" 的 ID
    
    Args:
        project_name: 專案名稱片段（如 PM9M1）
        
    Returns:
        父專案的 projectUid
    """
    pass
```

---

### Phase 2: Intent 定義

#### 2.1 新增意圖類型
**檔案**: `/library/saf_integration/smart_query/intent_types.py`

```python
# 在 IntentType enum 中新增
QUERY_PROJECT_FW_TEST_JOBS = "query_project_fw_test_jobs"  # 查詢專案 FW 測試工作結果
```

#### 2.2 更新意圖分析 Prompt
**檔案**: `/library/saf_integration/smart_query/intent_analyzer.py`

在 prompt 中新增意圖說明：

```
### XX. query_project_fw_test_jobs - 查詢專案 FW 測試工作結果 (Phase XX 新增)
用戶想查詢特定專案特定 FW 版本的完整測試結果（含 Test Category、Test Item、Capacity、Test Status 等）時使用。
這是查詢測試工作的完整詳細資訊，包括每個測試項目的執行狀態。
- 常見問法：
  - 「PM9M1 的 HHB0YBC1 測項結果」「PM9M1 HHB0YBC1 的測試項目結果」
  - 「查詢 XX 專案 FW YYY 的測試結果」「XX YYY 的測項狀態」
  - 「XX 專案 YYY 版本的測試項目」「列出 XX FW YYY 的所有測試」
  - 「XX 的 YYY 有哪些測試項目」「XX YYY 測試結果」
- 參數：
  - project_name (專案名稱，必須，可以是簡短名稱如 PM9M1)
  - fw_version (FW 版本，必須)
  - test_tool_key (選填，測試工具篩選)
- 【重要區分】
  - 如果用戶問「XX FW YYY 的測試結果/測項結果」→ 使用 query_project_fw_test_jobs（完整測試結果）
  - 如果用戶問「XX FW YYY 的測試統計/完成率」→ 使用 fw_detail_summary（統計摘要）
  - 如果用戶問「XX FW YYY 有哪些測試類別」→ 使用 query_project_fw_test_categories（類別列表）
```

#### 2.3 新增意圖範例
```
輸入：PM9M1 的 HHB0YBC1 測項結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_version": "HHB0YBC1"}, "confidence": 0.95}

輸入：PM9M1 HHB0YBC1 的測試項目結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "PM9M1", "fw_version": "HHB0YBC1"}, "confidence": 0.94}

輸入：查詢 Springsteen GD10YBJD 的測試結果
輸出：{"intent": "query_project_fw_test_jobs", "parameters": {"project_name": "Springsteen", "fw_version": "GD10YBJD"}, "confidence": 0.93}
```

---

### Phase 3: Handler 實作

#### 3.1 建立 Test Jobs Handler
**檔案**: `/library/saf_integration/smart_query/query_handlers/test_jobs_handler.py`

```python
"""
TestJobsHandler - 專案 FW 測試工作結果查詢
==========================================

處理 Phase XX 意圖：專案 FW 測試工作結果查詢
- 查詢特定專案特定 FW 版本的完整測試結果

API 端點：POST /api/v1/projects/test-jobs

特點：
- 支援簡短專案名稱（如 PM9M1）自動對應到完整專案 ID
- 返回完整測試項目列表（含 Category、Item、Status、Capacity 等）
- 支援測試工具篩選

作者：AI Platform Team
創建日期：2025-12-17
"""

import logging
from typing import Dict, Any, List, Optional

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class TestJobsHandler(BaseHandler):
    """
    專案 FW 測試工作結果查詢處理器
    
    支援的意圖：
    - query_project_fw_test_jobs: 查詢專案 FW 的完整測試結果
    
    用戶問法範例：
    - PM9M1 的 HHB0YBC1 測項結果
    - PM9M1 HHB0YBC1 的測試項目結果
    - 查詢 Springsteen GD10YBJD 的測試結果
    """
    
    handler_name = "test_jobs_handler"
    supported_intent = "query_project_fw_test_jobs"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行測試工作結果查詢
        
        Args:
            parameters: {
                "project_name": "PM9M1",
                "fw_version": "HHB0YBC1",
                "test_tool_key": "" (optional)
            }
            
        Returns:
            QueryResult: 包含測試工作結果列表
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(
            parameters, 
            required=['project_name', 'fw_version']
        )
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        project_name = parameters.get('project_name')
        fw_version = parameters.get('fw_version')
        test_tool_key = parameters.get('test_tool_key', '')
        
        try:
            # Step 1: 找到符合的專案（透過 FW 版本匹配）
            matched_project = self._find_project_by_fw(project_name, fw_version)
            
            if not matched_project:
                return self._handle_project_not_found(project_name, fw_version, parameters)
            
            project_uid = matched_project.get('projectUid')
            matched_fw = matched_project.get('fw', '')
            full_project_name = matched_project.get('projectName', '')
            
            logger.info(
                f"Test Jobs 查詢 - 版本匹配成功: {project_name} + {fw_version} "
                f"-> {full_project_name} / {matched_fw} (uid: {project_uid})"
            )
            
            # Step 2: 調用 Test Jobs API
            test_jobs_result = self.api_client.get_project_test_jobs(
                project_ids=[project_uid],
                test_tool_key=test_tool_key
            )
            
            if not test_jobs_result:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"無法獲取專案 '{project_name}' FW '{matched_fw}' 的測試結果"
                )
            
            # Step 3: 格式化回應
            return self._format_test_jobs_response(
                test_jobs=test_jobs_result,
                project_name=project_name,
                fw_version=matched_fw,
                full_project_name=full_project_name,
                project=matched_project,
                parameters=parameters
            )
            
        except Exception as e:
            logger.error(f"Test Jobs 查詢錯誤: {str(e)}")
            return self._handle_api_error(e, parameters)
    
    def _format_test_jobs_response(
        self,
        test_jobs: Dict[str, Any],
        project_name: str,
        fw_version: str,
        full_project_name: str,
        project: Dict[str, Any],
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """
        格式化測試工作結果回應
        """
        jobs = test_jobs.get('test_jobs', [])
        total = test_jobs.get('total', len(jobs))
        
        if not jobs:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"專案 {project_name} FW {fw_version} 沒有測試結果資料"
            )
        
        # 統計資訊
        pass_count = sum(1 for j in jobs if j.get('test_status') == 'Pass')
        fail_count = sum(1 for j in jobs if j.get('test_status') == 'Fail')
        
        # 按 Test Category 分組
        categories = {}
        for job in jobs:
            cat = job.get('test_category_name', 'Unknown')
            if cat not in categories:
                categories[cat] = {'pass': 0, 'fail': 0, 'items': []}
            categories[cat]['items'].append(job)
            if job.get('test_status') == 'Pass':
                categories[cat]['pass'] += 1
            else:
                categories[cat]['fail'] += 1
        
        # 格式化訊息
        message = self._build_response_message(
            project_name=project_name,
            fw_version=fw_version,
            total=total,
            pass_count=pass_count,
            fail_count=fail_count,
            categories=categories,
            jobs=jobs
        )
        
        # 構建表格資料（前端可用）
        table_data = [
            {
                'root_id': job.get('root_id'),
                'test_category': job.get('test_category_name'),
                'test_item': job.get('test_item_name'),
                'fw': job.get('fw'),
                'capacity': job.get('capacity'),
                'sample_id': job.get('sample_id'),
                'platform': job.get('platform'),
                'test_status': job.get('test_status'),
                'tool': ', '.join(job.get('test_tool_key_list', []))
            }
            for job in jobs
        ]
        
        return QueryResult.success(
            data={
                'project_name': project_name,
                'full_project_name': full_project_name,
                'fw_version': fw_version,
                'test_jobs': jobs,
                'total': total,
                'pass_count': pass_count,
                'fail_count': fail_count,
                'categories': categories
            },
            count=total,
            query_type=self.handler_name,
            parameters=parameters,
            message=message,
            metadata={
                'project_name': full_project_name,
                'customer': project.get('customer'),
                'controller': project.get('controller'),
                'fw': fw_version,
                'intent': 'query_project_fw_test_jobs'
            },
            table=table_data
        )
    
    def _build_response_message(
        self,
        project_name: str,
        fw_version: str,
        total: int,
        pass_count: int,
        fail_count: int,
        categories: Dict,
        jobs: List[Dict]
    ) -> str:
        """構建回應訊息（Markdown 格式）"""
        
        pass_rate = (pass_count / total * 100) if total > 0 else 0
        
        lines = [
            f"## 🧪 專案 {project_name} - FW {fw_version} 測試結果",
            "",
            f"**總測試項目**: {total} 個",
            f"**Pass**: {pass_count} | **Fail**: {fail_count} | **通過率**: {pass_rate:.1f}%",
            "",
            "### 測試結果列表",
            "",
            "| Root ID | Test Category | Test Item | Capacity | Sample | Platform | Status | Tool |",
            "|---------|---------------|-----------|----------|--------|----------|--------|------|"
        ]
        
        # 限制顯示數量（避免訊息過長）
        display_jobs = jobs[:50]  # 最多顯示 50 個
        
        for job in display_jobs:
            status_icon = "✅" if job.get('test_status') == 'Pass' else "❌"
            tool = ', '.join(job.get('test_tool_key_list', []))
            lines.append(
                f"| {job.get('root_id', '')} "
                f"| {job.get('test_category_name', '')} "
                f"| {job.get('test_item_name', '')[:40]}... "
                f"| {job.get('capacity', '')} "
                f"| {job.get('sample_id', '')} "
                f"| {job.get('platform', '')} "
                f"| {status_icon} {job.get('test_status', '')} "
                f"| {tool} |"
            )
        
        if len(jobs) > 50:
            lines.append(f"\n*（僅顯示前 50 項，共 {total} 項）*")
        
        # 按類別統計
        lines.extend([
            "",
            "### 📊 按類別統計",
            "",
            "| Test Category | Pass | Fail | Total |",
            "|---------------|------|------|-------|"
        ])
        
        for cat_name, cat_data in categories.items():
            cat_total = cat_data['pass'] + cat_data['fail']
            lines.append(
                f"| {cat_name} | {cat_data['pass']} | {cat_data['fail']} | {cat_total} |"
            )
        
        return "\n".join(lines)
    
    def _handle_project_not_found(
        self, 
        project_name: str, 
        fw_version: str,
        parameters: Dict[str, Any]
    ) -> QueryResult:
        """處理找不到專案的情況"""
        all_fw_versions = self._get_all_fw_versions(project_name)
        
        if all_fw_versions:
            fw_list = ", ".join(all_fw_versions[:5])
            more_info = f"（共 {len(all_fw_versions)} 個版本）" if len(all_fw_versions) > 5 else ""
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找不到專案 '{project_name}' 的 FW 版本 '{fw_version}'。\n可用版本：{fw_list}{more_info}"
            )
        else:
            return QueryResult.no_results(
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找不到專案 '{project_name}' 或該專案沒有 FW 版本資料"
            )
```

---

### Phase 4: Router 整合

#### 4.1 註冊 Handler
**檔案**: `/library/saf_integration/smart_query/query_router.py`

```python
# 導入新 Handler
from .query_handlers.test_jobs_handler import TestJobsHandler

# 在 handler 映射中新增
IntentType.QUERY_PROJECT_FW_TEST_JOBS: TestJobsHandler(),
```

#### 4.2 更新 Response Generator
**檔案**: `/library/saf_integration/smart_query/response_generator.py`

新增對應的回應生成邏輯。

---

## 📊 實作檢查清單

### Phase 1: API Client 擴展
- [ ] 在 `endpoint_registry.py` 新增 `project_test_jobs` endpoint
- [ ] 在 `api_client.py` 新增 `get_project_test_jobs()` 方法
- [ ] 在 `api_client.py` 新增 `find_parent_project_id()` 輔助方法
- [ ] 測試 API 連線和認證

### Phase 2: Intent 定義
- [ ] 在 `intent_types.py` 新增 `QUERY_PROJECT_FW_TEST_JOBS` enum
- [ ] 在 `intent_analyzer.py` 更新 prompt 說明
- [ ] 新增意圖識別範例（至少 5 個）
- [ ] 新增關鍵字匹配規則（「測項結果」「測試項目結果」等）

### Phase 3: Handler 實作
- [ ] 建立 `test_jobs_handler.py`
- [ ] 實作 `execute()` 方法
- [ ] 實作專案名稱對應邏輯（簡短名稱 → 完整專案 ID）
- [ ] 實作回應格式化（Markdown 表格）
- [ ] 實作錯誤處理

### Phase 4: Router 整合
- [ ] 在 `query_router.py` 註冊 Handler
- [ ] 在 `response_generator.py` 新增回應生成
- [ ] 整合測試

### Phase 5: 測試驗證
- [ ] 單元測試 API Client
- [ ] 單元測試 Intent 識別
- [ ] 整合測試完整流程
- [ ] 使用者驗收測試

---

## 🔑 關鍵技術細節

### 專案名稱匹配邏輯

```python
def find_parent_project_id(self, short_name: str, fw_version: str) -> Optional[str]:
    """
    根據簡短專案名稱和 FW 版本找到對應的專案 ID
    
    匹配策略：
    1. 先找所有 projectName 包含 short_name 的專案
    2. 在這些專案中找 fw 欄位匹配 fw_version 的
    3. 返回該專案的 projectUid
    
    範例：
    - short_name: "PM9M1"
    - fw_version: "HHB0YBC1"
    - 找到: Client_PCIe_Samsung_PM9M1_SM2504XT_Samsung V9 TLC (子專案 fw=HHB0YBC1)
    - 返回: 該子專案的 projectUid
    """
    all_projects = self.get_all_projects(flatten=True)
    
    short_name_lower = short_name.lower()
    fw_version_upper = fw_version.upper()
    
    for project in all_projects:
        project_name = project.get('projectName', '')
        project_fw = project.get('fw', '')
        
        # 專案名稱包含 short_name 且 FW 匹配
        if (short_name_lower in project_name.lower() and 
            project_fw.upper() == fw_version_upper):
            return project.get('projectUid')
    
    return None
```

### 認證處理

Test Jobs API 需要認證 headers，確保 `auth_manager` 正確配置：

```python
# SAFAuthManager 需提供的 headers
{
    "Authorization": "150",  # 使用者 ID
    "Authorization-Name": "test"  # 使用者名稱
}
```

---

## 📅 預估時程

| Phase | 工作項目 | 預估時間 |
|-------|---------|----------|
| Phase 1 | API Client 擴展 | 1 小時 |
| Phase 2 | Intent 定義 | 1 小時 |
| Phase 3 | Handler 實作 | 2 小時 |
| Phase 4 | Router 整合 | 0.5 小時 |
| Phase 5 | 測試驗證 | 1.5 小時 |
| **總計** | | **6 小時** |

---

## 📝 備註

1. **API 限制**: Test Jobs API 可能返回大量資料（範例中 total=982），需考慮分頁或限制顯示數量
2. **效能考量**: 建議對結果進行快取，避免重複查詢
3. **錯誤處理**: 需處理專案不存在、FW 版本不存在、API 超時等情況
4. **前端整合**: 返回的 `table` 欄位可直接用於前端表格渲染

---

## 🔗 相關文件

- [SAF API Client](/library/saf_integration/api_client.py)
- [Intent Analyzer](/library/saf_integration/smart_query/intent_analyzer.py)
- [Query Router](/library/saf_integration/smart_query/query_router.py)
- [Base Handler](/library/saf_integration/smart_query/query_handlers/base_handler.py)
- [FW All Test Items Handler](/library/saf_integration/smart_query/query_handlers/fw_all_test_items_handler.py) - 可參考的類似實作
