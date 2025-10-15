/**
 * Markdown 表格修復工具
 * 
 * 修復問題：remarkGfm 要求表格分隔線每個單元格至少 3 個破折號
 * 錯誤格式：|---|---|---| 
 * 正確格式：|------|------|------|
 */

/**
 * 檢測是否為表格分隔線
 * @param {string} line - 行內容
 * @returns {boolean}
 */
export const isTableSeparator = (line) => {
  // 匹配表格分隔線：| --- | --- | 或 |---|---|
  return /^\s*\|[\s\-:|]+\|\s*$/.test(line);
};

/**
 * 修復表格分隔線（確保每個單元格至少 3 個破折號）
 * @param {string} line - 原始分隔線
 * @returns {string} - 修復後的分隔線
 */
export const fixTableSeparator = (line) => {
  if (!isTableSeparator(line)) {
    return line;
  }

  // 分解單元格
  const cells = line.split('|').filter(cell => cell.trim().length > 0);
  
  // 修復每個單元格
  const fixedCells = cells.map(cell => {
    const trimmed = cell.trim();
    
    // 檢查是否有對齊標記
    const leftAlign = trimmed.startsWith(':');
    const rightAlign = trimmed.endsWith(':');
    
    // 計算破折號數量（至少 3 個）
    const dashCount = Math.max(3, trimmed.replace(/:/g, '').length);
    
    // 重建單元格
    let fixed = '-'.repeat(dashCount);
    if (leftAlign) fixed = ':' + fixed;
    if (rightAlign) fixed = fixed + ':';
    
    return fixed;
  });

  // 重建分隔線
  return '| ' + fixedCells.join(' | ') + ' |';
};

/**
 * 檢測是否為完整的 markdown 表格
 * @param {string} text - 文本內容
 * @returns {boolean}
 */
export const isMarkdownTable = (text) => {
  const lines = text.trim().split('\n');
  if (lines.length < 2) return false;
  
  // 檢查是否有分隔線
  return lines.some(line => isTableSeparator(line));
};

/**
 * 修復 markdown 表格格式
 * @param {string} text - 包含表格的文本
 * @returns {string} - 修復後的文本
 */
export const fixMarkdownTable = (text) => {
  const lines = text.split('\n');
  const fixedLines = lines.map(line => {
    if (isTableSeparator(line)) {
      return fixTableSeparator(line);
    }
    return line;
  });
  
  return fixedLines.join('\n');
};

/**
 * 修復整個 markdown 內容中的所有表格
 * @param {string} content - markdown 內容
 * @returns {string} - 修復後的內容
 */
export const fixAllMarkdownTables = (content) => {
  if (!content) return content;
  
  const lines = content.split('\n');
  const fixedLines = [];
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    // 如果是分隔線，修復它
    if (isTableSeparator(line)) {
      fixedLines.push(fixTableSeparator(line));
    } else {
      fixedLines.push(line);
    }
  }
  
  return fixedLines.join('\n');
};

/**
 * 驗證表格分隔線是否符合 remarkGfm 規範
 * @param {string} line - 分隔線
 * @returns {{valid: boolean, reason: string}}
 */
export const validateTableSeparator = (line) => {
  if (!isTableSeparator(line)) {
    return { valid: false, reason: '不是有效的表格分隔線格式' };
  }
  
  const cells = line.split('|').filter(cell => cell.trim().length > 0);
  
  for (let i = 0; i < cells.length; i++) {
    const cell = cells[i].trim();
    const dashCount = cell.replace(/:/g, '').length;
    
    if (dashCount < 3) {
      return { 
        valid: false, 
        reason: `第 ${i + 1} 個單元格只有 ${dashCount} 個破折號（需要至少 3 個）` 
      };
    }
  }
  
  return { valid: true, reason: '格式正確' };
};

// 測試範例
export const examples = {
  // 錯誤格式
  invalid: [
    '|---|---|---|',           // 每個單元格只有 1 個破折號
    '| -- | -- | -- |',        // 每個單元格只有 2 個破折號
    '|:-|:-:|--:|'             // 含對齊標記但破折號太少
  ],
  
  // 正確格式
  valid: [
    '|------|------|------|',  // 每個單元格 6 個破折號
    '| --- | --- | --- |',     // 每個單元格 3 個破折號
    '|:------|:------:|------:|' // 含對齊標記且破折號足夠
  ]
};

export default {
  isTableSeparator,
  fixTableSeparator,
  isMarkdownTable,
  fixMarkdownTable,
  fixAllMarkdownTables,
  validateTableSeparator,
  examples
};
