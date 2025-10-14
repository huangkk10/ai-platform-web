import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { minimalMarkdownComponents } from '../markdown/MinimalMarkdownComponents';
import { markdownComponents } from '../markdown/MarkdownComponents';
import { fixedMarkdownComponents } from '../markdown/FixedMarkdownComponents';

/**
 * RVT 實際表格測試
 * 測試真實 RVT Assistant 回應中的表格格式
 */
const RVTTableTest = () => {
  // 根據附件重構的實際表格內容
  const rvtTable = `
| 功能 | 主要說明 | 相關圖片 |
|------|----------|----------|
| UART 板數重置 | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常，方便使用者瞭解保護措施狀況。 | board_count.png |
| UART Log Folder | 一鍵啟動 UART 日誌所在資料夾（預設 C:\\UART_Server ），方便檢視已記錄的日誌檔。 | uart_log_folder.png |
| All Scan (全部掃描) | 檢查所有連接的電腦的 UART 裝置並正確識別裝置與優先權值，請務必與白名單。\\<br>1) UART TX 連至 SSD UART RX\\<br>2) force ROM ping 連至 SSD strap ping\\<br>3) J7 PC_PWR_SW | |
`;

  // 更複雜的表格測試
  const complexTable = `
| Protocol | Status | Description | Configuration | Notes |
|----------|--------|-------------|---------------|-------|
| ULINK | ✅ Active | USB-Link communication protocol for debugging | Default settings work well | Recommended for development |
| JTAG | ⚠️ Warning | Joint Test Action Group debugging interface | Requires specific pin configuration | Check pin connections |
| SWD | ❌ Error | Serial Wire Debug protocol implementation | Need to configure clock speed | Fix connection issues first |
| UART | 🔧 Setup | Universal Asynchronous Receiver/Transmitter | Baud rate: 115200, 8N1 | Standard configuration |
`;

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h2>🔧 RVT 實際表格測試</h2>
      
      <div style={{ marginBottom: '40px' }}>
        <h3>1. 原始 RVT 表格（從附件重構）</h3>
        
        <h4>Markdown 原始碼：</h4>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '11px', overflow: 'auto' }}>
          {rvtTable}
        </pre>
        
        <h4>無自定義組件渲染：</h4>
        <div style={{ border: '2px solid blue', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {rvtTable}
          </ReactMarkdown>
        </div>
        
        <h4>極簡組件渲染：</h4>
        <div style={{ border: '2px solid green', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={minimalMarkdownComponents}
          >
            {rvtTable}
          </ReactMarkdown>
        </div>
        
        <h4>完整自定義組件渲染：</h4>
        <div style={{ border: '2px solid red', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={markdownComponents}
          >
            {rvtTable}
          </ReactMarkdown>
        </div>
        
        <h4>修復版組件渲染（推薦）：</h4>
        <div style={{ border: '2px solid orange', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={fixedMarkdownComponents}
          >
            {rvtTable}
          </ReactMarkdown>
        </div>
      </div>
      
      <div style={{ marginBottom: '40px' }}>
        <h3>2. 複雜表格測試</h3>
        
        <h4>無自定義組件：</h4>
        <div style={{ border: '2px solid blue', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {complexTable}
          </ReactMarkdown>
        </div>
        
        <h4>極簡組件：</h4>
        <div style={{ border: '2px solid green', padding: '16px', margin: '10px 0' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={minimalMarkdownComponents}
          >
            {complexTable}
          </ReactMarkdown>
        </div>
      </div>
      
      <div style={{ marginTop: '30px', padding: '16px', backgroundColor: '#fff7e6', border: '1px solid #ffd666' }}>
        <h4>🔍 對比觀察重點：</h4>
        <ul>
          <li><strong>藍色邊框</strong>：react-markdown 原生渲染，應該是最標準的</li>
          <li><strong>綠色邊框</strong>：極簡自定義組件，只做最基本的 HTML 輸出</li>
          <li><strong>紅色邊框</strong>：完整自定義組件，包含所有業務邏輯</li>
          <li><strong>橘色邊框</strong>：修復版組件，專門解決表格格式問題 ⭐</li>
          <li>檢查哪個版本的表格列數和格式是正確的</li>
          <li>查看 Console 輸出了解組件調用情況</li>
          <li>如果修復版正確，我們將套用到實際系統中</li>
        </ul>
      </div>
    </div>
  );
};

export default RVTTableTest;