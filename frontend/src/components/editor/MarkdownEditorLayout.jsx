/**
 * 通用 Markdown 編輯器佈局組件
 * 支援多種內容類型的 Markdown 編輯
 * 
 * 使用範例：
 * <MarkdownEditorLayout 
 *   contentType="rvt-guide"
 *   contentId={id}
 *   navigate={navigate}
 * />
 */

import React, { useEffect, useRef, useCallback, useState } from 'react';
import { Input, Spin, Card, Drawer, Tooltip, Button, Modal, message } from 'antd';
import { PictureOutlined, CloseOutlined, ExclamationCircleOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';
import axios from 'axios';

// 組件導入
import ContentImageManager from '../ContentImageManager';

// Hook 導入
import useContentEditor from '../../hooks/useContentEditor';
import useMarkdownCursor from '../../hooks/useMarkdownCursor';
import useFullScreenDetection from '../../hooks/useFullScreenDetection';
import useImageManager from '../../hooks/useImageManager';

// 工具導入
import { uploadStagedImages } from '../../utils/uploadStagedImages';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';
import { fixAllMarkdownTables } from '../../utils/markdownTableFixer';
import { 
  validateMarkdownStructure, 
  formatValidationMessage 
} from '../../utils/markdownValidator';

// 存儲圖片管理器回調的全局變數（使用閉包）
let globalImageManagerHandler = null;

// 自定義圖片管理插件
class ImageManagerPlugin extends React.Component {
  static pluginName = 'image-manager';
  static align = 'left';

  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    console.log('🖼️ 圖片管理按鈕被點擊');

    if (globalImageManagerHandler && typeof globalImageManagerHandler === 'function') {
      console.log('✅ 執行 globalImageManagerHandler');
      globalImageManagerHandler();
    } else {
      console.error('❌ globalImageManagerHandler 未定義');
      console.log('Handler type:', typeof globalImageManagerHandler);
    }
  }

  render() {
    return (
      <span
        className="button button-type-image-manager"
        title="圖片管理"
        onClick={this.handleClick}
        style={{
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4px 8px',
          fontSize: '14px',
          userSelect: 'none'
        }}
      >
        📷
      </span>
    );
  }
}

// 註冊插件
MdEditor.use(ImageManagerPlugin);

// 自定義工具欄按鈕樣式
const customToolbarStyles = `
  .rc-md-editor .button.custom-image-manager {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    background: #fff;
    transition: all 0.2s;
    margin: 0 2px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .rc-md-editor .button.custom-image-manager:hover {
    border-color: #1890ff;
    background: #f0f8ff;
  }
  
  .rc-md-editor .button.custom-image-manager.active {
    border-color: #1890ff;
    background: #1890ff;
    color: white;
  }
  
  .rc-md-editor .button.custom-image-manager.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* 圖片管理按鈕樣式 */
  .rc-md-editor .button.button-type-image-manager {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    min-width: 30px;
    height: 30px;
    padding: 4px 8px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    background: #fff;
    transition: all 0.2s;
    margin: 0 2px;
    cursor: pointer;
    font-size: 16px;
  }
  
  .rc-md-editor .button.button-type-image-manager:hover {
    border-color: #1890ff;
    background: #f0f8ff;
  }
  
  .rc-md-editor .button.button-type-image-manager.active {
    border-color: #1890ff;
    background: #1890ff;
    filter: brightness(1.1);
  }

  /* 全螢幕模式下的浮動按鈕 */
  .fullscreen-image-manager-btn {
    position: fixed !important;
    top: 60px !important;
    right: 20px !important;
    z-index: 9999 !important;
    background: #1890ff !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3) !important;
    font-size: 14px !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
  }
  
  .fullscreen-image-manager-btn:hover {
    background: #40a9ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4) !important;
  }

  /* 全螢幕模式檢測 */
  .rc-md-editor.full {
    .fullscreen-image-manager-btn {
      display: flex !important;
    }
  }
  
  /* 🖼️ Markdown 預覽中的圖片樣式（與 DevMarkdownTestPage 一致）*/
  .rc-md-editor .custom-html-style img,
  .rc-md-editor .html-wrap img,
  .rc-md-editor .sec-html img {
    max-width: 100px !important;
    height: auto !important;
    display: inline-block !important;
    margin: 0 4px !important;
    vertical-align: middle !important;
    border: 1px solid #d9d9d9 !important;
    border-radius: 4px !important;
    padding: 4px !important;
    background-color: #fafafa !important;
    cursor: pointer !important;
    object-fit: contain !important;
  }
  
  /* Ant Design Image 組件樣式支援 */
  .rc-md-editor .ant-image {
    display: inline-block !important;
    margin: 0 4px !important;
    vertical-align: middle !important;
  }
  
  .rc-md-editor .ant-image img {
    max-width: 100px !important;
    height: auto !important;
  }
`;

// 初始化 Markdown 解析器（啟用 HTML 支援）
const mdParser = new MarkdownIt({
  html: true,        // ✅ 啟用 HTML 標籤支援（包含 <br>）
  breaks: true,      // ✅ 將換行符轉換為 <br>
  linkify: true,     // 自動將 URL 轉為連結
  typographer: true  // 啟用智能標點符號
});

/**
 * 自定義 renderHTML 函數（支援圖片預覽與 HTML 標籤）
 * 
 * ⚠️ 注意：由於 react-markdown-editor-lite 的 renderHTML 是同步函數，
 * 我們無法使用 React 組件的 useEffect 來異步加載圖片。
 * 
 * 解決方案：使用 markdown-it 渲染基礎 HTML，並自定義圖片規則
 * 
 * 新增功能：
 * - 支援 HTML 標籤（如 <br>）在預覽中正確顯示
 * - 將換行符自動轉換為 <br> 標籤
 * 
 * @param {string} text - Markdown 文本
 * @returns {string} - 渲染後的 HTML
 */
const renderMarkdownWithImages = (text) => {
  try {
    // 步驟 1：修復表格格式
    let processed = fixAllMarkdownTables(text);
    
    // 步驟 2：將 [IMG:ID] 轉換為 ![IMG:ID](http://..../api/content-images/ID/)
    processed = convertImageReferencesToMarkdown(processed);
    
    // 🔍 調試：輸出處理前的內容
    if (text.includes('<br>')) {
      console.log('📝 [Render] 輸入包含 <br> 標籤');
      console.log('原始內容片段:', text.substring(0, 200));
    }
    
    // 步驟 3：使用 markdown-it 渲染（支援 HTML 標籤與表格）
    let htmlString = mdParser.render(processed);
    
    // 🔍 調試：輸出渲染後的 HTML
    if (htmlString.includes('<br>')) {
      console.log('✅ [Render] 渲染後包含 <br> 標籤');
    } else if (htmlString.includes('&lt;br&gt;')) {
      console.log('❌ [Render] <br> 被轉義為 &lt;br&gt;');
    } else if (text.includes('<br>')) {
      console.log('⚠️ [Render] <br> 標籤消失了');
    }
    
    // 步驟 4：後處理圖片 HTML
    // 將 <img src="http://...api/content-images/32/" alt="IMG:32"> 
    // 轉換為帶有特殊 data 屬性的 img 標籤，以便客戶端 JavaScript 處理
    htmlString = htmlString.replace(
      /<img src="http:\/\/[^"]+\/api\/content-images\/(\d+)\/" alt="([^"]*)"[^>]*>/g,
      (match, imageId, altText) => {
        return `<img 
          class="content-image-preview" 
          data-image-id="${imageId}" 
          alt="${altText}"
          src="http://10.10.172.127/api/content-images/${imageId}/"
          style="max-width: 100%; height: auto; border: 1px solid #d9d9d9; border-radius: 4px; margin: 8px 0;"
        />`;
      }
    );
    
    return htmlString;
  } catch (error) {
    console.error('❌ Markdown 渲染錯誤:', error);
    // 發生錯誤時使用備用渲染器
    return mdParser.render(text);
  }
};

/**
 * Markdown 編輯器佈局組件
 */
const MarkdownEditorLayout = ({
  contentType = 'rvt-guide',
  contentId,
  navigate,
  customConfig = {},
  onBeforeSave,       // 儲存前鉤子
  onAfterSave,        // 儲存後鉤子
  onSavingChange,     // 儲存狀態變更回調
  renderExtraFields,  // 渲染額外欄位的插槽
  renderToolbarExtra, // 渲染工具欄額外按鈕的插槽
}) => {
  const mdEditorRef = useRef(null);
  const getStagedImagesRef = useRef(null);

  // 使用通用內容編輯器 Hook
  const {
    config,
    loading,
    // saving, // 未使用，註釋掉避免警告
    formData,
    images,
    setImages,  // ✅ 接收 setImages
    isEditMode,
    loadData,
    saveData,
    handleTitleChange,
    handleContentChange,
    setFormData,
    setSaving
  } = useContentEditor(contentType, contentId, navigate, customConfig);

  // 使用圖片管理 Hook（傳入 images 和 setImages）
  const {
    drawerVisible,
    toggleDrawer,
    handleImagesChange: handleImageManagerChange,
    handleContentUpdate,
  } = useImageManager(mdEditorRef, setFormData, images, setImages);  // ✅ 傳入 images 和 setImages

  // 組合圖片變更處理
  const handleImagesChange = (newImages) => {
    handleImageManagerChange(newImages);
  };

  // 使用游標管理 Hook
  const {
    cursorPosition,
    handleEditorCursorChange,
    handleEditorBlur,
    handleEditorFocus,
    insertImageAtCursor,
  } = useMarkdownCursor(mdEditorRef, formData, setFormData);

  // 使用全螢幕偵測 Hook
  const {
    isFullScreen,
    // toggleFullScreen // 未使用，註釋掉避免警告
  } = useFullScreenDetection();

  // 🆕 圖片上傳狀態管理
  const [pasteUploading, setPasteUploading] = useState(false);

  // 調試：確認 toggleDrawer 函數
  useEffect(() => {
    console.log('🔧 MarkdownEditorLayout 初始化');
    console.log('📷 toggleDrawer 函數:', typeof toggleDrawer);
    console.log('� toggleDrawer 值:', toggleDrawer);
    console.log('�📂 drawerVisible:', drawerVisible);
    console.log('📝 contentType:', contentType);
    console.log('🎨 isEditMode:', isEditMode);

    // 設置全局圖片管理處理函數
    if (typeof toggleDrawer === 'function') {
      globalImageManagerHandler = toggleDrawer;
      console.log('✅ 已設置 globalImageManagerHandler');
    } else {
      console.error('❌ toggleDrawer 不是函數！', typeof toggleDrawer);
    }

    // 清理函數
    return () => {
      globalImageManagerHandler = null;
      console.log('🧹 已清除 globalImageManagerHandler');
    };
  }, [toggleDrawer, drawerVisible, contentType, isEditMode]);

  // 載入現有記錄數據（編輯模式）
  useEffect(() => {
    if (isEditMode && contentId) {
      loadData();
    }
  }, [contentId, isEditMode]); // 只依賴 contentId 和 isEditMode，loadData 函數穩定

  // 處理儲存 - 支援暫存圖片上傳
  const handleSave = useCallback(async () => {
    try {
      // 🆕 步驟 1：驗證 Markdown 格式（僅針對 Protocol Guide）
      if (contentType === 'protocol-guide') {
        console.log('🔍 開始驗證 Protocol Guide Markdown 格式...');
        const validationResult = validateMarkdownStructure(formData.content);
        
        console.log('📊 驗證結果:', validationResult);

        // 🆕 步驟 1.1：如果驗證失敗，顯示錯誤訊息並阻止儲存
        if (!validationResult.valid) {
          console.log('❌ 驗證失敗，阻止儲存');
          
          Modal.error({
            title: '❌ 內容格式不符合要求',
            width: 650,
            content: formatValidationMessage(validationResult),
            okText: '我知道了',
            centered: true,
            onOk: () => {
              console.log('用戶關閉驗證錯誤對話框');
            }
          });
          
          // 🚫 阻止儲存
          return;
        }

        // 🆕 步驟 1.2：如果有警告，詢問用戶是否繼續
        if (validationResult.warnings.length > 0) {
          console.log('⚠️ 有警告訊息，詢問用戶是否繼續');
          
          const confirmed = await new Promise((resolve) => {
            Modal.confirm({
              title: '⚠️ 內容建議改進',
              width: 650,
              icon: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
              content: formatValidationMessage(validationResult),
              okText: '繼續儲存',
              cancelText: '返回修改',
              centered: true,
              onOk: () => resolve(true),
              onCancel: () => resolve(false)
            });
          });
          
          if (!confirmed) {
            console.log('用戶選擇返回修改');
            return;
          }
        }

        console.log('✅ Markdown 格式驗證通過，繼續儲存流程...');
      }

      // 通知父組件開始儲存
      if (onSavingChange) onSavingChange(true);

      // 執行儲存前鉤子
      let dataToSave = { ...formData };
      if (onBeforeSave) {
        dataToSave = await onBeforeSave(dataToSave);
        if (!dataToSave) {
          if (onSavingChange) onSavingChange(false);
          return; // 如果返回 falsy，取消儲存
        }
      }

      // 先儲存文檔本體
      const result = await saveData(dataToSave, {
        navigateAfterSave: false, // 先不導航，等圖片上傳完成
        redirectPath: config.listRoute
      });

      if (!result) {
        if (onSavingChange) onSavingChange(false);
        return; // 儲存失敗，不繼續
      }

      // 如果是新建模式且有暫存圖片，批量上傳
      if (!isEditMode && getStagedImagesRef.current) {
        const stagedImages = getStagedImagesRef.current();

        if (stagedImages && stagedImages.length > 0) {
          setSaving(true);

          try {
            await uploadStagedImages(
              result.id,
              contentType,
              stagedImages,
              config.imageEndpoint
            );
          } catch (error) {
            console.error('❌ 圖片上傳過程異常:', error);
          } finally {
            setSaving(false);
          }
        }
      }

      // 執行儲存後鉤子
      if (onAfterSave) {
        await onAfterSave(result);
      }

      // 通知父組件儲存完成
      if (onSavingChange) onSavingChange(false);

      // 導航到列表頁 (使用 setTimeout 確保 message 顯示後再跳轉)
      setTimeout(() => {
        navigate(config.listRoute);
      }, 300);

    } catch (error) {
      console.error('❌ 儲存過程發生錯誤:', error);
      setSaving(false);
      if (onSavingChange) onSavingChange(false);
    }
  }, [formData, onBeforeSave, onSavingChange, saveData, config.listRoute, isEditMode, getStagedImagesRef, contentType, config.imageEndpoint, setSaving, onAfterSave, navigate]);

  // 使用 ref 保存最新的 handleSave 函數
  const handleSaveRef = useRef(handleSave);

  useEffect(() => {
    handleSaveRef.current = handleSave;
  }, [handleSave]);

  // 🆕 處理剪貼簿貼上圖片
  const handlePasteImage = useCallback(async (file) => {
    try {
      // 驗證檔案類型
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'];
      if (!allowedTypes.includes(file.type)) {
        message.error('僅支援 PNG、JPEG、GIF、WebP 格式的圖片');
        return false;
      }

      // 驗證檔案大小（預設 5MB）
      const maxSizeMB = config.imageConfig?.maxSizeMB || 5;
      const maxSizeBytes = maxSizeMB * 1024 * 1024;
      if (file.size > maxSizeBytes) {
        message.error(`圖片大小不能超過 ${maxSizeMB}MB`);
        return false;
      }

      // 在游標位置插入「上傳中」的佔位符
      const timestamp = Date.now();
      const placeholderId = `uploading_${timestamp}`;
      const placeholder = `![圖片上傳中...](${placeholderId})`;
      
      // 使用編輯器 API 在游標位置插入佔位符
      if (mdEditorRef.current) {
        const editor = mdEditorRef.current;
        const currentContent = editor.getMdValue();
        console.log('📝 當前內容長度:', currentContent.length);
        console.log('📝 當前內容:', currentContent);
        
        const selection = editor.getSelection();
        console.log('🎯 游標位置:', selection);
        
        // 在選取位置插入佔位符
        const beforeText = currentContent.substring(0, selection.start);
        const afterText = currentContent.substring(selection.end);
        const newContent = beforeText + placeholder + afterText;
        
        console.log('📝 新內容長度:', newContent.length);
        console.log('📝 新內容:', newContent);
        
        editor.setText(newContent);
        
        // 設置游標到佔位符之後
        const newCursorPos = selection.start + placeholder.length;
        editor.setSelection({
          start: newCursorPos,
          end: newCursorPos
        });
        console.log('✅ 已插入佔位符，新游標位置:', newCursorPos);
      }

      setPasteUploading(true);

      // 如果是編輯模式，直接上傳到伺服器
      if (isEditMode && contentId) {
        // 準備 FormData
        const formData = new FormData();
        formData.append('image', file);
        formData.append('content_type', contentType);
        formData.append('content_id', contentId);  // ✅ 修正：使用 content_id 而非 object_id
        
        // ✅ 生成檔名：YYYY-MM-DD_HHMMSS 格式（與截圖工具一致）
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        const fileExtension = file.name.split('.').pop() || 'png';
        const filename = `${year}-${month}-${day}_${hours}${minutes}${seconds}.${fileExtension}`;
        formData.append('filename', filename);

        // 上傳圖片
        const response = await axios.post('/api/content-images/', formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });

        const imageData = response.data;
        
        // ✅ 生成圖片引用語法（簡潔格式，移除「剪貼簿貼上」標記）
        // 格式：🖼️ [IMG:ID] filename (標題: filename)
        // 這個格式會被 ContentImageManager 組件解析並轉換成圖片
        const imageReference = `🖼️ [IMG:${imageData.id}] ${filename} (標題: ${filename})`;
        
        // 替換佔位符為實際圖片引用（使用編輯器的 API）
        if (mdEditorRef.current) {
          const currentContent = mdEditorRef.current.getMdValue();
          console.log('🔄 準備替換佔位符');
          console.log('📝 當前內容:', currentContent);
          console.log('🔍 佔位符:', `![圖片上傳中...](${placeholderId})`);
          console.log('✨ 圖片引用:', imageReference);
          
          const updatedContent = currentContent.replace(`![圖片上傳中...](${placeholderId})`, imageReference);
          console.log('📝 替換後內容:', updatedContent);
          console.log('🔢 替換前後長度:', currentContent.length, '→', updatedContent.length);
          
          mdEditorRef.current.setText(updatedContent);
          console.log('✅ 已替換佔位符為圖片引用');
        }

        message.success(`✅ 圖片上傳成功！ID: ${imageData.id}`);
        
        // ✅ 更新圖片列表（方案 2：直接使用 setImages 更新）
        if (setImages && contentId) {
          // 方法 1：立即添加新圖片到列表（快速反應）
          setImages(prev => [...prev, imageData]);
          console.log('✅ 圖片已添加到列表 (立即更新)');
          
          // 方法 2：可選 - 500ms 後重新查詢完整列表（確保資料完整）
          setTimeout(async () => {
            try {
              const response = await axios.get('/api/content-images/', {
                params: {
                  content_type: contentType,
                  content_id: contentId
                }
              });
              
              const imageList = response.data.results || response.data;
              
              if (Array.isArray(imageList)) {
                setImages(imageList);
                console.log('✅ 圖片列表已完整更新，共', imageList.length, '張圖片');
              }
            } catch (error) {
              console.warn('⚠️ 無法刷新完整圖片列表:', error.message);
              // 靜默失敗，不影響用戶體驗（已有立即添加的圖片）
            }
          }, 500);
        }

      } else {
        // 新建模式：使用暫存模式
        // 將圖片轉換為 Base64（供暫存使用）
        const reader = new FileReader();
        
        await new Promise((resolve, reject) => {
          reader.onload = () => {
            const base64Data = reader.result;
            const stagingId = `staging_${timestamp}`;
            
            // 生成暫存圖片引用
            const imageReference = `\n![暫存圖片](${stagingId})\n`;
            
            // 替換佔位符
            setFormData(prev => ({
              ...prev,
              content: prev.content.replace(`![圖片上傳中...](${placeholderId})`, imageReference)
            }));

            message.info('📦 圖片已暫存，儲存文檔時將自動上傳');
            
            // 通知圖片管理器（如果需要）
            if (handleImageManagerChange) {
              // 這裡可以添加暫存圖片到圖片管理器
            }

            resolve();
          };
          
          reader.onerror = reject;
          reader.readAsDataURL(file);
        });
      }

      return true;

    } catch (error) {
      console.error('❌ 圖片上傳失敗:', error);
      message.error(`圖片上傳失敗: ${error.response?.data?.error || error.message}`);
      
      // 移除佔位符
      setFormData(prev => ({
        ...prev,
        content: prev.content.replace(/!\[圖片上傳中\.\.\.\]\(uploading_\d+\)/g, '')
      }));

      return false;
    } finally {
      setPasteUploading(false);
    }
  }, [
    config.imageConfig,
    isEditMode,
    contentId,
    contentType,
    setFormData,
    handleImageManagerChange
  ]);

  // 監聽來自 TopHeader 的保存事件
  useEffect(() => {
    const eventName = config.saveEventName || 'topheader-save';

    const handleSaveEvent = () => {
      console.log('🎯 收到儲存事件:', eventName);
      if (handleSaveRef.current) {
        handleSaveRef.current();
      }
    };

    console.log('📡 註冊儲存事件監聽器:', eventName);
    window.addEventListener(eventName, handleSaveEvent);

    return () => {
      console.log('🔌 移除儲存事件監聽器:', eventName);
      window.removeEventListener(eventName, handleSaveEvent);
    };
  }, [config.saveEventName]);

  // 🆕 監聽格式檢查事件（手動觸發格式檢查）
  useEffect(() => {
    const handleCheckFormatEvent = () => {
      console.log('🎯 收到格式檢查事件');
      
      // 支援 Protocol Guide 和 RVT Guide
      if (contentType !== 'protocol-guide' && contentType !== 'rvt-guide') {
        Modal.info({
          title: '💡 提示',
          content: '格式檢查功能僅適用於 Protocol Guide 和 RVT Guide',
          centered: true
        });
        return;
      }
      
      const validationResult = validateMarkdownStructure(formData.content);
      
      if (validationResult.valid) {
        // 驗證通過
        let title = '✅ 格式檢查通過';
        if (validationResult.warnings.length > 0) {
          title = '✅ 格式符合最低要求（有改進建議）';
        }
        
        Modal.success({
          title: title,
          width: 650,
          content: formatValidationMessage(validationResult),
          okText: '關閉',
          centered: true
        });
      } else {
        // 驗證失敗
        Modal.error({
          title: '❌ 格式檢查失敗',
          width: 650,
          content: formatValidationMessage(validationResult),
          okText: '我知道了',
          centered: true
        });
      }
    };

    window.addEventListener('check-markdown-format', handleCheckFormatEvent);
    
    return () => {
      window.removeEventListener('check-markdown-format', handleCheckFormatEvent);
    };
  }, [formData.content, contentType]);

  // 🆕 監聽剪貼簿貼上事件（Ctrl+V 貼上圖片）
  useEffect(() => {
    const handlePaste = async (event) => {
      // 確保事件來自編輯器區域
      const target = event.target;
      const isInEditor = target.closest('.rc-md-editor') || 
                         target.classList.contains('sec-md') ||
                         target.classList.contains('custom-md-editor');
      
      if (!isInEditor) {
        console.log('🔇 paste 事件不在編輯器內，忽略');
        return;
      }

      console.log('📋 偵測到 paste 事件');

      const items = event.clipboardData?.items;
      if (!items || items.length === 0) {
        console.log('🔇 剪貼簿中沒有內容');
        return;
      }

      // 檢查是否有圖片
      let hasImage = false;
      const imageFiles = [];

      for (let i = 0; i < items.length; i++) {
        const item = items[i];
        console.log(`📦 剪貼簿項目 ${i}:`, item.type);

        if (item.type.indexOf('image') !== -1) {
          hasImage = true;
          const file = item.getAsFile();
          if (file) {
            imageFiles.push(file);
            console.log(`🖼️ 找到圖片: ${file.name}, 類型: ${file.type}, 大小: ${(file.size / 1024).toFixed(2)}KB`);
          }
        }
      }

      // 如果有圖片，處理上傳
      if (hasImage && imageFiles.length > 0) {
        event.preventDefault(); // 阻止預設的貼上行為（避免貼上 base64）
        console.log(`✅ 準備上傳 ${imageFiles.length} 張圖片`);

        // 依序上傳每張圖片
        for (const file of imageFiles) {
          await handlePasteImage(file);
        }
      }
    };

    // 監聽全局 paste 事件
    document.addEventListener('paste', handlePaste);
    console.log('✅ 剪貼簿貼上監聽器已註冊');

    return () => {
      document.removeEventListener('paste', handlePaste);
      console.log('🧹 剪貼簿貼上監聽器已移除');
    };
  }, [handlePasteImage]);

  // 處理預覽面板中的圖片加載（客戶端）
  useEffect(() => {
    console.log('🖼️ [圖片加載 useEffect] 觸發，內容長度:', formData.content?.length);
    
    // 延遲執行，確保 HTML 已渲染（增加到 300ms）
    const timer = setTimeout(() => {
      console.log('⏰ [圖片加載] 開始處理...');
      
      // 嘗試多種選擇器
      const previewPane = document.querySelector('.rc-md-editor .rc-md-preview') 
                       || document.querySelector('.custom-html-style')
                       || document.querySelector('.html-wrap');
      
      if (!previewPane) {
        console.warn('❌ [圖片加載] 找不到預覽面板');
        return;
      }
      
      console.log('✅ [圖片加載] 找到預覽面板:', previewPane.className);

      // 嘗試多種選擇器找圖片
      let images = previewPane.querySelectorAll('img.content-image-preview[data-image-id]');
      
      if (images.length === 0) {
        // 備用：找所有包含 content-images URL 的圖片
        images = previewPane.querySelectorAll('img[src*="content-images"]');
        console.log('🔄 [圖片加載] 使用備用選擇器，找到圖片數:', images.length);
      } else {
        console.log('🎯 [圖片加載] 找到標準圖片數:', images.length);
      }
      
      images.forEach(async (img, index) => {
        let imageId = img.getAttribute('data-image-id');
        
        // 如果沒有 data-image-id，從 src 中提取
        if (!imageId) {
          const srcMatch = img.src.match(/content-images\/(\d+)/);
          imageId = srcMatch ? srcMatch[1] : null;
        }
        
        if (!imageId) {
          console.warn(`⚠️ [圖片 ${index}] 無法取得圖片 ID`);
          return;
        }

        console.log(`🔄 [圖片 ${imageId}] 開始載入...`);

        try {
          // 獲取圖片數據
          const response = await fetch(`http://10.10.172.127/api/content-images/${imageId}/`, {
            method: 'GET',
            headers: {
              'Accept': 'application/json'
            }
          });
          
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
          }

          const imageData = await response.json();
          console.log(`✅ [圖片 ${imageId}] API 回應成功，包含 data_url:`, !!imageData.data_url);
          
          // 設置圖片 src（使用 data_url）
          if (imageData.data_url) {
            img.src = imageData.data_url;
            img.title = imageData.title || imageData.filename || `Image ${imageId}`;
            img.alt = imageData.title || imageData.filename || `Image ${imageId}`;
            
            // 添加成功加載的樣式
            img.style.maxWidth = '100px';
            img.style.height = 'auto';
            img.style.border = '1px solid #52c41a';
            img.style.borderRadius = '4px';
            img.style.padding = '4px';
            img.style.margin = '0 4px';
            img.style.backgroundColor = '#fafafa';
            img.style.display = 'inline-block';
            img.style.verticalAlign = 'middle';
            img.style.opacity = '1';
            
            console.log(`✅ [圖片 ${imageId}] 載入成功！`);
          } else {
            throw new Error('No data_url in response');
          }
        } catch (error) {
          console.error(`❌ [圖片 ${imageId}] 載入失敗:`, error);
          
          // 設置錯誤狀態
          img.alt = `⊗ [圖片載入失敗: ${imageId}]`;
          img.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjEyMCIgZmlsbD0iI2Y1ZjVmNSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iMTQiIGZpbGw9IiNmZjQ0NDQiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGR5PSIuM2VtIj7ik4ogW+WclueLh+i8ieWFpeWksei0pV08L3RleHQ+PC9zdmc+';
          img.style.border = '1px solid #ff4d4f';
        }
      });
    }, 300); // 增加延遲到 300ms

    return () => clearTimeout(timer);
  }, [formData.content]); // 當內容變化時重新處理圖片

  return (
    <div style={{
      height: 'calc(100vh - 64px)',
      display: 'flex',
      flexDirection: 'column',
      background: '#f5f5f5'
    }}>
      {/* 注入自定義樣式 */}
      <style>{customToolbarStyles}</style>

      {/* 主要編輯區域 */}
      {loading ? (
        <div style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center'
        }}>
          <Spin size="large" />
          <span style={{ marginLeft: '12px', fontSize: '16px' }}>
            載入中...
          </span>
        </div>
      ) : (
        <div style={{
          flex: 1,
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px',
          overflow: 'hidden'  // 防止外層產生滾動，確保 toolbar sticky 生效
        }}>
          {/* 標題輸入 */}
          <Card size="small" style={{ flexShrink: 0 }}>
            <div>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                {config.labels.title}
              </label>
              <Input
                value={typeof formData.title === 'string' ? formData.title : ''}
                onChange={handleTitleChange}
                placeholder={`請輸入${config.labels.title}...`}
                size="large"
                style={{ fontSize: '16px' }}
              />
            </div>

            {/* 額外欄位插槽 */}
            {renderExtraFields && (
              <div style={{ marginTop: '16px' }}>
                {renderExtraFields(formData, setFormData)}
              </div>
            )}
          </Card>

          {/* Markdown 編輯器 */}
          <Card
            title={config.labels.content}
            size="small"
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0  // 重要：允許 flex 子元素正確收縮
            }}
            bodyStyle={{
              flex: 1,
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',  // 防止 Card 內部產生外層滾動
              minHeight: 0         // 確保高度受控
            }}
          >
            <div style={{ flex: 1, minHeight: '500px' }}>
              <MdEditor
                ref={mdEditorRef}
                value={formData.content}
                style={{ height: '100%' }}
                renderHTML={renderMarkdownWithImages}
                onChange={handleContentChange}
                onFocus={handleEditorFocus}
                onBlur={handleEditorBlur}
                onClick={handleEditorCursorChange}
                onKeyUp={handleEditorCursorChange}
                onSelect={handleEditorCursorChange}
                onMouseUp={handleEditorCursorChange}
                placeholder="請輸入 Markdown 格式的內容..."
                config={{
                  view: {
                    menu: true,
                    md: true,
                    html: true
                  },
                  canView: {
                    menu: true,
                    md: true,
                    html: true,
                    both: true,
                    fullScreen: true,
                    hideMenu: false
                  },
                  htmlClass: 'custom-html-preview',  // ✅ 添加自定義 HTML class
                  markdownClass: 'custom-md-editor', // 添加自定義 Markdown class
                  imageManager: {
                    onImageManagerClick: toggleDrawer,
                    isActive: drawerVisible,
                    label: isEditMode ? config.labels.imageManager : config.labels.imageManagerStaging
                  }
                }}
                plugins={[...config.editorPlugins, 'image-manager']}
              />
            </div>

            {/* 提示信息 */}
            <div style={{
              marginTop: '12px',
              padding: '12px',
              backgroundColor: '#f6ffed',
              border: '1px solid #b7eb8f',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#389e0d'
            }}>
              {config.hints.markdown}
            </div>

            {/* 🆕 圖片上傳中提示 */}
            {pasteUploading && (
              <div style={{
                marginTop: '8px',
                padding: '8px 12px',
                backgroundColor: '#e6f7ff',
                border: '1px solid #91d5ff',
                borderRadius: '6px',
                fontSize: '14px',
                color: '#0050b3',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Spin size="small" />
                <span>📤 圖片上傳中，請稍候...</span>
              </div>
            )}

            {/* 🆕 使用提示：剪貼簿貼上功能 */}
            <div style={{
              marginTop: '8px',
              padding: '8px 12px',
              backgroundColor: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: '6px',
              fontSize: '13px',
              color: '#ad6800'
            }}>
              💡 <strong>新功能：</strong>支援截圖後直接貼上（Ctrl+V）上傳圖片
            </div>
          </Card>
        </div>
      )}

      {/* 全螢幕模式下的浮動圖片管理按鈕 */}
      {isFullScreen && (
        <div style={{ position: 'fixed', top: '60px', right: '20px', zIndex: 9999 }}>
          <Button
            icon={<PictureOutlined />}
            onClick={toggleDrawer}
            type="primary"
            size="large"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(24, 144, 255, 0.4)',
              background: drawerVisible ? '#52c41a' : '#1890ff',
              borderColor: drawerVisible ? '#52c41a' : '#1890ff'
            }}
          >
            📷 {isEditMode ? config.labels.imageManager : config.labels.imageManagerStaging}
          </Button>
        </div>
      )}

      {/* 圖片管理側拉面板 */}
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PictureOutlined style={{ color: '#1890ff' }} />
            <span>{config.labels.imageManager}</span>
            {isEditMode ? (
              <span style={{
                fontSize: '12px',
                color: '#666',
                backgroundColor: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                ID: {contentId}
              </span>
            ) : (
              <span style={{
                fontSize: '12px',
                color: '#fa8c16',
                backgroundColor: '#fff7e6',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid #ffd591'
              }}>
                暫存模式
              </span>
            )}
          </div>
        }
        placement="right"
        width={450}
        open={drawerVisible}
        onClose={toggleDrawer}
        bodyStyle={{ padding: '12px' }}
        headerStyle={{
          borderBottom: '1px solid #e8e8e8',
          backgroundColor: '#fafafa'
        }}
        style={{ zIndex: isFullScreen ? 10000 : 1000 }}
        getContainer={isFullScreen ? () => document.fullscreenElement || document.body : false}
        extra={
          <Tooltip title="關閉圖片管理">
            <Button
              type="text"
              icon={<CloseOutlined />}
              onClick={toggleDrawer}
            />
          </Tooltip>
        }
      >
        <ContentImageManager
          contentType={contentType}
          contentId={contentId}
          images={images}
          onImagesChange={handleImagesChange}
          onContentUpdate={handleContentUpdate}
          onImageInsert={insertImageAtCursor}
          cursorPosition={cursorPosition}
          maxImages={config.imageConfig.maxImages}
          maxSizeMB={config.imageConfig.maxSizeMB}
          title=""
          stagingMode={!isEditMode}
          onGetStagedImages={(getterFn) => {
            getStagedImagesRef.current = getterFn;
          }}
        />
      </Drawer>
    </div>
  );
};

export default MarkdownEditorLayout;
