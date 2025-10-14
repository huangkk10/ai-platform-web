import React from 'react';

/**
 * 簡化的表格組件用於調試
 */
export const SimpleCustomTable = ({ children, ...props }) => {
  console.log('🔥 SimpleCustomTable rendered with children:', children);
  
  return (
    <table 
      {...props}
      style={{
        width: '100%',
        borderCollapse: 'collapse',
        border: '2px solid red', // 明顯的調試邊框
        margin: '10px 0'
      }}
    >
      {children}
    </table>
  );
};

export const SimpleCustomThead = ({ children, ...props }) => {
  console.log('🔥 SimpleCustomThead rendered with children:', children);
  
  return (
    <thead 
      {...props}
      style={{
        backgroundColor: '#1890ff',
        color: 'white'
      }}
    >
      {children}
    </thead>
  );
};

export const SimpleCustomTh = ({ children, ...props }) => {
  console.log('🔥 SimpleCustomTh rendered with children:', children);
  
  return (
    <th 
      {...props}
      style={{
        padding: '10px',
        border: '1px solid white',
        textAlign: 'center'
      }}
    >
      {children}
    </th>
  );
};

export const SimpleCustomTd = ({ children, ...props }) => {
  console.log('🔥 SimpleCustomTd rendered with children:', children);
  
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

// 簡化的組件映射
export const simpleMarkdownComponents = {
  table: SimpleCustomTable,
  thead: SimpleCustomThead,
  tbody: ({ children, ...props }) => {
    console.log('🔥 SimpleCustomTbody rendered with children:', children);
    return <tbody {...props}>{children}</tbody>;
  },
  tr: ({ children, ...props }) => {
    console.log('🔥 SimpleCustomTr rendered with children:', children);
    return <tr {...props}>{children}</tr>;
  },
  th: SimpleCustomTh,
  td: SimpleCustomTd,
  
  // 其他基本元素
  p: ({ children, ...props }) => <p {...props}>{children}</p>,
  strong: ({ children, ...props }) => <strong {...props}>{children}</strong>,
  em: ({ children, ...props }) => <em {...props}>{children}</em>
};