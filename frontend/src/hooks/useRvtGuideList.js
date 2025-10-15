import { useState, useCallback } from 'react';
import { message } from 'antd';
import axios from 'axios';

/**
 * RVT Guide 列表數據管理 Hook
 * 處理列表的 CRUD 操作
 * 
 * @param {boolean} initialized - 認證系統是否已初始化
 * @param {boolean} isAuthenticated - 用戶是否已認證
 * @returns {Object} 包含數據和操作方法的對象
 */
const useRvtGuideList = (initialized, isAuthenticated) => {
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(false);

  /**
   * 獲取指導文檔列表
   */
  const fetchGuides = useCallback(async () => {
    if (!initialized || !isAuthenticated) return;
    
    setLoading(true);
    try {
      // 添加 page_size 參數來覆蓋預設分頁限制
      const response = await axios.get('/api/rvt-guides/?page_size=100');
      setGuides(response.data.results || response.data);
      console.log('✅ RVT Guide 列表載入成功');
    } catch (error) {
      console.error('❌ 獲取 RVT Guide 資料失敗:', error);
      message.error('獲取資料失敗');
    } finally {
      setLoading(false);
    }
  }, [initialized, isAuthenticated]);

  /**
   * 獲取單個指導文檔的詳細資料
   * @param {number} id - 文檔 ID
   * @returns {Promise<Object>} 文檔詳細資料
   */
  const getGuideDetail = useCallback(async (id) => {
    try {
      const response = await axios.get(`/api/rvt-guides/${id}/`);
      console.log('✅ 文檔詳細資料載入成功:', id);
      return response.data;
    } catch (error) {
      console.error('❌ 獲取詳細資料失敗:', error);
      message.error('獲取詳細資料失敗');
      throw error;
    }
  }, []);

  /**
   * 刪除指導文檔
   * @param {number} id - 文檔 ID
   * @param {string} title - 文檔標題（用於確認提示）
   * @returns {Promise<boolean>} 是否刪除成功
   */
  const deleteGuide = useCallback(async (id, title) => {
    try {
      await axios.delete(`/api/rvt-guides/${id}/`);
      message.success('刪除成功');
      console.log('✅ 文檔刪除成功:', title);
      
      // 從本地狀態中移除已刪除的項目
      setGuides(prevGuides => prevGuides.filter(guide => guide.id !== id));
      
      return true;
    } catch (error) {
      console.error('❌ 刪除失敗:', error);
      message.error('刪除失敗');
      return false;
    }
  }, []);

  return {
    // 狀態
    guides,
    loading,
    
    // 操作方法
    fetchGuides,
    getGuideDetail,
    deleteGuide,
    
    // 狀態設定器（如果需要直接操作）
    setGuides,
    setLoading
  };
};

export default useRvtGuideList;
