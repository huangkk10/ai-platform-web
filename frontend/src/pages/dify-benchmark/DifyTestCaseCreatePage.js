import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Card, Space, Switch, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import difyBenchmarkApi from '../../services/difyBenchmarkApi';
import KeywordManager from './components/KeywordManager';

const { TextArea } = Input;
const { Option } = Select;

const DifyTestCaseCreatePage = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [keywords, setKeywords] = useState([]);

  // 監聽保存事件（來自 TopHeader 按鈕）
  useEffect(() => {
    const handleSaveEvent = () => {
      console.log('收到儲存事件 - 觸發表單提交');
      form.submit();
    };

    window.addEventListener('test-case-form-save', handleSaveEvent);
    
    return () => {
      window.removeEventListener('test-case-form-save', handleSaveEvent);
    };
  }, [form]);

  // 處理表單提交
  const handleSubmit = async (values) => {
    // 驗證關鍵字是否已添加
    if (keywords.length === 0) {
      message.warning('請至少添加一個答案關鍵字');
      return;
    }

    setLoading(true);
    try {
      const payload = {
        ...values,
        answer_keywords: keywords, // 使用 state 中的關鍵字
        expected_answer: '', // 自動設為空字串（評分不使用此欄位）
        test_type: 'vsa',
      };

      console.log('提交資料:', payload);
      await difyBenchmarkApi.createDifyTestCase(payload);
      message.success('測試案例新增成功');
      
      // 延遲一下再跳轉，讓用戶看到成功訊息
      setTimeout(() => {
        navigate('/benchmark/dify/test-cases');
      }, 500);
    } catch (error) {
      console.error('新增失敗:', error);
      message.error(`新增失敗: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '24px', 
      maxWidth: '1200px', 
      margin: '0 auto',
      background: '#f5f5f5',
      minHeight: 'calc(100vh - 64px)'
    }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        initialValues={{
          difficulty_level: 'medium',
          is_active: true,
          max_score: 100,
        }}
      >
        {/* 基本資訊卡片 */}
        <Card 
          title="📝 基本資訊" 
          style={{ marginBottom: '24px' }}
          headStyle={{ fontSize: '18px', fontWeight: 600 }}
        >
          <Form.Item
            name="question"
            label="測試問題"
            rules={[{ required: true, message: '請輸入測試問題' }]}
          >
            <TextArea
              rows={6}
              placeholder="輸入測試問題內容..."
              maxLength={1000}
              showCount
              style={{ fontSize: '15px' }}
            />
          </Form.Item>

          <Form.Item
            name="difficulty_level"
            label="難度等級"
            rules={[{ required: true, message: '請選擇難度等級' }]}
          >
            <Select placeholder="選擇難度" size="large">
              <Option value="easy">簡單</Option>
              <Option value="medium">中等</Option>
              <Option value="hard">困難</Option>
            </Select>
          </Form.Item>
        </Card>

        {/* VSA 測試配置卡片 */}
        <Card 
          title="🎯 VSA 測試配置" 
          style={{ marginBottom: '24px' }}
          headStyle={{ fontSize: '18px', fontWeight: 600 }}
        >
          {/* 關鍵字管理組件 */}
          <KeywordManager 
            keywords={keywords} 
            onChange={setKeywords}
          />

          <Form.Item
            name="max_score"
            label="滿分"
            tooltip="測試案例的最高分數"
          >
            <Input 
              type="number" 
              min={1} 
              max={1000} 
              size="large"
              style={{ width: '200px' }}
              placeholder="預設 100 分"
            />
          </Form.Item>
        </Card>

        {/* 進階選項卡片 */}
        <Card 
          title="⚙️ 進階選項" 
          style={{ marginBottom: '24px' }}
          headStyle={{ fontSize: '18px', fontWeight: 600 }}
        >
          <Form.Item name="notes" label="備註">
            <TextArea
              rows={4}
              placeholder="其他說明或注意事項..."
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item 
            name="is_active" 
            label="啟用狀態" 
            valuePropName="checked"
          >
            <Switch checkedChildren="啟用" unCheckedChildren="停用" />
          </Form.Item>
        </Card>

        {/* 底部操作按鈕 */}
        <div style={{ 
          textAlign: 'right', 
          padding: '16px 24px',
          background: '#fff',
          position: 'sticky',
          bottom: 0,
          borderTop: '1px solid #f0f0f0',
          zIndex: 10,
          marginLeft: '-24px',
          marginRight: '-24px',
          marginBottom: '-24px',
          boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.05)'
        }}>
          <Space size="middle">
            <Button 
              size="large"
              onClick={() => navigate('/benchmark/dify/test-cases')}
              disabled={loading}
            >
              取消
            </Button>
            <Button 
              type="primary" 
              size="large"
              loading={loading}
              onClick={() => form.submit()}
            >
              儲存測試案例
            </Button>
          </Space>
        </div>
      </Form>
    </div>
  );
};

export default DifyTestCaseCreatePage;
