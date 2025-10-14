import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../markdown/MarkdownComponents';

/**
 * 簡化表格問題診斷
 * 專門測試表格跑掉的根本原因
 */
const SimpleTableDiagnostic = () => {
  
  // 問題表格
  const problemTable = `| 功能 | 主要說明 | 相關圖片 |
|------|----------|----------|
| UART 板數重置 | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常，以免與痛板卡的接觸器異常。 | [IMG:14] |
| UART Log Folder | 一鍵啟動 UART 日誌所在資料夾（預設 C:\\\\UART_Server ），方便檢視已記錄的日誌檔。 | [IMG:15] |
| All Scan (全部掃描) | 檢查所有連接的電腦的 UART 裝置並正確識別裝置與優先權值，請務必與白名單。 | |`;

  // 簡單表格
  const simpleTable = `| A | B | C |
|---|---|---|
| 1 | 2 | 3 |
| 4 | 5 | 6 |`;

  // 創建一個臨時的調試組件
  const debugComponents = {
    ...markdownComponents,
    table: ({ children, ...props }) => {
      console.log('🔥 Table Debug - children:', children);
      console.log('🔥 Table Debug - props:', props);
      return (
        <div style={{ 
          border: '3px solid red',
          margin: '10px 0',
          padding: '5px',
          backgroundColor: '#fff'
        }}>
          <div style={{ fontSize: '12px', color: 'red', marginBottom: '5px' }}>
            DEBUG: TABLE WRAPPER
          </div>
          <table 
            {...props}
            style={{
              width: '100%',
              borderCollapse: 'collapse',
              border: '1px solid #333'
            }}
          >
            {children}
          </table>
        </div>
      );
    },
    thead: ({ children, ...props }) => {
      console.log('🔥 Thead Debug - children:', children);
      return (
        <thead {...props} style={{ backgroundColor: 'yellow' }}>
          {children}
        </thead>
      );
    },
    tr: ({ children, ...props }) => {
      console.log('🔥 Tr Debug - children:', children);
      return (
        <tr {...props} style={{ border: '2px solid green' }}>
          {children}
        </tr>
      );
    },
    th: ({ children, ...props }) => {
      console.log('🔥 Th Debug - children:', children);
      return (
        <th {...props} style={{ 
          border: '1px solid blue', 
          padding: '8px',
          backgroundColor: 'lightblue'
        }}>
          {children}
        </th>
      );
    },
    td: ({ children, ...props }) => {
      console.log('🔥 Td Debug - children:', children);
      return (
        <td {...props} style={{ 
          border: '1px solid purple', 
          padding: '8px'
        }}>
          {children}
        </td>
      );
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>🔬 簡化表格問題診斷</h1>
      
      <div style={{ marginBottom: '40px' }}>
        <h2>📋 測試 1: 簡單表格</h2>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
          {simpleTable}
        </pre>
        
        <h3>調試版組件（查看 Console）：</h3>
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={debugComponents}
        >
          {simpleTable}
        </ReactMarkdown>
        
        <h3>原生 ReactMarkdown（無組件）：</h3>
        <div style={{ border: '2px solid blue', padding: '10px' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {simpleTable}
          </ReactMarkdown>
        </div>
      </div>

      <div style={{ marginBottom: '40px' }}>
        <h2>📋 測試 2: 問題表格</h2>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '11px' }}>
          {problemTable}
        </pre>
        
        <h3>調試版組件（查看 Console）：</h3>
        <ReactMarkdown 
          remarkPlugins={[remarkGfm]}
          components={debugComponents}
        >
          {problemTable}
        </ReactMarkdown>
        
        <h3>原生 ReactMarkdown（無組件）：</h3>
        <div style={{ border: '2px solid blue', padding: '10px' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {problemTable}
          </ReactMarkdown>
        </div>
      </div>

      <div style={{ 
        padding: '20px', 
        backgroundColor: '#fff7e6', 
        border: '1px solid #ffd666',
        borderRadius: '8px'
      }}>
        <h3>🔍 調試說明：</h3>
        <ul>
          <li><strong>調試版組件</strong>：有紅色邊框和顏色標示，Console 會顯示詳細的組件調用信息</li>
          <li><strong>原生 ReactMarkdown</strong>：藍色邊框，完全不使用自定義組件</li>
          <li><strong>關鍵檢查</strong>：
            <ul>
              <li>表格是否正確解析為 table &gt; thead/tbody &gt; tr &gt; th/td 結構？</li>
              <li>每個 tr 是否包含正確數量的 th/td？</li>
              <li>長文字內容是否破壞表格結構？</li>
              <li>[IMG:14] 這類內容是否影響表格解析？</li>
            </ul>
          </li>
          <li><strong>請打開 F12 開發者工具查看 Console 輸出！</strong></li>
        </ul>
      </div>
    </div>
  );
};

export default SimpleTableDiagnostic;