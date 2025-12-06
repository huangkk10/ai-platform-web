/**
 * SAF Assistant 聊天頁面
 * =======================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 用於查詢 SAF 專案管理系統資訊
 * 
 * 權限：僅限 Admin 用戶可見（由 Sidebar.js 控制）
 */

import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useSafAssistantChat from '../hooks/useSafAssistantChat';
import '../components/markdown/ReactMarkdown.css';
import './SAfAssistantChatPage.css';

// SAF Assistant 專用歡迎訊息
// 🎯 使用列表格式而非表格（避免 Markdown 表格渲染問題）
const SAF_WELCOME_MESSAGE = `🔧 **歡迎使用 SAF Assistant！**

我是 SAF 專案管理系統的智能助手，可以協助你快速查詢專案相關資訊。

**📋 我可以幫助你：**
- 🏢 **查詢客戶專案** → 「WD 有哪些專案？」「Samsung 的專案列表」
- 🔌 **查詢控制器專案** → 「SM2264 用在哪些專案？」「哪些專案使用 SM2269？」
- 📊 **專案詳細資訊** → 「DEMETER 專案的詳細資訊」「查詢 Garuda 專案」
- 📈 **專案測試摘要** → 「DEMETER 的測試結果如何？」「TITAN 有多少測試通過？」
- 📁 **按類別查詢測試** → 「TITAN 的 Compliance 測試結果」「XX 專案的效能測試」
- 💾 **按容量查詢測試** → 「NV3 1TB 的測試狀況」「XX 512GB 測試結果」
- 🔢 **統計專案數量** → 「WD 有幾個專案？」「總共有多少專案？」
- 👥 **列出所有客戶** → 「有哪些客戶？」「列出所有客戶」
- 🎛️ **列出所有控制器** → 「有哪些控制器？」「系統支援哪些控制器」

**💡 提示**：直接用自然語言提問即可，系統會自動理解你的意圖！

現在就開始吧！有什麼 SAF 專案相關的問題需要查詢嗎？`;

const SAfAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="saf"
      assistantName="SAF Assistant"
      useChatHook={useSafAssistantChat}
      configApiPath={null}  // SAF 不需要額外配置 API
      storageKey="saf-assistant"
      permissionKey={null}  // 權限由 Sidebar.js 控制，這裡不再額外檢查
      placeholder="請輸入你的 SAF 查詢問題，例如：WD 有哪些專案？"
      welcomeMessage={SAF_WELCOME_MESSAGE}
      collapsed={collapsed}
      enableFileUpload={false}  // SAF 不需要檔案上傳功能
    />
  );
};

export default SAfAssistantChatPage;
