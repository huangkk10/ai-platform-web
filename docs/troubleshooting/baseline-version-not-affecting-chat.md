# Baseline 版本切換不影響 Chat 功能的問題診斷

## 🔴 問題描述

用戶在 VSA 版本管理中切換到 `Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)`，但在 Protocol Assistant Chat 中詢問問題時，沒有顯示「引用來源」區塊。

## 🔍 根本原因分析

### 關鍵發現：Baseline 版本**不影響** Chat 功能！

在 `ProtocolAssistantChatPage.js` 頂部的 Alert 組件中，有明確說明：

```javascript
description={
  <div style={{ fontSize: '12px' }}>
    <InfoCircleOutlined style={{ marginRight: '6px' }} />
    此配置僅用於 <strong>Benchmark 測試</strong>。
    Chat 功能的檢索參數在 <strong>Dify 工作室</strong> 中配置，與 Baseline 無關。
  </div>
}
```

**這表示**：
1. ✅ **Baseline 版本** → 只影響 VSA Benchmark 批量測試
2. ❌ **Baseline 版本** → **不影響** Protocol Assistant Chat 聊天功能
3. ✅ **Chat 功能** → 由 **Dify 工作室** 中的配置決定

### 系統架構說明

```
┌─────────────────────────────────────────────────────────────────┐
│                    Protocol Assistant 系統                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Protocol Assistant Chat（聊天功能）                         │
│     ├── 配置來源：Dify 工作室 (Dify Studio)                    │
│     ├── 配置代碼：library/config/dify_config_manager.py        │
│     ├── API 端點：/api/protocol-guide/chat/                    │
│     ├── 搜尋策略：SmartSearchRouter（動態路由）                │
│     └── 影響範圍：用戶在 Chat 頁面的所有對話                   │
│                                                                 │
│  2. VSA Benchmark 測試系統                                      │
│     ├── 配置來源：DifyConfigVersion 資料表 (Baseline)          │
│     ├── API 端點：/api/dify-benchmark/versions/batch_test/     │
│     ├── 搜尋策略：根據選擇的版本 (v1.1, v1.1.1, v1.2.1)       │
│     └── 影響範圍：只有批量測試、版本對比                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 為什麼沒有「引用來源」？

**可能原因 1：Dify 工作室配置問題**

```python
# library/config/dify_config_manager.py

@classmethod
def _get_protocol_guide_config(cls):
    """動態獲取 Protocol Guide 配置"""
    ai_pc_ip = cls._get_ai_pc_ip()
    return {
        'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
        'api_key': 'app-xxxxx',  # ⚠️ 實際的 App ID
        'base_url': f'http://{ai_pc_ip}',
        'app_name': 'Protocol Guide',
        'workspace': 'Protocol_Guide',
        # ...
    }
```

**檢查點**：
1. 這個 `api_key` 對應的 Dify App 是否啟用了知識庫檢索？
2. Dify App 的 RAG 配置是否正確？
3. 是否有綁定 `protocol_guide_db` 知識庫？

**可能原因 2：SmartSearchRouter 沒有返回 metadata**

```python
# library/protocol_guide/smart_search_router.py

def handle_smart_search(self, ...):
    # ...
    result = self.mode_b_handler.handle_two_tier_search(...)
    
    return result  # ⚠️ 是否包含 metadata？
```

**可能原因 3：TwoTierSearchHandler 的問題**

兩階段搜尋處理器可能沒有正確設置引用來源到 metadata。

## 🛠️ 診斷步驟

### 步驟 1：檢查 Dify 工作室配置

```bash
# 1. 查看當前 Protocol Guide 的 Dify 配置
docker exec ai-django python manage.py shell
```

```python
from library.config.dify_config_manager import get_protocol_guide_config

config = get_protocol_guide_config()
print(f"App Name: {config.app_name}")
print(f"API URL: {config.api_url}")
print(f"API Key: {config.api_key[:15]}...")  # 只顯示前 15 字元
print(f"Workspace: {config.workspace}")

# 測試 API 連接
import requests
try:
    response = requests.post(
        config.api_url,
        headers={'Authorization': f'Bearer {config.api_key}'},
        json={'query': '測試查詢', 'inputs': {}, 'response_mode': 'blocking', 'user': 'test'},
        timeout=10
    )
    print(f"Dify API 狀態: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"是否有 metadata: {'metadata' in data}")
        print(f"是否有 retriever_resources: {'retriever_resources' in data}")
except Exception as e:
    print(f"Dify API 錯誤: {str(e)}")
```

### 步驟 2：檢查實際的 Chat API 回應

```bash
# 查看最近的 Chat 請求日誌
docker logs ai-django --tail 200 | grep -A 20 "Protocol Guide Chat Request"
```

**應該看到的日誌格式**：
```
📩 Protocol Guide Chat Request
   User: admin
   Message: CrystalDiskMark 是什麼
   Conversation ID: xxx
🔍 智能路由: 用戶查詢='CrystalDiskMark 是什麼'
   檢測全文關鍵字: False
   路由決策: mode_b (標準兩階段搜尋)
✅ 智能搜尋完成
   模式: mode_b
   階段: 2
   是否降級: False
   響應時間: 2.34 秒
```

### 步驟 3：手動測試 Chat API

```bash
# 使用 curl 測試
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_SESSION_ID" \
  -d '{
    "message": "CrystalDiskMark 是什麼",
    "conversation_id": "",
    "user_id": "test_user"
  }' | jq '.'
```

**檢查回應中是否有**：
```json
{
  "success": true,
  "answer": "...",
  "metadata": {  // ⚠️ 這個欄位是否存在？
    "retriever_resources": [  // ⚠️ 引用來源
      {
        "document_name": "CrystalDiskMark 測試指南",
        "score": 0.92,
        "content": "..."
      }
    ]
  }
}
```

### 步驟 4：檢查前端是否正確處理 metadata

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js

const assistantMessage = {
  // ...
  metadata: data.metadata,  // ⚠️ 是否有傳遞？
  // ...
};
```

```javascript
// frontend/src/components/chat/MessageList.jsx

{msg.metadata?.retriever_resources && (
  <RetrievedSources sources={msg.metadata.retriever_resources} />
)}
```

## ✅ 解決方案

### 方案 1：確保 Dify App 啟用知識庫檢索

1. 登入 Dify 工作室：`http://10.10.172.37`
2. 找到 **Protocol Guide** 應用
3. 檢查「知識庫」設定：
   - ✅ 是否綁定了 `protocol_guide_db`
   - ✅ 檢索模式是否為「語義檢索」
   - ✅ Top K 是否設定正確（建議 3-5）
   - ✅ Score 閾值是否合理（建議 0.7）

### 方案 2：修正 TwoTierSearchHandler 的 metadata 回傳

檢查 `library/protocol_guide/two_tier_handler.py`，確保：

```python
def handle_two_tier_search(self, ...):
    # ... 執行搜尋
    
    # ✅ 從 Dify 回應中提取 metadata
    dify_response = dify_manager.send_chat_request(...)
    
    return {
        'answer': dify_response.get('answer'),
        'metadata': dify_response.get('metadata', {}),  # ⚠️ 必須包含
        # ...
    }
```

### 方案 3：啟用 Benchmark 版本影響 Chat（不推薦）

如果確實需要 Baseline 版本影響 Chat 功能，需要修改：

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js

const requestBody = {
  message: userMessage.content,
  conversation_id: conversationId,
  user_id: currentUserId,
  // 🆕 從 Baseline 讀取 version_code
  version_code: baselineVersion?.version_code  // ⚠️ 需要傳遞 Baseline
};
```

但這會**破壞原始設計**：
- ❌ Chat 應該使用固定的 Dify 配置（穩定性）
- ❌ Benchmark 測試才需要切換版本（對比測試）

## 📊 快速診斷指令

```bash
# 1. 檢查 Dify 配置
docker exec ai-django python -c "
from library.config.dify_config_manager import get_protocol_guide_config
config = get_protocol_guide_config()
print(f'App: {config.app_name}')
print(f'API Key: {config.api_key[:15]}...')
print(f'Workspace: {config.workspace}')
"

# 2. 測試 Chat API（替換 YOUR_COOKIE）
curl -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -H "Cookie: sessionid=YOUR_COOKIE" \
  -d '{"message":"測試查詢","conversation_id":"","user_id":"test"}' \
  | jq '.metadata'

# 3. 查看 Chat 日誌
docker logs ai-django --tail 100 | grep "Protocol Guide Chat"

# 4. 檢查 Dify 連接
docker exec ai-django python -c "
import requests
from library.config.dify_config_manager import get_protocol_guide_config
config = get_protocol_guide_config()
resp = requests.post(
    config.api_url,
    headers={'Authorization': f'Bearer {config.api_key}'},
    json={'query':'test','inputs':{},'response_mode':'blocking','user':'test'},
    timeout=5
)
print(f'Dify Status: {resp.status_code}')
print(f'Has metadata: {"metadata" in resp.json()}')
"
```

## 🎯 結論

**問題核心**：
1. ✅ Baseline 版本切換**只影響** VSA Benchmark 測試
2. ❌ Baseline 版本**不影響** Protocol Assistant Chat 功能
3. ✅ Chat 功能由 **Dify 工作室配置** 決定，與 Baseline 無關

**解決方向**：
1. 檢查 Dify 工作室中的 Protocol Guide App 配置
2. 確認知識庫檢索是否啟用
3. 檢查 Chat API 的實際回應中是否包含 metadata
4. 確認前端正確處理並顯示 retriever_resources

**不應該做的**：
- ❌ 期望切換 Baseline 版本會影響 Chat 功能
- ❌ 混淆 Benchmark 測試和 Chat 功能的配置來源

---

**更新日期**：2025-11-26  
**文檔類型**：故障排查  
**相關模組**：Protocol Assistant, VSA Benchmark, Dify Integration
