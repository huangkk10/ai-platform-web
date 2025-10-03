import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Space, Typography } from 'antd';
import {
  SettingOutlined,
  FileSearchOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  UserOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import smiLogo from '../assets/images/smi.png';

const { Sider } = Layout;
const { Text } = Typography;

const Sidebar = ({ collapsed, onCollapse }) => {
  const { user, isAuthenticated, loading, initialized } = useAuth();
  const navigate = useNavigate();

  // 動態生成頂部選單項目，根據用戶認證狀態
  const getTopMenuItems = () => {
    const baseItems = [];

    // 只有登入用戶才能看到 Protocol RAG
    if (isAuthenticated && user) {
      baseItems.push({
        key: 'know-issue-chat',
        icon: <MessageOutlined />,
        label: 'Protocol RAG',
      });
    }

    // RVT Assistant 所有用戶都可以看到
    baseItems.push({
      key: 'rvt-assistant-chat',
      icon: <FileTextOutlined />,
      label: 'RVT Assistant',
    });

    // 只有登入用戶才能看到 AI OCR
    if (isAuthenticated && user) {
      baseItems.splice(-1, 0, {
        key: 'log-analyze-chat',
        icon: <FileTextOutlined />,
        label: 'AI OCR',
      });
    }

    return baseItems;
  };

  const topMenuItems = getTopMenuItems();

  // 處理選單點擊
  const handleMenuClick = ({ key }) => {
    console.log('Menu clicked:', key);
    switch (key) {
      case 'dashboard':
        navigate('/dashboard');
        break;
      case 'query':
        navigate('/query');
        break;
      case 'settings':
        navigate('/settings');
        break;
      case 'know-issue':
        navigate('/knowledge/know-issue');
        break;
      case 'rvt-log':
        navigate('/knowledge/rvt-log');
        break;
      case 'ocr-storage-benchmark':
        navigate('/knowledge/ocr-storage-benchmark');
        break;
      case 'know-issue-chat':
        navigate('/know-issue-chat');
        break;
      case 'log-analyze-chat':
        navigate('/log-analyze-chat');
        break;
      case 'rvt-assistant-chat':
        navigate('/rvt-assistant-chat');
        break;
      case 'log-analyze':
        navigate('/log-analyze');
        break;
      case 'test-class-management':
        navigate('/admin/test-class-management');
        break;
      case 'user-management':
        navigate('/admin/user-management');
        break;
      default:
        console.log('Unknown menu key:', key);
        break;
    }
  };

  const getBottomMenuItems = () => {
    // 基本選單項目（移除查詢結果）
    const basicItems = [];

    // knowledge submenu for authenticated users - 動態生成子項目
    const getKnowledgeChildren = () => {
      const children = [
        { key: 'know-issue', icon: <DatabaseOutlined />, label: 'Protocol RAG' },
        { key: 'rvt-log', icon: <DatabaseOutlined />, label: 'RVT Assistant' },
      ];

      // 只有登入用戶才能看到 AI OCR
      if (isAuthenticated && user) {
        children.splice(1, 0, {
          key: 'ocr-storage-benchmark', 
          icon: <BarChartOutlined />, 
          label: 'AI OCR'
        });
      }

      return children;
    };

    const knowledgeSubmenu = {
      key: 'knowledge',
      icon: <DatabaseOutlined />,
      label: '知識庫',
      children: getKnowledgeChildren(),
    };

    // admin submenu - 只有管理員可見
    const adminSubmenu = {
      key: 'admin',
      icon: <SettingOutlined />,
      label: '管理功能',
      children: [
        { key: 'test-class-management', icon: <ExperimentOutlined />, label: 'TestClass 管理' },
        { key: 'user-management', icon: <UserOutlined />, label: '用戶管理' },
      ],
    };

    const settingsItem = {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系統設定',
    };

    const items = [...basicItems];
    
    // 檢查當前路徑
    const currentPath = window.location.pathname;
    const isKnowledgePage = currentPath.startsWith('/knowledge/');
    const isAdminPage = currentPath.startsWith('/admin/');
    
    // 知識庫選單 - 登入用戶可見
    if ((initialized && isAuthenticated && user) || 
        (!initialized && isKnowledgePage)) {
      items.push(knowledgeSubmenu);
    }
    
    // 管理功能選單 - 只有管理員可見
    if ((initialized && isAuthenticated && user && (user.is_staff || user.is_superuser)) ||
        (!initialized && isAdminPage)) {
      items.push(adminSubmenu);
    }
    
    // 系統設定 - 只有管理員可見
    if ((initialized && isAuthenticated && user && (user.is_staff || user.is_superuser)) ||
        (!initialized && currentPath === '/settings')) {
      items.push(settingsItem);
    }
    
    return items;
  };

  const bottomMenuItems = getBottomMenuItems();

  return (
    <Sider 
      trigger={null}
      collapsible 
      collapsed={collapsed}
      width={300}
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
        borderBottom: '1px solid rgba(255,255,255,0.1)',
        cursor: 'pointer'
      }}
      onClick={() => navigate('/dashboard')}
      >
        {!collapsed ? (
          <Space align="center">
            <Avatar 
              src={smiLogo}
              size={48}
              style={{ 
                backgroundColor: '#3498db',
                fontSize: '18px',
                fontWeight: 'bold'
              }}
            >
              IA
            </Avatar>
            <div>
              <Text style={{ color: '#fff', fontSize: '20px', fontWeight: 'bold' }}>
                IA
              </Text>
              <br />
              <Text style={{ color: '#bdc3c7', fontSize: '14px' }}>
                Intelligence Assistant
              </Text>
            </div>
          </Space>
        ) : (
          <Avatar 
            src={smiLogo}
            size={40}
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

      {/* 上方清爽區域 - Protocol RAG */}
      <div style={{
        borderBottom: '2px solid #1f1f1f',
        marginBottom: '32px',
        backgroundColor: '#34495e',
        padding: '8px 0'
      }}>
        <Menu
          theme="dark"
          mode="inline"
          onClick={handleMenuClick}
          items={topMenuItems}
          style={{
            background: '#34495e',
            border: 'none',
            color: '#ecf0f1',
            fontSize: '20px'
          }}
        />
      </div>

      {/* 下方區域 - 其他選項（貼著底部） */}
      <div style={{
        position: 'absolute',
        bottom: '60px', // 留出收縮按鈕的空間
        left: 0,
        right: 0,
        paddingTop: '16px',
        borderTop: '1px solid rgba(255,255,255,0.1)'
      }}>
        <Menu
          theme="dark"
          mode="inline"
          onClick={handleMenuClick}
          items={bottomMenuItems}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#ecf0f1',
            fontSize: '20px'
          }}
        />
      </div>

      {/* 收縮按鈕 */}
      <div 
        style={{
          position: 'absolute',
          bottom: 20,
          left: collapsed ? '50%' : '20px',
          transform: collapsed ? 'translateX(-50%)' : 'none',
          cursor: 'pointer',
          color: '#bdc3c7',
          fontSize: '18px',
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