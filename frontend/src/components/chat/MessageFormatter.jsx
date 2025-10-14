import React from 'react';
import ReactMarkdown from 'react-markdown';
import ContentRenderer from '../ContentRenderer';
import MessageImages from './MessageImages';
import useMessageFormatter from '../../hooks/useMessageFormatter';
import { loadImagesData } from '../../utils/imageProcessor';
import '../markdown/ReactMarkdown.css';

/**
 * 消息格式化組件
 * 
 * 功能：
 * - 根據消息類型選擇適當的格式化策略
 * - 處理純文字消息 (用戶消息)
 * - 處理包含圖片的 AI 回應消息
 * - 處理 IMG:ID 格式的混合內容
 * - 智能圖片內嵌顯示
 */
const MessageFormatter = ({ 
  content, 
  metadata = null, 
  messageType = 'user',  // 'user' | 'assistant'
  className = '',
  style = {}
}) => {
  const {
    markdownConfig,
    analyzeContentFormat,
    analyzeParagraphs,
    parseImgIdContent,
    prepareMarkdown,
    extractImages
  } = useMessageFormatter();

  // 分析內容格式
  const formatAnalysis = analyzeContentFormat(content);

  /**
   * 渲染純文字消息 (主要用於用戶消息)
   */
  const renderPlainTextMessage = () => {
    const processedContent = prepareMarkdown(content);
    
    return (
      <div 
        className={`markdown-content ${className}`}
        style={style}
      >
        <ReactMarkdown {...markdownConfig}>
          {processedContent}
        </ReactMarkdown>
      </div>
    );
  };

  /**
   * 渲染 IMG:ID 格式的混合內容
   * 處理 **[IMG:1]** 這樣的特殊格式
   */
  const renderImgIdContent = () => {
    const parts = parseImgIdContent(content);
    
    return (
      <div className={`message-with-mixed-content ${className}`} style={style}>
        {parts.map((part, index) => {
          if (part.type === 'image') {
            return (
              <div key={`img-${index}`} style={{ margin: '12px 0', maxWidth: '200px' }}>
                <ContentRenderer 
                  content={part.content}
                  showImageTitles={true}
                  showImageDescriptions={true}
                  imageMaxWidth={120}
                  imageMaxHeight={90}
                />
              </div>
            );
          } else {
            return (
              <div 
                key={`text-${index}`}
                className="markdown-content"
              >
                <ReactMarkdown {...markdownConfig}>
                  {part.processedContent}
                </ReactMarkdown>
              </div>
            );
          }
        })}
      </div>
    );
  };

  /**
   * 渲染帶智能圖片內嵌的 AI 回應
   * 分析段落內容，在適當位置插入相關圖片
   */
  const renderAssistantMessageWithImages = () => {
    const imageArray = extractImages(content, metadata);
    const paragraphs = analyzeParagraphs(content);
    
    console.log('🎯 內嵌圖片檢測結果:', imageArray);
    
    if (imageArray.length === 0) {
      // 沒有圖片，使用普通文字渲染
      return renderPlainTextMessage();
    }

    const result = [];
    let remainingImages = [...imageArray]; // 創建副本避免修改原數組
    
    paragraphs.forEach((paragraph, index) => {
      // 渲染當前段落
      result.push(
        <div 
          key={`paragraph-${index}`}
          className="markdown-content"
        >
          <ReactMarkdown {...markdownConfig}>
            {paragraph.processedContent}
          </ReactMarkdown>
        </div>
      );
      
      // 🔍 檢查是否提及圖片且確實有可用的圖片檔名
      if (paragraph.mentionsImage && remainingImages.length > 0) {
            // 🎯 進一步驗證圖片檔名的有效性
        const validImages = remainingImages.filter(filename => {
          const isValid = filename && 
            filename.length >= 10 && 
            /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename) &&
            !/[\s\n\r,，。()]/.test(filename);
          
          if (!isValid) {
            console.log('⚠️ MessageFormatter: 過濾無效圖片檔名:', filename);
          }
          
          return isValid;
        });
        
        if (validImages.length > 0) {
          console.log('📸 找到圖片描述段落', index, ':', paragraph.content.substring(0, 100));
          console.log('📸 在該段落下方顯示有效圖片:', validImages);
          
          // 在提及圖片的段落下方直接顯示相關圖片
          result.push(
            <div key={`inline-images-${index}`} style={{ 
              margin: '4px 0',
              padding: '4px',
              backgroundColor: '#f8f9ff',
              borderRadius: '4px',
              border: '1px solid #e6f7ff',
              boxShadow: '0 1px 2px rgba(0,0,0,0.02)'
            }}>
              <div style={{ 
                fontSize: '10px', 
                color: '#1890ff', 
                marginBottom: '4px',
                fontWeight: '500'
              }}>
                📸 相關圖片展示：
              </div>
              <MessageImages 
                filenames={validImages} 
                onImageLoad={loadImagesData}
                key={`images-${index}-${validImages.join('-')}`} // 添加 key 避免重複載入
              />
            </div>
          );
          
          // 避免重複顯示，清空剩餘圖片列表
          remainingImages = [];
        } else {
          console.log('⚠️ 檢測到圖片提及但無有效圖片檔名:', remainingImages);
          console.log('🔍 段落內容:', paragraph.content);
        }
      }
    });
    
    // 如果還有剩餘圖片沒有顯示，在最後顯示
    if (remainingImages.length > 0) {
      console.log('📸 在最後顯示剩餘圖片:', remainingImages);
      
      // 再次過濾有效圖片
      const finalValidImages = remainingImages.filter(filename => 
        filename && filename.length >= 8 && /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename)
      );
      
      if (finalValidImages.length > 0) {
        result.push(
          <div key="remaining-images" style={{ marginTop: '12px' }}>
            <MessageImages 
              filenames={finalValidImages} 
              onImageLoad={loadImagesData}
              key={`remaining-${finalValidImages.join('-')}`}
            />
          </div>
        );
      } else {
        console.log('⚠️ MessageFormatter: 沒有有效的剩餘圖片可顯示');
      }
    }
    
    return (
      <div className={`message-with-inline-images ${className}`} style={style}>
        {result}
      </div>
    );
  };

  // 根據內容格式和消息類型選擇適當的渲染策略
  if (formatAnalysis.hasImgIdReferences) {
    // 包含 IMG:ID 格式，使用混合內容渲染
    return renderImgIdContent();
  } else if (messageType === 'assistant' && formatAnalysis.needsImageProcessing) {
    // AI 回應且需要圖片處理，使用智能圖片內嵌
    return renderAssistantMessageWithImages();
  } else {
    // 普通文字消息，使用基礎 Markdown 渲染
    return renderPlainTextMessage();
  }
};

export default MessageFormatter;