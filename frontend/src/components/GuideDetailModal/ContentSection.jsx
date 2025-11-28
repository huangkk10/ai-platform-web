import React, { useEffect, useRef, useState } from 'react';
import { Typography, Image, Spin } from 'antd';
import MarkdownIt from 'markdown-it';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';
import { fixAllMarkdownTables } from '../../utils/markdownTableFixer';

const { Title } = Typography;

// 初始化 Markdown 解析器（與 MarkdownEditorLayout 一致）
const mdParser = new MarkdownIt({
  html: true,        // 啟用 HTML 標籤支援
  breaks: true,      // 將換行符轉換為 <br>
  linkify: true,     // 自動將 URL 轉為連結
  typographer: true  // 啟用智能標點符號
});

/**
 * 自定義 renderHTML 函數（支援圖片預覽）
 * 與 MarkdownEditorLayout 的 renderMarkdownWithImages 一致
 */
const renderMarkdownWithImages = (text) => {
  try {
    // 步驟 1：修復表格格式
    let processed = fixAllMarkdownTables(text);
    
    // 步驟 2：將 [IMG:ID] 轉換為 Markdown 圖片格式
    processed = convertImageReferencesToMarkdown(processed);
    
    // 步驟 3：使用 markdown-it 渲染
    let htmlString = mdParser.render(processed);
    
    // 步驟 4：後處理圖片 HTML（添加 data 屬性供異步載入）
    htmlString = htmlString.replace(
      /<img src="http:\/\/[^"]+\/api\/content-images\/(\d+)\/" alt="([^"]*)"[^>]*>/g,
      (match, imageId, altText) => {
        return `<img 
          class="content-image-preview" 
          data-image-id="${imageId}" 
          alt="${altText}"
          src="http://10.10.172.127/api/content-images/${imageId}/"
          style="max-width: 100px; height: auto; border: 1px solid #d9d9d9; border-radius: 4px; margin: 0 4px; padding: 4px; background-color: #fafafa; display: inline-block; vertical-align: middle; cursor: pointer;"
        />`;
      }
    );
    
    return htmlString;
  } catch (error) {
    console.error('❌ Markdown 渲染錯誤:', error);
    return mdParser.render(text);
  }
};

// 自定義樣式（與 MarkdownEditorLayout 一致）
const markdownStyles = `
  .markdown-preview-content img.content-image-preview {
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
    transition: all 0.3s ease !important;
  }
  
  .markdown-preview-content img.content-image-preview:hover {
    border-color: #1890ff !important;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3) !important;
  }
  
  .markdown-preview-content img.content-image-preview.loaded {
    border-color: #52c41a !important;
  }
  
  .markdown-preview-content img.content-image-preview.failed {
    border-color: #ff4d4f !important;
  }
  
  .markdown-preview-content table {
    border-collapse: collapse;
    width: 100%;
    margin: 16px 0;
  }
  
  .markdown-preview-content th,
  .markdown-preview-content td {
    border: 1px solid #d9d9d9;
    padding: 8px 12px;
    text-align: left;
  }
  
  .markdown-preview-content th {
    background-color: #fafafa;
    font-weight: 600;
  }
  
  .markdown-preview-content code {
    background-color: #f5f5f5;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: 'Consolas', 'Monaco', monospace;
    font-size: 13px;
  }
  
  .markdown-preview-content pre {
    background-color: #282c34;
    color: #abb2bf;
    padding: 16px;
    border-radius: 6px;
    overflow-x: auto;
  }
  
  .markdown-preview-content pre code {
    background-color: transparent;
    padding: 0;
    color: inherit;
  }
  
  .markdown-preview-content h1, 
  .markdown-preview-content h2, 
  .markdown-preview-content h3 {
    margin-top: 24px;
    margin-bottom: 12px;
    color: #1890ff;
    border-bottom: 1px solid #e8e8e8;
    padding-bottom: 8px;
  }
  
  .markdown-preview-content ul, 
  .markdown-preview-content ol {
    padding-left: 24px;
  }
  
  .markdown-preview-content li {
    margin-bottom: 4px;
  }
  
  .markdown-preview-content blockquote {
    border-left: 4px solid #1890ff;
    padding-left: 16px;
    margin: 16px 0;
    color: #666;
    background-color: #f9f9f9;
    padding: 12px 16px;
    border-radius: 0 4px 4px 0;
  }
`;

/**
 * 文檔內容區塊組件
 * 使用 Markdown 渲染（與 MarkdownEditorLayout 預覽效果一致）
 * 支援圖片顯示和點擊放大功能
 */
const ContentSection = ({ content }) => {
  const contentRef = useRef(null);
  const [imageDataMap, setImageDataMap] = useState({});
  const [loadingImages, setLoadingImages] = useState(new Set());
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');

  // 處理預覽面板中的圖片異步加載（與 MarkdownEditorLayout 一致）
  useEffect(() => {
    if (!content || !contentRef.current) return;
    
    // 延遲執行，確保 HTML 已渲染
    const timer = setTimeout(async () => {
      const container = contentRef.current;
      if (!container) return;
      
      // 找到所有需要載入的圖片
      const images = container.querySelectorAll('img.content-image-preview[data-image-id]');
      
      if (images.length === 0) {
        // 備用：找所有包含 content-images URL 的圖片
        const fallbackImages = container.querySelectorAll('img[src*="content-images"]');
        if (fallbackImages.length > 0) {
          console.log('🔄 [ContentSection] 使用備用選擇器，找到圖片數:', fallbackImages.length);
        }
      } else {
        console.log('🎯 [ContentSection] 找到圖片數:', images.length);
      }
      
      // 異步載入每張圖片
      images.forEach(async (img) => {
        let imageId = img.getAttribute('data-image-id');
        
        // 如果沒有 data-image-id，從 src 中提取
        if (!imageId) {
          const srcMatch = img.src.match(/content-images\/(\d+)/);
          imageId = srcMatch ? srcMatch[1] : null;
        }
        
        if (!imageId) return;
        
        // 避免重複載入
        if (loadingImages.has(imageId) || imageDataMap[imageId]) {
          if (imageDataMap[imageId]) {
            img.src = imageDataMap[imageId].data_url;
            img.classList.add('loaded');
          }
          return;
        }
        
        setLoadingImages(prev => new Set(prev).add(imageId));
        
        try {
          const response = await fetch(`http://10.10.172.127/api/content-images/${imageId}/`, {
            method: 'GET',
            headers: { 'Accept': 'application/json' }
          });
          
          if (!response.ok) throw new Error(`HTTP ${response.status}`);
          
          const imageData = await response.json();
          
          if (imageData.data_url) {
            // 更新圖片
            img.src = imageData.data_url;
            img.title = imageData.title || imageData.filename || `Image ${imageId}`;
            img.alt = imageData.title || imageData.filename || `Image ${imageId}`;
            img.classList.add('loaded');
            
            // 緩存圖片數據
            setImageDataMap(prev => ({
              ...prev,
              [imageId]: imageData
            }));
            
            // 添加點擊事件（放大預覽）
            img.onclick = () => {
              setPreviewImage(imageData.data_url);
              setPreviewVisible(true);
            };
            
            console.log(`✅ [ContentSection] 圖片 ${imageId} 載入成功`);
          }
        } catch (error) {
          console.error(`❌ [ContentSection] 圖片 ${imageId} 載入失敗:`, error);
          img.alt = `⊗ [圖片載入失敗: ${imageId}]`;
          img.classList.add('failed');
        } finally {
          setLoadingImages(prev => {
            const newSet = new Set(prev);
            newSet.delete(imageId);
            return newSet;
          });
        }
      });
    }, 300);
    
    return () => clearTimeout(timer);
  }, [content, imageDataMap, loadingImages]);

  if (!content) return null;

  // 渲染 Markdown 內容
  const htmlContent = renderMarkdownWithImages(content);

  return (
    <div style={{ 
      marginBottom: '20px',
      padding: '16px',
      backgroundColor: '#e6f7ff',
      borderRadius: '8px',
      border: '1px solid #91d5ff'
    }}>
      {/* 注入樣式 */}
      <style>{markdownStyles}</style>
      
      <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
        📄 文檔內容
      </Title>
      <div 
        ref={contentRef}
        className="markdown-preview-content"
        style={{ 
          backgroundColor: 'white',
          padding: '16px',
          borderRadius: '6px',
          border: '1px solid #f5f5f5',
          fontSize: '14px',
          lineHeight: '1.8',
          minHeight: '200px',
          maxHeight: '400px',
          overflowY: 'auto'
        }}
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
      
      {/* 載入中提示 */}
      {loadingImages.size > 0 && (
        <div style={{ 
          marginTop: '8px', 
          color: '#1890ff', 
          fontSize: '12px',
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <Spin size="small" />
          <span>正在載入 {loadingImages.size} 張圖片...</span>
        </div>
      )}
      
      {/* 圖片預覽 Modal（Ant Design Image 組件） */}
      <Image
        style={{ display: 'none' }}
        preview={{
          visible: previewVisible,
          src: previewImage,
          onVisibleChange: (visible) => setPreviewVisible(visible),
        }}
      />
    </div>
  );
};

export default ContentSection;
