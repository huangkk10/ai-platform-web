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
        message.error(`反饋提交失敗: ${data.error}`);
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
