import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography, Tag } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { useChatContext } from '../contexts/ChatContext';
import './KnowIssueChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;

// localStorage 相關常數
const STORAGE_KEY = 'know-issue-chat-messages';
const CONVERSATION_ID_KEY = 'know-issue-chat-conversation-id';
const MAX_STORAGE_DAYS = 7; // 最多保存 7 天
const MAX_MESSAGES = 200; // 最多保存 200 條消息

// localStorage 工具函數
const saveMessagesToStorage = (messages) => {
  try {
    const data = {
      messages: messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : msg.timestamp
      })),
      savedAt: new Date().toISOString()
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch (error) {
    console.warn('保存對話記錄失敗:', error);
  }
};

const loadMessagesFromStorage = () => {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) return null;
    
    const data = JSON.parse(stored);
    const savedAt = new Date(data.savedAt);
    const now = new Date();
    const daysDiff = (now - savedAt) / (1000 * 60 * 60 * 24);
    
    // 檢查是否過期
    if (daysDiff > MAX_STORAGE_DAYS) {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(CONVERSATION_ID_KEY);
      return null;
    }
    
    // 恢復消息並轉換時間戳
    const messages = data.messages.map(msg => ({
      ...msg,
      timestamp: new Date(msg.timestamp)
    }));
    
    // 如果消息太多，只保留最新的
    if (messages.length > MAX_MESSAGES) {
      return messages.slice(-MAX_MESSAGES);
    }
    
    return messages;
  } catch (error) {
    console.warn('讀取對話記錄失敗:', error);
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
};

const saveConversationId = (conversationId) => {
  try {
    if (conversationId) {
      localStorage.setItem(CONVERSATION_ID_KEY, conversationId);
    }
  } catch (error) {
    console.warn('保存對話ID失敗:', error);
  }
};

const loadConversationId = () => {
  try {
    return localStorage.getItem(CONVERSATION_ID_KEY) || '';
  } catch (error) {
    console.warn('讀取對話ID失敗:', error);
    return '';
  }
};

const clearStoredChat = () => {
  try {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(CONVERSATION_ID_KEY);
  } catch (error) {
    console.warn('清除對話記錄失敗:', error);
  }
};

const KnowIssueChatPage = ({ collapsed = false }) => {
  const { registerClearFunction, clearClearFunction } = useChatContext();
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
  const getInitialMessages = () => {
    const storedMessages = loadMessagesFromStorage();
    if (storedMessages && storedMessages.length > 0) {
      return storedMessages;
    }
    // 預設歡迎消息
    return [
      {
        id: 1,
        type: 'assistant',
        content: '你好！我是 Protocol Known Issue System 助手。我可以幫你查詢測試相關的問題和解決方案。請告訴我你遇到的問題。\n\n💡 提示：AI 分析知識庫可能需要 10-30 秒，請耐心等待。',
        timestamp: new Date()
      }
    ];
  };
  
  const [messages, setMessages] = useState(getInitialMessages);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [conversationId, setConversationId] = useState(loadConversationId);
  const [difyConfig, setDifyConfig] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // 自動保存消息到 localStorage
  useEffect(() => {
    if (messages.length > 0) {
      saveMessagesToStorage(messages);
    }
  }, [messages]);

  // 保存對話 ID
  useEffect(() => {
    if (conversationId) {
      saveConversationId(conversationId);
    }
  }, [conversationId]);

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

      // 檢查回應的 Content-Type
      const contentType = response.headers.get('content-type');
      
      let data;
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        // 如果不是 JSON，獲取文本內容並檢查
        const textResponse = await response.text();
        console.error('API 回應非 JSON 格式:', textResponse);
        
        if (textResponse.includes('<html>')) {
          throw new Error('API 請求被重定向到 HTML 頁面，可能是認證問題');
        } else {
          throw new Error(`API 回應格式錯誤: ${textResponse.substring(0, 100)}...`);
        }
      }
      
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
      let shouldRedirectToLogin = false;
      
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorText = '網路連接錯誤，請檢查網路連接';
      } else if (error.message.includes('Unexpected token') && error.message.includes('html')) {
        errorText = '用戶會話已過期，3秒後將自動跳轉到登入頁面';
        shouldRedirectToLogin = true;
      } else if (error.message.includes('認證問題') || error.message.includes('重定向到 HTML')) {
        errorText = '用戶認證已過期，3秒後將自動跳轉到登入頁面';
        shouldRedirectToLogin = true;
      } else if (error.message.includes('配置載入失敗')) {
        errorText = '系統配置載入失敗，請聯繫管理員';
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
      
      // 如果是認證錯誤，自動跳轉到登入頁面
      if (shouldRedirectToLogin) {
        setTimeout(() => {
          window.location.href = '/';
        }, 3000);
      }
      
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

  const clearChat = useCallback(() => {
    const defaultMessage = {
      id: 1,
      type: 'assistant',
      content: '對話已清空。我是 Protocol Known Issue System 助手，請告訴我你遇到的問題。',
      timestamp: new Date()
    };
    
    setMessages([defaultMessage]);
    setConversationId(''); // 重置對話 ID
    
    // 清除 localStorage 中的記錄
    clearStoredChat();
  }, []);

  // 將 clearChat 函數傳遞給父組件
  React.useEffect(() => {
    registerClearFunction(clearChat);
    return () => {
      clearClearFunction();
    };
  }, [registerClearFunction, clearClearFunction, clearChat]);

  const formatMessage = (content) => {
    // 完整的 Markdown 格式化
    return content
      .split('\n')
      .map((line, index) => {
        // 標題格式 (# ## ###)
        if (line.startsWith('###')) {
          return <Title key={index} level={5} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
            {line.replace(/^###\s*/, '')}
          </Title>;
        }
        if (line.startsWith('##')) {
          return <Title key={index} level={4} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
            {line.replace(/^##\s*/, '')}
          </Title>;
        }
        if (line.startsWith('#')) {
          return <Title key={index} level={3} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
            {line.replace(/^#\s*/, '')}
          </Title>;
        }
        
        // 粗體文字 (**text**)
        if (line.startsWith('**') && line.endsWith('**')) {
          return <Text key={index} strong style={{ display: 'block', marginBottom: '6px', fontSize: '14px' }}>
            {line.slice(2, -2)}
          </Text>;
        }
        
        // 水平分隔線
        if (line === '---' || line === '***') {
          return <hr key={index} style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #e8e8e8' }} />;
        }
        
        // 無序列表項目 (- 或 •)
        if (line.startsWith('- ') || line.startsWith('• ')) {
          const listContent = line.replace(/^[-•]\s*/, '');
          // 檢查是否包含粗體文字
          if (listContent.includes('**')) {
            const parts = listContent.split(/(\*\*.*?\*\*)/);
            return (
              <div key={index} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
                <span style={{ marginRight: '8px', color: '#666' }}>•</span>
                <Text style={{ flex: 1 }}>
                  {parts.map((part, partIndex) => 
                    part.startsWith('**') && part.endsWith('**') ? 
                      <Text key={partIndex} strong>{part.slice(2, -2)}</Text> : 
                      part
                  )}
                </Text>
              </div>
            );
          }
          return (
            <div key={index} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
              <span style={{ marginRight: '8px', color: '#666' }}>•</span>
              <Text style={{ flex: 1 }}>{listContent}</Text>
            </div>
          );
        }
        
        // 有序列表項目 (1. 2. 3.)
        if (/^\d+\.\s/.test(line)) {
          const match = line.match(/^(\d+)\.\s(.*)$/);
          if (match) {
            const [, number, listContent] = match;
            return (
              <div key={index} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
                <span style={{ marginRight: '8px', color: '#666', fontWeight: 'bold' }}>{number}.</span>
                <Text style={{ flex: 1 }}>{listContent}</Text>
              </div>
            );
          }
        }
        
        // 引用文字 (> text)
        if (line.startsWith('> ')) {
          return (
            <div key={index} style={{ 
              borderLeft: '4px solid #d9d9d9', 
              paddingLeft: '12px', 
              marginBottom: '8px',
              fontStyle: 'italic',
              color: '#666'
            }}>
              <Text>{line.slice(2)}</Text>
            </div>
          );
        }
        
        // 代碼塊 (```code```)
        if (line.startsWith('```') && line.endsWith('```') && line.length > 6) {
          return (
            <div key={index} style={{ 
              backgroundColor: '#f6f8fa', 
              border: '1px solid #e1e4e8',
              borderRadius: '6px',
              padding: '12px',
              margin: '8px 0',
              fontFamily: 'Monaco, Consolas, "Courier New", monospace',
              fontSize: '13px'
            }}>
              <Text code>{line.slice(3, -3)}</Text>
            </div>
          );
        }
        
        // 行內代碼 (`code`)
        if (line.includes('`')) {
          const parts = line.split(/(`[^`]*`)/);
          return (
            <Text key={index} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
              {parts.map((part, partIndex) => 
                part.startsWith('`') && part.endsWith('`') ? 
                  <Text key={partIndex} code>{part.slice(1, -1)}</Text> : 
                  part
              )}
            </Text>
          );
        }
        
        // 處理行內粗體文字
        if (line.includes('**')) {
          const parts = line.split(/(\*\*.*?\*\*)/);
          return (
            <Text key={index} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
              {parts.map((part, partIndex) => 
                part.startsWith('**') && part.endsWith('**') ? 
                  <Text key={partIndex} strong>{part.slice(2, -2)}</Text> : 
                  part
              )}
            </Text>
          );
        }
        
        // 處理行內斜體文字 (*text*)
        if (line.includes('*') && !line.includes('**')) {
          const parts = line.split(/(\*[^*]*\*)/);
          return (
            <Text key={index} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
              {parts.map((part, partIndex) => 
                part.startsWith('*') && part.endsWith('*') && part.length > 2 ? 
                  <Text key={partIndex} italic>{part.slice(1, -1)}</Text> : 
                  part
              )}
            </Text>
          );
        }
        
        // 普通文字
        return <Text key={index} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
          {line || '\u00A0'}
        </Text>;
      });
  };

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0', height: '100%', paddingTop: '64px' }}>
        {/* Messages Container */}
        <div className="messages-container" style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '8px 16px 16px 16px',  // 減少頂部 padding
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          height: 'calc(100vh - 64px - 100px)',  // 為固定的輸入區域預留空間
          paddingBottom: '100px'  // 為固定輸入框預留空間
        }}>
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

        {/* Input Area - 固定在底部 */}
        <div className="input-area" style={{
          position: 'fixed',
          bottom: 0,
          left: collapsed ? 80 : 250,
          right: 0,
          transition: 'left 0.2s',
          zIndex: 10
        }}>
          <div className="input-container">
            <TextArea
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={`請描述你遇到的問題... (按 Enter 發送，Shift + Enter 換行${difyConfig ? ` • 連接到: ${difyConfig.workspace}` : ''})`}
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
        </div>
      </Content>
    </Layout>
  );
};

export default KnowIssueChatPage;