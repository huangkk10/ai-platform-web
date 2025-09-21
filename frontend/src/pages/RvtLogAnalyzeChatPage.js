import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography, Tag, Table, Upload, Image, Popover } from 'antd';
import { SendOutlined, UserOutlined, RobotOutlined, InfoCircleOutlined, PlusOutlined, FileImageOutlined, DeleteOutlined, FileTextOutlined } from '@ant-design/icons';
import { useChatContext } from '../contexts/ChatContext';
import { recordChatUsage, CHAT_TYPES } from '../utils/chatUsage';
import './RvtLogAnalyzeChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text, Title } = Typography;

// localStorage 相關常數 - 使用不同的鍵值以區分不同聊天頁面
const STORAGE_KEY = 'rvt-log-analyze-chat-messages';
const CONVERSATION_ID_KEY = 'rvt-log-analyze-chat-conversation-id';
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

const RvtLogAnalyzeChatPage = ({ collapsed = false }) => {
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
      if (elapsedSeconds < 5) return 'AI 正在分析 RVT 日誌，請稍候...';
      if (elapsedSeconds < 15) return `AI 正在深度分析 RVT 日誌... (${elapsedSeconds}s)`;
      if (elapsedSeconds < 30) return `AI 正在分析複雜的 RVT 查詢... (${elapsedSeconds}s)`;
      return `AI 仍在處理 RVT 日誌，請耐心等待... (${elapsedSeconds}s)`;
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
        content: '你好！我是 RVT Assistant 智能助手 🤖\n\n我專門提供以下服務：\n• **RVT 用戶指南諮詢** - 回答 RVT 相關問題和操作指導\n• **RVT 日誌分析** - 分析日誌文件，查找錯誤模式和解決方案\n• **問題診斷與建議** - 提供 RVT 相關的技術支援和最佳實務\n\n您可以：\n📝 直接詢問 RVT 相關問題\n📁 上傳日誌檔案進行深度分析\n🔍 尋求故障排除的協助\n\n💡 提示：AI 分析可能需要 10-30 秒，請耐心等待\n📁 支援檔案：.txt 和 .log 文字檔案（最大 10MB）',
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
  const [uploadedFiles, setUploadedFiles] = useState([]); // 修改：只存儲文字檔案
  const [uploading, setUploading] = useState(false); // 上傳狀態
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null); // 文件輸入引用

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
    // 檢查是否有消息或檔案
    if (!inputMessage.trim() && uploadedFiles.length === 0) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputMessage.trim() || (
        uploadedFiles.length > 0 
          ? '請分析這個 RVT 日誌檔案' 
          : ''
      ),
      timestamp: new Date(),
      files: uploadedFiles.length > 0 ? [...uploadedFiles] : undefined
    };

    setMessages(prev => [...prev, userMessage]);
    const currentMessage = inputMessage.trim();
    const currentFiles = [...uploadedFiles];
    
    setInputMessage('');
    setUploadedFiles([]); // 清除上傳的檔案
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      let response, data;

      // 如果有檔案，使用文件分析 API
      if (currentFiles.length > 0) {
        // 對每個檔案進行分析
        for (let i = 0; i < currentFiles.length; i++) {
          const file = currentFiles[i];
          
          // 文字檔案處理
          const blob = new Blob([file.content], { type: 'text/plain' });
          
          // 創建 FormData
          const formData = new FormData();
          formData.append('file', blob, file.name);
          if (currentMessage) {
            formData.append('message', currentMessage);
          }
          if (conversationId) {
            formData.append('conversation_id', conversationId);
          }

          // 發送到文件分析 API
          response = await fetch('/api/dify/chat-with-file/', {
            method: 'POST',
            credentials: 'include',
            body: formData
          });

          // 只處理第一個檔案的響應
          if (i === 0) {
            break;
          }
        }
      } else {
        // 沒有檔案，使用普通聊天 API
        response = await fetch('/api/dify/chat/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          credentials: 'include',
          body: JSON.stringify({
            message: currentMessage,
            conversation_id: conversationId
          })
        });
      }

      // 檢查回應狀態
      if (!response.ok) {
        if (response.status === 403 || response.status === 401) {
          throw new Error('guest_auth_issue');
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 解析回應
      const contentType = response.headers.get('content-type');
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
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
        
        // 如果有警告信息（比如對話過期重新開始），顯示給用戶
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
          response_time: data.response_time,
          file_info: data.file_info // 如果是文件分析，包含文件信息
        };

        setMessages(prev => [...prev, assistantMessage]);
        
        // 記錄使用情況
        recordChatUsage(CHAT_TYPES.RVT_LOG_ANALYZE, {
          messageCount: 1,
          hasFileUpload: currentFiles.length > 0,
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
      console.error('Error calling Dify Chat API:', error);
      
      let errorText = '未知錯誤';
      
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        errorText = '網路連接錯誤，請檢查網路連接';
      } else if (error.message === 'guest_auth_issue') {
        errorText = '訪客模式可以正常使用聊天功能，請稍後再試';
      } else if (error.message === 'html_response') {
        errorText = '服務器回應格式異常，請稍後再試';
      } else if (error.message.includes('Unexpected token') && error.message.includes('html')) {
        errorText = '服務器回應格式錯誤，請稍後再試';
      } else if (error.message.includes('認證問題') || error.message.includes('重定向到 HTML')) {
        errorText = '用戶會話可能已過期，但可以繼續使用聊天功能';
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
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        errorText = '訪客可以使用聊天功能，無需登入。請稍後再試';
      } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        errorText = '用戶會話可能已過期，但可以繼續使用聊天功能';
      } else if (error.message.includes('對話已過期') || error.message.includes('重新發送您的問題')) {
        errorText = error.message; // 直接使用上面設定的錯誤消息
      } else {
        errorText = error.message;
      }
      
      message.error(`查詢失敗: ${errorText}`);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `抱歉，查詢過程中出現錯誤：${errorText}\n\n請稍後再試，或嘗試簡化問題描述。`,
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

  // 處理檔案上傳（僅支援 .txt 和 .log 檔案）
  const handleFileUpload = (file) => {
    // 檢查文件類型 - 只允許 .txt 和 .log 檔案
    const isValidType = file.name.toLowerCase().endsWith('.txt') || 
                       file.name.toLowerCase().endsWith('.log') ||
                       file.type === 'text/plain';
    
    if (!isValidType) {
      message.error('僅支援 .txt 和 .log 檔案！');
      return false;
    }

    // 檢查文件大小（限制為10MB）
    const isLt10M = file.size / 1024 / 1024 < 10;
    if (!isLt10M) {
      message.error('檔案大小不能超過 10MB！');
      return false;
    }

    console.log('開始上傳 RVT 日誌檔案:', file.name);
    setUploading(true);

    // 創建臨時加載項目
    const tempFileData = {
      uid: `temp-${Date.now()}`,
      name: file.name,
      status: 'uploading',
      file: file,
      content: null,
      size: file.size
    };

    console.log('添加加載狀態檔案:', tempFileData);
    // 立即添加加載狀態的檔案
    setUploadedFiles(prev => [...prev, tempFileData]);

    // 讀取文字檔案內容
    const reader = new FileReader();
    reader.onload = (e) => {
      console.log('RVT 日誌檔案讀取完成');
      const finalFileData = {
        uid: Date.now().toString(),
        name: file.name,
        status: 'done',
        file: file,
        content: e.target.result, // 文字內容
        size: file.size
      };

      // 移除臨時項目並添加完成的項目
      setUploadedFiles(prev => [
        ...prev.filter(f => f.uid !== tempFileData.uid),
        finalFileData
      ]);
      setUploading(false);
      message.success('RVT 日誌檔案添加成功！');
    };

    reader.onerror = () => {
      console.error('檔案讀取失敗');
      // 移除臨時項目
      setUploadedFiles(prev => prev.filter(f => f.uid !== tempFileData.uid));
      setUploading(false);
      message.error('檔案讀取失敗！');
    };

    // 讀取為文字
    reader.readAsText(file);
    
    // 阻止默認的上傳行為
    return false;
  };

  // 移除上傳的檔案
  const removeUploadedFile = (uid) => {
    setUploadedFiles(prev => prev.filter(f => f.uid !== uid));
    message.success('檔案已移除');
  };

  // 觸發文件選擇
  const triggerFileUpload = () => {
    fileInputRef.current?.click();
  };

  // 處理文件選擇
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileUpload(file);
    }
    // 清空 input value，允許重複選擇同一文件
    e.target.value = '';
  };

  const clearChat = useCallback(() => {
    const defaultMessage = {
      id: 1,
      type: 'assistant',
      content: '你好！我是 RVT Assistant 智能助手 🤖\n\n我專門提供以下服務：\n• **RVT 用戶指南諮詢** - 回答 RVT 相關問題和操作指導\n• **RVT 日誌分析** - 分析日誌文件，查找錯誤模式和解決方案\n• **問題診斷與建議** - 提供 RVT 相關的技術支援和最佳實務\n\n您可以：\n📝 直接詢問 RVT 相關問題\n📁 上傳日誌檔案進行深度分析\n🔍 尋求故障排除的協助\n\n💡 提示：AI 分析可能需要 10-30 秒，請耐心等待\n📁 支援檔案：.txt 和 .log 文字檔案（最大 10MB）',
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
          padding: '8px 16px 16px 16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '12px',
          height: 'calc(100vh - 64px - 100px)',
          paddingBottom: '100px'
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
                  {/* 如果用戶消息包含檔案，先顯示檔案 */}
                  {msg.type === 'user' && msg.files && msg.files.length > 0 && (
                    <div style={{ marginBottom: '12px' }}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                        {msg.files.map((file) => (
                          <div key={file.uid}>
                            {/* 文字檔案顯示 */}
                            <div
                              style={{
                                padding: '8px 12px',
                                backgroundColor: 'rgba(255, 255, 255, 0.1)',
                                border: '1px solid rgba(255, 255, 255, 0.3)',
                                borderRadius: '6px',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                color: 'white',
                                fontSize: '12px'
                              }}
                            >
                              <FileTextOutlined style={{ color: 'white' }} />
                              <span>{file.name}</span>
                              <span style={{ opacity: 0.7 }}>({(file.size / 1024).toFixed(1)} KB)</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  <div className="message-text">
                    {formatMessage(msg.content)}
                  </div>
                  
                  {/* 如果是文件分析結果，顯示文件信息 */}
                  {msg.file_info && (
                    <div style={{ 
                      marginTop: '8px', 
                      padding: '6px 8px', 
                      background: 'rgba(0, 0, 0, 0.05)', 
                      borderRadius: '4px',
                      fontSize: '11px',
                      color: '#666'
                    }}>
                      📁 已分析 RVT 日誌文件: {msg.file_info.name} ({(msg.file_info.size / 1024).toFixed(1)} KB)
                    </div>
                  )}
                  
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
          left: collapsed ? 80 : 300,
          right: 0,
          transition: 'left 0.2s',
          zIndex: 10
        }}>
          <div className="input-container">
            {/* 隱藏的文件輸入 */}
            <input
              ref={fileInputRef}
              type="file"
              accept=".txt,.log"
              onChange={handleFileSelect}
              style={{ display: 'none' }}
            />
            
            {/* 包含檔案上傳按鈕和預覽的輸入框 */}
            <div className="input-with-buttons">
              <Button
                type="text"
                icon={<PlusOutlined />}
                onClick={triggerFileUpload}
                loading={uploading}
                disabled={loading}
                className="file-upload-btn-inside"
                title="添加 RVT 日誌檔案 (.txt, .log)"
              />
              
              {/* 檔案預覽區域 - 在輸入框內 */}
              {uploadedFiles.length > 0 && (
                <div className="file-preview-inline">
                  {uploadedFiles.map((file) => (
                    <div key={file.uid} className="file-preview-item-inline">
                      {file.status === 'uploading' ? (
                        // 加載狀態的骨架屏
                        <div className="file-loading-skeleton">
                          <Spin size="small" />
                          <Text style={{ fontSize: '9px', color: '#1890ff', marginTop: '2px', fontWeight: 'bold' }}>處理中...</Text>
                        </div>
                      ) : (
                        // 正常的檔案預覽
                        <>
                          {/* 文字檔案預覽 */}
                          <div
                            style={{
                              width: 32,
                              height: 32,
                              backgroundColor: '#f0f8ff',
                              border: '1px solid #1890ff',
                              borderRadius: '4px',
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'center',
                              fontSize: '12px',
                              fontWeight: 'bold',
                              color: '#1890ff',
                              cursor: 'pointer'
                            }}
                            title={`RVT 日誌檔案: ${file.name}`}
                          >
                            <FileTextOutlined />
                          </div>
                          <Button
                            type="text"
                            icon={<DeleteOutlined />}
                            size="small"
                            onClick={() => removeUploadedFile(file.uid)}
                            className="file-remove-btn-inline"
                          />
                        </>
                      )}
                    </div>
                  ))}
                </div>
              )}
              
              <TextArea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder={`請描述你的 RVT 日誌問題或上傳日誌檔案... (按 Enter 發送，Shift + Enter 換行${difyConfig ? ` • 連接到: ${difyConfig.workspace}` : ''})`}
                autoSize={{ minRows: 1, maxRows: 4 }}
                disabled={loading}
                className="textarea-with-button"
              />
            </div>
            
            <Button
              type="primary"
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!inputMessage.trim() && uploadedFiles.length === 0}
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

export default RvtLogAnalyzeChatPage;