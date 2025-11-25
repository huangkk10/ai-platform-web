import React, { useState } from 'react';
import './App.css';
import axios from 'axios';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { Layout, Button } from 'antd';
import { DeleteOutlined, ArrowLeftOutlined, SaveOutlined, PlusOutlined, ReloadOutlined } from '@ant-design/icons';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import { ChatProvider, useChatContext } from './contexts/ChatContext';
import DashboardPage from './pages/DashboardPage';
import QueryPage from './pages/QueryPage';
import SettingsPage from './pages/SettingsPage';
import KnowIssuePage from './pages/KnowIssuePage';
import RvtGuidePage from './pages/RvtGuidePage';
import ProtocolGuidePage from './pages/ProtocolGuidePage';
import GuidePreviewPage from './pages/GuidePreviewPage';
import OcrStorageBenchmarkPage from './pages/OcrStorageBenchmarkPage';
import TestClassManagementPage from './pages/TestClassManagementPage';
import IntegratedUserManagementPage from './pages/admin/IntegratedUserManagementPage';
import ThresholdSettingsPage from './pages/admin/ThresholdSettingsPage';
import KnowIssueChatPage from './pages/KnowIssueChatPage';
import LogAnalyzeChatPage from './pages/LogAnalyzeChatPage';
import RvtAssistantChatPage from './pages/RvtAssistantChatPage';
import ProtocolAssistantChatPage from './pages/ProtocolAssistantChatPage';
import LogAnalyzePage from './pages/LogAnalyzePage';
import MarkdownEditorPage from './pages/MarkdownEditorPage';
import UnifiedAnalyticsPage from './pages/UnifiedAnalyticsPage';
import DevMarkdownTestPage from './pages/DevMarkdownTestPage';
import SystemLogViewerPage from './pages/admin/SystemLogViewerPage';
import BenchmarkDashboardPage from './pages/benchmark/BenchmarkDashboardPage';
// ✅ Test Execution 已移除，統一使用 Batch Test
// import BenchmarkTestExecutionPage from './pages/benchmark/BenchmarkTestExecutionPage';
import BatchTestExecutionPage from './pages/benchmark/BatchTestExecutionPage';
import BatchComparisonPage from './pages/benchmark/BatchComparisonPage';
import BatchTestHistoryPage from './pages/benchmark/BatchTestHistoryPage';
import TestCasesListPage from './pages/benchmark/TestCasesListPage';
import UnifiedTestCasePage from './pages/benchmark/UnifiedTestCasePage';

// Dify Benchmark 頁面
import DifyVersionManagementPage from './pages/dify-benchmark/DifyVersionManagementPage';
import DifyTestCasePage from './pages/dify-benchmark/DifyTestCasePage';
import DifyTestHistoryPage from './pages/benchmark/DifyTestHistoryPage';

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
      case '/protocol-assistant-chat':
        return 'Protocol Assistant';
      case '/dashboard':
        return 'Dashboard';
      case '/query':
        return 'Query';
      case '/settings':
        return 'Settings';
      case '/knowledge/know-issue':
        return 'Protocol RAG';
      case '/knowledge/rvt-log':
        return 'RVT Assistant 知識庫';
      case '/knowledge/protocol-log':
        return 'Protocol Assistant 知識庫';
      case '/admin/user-management':
        return '用戶權限管理';
      case '/admin/threshold-settings':
        return '搜尋 Threshold 設定';
      case '/admin/system-logs':
        return '系統日誌查看器';
      case '/admin/rvt-analytics':
      case '/admin/analytics':
        return 'Analytics Dashboard';
      case '/dev/markdown-test':
        return '🧪 Markdown 測試頁面';
      case '/benchmark/dashboard':
        return 'Benchmark Dashboard';
      case '/benchmark/test-cases':
        return '測試案例管理';
      // ✅ Test Execution 已移除
      // case '/benchmark/test-execution':
      //   return '測試執行';
      case '/benchmark/batch-test':
        return '批量測試';
      case '/benchmark/batch-history':
        return '批量測試歷史';
      case '/benchmark/results':
        return '測試結果';
      case '/benchmark/versions':
        return '版本管理';
      case '/benchmark/dify/versions':
      case '/dify-benchmark/versions':
        return 'VSA 版本管理';
      case '/benchmark/dify/test-cases':
      case '/dify-benchmark/test-cases':
        return 'VSA 測試案例';
      case '/benchmark/dify/batch-test':
      case '/dify-benchmark/batch-test':
        return 'VSA 批量測試';
      case '/benchmark/dify/history':
      case '/dify-benchmark/history':
        return 'VSA 測試歷史';
      case '/dify-benchmark/dashboard':
        return 'VSA Benchmark Dashboard';
      default:
        // Markdown 編輯器頁面標題（整頁模式）
        if (pathname.startsWith('/knowledge/rvt-guide/markdown-edit/')) {
          const id = pathname.split('/').pop();
          return { text: '編輯 RVT Guide', id: id };
        }
        if (pathname === '/knowledge/rvt-guide/markdown-create') {
          return { text: '新建 RVT Guide', id: null };
        }
        // Protocol Guide Markdown 編輯器頁面標題
        if (pathname.startsWith('/knowledge/protocol-guide/markdown-edit/')) {
          const id = pathname.split('/').pop();
          return { text: '編輯 Protocol Guide', id: id };
        }
        if (pathname === '/knowledge/protocol-guide/markdown-create') {
          return { text: '新建 Protocol Guide', id: null };
        }
        // 預覽頁面標題
        if (pathname.startsWith('/knowledge/rvt-guide/preview/')) {
          const id = pathname.split('/').pop();
          return { text: 'RVT Guide 預覽', id: id };
        }
        if (pathname.startsWith('/knowledge/protocol-guide/preview/')) {
          const id = pathname.split('/').pop();
          return { text: 'Protocol Guide 預覽', id: id };
        }
        return '';
    }
  };

  const getExtraActions = (pathname, navigate) => {
    if ((pathname === '/know-issue-chat' || pathname === '/log-analyze-chat' || pathname === '/rvt-assistant-chat' || pathname === '/protocol-assistant-chat') && clearChatFunction) {
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

    // RVT Assistant 知識庫頁面的按鈕
    if (pathname === '/knowledge/rvt-log') {
      return (
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              // 觸發自定義事件通知頁面重新載入
              window.dispatchEvent(new CustomEvent('rvt-guide-reload'));
            }}
            size="large"
          >
            重新整理
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<PlusOutlined />}
            onClick={() => navigate('/knowledge/rvt-guide/markdown-create')}
          >
            新增 User Guide
          </Button>
        </div>
      );
    }

    // Protocol Assistant 知識庫頁面的按鈕
    if (pathname === '/knowledge/protocol-log') {
      return (
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              // 觸發自定義事件通知頁面重新載入
              window.dispatchEvent(new CustomEvent('protocol-guide-reload'));
            }}
            size="large"
          >
            重新整理
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<PlusOutlined />}
            onClick={() => navigate('/knowledge/protocol-guide/markdown-create')}
          >
            新增 Protocol Guide
          </Button>
        </div>
      );
    }

    // Markdown 編輯器頁面的按鈕（整頁模式）
    if (pathname.startsWith('/knowledge/rvt-guide/markdown-') || pathname.startsWith('/knowledge/protocol-guide/markdown-')) {
      // 這些按鈕會在 TopHeader 中顯示
      // 更新按鈕通過全局事件觸發，MarkdownEditorPage 會監聽該事件
      const isEditMode = pathname.includes('/markdown-edit/');
      const isProtocolGuide = pathname.includes('/protocol-guide/');
      const returnPath = isProtocolGuide ? '/knowledge/protocol-log' : '/knowledge/rvt-log';

      return (
        <div style={{ display: 'flex', gap: '12px' }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(returnPath)}
            size="large"
          >
            返回列表
          </Button>
          <Button
            type="primary"
            size="large"
            icon={<SaveOutlined />}
            onClick={() => {
              // 觸發自定義事件，通知 MarkdownEditorPage 執行保存
              window.dispatchEvent(new CustomEvent('markdown-editor-save'));
            }}
          >
            {isEditMode ? '更新' : '儲存'}
          </Button>
        </div>
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
            <Route path="/knowledge/know-issue" element={
              <ProtectedRoute permission="kbProtocolRAG" fallbackTitle="Knowledge Base 存取受限">
                <KnowIssuePage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/rvt-log" element={
              <ProtectedRoute permission="kbRVTAssistant" fallbackTitle="Knowledge Base 存取受限">
                <RvtGuidePage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/protocol-log" element={
              <ProtectedRoute permission="kbProtocolAssistant" fallbackTitle="Knowledge Base 存取受限">
                <ProtocolGuidePage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/rvt-guide/preview/:id" element={
              <ProtectedRoute permission="kbRVTAssistant" fallbackTitle="Knowledge Base 存取受限">
                <GuidePreviewPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/protocol-guide/preview/:id" element={
              <ProtectedRoute permission="kbProtocolAssistant" fallbackTitle="Knowledge Base 存取受限">
                <GuidePreviewPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/rvt-guide/markdown-create" element={
              <ProtectedRoute permission="kbRVTAssistant" fallbackTitle="Knowledge Base 存取受限">
                <MarkdownEditorPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/rvt-guide/markdown-edit/:id" element={
              <ProtectedRoute permission="kbRVTAssistant" fallbackTitle="Knowledge Base 存取受限">
                <MarkdownEditorPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/protocol-guide/markdown-create" element={
              <ProtectedRoute permission="kbProtocolAssistant" fallbackTitle="Knowledge Base 存取受限">
                <MarkdownEditorPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/protocol-guide/markdown-edit/:id" element={
              <ProtectedRoute permission="kbProtocolAssistant" fallbackTitle="Knowledge Base 存取受限">
                <MarkdownEditorPage />
              </ProtectedRoute>
            } />
            <Route path="/knowledge/ocr-storage-benchmark" element={
              <ProtectedRoute permission="kbAIOCR" fallbackTitle="Knowledge Base 存取受限">
                <OcrStorageBenchmarkPage />
              </ProtectedRoute>
            } />
            <Route path="/know-issue-chat" element={
              <ProtectedRoute permission="webProtocolRAG" fallbackTitle="Protocol RAG 存取受限" fallbackMessage="您需要 Protocol RAG 權限才能使用此功能">
                <KnowIssueChatPage collapsed={collapsed} />
              </ProtectedRoute>
            } />
            <Route path="/log-analyze-chat" element={
              <ProtectedRoute permission="webAIOCR" fallbackTitle="AI OCR 存取受限" fallbackMessage="您需要 AI OCR 權限才能使用此功能">
                <LogAnalyzeChatPage collapsed={collapsed} />
              </ProtectedRoute>
            } />
            <Route path="/rvt-assistant-chat" element={<RvtAssistantChatPage collapsed={collapsed} />} />
            <Route path="/protocol-assistant-chat" element={
              <ProtectedRoute permission="webProtocolAssistant" fallbackTitle="Protocol Assistant 存取受限">
                <ProtocolAssistantChatPage collapsed={collapsed} />
              </ProtectedRoute>
            } />
            <Route path="/log-analyze" element={<LogAnalyzePage />} />
            <Route path="/admin/test-class-management" element={<TestClassManagementPage />} />
            <Route path="/admin/user-management" element={<IntegratedUserManagementPage />} />
            <Route path="/admin/threshold-settings" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Threshold 設定存取受限">
                <ThresholdSettingsPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/system-logs" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="系統日誌存取受限">
                <SystemLogViewerPage />
              </ProtectedRoute>
            } />
            <Route path="/admin/rvt-analytics" element={<UnifiedAnalyticsPage />} />
            <Route path="/admin/analytics" element={<UnifiedAnalyticsPage />} />

            {/* Benchmark 測試系統（需要管理員權限） */}
            <Route path="/benchmark/dashboard" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <BenchmarkDashboardPage />
              </ProtectedRoute>
            } />
            {/* Unified Test Cases - 統一測試案例管理 */}
            <Route path="/benchmark/test-cases" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <UnifiedTestCasePage defaultTab="protocol" />
              </ProtectedRoute>
            } />
            {/* VSA Test Cases - 導向統一頁面的 VSA Tab */}
            <Route path="/benchmark/dify/test-cases" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <UnifiedTestCasePage defaultTab="vsa" />
              </ProtectedRoute>
            } />
            {/* ✅ Test Execution 路由已移除，統一使用 Batch Test */}
            {/* <Route path="/benchmark/test-execution" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <BenchmarkTestExecutionPage />
              </ProtectedRoute>
            } /> */}
            <Route path="/benchmark/batch-test" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <BatchTestExecutionPage />
              </ProtectedRoute>
            } />
            <Route path="/benchmark/batch-history" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <BatchTestHistoryPage />
              </ProtectedRoute>
            } />
            <Route path="/benchmark/comparison/:batchId" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
                <BatchComparisonPage />
              </ProtectedRoute>
            } />

            {/* Dify Benchmark 測試系統（需要管理員權限） */}
            <Route path="/dify-benchmark/versions" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyVersionManagementPage />
              </ProtectedRoute>
            } />
            <Route path="/benchmark/dify/versions" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyVersionManagementPage />
              </ProtectedRoute>
            } />

            <Route path="/dify-benchmark/test-cases" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyTestCasePage />
              </ProtectedRoute>
            } />
            <Route path="/benchmark/dify/test-cases" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyTestCasePage />
              </ProtectedRoute>
            } />

            {/* Dify 測試歷史 */}
            <Route path="/benchmark/dify/history" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyTestHistoryPage />
              </ProtectedRoute>
            } />
            <Route path="/dify-benchmark/history" element={
              <ProtectedRoute permission="isStaff" fallbackTitle="Dify Benchmark 系統存取受限">
                <DifyTestHistoryPage />
              </ProtectedRoute>
            } />

            {/* 🧪 開發工具 - Markdown 測試頁面（所有用戶可訪問） */}
            <Route path="/dev/markdown-test" element={<DevMarkdownTestPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
