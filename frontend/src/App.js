import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout, Card, Typography, Space, Button, Row, Col, Alert, Tag } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined,
  ApiOutlined,
  DatabaseOutlined,
  ContainerOutlined,
  SettingOutlined
} from '@ant-design/icons';
import Sidebar from './components/Sidebar';
import TopHeader from './components/TopHeader';
import './App.css';

const { Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function App() {
  const [collapsed, setCollapsed] = useState(false);
  const [selectedKey, setSelectedKey] = useState('dashboard');
  const [apiStatus, setApiStatus] = useState('Loading...');
  const [apiData, setApiData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 測試 Django API 連線
    const testAPI = async () => {
      setLoading(true);
      try {
        const response = await axios.get('/api/');
        setApiStatus('Connected');
        setApiData(response.data);
      } catch (error) {
        console.log('API Error:', error);
        if (error.response?.status === 403) {
          setApiStatus('API Available (Authentication Required)');
          setApiData({ message: 'API is running but requires authentication' });
        } else if (error.response?.status === 401) {
          setApiStatus('API Available (Unauthorized)');
          setApiData({ message: 'API is running but user needs to login' });
        } else if (error.response?.status === 400) {
          setApiStatus('API Available (Bad Request)');
          setApiData({ message: 'API is running but request format needs adjustment' });
        } else {
          setApiStatus('Connection Failed');
          setApiData({ 
            error: `Request failed with status code ${error.response?.status || 'unknown'}`,
            message: error.message 
          });
        }
      } finally {
        setLoading(false);
      }
    };

    testAPI();
  }, []);

  const getStatusColor = (status) => {
    if (status === 'Connected' || status.includes('Available')) {
      return 'success';
    }
    if (status === 'Loading...') {
      return 'processing';
    }
    return 'error';
  };

  const getStatusIcon = (status) => {
    if (status === 'Connected' || status.includes('Available')) {
      return <CheckCircleOutlined />;
    }
    if (status === 'Loading...') {
      return <ExclamationCircleOutlined />;
    }
    return <CloseCircleOutlined />;
  };

  const handleMenuSelect = ({ key }) => {
    setSelectedKey(key);
  };

  const toggleSidebar = () => {
    setCollapsed(!collapsed);
  };





  const renderContent = () => {
    switch (selectedKey) {
      case 'dashboard':
        return (
          <div style={{ padding: 24 }}>
            <Card>
              <Title level={3}>歡迎使用 IA 系統</Title>
              <Paragraph>請從左側選單選擇功能。</Paragraph>
            </Card>
          </div>
        );

      case 'monitoring':
        return (
          <div style={{ padding: 24 }}>
            <Space direction="vertical" size="large" style={{ width: '100%' }}>
              {/* 系統狀態 */}
              <Card title={<><ApiOutlined /> 系統狀態</>} loading={loading}>
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={12} md={8}>
                    <Card size="small">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>Django API</Text>
                        <Tag 
                          color={getStatusColor(apiStatus)} 
                          icon={getStatusIcon(apiStatus)}
                          style={{ width: '100%', textAlign: 'center' }}
                        >
                          {apiStatus}
                        </Tag>
                      </Space>
                    </Card>
                  </Col>
                  
                  <Col xs={24} sm={12} md={8}>
                    <Card size="small">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>React Frontend</Text>
                        <Tag color="success" icon={<CheckCircleOutlined />} style={{ width: '100%', textAlign: 'center' }}>
                          Running (Port 3000)
                        </Tag>
                      </Space>
                    </Card>
                  </Col>
                  
                  <Col xs={24} sm={12} md={8}>
                    <Card size="small">
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Text strong>PostgreSQL</Text>
                        <Tag color="success" icon={<CheckCircleOutlined />} style={{ width: '100%', textAlign: 'center' }}>
                          Available (Port 5432)
                        </Tag>
                      </Space>
                    </Card>
                  </Col>
                </Row>
                
                {apiData && (
                  <div style={{ marginTop: 16 }}>
                    <Alert
                      message="API 回應資料"
                      description={
                        <pre style={{ 
                          background: '#f6f8fa', 
                          padding: 12, 
                          borderRadius: 4,
                          fontSize: 12,
                          maxHeight: 200,
                          overflow: 'auto'
                        }}>
                          {JSON.stringify(apiData, null, 2)}
                        </pre>
                      }
                      type="info"
                      showIcon
                    />
                  </div>
                )}
              </Card>

              {/* 可用服務 */}
              <Card title={<><SettingOutlined /> 可用服務</>}>
                <Row gutter={[16, 16]}>
                  <Col xs={24} sm={12} md={6}>
                    <Button 
                      type="primary" 
                      icon={<SettingOutlined />}
                      block
                      href="/admin/" 
                      target="_blank"
                    >
                      Django Admin
                    </Button>
                  </Col>
                  
                  <Col xs={24} sm={12} md={6}>
                    <Button 
                      type="default" 
                      icon={<ApiOutlined />}
                      block
                      href="/api/" 
                      target="_blank"
                    >
                      API 端點
                    </Button>
                  </Col>
                  
                  <Col xs={24} sm={12} md={6}>
                    <Button 
                      type="default" 
                      icon={<DatabaseOutlined />}
                      block
                      href="http://localhost:9090" 
                      target="_blank"
                    >
                      資料庫管理 (Adminer)
                    </Button>
                  </Col>
                  
                  <Col xs={24} sm={12} md={6}>
                    <Button 
                      type="default" 
                      icon={<ContainerOutlined />}
                      block
                      href="http://localhost:9000" 
                      target="_blank"
                    >
                      容器管理 (Portainer)
                    </Button>
                  </Col>
                </Row>
              </Card>
            </Space>
          </div>
        );

      default:
        return (
          <div style={{ padding: 24 }}>
            <Card>
              <Title level={3}>{selectedKey}</Title>
              <Paragraph>此功能正在開發中，敬請期待。</Paragraph>
            </Card>
          </div>
        );
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sidebar 
        collapsed={collapsed}
        onCollapse={toggleSidebar}
        selectedKey={selectedKey}
        onMenuSelect={handleMenuSelect}
      />
      
      <Layout style={{ marginLeft: collapsed ? 80 : 250, transition: 'margin-left 0.2s' }}>
        <TopHeader collapsed={collapsed} onToggleSidebar={toggleSidebar} />
        
        <Content style={{ 
          marginTop: 64,
          background: '#f5f5f5',
          minHeight: 'calc(100vh - 64px)',
          overflow: 'auto'
        }}>
          {renderContent()}
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;