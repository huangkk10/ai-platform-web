/**
 * SAF Assistant 聊天頁面
 * ==================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 用於查詢 SAF 專案管理系統資訊
 * 
 * 權限：僅限 Admin 用戶可見（由 Sidebar.js 控制）
 * 
 * 🆕 2024-12-18 更新：使用折疊式歡迎引導組件
 */

import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import SafWelcomeGuide from '../components/chat/SafWelcomeGuide';
import useSafAssistantChat from '../hooks/useSafAssistantChat';
import '../components/markdown/ReactMarkdown.css';
import './SAfAssistantChatPage.css';

// 🆕 保留純文字歡迎訊息作為 fallback（用於訊息儲存）
const SAF_WELCOME_MESSAGE_FALLBACK = `🔧 歡迎使用 SAF Assistant！我是 SAF 專案管理系統的智能助手，可以協助你快速查詢專案相關資訊。`;

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
      welcomeMessage={SAF_WELCOME_MESSAGE_FALLBACK}
      welcomeComponent={SafWelcomeGuide}  // 🆕 使用折疊式歡迎組件
      collapsed={collapsed}
      enableFileUpload={false}  // SAF 不需要檔案上傳功能
    />
  );
};

export default SAfAssistantChatPage;
