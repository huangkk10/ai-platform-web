import { Modal, message } from 'antd';

/**
 * 圖片處理工具模組 - 處理圖片載入、檢測和模態框顯示
 */

/**
 * 精準的圖片載入函數
 * @param {string[]} filenames - 圖片檔名列表
 * @returns {Promise<Array>} - 載入的圖片資料
 */
export const loadImagesData = async (filenames) => {
  console.log('🖼️ 開始載入圖片，檔名列表:', filenames);
  
  // 🐛 載入除錯資訊
  const loadDebugInfo = {
    originalFilenames: filenames,
    validationResults: {},
    apiResults: {},
    finalResults: null,
    timestamp: new Date().toISOString()
  };
  
  // 🧹 預先過濾明顯無效的檔名
  const validFilenames = filenames.filter(filename => {
    const isValid = filename && 
                   filename.length >= 8 && 
                   /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename) &&
                   !/[\s\n\r,，。()]/.test(filename); // 不包含空格或標點
    console.log(`🔍 檔名驗證: "${filename}" -> ${isValid ? '✅ 有效' : '❌ 無效'}`);
    
    // 記錄驗證結果
    loadDebugInfo.validationResults[filename] = {
      isValid,
      length: filename?.length || 0,
      hasExtension: /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename || ''),
      hasInvalidChars: /[\s\n\r,，。()]/.test(filename || '')
    };
    
    return isValid;
  });
  
  if (validFilenames.length === 0) {
    console.log('❌ 沒有有效的圖片檔名');
    return [];
  }
  
  console.log(`📋 有效檔名列表 (${validFilenames.length}/${filenames.length}):`, validFilenames);
  
  try {
    const imagePromises = validFilenames.map(async (filename) => {
      try {
        console.log(`🔍 正在載入圖片: "${filename}"`);
        
        // 🎯 使用精準搜尋策略
        console.log(`🔍 嘗試精確檔名搜尋: "${filename}"`);
        
        // 首先嘗試精確檔名匹配
        const exactResponse = await fetch(`/api/content-images/?filename=${encodeURIComponent(filename)}`, {
          credentials: 'include'
        });
        
        if (exactResponse.ok) {
          const exactData = await exactResponse.json();
          console.log(`📊 精確搜尋回應:`, exactData);
          const exactImages = exactData.results || exactData;
          
          if (Array.isArray(exactImages) && exactImages.length > 0) {
            const image = exactImages[0];
            if (image && image.data_url) {
              console.log(`✅ 精確匹配成功: "${filename}" -> 找到圖片 (${Math.round(image.file_size/1024)}KB)`);
              return image;
            } else {
              console.log(`⚠️ 找到記錄但缺少 data_url: "${filename}"`);
            }
          } else {
            console.log(`⚠️ 精確匹配返回空結果: "${filename}"`);
          }
        } else {
          console.log(`❌ 精確搜尋 API 錯誤: ${exactResponse.status} - "${filename}"`);
        }
        
        // 如果精確匹配失敗，嘗試標題包含搜尋（僅作為備用）
        console.log(`🔍 精確匹配失敗，嘗試標題搜尋: "${filename}"`);
        const titleResponse = await fetch(`/api/content-images/?title__icontains=${encodeURIComponent(filename)}`, {
          credentials: 'include'
        });
        
        if (titleResponse.ok) {
          const titleData = await titleResponse.json();
          console.log(`📊 標題搜尋回應:`, titleData);
          const titleImages = titleData.results || titleData;
          
          if (Array.isArray(titleImages) && titleImages.length > 0) {
            const image = titleImages[0];
            if (image && image.data_url) {
              console.log(`✅ 標題搜尋成功: "${filename}" -> 找到圖片 (${Math.round(image.file_size/1024)}KB)`);
              return image;
            } else {
              console.log(`⚠️ 標題搜尋找到記錄但缺少 data_url: "${filename}"`);
            }
          } else {
            console.log(`⚠️ 標題搜尋返回空結果: "${filename}"`);
          }
        } else {
          console.log(`❌ 標題搜尋 API 錯誤: ${titleResponse.status} - "${filename}"`);
        }
        
        console.log(`❌ 搜尋失敗: "${filename}" -> 無匹配結果`);
        return null;
      } catch (error) {
        console.warn(`❌ 載入異常: "${filename}"`, error.message);
        return null;
      }
    });
    
    const results = await Promise.all(imagePromises);
    const validImages = results.filter(img => img !== null);
    
    // 🐛 完善載入除錯資訊
    loadDebugInfo.finalResults = {
      totalAttempts: validFilenames.length,
      successfulLoads: validImages.length,
      failedLoads: validFilenames.length - validImages.length,
      loadedImages: validImages.map(img => ({
        filename: img.filename,
        fileSize: Math.round(img.file_size/1024) + 'KB',
        dimensions: img.dimensions_display,
        hasDataUrl: !!img.data_url
      }))
    };
    
    // 保存載入除錯資訊
    try {
      const loadDebugKey = `image_load_debug_${Date.now()}`;
      sessionStorage.setItem(loadDebugKey, JSON.stringify(loadDebugInfo, null, 2));
      console.log(`🐛 載入除錯資訊已保存至 sessionStorage: ${loadDebugKey}`);
    } catch (error) {
      console.warn('無法保存載入除錯資訊:', error);
    }
    
    console.log(`📸 最終載入結果: ${validImages.length}/${validFilenames.length} 張圖片成功載入`);
    if (validImages.length > 0) {
      console.log('🎉 成功載入的圖片:', validImages.map(img => `"${img.filename}" (${Math.round(img.file_size/1024)}KB)`));
    }
    
    return validImages;
  } catch (error) {
    console.error('❌ 批量載入圖片失敗:', error);
    return [];
  }
};

/**
 * 顯示圖片模態框
 * @param {Object} imageData - 圖片資料對象
 */
export const showImageModal = (imageData) => {
  // 支持兩種格式：新的 data_url 或舊的 image_data
  const imageUrl = imageData.data_url || `data:${imageData.content_type_mime};base64,${imageData.image_data}`;
  
  Modal.info({
    title: `📸 ${imageData.title || imageData.filename}`,
    width: 800,
    content: (
      <div style={{ textAlign: 'center', padding: '20px 0' }}>
        <img
          src={imageUrl}
          alt={imageData.title || imageData.filename}
          style={{ maxWidth: '100%', maxHeight: '500px', objectFit: 'contain' }}
        />
        {imageData.description && (
          <div style={{ marginTop: '16px', color: '#666', fontSize: '14px' }}>
            📝 {imageData.description}
          </div>
        )}
        <div style={{ marginTop: '12px', fontSize: '12px', color: '#999' }}>
          尺寸: {imageData.dimensions_display || (imageData.width && imageData.height ? `${imageData.width}×${imageData.height}` : '未知')} | 
          大小: {imageData.size_display || (imageData.file_size ? `${Math.round(imageData.file_size / 1024)}KB` : '未知')}
        </div>
      </div>
    ),
    okText: '關閉',
    icon: null
  });
  
  message.success(`已載入圖片: ${imageData.title || imageData.filename}`);
};

/**
 * 從 metadata 中提取圖片檔名
 * @param {Object} metadata - API 回應的 metadata
 * @returns {Set} - 圖片檔名集合
 */
export const extractImagesFromMetadata = (metadata) => {
  const imageFilenames = new Set();
  
  if (metadata && metadata.retriever_resources) {
    metadata.retriever_resources.forEach((resource) => {
      if (resource.content) {
        // 精準搜尋 kisspng 檔名
        const kisspngPattern = /kisspng-[a-zA-Z0-9\-_.]{15,}\.(?:png|jpg|jpeg|gif|bmp|webp)\b/gi;
        let match;
        while ((match = kisspngPattern.exec(resource.content)) !== null) {
          imageFilenames.add(match[0].trim());
        }
        
        // 搜尋其他長檔名
        const longFilenamePattern = /\b([a-zA-Z0-9\-_.]{20,}\.(?:png|jpg|jpeg|gif|bmp|webp))\b/gi;
        while ((match = longFilenamePattern.exec(resource.content)) !== null) {
          imageFilenames.add(match[1].trim());
        }
      }
    });
  }
  
  return imageFilenames;
};

/**
 * 從內容中直接提取圖片檔名
 * @param {string} content - 消息內容
 * @returns {Set} - 圖片檔名集合
 */
export const extractImagesFromContent = (content) => {
  const imageFilenames = new Set();
  
  const contentImagePatterns = [
    /🖼️\s*([a-zA-Z0-9\-_.]{10,}\.(?:png|jpg|jpeg|gif|bmp|webp))/gi,
    /kisspng-[a-zA-Z0-9\-_.]{10,}\.(?:png|jpg|jpeg|gif|bmp|webp)\b/gi,
    /\b([a-zA-Z0-9\-_.]{15,}\.(?:png|jpg|jpeg|gif|bmp|webp))\b/gi
  ];
  
  contentImagePatterns.forEach(pattern => {
    let match;
    while ((match = pattern.exec(content)) !== null) {
      let filename = match[1] ? match[1].trim() : match[0].trim();
      filename = filename.replace(/^🖼️\s*/, '').trim();
      if (filename && filename.length >= 10) {
        imageFilenames.add(filename);
      }
    }
  });
  
  return imageFilenames;
};

/**
 * 檢查段落是否提及圖片
 * 更嚴格的圖片提及檢測，避免誤判
 * @param {string} paragraph - 段落內容
 * @returns {boolean} - 是否提及圖片
 */
export const checkImageMention = (paragraph) => {
  // 🎯 更精確的圖片提及模式
  const imageIndicators = [
    // 包含實際圖片檔名的模式
    /🖼️.*kisspng-[a-zA-Z0-9\-_.]{10,}\.(?:png|jpg|jpeg|gif|bmp|webp)/i,
    /🖼️.*[a-zA-Z0-9\-_.]{15,}\.(?:png|jpg|jpeg|gif|bmp|webp)/i,
    
    // 明確指出有圖片展示的模式 (必須有具體描述)
    /(?:主圖.*為.*RVT.*的.*圖片.*展示|展示了.*Jenkins.*的.*工作流程圖|圖片展示了.*Jenkins.*與.*Ansible)/i,
    
    // 避免模糊的「如相關圖片所示」誤判，要求有更具體的圖片描述
    /如.*相關圖片.*所示.*(?:主圖|工作流程圖|架構圖|示意圖|流程圖).*展示/i
  ];
  
  return imageIndicators.some(pattern => pattern.test(paragraph));
};

/**
 * 處理 HTML 實體和格式化
 * @param {string} content - 原始內容
 * @returns {string} - 處理後的內容
 */
export const processContentFormat = (content) => {
  return content
    // ✅ 修正 HTML 實體處理順序和邏輯
    .replace(/&lt;br\s*\/?&gt;/gi, '\n')  // 處理各種 <br> 格式
    .replace(/&lt;\/br&gt;/gi, '')        // 移除錯誤的結束標籤
    .replace(/&amp;/g, '&')               // 先處理 &amp;
    .replace(/&lt;/g, '<')               // 再處理 &lt;
    .replace(/&gt;/g, '>')               // 處理 &gt;
    .replace(/&quot;/g, '"')             // 處理引號
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ')             // 處理不間斷空格
    // 統一列表格式
    .replace(/^\s*[*•]\s+/gm, '- ')
    .replace(/^\s*(\d+)\.\s+/gm, '$1. ')
    // 清理多餘空行但保留必要的格式
    .replace(/\n{3,}/g, '\n\n')
    // 確保列表前後有適當空行
    .replace(/(\n- .*?)(?=\n[^-\s\n])/g, '$1\n')
    .replace(/(\n\d+\. .*?)(?=\n[^0-9\s\n])/g, '$1\n');
};

/**
 * 檢查是否包含 IMG:ID 格式的圖片引用
 * @param {string} content - 內容
 * @returns {boolean} - 是否包含 IMG:ID 引用
 */
export const hasImgIdReferences = (content) => {
  return /\*?\*?\[IMG:\d+\]/i.test(content);
};