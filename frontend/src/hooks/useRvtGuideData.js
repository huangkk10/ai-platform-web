import { useState, useCallback } from 'react';
import { message } from 'antd';
import axios from 'axios';

/**
 * RVT Guide 資料管理 Hook
 * 處理資料的載入、儲存、更新等 CRUD 操作
 * 
 * @param {string|undefined} id - RVT Guide 的 ID (編輯模式時提供)
 * @param {Function} navigate - React Router 的導航函數
 * @returns {Object} 資料管理相關的狀態和方法
 */
const useRvtGuideData = (id, navigate) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: ''
  });
  const [images, setImages] = useState([]);

  const isEditMode = Boolean(id);

  /**
   * 載入 RVT Guide 資料（編輯模式）
   */
  const loadGuideData = useCallback(async () => {
    if (!isEditMode) return;

    setLoading(true);
    try {
      console.log('🔍 載入 RVT Guide 資料，ID:', id);
      
      // 同時載入基本資料和圖片資料
      const [guideResponse, imagesResponse] = await Promise.all([
        axios.get(`/api/rvt-guides/${id}/`),
        axios.get(`/api/content-images/?content_type=rvt-guide&content_id=${id}`)
      ]);
      
      console.log('📄 載入的資料:', guideResponse.data);
      console.log('🖼️ 載入的圖片:', imagesResponse.data);
      
      setFormData({
        title: guideResponse.data.title || '',
        content: guideResponse.data.content || ''
      });

      // 設定圖片資料
      if (imagesResponse.data.results) {
        setImages(imagesResponse.data.results);
      } else if (Array.isArray(imagesResponse.data)) {
        setImages(imagesResponse.data);
      }
      
      // 資料載入成功不需要顯示提示（這是正常行為）
      console.log('✅ 資料載入完成');
      return guideResponse.data;
    } catch (error) {
      console.error('❌ 載入資料失敗:', error);
      message.error('載入資料失敗');
      
      // 如果載入失敗，返回列表頁
      if (navigate) {
        navigate('/knowledge/rvt-guide');
      }
      
      throw error;
    } finally {
      setLoading(false);
    }
  }, [id, isEditMode, navigate]);

  /**
   * 儲存 RVT Guide 資料
   * @param {Object} dataToSave - 要儲存的資料 {title, content}
   * @param {Object} options - 儲存選項
   * @param {boolean} options.navigateAfterSave - 儲存後是否導航到列表頁
   * @param {string} options.redirectPath - 自定義重定向路徑
   */
  const saveGuideData = useCallback(async (dataToSave, options = {}) => {
    const { navigateAfterSave = true, redirectPath = '/knowledge/rvt-log' } = options;

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
      const saveData = {
        title: dataToSave.title.trim(),
        content: dataToSave.content.trim(),
        // 如果是新建記錄，設置默認值
        ...(isEditMode ? {} : {
          category: 'general',
          issue_type: 'guide',
          description: dataToSave.title.trim()
        })
      };

      console.log('💾 準備儲存資料:', saveData);

      let response;
      if (isEditMode) {
        // 更新現有記錄
        response = await axios.put(`/api/rvt-guides/${id}/`, saveData);
        console.log('✅ 更新成功:', response.data);
        message.success('更新成功！');
      } else {
        // 創建新記錄
        response = await axios.post('/api/rvt-guides/', saveData);
        console.log('✅ 創建成功:', response.data);
        message.success('創建成功！');
      }

      // 更新本地狀態
      setFormData(prev => ({
        ...prev,
        title: saveData.title,
        content: saveData.content
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
  }, [id, isEditMode, navigate]);

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
    const value = e.target?.value || e;
    updateFormData({ title: value });
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
    // 狀態
    loading,
    saving,
    formData,
    images,
    isEditMode,
    
    // 資料操作方法
    loadGuideData,
    saveGuideData,
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

export default useRvtGuideData;