import React, { useState, useRef, useEffect } from 'react';
import { Layout, Input, Button, Card, Avatar, message, Spin, Typography, Tooltip } from 'antd';
import { 
  SendOutlined, 
  MinusSquareFilled,
  UserOutlined, 
  ToolOutlined,
  LikeOutlined,
  DislikeOutlined,
  LikeFilled,
  DislikeFilled
} from '@ant-design/icons';
import { useChatContext } from '../contexts/ChatContext';
import { useAuth } from '../contexts/AuthContext';
import { recordChatUsage, CHAT_TYPES } from '../utils/chatUsage';
// 新的模組化組件和 hooks
import MessageFormatter from '../components/chat/MessageFormatter';
import useMessageStorage from '../hooks/useMessageStorage';
import './RvtAssistantChatPage.css';

const { Content } = Layout;
const { TextArea } = Input;
const { Text } = Typography;


const RvtAssistantChatPage = ({ collapsed = false }) => {
  const { registerClearFunction, clearClearFunction } = useChatContext();
  const { user } = useAuth();
  
  // 使用新的 useMessageStorage hook
  const {
    messages,
    conversationId,
    currentUserId,
    setMessages,
    setConversationId,
    clearChat,
    checkUserSwitch,
    handleUserSwitch
  } = useMessageStorage(user);
  
  // 其他状态
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const [rvtConfig, setRvtConfig] = useState(null);
  const [feedbackStates, setFeedbackStates] = useState({});
  const messagesEndRef = useRef(null);
  const abortControllerRef = useRef(null);
  
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

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

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

    // 🚨 檢查用戶是否在發送消息時發生切換
    const sendTimeUserId = user?.id || null;
    if (checkUserSwitch(sendTimeUserId)) {
      handleUserSwitch(sendTimeUserId);
      message.warning('偵測到用戶切換，請重新發送您的消息。');
      return;
    }

    // 现在每个用户都有独立的存储，不需要额外的安全检查

    // console.log('📤 發送消息:', {
    //   message: inputMessage.trim(),
    //   currentUserId,
    //   sendTimeUserId,
    //   user: user?.username || 'guest',
    //   userObject: user,
    //   conversationId,
    //   timestamp: new Date().toISOString()
    // });

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

    // 創建新的 AbortController
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      // console.log('🌐 準備發送 API 請求到:', '/api/rvt-guide/chat/');
      // console.log('🔑 使用對話ID:', conversationId || '(空 - 將創建新對話)');
      
      // 使用 RVT Guide Chat API (注意：此API有@csrf_exempt，不需要CSRF令牌)
      const response = await fetch('/api/rvt-guide/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'include',
        signal: abortController.signal, // 添加 abort signal
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId || ''  // 使用正確的 state 變數
        })
      });

      // 檢查回應狀態
      // console.log('📡 API 回應狀態:', {
      //   status: response.status,
      //   statusText: response.statusText,
      //   ok: response.ok,
      //   headers: Object.fromEntries(response.headers.entries())
      // });
      
      if (!response.ok) {
        if (response.status === 404) {
          // 404 錯誤 - 立即清除對話ID並重試
          // console.log('🔄 404錯誤，清除對話ID並準備重試');
          setConversationId('');
          throw new Error('conversation_expired_404');
        }
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
          response_time: data.response_time,
          message_id: data.message_id // 從 API 回應中獲取 message_id
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
          setConversationId('');
          
          // 檢查是否是用戶切換導致的問題
          const currentUser = user?.username || '訪客';
          // console.log('🔄 對話過期偵測，當前用戶:', currentUser, '- 將重新開始對話');
          
          // 提示用戶重新發送，同時清除對話ID讓下次請求自動創建新對話
          throw new Error(`🔄 用戶切換後對話已重置，請重新發送您的問題。\n\n💡 提示：下一條消息將自動開始新對話\n當前用戶: ${currentUser}`);
        }
        
        throw new Error(errorMessage);
      }

    } catch (error) {
      console.error('❌ RVT Guide Chat API 錯誤:', {
        error,
        message: error.message,
        stack: error.stack,
        name: error.name,
        currentUserId,
        conversationId,
        userLoggedIn: !!user?.id
      });
      
      // 檢查是否是用戶主動取消
      if (error.name === 'AbortError') {
        const cancelMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: '⏹️ 請求已被取消。\n\n您可以重新提問或修改問題。',
          timestamp: new Date()
        };
        setMessages(prev => [...prev, cancelMessage]);
        return;
      }
      
      // 🔄 404 錯誤自動重試邏輯
      if (error.message.includes('conversation_expired_404')) {
        // console.log('🔄 執行404自動重試...', {
        //   currentUser: user?.username || '訪客',
        //   userId: user?.id || null,
        //   conversationId: conversationId,
        //   requestUrl: '/api/rvt-guide/chat/',
        //   retryTime: new Date().toISOString()
        // });
        
        try {
          // 等待一小段時間讓認證狀態穩定
          await new Promise(resolve => setTimeout(resolve, 500));
          
          // 用空的conversation_id重新發送請求
          const retryResponse = await fetch('/api/rvt-guide/chat/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-Requested-With': 'XMLHttpRequest',
            },
            credentials: 'include',
            body: JSON.stringify({
              message: userMessage.content,
              conversation_id: '' // 空對話ID，創建新對話
            })
          });

          // console.log('🔄 重試回應詳情:', {
          //   status: retryResponse.status,
          //   statusText: retryResponse.statusText,
          //   ok: retryResponse.ok,
          //   headers: Object.fromEntries(retryResponse.headers.entries()),
          //   url: retryResponse.url
          // });

          if (retryResponse.ok) {
            const retryData = await retryResponse.json();
            // console.log('🔄 重試回應數據:', retryData);
            
            if (retryData.success) {
              // console.log('✅ 自動重試成功');
              
              // 更新對話ID
              setConversationId(retryData.conversation_id);
              
              const assistantMessage = {
                id: Date.now() + 1,
                type: 'assistant',
                content: `🔄 已自動重新開始對話\n\n${retryData.answer}`,
                timestamp: new Date(),
                metadata: retryData.metadata,
                usage: retryData.usage,
                response_time: retryData.response_time,
                message_id: retryData.message_id
              };

              setMessages(prev => [...prev, assistantMessage]);
              
              // 記錄使用情況
              recordChatUsage(CHAT_TYPES.RVT_ASSISTANT, {
                messageCount: 1,
                hasFileUpload: false,
                responseTime: retryData.response_time,
                sessionId: retryData.conversation_id
              });
              
              // 成功重試，直接返回不顯示錯誤
              return;
            } else {
              // console.log('❌ 重試時 API 返回 success: false:', retryData);
            }
          } else {
            // console.log('❌ 重試請求失敗:', retryResponse.status, retryResponse.statusText);
            
            // 如果重試也返回404，說明可能是認證問題
            if (retryResponse.status === 404) {
              const errorText = await retryResponse.text();
              // console.log('❌ 重試404錯誤內容:', errorText);
            }
          }
        } catch (retryError) {
          console.error('❌ 自動重試失敗詳情:', {
            error: retryError,
            message: retryError.message,
            name: retryError.name,
            stack: retryError.stack
          });
        }
      }
      
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
      } else if (error.message.includes('guest_auth_issue')) {
        errorText = '🔄 檢測到認證狀態問題，但 RVT Assistant 支援訪客使用。系統將自動重試...';
        // 可以考慮自動重試邏輯
      } else if (error.message.includes('403') || error.message.includes('Forbidden')) {
        errorText = '訪客可以使用 RVT Assistant，無需登入。請稍後再試';
      } else if (error.message.includes('401') || error.message.includes('Unauthorized')) {
        errorText = '用戶會話可能已過期，但可以繼續使用 RVT Assistant';
      } else if (error.message.includes('conversation_expired_404')) {
        errorText = '🔄 對話已自動重置，請重新發送您的消息。';
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
      abortControllerRef.current = null;
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleStopRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      message.info('正在停止當前任務...');
    }
  };

  const handleMessageFeedback = async (messageId, isHelpful) => {
    try {
      const response = await fetch('/api/rvt-analytics/feedback/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          message_id: messageId,
          is_helpful: isHelpful
        })
      });

      const data = await response.json();
      
      if (data.success) {
        // 更新反饋狀態
        setFeedbackStates(prev => ({
          ...prev,
          [messageId]: isHelpful
        }));
        
        message.success(isHelpful ? '感謝您的正面反饋！' : '感謝您的反饋，我們會持續改進！');
      } else {
        message.error(`反饋提交失敗: ${data.error}`);
      }
    } catch (error) {
      console.error('提交反饋失敗:', error);
      message.error('反饋提交失敗，請稍後再試');
    }
  };

  // 使用模組化的圖片載入函數，不需要重新定義
  
  // 將 clearChat 函數傳遞給父組件
  React.useEffect(() => {
    registerClearFunction(clearChat);
    return () => {
      clearClearFunction();
    };
  }, [registerClearFunction, clearClearFunction, clearChat]);

  // 消息格式化邏輯已移至 MessageFormatter 組件

  // 格式化函數已移至 MessageFormatter 組件

  return (
    <Layout style={{ height: '100vh', background: '#f5f5f5' }} className="chat-page rvt-assistant-chat-page">
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
                  styles={{ body: { padding: '12px 16px' } }}
                >
                  <div className="message-text chat-message-content">
                    <MessageFormatter 
                      content={msg.content}
                      metadata={msg.metadata}
                      messageType={msg.type}
                    />
                  </div>
                  
                  {/* AI 回覆的反饋按鈕 */}
                  {msg.type === 'assistant' && msg.message_id && (
                    <div className="message-feedback" style={{ 
                      marginTop: '8px', 
                      display: 'flex', 
                      gap: '8px', 
                      alignItems: 'center' 
                    }}>
                      <Tooltip title="回應良好" placement="top">
                        <Button
                          type="text"
                          size="small"
                          icon={feedbackStates[msg.message_id] === true ? <LikeFilled /> : <LikeOutlined />}
                          onClick={() => handleMessageFeedback(msg.message_id, true)}
                          style={{ 
                            color: feedbackStates[msg.message_id] === true ? '#52c41a' : '#8c8c8c',
                            backgroundColor: 'transparent',
                            border: 'none'
                          }}
                        />
                      </Tooltip>
                      <Tooltip title="回應不佳" placement="top">
                        <Button
                          type="text"
                          size="small"
                          icon={feedbackStates[msg.message_id] === false ? <DislikeFilled /> : <DislikeOutlined />}
                          onClick={() => handleMessageFeedback(msg.message_id, false)}
                          style={{ 
                            color: feedbackStates[msg.message_id] === false ? '#ff4d4f' : '#8c8c8c',
                            backgroundColor: 'transparent',
                            border: 'none'
                          }}
                        />
                      </Tooltip>
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
                  icon={<ToolOutlined />}
                  style={{ backgroundColor: '#52c41a', flexShrink: 0 }}
                />
                <Card 
                  className="message-card assistant"
                  styles={{ body: { padding: '12px 16px' } }}
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
              onClick={loading ? handleStopRequest : handleSendMessage}
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

export default RvtAssistantChatPage;