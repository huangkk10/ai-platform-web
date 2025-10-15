import React from 'react';
import { Typography } from 'antd';
import ContentRenderer from '../ContentRenderer';

const { Title } = Typography;

/**
 * 文檔內容區塊組件
 * 使用 ContentRenderer 渲染 Markdown 內容
 */
const ContentSection = ({ content }) => {
  if (!content) return null;

  return (
    <div style={{ 
      marginBottom: '20px',
      padding: '16px',
      backgroundColor: '#e6f7ff',
      borderRadius: '8px',
      border: '1px solid #91d5ff'
    }}>
      <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
        📄 文檔內容
      </Title>
      <div style={{ 
        backgroundColor: 'white',
        padding: '16px',
        borderRadius: '6px',
        border: '1px solid #f5f5f5',
        fontSize: '14px',
        lineHeight: '1.8',
        minHeight: '200px',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <ContentRenderer 
          content={content}
          showImageTitles={true}
          showImageDescriptions={true}
          imageMaxWidth={350}
          imageMaxHeight={250}
        />
      </div>
    </div>
  );
};

export default ContentSection;
