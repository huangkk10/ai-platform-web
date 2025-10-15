import { useMemo } from 'react';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../components/markdown/MarkdownComponents';
import { 
  processContentFormat,
  hasImgIdReferences,
  extractImagesFromMetadata,
  extractImagesFromContent,
  checkImageMention
} from '../utils/imageProcessor';
import { smartAnalyzeParagraphs } from '../utils/smartParagraphAnalyzer';

/**
 * 消息格式化 Hook
 * 處理聊天消息的 React Markdown 渲染和內容格式化
 * 
 * 功能特色：
 * - React 組件化的 Markdown 渲染
 * - 自定義組件處理表格和圖片
 * - 智能圖片檢測和提取
 * - 支援混合內容格式化
 * - GFM (GitHub Flavored Markdown) 支援
 */
const useMessageFormatter = () => {
  
  // React Markdown 配置 (使用 useMemo 優化性能)
  const markdownConfig = useMemo(() => ({
    remarkPlugins: [remarkGfm], // 支援表格、任務列表等 GFM 功能
    components: markdownComponents, // 自定義組件
    // 安全設定
    disallowedElements: ['script', 'iframe', 'object', 'embed'],
    unwrapDisallowed: true
  }), []);

  /**
   * 基礎文字內容預處理
   * 用於處理特殊格式和準備 React Markdown 渲染
   * 
   * @param {string} content - 原始內容
   * @returns {string} - 預處理後的 Markdown 內容
   */
  const prepareMarkdown = (content) => {
    return processContentFormat(content);
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
   * 🔧 智能分析內容段落，保持表格完整性
   * 修復版本：不會打散 markdown 表格
   * 用於智能圖片插入邏輯
   * 
   * @param {string} content - 內容字符串
   * @returns {Array} - 段落陣列，包含圖片提及資訊
   */
  const analyzeParagraphs = (content) => {
    const processedContent = processContentFormat(content);
    
    // 🎯 使用智能段落分析，保持表格完整性
    return smartAnalyzeParagraphs(processedContent);
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
          processedContent: processContentFormat(part), // 供 ReactMarkdown 使用
          index
        };
      }
    });
  };

  // 返回所有格式化相關的函數和工具
  return {
    // React Markdown 配置
    markdownConfig,          // React Markdown 配置物件
    
    // 基礎功能
    prepareMarkdown,         // 預處理 Markdown 內容
    
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