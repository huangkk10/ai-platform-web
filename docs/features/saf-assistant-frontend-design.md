# SAF Assistant 前端設計文檔

> **文檔狀態**：📋 規劃中（尚未執行）  
> **建立日期**：2025-12-05  
> **作者**：AI Platform Team  
> **參考範本**：Protocol Assistant

---

## 📋 概述

### 目標
建立 SAF Assistant 前端聊天介面，讓用戶可以透過 Web UI 與 SAF 專案管理系統互動查詢。

### 設計原則
- **仿效 Protocol Assistant**：使用相同的通用聊天組件架構
- **最小化新程式碼**：複製並修改現有組件
- **保持一致性**：與其他 Assistant 的 UI/UX 一致

---

## 🏗️ 系統架構

### 現有架構（Protocol Assistant）
```
┌─────────────────────────────────────────────────────────────────┐
│                    Protocol Assistant 架構                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ProtocolAssistantChatPage.js (頁面配置，~40 行)                 │
│         ↓                                                       │
│  CommonAssistantChatPage.jsx (通用聊天 UI，556 行)               │
│         ↓                                                       │
│  useProtocolAssistantChat.js (API 通訊 Hook，153 行)             │
│         ↓                                                       │
│  /api/protocol-guide/chat/ (Django 後端 API)                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### SAF Assistant 架構（規劃）
```
┌─────────────────────────────────────────────────────────────────┐
│                    SAF Assistant 架構                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  SAfAssistantChatPage.js (頁面配置，~50 行)         🆕 新建      │
│         ↓                                                       │
│  CommonAssistantChatPage.jsx (通用聊天 UI)         ✅ 已存在     │
│         ↓                                                       │
│  useSafAssistantChat.js (API 通訊 Hook，~160 行)   🆕 新建      │
│         ↓                                                       │
│  /api/saf/smart-query/ (Django 後端 API)           ✅ 已存在     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 檔案結構

### 需要新建的檔案

```
frontend/src/
├── pages/
│   ├── SAfAssistantChatPage.js      🆕 新建（頁面組件）
│   └── SAfAssistantChatPage.css     🆕 新建（樣式，可選）
├── hooks/
│   └── useSafAssistantChat.js       🆕 新建（API 通訊 Hook）
```

### 需要修改的檔案

```
frontend/src/
├── App.js                           📝 新增路由
├── components/
│   └── Sidebar.js                   📝 新增選單項目
```

### 共用組件（已存在，無需修改）

```
frontend/src/
├── components/
│   └── chat/
│       ├── CommonAssistantChatPage.jsx  ✅ 通用聊天頁面
│       ├── MessageList.jsx              ✅ 訊息列表
│       └── LoadingIndicator.jsx         ✅ 載入指示器
├── hooks/
│   ├── useMessageStorage.js             ✅ 訊息持久化
│   └── useMessageFeedback.js            ✅ 訊息反饋
```

---

## 📝 詳細設計

### 1. SAfAssistantChatPage.js

**檔案位置**：`frontend/src/pages/SAfAssistantChatPage.js`

**複製來源**：`ProtocolAssistantChatPage.js`

```javascript
/**
 * SAF Assistant 聊天頁面
 * =======================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 用於查詢 SAF 專案管理系統資訊
 */

import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useSafAssistantChat from '../hooks/useSafAssistantChat';
import '../components/markdown/ReactMarkdown.css';
import './SAfAssistantChatPage.css';

// SAF Assistant 專用歡迎訊息
const SAF_WELCOME_MESSAGE = `🔧 **歡迎使用 SAF Assistant！**

我是 SAF 專案管理系統的智能助手，可以協助你快速查詢專案相關資訊。

**📋 我可以幫助你：**

| 功能 | 範例問法 |
|------|----------|
| 🏢 查詢客戶專案 | 「WD 有哪些專案？」「Samsung 的專案列表」 |
| 🔌 查詢控制器專案 | 「SM2264 用在哪些專案？」「哪些專案使用 SM2269？」 |
| 📊 專案詳細資訊 | 「DEMETER 專案的詳細資訊」「查詢 Garuda 專案」 |
| 📈 專案測試摘要 | 「DEMETER 的測試結果如何？」 |
| 🔢 統計專案數量 | 「WD 有幾個專案？」「總共有多少專案？」 |
| 👥 列出所有客戶 | 「有哪些客戶？」「列出所有客戶」 |
| 🎛️ 列出所有控制器 | 「有哪些控制器？」「系統支援哪些控制器」 |

**💡 提示**：直接用自然語言提問即可，系統會自動理解你的意圖！

現在就開始吧！有什麼 SAF 專案相關的問題需要查詢嗎？`;

const SAfAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="saf"
      assistantName="SAF Assistant"
      useChatHook={useSafAssistantChat}
      configApiPath="/api/saf/smart-query/config/"
      storageKey="saf-assistant"
      permissionKey={null}  // 對所有用戶開放（包括訪客）
      placeholder="請輸入你的 SAF 查詢問題，例如：WD 有哪些專案？"
      welcomeMessage={SAF_WELCOME_MESSAGE}
      collapsed={collapsed}
      enableFileUpload={false}  // SAF 不需要檔案上傳功能
    />
  );
};

export default SAfAssistantChatPage;
```

---

### 2. useSafAssistantChat.js

**檔案位置**：`frontend/src/hooks/useSafAssistantChat.js`

**複製來源**：`useProtocolAssistantChat.js`

**主要修改**：
- API 端點改為 `/api/saf/smart-query/`
- 請求參數從 `message` 改為 `query`
- 回應欄位從 `answer` 改為 `response`

```javascript
/**
 * SAF Assistant Chat Hook
 * ========================
 * 
 * 處理 SAF Assistant 的 API 通訊
 * 
 * API 端點：POST /api/saf/smart-query/
 * 請求格式：{ query: "用戶問題" }
 * 回應格式：{
 *   success: true,
 *   response: "AI 回應",
 *   intent: "query_projects_by_customer",
 *   confidence: 0.97,
 *   parameters: { customer: "WD" },
 *   response_time_ms: 3500
 * }
 */

import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';

const useSafAssistantChat = (
  conversationId, 
  setConversationId, 
  setMessages, 
  user, 
  currentUserId
) => {
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const abortControllerRef = useRef(null);

  // 停止請求
  const stopRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setLoadingStartTime(null);
      message.info('已停止生成回應');
    }
  }, []);

  // 發送訊息
  const sendMessage = useCallback(async (userMessage) => {
    console.log('🚀 [SAF Assistant] sendMessage 開始執行');
    console.log('  - userMessage:', userMessage);
    
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      abortControllerRef.current = new AbortController();
      
      // ⚠️ SAF API 使用 "query" 參數，不是 "message"
      const requestBody = {
        query: userMessage.content
      };
      
      console.log('📤 [SAF Assistant] 發送請求:', requestBody);

      const response = await fetch('/api/saf/smart-query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });
      
      console.log('📥 [SAF Assistant] 收到回應:', {
        ok: response.ok,
        status: response.status
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('🔍 [SAF Assistant] 回應資料:', data);

      if (data.success) {
        // 創建 AI 回應訊息
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.response,  // ⚠️ SAF API 使用 "response"，不是 "answer"
          timestamp: new Date(),
          metadata: {
            intent: data.intent,
            confidence: data.confidence,
            parameters: data.parameters,
            response_time_ms: data.response_time_ms
          }
        };

        console.log('💬 [SAF Assistant] 創建 assistant 訊息:', assistantMessage);
        
        // 添加訊息到列表
        setMessages(prev => [...prev, assistantMessage]);
        
      } else {
        // 處理錯誤回應
        const errorMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.error_message || '抱歉，查詢失敗，請稍後再試。',
          timestamp: new Date(),
          isError: true
        };
        
        setMessages(prev => [...prev, errorMessage]);
      }

    } catch (error) {
      console.error('❌ [SAF Assistant] 發送訊息失敗:', error);
      
      if (error.name === 'AbortError') {
        console.log('🛑 [SAF Assistant] 請求已被取消');
        return;
      }
      
      // 添加錯誤訊息
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '抱歉，系統發生錯誤，請稍後再試。',
        timestamp: new Date(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
      message.error('發送訊息失敗');
      
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
      abortControllerRef.current = null;
    }
  }, [setMessages]);

  return {
    sendMessage,
    loading,
    loadingStartTime,
    stopRequest,
    setLoading,
    setLoadingStartTime
  };
};

export default useSafAssistantChat;
```

---

### 3. SAfAssistantChatPage.css（可選）

**檔案位置**：`frontend/src/pages/SAfAssistantChatPage.css`

```css
/**
 * SAF Assistant 聊天頁面樣式
 * 
 * 可以在這裡添加 SAF Assistant 特定的樣式
 * 如果不需要特殊樣式，可以省略此檔案
 */

/* SAF Assistant 特定樣式（如有需要） */
.saf-assistant-chat {
  /* 可以添加特定樣式 */
}

/* 表格在聊天中的顯示優化 */
.saf-assistant-chat .markdown-content table {
  font-size: 13px;
  margin: 8px 0;
}

.saf-assistant-chat .markdown-content th,
.saf-assistant-chat .markdown-content td {
  padding: 6px 10px;
}
```

---

### 4. App.js 路由配置

**修改位置**：`frontend/src/App.js`

**新增內容**：

```javascript
// 在 import 區塊新增
import SAfAssistantChatPage from './pages/SAfAssistantChatPage';

// 在 Route 配置區塊新增（約在 protocol-assistant-chat 路由附近）
<Route 
  path="/saf-assistant-chat" 
  element={<SAfAssistantChatPage collapsed={collapsed} />} 
/>
```

---

### 5. Sidebar.js 選單配置

**修改位置**：`frontend/src/components/Sidebar.js`

**目前選單順序**：
```
┌─────────────────────────────┐
│  🏠 Dashboard               │
│  🔍 Query                   │
│  📄 AI OCR (需權限)          │
│  📄 RVT Assistant           │
│  🔧 Protocol Assistant      │
│  🗄️ SAF Assistant    🆕     │  ← 新增在這裡
│  ─────────────────────────  │
│  📚 Knowledge Base ▼        │
│  ⚙️ Admin ▼ (需權限)        │
└─────────────────────────────┘
```

**新增內容**：

```javascript
// 1. 在 import 區塊確認有 DatabaseOutlined
import { 
  FileTextOutlined, 
  ToolOutlined,
  DatabaseOutlined,  // 🆕 SAF Assistant 用
  // ... 其他 icons
} from '@ant-design/icons';

// 2. 在 getTopMenuItems 函數中，Protocol Assistant 後面新增：
// （約在第 66-71 行之後）

    // Protocol Assistant - 對所有用戶開放（包括訪客）
    baseItems.push({
      key: 'protocol-assistant-chat',
      icon: <ToolOutlined />,
      label: 'Protocol Assistant',
    });

    // 🆕 SAF Assistant - 對所有用戶開放（包括訪客）
    baseItems.push({
      key: 'saf-assistant-chat',
      icon: <DatabaseOutlined />,
      label: 'SAF Assistant',
    });

    return baseItems;

// 3. 在 handleMenuClick 函數中，protocol-assistant-chat case 後面新增：
// （約在第 114 行之後）

      case 'protocol-assistant-chat':
        navigate('/protocol-assistant-chat');
        break;
      // 🆕 SAF Assistant
      case 'saf-assistant-chat':
        navigate('/saf-assistant-chat');
        break;
```

**修改位置精確定位**：

| 修改點 | 行號（約） | 內容 |
|-------|-----------|------|
| import icons | 第 1-20 行 | 確認有 `DatabaseOutlined` |
| 選單項目 | 第 66-71 行後 | 新增 `saf-assistant-chat` 項目 |
| 點擊處理 | 第 114 行後 | 新增 `case 'saf-assistant-chat'` |

---

## 🔧 後端配置（可選）

### 新增 Config API

如果需要讓前端獲取 SAF Assistant 的配置資訊，可以在後端新增：

**檔案位置**：`backend/api/views/saf_smart_query_views.py`

```python
# 新增 config action
@action(detail=False, methods=['get'])
def config(self, request):
    """
    取得 SAF Assistant 配置
    
    GET /api/saf/smart-query/config/
    """
    return Response({
        'success': True,
        'config': {
            'assistant_name': 'SAF Assistant',
            'version': '1.0.0',
            'supported_intents': [
                'query_projects_by_customer',
                'query_projects_by_controller',
                'query_project_detail',
                'query_project_summary',
                'count_projects',
                'list_all_customers',
                'list_all_controllers',
            ],
            'features': {
                'conversation_tracking': False,  # 目前不支援
                'file_upload': False,
            }
        }
    })
```

---

## 📊 API 格式對比

### 現有 SAF Smart Query API

| 項目 | 值 |
|------|-----|
| **端點** | `POST /api/saf/smart-query/` |
| **請求參數** | `{ "query": "用戶問題" }` |
| **成功回應** | `{ "success": true, "response": "...", "intent": "...", "confidence": 0.97 }` |
| **失敗回應** | `{ "success": false, "error_message": "..." }` |

### 與 Protocol Assistant API 的差異

| 項目 | Protocol Assistant | SAF Assistant |
|------|-------------------|---------------|
| 請求參數名 | `message` | `query` |
| 回應內容欄位 | `answer` | `response` |
| 對話追蹤 | ✅ `conversation_id` | ❌ 不支援 |
| 訊息 ID | ✅ `message_id` | ❌ 不支援 |

---

## ✅ 執行檢查清單

### 前端檔案

- [ ] 建立 `frontend/src/pages/SAfAssistantChatPage.js`
- [ ] 建立 `frontend/src/hooks/useSafAssistantChat.js`
- [ ] (可選) 建立 `frontend/src/pages/SAfAssistantChatPage.css`
- [ ] 修改 `frontend/src/App.js` 新增路由
- [ ] 修改 `frontend/src/components/Sidebar.js` 新增選單

### 後端檔案（可選）

- [ ] 修改 `backend/api/views/saf_smart_query_views.py` 新增 config API

### 測試驗證

- [ ] 前端編譯無錯誤
- [ ] 側邊欄顯示 SAF Assistant 選單
- [ ] 點擊選單可以導航到聊天頁面
- [ ] 歡迎訊息正確顯示
- [ ] 發送查詢可以收到回應
- [ ] 回應格式正確顯示（Markdown 表格）

---

## ⏱️ 預估工時

| 任務 | 預估時間 |
|------|---------|
| 建立 SAfAssistantChatPage.js | 30 分鐘 |
| 建立 useSafAssistantChat.js | 1 小時 |
| 修改 App.js 路由 | 10 分鐘 |
| 修改 Sidebar.js 選單 | 10 分鐘 |
| 測試與調整 | 30 分鐘 |
| **總計** | **約 2.5 小時** |

---

## 🚀 未來擴展

### Phase 2：對話追蹤功能
- 後端新增 conversation_id 支援
- 前端啟用對話歷史記錄

### Phase 3：進階功能
- 快速問題建議按鈕
- 查詢歷史記錄
- 匯出查詢結果

---

## 📚 參考資料

- Protocol Assistant 實作：`frontend/src/pages/ProtocolAssistantChatPage.js`
- 通用聊天組件：`frontend/src/components/chat/CommonAssistantChatPage.jsx`
- SAF Smart Query API：`backend/api/views/saf_smart_query_views.py`
- SAF Smart Query 設計文檔：`docs/architecture/llm-smart-api-router-design.md`

---

**文檔狀態**：📋 規劃完成，等待執行確認
