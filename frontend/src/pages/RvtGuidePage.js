import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  message,
  Input,
  Tooltip,
  Select,
  Row,
  Col,
  Modal
} from 'antd';
import { useNavigate } from 'react-router-dom';
import { 
  FileTextOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  EyeOutlined,
  ToolOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const RvtGuidePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const navigate = useNavigate();
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState(null);
  const [selectedMainCategory, setSelectedMainCategory] = useState('');

  // RVT 分類選項 - 對應資料庫的 main_category
  const mainCategoryOptions = [
    { value: 'system_architecture', label: '系統架構', color: 'blue' },
    { value: 'environment_setup', label: '環境準備', color: 'green' },
    { value: 'configuration_management', label: '配置管理', color: 'orange' },
    { value: 'test_case_management', label: '測項管理', color: 'purple' },
    { value: 'operation_flow', label: '操作流程', color: 'cyan' },
    { value: 'troubleshooting', label: '故障排除', color: 'red' },
    { value: 'contact_support', label: '聯絡支援', color: 'magenta' }
  ];

  // 問題類型選項
  const questionTypeOptions = [
    { value: 'operation_guide', label: '操作指南', color: 'blue' },
    { value: 'parameter_explanation', label: '參數說明', color: 'green' },
    { value: 'troubleshooting', label: '故障排除', color: 'red' },
    { value: 'concept_explanation', label: '概念說明', color: 'purple' }
  ];








  // 表格欄位定義 - 根據用戶需求調整：查看欄位在最左邊，顯示問題類型，移除 document_name
  const columns = [
    {
      title: '查看',
      key: 'view',
      width: 80,
      fixed: 'left',
      render: (_, record) => (
        <Button 
          icon={<EyeOutlined />}
          size="small"
          type="text"
          onClick={() => handleViewDetail(record)}
          title="查看詳細內容"
          style={{ color: '#1890ff' }}
        />
      ),
    },
    {
      title: '標題',
      dataIndex: 'title',
      key: 'title',
      width: 250,
      fixed: 'left',
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <Tooltip title={text}>
          <Text strong style={{ cursor: 'help' }} ellipsis>
            {text}
          </Text>
        </Tooltip>
      ),
      sorter: (a, b) => a.title.localeCompare(b.title),
    },
    {
      title: '主分類',
      dataIndex: 'main_category',
      key: 'main_category',
      width: 120,
      align: 'center',
      render: (mainCategory, record) => {
        const categoryOpt = mainCategoryOptions.find(opt => opt.value === mainCategory);
        return (
          <Tag color={categoryOpt?.color || 'default'}>
            {record.main_category_display || categoryOpt?.label || mainCategory}
          </Tag>
        );
      },
      filters: mainCategoryOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.main_category === value,
    },
    {
      title: '問題類型',
      dataIndex: 'question_type',
      key: 'question_type',
      width: 110,
      align: 'center',
      render: (questionType, record) => {
        const typeOpt = questionTypeOptions.find(opt => opt.value === questionType);
        return (
          <Tag color={typeOpt?.color || 'default'}>
            {record.question_type_display || typeOpt?.label || questionType}
          </Tag>
        );
      },
      filters: questionTypeOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.question_type === value,
    },
    {
      title: '建立時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 140,
      render: (text) => dayjs(text).format('YYYY-MM-DD HH:mm'),
      sorter: (a, b) => dayjs(a.created_at).unix() - dayjs(b.created_at).unix(),
      defaultSortOrder: 'descend',
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Button
            icon={<EditOutlined />}
            size="small"
            type="text"
            onClick={() => navigate(`/knowledge/rvt-guide/edit/${record.id}`)}
            title="編輯"
          />
          {user?.is_staff && (
            <Button
              icon={<DeleteOutlined />}
              size="small"
              type="text"
              danger
              onClick={() => handleDelete(record)}
              title="刪除"
            />
          )}
        </Space>
      ),
    },
  ];

  // 獲取指導文檔列表
  const fetchGuides = useCallback(async () => {
    if (!initialized || !isAuthenticated) return;
    
    setLoading(true);
    try {
      const response = await axios.get('/api/rvt-guides/');
      setGuides(response.data.results || response.data);
    } catch (error) {
      console.error('獲取 RVT Guide 資料失敗:', error);
      message.error('獲取資料失敗');
    } finally {
      setLoading(false);
    }
  }, [initialized, isAuthenticated]);

  useEffect(() => {
    if (initialized && isAuthenticated) {
      fetchGuides();
    }
  }, [initialized, isAuthenticated, fetchGuides]);

  // 處理查看詳細內容
  const handleViewDetail = async (record) => {
    try {
      // 發送單獨的 API 請求獲取完整資料
      const response = await axios.get(`/api/rvt-guides/${record.id}/`);
      setSelectedGuide(response.data);
      setDetailModalVisible(true);
    } catch (error) {
      console.error('獲取詳細資料失敗:', error);
      message.error('獲取詳細資料失敗');
    }
  };

  // 處理新增/編輯
  // 處理刪除
  const handleDelete = async (record) => {
    if (!user?.is_staff) {
      message.error('您沒有權限執行此操作');
      return;
    }

    Modal.confirm({
      title: '確認刪除',
      content: `確定要刪除指導文檔 "${record.title}" 嗎？`,
      okText: '確認',
      cancelText: '取消',
      onOk: async () => {
        try {
          await axios.delete(`/api/rvt-guides/${record.id}/`);
          message.success('刪除成功');
          fetchGuides();
        } catch (error) {
          console.error('刪除失敗:', error);
          message.error('刪除失敗');
        }
      },
    });
  };

  // 如果用戶未認證，顯示登入提示
  if (!initialized || authLoading) {
    return <div>載入中...</div>;
  }

  if (!isAuthenticated) {
    return (
      <Card title="RVT Assistant 知識庫" style={{ margin: '20px' }}>
        <p>請先登入以查看 RVT Assistant 知識庫內容。</p>
      </Card>
    );
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* 主要內容 */}
      <Card
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ToolOutlined />
            <Title level={4} style={{ margin: 0 }}>RVT Assistant 知識庫</Title>
          </div>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                fetchGuides();
              }}
              loading={loading}
            >
              重新整理
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => navigate('/knowledge/rvt-guide/create')}
            >
              新增 User Guide
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={guides}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400, y: 600 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
            pageSize: 10,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          size="middle"
        />
      </Card>

      {/* 詳細內容 Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileTextOutlined style={{ color: '#1890ff' }} />
            <span>資料預覽</span>
            {selectedGuide && (
              <Tag color="blue" style={{ marginLeft: '8px' }}>
                {selectedGuide.title}
              </Tag>
            )}
          </div>
        }
        open={detailModalVisible}
        onCancel={() => {
          setDetailModalVisible(false);
          setSelectedGuide(null);
        }}
        footer={[
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              navigate(`/knowledge/rvt-guide/edit/${selectedGuide.id}`);
            }}
          >
            編輯指導文檔
          </Button>,
          <Button key="close" onClick={() => {
            setDetailModalVisible(false);
            setSelectedGuide(null);
          }}>
            關閉
          </Button>
        ]}
        width={900}
      >
        {selectedGuide && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '0 4px' }}>
            {/* 基本信息 */}
            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e9ecef'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
                📝 基本信息
              </Title>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <strong>📂 標題：</strong>
                  <span style={{ marginLeft: '8px' }}>{selectedGuide.title}</span>
                </div>
                <div>
                  <strong>🏷️ 主分類：</strong>
                  <Tag 
                    color={mainCategoryOptions.find(opt => opt.value === selectedGuide.main_category)?.color || 'blue'}
                    style={{ marginLeft: '8px' }}
                  >
                    {selectedGuide.main_category_display}
                  </Tag>
                </div>

                <div>
                  <strong>🔄 問題類型：</strong>
                  <Tag 
                    color={questionTypeOptions.find(opt => opt.value === selectedGuide.question_type)?.color || 'green'}
                    style={{ marginLeft: '8px' }}
                  >
                    {selectedGuide.question_type_display}
                  </Tag>
                </div>



                <div>
                  <strong>📅 建立時間：</strong>
                  <span style={{ marginLeft: '8px' }}>
                    {dayjs(selectedGuide.created_at).format('YYYY-MM-DD HH:mm:ss')}
                  </span>
                </div>
                <div>
                  <strong>🔄 更新時間：</strong>
                  <span style={{ marginLeft: '8px' }}>
                    {dayjs(selectedGuide.updated_at).format('YYYY-MM-DD HH:mm:ss')}
                  </span>
                </div>
              </div>
            </div>

            {/* 文檔內容 */}
            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#e6f7ff',
              borderRadius: '8px',
              border: '1px solid #91d5ff'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
                📄 文檔內容
              </Title>
              <div style={{ 
                backgroundColor: 'white',
                padding: '16px',
                borderRadius: '6px',
                border: '1px solid #f5f5f5',
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word',
                fontSize: '14px',
                lineHeight: '1.8',
                minHeight: '200px',
                maxHeight: '400px',
                overflowY: 'auto'
              }}>
                {selectedGuide.content || '無內容'}
              </div>
            </div>

            {/* 完整分類路徑 */}
            {selectedGuide.full_category_name && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#f6ffed',
                borderRadius: '8px',
                border: '1px solid #b7eb8f'
              }}>
                <Title level={4} style={{ margin: '0 0 12px 0', color: '#52c41a' }}>
                  📍 分類路徑
                </Title>
                <div style={{ 
                  backgroundColor: 'white',
                  padding: '12px',
                  borderRadius: '6px',
                  border: '1px solid #f5f5f5',
                  fontSize: '14px'
                }}>
                  {selectedGuide.full_category_name}
                </div>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default RvtGuidePage;