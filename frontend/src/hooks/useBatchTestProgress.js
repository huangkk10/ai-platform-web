/**
 * useBatchTestProgress Hook
 * 
 * 使用 Server-Sent Events (SSE) 監聽批量測試進度
 * 
 * 功能：
 * - 建立 SSE 連接到後端進度 API
 * - 即時接收進度更新（每 0.5 秒）
 * - 自動重連機制（連接中斷時）
 * - 完成後自動關閉連接
 * 
 * 使用方式：
 * ```javascript
 * const { progress, progressData, isConnected, error } = useBatchTestProgress(batchId);
 * 
 * // progress: 整體進度百分比 (0-100)
 * // progressData: 完整進度資料（包含各版本詳細進度）
 * // isConnected: SSE 連接狀態
 * // error: 錯誤訊息
 * ```
 * 
 * 作者: AI Platform Team
 * 日期: 2025-11-24
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const useBatchTestProgress = (batchId) => {
  const [progress, setProgress] = useState(0);
  const [progressData, setProgressData] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const isUnmountedRef = useRef(false);
  
  // 建立 SSE 連接
  const connectSSE = useCallback(() => {
    // 如果沒有 batch_id，不建立連接
    if (!batchId) {
      console.warn('[useBatchTestProgress] ⚠️ batchId 為空，跳過連接');
      console.warn('[useBatchTestProgress] batchId 值:', batchId);
      return;
    }
    
    console.log('[useBatchTestProgress] 🎯 開始建立 SSE 連接流程...');
    console.log('[useBatchTestProgress] 📋 接收到的 batchId:', batchId);
    console.log('[useBatchTestProgress] 📋 batchId 類型:', typeof batchId);
    
    // 如果已經有連接，先關閉
    if (eventSourceRef.current) {
      console.log('[useBatchTestProgress] 🔄 偵測到現有連接，先關閉...');
      // 直接清理，不使用 cleanup 函數
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
    
    try {
      // 構建 SSE URL
      const apiUrl = `/api/dify-benchmark/versions/batch_test_progress/?batch_id=${batchId}`;
      console.log('[useBatchTestProgress] 🌐 SSE URL:', apiUrl);
      
      // ✅ 步驟 1：創建 EventSource（只創建，不做其他操作）
      const eventSource = new EventSource(apiUrl);
      
      // ✅ 步驟 2：使用 addEventListener 綁定事件（更可靠的方式）
      // 某些環境下 addEventListener 比直接賦值 onopen 更可靠
      
      console.log('[useBatchTestProgress] 🔧 開始綁定事件監聽器...');
      
      // 連接成功事件（使用 addEventListener）
      const handleOpen = () => {
        if (!isUnmountedRef.current) {
          console.log('[useBatchTestProgress] ✅ SSE 連接成功 (open 事件觸發)');
          console.log('[useBatchTestProgress] ✅ readyState:', eventSource.readyState);
          setIsConnected(true);
          setError(null);
        }
      };
      eventSource.addEventListener('open', handleOpen);
      
      // 接收訊息事件（使用 addEventListener）
      const handleMessage = (event) => {
        console.log('[useBatchTestProgress] 📨 ========== 收到 SSE 訊息 ==========');
        console.log('[useBatchTestProgress] 📨 event.type:', event.type);
        console.log('[useBatchTestProgress] 📨 event.data:', event.data);
        console.log('[useBatchTestProgress] 📨 isUnmountedRef.current:', isUnmountedRef.current);
        
        if (isUnmountedRef.current) {
          console.warn('[useBatchTestProgress] ⚠️ 組件已卸載，忽略訊息');
          return;
        }
        
        try {
          const data = JSON.parse(event.data);
          
          console.log('[useBatchTestProgress] 📊 解析後的資料:', {
            progress: data.progress,
            status: data.status,
            completed: data.completed_tests,
            total: data.total_tests,
            batch_id: data.batch_id
          });
          
          // 檢查是否有錯誤
          if (data.error) {
            console.error('[useBatchTestProgress] 服務器錯誤:', data.error);
            setError(data.error);
            // 直接清理連接
            if (eventSourceRef.current) {
              eventSourceRef.current.close();
              eventSourceRef.current = null;
              setIsConnected(false);
            }
            return;
          }
          
          // 更新進度資料
          setProgressData(data);
          setProgress(data.progress || 0);
          
          console.log(
            `[useBatchTestProgress] 進度更新: ${data.progress?.toFixed(1)}% ` +
            `(${data.completed_tests}/${data.total_tests})`
          );
          
          // 如果測試完成，關閉連接
          if (data.status === 'completed' || data.status === 'error') {
            console.log(`[useBatchTestProgress] 測試${data.status === 'completed' ? '完成' : '失敗'}，關閉連接`);
            
            // 延遲 2 秒關閉，確保最後一次更新顯示完整
            setTimeout(() => {
              if (!isUnmountedRef.current && eventSourceRef.current) {
                eventSourceRef.current.close();
                eventSourceRef.current = null;
                setIsConnected(false);
              }
            }, 2000);
          }
        } catch (err) {
          console.error('[useBatchTestProgress] 解析進度資料失敗:', err);
          console.error('[useBatchTestProgress] 原始資料:', event.data);
          setError('解析進度資料失敗');
        }
      };
      eventSource.addEventListener('message', handleMessage);
      console.log('[useBatchTestProgress] ✅ message 事件監聽器已綁定');
      
      // 連接錯誤事件（使用 addEventListener）
      const handleError = (err) => {
        if (isUnmountedRef.current) return;
        
        console.error('[useBatchTestProgress] ❌ SSE 連接錯誤事件觸發');
        console.error('[useBatchTestProgress] 錯誤對象:', err);
        console.error('[useBatchTestProgress] EventSource.readyState:', eventSource.readyState);
        console.error('[useBatchTestProgress] EventSource.url:', eventSource.url);
        
        // EventSource readyState 狀態：
        // 0 = CONNECTING (正在連接)
        // 1 = OPEN (連接已打開)
        // 2 = CLOSED (連接已關閉)
        
        if (eventSource.readyState === EventSource.CONNECTING) {
          console.warn('[useBatchTestProgress] ⚠️ 連接中斷，EventSource 正在自動重連...');
        } else if (eventSource.readyState === EventSource.CLOSED) {
          console.error('[useBatchTestProgress] ❌ 連接已完全關閉，無法重連');
          setIsConnected(false);
          setError('SSE 連接已關閉');
          
          // 嘗試重連（3 秒後）
          if (!isUnmountedRef.current) {
            console.log('[useBatchTestProgress] 3 秒後嘗試重連...');
            reconnectTimeoutRef.current = setTimeout(() => {
              if (!isUnmountedRef.current) {
                connectSSE();
              }
            }, 3000);
          }
        }
      };
      eventSource.addEventListener('error', handleError);
      console.log('[useBatchTestProgress] ✅ error 事件監聽器已綁定');
      
      // ✅ 步驟 3：所有事件處理器綁定完成後，才賦值給 ref
      // 這樣可以確保事件處理器在連接建立前就已經就位
      eventSourceRef.current = eventSource;
      
      console.log('[useBatchTestProgress] ✅ EventSource 創建完成，所有處理器已綁定');
      console.log('[useBatchTestProgress] 📊 初始 readyState:', eventSource.readyState);
      console.log('[useBatchTestProgress] 🎧 所有事件監聽器 (addEventListener) 已就緒');
      
    } catch (err) {
      console.error('[useBatchTestProgress] 建立 SSE 連接失敗:', err);
      setError('建立連接失敗');
      setIsConnected(false);
    }
  }, [batchId]);  // ✅ 移除 cleanup 依賴
  
  // 當 batchId 變更時，重新建立連接
  useEffect(() => {
    // ✅ 重要：每次 effect 執行時，重置 unmounted flag
    isUnmountedRef.current = false;
    console.log('[useBatchTestProgress] 🔄 useEffect 執行，重置 isUnmountedRef.current = false');
    
    if (batchId) {
      connectSSE();
    }
    
    // 清理函數：組件卸載或 batchId 變更時執行
    return () => {
      console.log('[useBatchTestProgress] 🧹 清理函數執行，設置 isUnmountedRef.current = true');
      isUnmountedRef.current = true;
      
      // 直接清理
      if (eventSourceRef.current) {
        console.log('[useBatchTestProgress] 🧹 關閉 EventSource 連接');
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = null;
      }
      
      setIsConnected(false);
    };
  }, [batchId, connectSSE]);
  
  return {
    progress,           // 整體進度百分比 (0-100)
    progressData,       // 完整進度資料
    isConnected,        // SSE 連接狀態
    error               // 錯誤訊息
  };
};

export default useBatchTestProgress;
