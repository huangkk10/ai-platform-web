# 📋 Known Issues 查詢意圖功能規劃

## 📅 建立日期：2025-12-15

---

## 1. 📊 新 API 規格分析

### 1.1 API 基本資訊

| 項目 | 說明 |
|------|------|
| **端點** | `POST /api/v1/projects/known-issues` |
| **伺服器** | `http://localhost:8080`（SAF API Server） |
| **認證方式** | Header-based（Authorization + Authorization-Name） |

### 1.2 認證 Headers

| Header | 說明 |
|--------|------|
| `Authorization` | 使用者 ID（從登入 API 取得） |
| `Authorization-Name` | 使用者名稱 |

### 1.3 Query 參數（皆為選填）

| 參數 | 類型 | 說明 | 預設值 |
|------|------|------|--------|
| `project_id` | string[] | 篩選專案 ID（可多選） | 空（全部） |
| `root_id` | string[] | 篩選 Root ID（可多選） | 空（全部） |
| `show_disable` | boolean | 是否顯示停用的 Issues | true |

### 1.4 回應資料結構

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "Issue ID",
        "project_id": "專案 ID",
        "project_name": "專案名稱",
        "root_id": "Root ID",
        "test_item_name": "測試項目名稱",
        "issue_id": "Issue 編號（如 Oakgate-1）",
        "case_name": "Case 名稱",
        "case_path": "Case 路徑",
        "created_by": "建立者",
        "created_at": "建立時間",
        "jira_id": "JIRA ID",
        "note": "備註",
        "is_enable": true,
        "jira_link": "JIRA 連結"
      }
    ],
    "total": 1
  },
  "timestamp": "2025-12-15T10:00:00Z"
}
```

### 1.5 回應欄位說明

| 欄位 | 說明 | 備註 |
|------|------|------|
| `id` | Issue 內部 ID | 唯一識別碼 |
| `project_id` | 專案 ID | 可用於篩選 |
| `project_name` | 專案名稱 | 人類可讀的名稱 |
| `root_id` | Root ID | 測試根節點 ID |
| `test_item_name` | 測試項目名稱 | 測試項目的完整名稱 |
| `issue_id` | Issue 編號 | 格式如 `Oakgate-1` |
| `case_name` | Case 名稱 | 測試案例名稱 |
| `case_path` | Case 路徑 | 測試案例的完整路徑 |
| `created_by` | 建立者 | 建立此 Issue 的人員 |
| `created_at` | 建立時間 | ISO 8601 格式 |
| `jira_id` | JIRA ID | 關聯的 JIRA 票號 |
| `note` | 備註 | Issue 的額外說明 |
| `is_enable` | 是否啟用 | true/false |
| `jira_link` | JIRA 連結 | 完整的 JIRA URL |

---

## 2. 🎯 功能需求分析

### 2.1 用戶需求場景

用戶希望能夠：
1. **指定專案**查詢該專案的所有 Known Issues
2. **指定 Test Item**查詢特定測試項目相關的 Issues
3. **組合查詢**：指定專案 + Test Item 進行精確查詢
4. 查看 Issue 詳細資訊（JIRA 連結、備註等）

### 2.2 預期的用戶問法

#### 📌 基礎查詢（按專案/Test Item）
```
1. 「APOLLO 專案有哪些 Known Issues？」
2. 「DEMETER 的 Known Issues 是什麼？」
3. 「查看 TITAN 專案的已知問題」
4. 「PHOENIX 專案的 PCIe 測試有什麼 Known Issue？」
5. 「APOLLO 的 OAKGATE 測試有哪些問題？」
6. 「列出 WD-001 專案的所有啟用中的 Issues」
```

#### 📊 統計分析
```
7. 「DEMETER 有幾個 Known Issues？」
8. 「APOLLO 專案有多少已知問題？」
9. 「哪個專案的 Known Issues 最多？」
10. 「列出 Known Issues 數量前 5 名的專案」
11. 「比較 APOLLO 和 DEMETER 的 Known Issues 數量」
```

#### 👤 按建立者查詢
```
12. 「John 建立了哪些 Known Issues？」
13. 「誰建立最多 Known Issues？」
14. 「列出所有 Known Issues 的建立者」
15. 「APOLLO 專案的 Issues 都是誰建的？」
```

#### 🔗 JIRA 相關
```
16. 「哪些 Known Issues 有 JIRA？」
17. 「APOLLO 專案有哪些 Issues 還沒開 JIRA？」
18. 「列出所有沒有 JIRA 連結的 Issues」
19. 「找出 JIRA-123 對應的 Known Issue」
```

#### 📅 時間相關
```
20. 「最近一週新增了哪些 Known Issues？」
21. 「這個月的 Known Issues 有哪些？」
22. 「APOLLO 專案 12 月的 Known Issues」
23. 「查看最近 10 個新增的 Issues」
```

#### 🔍 跨專案搜尋
```
24. 「所有專案的 PCIe 相關 Known Issues」
25. 「搜尋備註包含『timeout』的 Issues」
26. 「找出 case_path 包含 CV5 的 Issues」
27. 「哪些專案有 OAKGATE 的 Known Issues？」
```

---

## 3. 🏗️ 系統架構設計

### 3.0 完整意圖類型總覽

基於 API 回傳的資料欄位，可以設計以下 **12 種意圖類型**：

| # | 意圖類型 | 說明 | 必要參數 | 可選參數 | 優先級 |
|---|----------|------|----------|----------|--------|
| **基礎查詢** |
| 1 | `query_project_known_issues` | 查詢專案的所有 Known Issues | `project_name` | `show_disabled` | 🔴 高 |
| 2 | `query_project_test_item_known_issues` | 按專案 + Test Item 查詢 | `project_name`, `test_item` | - | 🔴 高 |
| **統計分析** |
| 3 | `count_project_known_issues` | 統計專案 Issues 數量 | `project_name` | - | 🟡 中 |
| 4 | `rank_projects_by_known_issues` | 按 Issues 數量排名專案 | - | `top_n`, `customer` | 🟡 中 |
| **按建立者** |
| 5 | `query_known_issues_by_creator` | 查詢特定人員建立的 Issues | `creator` | `project_name` | 🟢 低 |
| 6 | `list_known_issues_creators` | 列出所有 Issue 建立者 | - | `project_name` | 🟢 低 |
| **JIRA 相關** |
| 7 | `query_known_issues_with_jira` | 查詢有 JIRA 連結的 Issues | - | `project_name` | 🟡 中 |
| 8 | `query_known_issues_without_jira` | 查詢沒有 JIRA 的 Issues | - | `project_name` | 🟡 中 |
| **時間相關** |
| 9 | `query_recent_known_issues` | 查詢最近的 Issues | - | `days`, `limit`, `project_name` | 🟡 中 |
| 10 | `query_known_issues_by_date_range` | 按日期範圍查詢 | `start_date` | `end_date`, `project_name` | 🟢 低 |
| **跨專案搜尋** |
| 11 | `search_known_issues_by_keyword` | 按關鍵字搜尋（備註/Case） | `keyword` | `search_fields` | 🟡 中 |
| 12 | `query_all_known_issues_by_test_item` | 跨專案按 Test Item 搜尋 | `test_item` | `customer` | 🟡 中 |

### 3.1 新增意圖類型

在 `intent_types.py` 中新增：

```python
# 🆕 Phase 15: Known Issues 查詢（基礎查詢）
QUERY_PROJECT_KNOWN_ISSUES = "query_project_known_issues"  # 查詢專案的 Known Issues
QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES = "query_project_test_item_known_issues"  # 按 Test Item 查詢

# 🆕 Phase 15: Known Issues 統計分析
COUNT_PROJECT_KNOWN_ISSUES = "count_project_known_issues"  # 統計專案 Known Issues 數量
RANK_PROJECTS_BY_KNOWN_ISSUES = "rank_projects_by_known_issues"  # 按 Issues 數量排名專案

# 🆕 Phase 15: Known Issues 按建立者查詢
QUERY_KNOWN_ISSUES_BY_CREATOR = "query_known_issues_by_creator"  # 查詢特定人員建立的 Issues
LIST_KNOWN_ISSUES_CREATORS = "list_known_issues_creators"  # 列出所有 Issue 建立者

# 🆕 Phase 15: Known Issues JIRA 相關
QUERY_KNOWN_ISSUES_WITH_JIRA = "query_known_issues_with_jira"  # 查詢有 JIRA 連結的 Issues
QUERY_KNOWN_ISSUES_WITHOUT_JIRA = "query_known_issues_without_jira"  # 查詢沒有 JIRA 的 Issues

# 🆕 Phase 15: Known Issues 時間相關
QUERY_RECENT_KNOWN_ISSUES = "query_recent_known_issues"  # 查詢最近的 Known Issues
QUERY_KNOWN_ISSUES_BY_DATE_RANGE = "query_known_issues_by_date_range"  # 按日期範圍查詢

# 🆕 Phase 15: Known Issues 跨專案搜尋
SEARCH_KNOWN_ISSUES_BY_KEYWORD = "search_known_issues_by_keyword"  # 按關鍵字搜尋 Issues
QUERY_ALL_KNOWN_ISSUES_BY_TEST_ITEM = "query_all_known_issues_by_test_item"  # 跨專案按 Test Item 搜尋
```

### 3.2 新增 Handler

創建新文件 `known_issues_handler.py`：

```
library/saf_integration/smart_query/query_handlers/
└── known_issues_handler.py  (新增)
```

### 3.3 架構流程圖

```
用戶問題
    ↓
SAFIntentAnalyzer（意圖分析）
    ↓
IntentResult: {
    intent: "query_project_known_issues",
    parameters: {
        project_name: "APOLLO",
        test_item: "PCIe"  // 可選
    }
}
    ↓
QueryRouter（路由分發）
    ↓
KnownIssuesHandler.execute()
    ↓
SAF API Client（呼叫外部 API）
    POST /api/v1/projects/known-issues
    ↓
格式化回應
    ↓
返回結果給用戶
```

---

## 4. 📝 詳細實作規劃

### 4.1 第一步：更新 `intent_types.py`

**位置**：`library/saf_integration/smart_query/intent_types.py`

**新增內容**：

```python
class IntentType(Enum):
    # ... 現有意圖 ...
    
    # 🆕 Phase 15: Known Issues 查詢
    QUERY_PROJECT_KNOWN_ISSUES = "query_project_known_issues"
    QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES = "query_project_test_item_known_issues"


# 在 get_description() 方法中新增：
self.QUERY_PROJECT_KNOWN_ISSUES: "查詢專案的 Known Issues（已知問題）",
self.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: "查詢專案特定測試項目的 Known Issues",


# 在 get_required_parameters() 方法中新增：
self.QUERY_PROJECT_KNOWN_ISSUES: ['project_name'],
self.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: ['project_name', 'test_item'],
```

### 4.2 第二步：更新 `intent_analyzer.py` 的 Prompt

**位置**：`library/saf_integration/smart_query/intent_analyzer.py`

**在 `INTENT_ANALYSIS_PROMPT` 中新增意圖類型**：

```
## 可用的意圖類型

... 現有意圖 ...

=== Known Issues 相關意圖 ===

15. query_project_known_issues - 查詢專案的 Known Issues
    - 觸發詞：「XX 專案的 Known Issues」「XX 有哪些已知問題」「XX 的問題」
    - 參數：project_name (專案名稱)
    - 可選參數：show_disabled (是否顯示停用的 Issues)

16. query_project_test_item_known_issues - 查詢專案特定測試的 Known Issues
    - 觸發詞：「XX 專案的 YY 測試有什麼問題」「XX 的 YY Known Issue」
    - 參數：project_name (專案名稱), test_item (測試項目名稱)

17. count_project_known_issues - 統計專案 Known Issues 數量
    - 觸發詞：「XX 有幾個 Known Issues」「XX 有多少已知問題」
    - 參數：project_name (專案名稱)

18. rank_projects_by_known_issues - 按 Known Issues 數量排名專案
    - 觸發詞：「哪個專案 Known Issues 最多」「排名」「前幾名」
    - 可選參數：top_n (前幾名), customer (限定客戶)

19. query_known_issues_by_creator - 查詢特定人員建立的 Issues
    - 觸發詞：「XX 建立的 Issues」「XX 建了哪些問題」
    - 參數：creator (建立者名稱)
    - 可選參數：project_name (限定專案)

20. list_known_issues_creators - 列出 Issue 建立者
    - 觸發詞：「誰建立了 Issues」「列出建立者」「Issues 都是誰建的」
    - 可選參數：project_name (限定專案)

21. query_known_issues_with_jira - 查詢有 JIRA 的 Issues
    - 觸發詞：「有 JIRA 的 Issues」「已開 JIRA」「連結到 JIRA」
    - 可選參數：project_name (限定專案)

22. query_known_issues_without_jira - 查詢沒有 JIRA 的 Issues
    - 觸發詞：「沒有 JIRA」「未開 JIRA」「缺少 JIRA」
    - 可選參數：project_name (限定專案)

23. query_recent_known_issues - 查詢最近的 Known Issues
    - 觸發詞：「最近」「這週」「這個月」「新增的 Issues」
    - 可選參數：days (天數), limit (數量), project_name

24. query_known_issues_by_date_range - 按日期範圍查詢
    - 觸發詞：「X月到Y月」「從XX到YY」「12月的 Issues」
    - 參數：start_date (開始日期)
    - 可選參數：end_date (結束日期), project_name

25. search_known_issues_by_keyword - 按關鍵字搜尋 Issues
    - 觸發詞：「搜尋」「包含XX」「備註有XX」
    - 參數：keyword (關鍵字)
    - 可選參數：search_fields (搜尋欄位: note, case_name, case_path)

26. query_all_known_issues_by_test_item - 跨專案按 Test Item 搜尋
    - 觸發詞：「所有專案的 XX Issues」「哪些專案有 XX 問題」
    - 參數：test_item (測試項目)
    - 可選參數：customer (限定客戶)
```

**在範例區塊新增**：

```
=== Known Issues 範例 ===

# 基礎查詢
輸入：APOLLO 專案有哪些 Known Issues？
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "APOLLO"}, "confidence": 0.95}

輸入：DEMETER 的 PCIe 測試有什麼 Known Issue？
輸出：{"intent": "query_project_test_item_known_issues", "parameters": {"project_name": "DEMETER", "test_item": "PCIe"}, "confidence": 0.93}

輸入：查看 TITAN 專案的已知問題
輸出：{"intent": "query_project_known_issues", "parameters": {"project_name": "TITAN"}, "confidence": 0.94}

# 統計分析
輸入：APOLLO 有幾個 Known Issues？
輸出：{"intent": "count_project_known_issues", "parameters": {"project_name": "APOLLO"}, "confidence": 0.95}

輸入：哪個專案的 Known Issues 最多？
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {}, "confidence": 0.92}

輸入：列出 Known Issues 數量前 5 名的專案
輸出：{"intent": "rank_projects_by_known_issues", "parameters": {"top_n": 5}, "confidence": 0.93}

# 按建立者
輸入：John 建立了哪些 Known Issues？
輸出：{"intent": "query_known_issues_by_creator", "parameters": {"creator": "John"}, "confidence": 0.94}

輸入：APOLLO 專案的 Issues 都是誰建的？
輸出：{"intent": "list_known_issues_creators", "parameters": {"project_name": "APOLLO"}, "confidence": 0.91}

# JIRA 相關
輸入：APOLLO 專案有哪些 Issues 還沒開 JIRA？
輸出：{"intent": "query_known_issues_without_jira", "parameters": {"project_name": "APOLLO"}, "confidence": 0.93}

輸入：哪些 Known Issues 有 JIRA 連結？
輸出：{"intent": "query_known_issues_with_jira", "parameters": {}, "confidence": 0.92}

# 時間相關
輸入：最近一週新增了哪些 Known Issues？
輸出：{"intent": "query_recent_known_issues", "parameters": {"days": 7}, "confidence": 0.94}

輸入：APOLLO 專案 12 月的 Known Issues
輸出：{"intent": "query_known_issues_by_date_range", "parameters": {"project_name": "APOLLO", "start_date": "2025-12-01", "end_date": "2025-12-31"}, "confidence": 0.91}

# 跨專案搜尋
輸入：所有專案的 PCIe 相關 Known Issues
輸出：{"intent": "query_all_known_issues_by_test_item", "parameters": {"test_item": "PCIe"}, "confidence": 0.93}

輸入：搜尋備註包含 timeout 的 Issues
輸出：{"intent": "search_known_issues_by_keyword", "parameters": {"keyword": "timeout", "search_fields": ["note"]}, "confidence": 0.90}
```

### 4.3 第三步：創建 `known_issues_handler.py`

**位置**：`library/saf_integration/smart_query/query_handlers/known_issues_handler.py`

**設計大綱**：

```python
"""
KnownIssuesHandler - 專案 Known Issues 查詢
==========================================

處理「XX 專案有哪些 Known Issues？」這類查詢請求。

意圖類型：
- query_project_known_issues: 查詢專案的所有 Known Issues
- query_project_test_item_known_issues: 查詢專案特定測試項目的 Known Issues

用戶問法範例：
- 「APOLLO 專案有哪些 Known Issues？」
- 「DEMETER 的 PCIe 測試有什麼問題？」
- 「查看 TITAN 的已知問題」

作者：AI Platform Team
創建日期：2025-12-15
版本：1.0 (Phase 15)
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_handler import BaseHandler, QueryResult

logger = logging.getLogger(__name__)


class KnownIssuesHandler(BaseHandler):
    """
    Known Issues 查詢處理器
    
    支援的意圖：
    - query_project_known_issues: 按專案查詢 Known Issues
    - query_project_test_item_known_issues: 按專案 + Test Item 查詢
    """
    
    handler_name = "known_issues_handler"
    supported_intent = "query_project_known_issues"
    
    # Test Item 名稱對應表（標準化）
    TEST_ITEM_ALIASES = {
        'pcie': ['PCIe', 'pcie', 'PCI-E'],
        'nvme': ['NVMe', 'nvme'],
        'oakgate': ['OAKGATE', 'Oakgate', 'oakgate'],
        'performance': ['Performance', 'performance', 'perf'],
        'compatibility': ['Compatibility', 'compatibility', 'compat'],
        # ... 更多對應
    }
    
    def execute(self, parameters: Dict[str, Any]) -> QueryResult:
        """
        執行 Known Issues 查詢
        
        Args:
            parameters: {
                "project_name": "APOLLO",
                "test_item": "PCIe" (可選),
                "show_disabled": false (可選，預設只顯示啟用的)
            }
        """
        pass
    
    def _get_project_id(self, project_name: str) -> Optional[str]:
        """透過專案名稱獲取專案 ID"""
        pass
    
    def _call_known_issues_api(
        self, 
        project_ids: List[str] = None,
        root_ids: List[str] = None,
        show_disable: bool = False
    ) -> Dict[str, Any]:
        """呼叫 SAF Known Issues API"""
        pass
    
    def _filter_by_test_item(
        self, 
        issues: List[Dict], 
        test_item: str
    ) -> List[Dict]:
        """按 Test Item 過濾結果"""
        pass
    
    def _format_results(
        self, 
        issues: List[Dict],
        project_name: str,
        test_item: Optional[str] = None
    ) -> Dict[str, Any]:
        """格式化查詢結果為用戶友好的格式"""
        pass
```

### 4.4 第四步：更新 SAF API Client

**位置**：`library/saf_integration/api_client.py`

**新增方法**：

```python
def get_known_issues(
    self, 
    project_ids: List[str] = None,
    root_ids: List[str] = None,
    show_disable: bool = True
) -> Dict[str, Any]:
    """
    查詢 Known Issues
    
    Args:
        project_ids: 專案 ID 列表（可選）
        root_ids: Root ID 列表（可選）
        show_disable: 是否顯示停用的 Issues
        
    Returns:
        API 回應資料
    """
    url = f"{self.base_url}/api/v1/projects/known-issues"
    
    params = {}
    if project_ids:
        params['project_id'] = project_ids
    if root_ids:
        params['root_id'] = root_ids
    params['show_disable'] = str(show_disable).lower()
    
    response = requests.post(
        url,
        headers=self._get_auth_headers(),
        params=params
    )
    
    return response.json()
```

### 4.5 第五步：更新 `query_router.py`

**位置**：`library/saf_integration/smart_query/query_router.py`

**新增註冊**：

```python
from .query_handlers import (
    # ... 現有 imports ...
    KnownIssuesHandler,
)

# 在 _register_handlers() 方法中新增：
known_issues_handler = KnownIssuesHandler()

self._handlers.update({
    IntentType.QUERY_PROJECT_KNOWN_ISSUES: known_issues_handler,
    IntentType.QUERY_PROJECT_TEST_ITEM_KNOWN_ISSUES: known_issues_handler,
})
```

### 4.6 第六步：更新 `query_handlers/__init__.py`

**新增導出**：

```python
from .known_issues_handler import KnownIssuesHandler

__all__ = [
    # ... 現有導出 ...
    'KnownIssuesHandler',
]
```

---

## 5. 📤 輸出格式設計

### 5.1 成功查詢回應格式

```
📋 APOLLO 專案 Known Issues 查詢結果

📊 統計摘要：
• 總共找到 5 個 Known Issues
• 啟用中：4 個
• 已停用：1 個

🔍 詳細列表：

┌──────────────┬──────────────────┬──────────────┬──────────────┐
│ Issue 編號    │ 測試項目         │ Case 名稱     │ JIRA         │
├──────────────┼──────────────────┼──────────────┼──────────────┤
│ Oakgate-1    │ OAKGATE Test     │ Case_001     │ JIRA-123     │
│ Oakgate-2    │ OAKGATE Test     │ Case_002     │ JIRA-456     │
│ PCIe-1       │ PCIe CV5         │ Case_PCIe_01 │ JIRA-789     │
└──────────────┴──────────────────┴──────────────┴──────────────┘

💡 提示：
• 輸入「APOLLO 的 PCIe 問題」可查看特定測試的 Issues
• 輸入「APOLLO Known Issues 詳情」可查看完整備註
```

### 5.2 按 Test Item 篩選的回應格式

```
📋 APOLLO 專案 PCIe 相關 Known Issues

📊 統計：找到 2 個相關 Issues

🔍 詳細資訊：

【PCIe-1】
• 測試項目：PCIe CV5
• Case 名稱：Case_PCIe_01
• Case 路徑：/tests/pcie/cv5/case_01
• JIRA：JIRA-789 (🔗 連結)
• 備註：電壓測試異常，需要特殊配置
• 建立者：John Doe
• 建立時間：2025-12-10

【PCIe-2】
• 測試項目：PCIe CV5
• Case 名稱：Case_PCIe_02
• JIRA：JIRA-790 (🔗 連結)
• 備註：溫度敏感問題
```

### 5.3 無結果回應格式

```
📋 查詢結果

❌ 未找到 APOLLO 專案的 Known Issues

可能原因：
• 專案名稱可能有誤
• 該專案目前沒有記錄的 Known Issues

💡 建議：
• 確認專案名稱是否正確
• 嘗試查詢「有哪些專案？」來確認專案列表
```

---

## 6. ✅ 測試計劃

### 6.1 單元測試

創建測試文件：`tests/test_known_issues_handler.py`

```python
"""
Known Issues Handler 單元測試
"""

import pytest
from library.saf_integration.smart_query.query_handlers.known_issues_handler import KnownIssuesHandler


class TestKnownIssuesHandler:
    """測試 KnownIssuesHandler"""
    
    def test_execute_with_project_name(self):
        """測試按專案名稱查詢"""
        pass
    
    def test_execute_with_test_item(self):
        """測試按 Test Item 過濾"""
        pass
    
    def test_format_results(self):
        """測試結果格式化"""
        pass
    
    def test_no_results(self):
        """測試無結果情況"""
        pass
```

### 6.2 整合測試

```python
def test_intent_recognition():
    """測試意圖識別"""
    analyzer = SAFIntentAnalyzer()
    
    test_cases = [
        ("APOLLO 專案有哪些 Known Issues？", "query_project_known_issues"),
        ("DEMETER 的 PCIe 測試有什麼問題？", "query_project_test_item_known_issues"),
        ("查看 TITAN 的已知問題", "query_project_known_issues"),
    ]
    
    for query, expected_intent in test_cases:
        result = analyzer.analyze(query)
        assert result.intent == expected_intent
```

### 6.3 端到端測試

```bash
# 測試完整流程
docker exec ai-django python -c "
from library.saf_integration.smart_query import SmartQueryRouter

router = SmartQueryRouter()
result = router.query('APOLLO 專案有哪些 Known Issues？')
print(result)
"
```

---

## 7. 📁 需要修改的檔案清單

| 檔案路徑 | 修改類型 | 說明 |
|----------|----------|------|
| `library/saf_integration/smart_query/intent_types.py` | 修改 | 新增 12 個意圖類型 |
| `library/saf_integration/smart_query/intent_analyzer.py` | 修改 | 更新 Prompt 添加新意圖識別 |
| `library/saf_integration/smart_query/query_handlers/known_issues_handler.py` | **新增** | 創建主要 Handler（處理多種意圖） |
| `library/saf_integration/smart_query/query_handlers/__init__.py` | 修改 | 導出新 Handler |
| `library/saf_integration/smart_query/query_router.py` | 修改 | 註冊新 Handler（12 個意圖映射） |
| `library/saf_integration/api_client.py` | 修改 | 新增 `get_known_issues()` 方法 |
| `tests/test_known_issues_handler.py` | **新增** | 單元測試 |

---

## 8. 📅 實作時程估計（分階段）

### Phase 1：核心功能（優先級 🔴 高）
| 工作項目 | 預估時間 |
|----------|----------|
| 更新 intent_types.py（基礎 2 個意圖） | 15 分鐘 |
| 更新 intent_analyzer.py Prompt（基礎意圖） | 30 分鐘 |
| 創建 known_issues_handler.py（基礎查詢） | 2 小時 |
| 更新 api_client.py | 30 分鐘 |
| 更新 query_router.py 和 __init__.py | 15 分鐘 |
| 基礎測試 | 1 小時 |
| **Phase 1 小計** | **約 4.5 小時** |

### Phase 2：統計與 JIRA 功能（優先級 🟡 中）
| 工作項目 | 預估時間 |
|----------|----------|
| 新增 4 個意圖（統計 + JIRA） | 30 分鐘 |
| 擴展 Handler（統計和 JIRA 方法） | 2 小時 |
| 測試與除錯 | 1 小時 |
| **Phase 2 小計** | **約 3.5 小時** |

### Phase 3：進階功能（優先級 🟢 低）
| 工作項目 | 預估時間 |
|----------|----------|
| 新增 6 個意圖（時間/建立者/搜尋） | 45 分鐘 |
| 擴展 Handler（進階方法） | 3 小時 |
| 完整測試 | 1.5 小時 |
| **Phase 3 小計** | **約 5.5 小時** |

### 總計
| 階段 | 時間 | 累計 |
|------|------|------|
| Phase 1 | 4.5 小時 | 4.5 小時 |
| Phase 2 | 3.5 小時 | 8 小時 |
| Phase 3 | 5.5 小時 | 13.5 小時 |

---

## 9. 🔮 未來擴展考慮

### 9.1 已規劃的 12 種意圖功能摘要

| 類別 | 意圖數量 | 功能描述 |
|------|----------|----------|
| 基礎查詢 | 2 | 按專案、按 Test Item 查詢 |
| 統計分析 | 2 | 數量統計、排名比較 |
| 按建立者 | 2 | 查詢特定人員、列出建立者 |
| JIRA 相關 | 2 | 有/沒有 JIRA 的 Issues |
| 時間相關 | 2 | 最近、日期範圍 |
| 跨專案搜尋 | 2 | 關鍵字搜尋、按 Test Item |

### 9.2 可能的進一步擴展

1. **Issue 狀態追蹤**
   - 「APOLLO 有多少啟用中的 Issues？」
   - 「顯示已停用的 Issues」
   - 「比較啟用/停用 Issues 比例」

2. **趨勢分析**
   - 「APOLLO 每月新增多少 Known Issues？」
   - 「Known Issues 趨勢圖」
   - 「預測下個月 Issue 數量」

3. **關聯分析**
   - 「哪些 Test Item 產生最多 Issues？」
   - 「Root ID 和 Issue 數量的關係」
   - 「不同客戶的 Issue 分布」

4. **智能建議**
   - 「哪些 Issues 應該優先處理？」
   - 「建議開 JIRA 的 Issues」
   - 「相似 Issues 歸類」

### 9.2 API 增強建議

如果未來 SAF API 支援以下功能會更好：
- 按 `test_item_name` 直接篩選
- 按 `created_at` 日期範圍篩選
- 按 `created_by` 建立者篩選
- 支援分頁查詢

---

## 10. ⚠️ 注意事項

1. **認證處理**：需要確認 SAF API Client 中的認證 Headers 設定正確
2. **專案 ID 映射**：需要建立 project_name 到 project_id 的對應機制
3. **效能考量**：如果 Issues 數量很大，考慮實作分頁或限制返回數量
4. **錯誤處理**：需要處理 API 連線失敗、認證失敗等異常情況
5. **Test Item 模糊匹配**：用戶輸入的 test_item 可能需要標準化處理

---

## 11. 📚 參考資料

- [SAF Smart Query 設計文檔](/docs/architecture/llm-smart-api-router-design.md)
- [SAF Integration 架構說明](/docs/features/saf-assistant-project-test-query-planning.md)
- [現有 Handler 範例](/library/saf_integration/smart_query/query_handlers/test_category_search_handler.py)

---

**文檔作者**：AI Platform Team  
**最後更新**：2025-12-15  
**版本**：v1.0 (規劃階段)
