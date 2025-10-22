// 聊天使用記錄工具函數
export const recordChatUsage = async (chatType, options = {}) => {
  try {
    const data = {
      chat_type: chatType,
      message_count: options.messageCount || 1,
      has_file_upload: options.hasFileUpload || false,
      response_time: options.responseTime || null,
      session_id: options.sessionId || getOrCreateSessionId(chatType)
    };

    const response = await fetch('/api/chat/record-usage/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(data)
    });

    if (response.ok) {
      const result = await response.json();
      return result.success;
    }
  } catch (error) {
    console.warn('記錄聊天使用情況失敗:', error);
  }
  return false;
};

// 獲取聊天使用統計
export const getChatStatistics = async (days = null) => {
  try {
    // days=null 或未指定時，查詢所有歷史資料
    const url = days ? `/api/chat/statistics/?days=${days}` : '/api/chat/statistics/';
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include'
    });

    if (response.ok) {
      const result = await response.json();
      if (result.success) {
        return result.data;
      }
    }
  } catch (error) {
    console.error('獲取聊天統計失敗:', error);
  }
  return null;
};

// 獲取或創建會話ID
const getOrCreateSessionId = (chatType) => {
  const sessionKey = `session_${chatType}`;
  let sessionId = localStorage.getItem(sessionKey);
  
  if (!sessionId) {
    sessionId = generateSessionId();
    localStorage.setItem(sessionKey, sessionId);
  }
  
  return sessionId;
};

// 生成會話ID
const generateSessionId = () => {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
};

// 聊天類型映射
export const CHAT_TYPES = {
  KNOW_ISSUE: 'know_issue_chat',
  LOG_ANALYZE: 'log_analyze_chat',
  RVT_ASSISTANT: 'rvt_assistant_chat'
};