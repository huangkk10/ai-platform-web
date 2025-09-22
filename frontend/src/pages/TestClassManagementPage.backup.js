import React, { useState } from 'react';
import {
  Card,
  Space,
  Typography,
  Tabs,
  Badge,
  ConfigProvider,
  theme
} from 'antd';
import {
  ExperimentOutlined,
  DatabaseOutlined,
  ScanOutlined,
  RobotOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import TestClassTable from '../components/TestClassTable';

const { Title, Text } = Typography;

const TestClassManagementPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('protocol-rag');

  // 如果不是管理員，顯示權限錯誤
  if (!user?.is_staff && !user?.is_superuser) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Card>
          <Space direction="vertical" size="large">
            <ExperimentOutlined style={{ fontSize: '64px', color: '#ff4d4f' }} />
            <Title level={3}>權限不足</Title>
            <Text type="secondary">
              只有管理員才能訪問 TestClass 管理功能
            </Text>
          </Space>
        </Card>
      </div>
    );
  }

  // 定義標籤頁配置 - 使用 Ant Design 內建樣式
  const tabItems = [
    {
      key: 'protocol-rag',
      label: (
        <Badge.Ribbon 
          text={activeTab === 'protocol-rag' ? 'ACTIVE' : ''} 
          color="blue"
          style={{ display: activeTab === 'protocol-rag' ? 'block' : 'none' }}
        >
          <Space size={8}>
            <DatabaseOutlined style={{ 
              color: activeTab === 'protocol-rag' ? '#1890ff' : '#8c8c8c',
              fontSize: '18px'
            }} />
            <span style={{ 
              fontWeight: activeTab === 'protocol-rag' ? '600' : 'normal',
              fontSize: '16px'
            }}>
              Protocol RAG TestClass
            </span>
          </Space>
        </Badge.Ribbon>
      ),
      children: (
        <TestClassTable 
          apiEndpoint="/api/test-classes/"
          title="Protocol RAG TestClass 管理"
          entityName="Protocol RAG TestClass"
          className="Protocol TestClass"
        />
      ),
    },
    {
      key: 'ocr',
      label: (
        <Badge.Ribbon 
          text={activeTab === 'ocr' ? 'ACTIVE' : ''} 
          color="green"
          style={{ display: activeTab === 'ocr' ? 'block' : 'none' }}
        >
          <Space size={8}>
            <ScanOutlined style={{ 
              color: activeTab === 'ocr' ? '#52c41a' : '#8c8c8c',
              fontSize: '18px'
            }} />
            <span style={{ 
              fontWeight: activeTab === 'ocr' ? '600' : 'normal',
              fontSize: '16px'
            }}>
              AI OCR TestClass
            </span>
          </Space>
        </Badge.Ribbon>
      ),
      children: (
        <TestClassTable 
          apiEndpoint="/api/ocr-test-classes/"
          title="AI OCR TestClass 管理"
          entityName="AI OCR TestClass"
          className="OCR TestClass"
        />
      ),
    },
    {
      key: 'rvt',
      label: (
        <Badge.Ribbon 
          text={activeTab === 'rvt' ? 'COMING SOON' : ''} 
          color="purple"
          style={{ display: activeTab === 'rvt' ? 'block' : 'none' }}
        >
          <Space size={8}>
            <RobotOutlined style={{ 
              color: activeTab === 'rvt' ? '#722ed1' : '#8c8c8c',
              fontSize: '18px'
            }} />
            <span style={{ 
              fontWeight: activeTab === 'rvt' ? '600' : 'normal',
              fontSize: '16px'
            }}>
              RVT TestClass
            </span>
          </Space>
        </Badge.Ribbon>
      ),
      children: (
        <Card 
          style={{ 
            textAlign: 'center',
            background: 'linear-gradient(135deg, #f9f0ff 0%, #fafafa 100%)',
            border: '2px dashed #722ed1'
          }}
          bodyStyle={{ padding: '60px 20px' }}
        >
          <Badge.Ribbon text="開發中" color="purple">
            <Space direction="vertical" size={20}>
              <RobotOutlined style={{ 
                fontSize: '64px', 
                color: '#722ed1', 
                opacity: 0.7
              }} />
              <Title level={3} style={{ color: '#722ed1', margin: 0 }}>
                RVT TestClass 管理
              </Title>
              <Text type="secondary" style={{ fontSize: '16px' }}>
                此功能正在開發中，敬請期待...
              </Text>
            </Space>
          </Badge.Ribbon>
        </Card>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <ExperimentOutlined style={{ color: '#1890ff' }} />
            <span>TestClass 統一管理平台</span>
          </Space>
        }
        bodyStyle={{ padding: '0' }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="large"
          items={tabItems}
          style={{ 
            minHeight: '500px',
            padding: '16px' 
          }}
          tabBarStyle={{
            margin: '0',
            paddingLeft: '16px',
            paddingRight: '16px',
            background: 'linear-gradient(135deg, #f6f8fa 0%, #ffffff 100%)',
            borderBottom: '2px solid #e8e8e8',
            borderRadius: '8px 8px 0 0'
          }}
          tabBarGutter={8}
          // 自定義 Tab 樣式
          tabBarExtraContent={{
            right: (
              <div style={{ 
                padding: '8px 16px',
                color: '#8c8c8c',
                fontSize: '14px'
              }}>
                <Text type="secondary">
                  當前標籤: <Text strong style={{ color: '#1890ff' }}>
                    {tabItems.find(item => item.key === activeTab)?.label.props.children[1] || activeTab}
                  </Text>
                </Text>
              </div>
            )
          }}
          // 添加自定義 CSS 類名以進一步自定義樣式
          className="enhanced-tabs"
        />
      </Card>

      {/* 添加自定義 CSS 樣式 */}
      <style jsx>{`
        .enhanced-tabs .ant-tabs-tab {
          border-radius: 8px 8px 0 0 !important;
          border: 2px solid transparent !important;
          margin-right: 4px !important;
          padding: 12px 20px !important;
          transition: all 0.3s ease !important;
          background: #ffffff !important;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
        }
        
        .enhanced-tabs .ant-tabs-tab:hover {
          border-color: #d9d9d9 !important;
          transform: translateY(-1px) !important;
          box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
        }
        
        .enhanced-tabs .ant-tabs-tab-active {
          border-color: #1890ff !important;
          background: linear-gradient(135deg, #e6f7ff 0%, #ffffff 100%) !important;
          transform: translateY(-2px) !important;
          box-shadow: 0 6px 12px rgba(24,144,255,0.2) !important;
        }
        
        .enhanced-tabs .ant-tabs-tab-active .ant-tabs-tab-btn {
          color: #1890ff !important;
          font-weight: bold !important;
        }
        
        .enhanced-tabs .ant-tabs-content-holder {
          background: #ffffff !important;
          border-radius: 0 0 8px 8px !important;
          box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
        }
        
        .enhanced-tabs .ant-tabs-tabpane {
          padding: 24px !important;
        }
      `}</style>
    </div>
  );
};

export default TestClassManagementPage;