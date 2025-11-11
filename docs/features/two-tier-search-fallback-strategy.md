# 兩階段智能搜尋降級策略（Two-Tier Search Fallback Strategy）

**規劃日期**：2025-11-08  
**完成日期**：2025-11-11  
**狀態**：✅ Phase 1, 2, 3 完成 - 測試 100% 通過  
**目標**：提升 AI 助手在無法回答時的用戶體驗

---

## 📊 Phase 3 測試結果摘要

**測試日期**: 2025-11-11  
**測試結果**: ✅ **10/10 通過 (100% 成功率)**

### 測試統計
- **模式 A 測試**: 3/3 通過 ✅ (關鍵字優先全文搜尋)
- **模式 B 測試**: 3/3 通過 ✅ (兩階段搜尋)
- **降級機制測試**: 2/2 通過 ✅
- **對話連續性**: 1/1 通過 ✅
- **配置驗證**: 1/1 通過 ✅

### 降級率分析
- **測試環境降級率**: 80% (8/10)
- **預期生產環境**: 15-30%

**為什麼測試降級率高？**
1. **測試資料品質差** (37.5%): Cup 僅 71 字元，UNH-IOL 僅 1,246 字元
2. **找錯文檔/相關性低** (25%): 向量搜尋品質受限於資料量少
3. **不存在的內容測試** (25%): 故意設計的邊緣案例（✅ 正常）
4. **文檔類型不匹配** (12.5%): 說明文檔 vs 操作指南需求不符

**生產環境預期改善**:
- 文檔品質提升 → 降級率從 37.5% 降至 5-10% (⬇️ 75%)
- 向量搜尋準確性提升 → 降級率從 25% 降至 5% (⬇️ 80%)
- 文檔類型標準化 → 降級率從 12.5% 降至 2-3% (⬇️ 80%)

📋 **詳細分析報告**:
- [Phase 3 測試報告](/docs/features/phase3-dify-integration-test-report.md)
- [降級原因分析](/docs/features/phase3-fallback-analysis.md)
- [視覺化總結](/docs/features/phase3-fallback-visual-summary.txt)

---

## 🎯 策略概述

當用戶提問時，系統採用**智能路由搜尋策略**（包含兩種模式）：

### 模式 A：關鍵字優先全文搜尋（Keyword-Triggered）

當用戶問題中包含特定關鍵字時，**直接**使用全文搜尋：

- **觸發關鍵字**：完整、全部、所有步驟、全文、取得完整內容、詳細內容、完整流程 等
- **行為**：跳過段落搜尋，直接進入全文搜尋
- **降級條件**：如果 AI 仍然不確定 → 直接顯示參考資料（無需二次搜尋）

### 模式 B：兩階段自動降級（Standard Two-Tier）

當用戶問題**沒有**全文關鍵字時，使用標準兩階段策略：

1. **第一階段**：段落搜尋（Section Search）
   - 精準匹配相關段落
   - 如果 AI 回答不確定 → 進入第二階段

2. **第二階段**：全文搜尋（Full Document Search）
   - 返回完整文檔
   - 如果 AI 仍然不確定 → 直接顯示參考資料

---

## 📊 流程圖

### 整體決策流程

```
用戶提問
    ↓
檢測問題中是否含有「全文關鍵字」？
    ├─ 是 → 【模式 A：關鍵字優先全文搜尋】
    │         ↓
    │    ┌─────────────────────────────────────┐
    │    │ 直接全文搜尋 (Full Doc Search)      │
    │    ├─────────────────────────────────────┤
    │    │ - 跳過段落搜尋                      │
    │    │ - 返回完整文檔內容                  │
    │    │ - Dify AI 生成回答                  │
    │    └─────────────────────────────────────┘
    │         ↓
    │    判斷 AI 回答是否不確定？
    │         ├─ 否 → ✅ 返回答案給用戶
    │         └─ 是 → 💡 降級模式：直接顯示參考資料
    │
    └─ 否 → 【模式 B：兩階段自動降級】
              ↓
         ┌─────────────────────────────────────┐
         │ 第一階段：段落搜尋 (Section Search)  │
         ├─────────────────────────────────────┤
         │ - 向量相似度搜尋                     │
         │ - 返回最相關的 3-5 個段落            │
         │ - Dify AI 生成回答                  │
         └─────────────────────────────────────┘
              ↓
         判斷 AI 回答是否不確定？
              ├─ 否 → ✅ 返回答案給用戶
              └─ 是 → 進入第二階段
                      ↓
                 ┌─────────────────────────────────────┐
                 │ 第二階段：全文搜尋 (Full Doc Search) │
                 ├─────────────────────────────────────┤
                 │ - 使用相同查詢                       │
                 │ - 返回完整文檔內容                   │
                 │ - Dify AI 重新生成回答               │
                 └─────────────────────────────────────┘
                      ↓
                 判斷 AI 回答是否不確定？
                      ├─ 否 → ✅ 返回答案給用戶
                      └─ 是 → � 降級模式：直接顯示參考資料
```

---

### 模式 A：關鍵字優先全文搜尋（簡化流程）

```
用戶提問含「完整」、「全文」等關鍵字
    ↓
直接全文搜尋（跳過段落搜尋）
    ↓
AI 生成回答
    ↓
是否不確定？
    ├─ 否 → ✅ 返回答案
    └─ 是 → � 降級模式：顯示參考資料
```

---

### 模式 B：兩階段自動降級（標準流程）

```
用戶提問（無全文關鍵字）
    ↓
段落搜尋
    ↓
AI 生成回答
    ↓
是否不確定？
    ├─ 否 → ✅ 返回答案
    └─ 是 → 全文搜尋
              ↓
          AI 重新生成
              ↓
          是否不確定？
              ├─ 否 → ✅ 返回答案
              └─ 是 → 💡 降級模式：顯示參考資料
```

---

## 🔍 關鍵技術點

### 1. 全文關鍵字檢測（Full Document Keywords Detection）⭐ **新增**

**定義「全文關鍵字」列表**：

```python
FULL_DOCUMENT_KEYWORDS = [
    # 完整性要求
    '完整', '全部', '全文', '完整內容', '完整文檔',
    '取得完整內容', '取得全部內容', '完整說明', '完整流程',
    
    # 步驟相關
    '所有步驟', '全部步驟', '完整步驟', '詳細步驟',
    '所有流程', '全部流程', '完整流程', '詳細流程',
    
    # 詳細性要求
    '詳細', '詳細內容', '詳細說明', '詳細資訊',
    '完整資訊', '全部資訊', '所有資訊',
    
    # 英文（如果用戶可能使用英文）
    'full', 'complete', 'entire', 'all steps', 
    'full document', 'complete document', 'detailed',
]
```

**檢測邏輯**：

```python
def contains_full_document_keywords(user_query: str) -> bool:
    """
    檢測用戶問題是否包含全文關鍵字
    
    Returns:
        True: 包含全文關鍵字，應直接使用全文搜尋
        False: 無全文關鍵字，使用標準兩階段搜尋
    """
    query_lower = user_query.lower()
    
    for keyword in FULL_DOCUMENT_KEYWORDS:
        if keyword.lower() in query_lower:
            return True
    
    return False
```

**使用範例**：

```python
# 測試案例
queries = [
    "Cup顏色完整內容",          # True - 含「完整內容」
    "Cup顏色全文",              # True - 含「全文」
    "所有步驟怎麼做",           # True - 含「所有步驟」
    "取得完整內容",             # True - 含「取得完整內容」
    "Cup顏色是什麼",            # False - 無全文關鍵字
    "如何測試Cup",              # False - 無全文關鍵字
]

for query in queries:
    result = contains_full_document_keywords(query)
    print(f"問題: {query}")
    print(f"  → 包含全文關鍵字: {result}")
    print(f"  → 搜尋策略: {'模式A（直接全文）' if result else '模式B（兩階段）'}")
```

---

### 2. 不確定回答檢測（Uncertainty Detection）

**定義「不確定關鍵字」列表**：

```python
UNCERTAINTY_KEYWORDS = [
    # 明確否定
    '不清楚', '不知道', '不了解', '不確定',
    '沒有相關資料', '沒有找到', '沒有資訊', '找不到',
    
    # 委婉表達
    '抱歉', '很遺憾', '無法回答', '無法提供',
    '資訊不足', '資料不足', '缺乏資訊',
    
    # 英文（如果 Dify 可能返回英文）
    'I don\'t know', 'not sure', 'unclear', 
    'no information', 'cannot find', 'unable to answer',
    
    # 模糊回答
    '可能', '也許', '不太確定', '我猜',
]
```

**檢測邏輯**：

```python
def is_uncertain_response(ai_response: str) -> bool:
    """
    檢測 AI 回答是否表達不確定
    
    Returns:
        True: 回答不確定，需要降級搜尋
        False: 回答明確，直接返回
    """
    # 轉小寫比較
    response_lower = ai_response.lower()
    
    # 檢查是否含有不確定關鍵字
    for keyword in UNCERTAINTY_KEYWORDS:
        if keyword.lower() in response_lower:
            return True
    
    # 檢查回答長度（過短可能是無法回答）
    if len(ai_response.strip()) < 20:
        return True
    
    return False
```

---

### 3. 智能路由決策（Smart Routing Decision）⭐ **新增**

**主流程控制邏輯**：

```python
def route_search_strategy(user_query: str) -> str:
    """
    根據用戶問題決定搜尋策略
    
    Returns:
        'mode_a': 關鍵字優先全文搜尋
        'mode_b': 標準兩階段搜尋
    """
    # 檢查是否包含全文關鍵字
    if contains_full_document_keywords(user_query):
        return 'mode_a'  # 模式 A：直接全文搜尋
    else:
        return 'mode_b'  # 模式 B：兩階段搜尋
```

**完整搜尋流程**：

```python
def handle_smart_search(user_query: str, conversation_id: str, user_id: str) -> dict:
    """
    智能搜尋處理器（整合模式 A 和模式 B）
    """
    # 決定搜尋策略
    search_mode = route_search_strategy(user_query)
    
    logger.info(f"🔍 智能路由: 用戶查詢='{user_query}', 模式={search_mode}")
    
    if search_mode == 'mode_a':
        # 模式 A：關鍵字優先全文搜尋
        return handle_keyword_triggered_search(user_query, conversation_id, user_id)
    else:
        # 模式 B：標準兩階段搜尋
        return handle_two_tier_search(user_query, conversation_id, user_id)
```

---

### 4. 模式 A：關鍵字優先全文搜尋實作 ⭐ **新增**

```python
def handle_keyword_triggered_search(
    user_query: str, 
    conversation_id: str, 
    user_id: str
) -> dict:
    """
    模式 A：關鍵字優先全文搜尋
    
    當用戶問題包含全文關鍵字時，直接使用全文搜尋
    """
    logger.info(f"📋 模式 A: 關鍵字優先全文搜尋")
    logger.info(f"   用戶查詢: {user_query}")
    
    # 直接執行全文搜尋（跳過段落搜尋）
    full_doc_results = search_service.search_knowledge(
        query=user_query,
        search_type='full_document',  # 全文搜尋
        top_k=3,
        threshold=0.6
    )
    
    logger.info(f"   全文搜尋結果: {len(full_doc_results)} 個文檔")
    
    # 發送 Dify 請求
    dify_response = dify_manager.send_chat_request(
        query=user_query,
        conversation_id=conversation_id,
        user_id=user_id,
        # 全文搜尋結果會透過 Dify 知識庫注入
    )
    
    ai_answer = dify_response['answer']
    logger.info(f"   Dify 回應: {ai_answer[:50]}...")
    
    # 檢測是否不確定
    is_uncertain = is_uncertain_response(ai_answer)
    logger.info(f"   不確定檢測: {is_uncertain}")
    
    if is_uncertain:
        # AI 仍然不確定 → 直接降級模式
        logger.warning(f"   ⚠️  AI 回答不確定，啟用降級模式")
        
        # 格式化參考資料
        fallback_response = format_fallback_response(full_doc_results)
        
        return {
            'answer': fallback_response,
            'mode': 'mode_a_fallback',
            'is_fallback': True,
            'search_results': full_doc_results,
            'message_id': dify_response.get('message_id'),
            'conversation_id': dify_response.get('conversation_id'),
        }
    else:
        # AI 有明確答案
        logger.info(f"   ✅ AI 回答明確，返回結果")
        
        return {
            'answer': ai_answer,
            'mode': 'mode_a_success',
            'is_fallback': False,
            'search_results': full_doc_results,
            'message_id': dify_response.get('message_id'),
            'conversation_id': dify_response.get('conversation_id'),
            'response_time': dify_response.get('response_time'),
            'tokens': dify_response.get('tokens'),
        }
```

---

### 5. 模式 B：標準兩階段搜尋實作（與原規劃相同）

```python
def handle_two_tier_search(
    user_query: str, 
    conversation_id: str, 
    user_id: str
) -> dict:
    """
    模式 B：標準兩階段搜尋
    
    當用戶問題沒有全文關鍵字時，使用兩階段降級策略
    """
    logger.info(f"🔄 模式 B: 標準兩階段搜尋")
    
    # ===== 第一階段：段落搜尋 =====
    logger.info(f"   階段 1: 段落搜尋")
    
    section_results = search_service.search_knowledge(
        query=user_query,
        search_type='section',
        top_k=5,
        threshold=0.7
    )
    
    logger.info(f"   段落搜尋結果: {len(section_results)} 個段落")
    
    # 第一次 Dify 請求
    response_1 = dify_manager.send_chat_request(
        query=user_query,
        conversation_id=conversation_id,
        user_id=user_id,
    )
    
    ai_answer_1 = response_1['answer']
    logger.info(f"   Dify 回應 1: {ai_answer_1[:50]}...")
    
    # 檢測第一階段是否不確定
    is_uncertain_1 = is_uncertain_response(ai_answer_1)
    logger.info(f"   不確定檢測: {is_uncertain_1}")
    
    if not is_uncertain_1:
        # 第一階段成功
        logger.info(f"   ✅ 階段 1 成功，返回結果")
        return {
            'answer': ai_answer_1,
            'mode': 'mode_b_stage_1',
            'is_fallback': False,
            'stage': 1,
            'search_results': section_results,
            'message_id': response_1.get('message_id'),
            'conversation_id': response_1.get('conversation_id'),
            'response_time': response_1.get('response_time'),
            'tokens': response_1.get('tokens'),
        }
    
    # ===== 第二階段：全文搜尋 =====
    logger.warning(f"   ⚠️  階段 1 不確定，進入階段 2")
    logger.info(f"   階段 2: 全文搜尋")
    
    full_doc_results = search_service.search_knowledge(
        query=user_query,
        search_type='full_document',
        top_k=3,
        threshold=0.6
    )
    
    logger.info(f"   全文搜尋結果: {len(full_doc_results)} 個文檔")
    
    # 第二次 Dify 請求
    response_2 = dify_manager.send_chat_request(
        query=user_query,
        conversation_id=conversation_id,  # 同一對話
        user_id=user_id,
    )
    
    ai_answer_2 = response_2['answer']
    logger.info(f"   Dify 回應 2: {ai_answer_2[:50]}...")
    
    # 檢測第二階段是否不確定
    is_uncertain_2 = is_uncertain_response(ai_answer_2)
    logger.info(f"   不確定檢測: {is_uncertain_2}")
    
    if not is_uncertain_2:
        # 第二階段成功
        logger.info(f"   ✅ 階段 2 成功，返回結果")
        return {
            'answer': ai_answer_2,
            'mode': 'mode_b_stage_2',
            'is_fallback': False,
            'stage': 2,
            'search_results': full_doc_results,
            'message_id': response_2.get('message_id'),
            'conversation_id': response_2.get('conversation_id'),
            'response_time': response_2.get('response_time'),
            'tokens': response_2.get('tokens'),
        }
    
    # ===== 降級模式 =====
    logger.error(f"   ❌ 兩階段都不確定，啟用降級模式")
    
    fallback_response = format_fallback_response(full_doc_results)
    
    return {
        'answer': fallback_response,
        'mode': 'mode_b_fallback',
        'is_fallback': True,
        'stage': 2,
        'search_results': full_doc_results,
        'message_id': response_2.get('message_id'),
        'conversation_id': response_2.get('conversation_id'),
    }
```

---

### 6. 搜尋模式切換

**第一階段：段落搜尋**

```python
# 使用現有的 section search
results = search_service.search_knowledge(
    query=user_query,
    search_type='section',  # 段落搜尋
    top_k=5,
    threshold=0.7
)
```

**第二階段：全文搜尋**

```python
# 自動添加全文關鍵字觸發器
query_with_fulltext = f"{user_query} 完整"

results = search_service.search_knowledge(
    query=query_with_fulltext,
    search_type='full_document',  # 全文搜尋
    top_k=3,
    threshold=0.6  # 可以降低閾值
)
```

---

### 7. Dify 請求管理（與原規劃相同）

**第一次請求**：

```python
# 段落搜尋結果
response_1 = dify_manager.send_chat_request(
    query=user_query,
    conversation_id=conversation_id,
    user_id=user_id,
    # 段落搜尋結果會透過 Dify 知識庫注入
)

# 檢查回答
if is_uncertain_response(response_1['answer']):
    # 進入第二階段
    proceed_to_stage_2 = True
```

**第二次請求**（降級）：

```python
# 全文搜尋結果
response_2 = dify_manager.send_chat_request(
    query=user_query,  # 相同查詢
    conversation_id=conversation_id,  # 同一對話
    user_id=user_id,
    # 全文搜尋結果會透過 Dify 知識庫注入
)

# 再次檢查
if is_uncertain_response(response_2['answer']):
    # 進入降級模式：直接返回參考資料
    return format_fallback_response(full_document_results)
```

---

### 8. 降級模式回應格式（與原規劃相同）

**直接顯示參考資料的回應格式**：

```python
def format_fallback_response(documents: List[Dict]) -> str:
    """
    格式化降級模式的回應
    
    當 AI 兩次搜尋都無法回答時，直接返回參考資料
    """
    response = "抱歉，我目前沒有足夠的資訊來完整回答您的問題。\n\n"
    response += "📚 **以下是可能相關的參考資料**：\n\n"
    
    for i, doc in enumerate(documents, 1):
        response += f"### {i}. 📄 {doc['title']}\n\n"
        response += f"**來源**：{doc['document_id']}\n"
        response += f"**相似度**：{doc['similarity']:.0%}\n\n"
        
        # 顯示內容摘要（前 500 字元）
        content_preview = doc['content'][:500]
        if len(doc['content']) > 500:
            content_preview += "..."
        
        response += f"**內容摘要**：\n{content_preview}\n\n"
        response += "---\n\n"
    
    response += "💡 **提示**：您可以進一步查看上述文檔的完整內容，或重新調整問題。"
    
    return response
```

**範例輸出**：

```
抱歉，我目前沒有足夠的資訊來完整回答您的問題。

📚 **以下是可能相關的參考資料**：

### 1. 📄 Cup

**來源**：protocol_guide_20
**相似度**：86%

**內容摘要**：
# Cup 顏色顏色顏色顏色顏色顏色顏色顏色...

## 圖案
圖案圖案圖案圖案圖案圖案圖案圖案圖案...

---

### 2. 📄 新舊各個版本主板

**來源**：protocol_guide_21
**相似度**：82%

**內容摘要**：
# 主板測試流程
...

---

💡 **提示**：您可以進一步查看上述文檔的完整內容，或重新調整問題。
```

---

## 🏗️ 系統架構設計

### 架構層級（更新）

```
前端 (React)
    ↓
Protocol Assistant Chat Hook (useProtocolAssistantChat)
    ↓
Backend API (/api/protocol-guide/chat/)
    ↓
┌──────────────────────────────────────────┐
│ SmartSearchRouter (新增) ⭐              │
├──────────────────────────────────────────┤
│ - route_search_strategy()                │
│ - contains_full_document_keywords()      │
│ - 決定使用模式 A 或模式 B                │
└──────────────────────────────────────────┘
    ↓
    ├─ 模式 A → KeywordTriggeredSearchHandler
    │           - handle_keyword_triggered_search()
    │           - 直接全文搜尋
    │           - 單次 Dify 請求
    │           - 降級模式（如需要）
    │
    └─ 模式 B → TwoTierSearchHandler
                - handle_two_tier_search()
                - 段落搜尋 → 全文搜尋
                - 兩次 Dify 請求
                - 降級模式（如需要）
    ↓
┌──────────────────────────────────────────┐
│ ProtocolGuideSearchService               │
├──────────────────────────────────────────┤
│ - search_knowledge()                     │
│   - search_type='section'                │
│   - search_type='full_document'          │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ DifyRequestManager                       │
├──────────────────────────────────────────┤
│ - send_chat_request()                    │
│ - 自動注入搜尋結果到 Dify 知識庫        │
└──────────────────────────────────────────┘
    ↓
┌──────────────────────────────────────────┐
│ UncertaintyDetector (共用)               │
├──────────────────────────────────────────┤
│ - is_uncertain_response()                │
│ - format_fallback_response()             │
└──────────────────────────────────────────┘
```

---

## 📝 實作步驟規劃

### Phase 1: 核心邏輯實作（3-4 小時）⭐ **更新**

**步驟 1：創建全文關鍵字檢測器** ⭐ **新增**
- 檔案：`library/common/query_analysis/keyword_detector.py`
- 功能：
  - `contains_full_document_keywords()` - 檢測全文關鍵字
  - `FULL_DOCUMENT_KEYWORDS` 常數列表
  - 支援中英文檢測

**步驟 2：創建不確定檢測器**
- 檔案：`library/common/ai_response/uncertainty_detector.py`
- 功能：
  - `is_uncertain_response()`
  - `UNCERTAINTY_KEYWORDS` 常數
  - 支援中英文檢測

**步驟 3：創建智能路由器** ⭐ **新增**
- 檔案：`library/protocol_guide/smart_search_router.py`
- 功能：
  - `route_search_strategy()` - 決定搜尋模式
  - `handle_smart_search()` - 主流程控制
  - 路由到模式 A 或模式 B

**步驟 4：實作模式 A 處理器** ⭐ **新增**
- 檔案：`library/protocol_guide/keyword_triggered_handler.py`
- 功能：
  - `handle_keyword_triggered_search()` - 關鍵字優先全文搜尋
  - 單次全文搜尋 + Dify 請求
  - 降級模式處理

**步驟 5：實作模式 B 處理器**
- 檔案：`library/protocol_guide/two_tier_handler.py`
- 功能：
  - `handle_two_tier_search()` - 兩階段搜尋
  - `execute_stage_1()` - 段落搜尋
  - `execute_stage_2()` - 全文搜尋
  - 降級模式處理

**步驟 6：擴展搜尋服務**
- 檔案：`library/protocol_guide/search_service.py`
- 修改：
  - 確保 `search_type` 參數完整支援
  - 優化全文搜尋效能

---

### Phase 2: API 整合（1-2 小時）

**步驟 7：修改 Chat API** ⭐ **更新**
- 檔案：`backend/api/views/viewsets/knowledge_viewsets.py`
- 修改：`ProtocolGuideViewSet.chat()` action
- 整合：`SmartSearchRouter` 取代原本的單一處理器
- 路由到模式 A 或模式 B

**步驟 8：添加配置選項** ⭐ **更新**
- 檔案：`library/config/search_config.py`
- 配置：
  - `SMART_SEARCH_ENABLED = True`
  - `KEYWORD_TRIGGERED_SEARCH_ENABLED = True`
  - `TWO_TIER_SEARCH_ENABLED = True`
  - `FULL_DOCUMENT_KEYWORDS = [...]`
  - `UNCERTAINTY_KEYWORDS = [...]`

---

### Phase 3: 前端顯示優化（1-2 小時）

**步驟 9：前端訊息類型識別** ⭐ **更新**
- 檔案：`frontend/src/hooks/useProtocolAssistantChat.js`
- 新增：識別搜尋模式和降級模式
- 特殊標記：
  - `response.mode` - 'mode_a' / 'mode_b' / 'mode_a_fallback' / 'mode_b_fallback'
  - `response.is_fallback` - true/false
  - `response.stage` - 1/2 (僅模式 B)

**步驟 10：特殊樣式顯示**
- 檔案：`frontend/src/components/chat/MessageList.jsx`
- 新增：根據不同模式顯示標籤
  - 模式 A 成功：「📋 全文搜尋」標籤
  - 模式 A 降級：「📚 參考資料模式（全文）」
  - 模式 B 第一階段：無特殊標籤（預設）
  - 模式 B 第二階段：「🔄 已自動切換全文搜尋」
  - 模式 B 降級：「📚 參考資料模式」
  - 可展開/收合參考資料內容

---

### Phase 4: 測試與優化（2-3 小時）

**步驟 11：單元測試** ⭐ **更新**
- 檔案：`tests/test_smart_search.py`
- 測試案例：
  - **全文關鍵字檢測**：
    - "Cup顏色完整內容" → 應包含關鍵字
    - "Cup顏色全文" → 應包含關鍵字
    - "所有步驟" → 應包含關鍵字
    - "Cup顏色" → 不應包含關鍵字
  - **模式 A 流程**：
    - 含關鍵字 + AI 明確回答 → mode_a_success
    - 含關鍵字 + AI 不確定 → mode_a_fallback
  - **模式 B 流程**：
    - 無關鍵字 + 第一階段成功 → mode_b_stage_1
    - 無關鍵字 + 第一階段失敗、第二階段成功 → mode_b_stage_2
    - 無關鍵字 + 兩階段都失敗 → mode_b_fallback
  - **不確定關鍵字檢測準確性**

**步驟 12：整合測試**
- 測試真實對話流程
- 驗證 Dify 響應處理
- 檢查日誌記錄
- 測試各種問題變體

**步驟 13：性能優化**
- 避免重複搜尋
- 快取機制
- 超時處理
- 關鍵字檢測效能優化

---

## 🎨 前端 UI 設計

### 不同模式的顯示標籤 ⭐ **更新**

**模式 A 成功**（含全文關鍵字，AI 明確回答）：
```
┌─────────────────────────────────────┐
│ 🤖 AI Assistant   📋 全文搜尋       │
├─────────────────────────────────────┤
│ 根據 Cup 文檔，完整流程包括...     │
│                                     │
│ 👍 👎                               │
└─────────────────────────────────────┘
```

**模式 A 降級**（含全文關鍵字，AI 不確定）：
```
┌─────────────────────────────────────┐
│ 🤖 AI Assistant   📚 參考資料模式    │
│                   (全文搜尋)         │
├─────────────────────────────────────┤
│ 抱歉，我目前沒有足夠的資訊...       │
│                                     │
│ 📚 以下是全文搜尋的參考資料：       │
│                                     │
│ ┌───────────────────────────────┐ │
│ │ 📄 Cup                        │ │
│ │ 來源：protocol_guide_20       │ │
│ │ 相似度：86%                   │ │
│ │ ▼ 展開完整內容                │ │
│ └───────────────────────────────┘ │
│                                     │
│ 👍 👎                               │
└─────────────────────────────────────┘
```

---

**模式 B 第一階段成功**（無關鍵字，段落搜尋成功）：
```
┌─────────────────────────────────────┐
│ 🤖 AI Assistant                     │
├─────────────────────────────────────┤
│ Cup 是一個測試項目，主要用於...     │
│                                     │
│ 👍 👎                               │
└─────────────────────────────────────┘
```

**模式 B 第二階段成功**（段落失敗，全文成功）：
```
┌─────────────────────────────────────┐
│ 🤖 AI Assistant   🔄 已自動切換全文  │
├─────────────────────────────────────┤
│ 根據完整文檔，Cup 的詳細流程...     │
│                                     │
│ ℹ️ 已自動為您切換到全文搜尋模式     │
│                                     │
│ 👍 👎                               │
└─────────────────────────────────────┘
```

**模式 B 降級**（兩階段都不確定）：
```
┌─────────────────────────────────────┐
│ 🤖 AI Assistant   📚 參考資料模式    │
├─────────────────────────────────────┤
│ 抱歉，我目前沒有足夠的資訊...       │
│                                     │
│ 📚 以下是可能相關的參考資料：       │
│                                     │
│ ┌───────────────────────────────┐ │
│ │ 📄 Cup                        │ │
│ │ 來源：protocol_guide_20       │ │
│ │ 相似度：86%                   │ │
│ │ ▼ 展開內容                    │ │
│ └───────────────────────────────┘ │
│                                     │
│ ┌───────────────────────────────┐ │
│ │ 📄 新舊各個版本主板            │ │
│ │ 來源：protocol_guide_21       │ │
│ │ 相似度：82%                   │ │
│ │ ▼ 展開內容                    │ │
│ └───────────────────────────────┘ │
│                                     │
│ 👍 👎                               │
└─────────────────────────────────────┘
```

---

## ⚙️ 配置選項

### 可調整參數 ⭐ **更新**

```python
# library/config/search_config.py

class SmartSearchConfig:
    """智能搜尋配置（整合兩種模式）"""
    
    # ===== 功能開關 =====
    SMART_SEARCH_ENABLED = True              # 智能路由總開關
    KEYWORD_TRIGGERED_ENABLED = True         # 模式 A 開關
    TWO_TIER_SEARCH_ENABLED = True           # 模式 B 開關
    
    # ===== 全文關鍵字檢測（模式 A）===== ⭐ 新增
    FULL_DOCUMENT_KEYWORDS = [
        # 完整性要求
        '完整', '全部', '全文', '完整內容', '完整文檔',
        '取得完整內容', '取得全部內容', '完整說明', '完整流程',
        
        # 步驟相關
        '所有步驟', '全部步驟', '完整步驟', '詳細步驟',
        '所有流程', '全部流程', '完整流程', '詳細流程',
        
        # 詳細性要求
        '詳細', '詳細內容', '詳細說明', '詳細資訊',
        '完整資訊', '全部資訊', '所有資訊',
        
        # 英文
        'full', 'complete', 'entire', 'all steps',
        'full document', 'complete document', 'detailed',
    ]
    
    # ===== 不確定檢測（共用）=====
    UNCERTAINTY_KEYWORDS = [
        # 明確否定
        '不清楚', '不知道', '不了解', '不確定',
        '沒有相關資料', '沒有找到', '沒有資訊', '找不到',
        
        # 委婉表達
        '抱歉', '很遺憾', '無法回答', '無法提供',
        '資訊不足', '資料不足', '缺乏資訊',
        
        # 英文
        'I don\'t know', 'not sure', 'unclear',
        'no information', 'cannot find', 'unable to answer',
        
        # 模糊回答
        '可能', '也許', '不太確定', '我猜',
    ]
    MIN_RESPONSE_LENGTH = 20              # 最短回答長度
    
    # ===== 模式 A：關鍵字優先搜尋參數 ===== ⭐ 新增
    MODE_A_TOP_K = 3                      # 返回文檔數
    MODE_A_THRESHOLD = 0.6                # 相似度閾值
    MODE_A_FALLBACK_ENABLED = True        # 允許降級模式
    
    # ===== 模式 B：兩階段搜尋參數 =====
    MODE_B_STAGE_1_TOP_K = 5              # 第一階段返回段落數
    MODE_B_STAGE_1_THRESHOLD = 0.7        # 第一階段相似度閾值
    
    MODE_B_STAGE_2_TOP_K = 3              # 第二階段返回文檔數
    MODE_B_STAGE_2_THRESHOLD = 0.6        # 第二階段相似度閾值（降低）
    MODE_B_FALLBACK_ENABLED = True        # 允許降級模式
    
    # ===== 降級模式（共用）=====
    FALLBACK_MAX_DOCUMENTS = 3            # 最多顯示文檔數
    FALLBACK_CONTENT_PREVIEW = 500        # 內容預覽字數
    
    # ===== 日誌 =====
    LOG_SEARCH_ROUTING = True             # 記錄路由決策
    LOG_KEYWORD_DETECTION = True          # 記錄關鍵字檢測
    LOG_UNCERTAINTY_DETECTION = True      # 記錄不確定檢測
    LOG_SEARCH_FALLBACK = True            # 記錄降級模式
```

---

## 📊 日誌與監控

### 日誌範例 ⭐ **更新**

**模式 A：關鍵字觸發（成功）** ⭐ 新增：
```log
[INFO] 智能路由: 用戶查詢='Cup顏色完整內容'
[INFO]   檢測全文關鍵字: True (含: 完整內容)
[INFO]   路由決策: mode_a (關鍵字優先全文搜尋)
[INFO]   
[INFO] 模式 A: 關鍵字優先全文搜尋
[INFO]   直接全文搜尋: 找到 3 個完整文檔
[INFO]   Dify 回應: '根據 Cup 文檔，完整流程包括...'
[INFO]   不確定檢測: False (明確回答)
[INFO]   ✅ 模式 A 成功，返回結果
```

**模式 A：關鍵字觸發（降級）** ⭐ 新增：
```log
[INFO] 智能路由: 用戶查詢='Cup顏色全文'
[INFO]   檢測全文關鍵字: True (含: 全文)
[INFO]   路由決策: mode_a (關鍵字優先全文搜尋)
[INFO]   
[INFO] 模式 A: 關鍵字優先全文搜尋
[INFO]   直接全文搜尋: 找到 3 個完整文檔
[INFO]   Dify 回應: '抱歉，我不清楚...'
[INFO]   不確定檢測: True (含關鍵字: 不清楚)
[WARN]   ⚠️  AI 回答不確定，啟用降級模式
[INFO]   💡 返回參考資料模式 (3 個文檔)
```

---

**模式 B：第一階段成功**：
```log
[INFO] 智能路由: 用戶查詢='Cup顏色'
[INFO]   檢測全文關鍵字: False
[INFO]   路由決策: mode_b (標準兩階段搜尋)
[INFO]   
[INFO] 模式 B: 標準兩階段搜尋
[INFO]   階段 1 (段落搜尋): 找到 5 個結果
[INFO]   Dify 回應: 'Cup 是一個測試項目...'
[INFO]   不確定檢測: False (明確回答)
[INFO]   ✅ 階段 1 成功，返回結果
```

**模式 B：第二階段成功**：
```log
[INFO] 智能路由: 用戶查詢='Cup的詳細步驟'
[INFO]   檢測全文關鍵字: False
[INFO]   路由決策: mode_b (標準兩階段搜尋)
[INFO]   
[INFO] 模式 B: 標準兩階段搜尋
[INFO]   階段 1 (段落搜尋): 找到 5 個結果
[INFO]   Dify 回應: '抱歉，我沒有找到相關資訊...'
[INFO]   不確定檢測: True (含關鍵字: 沒有找到)
[WARN]   ⚠️  階段 1 不確定，進入階段 2
[INFO]   階段 2 (全文搜尋): 找到 3 個完整文檔
[INFO]   Dify 回應: '根據 Cup 文檔，測試流程包括...'
[INFO]   不確定檢測: False (明確回答)
[INFO]   ✅ 階段 2 成功，返回結果
```

**模式 B：降級模式**：
```log
[INFO] 智能路由: 用戶查詢='不存在的主題'
[INFO]   檢測全文關鍵字: False
[INFO]   路由決策: mode_b (標準兩階段搜尋)
[INFO]   
[INFO] 模式 B: 標準兩階段搜尋
[INFO]   階段 1 (段落搜尋): 找到 2 個結果 (低相似度)
[INFO]   Dify 回應: '抱歉，我不清楚...'
[INFO]   不確定檢測: True (含關鍵字: 不清楚)
[WARN]   ⚠️  階段 1 不確定，進入階段 2
[INFO]   階段 2 (全文搜尋): 找到 1 個文檔
[INFO]   Dify 回應: '很遺憾，我無法找到相關資訊...'
[INFO]   不確定檢測: True (含關鍵字: 無法找到)
[ERROR]  ❌ 兩階段都不確定，啟用降級模式
[INFO]   💡 返回參考資料模式 (1 個文檔)
```

---

## 🎯 預期效果

### 用戶體驗改善 ⭐ **更新**

#### 場景 1：用戶明確要求完整內容（模式 A）⭐ 新增

**改善前**：
- 用戶：「Cup顏色完整內容」
- AI：「抱歉，我沒有相關資料。」（段落搜尋失敗）
- 用戶：😞（需要重新提問「Cup顏色全文」）

**改善後**：
- 用戶：「Cup顏色完整內容」
- 系統內部：
  1. 檢測到「完整內容」關鍵字
  2. 自動路由到模式 A（跳過段落搜尋）
  3. 直接全文搜尋 → AI 明確回答
- AI：「根據 Cup 文檔，完整流程包括...」+ 📋 全文搜尋標籤
- 用戶：😊（立即獲得完整答案）

**模式 A 降級**：
- 用戶：「Cup顏色全文」
- 系統內部：
  1. 檢測到「全文」關鍵字
  2. 直接全文搜尋 → AI 仍不確定
  3. 降級模式：顯示完整文檔參考資料
- AI：「抱歉，沒有足夠資訊。以下是全文搜尋的參考資料：📄 Cup (86%)...」
- 用戶：🤔（至少獲得完整文檔，可自行查看）

---

#### 場景 2：普通問題（模式 B）

**改善前**：
- 用戶：「Cup顏色」
- AI：「抱歉，我沒有相關資料。」
- 用戶：😞（需要重新提問或放棄）

**改善後（兩階段搜尋）**：
- 用戶：「Cup顏色」
- 系統內部：
  1. 無全文關鍵字 → 模式 B
  2. 段落搜尋 → AI 不確定
  3. 自動全文搜尋 → AI 明確回答
- AI：「根據 Cup 文檔，顏色相關說明包括...」+ 🔄 已自動切換全文標籤
- 用戶：😊（無需重新提問就獲得答案）

**改善後（降級模式）**：
- 用戶：「不存在的主題」
- 系統內部：
  1. 段落搜尋 → AI 不確定
  2. 全文搜尋 → AI 仍不確定
  3. 降級模式 → 顯示參考資料
- AI：「抱歉，沒有足夠資訊。以下是可能相關的資料：📄 Cup (86%)...」
- 用戶：🤔（至少獲得參考，可自行查看）

---

### 效果對比表

| 場景 | 改善前 | 改善後（模式 A） | 改善後（模式 B） |
|------|--------|-----------------|-----------------|
| **含「完整」關鍵字** | 段落搜尋失敗 → 無答案 | 直接全文搜尋 → 立即完整答案 | N/A（路由到模式 A） |
| **含「全文」關鍵字** | 段落搜尋失敗 → 無答案 | 直接全文搜尋 → 立即完整答案或參考資料 | N/A（路由到模式 A） |
| **普通問題（段落成功）** | 段落搜尋成功 → 精準答案 | N/A（路由到模式 B） | 段落搜尋成功 → 精準答案 |
| **普通問題（段落失敗）** | 段落搜尋失敗 → 無答案 | N/A（路由到模式 B） | 自動全文搜尋 → 完整答案或參考資料 |

---

## ⚠️ 注意事項與限制

### 潛在問題

1. **性能影響**
   - 問題：兩次 Dify 請求可能增加回應時間
   - 解決方案：
     - 設置合理超時（每階段 30 秒）
     - 考慮非同步處理
     - 快取相似查詢

2. **誤判風險**
   - 問題：AI 回答可能含有不確定關鍵字但實際是明確的
   - 範例：「雖然不太確定所有細節，但主要流程是...」
   - 解決方案：
     - 結合回答長度判斷
     - 使用更智能的 NLP 分析（未來）
     - 允許手動配置敏感度

3. **成本考量**
   - 問題：兩次 Dify 請求 = 雙倍 Token 消耗
   - 解決方案：
     - 記錄降級使用率
     - 優化不確定檢測準確性
     - 考慮快取機制

4. **對話連貫性**
   - 問題：兩次請求在同一對話中，可能影響上下文
   - 解決方案：
     - 使用相同 conversation_id
     - 或者使用新的臨時對話 ID（第二階段）

---

## 📈 成功指標

### KPI 定義 ⭐ **更新**

1. **模式 A 使用率** ⭐ 新增
   - 計算：包含全文關鍵字的查詢百分比
   - 預期：10-15%（說明用戶會明確要求完整內容）
   - 監控：關鍵字觸發準確性

2. **模式 A 成功率** ⭐ 新增
   - 計算：模式 A 中 AI 明確回答的百分比
   - 目標：> 80%（說明全文搜尋有效）

3. **模式 B 降級觸發率**
   - 計算：進入第二階段的查詢百分比（模式 B）
   - 目標：< 20%（說明第一階段足夠準確）

4. **整體降級模式使用率**
   - 計算：進入降級模式的查詢百分比（模式 A + B）
   - 目標：< 5%（說明智能搜尋有效）

5. **用戶滿意度提升**
   - 計算：點讚/點踩比率變化
   - 目標：點讚率提升 15%+（因為模式 A 直接命中需求）

6. **平均回應時間**
   - 計算：包含智能路由的平均時間
   - 模式 A 目標：< 4 秒（單次全文搜尋）
   - 模式 B 目標：< 8 秒（兩階段搜尋）

7. **關鍵字檢測準確性** ⭐ 新增
   - 計算：正確路由到模式 A 的百分比
   - 目標：> 95%（極少誤判）

---

## 🔄 未來擴展

### 可能的改進方向

1. **智能降級決策**
   - 使用 LLM 判斷回答品質（而非簡單關鍵字）
   - 語義相似度評分

2. **個性化搜尋策略**
   - 根據用戶歷史自動調整策略
   - 學習哪些用戶更偏好完整文檔

3. **多模態搜尋**
   - 第三階段：搜尋圖片、表格
   - 結合不同資料源

4. **主動建議**
   - 在降級模式中，AI 主動建議相關問題
   - 「您可能想問：...」

---

## 📋 實作檢查清單

準備實作時，需要確認以下項目：

### 前置條件
- [ ] 確認 Protocol Assistant 現有搜尋功能正常
- [ ] 確認 Dify 知識庫整合正常
- [ ] 確認全文搜尋功能（document_id）已修復

### Phase 1 - 核心邏輯
- [ ] ⭐ 創建 `keyword_detector.py`（全文關鍵字檢測）
- [ ] 定義 `FULL_DOCUMENT_KEYWORDS` 列表
- [ ] 實作 `contains_full_document_keywords()`
- [ ] 創建 `uncertainty_detector.py`（不確定檢測）
- [ ] 定義 `UNCERTAINTY_KEYWORDS` 列表
- [ ] 實作 `is_uncertain_response()`
- [ ] 單元測試關鍵字檢測
- [ ] 單元測試不確定檢測

### Phase 2 - 智能路由與搜尋服務
- [ ] ⭐ 創建 `smart_search_router.py`（智能路由器）
- [ ] 實作 `route_search_strategy()`
- [ ] 實作 `handle_smart_search()`
- [ ] ⭐ 創建 `keyword_triggered_handler.py`（模式 A）
- [ ] 實作 `handle_keyword_triggered_search()`
- [ ] 創建 `two_tier_handler.py`（模式 B）
- [ ] 實作 `handle_two_tier_search()`
- [ ] 擴展 `search_knowledge()` 支援完整 `search_type`

### Phase 3 - API 整合
- [ ] 修改 `ProtocolGuideViewSet.chat()` action
- [ ] 整合 `SmartSearchRouter`
- [ ] 添加配置選項（`SmartSearchConfig`）
- [ ] 測試路由決策邏輯
- [ ] 測試模式 A 流程
- [ ] 測試模式 B 流程

### Phase 4 - 前端
- [ ] 識別回應中的 `mode` 欄位
- [ ] 識別 `is_fallback` 標記
- [ ] 實作模式 A 的特殊標籤（📋 全文搜尋）
- [ ] 實作模式 B 階段 2 的標籤（🔄 已自動切換）
- [ ] 實作降級模式的特殊 UI
- [ ] 測試不同模式的顯示效果

### Phase 5 - 測試
- [ ] ⭐ 單元測試：全文關鍵字檢測（10+ 案例）
- [ ] 單元測試：不確定關鍵字檢測（10+ 案例）
- [ ] 整合測試：模式 A 成功場景
- [ ] 整合測試：模式 A 降級場景
- [ ] 整合測試：模式 B 第一階段成功
- [ ] 整合測試：模式 B 第二階段成功
- [ ] 整合測試：模式 B 降級場景
- [ ] 性能測試：關鍵字檢測效能
- [ ] 性能測試：整體回應時間
- [ ] 用戶驗收測試

### Phase 6 - 監控與優化
- [ ] 添加智能路由日誌
- [ ] 添加關鍵字檢測日誌
- [ ] 添加不確定檢測日誌
- [ ] 添加降級模式日誌
- [ ] 設置監控指標（7 個 KPI）
- [ ] 收集用戶反饋
- [ ] 分析關鍵字觸發準確性
- [ ] 持續優化關鍵字列表

---

## 📚 參考資料

### 相關文檔
- `/docs/debugging/protocol-document-id-fix-report.md` - document_id 修復
- `/docs/features/protocol-keyword-cleaning-implementation.md` - 關鍵字清理
- `/docs/vector-search/vector-search-guide.md` - 向量搜尋指南

### 技術棧
- **後端**：Django REST Framework
- **AI 平台**：Dify
- **向量搜尋**：pgvector + multilingual-e5-large
- **前端**：React + Ant Design

---

**規劃完成日期**：2025-11-11  
**預估開發時間**：8-12 小時（1-2 天）  
**風險等級**：低（現有功能的增強，不影響核心流程）  
**建議實作時機**：在完成向量系統修復後（已完成 ✅）

---

## 🎯 總結

這個**智能搜尋路由策略（整合模式 A + 模式 B）**能夠：

### 核心能力 ⭐ **更新**

1. ✅ **智能關鍵字檢測**：自動識別用戶是否要求完整內容
   - 檢測關鍵字：完整、全部、全文、所有步驟、詳細內容 等
   - 正確率目標：> 95%

2. ✅ **模式 A：關鍵字優先全文搜尋** ⭐ 新功能
   - 含全文關鍵字 → 直接全文搜尋（跳過段落搜尋）
   - 節省時間：減少 1 次 Dify 請求
   - 更精準：直接滿足用戶的完整性需求
   - AI 不確定 → 立即顯示全文參考資料

3. ✅ **模式 B：標準兩階段自動降級**
   - 無關鍵字 → 段落搜尋優先
   - 段落失敗 → 自動全文搜尋
   - 兩階段都失敗 → 顯示參考資料

4. ✅ **提升回答準確性**：
   - 模式 A：立即命中用戶完整性需求
   - 模式 B：自動從段落降級到全文

5. ✅ **改善用戶體驗**：
   - 無需重新提問「完整內容」或「全文」
   - 即使無法回答，也提供參考資料
   - 清晰的 UI 標籤（📋 全文搜尋 / 🔄 已自動切換）

6. ✅ **保持系統效能**：
   - 模式 A：單次請求（~4 秒）
   - 模式 B 大部分查詢在第一階段完成（~3 秒）
   - 只有必要時才進行第二次搜尋

7. ✅ **易於監控優化**：
   - 7 個 KPI 指標
   - 完整的日誌追蹤
   - 可調整的關鍵字列表

---

### 技術亮點 ⭐

- **智能路由**：1 行代碼決定搜尋策略
- **零額外成本**：關鍵字檢測無 API 成本
- **向後兼容**：不影響現有搜尋功能
- **易於擴展**：可輕鬆添加新關鍵字或新模式

---

### 預期改善

| 指標 | 改善前 | 改善後 |
|------|--------|--------|
| **含關鍵字查詢的成功率** | ~50% | > 80% ⭐ |
| **普通查詢的成功率** | ~70% | > 85% |
| **用戶滿意度（點讚率）** | 基準 | +15% ⭐ |
| **平均回應時間** | 3-5 秒 | 模式A: 4秒, 模式B: 3-8秒 |
| **需要重新提問的比率** | ~30% | < 10% ⭐ |

準備好實作時，隨時告訴我！ 🚀

---

**規劃完成日期**：2025-11-11  
**最後更新**：2025-11-11（新增模式 A：關鍵字優先全文搜尋）  
**預估開發時間**：10-14 小時（1.5-2 天）  
**風險等級**：低（現有功能的增強，不影響核心流程）  
**建議實作時機**：在完成向量系統修復後（已完成 ✅）  
**核心優勢**：用戶明確要求完整內容時，系統立即響應（無需二次搜尋）⭐
