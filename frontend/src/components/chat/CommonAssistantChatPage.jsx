/**
 * 通用 Assistant 聊天頁面組件
 * =============================
 * 
 * 用途：所有 Assistant (RVT, Protocol, QA 等) 的統一聊天介面
 * 優點：
 * - 統一的 UI 和 UX
 * - 集中維護，修改一處即可影響所有 Assistant
 * - 新增 Assistant 只需配置，無需重寫頁面
 * 
 * 使用範例：
 * ```jsx
 * <CommonAssistantChatPage
 *   assistantType="rvt"
 *   assistantName="RVT Assistant"
 *   useChatHook={useRvtChat}
 *   configApiPath="/api/rvt-guide/config/"
 *   storageKey="rvt"
 *   permissionKey="webRvtAssistant"
 *   placeholder="請描述你的 RVT 問題..."
 *   collapsed={collapsed}
 * />
 * ```
 */

import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, message } from 'antd';
import { SendOutlined, MinusSquareFilled } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { useChatContext } from '../../contexts/ChatContext';
import { useAuth } from '../../contexts/AuthContext';
import MessageList from './MessageList';
import useMessageStorage from '../../hooks/useMessageStorage';
import useMessageFeedback from '../../hooks/useMessageFeedback';

const { Content } = Layout;
const { TextArea } = Input;

const CommonAssistantChatPage = ({
  assistantType,
  assistantName,
  storageKey,
  useChatHook,
  configApiPath,
  permissionKey,
  placeholder,
  welcomeMessage,
  collapsed = false
}) => {
  const { user, permissions } = useAuth();
  const navigate = useNavigate();
  const { registerClearFunction, clearClearFunction } = useChatContext();
  
  const {
    messages,
    conversationId,
    currentUserId,
    setMessages,
    setConversationId,
    clearChat,
    checkUserSwitch,
    handleUserSwitch
  } = useMessageStorage(user, storageKey, welcomeMessage);
  
  const [inputMessage, setInputMessage] = useState('');
  const [assistantConfig, setAssistantConfig] = useState(null);
  const messagesEndRef = useRef(null);
  
  // 使用傳入的 Chat Hook
  const { sendMessage, loading, loadingStartTime, stopRequest } = useChatHook(
    conversationId,
    setConversationId,
    setMessages,
    user,
    currentUserId
  );
  
  const { feedbackStates, submitFeedback } = useMessageFeedback();
  
  // 權限檢查函數
  const hasPermission = (key) => {
    return permissions[key] === true;
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 載入 Assistant 配置
  useEffect(() => {
    loadAssistantConfig();
  }, []);

  const loadAssistantConfig = async () => {
    try {
      const response = await fetch(configApiPath, {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setAssistantConfig(data.config);
        }
      }
    } catch (error) {
      console.error(`載入 ${assistantName} 配置失敗:`, error);
    }
  };

  const handleSendMessage = async () => {
    console.log('🎬 [CommonAssistantChatPage] handleSendMessage 開始執行');
    console.log('  - inputMessage:', inputMessage);
    console.log('  - assistantType:', assistantType);
    
    if (!inputMessage.trim()) {
      console.log('⚠️ [CommonAssistantChatPage] 訊息為空，返回');
      return;
    }

    const sendTimeUserId = user?.id || null;
    if (checkUserSwitch(sendTimeUserId)) {
      handleUserSwitch(sendTimeUserId);
      message.warning('偵測到用戶切換，請重新發送您的消息。');
      return;
    }

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    console.log('📨 [CommonAssistantChatPage] 創建 userMessage:', userMessage);
    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    
    console.log('🔗 [CommonAssistantChatPage] 調用 sendMessage');
    console.log('  - sendMessage 函數:', typeof sendMessage);
    try {
      await sendMessage(userMessage);
      console.log('✅ [CommonAssistantChatPage] sendMessage 執行完成');
    } catch (error) {
      console.error('❌ [CommonAssistantChatPage] sendMessage 執行錯誤:', error);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  useEffect(() => {
    registerClearFunction(clearChat);
    return () => clearClearFunction();
  }, [registerClearFunction, clearClearFunction, clearChat]);

  // 權限檢查（如果 permissionKey 為 null，則跳過權限檢查，允許訪客使用）
  if (permissionKey && !hasPermission(permissionKey)) {
    return (
      <Layout style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>⚠️ 權限不足</h2>
          <p>您沒有使用 {assistantName} 的權限，請聯絡管理員。</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }} className={`chat-page ${assistantType}-assistant-chat-page`}>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0', height: '100%', paddingTop: '64px' }}>
        <MessageList
          messages={messages}
          loading={loading}
          loadingStartTime={loadingStartTime}
          feedbackStates={feedbackStates}
          onFeedback={submitFeedback}
          messagesEndRef={messagesEndRef}
          assistantName={assistantName}
        />
        <div className="input-area" style={{
          position: 'fixed',
          bottom: 0,
          left: collapsed ? 80 : 300,
          right: 0,
          transition: 'left 0.2s',
          zIndex: 10,
          background: 'white',
          borderTop: '1px solid #e8e8e8',
          padding: '16px 24px',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.06)'
        }}>
          <div className="input-container" style={{
            display: 'flex',
            alignItems: 'flex-end',
            gap: '8px',
            maxWidth: '800px',
            margin: '0 auto'
          }}>
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`${placeholder} (按 Enter 發送，Shift + Enter 換行${assistantConfig ? ` • ${assistantConfig.app_name}` : ''})`}
              autoSize={{ minRows: 1, maxRows: 12 }}
              disabled={loading}
              className="chat-input-area"
              style={{ 
                borderRadius: '20px', 
                resize: 'none',
                flex: 1,
                padding: '12px 16px',
                fontSize: '14px',
                border: '1px solid #d9d9d9',
                transition: 'all 0.3s'
              }}
            />
            <button
              onClick={() => {
                console.log('🖱️ [CommonAssistantChatPage] 發送按鈕被點擊');
                console.log('  - loading:', loading);
                console.log('  - inputMessage:', inputMessage);
                if (loading) {
                  console.log('  - 執行 stopRequest');
                  stopRequest();
                } else {
                  console.log('  - 執行 handleSendMessage');
                  handleSendMessage();
                }
              }}
              disabled={!loading && !inputMessage.trim()}
              title={loading ? "點擊停止當前任務" : "發送消息"}
              style={{ 
                borderRadius: '50%', 
                width: '40px', 
                height: '40px',
                marginLeft: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: loading ? '#595959' : (!inputMessage.trim() ? '#d9d9d9' : '#1890ff'),
                color: '#fff',
                border: `1px solid ${loading ? '#595959' : (!inputMessage.trim() ? '#d9d9d9' : '#1890ff')}`,
                cursor: (loading || inputMessage.trim()) ? 'pointer' : 'not-allowed',
                fontSize: '16px',
                transition: 'all 0.3s ease',
                outline: 'none'
              }}
            >
              {loading ? <MinusSquareFilled /> : <SendOutlined />}
            </button>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default CommonAssistantChatPage;
