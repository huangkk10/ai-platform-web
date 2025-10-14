import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../markdown/MarkdownComponents';
import { minimalMarkdownComponents } from '../markdown/MinimalMarkdownComponents';
import { forceLayoutComponents } from '../markdown/ForceLayoutComponents';
import MessageFormatter from '../chat/MessageFormatter';

/**
 * 真實場景表格測試
 * 使用跟用戶遇到的完全相同的表格內容和圖片
 */
const RealScenarioTableTest = () => {
  // 完全按照用戶附件重構的實際表格內容
  const realTable = `
| 功能 | 主要說明 | 相關圖片 |
|------|----------|----------|
| UART 板數重置 (UART Board Count) | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常，以免與痛板卡的接觸器異常。 | ![board_count](board_count.png) |
| UART 日誌資料夾 (UART Log Folder) | 一鍵啟動 UART 日誌所在資料夾（預設 C:\\\\UART_Server ），方便檢視已記錄的日誌檔。 | ![uart_log_folder](uart_log_folder.png) |
| 全部掃描 (All Scan) | 檢查所有連接的電腦的 UART 裝置並正確識別裝置與優先權值，請務必與白名單。<br>1) UART TX 連至 SSD UART RX<br>2) force ROM ping 連至 SSD strap ping<br>3) J7 PC_PWR_SW 連接器異常目，並顯示可使用/不可用程序。 | |
`;

  // 帶有 ID 格式的圖片測試
  const tableWithImgIds = `
| 功能 | 說明 | 相關圖片 |
|------|------|----------|
| UART 板數重置 | 顯示目前板數統計的 UART 板數重置各區域狀況是否異常 | [IMG:14] |
| UART Log Folder | 一鍵啟動 UART 日誌所在資料夾（預設 C:\\\\UART_Server） | [IMG:15] |
| All Scan (全部掃描) | 檢查所有連接的電腦的 UART 板，檢查 UART TX、force ROM ping、PC_PWR_SW 連接器異常 | |
`;

  return (
    <div style={{ padding: '20px', maxWidth: '1400px', margin: '0 auto' }}>
      <h1>🔬 真實場景表格測試</h1>
      <p style={{ color: '#666', marginBottom: '30px' }}>
        使用與用戶遇到問題完全相同的表格內容和圖片進行測試
      </p>
      
      {/* 測試 1: 真實 Markdown 圖片語法 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📋 測試 1: 真實 Markdown 圖片語法</h2>
        
        <h3>Markdown 原始碼：</h3>
        <pre style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '15px', 
          fontSize: '11px', 
          overflow: 'auto',
          border: '1px solid #dee2e6',
          borderRadius: '4px'
        }}>
          {realTable}
        </pre>
        
        <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: '1fr 1fr', marginTop: '20px' }}>
          
          <div>
            <h4>🔴 使用目前的 markdownComponents（修復版）</h4>
            <div style={{ border: '3px solid red', padding: '16px', backgroundColor: '#fff', minHeight: '200px' }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {realTable}
              </ReactMarkdown>
            </div>
          </div>
          
          <div>
            <h4>🔵 無自定義組件（原生 react-markdown）</h4>
            <div style={{ border: '3px solid blue', padding: '16px', backgroundColor: '#fff', minHeight: '200px' }}>
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {realTable}
              </ReactMarkdown>
            </div>
          </div>
          
        </div>
      </div>

      {/* 測試 2: IMG:ID 格式 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📋 測試 2: IMG:ID 格式圖片</h2>
        
        <h3>Markdown 原始碼：</h3>
        <pre style={{ 
          backgroundColor: '#f8f9fa', 
          padding: '15px', 
          fontSize: '11px', 
          overflow: 'auto',
          border: '1px solid #dee2e6',
          borderRadius: '4px'
        }}>
          {tableWithImgIds}
        </pre>
        
        <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: '1fr 1fr', marginTop: '20px' }}>
          
          <div>
            <h4>🔴 使用目前的 markdownComponents</h4>
            <div style={{ border: '3px solid red', padding: '16px', backgroundColor: '#fff', minHeight: '200px' }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={markdownComponents}
              >
                {tableWithImgIds}
              </ReactMarkdown>
            </div>
          </div>
          
          <div>
            <h4>🟢 使用極簡組件</h4>
            <div style={{ border: '3px solid green', padding: '16px', backgroundColor: '#fff', minHeight: '200px' }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={minimalMarkdownComponents}
              >
                {tableWithImgIds}
              </ReactMarkdown>
            </div>
          </div>
          
        </div>
      </div>

      {/* 測試 3: 使用真實 MessageFormatter 與圖片數據 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📋 測試 3: 使用真實 MessageFormatter（包含圖片數據）</h2>
        
        <div style={{ marginBottom: '20px' }}>
          <h4>🟣 使用 MessageFormatter（實際系統使用的渲染方式）</h4>
          <div style={{ border: '3px solid purple', padding: '16px', backgroundColor: '#fff', minHeight: '200px' }}>
            <MessageFormatter 
              content={tableWithImgIds}
              metadata={{
                images: [
                  { id: 14, filename: 'board_count.png' },
                  { id: 15, filename: 'uart_log_folder.png' }
                ]
              }}
            />
          </div>
        </div>
        
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f0f8ff', 
          border: '1px solid #d6e4ff', 
          borderRadius: '6px',
          fontSize: '13px'
        }}>
          <strong>💡 說明：</strong> 這個測試使用實際的 MessageFormatter 組件，並提供了包含圖片 ID 14 和 15 的 metadata，
          模擬真實的 RVT Assistant 回應情況。
        </div>
      </div>

      {/* 測試 3: 帶實際圖片的 HTML 表格對照 */}
      <div style={{ marginBottom: '50px' }}>
        <h2>📋 測試 3: HTML 表格 + 實際圖片（對照組）</h2>
        
        <div style={{ border: '3px solid orange', padding: '16px', backgroundColor: '#fff' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse', 
            border: '1px solid #e8e8e8',
            fontSize: '14px'
          }}>
            <thead style={{ backgroundColor: '#1890ff', color: 'white' }}>
              <tr>
                <th style={{ border: '1px solid rgba(255,255,255,0.2)', padding: '12px 8px', textAlign: 'center' }}>功能</th>
                <th style={{ border: '1px solid rgba(255,255,255,0.2)', padding: '12px 8px', textAlign: 'center' }}>主要說明</th>
                <th style={{ border: '1px solid rgba(255,255,255,0.2)', padding: '12px 8px', textAlign: 'center' }}>相關圖片</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  UART 板數重置 (UART Board Count)
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  顯示目前板數統計的 UART 板數重置各區域狀況是否異常，以免與痛板卡的接觸器異常。
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top', textAlign: 'center' }}>
                  <div style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '4px', 
                    padding: '4px 8px',
                    backgroundColor: '#f0f8ff',
                    border: '1px solid #d6e4ff',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#1890ff'
                  }}>
                    📸 board_count.png
                  </div>
                </td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  UART 日誌資料夾 (UART Log Folder)
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  一鍵啟動 UART 日誌所在資料夾（預設 C:\UART_Server ），方便檢視已記錄的日誌檔。
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top', textAlign: 'center' }}>
                  <div style={{ 
                    display: 'inline-flex', 
                    alignItems: 'center', 
                    gap: '4px', 
                    padding: '4px 8px',
                    backgroundColor: '#f0f8ff',
                    border: '1px solid #d6e4ff',
                    borderRadius: '4px',
                    fontSize: '12px',
                    color: '#1890ff'
                  }}>
                    📸 uart_log_folder.png
                  </div>
                </td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  全部掃描 (All Scan)
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top' }}>
                  檢查所有連接的電腦的 UART 裝置並正確識別裝置與優先權值，請務必與白名單。<br/>
                  1) UART TX 連至 SSD UART RX<br/>
                  2) force ROM ping 連至 SSD strap ping<br/>
                  3) J7 PC_PWR_SW 連接器異常
                </td>
                <td style={{ border: '1px solid #f0f0f0', padding: '8px 12px', verticalAlign: 'top', textAlign: 'center' }}>
                  <span style={{ color: '#999', fontSize: '12px' }}>無圖片</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 觀察重點 */}
      <div style={{ 
        marginTop: '40px', 
        padding: '20px', 
        backgroundColor: '#fff7e6', 
        border: '1px solid #ffd666',
        borderRadius: '8px'
      }}>
        <h3>🔍 關鍵觀察重點：</h3>
        <ul style={{ lineHeight: '1.8' }}>
          <li><strong>🔴 紅色邊框</strong>：使用修復後的 markdownComponents - 這是實際系統使用的版本</li>
          <li><strong>🔵 藍色邊框</strong>：原生 react-markdown 渲染 - 看是否是組件問題</li>
          <li><strong>🟢 綠色邊框</strong>：極簡組件版本 - 對照測試</li>
          <li><strong>🟠 橘色邊框</strong>：純 HTML 表格 - 理想狀態參考</li>
          <li><strong>檢查要點</strong>：
            <ul>
              <li>表格是否正確分為三欄？</li>
              <li>內容是否在正確的欄位中？</li>
              <li>圖片佔位符是否影響表格結構？</li>
              <li>長文字是否導致表格變形？</li>
            </ul>
          </li>
        </ul>
      </div>
    </div>
  );
};

export default RealScenarioTableTest;