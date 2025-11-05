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
    console.log('🚀 [Protocol Assistant] sendMessage 開始執行');
    console.log('  - userMessage:', userMessage);
    console.log('  - conversationId:', conversationId);
    console.log('  - currentUserId:', currentUserId);
    
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      abortControllerRef.current = new AbortController();
      
      const requestBody = {
        message: userMessage.content,
        conversation_id: conversationId,  // ✅ 恢復：使用 conversation_id 保持對話上下文
        user_id: currentUserId
      };
      
      console.log('📤 [Protocol Assistant] 發送請求:', requestBody);

      // ✅ 修正：使用正確的 API 端點 /api/protocol-guide/chat/
      // 原本錯誤的端點：/api/protocol-assistant/chat/ (404)
      console.log('🌐 [Protocol Assistant] 發送 fetch 請求到 /api/protocol-guide/chat/');
      const response = await fetch('/api/protocol-guide/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });
      
      console.log('📥 [Protocol Assistant] 收到回應:', {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText
      });

      // ✅ 修正：處理 404 錯誤（conversation_id 失效）
      let data;
      let isRetry = false;
      
      if (!response.ok) {
        if (response.status === 404 && conversationId) {
          // Conversation ID 失效，清除並重試
          console.warn('⚠️ Conversation ID 失效，清除並發起新對話');
          setConversationId(null);
          
          // 重試請求（不帶 conversation_id）
          const retryBody = {
            message: userMessage.content,
            user_id: currentUserId
            // 不包含 conversation_id，發起新對話
          };
          
          const retryResponse = await fetch('/api/protocol-guide/chat/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            credentials: 'include',
            body: JSON.stringify(retryBody),
            signal: abortControllerRef.current.signal
          });
          
          if (!retryResponse.ok) {
            throw new Error(`HTTP error! status: ${retryResponse.status}`);
          }
          
          data = await retryResponse.json();
          isRetry = true;
        } else {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
      } else {
        data = await response.json();
      }

      // ✅ DEBUG: 記錄收到的資料
      console.log('🔍 [Protocol Assistant] 收到後端回應:', {
        success: data.success,
        answer_length: data.answer?.length || 0,
        conversation_id: data.conversation_id,
        message_id: data.message_id,
        has_answer: !!data.answer
      });

      // 處理回應
      console.log('🔄 [Protocol Assistant] 開始處理回應, data.success =', data.success);
      if (data.success) {
        const newConversationId = data.conversation_id || conversationId;
        if (newConversationId !== conversationId) {
          console.log('🆔 [Protocol Assistant] 更新 conversation_id:', conversationId, '=>', newConversationId);
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

        console.log('💬 [Protocol Assistant] 創建 assistant 訊息:', {
          id: assistantMessage.id,
          content_length: assistantMessage.content.length,
          message_id: assistantMessage.message_id
        });

        console.log('📝 [Protocol Assistant] 調用 setMessages 添加訊息');
        setMessages(prev => {
          const newMessages = [...prev, assistantMessage];
          console.log('  - 訊息列表長度:', prev.length, '=>', newMessages.length);
          return newMessages;
        });
        
        if (isRetry) {
          message.success('已發起新對話');
        }
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
