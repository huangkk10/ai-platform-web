import React, { useState, useEffect } from 'react';
import { Card, Table, Typography, Button, message, Tag, Space, Modal, Form, Input, Select } from 'antd';
import { DatabaseOutlined, PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const { Title } = Typography;
const { Option } = Select;

const KnowIssuePage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const [issues, setIssues] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingIssue, setEditingIssue] = useState(null);
  const [form] = Form.useForm();

  // 載入員工資料
  const fetchEmployees = async () => {
    try {
      const response = await axios.get('/api/employees/', {
        withCredentials: true
      });
      setEmployees(response.data.results || []);
    } catch (error) {
      console.error('載入員工列表失敗:', error);
      // 員工列表載入失敗不影響主要功能
    }
  };

  // 載入資料
  const fetchIssues = async () => {
    try {
      setLoading(true);
      console.log('Fetching issues, authenticated:', isAuthenticated, 'user:', user);
      
      // 確保用戶已認證且有權限
      if (!isAuthenticated) {
        message.error('請先登入');
        return;
      }
      
      if (!user || (!user.is_staff && !user.is_superuser)) {
        message.error('權限不足，需要管理員權限');
        return;
      }
      
      const response = await axios.get('/api/know-issues/', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }
      });
      
      console.log('API Response:', response.data);
      setIssues(response.data.results || []);
      message.success(`資料載入成功，共 ${response.data.results?.length || 0} 筆記錄`);
    } catch (error) {
      console.error('載入 know issues 失敗:', error);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      
      if (error.response?.status === 401) {
        message.error('認證已過期，請重新登入');
      } else if (error.response?.status === 403) {
        message.error('權限不足，請確認您有管理員權限');
      } else {
        message.error('載入資料失敗: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    console.log('KnowIssuePage mounted, isAuthenticated:', isAuthenticated, 'user:', user, 'initialized:', initialized);
    
    // 只有在認證狀態初始化完成且用戶已認證時才載入資料
    if (initialized && isAuthenticated && user && (user.is_staff || user.is_superuser)) {
      fetchIssues();
      fetchEmployees();
    } else if (initialized && (!isAuthenticated || !user || (!user.is_staff && !user.is_superuser))) {
      console.log('User not authorized or not authenticated');
      if (!isAuthenticated) {
        message.warning('請先登入以查看知識庫');
      } else {
        message.warning('需要管理員權限才能查看知識庫');
      }
    }
  }, [isAuthenticated, user, initialized]); // 依賴認證狀態和初始化狀態

  // 表格欄位定義
  const columns = [
    {
      title: 'Issue ID',
      dataIndex: 'issue_id',
      key: 'issue_id',
      width: 120,
      fixed: 'left',
      render: (text) => <Tag color="blue">{text}</Tag>,
      sorter: (a, b) => a.issue_id.localeCompare(b.issue_id),
    },
    {
      title: '專案',
      dataIndex: 'project',
      key: 'project',
      width: 150,
      ellipsis: true,
    },
    {
      title: '測試版本',
      dataIndex: 'test_version',
      key: 'test_version',
      width: 120,
    },
    {
      title: 'JIRA 號碼',
      dataIndex: 'jira_number',
      key: 'jira_number',
      width: 120,
      render: (text) => text ? <Tag color="orange">{text}</Tag> : '-',
    },
    {
      title: '問題類型',
      dataIndex: 'issue_type_display',
      key: 'issue_type',
      width: 100,
      render: (text, record) => {
        const colors = {
          'bug': 'red',
          'feature': 'green',
          'improvement': 'blue',
          'task': 'purple',
          'support': 'cyan',
          'other': 'default'
        };
        return <Tag color={colors[record.issue_type] || 'default'}>{text}</Tag>;
      },
    },
    {
      title: '狀態',
      dataIndex: 'status_display',
      key: 'status',
      width: 100,
      render: (text, record) => {
        const colors = {
          'open': 'red',
          'in_progress': 'orange',
          'resolved': 'green',
          'closed': 'gray',
          'pending': 'yellow',
          'won_fix': 'gray'
        };
        return <Tag color={colors[record.status] || 'default'}>{text}</Tag>;
      },
    },
    {
      title: '更新人員',
      dataIndex: 'updated_by_name',
      key: 'updated_by',
      width: 100,
    },
    {
      title: '錯誤訊息',
      dataIndex: 'error_message',
      key: 'error_message',
      width: 200,
      ellipsis: true,
      render: (text) => (
        <div style={{ maxWidth: 200 }} title={text}>
          {text}
        </div>
      ),
    },
    {
      title: '更新時間',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 120,
      render: (text) => new Date(text).toLocaleDateString('zh-TW'),
      sorter: (a, b) => new Date(a.updated_at) - new Date(b.updated_at),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            onClick={() => handleEdit(record)}
          />
          <Button 
            icon={<DeleteOutlined />} 
            size="small" 
            danger
            onClick={() => handleDelete(record.id)}
          />
        </Space>
      ),
    },
  ];

  // 編輯處理
  const handleEdit = (issue) => {
    setEditingIssue(issue);
    form.setFieldsValue(issue);
    setModalVisible(true);
  };

  // 刪除處理
  const handleDelete = async (id) => {
    Modal.confirm({
      title: '確認刪除',
      content: '確定要刪除這個問題記錄嗎？',
      onOk: async () => {
        try {
          await axios.delete(`/api/know-issues/${id}/`, {
            withCredentials: true
          });
          message.success('刪除成功');
          fetchIssues();
        } catch (error) {
          message.error('刪除失敗');
        }
      },
    });
  };

  // 新增/編輯提交
  const handleSubmit = async (values) => {
    try {
      if (editingIssue) {
        await axios.put(`/api/know-issues/${editingIssue.id}/`, values, {
          withCredentials: true
        });
        message.success('更新成功');
      } else {
        await axios.post('/api/know-issues/', values, {
          withCredentials: true
        });
        message.success('新增成功');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingIssue(null);
      fetchIssues();
    } catch (error) {
      message.error('操作失敗: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 如果還未初始化，顯示載入狀態
  if (!initialized) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>載入中...</Title>
            <p>正在檢查認證狀態，請稍候</p>
          </div>
        </Card>
      </div>
    );
  }

  // 如果未認證，顯示提示
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>需要登入</Title>
            <p>請登入後才能查看 Know Issue 資料</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center' 
      }}>
        <Title level={2} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Know Issue 管理
        </Title>
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={fetchIssues}
            loading={loading}
          >
            重新載入
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingIssue(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            新增問題
          </Button>
        </Space>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={issues}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1200 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
          }}
          bordered
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={editingIssue ? '編輯問題' : '新增問題'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingIssue(null);
        }}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="issue_id"
            label="Issue ID"
            rules={[{ required: true, message: '請輸入 Issue ID' }]}
          >
            <Input placeholder="例如: BUG-001" />
          </Form.Item>
          
          <Form.Item
            name="test_version"
            label="測試版本"
            rules={[{ required: true, message: '請輸入測試版本' }]}
          >
            <Input placeholder="例如: v1.0.0" />
          </Form.Item>
          
          <Form.Item
            name="jira_number"
            label="JIRA 號碼"
          >
            <Input placeholder="例如: PROJ-123" />
          </Form.Item>
          
          <Form.Item
            name="project"
            label="Project"
            rules={[{ required: true, message: '請輸入專案名稱' }]}
          >
            <Input placeholder="例如: AI Platform Web" />
          </Form.Item>
          
          <Form.Item
            name="issue_type"
            label="Issue Type"
            rules={[{ required: true, message: '請輸入問題類型' }]}
          >
            <Input placeholder="例如: Bug, Feature Request, Improvement, Task" />
          </Form.Item>
          
          <Form.Item
            name="status"
            label="修復狀態"
            rules={[{ required: true, message: '請輸入狀態' }]}
          >
            <Input placeholder="例如: 開放中, 處理中, 已解決, 已關閉" />
          </Form.Item>
          
          <Form.Item
            name="updated_by"
            label="更新人員"
          >
            <Select placeholder="請選擇更新人員" allowClear>
              {employees.map(employee => (
                <Option key={employee.id} value={employee.id}>
                  {employee.name}
                </Option>
              ))}
            </Select>
          </Form.Item>
          
          <Form.Item
            name="error_message"
            label="錯誤訊息"
            rules={[{ required: true, message: '請輸入錯誤訊息' }]}
          >
            <Input.TextArea rows={3} placeholder="請描述具體的錯誤訊息..." />
          </Form.Item>
          
          <Form.Item
            name="script"
            label="Script"
          >
            <Input.TextArea rows={3} placeholder="相關的腳本或代碼..." />
          </Form.Item>
          
          <Form.Item
            name="supplement"
            label="補充"
          >
            <Input.TextArea rows={3} placeholder="額外的補充說明或解決方案..." />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default KnowIssuePage;