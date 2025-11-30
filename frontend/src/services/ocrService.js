/**
 * OCR API 服務
 * =============
 * 
 * 呼叫後端 OCR API 分析圖片
 */

/**
 * 從 Cookie 中獲取 CSRF Token
 */
const getCsrfToken = () => {
  const name = 'csrftoken';
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
};

/**
 * 呼叫 OCR API 分析圖片
 * @param {File} file - 圖片檔案
 * @returns {Promise<{success: boolean, text?: string, error?: string, filename?: string}>}
 */
export const analyzeImageOCR = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    // 獲取 CSRF Token
    const csrfToken = getCsrfToken();
    
    const headers = {};
    if (csrfToken) {
      headers['X-CSRFToken'] = csrfToken;
    }
    
    const response = await fetch('/api/ocr/analyze/', {
      method: 'POST',
      credentials: 'include',
      headers: headers,
      body: formData,
      // 不設定 Content-Type，讓瀏覽器自動設定 multipart/form-data
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }
    
    const data = await response.json();
    return data;
    
  } catch (error) {
    console.error('OCR API 錯誤:', error);
    return {
      success: false,
      error: error.message || 'OCR 服務錯誤'
    };
  }
};

const ocrService = { analyzeImageOCR };
export default ocrService;
