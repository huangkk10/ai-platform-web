import React, { useState } from 'react';
import { 
  Card, 
  Typography, 
  Form, 
  Input, 
  Button, 
  Space, 
  Divider, 
  message,
  Row,
  Col,
  Alert
} from 'antd';
import { 
  SettingOutlined, 
  LockOutlined, 
  UserOutlined,
  SafetyOutlined 
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;

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