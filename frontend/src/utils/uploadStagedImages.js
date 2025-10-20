/**
 * 暫存圖片上傳工具
 * 用於新建文檔時批量上傳暫存的圖片
 */

import axios from 'axios';
import { message } from 'antd';

/**
 * 獲取內容 API 端點
 * @param {string} contentType - 內容類型
 * @returns {string} API 端點
 */
const getContentApiEndpoint = (contentType) => {
  switch (contentType) {
    case 'rvt-guide':
      return '/api/rvt-guides/';
    case 'protocol-guide':
      return '/api/protocol-guides/';
    default:
      console.warn(`⚠️ 未知的內容類型: ${contentType}`);
      return `/api/${contentType}s/`;
  }
};

/**
 * 替換內容中的圖片 ID（temp_xxx → 實際 ID）
 * @param {number|string} contentId - 內容 ID
 * @param {string} contentType - 內容類型
 * @param {Object} imageIdMap - 圖片 ID 映射 {temp_xxx: 實際ID}
 * @returns {Promise<void>}
 */
const replaceImageIdsInContent = async (contentId, contentType, imageIdMap) => {
  if (!imageIdMap || Object.keys(imageIdMap).length === 0) {
    console.log('📭 沒有需要替換的圖片 ID');
    return;
  }

  try {
    // 1. 獲取當前文檔內容
    const contentEndpoint = getContentApiEndpoint(contentType);
    const getResponse = await axios.get(`${contentEndpoint}${contentId}/`, {
      withCredentials: true,
    });

    let currentContent = getResponse.data.content || '';
    console.log('📄 當前內容長度:', currentContent.length);

    // 2. 替換所有 temp_ ID 為實際 ID
    let updatedContent = currentContent;
    let replacementCount = 0;

    for (const [tempId, realId] of Object.entries(imageIdMap)) {
      const tempPattern = new RegExp(`\\[IMG:${tempId}\\]`, 'g');
      const matches = updatedContent.match(tempPattern);
      
      if (matches) {
        updatedContent = updatedContent.replace(tempPattern, `[IMG:${realId}]`);
        replacementCount += matches.length;
        console.log(`🔄 替換: [IMG:${tempId}] → [IMG:${realId}] (${matches.length} 處)`);
      }
    }

    // 3. 如果有替換，更新文檔
    if (replacementCount > 0) {
      console.log(`📝 總共替換 ${replacementCount} 處圖片引用，準備更新文檔...`);
      
      await axios.put(
        `${contentEndpoint}${contentId}/`,
        { content: updatedContent },
        { withCredentials: true }
      );

      console.log('✅ 文檔內容更新成功');
    } else {
      console.log('ℹ️ 內容中沒有找到需要替換的 temp_ 標記');
    }
  } catch (error) {
    console.error('❌ 替換圖片 ID 時發生錯誤:', error);
    throw error;
  }
};

/**
 * 上傳暫存圖片
 * @param {number|string} contentId - 內容 ID
 * @param {string} contentType - 內容類型 ('rvt-guide', 'protocol-guide', etc.)
 * @param {Array} stagedImages - 暫存的圖片列表
 * @param {string} apiEndpoint - API 端點（可選，默認 /api/content-images/）
 * @returns {Promise<{success: number, failed: number, errors: Array, imageIdMap: Object}>}
 */
export const uploadStagedImages = async (
  contentId,
  contentType,
  stagedImages,
  apiEndpoint = '/api/content-images/'
) => {
  if (!stagedImages || stagedImages.length === 0) {
    console.log('📭 沒有暫存圖片需要上傳');
    return { success: 0, failed: 0, errors: [], imageIdMap: {} };
  }

  console.log(`📤 開始上傳暫存圖片: ${stagedImages.length} 張`);
  console.log(`   內容 ID: ${contentId}`);
  console.log(`   內容類型: ${contentType}`);

  // 顯示上傳進度提示
  const hideLoading = message.loading(
    `正在上傳圖片 (0/${stagedImages.length})...`,
    0
  );

  let successCount = 0;
  let failCount = 0;
  const errors = [];
  const imageIdMap = {}; // 🆕 儲存 temp_xxx → 實際 ID 的映射

  try {
    // 逐個上傳暫存圖片
    for (let i = 0; i < stagedImages.length; i++) {
      const stagedImage = stagedImages[i];

      try {
        const formData = new FormData();
        
        // 處理圖片文件
        let imageFile = stagedImage.file;
        
        // 如果沒有 file 屬性，從 Base64 創建 Blob
        if (!imageFile && stagedImage.data_url) {
          console.log('📦 從 Base64 創建 Blob:', stagedImage.filename);
          const base64Data = stagedImage.data_url.split(',')[1];
          const byteString = atob(base64Data);
          const mimeString = stagedImage.data_url.split(',')[0].split(':')[1].split(';')[0];
          const ab = new ArrayBuffer(byteString.length);
          const ia = new Uint8Array(ab);
          for (let j = 0; j < byteString.length; j++) {
            ia[j] = byteString.charCodeAt(j);
          }
          imageFile = new Blob([ab], { type: mimeString });
        }
        
        if (!imageFile) {
          throw new Error('無法獲取圖片文件');
        }
        
        formData.append('image', imageFile, stagedImage.filename);
        formData.append('content_type', contentType);
        formData.append('content_id', contentId);

        // 添加圖片元數據
        if (stagedImage.title) {
          formData.append('title', stagedImage.title);
        }
        if (stagedImage.description) {
          formData.append('description', stagedImage.description);
        }
        if (stagedImage.is_primary) {
          formData.append('is_primary', 'true');
        }

        // 上傳圖片
        const response = await axios.post(apiEndpoint, formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
          withCredentials: true,
        });

        // 🆕 保存 temp ID 到實際 ID 的映射
        const uploadedImageId = response.data.id;
        const tempId = stagedImage.id;
        
        if (tempId && String(tempId).startsWith('temp_')) {
          imageIdMap[tempId] = uploadedImageId;
          console.log(`🔗 ID 映射: ${tempId} → ${uploadedImageId}`);
        }

        successCount++;
        console.log(
          `✅ 圖片上傳成功 (${successCount}/${stagedImages.length}):`,
          stagedImage.filename,
          `(ID: ${uploadedImageId})`
        );

        // 更新進度提示
        hideLoading();
        message.loading(
          `正在上傳圖片 (${successCount}/${stagedImages.length})...`,
          0.5
        );
      } catch (error) {
        failCount++;
        const errorMsg = error.response?.data?.detail || error.message || '未知錯誤';
        errors.push({
          filename: stagedImage.filename,
          error: errorMsg,
        });
        console.error(
          `❌ 圖片上傳失敗 (${failCount}):`,
          stagedImage.filename,
          errorMsg
        );
      }
    }

    // 關閉進度提示
    hideLoading();

    // 🆕 如果有圖片上傳成功且存在 ID 映射，替換內容中的 temp_ 標記
    if (successCount > 0 && Object.keys(imageIdMap).length > 0) {
      try {
        console.log('🔄 開始替換內容中的圖片 ID...');
        await replaceImageIdsInContent(contentId, contentType, imageIdMap);
        console.log('✅ 內容中的圖片 ID 替換成功');
      } catch (error) {
        console.error('⚠️ 替換圖片 ID 失敗（不影響上傳）:', error);
        // 不拋出錯誤，因為圖片已經上傳成功
      }
    }

    // 顯示最終結果
    if (successCount > 0 && failCount === 0) {
      message.success(`文檔和 ${successCount} 張圖片已成功儲存！`);
    } else if (successCount > 0 && failCount > 0) {
      message.warning(`文檔已儲存，${successCount} 張圖片成功，${failCount} 張失敗`);
    } else if (failCount > 0) {
      message.error('文檔已儲存，但所有圖片上傳失敗');
    }

    return {
      success: successCount,
      failed: failCount,
      errors,
      imageIdMap, // 🆕 返回 ID 映射
    };
  } catch (error) {
    hideLoading();
    console.error('❌ 批量上傳過程異常:', error);
    message.error('文檔已儲存，但圖片上傳過程發生錯誤');

    return {
      success: successCount,
      failed: failCount + (stagedImages.length - successCount - failCount),
      errors: [...errors, { filename: 'unknown', error: error.message }],
      imageIdMap: {}, // 🆕 返回空映射
    };
  }
};

/**
 * 驗證暫存圖片
 * @param {Array} stagedImages - 暫存的圖片列表
 * @param {object} config - 配置 { maxImages, maxSizeMB, supportedFormats }
 * @returns {{valid: boolean, errors: Array}}
 */
export const validateStagedImages = (stagedImages, config = {}) => {
  const {
    maxImages = 10,
    maxSizeMB = 2,
    supportedFormats = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'],
  } = config;

  const errors = [];

  // 檢查數量
  if (stagedImages.length > maxImages) {
    errors.push(`圖片數量超過限制（最多 ${maxImages} 張）`);
  }

  // 檢查每張圖片
  stagedImages.forEach((image, index) => {
    // 檢查大小
    if (image.file && image.file.size > maxSizeMB * 1024 * 1024) {
      errors.push(`圖片 ${index + 1} "${image.filename}" 超過 ${maxSizeMB}MB`);
    }

    // 檢查格式
    if (image.file && !supportedFormats.includes(image.file.type)) {
      errors.push(
        `圖片 ${index + 1} "${image.filename}" 格式不支援（僅支援 JPEG, PNG, GIF）`
      );
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
};

/**
 * 批量上傳帶驗證
 * @param {number|string} contentId - 內容 ID
 * @param {string} contentType - 內容類型
 * @param {Array} stagedImages - 暫存的圖片列表
 * @param {object} config - 配置
 * @returns {Promise<{success: number, failed: number, errors: Array}>}
 */
export const uploadStagedImagesWithValidation = async (
  contentId,
  contentType,
  stagedImages,
  config = {}
) => {
  // 先驗證
  const validation = validateStagedImages(stagedImages, config);

  if (!validation.valid) {
    console.error('❌ 圖片驗證失敗:', validation.errors);
    validation.errors.forEach((error) => message.error(error));
    return {
      success: 0,
      failed: stagedImages.length,
      errors: validation.errors.map((error) => ({ filename: 'validation', error })),
    };
  }

  // 驗證通過，開始上傳
  return uploadStagedImages(
    contentId,
    contentType,
    stagedImages,
    config.apiEndpoint
  );
};

export default uploadStagedImages;
