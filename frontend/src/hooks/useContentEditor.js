/**
 * 通用內容編輯器 Hook
 * 基於 useRvtGuideData 重構，支援多種內容類型
 * 
 * 使用範例：
 * const editor = useContentEditor('rvt-guide', id, navigate);
 * const protocolEditor = useContentEditor('protocol-guide', id, navigate);
 */

import { useState, useCallback } from 'react';
import { message } from 'antd';
import axios from 'axios';
import { getEditorConfig } from '../config/editorConfig';

/**
 * 通用內容編輯器 Hook
 * @param {string} contentType - 內容類型 ('rvt-guide', 'protocol-guide', etc.)
 * @param {string|undefined} contentId - 內容 ID (編輯模式時提供)
 * @param {Function} navigate - React Router 的導航函數
 * @param {object} customConfig - 自定義配置（可選）
 * @returns {Object} 編輯器狀態和方法
 */
const useContentEditor = (contentType, contentId, navigate, customConfig = {}) => {
  // 獲取配置
  const config = getEditorConfig(contentType, customConfig);
  
  // 狀態管理
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: ''
  });
  const [images, setImages] = useState([]);

  const isEditMode = Boolean(contentId);

  /**
   * 載入內容資料（編輯模式）
   */
  const loadData = useCallback(async () => {
    if (!isEditMode) return;

    setLoading(true);
    try {
      console.log(`🔍 載入 ${contentType} 資料，ID:`, contentId);
      
      // 同時載入基本資料和圖片資料
      const [contentResponse, imagesResponse] = await Promise.all([
        axios.get(`${config.apiEndpoint}${contentId}/`),
        axios.get(`${config.imageEndpoint}?content_type=${contentType}&content_id=${contentId}`)
      ]);
      
      console.log('📄 載入的資料:', contentResponse.data);
      console.log('🖼️ 載入的圖片:', imagesResponse.data);
      
      // 確保 title 和 content 永遠是字串，避免出現 [object Object]
      const responseData = contentResponse.data;
      setFormData({
        title: String(responseData.title || ''),
        content: String(responseData.content || ''),
        ...responseData  // 保留其他欄位
      });

      // 設定圖片資料
      if (imagesResponse.data.results) {
        setImages(imagesResponse.data.results);
      } else if (Array.isArray(imagesResponse.data)) {
        setImages(imagesResponse.data);
      }
      
      console.log('✅ 資料載入完成');
      return contentResponse.data;
    } catch (error) {
      console.error('❌ 載入資料失敗:', error);
      message.error(`載入${config.labels.createTitle}失敗`);
      
      // 如果載入失敗，返回列表頁
      if (navigate) {
        navigate(config.listRoute);
      }
      
      throw error;
    } finally {
      setLoading(false);
    }
  }, [contentId, isEditMode, contentType, config.apiEndpoint, config.imageEndpoint, config.labels.createTitle, config.listRoute, navigate]);

  /**
   * 儲存內容資料
   * @param {Object} dataToSave - 要儲存的資料 {title, content, ...}
   * @param {Object} options - 儲存選項
   * @param {boolean} options.navigateAfterSave - 儲存後是否導航到列表頁
   * @param {string} options.redirectPath - 自定義重定向路徑
   * @returns {Promise<Object|false>} 儲存成功返回資料，失敗返回 false
   */
  const saveData = useCallback(async (dataToSave, options = {}) => {
    const { navigateAfterSave = true, redirectPath = config.listRoute } = options;

    // 驗證必填欄位
    if (!dataToSave.title?.trim()) {
      message.error('請輸入標題');
      return false;
    }

    if (!dataToSave.content?.trim()) {
      message.error('請輸入內容');
      return false;
    }

    setSaving(true);

    try {
      const savePayload = {
        title: dataToSave.title.trim(),
        content: dataToSave.content.trim(),
        // 如果是新建記錄，合併默認值
        ...(isEditMode ? {} : config.defaults),
        // 合併其他欄位
        ...dataToSave
      };

      console.log(`💾 準備儲存 ${contentType} 資料:`, savePayload);

      let response;
      if (isEditMode) {
        // 更新現有記錄
        response = await axios.put(`${config.apiEndpoint}${contentId}/`, savePayload);
        console.log('✅ 更新成功:', response.data);
        message.success('更新成功！');
      } else {
        // 創建新記錄
        response = await axios.post(config.apiEndpoint, savePayload);
        console.log('✅ 創建成功:', response.data);
        message.success('創建成功！');
      }

      // 更新本地狀態
      setFormData(prev => ({
        ...prev,
        title: savePayload.title,
        content: savePayload.content
      }));

      // 導航到指定頁面
      if (navigateAfterSave && navigate) {
        navigate(redirectPath);
      }

      return response.data;
      
    } catch (error) {
      console.error('❌ 儲存失敗:', error);
      
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          // 處理字段驗證錯誤
          Object.keys(errorData).forEach(field => {
            const fieldErrors = Array.isArray(errorData[field]) 
              ? errorData[field].join(', ')
              : errorData[field];
            message.error(`${field}: ${fieldErrors}`);
          });
        } else {
          message.error(`儲存失敗: ${errorData}`);
        }
      } else {
        message.error('儲存失敗，請稍後再試');
      }
      
      return false;
    } finally {
      setSaving(false);
    }
  }, [contentId, isEditMode, contentType, config.apiEndpoint, config.defaults, config.listRoute, navigate]);

  /**
   * 更新表單資料
   * @param {Object} updates - 要更新的資料
   */
  const updateFormData = useCallback((updates) => {
    setFormData(prev => ({
      ...prev,
      ...updates
    }));
  }, []);

  /**
   * 重置表單資料
   */
  const resetFormData = useCallback(() => {
    setFormData({
      title: '',
      content: ''
    });
    setImages([]);
  }, []);

  /**
   * 處理標題改變
   */
  const handleTitleChange = useCallback((e) => {
    // 確保永遠是字串，避免出現 [object Object]
    const value = e.target?.value ?? e;
    const stringValue = typeof value === 'string' ? value : '';
    updateFormData({ title: stringValue });
  }, [updateFormData]);

  /**
   * 處理內容改變
   */
  const handleContentChange = useCallback(({ text }) => {
    updateFormData({ content: text });
  }, [updateFormData]);

  /**
   * 檢查資料是否有變更
   * @param {Object} originalData - 原始資料
   */
  const hasChanges = useCallback((originalData) => {
    if (!originalData) return formData.title || formData.content;
    
    return (
      formData.title !== (originalData.title || '') ||
      formData.content !== (originalData.content || '')
    );
  }, [formData]);

  /**
   * 驗證表單資料
   */
  const validateFormData = useCallback(() => {
    const errors = [];
    
    if (!formData.title?.trim()) {
      errors.push('請輸入標題');
    }
    
    if (!formData.content?.trim()) {
      errors.push('請輸入內容');
    }
    
    return {
      isValid: errors.length === 0,
      errors
    };
  }, [formData]);

  return {
    // 配置
    config,
    
    // 狀態
    loading,
    saving,
    formData,
    images,
    isEditMode,
    
    // 資料操作方法
    loadData,
    saveData,
    updateFormData,
    resetFormData,
    
    // 表單處理方法
    handleTitleChange,
    handleContentChange,
    
    // 工具方法
    hasChanges,
    validateFormData,
    
    // 狀態設定器 (如果需要直接控制)
    setFormData,
    setImages,
    setLoading,
    setSaving
  };
};

export default useContentEditor;
