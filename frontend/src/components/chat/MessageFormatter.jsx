import React from 'react';
import ReactMarkdown from 'react-markdown';
import ContentRenderer from '../ContentRenderer';
import MessageImages from './MessageImages';
import RetrievalSourcesDisplay from './RetrievalSourcesDisplay';
import useMessageFormatter from '../../hooks/useMessageFormatter';
import { loadImagesData } from '../../utils/imageProcessor';
import { fixAllMarkdownTables } from '../../utils/markdownTableFixer';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';
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
  
  // 🎯 新增：檢測內容是否包含 Markdown 表格
  const hasMarkdownTable = content && /\|.*\|[\r\n]+\|[\s\-:|]+\|/.test(content);

  /**
   * 渲染純文字消息 (主要用於用戶消息)
   * 當 skipMetadataImages=true 時，不處理 metadata 中的圖片（讓表格內的圖片自己處理）
   */
  const renderPlainTextMessage = (skipMetadataImages = false) => {
    // ✅ 方案 1：使用 Markdown 測試頁面的簡化流程
    // 不調用 prepareMarkdown()，直接使用原始 content
    let processedContent = content;
    // 修復表格分隔線格式
    processedContent = fixAllMarkdownTables(processedContent);
    // 🎯 關鍵：將 [IMG:ID] 轉換為 Markdown 圖片格式 ![IMG:ID](IMG:ID)
    // 這樣 ReactMarkdown 才會調用 CustomImage 組件
    processedContent = convertImageReferencesToMarkdown(processedContent);
    
    // 如果需要顯示 metadata 中的圖片（且不是表格情況）
    if (!skipMetadataImages && metadata && messageType === 'assistant') {
      const imageArray = extractImages(content, metadata);
      
      // 只顯示不在內容中的圖片（避免重複）
      const imagesNotInContent = imageArray.filter(filename => {
        // 檢查圖片是否已經在內容中被引用
        return !content.includes(filename) && !content.includes('[IMG:');
      });
      
      if (imagesNotInContent.length > 0) {
        return (
          <div className={`markdown-preview-content markdown-content ${className}`} style={style}>
            <ReactMarkdown {...markdownConfig}>
              {processedContent}
            </ReactMarkdown>
            <div style={{ marginTop: '12px' }}>
              <MessageImages 
                filenames={imagesNotInContent} 
                onImageLoad={loadImagesData}
              />
            </div>
            {/* 🆕 添加引用來源顯示（只在 AI 回覆時） */}
            {messageType === 'assistant' && metadata?.retriever_resources && (
              <RetrievalSourcesDisplay 
                retrieverResources={metadata.retriever_resources}
                maxDisplay={5}
              />
            )}
          </div>
        );
      }
    }
    
    return (
      <div 
        className={`markdown-preview-content markdown-content ${className}`}
        style={style}
      >
        <ReactMarkdown {...markdownConfig}>
          {processedContent}
        </ReactMarkdown>
        {/* 🆕 添加引用來源顯示（只在 AI 回覆時） */}
        {messageType === 'assistant' && metadata?.retriever_resources && (
          <RetrievalSourcesDisplay 
            retrieverResources={metadata.retriever_resources}
            maxDisplay={5}
          />
        )}
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
                className="markdown-preview-content markdown-content"
              >
                <ReactMarkdown {...markdownConfig}>
                  {part.processedContent}
                </ReactMarkdown>
              </div>
            );
          }
        })}
        {/* 🆕 添加引用來源顯示（只在 AI 回覆時） */}
        {messageType === 'assistant' && metadata?.retriever_resources && (
          <RetrievalSourcesDisplay 
            retrieverResources={metadata.retriever_resources}
            maxDisplay={5}
          />
        )}
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
    console.log('📊 智能段落分析結果:', paragraphs);
    
    if (imageArray.length === 0) {
      // 沒有圖片，使用普通文字渲染
      return renderPlainTextMessage();
    }

    const result = [];
    let remainingImages = [...imageArray]; // 創建副本避免修改原數組
    const markdownBuffer = []; // 用於累積需要一起渲染的 markdown 內容
    
    const flushMarkdownBuffer = (key) => {
      if (markdownBuffer.length > 0) {
        // 將累積的 markdown 內容一次性渲染，並修復表格格式
        // 🎯 使用 \n 而不是 \n\n，避免產生過大間距
        let combinedMarkdown = markdownBuffer.join('\n');
        combinedMarkdown = fixAllMarkdownTables(combinedMarkdown);
        
        result.push(
          <div 
            key={key}
            className="markdown-preview-content markdown-content"
          >
            <ReactMarkdown {...markdownConfig}>
              {combinedMarkdown}
            </ReactMarkdown>
          </div>
        );
        // 清空 buffer
        markdownBuffer.length = 0;
      }
    };
    
    paragraphs.forEach((paragraph, index) => {
      // 🎯 關鍵修復：將 markdown 內容累積，而不是立即渲染
      markdownBuffer.push(paragraph.processedContent);
      
      // 🔍 檢查是否提及圖片且確實有可用的圖片檔名
      if (paragraph.mentionsImage && remainingImages.length > 0) {
        // 🎯 先將累積的 markdown 渲染出來
        flushMarkdownBuffer(`markdown-${index}`);
        
        // 🎯 進一步驗證圖片檔名的有效性
        const validImages = remainingImages.filter(filename => {
          const basicCheck = filename && 
            filename.length >= 10 && 
            /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename) &&
            !/[\s\n\r,，。()]/.test(filename);
          
          if (!basicCheck) {
            console.log('⚠️ MessageFormatter: 過濾無效圖片檔名（基本檢查）:', filename);
            return false;
          }
          
          // 🎯 進階檢查：避免誤判簡短檔名
          const filenameWithoutExt = filename.replace(/\.(png|jpg|jpeg|gif|bmp|webp)$/i, '');
          const hasMinLength = filenameWithoutExt.length >= 5;
          const hasSpecialChars = /[-_]/.test(filenameWithoutExt);
          const isValid = hasMinLength || hasSpecialChars;
          
          if (!isValid) {
            console.log('⚠️ MessageFormatter: 過濾無效圖片檔名（檔名太短）:', filename);
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
    
    // 🎯 渲染剩餘的 markdown 內容
    flushMarkdownBuffer('markdown-final');
    
    // 如果還有剩餘圖片沒有顯示，在最後顯示
    if (remainingImages.length > 0) {
      console.log('📸 在最後顯示剩餘圖片:', remainingImages);
      
      // 再次過濾有效圖片
      const finalValidImages = remainingImages.filter(filename => {
        if (!filename || filename.length < 8 || !/\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename)) {
          return false;
        }
        
        // 🎯 進階檢查：避免誤判簡短檔名
        const filenameWithoutExt = filename.replace(/\.(png|jpg|jpeg|gif|bmp|webp)$/i, '');
        const hasMinLength = filenameWithoutExt.length >= 5;
        const hasSpecialChars = /[-_]/.test(filenameWithoutExt);
        
        return hasMinLength || hasSpecialChars;
      });
      
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
    
    // 🆕 添加引用來源顯示到結果陣列
    if (metadata?.retriever_resources) {
      result.push(
        <RetrievalSourcesDisplay 
          key="retrieval-sources"
          retrieverResources={metadata.retriever_resources}
          maxDisplay={5}
        />
      );
    }
    
    return (
      <div className={`message-with-inline-images ${className}`} style={style}>
        {result}
      </div>
    );
  };

  // 根據內容格式和消息類型選擇適當的渲染策略
  // 🎯 關鍵修復：優先檢查表格，因為表格可能包含 [IMG:ID]
  if (hasMarkdownTable) {
    // 如果內容包含 Markdown 表格，使用純文字渲染
    // 表格中的圖片由 CustomImage 組件自動處理，不切斷表格
    // skipMetadataImages=true：不顯示 metadata 中的圖片，避免重複
    console.log('📊 檢測到 Markdown 表格，使用純文字渲染以保持表格完整性');
    return renderPlainTextMessage(true); // 傳入 true 跳過 metadata 圖片
  } else if (formatAnalysis.hasImgIdReferences) {
    // ✅ 方案 1：包含 IMG:ID 格式也使用純文字渲染（與 Markdown 測試頁面一致）
    console.log('🖼️ 檢測到 IMG:ID 引用，使用純文字渲染（與 Markdown 測試頁面一致）');
    return renderPlainTextMessage(false);
  } else if (messageType === 'assistant' && formatAnalysis.needsImageProcessing) {
    // AI 回應且需要圖片處理，使用智能圖片內嵌
    return renderAssistantMessageWithImages();
  } else {
    // 普通文字消息，使用基礎 Markdown 渲染
    return renderPlainTextMessage(false); // 傳入 false 處理 metadata 圖片
  }
};

// 🎯 使用 React.memo 優化，避免不必要的重新渲染
// 只有當 content 或 metadata 真正改變時才重新渲染
export default React.memo(MessageFormatter, (prevProps, nextProps) => {
  return (
    prevProps.content === nextProps.content &&
    prevProps.metadata === nextProps.metadata &&
    prevProps.messageType === nextProps.messageType
  );
});