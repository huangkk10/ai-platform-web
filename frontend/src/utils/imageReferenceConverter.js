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
 * @param {string} content - 原始內容
 * @returns {string} - 轉換後的內容
 */
export const convertImageReferencesToMarkdown = (content) => {
  if (!content) return content;
  
  // 匹配 [IMG:數字] 格式，但排除已經是 Markdown 圖片格式的 ![IMG:數字](...)
  // 使用負向後視確保前面不是 !
  const pattern = /(?<!\!)(\[IMG:(\d+)\])/g;
  
  // 🔥 使用實際的 API URL，這樣即使用標準的 <img> 標籤也能顯示
  // ReactMarkdown 會渲染為：<img src="http://10.10.173.12/api/content-images/8/" alt="IMG:8" />
  const converted = content.replace(pattern, (match, fullMatch, imageId) => {
    const apiUrl = `http://10.10.173.12/api/content-images/${imageId}/`;
    return `![IMG:${imageId}](${apiUrl})`;
  });
  
  return converted;
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
