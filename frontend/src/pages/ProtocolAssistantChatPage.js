import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, message } from 'antd';
import { SendOutlined, MinusSquareFilled } from '@ant-design/icons';
import { useChatContext } from '../contexts/ChatContext';
import { useAuth } from '../contexts/AuthContext';
import MessageList from '../components/chat/MessageList';
import useMessageStorage from '../hooks/useMessageStorage';
import useProtocolAssistantChat from '../hooks/useProtocolAssistantChat';
import useMessageFeedback from '../hooks/useMessageFeedback';
import './ProtocolAssistantChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;

const ProtocolAssistantChatPage = ({ collapsed = false }) => {
  const { registerClearFunction, clearClearFunction } = useChatContext();
  const { user, hasPermission } = useAuth();
  
  const {
    messages,
    conversationId,
    currentUserId,
    setMessages,
    setConversationId,
    clearChat,
    checkUserSwitch,
    handleUserSwitch
  } = useMessageStorage(user, 'protocol-assistant');
  
  const [inputMessage, setInputMessage] = useState('');
  const [protocolConfig, setProtocolConfig] = useState(null);
  const messagesEndRef = useRef(null);
  
  const { sendMessage, loading, loadingStartTime, stopRequest } = useProtocolAssistantChat(
    conversationId,
    setConversationId,
    setMessages,
    user,
    currentUserId
  );
  
  const { feedbackStates, submitFeedback } = useMessageFeedback();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    loadProtocolConfig();
  }, []);

  const loadProtocolConfig = async () => {
    try {
      const response = await fetch('/api/protocol-assistant/config/', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setProtocolConfig(data.config);
        }
      }
    } catch (error) {
      console.error('載入 Protocol Assistant 配置失敗:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

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

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    await sendMessage(userMessage);
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

  // 權限檢查
  if (!hasPermission('webProtocolAssistant')) {
    return (
      <Layout style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', padding: '40px' }}>
          <h2>⚠️ 權限不足</h2>
          <p>您沒有使用 Protocol Assistant 的權限，請聯絡管理員。</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }} className="chat-page protocol-assistant-chat-page">
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0', height: '100%', paddingTop: '64px' }}>
        <MessageList
          messages={messages}
          loading={loading}
          loadingStartTime={loadingStartTime}
          feedbackStates={feedbackStates}
          onFeedback={submitFeedback}
          messagesEndRef={messagesEndRef}
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
              placeholder={`請描述你的 Protocol 問題... (按 Enter 發送，Shift + Enter 換行${protocolConfig ? ` • ${protocolConfig.app_name}` : ''})`}
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
              onClick={loading ? stopRequest : handleSendMessage}
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

export default ProtocolAssistantChatPage;
