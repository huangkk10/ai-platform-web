import React, { useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Button, Space, Spin, Alert, Card, Image } from 'antd';
import { ArrowLeftOutlined, EditOutlined } from '@ant-design/icons';
import MarkdownIt from 'markdown-it';

import TopHeader from '../../components/TopHeader';
import { knowledgeBaseConfigs } from '../../config/knowledgeBaseConfig';
import useGuidePreview from '../../hooks/useGuidePreview';
import { fixAllMarkdownTables } from '../../utils/markdownTableFixer';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';

import '../../components/markdown/ReactMarkdown.css';
import './GuidePreviewPage.css';

// 初始化 Markdown 解析器（與 MarkdownEditorLayout 一致）
const mdParser = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: true,
  typographer: true
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
    // 🔧 修復：使用動態 origin 而非硬編碼的 IP
    const baseUrl = window.location.origin;
    htmlString = htmlString.replace(
      /<img src="http:\/\/[^"]+\/api\/content-images\/(\d+)\/" alt="([^"]*)"[^>]*>/g,
      (match, imageId, altText) => {
        return `<img 
          class="content-image-preview" 
          data-image-id="${imageId}" 
          alt="${altText}"
          src="${baseUrl}/api/content-images/${imageId}/"
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

// 圖片預覽樣式
const imagePreviewStyles = `
  .guide-preview-content img.content-image-preview {
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
  
  .guide-preview-content img.content-image-preview:hover {
    border-color: #1890ff !important;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3) !important;
  }
  
  .guide-preview-content img.content-image-preview.loaded {
    border-color: #52c41a !important;
  }
  
  .guide-preview-content img.content-image-preview.failed {
    border-color: #ff4d4f !important;
  }
`;

/**
 * Guide 預覽頁面（整頁模式）
 * 
 * 功能：
 * - 整頁顯示 Markdown 內容
 * - 使用 MarkdownIt 渲染（與編輯器預覽一致）
 * - 支持圖片顯示和點擊放大
 * - 提供返回和編輯按鈕
 * 
 * 路由：/knowledge/rvt-guide/preview/:id
 */
const GuidePreviewPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = window.location || { pathname: '' };
  const contentRef = useRef(null);
  const [imageDataMap, setImageDataMap] = useState({});
  const [loadingImages, setLoadingImages] = useState(new Set());
  const [previewVisible, setPreviewVisible] = useState(false);
  const [previewImage, setPreviewImage] = useState('');

  // 🎯 根據 URL 路徑自動識別配置
  const isProtocolGuide = location.pathname?.includes('/protocol-guide/');
  const configKey = isProtocolGuide ? 'protocol-assistant' : 'rvt-assistant';
  const config = knowledgeBaseConfigs[configKey];

  // 使用 Hook 載入數據
  const { guide, loading, error } = useGuidePreview(id, config);

  // 處理預覽面板中的圖片異步加載（與 MarkdownEditorLayout 一致）
  useEffect(() => {
    if (!guide?.content || !contentRef.current) return;
    
    // 延遲執行，確保 HTML 已渲染
    const timer = setTimeout(async () => {
      const container = contentRef.current;
      if (!container) return;
      
      // 找到所有需要載入的圖片
      let images = container.querySelectorAll('img.content-image-preview[data-image-id]');
      
      if (images.length === 0) {
        // 備用：找所有包含 content-images URL 的圖片
        images = container.querySelectorAll('img[src*="content-images"]');
        console.log('� [GuidePreviewPage] 使用備用選擇器，找到圖片數:', images.length);
      } else {
        console.log('🎯 [GuidePreviewPage] 找到圖片數:', images.length);
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
          // 🔧 修復：使用相對路徑而非硬編碼的 IP
          const response = await fetch(`/api/content-images/${imageId}/`, {
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
            
            console.log(`✅ [GuidePreviewPage] 圖片 ${imageId} 載入成功`);
          }
        } catch (error) {
          console.error(`❌ [GuidePreviewPage] 圖片 ${imageId} 載入失敗:`, error);
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
  }, [guide?.content, imageDataMap, loadingImages]);

  /**
   * 處理返回
   * 🆕 優先使用瀏覽器歷史記錄返回，以保留分頁狀態
   */
  const handleBack = () => {
    // 檢查是否有歷史記錄可以返回
    if (window.history.length > 1) {
      navigate(-1);  // 返回上一頁，保留分頁狀態
    } else {
      // 沒有歷史記錄時，導航到列表頁
      navigate(config.routes.list);
    }
  };

  /**
   * 處理編輯
   */
  const handleEdit = () => {
    if (guide) {
      const editPath = config.routes.getEditPath(guide.id);
      navigate(editPath);
    }
  };

  // TopHeader 按鈕
  const extraActions = (
    <Space>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={handleBack}
        size="large"
      >
        返回列表
      </Button>
      <Button
        type="primary"
        icon={<EditOutlined />}
        onClick={handleEdit}
        size="large"
        disabled={!guide}
      >
        編輯
      </Button>
    </Space>
  );

  // 載入中狀態
  if (loading) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="載入中..."
          extraActions={extraActions}
        />
        <div className="guide-preview-loading">
          <Spin size="large" tip="正在載入文檔..." />
        </div>
      </div>
    );
  }

  // 錯誤狀態
  if (error) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="載入失敗"
          extraActions={extraActions}
        />
        <div className="guide-preview-error">
          <Alert
            message="載入失敗"
            description={error}
            type="error"
            showIcon
            action={
              <Button size="small" onClick={handleBack}>
                返回列表
              </Button>
            }
          />
        </div>
      </div>
    );
  }

  // 沒有數據
  if (!guide) {
    return (
      <div className="guide-preview-container">
        <TopHeader
          pageTitle="找不到文檔"
          extraActions={extraActions}
        />
        <div className="guide-preview-error">
          <Alert
            message="找不到文檔"
            description="請檢查文檔 ID 是否正確"
            type="warning"
            showIcon
          />
        </div>
      </div>
    );
  }

  // 處理內容
  const processedContent = guide ? renderMarkdownWithImages(guide.content) : '';

  // 正常顯示
  return (
    <div className="guide-preview-container">
      {/* 注入樣式 */}
      <style>{imagePreviewStyles}</style>
      
      <TopHeader
        pageTitle={guide?.title || '文檔預覽'}
        extraActions={extraActions}
      />

      <div className="guide-preview-wrapper">
        <Card className="guide-preview-card">
          {/* 文檔元信息 */}
          {guide?.full_category_name && (
            <div className="guide-preview-meta">
              <span className="meta-label">分類：</span>
              <span className="meta-value">{guide.full_category_name}</span>
            </div>
          )}

          {guide?.created_at && (
            <div className="guide-preview-meta">
              <span className="meta-label">建立時間：</span>
              <span className="meta-value">
                {new Date(guide.created_at).toLocaleString('zh-TW')}
              </span>
            </div>
          )}

          {/* Markdown 內容 */}
          <div 
            ref={contentRef}
            className="guide-preview-content markdown-content"
            dangerouslySetInnerHTML={{ __html: processedContent }}
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
        </Card>
      </div>
      
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

export default GuidePreviewPage;
