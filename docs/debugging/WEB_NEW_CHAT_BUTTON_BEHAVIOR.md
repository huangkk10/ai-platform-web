# 🆕 Web 前端「新聊天」按鈕行為分析

## ✅ **你的理解完全正確！**

**是的，在 Web 上按了「新聊天」按鈕，就會使用新的 conversation_id！**

---

## 📋 **「新聊天」按鈕的完整執行流程**

### **1. 用戶點擊「新聊天」按鈕**

位置：頂部導航欄右側的「新對話」按鈕

```javascript
// frontend/src/components/TopHeader.js
<Button 
  icon={<PlusOutlined />} 
  onClick={handleNewChat}  // ✅ 觸發清除對話
>
  新對話
</Button>
```

---

### **2. 觸發 `clearChat()` 函數**

```javascript
// frontend/src/hooks/useMessageStorage.js (Lines 275-281)

const clearChat = useCallback(() => {
  const welcomeContent = welcomeMessage || DEFAULT_WELCOME_MESSAGE.content;
  const defaultMessage = { 
    id: 1, 
    type: 'assistant', 
    content: welcomeContent, 
    timestamp: new Date() 
  };
  
  // ✅ 步驟 1：重置訊息列表（只保留歡迎訊息）
  setMessages([defaultMessage]);
  
  // ✅ 步驟 2：清空 conversation_id（設為空字串）
  setConversationId('');
  
  // ✅ 步驟 3：從 localStorage 中刪除舊的 conversation_id
  clearStoredChat(storageKey, currentUserId);
}, [currentUserId, storageKey, welcomeMessage]);
```

**執行結果**：
- ✅ 訊息列表被清空（只剩歡迎訊息）
- ✅ `conversationId` 被設為空字串 `""`
- ✅ localStorage 中的 `conversation_id` 被刪除

---

### **3. 用戶發送第一條新訊息**

當 `conversationId` 為空時，後端會自動生成新的 conversation_id：

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js (Line 35-40)

const requestBody = {
  message: userMessage.content,
  conversation_id: conversationId,  // ✅ 此時為空字串 ""
  user_id: currentUserId,
  search_version: 'v2'
};

// 發送到後端 API
fetch('/api/protocol-guide/chat/', {
  method: 'POST',
  body: JSON.stringify(requestBody),
  // ...
});
```

**後端處理**（Django）：

```python
# library/dify_integration/dify_request_manager.py

def send_chat_request(self, query, user_id, conversation_id=None):
    """發送聊天請求到 Dify"""
    
    payload = {
        "query": query,
        "user": user_id,
        "inputs": {},
        "response_mode": "blocking"
    }
    
    # ✅ 如果 conversation_id 為空，Dify 會自動生成新的 ID
    if conversation_id:
        payload["conversation_id"] = conversation_id
    # 否則不傳入 conversation_id，Dify 會創建新對話
    
    response = requests.post(self.api_url, json=payload, ...)
    return response.json()
```

**Dify 回應**：

```json
{
  "success": true,
  "conversation_id": "NEW-UUID-GENERATED-BY-DIFY",  // ✅ 全新的 ID
  "message_id": "msg_xxxxx",
  "answer": "...",
  "metadata": {...}
}
```

---

### **4. 前端接收並儲存新的 conversation_id**

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js (Line 75-79)

if (data.success) {
  const newConversationId = data.conversation_id || conversationId;
  
  // ✅ 如果後端返回新的 conversation_id，就更新
  if (newConversationId !== conversationId) {
    console.log('🆔 更新 conversation_id:', conversationId, '=>', newConversationId);
    setConversationId(newConversationId);  // ✅ 儲存新 ID
  }
  
  // ... 處理回應訊息
}
```

**localStorage 自動儲存**：

```javascript
// frontend/src/hooks/useMessageStorage.js (Lines 267-271)

useEffect(() => {
  if (conversationId) {
    // ✅ 自動將新的 conversation_id 儲存到 localStorage
    saveConversationId(conversationId, storageKey, currentUserId);
  }
}, [conversationId, currentUserId, storageKey]);
```

---

## 🎯 **完整流程總結**

| 步驟 | 動作 | conversation_id 狀態 |
|------|------|---------------------|
| **1** | 用戶點擊「新聊天」 | 清空（設為 `""`） |
| **2** | localStorage 被清除 | 移除舊的 ID |
| **3** | 用戶發送新訊息 | 傳送空字串到後端 |
| **4** | 後端/Dify 生成新 ID | Dify 創建新對話 |
| **5** | 前端接收新 ID | 儲存新 ID（如 `4f5510ae-...`） |
| **6** | localStorage 自動儲存 | 持久化新 ID |
| **7** | 後續查詢都使用這個新 ID | 持續使用直到再次點擊「新聊天」 |

---

## 🔍 **關鍵證據：localStorage 行為**

### **正常使用流程（無「新聊天」）**

```javascript
// 第一次查詢
localStorage.getItem('protocol-assistant-conversation-1') 
// → null（沒有儲存）

// Dify 生成：4f5510ae-8df5-452e-903f-87aa6ca691b2

// 自動儲存
localStorage.setItem('protocol-assistant-conversation-1', '4f5510ae-...')

// 第二次查詢
localStorage.getItem('protocol-assistant-conversation-1')
// → "4f5510ae-8df5-452e-903f-87aa6ca691b2" ✅ 重用舊 ID

// 第三次、第四次... 都使用相同 ID
```

### **點擊「新聊天」後**

```javascript
// 用戶點擊「新聊天」
clearChat() // 執行

// 清除 localStorage
localStorage.removeItem('protocol-assistant-conversation-1') 
// ✅ 刪除舊 ID

// conversation_id 設為 ""
setConversationId('')

// 下一次查詢時
localStorage.getItem('protocol-assistant-conversation-1')
// → null（已被清除）

// 後端會生成全新的 ID
// 如：8e928401-7ecd-46e7-bb70-3810b5d96c35 ✅ 全新 ID
```

---

## 📊 **測試腳本 vs Web 前端對比**

| 特性 | 測試腳本 | Web 前端（正常使用） | Web 前端（新聊天後） |
|------|---------|-------------------|-------------------|
| **conversation_id 來源** | 代碼生成並持續使用 | localStorage 持久化 | 清空後重新生成 |
| **「新聊天」功能** | ❌ 無（需手動改代碼） | ✅ 有（按鈕觸發） | ✅ 執行清除 |
| **對話累積** | 10 輪（腳本限制） | 無限制（直到清除） | 重新開始（0 輪） |
| **模擬情境** | 持續對話場景 | 日常使用場景 | 清除對話場景 |

---

## 🎯 **你的問題：測試腳本如何模擬「新聊天」？**

### **目前測試腳本的模式**

```python
# backend/test_protocol_crystaldiskmark_stability.py

# 模式 1：持續使用相同 conversation_id（模擬正常使用）
tester.run_stability_test(
    query="crystaldiskmark",
    test_count=10,
    use_same_conversation=True,  # ✅ 持續使用相同 ID
    delay_between_tests=1.0
)

# 模式 2：每次使用新 conversation_id（模擬「新聊天」）
tester.run_stability_test(
    query="crystaldiskmark",
    test_count=10,
    use_same_conversation=False,  # ✅ 每次都是新 ID（模擬點擊「新聊天」）
    delay_between_tests=1.0
)
```

### **模式 2 的實際行為**

```python
def run_stability_test(self, ..., use_same_conversation=False):
    """執行穩定性測試"""
    
    # ✅ 如果 use_same_conversation=False，每次都傳空字串
    conversation_id = "" if not use_same_conversation else None
    
    for i in range(1, test_count + 1):
        result = self.run_single_query(
            query=query,
            test_number=i,
            conversation_id=conversation_id if conversation_id is not None else ""
            # ✅ 每次都傳 ""，後端每次都會生成新 ID
        )
        
        # ❌ 如果 use_same_conversation=False，不更新 conversation_id
        # 結果：每次都是全新對話（模擬連續點擊「新聊天」10 次）
        if use_same_conversation and conversation_id is None:
            conversation_id = result.get('conversation_id', "")
```

**模式 2 的測試結果（100% 成功）**：

```
📊 測試統計分析
===================================
📈 總測試次數: 10

🔍 搜尋模式分佈:
  模式 B（兩階段搜尋）: 10 次 (100.0%)

📊 模式 B 階段分佈:
  階段 1 成功: 10 次 (100.0%)
  階段 2 觸發: 0 次 (0.0%)

⚠️ 異常指標:
  降級次數: 0 次 (0.0%)
  不確定次數: 0 次 (0.0%)

🚨 問題檢測:
  ✅ 未檢測到明顯問題
```

**為什麼模式 2 成功率 100%？**
- ✅ **每次都是全新對話（無歷史記憶）**
- ✅ **無對話污染（每次都是首次查詢）**
- ✅ **Dify 記憶為空（無錯誤關聯）**

這就像用戶**每次查詢前都點擊「新聊天」**，所以永遠不會受到錯誤記憶影響！

---

## 💡 **結論**

### **你的理解完全正確！**

1. ✅ **Web 前端點擊「新聊天」會清空 conversation_id**
2. ✅ **下一次查詢會生成全新的 conversation_id**
3. ✅ **測試腳本的模式 2 完美模擬了這個行為**
4. ✅ **模式 2 成功率 100% 證明「新聊天」可以避免記憶污染**

### **這解釋了為什麼**：

| 場景 | conversation_id 行為 | Dify 記憶 | 成功率 |
|------|---------------------|----------|-------|
| **Web 正常使用** | 持續重用（可能累積很長） | 累積（可能包含錯誤關聯） | ❌ 14.3% |
| **Web 新聊天後** | 全新生成（無歷史） | 乾淨（無錯誤關聯） | ✅ 預計 90%+ |
| **測試腳本模式 1** | 持續重用（10 輪） | 短期累積 | ⚠️ 80% |
| **測試腳本模式 2** | 每次都新（無累積） | 每次都乾淨 | ✅ 100% |

### **實際建議給用戶**：

**如果遇到 Protocol Assistant 回答錯誤（如持續回答 I3C）**：
1. 🔴 **立即點擊「新聊天」按鈕**
2. 🟢 **重新提問（使用全新 conversation_id）**
3. ✅ **應該就能獲得正確回答了！**

---

## 🚀 **終極解決方案（不變）**

雖然「新聊天」可以暫時解決問題，但根本解決方案仍然是：

```sql
-- 提高 Score Threshold 到 0.88
UPDATE search_threshold_settings 
SET threshold = 0.88 
WHERE assistant_type = 'protocol_assistant';
```

**為什麼這個方案更好？**
- ✅ 用戶不需要手動點擊「新聊天」
- ✅ 即使對話很長也不會錯亂
- ✅ 從根本上過濾掉錯誤文檔（I3C 85.32%）
- ✅ 只保留正確文檔（CrystalDiskMark 90.74%）

---

## 📅 **更新記錄**

**2025-11-12 18:00**：
- ✅ 驗證 Web 前端「新聊天」按鈕會清空 conversation_id
- ✅ 確認測試腳本模式 2 完美模擬「新聊天」行為
- ✅ 解釋為什麼模式 2 成功率 100%（無對話記憶污染）
- ✅ 提供用戶實際操作建議（點擊「新聊天」可暫時解決問題）

**關鍵洞察**：
> "點擊「新聊天」= 清空 conversation_id = 全新對話 = 無錯誤記憶 = 高成功率。測試腳本模式 2 (100% 成功) 完美驗證了這個機制！"

