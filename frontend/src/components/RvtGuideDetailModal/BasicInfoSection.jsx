import React from 'react';
import { Typography } from 'antd';
import dayjs from 'dayjs';

const { Title } = Typography;

/**
 * 基本信息區塊組件
 * 顯示文檔的標題、建立時間、更新時間
 */
const BasicInfoSection = ({ guide }) => {
  if (!guide) return null;

  return (
    <div style={{ 
      marginBottom: '20px',
      padding: '16px',
      backgroundColor: '#f8f9fa',
      borderRadius: '8px',
      border: '1px solid #e9ecef'
    }}>
      <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
        📝 基本信息
      </Title>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
        <div>
          <strong>📂 標題：</strong>
          <span style={{ marginLeft: '8px' }}>{guide.title}</span>
        </div>
        <div>
          <strong>📅 建立時間：</strong>
          <span style={{ marginLeft: '8px' }}>
            {dayjs(guide.created_at).format('YYYY-MM-DD HH:mm:ss')}
          </span>
        </div>
        <div>
          <strong>🔄 更新時間：</strong>
          <span style={{ marginLeft: '8px' }}>
            {dayjs(guide.updated_at).format('YYYY-MM-DD HH:mm:ss')}
          </span>
        </div>
      </div>
    </div>
  );
};

export default BasicInfoSection;
