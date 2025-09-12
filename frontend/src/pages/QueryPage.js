import React from 'react';
import { Card, Typography } from 'antd';
import { FileSearchOutlined } from '@ant-design/icons';

const { Title } = Typography;

const QueryPage = () => {
  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <Title level={3}>
          <FileSearchOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          查詢結果
        </Title>
        <p>查詢功能正在開發中...</p>
      </Card>
    </div>
  );
};

export default QueryPage;