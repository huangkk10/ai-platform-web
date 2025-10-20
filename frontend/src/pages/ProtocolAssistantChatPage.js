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
    <Layout className="protocol-assistant-chat-page" style={{ height: '100vh', overflow: 'hidden' }}>
      <Content style={{ 
        display: 'flex', 
        flexDirection: 'column',
        height: '100%',
        padding: '16px',
        backgroundColor: '#f5f5f5'
      }}>
        {/* 聊天訊息區域 */}
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px',
          backgroundColor: 'white',
          borderRadius: '8px',
          marginBottom: '16px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <MessageList 
            messages={messages}
            feedbackStates={feedbackStates}
            onFeedback={submitFeedback}
            assistantName="Protocol Assistant"
          />
          <div ref={messagesEndRef} />
        </div>

        {/* 輸入區域 */}
        <div style={{ 
          backgroundColor: 'white',
          padding: '16px',
          borderRadius: '8px',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
        }}>
          <div style={{ display: 'flex', gap: '8px', alignItems: 'flex-end' }}>
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="請輸入您的 Protocol 相關問題..."
              autoSize={{ minRows: 2, maxRows: 6 }}
              disabled={loading}
              style={{ 
                flex: 1,
                fontFamily: "'Microsoft JhengHei', sans-serif",
                fontSize: '14px'
              }}
            />
            <div style={{ display: 'flex', gap: '8px' }}>
              {loading && (
                <button
                  onClick={stopRequest}
                  className="stop-button"
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#ff4d4f',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px'
                  }}
                >
                  <MinusSquareFilled />
                  停止生成
                </button>
              )}
              <button
                onClick={handleSendMessage}
                disabled={loading || !inputMessage.trim()}
                style={{
                  padding: '8px 16px',
                  backgroundColor: loading || !inputMessage.trim() ? '#d9d9d9' : '#1890ff',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: loading || !inputMessage.trim() ? 'not-allowed' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '4px'
                }}
              >
                <SendOutlined />
                發送
              </button>
            </div>
          </div>
          
          {protocolConfig && (
            <div style={{ marginTop: '8px', fontSize: '12px', color: '#666' }}>
              💡 提示：AI 分析可能需要 10-30 秒，請耐心等待
            </div>
          )}
        </div>
      </Content>
    </Layout>
  );
};

export default ProtocolAssistantChatPage;
