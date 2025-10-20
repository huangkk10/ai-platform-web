import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Space, 
  Typography, 
  Switch, 
  message, 
  Tooltip, 
  Modal, 
  Form,
  Row,
  Col,
  Divider,
  Tag,
  Alert,
  Spin
} from 'antd';
import { 
  EditOutlined, 
  ReloadOutlined, 
  UserOutlined, 
  SettingOutlined,
  SaveOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import axios from 'axios';

const { Title, Text } = Typography;
const { confirm } = Modal;

const PermissionManagementPage = () => {
  const { canManagePermissions } = useAuth();
  const [loading, setLoading] = useState(true);
  const [users, setUsers] = useState([]);
  const [editingUser, setEditingUser] = useState(null);
  const [modalVisible, setModalVisible] = useState(false);
  const [form] = Form.useForm();

  // 權限定義
  const permissionDefinitions = [
    { key: 'web_protocol_rag', label: 'Web Protocol RAG', description: 'Web版本的Protocol RAG功能' },
    { key: 'web_ai_ocr', label: 'Web AI OCR', description: 'Web版本的AI OCR功能' },
    { key: 'web_rvt_assistant', label: 'Web RVT Assistant', description: 'Web版本的RVT Assistant功能' },
    { key: 'web_protocol_assistant', label: 'Web Protocol Assistant', description: 'Web版本的Protocol Assistant功能' },
    { key: 'kb_protocol_rag', label: '知識庫 Protocol RAG', description: '知識庫版本的Protocol RAG功能' },
    { key: 'kb_ai_ocr', label: '知識庫 AI OCR', description: '知識庫版本的AI OCR功能' },
    { key: 'kb_rvt_assistant', label: '知識庫 RVT Assistant', description: '知識庫版本的RVT Assistant功能' },
    { key: 'kb_protocol_assistant', label: '知識庫 Protocol Assistant', description: '知識庫版本的Protocol Assistant功能' },
    { key: 'is_super_admin', label: '超級管理員', description: '可以管理所有用戶權限的超級管理員' }
  ];

  // 檢查權限
  useEffect(() => {
    if (!canManagePermissions()) {
      message.error('權限不足，僅超級管理員可以訪問此頁面');
      return;
    }
    
    fetchUsers();
  }, [canManagePermissions]);

  // 獲取用戶列表
  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/profiles/permissions/', {
        withCredentials: true
      });

      if (response.data.success) {
        setUsers(response.data.data);
        message.success(`成功載入 ${response.data.count} 個用戶的權限資訊`);
      } else {
        message.error('載入用戶權限失敗');
      }
    } catch (error) {
      console.error('獲取用戶權限失敗:', error);
      message.error('載入用戶權限時發生錯誤');
    } finally {
      setLoading(false);
    }
  };

  // 打開編輯對話框
  const handleEdit = (record) => {
    setEditingUser(record);
    form.setFieldsValue({
      web_protocol_rag: record.web_protocol_rag,
      web_ai_ocr: record.web_ai_ocr,
      web_rvt_assistant: record.web_rvt_assistant,
      kb_protocol_rag: record.kb_protocol_rag,
      kb_ai_ocr: record.kb_ai_ocr,
      kb_rvt_assistant: record.kb_rvt_assistant,
      kb_protocol_assistant: record.kb_protocol_assistant,
      is_super_admin: record.is_super_admin
    });
    setModalVisible(true);
  };

  // 保存權限更改
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      
      const response = await axios.patch(`/api/profiles/${editingUser.user.id}/permissions/`, values, {
        withCredentials: true
      });

      if (response.data.success) {
        message.success(response.data.message);
        setModalVisible(false);
        setEditingUser(null);
        form.resetFields();
        fetchUsers(); // 重新載入用戶列表
      } else {
        message.error('更新權限失敗');
      }
    } catch (error) {
      console.error('更新權限失敗:', error);
      
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else {
        message.error('更新權限時發生錯誤');
      }
    }
  };

  // 快速切換權限
  const handleQuickToggle = async (userId, permissionKey, currentValue) => {
    confirm({
      title: '確認更改權限',
      icon: <ExclamationCircleOutlined />,
      content: `確定要${currentValue ? '取消' : '授予'}此權限嗎？`,
      onOk: async () => {
        try {
          const updateData = { [permissionKey]: !currentValue };
          
          const response = await axios.patch(`/api/profiles/${userId}/permissions/`, updateData, {
            withCredentials: true
          });

          if (response.data.success) {
            message.success('權限已更新');
            fetchUsers();
          } else {
            message.error('更新權限失敗');
          }
        } catch (error) {
          console.error('快速更新權限失敗:', error);
          
          if (error.response?.data?.error) {
            message.error(error.response.data.error);
          } else {
            message.error('更新權限時發生錯誤');
          }
        }
      }
    });
  };

  // 表格列定義
  const columns = [
    {
      title: '用戶信息',
      key: 'user',
      width: 200,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          <Space>
            <UserOutlined />
            <Text strong>{record.user.username}</Text>
          </Space>
          {record.user.email && (
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.user.email}
            </Text>
          )}
          <Space>
            {record.user.is_superuser && <Tag color="red">Django 超級用戶</Tag>}
            {record.is_super_admin && <Tag color="orange">超級管理員</Tag>}
            {record.user.is_staff && <Tag color="blue">工作人員</Tag>}
          </Space>
        </Space>
      )
    },
    {
      title: 'Web 功能權限',
      key: 'web_permissions',
      width: 300,
      render: (_, record) => (
        <Row gutter={[8, 8]}>
          <Col span={24}>
            <Space wrap>
              <Tooltip title="Web版本的Protocol RAG功能">
                <Tag 
                  color={record.web_protocol_rag ? 'green' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'web_protocol_rag', record.web_protocol_rag)}
                >
                  Protocol RAG {record.web_protocol_rag ? '✓' : '✗'}
                </Tag>
              </Tooltip>
              <Tooltip title="Web版本的AI OCR功能">
                <Tag 
                  color={record.web_ai_ocr ? 'green' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'web_ai_ocr', record.web_ai_ocr)}
                >
                  AI OCR {record.web_ai_ocr ? '✓' : '✗'}
                </Tag>
              </Tooltip>
              <Tooltip title="Web版本的RVT Assistant功能">
                <Tag 
                  color={record.web_rvt_assistant ? 'green' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'web_rvt_assistant', record.web_rvt_assistant)}
                >
                  RVT Assistant {record.web_rvt_assistant ? '✓' : '✗'}
                </Tag>
              </Tooltip>
            </Space>
          </Col>
        </Row>
      )
    },
    {
      title: '知識庫權限',
      key: 'kb_permissions',
      width: 300,
      render: (_, record) => (
        <Row gutter={[8, 8]}>
          <Col span={24}>
            <Space wrap>
              <Tooltip title="知識庫版本的Protocol RAG功能">
                <Tag 
                  color={record.kb_protocol_rag ? 'blue' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'kb_protocol_rag', record.kb_protocol_rag)}
                >
                  KB Protocol RAG {record.kb_protocol_rag ? '✓' : '✗'}
                </Tag>
              </Tooltip>
              <Tooltip title="知識庫版本的AI OCR功能">
                <Tag 
                  color={record.kb_ai_ocr ? 'blue' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'kb_ai_ocr', record.kb_ai_ocr)}
                >
                  KB AI OCR {record.kb_ai_ocr ? '✓' : '✗'}
                </Tag>
              </Tooltip>
              <Tooltip title="知識庫版本的RVT Assistant功能">
                <Tag 
                  color={record.kb_rvt_assistant ? 'blue' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'kb_rvt_assistant', record.kb_rvt_assistant)}
                >
                  KB RVT Assistant {record.kb_rvt_assistant ? '✓' : '✗'}
                </Tag>
              </Tooltip>
              <Tooltip title="知識庫版本的Protocol Assistant功能">
                <Tag 
                  color={record.kb_protocol_assistant ? 'blue' : 'default'}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleQuickToggle(record.user.id, 'kb_protocol_assistant', record.kb_protocol_assistant)}
                >
                  KB Protocol Assistant {record.kb_protocol_assistant ? '✓' : '✗'}
                </Tag>
              </Tooltip>
            </Space>
          </Col>
        </Row>
      )
    },
    {
      title: '權限摘要',
      key: 'permissions_summary',
      width: 200,
      render: (_, record) => (
        <Text style={{ fontSize: '12px' }}>
          {record.permissions_summary || '無特殊權限'}
        </Text>
      )
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Space>
          <Tooltip title="編輯權限">
            <Button 
              type="primary" 
              size="small" 
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
        </Space>
      )
    }
  ];

  if (!canManagePermissions()) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="權限不足"
          description="您沒有權限訪問此頁面，僅超級管理員可以管理用戶權限。"
          type="error"
          showIcon
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <Card>
        <div style={{ marginBottom: '24px' }}>
          <Title level={2} style={{ margin: 0 }}>
            <SettingOutlined /> 用戶權限管理
          </Title>
          <Text type="secondary">
            管理所有用戶的功能權限，控制用戶可以訪問的Web功能和知識庫功能
          </Text>
        </div>

        <div style={{ marginBottom: '16px' }}>
          <Space>
            <Button 
              type="primary" 
              icon={<ReloadOutlined />} 
              onClick={fetchUsers}
              loading={loading}
            >
              重新載入
            </Button>
            <Text type="secondary">
              總共 {users.length} 個用戶
            </Text>
          </Space>
        </div>

        <Alert
          message="權限說明"
          description={
            <div>
              <p>• <strong>Web 功能權限</strong>：控制用戶在Web界面中可以使用的功能</p>
              <p>• <strong>知識庫權限</strong>：控制用戶可以訪問和管理的知識庫功能</p>
              <p>• <strong>超級管理員</strong>：可以管理所有用戶的權限設定</p>
              <p>• 點擊權限標籤可快速切換該權限，或使用編輯按鈕進行批量修改</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />

        <Table
          dataSource={users}
          columns={columns}
          rowKey={(record) => record.user.id}
          loading={loading}
          pagination={{
            total: users.length,
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 條，共 ${total} 條記錄`
          }}
          scroll={{ x: 1200 }}
        />

        <Modal
          title={`編輯用戶權限 - ${editingUser?.user.username}`}
          open={modalVisible}
          onOk={handleSave}
          onCancel={() => {
            setModalVisible(false);
            setEditingUser(null);
            form.resetFields();
          }}
          width={800}
          okText="保存"
          cancelText="取消"
          okButtonProps={{ icon: <SaveOutlined /> }}
        >
          {editingUser && (
            <Form
              form={form}
              layout="vertical"
              initialValues={{
                web_protocol_rag: editingUser.web_protocol_rag,
                web_ai_ocr: editingUser.web_ai_ocr,
                web_rvt_assistant: editingUser.web_rvt_assistant,
                kb_protocol_rag: editingUser.kb_protocol_rag,
                kb_ai_ocr: editingUser.kb_ai_ocr,
                kb_rvt_assistant: editingUser.kb_rvt_assistant,
                kb_protocol_assistant: editingUser.kb_protocol_assistant,
                is_super_admin: editingUser.is_super_admin
              }}
            >
              <Alert
                message={`正在編輯用戶: ${editingUser.user.username} (${editingUser.user.email || '無郵箱'})`}
                type="info"
                style={{ marginBottom: '16px' }}
              />

              <Divider orientation="left">Web 功能權限</Divider>
              <Row gutter={16}>
                <Col span={8}>
                  <Form.Item 
                    name="web_protocol_rag" 
                    label="Web Protocol RAG" 
                    valuePropName="checked"
                    tooltip="Web版本的Protocol RAG功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item 
                    name="web_ai_ocr" 
                    label="Web AI OCR" 
                    valuePropName="checked"
                    tooltip="Web版本的AI OCR功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item 
                    name="web_rvt_assistant" 
                    label="Web RVT Assistant" 
                    valuePropName="checked"
                    tooltip="Web版本的RVT Assistant功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">知識庫權限</Divider>
              <Row gutter={16}>
                <Col span={6}>
                  <Form.Item 
                    name="kb_protocol_rag" 
                    label="知識庫 Protocol RAG" 
                    valuePropName="checked"
                    tooltip="知識庫版本的Protocol RAG功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item 
                    name="kb_ai_ocr" 
                    label="知識庫 AI OCR" 
                    valuePropName="checked"
                    tooltip="知識庫版本的AI OCR功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item 
                    name="kb_rvt_assistant" 
                    label="知識庫 RVT Assistant" 
                    valuePropName="checked"
                    tooltip="知識庫版本的RVT Assistant功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item 
                    name="kb_protocol_assistant" 
                    label="知識庫 Protocol Assistant" 
                    valuePropName="checked"
                    tooltip="知識庫版本的Protocol Assistant功能"
                  >
                    <Switch />
                  </Form.Item>
                </Col>
              </Row>

              <Divider orientation="left">管理權限</Divider>
              <Row gutter={16}>
                <Col span={24}>
                  <Form.Item 
                    name="is_super_admin" 
                    label="超級管理員" 
                    valuePropName="checked"
                    tooltip="可以管理所有用戶權限的超級管理員"
                  >
                    <Switch />
                  </Form.Item>
                  <Alert
                    message="注意"
                    description="超級管理員可以管理所有用戶的權限設定，請謹慎授權。"
                    type="warning"
                    showIcon
                    style={{ marginTop: '8px' }}
                  />
                </Col>
              </Row>
            </Form>
          )}
        </Modal>
      </Card>
    </div>
  );
};

export default PermissionManagementPage;