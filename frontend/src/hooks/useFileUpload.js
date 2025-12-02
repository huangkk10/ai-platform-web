/**
 * useFileUpload Hook
 * ==================
 * 
 * 處理檔案上傳和 OCR 辨識的通用 Hook
 * 
 * 功能：
 * - 支援圖片上傳 → 即時預覽（不立即執行 OCR）
 * - 支援文字檔上傳 → 即時預覽
 * - 當用戶送出訊息時才執行 OCR 或讀取檔案
 * - 組合訊息格式供 AI Assistant 使用
 * 
 * 設計理念：
 * - 上傳是一個動作（快速，只顯示預覽）
 * - 送出是另一個動作（執行 OCR + 發送訊息）
 */

import { useState, useCallback, useRef } from 'react';
import { message } from 'antd';
import { analyzeImageOCR } from '../services/ocrService';

// 🔧 檔案大小限制（2025-12-02 調整，防止大檔案導致瀏覽器當機）
const MAX_TEXT_FILE_SIZE = 500 * 1024; // 500KB（文字檔）
const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB（圖片，因為要 OCR 壓縮）

// 🔧 內容長度限制
const MAX_TEXT_CONTENT_LENGTH = 100000; // 10 萬字元（超過則拒絕）
const RECOMMENDED_CONTENT_LENGTH = 30000; // 3 萬字元（超過顯示警告）

// 支援的檔案類型
const SUPPORTED_IMAGE_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/bmp',
  'image/webp'
];

const SUPPORTED_TEXT_EXTENSIONS = ['.txt', '.log', '.md'];

/**
 * 檢查是否為圖片檔案
 */
const isImageFile = (file) => {
  return SUPPORTED_IMAGE_TYPES.includes(file.type);
};

/**
 * 檢查是否為文字檔案
 */
const isTextFile = (file) => {
  if (file.type === 'text/plain') return true;
  const fileName = file.name.toLowerCase();
  return SUPPORTED_TEXT_EXTENSIONS.some(ext => fileName.endsWith(ext));
};

/**
 * 讀取文字檔內容
 */
const readTextFile = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(new Error('讀取檔案失敗'));
    reader.readAsText(file);
  });
};

/**
 * useFileUpload Hook
 */
export const useFileUpload = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContent, setFileContent] = useState(null); // OCR 文字或文字檔內容（處理後才有）
  const [filePreviewUrl, setFilePreviewUrl] = useState(null); // 圖片預覽 URL
  const [isProcessing, setIsProcessing] = useState(false); // 正在執行 OCR 或讀取
  const [isProcessed, setIsProcessed] = useState(false); // 是否已完成處理
  const [error, setError] = useState(null);
  
  // 用於追蹤檔案狀態
  const fileRef = useRef(null);
  
  /**
   * 處理檔案選擇（只儲存檔案和顯示預覽，不執行 OCR）
   */
  const handleFileSelect = useCallback(async (file) => {
    // 1. 檢查檔案類型
    const isImage = isImageFile(file);
    const isText = isTextFile(file);
    
    if (!isImage && !isText) {
      message.error('不支援的檔案格式。支援：圖片 (jpg, png, gif, bmp, webp) 和文字檔 (txt, log, md)');
      return;
    }
    
    // 2. 根據檔案類型檢查大小限制
    const sizeLimit = isImage ? MAX_IMAGE_SIZE : MAX_TEXT_FILE_SIZE;
    const sizeLimitText = isImage ? '5MB' : '500KB';
    
    if (file.size > sizeLimit) {
      message.error(`${isImage ? '圖片' : '文字檔'}大小不能超過 ${sizeLimitText}。您的檔案大小：${(file.size / 1024).toFixed(0)}KB`);
      return;
    }
    
    // 3. 儲存檔案（不執行 OCR）
    setUploadedFile(file);
    fileRef.current = file;
    setFileContent(null);
    setError(null);
    setIsProcessing(false);
    setIsProcessed(false);
    
    // 4. 設定圖片預覽 URL（圖片顯示縮圖，文字檔顯示圖示）
    if (isImage) {
      const previewUrl = URL.createObjectURL(file);
      setFilePreviewUrl(previewUrl);
    } else {
      setFilePreviewUrl(null);
    }
    
    // 5. 顯示上傳成功訊息
    const fileType = isImage ? '圖片' : '文字檔';
    message.success(`${fileType}已上傳，送出訊息時將自動處理`);
    console.log('📎 檔案已上傳（待處理）:', file.name, `(${(file.size / 1024).toFixed(1)} KB)`);
  }, []);
  
  /**
   * 處理檔案內容（用於送出訊息時呼叫）
   * 圖片：執行 OCR
   * 文字檔：讀取內容
   * 
   * @returns {Promise<{success: boolean, text: string, error?: string}>}
   */
  const processFileForSend = useCallback(async () => {
    const file = fileRef.current || uploadedFile;
    
    if (!file) {
      return { success: false, error: '沒有檔案可處理' };
    }
    
    // 如果已經處理過，直接返回之前的結果
    if (isProcessed && fileContent) {
      console.log('📄 使用已處理的內容');
      return { success: true, text: fileContent };
    }
    
    setIsProcessing(true);
    setError(null);
    
    try {
      let resultText = '';
      
      if (isImageFile(file)) {
        // 圖片：呼叫 OCR API
        console.log('📷 開始 OCR 辨識...', file.name);
        const result = await analyzeImageOCR(file);
        
        if (result.success) {
          resultText = result.text;
          console.log('✅ OCR 成功，文字長度:', result.text?.length);
        } else {
          throw new Error(result.error || 'OCR 辨識失敗');
        }
      } else {
        // 文字檔：直接讀取
        console.log('📄 讀取文字檔...', file.name);
        resultText = await readTextFile(file);
        console.log('✅ 讀取成功，文字長度:', resultText?.length);
      }
      
      // 儲存處理結果
      setFileContent(resultText);
      setIsProcessed(true);
      
      return { success: true, text: resultText };
      
    } catch (err) {
      console.error('❌ 檔案處理失敗:', err);
      setError(err.message);
      return { success: false, error: err.message };
    } finally {
      setIsProcessing(false);
    }
  }, [uploadedFile, fileContent, isProcessed]);
  
  /**
   * 清除上傳的檔案
   */
  const clearFile = useCallback(() => {
    // 釋放預覽 URL
    if (filePreviewUrl) {
      URL.revokeObjectURL(filePreviewUrl);
    }
    
    setUploadedFile(null);
    fileRef.current = null;
    setFileContent(null);
    setFilePreviewUrl(null);
    setIsProcessed(false);
    setError(null);
  }, [filePreviewUrl]);
  
  /**
   * 取得要附加到訊息的內容（用於組合 AI 訊息）
   * 需要先呼叫 processFileForSend() 才會有內容
   */
  const getFileContextForMessage = useCallback(() => {
    if (!fileContent) return null;
    
    const isImage = uploadedFile && isImageFile(uploadedFile);
    const prefix = isImage 
      ? `【以下是從上傳圖片中 OCR 辨識出的文字內容】\n`
      : `【以下是上傳的文字檔 ${uploadedFile?.name} 的內容】\n`;
    
    return `${prefix}---\n${fileContent}\n---\n\n`;
  }, [fileContent, uploadedFile]);
  
  /**
   * 取得檔案處理狀態說明文字
   */
  const getStatusText = useCallback(() => {
    if (isProcessing) {
      return uploadedFile && isImageFile(uploadedFile) ? 'OCR 辨識中...' : '讀取中...';
    }
    if (isProcessed) {
      return '已處理';
    }
    if (uploadedFile) {
      return '待處理';
    }
    return null;
  }, [isProcessing, isProcessed, uploadedFile]);
  
  return {
    // 狀態
    uploadedFile,
    fileContent,
    filePreviewUrl,
    isProcessing,
    isProcessed,
    error,
    
    // 方法
    handleFileSelect,
    clearFile,
    processFileForSend,  // 新增：送出時處理檔案
    getFileContextForMessage,
    getStatusText,  // 新增：取得狀態文字
    
    // 便利屬性
    hasFile: !!uploadedFile,
    hasContent: !!fileContent,
    isImage: uploadedFile ? isImageFile(uploadedFile) : false,
    isText: uploadedFile ? isTextFile(uploadedFile) : false,
    isPending: !!uploadedFile && !isProcessed && !isProcessing  // 新增：是否待處理
  };
};

// 🔧 導出常數供其他組件使用
export { 
  MAX_TEXT_FILE_SIZE, 
  MAX_IMAGE_SIZE, 
  MAX_TEXT_CONTENT_LENGTH, 
  RECOMMENDED_CONTENT_LENGTH 
};

export default useFileUpload;
