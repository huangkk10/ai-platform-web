/**
 * RVT Assistant 聊天頁面
 * ======================
 * 
 * 使用通用 CommonAssistantChatPage 組件
 * 只需配置參數即可
 */

import React from 'react';
import CommonAssistantChatPage from '../components/chat/CommonAssistantChatPage';
import useRvtChat from '../hooks/useRvtChat';
import './RvtAssistantChatPage.css';

// RVT Assistant 專用歡迎訊息
const RVT_WELCOME_MESSAGE = '🛠️ 歡迎使用 RVT Assistant！我是你的 RVT 測試專家助手，可以協助你解決 RVT 相關的問題。\n\n**我可以幫助你：**\n- RVT 測試流程指導\n- 故障排除和問題診斷\n- RVT 工具使用方法\n\n現在就開始吧！有什麼 RVT 相關的問題需要協助嗎？';

const RvtAssistantChatPage = ({ collapsed = false }) => {
  return (
    <CommonAssistantChatPage
      assistantType="rvt"
      assistantName="RVT Assistant"
      useChatHook={useRvtChat}
      configApiPath="/api/rvt-guide/config/"
      storageKey="rvt"
      permissionKey="webRVTAssistant"
      placeholder="請描述你的 RVT 問題..."
      welcomeMessage={RVT_WELCOME_MESSAGE}
      collapsed={collapsed}
    />
  );
};

export default RvtAssistantChatPage;
