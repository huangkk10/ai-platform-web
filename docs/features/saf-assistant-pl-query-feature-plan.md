# SAF Assistant - PL 查詢功能規劃方案

## 📋 文件資訊

| 項目 | 內容 |
|------|------|
| **功能名稱** | SAF Assistant PL（專案負責人）查詢功能 |
| **Phase** | Phase 7 |
| **建立日期** | 2025-12-08 |
| **狀態** | ✅ 已完成 |
| **負責人** | AI Platform Team |

---

## 🎯 功能目標

新增 **按 PL（專案負責人 / Project Leader）查詢專案** 的功能，讓使用者可以透過 SAF Assistant 詢問：

- 「Ryder 負責哪些專案？」
- 「ryder.lin 的專案有哪些？」
- 「列出 Jeffery 管理的專案」
- 「查詢專案負責人是 Wei-Zhen 的專案」
- 「哪些專案是 bruce.zhang 負責的」

---

## 📊 背景分析

### SAF API 資料結構確認

透過 SAF API 測試，確認專案資料中包含 `pl` 欄位：

```json
{
  "key": "...",
  "projectUid": "...",
  "projectId": "...",
  "projectName": "DEMETER",
  "productCategory": "Automotive_PCIe",
  "customer": "WD",
  "controller": "SM2264XT",
  "subVersion": "AC",
  "nand": "WDC BiCS5 TLC",
  "fw": "[Demeter01][X0426E][dec97ba]",
  "pl": "Ryder",                          // ✅ PL 欄位存在
  "status": 3,
  "visible": true,
  "createdBy": "anila.hsu",
  "taskId": "SM2264AUTO-3993"
}
```

### 已知 PL 名稱範例

從 SAF 資料中發現的 PL 名稱格式：
- 簡稱：`Ryder`, `Jeffery`, `Wei-Zhen`, `Zhenyuan`
- 完整格式：`ryder.lin`, `jeffery.kuo`, `bruce.zhang`, `Zhenyuan Peng`

---

## 📁 需要修改的檔案

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `library/saf_integration/smart_query/intent_types.py` | 修改 | 新增 `QUERY_PROJECTS_BY_PL` 意圖 |
| `library/saf_integration/smart_query/intent_analyzer.py` | 修改 | 新增 PL 查詢的 Prompt 說明 |
| `library/saf_integration/smart_query/query_handlers/pl_handler.py` | **新增** | PL 查詢處理器 |
| `library/saf_integration/smart_query/query_handlers/__init__.py` | 修改 | 導出 `PLHandler` |
| `library/saf_integration/smart_query/query_router.py` | 修改 | 註冊 `PLHandler` |
| `library/saf_integration/data_transformer.py` | 修改 | 新增 `pl` 欄位到內容和元數據 |
| `library/saf_integration/endpoint_registry.py` | 修改 | 新增 `pl` 到搜尋欄位 |

---

## 📝 詳細實作規劃

### 1️⃣ intent_types.py - 新增意圖類型

**新增意圖枚舉**：
```python
class IntentType(Enum):
    # ... 現有意圖
    
    # 🆕 Phase 7: 按 PL 查詢專案
    QUERY_PROJECTS_BY_PL = "query_projects_by_pl"
```

**更新方法**：
- `get_description()`: 新增 `"按專案負責人查詢專案"`
- `get_required_parameters()`: 新增 `["pl"]`
- `get_optional_parameters()`: 空列表

**新增已知 PL 清單**：
```python
KNOWN_PLS = [
    'Ryder', 'ryder.lin', 
    'Jeffery', 'jeffery.kuo',
    'bruce.zhang', 
    'Wei-Zhen', 
    'Zhenyuan', 'Zhenyuan Peng',
    # ... 可擴展
]
```

---

### 2️⃣ intent_analyzer.py - 新增 Prompt

在 `INTENT_ANALYSIS_PROMPT` 中新增意圖說明：

```
### X. query_projects_by_pl - 按專案負責人查詢專案
用戶想知道某位專案負責人（PL / Project Leader）負責哪些專案時使用。
- 常見問法：
  - 「Ryder 負責哪些專案」「ryder.lin 的專案」
  - 「Jeffery 管理的專案有哪些」「查詢 PL 是 Wei-Zhen 的專案」
  - 「哪些專案是 bruce.zhang 負責的」「列出 Zhenyuan 的專案」
  - 「XX 的專案有哪些」（當 XX 是人名時）
- 參數：pl (專案負責人名稱)
- 【區分】
  - 如果名稱是公司名（WD, Samsung）→ 使用 query_projects_by_customer
  - 如果名稱是人名（Ryder, Jeffery）→ 使用 query_projects_by_pl
```

**新增範例**：
```
輸入：Ryder 負責哪些專案？
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Ryder"}, "confidence": 0.95}

輸入：ryder.lin 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "ryder.lin"}, "confidence": 0.93}

輸入：查詢 PL 是 Jeffery 的專案
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "Jeffery"}, "confidence": 0.92}

輸入：哪些專案是 bruce.zhang 負責的
輸出：{"intent": "query_projects_by_pl", "parameters": {"pl": "bruce.zhang"}, "confidence": 0.90}
```

---

### 3️⃣ pl_handler.py - 新增處理器（新檔案）

```python
"""
PLHandler - 按專案負責人查詢專案
================================

處理 query_projects_by_pl 意圖。

作者：AI Platform Team
創建日期：2025-12-08
"""

import logging
from typing import Dict, Any, List

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class PLHandler(BaseHandler):
    """
    專案負責人查詢處理器
    
    處理按 PL（Project Leader）查詢專案的請求。
    """
    
    handler_name = "pl_handler"
    supported_intent = "query_projects_by_pl"
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行按 PL 查詢專案
        
        Args:
            parameters: {"pl": "Ryder"}
            
        Returns:
            QueryResult: 包含該 PL 負責的所有專案
        """
        self._log_query(parameters)
        
        # 驗證參數
        error = self.validate_parameters(parameters, required=['pl'])
        if error:
            return QueryResult.error(error, self.handler_name, parameters)
        
        pl = parameters.get('pl')
        
        try:
            # 獲取所有專案
            projects_list = self.api_client.get_all_projects()
            
            if not projects_list:
                return QueryResult.error(
                    "無法獲取專案列表",
                    self.handler_name,
                    parameters
                )
            
            # 過濾指定 PL 的專案（模糊匹配）
            filtered_projects = self._filter_projects_by_pl(
                projects_list, 
                pl
            )
            
            if not filtered_projects:
                return QueryResult.no_results(
                    query_type=self.handler_name,
                    parameters=parameters,
                    message=f"找不到專案負責人 '{pl}' 的專案"
                )
            
            # 格式化結果
            formatted_projects = [
                self._format_project_data(p) for p in filtered_projects
            ]
            
            result = QueryResult.success(
                data=formatted_projects,
                query_type=self.handler_name,
                parameters=parameters,
                message=f"找到 {len(formatted_projects)} 個 {pl} 負責的專案"
            )
            
            self._log_result(result)
            return result
            
        except Exception as e:
            return self._handle_api_error(e, parameters)
    
    def _filter_projects_by_pl(
        self, 
        projects: List[Dict[str, Any]], 
        pl: str
    ) -> List[Dict[str, Any]]:
        """
        按 PL 過濾專案（支援模糊匹配）
        
        匹配規則：
        1. 精確匹配（大小寫不敏感）
        2. 包含匹配（用於 ryder.lin 匹配 Ryder）
        
        Args:
            projects: 專案列表
            pl: PL 名稱（如 Ryder, ryder.lin）
            
        Returns:
            過濾後的專案列表
        """
        pl_lower = pl.lower()
        filtered = []
        
        for project in projects:
            project_pl = project.get('pl', '')
            if not project_pl:
                continue
                
            project_pl_lower = project_pl.lower()
            
            # 精確匹配或包含匹配
            if (project_pl_lower == pl_lower or 
                pl_lower in project_pl_lower or
                project_pl_lower in pl_lower):
                filtered.append(project)
        
        return filtered
```

---

### 4️⃣ query_handlers/__init__.py - 導出新處理器

```python
from .pl_handler import PLHandler

__all__ = [
    # ... 現有
    'PLHandler',
]
```

---

### 5️⃣ query_router.py - 註冊處理器

```python
from .query_handlers import (
    # ... 現有
    PLHandler,
)

def _register_handlers(self):
    # ... 現有處理器
    
    # Phase 7: PL 處理器
    pl_handler = PLHandler()
    
    self._handlers = {
        # ... 現有
        
        # Phase 7: 按 PL 查詢
        IntentType.QUERY_PROJECTS_BY_PL: pl_handler,
    }
```

---

### 6️⃣ data_transformer.py - 新增 PL 欄位

**在 `_build_project_content()` 中新增**：
```python
def _build_project_content(self, project: Dict[str, Any]) -> str:
    lines = []
    
    # 基本資訊
    lines.append(f"專案名稱: {project.get('projectName', 'N/A')}")
    lines.append(f"客戶: {project.get('customer', 'N/A')}")
    
    # 🆕 專案負責人
    if project.get("pl"):
        lines.append(f"專案負責人 (PL): {project.get('pl')}")
    
    # ... 其他欄位
```

**在 `metadata` 中新增**：
```python
metadata = {
    "source": "saf_projects",
    "project_id": project_id,
    "project_name": project_name,
    "customer": customer,
    "pl": project.get("pl", ""),  # 🆕 新增
    # ... 其他欄位
}
```

---

### 7️⃣ endpoint_registry.py - 新增搜尋欄位

```python
SAF_ENDPOINTS = {
    "projects": {
        "path": "/api/v1/projects",
        "method": "GET",
        "description": "查詢 SAF 專案列表（完整資訊）",
        "params": {
            "page": 1,
            "size": 100
        },
        "search_fields": [
            "projectName", 
            "customer", 
            "controller", 
            "nand", 
            "fw", 
            "productCategory",
            "pl"  # 🆕 新增
        ],
        # ...
    },
}
```

---

## 📊 功能規格表

| 項目 | 內容 |
|------|------|
| **意圖名稱** | `query_projects_by_pl` |
| **必要參數** | `pl`（專案負責人名稱） |
| **可選參數** | 無 |
| **處理器** | `PLHandler` |
| **支援匹配** | 精確匹配 + 包含匹配（大小寫不敏感） |

---

## 💬 支援的問法範例

| 問題 | 識別結果 |
|------|----------|
| Ryder 負責哪些專案？ | `{"intent": "query_projects_by_pl", "parameters": {"pl": "Ryder"}}` |
| ryder.lin 的專案 | `{"intent": "query_projects_by_pl", "parameters": {"pl": "ryder.lin"}}` |
| 列出 Jeffery 管理的專案 | `{"intent": "query_projects_by_pl", "parameters": {"pl": "Jeffery"}}` |
| 查詢 PL 是 Wei-Zhen 的專案 | `{"intent": "query_projects_by_pl", "parameters": {"pl": "Wei-Zhen"}}` |
| 哪些專案是 bruce.zhang 負責的 | `{"intent": "query_projects_by_pl", "parameters": {"pl": "bruce.zhang"}}` |

---

## 🔄 與現有功能的區分

| 情境 | 使用意圖 |
|------|----------|
| 「WD 有哪些專案」→ WD 是客戶 | `query_projects_by_customer` |
| 「Ryder 負責哪些專案」→ Ryder 是人名 | `query_projects_by_pl` |
| 「SM2264 用在哪些專案」→ SM2264 是控制器 | `query_projects_by_controller` |

**區分邏輯**：
- 客戶名稱通常是公司名：WD, Samsung, Micron, Transcend, ADATA 等
- PL 名稱通常是人名：包含 `.`（如 ryder.lin）或首字母大寫的人名（如 Ryder, Jeffery）

---

## 📅 實作工作量估計

| 步驟 | 估計時間 |
|------|----------|
| 修改 intent_types.py | 5 分鐘 |
| 修改 intent_analyzer.py | 10 分鐘 |
| 新增 pl_handler.py | 15 分鐘 |
| 修改 __init__.py | 2 分鐘 |
| 修改 query_router.py | 5 分鐘 |
| 修改 data_transformer.py | 5 分鐘 |
| 修改 endpoint_registry.py | 2 分鐘 |
| 測試驗證 | 10 分鐘 |
| **總計** | **約 55 分鐘** |

---

## 🧪 測試計畫

### 單元測試
```python
def test_pl_handler_basic():
    """測試基本 PL 查詢"""
    handler = PLHandler()
    result = handler.execute({"pl": "Ryder"})
    assert result.success
    assert len(result.data) > 0

def test_pl_handler_fuzzy_match():
    """測試模糊匹配"""
    handler = PLHandler()
    # ryder.lin 應該匹配 Ryder
    result = handler.execute({"pl": "ryder.lin"})
    assert result.success

def test_pl_handler_not_found():
    """測試找不到 PL 的情況"""
    handler = PLHandler()
    result = handler.execute({"pl": "NotExistPL"})
    assert not result.success or len(result.data) == 0
```

### 整合測試（SAF Assistant 對話）
```
User: Ryder 負責哪些專案？
Expected: 返回 Ryder 負責的專案列表

User: ryder.lin 的專案
Expected: 返回 ryder.lin 負責的專案列表（與 Ryder 結果相同或重疊）

User: 查詢 PL 是 Jeffery 的專案
Expected: 返回 Jeffery 負責的專案列表
```

---

## ✅ 確認清單

- [x] SAF API 確實返回 `pl` 欄位
- [x] 實作 intent_types.py 修改
- [x] 實作 intent_analyzer.py 修改
- [x] 實作 pl_handler.py（新檔案）
- [x] 實作 __init__.py 修改
- [x] 實作 query_router.py 修改
- [x] 實作 data_transformer.py 修改
- [x] 實作 endpoint_registry.py 修改
- [x] 執行測試驗證
- [x] 更新文件狀態

---

## 🔮 未來擴展（可選）

1. **列出所有 PL** (`list_all_pls`)
   - 問法：「有哪些專案負責人」「PL 列表」
   
2. **統計 PL 專案數量** (`count_projects_by_pl`)
   - 問法：「Ryder 負責幾個專案」「統計各 PL 專案數」

3. **按 PL 和客戶組合查詢**
   - 問法：「Ryder 負責的 WD 專案有哪些」

---

## 📚 相關文件

- SAF Integration 架構：`/library/saf_integration/`
- 意圖分析器：`/library/saf_integration/smart_query/intent_analyzer.py`
- 查詢處理器：`/library/saf_integration/smart_query/query_handlers/`
- 文檔分類規範：`/docs/ai_instructions.md`

---

**文件版本**: v1.0  
**最後更新**: 2025-12-08
