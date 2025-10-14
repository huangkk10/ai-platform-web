import React from 'react';

/**
 * 修復版表格組件
 * 專門解決表格格式跑掉的問題
 */
export const FixedCustomTable = ({ children, ...props }) => {
  return (
    <div style={{ 
      width: '100%',
      overflowX: 'auto',
      margin: '12px 0',
      border: '1px solid #e8e8e8',
      borderRadius: '6px'
    }}>
      <table 
        {...props}
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          margin: 0,
          fontSize: '14px',
          backgroundColor: 'white'
        }}
      >
        {children}
      </table>
    </div>
  );
};

export const FixedCustomThead = ({ children, ...props }) => {
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

export const FixedCustomTbody = ({ children, ...props }) => {
  return <tbody {...props}>{children}</tbody>;
};

export const FixedCustomTr = ({ children, ...props }) => {
  return <tr {...props}>{children}</tr>;
};

export const FixedCustomTh = ({ children, ...props }) => {
  return (
    <th 
      {...props}
      style={{
        padding: '12px 8px',
        textAlign: 'center',
        fontWeight: 'bold',
        fontSize: '14px',
        color: 'white',
        border: '1px solid rgba(255,255,255,0.2)',
        minWidth: '80px' // 確保最小寬度
      }}
    >
      {children}
    </th>
  );
};

export const FixedCustomTd = ({ children, ...props }) => {
  return (
    <td 
      {...props}
      style={{
        padding: '8px 12px',
        border: '1px solid #f0f0f0',
        fontSize: '13px',
        verticalAlign: 'top',
        lineHeight: '1.5',
        minWidth: '80px' // 確保最小寬度
      }}
    >
      {children}
    </td>
  );
};

// 修復版組件映射
export const fixedMarkdownComponents = {
  table: FixedCustomTable,
  thead: FixedCustomThead,
  tbody: FixedCustomTbody,
  tr: FixedCustomTr,
  th: FixedCustomTh,
  td: FixedCustomTd,
  
  // 其他基本組件保持不變
  p: ({ children, ...props }) => <p {...props}>{children}</p>,
  strong: ({ children, ...props }) => <strong {...props}>{children}</strong>,
  em: ({ children, ...props }) => <em {...props}>{children}</em>,
  code: ({ children, ...props }) => (
    <code {...props} style={{ 
      backgroundColor: '#f5f5f5', 
      padding: '2px 4px', 
      borderRadius: '3px',
      fontSize: '0.9em' 
    }}>
      {children}
    </code>
  )
};