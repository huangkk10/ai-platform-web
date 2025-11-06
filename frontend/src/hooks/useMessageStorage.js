import { useState, useEffect, useCallback } from 'react';

// localStorage 相關常數 - 基于用户ID隔离
// 注意：現在使用動態的 storageKey 參數，不再硬編碼
const MAX_STORAGE_DAYS = 7; // 最多保存 7 天
const MAX_MESSAGES = 200; // 最多保存 200 條消息

// 預設通用歡迎消息（當沒有提供自訂歡迎訊息時使用）
const DEFAULT_WELCOME_MESSAGE = {
  id: 1,
  type: 'assistant',
  content: '🛠️ 歡迎使用 Assistant！我是你的智能助手，可以協助你解決相關的問題。\n\n現在就開始吧！有什麼問題需要協助嗎？',
  timestamp: new Date()
};

/**
 * 获取用户特定的存储键
 * @param {string} storageKey - 存储键前缀（例如：'rvt', 'protocol-assistant'）
 * @param {string|number} userId - 用户ID
 * @returns {string} - 存储键
 */
const getUserStorageKey = (storageKey, userId) => `${storageKey}-chat-messages-${userId || 'guest'}`;

/**
 * 获取用户特定的对话ID键
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 * @returns {string} - 对话ID键
 */
const getUserConversationKey = (storageKey, userId) => `${storageKey}-chat-conversation-id-${userId || 'guest'}`;

/**
 * 保存消息到 localStorage
 * @param {Array} messages - 消息列表
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 */
const saveMessagesToStorage = (messages, storageKey, userId) => {
  try {
    const key = getUserStorageKey(storageKey, userId);
    const data = {
      messages: messages.map(msg => ({
        ...msg,
        timestamp: msg.timestamp instanceof Date ? msg.timestamp.toISOString() : msg.timestamp
      })),
      savedAt: new Date().toISOString(),
      userId: userId || 'guest'
    };
    localStorage.setItem(key, JSON.stringify(data));
    // console.log(`💾 保存对话记录 - 类型: ${storageKey}, 用户: ${userId || 'guest'}, 消息数: ${messages.length}`);
  } catch (error) {
    console.warn('保存對話記錄失敗:', error);
  }
};

/**
 * 从 localStorage 加载消息
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 * @returns {Array|null} - 消息列表或null
 */
const loadMessagesFromStorage = (storageKey, userId) => {
  try {
    const key = getUserStorageKey(storageKey, userId);
    const stored = localStorage.getItem(key);
    if (!stored) {
      // console.log(`📂 未找到对话记录 - 类型: ${storageKey}, 用户: ${userId || 'guest'}`);
      return null;
    }
    
    const data = JSON.parse(stored);
    const savedAt = new Date(data.savedAt);
    const now = new Date();
    const daysDiff = (now - savedAt) / (1000 * 60 * 60 * 24);
    
    // 检查数据是否属于正确的用户
    if (data.userId !== (userId || 'guest')) {
      // console.log(`🔄 用户不匹配，清除旧数据 - 存储用户: ${data.userId}, 当前用户: ${userId || 'guest'}`);
      localStorage.removeItem(key);
      return null;
    }
    
    // 檢查是否過期
    if (daysDiff > MAX_STORAGE_DAYS) {
      // console.log(`⏰ 对话记录已过期 - 类型: ${storageKey}, 用户: ${userId || 'guest'}`);
      localStorage.removeItem(key);
      localStorage.removeItem(getUserConversationKey(storageKey, userId));
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
    
    // console.log(`📖 载入对话记录 - 类型: ${storageKey}, 用户: ${userId || 'guest'}, 消息数: ${messages.length}`);
    return messages;
  } catch (error) {
    console.warn('讀取對話記錄失敗:', error);
    const key = getUserStorageKey(storageKey, userId);
    localStorage.removeItem(key);
    return null;
  }
};

/**
 * 保存对话ID
 * @param {string} conversationId - 对话ID
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 */
const saveConversationId = (conversationId, storageKey, userId) => {
  try {
    if (conversationId) {
      const key = getUserConversationKey(storageKey, userId);
      localStorage.setItem(key, conversationId);
      // console.log(`💾 保存对话ID - 类型: ${storageKey}, 用户: ${userId || 'guest'}, ID: ${conversationId}`);
    }
  } catch (error) {
    console.warn('保存對話ID失敗:', error);
  }
};

/**
 * 加载对话ID
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 * @returns {string} - 对话ID
 */
const loadConversationId = (storageKey, userId) => {
  try {
    const key = getUserConversationKey(storageKey, userId);
    const conversationId = localStorage.getItem(key) || '';
    if (conversationId) {
      // console.log(`📖 载入对话ID - 类型: ${storageKey}, 用户: ${userId || 'guest'}, ID: ${conversationId}`);
    }
    return conversationId;
  } catch (error) {
    console.warn('讀取對話ID失敗:', error);
    return '';
  }
};

/**
 * 清除用户的聊天记录
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 */
const clearStoredChat = (storageKey, userId) => {
  try {
    const messageKey = getUserStorageKey(storageKey, userId);
    const conversationKey = getUserConversationKey(storageKey, userId);
    localStorage.removeItem(messageKey);
    localStorage.removeItem(conversationKey);
    // console.log(`🗑️ 清除用户数据 - 类型: ${storageKey}, 用户: ${userId || 'guest'}`);
  } catch (error) {
    console.warn('清除對話記錄失敗:', error);
  }
};

/**
 * 获取初始消息
 * @param {string} storageKey - 存储键前缀
 * @param {string|number} userId - 用户ID
 * @param {string} welcomeMessage - 自訂歡迎訊息（可選）
 * @returns {Array} - 消息列表
 */
const getInitialMessages = (storageKey, userId, welcomeMessage) => {
  const storedMessages = loadMessagesFromStorage(storageKey, userId);
  if (storedMessages && storedMessages.length > 0) {
    return storedMessages;
  }
  // 使用自訂歡迎訊息或預設歡迎消息
  const welcomeContent = welcomeMessage || DEFAULT_WELCOME_MESSAGE.content;
  return [{ id: 1, type: 'assistant', content: welcomeContent, timestamp: new Date() }];
};

/**
 * useMessageStorage Hook - 管理消息存储和用户切换
 * @param {Object} user - 用户对象
 * @param {string} storageKey - 存储键前缀（例如：'rvt', 'protocol-assistant'）
 * @param {string} welcomeMessage - 自訂歡迎訊息（可選）
 * @returns {Object} - 包含消息状态和操作函数的对象
 */
const useMessageStorage = (user, storageKey = 'default', welcomeMessage = null) => {
  const [messages, setMessagesInternal] = useState(() => getInitialMessages(storageKey, user?.id, welcomeMessage));
  const [conversationId, setConversationId] = useState('');
  const [currentUserId, setCurrentUserId] = useState(null);
  
  // ✅ DEBUG: 包裝 setMessages 以記錄所有調用
  const setMessages = useCallback((updater) => {
    console.log('📦 [useMessageStorage] setMessages 被調用');
    console.log('  - storageKey:', storageKey);
    console.log('  - updater type:', typeof updater);
    
    setMessagesInternal(prev => {
      const newMessages = typeof updater === 'function' ? updater(prev) : updater;
      console.log('  - 舊訊息數量:', prev.length);
      console.log('  - 新訊息數量:', newMessages.length);
      if (newMessages.length > prev.length) {
        console.log('  - 新增的訊息:', newMessages[newMessages.length - 1]);
      }
      return newMessages;
    });
  }, [storageKey]);

  // 监听用户状态变化，在用户切换时重置对话
  useEffect(() => {
    const newUserId = user?.id || null;
    
    // 如果是第一次初始化，设置用户ID并加载用户特定数据
    if (currentUserId === null) {
      setCurrentUserId(newUserId);
      
      // ✅ 載入消息記錄和 conversation_id
      const userMessages = loadMessagesFromStorage(storageKey, newUserId);
      const savedConversationId = loadConversationId(storageKey, newUserId);
      
      if (savedConversationId) {
        setConversationId(savedConversationId);
      }
      
      if (userMessages && userMessages.length > 0) {
        setMessages(userMessages);
      } else {
        const welcomeContent = welcomeMessage || DEFAULT_WELCOME_MESSAGE.content;
        setMessages([{ id: 1, type: 'assistant', content: welcomeContent, timestamp: new Date() }]);
      }
      
      return;
    }
    
    // 检查用户是否发生变化
    if (currentUserId !== newUserId) {
      // 载入新用户的数据
      const newUserMessages = loadMessagesFromStorage(storageKey, newUserId);
      const newUserConversationId = loadConversationId(storageKey, newUserId);
      
      // ✅ 載入新用戶的 conversation_id
      setConversationId(newUserConversationId || '');
      
      if (newUserMessages && newUserMessages.length > 0) {
        setMessages(newUserMessages);
      } else {
        const welcomeContent = welcomeMessage || DEFAULT_WELCOME_MESSAGE.content;
        setMessages([{ id: 1, type: 'assistant', content: welcomeContent, timestamp: new Date() }]);
      }
      
      // 更新当前用户ID
      setCurrentUserId(newUserId);
    }
  }, [user?.id, currentUserId, storageKey, welcomeMessage]);

  // 自动保存消息到 localStorage (基于当前用户和storageKey)
  useEffect(() => {
    if (messages.length > 0 && currentUserId !== null) {
      saveMessagesToStorage(messages, storageKey, currentUserId);
    }
  }, [messages, currentUserId, storageKey]);

  // 保存对话 ID (基于当前用户和storageKey)
  useEffect(() => {
    if (conversationId && currentUserId !== null) {
      saveConversationId(conversationId, storageKey, currentUserId);
    }
  }, [conversationId, currentUserId, storageKey]);

  // 清除聊天记录
  const clearChat = useCallback(() => {
    const welcomeContent = welcomeMessage || DEFAULT_WELCOME_MESSAGE.content;
    const defaultMessage = { id: 1, type: 'assistant', content: welcomeContent, timestamp: new Date() };
    setMessages([defaultMessage]);
    setConversationId('');
    clearStoredChat(storageKey, currentUserId);
  }, [currentUserId, storageKey, welcomeMessage]);

  // 检查用户切换状态
  const checkUserSwitch = useCallback((sendTimeUserId) => {
    return currentUserId !== null && currentUserId !== sendTimeUserId;
  }, [currentUserId]);

  // 处理用户切换
  const handleUserSwitch = useCallback((sendTimeUserId) => {
    setCurrentUserId(sendTimeUserId);
    setConversationId('');
    const conversationKey = getUserConversationKey(storageKey, sendTimeUserId);
    localStorage.removeItem(conversationKey);
  }, [storageKey]);

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
    getInitialMessages: () => getInitialMessages(storageKey, currentUserId, welcomeMessage),
    saveConversationId: (id) => saveConversationId(id, storageKey, currentUserId),
    loadConversationId: () => loadConversationId(storageKey, currentUserId),
  };
};

export default useMessageStorage;