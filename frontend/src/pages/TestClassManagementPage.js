import React, { useState } from 'react';
import {
  Card,
  Space,
  Typography,
  Tabs,
  Badge
} from 'antd';
import {
  ExperimentOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import TestClassTable from '../components/TestClassTable';
import '../styles/EnhancedTabs.css';

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

  // 定義標籤頁配置 - 增強視覺效果
  const tabItems = [
    {
      key: 'protocol-rag',
      label: (
        <Space size={12}>
          <Badge 
            status={activeTab === 'protocol-rag' ? 'processing' : 'default'} 
            style={{ marginRight: 4 }}
          />
          <MessageOutlined style={{ 
            color: activeTab === 'protocol-rag' ? '#1890ff' : '#8c8c8c',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }} />
          <span style={{ 
            fontWeight: activeTab === 'protocol-rag' ? '600' : 'normal',
            color: activeTab === 'protocol-rag' ? '#1890ff' : '#595959',
            fontSize: '15px',
            transition: 'all 0.3s ease'
          }}>
            Protocol RAG TestClass
          </span>
          {activeTab === 'protocol-rag' && (
            <span style={{
              background: '#1890ff',
              color: 'white',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 'bold',
              marginLeft: '8px'
            }}>
              ACTIVE
            </span>
          )}
        </Space>
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
        <Space size={12}>
          <Badge 
            status={activeTab === 'ocr' ? 'success' : 'default'} 
            style={{ marginRight: 4 }}
          />
          <BarChartOutlined style={{ 
            color: activeTab === 'ocr' ? '#52c41a' : '#8c8c8c',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }} />
          <span style={{ 
            fontWeight: activeTab === 'ocr' ? '600' : 'normal',
            color: activeTab === 'ocr' ? '#52c41a' : '#595959',
            fontSize: '15px',
            transition: 'all 0.3s ease'
          }}>
            AI OCR TestClass
          </span>
          {activeTab === 'ocr' && (
            <span style={{
              background: '#52c41a',
              color: 'white',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 'bold',
              marginLeft: '8px'
            }}>
              ACTIVE
            </span>
          )}
        </Space>
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
        <Space size={12}>
          <Badge 
            status={activeTab === 'rvt' ? 'warning' : 'default'} 
            style={{ marginRight: 4 }}
          />
          <FileTextOutlined style={{ 
            color: activeTab === 'rvt' ? '#722ed1' : '#8c8c8c',
            fontSize: '16px',
            transition: 'all 0.3s ease'
          }} />
          <span style={{ 
            fontWeight: activeTab === 'rvt' ? '600' : 'normal',
            color: activeTab === 'rvt' ? '#722ed1' : '#595959',
            fontSize: '15px',
            transition: 'all 0.3s ease'
          }}>
            RVT TestClass
          </span>
          {activeTab === 'rvt' && (
            <span style={{
              background: '#722ed1',
              color: 'white',
              padding: '2px 8px',
              borderRadius: '12px',
              fontSize: '11px',
              fontWeight: 'bold',
              marginLeft: '8px'
            }}>
              COMING SOON
            </span>
          )}
        </Space>
      ),
      children: (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: 'linear-gradient(135deg, #f9f0ff 0%, #fafafa 100%)',
          borderRadius: '8px',
          border: '2px dashed #722ed1',
          position: 'relative'
        }}>
          <div style={{
            position: 'absolute',
            top: '20px',
            right: '20px',
            background: '#722ed1',
            color: 'white',
            padding: '4px 12px',
            borderRadius: '12px',
            fontSize: '12px',
            fontWeight: 'bold'
          }}>
            開發中
          </div>
          <FileTextOutlined style={{ 
            fontSize: '48px', 
            color: '#722ed1', 
            marginBottom: '16px',
            opacity: 0.7
          }} />
          <Title level={4} style={{ color: '#722ed1' }}>RVT TestClass 管理</Title>
          <Text type="secondary">此功能正在開發中，敬請期待...</Text>
        </div>
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