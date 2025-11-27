import { useState, useCallback } from 'react';

/**
 * 圖片管理狀態 Hook
 * 處理圖片上傳、管理、內容更新等功能
 * 
 * @param {Object} editorRef - Markdown 編輯器的 ref 對象
 * @param {Function} setFormData - 更新表單資料的函數
 * @param {Array} externalImages - 外部傳入的圖片列表（來自 useContentEditor）
 * @param {Function} setExternalImages - 外部圖片列表的更新函數（來自 useContentEditor）
 * @returns {Object} 圖片管理相關的狀態和方法
 */
const useImageManager = (editorRef, setFormData, externalImages, setExternalImages) => {
  const [drawerVisible, setDrawerVisible] = useState(false);
  
  // ✅ 使用外部傳入的 images 和 setImages，不再維護內部 state
  const images = externalImages;
  const setImages = setExternalImages;

  /**
   * 處理圖片列表變更
   * @param {Array} newImages - 新的圖片列表
   */
  const handleImagesChange = useCallback((newImages) => {
    setImages(newImages);
    console.log('✅ 圖片列表已更新 (useImageManager):', newImages);
  }, [setImages]);

  /**
   * 處理內容更新 (當圖片操作導致內容變化時)
   * @param {string} updatedContent - 更新後的內容
   */
  const handleContentUpdate = useCallback((updatedContent) => {
    // 更新表單資料
    setFormData(prev => ({
      ...prev,
      content: updatedContent
    }));
    
    // 更新編輯器內容
    if (editorRef?.current) {
      editorRef.current.setText(updatedContent);
    }
    
    console.log('內容已自動更新圖片引用');
  }, [editorRef, setFormData]);

  /**
   * 切換圖片管理面板的顯示狀態
   */
  const toggleDrawer = useCallback(() => {
    setDrawerVisible(prev => !prev);
  }, []);

  /**
   * 開啟圖片管理面板
   */
  const openDrawer = useCallback(() => {
    setDrawerVisible(true);
  }, []);

  /**
   * 關閉圖片管理面板
   */
  const closeDrawer = useCallback(() => {
    setDrawerVisible(false);
  }, []);

  /**
   * 添加圖片到列表
   * @param {Object|Array} newImage - 要添加的圖片或圖片陣列
   */
  const addImages = useCallback((newImage) => {
    if (Array.isArray(newImage)) {
      setImages(prev => [...prev, ...newImage]);
    } else {
      setImages(prev => [...prev, newImage]);
    }
  }, []);

  /**
   * 從列表中移除圖片
   * @param {string|number} imageId - 要移除的圖片 ID
   */
  const removeImage = useCallback((imageId) => {
    setImages(prev => prev.filter(img => img.id !== imageId));
  }, []);

  /**
   * 更新特定圖片的資料
   * @param {string|number} imageId - 圖片 ID
   * @param {Object} updates - 要更新的資料
   */
  const updateImage = useCallback((imageId, updates) => {
    setImages(prev => 
      prev.map(img => 
        img.id === imageId ? { ...img, ...updates } : img
      )
    );
  }, []);

  /**
   * 清空所有圖片
   */
  const clearImages = useCallback(() => {
    setImages([]);
  }, []);

  /**
   * 根據 ID 查找圖片
   * @param {string|number} imageId - 圖片 ID
   * @returns {Object|undefined} 找到的圖片對象
   */
  const findImageById = useCallback((imageId) => {
    return images.find(img => img.id === imageId);
  }, [images]);

  /**
   * 獲取圖片統計資訊
   * @returns {Object} 統計資訊
   */
  const getImageStats = useCallback(() => {
    const totalCount = images.length;
    const totalSize = images.reduce((sum, img) => sum + (img.size || 0), 0);
    
    return {
      totalCount,
      totalSize,
      averageSize: totalCount > 0 ? totalSize / totalCount : 0
    };
  }, [images]);

  /**
   * 驗證圖片是否符合限制
   * @param {Object} options - 驗證選項
   * @param {number} options.maxImages - 最大圖片數量
   * @param {number} options.maxSizeMB - 單個圖片最大大小 (MB)
   * @param {Array} options.allowedTypes - 允許的檔案類型
   */
  const validateImageConstraints = useCallback((options = {}) => {
    const { maxImages = 10, maxSizeMB = 2, allowedTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'] } = options;
    const errors = [];

    // 檢查圖片數量限制
    if (images.length >= maxImages) {
      errors.push(`圖片數量已達上限 (${maxImages} 張)`);
    }

    // 檢查圖片大小和類型
    images.forEach((img, index) => {
      if (img.size && img.size > maxSizeMB * 1024 * 1024) {
        errors.push(`圖片 ${index + 1} 超過大小限制 (${maxSizeMB}MB)`);
      }
      
      if (img.type && !allowedTypes.includes(img.type)) {
        errors.push(`圖片 ${index + 1} 格式不支援`);
      }
    });

    return {
      isValid: errors.length === 0,
      errors,
      canAddMore: images.length < maxImages
    };
  }, [images]);

  /**
   * 批量處理圖片操作
   * @param {string} action - 操作類型 ('delete', 'update')
   * @param {Array} imageIds - 圖片 ID 陣列
   * @param {Object} data - 操作相關資料
   */
  const batchImageOperation = useCallback((action, imageIds, data = {}) => {
    switch (action) {
      case 'delete':
        setImages(prev => prev.filter(img => !imageIds.includes(img.id)));
        break;
      case 'update':
        setImages(prev => 
          prev.map(img => 
            imageIds.includes(img.id) ? { ...img, ...data } : img
          )
        );
        break;
      default:
        console.warn('未知的批量操作:', action);
    }
  }, []);

  return {
    // 狀態
    drawerVisible,
    images,
    
    // 面板控制方法
    toggleDrawer,
    openDrawer,
    closeDrawer,
    
    // 圖片操作方法
    handleImagesChange,
    handleContentUpdate,
    addImages,
    removeImage,
    updateImage,
    clearImages,
    
    // 查詢和工具方法
    findImageById,
    getImageStats,
    validateImageConstraints,
    batchImageOperation,
    
    // 狀態設定器 (如果需要直接控制)
    setDrawerVisible,
    setImages
  };
};

export default useImageManager;