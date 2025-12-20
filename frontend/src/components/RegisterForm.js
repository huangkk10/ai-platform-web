import React, { useState } from 'react';
import { Modal, Form, Input, Button, message, Space, Divider } from 'antd';
import { UserOutlined, LockOutlined, MailOutlined, UserAddOutlined } from '@ant-design/icons';
import axios from 'axios';

const RegisterForm = ({ visible, onClose, onSuccess }) => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);

  // 調試：當模態框顯示時在控制台輸出
  React.useEffect(() => {
    if (visible) {
      console.log('🚀 REGISTER MODAL IS NOW VISIBLE! 🚀');
      console.log('Modal width should be 95vw with cyan border');
    }
  }, [visible]);

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      
      const response = await axios.post('/api/auth/register/', {
        username: values.username,
        password: values.password,
        email: values.email,
        first_name: values.first_name,
        last_name: values.last_name,
        application_department: values.application_department,  // 🆕 申請部門
        application_reason: values.application_reason           // 🆕 申請理由
      }, {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (response.data.success) {
        // 🆕 顯示審核等待訊息
        Modal.success({
          title: '註冊申請已提交',
          content: (
            <div>
              <p>{response.data.message}</p>
              <p style={{ marginTop: '12px', color: '#666' }}>
                管理員會盡快審核您的申請，審核通過後您將收到通知。
              </p>
              <p style={{ marginTop: '8px', color: '#999' }}>
                請記住您的用戶名：<strong>{values.username}</strong>
              </p>
            </div>
          ),
          okText: '我知道了',
        });
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
      
      if (error.response?.data?.error) {
        message.error(error.response.data.error);
      } else if (error.response?.data?.message) {
        message.error(error.response.data.message);
      } else if (error.response?.data?.errors) {
        // 顯示具體的驗證錯誤
        const errorMessages = Object.values(error.response.data.errors).join(', ');
        message.error(`註冊失敗: ${errorMessages}`);
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
        <div style={{ 
          textAlign: 'center', 
          fontSize: '18px', 
          fontWeight: 'bold'
        }}>
          <UserAddOutlined style={{ marginRight: '8px', fontSize: '18px' }} />
          用戶註冊
        </div>
      }
      open={visible}
      onCancel={handleCancel}
      footer={null}
      width={700}
      centered
      styles={{
        body: { 
          padding: '24px 32px',
          backgroundColor: '#f6ffed'
        },
        header: {
          backgroundColor: '#f6ffed',
          borderBottom: '1px solid #d9d9d9'
        }
      }}
    >
      <Divider />
      
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        size="large"
        autoComplete="off"
        style={{ maxWidth: '500px', margin: '0 auto' }}
      >
        <Form.Item
          name="username"
          label="用戶名"
          rules={[
            { required: true, message: '請輸入用戶名' },
            { min: 3, message: '用戶名至少需要 3 個字符' },
            { max: 150, message: '用戶名不能超過 150 個字符' },
            { pattern: /^[a-zA-Z0-9_-]{3,150}$/, message: '用戶名只能包含字母、數字、下劃線和短橫線（3-150個字符）' },
            {
              validator: (_, value) => {
                if (!value) return Promise.resolve();
                if (value.includes('@') || value.includes('.')) {
                  return Promise.reject(new Error('用戶名不能是 Email 地址，請輸入獨特的用戶名'));
                }
                return Promise.resolve();
              }
            }
          ]}
        >
          <Input 
            prefix={<UserOutlined />} 
            placeholder="請輸入用戶名（不能是Email，3-150個字符）"
            autoComplete="username"
          />
        </Form.Item>

        <Form.Item
          name="email"
          label="電子郵件"
          rules={[
            { required: true, message: '請輸入電子郵件' },
            { type: 'email', message: '請輸入有效的電子郵件格式' },
            { max: 254, message: 'Email 地址不能超過 254 個字符' }
          ]}
        >
          <Input 
            prefix={<MailOutlined />} 
            placeholder="請輸入電子郵件"
            autoComplete="email"
          />
        </Form.Item>

        <Form.Item
          name="password"
          label="密碼"
          rules={[
            { required: true, message: '請輸入密碼' },
            { min: 6, message: '密碼至少需要 6 個字符' },
            { max: 128, message: '密碼不能超過 128 個字符' }
          ]}
        >
          <Input.Password 
            prefix={<LockOutlined />} 
            placeholder="請輸入密碼（至少 6 個字符）"
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
          rules={[
            { max: 30, message: '姓名不能超過 30 個字符' }
          ]}
        >
          <Input 
            placeholder="請輸入姓名（可選）"
            autoComplete="given-name"
          />
        </Form.Item>

        <Form.Item
          name="last_name"
          label="姓氏"
          rules={[
            { max: 30, message: '姓氏不能超過 30 個字符' }
          ]}
        >
          <Input 
            placeholder="請輸入姓氏（可選）"
            autoComplete="family-name"
          />
        </Form.Item>

        <Divider orientation="left">申請資訊</Divider>

        <Form.Item
          name="application_department"
          label="申請部門"
          rules={[
            { required: true, message: '請輸入您的部門' },
            { max: 100, message: '部門名稱不能超過 100 個字符' }
          ]}
          tooltip="請填寫您所屬的部門，例如：測試部、研發部、QA部"
        >
          <Input 
            placeholder="例如：測試部、研發部、QA部"
            autoComplete="organization"
          />
        </Form.Item>

        <Form.Item
          name="application_reason"
          label="申請理由"
          rules={[
            { required: true, message: '請說明您需要使用此系統的原因' },
            { min: 10, message: '申請理由至少需要 10 個字符' },
            { max: 500, message: '申請理由不能超過 500 個字符' }
          ]}
          tooltip="請簡述您需要使用此系統的工作需求或用途"
        >
          <Input.TextArea 
            rows={4}
            placeholder="請簡述您需要使用此系統的原因，例如：需要進行 Protocol 測試、使用 AI OCR 功能等（至少 10 個字符）"
            showCount
            maxLength={500}
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