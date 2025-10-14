import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { minimalMarkdownComponents } from '../markdown/MinimalMarkdownComponents';

/**
 * 最基本的表格測試 - 不使用自定義組件
 */
const BasicTableTest = () => {
  const simpleTable = `
| 欄位1 | 欄位2 | 欄位3 |
|-------|-------|-------|
| 資料1 | 資料2 | 資料3 |
| 資料4 | 資料5 | 資料6 |
`;

  return (
    <div style={{ padding: '20px' }}>
      <h2>基本表格測試</h2>
      
      <div style={{ marginBottom: '40px' }}>
        <h3>原始 Markdown 語法：</h3>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
          {simpleTable}
        </pre>
        
          <h3>使用 ReactMarkdown + remarkGfm（無自定義組件）：</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
              table: ({ children, ...props }) => {
                console.log('🔥 Basic table children:', children);
                return <table {...props} style={{ 
                  width: '100%', 
                  borderCollapse: 'collapse',
                  border: '2px solid red'
                }}>{children}</table>;
              }
            }}
          >
            {simpleTable}
          </ReactMarkdown>
        </div>
        
        <h3>使用 ReactMarkdown + remarkGfm（完全無組件）：</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px' }}>
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {simpleTable}
          </ReactMarkdown>
        </div>
        
        <h3>使用極簡組件（純 HTML 表格）：</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px' }}>
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={minimalMarkdownComponents}
          >
            {simpleTable}
          </ReactMarkdown>
        </div>        <h3>使用原生 HTML 表格（對照組）：</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', border: '1px solid #ccc' }}>
            <thead style={{ backgroundColor: '#f5f5f5' }}>
              <tr>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>欄位1</th>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>欄位2</th>
                <th style={{ border: '1px solid #ccc', padding: '8px' }}>欄位3</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料1</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料2</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料3</td>
              </tr>
              <tr>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料4</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料5</td>
                <td style={{ border: '1px solid #ccc', padding: '8px' }}>資料6</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default BasicTableTest;