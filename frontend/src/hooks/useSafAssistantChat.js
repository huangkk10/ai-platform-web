/**
 * SAF Assistant Chat Hook
 * ========================
 * 
 * 處理 SAF Assistant 的 API 通訊
 * 
 * API 端點：POST /api/saf/smart-query/
 * 請求格式：{ query: "用戶問題" }
 * 回應格式：{
 *   success: true,
 *   answer: "AI 回應（自然語言）",
 *   intent: { type: "query_projects_by_customer", ... },
 *   result: { status: "success", data: [...] },
 *   metadata: { ... }
 * }
 * 
 * ⚠️ 與 Protocol Assistant API 的差異：
 * - 請求參數名：query（不是 message）
 * - 不支援 conversation_id（無對話追蹤）
 */

import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';
import { useIdleReset } from './useIdleReset';
import { ASSISTANT_IDLE_CONFIG, clearAssistantStorage } from '../config/assistantConfig';

const useSafAssistantChat = (
  conversationId, 
  setConversationId, 
  setMessages, 
  user, 
  currentUserId
) => {
  const [loading, setLoading] = useState(false);
  const [loadingStartTime, setLoadingStartTime] = useState(null);
  const abortControllerRef = useRef(null);

  // ============================================================
  // 🆕 閒置自動重置功能（12 小時後自動清除對話和訊息）
  // ============================================================
  const idleConfig = ASSISTANT_IDLE_CONFIG.saf;

  /**
   * 重置對話回調函數
   * 當閒置超過 12 小時時自動執行
   */
  const handleIdleReset = useCallback(() => {
    console.log('🔄 [SAF] 閒置超時 - 重置對話並清除訊息');
    
    // 1. 清除 conversation_id
    setConversationId('');
    
    // 2. 清除訊息列表
    setMessages([]);
    
    // 3. 清除 localStorage 中的相關資料
    clearAssistantStorage('saf');
    
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

  // 停止請求
  const stopRequest = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
      setLoading(false);
      setLoadingStartTime(null);
      message.info('已停止生成回應');
    }
  }, []);

  // 發送訊息
  const sendMessage = useCallback(async (userMessage) => {
    // 🆕 檢查閒置狀態，如需要則重置（會清除訊息）
    checkAndReset();
    
    // 🆕 更新活動時間
    updateLastActivity();

    console.log('🚀 [SAF Assistant] sendMessage 開始執行');
    console.log('  - userMessage:', userMessage);
    
    setLoading(true);
    setLoadingStartTime(Date.now());

    try {
      abortControllerRef.current = new AbortController();
      
      // ⚠️ SAF API 使用 "query" 參數，不是 "message"
      const requestBody = {
        query: userMessage.content
      };
      
      console.log('📤 [SAF Assistant] 發送請求:', requestBody);
      console.log('🌐 [SAF Assistant] 發送 fetch 請求到 /api/saf/smart-query/');

      const response = await fetch('/api/saf/smart-query/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(requestBody),
        signal: abortControllerRef.current.signal
      });
      
      console.log('📥 [SAF Assistant] 收到回應:', {
        ok: response.ok,
        status: response.status,
        statusText: response.statusText
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      console.log('🔍 [SAF Assistant] 回應資料:', {
        success: data.success,
        answer_length: data.answer?.answer?.length || data.answer?.length || 0,
        intent: data.intent?.type,
        confidence: data.intent?.confidence,
        result_status: data.result?.status
      });

      // 提取回答內容（answer 可能是字串或物件）
      let answerContent = '';
      if (typeof data.answer === 'string') {
        answerContent = data.answer;
      } else if (data.answer && data.answer.answer) {
        answerContent = data.answer.answer;
      }

      if (data.success && answerContent) {
        // 創建 AI 回應訊息
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: answerContent,
          timestamp: new Date(),
          metadata: {
            intent: data.intent,
            result: data.result,
            query_metadata: data.metadata
          }
        };

        console.log('💬 [SAF Assistant] 創建 assistant 訊息:', {
          id: assistantMessage.id,
          content_length: assistantMessage.content.length,
          intent: data.intent
        });
        
        // 添加訊息到列表
        console.log('📝 [SAF Assistant] 調用 setMessages 添加訊息');
        setMessages(prev => {
          const newMessages = [...prev, assistantMessage];
          console.log('  - 訊息列表長度:', prev.length, '=>', newMessages.length);
          return newMessages;
        });
        
      } else {
        // 處理錯誤或無法理解的回應
        // 優先使用 answer 欄位（包含幫助提示），否則使用 result.message
        let errorContent = answerContent || 
                           data.result?.message || 
                           data.error_message || 
                           data.error || 
                           '抱歉，查詢失敗，請稍後再試。';
        
        const errorMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: errorContent,
          timestamp: new Date(),
          error: !data.success
        };
        
        console.log('⚠️ [SAF Assistant] 無法處理查詢:', data.intent?.type);
        setMessages(prev => [...prev, errorMessage]);
      }

    } catch (error) {
      console.error('❌ [SAF Assistant] 發送訊息失敗:', error);
      
      if (error.name === 'AbortError') {
        console.log('🛑 [SAF Assistant] 請求已被取消');
        message.info('已停止生成回應');
        return;
      }
      
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
  }, [setMessages, checkAndReset, updateLastActivity]);  // 🆕 添加閒置重置依賴

  return {
    sendMessage,
    loading,
    loadingStartTime,
    stopRequest,
    setLoading,
    setLoadingStartTime
  };
};

export default useSafAssistantChat;
