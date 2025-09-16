import React, { useState } from 'react';
import { 
  Modal, 
  Form, 
  Input, 
  Button, 
  message, 
  Typography, 
  Divider,
  Space,
  Card,
  Row,
  Col
} from 'antd';
import { 
  LockOutlined, 
  UserOutlined,
  SafetyOutlined 
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const { Title, Text, Paragraph } = Typography;

const AccountSettingsModal = ({ visible, onClose }) => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [passwordForm] = Form.useForm();

  // 更改密碼
  const handleChangePassword = async (values) => {
    if (values.newPassword !== values.confirmPassword) {
      message.error('新密碼與確認密碼不一致');
      return;
    }

    setLoading(true);
    try {
      const response = await axios.post('/api/auth/change-password/', {
        old_password: values.currentPassword,
        new_password: values.newPassword
      }, {
        withCredentials: true
      });

      if (response.status === 200) {
        message.success('密碼更改成功！');
        passwordForm.resetFields();
      }
    } catch (error) {
      if (error.response?.status === 400) {
        if (error.response.data?.old_password) {
          message.error('目前密碼不正確');
        } else if (error.response.data?.new_password) {
          message.error('新密碼格式不符合要求');
        } else {
          message.error('密碼更改失敗：' + (error.response.data?.detail || '請檢查輸入資訊'));
        }
      } else {
        message.error('系統錯誤，請稍後再試');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleModalClose = () => {
    passwordForm.resetFields();
    onClose();
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <SafetyOutlined style={{ color: '#1890ff' }} />
          <span>帳戶設定</span>
        </div>
      }
      open={visible}
      onCancel={handleModalClose}
      footer={null}
      width={600}
      destroyOnClose
    >
      <div style={{ padding: '8px 0' }}>
        {/* 帳戶資訊 */}
        <Card size="small" style={{ marginBottom: '24px', backgroundColor: '#fafafa' }}>
          <Title level={4} style={{ margin: '0 0 16px 0', color: '#1890ff' }}>
            <UserOutlined style={{ marginRight: '8px' }} />
            帳戶資訊
          </Title>
          <Row gutter={16}>
            <Col span={12}>
              <div style={{ marginBottom: '12px' }}>
                <Text strong>用戶名：</Text>
                <br />
                <Text>{user?.username || '未設定'}</Text>
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '12px' }}>
                <Text strong>郵箱：</Text>
                <br />
                <Text>{user?.email || '未設定'}</Text>
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '12px' }}>
                <Text strong>姓名：</Text>
                <br />
                <Text>
                  {user?.first_name && user?.last_name 
                    ? `${user.first_name} ${user.last_name}` 
                    : '未設定'
                  }
                </Text>
              </div>
            </Col>
            <Col span={12}>
              <div style={{ marginBottom: '12px' }}>
                <Text strong>角色：</Text>
                <br />
                <Text type={user?.is_superuser ? 'success' : user?.is_staff ? 'warning' : 'secondary'}>
                  {user?.is_superuser ? '超級管理員' : user?.is_staff ? '管理員' : '一般用戶'}
                </Text>
              </div>
            </Col>
          </Row>
        </Card>

        <Divider orientation="left">
          <LockOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          更改密碼
        </Divider>

        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handleChangePassword}
        >
          <Form.Item
            name="currentPassword"
            label="目前密碼"
            rules={[
              { required: true, message: '請輸入目前密碼' }
            ]}
          >
            <Input.Password
              placeholder="請輸入目前密碼"
              prefix={<LockOutlined />}
            />
          </Form.Item>

          <Form.Item
            name="newPassword"
            label="新密碼"
            rules={[
              { required: true, message: '請輸入新密碼' }
            ]}
          >
            <Input.Password
              placeholder="請輸入新密碼"
              prefix={<LockOutlined />}
            />
          </Form.Item>

          <Form.Item
            name="confirmPassword"
            label="確認新密碼"
            dependencies={['newPassword']}
            rules={[
              { required: true, message: '請確認新密碼' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('newPassword') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('兩次輸入的密碼不一致'));
                },
              }),
            ]}
          >
            <Input.Password
              placeholder="請再次輸入新密碼"
              prefix={<LockOutlined />}
            />
          </Form.Item>

          <div style={{ marginTop: '24px' }}>
            <Space>
              <Button 
                type="primary" 
                htmlType="submit" 
                loading={loading}
                icon={<SafetyOutlined />}
              >
                更改密碼
              </Button>
              <Button onClick={handleModalClose}>
                取消
              </Button>
            </Space>
          </div>
        </Form>

        <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f6ffed', borderRadius: '6px', border: '1px solid #b7eb8f' }}>
          <Paragraph style={{ margin: 0, fontSize: '12px', color: '#52c41a' }}>
            <SafetyOutlined style={{ marginRight: '4px' }} />
            <strong>密碼安全提示：</strong>
            <br />
            • 避免使用個人資訊或常見密碼
            <br />
            • 定期更換密碼以保護帳戶安全
          </Paragraph>
        </div>
      </div>
    </Modal>
  );
};

export default AccountSettingsModal;