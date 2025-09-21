import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography, Tag, Table } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, InfoCircleOutlined, ToolOutlined } from '@ant-design/icons';
import { useChatContext } from '../contexts/ChatContext';
import { recordChatUsage, CHAT_TYPES } from '../utils/chatUsage';
import './RvtAssistantChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;

// localStorage 相關常數
const STORAGE_KEY = 'rvt-assistant-chat-messages';
const CONVERSATION_ID_KEY = 'rvt-assistant-chat-conversation-id';
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

const RvtAssistantChatPage = ({ collapsed = false }) => {
  const { registerClearFunction, clearClearFunction } = useChatContext();
  
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
      if (elapsedSeconds < 5) return 'RVT Assistant 正在分析您的問題...';
      if (elapsedSeconds < 15) return `RVT Assistant 正在查找相關資料... (${elapsedSeconds}s)`;
      if (elapsedSeconds < 30) return `RVT Assistant 正在深度分析... (${elapsedSeconds}s)`;
      return `RVT Assistant 仍在處理，請耐心等待... (${elapsedSeconds}s)`;
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
        content: '🛠️ 歡迎使用 RVT Assistant！\n\n我是你的 RVT 測試專家助手，可以協助你解決 RVT 相關的問題。\n\n**我可以幫助你：**\n- RVT 測試流程指導\n- 故障排除和問題診斷\n- Jenkins 和 Ansible 配置建議\n- 最佳實踐建議\n- RVT 工具使用方法\n\n**提問建議：**\n• 具體描述你遇到的問題\n• 提供錯誤訊息或日誌片段\n• 說明你的環境配置\n\n現在就開始吧！有什麼 RVT 相關的問題需要協助嗎？',
        timestamp: new Date()
      }
    ];
  };
  
  const [messages, setMessages] = useState(getInitialMessages);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [conversationId, setConversationId] = useState(loadConversationId);
  const [rvtConfig, setRvtConfig] = useState(null);
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

  // 載入 RVT Guide 配置資訊
  useEffect(() => {
    loadRvtConfig();
  }, []);

  const loadRvtConfig = async () => {
    try {
      const response = await fetch('/api/rvt-guide/config/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include'
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          setRvtConfig(data.config);
        }
      }
    } catch (error) {
      console.error('載入 RVT Guide 配置失敗:', error);
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
      // 使用 RVT Guide Chat API
      const response = await fetch('/api/rvt-guide/chat/', {
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

      // 檢查回應狀態
      if (!response.ok) {
        if (response.status === 403 || response.status === 401) {
          throw new Error('guest_auth_issue');
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

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
          throw new Error('html_response');
        } else {
          throw new Error(`API 回應格式錯誤: ${textResponse.substring(0, 100)}...`);
        }
      }
      
      if (response.ok && data.success) {
        // 更新對話 ID
        if (data.conversation_id) {
          setConversationId(data.conversation_id);
          saveConversationId(data.conversation_id);
        }
        
        // 如果有警告信息，顯示給用戶
        let assistantContent = data.answer;
        if (data.warning) {
          assistantContent = `⚠️ ${data.warning}\n\n${assistantContent}`;
        }

        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: assistantContent,
          timestamp: new Date(),
          metadata: data.metadata,
          usage: data.usage,
          response_time: data.response_time
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // 記錄使用情況
        recordChatUsage(CHAT_TYPES.RVT_ASSISTANT, {
          messageCount: 1,
          hasFileUpload: false,
          responseTime: data.response_time,
          sessionId: data.conversation_id
        });
      } else {
        // 處理 API 返回的錯誤
        const errorMessage = data.error || `API 請求失敗: ${response.status}`;
        
        // 檢查是否是對話過期錯誤
        if (errorMessage.includes('Conversation Not Exists') || 
            errorMessage.includes('對話已過期') || 
            errorMessage.includes('conversation_id') ||
            errorMessage.includes('404')) {
          // 清除無效的對話ID
          console.log('清除無效的對話ID:', conversationId);
          setConversationId('');
          localStorage.removeItem(CONVERSATION_ID_KEY);
          
          // 提示用戶重新發送
          throw new Error('對話已過期，請重新發送您的問題。系統將自動開始新對話。');
        }
        
        throw new Error(errorMessage);
      }

    } catch (error) {
      console.error('Error calling RVT Guide Chat API:', error);
      
      let errorText = '未知錯誤';
      
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorText = '網路連接錯誤，請檢查網路連接';
      } else if (error.message.includes('Unexpected token') && error.message.includes('html')) {
        errorText = '服務器回應格式錯誤，請稍後再試';
      } else if (error.message.includes('認證問題') || error.message.includes('重定向到 HTML')) {
        errorText = '用戶會話可能已過期，但可以繼續使用聊天功能';
      } else if (error.message.includes('配置載入失敗')) {
        errorText = '系統配置載入失敗，請聯繫管理員';
      } else if (error.message.includes('504')) {
        errorText = 'RVT Assistant 分析超時，可能是因為查詢較複雜，請稍後再試或簡化問題描述';
      } else if (error.message.includes('503')) {
        errorText = 'RVT Assistant 服務暫時不可用，請稍後再試';
      } else if (error.message.includes('408')) {
        errorText = 'RVT Assistant 分析時間較長，請稍後再試';
      } else if (error.message.includes('timeout') || error.message.includes('超時')) {
        errorText = 'RVT Assistant 分析超時，建議簡化問題描述後重試';
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        errorText = '訪客可以使用 RVT Assistant，無需登入。請稍後再試';
      } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        errorText = '用戶會話可能已過期，但可以繼續使用 RVT Assistant';
      } else if (error.message.includes('對話已過期') || error.message.includes('重新發送您的問題')) {
        errorText = error.message;
      } else {
        errorText = error.message;
      }
      
      message.error(`查詢失敗: ${errorText}`);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `❌ 抱歉，查詢過程中出現錯誤：${errorText}\n\n請稍後再試，或嘗試：\n• 簡化問題描述\n• 提供更具體的錯誤信息\n• 分段提問複雜問題`,
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
      content: '🛠️ 歡迎使用 RVT Assistant！\n\n我是你的 RVT 測試專家助手，可以協助你解決 RVT 相關的問題。\n\n**我可以幫助你：**\n- RVT 測試流程指導\n- 故障排除和問題診斷\n- Jenkins 和 Ansible 配置建議\n- 最佳實踐建議\n- RVT 工具使用方法\n\n**提問建議：**\n• 具體描述你遇到的問題\n• 提供錯誤訊息或日誌片段\n• 說明你的環境配置\n\n現在就開始吧！有什麼 RVT 相關的問題需要協助嗎？',
      timestamp: new Date()
    };
    
    setMessages([defaultMessage]);
    setConversationId('');
    
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
    const lines = content.split('\n');
    const result = [];
    let i = 0;
    
    while (i < lines.length) {
      const line = lines[i];
      
      // 檢查是否為表格開始（包含 | 符號的行）
      if (line.includes('|') && i + 1 < lines.length && lines[i + 1].includes('|')) {
        // 可能是表格，嘗試解析
        const tableLines = [];
        let j = i;
        
        // 收集所有連續的表格行
        while (j < lines.length && lines[j].includes('|')) {
          tableLines.push(lines[j]);
          j++;
        }
        
        // 檢查是否為有效的表格（至少有標題行和分隔行）
        if (tableLines.length >= 2) {
          try {
            // 解析表格
            const headerRow = tableLines[0].split('|').map(cell => cell.trim()).filter(cell => cell);
            const separatorRow = tableLines[1];
            
            // 檢查分隔行是否符合表格格式
            if (separatorRow.includes('-') || separatorRow.includes(':')) {
              const dataRows = tableLines.slice(2).map(row => 
                row.split('|').map(cell => cell.trim()).filter(cell => cell)
              ).filter(row => row.length > 0);
              
              // 創建 Ant Design Table 的數據結構
              const columns = headerRow.map((header, index) => ({
                title: header,
                dataIndex: `col${index}`,
                key: `col${index}`,
                render: (text) => {
                  // 處理單元格內的 Markdown 格式
                  if (typeof text === 'string') {
                    if (text.startsWith('**') && text.endsWith('**')) {
                      return <Text strong>{text.slice(2, -2)}</Text>;
                    }
                    if (text.startsWith('`') && text.endsWith('`')) {
                      return <Text code>{text.slice(1, -1)}</Text>;
                    }
                  }
                  return text;
                }
              }));
              
              const dataSource = dataRows.map((row, rowIndex) => {
                const rowData = { key: rowIndex };
                row.forEach((cell, cellIndex) => {
                  rowData[`col${cellIndex}`] = cell;
                });
                return rowData;
              });
              
              result.push(
                <div key={`table-${i}`} style={{ margin: '12px 0' }}>
                  <Table 
                    columns={columns}
                    dataSource={dataSource}
                    pagination={false}
                    size="small"
                    bordered
                    style={{ fontSize: '13px' }}
                  />
                </div>
              );
              
              i = j; // 跳過已處理的表格行
              continue;
            }
          } catch (error) {
            console.warn('表格解析失敗:', error);
          }
        }
      }
      
      // 標題格式 (# ## ###)
      if (line.startsWith('###')) {
        result.push(<Title key={i} level={5} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
          {line.replace(/^###\s*/, '')}
        </Title>);
      }
      else if (line.startsWith('##')) {
        result.push(<Title key={i} level={4} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
          {line.replace(/^##\s*/, '')}
        </Title>);
      }
      else if (line.startsWith('#')) {
        result.push(<Title key={i} level={3} style={{ display: 'block', marginBottom: '8px', marginTop: '12px' }}>
          {line.replace(/^#\s*/, '')}
        </Title>);
      }
      // 粗體文字 (**text**)
      else if (line.startsWith('**') && line.endsWith('**')) {
        result.push(<Text key={i} strong style={{ display: 'block', marginBottom: '6px', fontSize: '14px' }}>
          {line.slice(2, -2)}
        </Text>);
      }
      // 水平分隔線
      else if (line === '---' || line === '***') {
        result.push(<hr key={i} style={{ margin: '16px 0', border: 'none', borderTop: '1px solid #e8e8e8' }} />);
      }
      // 無序列表項目 (- 或 •)
      else if (line.startsWith('- ') || line.startsWith('• ')) {
        const listContent = line.replace(/^[-•]\s*/, '');
        // 檢查是否包含粗體文字
        if (listContent.includes('**')) {
          const parts = listContent.split(/(\*\*.*?\*\*)/);
          result.push(
            <div key={i} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
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
        } else {
          result.push(
            <div key={i} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
              <span style={{ marginRight: '8px', color: '#666' }}>•</span>
              <Text style={{ flex: 1 }}>{listContent}</Text>
            </div>
          );
        }
      }
      // 有序列表項目 (1. 2. 3.)
      else if (/^\d+\.\s/.test(line)) {
        const match = line.match(/^(\d+)\.\s(.*)$/);
        if (match) {
          const [, number, listContent] = match;
          result.push(
            <div key={i} style={{ display: 'flex', marginLeft: '16px', marginBottom: '4px' }}>
              <span style={{ marginRight: '8px', color: '#666', fontWeight: 'bold' }}>{number}.</span>
              <Text style={{ flex: 1 }}>{listContent}</Text>
            </div>
          );
        }
      }
      // 引用文字 (> text)
      else if (line.startsWith('> ')) {
        result.push(
          <div key={i} style={{ 
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
      else if (line.startsWith('```') && line.endsWith('```') && line.length > 6) {
        result.push(
          <div key={i} style={{ 
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
      else if (line.includes('`')) {
        const parts = line.split(/(`[^`]*`)/);
        result.push(
          <Text key={i} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
            {parts.map((part, partIndex) => 
              part.startsWith('`') && part.endsWith('`') ? 
                <Text key={partIndex} code>{part.slice(1, -1)}</Text> : 
                part
            )}
          </Text>
        );
      }
      // 處理行內粗體文字
      else if (line.includes('**')) {
        const parts = line.split(/(\*\*.*?\*\*)/);
        result.push(
          <Text key={i} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
            {parts.map((part, partIndex) => 
              part.startsWith('**') && part.endsWith('**') ? 
                <Text key={partIndex} strong>{part.slice(2, -2)}</Text> : 
                part
            )}
          </Text>
        );
      }
      // 處理行內斜體文字 (*text*)
      else if (line.includes('*') && !line.includes('**')) {
        const parts = line.split(/(\*[^*]*\*)/);
        result.push(
          <Text key={i} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
            {parts.map((part, partIndex) => 
              part.startsWith('*') && part.endsWith('*') && part.length > 2 ? 
                <Text key={partIndex} italic>{part.slice(1, -1)}</Text> : 
                part
            )}
          </Text>
        );
      }
      // 普通文字
      else {
        result.push(<Text key={i} style={{ display: 'block', marginBottom: line.trim() ? '4px' : '8px' }}>
          {line || '\u00A0'}
        </Text>);
      }
      
      i++;
    }
    
    return result;
  };

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }}>
      <Content style={{ display: 'flex', flexDirection: 'column', padding: '0', height: '100%', paddingTop: '64px' }}>

        {/* Messages Container */}
        <div className="messages-container" style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          height: 'calc(100vh - 64px - 100px)',
          paddingBottom: '100px',
          background: '#f5f5f5',
          backgroundImage: 
            'radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.05) 0%, transparent 50%), radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.05) 0%, transparent 50%)'
        }}>
          {messages.map((msg) => (
            <div key={msg.id} className={`message-wrapper ${msg.type}`}>
              <div className="message-content">
                <Avatar 
                  icon={msg.type === 'user' ? <UserOutlined /> : <ToolOutlined />}
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
                  icon={<ToolOutlined />}
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
              placeholder={`請描述你的 RVT 問題... (按 Enter 發送，Shift + Enter 換行${rvtConfig ? ` • ${rvtConfig.app_name}` : ''})`}
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
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

export default RvtAssistantChatPage;