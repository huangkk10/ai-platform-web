import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Typography, 
  Form, 
  Input, 
  Button, 
  Space, 
  Divider, 
  message,
  Row,
  Col,
  Alert,
  Progress,
  Statistic,
  Table,
  Tag,
  Switch,
  Spin,
  Tooltip,
  Badge
} from 'antd';
import {
  SettingOutlined, 
  LockOutlined, 
  UserOutlined,
  SafetyOutlined,
  DatabaseOutlined,
  CloudServerOutlined,
  MonitorOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  MemoryOutlined,
  HddOutlined,
  ApiOutlined,
  ContainerOutlined,
  QuestionCircleOutlined,
  FolderOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

const SettingsPage = () => {
  const { user } = useAuth();
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(false);

  // 獲取系統狀態
  const fetchSystemStatus = useCallback(async () => {
    setLoading(true);
    try {
      // 根據用戶權限選擇不同的 API
      const apiEndpoint = (user?.is_staff || user?.is_superuser) 
        ? '/api/system/simple-status/' 
        : '/api/system/basic-status/';
        
      const response = await axios.get(apiEndpoint);
      setSystemStatus(response.data);
    } catch (error) {
      console.error('獲取系統狀態失敗:', error);
      
      if (error.response?.status === 403) {
        // 權限不足，顯示基本信息
        setSystemStatus({
          status: 'limited',
          message: '權限不足，無法獲取詳細系統狀態',
          user_level: 'limited'
        });
        message.warning('權限不足，僅顯示基本系統狀態');
      } else {
        message.error('獲取系統狀態失敗');
        setSystemStatus({
          status: 'error',
          error: '無法獲取系統狀態'
        });
      }
    } finally {
      setLoading(false);
    }
  }, [user]);

  // 自動刷新
  useEffect(() => {
    if (user) {  // 只要用戶已登入就可以獲取狀態
      fetchSystemStatus();
      
      if (autoRefresh) {
        const interval = setInterval(fetchSystemStatus, 30000); // 30秒刷新
        return () => clearInterval(interval);
      }
    }
  }, [autoRefresh, user, fetchSystemStatus]);

  // 獲取狀態顏色
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#52c41a';
      case 'warning': return '#faad14';
      case 'error': return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  // 獲取狀態圖標
  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'warning': return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'error': return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      default: return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  // 容器狀態表格欄位
  const containerColumns = [
    {
      title: '容器名稱',
      dataIndex: 'name',
      key: 'name',
      render: (name) => (
        <Space>
          <ContainerOutlined style={{ color: '#1890ff' }} />
          <Text strong>{name}</Text>
        </Space>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={status === 'running' ? 'green' : 'red'}>
          {status === 'running' ? '運行中' : '已停止'}
        </Tag>
      ),
    },
    {
      title: '映像',
      dataIndex: 'image',
      key: 'image',
      render: (image) => <Text code>{image}</Text>,
    },
    {
      title: '創建時間',
      dataIndex: 'created',
      key: 'created',
      render: (created) => (
        <Text type="secondary">
          {dayjs(created).format('YYYY-MM-DD HH:mm')}
        </Text>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Space direction="vertical" size="large" style={{ width: '100%' }}>
        {/* 標題和控制項 */}
        <Card>
          <Row justify="space-between" align="middle">
            <Col>
              <Title level={3} style={{ margin: 0 }}>
                <MonitorOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
                系統狀態監控
              </Title>
              {!user?.is_staff && !user?.is_superuser && (
                <Text type="secondary" style={{ display: 'block', marginTop: '4px' }}>
                  基本模式 - 詳細監控功能需要管理員權限
                </Text>
              )}
            </Col>
            <Col>
              <Space>
                <Text>自動刷新：</Text>
                <Switch
                  checked={autoRefresh}
                  onChange={setAutoRefresh}
                  checkedChildren="開"
                  unCheckedChildren="關"
                />
                <Button
                  type="primary"
                  icon={<ReloadOutlined />}
                  onClick={fetchSystemStatus}
                  loading={loading}
                >
                  手動刷新
                </Button>
              </Space>
            </Col>
          </Row>
        </Card>

        {/* 系統整體狀態 */}
        {systemStatus && (
          <Card
            title={
              <Space>
                {getStatusIcon(systemStatus.status)}
                <Text strong>系統整體狀態</Text>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Badge
                  status={systemStatus.status === 'healthy' ? 'success' : 'error'}
                  text={
                    <Text strong style={{ fontSize: '16px' }}>
                      {systemStatus.status === 'healthy' ? '系統正常' : '需要注意'}
                    </Text>
                  }
                />
              </Col>
              <Col span={6}>
                <Text type="secondary">
                  最後更新：{dayjs(systemStatus.timestamp).format('HH:mm:ss')}
                </Text>
              </Col>
              <Col span={12}>
                <Text type="secondary">
                  服務器時間：{systemStatus.server_time}
                </Text>
              </Col>
            </Row>
            
            {/* 警告列表 */}
            {systemStatus.alerts && systemStatus.alerts.length > 0 && (
              <Alert
                message="系統警告"
                description={
                  <ul style={{ margin: 0, paddingLeft: '20px' }}>
                    {systemStatus.alerts.map((alert, index) => (
                      <li key={index}>{alert}</li>
                    ))}
                  </ul>
                }
                type="warning"
                showIcon
                style={{ marginTop: '16px' }}
              />
            )}
          </Card>
        )}

        {/* 資料庫狀態 */}
        {systemStatus?.services?.database && (
          <Card
            title={
              <Space>
                <DatabaseOutlined style={{ color: '#1890ff' }} />
                <Text strong>資料庫狀態</Text>
                {getStatusIcon(systemStatus.services.database.status)}
              </Space>
            }
          >
            {systemStatus.services.database.status === 'healthy' ? (
              <Row gutter={[16, 16]}>
                {systemStatus.database_stats ? (
                  // 管理員版本 - 顯示詳細統計
                  <>
                    <Col span={8}>
                      <Statistic
                        title="用戶總數"
                        value={systemStatus.database_stats?.users || 0}
                        prefix={<UserOutlined />}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="知識庫條目"
                        value={systemStatus.database_stats?.know_issues || 0}
                        prefix={<DatabaseOutlined />}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title="專案數量"
                        value={systemStatus.database_stats?.projects || 0}
                        prefix={<FolderOutlined />}
                      />
                    </Col>
                  </>
                ) : systemStatus.basic_stats ? (
                  // 基本版本 - 顯示帶說明的統計
                  <>
                    <Col span={8}>
                      <Statistic
                        title={
                          <Tooltip title={systemStatus.basic_stats.active_users?.description}>
                            <span>活躍用戶 <QuestionCircleOutlined style={{ color: '#1890ff' }} /></span>
                          </Tooltip>
                        }
                        value={systemStatus.basic_stats.active_users?.count || systemStatus.basic_stats.active_users || 0}
                        prefix={<UserOutlined />}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title={
                          <Tooltip title={systemStatus.basic_stats.total_know_issues?.description}>
                            <span>知識庫條目 <QuestionCircleOutlined style={{ color: '#1890ff' }} /></span>
                          </Tooltip>
                        }
                        value={systemStatus.basic_stats.total_know_issues?.count || systemStatus.basic_stats.total_know_issues || 0}
                        prefix={<DatabaseOutlined />}
                      />
                    </Col>
                    <Col span={8}>
                      <Statistic
                        title={
                          <Tooltip title={systemStatus.basic_stats.total_projects?.description}>
                            <span>專案數量 <QuestionCircleOutlined style={{ color: '#1890ff' }} /></span>
                          </Tooltip>
                        }
                        value={systemStatus.basic_stats.total_projects?.count || 0}
                        prefix={<FolderOutlined />}
                      />
                    </Col>
                  </>
                ) : (
                  <Col span={24}>
                    <Text>基本統計信息</Text>
                  </Col>
                )}
              </Row>
            ) : (
              <Alert
                message="資料庫連接錯誤"
                description={systemStatus.services.database.message || '資料庫連接失敗'}
                type="error"
                showIcon
              />
            )}
          </Card>
        )}

        {/* 系統資源狀態 - 只有管理員可見且 API 返回系統資源數據 */}
        {(user?.is_staff || user?.is_superuser) && systemStatus?.system && systemStatus.system.cpu_percent !== undefined && (
          <Card
            title={
              <Space>
                <CloudServerOutlined style={{ color: '#1890ff' }} />
                <Text strong>系統資源</Text>
                {getStatusIcon(systemStatus.system.status || 'healthy')}
              </Space>
            }
          >
            <Row gutter={[24, 24]} justify="center" align="middle">
              <Col span={8}>
                <Card 
                  size="small" 
                  style={{ 
                    textAlign: 'center', 
                    padding: '20px',
                    minHeight: '200px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ marginBottom: '16px' }}>
                    <Progress
                      type="circle"
                      percent={Math.round(systemStatus.system.cpu_percent || 0)}
                      format={(percent) => `${percent}%`}
                      strokeColor={percent => percent > 80 ? '#ff4d4f' : percent > 60 ? '#faad14' : '#52c41a'}
                      size={120}
                      strokeWidth={6}
                    />
                  </div>
                  <Text strong style={{ fontSize: '14px', lineHeight: '20px' }}>
                    CPU 使用率
                  </Text>
                </Card>
              </Col>
              <Col span={8}>
                <Card 
                  size="small" 
                  style={{ 
                    textAlign: 'center', 
                    padding: '20px',
                    minHeight: '200px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ marginBottom: '16px' }}>
                    <Progress
                      type="circle"
                      percent={Math.round(systemStatus.system.memory?.percent || 0)}
                      format={() => `${systemStatus.system.memory?.used || 0}GB`}
                      strokeColor={percent => percent > 80 ? '#ff4d4f' : percent > 60 ? '#faad14' : '#52c41a'}
                      size={120}
                      strokeWidth={6}
                    />
                  </div>
                  <Text strong style={{ fontSize: '14px', lineHeight: '20px' }}>
                    記憶體使用
                  </Text>
                  <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                    {systemStatus.system.memory?.total || 0}GB 總計
                  </Text>
                </Card>
              </Col>
              <Col span={8}>
                <Card 
                  size="small" 
                  style={{ 
                    textAlign: 'center', 
                    padding: '20px',
                    minHeight: '200px',
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center'
                  }}
                >
                  <div style={{ marginBottom: '16px' }}>
                    <Progress
                      type="circle"
                      percent={Math.round(systemStatus.system.disk?.percent || 0)}
                      format={() => `${systemStatus.system.disk?.used || 0}GB`}
                      strokeColor={percent => percent > 80 ? '#ff4d4f' : percent > 60 ? '#faad14' : '#52c41a'}
                      size={120}
                      strokeWidth={6}
                    />
                  </div>
                  <Text strong style={{ fontSize: '14px', lineHeight: '20px' }}>
                    磁碟使用
                  </Text>
                  <Text type="secondary" style={{ fontSize: '12px', marginTop: '4px' }}>
                    {systemStatus.system.disk?.total || 0}GB 總計
                  </Text>
                </Card>
              </Col>
            </Row>
          </Card>
        )}

        {/* 服務狀態 */}
        {systemStatus?.services && (
          <Card
            title={
              <Space>
                <CloudServerOutlined style={{ color: '#1890ff' }} />
                <Text strong>服務狀態</Text>
              </Space>
            }
          >
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Card size="small">
                  <Space>
                    {getStatusIcon(systemStatus.services.django?.status || 'unknown')}
                    <div>
                      <Text strong>Django API</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        REST API 服務 (8000)
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Space>
                    {getStatusIcon(systemStatus.services.database?.status || 'unknown')}
                    <div>
                      <Text strong>PostgreSQL</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        主資料庫
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Space>
                    {getStatusIcon(systemStatus.services.frontend?.status || 'unknown')}
                    <div>
                      <Text strong>React Frontend</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        前端服務 (3000)
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Space>
                    {getStatusIcon(systemStatus.services.nginx?.status || 'unknown')}
                    <div>
                      <Text strong>Nginx</Text>
                      <br />
                      <Text type="secondary" style={{ fontSize: '12px' }}>
                        反向代理 (80)
                      </Text>
                    </div>
                  </Space>
                </Card>
              </Col>
            </Row>
          </Card>
        )}

        {/* 載入中狀態 */}
        {loading && !systemStatus && (
          <Card style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <Text style={{ display: 'block', marginTop: '16px' }}>
              正在獲取系統狀態...
            </Text>
          </Card>
        )}

        {/* 錯誤狀態顯示 */}
        {systemStatus?.status === 'error' && (
          <Card>
            <Alert
              message="系統狀態獲取失敗"
              description={systemStatus.error}
              type="error"
              showIcon
            />
          </Card>
        )}

        {/* 權限限制提示 */}
        {systemStatus?.status === 'limited' && (
          <Card>
            <Alert
              message="權限限制"
              description={systemStatus.message}
              type="info"
              showIcon
            />
          </Card>
        )}
      </Space>
    </div>
  );
};

export default SettingsPage;