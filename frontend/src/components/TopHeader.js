import React, { useState } from 'react';
import { Layout, Button, Dropdown, Avatar, Badge, Space, Typography, message } from 'antd';
import { 
  MenuOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  LoginOutlined,
  BellOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from './LoginForm';

const { Header } = Layout;
const { Text } = Typography;

const TopHeader = ({ collapsed, onToggleSidebar }) => {
  const { user, isAuthenticated, logout, loading } = useAuth();
  const [loginVisible, setLoginVisible] = useState(false);
  
  const handleLogout = async () => {
    try {
      const result = await logout();
      if (result.success) {
        message.success(result.message);
      } else {
        message.warning(result.message);
      }
    } catch (error) {
      message.error('登出失敗');
    }
  };

  const handleLoginSuccess = (msg) => {
    message.success(msg || '登入成功');
  };

  // 已登入用戶的下拉選單
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
      onClick: handleLogout,
    },
  ];

  // 訪客用戶的下拉選單
  const guestMenuItems = [
    {
      key: 'login',
      icon: <LoginOutlined />,
      label: '登入',
      onClick: () => setLoginVisible(true),
    },
  ];

  return (
    <>
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
        <Space size="large">
          {/* 通知圖標 */}
          <Badge count={3} size="small">
            <Button 
              type="text" 
              icon={<BellOutlined />} 
              style={{ fontSize: '16px' }}
            />
          </Badge>

          {/* 用戶下拉選單 */}
          {loading ? (
            <Avatar icon={<UserOutlined />} />
          ) : isAuthenticated ? (
            <Dropdown
              menu={{ items: userMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar 
                  style={{ backgroundColor: '#1890ff' }}
                  icon={<UserOutlined />}
                />
                <div style={{ textAlign: 'left' }}>
                  <Text strong style={{ display: 'block', lineHeight: '16px' }}>
                    {user?.first_name && user?.last_name 
                      ? `${user.first_name} ${user.last_name}` 
                      : user?.username || '用戶'
                    }
                  </Text>
                  <Text type="secondary" style={{ fontSize: '12px', lineHeight: '16px' }}>
                    {user?.is_superuser ? '超級管理員' : user?.is_staff ? '管理員' : '用戶'}
                  </Text>
                </div>
              </Space>
            </Dropdown>
          ) : (
            <Dropdown
              menu={{ items: guestMenuItems }}
              placement="bottomRight"
              arrow
            >
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <div style={{ textAlign: 'left' }}>
                  <Text style={{ display: 'block', lineHeight: '16px' }}>
                    訪客
                  </Text>
                  <Text type="secondary" style={{ fontSize: '12px', lineHeight: '16px' }}>
                    點擊登入
                  </Text>
                </div>
              </Space>
            </Dropdown>
          )}
        </Space>
      </Header>

      {/* 登入表單 Modal */}
      <LoginForm
        visible={loginVisible}
        onClose={() => setLoginVisible(false)}
        onSuccess={handleLoginSuccess}
      />
    </>
  );
};

export default TopHeader;