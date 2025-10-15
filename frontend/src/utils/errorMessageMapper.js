/**
 * 錯誤訊息映射工具
 * 將各種錯誤類型轉換為用戶友好的訊息
 */

/**
 * 將錯誤對象映射為用戶友好的錯誤訊息
 * @param {Error} error - 錯誤對象
 * @returns {string} - 用戶友好的錯誤訊息
 */
export const mapErrorToMessage = (error) => {
  // 網路連接錯誤
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return '網路連接錯誤，請檢查網路連接';
  }
  
  // HTML 回應錯誤
  if (error.message.includes('Unexpected token') && error.message.includes('html')) {
    return '服務器回應格式錯誤，請稍後再試';
  }
  
  // 認證問題
  if (error.message.includes('認證問題') || error.message.includes('重定向到 HTML')) {
    return '用戶會話可能已過期，但可以繼續使用聊天功能';
  }
  
  // 配置載入失敗
  if (error.message.includes('配置載入失敗')) {
    return '系統配置載入失敗，請聯繫管理員';
  }
  
  // 超時錯誤
  if (error.message.includes('504')) {
    return 'RVT Assistant 分析超時，可能是因為查詢較複雜，請稍後再試或簡化問題描述';
  }
  
  if (error.message.includes('503')) {
    return 'RVT Assistant 服務暫時不可用，請稍後再試';
  }
  
  if (error.message.includes('408')) {
    return 'RVT Assistant 分析時間較長，請稍後再試';
  }
  
  if (error.message.includes('timeout') || error.message.includes('超時')) {
    return 'RVT Assistant 分析超時，建議簡化問題描述後重試';
  }
  
  // 認證狀態問題
  if (error.message.includes('guest_auth_issue')) {
    return '🔄 檢測到認證狀態問題，但 RVT Assistant 支援訪客使用。系統將自動重試...';
  }
  
  // 權限錯誤
  if (error.message.includes('403') || error.message.includes('Forbidden')) {
    return '訪客可以使用 RVT Assistant，無需登入。請稍後再試';
  }
  
  if (error.message.includes('401') || error.message.includes('Unauthorized')) {
    return '用戶會話可能已過期，但可以繼續使用 RVT Assistant';
  }
  
  // 對話過期錯誤
  if (error.message.includes('conversation_expired_404')) {
    return '🔄 對話已自動重置，請重新發送您的消息。';
  }
  
  if (error.message.includes('對話已過期') || error.message.includes('重新發送您的問題')) {
    return error.message;
  }
  
  // 預設返回原始錯誤訊息
  return error.message || '未知錯誤';
};

/**
 * 生成包含建議的完整錯誤訊息
 * @param {string} errorText - 錯誤訊息
 * @returns {string} - 包含建議的完整錯誤訊息
 */
export const generateErrorMessageWithSuggestions = (errorText) => {
  return `❌ 抱歉，查詢過程中出現錯誤：${errorText}\n\n請稍後再試，或嘗試：\n• 簡化問題描述\n• 提供更具體的錯誤信息\n• 分段提問複雜問題`;
};

/**
 * 檢查是否需要自動重試
 * @param {Error} error - 錯誤對象
 * @returns {boolean} - 是否需要重試
 */
export const shouldRetryConversation = (error) => {
  return error.message.includes('conversation_expired_404');
};

/**
 * 檢查錯誤是否是用戶主動取消
 * @param {Error} error - 錯誤對象
 * @returns {boolean} - 是否是用戶取消
 */
export const isUserCancellation = (error) => {
  return error.name === 'AbortError';
};
