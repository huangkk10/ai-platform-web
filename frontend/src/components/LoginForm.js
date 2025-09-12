import React, { useState } from 'react';
import { Modal, Form, Input, Button, Alert, Space } from 'antd';
import { UserOutlined, LockOutlined, LoginOutlined } from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';

const LoginForm = ({ visible, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login } = useAuth();

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
        setError(result.message);
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
        <Space>
          <LoginOutlined />
          <span>用戶登入</span>
        </Space>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={400}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
        autoComplete="off"
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
            { required: true, message: '請輸入密碼' },
            { min: 6, message: '密碼至少需要6個字符' }
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

      <div style={{ 
        marginTop: 16, 
        padding: 12, 
        background: '#f6f8fa', 
        borderRadius: 4,
        fontSize: 12,
        color: '#666'
      }}>
        <div><strong>測試帳號：</strong></div>
        <div>用戶名：admin</div>
        <div>密碼：admin123</div>
      </div>
    </Modal>
  );
};

export default LoginForm;