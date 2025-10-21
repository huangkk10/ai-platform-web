/**
 * 圖片引用轉換工具
 * 將 [IMG:ID] 格式轉換為 Markdown 圖片格式 ![IMG:ID](IMG:ID)
 */

/**
 * 將內容中的 [IMG:ID] 轉換為 Markdown 圖片格式（使用實際 API URL）
 * 
 * 🎯 關鍵改進：直接使用 API URL，讓 ReactMarkdown 的標準 img 標籤就能顯示圖片
 * 格式：[IMG:8] → ![IMG:8](http://10.10.173.12/api/content-images/8/)
 * 
 * ⚠️ 後端清理策略：
 * - 後端 (process_dify_answer) 已經清理了描述文字和檔名
 * - 前端只需處理簡單的 [IMG:ID] 轉換
 * - 這樣邏輯更清晰，不需要在前端做複雜的字串處理
 * 
 * @param {string} content - 原始內容
 * @returns {string} - 轉換後的內容
 */
export const convertImageReferencesToMarkdown = (content) => {
  if (!content) return content;
  
  // 🎯 簡化邏輯：後端已清理，只需轉換 [IMG:ID] → ![IMG:ID](URL)
  // 使用 negative lookbehind 避免重複轉換已經是 ![IMG:ID] 格式的內容
  const processed = content.replace(
    /(?<!\!)\[IMG:(\d+)\]/gi,
    (match, imageId) => {
      const apiUrl = `http://10.10.173.12/api/content-images/${imageId}/`;
      return `![IMG:${imageId}](${apiUrl})`;
    }
  );
  
  return processed;
};

/**
 * 檢查內容是否包含圖片引用
 * 
 * @param {string} content - 內容
 * @returns {boolean} - 是否包含圖片引用
 */
export const hasImageReferences = (content) => {
  if (!content) return false;
  return /\[IMG:\d+\]/i.test(content);
};

/**
 * 從內容中提取所有圖片 ID
 * 
 * @param {string} content - 內容
 * @returns {Array<number>} - 圖片 ID 數組
 */
export const extractImageIds = (content) => {
  if (!content) return [];
  
  const matches = content.matchAll(/\[IMG:(\d+)\]/gi);
  const ids = [];
  
  for (const match of matches) {
    ids.push(parseInt(match[1], 10));
  }
  
  return ids;
};

export default {
  convertImageReferencesToMarkdown,
  hasImageReferences,
  extractImageIds
};
