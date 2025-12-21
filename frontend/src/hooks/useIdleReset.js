/**
 * useIdleReset Hook
 * =================
 * 
 * 閒置自動重置對話 Hook
 * 
 * 功能：
 * - 追蹤用戶最後活動時間
 * - 超過閒置時間後自動執行重置回調
 * - 支援 localStorage 持久化（跨頁面、跨瀏覽器重開）
 * 
 * 預設閒置時間：12 小時
 * 
 * @example
 * const { updateLastActivity, checkAndReset } = useIdleReset({
 *   idleTimeout: 12 * 60 * 60 * 1000,  // 12 小時
 *   storageKey: 'rvt_assistant',
 *   onReset: () => {
 *     setConversationId(null);
 *     setMessages([]);
 *   },
 *   enabled: true
 * });
 * 
 * // 在發送訊息時調用
 * const sendMessage = async (msg) => {
 *   checkAndReset();  // 檢查是否需要重置
 *   updateLastActivity();  // 更新活動時間
 *   // ... 發送訊息邏輯
 * };
 */

import { useEffect, useRef, useCallback } from 'react';

// 預設閒置時間：12 小時
const DEFAULT_IDLE_TIMEOUT = 12 * 60 * 60 * 1000;

/**
 * 閒置自動重置 Hook
 * 
 * @param {Object} options 配置選項
 * @param {number} options.idleTimeout - 閒置超時時間（毫秒），預設 12 小時
 * @param {string} options.storageKey - localStorage 存儲鍵名前綴
 * @param {Function} options.onReset - 重置時的回調函數
 * @param {boolean} options.enabled - 是否啟用（預設 true）
 * @returns {Object} - { updateLastActivity, checkAndReset, getIdleTime }
 */
export const useIdleReset = ({
  idleTimeout = DEFAULT_IDLE_TIMEOUT,
  storageKey,
  onReset,
  enabled = true
}) => {
  const lastActivityRef = useRef(Date.now());
  const hasInitializedRef = useRef(false);

  /**
   * 獲取 localStorage 鍵名
   */
  const getStorageKey = useCallback(() => {
    return storageKey ? `${storageKey}_lastActivity` : null;
  }, [storageKey]);

  /**
   * 更新最後活動時間
   * 在用戶發送訊息時調用
   */
  const updateLastActivity = useCallback(() => {
    const now = Date.now();
    lastActivityRef.current = now;
    
    const key = getStorageKey();
    if (key) {
      try {
        localStorage.setItem(key, now.toString());
      } catch (e) {
        console.warn(`[useIdleReset] 無法寫入 localStorage: ${e.message}`);
      }
    }
  }, [getStorageKey]);

  /**
   * 從 localStorage 讀取上次活動時間
   */
  const getLastActivityFromStorage = useCallback(() => {
    const key = getStorageKey();
    if (!key) return null;

    try {
      const stored = localStorage.getItem(key);
      if (stored) {
        const timestamp = parseInt(stored, 10);
        if (!isNaN(timestamp) && timestamp > 0) {
          return timestamp;
        }
      }
    } catch (e) {
      console.warn(`[useIdleReset] 無法讀取 localStorage: ${e.message}`);
    }
    return null;
  }, [getStorageKey]);

  /**
   * 檢查是否需要重置，如需要則執行重置
   * @returns {boolean} - 是否執行了重置
   */
  const checkAndReset = useCallback(() => {
    if (!enabled) return false;

    // 從 localStorage 讀取上次活動時間（優先）
    let lastActivity = getLastActivityFromStorage();
    if (!lastActivity) {
      lastActivity = lastActivityRef.current;
    } else {
      // 同步到 ref
      lastActivityRef.current = lastActivity;
    }

    const now = Date.now();
    const idleTime = now - lastActivity;

    if (idleTime > idleTimeout) {
      const idleHours = (idleTime / (60 * 60 * 1000)).toFixed(1);
      console.log(
        `🔄 [${storageKey || 'useIdleReset'}] 閒置超時 (${idleHours} 小時)，` +
        `自動重置對話並清除訊息`
      );
      
      // 執行重置回調
      if (onReset && typeof onReset === 'function') {
        onReset();
      }
      
      // 更新活動時間（重置後重新開始計時）
      updateLastActivity();
      
      return true; // 表示已重置
    }

    return false; // 未重置
  }, [enabled, idleTimeout, storageKey, onReset, getLastActivityFromStorage, updateLastActivity]);

  /**
   * 獲取當前閒置時間（毫秒）
   */
  const getIdleTime = useCallback(() => {
    const lastActivity = getLastActivityFromStorage() || lastActivityRef.current;
    return Date.now() - lastActivity;
  }, [getLastActivityFromStorage]);

  /**
   * 獲取當前閒置時間（小時，便於顯示）
   */
  const getIdleTimeHours = useCallback(() => {
    return (getIdleTime() / (60 * 60 * 1000)).toFixed(1);
  }, [getIdleTime]);

  // 初始化：頁面載入時從 localStorage 恢復並檢查
  useEffect(() => {
    if (hasInitializedRef.current) return;
    hasInitializedRef.current = true;

    // 從 localStorage 恢復上次活動時間
    const stored = getLastActivityFromStorage();
    if (stored) {
      lastActivityRef.current = stored;
      console.log(
        `📋 [${storageKey || 'useIdleReset'}] 恢復上次活動時間: ` +
        `${new Date(stored).toLocaleString()}`
      );
    } else {
      // 首次使用，記錄當前時間
      updateLastActivity();
    }

    // 頁面載入時立即檢查是否需要重置
    checkAndReset();
  }, [storageKey, getLastActivityFromStorage, updateLastActivity, checkAndReset]);

  return {
    updateLastActivity,
    checkAndReset,
    getIdleTime,
    getIdleTimeHours
  };
};

export default useIdleReset;
