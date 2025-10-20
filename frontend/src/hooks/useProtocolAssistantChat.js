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

    const assistantMessage = {
      id: Date.now() + 1,
      type: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true
    };

    setMessages(prev => [...prev, assistantMessage]);

    try {
      abortControllerRef.current = new AbortController();
      
      const requestBody = {
        query: userMessage.content,
        conversation_id: conversationId,
        user_id: currentUserId
      };

      const response = await fetch('/api/protocol-assistant/chat/', {
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

        setMessages(prev => prev.map(msg =>
          msg.id === assistantMessage.id
            ? { 
                ...msg, 
                content: data.answer || '抱歉，我無法生成回應。', 
                loading: false,
                metadata: data.metadata
              }
            : msg
        ));
      } else {
        throw new Error(data.message || '發送訊息失敗');
      }
    } catch (error) {
      if (error.name === 'AbortError') {
        setMessages(prev => prev.filter(msg => msg.id !== assistantMessage.id));
        return;
      }

      console.error('發送訊息時發生錯誤:', error);
      
      setMessages(prev => prev.map(msg =>
        msg.id === assistantMessage.id
          ? { 
              ...msg, 
              content: `❌ 發生錯誤：${error.message || '無法連接到伺服器'}`, 
              loading: false,
              error: true
            }
          : msg
      ));
      
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
