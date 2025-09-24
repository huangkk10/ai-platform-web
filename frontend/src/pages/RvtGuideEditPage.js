import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Select, 
  Button, 
  Space, 
  Typography,
  Row,
  Col,
  message,
  Spin
} from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const RvtGuideEditPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!id);
  
  const isEdit = !!id;

  // 分類選項
  const mainCategoryOptions = [
    { value: 'system_architecture', label: '系統架構' },
    { value: 'environment_setup', label: '環境準備' },
    { value: 'configuration_management', label: '配置管理' },
    { value: 'test_case_management', label: '測項管理' },
    { value: 'operation_flow', label: '操作流程' },
    { value: 'troubleshooting', label: '故障排除' },
    { value: 'contact_support', label: '聯絡支援' }
  ];

  const questionTypeOptions = [
    { value: 'operation_guide', label: '操作指南' },
    { value: 'parameter_explanation', label: '參數說明' },
    { value: 'troubleshooting', label: '故障排除' },
    { value: 'concept_explanation', label: '概念說明' }
  ];

  // 載入資料 (編輯模式)
  useEffect(() => {
    if (id) {
      loadGuideData();
    }
  }, [id]);

  const loadGuideData = async () => {
    try {
      setInitialLoading(true);
      const response = await axios.get(`/api/rvt-guides/${id}/`);
      
      if (response.data) {
        form.setFieldsValue(response.data);
      } else {
        message.error('載入資料失敗');
        navigate('/knowledge/rvt-log');
      }
    } catch (error) {
      console.error('載入失敗:', error);
      message.error('載入資料失敗');
      navigate('/knowledge/rvt-log');
    } finally {
      setInitialLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      
      if (isEdit) {
        await axios.put(`/api/rvt-guides/${id}/`, values);
        message.success('更新成功');
      } else {
        await axios.post('/api/rvt-guides/', values);
        message.success('新增成功');
      }
      
      navigate('/knowledge/rvt-log');
    } catch (error) {
      console.error('操作失敗:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.message || 
                          (isEdit ? '更新失敗' : '新增失敗');
      message.error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    navigate('/knowledge/rvt-log');
  };

  if (initialLoading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" tip="載入中..." />
      </div>
    );
  }

  return (
    <div style={{ 
      position: 'relative',
      minHeight: 'calc(100vh - 64px)', // 減去 TopHeader 高度
      paddingBottom: '80px', // 為 fixed footer 留空間
      overflow: 'hidden' // 限制 fixed 元素在此容器內
    }}>
      {/* 內容區域 */}
      <div style={{ 
        padding: '24px',
        height: 'calc(100vh - 144px)', // TopHeader 64px + Footer 80px
        overflowY: 'auto'
      }}>
        <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
          {/* 編輯表單 */}
          <Card>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSubmit}
              size="large"
            >
              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item
                    name="title"
                    label="標題"
                    rules={[{ required: true, message: '請輸入標題' }]}
                  >
                    <Input 
                      placeholder="請輸入指導文檔標題" 
                      style={{ fontSize: '16px' }}
                    />
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={24}>
                <Col span={12}>
                  <Form.Item
                    name="main_category"
                    label="主分類"
                    rules={[{ required: true, message: '請選擇主分類' }]}
                  >
                    <Select placeholder="請選擇主分類">
                      {mainCategoryOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item
                    name="question_type"
                    label="問題類型"
                    rules={[{ required: true, message: '請選擇問題類型' }]}
                  >
                    <Select placeholder="請選擇問題類型">
                      {questionTypeOptions.map(option => (
                        <Option key={option.value} value={option.value}>
                          {option.label}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              <Row gutter={24}>
                <Col span={24}>
                  <Form.Item
                    name="content"
                    label="內容"
                    rules={[{ required: true, message: '請輸入內容' }]}
                  >
                    <TextArea 
                      rows={20}
                      placeholder="請輸入指導文檔內容&#10;&#10;支援 Markdown 格式：&#10;# 標題&#10;## 副標題&#10;- 項目列表&#10;**粗體文字**&#10;*斜體文字*&#10;`程式碼`&#10;```&#10;程式碼區塊&#10;```"
                      showCount
                      style={{ 
                        fontSize: '14px',
                        lineHeight: '1.6',
                        fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
                      }}
                    />
                  </Form.Item>
                </Col>
              </Row>
            </Form>
          </Card>
        </div>
      </div>

      {/* Fixed Footer - 相對於父容器固定 */}
      <div style={{
        position: 'absolute',
        bottom: '0',
        left: '0',
        right: '0',
        height: '80px',
        backgroundColor: 'white',
        borderTop: '1px solid #f0f0f0',
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '0 24px',
        boxShadow: '0 -2px 4px rgba(0,0,0,0.1)'
      }}>
        <Space size="large">
          <Button 
            onClick={handleBack}
            size="large"
            style={{ minWidth: '100px' }}
          >
            取消
          </Button>
          <Button 
            type="primary" 
            onClick={() => form.submit()}
            icon={<SaveOutlined />}
            loading={loading}
            size="large"
            style={{ minWidth: '120px' }}
          >
            {isEdit ? '更新' : '新增'}
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default RvtGuideEditPage;