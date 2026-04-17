# RVT Assistant — 完整流程

## 聊天請求進入點

```
POST /api/rvt-guide/chat/
Body: { "message": "ucc 如何使用", "conversation_id": "" }
```

↓ Django `split_views.py` → `rvt_guide_chat` → `RVTGuideAPIHandler.handle_chat_api(request)`

---

## Mode A 流程（含全文關鍵字）

觸發條件：query 中含 `FULL_DOCUMENT_KEYWORDS`（如「完整」「SOP」「手冊」「指南」等）

```
1. contains_full_document_keywords(query) → True
2. SmartSearchRouter → route = 'mode_a'
3. KeywordTriggeredSearchHandler.handle_keyword_triggered_search()
   - 在 query 前加 "__FULL_SEARCH__" 前綴
   - 呼叫 DifyChatClient.chat(modified_query, ...)
4. Dify 呼叫外部知識庫 callback:
   POST /api/dify/knowledge/retrieval/
   {
     "knowledge_id": "rvt_guide_db_dev",
     "query": "__FULL_SEARCH__ ucc 使用手冊",
     "retrieval_setting": { "top_k": 10, "score_threshold": 0.5 }
   }
5. dify_knowledge_views.py 偵測到 __FULL_SEARCH__ 前綴
   → 使用 top_k=50 大量搜尋（取整份文件）
6. 回傳結果給 Dify LLM
7. LLM 生成完整回答
8. is_uncertain_response(answer) → False → 直接回傳
```

---

## Mode B 流程（標準兩階段搜尋）

觸發條件：query 中不含全文關鍵字（大多數問題走這條）

### Stage 1
```
1. SmartSearchRouter → route = 'mode_b'
2. TwoTierSearchHandler.handle_two_tier_search()
3. 直接發原始 query 給 Dify（search_mode='auto'）
4. Dify callback: POST /api/dify/knowledge/retrieval/
   knowledge_id='rvt_guide_db_dev', stage=1, top_k=3, threshold=0.8
5. DifyKnowledgeSearchHandler:
   - knowledge_id 標準化: rvt_guide_db_dev → rvt_guide
   - assistant_type 識別: rvt_assistant
   - ThresholdManager: stage1 threshold = 0.8
   - 段落搜尋 (SectionSearchService): 標題 70% / 內容 30%
   - 回傳 top 2-3 結果（score >= 0.8）
6. Dify 生成回答
7. is_uncertain_response(answer) 判斷：
   - False → 直接回傳 (stage=1, is_fallback=False)
   - True → 進入 Stage 2
```

### Stage 2（Stage 1 答案不確定時）
```
8. 使用更精確的搜尋參數重新查詢
9. 再次呼叫 Dify，這次提供更多文件上下文
10. 若仍不確定 → is_fallback=True，回傳降級訊息
    「建議您參考以下文件以獲更準確的資訊。」
```

---

## 外部知識庫 Callback 詳情

### 請求格式（Dify → Django）
```json
POST /api/dify/knowledge/retrieval/
Authorization: Bearer <DIFY_KEY>
{
  "knowledge_id": "rvt_guide_db_dev",
  "query": "ucc 如何使用",
  "retrieval_setting": {
    "top_k": 3,
    "score_threshold": 0.8
  }
}
```

### 回應格式（Django → Dify）
```json
{
  "records": [
    {
      "content": "UCC(UART Control Center)...",
      "score": 0.8726,
      "title": "UCC(UART Control Center) User Guide",
      "metadata": { "source": "rvt_guide", "id": 42 }
    },
    {
      "content": "UART Tool 說明...",
      "score": 0.8484,
      "title": "UART Tool 說明",
      "metadata": { "source": "rvt_guide", "id": 37 }
    }
  ]
}
```

---

## knowledge_id → assistant_type 對照

`backend/api/views/dify_knowledge_views.py` line ~420：
```python
KNOWLEDGE_ID_TO_ASSISTANT_TYPE = {
    'rvt_guide':         'rvt_assistant',
    'rvt_guide_db':      'rvt_assistant',
    'rvt_guide_db_dev':  'rvt_assistant',   # Dev 環境
    'rvt_assistant':     'rvt_assistant',
}
```

---

## 不確定性偵測（Fallback 判斷）

```python
# library/common/ai_response/uncertainty_detector.py

UNCERTAINTY_KEYWORDS = [
    "建議您參考",
    "請參閱",
    "I don't know",
    "無法回答",
    ...
]
MIN_RESPONSE_LENGTH = 20

def is_uncertain_response(answer) -> (bool, keyword_or_None):
    # 1. answer 長度 < 20 → True（too short）
    # 2. answer 含 UNCERTAINTY_KEYWORDS → True
    # 3. 否則 → False（正常回答）
```

---

## 圖片系統流程（RVT 獨有）

1. 文件 content 欄位含 `[IMG:14] board_count.png` 格式
2. `base_search_service.py` 的 `extract_image_ids()` 用 regex `\[IMG:(\d+)\]` 提取 ID
3. 搜尋結果 metadata 附帶 image_ids 列表
4. Dify 回答中保留 `[IMG:14]` 標記
5. 前端收到回答後，用 ID 請求 `/api/rvt-guides/{rvt_id}/images/{content_image_id}/` 取得圖片

---

## 對話記錄

每次成功回答後，`RVTGuideAPIHandler._save_conversation_to_db()` 儲存：
```python
ConversationSession(
    chat_type='rvt_assistant_chat',
    session_id=dify_conversation_id,   # Dify 的 conversation_id
    user=request.user,
)
ChatMessage(
    session=session,
    role='user' / 'assistant',
    content=message / answer,
    response_time=elapsed,
)
```

---

## 錯誤處理路徑

| 情況 | 行為 |
|------|------|
| Dify HTTP 400 (Reranking 錯誤) | `chat()` 返回 `{'success': False}` → `answer=''` → `is_uncertain=True` → fallback |
| Dify 超時 / 外部 KB URL 錯誤 | 30s timeout → 同上 fallback |
| library 組件初始化失敗 | 自動切換到 `RVTGuideFallbackHandler` |
| `search_rvt_guide_with_vectors()` 參數錯誤 | 自動回退到 `RVTGuideSearchService`（不影響功能） |
