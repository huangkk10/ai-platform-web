import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout, Menu, Avatar, Space, Typography, Dropdown } from 'antd';
import {
  SettingOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  UserOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined,
  ToolOutlined,
  RightOutlined,
  SlidersOutlined,
  DashboardOutlined,
  PlayCircleOutlined,
  TagOutlined,
  ThunderboltOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import smiLogo from '../assets/images/smi.png';

const { Sider } = Layout;
const { Text } = Typography;

const Sidebar = ({ collapsed, onCollapse }) => {
  const { user, isAuthenticated, initialized, hasPermission, canManagePermissions } = useAuth();
  const navigate = useNavigate();
  const [knowledgeMenuVisible, setKnowledgeMenuVisible] = useState(false);

  // 動態生成頂部選單項目，根據用戶權限
  const getTopMenuItems = () => {
    const baseItems = [];

    // Protocol RAG - 需要 web_protocol_rag 權限
    if (isAuthenticated && user && hasPermission('webProtocolRAG')) {
      baseItems.push({
        key: 'know-issue-chat',
        icon: <MessageOutlined />,
        label: 'Protocol RAG',
      });
    }

    // AI OCR - 需要 web_ai_ocr 權限
    if (isAuthenticated && user && hasPermission('webAIOCR')) {
      baseItems.push({
        key: 'log-analyze-chat',
        icon: <FileTextOutlined />,
        label: 'AI OCR',
      });
    }

    // RVT Assistant - 對所有用戶開放（包括訪客）
    baseItems.push({
      key: 'rvt-assistant-chat',
      icon: <FileTextOutlined />,
      label: 'RVT Assistant',
    });

    // Protocol Assistant - 需要 web_protocol_assistant 權限
    if (isAuthenticated && user && hasPermission('webProtocolAssistant')) {
      baseItems.push({
        key: 'protocol-assistant-chat',
        icon: <ToolOutlined />,
        label: 'Protocol Assistant',
      });
    }

    return baseItems;
  }; const topMenuItems = getTopMenuItems();

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
      case 'protocol-log':
        navigate('/knowledge/protocol-log');
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
      case 'protocol-assistant-chat':
        navigate('/protocol-assistant-chat');
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
      case 'threshold-settings':
        navigate('/admin/threshold-settings');
        break;
      case 'system-logs':
        navigate('/admin/system-logs');
        break;
      case 'rvt-analytics':
        navigate('/admin/rvt-analytics');
        break;
      case 'markdown-test':
        navigate('/dev/markdown-test');
        break;
      case 'benchmark-dashboard':
        navigate('/benchmark/dashboard');
        break;
      case 'benchmark-test-cases':
        navigate('/benchmark/test-cases');
        break;
      case 'benchmark-test-execution':
        navigate('/benchmark/test-execution');
        break;
      case 'benchmark-batch-test':
        navigate('/benchmark/batch-test');
        break;
      case 'benchmark-batch-history':
        navigate('/benchmark/batch-history');
        break;
      case 'benchmark-results':
        navigate('/benchmark/results');
        break;
      case 'benchmark-versions':
        navigate('/benchmark/versions');
        break;
      default:
        console.log('Unknown menu key:', key);
        break;
    }
  };

  const getBottomMenuItems = () => {
    // 基本選單項目（移除查詢結果）
    const basicItems = [];

    // 獲取知識庫子項目用於 Dropdown
    const getKnowledgeMenuItems = () => {
      const items = [];

      // Protocol RAG 知識庫 - 需要 kb_protocol_rag 權限
      if (isAuthenticated && user && hasPermission('kbProtocolRAG')) {
        items.push({
          key: 'know-issue',
          icon: <DatabaseOutlined />,
          label: 'Protocol RAG',
          onClick: () => navigate('/knowledge/know-issue')
        });
      }

      // AI OCR 知識庫 - 需要 kb_ai_ocr 權限
      if (isAuthenticated && user && hasPermission('kbAIOCR')) {
        items.push({
          key: 'ocr-storage-benchmark',
          icon: <BarChartOutlined />,
          label: 'AI OCR',
          onClick: () => navigate('/knowledge/ocr-storage-benchmark')
        });
      }

      // RVT Assistant 知識庫 - 需要 kb_rvt_assistant 權限
      if (isAuthenticated && user && hasPermission('kbRVTAssistant')) {
        items.push({
          key: 'rvt-log',
          icon: <DatabaseOutlined />,
          label: 'RVT Assistant',
          onClick: () => navigate('/knowledge/rvt-log')
        });
      }

      // Protocol Assistant 知識庫 - 需要 kb_protocol_assistant 權限
      if (isAuthenticated && user && hasPermission('kbProtocolAssistant')) {
        items.push({
          key: 'protocol-log',
          icon: <ToolOutlined />,
          label: 'Protocol Assistant',
          onClick: () => navigate('/knowledge/protocol-log')
        });
      }

      return items;
    };

    // 知識庫選單項目 - 不使用 children，改用自定義渲染
    const knowledgeMenuItem = {
      key: 'knowledge',
      icon: <DatabaseOutlined />,
      label: (
        <Dropdown
          menu={{ items: getKnowledgeMenuItems() }}
          placement="right"
          trigger={['hover']}
          overlayClassName="knowledge-submenu-popup"
          open={knowledgeMenuVisible}
          onOpenChange={setKnowledgeMenuVisible}
        >
          <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
            知識庫
            <RightOutlined style={{ fontSize: '12px', marginLeft: '8px' }} />
          </span>
        </Dropdown>
      ),
    };

    // admin submenu - 只有管理員可見
    const getAdminChildren = () => {
      const children = [];

      // TestClass 管理 - Django 管理員權限
      if (user && (user.is_staff || user.is_superuser)) {
        children.push({ key: 'test-class-management', icon: <ExperimentOutlined />, label: 'TestClass 管理' });
      }

      // 整合的用戶權限管理 - Django 管理員權限
      if (user && (user.is_staff || user.is_superuser)) {
        children.push({ key: 'user-management', icon: <UserOutlined />, label: '用戶權限管理' });
      }

      // Threshold 設定 - Django 管理員權限
      if (user && (user.is_staff || user.is_superuser)) {
        children.push({ key: 'threshold-settings', icon: <SlidersOutlined />, label: 'Threshold 設定' });
      }

      // 系統日誌查看器 - Django 管理員權限
      if (user && (user.is_staff || user.is_superuser)) {
        children.push({ key: 'system-logs', icon: <FileTextOutlined />, label: '系統日誌' });
      }

      // RVT Analytics 分析報告 - Django 管理員權限
      if (user && (user.is_staff || user.is_superuser)) {
        children.push({ key: 'rvt-analytics', icon: <BarChartOutlined />, label: 'Assistant 分析' });
      }

      return children;
    };

    const adminSubmenu = {
      key: 'admin',
      icon: <SettingOutlined />,
      label: '管理功能',
      children: getAdminChildren(),
    };

    const settingsItem = {
      key: 'settings',
      icon: <SettingOutlined />,
      label: '系統設定',
    };

    // Benchmark 測試系統選單
    const benchmarkSubmenu = {
      key: 'benchmark',
      icon: <ThunderboltOutlined />,
      label: 'Benchmark 測試',
      children: [
        {
          key: 'benchmark-dashboard',
          icon: <DashboardOutlined />,
          label: 'Dashboard',
        },
        {
          key: 'benchmark-test-cases',
          icon: <FileTextOutlined />,
          label: 'Test Cases',
        },
        {
          key: 'benchmark-test-execution',
          icon: <PlayCircleOutlined />,
          label: 'Test Execution',
        },
        {
          key: 'benchmark-batch-test',
          icon: <ThunderboltOutlined />,
          label: 'Batch Test',
        },
        {
          key: 'benchmark-batch-history',
          icon: <HistoryOutlined />,
          label: 'Batch History',
        },
        {
          key: 'benchmark-results',
          icon: <BarChartOutlined />,
          label: 'Results',
        },
        {
          key: 'benchmark-versions',
          icon: <TagOutlined />,
          label: 'Versions',
        },
      ],
    };

    const devToolsItem = {
      key: 'dev-tools',
      icon: <ExperimentOutlined />,
      label: '開發工具',
      children: [
        {
          key: 'markdown-test',
          icon: <FileTextOutlined />,
          label: 'Markdown 測試',
        },
      ],
    };

    const items = [...basicItems];

    // 檢查當前路徑
    const currentPath = window.location.pathname;
    const isKnowledgePage = currentPath.startsWith('/knowledge/');
    const isAdminPage = currentPath.startsWith('/admin/');
    const isBenchmarkPage = currentPath.startsWith('/benchmark/');

    // Benchmark 測試系統選單 - 需要管理員權限（暫定）
    if ((initialized && isAuthenticated && user && (user.is_staff || user.is_superuser)) ||
      (!initialized && isBenchmarkPage)) {
      items.push(benchmarkSubmenu);
    }

    // 知識庫選單 - 需要任何知識庫權限
    const knowledgeMenuItems = getKnowledgeMenuItems();
    if ((initialized && isAuthenticated && user && knowledgeMenuItems.length > 0) ||
      (!initialized && isKnowledgePage)) {
      items.push(knowledgeMenuItem);
    }

    // 管理功能選單 - 需要管理權限
    const adminChildren = getAdminChildren();
    if ((initialized && isAuthenticated && user && adminChildren.length > 0) ||
      (!initialized && isAdminPage)) {
      items.push(adminSubmenu);
    }

    // 系統設定 - 只有管理員可見
    if ((initialized && isAuthenticated && user && (user.is_staff || user.is_superuser || canManagePermissions())) ||
      (!initialized && currentPath === '/settings')) {
      items.push(settingsItem);
    }

    // 開發工具 - 所有登入用戶可見
    const isDevPage = currentPath.startsWith('/dev/');
    if ((initialized && isAuthenticated && user) ||
      (!initialized && isDevPage)) {
      items.push(devToolsItem);
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