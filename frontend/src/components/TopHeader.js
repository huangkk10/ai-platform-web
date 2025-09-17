import React, { useState } from 'react';
import { Layout, Button, Dropdown, Avatar, Space, Typography, message } from 'antd';
import { 
  MenuOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  LoginOutlined,
  UserAddOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import LoginForm from './LoginForm';
import RegisterForm from './RegisterForm';
import AccountSettingsModal from './AccountSettingsModal';

const { Header } = Layout;
const { Text } = Typography;

const TopHeader = ({ collapsed, onToggleSidebar, pageTitle, extraActions }) => {
  const { user, isAuthenticated, logout, loading, initialized } = useAuth();
  const [loginVisible, setLoginVisible] = useState(false);
  const [registerVisible, setRegisterVisible] = useState(false);
  const [settingsVisible, setSettingsVisible] = useState(false);
  
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

  const handleRegisterSuccess = (msg) => {
    message.success(msg || '註冊成功！請使用新帳號登入');
    // 註冊成功後可以選擇自動打開登入表單
    setTimeout(() => {
      setLoginVisible(true);
    }, 1000);
  };

  // 下拉菜單點擊處理
  const handleMenuClick = ({ key }) => {
    switch (key) {
      case 'profile':
        message.info('個人資料功能開發中...');
        break;
      case 'settings':
        setSettingsVisible(true);
        break;
      case 'logout':
        handleLogout();
        break;
      default:
        break;
    }
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
    {
      key: 'register',
      icon: <UserAddOutlined />,
      label: '註冊',
      onClick: () => setRegisterVisible(true),
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
        {/* 左側：選單切換按鈕和頁面標題 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
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
          {pageTitle && (
            <Text strong style={{ 
              fontSize: '18px', 
              color: '#1890ff',
              lineHeight: '64px'
            }}>
              {pageTitle}
            </Text>
          )}
          
          {/* 額外的操作按鈕 */}
          {extraActions && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginLeft: 'auto', marginRight: '20px' }}>
              {extraActions}
            </div>
          )}
        </div>

        {/* 右側：用戶資訊 */}
        <div style={{ display: 'flex', alignItems: 'center', minWidth: '200px', justifyContent: 'flex-end' }}>
          <Space size="large">
            {/* 用戶下拉選單 */}
            {!initialized ? (
              <div style={{ display: 'flex', alignItems: 'center', minWidth: '120px' }}>
                <Avatar icon={<UserOutlined />} />
                <div style={{ marginLeft: '8px', textAlign: 'left' }}>
                  <Text>載入中...</Text>
                </div>
              </div>
            ) : isAuthenticated ? (
              <Dropdown
                menu={{ items: userMenuItems, onClick: handleMenuClick }}
                placement="bottom"
                arrow={false}
                overlayStyle={{ marginTop: '-2px' }}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  cursor: 'pointer',
                  minWidth: '120px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  transition: 'background-color 0.2s'
                }}>
                  <Avatar 
                    style={{ backgroundColor: '#1890ff' }}
                    icon={<UserOutlined />}
                  />
                  <div style={{ marginLeft: '8px', textAlign: 'left', flex: 1, paddingTop: '6px' }}>
                    <Text strong style={{ 
                      display: 'block', 
                      lineHeight: '18px',
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: '100px',
                      marginTop: '6px'
                    }}>
                      {user?.first_name && user?.last_name 
                        ? `${user.first_name} ${user.last_name}` 
                        : user?.username || '用戶'
                      }
                    </Text>
                    <Text type="secondary" style={{ 
                      fontSize: '12px', 
                      lineHeight: '14px',
                      whiteSpace: 'nowrap',
                      marginTop: '2px'
                    }}>
                      {user?.is_superuser ? '超級管理員' : user?.is_staff ? '管理員' : '用戶'}
                    </Text>
                  </div>
                </div>
              </Dropdown>
            ) : (
              <Dropdown
                menu={{ items: guestMenuItems }}
                placement="bottom"
                arrow={false}
                overlayStyle={{ marginTop: '-2px' }}
              >
                <div style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  cursor: 'pointer',
                  minWidth: '120px',
                  padding: '8px 12px',
                  borderRadius: '6px',
                  transition: 'background-color 0.2s'
                }}>
                  <Avatar icon={<UserOutlined />} />
                  <div style={{ marginLeft: '8px', textAlign: 'left', flex: 1, paddingTop: '6px' }}>
                    <Text style={{ 
                      display: 'block', 
                      lineHeight: '18px',
                      whiteSpace: 'nowrap',
                      marginTop: '6px'
                    }}>
                      訪客
                    </Text>
                    <Text type="secondary" style={{ 
                      fontSize: '12px', 
                      lineHeight: '14px',
                      whiteSpace: 'nowrap',
                      marginTop: '2px'
                    }}>
                      點擊登入
                    </Text>
                  </div>
                </div>
              </Dropdown>
            )}
          </Space>
        </div>
      </Header>

      {/* 登入表單 Modal */}
      <LoginForm
        visible={loginVisible}
        onClose={() => setLoginVisible(false)}
        onSuccess={handleLoginSuccess}
      />

      {/* 註冊表單 Modal */}
      <RegisterForm
        visible={registerVisible}
        onClose={() => setRegisterVisible(false)}
        onSuccess={handleRegisterSuccess}
      />

      {/* 帳戶設定 Modal */}
      <AccountSettingsModal
        visible={settingsVisible}
        onClose={() => setSettingsVisible(false)}
      />
    </>
  );
};

export default TopHeader;