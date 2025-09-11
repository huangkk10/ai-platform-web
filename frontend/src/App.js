import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Layout, Card, Typography, Space, Tag, Divider, Button, Row, Col, Alert } from 'antd';
import { 
  CheckCircleOutlined, 
  ExclamationCircleOutlined, 
  CloseCircleOutlined,
  ApiOutlined,
  DatabaseOutlined,
  ContainerOutlined,
  SettingOutlined 
} from '@ant-design/icons';
import './App.css';

const { Header, Content } = Layout;
const { Title, Paragraph, Text } = Typography;

function App() {
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

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 50px' }}>
        <Title level={2} style={{ color: '#fff', margin: '16px 0', float: 'left' }}>
          🚀 AI Platform
        </Title>
      </Header>
      
      <Content style={{ padding: '50px', background: '#f0f2f5' }}>
        <div style={{ maxWidth: 1200, margin: '0 auto' }}>
          <Space direction="vertical" size="large" style={{ width: '100%' }}>
            
            {/* 歡迎區域 */}
            <Card>
              <Title level={1} style={{ textAlign: 'center', marginBottom: 16 }}>
                歡迎來到 AI Platform 🎉
              </Title>
              <Paragraph style={{ textAlign: 'center', fontSize: 16 }}>
                基於 Docker 的全端 AI 平台，整合 React + Django + PostgreSQL
              </Paragraph>
            </Card>

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

            {/* 開發資訊 */}
            <Card title={<><ContainerOutlined /> 開發資訊</>}>
              <Row gutter={[16, 16]}>
                <Col xs={24} md={12}>
                  <Title level={4}>🖥️ 前端服務</Title>
                  <ul>
                    <li><Text code>React Frontend</Text>: Port 3000</li>
                    <li><Text code>Nginx Proxy</Text>: Port 80/443</li>
                  </ul>
                </Col>
                
                <Col xs={24} md={12}>
                  <Title level={4}>⚙️ 後端服務</Title>
                  <ul>
                    <li><Text code>Django Backend</Text>: Port 8000</li>
                    <li><Text code>PostgreSQL DB</Text>: Port 5432</li>
                  </ul>
                </Col>
              </Row>
              
              <Divider />
              
              <Alert
                message="🎉 Ant Design 已成功整合！"
                description="現在你可以使用 antd 的所有組件來建構漂亮的用戶界面。"
                type="success"
                showIcon
              />
            </Card>

          </Space>
        </div>
      </Content>
    </Layout>
  );
}

export default App;