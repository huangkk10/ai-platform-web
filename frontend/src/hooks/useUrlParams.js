/**
 * useUrlParams Hook
 * 
 * 功能：管理 URL Query Parameters，實現頁面狀態持久化
 * 優勢：
 * - 支援 F5 刷新後保持狀態
 * - 支援複製 URL 分享搜尋結果
 * - 支援瀏覽器前進/後退
 * - 自動同步 URL 和 State
 */

import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

/**
 * 使用 URL 參數管理狀態
 * @param {string} key - URL 參數的 key
 * @param {*} defaultValue - 預設值
 * @param {number} debounceMs - 防抖延遲時間（毫秒），預設 0（不防抖）
 * @returns {[value, setValue]} - 類似 useState 的返回值
 */
export const useUrlParam = (key, defaultValue = '', debounceMs = 0) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const debounceTimerRef = useCallback(() => ({ current: null }), [])();
  
  // 從 URL 讀取初始值
  const getInitialValue = useCallback(() => {
    const paramValue = searchParams.get(key);
    
    // 如果 URL 中沒有此參數，使用預設值
    if (paramValue === null) {
      return defaultValue;
    }
    
    // 處理布林值
    if (defaultValue === true || defaultValue === false) {
      return paramValue === 'true';
    }
    
    // 處理數字
    if (typeof defaultValue === 'number') {
      const num = Number(paramValue);
      return isNaN(num) ? defaultValue : num;
    }
    
    // 處理陣列（逗號分隔）
    if (Array.isArray(defaultValue)) {
      return paramValue ? paramValue.split(',').filter(Boolean) : defaultValue;
    }
    
    // 處理物件（JSON）
    if (typeof defaultValue === 'object' && defaultValue !== null) {
      try {
        return JSON.parse(decodeURIComponent(paramValue));
      } catch {
        return defaultValue;
      }
    }
    
    // 字串類型（預設）
    return paramValue;
  }, [searchParams, key, defaultValue]);
  
  const [value, setValue] = useState(getInitialValue);
  
  // 更新 URL 參數
  const updateUrlParam = useCallback((newValue) => {
    setValue(newValue);
    
    // 如果設定了防抖，延遲更新 URL
    if (debounceMs > 0) {
      // 清除之前的定時器
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
      
      // 設定新的定時器
      debounceTimerRef.current = setTimeout(() => {
        updateUrl(newValue);
      }, debounceMs);
    } else {
      // 沒有防抖，立即更新
      updateUrl(newValue);
    }
  }, [debounceMs, debounceTimerRef]);
  
  // 實際更新 URL 的函數
  const updateUrl = useCallback((newValue) => {
    const newSearchParams = new URLSearchParams(searchParams);
    
    // 如果值為空或等於預設值，移除 URL 參數（保持 URL 簡潔）
    const shouldRemove = 
      newValue === '' || 
      newValue === null || 
      newValue === undefined ||
      newValue === defaultValue ||
      (Array.isArray(newValue) && newValue.length === 0);
    
    if (shouldRemove) {
      newSearchParams.delete(key);
    } else {
      // 處理不同類型的值
      let paramValue;
      
      if (Array.isArray(newValue)) {
        paramValue = newValue.join(',');
      } else if (typeof newValue === 'object' && newValue !== null) {
        paramValue = encodeURIComponent(JSON.stringify(newValue));
      } else {
        paramValue = String(newValue);
      }
      
      newSearchParams.set(key, paramValue);
    }
    
    // 更新 URL（不會觸發頁面重新載入）
    setSearchParams(newSearchParams, { replace: true });
  }, [searchParams, setSearchParams, key, defaultValue]);
  
  // 清理定時器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, [debounceTimerRef]);
  
  return [value, updateUrlParam];
};

/**
 * 批量管理多個 URL 參數
 * @param {Object} paramConfig - 參數配置 { key: defaultValue }
 * @returns {Object} - { values, setParam, setParams, clearParams }
 */
export const useUrlParams = (paramConfig = {}) => {
  const [searchParams, setSearchParams] = useSearchParams();
  
  // 從 URL 讀取所有參數
  const getValues = useCallback(() => {
    const values = {};
    
    Object.entries(paramConfig).forEach(([key, defaultValue]) => {
      const paramValue = searchParams.get(key);
      
      if (paramValue === null) {
        values[key] = defaultValue;
      } else {
        // 根據預設值類型解析參數
        if (typeof defaultValue === 'boolean') {
          values[key] = paramValue === 'true';
        } else if (typeof defaultValue === 'number') {
          const num = Number(paramValue);
          values[key] = isNaN(num) ? defaultValue : num;
        } else if (Array.isArray(defaultValue)) {
          values[key] = paramValue ? paramValue.split(',').filter(Boolean) : defaultValue;
        } else if (typeof defaultValue === 'object' && defaultValue !== null) {
          try {
            values[key] = JSON.parse(decodeURIComponent(paramValue));
          } catch {
            values[key] = defaultValue;
          }
        } else {
          values[key] = paramValue;
        }
      }
    });
    
    return values;
  }, [searchParams, paramConfig]);
  
  const [values, setValues] = useState(getValues);
  
  // 監聽 URL 變化（處理瀏覽器前進/後退）
  useEffect(() => {
    setValues(getValues());
  }, [searchParams, getValues]);
  
  // 更新單個參數
  const setParam = useCallback((key, value) => {
    const newSearchParams = new URLSearchParams(searchParams);
    const defaultValue = paramConfig[key];
    
    // 判斷是否應該移除參數
    const shouldRemove = 
      value === '' || 
      value === null || 
      value === undefined ||
      value === defaultValue ||
      (Array.isArray(value) && value.length === 0);
    
    if (shouldRemove) {
      newSearchParams.delete(key);
    } else {
      let paramValue;
      
      if (Array.isArray(value)) {
        paramValue = value.join(',');
      } else if (typeof value === 'object' && value !== null) {
        paramValue = encodeURIComponent(JSON.stringify(value));
      } else {
        paramValue = String(value);
      }
      
      newSearchParams.set(key, paramValue);
    }
    
    setSearchParams(newSearchParams, { replace: true });
  }, [searchParams, setSearchParams, paramConfig]);
  
  // 批量更新參數
  const setParams = useCallback((updates) => {
    const newSearchParams = new URLSearchParams(searchParams);
    
    Object.entries(updates).forEach(([key, value]) => {
      const defaultValue = paramConfig[key];
      
      const shouldRemove = 
        value === '' || 
        value === null || 
        value === undefined ||
        value === defaultValue ||
        (Array.isArray(value) && value.length === 0);
      
      if (shouldRemove) {
        newSearchParams.delete(key);
      } else {
        let paramValue;
        
        if (Array.isArray(value)) {
          paramValue = value.join(',');
        } else if (typeof value === 'object' && value !== null) {
          paramValue = encodeURIComponent(JSON.stringify(value));
        } else {
          paramValue = String(value);
        }
        
        newSearchParams.set(key, paramValue);
      }
    });
    
    setSearchParams(newSearchParams, { replace: true });
  }, [searchParams, setSearchParams, paramConfig]);
  
  // 清除所有參數（回到預設狀態）
  const clearParams = useCallback(() => {
    setSearchParams({}, { replace: true });
  }, [setSearchParams]);
  
  return {
    values,
    setParam,
    setParams,
    clearParams,
  };
};

export default useUrlParams;
