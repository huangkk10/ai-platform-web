import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { forceLayoutComponents } from '../markdown/ForceLayoutComponents';

/**
 * 原生 Markdown 表格測試
 * 不使用任何自定義組件，測試 react-markdown 原始行為
 */
const NativeMarkdownTest = () => {
  // 從附件重構的實際問題表格
  const problemTable = `
| 功能 | 說明 | 相關圖片 |
|------|------|----------|
| UART 板數重置 (UART Board Count) | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常，以免與痛板卡的接觸器異常。 | board_count.png |
| UART 日誌資料夾 (UART Log Folder) | 點擊後會即時啟動 C:\\UART_Server （設置所放設的目標檔案），方便檢視檢測已記錄的 UART 日誌檔。 | uart_log_folder.png |
| 全部掃描 (All Scan) | 保護項目所有連接的電腦的 UART 板，檢查 UART TX、force ROM ping、PC_PWR_SW 連接器最高目，並顯示可使用/不可用程序。 |  |
`;

  // 簡單測試表格
  const simpleTable = `
| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 | 6 |
`;

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>🔧 原生 Markdown 表格測試</h1>
      
      {/* 簡單表格測試 */}
      <div style={{ marginBottom: '40px' }}>
        <h2>1. 簡單表格測試</h2>
        <h3>Markdown 代碼：</h3>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
          {simpleTable}
        </pre>
        
        <h3>ReactMarkdown 渲染（無組件）：</h3>
        <div style={{ border: '2px solid blue', padding: '16px', backgroundColor: '#fff' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {simpleTable}
          </ReactMarkdown>
        </div>
        
        <h3>原生 HTML 表格（對照組）：</h3>
        <div style={{ border: '2px solid green', padding: '16px', backgroundColor: '#fff' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ccc' }}>
            <thead>
              <tr>
                <th style={{ border: '1px solid #ccc', padding: '8px', backgroundColor: '#f5f5f5' }}>A</th>
                <th style={{ border: '1px solid #ccc', padding: '8px', backgroundColor: '#f5f5f5' }}>B</th>
                <th style={{ border: '1px solid #ccc', padding: '8px', backgroundColor: '#f5f5f5' }}>C</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>1</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>2</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>3</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>4</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>5</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>6</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 問題表格測試 */}
      <div style={{ marginBottom: '40px' }}>
        <h2>2. 問題表格測試（從附件重構）</h2>
        <h3>Markdown 代碼：</h3>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '11px', overflow: 'auto' }}>
          {problemTable}
        </pre>
        
        <h3>ReactMarkdown 渲染（無組件）：</h3>
        <div style={{ border: '2px solid red', padding: '16px', backgroundColor: '#fff' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {problemTable}
          </ReactMarkdown>
        </div>
        
        <h3>ReactMarkdown 渲染（強制佈局組件）：</h3>
        <div style={{ border: '2px solid purple', padding: '16px', backgroundColor: '#fff' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={forceLayoutComponents}
          >
            {problemTable}
          </ReactMarkdown>
        </div>
      </div>

      {/* 檢查元素結構 */}
      <div style={{ marginTop: '30px', padding: '16px', backgroundColor: '#fff7e6', border: '1px solid #ffd666' }}>
        <h3>🔍 調試說明：</h3>
        <ul>
          <li>藍色邊框：簡單表格的 ReactMarkdown 渲染</li>
          <li>綠色邊框：原生 HTML 表格作為對照組</li>
          <li>紅色邊框：問題表格的 ReactMarkdown 渲染（無組件）</li>
          <li><strong>紫色邊框</strong>：問題表格的強制佈局組件渲染 ⭐</li>
          <li>請右鍵檢查元素，觀察實際的 HTML 結構</li>
          <li>檢查是否有 CSS 樣式影響表格顯示</li>
          <li>如果紫色邊框顯示正確，我們將應用這個修復</li>
        </ul>
      </div>
    </div>
  );
};

export default NativeMarkdownTest;