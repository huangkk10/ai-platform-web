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
 *   response: "AI 回應",
 *   intent: "query_projects_by_customer",
 *   confidence: 0.97,
 *   parameters: { customer: "WD" },
 *   response_time_ms: 3500
 * }
 * 
 * ⚠️ 與 Protocol Assistant API 的差異：
 * - 請求參數名：query（不是 message）
 * - 回應內容欄位：response（不是 answer）
 * - 不支援 conversation_id（無對話追蹤）
 */

import { useState, useRef, useCallback } from 'react';
import { message } from 'antd';

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
        response_length: data.response?.length || 0,
        intent: data.intent,
        confidence: data.confidence,
        response_time_ms: data.response_time_ms
      });

      if (data.success) {
        // 創建 AI 回應訊息
        // ⚠️ SAF API 使用 "response" 欄位，不是 "answer"
        const assistantMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: data.response || '抱歉，我無法生成回應。',
          timestamp: new Date(),
          metadata: {
            intent: data.intent,
            confidence: data.confidence,
            parameters: data.parameters,
            response_time_ms: data.response_time_ms
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
        // 處理錯誤回應
        const errorContent = data.error_message || data.error || '抱歉，查詢失敗，請稍後再試。';
        
        const errorMessage = {
          id: Date.now() + 1,
          type: 'assistant',
          content: `❌ ${errorContent}`,
          timestamp: new Date(),
          error: true
        };
        
        console.log('⚠️ [SAF Assistant] API 回傳錯誤:', errorContent);
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
  }, [setMessages]);

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
