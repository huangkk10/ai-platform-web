import React, { useState } from 'react';
import { Modal, Form, Input, Button, Alert, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined, UserAddOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const LoginForm = ({ visible, onClose, onSuccess, onRegister }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

  // 當模態框顯示時重置表單
  React.useEffect(() => {
    if (visible) {
      form.resetFields();
      setError('');
    }
  }, [visible, form]);

  const handleSubmit = async (values) => {
    setLoading(true);
    setError('');

    try {
      const result = await login(values.username, values.password);
      
      if (result.success) {
        form.resetFields();
        setError('');
        onSuccess?.(result.message);
        onClose();
      } else {
        // 🆕 根據審核狀態顯示不同訊息
        if (result.status === 'pending') {
          Modal.warning({
            title: '帳號待審核',
            content: (
              <div>
                <p>{result.message}</p>
                <p style={{ marginTop: '12px', color: '#666' }}>
                  管理員會盡快審核您的申請，審核通過後會收到通知。
                </p>
              </div>
            ),
            okText: '我知道了',
          });
          setError('');
        } else if (result.status === 'rejected') {
          Modal.error({
            title: '帳號申請已被拒絕',
            content: (
              <div>
                <p>{result.message}</p>
                {result.rejection_reason && (
                  <p style={{ marginTop: '12px', color: '#666' }}>
                    拒絕原因：{result.rejection_reason}
                  </p>
                )}
                <p style={{ marginTop: '12px', color: '#999' }}>
                  如有疑問，請聯絡系統管理員。
                </p>
              </div>
            ),
            okText: '我知道了',
          });
          setError('');
        } else if (result.status === 'suspended') {
          Modal.error({
            title: '帳號已停用',
            content: (
              <div>
                <p>{result.message}</p>
                <p style={{ marginTop: '12px', color: '#999' }}>
                  如有疑問，請聯絡系統管理員。
                </p>
              </div>
            ),
            okText: '我知道了',
          });
          setError('');
        } else {
          setError(result.message);
        }
      }
    } catch (error) {
      setError('登入失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    setError('');
    onClose();
  };

  return (
    <Modal
      title={
        <div style={{ 
          textAlign: 'center', 
          fontSize: '18px', 
          fontWeight: 'bold'
        }}>
          <LoginOutlined style={{ marginRight: '8px', fontSize: '18px' }} />
          用戶登入
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={600}
      centered
      destroyOnClose
      styles={{
        body: { 
          padding: '24px 32px',
          backgroundColor: '#fafafa'
        },
        header: {
          backgroundColor: '#f0f8ff',
          borderBottom: '1px solid #d9d9d9'
        }
      }}
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
        autoComplete="off"
        style={{ maxWidth: '400px', margin: '0 auto' }}
      >
        {error && (
          <Alert
            message={error}
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
        )}

        <Form.Item
          name="username"
          label="用戶名"
          rules={[
            { required: true, message: '請輸入用戶名' },
            { min: 3, message: '用戶名至少需要3個字符' }
          ]}
        >
          <Input
            prefix={<UserOutlined />}
            placeholder="請輸入用戶名"
            autoComplete="username"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="密碼"
          rules={[
            { required: true, message: '請輸入密碼' }
          ]}
        >
          <Input.Password
            prefix={<LockOutlined />}
            placeholder="請輸入密碼"
            autoComplete="current-password"
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0 }}>
          <Space style={{ width: '100%', justifyContent: 'space-between' }}>
            <Button onClick={handleCancel}>
              取消
            </Button>
            <Button
              type="primary"
              htmlType="submit"
              loading={loading}
              icon={<LoginOutlined />}
            >
              {loading ? '登入中...' : '登入'}
            </Button>
          </Space>
        </Form.Item>
      </Form>

      {onRegister && (
        <>
          <Divider style={{ margin: '16px 0' }}>或</Divider>
          <div style={{ textAlign: 'center' }}>
            <Button 
              type="link" 
              icon={<UserAddOutlined />}
              onClick={() => {
                onClose();
                onRegister();
              }}
              style={{ padding: 0 }}
            >
              沒有帳號？立即註冊
            </Button>
          </div>
        </>
      )}
    </Modal>
  );
};

export default LoginForm;