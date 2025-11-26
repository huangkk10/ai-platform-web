# Protocol Assistant 沒有顯示引用來源 - 完整診斷報告

## 🔍 問題分析

**用戶反映**：在 Protocol Assistant 中詢問「CrystalDiskMark 是什麼？」，AI 有回答，但沒有顯示「引用來源」區塊。

## ✅ 已確認的正常部分

### 1. Dify API 正常返回 metadata
```bash
測試結果：
✅ HTTP 狀態碼: 200
✅ has metadata: True
✅ metadata.retriever_resources 存在
✅ 引用來源數量: 1
```

### 2. 後端代碼正確傳遞 metadata
```python
# library/protocol_guide/two_tier_handler.py
return {
    'answer': stage_2_answer,
    'metadata': stage_2_response.get('raw_response', {}).get('metadata', {}),  # ✅
    # ...
}
```

### 3. 前端組件支援顯示引用來源
```jsx
// frontend/src/components/chat/MessageFormatter.jsx
{metadata?.retriever_resources && (
  <RetrievedSources retrieverResources={metadata.retriever_resources} />
)}
```

### 4. MessageList 正確傳遞 metadata
```jsx
// frontend/src/components/chat/MessageList.jsx
<MessageFormatter 
  content={msg.content}
  metadata={msg.metadata}  // ✅ 正確傳遞
  messageType={msg.type}
/>
```

## ❌ 問題所在：Hook 沒有正確傳遞 metadata

### 發現的問題

在 `useProtocolAssistantChat.js` 中：

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js (第 88-100 行)

const assistantMessage = {
  id: Date.now() + 1,
  type: 'assistant',
  content: data.answer || '抱歉，我無法生成回應。',
  timestamp: new Date(),
  metadata: data.metadata,  // ⚠️ 這裡正確接收了 metadata
  usage: data.usage,
  response_time: data.response_time,
  message_id: data.message_id
};

console.log('💬 [Protocol Assistant] 創建 assistant 訊息:', {
  id: assistantMessage.id,
  content_length: assistantMessage.content.length,
  has_metadata: !!assistantMessage.metadata,  // ⚠️ 需要檢查這個
  message_id: assistantMessage.message_id
});

// 添加 assistant 訊息到列表
setMessages(prevMessages => [...prevMessages, assistantMessage]);
```

**潛在問題**：
1. 後端可能返回了 `metadata`，但內容為空或格式不對
2. `data.metadata` 可能是 `undefined` 或 `null`
3. `retriever_resources` 可能在不同的位置

## 🛠️ 診斷步驟

### 步驟 1：檢查後端實際返回的資料

```bash
# 1. 啟動 Django shell
docker exec -it ai-django python manage.py shell

# 2. 執行測試
from library.protocol_guide.api_handlers import ProtocolGuideAPIHandler
from django.test import RequestFactory
from django.contrib.auth.models import User

factory = RequestFactory()
user = User.objects.first()

request = factory.post('/api/protocol-guide/chat/', {
    'message': 'CrystalDiskMark 是什麼',
    'conversation_id': '',
    'user_id': f'user_{user.id}'
}, content_type='application/json')

request.user = user

response = ProtocolGuideAPIHandler.handle_chat_api(request)

print(f"Status: {response.status_code}")
print(f"Data keys: {response.data.keys()}")
print(f"Has metadata: {'metadata' in response.data}")

if 'metadata' in response.data:
    metadata = response.data['metadata']
    print(f"Metadata keys: {metadata.keys()}")
    print(f"Has retriever_resources: {'retriever_resources' in metadata}")
    if 'retriever_resources' in metadata:
        print(f"Resources count: {len(metadata['retriever_resources'])}")
```

### 步驟 2：檢查前端 Console 日誌

在瀏覽器中：
1. 打開 DevTools (F12)
2. 進入 Console 面板
3. 發送一個測試訊息「ULINK」
4. 查找日誌：

```
🔍 [Protocol Assistant] 收到後端回應:
  - success: true
  - answer_length: 1234
  - conversation_id: xxx
  - message_id: xxx
  - has_answer: true
  - has_metadata: ???  ← 檢查這個
```

5. 查找創建訊息的日誌：

```
💬 [Protocol Assistant] 創建 assistant 訊息:
  - id: xxx
  - content_length: 1234
  - has_metadata: ???  ← 檢查這個
  - message_id: xxx
```

6. 在 Console 中手動檢查最後一條訊息：

```javascript
// 在 Console 中執行
const lastMessage = JSON.parse(localStorage.getItem('protocol-assistant-messages')).pop();
console.log('Last message metadata:', lastMessage.metadata);
console.log('Has retriever_resources:', lastMessage.metadata?.retriever_resources);
```

### 步驟 3：檢查網絡請求

在 DevTools 的 Network 面板：
1. 找到 `/api/protocol-guide/chat/` 請求
2. 查看 Response：

```json
{
  "success": true,
  "answer": "...",
  "metadata": {  ← 檢查這個欄位
    "retriever_resources": [  ← 檢查是否存在
      {
        "document_name": "...",
        "score": 0.92,
        "content": "..."
      }
    ]
  }
}
```

## 🔧 修復方案

### 方案 1：增強日誌記錄（診斷用）

修改 `useProtocolAssistantChat.js`：

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js

// 在第 74 行附近添加更詳細的日誌
console.log('🔍 [Protocol Assistant] 收到後端回應:', {
  success: data.success,
  answer_length: data.answer?.length || 0,
  conversation_id: data.conversation_id,
  message_id: data.message_id,
  has_answer: !!data.answer,
  has_metadata: !!data.metadata,  // ✅ 添加
  metadata_keys: data.metadata ? Object.keys(data.metadata) : [],  // ✅ 添加
  has_retriever_resources: !!data.metadata?.retriever_resources,  // ✅ 添加
  retriever_resources_count: data.metadata?.retriever_resources?.length || 0  // ✅ 添加
});

// ... 

// 在第 88-100 行附近，創建 assistantMessage 後
const assistantMessage = {
  id: Date.now() + 1,
  type: 'assistant',
  content: data.answer || '抱歉，我無法生成回應。',
  timestamp: new Date(),
  metadata: data.metadata,
  usage: data.usage,
  response_time: data.response_time,
  message_id: data.message_id
};

console.log('💬 [Protocol Assistant] 創建 assistant 訊息:', {
  id: assistantMessage.id,
  content_length: assistantMessage.content.length,
  has_metadata: !!assistantMessage.metadata,
  metadata_keys: assistantMessage.metadata ? Object.keys(assistantMessage.metadata) : [],  // ✅ 添加
  has_retriever_resources: !!assistantMessage.metadata?.retriever_resources,  // ✅ 添加
  retriever_resources_count: assistantMessage.metadata?.retriever_resources?.length || 0,  // ✅ 添加
  message_id: assistantMessage.message_id
});
```

### 方案 2：修正可能的 metadata 結構問題

如果後端返回的 metadata 結構不對，修改 `api_handlers.py`：

```python
# library/protocol_guide/api_handlers.py (第 142-153 行)

return Response({
    'success': True,
    'answer': result.get('answer', ''),
    'mode': result.get('mode'),
    'stage': result.get('stage'),
    'is_fallback': result.get('is_fallback', False),
    'fallback_reason': result.get('fallback_reason'),
    'message_id': result.get('message_id'),
    'conversation_id': result.get('conversation_id', conversation_id),
    'response_time': elapsed,
    'tokens': result.get('tokens', {}),
    'metadata': result.get('metadata', {}),  # ⚠️ 確保這裡傳遞了完整的 metadata
    'search_results_count': len(result.get('search_results', []))
}, status=status.HTTP_200_OK)
```

### 方案 3：檢查 TwoTierSearchHandler 的 raw_response

修改 `two_tier_handler.py`，確保正確讀取 metadata：

```python
# library/protocol_guide/two_tier_handler.py

def _request_dify_chat(self, query, conversation_id, user_id, is_full_search=False):
    """發送請求到 Dify API"""
    # ...
    
    response_data = dify_manager.send_chat_request(
        query=query,
        conversation_id=conversation_id,
        user_id=user_id,
        # ...
    )
    
    # ✅ 確保保存 raw_response
    if 'raw_response' not in response_data:
        response_data['raw_response'] = response_data  # 直接使用整個回應
    
    # ✅ 記錄日誌以便診斷
    logger.info(f"Dify 回應 metadata keys: {response_data.get('metadata', {}).keys()}")
    logger.info(f"Has retriever_resources: {'retriever_resources' in response_data.get('metadata', {})}")
    
    return response_data
```

## 📊 快速診斷命令

```bash
# 1. 測試後端 API
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=$(grep sessionid ~/.local/share/httpie/sessions/localhost/default.json | cut -d'"' -f4)" \
  -d '{"message":"ULINK","conversation_id":"","user_id":"test"}' \
  | jq '.metadata.retriever_resources'

# 2. 查看實時日誌
docker logs ai-django -f | grep -A 10 "Protocol Guide Chat Request"

# 3. 檢查 localStorage
# 在瀏覽器 Console 中執行：
JSON.parse(localStorage.getItem('protocol-assistant-messages')).slice(-3).map(m => ({
  type: m.type,
  has_metadata: !!m.metadata,
  has_retriever_resources: !!m.metadata?.retriever_resources,
  resources_count: m.metadata?.retriever_resources?.length || 0
}))
```

## 🎯 預期結果

### 正常情況下應該看到：

1. **後端日誌**：
```
📩 Protocol Guide Chat Request
Dify 回應 metadata keys: dict_keys(['annotation_reply', 'retriever_resources', 'usage'])
Has retriever_resources: True
✅ 智能搜尋完成
```

2. **前端 Console**：
```
🔍 [Protocol Assistant] 收到後端回應:
  - has_metadata: true
  - metadata_keys: ["retriever_resources", "usage", ...]
  - has_retriever_resources: true
  - retriever_resources_count: 1

💬 [Protocol Assistant] 創建 assistant 訊息:
  - has_metadata: true
  - has_retriever_resources: true
  - retriever_resources_count: 1
```

3. **UI 顯示**：
```
┌─────────────────────────────────────┐
│ 🤖 Assistant 回應                   │
│                                     │
│ CrystalDiskMark 是一款...           │
│                                     │
│ 📚 引用來源 (1)                     │
│ ├─ CrystalDiskMark 測試指南         │
│ │  相似度: 92%                      │
│ └─ 文檔片段: ...                    │
└─────────────────────────────────────┘
```

## 🚨 如果仍然沒有顯示

### 可能的原因：

1. **Dify 工作室知識庫未綁定**
   - 檢查 Protocol Guide App 是否綁定了知識庫
   - 檢查知識庫中是否有文檔

2. **查詢沒有觸發知識庫檢索**
   - Dify 可能認為問題可以直接回答
   - Score 閾值設定太高

3. **前端組件條件渲染失敗**
   - `metadata?.retriever_resources` 檢查失敗
   - 資料格式不匹配

## 📝 下一步建議

1. **先執行診斷命令**，收集日誌資料
2. **查看瀏覽器 Console**，確認 metadata 是否到達前端
3. **檢查 Network 面板**，確認後端回應格式
4. **必要時添加增強日誌**，追蹤資料流向

---

**更新日期**：2025-11-26  
**文檔類型**：故障診斷  
**問題狀態**：診斷中
