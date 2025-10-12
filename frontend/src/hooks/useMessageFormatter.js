import { useMemo } from 'react';
import MarkdownIt from 'markdown-it';
import DOMPurify from 'dompurify';
import { 
  processContentFormat,
  hasImgIdReferences,
  extractImagesFromMetadata,
  extractImagesFromContent,
  checkImageMention
} from '../utils/imageProcessor';

/**
 * 消息格式化 Hook
 * 處理聊天消息的 Markdown 渲染、HTML 安全清理和內容格式化
 * 
 * 功能特色：
 * - 統一的 Markdown 解析器配置
 * - 安全的 HTML 內容清理
 * - 智能圖片檢測和提取
 * - 支援混合內容格式化
 */
const useMessageFormatter = () => {
  
  // 初始化 Markdown 解析器 (使用 useMemo 優化性能)
  const md = useMemo(() => {
    return new MarkdownIt({
      html: true,        // 允許 HTML 標籤
      xhtmlOut: false,   // 不使用 XHTML 輸出
      breaks: true,      // 將換行符轉換為 <br>
      linkify: true,     // 自動連結 URL
      typographer: true  // 啟用智能標點符號
    });
  }, []);

  /**
   * 基礎文字內容格式化
   * 用於普通 Markdown 文字內容的渲染
   * 
   * @param {string} content - 原始內容
   * @returns {string} - 格式化後的 HTML 字符串
   */
  const renderMarkdown = (content) => {
    const processedContent = processContentFormat(content);
    const html = md.render(processedContent);
    return DOMPurify.sanitize(html);
  };

  /**
   * 檢測內容中的圖片資訊
   * 從 metadata 和 content 中提取圖片檔名
   * 
   * @param {string} content - 內容字符串
   * @param {Object|null} metadata - 消息元數據
   * @returns {Array} - 圖片檔名陣列
   */
  const extractImages = (content, metadata = null) => {
    const imageFilenames = new Set();
    
    // 從 metadata 提取圖片
    const metadataImages = extractImagesFromMetadata(metadata);
    console.log('🔍 從 metadata 提取到的圖片:', metadataImages);
    
    // 從 content 提取圖片
    const contentImages = extractImagesFromContent(content);
    console.log('🔍 從 content 提取到的圖片:', contentImages);
    
    // 合併並驗證圖片檔名
    [...metadataImages, ...contentImages].forEach(filename => {
      // 🎯 更嚴格的圖片檔名驗證
      if (filename && 
          filename.length >= 10 && 
          /\.(png|jpg|jpeg|gif|bmp|webp)$/i.test(filename) &&
          !/[\s\n\r,，。()]/.test(filename)) {
        imageFilenames.add(filename);
        console.log('✅ 有效圖片檔名:', filename);
      } else {
        console.log('❌ 無效圖片檔名:', filename);
      }
    });
    
    const validImages = Array.from(imageFilenames);
    console.log('🎯 最終有效圖片列表:', validImages);
    
    return validImages;
  };

  /**
   * 分析內容段落，找出提及圖片的段落
   * 用於智能圖片插入邏輯
   * 
   * @param {string} content - 內容字符串
   * @returns {Array} - 段落陣列，包含圖片提及資訊
   */
  const analyzeParagraphs = (content) => {
    const processedContent = processContentFormat(content);
    const paragraphs = processedContent.split('\n\n').filter(p => p.trim());
    
    return paragraphs.map((paragraph, index) => ({
      index,
      content: paragraph,
      mentionsImage: checkImageMention(paragraph),
      html: DOMPurify.sanitize(md.render(paragraph))
    }));
  };

  /**
   * 檢查內容格式類型
   * 判斷是否包含特殊的 IMG:ID 格式
   * 
   * @param {string} content - 內容字符串
   * @returns {Object} - 格式分析結果
   */
  const analyzeContentFormat = (content) => {
    const hasImgIdRef = hasImgIdReferences(content);
    
    return {
      hasImgIdReferences: hasImgIdRef,
      isPlainText: !hasImgIdRef,
      needsImageProcessing: hasImgIdRef || extractImagesFromContent(content).length > 0
    };
  };

  /**
   * 分離 IMG:ID 格式的混合內容
   * 將包含 **[IMG:1]** 格式的內容分離為文字和圖片部分
   * 
   * @param {string} content - 包含 IMG:ID 格式的內容
   * @returns {Array} - 分離後的內容段落陣列
   */
  const parseImgIdContent = (content) => {
    const parts = content.split(/(\*?\*?\[IMG:\d+\]\*?\*?)/g);
    
    return parts.filter(part => part.trim()).map((part, index) => {
      const isImageRef = /\*?\*?\[IMG:\d+\]\*?\*?/.test(part);
      
      if (isImageRef) {
        return {
          type: 'image',
          content: part.replace(/^\*+|\*+$/g, ''), // 移除前後的 * 符號
          index
        };
      } else {
        return {
          type: 'text',
          content: part,
          html: DOMPurify.sanitize(md.render(processContentFormat(part))),
          index
        };
      }
    });
  };

  // 返回所有格式化相關的函數和工具
  return {
    // 基礎功能
    md,                      // Markdown 解析器實例
    renderMarkdown,          // 基礎 Markdown 渲染
    
    // 內容分析
    analyzeContentFormat,    // 分析內容格式類型
    analyzeParagraphs,       // 分析段落和圖片提及
    parseImgIdContent,       // 解析 IMG:ID 格式內容
    
    // 圖片處理
    extractImages,           // 提取圖片檔名
    
    // 工具函數
    processContentFormat,    // 內容預處理 (從 imageProcessor 導入)
    hasImgIdReferences,      // 檢查 IMG:ID 格式 (從 imageProcessor 導入)
    checkImageMention        // 檢查圖片提及 (從 imageProcessor 導入)
  };
};

export default useMessageFormatter;