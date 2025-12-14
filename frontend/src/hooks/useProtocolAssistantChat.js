import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';
import { useIdleReset } from './useIdleReset';
import { ASSISTANT_IDLE_CONFIG, clearAssistantStorage } from '../config/assistantConfig';

const useProtocolAssistantChat = (conversationId, setConversationId, setMessages, user, currentUserId, selectedVersion = null) => {
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const abortControllerRef = useRef(null);

  // ============================================================
  // 🆕 閒置自動重置功能（12 小時後自動清除對話和訊息）
  // ============================================================
  const idleConfig = ASSISTANT_IDLE_CONFIG.protocol;

  /**
   * 重置對話回調函數
   * 當閒置超過 12 小時時自動執行
   */
  const handleIdleReset = useCallback(() => {
    console.log('🔄 [Protocol] 閒置超時 - 重置對話並清除訊息');
    
    // 1. 清除 conversation_id
    setConversationId('');
    
    // 2. 清除訊息列表
    setMessages([]);
    
    // 3. 清除 localStorage 中的相關資料
    clearAssistantStorage('protocol');
    
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
    // 🆕 檢查閒置狀態，如需要則重置（會清除訊息）
    checkAndReset();
    
    // 🆕 更新活動時間
    updateLastActivity();

    console.log('🚀 [Protocol Assistant] sendMessage 開始執行');
    console.log('  - userMessage:', userMessage);
    console.log('  - conversationId:', conversationId);
    console.log('  - currentUserId:', currentUserId);
    console.log('  - selectedVersion:', selectedVersion);  // 🆕 記錄版本資訊
    
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      abortControllerRef.current = new AbortController();
      
      const requestBody = {
        message: userMessage.content,
        conversation_id: conversationId,
        user_id: currentUserId,
        // 🆕 添加 version_code（如果有選擇版本）
        ...(selectedVersion?.version_code && {
          version_code: selectedVersion.version_code
        })
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

      // ✅ 處理回應
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();

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
  }, [conversationId, setConversationId, setMessages, currentUserId, selectedVersion, checkAndReset, updateLastActivity]);  // 🆕 添加閒置重置依賴

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

export default useProtocolAssistantChat;
