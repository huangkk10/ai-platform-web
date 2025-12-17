# Phase 18: 多版本 FW 比較功能計畫

> **文件狀態**: 規劃中  
> **建立日期**: 2025-12-17  
> **作者**: AI Platform Team  
> **前置需求**: Phase 17 (Compare FW Test Jobs) 已完成

---

## 📋 目錄

1. [概述](#1-概述)
2. [現況分析](#2-現況分析)
3. [目標與範圍](#3-目標與範圍)
4. [技術架構設計](#4-技術架構設計)
5. [詳細實作計畫](#5-詳細實作計畫)
6. [資料結構定義](#6-資料結構定義)
7. [UI/UX 設計](#7-uiux-設計)
8. [測試計畫](#8-測試計畫)
9. [風險評估](#9-風險評估)
10. [時程規劃](#10-時程規劃)

---

## 1. 概述

### 1.1 背景

Phase 17 實現了 2 個 FW 版本的測試項目比較功能。用戶反饋希望能夠同時比較 3 個以上的 FW 版本，以便更全面地分析不同版本之間的測試差異。

### 1.2 目標

擴展現有的 `COMPARE_FW_TEST_JOBS` 意圖，支援 **2-10 個 FW 版本** 的同時比較，並保持向後相容性。

### 1.3 方案選擇

| 方案 | 說明 | 優缺點 |
|------|------|--------|
| **方案 A (採用)** | 擴展現有 Intent，使用 `fw_versions` 陣列 | ✅ 改動小、向後相容、維護成本低 |
| 方案 B | 新增獨立 Intent `COMPARE_MULTI_FW_TEST_JOBS` | ❌ 改動大、兩套邏輯、可能混淆用戶 |

**決策**: 採用方案 A - 擴展現有 Intent

---

## 2. 現況分析

### 2.1 現有架構 (Phase 17)

```
用戶輸入: "比較 springsteen GM10YCBM_Opal 和 PH10YC3H_Pyrite_512Byte"
                    ↓
           Intent Analyzer (LLM)
                    ↓
Intent: COMPARE_FW_TEST_JOBS
Parameters: {
    "project_name": "springsteen",
    "fw_version_1": "GM10YCBM_Opal",
    "fw_version_2": "PH10YC3H_Pyrite_512Byte"
}
                    ↓
           CompareTestJobsHandler
                    ↓
           Response Generator
                    ↓
輸出: 2 欄比較表格
```

### 2.2 現有參數結構

```python
# 現行結構（Phase 17）
{
    "intent": "compare_fw_test_jobs",
    "parameters": {
        "project_name": "springsteen",
        "fw_version_1": "GM10YCBM_Opal",
        "fw_version_2": "PH10YC3H_Pyrite_512Byte"
    },
    "confidence": 0.95
}
```

### 2.3 現有限制

1. **參數限制**: 只支援 `fw_version_1` 和 `fw_version_2` 兩個固定參數
2. **處理邏輯**: 當用戶輸入多於 2 個版本時，只取前 2 個（無提示）
3. **表格固定**: 輸出表格固定為 2 欄

### 2.4 相關檔案

| 檔案路徑 | 用途 |
|----------|------|
| `library/saf_integration/smart_query/intent_analyzer.py` | 意圖分析與 LLM Prompt |
| `library/saf_integration/smart_query/intent_types.py` | 意圖類型定義 |
| `library/saf_integration/smart_query/query_handlers/compare_test_jobs_handler.py` | 比較處理邏輯 |
| `library/saf_integration/smart_query/response_generator.py` | 回應訊息生成 |

---

## 3. 目標與範圍

### 3.1 功能目標

| 目標 | 說明 | 優先級 |
|------|------|--------|
| 多版本支援 | 支援 2-10 個 FW 版本同時比較 | P0 |
| 向後相容 | 現有 2 版本查詢仍可正常運作 | P0 |
| 動態表格 | 根據版本數量自動生成對應欄位 | P0 |
| 版本名稱處理 | 長版本名稱適當截斷或縮寫 | P1 |
| 錯誤提示 | 超過上限或版本不足時給予明確提示 | P1 |

### 3.2 範圍定義

#### ✅ 在範圍內 (In Scope)

- 修改 LLM Prompt 支援 `fw_versions` 陣列輸出
- 更新 Handler 處理多版本比較邏輯
- 更新 Response Generator 生成動態表格
- 更新 Fallback 邏輯提取多個 FW 版本
- 向後相容處理 `fw_version_1`/`fw_version_2` 格式

#### ❌ 不在範圍內 (Out of Scope)

- 新增獨立 Intent
- 前端特殊表格渲染（使用現有 Markdown 表格）
- 版本之間的趨勢分析圖表
- 匯出比較報告功能

### 3.3 成功標準

1. ✅ 用戶輸入 2 個版本 → 正常比較（向後相容）
2. ✅ 用戶輸入 3-10 個版本 → 全部版本同時比較
3. ✅ 用戶輸入 11+ 個版本 → 提示超過上限
4. ✅ 表格正確顯示所有版本的狀態

---

## 4. 技術架構設計

### 4.1 新參數結構

```python
# 新結構（Phase 18）
{
    "intent": "compare_fw_test_jobs",
    "parameters": {
        "project_name": "springsteen",
        "fw_versions": [
            "GM10YCBM_Opal",
            "PH10YC3H_Pyrite_512Byte",
            "GD10YBSD_Opal",
            "PH10YC3H_Pyrite_4K",
            "PH10YC3H_Opal_4K"
        ]
    },
    "confidence": 0.95
}
```

### 4.2 資料流程

```
用戶輸入: "比較 springsteen 5 版 FW: GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal..."
                    ↓
           Intent Analyzer (LLM)
                    ↓
           [新] 返回 fw_versions 陣列
                    ↓
           CompareTestJobsHandler
                    ↓
           [新] _normalize_fw_versions() - 統一格式
                    ↓
           [新] _compare_multi_test_jobs() - 多版本比較
                    ↓
           Response Generator
                    ↓
           [新] 動態生成 N 欄表格
                    ↓
輸出: 5 欄比較表格
```

### 4.3 向後相容策略

```python
def _normalize_fw_versions(self, parameters: Dict[str, Any]) -> List[str]:
    """
    統一轉換為 fw_versions 陣列格式
    
    支援三種輸入格式:
    1. fw_versions: ["FW1", "FW2", ...]     → 直接使用
    2. fw_version_1 + fw_version_2          → 轉換為陣列
    3. 混合格式                              → 合併處理
    """
    fw_versions = []
    
    # 格式 1: 新的陣列格式
    if 'fw_versions' in parameters:
        versions = parameters['fw_versions']
        if isinstance(versions, list):
            fw_versions.extend(versions)
        elif isinstance(versions, str):
            fw_versions.append(versions)
    
    # 格式 2: 舊的個別參數格式（向後相容）
    if 'fw_version_1' in parameters:
        fw_versions.append(parameters['fw_version_1'])
    if 'fw_version_2' in parameters:
        fw_versions.append(parameters['fw_version_2'])
    
    # 去重並保持順序
    seen = set()
    unique_versions = []
    for v in fw_versions:
        if v and v not in seen:
            seen.add(v)
            unique_versions.append(v)
    
    return unique_versions
```

---

## 5. 詳細實作計畫

### 5.1 Phase 18-1: 更新 Intent Analyzer

**檔案**: `library/saf_integration/smart_query/intent_analyzer.py`

#### 5.1.1 更新意圖說明

**位置**: LLM Prompt 的意圖列表區塊

```python
# 舊說明
- compare_fw_test_jobs: 比較兩個 FW 版本的測試項目結果（需要 project_name, fw_version_1, fw_version_2）

# 新說明
- compare_fw_test_jobs: 比較多個 FW 版本的測試項目結果（需要 project_name, fw_versions 陣列，支援 2-10 個版本）
```

#### 5.1.2 更新參數說明

**位置**: LLM Prompt 的參數說明區塊

```python
# 舊參數說明
- fw_version_1: 第一個要比較的 FW 版本
- fw_version_2: 第二個要比較的 FW 版本

# 新參數說明
- fw_versions: FW 版本陣列，包含 2-10 個要比較的版本（按用戶輸入順序）
```

#### 5.1.3 更新範例

**位置**: LLM Prompt 的範例區塊

```python
# 舊範例（保留，展示 2 版本情況）
輸入：比較 Springsteen PH10YC3H_Pyrite_4K 和 GD10YBJD_Opal 的測項結果
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "fw_versions": ["PH10YC3H_Pyrite_4K", "GD10YBJD_Opal"]}, "confidence": 0.95}

# 新範例（3 版本）
輸入：比較 springsteen 三版 FW GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal 的測試結果
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "springsteen", "fw_versions": ["GM10YCBM_Opal", "PH10YC3H_Pyrite_512Byte", "GD10YBSD_Opal"]}, "confidence": 0.95}

# 新範例（5 版本）
輸入：比較 springsteen 幾版 FW 的測試項目結果 GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal PH10YC3H_Pyrite_4K PH10YC3H_Opal_4K
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "springsteen", "fw_versions": ["GM10YCBM_Opal", "PH10YC3H_Pyrite_512Byte", "GD10YBSD_Opal", "PH10YC3H_Pyrite_4K", "PH10YC3H_Opal_4K"]}, "confidence": 0.95}

# 新範例（使用「和」連接）
輸入：Springsteen FW1_Opal 和 FW2_Pyrite 和 FW3_Opal 的測試比較
輸出：{"intent": "compare_fw_test_jobs", "parameters": {"project_name": "Springsteen", "fw_versions": ["FW1_Opal", "FW2_Pyrite", "FW3_Opal"]}, "confidence": 0.95}
```

#### 5.1.4 更新 Fallback 邏輯

**位置**: `_fallback_intent_detection()` 方法中的「測試項目結果比較」檢測

```python
def _fallback_compare_fw_test_jobs(self, query: str, detected_project: str) -> Optional[Dict[str, Any]]:
    """
    Fallback: 從查詢中提取多個 FW 版本
    
    支援格式:
    - 比較 project FW1 和 FW2 和 FW3
    - 比較 project FW1 FW2 FW3 FW4 FW5
    - project 的 FW1, FW2, FW3 測試比較
    """
    # FW 版本模式: 通常以 2 個大寫字母開頭 + 數字 + 可選後綴
    fw_pattern = r'\b([A-Z]{2}\d{2}[A-Z0-9]*(?:_[A-Za-z0-9_]+)?)\b'
    
    # 提取所有匹配的 FW 版本
    all_matches = re.findall(fw_pattern, query)
    
    # 過濾掉不太像 FW 版本的匹配（例如專案名稱）
    fw_versions = []
    for match in all_matches:
        # 排除已識別為專案名稱的
        if match.lower() == detected_project.lower():
            continue
        # 排除太短的匹配
        if len(match) < 6:
            continue
        fw_versions.append(match)
    
    # 去重並保持順序
    seen = set()
    unique_versions = []
    for v in fw_versions:
        if v not in seen:
            seen.add(v)
            unique_versions.append(v)
    
    if len(unique_versions) >= 2:
        return {
            'project_name': detected_project,
            'fw_versions': unique_versions
        }
    
    return None
```

---

### 5.2 Phase 18-2: 更新 Handler

**檔案**: `library/saf_integration/smart_query/query_handlers/compare_test_jobs_handler.py`

#### 5.2.1 新增常數定義

```python
class CompareTestJobsHandler(BaseQueryHandler):
    """比較多個 FW 版本的測試項目結果"""
    
    # 版本數量限制
    MIN_VERSIONS = 2
    MAX_VERSIONS = 10
```

#### 5.2.2 新增 `_normalize_fw_versions()` 方法

```python
def _normalize_fw_versions(self, parameters: Dict[str, Any]) -> List[str]:
    """
    統一轉換為 fw_versions 陣列格式（向後相容）
    
    Args:
        parameters: 原始參數字典
        
    Returns:
        List[str]: FW 版本陣列（已去重）
    """
    fw_versions = []
    
    # 格式 1: 新的陣列格式
    if 'fw_versions' in parameters:
        versions = parameters['fw_versions']
        if isinstance(versions, list):
            fw_versions.extend(versions)
        elif isinstance(versions, str):
            fw_versions.append(versions)
    
    # 格式 2: 舊的個別參數格式（向後相容）
    if 'fw_version_1' in parameters and parameters['fw_version_1'] not in fw_versions:
        fw_versions.insert(0, parameters['fw_version_1'])
    if 'fw_version_2' in parameters and parameters['fw_version_2'] not in fw_versions:
        if 'fw_version_1' in parameters:
            fw_versions.insert(1, parameters['fw_version_2'])
        else:
            fw_versions.append(parameters['fw_version_2'])
    
    # 去重並保持順序
    seen = set()
    unique_versions = []
    for v in fw_versions:
        if v and v not in seen:
            seen.add(v)
            unique_versions.append(v)
    
    return unique_versions
```

#### 5.2.3 修改 `handle()` 方法

```python
def handle(self, parameters: Dict[str, Any]) -> QueryResult:
    """處理多版本 FW 比較請求"""
    self._log_query(parameters)
    
    # Step 1: 統一轉換為 fw_versions 陣列
    fw_versions = self._normalize_fw_versions(parameters)
    
    # Step 2: 驗證版本數量
    if len(fw_versions) < self.MIN_VERSIONS:
        return QueryResult.error(
            f"至少需要 {self.MIN_VERSIONS} 個 FW 版本才能進行比較，"
            f"目前只有 {len(fw_versions)} 個",
            self.handler_name,
            parameters
        )
    
    if len(fw_versions) > self.MAX_VERSIONS:
        return QueryResult.error(
            f"最多支援比較 {self.MAX_VERSIONS} 個版本，"
            f"您提供了 {len(fw_versions)} 個。請減少版本數量或分批比較。",
            self.handler_name,
            parameters
        )
    
    # Step 3: 驗證必要參數
    project_name = parameters.get('project_name')
    if not project_name:
        return QueryResult.error(
            "缺少專案名稱 (project_name)",
            self.handler_name,
            parameters
        )
    
    test_category = parameters.get('test_category', '')
    
    try:
        # Step 4: 獲取所有版本的測試結果
        results = {}
        not_found_versions = []
        
        for fw_version in fw_versions:
            result, project = self._get_test_jobs_for_fw(project_name, fw_version)
            if result:
                results[fw_version] = {
                    'data': result,
                    'project': project
                }
            else:
                not_found_versions.append(fw_version)
        
        # Step 5: 檢查是否有足夠版本可比較
        if len(results) < self.MIN_VERSIONS:
            return QueryResult.error(
                f"找不到足夠的 FW 版本資料進行比較。\n"
                f"找到: {list(results.keys())}\n"
                f"未找到: {not_found_versions}",
                self.handler_name,
                parameters
            )
        
        # Step 6: 執行多版本比較
        comparison = self._compare_multi_test_jobs(
            results=results,
            fw_versions=list(results.keys()),  # 只使用有資料的版本
            test_category=test_category
        )
        
        # Step 7: 添加警告訊息（如果有版本未找到）
        if not_found_versions:
            comparison['warnings'] = [
                f"以下版本未找到資料，已從比較中排除: {', '.join(not_found_versions)}"
            ]
        
        return QueryResult.success(
            data=comparison,
            handler=self.handler_name,
            intent=IntentType.COMPARE_FW_TEST_JOBS,
            query=str(parameters)
        )
        
    except Exception as e:
        logger.exception(f"多版本比較時發生錯誤: {e}")
        return QueryResult.error(
            f"比較過程中發生錯誤: {str(e)}",
            self.handler_name,
            parameters
        )
```

#### 5.2.4 新增 `_compare_multi_test_jobs()` 方法

```python
def _compare_multi_test_jobs(
    self,
    results: Dict[str, Dict[str, Any]],
    fw_versions: List[str],
    test_category: str = ''
) -> Dict[str, Any]:
    """
    比較多個 FW 版本的測試結果
    
    Args:
        results: {fw_version: {'data': test_jobs_data, 'project': project_info}}
        fw_versions: 要比較的版本列表（按順序）
        test_category: 可選的測試類別過濾
        
    Returns:
        comparison: {
            'project_name': str,
            'fw_versions': List[str],
            'summary': {
                fw_version: {'total': int, 'pass': int, 'fail': int, 'pass_rate': float}
            },
            'differences': List[Dict],
            'all_items_by_category': Dict[str, List[Dict]],
            'has_differences': bool,
            'diff_count': int,
            'total_items': int
        }
    """
    # 取得專案名稱（從第一個版本）
    first_version = fw_versions[0]
    project_name = results[first_version]['project'].get('name', 'Unknown')
    
    # 建立測試項目對照表: {(test_item, capacity): {fw_version: status}}
    item_status_map = defaultdict(dict)
    item_category_map = {}  # {(test_item, capacity): category}
    
    for fw_version in fw_versions:
        test_jobs = results[fw_version]['data'].get('test_jobs', [])
        
        for job in test_jobs:
            test_item = job.get('test_item', '')
            capacity = job.get('capacity', '')
            category = job.get('test_category', 'Other')
            status = job.get('status', 'Unknown')
            
            # 可選: 按類別過濾
            if test_category and category.lower() != test_category.lower():
                continue
            
            key = (test_item, capacity)
            item_status_map[key][fw_version] = status
            item_category_map[key] = category
    
    # 分析差異
    differences = []
    all_items_by_category = defaultdict(list)
    
    for (test_item, capacity), statuses in item_status_map.items():
        category = item_category_map.get((test_item, capacity), 'Other')
        
        # 檢查是否有差異（任意兩個版本狀態不同）
        status_values = list(statuses.values())
        has_diff = len(set(status_values)) > 1
        
        item_data = {
            'test_item': test_item,
            'capacity': capacity,
            'category': category,
            'statuses': {fw: statuses.get(fw, 'N/A') for fw in fw_versions},
            'has_diff': has_diff
        }
        
        all_items_by_category[category].append(item_data)
        
        if has_diff:
            differences.append(item_data)
    
    # 計算各版本統計
    summary = {}
    for fw_version in fw_versions:
        test_jobs = results[fw_version]['data'].get('test_jobs', [])
        
        # 如果有類別過濾，只計算該類別
        if test_category:
            test_jobs = [j for j in test_jobs if j.get('test_category', '').lower() == test_category.lower()]
        
        total = len(test_jobs)
        pass_count = sum(1 for j in test_jobs if j.get('status') == 'Pass')
        fail_count = sum(1 for j in test_jobs if j.get('status') == 'Fail')
        pass_rate = (pass_count / total * 100) if total > 0 else 0
        
        summary[fw_version] = {
            'total': total,
            'pass': pass_count,
            'fail': fail_count,
            'pass_rate': round(pass_rate, 1)
        }
    
    # 排序類別內的項目
    for category in all_items_by_category:
        all_items_by_category[category].sort(key=lambda x: (x['test_item'], x['capacity']))
    
    return {
        'project_name': project_name,
        'fw_versions': fw_versions,
        'version_count': len(fw_versions),
        'summary': summary,
        'differences': differences,
        'all_items_by_category': dict(all_items_by_category),
        'has_differences': len(differences) > 0,
        'diff_count': len(differences),
        'total_items': len(item_status_map)
    }
```

---

### 5.3 Phase 18-3: 更新 Response Generator

**檔案**: `library/saf_integration/smart_query/response_generator.py`

#### 5.3.1 更新 `_generate_compare_test_jobs_response()` 方法

```python
def _generate_compare_test_jobs_response(self, result: QueryResult) -> str:
    """
    生成多版本 FW 比較的回應訊息
    
    支援 2-10 個版本的動態表格生成
    """
    data = result.data
    project_name = data.get('project_name', 'Unknown')
    fw_versions = data.get('fw_versions', [])
    version_count = len(fw_versions)
    summary = data.get('summary', {})
    differences = data.get('differences', [])
    all_items_by_category = data.get('all_items_by_category', {})
    has_differences = data.get('has_differences', False)
    warnings = data.get('warnings', [])
    
    lines = []
    
    # 標題
    lines.append(f"## 📊 {project_name} FW 版本測試項目比較")
    lines.append("")
    
    # 比較版本列表
    version_display = " ↔ ".join(fw_versions)
    lines.append(f"**比較版本** ({version_count} 個): {version_display}")
    lines.append("")
    
    # 警告訊息（如果有）
    if warnings:
        lines.append("### ⚠️ 注意")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")
    
    # === 整體統計表 ===
    lines.append("### 📈 整體統計")
    lines.append("")
    
    # 動態生成表頭
    header = "| 指標 |"
    separator = "|------|"
    for fw in fw_versions:
        short_name = self._shorten_fw_name(fw, max_len=18)
        header += f" {short_name} |"
        separator += "----------|"
    
    lines.append(header)
    lines.append(separator)
    
    # 統計資料列
    metrics = [
        ('總測試項目', 'total'),
        ('Pass', 'pass'),
        ('Fail', 'fail'),
        ('通過率', 'pass_rate')
    ]
    
    for label, key in metrics:
        row = f"| {label} |"
        for fw in fw_versions:
            value = summary.get(fw, {}).get(key, 'N/A')
            if key == 'pass_rate':
                value = f"{value}%"
            row += f" {value} |"
        lines.append(row)
    
    lines.append("")
    
    # === 差異區塊 ===
    if has_differences:
        diff_count = data.get('diff_count', len(differences))
        lines.append(f"### ❌ 有差異的測試項目 ({diff_count} 項)")
        lines.append("")
        lines.append(self._build_multi_version_table(differences, fw_versions))
    else:
        lines.append("### ✅ 無差異")
        lines.append("")
        lines.append("所有 FW 版本的測試項目結果完全相同。")
    
    lines.append("")
    
    # === 所有測試項目區塊 ===
    lines.append("### 📋 所有測試項目")
    lines.append("")
    
    for category, items in sorted(all_items_by_category.items()):
        pass_count = sum(1 for item in items if all(
            item['statuses'].get(fw) == 'Pass' for fw in fw_versions
        ))
        fail_count = sum(1 for item in items if any(
            item['statuses'].get(fw) == 'Fail' for fw in fw_versions
        ))
        
        lines.append(f"<details>")
        lines.append(f"<summary>📁 {category} ({len(items)} 項，✅ {pass_count} / ❌ {fail_count})</summary>")
        lines.append("")
        lines.append(self._build_multi_version_table(items, fw_versions))
        lines.append("")
        lines.append("</details>")
        lines.append("")
    
    return "\n".join(lines)


def _build_multi_version_table(self, items: List[Dict], fw_versions: List[str]) -> str:
    """
    建立多版本比較表格
    
    Args:
        items: 測試項目列表
        fw_versions: FW 版本列表
        
    Returns:
        Markdown 表格字串
    """
    if not items:
        return "_沒有資料_"
    
    lines = []
    
    # 表頭
    header = "| Test Item | Capacity |"
    separator = "|-----------|----------|"
    
    for fw in fw_versions:
        short_name = self._shorten_fw_name(fw, max_len=12)
        header += f" {short_name} |"
        separator += "--------|"
    
    lines.append(header)
    lines.append(separator)
    
    # 資料列
    for item in items:
        test_item = item.get('test_item', '')
        capacity = item.get('capacity', '')
        statuses = item.get('statuses', {})
        
        # 截斷過長的測試項目名稱
        display_name = test_item[:40] + "..." if len(test_item) > 40 else test_item
        
        row = f"| {display_name} | {capacity} |"
        
        for fw in fw_versions:
            status = statuses.get(fw, 'N/A')
            icon = self._get_status_icon(status)
            row += f" {icon} |"
        
        lines.append(row)
    
    return "\n".join(lines)


def _shorten_fw_name(self, fw_name: str, max_len: int = 15) -> str:
    """
    縮短 FW 版本名稱以適應表格
    
    策略:
    1. 如果小於 max_len，直接返回
    2. 嘗試保留前綴和後綴，中間用 ... 替代
    """
    if len(fw_name) <= max_len:
        return fw_name
    
    # 保留前 8 個字元和後 4 個字元
    prefix_len = max_len - 7  # 留出 ... 和後綴的空間
    suffix_len = 4
    
    return f"{fw_name[:prefix_len]}...{fw_name[-suffix_len:]}"


def _get_status_icon(self, status: str) -> str:
    """獲取狀態對應的 icon"""
    status_icons = {
        'Pass': '✅',
        'Fail': '❌',
        'Skip': '⏭️',
        'Error': '⚠️',
        'N/A': '➖',
        'Unknown': '❓'
    }
    return status_icons.get(status, '❓')
```

---

## 6. 資料結構定義

### 6.1 輸入參數結構

```typescript
// LLM 返回的意圖結構
interface IntentResult {
    intent: "compare_fw_test_jobs";
    parameters: {
        project_name: string;
        fw_versions: string[];      // 2-10 個版本
        test_category?: string;     // 可選: 過濾特定類別
    };
    confidence: number;             // 0.0 - 1.0
}
```

### 6.2 比較結果結構

```typescript
interface ComparisonResult {
    project_name: string;
    fw_versions: string[];
    version_count: number;
    
    summary: {
        [fw_version: string]: {
            total: number;
            pass: number;
            fail: number;
            pass_rate: number;
        }
    };
    
    differences: TestItemComparison[];
    all_items_by_category: {
        [category: string]: TestItemComparison[]
    };
    
    has_differences: boolean;
    diff_count: number;
    total_items: number;
    warnings?: string[];
}

interface TestItemComparison {
    test_item: string;
    capacity: string;
    category: string;
    statuses: {
        [fw_version: string]: "Pass" | "Fail" | "Skip" | "Error" | "N/A"
    };
    has_diff: boolean;
}
```

---

## 7. UI/UX 設計

### 7.1 表格顯示範例

#### 5 版本比較

```markdown
## 📊 springsteen FW 版本測試項目比較

**比較版本** (5 個): GM10YCBM_Opal ↔ PH10YC3H_Pyr...Byte ↔ GD10YBSD_Opal ↔ PH10YC3H_Pyr...4K ↔ PH10YC3H_Opal_4K

### 📈 整體統計

| 指標 | GM10YCBM_Opal | PH10YC3H_Pyr... | GD10YBSD_Opal | PH10YC3H_Pyr... | PH10YC3H_Op... |
|------|---------------|-----------------|---------------|-----------------|----------------|
| 總測試項目 | 805 | 805 | 805 | 805 | 805 |
| Pass | 443 | 443 | 445 | 440 | 442 |
| Fail | 68 | 68 | 66 | 70 | 69 |
| 通過率 | 55.0% | 55.0% | 55.3% | 54.7% | 54.9% |

### ❌ 有差異的測試項目 (12 項)

| Test Item | Capacity | GM10YC... | PH10YC... | GD10YB... | PH10YC... | PH10YC... |
|-----------|----------|-----------|-----------|-----------|-----------|-----------|
| NVMe_Validation_Tool_2_Standard... | 2048GB | ❌ | ❌ | ✅ | ❌ | ❌ |
| NVMe_Validation_Tool_2(SMBus_MI... | 4096GB | ⚠️ | ⚠️ | ⚠️ | ✅ | ⚠️ |
```

### 7.2 版本名稱縮寫規則

| 原始名稱 | 縮寫顯示 |
|----------|----------|
| `GM10YCBM_Opal` | `GM10YCBM_Opal` (不變) |
| `PH10YC3H_Pyrite_512Byte` | `PH10YC3H_...Byte` |
| `PH10YC3H_Pyrite_4K` | `PH10YC3H_P...4K` |

### 7.3 狀態圖示對照

| 狀態 | 圖示 | 說明 |
|------|------|------|
| Pass | ✅ | 測試通過 |
| Fail | ❌ | 測試失敗 |
| Skip | ⏭️ | 跳過 |
| Error | ⚠️ | 執行錯誤 |
| N/A | ➖ | 無資料 |
| Unknown | ❓ | 未知狀態 |

---

## 8. 測試計畫

### 8.1 單元測試

| 測試案例 | 輸入 | 預期結果 |
|----------|------|----------|
| 2 版本（向後相容） | `fw_version_1`, `fw_version_2` | 正常比較 |
| 2 版本（新格式） | `fw_versions: [FW1, FW2]` | 正常比較 |
| 3 版本 | `fw_versions: [FW1, FW2, FW3]` | 3 欄表格 |
| 5 版本 | `fw_versions: [FW1, ..., FW5]` | 5 欄表格 |
| 10 版本 | `fw_versions: [FW1, ..., FW10]` | 10 欄表格 |
| 11 版本（超限） | `fw_versions: [FW1, ..., FW11]` | 錯誤提示 |
| 1 版本（不足） | `fw_versions: [FW1]` | 錯誤提示 |
| 重複版本 | `fw_versions: [FW1, FW1, FW2]` | 去重後 2 版本 |
| 部分版本不存在 | 3 個版本，1 個不存在 | 警告 + 2 版本比較 |

### 8.2 整合測試

| 測試情境 | 查詢語句 | 預期結果 |
|----------|----------|----------|
| LLM 解析 2 版本 | "比較 springsteen FW1 和 FW2" | `fw_versions: [FW1, FW2]` |
| LLM 解析 5 版本 | "比較 springsteen FW1 FW2 FW3 FW4 FW5" | `fw_versions: [FW1, ..., FW5]` |
| Fallback 解析 | 同上，LLM 失敗時 | 正確提取所有版本 |
| 端對端測試 | 完整查詢 | 正確表格輸出 |

### 8.3 測試指令

```bash
# 單元測試
docker exec ai-django python -c "
from library.saf_integration.smart_query.query_handlers.compare_test_jobs_handler import CompareTestJobsHandler

handler = CompareTestJobsHandler()

# 測試版本正規化
params = {
    'project_name': 'test',
    'fw_versions': ['FW1', 'FW2', 'FW3']
}
versions = handler._normalize_fw_versions(params)
print(f'Test 1 - fw_versions array: {versions}')

# 測試向後相容
params2 = {
    'project_name': 'test',
    'fw_version_1': 'FW1',
    'fw_version_2': 'FW2'
}
versions2 = handler._normalize_fw_versions(params2)
print(f'Test 2 - backward compat: {versions2}')
"

# LLM 解析測試
docker exec ai-django python -c "
from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer

analyzer = SAFIntentAnalyzer()
result = analyzer.analyze('比較 springsteen GM10YCBM_Opal PH10YC3H_Pyrite_512Byte GD10YBSD_Opal 的測試結果')
print(f'Intent: {result.intent}')
print(f'Parameters: {result.parameters}')
"
```

---

## 9. 風險評估

### 9.1 技術風險

| 風險 | 影響 | 機率 | 緩解措施 |
|------|------|------|----------|
| LLM 無法正確解析多版本 | 中 | 低 | Fallback 機制 + 明確範例 |
| 表格過寬導致顯示問題 | 低 | 中 | 版本名稱縮寫 + 橫向滾動 |
| 大量版本造成效能問題 | 中 | 低 | 限制最多 10 版本 |
| 向後相容問題 | 高 | 低 | 保留舊參數格式支援 |

### 9.2 緩解策略

1. **LLM 解析問題**: 增加多版本範例，確保 Fallback 邏輯正確
2. **表格顯示問題**: 實作版本名稱縮寫，最多顯示 12-15 字元
3. **效能問題**: 限制版本數量上限為 10，API 呼叫使用平行處理
4. **相容性問題**: `_normalize_fw_versions()` 同時支援新舊格式

---

## 10. 時程規劃

### 10.1 開發階段

| 階段 | 任務 | 預估時間 | 依賴 |
|------|------|----------|------|
| Phase 18-1 | Intent Analyzer 更新 | 1 小時 | - |
| Phase 18-2 | Handler 更新 | 1.5 小時 | 18-1 |
| Phase 18-3 | Response Generator 更新 | 1 小時 | 18-2 |
| Phase 18-4 | 單元測試 | 30 分鐘 | 18-3 |
| Phase 18-5 | 整合測試 | 30 分鐘 | 18-4 |
| Phase 18-6 | 端對端測試 | 30 分鐘 | 18-5 |

### 10.2 總預估時間

| 項目 | 時間 |
|------|------|
| 開發 | 3.5 小時 |
| 測試 | 1.5 小時 |
| 緩衝 | 1 小時 |
| **總計** | **6 小時** |

---

## 附錄 A: 修改檔案清單

| 檔案 | 修改類型 | 說明 |
|------|----------|------|
| `intent_analyzer.py` | 修改 | 更新 Prompt + Fallback |
| `compare_test_jobs_handler.py` | 修改 | 新增多版本比較邏輯 |
| `response_generator.py` | 修改 | 動態表格生成 |

## 附錄 B: 相關文件

- Phase 17 實作: `docs/features/phase17-compare-fw-test-jobs.md` (如果存在)
- SAF Smart Query 架構: `docs/architecture/saf-smart-query-architecture.md` (如果存在)

---

**文件結束**

> 📝 **下一步**: 確認此計畫後開始實作 Phase 18-1
