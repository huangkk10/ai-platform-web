# Protocol Assistant — 搜尋流程與模式詳解

## 模式判斷——關鍵字偵測

**檔案**: `library/common/query_analysis/keyword_detector.py`  
**函數**: `contains_full_document_keywords(user_query) → (bool, keyword)`

觸發 Mode A 的關鍵字（部分）：
```python
FULL_DOCUMENT_KEYWORDS = [
    # 完整性
    '完整', '全部', '全文', '詳細', '詳盡',
    # 步驟
    '所有步驟', '完整步驟', '詳細步驟', '所有流程',
    # 教學/文件
    '教學', '指南', '手冊', 'SOP', '操作手冊', '使用手冊',
    # 英文
    'full', 'complete', 'detailed', 'tutorial', 'guide', 'manual',
    ...
]
```

**新增關鍵字**（永久）：直接修改 `FULL_DOCUMENT_KEYWORDS` 列表  
**動態新增**（重啟後消失）：呼叫 `add_custom_keyword(keyword)`

---

## Mode A — 關鍵字觸發全文搜尋

**檔案**: `library/protocol_guide/keyword_triggered_handler.py`  
**類別**: `ProtocolGuideKeywordTriggeredHandler`（別名 `KeywordTriggeredSearchHandler`）

```
用戶問題（含關鍵字）
  ↓
查詢加入 __FULL_SEARCH__ 標記
full_search_query = f"{user_query} __FULL_SEARCH__"
  ↓
inputs = {'search_mode': 'document_only', 'require_detailed_answer': 'true'}
  ↓
DifyChatClient.chat(question=full_search_query, inputs=inputs)
  ↓
Dify callback → Django /api/dify/knowledge/retrieval/
  偵測 __FULL_SEARCH__ → search_mode='document_only' → 全文搜尋
  ↓
Dify 生成回答
  ↓
is_uncertain_response(answer)?
  → True:  original_answer + "\n\n---\n\n💡 建議您參考以下文件..."  (is_fallback=True)
  → False: 正常回傳 answer (is_fallback=False)
```

**回傳 dict**:
```python
{
    'answer': str,
    'mode': 'mode_a',
    'is_fallback': bool,
    'fallback_reason': str | None,
    'message_id': str,
    'conversation_id': str,
    'response_time': float,
    'tokens': dict,
    'metadata': dict,  # 包含 retriever_resources（引用來源）
}
```

---

## Mode B — 兩階段搜尋

**檔案**: `library/protocol_guide/two_tier_handler.py`  
**類別**: `TwoTierSearchHandler`

```
用戶問題（不含關鍵字）
  ↓
─── Stage 1: 段落搜尋 ───
DifyChatClient.chat(query=user_query, is_full_search=False)
Dify callback → search_mode='auto'（段落搜尋）
  ↓
is_uncertain_response(stage_1_answer)?
  → False: ✅ 直接回傳（stage=1, is_fallback=False）
  → True: 進入 Stage 2
  ↓
─── Stage 2: 全文搜尋 ───
stage_2_query = f"{user_query} __FULL_SEARCH__"
DifyChatClient.chat(query=stage_2_query, is_full_search=True)
Dify callback → 偵測 __FULL_SEARCH__ → search_mode='document_only'
  ↓
is_uncertain_response(stage_2_answer)?
  → False: ✅ 回傳（stage=2, is_fallback=False）
  → True: 進入 Fallback
  ↓
─── Fallback ───
original_answer = stage_2_answer.strip()
combined_answer = f"{original_answer}\n\n---\n\n💡 建議您參考以下文件..."
回傳（stage=2, is_fallback=True）
```

---

## 不確定性偵測

**檔案**: `library/common/ai_response/uncertainty_detector.py`  
**函數**: `is_uncertain_response(ai_response, strict_mode=False) → (bool, keyword)`

**觸發不確定的條件**：
1. 回答含以下關鍵字（`UNCERTAINTY_KEYWORDS`）：
   ```python
   '不清楚', '不知道', '不了解', '不確定',
   '沒有相關資料', '沒有找到', '找不到',
   '抱歉', '很遺憾', '無法回答', '無法提供',
   'sorry', 'i don\'t know', 'not sure', 'cannot find',
   '也許', '大概', '似乎', '或許',
   ...
   ```
2. 回答長度 < 20 字元（`MIN_RESPONSE_LENGTH`，非 strict mode）
3. 回答為空字串 → 視為不確定（⚠️ Dify 呼叫失敗時也會觸發此情況）

**重要**: Dify 呼叫失敗（HTTP 4xx/timeout）時 `answer=''` → 也會進入 fallback。  
應在 handler 層檢查 `response.get('success', True)` 來區分「真不確定」和「API 失敗」。

---

## 外部知識庫 API（Django → Dify Callback）

**URL**: `POST /api/dify/knowledge/retrieval/`  
**檔案**: `backend/api/views/dify_knowledge_views.py` → `dify_knowledge_search()`

### 請求格式（Dify 傳來）
```json
{
    "query": "用戶問題 __FULL_SEARCH__",
    "knowledge_id": "protocol_guide_database",
    "retrieval_setting": {
        "top_k": 3,
        "score_threshold": 0.5
    }
}
```

### 處理邏輯
```python
# 1. 偵測 __FULL_SEARCH__ 標記
if '__FULL_SEARCH__' in query:
    search_mode = 'document_only'   # 全文搜尋
    stage = 2
    query = query.replace('__FULL_SEARCH__', '').strip()
else:
    search_mode = 'auto'            # 段落搜尋
    stage = 1

# 2. knowledge_id 映射
'protocol_guide_database' → assistant_type = 'protocol_assistant'

# 3. Score threshold 優先順序
# 優先級 1: Dify Studio 設定 (retrieval_setting.score_threshold > 0)
# 優先級 2: DB ThresholdManager
# 優先級 3: 系統預設值
```

### 回傳格式（給 Dify）
```json
{
    "records": [
        {
            "content": "文檔內容...",
            "score": 0.98,
            "title": "CrystalDiskMark 5",
            "metadata": {"source_table": "protocol_guide"}
        }
    ]
}
```

---

## SmartSearchConfig — 可調整的參數

**檔案**: `library/protocol_guide/smart_search_config.py`

```python
SmartSearchConfig(
    mode_a_top_k = 3,              # Mode A 返回幾筆文件
    mode_a_threshold = 0.5,        # Mode A 相似度閾值

    mode_b_stage_1_top_k = 5,      # Mode B Stage 1 返回幾筆段落
    mode_b_stage_1_threshold = 0.5,
    mode_b_stage_2_top_k = 3,      # Mode B Stage 2 返回幾筆文件
    mode_b_stage_2_threshold = 0.5,

    uncertainty_strict_mode = False, # True = 只偵測明確否定關鍵字
    min_response_length = 20,        # 回答少於此字數視為不確定

    dify_timeout = 75,               # Dify API 超時秒數
    dify_verbose = False,
)
```

---

## 對話記錄

**檔案**: `library/conversation_management/`  
**流程**: `SmartSearchRouter._record_conversation()` → 呼叫 `record_complete_exchange()`

記錄到 DB 的 metadata：
```python
{
    'dify_message_id': str,
    'mode': 'mode_a' | 'mode_b',
    'stage': 1 | 2,
    'is_fallback': bool,
    'fallback_reason': str,
    'dify_metadata': dict,        # Dify 回傳的完整 metadata（含引用來源）
    'workspace': 'Protocol_Guide',
    'app_name': 'Protocol Assistant'
}
```
