import React from 'react';
import { Layout, Avatar, Space, Dropdown, Typography, Badge, Button } from 'antd';
import {
  BellOutlined,
  SettingOutlined,
  LogoutOutlined,
  UserOutlined,
  MenuOutlined
} from '@ant-design/icons';

const { Header } = Layout;
const { Text } = Typography;

const TopHeader = ({ collapsed, onToggleSidebar }) => {
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '個人資料',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '帳戶設定',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '登出',
      danger: true,
    },
  ];

  return (
    <Header 
      style={{
        background: '#fff',
        padding: '0 20px',
        height: 64,
        lineHeight: '64px',
        borderBottom: '1px solid #f0f0f0',
        position: 'fixed',
        top: 0,
        right: 0,
        left: collapsed ? 80 : 250,
        zIndex: 999,
        transition: 'left 0.2s',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        boxShadow: '0 1px 4px rgba(0,21,41,.08)'
      }}
    >
      {/* 左側：選單切換按鈕 */}
      <Button 
        type="text" 
        icon={<MenuOutlined />} 
        onClick={onToggleSidebar}
        style={{
          fontSize: '16px',
          width: 40,
          height: 40,
        }}
      />

      {/* 右側：用戶資訊 */}
      <Space size="middle">
        {/* 通知鈴鐺 */}
        <Badge count={3} size="small">
          <Button
            type="text"
            icon={<BellOutlined />}
            style={{
              fontSize: '16px',
              width: 40,
              height: 40,
            }}
          />
        </Badge>

        {/* 用戶下拉選單 */}
        <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
          <Space style={{ cursor: 'pointer' }}>
            <Avatar
              style={{ 
                backgroundColor: '#87d068',
                fontSize: '14px'
              }}
            >
              管
            </Avatar>
            <div style={{ textAlign: 'right' }}>
              <Text strong style={{ fontSize: '14px', color: '#333' }}>
                admin
              </Text>
              <br />
              <Text type="secondary" style={{ fontSize: '12px' }}>
                系統管理員
              </Text>
            </div>
          </Space>
        </Dropdown>
      </Space>
    </Header>
  );
};

export default TopHeader;