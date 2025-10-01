import React, { useState } from 'react';
import {
  Card,
  Space,
  Typography,
  Tabs,
  ConfigProvider,
  Alert
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

  // 定義標籤頁配置 - 使用反白效果
  const tabItems = [
    {
      key: 'protocol-rag',
      label: (
        <Space size={8}>
          <DatabaseOutlined style={{ fontSize: '16px' }} />
          <span>Protocol RAG TestClass</span>
        </Space>
      ),
      children: (
        <TestClassTable 
          apiEndpoint="/api/test-classes/"
          title="Protocol RAG TestClass 管理"
          entityName="Protocol RAG TestClass"
          className="TestClass"
        />
      ),
    },
    {
      key: 'ocr',
      label: (
        <Space size={8}>
          <ScanOutlined style={{ fontSize: '16px' }} />
          <span>AI OCR TestClass</span>
        </Space>
      ),
      children: (
        <TestClassTable 
          apiEndpoint="/api/ocr-test-classes/"
          title="AI OCR TestClass 管理"
          entityName="AI OCR TestClass"
          className="TestClass"
        />
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space size={16}>
            <ExperimentOutlined style={{ 
              color: '#1890ff', 
              fontSize: '20px' 
            }} />
            <Title level={4} style={{ margin: 0 }}>
              TestClass 統一管理平台
            </Title>
          </Space>
        }
        styles={{ body: { padding: '16px' } }}
        style={{
          borderRadius: '12px',
          overflow: 'hidden'
        }}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          size="large"
          items={tabItems}
          style={{ 
            minHeight: '500px',
          }}
          tabBarStyle={{
            margin: '0 0 20px 0',
            background: 'transparent'
          }}
          tabBarGutter={8}
        />
      </Card>
      
      {/* 強化反白效果的自定義樣式 */}
      <style>{`
        /* 選中的標籤：強制藍底白字 */
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active {
          background: #1890ff !important;
          color: #ffffff !important;
          border: 2px solid #1890ff !important;
          box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4) !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active .ant-tabs-tab-btn {
          color: #ffffff !important;
          font-weight: bold !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active .anticon {
          color: #ffffff !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active span {
          color: #ffffff !important;
        }
        
        /* 未選中的標籤：白底深色字 */
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:not(.ant-tabs-tab-active) {
          background: #ffffff !important;
          color: #595959 !important;
          border: 1px solid #d9d9d9 !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:not(.ant-tabs-tab-active) .ant-tabs-tab-btn {
          color: #595959 !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:not(.ant-tabs-tab-active) .anticon {
          color: #8c8c8c !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:not(.ant-tabs-tab-active) span {
          color: #595959 !important;
        }
        
        /* 懸停效果：淺藍底 */
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:hover:not(.ant-tabs-tab-active) {
          background: #e6f7ff !important;
          border-color: #91d5ff !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:hover:not(.ant-tabs-tab-active) .ant-tabs-tab-btn {
          color: #1890ff !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:hover:not(.ant-tabs-tab-active) .anticon {
          color: #1890ff !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:hover:not(.ant-tabs-tab-active) span {
          color: #1890ff !important;
        }
        
        /* Tab 的基本樣式 */
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab {
          padding: 14px 24px !important;
          border-radius: 8px 8px 0 0 !important;
          margin-right: 6px !important;
          font-size: 15px !important;
          transition: all 0.3s ease !important;
          min-height: 48px !important;
          display: flex !important;
          align-items: center !important;
        }
        
        /* 確保所有子元素都繼承顏色 */
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab-active * {
          color: #ffffff !important;
        }
        
        .ant-tabs-card > .ant-tabs-nav .ant-tabs-tab:not(.ant-tabs-tab-active) * {
          color: inherit !important;
        }
      `}</style>
    </div>
  );
};

export default TestClassManagementPage;