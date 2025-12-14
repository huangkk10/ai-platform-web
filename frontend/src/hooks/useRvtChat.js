import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';
import { recordChatUsage, CHAT_TYPES } from '../utils/chatUsage';
import { 
  mapErrorToMessage, 
  generateErrorMessageWithSuggestions,
  shouldRetryConversation,
  isUserCancellation
} from '../utils/errorMessageMapper';
import { useIdleReset } from './useIdleReset';
import { ASSISTANT_IDLE_CONFIG, clearAssistantStorage } from '../config/assistantConfig';

/**
 * useRvtChat Hook
 * 處理 RVT Assistant 的 API 通訊邏輯
 * 包含：發送訊息、錯誤處理、自動重試、取消請求等功能
 * 
 * @param {string} conversationId - 當前對話 ID
 * @param {Function} setConversationId - 更新對話 ID 的函數
 * @param {Function} setMessages - 更新訊息列表的函數
 * @param {Object} user - 當前用戶對象
 * @param {number} currentUserId - 當前用戶 ID
 * @returns {Object} - { sendMessage, loading, stopRequest }
 */
const useRvtChat = (conversationId, setConversationId, setMessages, user, currentUserId) => {
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const abortControllerRef = useRef(null);

  // ============================================================
  // 🆕 閒置自動重置功能（12 小時後自動清除對話和訊息）
  // ============================================================
  const idleConfig = ASSISTANT_IDLE_CONFIG.rvt;

  /**
   * 重置對話回調函數
   * 當閒置超過 12 小時時自動執行
   */
  const handleIdleReset = useCallback(() => {
    console.log('🔄 [RVT] 閒置超時 - 重置對話並清除訊息');
    
    // 1. 清除 conversation_id
    setConversationId('');
    
    // 2. 清除訊息列表
    setMessages([]);
    
    // 3. 清除 localStorage 中的相關資料
    clearAssistantStorage('rvt');
    
    // 4. 重置其他狀態
    setLoading(false);
    setLoadingStartTime(null);
  }, [setConversationId, setMessages]);

  // 使用閒置重置 Hook
  const { updateLastActivity, checkAndReset } = useIdleReset({
    idleTimeout: idleConfig.idleTimeout,
    storageKey: idleConfig.storageKey,
    onReset: handleIdleReset,
    enabled: true
  });

  /**
   * 發送訊息到 RVT Assistant API
   * @param {Object} userMessage - 用戶訊息對象
   */
  const sendMessage = async (userMessage) => {
    // 🆕 檢查閒置狀態，如需要則重置（會清除訊息）
    checkAndReset();
    
    // 🆕 更新活動時間
    updateLastActivity();

    setLoading(true);
    setLoadingStartTime(Date.now());

    // 創建新的 AbortController
    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    try {
      // 使用 RVT Guide Chat API (注意：此API有@csrf_exempt，不需要CSRF令牌)
      const response = await fetch('/api/rvt-guide/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest',
        },
        credentials: 'include',
        signal: abortController.signal,
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: conversationId || '',
          search_version: 'v2'  // 固定使用 V2 版本
        })
      });

      // 檢查回應狀態
      if (!response.ok) {
        if (response.status === 404) {
          // 404 錯誤 - 立即清除對話ID並重試
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
          message_id: data.message_id
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
      if (isUserCancellation(error)) {
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
      if (shouldRetryConversation(error)) {
        const retried = await retryConversation(userMessage);
        if (retried) return; // 重試成功，直接返回
      }
      
      // 映射錯誤訊息
      const errorText = mapErrorToMessage(error);
      
      message.error(`查詢失敗: ${errorText}`);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: generateErrorMessageWithSuggestions(errorText),
        timestamp: new Date()
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
      abortControllerRef.current = null;
    }
  };

  /**
   * 404 錯誤自動重試邏輯
   * @param {Object} userMessage - 用戶訊息對象
   * @returns {boolean} - 是否重試成功
   */
  const retryConversation = async (userMessage) => {
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

      if (retryResponse.ok) {
        const retryData = await retryResponse.json();
        
        if (retryData.success) {
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
          
          return true; // 成功重試
        }
      } else {
        // 如果重試也返回404，說明可能是認證問題
        if (retryResponse.status === 404) {
          const errorText = await retryResponse.text();
          console.error('❌ 重試404錯誤內容:', errorText);
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
    
    return false; // 重試失敗
  };

  /**
   * 停止當前請求
   */
  const stopRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      message.info('正在停止當前任務...');
    }
  };

  return {
    sendMessage,
    loading,
    loadingStartTime,
    stopRequest,
    // 🆕 暴露 loading 控制函數（供 OCR 等前置處理使用）
    setLoading,
    setLoadingStartTime
  };
};

export default useRvtChat;
