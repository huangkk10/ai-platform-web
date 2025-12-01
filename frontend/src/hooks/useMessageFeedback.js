import { useState } from 'react';
import { message } from 'antd';

/**
 * useMessageFeedback Hook
 * 管理聊天訊息的反饋功能（點讚/點踩）
 * 
 * @returns {Object} - { feedbackStates, submitFeedback }
 */
const useMessageFeedback = () => {
  const [feedbackStates, setFeedbackStates] = useState({});

  /**
   * 提交訊息反饋
   * @param {string} messageId - 訊息 ID
   * @param {boolean} isHelpful - 是否有幫助（true: 讚, false: 踩）
   */
  const submitFeedback = async (messageId, isHelpful) => {
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
        
        message.success(
          isHelpful 
            ? '感謝您的正面反饋！' 
            : '感謝您的反饋，我們會持續改進！'
        );
      } else {
        // 根據錯誤類型顯示不同的提示
        const errorMsg = data.error || '未知錯誤';
        
        if (errorMsg.includes('消息不存在') || errorMsg.includes('Message Not')) {
          // 舊對話的訊息，提示用戶清除對話
          message.warning(
            '此訊息已過期，無法提交反饋。請點擊「新聊天」開始新對話後再進行反饋。',
            5  // 顯示 5 秒
          );
        } else {
          message.error(`反饋提交失敗: ${errorMsg}`);
        }
      }
    } catch (error) {
      console.error('提交反饋失敗:', error);
      message.error('反饋提交失敗，請稍後再試');
    }
  };

  return {
    feedbackStates,
    submitFeedback
  };
};

export default useMessageFeedback;
