import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Space,
  Typography,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  message,
  Popconfirm,
  Tag,
  Avatar,
  Tooltip,
  Row,
  Col,
  Alert
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  SafetyOutlined,
  MailOutlined,
  CalendarOutlined,
  SearchOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import axios from 'axios';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const UserManagementPage = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    // 只有管理員才執行獲取用戶列表
    if (user?.is_staff || user?.is_superuser) {
      fetchUsers();
    }
  }, [user]);

  // 檢查管理員權限
  if (!user?.is_staff && !user?.is_superuser) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Card>
          <Space direction="vertical" size="large">
            <UserOutlined style={{ fontSize: '64px', color: '#ff4d4f' }} />
            <Title level={3}>權限不足</Title>
            <Text type="secondary">
              只有管理員才能訪問用戶管理功能
            </Text>
          </Space>
        </Card>
      </div>
    );
  }

  // 獲取用戶列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/users/');
      console.log('API Response:', response.data);
      
      // 確保回應是陣列格式
      if (Array.isArray(response.data)) {
        setUsers(response.data);
      } else if (response.data && Array.isArray(response.data.results)) {
        // 如果是分頁格式，取 results 陣列
        setUsers(response.data.results);
      } else {
        console.error('Invalid API response format:', response.data);
        setUsers([]);
        message.error('API 回應格式錯誤');
      }
    } catch (error) {
      console.error('獲取用戶列表失敗:', error);
      setUsers([]); // 確保設定為空陣列
      message.error('獲取用戶列表失敗');
    } finally {
      setLoading(false);
    }
  };

  // 新增/編輯用戶
  const handleSaveUser = async (values) => {
    try {
      if (editingUser) {
        // 編輯現有用戶
        await axios.put(`/api/users/${editingUser.id}/`, values);
        message.success('用戶資料更新成功');
      } else {
        // 新增用戶
        await axios.post('/api/users/', values);
        message.success('新增用戶成功');
      }
      
      fetchUsers();
      setModalVisible(false);
      form.resetFields();
      setEditingUser(null);
    } catch (error) {
      console.error('儲存用戶失敗:', error);
      message.error(editingUser ? '更新用戶失敗' : '新增用戶失敗');
    }
  };

  // 刪除用戶
  const handleDeleteUser = async (userId) => {
    try {
      await axios.delete(`/api/users/${userId}/`);
      message.success('刪除用戶成功');
      fetchUsers();
    } catch (error) {
      console.error('刪除用戶失敗:', error);
      message.error('刪除用戶失敗');
    }
  };

  // 切換用戶狀態
  const handleToggleStatus = async (userId, currentStatus) => {
    try {
      await axios.patch(`/api/users/${userId}/`, { 
        is_active: !currentStatus 
      });
      message.success(currentStatus ? '已停用用戶' : '已啟用用戶');
      fetchUsers();
    } catch (error) {
      console.error('切換用戶狀態失敗:', error);
      message.error('切換用戶狀態失敗');
    }
  };

  // 開啟編輯模式
  const handleEditUser = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      username: user.username,
      email: user.email,
      first_name: user.first_name,
      last_name: user.last_name,
      is_staff: user.is_staff,
      is_superuser: user.is_superuser,
      is_active: user.is_active
    });
    setModalVisible(true);
  };

  // 開啟新增模式
  const handleAddUser = () => {
    setEditingUser(null);
    form.resetFields();
    setModalVisible(true);
  };

  // 篩選用戶
  const filteredUsers = Array.isArray(users) ? users.filter(user => 
    user.username?.toLowerCase().includes(searchText.toLowerCase()) ||
    user.email?.toLowerCase().includes(searchText.toLowerCase()) ||
    (user.first_name + ' ' + user.last_name)?.toLowerCase().includes(searchText.toLowerCase())
  ) : [];

  // 表格欄位定義
  const columns = [
    {
      title: '頭像',
      dataIndex: 'avatar',
      key: 'avatar',
      width: 80,
      render: (_, record) => (
        <Avatar 
          icon={<UserOutlined />} 
          size={40}
          style={{ backgroundColor: record.is_active ? '#1890ff' : '#d9d9d9' }}
        >
          {record.username.charAt(0).toUpperCase()}
        </Avatar>
      ),
    },
    {
      title: '用戶名',
      dataIndex: 'username',
      key: 'username',
      sorter: (a, b) => a.username.localeCompare(b.username),
      render: (text, record) => (
        <Space direction="vertical" size={0}>
          <Text strong style={{ color: record.is_active ? '#1890ff' : '#999' }}>
            {text}
          </Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            ID: {record.id}
          </Text>
        </Space>
      ),
    },
    {
      title: '姓名',
      key: 'fullName',
      render: (_, record) => (
        <Text>{record.first_name} {record.last_name}</Text>
      ),
    },
    {
      title: '電子郵件',
      dataIndex: 'email',
      key: 'email',
      render: (email) => (
        <Space>
          <MailOutlined style={{ color: '#1890ff' }} />
          <Text copyable>{email}</Text>
        </Space>
      ),
    },
    {
      title: '權限',
      key: 'permissions',
      render: (_, record) => (
        <Space>
          {record.is_superuser && (
            <Tag color="red" icon={<SafetyOutlined />}>
              超級管理員
            </Tag>
          )}
          {record.is_staff && !record.is_superuser && (
            <Tag color="orange" icon={<SafetyOutlined />}>
              管理員
            </Tag>
          )}
          {!record.is_staff && !record.is_superuser && (
            <Tag color="blue">
              一般用戶
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive, record) => (
        <Space>
          <Switch
            checked={isActive}
            onChange={() => handleToggleStatus(record.id, isActive)}
            size="small"
          />
          <Text type={isActive ? 'success' : 'secondary'}>
            {isActive ? '啟用' : '停用'}
          </Text>
        </Space>
      ),
    },
    {
      title: '加入時間',
      dataIndex: 'date_joined',
      key: 'date_joined',
      sorter: (a, b) => new Date(a.date_joined) - new Date(b.date_joined),
      render: (date) => (
        <Space>
          <CalendarOutlined style={{ color: '#1890ff' }} />
          <Text>{dayjs(date).format('YYYY-MM-DD HH:mm')}</Text>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      render: (_, record) => (
        <Space>
          <Tooltip title="編輯用戶">
            <Button
              type="primary"
              icon={<EditOutlined />}
              size="small"
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          
          {record.id !== user?.id && (
            <Popconfirm
              title="確認刪除"
              description="確定要刪除這個用戶嗎？此操作不可復原。"
              onConfirm={() => handleDeleteUser(record.id)}
              okText="確定"
              cancelText="取消"
              icon={<ExclamationCircleOutlined style={{ color: 'red' }} />}
            >
              <Tooltip title="刪除用戶">
                <Button
                  type="primary"
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space size={16}>
            <UserOutlined style={{ 
              color: '#1890ff', 
              fontSize: '20px' 
            }} />
            <Title level={4} style={{ margin: 0 }}>
              用戶管理
            </Title>
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="搜索用戶..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
            />
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleAddUser}
            >
              新增用戶
            </Button>
          </Space>
        }
        styles={{ body: { padding: '16px' } }}
        style={{
          borderRadius: '12px',
          overflow: 'hidden'
        }}
      >
        {user?.is_superuser && (
          <Alert
            message="超級管理員權限"
            description="您擁有完整的用戶管理權限，包括新增、編輯、刪除用戶和權限管理。"
            type="info"
            icon={<SafetyOutlined />}
            style={{ marginBottom: '16px' }}
            closable
          />
        )}

        <Table
          columns={columns}
          dataSource={filteredUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `第 ${range[0]}-${range[1]} 項，共 ${total} 位用戶`
          }}
          scroll={{ x: 1000 }}
          style={{
            borderRadius: '8px',
            overflow: 'hidden'
          }}
        />
      </Card>

      {/* 新增/編輯用戶 Modal */}
      <Modal
        title={editingUser ? '編輯用戶' : '新增用戶'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        footer={null}
        width={600}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
          style={{ marginTop: '16px' }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="用戶名"
                rules={[
                  { required: true, message: '請輸入用戶名' },
                  { min: 3, message: '用戶名至少需要3個字元' }
                ]}
              >
                <Input 
                  prefix={<UserOutlined />} 
                  placeholder="請輸入用戶名"
                  disabled={!!editingUser} // 編輯時禁用用戶名修改
                />
              </Form.Item>
            </Col>
            
            <Col span={12}>
              <Form.Item
                name="email"
                label="電子郵件"
                rules={[
                  { required: true, message: '請輸入電子郵件' },
                  { type: 'email', message: '請輸入有效的電子郵件格式' }
                ]}
              >
                <Input 
                  prefix={<MailOutlined />} 
                  placeholder="請輸入電子郵件"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="first_name"
                label="名字"
              >
                <Input placeholder="請輸入名字" />
              </Form.Item>
            </Col>
            
            <Col span={12}>
              <Form.Item
                name="last_name"
                label="姓氏"
              >
                <Input placeholder="請輸入姓氏" />
              </Form.Item>
            </Col>
          </Row>

          {!editingUser && (
            <Form.Item
              name="password"
              label="密碼"
              rules={[
                { required: true, message: '請輸入密碼' },
                { min: 6, message: '密碼至少需要6個字元' }
              ]}
            >
              <Input.Password placeholder="請輸入密碼" />
            </Form.Item>
          )}

          {user?.is_superuser && (
            <>
              <Form.Item
                name="is_staff"
                label="管理員權限"
                valuePropName="checked"
              >
                <Switch 
                  checkedChildren="是"
                  unCheckedChildren="否"
                />
              </Form.Item>

              <Form.Item
                name="is_superuser"
                label="超級管理員權限"
                valuePropName="checked"
              >
                <Switch 
                  checkedChildren="是"
                  unCheckedChildren="否"
                />
              </Form.Item>
            </>
          )}

          <Form.Item
            name="is_active"
            label="帳戶狀態"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch 
              checkedChildren="啟用"
              unCheckedChildren="停用"
            />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0, textAlign: 'right' }}>
            <Space>
              <Button
                onClick={() => {
                  setModalVisible(false);
                  setEditingUser(null);
                  form.resetFields();
                }}
              >
                取消
              </Button>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
              >
                {editingUser ? '更新' : '新增'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagementPage;