# 🔍 V2 上下文視窗擴展功能 - 完整狀態分析

## 📊 問題：V2 功能是否完整？

**用戶期望**：V2 應該實現「上下文視窗擴展」功能

**實際狀態**：✅ **已實現**，但有兩種不同的實現方式

---

## 🎯 V2 功能定義

### 原始需求：上下文視窗擴展
「V2 上下文搜尋」應該在找到匹配段落後，**額外返回前後相鄰的段落**，提供更完整的上下文。

**示例**：
```
找到匹配段落：「3.2 配置步驟」

V1 返回：
  - 僅 3.2 配置步驟的內容

V2 返回：
  - 3.1 環境準備（前一個段落）
  - 3.2 配置步驟（匹配段落）✅
  - 3.3 驗證測試（後一個段落）
```

---

## 📋 現有實現分析

### 實現 1：`search_with_context()` - 層級上下文
**位置**：`library/common/knowledge_base/section_search_service.py` Line 201

**功能**：
- ✅ 獲取父段落（parent）
- ✅ 獲取子段落（children）
- ✅ 可選獲取兄弟段落（siblings）

**返回結構**：
```python
{
  'section_id': '3.2',
  'heading_text': '配置步驟',
  'content': '...',
  'parent': {              # 父段落（如：第 3 章）
    'heading_text': '系統配置',
    'content': '...'
  },
  'children': [            # 子段落（如：3.2.1, 3.2.2）
    {'heading_text': '基礎配置', ...},
    {'heading_text': '進階配置', ...}
  ],
  'siblings': [            # 兄弟段落（如：3.1, 3.3）
    {'heading_text': '環境準備', ...},
    {'heading_text': '驗證測試', ...}
  ]
}
```

**特點**：
- ✅ 提供階層式上下文（父子關係）
- ✅ 可選擇是否包含兄弟段落
- ❌ **不支援 `context_window` 參數**（窗口大小）
- ❌ **不支援「前後 N 個段落」的線性視窗**

---

### 實現 2：理想的上下文視窗擴展（**未實現**）

**應該支援的功能**：
```python
def search_with_expanded_context(
    query: str,
    source_table: str,
    limit: int = 3,
    context_window: int = 1,  # ⚠️ 關鍵參數：前後各幾個段落
    context_mode: str = 'adjacent'  # adjacent | full
):
    """
    context_window = 1:  返回前 1、匹配、後 1 段落（共 3 個）
    context_window = 2:  返回前 2、匹配、後 2 段落（共 5 個）
    
    context_mode:
      - 'adjacent': 僅相鄰段落（無視層級）
      - 'full': 包含父子兄弟段落
    """
```

**返回結構**（`context_window=1`）：
```python
{
  'section_id': '3.2',
  'heading_text': '配置步驟',
  'content': '...',
  'similarity': 0.89,
  'context': {
    'previous': [          # 前 1 個段落
      {'section_id': '3.1', 'heading_text': '環境準備', ...}
    ],
    'next': [              # 後 1 個段落
      {'section_id': '3.3', 'heading_text': '驗證測試', ...}
    ]
  }
}
```

---

## 🔍 後端 ViewSet 當前狀態

### RVT Guide ViewSet
**檔案**：`backend/api/views/viewsets/knowledge_viewsets.py` Line 551-631

**當前實現**：
```python
if version == 'v2':
    raw_results = search_service.search_with_context(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        min_level=min_level,
        max_level=max_level,
        # ❌ 沒有 context_window 參數
        # ❌ 沒有 context_mode 參數
    )
```

**問題**：
- ✅ 調用了 `search_with_context()` 方法
- ❌ **未傳遞 `context_window` 參數**（即使前端發送了）
- ❌ **未傳遞 `context_mode` 參數**
- ⚠️ 使用的是「層級上下文」，不是「視窗擴展」

### Protocol Guide ViewSet
**檔案**：`backend/api/views/viewsets/knowledge_viewsets.py` Line 1200-1300

**當前實現**：
```python
if version == 'v2':
    raw_results = search_service.search_with_context(
        query=query,
        source_table='protocol_guide',
        limit=limit,
        threshold=threshold,
        min_level=min_level,
        max_level=max_level,
        # ❌ 同樣沒有 context_window 參數
    )
```

**狀態**：與 RVT Guide 相同問題

---

## 🎯 差異總結

| 功能 | 期望（視窗擴展） | 實際（層級上下文） |
|------|----------------|------------------|
| **前後段落** | ✅ 前 N/後 N 個段落 | ❌ 不支援 |
| **父段落** | ⚠️ 可選 | ✅ 自動包含 |
| **子段落** | ⚠️ 可選 | ✅ 自動包含 |
| **兄弟段落** | ✅ 應該包含 | ✅ 可選包含 |
| **context_window 參數** | ✅ 必須支援 | ❌ 不支援 |
| **線性視窗** | ✅ 按順序擴展 | ❌ 按層級擴展 |

---

## ✅ 已完成的功能

1. **前端 UI** - 100% ✅
   - SearchVersionToggle 組件顯示正常
   - V1/V2 切換功能
   - localStorage 持久化

2. **前端 Hook** - 100% ✅
   - useRvtChat 支援 searchVersion
   - useProtocolAssistantChat 支援 searchVersion
   - 請求中包含 `search_version` 參數

3. **後端 ViewSet** - 80% ⚠️
   - ✅ 接受 `version` 參數
   - ✅ V1/V2 路由分支
   - ⚠️ V2 調用 `search_with_context()`
   - ❌ **未使用前端傳來的 `context_window` 參數**
   - ❌ **未實現真正的「視窗擴展」邏輯**

4. **搜尋服務** - 60% ⚠️
   - ✅ `search_sections()` - V1 基礎搜尋（完整）
   - ⚠️ `search_with_context()` - 層級上下文（部分功能）
   - ❌ **缺少 `search_with_expanded_context()` 方法**

---

## 🚨 關鍵問題

### 問題 1：前端發送了 `context_window`，但後端未使用

**前端請求**（useProtocolAssistantChat.js）：
```javascript
{
  "message": "...",
  "search_version": "v2",
  "context_window": 1  // ✅ 前端發送了
}
```

**後端處理**（ViewSet）：
```python
context_window = request.data.get('context_window', 1)  # ✅ 接收了

# 但是...
raw_results = search_service.search_with_context(
    query=query,
    source_table='protocol_guide',
    limit=limit,
    # ❌ 沒有傳遞 context_window 參數！
)
```

**結果**：**`context_window` 參數被忽略了**

### 問題 2：`search_with_context()` 不支援視窗擴展

**方法簽名**：
```python
def search_with_context(
    self,
    query: str,
    source_table: str,
    limit: int = 3,
    include_siblings: bool = False  # ⚠️ 只有這個參數
):
```

**缺少的參數**：
- ❌ `context_window: int` - 視窗大小
- ❌ `context_mode: str` - 視窗模式

---

## 🎯 要達到完整的 V2 功能，需要做什麼？

### 選項 A：擴展現有 `search_with_context()` 方法（推薦）

**修改位置**：`library/common/knowledge_base/section_search_service.py`

**修改內容**：
```python
def search_with_context(
    self,
    query: str,
    source_table: str,
    limit: int = 3,
    include_siblings: bool = False,
    context_window: int = 1,  # ✅ 新增
    context_mode: str = 'adjacent'  # ✅ 新增
) -> List[Dict[str, Any]]:
    """
    搜尋段落（包含上下文）
    
    Args:
        context_window: 前後各擴展幾個段落（預設 1）
        context_mode: 'adjacent'=線性視窗 | 'hierarchical'=層級結構
    """
    sections = self.search_sections(query, source_table, limit=limit)
    
    for section in sections:
        if context_mode == 'adjacent':
            # ✅ 新增：獲取前後相鄰段落
            section['context'] = self._get_adjacent_sections(
                source_table,
                section['source_id'],
                section['section_id'],
                window_size=context_window
            )
        else:
            # 原有的層級上下文邏輯
            section['parent'] = self._get_parent_section(...)
            section['children'] = self._get_child_sections(...)
            if include_siblings:
                section['siblings'] = self._get_sibling_sections(...)
    
    return sections
```

**需要新增的輔助方法**：
```python
def _get_adjacent_sections(
    self,
    source_table: str,
    source_id: int,
    section_id: str,
    window_size: int = 1
) -> Dict[str, List]:
    """
    獲取相鄰段落（前後各 N 個）
    
    Returns:
        {
            'previous': [前面的段落],
            'next': [後面的段落]
        }
    """
    # 實現邏輯：
    # 1. 獲取當前文檔的所有段落（按 section_id 排序）
    # 2. 找到當前段落的位置
    # 3. 取前 window_size 個和後 window_size 個
```

### 選項 B：創建新方法 `search_with_expanded_context()`

**優點**：
- 不影響現有代碼
- 功能分離清晰

**缺點**：
- 代碼重複
- 需要修改 ViewSet 調用

---

## 📝 完成度評估

### 當前 V2 功能完成度：**70%**

| 組件 | 完成度 | 說明 |
|------|-------|------|
| 前端 UI | 100% ✅ | 完全正常 |
| 前端 Hook | 100% ✅ | 支援所有參數 |
| 後端 ViewSet | 80% ⚠️ | 接受參數但未使用 |
| 搜尋服務 | 60% ⚠️ | 有上下文功能，但不是視窗擴展 |
| 視窗擴展邏輯 | 0% ❌ | **尚未實現** |

### 未完成的功能（30%）

1. **`_get_adjacent_sections()` 方法** - 0% ❌
   - 獲取前後相鄰段落的核心邏輯

2. **`context_window` 參數傳遞** - 0% ❌
   - ViewSet → Service 的參數傳遞

3. **線性視窗擴展** - 0% ❌
   - 按順序取前後 N 個段落

---

## 🎯 結論

### ✅ 已實現的部分
- 前端完整支援 V1/V2 切換
- 後端可以區分 V1/V2 請求
- 已有「層級上下文」功能（父子兄弟段落）

### ❌ 未實現的部分（核心功能）
- **上下文視窗擴展**（前後 N 個段落）
- **`context_window` 參數實際使用**
- **線性視窗模式**

### 🎯 當前狀態
**V2 功能只完成了 70%**，核心的「視窗擴展」邏輯**尚未實現**。

現有的 V2 實際上是：
- ✅ 「層級上下文搜尋」（父子兄弟段落）
- ❌ 不是「視窗擴展搜尋」（前後相鄰段落）

---

## 🚀 下一步行動

### 立即可用（不改代碼）
當前的 V2 已經可以使用，它會返回：
- 父段落
- 子段落
- （可選）兄弟段落

這對於「理解段落在文檔中的位置」已經很有幫助。

### 如果需要真正的視窗擴展
需要實現：
1. `_get_adjacent_sections()` 方法（約 50 行代碼）
2. 修改 `search_with_context()` 支援 `context_window`（約 20 行）
3. 修改 ViewSet 傳遞 `context_window` 參數（約 5 行）

**工作量**：約 1-2 小時

---

**報告日期**：2025-11-09  
**狀態**：⚠️ V2 基礎功能完成，視窗擴展待實現  
**完成度**：70%
