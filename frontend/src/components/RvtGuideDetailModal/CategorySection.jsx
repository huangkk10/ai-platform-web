import React from 'react';
import { Typography } from 'antd';

const { Title } = Typography;

/**
 * 分類路徑區塊組件
 * 顯示文檔的完整分類路徑
 */
const CategorySection = ({ categoryName }) => {
  if (!categoryName) return null;

  return (
    <div style={{ 
      marginBottom: '20px',
      padding: '16px',
      backgroundColor: '#f6ffed',
      borderRadius: '8px',
      border: '1px solid #b7eb8f'
    }}>
      <Title level={4} style={{ margin: '0 0 12px 0', color: '#52c41a' }}>
        📍 分類路徑
      </Title>
      <div style={{ 
        backgroundColor: 'white',
        padding: '12px',
        borderRadius: '6px',
        border: '1px solid #f5f5f5',
        fontSize: '14px'
      }}>
        {categoryName}
      </div>
    </div>
  );
};

export default CategorySection;
