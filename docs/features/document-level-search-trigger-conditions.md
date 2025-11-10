# 文檔級搜尋觸發條件說明

**功能**：Protocol Assistant 智能文檔級搜尋  
**版本**：v1.0  
**更新日期**：2025-11-10  

---

## 📋 概述

Protocol Assistant 現在具備**智能查詢分類**功能：
- 🎯 **文檔級查詢** → 返回**完整文檔**（1000-3000 字元，包含所有 sections）
- 📄 **Section 級查詢** → 返回**相關段落**（200-500 字元，單個 section）

系統會根據**用戶查詢中的關鍵字**自動判斷應該返回哪種結果。

---

## 🎯 觸發條件：關鍵字列表

### ✅ 會觸發「文檔級搜尋」的關鍵字

當用戶查詢包含以下**任一關鍵字**時，系統會返回**完整文檔**：

#### 1️⃣ **SOP 相關**（最常用）
```
sop
SOP
標準作業流程
作業流程
操作流程
```

**範例查詢**：
- ✅ "IOL 放測 **SOP**" → 返回 UNH-IOL 完整文檔（1246 字元）
- ✅ "UNH-IOL **標準作業流程**" → 返回完整文檔
- ✅ "如何進行 IOL **操作流程**" → 返回完整文檔

---

#### 2️⃣ **完整性關鍵字**
```
完整
全部
整個
所有步驟
全文
```

**範例查詢**：
- ✅ "給我 IOL 的**完整**說明" → 返回完整文檔
- ✅ "UNH-IOL **全部**內容" → 返回完整文檔
- ✅ "IOL **所有步驟**" → 返回完整文檔

---

#### 3️⃣ **文檔類型關鍵字**
```
教學
教程
指南
手冊
說明書
```

**範例查詢**：
- ✅ "IOL **教學**" → 返回完整文檔
- ✅ "UNH-IOL **使用手冊**" → 返回完整文檔
- ✅ "IOL **操作指南**" → 返回完整文檔

---

### ❌ 不會觸發「文檔級搜尋」的查詢

以下查詢**不包含觸發關鍵字**，會返回 **section 級結果**：

**範例查詢**：
- ❌ "IOL 網路設定" → 返回「網路設定」section（230 字元）
- ❌ "IOL 安裝需求" → 返回「安裝需求」section（490 字元）
- ❌ "如何初始化 Ubuntu" → 返回「初始化」section（548 字元）
- ❌ "IOL 執行檔路徑" → 返回「執行檔路徑」section
- ❌ "IOL 版本對應" → 返回「版本對應」section

---

## 🔍 判斷邏輯

### 程式碼位置
`/library/protocol_guide/search_service.py` → `_classify_query()` 方法

### 判斷流程
```python
def _classify_query(self, query: str) -> str:
    """
    分類查詢類型
    
    1. 將查詢轉為小寫
    2. 遍歷所有觸發關鍵字
    3. 如果查詢包含任一關鍵字 → 返回 'document'
    4. 否則 → 返回 'section'
    """
    query_lower = query.lower()
    
    for keyword in DOCUMENT_KEYWORDS:
        if keyword.lower() in query_lower:
            return 'document'  # ✅ 觸發文檔級搜尋
    
    return 'section'  # ❌ 普通 section 級搜尋
```

### 關鍵字匹配規則
- **大小寫不敏感**：`"SOP"` 和 `"sop"` 都會觸發
- **部分匹配**：只要查詢**包含**關鍵字即可
  - ✅ "IOL 的 **sop** 是什麼" → 觸發（包含 "sop"）
  - ✅ "請給我**完整**的教學" → 觸發（包含 "完整"）
  - ✅ "**操作流程**說明" → 觸發（包含 "操作流程"）

---

## 📊 查詢範例對比

| 用戶查詢 | 包含關鍵字 | 返回類型 | 內容長度 | 包含 Sections |
|---------|-----------|---------|---------|--------------|
| **"IOL 放測 SOP"** | ✅ sop | 完整文檔 | 1246 字元 | 10 個 |
| **"UNH-IOL 標準作業流程"** | ✅ 標準作業流程 | 完整文檔 | 1246 字元 | 10 個 |
| **"給我完整的 IOL 教學"** | ✅ 完整, 教學 | 完整文檔 | 1246 字元 | 10 個 |
| **"IOL 操作指南"** | ✅ 指南 | 完整文檔 | 1246 字元 | 10 個 |
| "IOL 網路設定" | ❌ 無 | Section | 230 字元 | 1 個 |
| "IOL 安裝需求" | ❌ 無 | Section | 490 字元 | 1 個 |
| "如何初始化" | ❌ 無 | Section | 548 字元 | 1 個 |

---

## 🎓 實際案例分析

### 案例 1：成功觸發文檔級搜尋
**用戶查詢**：`"iol sop 說明"`

**分析**：
1. 查詢包含關鍵字：`"sop"` ✅
2. 系統判斷：`document` 類型
3. 執行流程：
   - 先執行向量搜尋找到相關 sections
   - 從 sections 提取 `document_id`
   - 查詢該文檔的所有 sections
   - 按 `heading_level` 排序組裝
   - 返回完整 Markdown 文檔

**返回結果**：
```json
{
  "title": "UNH-IOL",
  "content": "# UNH-IOL\n\n## 1. IOL 執行檔＆文件...\n\n## 2. 原廠下載路徑...",
  "score": 0.896,
  "metadata": {
    "document_title": "UNH-IOL",
    "is_full_document": true,
    "sections_count": 10
  }
}
```

**Dify 顯示**：
- ✅ 顯示「已使用知識庫資料」
- ✅ 引用來源：「UNH-IOL」
- ✅ 完整的 SOP 內容（1246 字元）

---

### 案例 2：不觸發文檔級搜尋
**用戶查詢**：`"iol 網路設定"`

**分析**：
1. 查詢不包含任何觸發關鍵字 ❌
2. 系統判斷：`section` 類型
3. 執行流程：
   - 執行向量搜尋找到相關 sections
   - 直接返回 section 級結果（不組裝完整文檔）

**返回結果**：
```json
{
  "title": "",  // section 沒有標題
  "content": "## 網路設定\n\n1. 設定靜態 IP...",
  "score": 0.845,
  "metadata": {
    "source_table": "protocol_guide",
    "source_id": 10,
    "is_full_document": false
  }
}
```

**Dify 顯示**：
- ✅ 顯示「已使用知識庫資料」
- ✅ 返回相關段落（230 字元）
- ⚪ 不是完整文檔

---

## 🛠️ 自訂關鍵字

如果需要**添加或修改觸發關鍵字**：

### 修改位置
`/library/protocol_guide/search_service.py` → `DOCUMENT_KEYWORDS` 列表

### 修改方法
```python
# 🆕 文檔級查詢關鍵字（觸發完整文檔返回）
DOCUMENT_KEYWORDS = [
    # SOP 相關
    'sop', 'SOP', '標準作業流程', '作業流程', '操作流程',
    
    # 完整性關鍵字
    '完整', '全部', '整個', '所有步驟', '全文',
    
    # 文檔類型關鍵字
    '教學', '教程', '指南', '手冊', '說明書',
    
    # ✅ 新增自訂關鍵字
    '步驟',           # 新增：「所有步驟」變成「步驟」也可觸發
    'manual',         # 新增：英文 manual
    'tutorial',       # 新增：英文 tutorial
    '流程圖',         # 新增：流程圖
]
```

### 部署步驟
1. 修改 `/library/protocol_guide/search_service.py`
2. 同步到容器：
   ```bash
   docker cp library/protocol_guide/search_service.py ai-django:/app/library/protocol_guide/
   ```
3. 重啟 Django（可選，熱加載會自動生效）：
   ```bash
   docker compose restart ai-django
   ```

---

## 📈 效能指標

### 文檔級搜尋效能
- **響應時間**：~400ms
- **資料庫查詢**：2 次
  1. Section 向量搜尋
  2. 完整文檔組裝查詢
- **向量計算**：1 次（查詢向量化）

### Section 級搜尋效能
- **響應時間**：~300ms
- **資料庫查詢**：1 次
- **向量計算**：1 次

---

## 🎯 使用建議

### 何時應該使用文檔級查詢？
✅ **推薦使用場景**：
- 需要**完整的 SOP 流程**
- 需要**全面了解某個主題**
- 需要**所有相關步驟**
- 需要**打印或分享完整文檔**

### 何時應該使用 Section 級查詢？
✅ **推薦使用場景**：
- 只需要**特定的資訊**（如：安裝需求、網路設定）
- 需要**快速找到答案**
- 不需要完整上下文

---

## 🔄 未來改進方向

### 1. 智能學習（計劃中）
- 記錄用戶反饋（點讚/點踩）
- 分析哪些查詢應該返回完整文檔
- 自動調整關鍵字列表

### 2. 關鍵字擴充（持續更新）
- 根據實際使用情況添加新關鍵字
- 支援更多語言（英文、日文）
- 支援同義詞和變體

### 3. 上下文理解（未來）
- 使用 LLM 分析用戶意圖
- 不僅依賴關鍵字，也考慮語義
- 更智能的文檔 vs Section 判斷

---

## 📚 相關文檔

- **實施計劃**：`/docs/features/document-level-search-implementation-plan.md`
- **實施報告**：`/docs/features/document-level-search-implementation-report.md`
- **故障排除**：`/docs/debugging/dify-knowledge-not-showing-issue.md`
- **測試腳本**：`/backend/tests/test_document_level_search.py`

---

**作者**：AI Platform Team  
**最後更新**：2025-11-10  
**版本**：v1.0
