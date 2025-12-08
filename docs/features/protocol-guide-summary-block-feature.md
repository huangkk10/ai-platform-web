# Protocol Guide 摘要區塊功能規劃

## 📋 文件資訊

| 項目 | 內容 |
|------|------|
| **功能名稱** | Protocol Guide 摘要區塊（Summary Block） |
| **建立日期** | 2025-12-08 |
| **完成日期** | 2025-12-08 |
| **狀態** | ✅ 已完成 |
| **相關頁面** | `/knowledge/protocol-guide/markdown-edit/:id` |

---

## 🎯 功能概述

### 目標
在 Protocol Guide 的 Markdown 編輯器中新增**摘要區塊語法**功能，讓用戶可以：
1. 在左側編輯區使用特殊語法定義摘要區塊
2. 在右側預覽區即時看到渲染後的摘要卡片
3. **點擊摘要項目可跳轉到對應的文檔位置**

### 使用場景
- 在長篇 Protocol 文檔開頭建立導覽摘要
- 快速概覽文檔的主要章節和步驟
- 提供可點擊的錨點導航功能

---

## 📝 語法規格

### 採用方案：`:::` 容器語法（方案 A）

#### 基本語法
```markdown
::: summary 摘要標題
- [項目1 文字](#錨點1)
- [項目2 文字](#錨點2)
- [項目3 文字](#錨點3)
:::
```

#### 完整範例
```markdown
::: summary AVL SOP 快速導覽
- [Chromebook NB 設備清單](#chromebook-nb)
- [Chrome image 燒錄步驟](#chrome-image-燒錄)
- [官網下載 Image OS](#chorme-官網下載對應-image-os)
- [透過搜尋設定參數](#step3-透過搜尋設定參數)
:::

## Chromebook NB

NB-SSD-1685 (HP Elite c645 14 G2 )
NB-SSD-1910 (ACER Chromebook Spin 714 cp714)

## Chrome image 燒錄

### Chorme 官網下載對應 Image OS

Step.1 官網連結如下
https://chromeos.google.com/partner/dlm/buildImages/list

...
```

### 語法規則

| 規則 | 說明 |
|------|------|
| 開始標記 | `::: summary 標題文字` |
| 結束標記 | `:::` |
| 內容格式 | 支援 Markdown 列表和連結語法 |
| 錨點連結 | 使用 `[文字](#錨點)` 格式 |
| 錨點生成 | 標題自動生成錨點（中文支援） |

### 錨點命名規則

標題會自動轉換為錨點 ID：

| 標題 | 生成的錨點 ID |
|------|--------------|
| `## Chromebook NB` | `#chromebook-nb` |
| `## Chrome image 燒錄` | `#chrome-image-燒錄` |
| `### Step.1 官網連結` | `#step1-官網連結` |

轉換規則：
1. 轉為小寫
2. 空格替換為 `-`
3. 移除特殊字元（保留中文）
4. 移除開頭的 `#` 符號

---

## 🎨 UI 設計

### 預覽區渲染樣式

```
┌─────────────────────────────────────────────┐
│ 📋 AVL SOP 快速導覽                          │
├─────────────────────────────────────────────┤
│                                             │
│  • Chromebook NB 設備清單      ← 可點擊     │
│  • Chrome image 燒錄步驟       ← 可點擊     │
│  • 官網下載 Image OS           ← 可點擊     │
│  • 透過搜尋設定參數            ← 可點擊     │
│                                             │
└─────────────────────────────────────────────┘
```

### 樣式規格

```css
.markdown-summary-block {
  /* 容器樣式 */
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border: 1px solid #bae6fd;
  border-left: 4px solid #0284c7;
  border-radius: 8px;
  margin: 16px 0;
  overflow: hidden;
}

.markdown-summary-header {
  /* 標題樣式 */
  background: rgba(2, 132, 199, 0.1);
  padding: 12px 16px;
  font-weight: 600;
  font-size: 16px;
  color: #0369a1;
  display: flex;
  align-items: center;
  gap: 8px;
}

.markdown-summary-header::before {
  content: '📋';
}

.markdown-summary-content {
  /* 內容樣式 */
  padding: 12px 16px;
}

.markdown-summary-content a {
  /* 連結樣式 */
  color: #0284c7;
  text-decoration: none;
  transition: color 0.2s;
}

.markdown-summary-content a:hover {
  color: #0369a1;
  text-decoration: underline;
}

.markdown-summary-content li {
  /* 列表項目樣式 */
  margin: 8px 0;
  cursor: pointer;
}
```

### 點擊跳轉行為

1. 用戶點擊摘要中的連結項目
2. 右側預覽區平滑滾動到對應的錨點位置
3. 目標區塊短暫高亮顯示（可選）

---

## 🔧 技術實作規劃

### 需要修改的檔案

| 檔案路徑 | 修改內容 | 狀態 |
|---------|---------|------|
| `frontend/src/utils/markdownSummaryParser.js` | 🆕 新增 - 摘要語法解析器 | ✅ 完成 |
| `frontend/src/components/editor/MarkdownEditorLayout.jsx` | 整合摘要解析、CSS 樣式、錨點跳轉 | ✅ 完成 |

### 實作步驟

#### Phase 1：摘要區塊解析與渲染

**Step 1.1：建立摘要語法解析器**

```javascript
// frontend/src/utils/markdownParser.js

/**
 * 解析摘要區塊語法
 * 將 ::: summary 標題 ... ::: 轉換為 HTML
 */
export const parseSummaryBlocks = (markdown) => {
  // 正則表達式匹配 ::: summary ... :::
  const summaryRegex = /^:::\s*summary\s+(.+?)\n([\s\S]*?)^:::/gm;
  
  return markdown.replace(summaryRegex, (match, title, content) => {
    // 解析內容中的 Markdown 列表和連結
    const parsedContent = parseMarkdownList(content);
    
    return `
      <div class="markdown-summary-block">
        <div class="markdown-summary-header">${escapeHtml(title)}</div>
        <div class="markdown-summary-content">${parsedContent}</div>
      </div>
    `;
  });
};

/**
 * 解析 Markdown 列表語法
 */
const parseMarkdownList = (content) => {
  // 處理列表項目和連結
  // - [文字](#錨點) => <li><a href="#錨點">文字</a></li>
};
```

**Step 1.2：整合到 MarkdownEditorPage**

```javascript
// frontend/src/pages/MarkdownEditorPage.js

import { parseSummaryBlocks } from '../utils/markdownParser';

// 在渲染預覽時先處理摘要區塊
const renderPreview = (content) => {
  // 1. 先解析摘要區塊
  let processedContent = parseSummaryBlocks(content);
  
  // 2. 再用標準 Markdown 渲染器處理其他內容
  return markdownRenderer.render(processedContent);
};
```

**Step 1.3：添加 CSS 樣式**

```css
/* frontend/src/pages/MarkdownEditorPage.css */

/* 摘要區塊樣式 - 如上方樣式規格所示 */
```

#### Phase 2：錨點跳轉功能

**Step 2.1：自動生成標題錨點**

```javascript
/**
 * 為所有標題生成錨點 ID
 */
export const generateHeadingAnchors = (markdown) => {
  // 將 ## 標題 轉換為 <h2 id="錨點">標題</h2>
  const headingRegex = /^(#{1,6})\s+(.+)$/gm;
  
  return markdown.replace(headingRegex, (match, hashes, title) => {
    const level = hashes.length;
    const anchorId = generateAnchorId(title);
    return `<h${level} id="${anchorId}">${title}</h${level}>`;
  });
};

/**
 * 生成錨點 ID
 * "Chrome image 燒錄" => "chrome-image-燒錄"
 */
const generateAnchorId = (title) => {
  return title
    .toLowerCase()
    .trim()
    .replace(/\s+/g, '-')           // 空格轉為 -
    .replace(/[^\w\u4e00-\u9fa5-]/g, ''); // 保留英數字、中文、-
};
```

**Step 2.2：實作平滑滾動**

```javascript
/**
 * 處理摘要連結點擊事件
 */
const handleSummaryLinkClick = (e) => {
  const href = e.target.getAttribute('href');
  if (href && href.startsWith('#')) {
    e.preventDefault();
    const targetId = href.slice(1);
    const targetElement = document.getElementById(targetId);
    
    if (targetElement) {
      // 平滑滾動到目標位置
      targetElement.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
      
      // 可選：短暫高亮目標區塊
      targetElement.classList.add('highlight-anchor');
      setTimeout(() => {
        targetElement.classList.remove('highlight-anchor');
      }, 2000);
    }
  }
};
```

---

## 📊 工作量預估

| 階段 | 工作項目 | 預估時間 |
|------|---------|---------|
| Phase 1 | 摘要區塊解析與渲染 | 2-3 小時 |
| Phase 2 | 錨點跳轉功能 | 1-2 小時 |
| 測試 | 功能測試與調整 | 1 小時 |
| **總計** | | **4-6 小時** |

---

## ✅ 驗收標準

### 功能驗收

- [ ] 在編輯區輸入 `::: summary 標題 ... :::` 語法
- [ ] 右側預覽區正確顯示摘要卡片
- [ ] 摘要卡片樣式符合設計規格
- [ ] 點擊摘要中的連結可跳轉到對應位置
- [ ] 跳轉動畫平滑流暢
- [ ] 支援中文標題和錨點

### 相容性驗收

- [ ] 不影響現有 Markdown 語法解析
- [ ] 不影響圖片上傳和顯示功能
- [ ] 在不同瀏覽器中表現一致（Chrome、Firefox、Edge）

---

## 🔄 後續擴展（未來考慮）

| 功能 | 說明 | 優先級 |
|------|------|--------|
| 折疊/展開 | 摘要區塊可折疊 | 低 |
| 多種區塊類型 | 支援 warning、info、tip 等 | 中 |
| 自動生成摘要 | 根據標題自動生成摘要區塊 | 中 |
| 編輯器工具欄按鈕 | 一鍵插入摘要語法模板 | 中 |

---

## 📚 參考資料

- [Markdown Container Syntax](https://github.com/markdown-it/markdown-it-container)
- [GitHub Flavored Markdown](https://github.github.com/gfm/)
- 現有實作參考：`frontend/src/pages/MarkdownEditorPage.js`

---

**📅 更新日期**: 2025-12-08  
**✍️ 作者**: AI Platform Team  
**🎯 狀態**: ✅ 已完成

## 📦 實際修改檔案清單

### 1. 新增檔案
- `frontend/src/utils/markdownSummaryParser.js` - 摘要區塊解析器

### 2. 修改檔案
- `frontend/src/components/editor/MarkdownEditorLayout.jsx`
  - 導入 `markdownSummaryParser` 工具
  - 修改 `renderMarkdownWithImages` 函數，整合摘要解析和錨點生成
  - 添加摘要區塊 CSS 樣式到 `customToolbarStyles`
  - 添加摘要連結點擊事件處理 `useEffect`
