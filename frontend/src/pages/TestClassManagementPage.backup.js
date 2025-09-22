import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  message,
  Popconfirm,
  Tag,
  Typography,
  Divider,
  Tabs
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SearchOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  MessageOutlined,
  FileTextOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import TestClassTable from '../components/TestClassTable';

const { TextArea } = Input;
const { Title, Text } = Typography;

const TestClassManagementPage = () => {
  const { user } = useAuth();

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

  // 定義標籤頁配置
  const tabItems = [
    {
      key: 'protocol-rag',
      label: (
        <Space>
          <MessageOutlined />
          Protocol RAG TestClass
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
        <Space>
          <BarChartOutlined />
          AI OCR TestClass
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
        <Space>
          <FileTextOutlined />
          RVT TestClass
        </Space>
      ),
      children: (
        <div style={{ 
          textAlign: 'center', 
          padding: '60px 20px',
          background: '#fafafa',
          borderRadius: '6px',
          border: '1px dashed #d9d9d9'
        }}>
          <FileTextOutlined style={{ fontSize: '48px', color: '#d9d9d9', marginBottom: '16px' }} />
          <Title level={4} type="secondary">RVT TestClass 管理</Title>
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
          defaultActiveKey="protocol-rag"
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
            background: '#fafafa',
            borderBottom: '1px solid #f0f0f0'
          }}
        />
      </Card>
    </div>
  );
};

export default TestClassManagementPage;

const TestClassManagementPage = () => {
  const { user } = useAuth();
  const [testClasses, setTestClasses] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');

  // 獲取 CSRF token 的 helper 函數
  const getCsrfToken = () => {
    const name = 'csrftoken';
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
      const cookies = document.cookie.split(';');
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === (name + '=')) {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  };

  // 檢查權限 - 只有 admin 可以訪問
  useEffect(() => {
    if (!user?.is_staff && !user?.is_superuser) {
      message.error('您沒有權限訪問此頁面');
      return;
    }
    fetchTestClasses();
  }, [user]);

  const fetchTestClasses = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/test-classes/', {
        credentials: 'include',
      });
      
      if (response.ok) {
        const data = await response.json();
        setTestClasses(data.results || data);
      } else if (response.status === 403) {
        message.error('權限不足，無法訪問 TestClass 資料');
      } else {
        message.error('載入 TestClass 資料失敗');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      message.error('網路錯誤，無法載入資料');
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setEditingClass(null);
    form.resetFields();
    form.setFieldsValue({ is_active: true }); // 預設啟用
    setModalVisible(true);
  };

  const handleEdit = (record) => {
    setEditingClass(record);
    form.setFieldsValue(record);
    setModalVisible(true);
  };

  const handleDelete = async (id) => {
    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(`/api/test-classes/${id}/`, {
        method: 'DELETE',
        headers: {
          'X-CSRFToken': csrfToken,
        },
        credentials: 'include',
      });
      
      if (response.ok) {
        message.success('刪除成功');
        fetchTestClasses();
      } else {
        message.error('刪除失敗');
      }
    } catch (error) {
      console.error('Delete error:', error);
      message.error('刪除失敗');
    }
  };

  const handleSubmit = async (values) => {
    try {
      const url = editingClass 
        ? `/api/test-classes/${editingClass.id}/`
        : '/api/test-classes/';
      
      const method = editingClass ? 'PUT' : 'POST';
      const csrfToken = getCsrfToken();
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken,
        },
        credentials: 'include',
        body: JSON.stringify(values),
      });

      if (response.ok) {
        message.success(editingClass ? '更新成功' : '新增成功');
        setModalVisible(false);
        fetchTestClasses();
      } else {
        const errorData = await response.json();
        message.error(errorData.detail || (editingClass ? '更新失敗' : '新增失敗'));
      }
    } catch (error) {
      console.error('Submit error:', error);
      message.error(editingClass ? '更新失敗' : '新增失敗');
    }
  };

  // 過濾資料
  const filteredClasses = testClasses.filter(item => 
    item.name.toLowerCase().includes(searchText.toLowerCase()) ||
    (item.description && item.description.toLowerCase().includes(searchText.toLowerCase()))
  );

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      sorter: (a, b) => a.id - b.id,
    },
    {
      title: 'Class 名稱',
      dataIndex: 'name',
      key: 'name',
      sorter: (a, b) => a.name.localeCompare(b.name),
      render: (text) => (
        <Text strong style={{ color: '#1890ff' }}>
          {text}
        </Text>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || <Text type="secondary">無描述</Text>,
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'error'}>
          {isActive ? '啟用' : '停用'}
        </Tag>
      ),
      sorter: (a, b) => a.is_active - b.is_active,
    },
    {
      title: '建立者',
      dataIndex: 'created_by_name',
      key: 'created_by_name',
      width: 100,
    },
    {
      title: '建立時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-TW'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Button
            icon={<EditOutlined />}
            size="small"
            type="primary"
            ghost
            onClick={() => handleEdit(record)}
            title="編輯"
          />
          <Popconfirm
            title="確定要刪除這個 TestClass 嗎？"
            description="此操作無法復原"
            onConfirm={() => handleDelete(record.id)}
            okText="確定"
            cancelText="取消"
            okType="danger"
          >
            <Button
              icon={<DeleteOutlined />}
              size="small"
              danger
              title="刪除"
            />
          </Popconfirm>
        </Space>
      ),
    },
  ];

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

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <ExperimentOutlined style={{ color: '#1890ff' }} />
            <span>Protocol RAG TestClass 管理</span>
          </Space>
        }
        extra={
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            新增 TestClass
          </Button>
        }
      >
        {/* 搜尋和操作區域 */}
        <div style={{ 
          marginBottom: 16, 
          display: 'flex', 
          gap: 16, 
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <Input
            placeholder="搜尋 TestClass 名稱或描述"
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchTestClasses}
            loading={loading}
          >
            重新載入
          </Button>
          <div style={{ marginLeft: 'auto' }}>
            <Text type="secondary">
              總計: {filteredClasses.length} 個 TestClass
            </Text>
          </div>
        </div>

        <Divider style={{ margin: '16px 0' }} />

        <Table
          columns={columns}
          dataSource={filteredClasses}
          rowKey="id"
          loading={loading}
          pagination={{
            total: filteredClasses.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `顯示 ${range[0]}-${range[1]} 筆，共 ${total} 筆資料`,
          }}
          scroll={{ x: 800 }}
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={
          <Space>
            {editingClass ? <EditOutlined /> : <PlusOutlined />}
            {editingClass ? '編輯 TestClass' : '新增 TestClass'}
          </Space>
        }
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          style={{ marginTop: 24 }}
        >
          <Form.Item
            label="TestClass 名稱"
            name="name"
            rules={[
              { required: true, message: '請輸入 TestClass 名稱' },
              { max: 200, message: '名稱不能超過 200 個字元' },
              { min: 2, message: '名稱至少需要 2 個字元' }
            ]}
          >
            <Input 
              placeholder="請輸入 TestClass 名稱" 
              autoFocus
            />
          </Form.Item>

          <Form.Item
            label="描述"
            name="description"
            rules={[
              { max: 1000, message: '描述不能超過 1000 個字元' }
            ]}
          >
            <TextArea
              rows={4}
              placeholder="請輸入 TestClass 描述（可選）"
              showCount
              maxLength={1000}
            />
          </Form.Item>

          <Form.Item
            label="狀態"
            name="is_active"
            valuePropName="checked"
            extra="啟用後此 TestClass 將可供使用"
          >
            <Switch 
              checkedChildren="啟用" 
              unCheckedChildren="停用"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button onClick={() => setModalVisible(false)}>
                取消
              </Button>
              <Button type="primary" htmlType="submit">
                {editingClass ? '更新' : '新增'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TestClassManagementPage;