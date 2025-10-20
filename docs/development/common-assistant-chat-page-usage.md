# CommonAssistantChatPage 使用指南

## 📋 概述

`CommonAssistantChatPage` 是一個通用的 Assistant 聊天頁面組件，用於統一所有 Assistant（RVT、Protocol、QA 等）的聊天介面。

## 🎯 為什麼需要通用組件？

### 問題
- 每個 Assistant 都有獨立的聊天頁面（180+ 行代碼）
- UI 結構和邏輯完全相同，造成大量重複代碼
- 修改 UI 時需要同時修改多個文件
- 不利於維護和新功能開發

### 解決方案
- 提取共同的 UI 和邏輯到 `CommonAssistantChatPage`
- 各 Assistant 頁面簡化為 10-20 行配置代碼
- 統一維護，修改一處即可影響所有 Assistant

## 📁 文件位置

```
frontend/src/
├── components/
│   └── chat/
│       └── CommonAssistantChatPage.jsx  # 通用聊天頁面組件
└── pages/
    ├── RvtAssistantChatPage.js          # RVT Assistant (使用通用組件)
    ├── ProtocolAssistantChatPage.js     # Protocol Assistant (使用通用組件)
    └── XxxAssistantChatPage.js          # 未來的 Assistant (使用通用組件)
```

## 🚀 使用方式

### 基本使用

```javascript
import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useXxxChat from '../hooks/useXxxChat';
import './XxxAssistantChatPage.css';

const XxxAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="xxx"
      assistantName="Xxx Assistant"
      useChatHook={useXxxChat}
      configApiPath="/api/xxx-assistant/config/"
      storageKey="xxx-assistant"
      permissionKey="webXxxAssistant"
      placeholder="請描述你的 Xxx 問題..."
      collapsed={collapsed}
    />
  );
};

export default XxxAssistantChatPage;
```

## 📋 組件參數說明

| 參數 | 類型 | 必填 | 說明 | 範例 |
|------|------|------|------|------|
| `assistantType` | string | ✅ | Assistant 類型標識 | `'rvt'`, `'protocol'`, `'qa'` |
| `assistantName` | string | ✅ | Assistant 顯示名稱 | `'RVT Assistant'` |
| `useChatHook` | function | ✅ | 聊天 Hook 函數 | `useRvtChat` |
| `configApiPath` | string | ✅ | 配置 API 路徑 | `'/api/rvt-guide/config/'` |
| `storageKey` | string | ✅ | localStorage 鍵名 | `'rvt'`, `'protocol-assistant'` |
| `permissionKey` | string | ✅ | 權限檢查鍵名 | `'webRvtAssistant'` |
| `placeholder` | string | ❌ | 輸入框提示文字 | `'請描述你的 RVT 問題...'` |
| `collapsed` | boolean | ❌ | 側邊欄是否收合 | `false` |

## 📝 完整範例

### 1. RVT Assistant（已實現）

```javascript
// frontend/src/pages/RvtAssistantChatPage.js
import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useRvtChat from '../hooks/useRvtChat';
import './RvtAssistantChatPage.css';

const RvtAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="rvt"
      assistantName="RVT Assistant"
      useChatHook={useRvtChat}
      configApiPath="/api/rvt-guide/config/"
      storageKey="rvt"
      permissionKey="webRvtAssistant"
      placeholder="請描述你的 RVT 問題..."
      collapsed={collapsed}
    />
  );
};

export default RvtAssistantChatPage;
```

### 2. Protocol Assistant（已實現）

```javascript
// frontend/src/pages/ProtocolAssistantChatPage.js
import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useProtocolAssistantChat from '../hooks/useProtocolAssistantChat';
import './ProtocolAssistantChatPage.css';

const ProtocolAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="protocol"
      assistantName="Protocol Assistant"
      useChatHook={useProtocolAssistantChat}
      configApiPath="/api/protocol-assistant/config/"
      storageKey="protocol-assistant"
      permissionKey="webProtocolAssistant"
      placeholder="請描述你的 Protocol 問題..."
      collapsed={collapsed}
    />
  );
};

export default ProtocolAssistantChatPage;
```

### 3. 未來新增的 QA Assistant（範例）

```javascript
// frontend/src/pages/QaAssistantChatPage.js
import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useQaChat from '../hooks/useQaChat';
import './QaAssistantChatPage.css';

const QaAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="qa"
      assistantName="QA Assistant"
      useChatHook={useQaChat}
      configApiPath="/api/qa-assistant/config/"
      storageKey="qa-assistant"
      permissionKey="webQaAssistant"
      placeholder="請描述你的 QA 問題..."
      collapsed={collapsed}
    />
  );
};

export default QaAssistantChatPage;
```

## 🔧 依賴條件

### 1. Chat Hook

每個 Assistant 需要實現自己的 Chat Hook：

```javascript
// frontend/src/hooks/useXxxChat.js
const useXxxChat = (conversationId, setConversationId, setMessages, user, currentUserId) => {
  // 實現聊天邏輯
  return {
    sendMessage,
    loading,
    loadingStartTime,
    stopRequest
  };
};
```

### 2. 配置 API

後端需要提供配置 API：

```python
# backend/api/views/...
@action(detail=False, methods=['get'])
def config(self, request):
    return Response({
        'success': True,
        'config': {
            'app_name': 'Xxx Assistant',
            # 其他配置...
        }
    })
```

### 3. 權限設定

需要在 UserProfile 和 UserContext 中設定權限：

```python
# backend/api/models.py
class UserProfile(models.Model):
    web_xxx_assistant = models.BooleanField(default=False)
```

```javascript
// frontend/src/contexts/UserContext.js
const permissions = {
  webXxxAssistant: profile?.web_xxx_assistant || false,
};
```

## 📊 代碼對比

### 重構前
```javascript
// RvtAssistantChatPage.js - 188 行
// ProtocolAssistantChatPage.js - 180 行
// 總計: 368 行重複代碼
```

### 重構後
```javascript
// CommonAssistantChatPage.jsx - 230 行（通用組件）
// RvtAssistantChatPage.js - 24 行（配置）
// ProtocolAssistantChatPage.js - 24 行（配置）
// 總計: 278 行（減少 90 行）
```

**新增 Assistant 時**：
- 重構前：需要複製 180+ 行代碼並修改
- 重構後：只需要 24 行配置代碼

## ✅ 優點

1. **代碼減少**：新增 Assistant 只需 10-20 行代碼
2. **統一維護**：修改 UI 只需改 CommonAssistantChatPage
3. **一致性**：所有 Assistant 的 UI 和 UX 完全一致
4. **易於測試**：只需測試一個通用組件
5. **快速開發**：新增 Assistant 只需幾分鐘

## 🔄 遷移步驟

### 現有 Assistant 遷移

1. **保留原有的 CSS 文件**（可選）
2. **創建新的頁面文件**（或重構現有文件）
3. **使用 CommonAssistantChatPage 並配置參數**
4. **測試功能是否正常**

### 新增 Assistant

1. **創建 Chat Hook**（`useXxxChat.js`）
2. **創建頁面文件**（複製範例並修改配置）
3. **添加路由**（`App.js`）
4. **設定權限**（後端 + 前端）
5. **測試完整流程**

## 🎨 自定義樣式

如果需要為特定 Assistant 添加自定義樣式，可以通過 CSS 類名：

```css
/* XxxAssistantChatPage.css */
.xxx-assistant-chat-page {
  /* 自定義樣式 */
}

.xxx-assistant-chat-page .chat-input-area {
  /* 自定義輸入框樣式 */
}
```

組件會自動添加類名：`{assistantType}-assistant-chat-page`

## 🚀 未來優化方向

### 階段 2：統一 Chat Hook
- 創建 `useAssistantChat` 通用 Hook
- 將 API 端點配置化
- 合併所有 Chat Hook

### 階段 3：配置驅動
- 創建 `assistantChatConfig.js` 配置文件
- 完全配置驅動，無需創建新文件
- 新增 Assistant 只需添加配置

## 📚 相關文檔

- **Assistant 範本指南**：`/docs/development/assistant-template-guide.md`
- **UI 組件規範**：`/docs/development/ui-component-guidelines.md`
- **前端開發指南**：`/docs/development/frontend-development.md`

---

**更新日期**: 2025-10-20  
**版本**: v1.0  
**作者**: AI Platform Team  
**狀態**: ✅ 階段 1 完成（通用組件）
