/**
 * 智能段落分析工具
 * 修復 MessageFormatter 中 analyzeParagraphs 打散表格的問題
 */

/**
 * 檢查文字是否為 markdown 表格的一部分
 * @param {string} text - 要檢查的文字
 * @returns {boolean} - 是否為表格內容
 */
export const isMarkdownTableContent = (text) => {
  // 檢查是否包含表格分隔符 |
  const hasTableSeparator = text.includes('|');
  
  // 檢查是否為表頭分隔行 (包含 - 和 |)
  const isTableSeparatorLine = /^\s*\|[\s\-|:]+\|\s*$/.test(text.trim());
  
  // 檢查是否為表格行 (以 | 開始和結束)
  const isTableRow = /^\s*\|.*\|\s*$/.test(text.trim());
  
  return hasTableSeparator && (isTableSeparatorLine || isTableRow);
};

/**
 * 檢查段落是否為完整的 markdown 表格
 * @param {string} paragraph - 段落內容
 * @returns {boolean} - 是否為完整表格
 */
export const isCompleteMarkdownTable = (paragraph) => {
  const lines = paragraph.split('\n').filter(line => line.trim());
  
  // 需要至少 3 行：表頭、分隔符、至少一行數據
  if (lines.length < 3) return false;
  
  // 檢查所有行都包含 |
  const allLinesHaveTableSeparator = lines.every(line => line.includes('|'));
  if (!allLinesHaveTableSeparator) return false;
  
  // 檢查第二行是否為表頭分隔符
  const hasHeaderSeparator = /^\s*\|[\s\-|:]+\|\s*$/.test(lines[1].trim());
  
  return hasHeaderSeparator;
};

/**
 * 智能段落分析 - 保持表格完整性
 * 替換原有的 analyzeParagraphs 邏輯
 * 
 * @param {string} content - 原始內容
 * @returns {Array} - 智能分析後的段落數組
 */
export const smartAnalyzeParagraphs = (content) => {
  // 按 \n\n 初步分割
  const initialSplits = content.split('\n\n').filter(p => p.trim());
  
  const smartParagraphs = [];
  let i = 0;
  
  while (i < initialSplits.length) {
    const currentParagraph = initialSplits[i];
    
    // 檢查當前段落是否包含表格內容
    if (isMarkdownTableContent(currentParagraph)) {
      // 如果當前段落是完整表格，直接加入
      if (isCompleteMarkdownTable(currentParagraph)) {
        smartParagraphs.push({
          content: currentParagraph,
          type: 'complete_table',
          mentionsImage: false, // 表格段落不插入圖片
          processedContent: currentParagraph
        });
        i++;
      } else {
        // 如果是不完整的表格，嘗試合併後續段落
        let combinedTable = currentParagraph;
        let j = i + 1;
        
        // 向前查找，合併表格相關的段落
        while (j < initialSplits.length) {
          const nextParagraph = initialSplits[j];
          
          if (isMarkdownTableContent(nextParagraph)) {
            combinedTable += '\n\n' + nextParagraph;
            j++;
          } else {
            break; // 不是表格內容，停止合併
          }
        }
        
        smartParagraphs.push({
          content: combinedTable,
          type: 'merged_table',
          mentionsImage: false, // 表格段落不插入圖片
          processedContent: combinedTable
        });
        
        i = j; // 跳過已合併的段落
      }
    } else {
      // 普通文字段落，保持原邏輯
      smartParagraphs.push({
        content: currentParagraph,
        type: 'text',
        mentionsImage: checkImageMention(currentParagraph),
        processedContent: currentParagraph
      });
      i++;
    }
  }
  
  return smartParagraphs.map((paragraph, index) => ({
    ...paragraph,
    index
  }));
};

/**
 * 檢查圖片提及 (從 imageProcessor 複製的輔助函數)
 * @param {string} content - 內容
 * @returns {boolean} - 是否提及圖片
 */
const checkImageMention = (content) => {
  // 簡化的圖片提及檢查邏輯
  const imageKeywords = [
    '圖片', '圖像', '截圖', '畫面', '顯示', '如圖', '見圖',
    'image', 'screenshot', 'picture', 'photo', 'figure',
    '如下圖', '參考圖片', '附圖'
  ];
  
  return imageKeywords.some(keyword => 
    content.toLowerCase().includes(keyword.toLowerCase())
  );
};

const smartParagraphUtils = {
  isMarkdownTableContent,
  isCompleteMarkdownTable,
  smartAnalyzeParagraphs
};

export default smartParagraphUtils;