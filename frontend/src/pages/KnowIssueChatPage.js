import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography, Tag } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, DeleteOutlined, InfoCircleOutlined } from '@ant-design/icons';
import './KnowIssueChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;

const KnowIssueChatPage = () => {
  // ... state variables ...

  // 動態載入提示組件
  const LoadingIndicator = () => {
    const [elapsedSeconds, setElapsedSeconds] = useState(0);

    useEffect(() => {
      if (!loading || !loadingStartTime) return;

      const interval = setInterval(() => {
        const elapsed = Math.floor((Date.now() - loadingStartTime) / 1000);
        setElapsedSeconds(elapsed);
      }, 1000);

      return () => clearInterval(interval);
    }, [loading, loadingStartTime]);

    const getMessage = () => {
      if (elapsedSeconds < 5) return 'AI 正在分析知識庫，請稍候...';
      if (elapsedSeconds < 15) return `AI 正在深度搜索知識庫... (${elapsedSeconds}s)`;
      if (elapsedSeconds < 30) return `AI 正在分析複雜查詢... (${elapsedSeconds}s)`;
      return `AI 仍在處理，請耐心等待... (${elapsedSeconds}s)`;
    };

    return (
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Spin size="small" />
        <Text style={{ marginLeft: '8px', color: '#666' }}>
          {getMessage()}
        </Text>
      </div>
    );
  };
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '你好！我是 Protocol Known Issue System 助手。我可以幫你查詢測試相關的問題和解決方案。請告訴我你遇到的問題。\n\n💡 提示：AI 分析知識庫可能需要 10-30 秒，請耐心等待。',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [conversationId, setConversationId] = useState('');
  const [difyConfig, setDifyConfig] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 載入 Dify 配置資訊
  useEffect(() => {
    loadDifyConfig();
  }, []);

  const loadDifyConfig = async () => {
    try {
      const response = await fetch('/api/dify/config/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setDifyConfig(data.config);
        }
      }
    } catch (error) {
      console.error('載入 Dify 配置失敗:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      // 使用新的 Dify Chat API
      const response = await fetch('/api/dify/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId
        })
      });

      const data = await response.json();
      
      if (response.ok && data.success) {
        // 更新對話 ID
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
        }

        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.answer,
          timestamp: new Date(),
          metadata: data.metadata,
          usage: data.usage,
          response_time: data.response_time
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        // 處理 API 返回的錯誤
        const errorMessage = data.error || `API 請求失敗: ${response.status}`;
        throw new Error(errorMessage);
      }

    } catch (error) {
      console.error('Error calling Dify Chat API:', error);
      
      let errorText = '未知錯誤';
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorText = '網路連接錯誤，請檢查網路連接';
      } else if (error.message.includes('504')) {
        errorText = 'AI 分析超時，可能是因為查詢較複雜，請稍後再試或簡化問題描述';
      } else if (error.message.includes('503')) {
        errorText = 'Dify 智能助手服務暫時不可用，請稍後再試';
      } else if (error.message.includes('408')) {
        errorText = 'AI 分析時間較長，請稍後再試。複雜問題可能需要更多時間分析';
      } else if (error.message.includes('timeout') || error.message.includes('超時')) {
        errorText = 'AI 分析超時，可能是查詢較複雜。建議簡化問題描述後重試';
      } else {
        errorText = error.message;
      }
      
      message.error(`查詢失敗: ${errorText}`);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `抱歉，查詢過程中出現錯誤：${errorText}\n\n請檢查網路連接或稍後再試。`,
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const clearChat = () => {
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: '對話已清空。我是 Protocol Known Issue System 助手，請告訴我你遇到的問題。',
        timestamp: new Date()
      }
    ]);
    setConversationId(''); // 重置對話 ID
  };

  const formatMessage = (content) => {
    // 簡單的 Markdown 格式化
    return content
      .split('\n')
      .map((line, index) => {
        if (line.startsWith('**') && line.endsWith('**')) {
          return <Text key={index} strong style={{ display: 'block', marginBottom: '4px' }}>
            {line.slice(2, -2)}
          </Text>;
        }
        if (line === '---') {
          return <hr key={index} style={{ margin: '12px 0', border: 'none', borderTop: '1px solid #e8e8e8' }} />;
        }
        if (line.startsWith('• ')) {
          return <Text key={index} style={{ display: 'block', marginLeft: '16px', marginBottom: '4px' }}>
            {line}
          </Text>;
        }
        return <Text key={index} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
          {line || '\u00A0'}
        </Text>;
      });
  };

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0' }}>
        {/* Header */}
        <div className="chat-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
              Know Issue Chat
            </Title>
            {difyConfig && (
              <Tag icon={<InfoCircleOutlined />} color="blue">
                {difyConfig.app_name}
              </Tag>
            )}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            {conversationId && (
              <Tag color="green" style={{ fontSize: '11px' }}>
                對話中: {conversationId.slice(-8)}
              </Tag>
            )}
            <Button 
              icon={<DeleteOutlined />} 
              onClick={clearChat}
              type="text"
              style={{ color: '#666' }}
            >
              清空對話
            </Button>
          </div>
        </div>

        {/* Messages Container */}
        <div className="messages-container">
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.type}`}>
              <div className="message-content">
                <Avatar 
                  icon={msg.type === 'user' ? <UserOutlined /> : <RobotOutlined />}
                  style={{ 
                    backgroundColor: msg.type === 'user' ? '#1890ff' : '#52c41a',
                    flexShrink: 0
                  }}
                />
                <Card 
                  className={`message-card ${msg.type}`}
                  bodyStyle={{ padding: '12px 16px' }}
                >
                  <div className="message-text">
                    {formatMessage(msg.content)}
                  </div>
                  <div className="message-time">
                    {msg.timestamp.toLocaleTimeString('zh-TW', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                    {msg.response_time && (
                      <Text type="secondary" style={{ marginLeft: '8px', fontSize: '11px' }}>
                        ({msg.response_time.toFixed(1)}s)
                      </Text>
                    )}
                    {msg.usage && msg.usage.total_tokens && (
                      <Text type="secondary" style={{ marginLeft: '8px', fontSize: '11px' }}>
                        {msg.usage.total_tokens} tokens
                      </Text>
                    )}
                  </div>
                </Card>
              </div>
            </div>
          ))}
          
          {loading && (
            <div className="message-wrapper assistant">
              <div className="message-content">
                <Avatar 
                  icon={<RobotOutlined />}
                  style={{ backgroundColor: '#52c41a', flexShrink: 0 }}
                />
                <Card 
                  className="message-card assistant"
                  bodyStyle={{ padding: '12px 16px' }}
                >
                  <LoadingIndicator />
                </Card>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-area">
          <div className="input-container">
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="請描述你遇到的問題..."
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
              style={{ borderRadius: '20px', resize: 'none' }}
            />
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!inputMessage.trim()}
              style={{ 
                borderRadius: '50%', 
                width: '40px', 
                height: '40px',
                marginLeft: '12px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}
            />
          </div>
          <div className="input-hint">
            <Text type="secondary" style={{ fontSize: '12px' }}>
              按 Enter 發送，Shift + Enter 換行 
              {difyConfig && (
                <span style={{ marginLeft: '16px' }}>
                  • 連接到: {difyConfig.workspace}
                </span>
              )}
            </Text>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default KnowIssueChatPage;