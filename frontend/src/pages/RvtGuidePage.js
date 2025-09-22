import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  Select, 
  Tag, 
  Space, 
  Typography,
  message,
  Tooltip,
  Statistic,
  Row,
  Col,
  Rate,
  Divider
} from 'antd';
import { 
  FileTextOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  EyeOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  BarChartOutlined,
  StarOutlined,
  LikeOutlined,
  ToolOutlined,
  BookOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Paragraph, Text } = Typography;
const { Option } = Select;
const { TextArea } = Input;

const RvtGuidePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const [guides, setGuides] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedGuide, setSelectedGuide] = useState(null);
  const [editingGuide, setEditingGuide] = useState(null);
  const [form] = Form.useForm();
  const [statistics, setStatistics] = useState({});

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

  // 狀態選項
  const statusOptions = [
    { value: 'draft', label: '草稿', color: 'default' },
    { value: 'published', label: '已發布', color: 'green' },
    { value: 'archived', label: '已歸檔', color: 'gray' }
  ];

  // 目標用戶選項
  const targetUserOptions = [
    { value: 'beginner', label: '初學者', color: 'green' },
    { value: 'advanced', label: '進階使用者', color: 'blue' },
    { value: 'admin', label: '系統管理員', color: 'orange' },
    { value: 'all', label: '所有用戶', color: 'purple' }
  ];

  // 表格欄位定義
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
      render: (text, record) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Tooltip title={text}>
              <Text strong style={{ cursor: 'help', maxWidth: '200px' }} ellipsis>
                {text}
              </Text>
            </Tooltip>
          </div>
          <div style={{ marginTop: '4px' }}>
            <Tag 
              color={mainCategoryOptions.find(opt => opt.value === record.main_category)?.color || 'default'} 
              size="small"
            >
              {record.main_category_display}
            </Tag>
          </div>
        </div>
      ),
      sorter: (a, b) => a.title.localeCompare(b.title),
    },
    {
      title: '分類',
      dataIndex: 'main_category',
      key: 'main_category',
      width: 120,
      align: 'center',
      render: (category, record) => (
        <Tag color={mainCategoryOptions.find(opt => opt.value === category)?.color || 'default'}>
          {record.main_category_display}
        </Tag>
      ),
      filters: mainCategoryOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.main_category === value,
    },
    {
      title: '子分類',
      dataIndex: 'sub_category_display',
      key: 'sub_category',
      width: 150,
      ellipsis: true,
      render: (text) => text || '-',
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center',
      render: (status, record) => {
        const statusOpt = statusOptions.find(opt => opt.value === status);
        return (
          <Tag color={statusOpt?.color || 'default'}>
            {record.status_display}
          </Tag>
        );
      },
      filters: statusOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.status === value,
    },
    {
      title: '問題類型',
      dataIndex: 'question_type',
      key: 'question_type',
      width: 120,
      align: 'center',
      render: (questionType, record) => {
        const typeOpt = questionTypeOptions.find(opt => opt.value === questionType);
        return (
          <Tag color={typeOpt?.color || 'default'}>
            {record.question_type_display}
          </Tag>
        );
      },
      filters: questionTypeOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.question_type === value,
    },
    {
      title: '目標用戶',
      dataIndex: 'target_user',
      key: 'target_user',
      width: 120,
      align: 'center',
      render: (targetUser, record) => {
        const userOpt = targetUserOptions.find(opt => opt.value === targetUser);
        return (
          <Tag color={userOpt?.color || 'default'}>
            {record.target_user_display}
          </Tag>
        );
      },
      filters: targetUserOptions.map(opt => ({ text: opt.label, value: opt.value })),
      onFilter: (value, record) => record.target_user === value,
    },
    {
      title: '版本',
      dataIndex: 'version',
      key: 'version',
      width: 80,
      align: 'center',
      render: (text) => text || '1.0',
    },
    {
      title: '文檔名稱',
      dataIndex: 'document_name',
      key: 'document_name',
      width: 150,
      ellipsis: true,
      render: (text) => text || '-',
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
            onClick={() => handleEdit(record)}
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
  const fetchGuides = async () => {
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
  };

  // 獲取統計資料
  const fetchStatistics = async () => {
    if (!initialized || !isAuthenticated) return;
    
    try {
      const response = await axios.get('/api/rvt-guides/statistics/');
      setStatistics(response.data);
    } catch (error) {
      console.error('獲取統計資料失敗:', error);
    }
  };

  useEffect(() => {
    if (initialized && isAuthenticated) {
      fetchGuides();
      fetchStatistics();
    }
  }, [initialized, isAuthenticated]);

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
  const handleEdit = (record = null) => {
    setEditingGuide(record);
    if (record) {
      form.setFieldsValue({
        ...record,
      });
    } else {
      form.resetFields();
    }
    setModalVisible(true);
  };

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
          fetchStatistics();
        } catch (error) {
          console.error('刪除失敗:', error);
          message.error('刪除失敗');
        }
      },
    });
  };

  // 處理表單提交
  const handleFormSubmit = async (values) => {
    try {
      const submitData = {
        ...values,
      };

      if (editingGuide) {
        await axios.put(`/api/rvt-guides/${editingGuide.id}/`, submitData);
        message.success('更新成功');
      } else {
        await axios.post('/api/rvt-guides/', submitData);
        message.success('新增成功');
      }

      setModalVisible(false);
      setEditingGuide(null);
      form.resetFields();
      fetchGuides();
      fetchStatistics();
    } catch (error) {
      console.error('操作失敗:', error);
      message.error('操作失敗');
    }
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
      {/* 統計卡片 */}
      {Object.keys(statistics).length > 0 && (
        <Row gutter={16} style={{ marginBottom: '20px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="總指導文檔"
                value={statistics.total_guides}
                prefix={<BookOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="已發布文檔"
                value={statistics.published_guides}
                prefix={<CheckCircleOutlined />}
                valueStyle={{ color: '#52c41a' }}
                suffix={`/ ${statistics.total_guides}`}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="精選文檔"
                value={statistics.featured_guides}
                prefix={<StarOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="發布率"
                value={statistics.publish_rate}
                suffix="%"
                prefix={<BarChartOutlined />}
                precision={1}
                valueStyle={{ 
                  color: statistics.publish_rate > 70 ? '#52c41a' : statistics.publish_rate > 40 ? '#faad14' : '#f5222d'
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

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
                fetchStatistics();
              }}
              loading={loading}
            >
              重新整理
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleEdit()}
            >
              新增指導文檔
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

      {/* 新增/編輯表單 Modal */}
      <Modal
        title={editingGuide ? '編輯指導文檔' : '新增指導文檔'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingGuide(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleFormSubmit}
          preserve={false}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="title"
                label="標題"
                rules={[{ required: true, message: '請輸入標題' }]}
              >
                <Input placeholder="請輸入指導文檔標題" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="document_name"
                label="文檔名稱"
                rules={[{ required: true, message: '請輸入文檔名稱' }]}
              >
                <Input placeholder="請輸入文檔的唯一名稱" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="main_category"
                label="主分類"
                rules={[{ required: true, message: '請選擇主分類' }]}
              >
                <Select placeholder="請選擇主分類">
                  {mainCategoryOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="question_type"
                label="問題類型"
                rules={[{ required: true, message: '請選擇問題類型' }]}
              >
                <Select placeholder="請選擇問題類型">
                  {questionTypeOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="target_user"
                label="目標用戶"
                rules={[{ required: true, message: '請選擇目標用戶' }]}
              >
                <Select placeholder="請選擇目標用戶">
                  {targetUserOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="content"
            label="內容"
            rules={[{ required: true, message: '請輸入內容' }]}
          >
            <TextArea 
              rows={8} 
              placeholder="請輸入指導文檔內容" 
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="version"
                label="版本"
              >
                <Input placeholder="如：1.0" defaultValue="1.0" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="status"
                label="狀態"
                rules={[{ required: true, message: '請選擇狀態' }]}
              >
                <Select placeholder="請選擇狀態">
                  {statusOptions.map(option => (
                    <Option key={option.value} value={option.value}>
                      {option.label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item
                name="keywords"
                label="關鍵字"
              >
                <Input placeholder="用逗號分隔的關鍵字" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                {editingGuide ? '更新' : '新增'}
              </Button>
              <Button onClick={() => {
                setModalVisible(false);
                setEditingGuide(null);
                form.resetFields();
              }}>
                取消
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 詳細內容 Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <FileTextOutlined style={{ color: '#1890ff' }} />
            <span>資料預覽</span>
            {selectedGuide && (
              <Tag color="blue" style={{ marginLeft: '8px' }}>
                {selectedGuide.document_name}
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
          <Button key="close" onClick={() => {
            setDetailModalVisible(false);
            setSelectedGuide(null);
          }}>
            關閉
          </Button>,
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              handleEdit(selectedGuide);
            }}
          >
            編輯
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
                  <strong>📁 文檔名稱：</strong>
                  <span style={{ marginLeft: '8px' }}>{selectedGuide.document_name}</span>
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
                  <strong>📋 子分類：</strong>
                  <span style={{ marginLeft: '8px' }}>{selectedGuide.sub_category_display || '-'}</span>
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
                  <strong>👥 目標用戶：</strong>
                  <Tag 
                    color={targetUserOptions.find(opt => opt.value === selectedGuide.target_user)?.color || 'purple'}
                    style={{ marginLeft: '8px' }}
                  >
                    {selectedGuide.target_user_display}
                  </Tag>
                </div>
                <div>
                  <strong>📊 狀態：</strong>
                  <Tag 
                    color={statusOptions.find(opt => opt.value === selectedGuide.status)?.color || 'default'}
                    style={{ marginLeft: '8px' }}
                  >
                    {selectedGuide.status_display}
                  </Tag>
                </div>
                <div>
                  <strong>🔖 版本：</strong>
                  <span style={{ marginLeft: '8px' }}>{selectedGuide.version || '1.0'}</span>
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

            {/* 關鍵字 */}
            {selectedGuide.keywords_list && selectedGuide.keywords_list.length > 0 && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                backgroundColor: '#f9f0ff',
                borderRadius: '8px',
                border: '1px solid #d3adf7'
              }}>
                <Title level={4} style={{ margin: '0 0 12px 0', color: '#722ed1' }}>
                  🏷️ 關鍵字
                </Title>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                  {selectedGuide.keywords_list.map((keyword, index) => (
                    <Tag key={index} color="purple">
                      {keyword}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

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