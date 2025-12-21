import React, { useState, useEffect } from 'react';
import { Card, Table, Button, Tag, Modal, Input, message, Space, Tooltip, Descriptions } from 'antd';
import { CheckOutlined, CloseOutlined, ReloadOutlined, EyeOutlined, StopOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;

const PendingUsersPage = () => {
  const [pendingUsers, setPendingUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [rejectModalVisible, setRejectModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [rejectingUser, setRejectingUser] = useState(null);
  const [viewingUser, setViewingUser] = useState(null);
  const [rejectionReason, setRejectionReason] = useState('');

  const fetchPendingUsers = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/admin/pending-users/');
      if (response.data.success) {
        setPendingUsers(response.data.data);
      }
    } catch (error) {
      message.error('獲取待審核用戶失敗');
      console.error('獲取待審核用戶失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPendingUsers();
  }, []);

  const handleApprove = async (user) => {
    Modal.confirm({
      title: '確認批准',
      content: (
        <div>
          <p>確定要批准用戶 <strong>{user.username}</strong> 的註冊申請嗎？</p>
          <div style={{ marginTop: '12px', padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            <p style={{ margin: 0 }}><strong>Email:</strong> {user.email}</p>
            <p style={{ margin: 0 }}><strong>部門:</strong> {user.application_department}</p>
          </div>
        </div>
      ),
      okText: '批准',
      cancelText: '取消',
      onOk: async () => {
        try {
          const response = await axios.post(`/api/admin/pending-users/${user.id}/approve/`);
          if (response.data.success) {
            message.success(`已批准用戶 ${user.username} 的註冊申請`);
            fetchPendingUsers();
          }
        } catch (error) {
          message.error('批准失敗');
          console.error('批准失敗:', error);
        }
      },
    });
  };

  const handleReject = (user) => {
    setRejectingUser(user);
    setRejectionReason('');
    setRejectModalVisible(true);
  };

  const confirmReject = async () => {
    if (!rejectionReason.trim()) {
      message.warning('請輸入拒絕原因');
      return;
    }

    try {
      const response = await axios.post(`/api/admin/pending-users/${rejectingUser.id}/reject/`, {
        reason: rejectionReason,
      });
      if (response.data.success) {
        message.success(`已拒絕用戶 ${rejectingUser.username} 的註冊申請`);
        setRejectModalVisible(false);
        setRejectionReason('');
        fetchPendingUsers();
      }
    } catch (error) {
      message.error('拒絕失敗');
      console.error('拒絕失敗:', error);
    }
  };

  const handleViewDetail = (user) => {
    setViewingUser(user);
    setDetailModalVisible(true);
  };

  const columns = [
    {
      title: '用戶名',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      fixed: 'left',
      render: (text) => <strong>{text}</strong>,
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      width: 200,
      ellipsis: true,
    },
    {
      title: '姓名',
      key: 'name',
      width: 120,
      render: (_, record) => {
        const name = [record.first_name, record.last_name].filter(Boolean).join(' ');
        return name || '-';
      },
    },
    {
      title: '申請部門',
      dataIndex: 'application_department',
      key: 'department',
      width: 150,
      ellipsis: true,
    },
    {
      title: '申請理由',
      dataIndex: 'application_reason',
      key: 'reason',
      width: 250,
      ellipsis: true,
      render: (text) => (
        <Tooltip title={text}>
          <div style={{ 
            maxWidth: '100%', 
            overflow: 'hidden', 
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap' 
          }}>
            {text}
          </div>
        </Tooltip>
      ),
    },
    {
      title: '申請時間',
      dataIndex: 'date_joined',
      key: 'date_joined',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-TW'),
      sorter: (a, b) => new Date(a.date_joined) - new Date(b.date_joined),
    },
    {
      title: '狀態',
      key: 'status',
      width: 100,
      render: () => <Tag color="orange">待審核</Tag>,
    },
    {
      title: '操作',
      key: 'actions',
      width: 200,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看詳情">
            <Button
              icon={<EyeOutlined />}
              onClick={() => handleViewDetail(record)}
              size="small"
            />
          </Tooltip>
          <Button
            type="primary"
            icon={<CheckOutlined />}
            onClick={() => handleApprove(record)}
            size="small"
          >
            批准
          </Button>
          <Button
            danger
            icon={<CloseOutlined />}
            onClick={() => handleReject(record)}
            size="small"
          >
            拒絕
          </Button>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <Card
        title={
          <Space>
            <span style={{ fontSize: '18px', fontWeight: 'bold' }}>待審核用戶</span>
            <Tag color="orange">{pendingUsers.length}</Tag>
          </Space>
        }
        extra={
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchPendingUsers}
            loading={loading}
          >
            重新整理
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={pendingUsers}
          rowKey="id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>

      {/* 詳情 Modal */}
      <Modal
        title={`用戶申請詳情 - ${viewingUser?.username}`}
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            關閉
          </Button>,
          <Button
            key="approve"
            type="primary"
            icon={<CheckOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              handleApprove(viewingUser);
            }}
          >
            批准
          </Button>,
          <Button
            key="reject"
            danger
            icon={<CloseOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              handleReject(viewingUser);
            }}
          >
            拒絕
          </Button>,
        ]}
        width={700}
      >
        {viewingUser && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="用戶名">
              <strong>{viewingUser.username}</strong>
            </Descriptions.Item>
            <Descriptions.Item label="Email">
              {viewingUser.email}
            </Descriptions.Item>
            <Descriptions.Item label="姓名">
              {[viewingUser.first_name, viewingUser.last_name].filter(Boolean).join(' ') || '-'}
            </Descriptions.Item>
            <Descriptions.Item label="申請部門">
              <Tag color="blue">{viewingUser.application_department}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="申請理由">
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {viewingUser.application_reason}
              </div>
            </Descriptions.Item>
            <Descriptions.Item label="申請時間">
              {new Date(viewingUser.date_joined).toLocaleString('zh-TW')}
            </Descriptions.Item>
            <Descriptions.Item label="帳號狀態">
              <Tag color="orange">待審核</Tag>
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>

      {/* 拒絕原因 Modal */}
      <Modal
        title="拒絕申請"
        open={rejectModalVisible}
        onOk={confirmReject}
        onCancel={() => {
          setRejectModalVisible(false);
          setRejectionReason('');
        }}
        okText="確認拒絕"
        cancelText="取消"
        okButtonProps={{ danger: true }}
      >
        <p>拒絕用戶：<strong>{rejectingUser?.username}</strong></p>
        <p style={{ marginTop: '12px', color: '#666' }}>
          請輸入拒絕原因（會通知給用戶）：
        </p>
        <TextArea
          rows={4}
          placeholder="請輸入拒絕原因，例如：資料不完整、非本公司員工等"
          value={rejectionReason}
          onChange={(e) => setRejectionReason(e.target.value)}
          showCount
          maxLength={500}
        />
      </Modal>
    </div>
  );
};

export default PendingUsersPage;
