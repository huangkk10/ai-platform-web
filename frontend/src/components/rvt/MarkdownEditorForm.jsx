import React, { useState, useEffect } from 'react';
import { Modal, Form, Input, Select, message, Button, Space } from 'antd';
import { SaveOutlined, EyeOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';

const { Option } = Select;

// 初始化 Markdown 解析器
const mdParser = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

/**
 * 新的 Markdown 編輯器組件 - 使用 react-markdown-editor-lite
 * 用於編輯 RVT Guide 內容，提供豐富的 Markdown 編輯體驗
 */
const MarkdownEditorForm = ({ 
  visible, 
  onCancel, 
  onSave, 
  initialData = null,
  loading = false 
}) => {
  const [form] = Form.useForm();
  const [markdownContent, setMarkdownContent] = useState('');
  const [previewMode, setPreviewMode] = useState(false);

  // 當初始數據變化時更新表單
  useEffect(() => {
    if (initialData) {
      form.setFieldsValue({
        title: initialData.title || '',
        category: initialData.category || '',
        problem_type: initialData.problem_type || '',
        description: initialData.description || '',
      });
      setMarkdownContent(initialData.content || '');
    } else {
      // 新建時清空表單
      form.resetFields();
      setMarkdownContent('');
    }
  }, [initialData, form]);

  // Markdown 編輯器配置
  const editorConfig = {
    view: {
      menu: true,
      md: true,
      html: false,
    },
    canView: {
      menu: true,
      md: true,
      html: true,
      both: false,
      fullScreen: true,
      hideMenu: true,
    },
    markdownOptions: {
      html: true,
      linkify: true,
      typographer: true,
    },
    syncScrollMode: ['leftFollowRight', 'rightFollowLeft'],
  };

  // 處理 Markdown 內容變化
  const handleEditorChange = ({ html, text }) => {
    setMarkdownContent(text);
  };

  // 處理表單提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      const formData = {
        ...values,
        content: markdownContent,
      };

      console.log('📝 新 Markdown 編輯器提交數據:', formData);
      
      await onSave(formData);
      
      // 重置表單
      form.resetFields();
      setMarkdownContent('');
      
    } catch (error) {
      console.error('表單驗證失敗:', error);
      message.error('請檢查表單內容');
    }
  };

  // 切換預覽模式
  const togglePreview = () => {
    setPreviewMode(!previewMode);
  };

  return (
    <Modal
      title={
        <Space>
          <span>{initialData ? '編輯 RVT Guide (Markdown 編輯器)' : '新增 RVT Guide (Markdown 編輯器)'}</span>
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={togglePreview}
            title={previewMode ? '切換到編輯模式' : '切換到預覽模式'}
          >
            {previewMode ? '編輯' : '預覽'}
          </Button>
        </Space>
      }
      open={visible}
      onCancel={onCancel}
      width={1200}
      style={{ top: 20 }}
      footer={[
        <Button key="cancel" onClick={onCancel}>
          取消
        </Button>,
        <Button 
          key="save" 
          type="primary" 
          icon={<SaveOutlined />}
          loading={loading}
          onClick={handleSubmit}
        >
          {initialData ? '更新' : '新增'}
        </Button>,
      ]}
      destroyOnClose
    >
      <Form
        form={form}
        layout="vertical"
        style={{ marginBottom: '16px' }}
      >
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <Form.Item
            name="title"
            label="標題"
            rules={[
              { required: true, message: '請輸入標題' },
              { min: 2, message: '標題至少需要 2 個字符' },
            ]}
          >
            <Input placeholder="請輸入指導標題" />
          </Form.Item>

          <Form.Item
            name="category"
            label="分類"
            rules={[{ required: true, message: '請選擇分類' }]}
          >
            <Select placeholder="請選擇分類">
              <Option value="測試指導">測試指導</Option>
              <Option value="故障排除">故障排除</Option>
              <Option value="操作手冊">操作手冊</Option>
              <Option value="常見問題">常見問題</Option>
              <Option value="最佳實踐">最佳實踐</Option>
              <Option value="工具使用">工具使用</Option>
              <Option value="環境設置">環境設置</Option>
            </Select>
          </Form.Item>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
          <Form.Item
            name="problem_type"
            label="問題類型"
          >
            <Select placeholder="請選擇問題類型" allowClear>
              <Option value="硬體問題">硬體問題</Option>
              <Option value="軟體問題">軟體問題</Option>
              <Option value="網路問題">網路問題</Option>
              <Option value="性能問題">性能問題</Option>
              <Option value="配置問題">配置問題</Option>
              <Option value="相容性問題">相容性問題</Option>
              <Option value="操作問題">操作問題</Option>
              <Option value="其他">其他</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="簡短描述"
          >
            <Input placeholder="簡短描述問題或指導內容" />
          </Form.Item>
        </div>
      </Form>

      {/* Markdown 編輯器區域 */}
      <div style={{ border: '1px solid #d9d9d9', borderRadius: '6px' }}>
        <div style={{ 
          padding: '8px 12px', 
          borderBottom: '1px solid #d9d9d9', 
          backgroundColor: '#fafafa',
          fontSize: '14px',
          fontWeight: 500,
          color: '#666'
        }}>
          內容編輯 (支援 Markdown 語法)
        </div>
        
        {previewMode ? (
          // 預覽模式
          <div 
            style={{ 
              minHeight: '400px', 
              padding: '16px',
              backgroundColor: '#fff'
            }}
            className="markdown-preview"
            dangerouslySetInnerHTML={{ 
              __html: mdParser.render(markdownContent) 
            }}
          />
        ) : (
          // 編輯模式
          <MdEditor
            value={markdownContent}
            style={{ height: '400px' }}
            renderHTML={(text) => mdParser.render(text)}
            onChange={handleEditorChange}
            config={editorConfig}
            placeholder="請輸入 Markdown 格式的內容..."
          />
        )}
      </div>

      {/* 使用提示 */}
      <div style={{ 
        marginTop: '12px', 
        padding: '8px 12px', 
        backgroundColor: '#f6ffed', 
        border: '1px solid #b7eb8f', 
        borderRadius: '4px',
        fontSize: '12px',
        color: '#52c41a'
      }}>
        💡 提示：支援 Markdown 語法，包括標題、列表、代碼塊、表格、鏈接等。使用工具欄快速插入常用格式。
      </div>
    </Modal>
  );
};

export default MarkdownEditorForm;