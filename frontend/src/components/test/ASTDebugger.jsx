import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

/**
 * AST 調試組件
 * 顯示 react-markdown 解析的 AST 結構
 */
const ASTDebugger = () => {
  const simpleTable = `
| 欄位1 | 欄位2 | 欄位3 |
|-------|-------|-------|
| 資料1 | 資料2 | 資料3 |
| 資料4 | 資料5 | 資料6 |
`;

  // 自定義組件來檢查 AST 結構
  const debugComponents = {
    table: ({ node, children, ...props }) => {
      console.log('🔥 Table node:', node);
      console.log('🔥 Table children:', children);
      console.log('🔥 Table props:', props);
      return (
        <div style={{ border: '3px solid red', margin: '10px', padding: '10px' }}>
          <div style={{ color: 'red', fontSize: '12px', marginBottom: '5px' }}>TABLE WRAPPER</div>
          <table {...props} style={{ width: '100%', borderCollapse: 'collapse' }}>
            {children}
          </table>
        </div>
      );
    },
    thead: ({ node, children, ...props }) => {
      console.log('🔥 Thead node:', node);
      console.log('🔥 Thead children:', children);
      return (
        <thead {...props} style={{ backgroundColor: 'yellow' }}>
          {children}
        </thead>
      );
    },
    tbody: ({ node, children, ...props }) => {
      console.log('🔥 Tbody node:', node);
      console.log('🔥 Tbody children:', children);
      return (
        <tbody {...props} style={{ backgroundColor: 'lightblue' }}>
          {children}
        </tbody>
      );
    },
    tr: ({ node, children, ...props }) => {
      console.log('🔥 Tr node:', node);
      console.log('🔥 Tr children:', children);
      return (
        <tr {...props} style={{ border: '1px solid green' }}>
          {children}
        </tr>
      );
    },
    th: ({ node, children, ...props }) => {
      console.log('🔥 Th node:', node);
      console.log('🔥 Th children:', children);
      return (
        <th {...props} style={{ border: '1px solid blue', padding: '8px', backgroundColor: 'orange' }}>
          {children}
        </th>
      );
    },
    td: ({ node, children, ...props }) => {
      console.log('🔥 Td node:', node);
      console.log('🔥 Td children:', children);
      return (
        <td {...props} style={{ border: '1px solid purple', padding: '8px' }}>
          {children}
        </td>
      );
    }
  };

  return (
    <div style={{ padding: '20px' }}>
      <h2>AST 調試器</h2>
      
      <div style={{ marginBottom: '40px' }}>
        <h3>Markdown 原始碼：</h3>
        <pre style={{ backgroundColor: '#f5f5f5', padding: '10px', fontSize: '12px' }}>
          {simpleTable}
        </pre>
        
        <h3>AST 調試渲染（查看 Console）：</h3>
        <div style={{ border: '1px solid #ddd', padding: '16px' }}>
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={debugComponents}
          >
            {simpleTable}
          </ReactMarkdown>
        </div>
        
        <div style={{ marginTop: '20px', padding: '16px', backgroundColor: '#e6f7ff', border: '1px solid #91d5ff' }}>
          <h4>📋 調試說明：</h4>
          <ul>
            <li>打開瀏覽器開發者工具 (F12) 查看 Console 日誌</li>
            <li>觀察 node 和 children 的結構</li>
            <li>每個表格元素都有不同的顏色邊框：
              <ul>
                <li>紅色邊框：table</li>
                <li>綠色邊框：tr</li>
                <li>藍色邊框：th</li>
                <li>紫色邊框：td</li>
                <li>黃色背景：thead</li>
                <li>淺藍背景：tbody</li>
                <li>橘色背景：th</li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default ASTDebugger;