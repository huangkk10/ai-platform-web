import React from 'react';

/**
 * 極簡表格組件 - 純粹的 HTML 表格，不做任何額外處理
 */
export const MinimalCustomTable = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomTable:', { children, props });
  return (
    <table 
      {...props} 
      style={{ 
        width: '100%', 
        borderCollapse: 'collapse',
        border: '1px solid #333',
        margin: '10px 0'
      }}
    >
      {children}
    </table>
  );
};

export const MinimalCustomThead = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomThead:', { children, props });
  return (
    <thead {...props} style={{ backgroundColor: '#1890ff', color: 'white' }}>
      {children}
    </thead>
  );
};

export const MinimalCustomTbody = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomTbody:', { children, props });
  return <tbody {...props}>{children}</tbody>;
};

export const MinimalCustomTr = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomTr:', { children, props });
  return <tr {...props}>{children}</tr>;
};

export const MinimalCustomTh = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomTh:', { children, props });
  return (
    <th 
      {...props} 
      style={{ 
        padding: '8px', 
        border: '1px solid white',
        textAlign: 'center'
      }}
    >
      {children}
    </th>
  );
};

export const MinimalCustomTd = ({ children, ...props }) => {
  console.log('🔥 MinimalCustomTd:', { children, props });
  return (
    <td 
      {...props} 
      style={{ 
        padding: '8px', 
        border: '1px solid #ccc'
      }}
    >
      {children}
    </td>
  );
};

// 極簡組件映射 - 只處理表格
export const minimalMarkdownComponents = {
  table: MinimalCustomTable,
  thead: MinimalCustomThead,
  tbody: MinimalCustomTbody,
  tr: MinimalCustomTr,
  th: MinimalCustomTh,
  td: MinimalCustomTd
};