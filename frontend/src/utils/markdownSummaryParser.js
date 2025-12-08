/**
 * Markdown 摘要區塊解析器（自動生成 TOC）
 * 
 * 功能：
 * - 解析 ::: summary [可選標題] 語法（無需結束標記）
 * - 自動掃描文檔中的 #、##、### 標題
 * - 生成帶有層級縮排的目錄（Table of Contents）
 * - 支援錨點連結跳轉
 * - 為標題自動生成錨點 ID
 * 
 * 語法範例：
 * ::: summary                     -> 自動生成 TOC（標題為「目錄」）
 * ::: summary AVL SOP 快速導覽   -> 自動生成 TOC（自訂標題）
 * 
 * @author AI Platform Team
 * @date 2025-12-08
 */

/**
 * 生成錨點 ID
 * 將標題文字轉換為有效的 HTML ID
 * 
 * @param {string} title - 標題文字
 * @returns {string} - 錨點 ID
 * 
 * @example
 * generateAnchorId('Chromebook NB') => 'chromebook-nb'
 * generateAnchorId('Chrome image 燒錄') => 'chrome-image-燒錄'
 * generateAnchorId('Step.1 官網連結') => 'step1-官網連結'
 */
export const generateAnchorId = (title) => {
  if (!title) return '';
  
  return title
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')                    // 空格轉為 -
    .replace(/[^\w\u4e00-\u9fa5-]/g, '')     // 只保留英數字、中文、-
    .replace(/--+/g, '-')                    // 多個 - 合併為一個
    .replace(/^-|-$/g, '');                  // 移除開頭和結尾的 -
};

/**
 * 跳脫 HTML 特殊字元
 * 
 * @param {string} text - 原始文字
 * @returns {string} - 跳脫後的文字
 */
const escapeHtml = (text) => {
  if (!text) return '';
  
  const htmlEscapes = {
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  };
  
  return text.replace(/[&<>"']/g, char => htmlEscapes[char]);
};

/**
 * 從 Markdown 文本中提取所有標題
 * 掃描 #、##、### 標題（最多支援 3 級）
 * 
 * @param {string} markdown - Markdown 文本
 * @returns {Array} - 標題列表 [{ level: 1-3, text: '標題文字', anchorId: '錨點id' }]
 */
const extractHeadings = (markdown) => {
  if (!markdown) return [];
  
  const headings = [];
  
  // 匹配 #、##、### 標題（最多 3 級）
  // 忽略在程式碼區塊內的標題
  const lines = markdown.split('\n');
  let inCodeBlock = false;
  
  for (const line of lines) {
    // 檢查是否進入/離開程式碼區塊
    if (line.trim().startsWith('```')) {
      inCodeBlock = !inCodeBlock;
      continue;
    }
    
    // 跳過程式碼區塊內的內容
    if (inCodeBlock) continue;
    
    // 匹配標題：# 標題、## 標題、### 標題
    const headingMatch = line.match(/^(#{1,3})\s+(.+)$/);
    
    if (headingMatch) {
      const [, hashes, text] = headingMatch;
      const level = hashes.length;
      const cleanText = text.trim();
      const anchorId = generateAnchorId(cleanText);
      
      headings.push({
        level,
        text: cleanText,
        anchorId
      });
    }
  }
  
  return headings;
};

/**
 * 生成 TOC HTML
 * 根據標題列表生成帶有層級縮排的目錄 HTML
 * 
 * @param {Array} headings - 標題列表
 * @returns {string} - TOC HTML
 */
const generateTocHtml = (headings) => {
  if (!headings || headings.length === 0) {
    return '<div class="summary-text">（文檔中沒有找到標題）</div>';
  }
  
  const items = headings.map(({ level, text, anchorId }) => {
    return `<li class="summary-item summary-item-h${level}">` +
      `<a href="#${escapeHtml(anchorId)}" class="summary-link" data-anchor="${escapeHtml(anchorId)}">` +
      `${escapeHtml(text)}` +
      `</a>` +
      `</li>`;
  });
  
  return `<ul class="summary-list">${items.join('\n')}</ul>`;
};

/**
 * 解析摘要區塊語法（自動生成 TOC）
 * 將 ::: summary [可選標題] 轉換為 HTML 目錄卡片
 * 
 * 重要：此語法不需要結束標記 :::
 * 會自動掃描整個文檔的標題來生成目錄
 * 
 * @param {string} markdown - Markdown 文本
 * @returns {string} - 處理後的 Markdown（摘要區塊已轉換為 HTML）
 */
export const parseSummaryBlocks = (markdown) => {
  if (!markdown) return '';
  
  // 正則表達式匹配 ::: summary [可選標題]
  // 不需要結束標記，只匹配這一行
  // 使用 i 標誌使其大小寫不敏感（支援 Summary、SUMMARY、summary）
  const summaryRegex = /^:::\s*summary(?:\s+(.+))?$/im;
  
  const match = markdown.match(summaryRegex);
  
  if (!match) {
    // 沒有 ::: summary 語法，直接返回原始內容
    return markdown;
  }
  
  // 提取可選的自訂標題，預設為「目錄」
  const customTitle = match[1] ? match[1].trim() : '目錄';
  
  // 移除 ::: summary 行後，提取標題
  // 注意：我們需要從整個文檔中提取標題（不只是 ::: summary 之後的內容）
  const headings = extractHeadings(markdown);
  
  // 生成 TOC HTML
  const tocHtml = generateTocHtml(headings);
  
  // 生成摘要區塊 HTML
  const summaryBlockHtml = `
<div class="markdown-summary-block" data-summary-title="${escapeHtml(customTitle)}">
  <div class="markdown-summary-header">
    <span class="summary-icon">📋</span>
    <span class="summary-title">${escapeHtml(customTitle)}</span>
  </div>
  <div class="markdown-summary-content">
    ${tocHtml}
  </div>
</div>
`;
  
  // 將 ::: summary 行替換為生成的 HTML
  return markdown.replace(summaryRegex, summaryBlockHtml);
};

/**
 * 為所有標題添加錨點 ID
 * 將 ## 標題 轉換為 <h2 id="錨點">標題</h2>
 * 
 * 注意：此函數應在 markdown-it 渲染後執行（處理已渲染的 HTML）
 * 或在渲染前處理 Markdown 文本
 * 
 * @param {string} html - 已渲染的 HTML 或 Markdown 文本
 * @param {boolean} isHtml - 是否為已渲染的 HTML
 * @returns {string} - 添加錨點後的內容
 */
export const addHeadingAnchors = (html, isHtml = true) => {
  if (!html) return '';
  
  if (isHtml) {
    // 處理已渲染的 HTML：為 <h1> ~ <h6> 添加 id 屬性
    return html.replace(
      /<h([1-6])>([^<]+)<\/h[1-6]>/g,
      (match, level, text) => {
        const anchorId = generateAnchorId(text);
        return `<h${level} id="${anchorId}" class="anchor-heading">${text}</h${level}>`;
      }
    );
  } else {
    // 處理 Markdown 文本：將 ## 標題 轉換為帶有特殊標記的格式
    // markdown-it 會處理這些標題，我們需要另一種方式
    // 這裡返回原始文本，讓 addHeadingAnchors 在渲染後處理
    return html;
  }
};

/**
 * 完整的摘要區塊處理流程
 * 整合解析摘要和添加錨點
 * 
 * @param {string} markdown - 原始 Markdown 文本
 * @returns {object} - { processedMarkdown, postProcessor }
 */
export const processSummaryAndAnchors = (markdown) => {
  // 步驟 1：解析摘要區塊（在 markdown-it 渲染前）
  const processedMarkdown = parseSummaryBlocks(markdown);
  
  // 步驟 2：返回後處理函數（在 markdown-it 渲染後執行）
  const postProcessor = (html) => {
    return addHeadingAnchors(html, true);
  };
  
  return {
    processedMarkdown,
    postProcessor
  };
};

/**
 * 摘要區塊的 CSS 樣式
 * 可以透過 <style> 標籤注入到頁面中
 */
export const summaryBlockStyles = `
/* ========================================
   摘要區塊樣式 (Summary Block Styles)
   自動生成 TOC 版本
   ======================================== */

/* 摘要區塊容器 */
.markdown-summary-block {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-left: 4px solid #0284c7;
  border-radius: 8px;
  margin: 16px 0;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(2, 132, 199, 0.1);
}

/* 摘要標題區域 */
.markdown-summary-header {
  background: rgba(2, 132, 199, 0.1);
  padding: 12px 16px;
  font-weight: 600;
  font-size: 16px;
  color: #0369a1;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid rgba(2, 132, 199, 0.15);
}

/* 摘要圖標 */
.markdown-summary-header .summary-icon {
  font-size: 18px;
}

/* 摘要標題文字 */
.markdown-summary-header .summary-title {
  flex: 1;
}

/* 摘要內容區域 */
.markdown-summary-content {
  padding: 12px 16px;
}

/* 摘要列表 */
.markdown-summary-content .summary-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

/* 摘要列表項目 - 基礎樣式 */
.markdown-summary-content .summary-item {
  margin: 6px 0;
  padding: 4px 0;
  position: relative;
  display: flex;
  align-items: center;
}

/* 列表項目前的圖標 - 基礎 */
.markdown-summary-content .summary-item::before {
  content: '';
  display: inline-block;
  margin-right: 8px;
  flex-shrink: 0;
}

/* ========================================
   層級縮排樣式 (Heading Level Indentation)
   ======================================== */

/* H1 標題 - 無縮排，藍色圓點 */
.markdown-summary-content .summary-item-h1 {
  padding-left: 0;
  font-weight: 600;
  font-size: 15px;
}

.markdown-summary-content .summary-item-h1::before {
  content: '●';
  color: #0284c7;
  font-size: 10px;
}

/* H2 標題 - 16px 縮排，青色方點 */
.markdown-summary-content .summary-item-h2 {
  padding-left: 16px;
  font-weight: 500;
  font-size: 14px;
}

.markdown-summary-content .summary-item-h2::before {
  content: '■';
  color: #0891b2;
  font-size: 8px;
}

/* H3 標題 - 32px 縮排，灰色破折號 */
.markdown-summary-content .summary-item-h3 {
  padding-left: 32px;
  font-weight: 400;
  font-size: 13px;
}

.markdown-summary-content .summary-item-h3::before {
  content: '–';
  color: #64748b;
  font-size: 12px;
}

/* ========================================
   連結樣式 (Link Styles)
   ======================================== */

/* 摘要連結樣式 */
.markdown-summary-content .summary-link {
  color: #0284c7;
  text-decoration: none;
  transition: all 0.2s ease;
  padding: 2px 4px;
  border-radius: 4px;
}

.markdown-summary-content .summary-link:hover {
  color: #0369a1;
  background-color: rgba(2, 132, 199, 0.1);
  text-decoration: underline;
}

/* H1 連結加粗 */
.markdown-summary-content .summary-item-h1 .summary-link {
  color: #0369a1;
  font-weight: 600;
}

/* H2 連結 */
.markdown-summary-content .summary-item-h2 .summary-link {
  color: #0891b2;
}

/* H3 連結稍淺 */
.markdown-summary-content .summary-item-h3 .summary-link {
  color: #0e7490;
}

/* 純文字摘要 */
.markdown-summary-content .summary-text {
  color: #6b7280;
  line-height: 1.6;
  font-style: italic;
}

/* ========================================
   錨點標題樣式 (Anchor Heading Styles)
   ======================================== */

/* 帶錨點的標題 */
.anchor-heading {
  scroll-margin-top: 20px; /* 跳轉時預留頂部空間 */
  position: relative;
}

/* 錨點高亮動畫 */
.anchor-heading.highlight-anchor {
  animation: anchorHighlight 2s ease-out;
}

@keyframes anchorHighlight {
  0% {
    background-color: #fef08a;
    border-radius: 4px;
  }
  100% {
    background-color: transparent;
  }
}

/* 滾動時的平滑過渡 */
html {
  scroll-behavior: smooth;
}

/* ========================================
   深色模式支援（可選）
   ======================================== */
   
@media (prefers-color-scheme: dark) {
  .markdown-summary-block {
    background: linear-gradient(135deg, #1e3a5f 0%, #0c4a6e 100%);
    border-color: #0369a1;
  }
  
  .markdown-summary-header {
    background: rgba(14, 165, 233, 0.2);
    color: #7dd3fc;
    border-bottom-color: rgba(14, 165, 233, 0.3);
  }
  
  .markdown-summary-content .summary-link {
    color: #7dd3fc;
  }
  
  .markdown-summary-content .summary-link:hover {
    color: #bae6fd;
    background-color: rgba(14, 165, 233, 0.2);
  }
  
  .markdown-summary-content .summary-text {
    color: #9ca3af;
  }
  
  .markdown-summary-content .summary-item-h1::before {
    color: #38bdf8;
  }
  
  .markdown-summary-content .summary-item-h2::before {
    color: #22d3ee;
  }
  
  .markdown-summary-content .summary-item-h3::before {
    color: #94a3b8;
  }
}
`;

/**
 * 處理摘要區塊中連結的點擊事件
 * 實現平滑滾動到目標錨點
 * 
 * @param {Event} event - 點擊事件
 * @param {HTMLElement} previewContainer - 預覽區容器元素
 */
export const handleSummaryLinkClick = (event, previewContainer) => {
  const target = event.target;
  
  // 檢查是否點擊了摘要連結
  if (!target.classList.contains('summary-link')) {
    return;
  }
  
  const href = target.getAttribute('href');
  if (!href || !href.startsWith('#')) {
    return;
  }
  
  event.preventDefault();
  
  const anchorId = href.slice(1); // 移除 # 符號
  const targetElement = previewContainer 
    ? previewContainer.querySelector(`#${CSS.escape(anchorId)}`)
    : document.getElementById(anchorId);
  
  if (targetElement) {
    // 平滑滾動到目標位置
    targetElement.scrollIntoView({
      behavior: 'smooth',
      block: 'start'
    });
    
    // 添加高亮效果
    targetElement.classList.add('highlight-anchor');
    
    // 2 秒後移除高亮
    setTimeout(() => {
      targetElement.classList.remove('highlight-anchor');
    }, 2000);
    
    console.log(`📍 跳轉到錨點: #${anchorId}`);
  } else {
    console.warn(`⚠️ 找不到錨點: #${anchorId}`);
  }
};

/**
 * 為預覽區綁定摘要連結點擊事件
 * 
 * @param {HTMLElement} previewContainer - 預覽區容器元素
 * @returns {Function} - 清理函數（移除事件監聽器）
 */
export const bindSummaryLinkHandler = (previewContainer) => {
  if (!previewContainer) {
    console.warn('⚠️ bindSummaryLinkHandler: previewContainer 為空');
    return () => {};
  }
  
  const handler = (event) => handleSummaryLinkClick(event, previewContainer);
  
  previewContainer.addEventListener('click', handler);
  console.log('✅ 摘要連結點擊事件已綁定');
  
  // 返回清理函數
  return () => {
    previewContainer.removeEventListener('click', handler);
    console.log('🧹 摘要連結點擊事件已解綁');
  };
};

export default {
  generateAnchorId,
  parseSummaryBlocks,
  addHeadingAnchors,
  processSummaryAndAnchors,
  summaryBlockStyles,
  handleSummaryLinkClick,
  bindSummaryLinkHandler
};
