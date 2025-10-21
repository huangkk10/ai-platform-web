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
 * 🔧 修復：同時處理 **[IMG:ID] filename.jpg** 這種包含粗體和檔名的格式
 * 
 * @param {string} content - 原始內容
 * @returns {string} - 轉換後的內容
 */
export const convertImageReferencesToMarkdown = (content) => {
  if (!content) return content;
  
  // 🔧 一步到位：匹配並清理所有格式的圖片引用
  // 關鍵修正：檔名在星號之間，所以模式是 **[IMG:ID] filename**
  // 格式範例：
  // - **[IMG:30] 1.1.jpg**  → ![IMG:30](URL)
  // - **[IMG:30]**          → ![IMG:30](URL)
  // - [IMG:30] test.png     → ![IMG:30](URL)
  // - [IMG:30]              → ![IMG:30](URL)
  const processed = content.replace(
    /\*+\[IMG:(\d+)\](?:\s+[\w.-]+\.(?:png|jpg|jpeg|gif|bmp|webp))?\*+|\[IMG:(\d+)\](?:\s+[\w.-]+\.(?:png|jpg|jpeg|gif|bmp|webp))?/gi,
    (match, id1, id2) => {
      const imageId = id1 || id2;  // 從兩個分支中取得 ID
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
