import { useState, useCallback } from 'react';
import { message } from 'antd';
import axios from 'axios';

/**
 * 通用知識庫列表數據管理 Hook
 * 
 * 支持配置驅動的 CRUD 操作，可用於任何知識庫系統
 * 
 * @param {Object} config - 知識庫配置對象（來自 knowledgeBaseConfig.js）
 * @param {boolean} initialized - 認證系統是否已初始化
 * @param {boolean} isAuthenticated - 用戶是否已認證
 * @returns {Object} 包含數據和操作方法的對象
 * 
 * @example
 * import { knowledgeBaseConfigs } from '@/config/knowledgeBaseConfig';
 * import useKnowledgeBaseList from '@/hooks/useKnowledgeBaseList';
 * 
 * const config = knowledgeBaseConfigs['rvt-assistant'];
 * const { items, loading, fetchItems, getItemDetail, deleteItem } = 
 *   useKnowledgeBaseList(config, initialized, isAuthenticated);
 */
const useKnowledgeBaseList = (config, initialized, isAuthenticated) => {
  // 驗證配置
  if (!config) {
    console.error('❌ useKnowledgeBaseList: config 參數為必需');
    throw new Error('useKnowledgeBaseList 需要 config 參數');
  }

  if (!config.apiEndpoint) {
    console.error('❌ useKnowledgeBaseList: config.apiEndpoint 未定義');
    throw new Error('config.apiEndpoint 為必需參數');
  }

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);

  /**
   * 獲取列表數據
   */
  const fetchItems = useCallback(async () => {
    if (!initialized || !isAuthenticated) {
      console.log('⏸️ 未初始化或未認證，跳過數據載入');
      return;
    }
    
    setLoading(true);
    try {
      // 使用配置中的 API endpoint 和 pageSize
      const pageSize = config.pageSize || 100;
      const url = `${config.apiEndpoint}?page_size=${pageSize}`;
      
      console.log(`📡 正在載入數據: ${url}`);
      const response = await axios.get(url);
      
      // 支持分頁和非分頁響應格式
      const data = response.data.results || response.data;
      setItems(data);
      
      // 使用配置中的成功訊息
      const successMsg = config.labels?.fetchSuccess || '列表載入成功';
      console.log(`✅ ${successMsg}`);
    } catch (error) {
      console.error('❌ 獲取數據失敗:', error);
      
      // 使用配置中的失敗訊息
      const errorMsg = config.labels?.fetchFailed || '獲取資料失敗';
      message.error(errorMsg);
    } finally {
      setLoading(false);
    }
  }, [config, initialized, isAuthenticated]);

  /**
   * 獲取單個項目的詳細資料
   * @param {number|string} id - 項目 ID
   * @returns {Promise<Object>} 項目詳細資料
   */
  const getItemDetail = useCallback(async (id) => {
    try {
      const url = `${config.apiEndpoint}${id}/`;
      console.log(`📡 正在載入詳細資料: ${url}`);
      
      const response = await axios.get(url);
      
      // 使用配置中的成功訊息
      const successMsg = config.labels?.detailSuccess || '詳細資料載入成功';
      console.log(`✅ ${successMsg}:`, id);
      
      return response.data;
    } catch (error) {
      console.error('❌ 獲取詳細資料失敗:', error);
      
      // 使用配置中的失敗訊息
      const errorMsg = config.labels?.detailFailed || '獲取詳細資料失敗';
      message.error(errorMsg);
      
      throw error;
    }
  }, [config]);

  /**
   * 刪除項目
   * @param {number|string} id - 項目 ID
   * @param {string} title - 項目標題（用於日誌和提示）
   * @returns {Promise<boolean>} 是否刪除成功
   */
  const deleteItem = useCallback(async (id, title) => {
    try {
      const url = `${config.apiEndpoint}${id}/`;
      console.log(`🗑️ 正在刪除: ${url}`);
      
      await axios.delete(url);
      
      // 使用配置中的成功訊息
      const successMsg = config.labels?.deleteSuccess || '刪除成功';
      message.success(successMsg);
      console.log(`✅ 刪除成功:`, title);
      
      // 從本地狀態中移除已刪除的項目
      setItems(prevItems => prevItems.filter(item => item.id !== id));
      
      return true;
    } catch (error) {
      console.error('❌ 刪除失敗:', error);
      
      // 使用配置中的失敗訊息
      const errorMsg = config.labels?.deleteFailed || '刪除失敗';
      message.error(errorMsg);
      
      return false;
    }
  }, [config]);

  /**
   * 更新項目（可選功能，未來擴展）
   * @param {number|string} id - 項目 ID
   * @param {Object} data - 更新的數據
   * @returns {Promise<Object>} 更新後的項目
   */
  const updateItem = useCallback(async (id, data) => {
    try {
      const url = `${config.apiEndpoint}${id}/`;
      console.log(`📝 正在更新: ${url}`);
      
      const response = await axios.patch(url, data);
      
      message.success(config.labels?.updateSuccess || '更新成功');
      console.log(`✅ 更新成功:`, id);
      
      // 更新本地狀態
      setItems(prevItems => 
        prevItems.map(item => item.id === id ? response.data : item)
      );
      
      return response.data;
    } catch (error) {
      console.error('❌ 更新失敗:', error);
      message.error(config.labels?.updateFailed || '更新失敗');
      throw error;
    }
  }, [config]);

  /**
   * 創建新項目（可選功能，未來擴展）
   * @param {Object} data - 新項目數據
   * @returns {Promise<Object>} 創建的項目
   */
  const createItem = useCallback(async (data) => {
    try {
      console.log(`➕ 正在創建新項目: ${config.apiEndpoint}`);
      
      const response = await axios.post(config.apiEndpoint, data);
      
      message.success(config.labels?.createSuccess || '創建成功');
      console.log(`✅ 創建成功`);
      
      // 添加到本地狀態
      setItems(prevItems => [response.data, ...prevItems]);
      
      return response.data;
    } catch (error) {
      console.error('❌ 創建失敗:', error);
      message.error(config.labels?.createFailed || '創建失敗');
      throw error;
    }
  }, [config]);

  return {
    // ===== 狀態 =====
    items,          // 項目列表
    loading,        // 載入狀態
    
    // ===== 核心操作方法 =====
    fetchItems,     // 獲取列表
    getItemDetail,  // 獲取詳細資料
    deleteItem,     // 刪除項目
    
    // ===== 可選操作方法（未來擴展） =====
    updateItem,     // 更新項目
    createItem,     // 創建項目
    
    // ===== 狀態設定器（高級用法） =====
    setItems,       // 直接設定項目列表
    setLoading,     // 直接設定載入狀態
  };
};

export default useKnowledgeBaseList;
