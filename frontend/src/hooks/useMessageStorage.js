import { useState, useEffect, useCallback } from 'react';

// localStorage 相關常數 - 基于用户ID隔离
const STORAGE_KEY_PREFIX = 'rvt-assistant-chat-messages';
const CONVERSATION_ID_KEY_PREFIX = 'rvt-assistant-chat-conversation-id';
const MAX_STORAGE_DAYS = 7; // 最多保存 7 天
const MAX_MESSAGES = 200; // 最多保存 200 條消息

// 预设欢迎消息常量
const DEFAULT_WELCOME_MESSAGE = {
  id: 1,
  type: 'assistant',
  content: '🛠️ 歡迎使用 RVT Assistant！我是你的 RVT 測試專家助手，可以協助你解決 RVT 相關的問題。\n\n**我可以幫助你：**\n- RVT 測試流程指導\n- 故障排除和問題診斷\n- RVT 工具使用方法\n\n現在就開始吧！有什麼 RVT 相關的問題需要協助嗎？',
  timestamp: new Date()
};

/**
 * 获取用户特定的存储键
 * @param {string|number} userId - 用户ID
 * @returns {string} - 存储键
 */
const getUserStorageKey = (userId) => `${STORAGE_KEY_PREFIX}-${userId || 'guest'}`;

/**
 * 获取用户特定的对话ID键
 * @param {string|number} userId - 用户ID
 * @returns {string} - 对话ID键
 */
const getUserConversationKey = (userId) => `${CONVERSATION_ID_KEY_PREFIX}-${userId || 'guest'}`;

/**
 * 保存消息到 localStorage
 * @param {Array} messages - 消息列表
 * @param {string|number} userId - 用户ID
 */
const saveMessagesToStorage = (messages, userId) => {
  try {
    const storageKey = getUserStorageKey(userId);
    const data = {
      messages: messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : msg.timestamp
      })),
      savedAt: new Date().toISOString(),
      userId: userId || 'guest'
    };
    localStorage.setItem(storageKey, JSON.stringify(data));
    // console.log(`💾 保存对话记录 - 用户: ${userId || 'guest'}, 消息数: ${messages.length}`);
  } catch (error) {
    console.warn('保存對話記錄失敗:', error);
  }
};

/**
 * 从 localStorage 加载消息
 * @param {string|number} userId - 用户ID
 * @returns {Array|null} - 消息列表或null
 */
const loadMessagesFromStorage = (userId) => {
  try {
    const storageKey = getUserStorageKey(userId);
    const stored = localStorage.getItem(storageKey);
    if (!stored) {
      // console.log(`📂 未找到对话记录 - 用户: ${userId || 'guest'}`);
      return null;
    }
    
    const data = JSON.parse(stored);
    const savedAt = new Date(data.savedAt);
    const now = new Date();
    const daysDiff = (now - savedAt) / (1000 * 60 * 60 * 24);
    
    // 检查数据是否属于正确的用户
    if (data.userId !== (userId || 'guest')) {
      // console.log(`🔄 用户不匹配，清除旧数据 - 存储用户: ${data.userId}, 当前用户: ${userId || 'guest'}`);
      localStorage.removeItem(storageKey);
      return null;
    }
    
    // 檢查是否過期
    if (daysDiff > MAX_STORAGE_DAYS) {
      // console.log(`⏰ 对话记录已过期 - 用户: ${userId || 'guest'}`);
      localStorage.removeItem(storageKey);
      localStorage.removeItem(getUserConversationKey(userId));
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
    
    // console.log(`📖 载入对话记录 - 用户: ${userId || 'guest'}, 消息数: ${messages.length}`);
    return messages;
  } catch (error) {
    console.warn('讀取對話記錄失敗:', error);
    const storageKey = getUserStorageKey(userId);
    localStorage.removeItem(storageKey);
    return null;
  }
};

/**
 * 保存对话ID
 * @param {string} conversationId - 对话ID
 * @param {string|number} userId - 用户ID
 */
const saveConversationId = (conversationId, userId) => {
  try {
    if (conversationId) {
      const conversationKey = getUserConversationKey(userId);
      localStorage.setItem(conversationKey, conversationId);
      // console.log(`💾 保存对话ID - 用户: ${userId || 'guest'}, ID: ${conversationId}`);
    }
  } catch (error) {
    console.warn('保存對話ID失敗:', error);
  }
};

/**
 * 加载对话ID
 * @param {string|number} userId - 用户ID
 * @returns {string} - 对话ID
 */
const loadConversationId = (userId) => {
  try {
    const conversationKey = getUserConversationKey(userId);
    const conversationId = localStorage.getItem(conversationKey) || '';
    if (conversationId) {
      // console.log(`📖 载入对话ID - 用户: ${userId || 'guest'}, ID: ${conversationId}`);
    }
    return conversationId;
  } catch (error) {
    console.warn('讀取對話ID失敗:', error);
    return '';
  }
};

/**
 * 清除用户的聊天记录
 * @param {string|number} userId - 用户ID
 */
const clearStoredChat = (userId) => {
  try {
    const storageKey = getUserStorageKey(userId);
    const conversationKey = getUserConversationKey(userId);
    localStorage.removeItem(storageKey);
    localStorage.removeItem(conversationKey);
    // console.log(`🗑️ 清除用户数据 - 用户: ${userId || 'guest'}`);
  } catch (error) {
    console.warn('清除對話記錄失敗:', error);
  }
};

/**
 * 获取初始消息
 * @param {string|number} userId - 用户ID
 * @returns {Array} - 消息列表
 */
const getInitialMessages = (userId) => {
  const storedMessages = loadMessagesFromStorage(userId);
  if (storedMessages && storedMessages.length > 0) {
    return storedMessages;
  }
  // 使用預設歡迎消息常量
  return [{ ...DEFAULT_WELCOME_MESSAGE, timestamp: new Date() }];
};

/**
 * useMessageStorage Hook - 管理消息存储和用户切换
 * @param {Object} user - 用户对象
 * @returns {Object} - 包含消息状态和操作函数的对象
 */
const useMessageStorage = (user) => {
  const [messages, setMessages] = useState(() => getInitialMessages(user?.id));
  const [conversationId, setConversationId] = useState('');
  const [currentUserId, setCurrentUserId] = useState(null);

  // 监听用户状态变化，在用户切换时重置对话
  useEffect(() => {
    const newUserId = user?.id || null;
    
    // 如果是第一次初始化，设置用户ID并加载用户特定数据
    if (currentUserId === null) {
      setCurrentUserId(newUserId);
      
      // 载入当前用户的对话ID和消息
      const userConversationId = loadConversationId(newUserId);
      const userMessages = loadMessagesFromStorage(newUserId);
      
      if (userConversationId) {
        setConversationId(userConversationId);
      }
      
      if (userMessages && userMessages.length > 0) {
        setMessages(userMessages);
      } else {
        setMessages([{ ...DEFAULT_WELCOME_MESSAGE, timestamp: new Date() }]);
      }
      
      return;
    }
    
    // 检查用户是否发生变化
    if (currentUserId !== newUserId) {
      // 载入新用户的数据
      const newUserConversationId = loadConversationId(newUserId);
      const newUserMessages = loadMessagesFromStorage(newUserId);
      
      // 设置新用户的对话ID和消息
      setConversationId(newUserConversationId || '');
      
      if (newUserMessages && newUserMessages.length > 0) {
        setMessages(newUserMessages);
      } else {
        setMessages([{ ...DEFAULT_WELCOME_MESSAGE, timestamp: new Date() }]);
      }
      
      // 更新当前用户ID
      setCurrentUserId(newUserId);
    }
  }, [user?.id, currentUserId]);

  // 自动保存消息到 localStorage (基于当前用户)
  useEffect(() => {
    if (messages.length > 0 && currentUserId !== null) {
      saveMessagesToStorage(messages, currentUserId);
    }
  }, [messages, currentUserId]);

  // 保存对话 ID (基于当前用户)
  useEffect(() => {
    if (currentUserId !== null) {
      if (conversationId) {
        saveConversationId(conversationId, currentUserId);
      } else {
        // 如果对话ID被清空，也要清除localStorage
        const conversationKey = getUserConversationKey(currentUserId);
        localStorage.removeItem(conversationKey);
      }
    }
  }, [conversationId, currentUserId]);

  // 清除聊天记录
  const clearChat = useCallback(() => {
    const defaultMessage = { ...DEFAULT_WELCOME_MESSAGE, timestamp: new Date() };
    setMessages([defaultMessage]);
    setConversationId('');
    clearStoredChat(currentUserId);
  }, [currentUserId]);

  // 检查用户切换状态
  const checkUserSwitch = useCallback((sendTimeUserId) => {
    return currentUserId !== null && currentUserId !== sendTimeUserId;
  }, [currentUserId]);

  // 处理用户切换
  const handleUserSwitch = useCallback((sendTimeUserId) => {
    setCurrentUserId(sendTimeUserId);
    setConversationId('');
    const conversationKey = getUserConversationKey(sendTimeUserId);
    localStorage.removeItem(conversationKey);
  }, []);

  return {
    // 状态
    messages,
    conversationId,
    currentUserId,
    
    // 操作函数
    setMessages,
    setConversationId,
    clearChat,
    
    // 用户切换检测
    checkUserSwitch,
    handleUserSwitch,
    
    // 工具函数
    getInitialMessages: () => getInitialMessages(currentUserId),
    saveConversationId: (id) => saveConversationId(id, currentUserId),
    loadConversationId: () => loadConversationId(currentUserId),
  };
};

export default useMessageStorage;