import React, { useState } from 'react';
import './App.css';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Button } from 'antd';
import { DeleteOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider, useChatContext } from './contexts/ChatContext';
import DashboardPage from './pages/DashboardPage';
import QueryPage from './pages/QueryPage';
import SettingsPage from './pages/SettingsPage';
import KnowIssuePage from './pages/KnowIssuePage';
import RvtGuidePage from './pages/RvtGuidePage';
import OcrStorageBenchmarkPage from './pages/OcrStorageBenchmarkPage';
import TestClassManagementPage from './pages/TestClassManagementPage';
import IntegratedUserManagementPage from './pages/admin/IntegratedUserManagementPage';
import KnowIssueChatPage from './pages/KnowIssueChatPage';
import LogAnalyzeChatPage from './pages/LogAnalyzeChatPage';
import RvtAssistantChatPage from './pages/RvtAssistantChatPage';
import LogAnalyzePage from './pages/LogAnalyzePage';
import RvtGuideEditPage from './pages/RvtGuideEditPage';

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
  const navigate = useNavigate();

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/know-issue-chat':
        return 'Protocol RAG';
      case '/log-analyze-chat':
        return 'AI OCR';
      case '/rvt-assistant-chat':
        return 'RVT Assistant';
      case '/dashboard':
        return 'Dashboard';
      case '/query':
        return 'Query';
      case '/settings':
        return 'Settings';
      case '/knowledge/know-issue':
        return 'Protocol RAG';
      case '/knowledge/rvt-log':
        return 'RVT Assistant';
      case '/knowledge/rvt-guide/create':
        return 'RVT Assistant - 新增 User Guide';
      case '/admin/user-management':
        return '用戶權限管理';
      default:
        // 動態處理編輯頁面的標題
        if (pathname.startsWith('/knowledge/rvt-guide/edit/')) {
          return 'RVT Assistant - 編輯 User Guide';
        }
        return '';
    }
  };

  const getExtraActions = (pathname, navigate) => {
    if ((pathname === '/know-issue-chat' || pathname === '/log-analyze-chat' || pathname === '/rvt-assistant-chat') && clearChatFunction) {
      return (
        <Button 
          icon={<DeleteOutlined />} 
          onClick={clearChatFunction}
          type="text"
          style={{ color: '#666' }}
        >
          新聊天
        </Button>
      );
    }
    
    // RVT Guide 編輯頁面的返回按鈕
    if (pathname === '/knowledge/rvt-guide/create' || pathname.startsWith('/knowledge/rvt-guide/edit/')) {
      return (
        <Button 
          icon={<ArrowLeftOutlined />} 
          onClick={() => navigate('/knowledge/rvt-log')}
          type="text"
          style={{ color: '#666' }}
        >
          返回列表
        </Button>
      );
    }
    
    return null;
  };

  const currentPageTitle = getPageTitle(location.pathname);
  const currentExtraActions = getExtraActions(location.pathname, navigate);

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar 
        collapsed={collapsed}
        onCollapse={toggleSidebar}
      />
      
      <Layout style={{ marginLeft: collapsed ? 80 : 300, transition: 'margin-left 0.2s' }}>
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
            <Route path="/knowledge/rvt-log" element={<RvtGuidePage />} />
            <Route path="/knowledge/rvt-guide/create" element={<RvtGuideEditPage />} />
            <Route path="/knowledge/rvt-guide/edit/:id" element={<RvtGuideEditPage />} />
            <Route path="/knowledge/ocr-storage-benchmark" element={<OcrStorageBenchmarkPage />} />
            <Route path="/know-issue-chat" element={<KnowIssueChatPage collapsed={collapsed} />} />
            <Route path="/log-analyze-chat" element={<LogAnalyzeChatPage collapsed={collapsed} />} />
            <Route path="/rvt-assistant-chat" element={<RvtAssistantChatPage collapsed={collapsed} />} />
            <Route path="/log-analyze" element={<LogAnalyzePage />} />
            <Route path="/admin/test-class-management" element={<TestClassManagementPage />} />
            <Route path="/admin/user-management" element={<IntegratedUserManagementPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
