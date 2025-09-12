import React from 'react';
import { Card, Typography, Alert } from 'antd';
import { FileTextOutlined } from '@ant-design/icons';

const { Title, Paragraph } = Typography;

const RvtLogPage = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Title level={2}>
        <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
        RVT Log 管理
      </Title>
      
      <Alert
        message="功能開發中"
        description="RVT Log 管理功能正在開發中，敬請期待。"
        type="info"
        showIcon
        style={{ marginBottom: '24px' }}
      />
      
      <Card title="RVT Log 功能">
        <Paragraph>
          這裡將提供 RVT Log 的管理功能，包括：
        </Paragraph>
        <ul>
          <li>日誌查看與搜尋</li>
          <li>日誌分類與篩選</li>
          <li>異常日誌分析</li>
          <li>日誌匯出功能</li>
        </ul>
      </Card>
    </div>
  );
};

export default RvtLogPage;