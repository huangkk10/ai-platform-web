import React, { useState, useEffect } from 'react';
import './App.css';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Layout, Button } from 'antd';
import { DeleteOutlined } from '@ant-design/icons';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider, useChatContext } from './contexts/ChatContext';
import DashboardPage from './pages/DashboardPage';
import QueryPage from './pages/QueryPage';
import SettingsPage from './pages/SettingsPage';
import KnowIssuePage from './pages/KnowIssuePage';
import RvtLogPage from './pages/RvtLogPage';
import TestClassManagementPage from './pages/TestClassManagementPage';
import KnowIssueChatPage from './pages/KnowIssueChatPage';
import LogAnalyzePage from './pages/LogAnalyzePage';

const { Content } = Layout;

// 配置 axios
// 使用相對路徑，這樣會自動使用當前頁面的 host
axios.defaults.baseURL = '';  // 或者使用 window.location.origin
axios.defaults.withCredentials = true;

function App() {
  return (
    <AuthProvider>
      <ChatProvider>
        <Router>
          <AppLayout />
        </Router>
      </ChatProvider>
    </AuthProvider>
  );
}

function AppLayout() {
  const [collapsed, setCollapsed] = useState(false);
  const { clearChatFunction } = useChatContext();
  const location = useLocation();

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/know-issue-chat':
        return 'Know Issue Chat';
      case '/dashboard':
        return 'Dashboard';
      case '/query':
        return 'Query';
      case '/settings':
        return 'Settings';
      case '/knowledge/know-issue':
        return 'Know Issue';
      case '/knowledge/rvt-log':
        return 'RVT Log';
      case '/log-analyze':
        return 'Log Analyze';
      case '/admin/test-class-management':
        return 'Test Class Management';
      default:
        return '';
    }
  };

  const getExtraActions = (pathname) => {
    if (pathname === '/know-issue-chat' && clearChatFunction) {
      return (
        <Button 
          icon={<DeleteOutlined />} 
          onClick={clearChatFunction}
          type="text"
          style={{ color: '#666' }}
        >
          清空對話
        </Button>
      );
    }
    return null;
  };

  const currentPageTitle = getPageTitle(location.pathname);
  const currentExtraActions = getExtraActions(location.pathname);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar 
        collapsed={collapsed}
        onCollapse={toggleSidebar}
      />
      
      <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'margin-left 0.2s' }}>
        <TopHeader 
          collapsed={collapsed} 
          onToggleSidebar={toggleSidebar}
          pageTitle={currentPageTitle}
          extraActions={currentExtraActions}
        />
        
        <Content style={{ 
          marginTop: 64,
          background: '#f5f5f5',
          minHeight: 'calc(100vh - 64px)',
          overflow: 'auto'
        }}>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/query" element={<QueryPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/knowledge/know-issue" element={<KnowIssuePage />} />
            <Route path="/knowledge/rvt-log" element={<RvtLogPage />} />
            <Route path="/know-issue-chat" element={<KnowIssueChatPage collapsed={collapsed} />} />
            <Route path="/log-analyze" element={<LogAnalyzePage />} />
            <Route path="/admin/test-class-management" element={<TestClassManagementPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
