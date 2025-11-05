import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';

const useProtocolAssistantChat = (conversationId, setConversationId, setMessages, user, currentUserId) => {
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const abortControllerRef = useRef(null);

  const stopRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setLoadingStartTime(null);
      message.info('已停止生成回應');
    }
  }, []);

  const sendMessage = useCallback(async (userMessage) => {
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      abortControllerRef.current = new AbortController();
      
      const requestBody = {
        message: userMessage.content,
        conversation_id: conversationId,
        user_id: currentUserId
      };

      // ✅ 修正：使用正確的 API 端點 /api/protocol-guide/chat/
      // 原本錯誤的端點：/api/protocol-assistant/chat/ (404)
      const response = await fetch('/api/protocol-guide/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      if (data.success) {
        const newConversationId = data.conversation_id || conversationId;
        if (newConversationId !== conversationId) {
          setConversationId(newConversationId);
        }

        // 創建 AI 回應訊息（跟 RVT Assistant 一樣的邏輯）
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.answer || '抱歉，我無法生成回應。',
          timestamp: new Date(),
          metadata: data.metadata,
          usage: data.usage,
          response_time: data.response_time,
          message_id: data.message_id
        };

        setMessages(prev => [...prev, assistantMessage]);
      } else {
        throw new Error(data.error || '發送訊息失敗');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        message.info('已停止生成回應');
        return;
      }

      console.error('發送訊息時發生錯誤:', error);
      
      // 添加錯誤訊息
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: `❌ 發生錯誤：${error.message || '無法連接到伺服器'}`,
        timestamp: new Date(),
        error: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
      message.error(`發送失敗：${error.message || '請檢查網絡連接'}`);
    } finally {
      setLoading(false);
      setLoadingStartTime(null);
      abortControllerRef.current = null;
    }
  }, [conversationId, setConversationId, setMessages, currentUserId]);

  return {
    sendMessage,
    loading,
    loadingStartTime,
    stopRequest
  };
};

export default useProtocolAssistantChat;
