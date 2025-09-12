import React from 'react';
import { Card, Typography } from 'antd';
import { SettingOutlined } from '@ant-design/icons';

const { Title } = Typography;

const SettingsPage = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3}>
          <SettingOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          系統設定
        </Title>
        <p>系統設定功能正在開發中...</p>
      </Card>
    </div>
  );
};

export default SettingsPage;