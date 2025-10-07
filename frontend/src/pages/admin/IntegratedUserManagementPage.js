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
  Alert,
  Checkbox,
  Divider,
  Badge
} from 'antd';
import {
  UserOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  ExclamationCircleOutlined,
  SafetyOutlined,
  MailOutlined,
  SearchOutlined,
  LockOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const { Title, Text } = Typography;

/**
 * 整合的用戶權限管理頁面
 * 將用戶管理和權限管理合併在一個頁面中
 */
const IntegratedUserManagementPage = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [form] = Form.useForm();

  useEffect(() => {
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
              只有管理員才能訪問用戶權限管理功能
            </Text>
          </Space>
        </Card>
      </div>
    );
  }

  // 獲取用戶列表（包含權限信息）
  const fetchUsers = async () => {
    setLoading(true);
    try {
      // 獲取用戶基本信息
      const usersResponse = await axios.get('/api/users/', { withCredentials: true });
      // 獲取用戶權限信息
      const permissionsResponse = await axios.get('/api/profiles/permissions/', { withCredentials: true });
      
      // 合併用戶信息和權限信息
      const usersData = Array.isArray(usersResponse.data) ? usersResponse.data : usersResponse.data.results || [];
      const permissionsData = permissionsResponse.data.success ? permissionsResponse.data.data : [];
      
      const enrichedUsers = usersData.map(userData => {
        const userPermissions = permissionsData.find(p => p.user.id === userData.id);
        return {
          ...userData,
          permissions: userPermissions || {
            web_protocol_rag: false,
            web_ai_ocr: false,
            web_rvt_assistant: false,
            kb_protocol_rag: false,
            kb_ai_ocr: false,
            kb_rvt_assistant: false,
            is_super_admin: false
          }
        };
      });
      
      setUsers(enrichedUsers);
    } catch (error) {
      console.error('獲取用戶列表失敗:', error);
      setUsers([]);
      message.error('獲取用戶列表失敗');
    } finally {
      setLoading(false);
    }
  };

  // 保存用戶資料（包含基本信息和權限）
  const handleSaveUser = async (values) => {
    try {
      // 分離基本用戶資料和權限資料
      const {
        web_protocol_rag,
        web_ai_ocr,
        web_rvt_assistant,
        kb_protocol_rag,
        kb_ai_ocr,
        kb_rvt_assistant,
        is_super_admin,
        ...basicUserData
      } = values;

      const permissionData = {
        web_protocol_rag,
        web_ai_ocr,
        web_rvt_assistant,
        kb_protocol_rag,
        kb_ai_ocr,
        kb_rvt_assistant,
        is_super_admin
      };

      if (editingUser) {
        // 更新基本用戶資料
        await axios.put(`/api/users/${editingUser.id}/`, basicUserData, { withCredentials: true });
        
        // 更新權限資料
        await axios.patch(`/api/profiles/${editingUser.id}/permissions/`, permissionData, { withCredentials: true });
        
        message.success('用戶資料和權限更新成功');
      } else {
        // 創建新用戶
        const userResponse = await axios.post('/api/users/', basicUserData, { withCredentials: true });
        const newUserId = userResponse.data.id;
        
        // 設定新用戶權限
        await axios.patch(`/api/profiles/${newUserId}/permissions/`, permissionData, { withCredentials: true });
        
        message.success('新增用戶和權限設定成功');
      }
      
      fetchUsers();
      setModalVisible(false);
      form.resetFields();
      setEditingUser(null);
    } catch (error) {
      console.error('儲存用戶失敗:', error);
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error(editingUser ? '更新用戶失敗' : '新增用戶失敗');
      }
    }
  };



  // 刪除用戶
  const handleDeleteUser = async (userId) => {
    try {
      await axios.delete(`/api/users/${userId}/`, { withCredentials: true });
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
      }, { withCredentials: true });
      message.success(currentStatus ? '已停用用戶' : '已啟用用戶');
      fetchUsers();
    } catch (error) {
      console.error('切換用戶狀態失敗:', error);
      message.error('切換用戶狀態失敗');
    }
  };

  // 開啟用戶編輯（包含權限設定）
  const handleEditUser = (userData) => {
    setEditingUser(userData);
    form.setFieldsValue({
      // 基本資料
      username: userData.username,
      email: userData.email,
      first_name: userData.first_name,
      last_name: userData.last_name,
      is_staff: userData.is_staff,
      is_superuser: userData.is_superuser,
      is_active: userData.is_active,
      
      // 功能權限
      web_protocol_rag: userData.permissions?.web_protocol_rag || false,
      web_ai_ocr: userData.permissions?.web_ai_ocr || false,
      web_rvt_assistant: userData.permissions?.web_rvt_assistant || false,
      kb_protocol_rag: userData.permissions?.kb_protocol_rag || false,
      kb_ai_ocr: userData.permissions?.kb_ai_ocr || false,
      kb_rvt_assistant: userData.permissions?.kb_rvt_assistant || false,
      is_super_admin: userData.permissions?.is_super_admin || false
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
  const filteredUsers = Array.isArray(users) ? users.filter(userData => 
    userData.username?.toLowerCase().includes(searchText.toLowerCase()) ||
    userData.email?.toLowerCase().includes(searchText.toLowerCase()) ||
    (userData.first_name + ' ' + userData.last_name)?.toLowerCase().includes(searchText.toLowerCase())
  ) : [];

  // 獲取權限標籤
  const getPermissionTags = (permissions) => {
    const tags = [];
    
    if (permissions.is_super_admin) {
      tags.push(<Tag key="super" color="red">超級管理員</Tag>);
    }
    
    // Web 權限
    if (permissions.web_protocol_rag) tags.push(<Tag key="web_protocol" color="blue">Web Protocol RAG</Tag>);
    if (permissions.web_ai_ocr) tags.push(<Tag key="web_ocr" color="blue">Web AI OCR</Tag>);
    if (permissions.web_rvt_assistant) tags.push(<Tag key="web_rvt" color="blue">Web RVT Assistant</Tag>);
    
    // 知識庫權限
    if (permissions.kb_protocol_rag) tags.push(<Tag key="kb_protocol" color="green">KB Protocol RAG</Tag>);
    if (permissions.kb_ai_ocr) tags.push(<Tag key="kb_ocr" color="green">KB AI OCR</Tag>);
    if (permissions.kb_rvt_assistant) tags.push(<Tag key="kb_rvt" color="green">KB RVT Assistant</Tag>);
    
    return tags.length > 0 ? tags : <Tag color="default">無特殊權限</Tag>;
  };

  // 表格欄位定義
  const columns = [
    {
      title: '用戶',
      key: 'user_info',
      width: 200,
      render: (_, record) => (
        <Space>
          <Avatar 
            icon={<UserOutlined />} 
            size={40}
            style={{ backgroundColor: record.is_active ? '#1890ff' : '#d9d9d9' }}
          >
            {record.username.charAt(0).toUpperCase()}
          </Avatar>
          <Space direction="vertical" size={0}>
            <Text strong style={{ color: record.is_active ? '#1890ff' : '#999' }}>
              {record.username}
            </Text>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.first_name} {record.last_name}
            </Text>
          </Space>
        </Space>
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
      title: '系統權限',
      key: 'system_permissions',
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
      title: '功能權限',
      key: 'feature_permissions',
      width: 300,
      render: (_, record) => (
        <div style={{ maxWidth: '280px' }}>
          {getPermissionTags(record.permissions)}
        </div>
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
      title: '操作',
      key: 'actions',
      width: 200,
      render: (_, record) => (
        <Space>
          <Tooltip title="編輯用戶資料與權限">
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
              用戶權限管理
            </Title>
            <Badge count={filteredUsers.length} style={{ backgroundColor: '#52c41a' }} />
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
      >
        {user?.is_superuser && (
          <Alert
            message="超級管理員權限"
            description="您可以管理所有用戶的基本資料和功能權限，包括系統管理員權限設定。"
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
          scroll={{ x: 1200 }}
        />
      </Card>

      {/* 新增/編輯用戶 Modal - 整合權限管理 */}
      <Modal
        title={editingUser ? '編輯用戶資料與權限' : '新增用戶'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          setEditingUser(null);
          form.resetFields();
        }}
        footer={null}
        width={800}
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
                  disabled={!!editingUser}
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
              <Form.Item name="first_name" label="名字">
                <Input placeholder="請輸入名字" />
              </Form.Item>
            </Col>
            
            <Col span={12}>
              <Form.Item name="last_name" label="姓氏">
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

          {/* 功能權限設定 */}
          <Divider orientation="left">功能權限設定</Divider>
          
          <Row gutter={24}>
            <Col span={12}>
              <Card 
                title="Web 應用功能" 
                size="small"
                style={{ marginBottom: '16px' }}
              >
                <Form.Item
                  name="web_protocol_rag"
                  valuePropName="checked"
                >
                  <Checkbox>Web Protocol RAG</Checkbox>
                </Form.Item>
                
                <Form.Item
                  name="web_ai_ocr"
                  valuePropName="checked"
                >
                  <Checkbox>Web AI OCR</Checkbox>
                </Form.Item>
                
                <Form.Item
                  name="web_rvt_assistant"
                  valuePropName="checked"
                >
                  <Checkbox>Web RVT Assistant</Checkbox>
                </Form.Item>
              </Card>
            </Col>
            
            <Col span={12}>
              <Card 
                title="知識庫功能" 
                size="small"
                style={{ marginBottom: '16px' }}
              >
                <Form.Item
                  name="kb_protocol_rag"
                  valuePropName="checked"
                >
                  <Checkbox>知識庫 Protocol RAG</Checkbox>
                </Form.Item>
                
                <Form.Item
                  name="kb_ai_ocr"
                  valuePropName="checked"
                >
                  <Checkbox>知識庫 AI OCR</Checkbox>
                </Form.Item>
                
                <Form.Item
                  name="kb_rvt_assistant"
                  valuePropName="checked"
                >
                  <Checkbox>知識庫 RVT Assistant</Checkbox>
                </Form.Item>
              </Card>
            </Col>
          </Row>

          {user?.is_superuser && (
            <>
              <Divider orientation="left">管理權限</Divider>
              
              <Form.Item
                name="is_super_admin"
                valuePropName="checked"
              >
                <Checkbox>
                  <Space>
                    <LockOutlined />
                    <span>超級管理員</span>
                    <Text type="secondary" style={{ fontSize: '12px' }}>
                      (可管理所有用戶權限)
                    </Text>
                  </Space>
                </Checkbox>
              </Form.Item>
            </>
          )}

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

export default IntegratedUserManagementPage;