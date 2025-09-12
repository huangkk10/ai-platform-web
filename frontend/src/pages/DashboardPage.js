import React from 'react';
import { Card, Typography } from 'antd';

const { Title, Paragraph } = Typography;

const DashboardPage = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3}>歡迎使用 IA 系統</Title>
        <Paragraph>請從左側選單選擇功能。</Paragraph>
      </Card>
    </div>
  );
};

export default DashboardPage;