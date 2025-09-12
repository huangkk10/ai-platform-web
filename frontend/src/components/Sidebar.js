import React from 'react';
import { Layout, Menu, Avatar, Space, Typography } from 'antd';
import {
  SettingOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const { Sider } = Layout;
const { Text } = Typography;

const Sidebar = ({ collapsed, onCollapse, selectedKey, onMenuSelect }) => {
  const { user, isAuthenticated } = useAuth();

  // 基本選單項目（所有用戶都能看到）
  const baseMenuItems = [
    {
      key: 'query',
      icon: <FileSearchOutlined />,
      label: '查詢結果',
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系統設定',
    },
  ];

  // knowledge submenu only for admin users
  const knowledgeSubmenu = {
    key: 'knowledge',
    icon: <DatabaseOutlined />,
    label: '知識庫',
    children: [
      { key: 'knowledge.know_issue', icon: <DatabaseOutlined />, label: 'know issue' },
      { key: 'knowledge.rvt_log', icon: <DatabaseOutlined />, label: 'RVT Log' },
    ],
  };

  const getMenuItems = () => {
    const items = [...baseMenuItems];
    if (isAuthenticated && user && (user.is_staff || user.is_superuser)) {
      // insert knowledge menu before settings if present
      const idx = items.findIndex(i => i.key === 'settings');
      if (idx >= 0) {
        items.splice(idx, 0, knowledgeSubmenu);
      } else {
        items.push(knowledgeSubmenu);
      }
    }
    return items;
  };

  const menuItems = getMenuItems();

  return (
    <Sider 
      trigger={null}
      collapsible 
      collapsed={collapsed}
      width={250}
      style={{
        background: '#2c3e50',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        zIndex: 1000,
        boxShadow: '2px 0 8px rgba(0,0,0,0.15)'
      }}
    >
      {/* Logo 區域 */}
      <div style={{
        height: 64,
        background: '#34495e',
        display: 'flex',
        alignItems: 'center',
        justifyContent: collapsed ? 'center' : 'flex-start',
        padding: collapsed ? 0 : '0 20px',
        borderBottom: '1px solid rgba(255,255,255,0.1)'
      }}>
        {!collapsed ? (
          <Space align="center">
            <Avatar 
              style={{ 
                backgroundColor: '#3498db',
                fontSize: '18px',
                fontWeight: 'bold'
              }}
            >
              IA
            </Avatar>
            <div>
              <Text style={{ color: '#fff', fontSize: '16px', fontWeight: 'bold' }}>
                IA
              </Text>
              <br />
              <Text style={{ color: '#bdc3c7', fontSize: '12px' }}>
                Intelligence Assistant
              </Text>
            </div>
          </Space>
        ) : (
          <Avatar 
            style={{ 
              backgroundColor: '#3498db',
              fontSize: '18px',
              fontWeight: 'bold'
            }}
          >
            IA
          </Avatar>
        )}
      </div>

      {/* 菜單 */}
      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={[selectedKey]}
        onClick={onMenuSelect}
        items={menuItems}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#ecf0f1'
        }}
      />

      {/* 收縮按鈕 */}
      <div 
        style={{
          position: 'absolute',
          bottom: 20,
          left: collapsed ? '50%' : '20px',
          transform: collapsed ? 'translateX(-50%)' : 'none',
          cursor: 'pointer',
          color: '#bdc3c7',
          fontSize: '16px',
          padding: '8px',
          borderRadius: '4px',
          transition: 'all 0.3s'
        }}
        onClick={onCollapse}
        onMouseEnter={(e) => e.target.style.color = '#fff'}
        onMouseLeave={(e) => e.target.style.color = '#bdc3c7'}
      >
        {collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
      </div>
    </Sider>
  );
};

export default Sidebar;