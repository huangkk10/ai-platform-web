import React from 'react';
import { Card, Avatar, Button, Tooltip, Typography, Image } from 'antd';
import {
  UserOutlined,
  ToolOutlined,
  LikeOutlined,
  DislikeOutlined,
  LikeFilled,
  DislikeFilled,
  FileImageOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import MessageFormatter from './MessageFormatter';
import LoadingIndicator from './LoadingIndicator';

const { Text } = Typography;

/**
 * MessageList 組件
 * 顯示聊天訊息列表，包含用戶訊息和 AI 回覆
 * 
 * @param {Array} messages - 訊息列表
 * @param {boolean} loading - 是否正在載入
 * @param {number} loadingStartTime - 載入開始時間
 * @param {Object} feedbackStates - 反饋狀態對象
 * @param {Function} onFeedback - 反饋處理函數
 * @param {Object} messagesEndRef - 訊息列表底部 ref
 * @param {string} assistantName - Assistant 名稱（用於載入指示器）
 * @param {React.Component} welcomeComponent - 🆕 自訂歡迎訊息組件（可選）
 * @param {Function} onExampleClick - 🆕 點擊範例問句的回調函數（可選）
 */
const MessageList = ({
  messages = [],
  loading = false,
  loadingStartTime = null,
  feedbackStates = {},
  onFeedback,
  messagesEndRef,
  assistantName = 'Assistant',
  welcomeComponent: WelcomeComponent = null,
  onExampleClick = null
}) => {
  return (
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
              {/* 🖼️ 圖片附件顯示 */}
              {msg.type === 'user' && msg.attachment && (
                <div style={{ 
                  marginBottom: msg.content ? '8px' : 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  {msg.attachment.isImage && msg.attachment.imageUrl ? (
                    <Image
                      src={msg.attachment.imageUrl}
                      alt={msg.attachment.fileName}
                      style={{
                        maxWidth: '200px',
                        maxHeight: '150px',
                        borderRadius: '8px',
                        objectFit: 'cover'
                      }}
                      preview={{
                        mask: '點擊查看'
                      }}
                    />
                  ) : (
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '6px',
                      padding: '6px 10px',
                      backgroundColor: 'rgba(255,255,255,0.2)',
                      borderRadius: '6px',
                      fontSize: '12px'
                    }}>
                      {msg.attachment.isImage ? <FileImageOutlined /> : <FileTextOutlined />}
                      <span>{msg.attachment.fileName}</span>
                    </div>
                  )}
                </div>
              )}
              
              {/* 訊息文字內容 */}
              <div className="message-text markdown-preview-content">
                {/* 🆕 如果是歡迎訊息(id=1)且有自訂組件，使用自訂組件渲染 */}
                {msg.id === 1 && msg.type === 'assistant' && WelcomeComponent ? (
                  <WelcomeComponent onExampleClick={onExampleClick} />
                ) : (
                  <MessageFormatter 
                    content={msg.content}
                    metadata={msg.metadata}
                    messageType={msg.type}
                  />
                )}
              </div>
              
              {/* AI 回覆的反饋按鈕 */}
              {msg.type === 'assistant' && msg.message_id && onFeedback && (
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
                      onClick={() => onFeedback(msg.message_id, true)}
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
                      onClick={() => onFeedback(msg.message_id, false)}
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
                            <LoadingIndicator 
                loading={loading} 
                loadingStartTime={loadingStartTime}
                serviceName={assistantName}
              />
            </Card>
          </div>
        </div>
      )}
      
      <div ref={messagesEndRef} />
    </div>
  );
};

// 🎯 使用 React.memo 優化，避免輸入框變化時重新渲染整個訊息列表
export default React.memo(MessageList, (prevProps, nextProps) => {
  // 只有當訊息列表、loading 狀態或反饋狀態改變時才重新渲染
  return (
    prevProps.messages.length === nextProps.messages.length &&
    prevProps.loading === nextProps.loading &&
    prevProps.feedbackStates === nextProps.feedbackStates &&
    // 簡單檢查最後一條訊息是否相同
    (prevProps.messages.length === 0 || 
     prevProps.messages[prevProps.messages.length - 1]?.id === 
     nextProps.messages[nextProps.messages.length - 1]?.id)
  );
});
