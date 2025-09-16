import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, UserAddOutlined } from '@ant-design/icons';
import axios from 'axios';

const RegisterForm = ({ visible, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      
      const response = await axios.post('/api/auth/register/', {
        username: values.username,
        password: values.password,
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name
      }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.data.success) {
        message.success(response.data.message);
        form.resetFields();
        onClose();
        if (onSuccess) {
          onSuccess(response.data.message);
        }
      } else {
        message.error(response.data.message || '註冊失敗');
      }
    } catch (error) {
      console.error('Registration error:', error);
      
      if (error.response?.data?.message) {
        message.error(error.response.data.message);
      } else if (error.response?.status === 400) {
        message.error('請檢查輸入的資料格式');
      } else if (error.response?.status === 500) {
        message.error('伺服器錯誤，請稍後再試');
      } else {
        message.error('註冊失敗，請稍後再試');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = () => {
    form.resetFields();
    onClose();
  };

  return (
    <Modal
      title={
        <div style={{ textAlign: 'center' }}>
          <UserAddOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          用戶註冊
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={450}
      centered
    >
      <Divider />
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
        autoComplete="off"
      >
        <Form.Item
          name="username"
          label="用戶名"
          rules={[
            { required: true, message: '請輸入用戶名' },
            { min: 3, message: '用戶名至少需要 3 個字符' },
            { max: 20, message: '用戶名不能超過 20 個字符' },
            { pattern: /^[a-zA-Z0-9_-]+$/, message: '用戶名只能包含字母、數字、下劃線和短橫線' }
          ]}
        >
          <Input 
            prefix={<UserOutlined />} 
            placeholder="請輸入用戶名（3-20個字符）"
            autoComplete="off"
          />
        </Form.Item>

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
            autoComplete="off"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="密碼"
          rules={[
            { required: true, message: '請輸入密碼' },
            { max: 128, message: '密碼不能超過 128 個字符' }
          ]}
        >
          <Input.Password 
            prefix={<LockOutlined />} 
            placeholder="請輸入密碼"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="confirmPassword"
          label="確認密碼"
          dependencies={['password']}
          rules={[
            { required: true, message: '請確認密碼' },
            ({ getFieldValue }) => ({
              validator(_, value) {
                if (!value || getFieldValue('password') === value) {
                  return Promise.resolve();
                }
                return Promise.reject(new Error('兩次輸入的密碼不一致'));
              },
            }),
          ]}
        >
          <Input.Password 
            prefix={<LockOutlined />} 
            placeholder="請再次輸入密碼"
            autoComplete="new-password"
          />
        </Form.Item>

        <Form.Item
          name="first_name"
          label="姓名"
        >
          <Input 
            placeholder="請輸入姓名（可選）"
            autoComplete="off"
          />
        </Form.Item>

        <Form.Item
          name="last_name"
          label="姓氏"
        >
          <Input 
            placeholder="請輸入姓氏（可選）"
            autoComplete="off"
          />
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: '24px' }}>
          <Space style={{ width: '100%', justifyContent: 'center' }} size="large">
            <Button onClick={handleCancel} size="large">
              取消
            </Button>
            <Button 
              type="primary" 
              htmlType="submit" 
              loading={loading}
              size="large"
              style={{ minWidth: '120px' }}
            >
              註冊
            </Button>
          </Space>
        </Form.Item>
      </Form>
      
      <Divider />
      
      <div style={{ textAlign: 'center', color: '#666' }}>
        <small>註冊即表示您同意我們的服務條款和隱私政策</small>
      </div>
    </Modal>
  );
};

export default RegisterForm;