import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, DeleteOutlined } from '@ant-design/icons';
import './KnowIssueChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;

const KnowIssueChatPage = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: '你好！我是 Know Issue 助手。我可以幫你查詢測試相關的問題和解決方案。請告訴我你遇到的問題。',
      timestamp: new Date()
    }
  ]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    try {
      // 調用後端 API 查詢 Know Issue
      const response = await fetch('/api/dify/knowledge/retrieval/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          knowledge_id: 'know_issue_db',
          query: userMessage.content,
          retrieval_setting: {
            top_k: 3,
            score_threshold: 0.3
          }
        })
      });

      if (!response.ok) {
        throw new Error('API 請求失敗');
      }

      const data = await response.json();
      
      let assistantResponse = '';
      
      if (data.records && data.records.length > 0) {
        assistantResponse = '我找到了以下相關的 Know Issue 資訊：\n\n';
        
        data.records.forEach((record, index) => {
          assistantResponse += `**${index + 1}. ${record.title}**\n`;
          assistantResponse += `相關度分數: ${(record.score * 100).toFixed(1)}%\n`;
          assistantResponse += `${record.content}\n\n`;
          assistantResponse += '---\n\n';
        });
        
        assistantResponse += '如果你需要更多資訊或有其他問題，請繼續詢問。';
      } else {
        assistantResponse = '抱歉，我沒有找到與你的問題相關的 Know Issue 資訊。\n\n' +
                          '你可以嘗試：\n' +
                          '• 使用不同的關鍵字\n' +
                          '• 描述更具體的問題場景\n' +
                          '• 提及相關的產品型號或測試項目';
      }

      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: assistantResponse,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error calling API:', error);
      message.error('查詢失敗，請稍後再試');
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: '抱歉，查詢過程中出現錯誤。請檢查網路連接或稍後再試。',
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
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
        content: '對話已清空。我是 Know Issue 助手，請告訴我你遇到的問題。',
        timestamp: new Date()
      }
    ]);
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
          <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
            Know Issue Chat
          </Title>
          <Button 
            icon={<DeleteOutlined />} 
            onClick={clearChat}
            type="text"
            style={{ color: '#666' }}
          >
            清空對話
          </Button>
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
                  <Spin size="small" />
                  <Text style={{ marginLeft: '8px', color: '#666' }}>正在查詢...</Text>
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
            </Text>
          </div>
        </div>
      </Content>
    </Layout>
  );
};

export default KnowIssueChatPage;