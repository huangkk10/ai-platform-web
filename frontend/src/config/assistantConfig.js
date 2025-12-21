/**
 * Assistant 配置
 * ==============
 * 
 * 統一管理所有 AI Assistant 的配置
 * 
 * 包含：
 * - 閒置重置配置（idleTimeout, storageKey 等）
 * - 各 Assistant 的特定設定
 */

// ============================================================
// 閒置重置配置
// ============================================================

/**
 * 閒置超時時間（毫秒）
 * 預設：12 小時
 */
export const IDLE_TIMEOUT_HOURS = 12;
export const IDLE_TIMEOUT_MS = IDLE_TIMEOUT_HOURS * 60 * 60 * 1000;

/**
 * 各 Assistant 的閒置重置配置
 */
export const ASSISTANT_IDLE_CONFIG = {
  // RVT Assistant
  rvt: {
    idleTimeout: IDLE_TIMEOUT_MS,
    storageKey: 'rvt_assistant',
    messagesStorageKey: 'rvt_assistant_messages',
    conversationIdStorageKey: 'rvt_assistant_conversationId'
  },
  
  // Protocol Assistant
  protocol: {
    idleTimeout: IDLE_TIMEOUT_MS,
    storageKey: 'protocol_assistant',
    messagesStorageKey: 'protocol_assistant_messages',
    conversationIdStorageKey: 'protocol_assistant_conversationId'
  },
  
  // SAF Assistant
  saf: {
    idleTimeout: IDLE_TIMEOUT_MS,
    storageKey: 'saf_assistant',
    messagesStorageKey: 'saf_assistant_messages',
    conversationIdStorageKey: 'saf_assistant_conversationId'
  }
};

/**
 * 獲取指定 Assistant 的閒置配置
 * @param {string} assistantType - 'rvt' | 'protocol' | 'saf'
 * @returns {Object} 閒置配置
 */
export const getAssistantIdleConfig = (assistantType) => {
  return ASSISTANT_IDLE_CONFIG[assistantType] || {
    idleTimeout: IDLE_TIMEOUT_MS,
    storageKey: `${assistantType}_assistant`,
    messagesStorageKey: `${assistantType}_assistant_messages`,
    conversationIdStorageKey: `${assistantType}_assistant_conversationId`
  };
};

/**
 * 清除指定 Assistant 的所有 localStorage 資料
 * @param {string} assistantType - 'rvt' | 'protocol' | 'saf'
 */
export const clearAssistantStorage = (assistantType) => {
  const config = getAssistantIdleConfig(assistantType);
  
  try {
    localStorage.removeItem(config.messagesStorageKey);
    localStorage.removeItem(config.conversationIdStorageKey);
    localStorage.removeItem(`${config.storageKey}_lastActivity`);
    console.log(`🧹 [${assistantType}] 已清除所有 localStorage 資料`);
  } catch (e) {
    console.warn(`[${assistantType}] 清除 localStorage 失敗: ${e.message}`);
  }
};

// ============================================================
// 其他 Assistant 配置（可擴展）
// ============================================================

/**
 * Assistant API 端點配置
 */
export const ASSISTANT_API_ENDPOINTS = {
  rvt: '/api/rvt-guide/chat/',
  protocol: '/api/protocol-guide/chat/',
  saf: '/api/saf/smart-query/'
};

/**
 * Assistant 顯示名稱
 */
export const ASSISTANT_DISPLAY_NAMES = {
  rvt: 'RVT Assistant',
  protocol: 'Protocol Assistant',
  saf: 'SAF Assistant'
};

export default {
  IDLE_TIMEOUT_HOURS,
  IDLE_TIMEOUT_MS,
  ASSISTANT_IDLE_CONFIG,
  getAssistantIdleConfig,
  clearAssistantStorage,
  ASSISTANT_API_ENDPOINTS,
  ASSISTANT_DISPLAY_NAMES
};
