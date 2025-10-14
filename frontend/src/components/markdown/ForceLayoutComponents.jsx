import React from 'react';

/**
 * 強制表格佈局組件
 * 使用內聯樣式強制表格正確顯示
 */
export const ForceLayoutTable = ({ children, ...props }) => {
  return (
    <div 
      style={{ 
        width: '100%',
        overflowX: 'auto',
        margin: '12px 0',
        border: '1px solid #e8e8e8',
        borderRadius: '6px',
        backgroundColor: 'white'
      }}
    >
      <table 
        {...props}
        style={{
          width: '100%',
          borderCollapse: 'collapse',
          margin: 0,
          fontSize: '14px',
          backgroundColor: 'white',
          display: 'table',
          tableLayout: 'auto',
          borderSpacing: 0
        }}
      >
        {children}
      </table>
    </div>
  );
};

export const ForceLayoutThead = ({ children, ...props }) => {
  return (
    <thead 
      {...props}
      style={{
        backgroundColor: '#1890ff',
        color: 'white',
        display: 'table-header-group'
      }}
    >
      {children}
    </thead>
  );
};

export const ForceLayoutTbody = ({ children, ...props }) => {
  return (
    <tbody 
      {...props}
      style={{
        display: 'table-row-group'
      }}
    >
      {children}
    </tbody>
  );
};

export const ForceLayoutTr = ({ children, ...props }) => {
  return (
    <tr 
      {...props}
      style={{
        display: 'table-row'
      }}
    >
      {children}
    </tr>
  );
};

export const ForceLayoutTh = ({ children, ...props }) => {
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
        display: 'table-cell',
        minWidth: '100px',
        maxWidth: 'none',
        whiteSpace: 'nowrap',
        overflow: 'visible'
      }}
    >
      {children}
    </th>
  );
};

export const ForceLayoutTd = ({ children, ...props }) => {
  return (
    <td 
      {...props}
      style={{
        padding: '8px 12px',
        border: '1px solid #f0f0f0',
        fontSize: '13px',
        verticalAlign: 'top',
        lineHeight: '1.5',
        display: 'table-cell',
        minWidth: '100px',
        maxWidth: 'none',
        wordWrap: 'break-word',
        whiteSpace: 'normal'
      }}
    >
      {children}
    </td>
  );
};

// 強制佈局組件映射
export const forceLayoutComponents = {
  table: ForceLayoutTable,
  thead: ForceLayoutThead,
  tbody: ForceLayoutTbody,
  tr: ForceLayoutTr,
  th: ForceLayoutTh,
  td: ForceLayoutTd,
  
  // 其他基本組件
  p: ({ children, ...props }) => <p {...props}>{children}</p>,
  strong: ({ children, ...props }) => <strong {...props}>{children}</strong>,
  em: ({ children, ...props }) => <em {...props}>{children}</em>
};