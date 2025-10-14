import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../markdown/MarkdownComponents';
import { simpleMarkdownComponents } from '../markdown/SimpleMarkdownComponents';

/**
 * Markdown 表格調試組件
 * 用於測試和調試表格渲染問題
 */
const MarkdownTableDebugger = () => {
  // 簡單的表格測試
  const simpleTable = `
| 欄位1 | 欄位2 | 欄位3 |
|-------|-------|-------|
| 資料1 | 資料2 | 資料3 |
| 資料4 | 資料5 | 資料6 |
`;

  // 帶圖片的表格測試
  const tableWithImages = `
| 名稱 | 描述 | 圖片 |
|------|------|------|
| 項目A | 這是項目A的描述 | ![圖片A](image1.jpg) |
| 項目B | 這是項目B的描述 | ![圖片B](image2.jpg) |
`;

  // 複雜表格測試
  const complexTable = `
| Protocol | Status | Description | Image | Action |
|----------|--------|-------------|-------|--------|
| ULINK | ✅ Active | USB-Link communication protocol | ![ULINK](ulink.jpg) | Configure |
| JTAG | ⚠️ Warning | JTAG debugging interface | ![JTAG](jtag.jpg) | Check |
| SWD | ❌ Error | Serial Wire Debug protocol | ![SWD](swd.jpg) | Fix |
`;

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h2>Markdown 表格調試器</h2>
      
      <div style={{ marginBottom: '40px' }}>
        <h3>1. 簡單表格測試</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px', backgroundColor: '#fafafa' }}>
          <h4>Markdown 原始碼：</h4>
          <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px' }}>
            {simpleTable}
          </pre>
          <h4>渲染結果（簡化組件）：</h4>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={simpleMarkdownComponents}
          >
            {simpleTable}
          </ReactMarkdown>
          
          <h4>渲染結果（原組件）：</h4>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {simpleTable}
          </ReactMarkdown>
        </div>
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h3>2. 帶圖片的表格測試</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px', backgroundColor: '#fafafa' }}>
          <h4>Markdown 原始碼：</h4>
          <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px' }}>
            {tableWithImages}
          </pre>
          <h4>渲染結果：</h4>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {tableWithImages}
          </ReactMarkdown>
        </div>
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h3>3. 複雜表格測試（Protocol 示例）</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px', backgroundColor: '#fafafa' }}>
          <h4>Markdown 原始碼：</h4>
          <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '8px' }}>
            {complexTable}
          </pre>
          <h4>渲染結果：</h4>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {complexTable}
          </ReactMarkdown>
        </div>
      </div>

      <div style={{ marginTop: '40px', padding: '16px', backgroundColor: '#e6f7ff', border: '1px solid #91d5ff' }}>
        <h4>📋 調試說明：</h4>
        <ul>
          <li>打開瀏覽器開發者工具 (F12) 查看 Console 日誌</li>
          <li>觀察表格元素的渲染順序和內容</li>
          <li>檢查是否有錯誤訊息或警告</li>
          <li>確認表格結構是否正確解析</li>
        </ul>
      </div>
    </div>
  );
};

export default MarkdownTableDebugger;