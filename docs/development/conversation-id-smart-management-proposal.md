# 智能 Conversation ID 管理方案

## 問題背景

Dify 的 `conversation_id` 有以下特性：
1. **快速失效**：幾秒到幾分鐘內就可能過期
2. **404 錯誤**：使用過期的 conversation_id 會返回 404
3. **隨機性**：即使知識庫結果相同，AI 回答也有隨機性

## 方案：智能檢測與自動清除

### 核心邏輯

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js

const sendMessage = async (message) => {
  // ... 準備用戶訊息
  
  const requestBody = {
    message: userMessage.content,
    conversation_id: conversationId,  // 保留，但有策略
    user_id: currentUserId
  };
  
  try {
    const response = await api.post('/api/protocol-guide/chat/', requestBody);
    
    // ✅ 成功：更新 conversation_id
    if (response.data.conversation_id) {
      setConversationId(response.data.conversation_id);
      // 設置過期時間（例如 5 分鐘）
      conversationExpiryRef.current = Date.now() + 5 * 60 * 1000;
    }
    
  } catch (error) {
    if (error.response?.status === 404) {
      // ❌ 404 錯誤：清空 conversation_id，重試
      console.warn('⚠️ Conversation 已失效，開始新對話');
      setConversationId('');
      
      // 重試（不帶 conversation_id）
      const retryBody = {
        message: userMessage.content,
        user_id: currentUserId
      };
      
      const retryResponse = await api.post('/api/protocol-guide/chat/', retryBody);
      // ... 處理重試結果
    }
  }
};

// 發送前檢查過期
useEffect(() => {
  const checkInterval = setInterval(() => {
    if (conversationId && conversationExpiryRef.current < Date.now()) {
      console.log('⏰ Conversation 已過期，自動清除');
      setConversationId('');
    }
  }, 10000); // 每 10 秒檢查一次
  
  return () => clearInterval(checkInterval);
}, [conversationId]);
```

### 優點

1. **保留對話記憶**：在 conversation_id 有效期內可以多輪對話
2. **自動容錯**：過期後自動清除，不會造成 404
3. **主動過期**：前端預先清除，減少失敗機率

### 缺點

1. **複雜度增加**：需要管理過期時間
2. **仍有隨機性**：LLM 本身的隨機性無法完全消除
3. **需要調校**：過期時間需要根據 Dify 實際情況調整

## 實作步驟

1. **添加過期檢測**：useRef 記錄過期時間
2. **404 自動重試**：保留現有的自動重試機制
3. **主動清除**：定時檢查並清除過期的 conversation_id
4. **用戶可選**：提供"清除對話"按鈕，讓用戶手動開始新對話

## 測試計劃

1. **單次請求**：測試不帶 conversation_id 的成功率
2. **連續請求**：測試 conversation_id 的有效期
3. **過期處理**：測試自動清除機制
4. **多輪對話**：測試對話記憶功能

## 建議

**短期**：保持目前的修正（完全不使用 conversation_id）
**長期**：如果用戶需要多輪對話，再實作智能管理方案
