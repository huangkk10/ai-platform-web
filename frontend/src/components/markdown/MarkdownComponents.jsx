import React, { useState, useEffect } from 'react';
import { Image, Spin, message, Space, Tag, Typography } from 'antd';
import { 
  PictureOutlined, 
  ExclamationCircleOutlined,
  StarFilled,
  InfoCircleOutlined
} from '@ant-design/icons';
// 移除可能導致錯誤的圖片載入邏輯
// import MessageImages from '../chat/MessageImages';
// import { loadImagesData } from '../../utils/imageProcessor';

const { Text } = Typography;

/**
 * 自定義表格組件 - 強制佈局修復版本
 * 使用內聯樣式強制表格正確顯示，解決 CSS 衝突問題
 */
export const CustomTable = ({ children, ...props }) => {
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
        className="markdown-table"
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

/**
 * 自定義表格標題組件 - 強制佈局版本
 */
export const CustomTableHead = ({ children, ...props }) => (
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

/**
 * 自定義表格標題儲存格組件 - 強制佈局版本
 */
export const CustomTh = ({ children, ...props }) => {
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
        overflow: 'visible',
        ...props.style
      }}
    >
      {children}
    </th>
  );
};

/**
 * 自定義表格資料儲存格組件 - 強制佈局版本
 */
export const CustomTd = ({ children, ...props }) => {
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
        whiteSpace: 'normal',
        ...props.style
      }}
    >
      {children}
    </td>
  );
};

/**
 * 自定義圖片組件 - 在表格中顯示佔位符，避免載入錯誤
 * 圖片會由 MessageFormatter 統一處理
 */
export const CustomImage = ({ src, alt, title, ...props }) => {
  // 檢查是否是圖片引用格式或在表格內
  if (src && (src.includes('[IMG:') || alt?.includes('[IMG:') || alt?.includes('圖片'))) {
    return (
      <span 
        className="image-placeholder"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '4px',
          padding: '2px 6px',
          backgroundColor: '#f0f8ff',
          border: '1px solid #d6e4ff',
          borderRadius: '4px',
          fontSize: '11px',
          color: '#1890ff',
          margin: '0 4px'
        }}
      >
        <PictureOutlined style={{ fontSize: '10px' }} />
        <span>[圖片: {alt || src || '圖片'}]</span>
      </span>
    );
  }

  // 對於其他圖片，也先顯示佔位符，避免 404 錯誤
  return (
    <span 
      className="image-placeholder"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '4px 8px',
        backgroundColor: '#f6f8fa',
        border: '1px solid #e1e4e8',
        borderRadius: '4px',
        fontSize: '12px',
        color: '#666',
        margin: '4px 0'
      }}
    >
      <PictureOutlined style={{ fontSize: '12px' }} />
      <span>圖片: {alt || title || src}</span>
    </span>
  );
};

/**
 * 自定義程式碼塊組件
 */
export const CustomCode = ({ children, className, ...props }) => {
  // 檢查是否是程式碼塊（有 language class）
  const isCodeBlock = className?.startsWith('language-');
  
  if (isCodeBlock) {
    return (
      <pre
        style={{
          backgroundColor: '#f6f8fa',
          border: '1px solid #e1e4e8',
          borderRadius: '6px',
          padding: '12px',
          margin: '8px 0',
          overflow: 'auto',
          fontFamily: "'Monaco', 'Consolas', 'Courier New', monospace",
          fontSize: '13px'
        }}
      >
        <code className={className} {...props}>
          {children}
        </code>
      </pre>
    );
  }

  // 行內程式碼
  return (
    <code
      style={{
        backgroundColor: '#f6f8fa',
        border: '1px solid #e1e4e8',
        borderRadius: '3px',
        padding: '2px 4px',
        fontSize: '12px',
        fontFamily: "'Monaco', 'Consolas', 'Courier New', monospace"
      }}
      {...props}
    >
      {children}
    </code>
  );
};

/**
 * 自定義標題組件
 */
export const CustomHeading = ({ level, children, ...props }) => {
  const HeadingTag = `h${level}`;
  
  const headingStyles = {
    1: {
      color: '#1890ff',
      fontSize: '20px',
      fontWeight: 600,
      margin: '12px 0 8px 0',
      borderBottom: '2px solid #1890ff',
      paddingBottom: '4px'
    },
    2: {
      color: '#1890ff',
      fontSize: '18px',
      fontWeight: 600,
      margin: '8px 0 6px 0'
    },
    3: {
      color: '#1890ff',
      fontSize: '16px',
      fontWeight: 600,
      margin: '6px 0 4px 0',
      borderLeft: '4px solid #1890ff',
      paddingLeft: '12px'
    },
    4: {
      color: '#333',
      fontSize: '15px',
      fontWeight: 600,
      margin: '4px 0 2px 0'
    }
  };

  return React.createElement(
    HeadingTag,
    {
      ...props,
      style: {
        ...headingStyles[level],
        ...props.style
      }
    },
    children
  );
};

/**
 * 自定義列表項目組件
 */
export const CustomListItem = ({ children, ordered, index, ...props }) => {
  if (ordered) {
    return (
      <li 
        style={{
          marginBottom: '2px',
          lineHeight: 1.5,
          paddingLeft: 0,
          position: 'relative',
          marginLeft: '24px'
        }}
        {...props}
      >
        {children}
      </li>
    );
  }

  return (
    <li 
      style={{
        marginBottom: '2px',
        lineHeight: 1.5,
        paddingLeft: 0,
        position: 'relative',
        marginLeft: '18px'
      }}
      {...props}
    >
      {children}
    </li>
  );
};

/**
 * 自定義引用組件
 */
export const CustomBlockquote = ({ children, ...props }) => (
  <blockquote
    style={{
      borderLeft: '4px solid #d9d9d9',
      margin: '8px 0',
      padding: '8px 12px',
      backgroundColor: '#f8f9ff',
      color: '#666',
      fontStyle: 'italic'
    }}
    {...props}
  >
    {children}
  </blockquote>
);

/**
 * 所有自定義組件的集合
 */
export const markdownComponents = {
  // 表格相關組件
  table: CustomTable,
  thead: CustomTableHead,
  tbody: ({ children, ...props }) => (
    <tbody {...props} style={{ display: 'table-row-group' }}>{children}</tbody>
  ),
  tr: ({ children, ...props }) => (
    <tr {...props} style={{ display: 'table-row' }}>{children}</tr>
  ),
  th: CustomTh,
  td: CustomTd,
  
  // 圖片組件
  img: CustomImage,
  
  // 程式碼組件
  code: CustomCode,
  pre: ({ children, ...props }) => <pre {...props}>{children}</pre>,
  
  // 標題組件
  h1: (props) => <CustomHeading level={1} {...props} />,
  h2: (props) => <CustomHeading level={2} {...props} />,
  h3: (props) => <CustomHeading level={3} {...props} />,
  h4: (props) => <CustomHeading level={4} {...props} />,
  h5: (props) => <CustomHeading level={5} {...props} />,
  h6: (props) => <CustomHeading level={6} {...props} />,
  
  // 列表組件
  ul: ({ children, ...props }) => <ul {...props}>{children}</ul>,
  ol: ({ children, ...props }) => <ol {...props}>{children}</ol>,
  li: CustomListItem,
  
  // 其他組件
  blockquote: CustomBlockquote,
  p: ({ children, ...props }) => <p {...props}>{children}</p>,
  a: ({ children, href, ...props }) => (
    <a href={href} {...props} style={{ color: '#1890ff', textDecoration: 'none' }}>
      {children}
    </a>
  ),
  strong: ({ children, ...props }) => <strong {...props}>{children}</strong>,
  em: ({ children, ...props }) => <em {...props}>{children}</em>,
  hr: ({ ...props }) => <hr {...props} style={{ border: 'none', borderTop: '1px solid #e8e8e8', margin: '16px 0' }} />
};