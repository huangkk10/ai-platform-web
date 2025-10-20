/**
 * Protocol Assistant 聊天頁面
 * ===========================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 只需配置參數即可
 */

import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useProtocolAssistantChat from '../hooks/useProtocolAssistantChat';
import './ProtocolAssistantChatPage.css';

// Protocol Assistant 專用歡迎訊息
const PROTOCOL_WELCOME_MESSAGE = '🛠️ 歡迎使用 Protocol Assistant！我是你的 Protocol 測試專家助手，可以協助你解決 Protocol 相關的問題。\n\n**我可以幫助你：**\n- Protocol 測試流程指導\n- 故障排除和問題診斷\n- Protocol 工具使用方法\n\n現在就開始吧！有什麼 Protocol 相關的問題需要協助嗎？';

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
      welcomeMessage={PROTOCOL_WELCOME_MESSAGE}
      collapsed={collapsed}
    />
  );
};

export default ProtocolAssistantChatPage;
