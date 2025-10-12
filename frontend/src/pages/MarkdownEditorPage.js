import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Input, message, Spin, Card, Space } from 'antd';
import { SaveOutlined, ArrowLeftOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';
import axios from 'axios';

// 初始化 Markdown 解析器
const mdParser = new MarkdownIt();

/**
 * 整頁 Markdown 編輯器頁面
 * 路由: /knowledge/rvt-guide/markdown-edit/:id 或 /knowledge/rvt-guide/markdown-create
 */
const MarkdownEditorPage = () => {
  const navigate = useNavigate();
  const { id } = useParams(); // 如果是編輯模式，會有 id
  const isEditMode = Boolean(id);

  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: ''
  });

  // 載入現有記錄數據（編輯模式）
  useEffect(() => {
    if (isEditMode) {
      loadGuideData();
    }
  }, [id, isEditMode]);

  const loadGuideData = async () => {
    setLoading(true);
    try {
      console.log('🔍 載入 RVT Guide 資料，ID:', id);
      const response = await axios.get(`/api/rvt-guides/${id}/`);
      
      console.log('📄 載入的資料:', response.data);
      
      setFormData({
        title: response.data.title || '',
        content: response.data.content || ''
      });
      
      message.success('資料載入成功');
    } catch (error) {
      console.error('❌ 載入資料失敗:', error);
      message.error('載入資料失敗');
      // 如果載入失敗，返回列表頁
      navigate('/knowledge/rvt-guide');
    } finally {
      setLoading(false);
    }
  };

  // 處理 Markdown 編輯器內容改變
  const handleEditorChange = ({ text }) => {
    setFormData(prev => ({
      ...prev,
      content: text
    }));
  };

  // 處理標題改變
  const handleTitleChange = (e) => {
    setFormData(prev => ({
      ...prev,
      title: e.target.value
    }));
  };

  // 處理儲存
  const handleSave = async () => {
    if (!formData.title.trim()) {
      message.error('請輸入標題');
      return;
    }

    if (!formData.content.trim()) {
      message.error('請輸入內容');
      return;
    }

    setSaving(true);

    try {
      const saveData = {
        title: formData.title.trim(),
        content: formData.content.trim(),
        // 如果是新建記錄，設置默認值
        ...(isEditMode ? {} : {
          category: 'general',
          issue_type: 'guide',
          description: formData.title.trim()
        })
      };

      console.log('💾 準備儲存資料:', saveData);

      let response;
      if (isEditMode) {
        // 更新現有記錄
        response = await axios.put(`/api/rvt-guides/${id}/`, saveData);
        console.log('✅ 更新成功:', response.data);
        message.success('更新成功！');
      } else {
        // 創建新記錄
        response = await axios.post('/api/rvt-guides/', saveData);
        console.log('✅ 創建成功:', response.data);
        message.success('創建成功！');
      }

      // 返回列表頁
      navigate('/knowledge/rvt-guide');
      
    } catch (error) {
      console.error('❌ 儲存失敗:', error);
      
      if (error.response?.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          // 處理字段驗證錯誤
          Object.keys(errorData).forEach(field => {
            const fieldErrors = Array.isArray(errorData[field]) 
              ? errorData[field].join(', ')
              : errorData[field];
            message.error(`${field}: ${fieldErrors}`);
          });
        } else {
          message.error(`儲存失敗: ${errorData}`);
        }
      } else {
        message.error('儲存失敗，請稍後再試');
      }
    } finally {
      setSaving(false);
    }
  };

  // 處理返回
  const handleGoBack = () => {
    if (formData.title || formData.content) {
      // 有未儲存的更改，顯示確認對話框
      if (window.confirm('有未儲存的更改，確定要離開嗎？')) {
        navigate('/knowledge/rvt-guide');
      }
    } else {
      navigate('/knowledge/rvt-guide');
    }
  };

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f5f5f5'
    }}>
      {/* 頂部操作欄 */}
      <Card 
        size="small" 
        style={{ 
          margin: 0, 
          borderRadius: 0,
          borderBottom: '1px solid #e8e8e8',
          boxShadow: '0 2px 8px rgba(0,0,0,0.06)'
        }}
      >
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={handleGoBack}
              size="large"
            >
              返回列表
            </Button>
            <h2 style={{ margin: 0, color: '#1890ff' }}>
              {isEditMode ? '編輯 RVT Guide' : '新建 RVT Guide'} (Markdown 編輯器)
            </h2>
            {isEditMode && (
              <span style={{ color: '#666', fontSize: '14px' }}>
                ID: {id}
              </span>
            )}
          </div>

          <Button
            type="primary"
            size="large"
            icon={<SaveOutlined />}
            loading={saving}
            onClick={handleSave}
            style={{ minWidth: '100px' }}
          >
            {isEditMode ? '更新' : '儲存'}
          </Button>
        </div>
      </Card>

      {/* 主要編輯區域 */}
      {loading ? (
        <div style={{ 
          flex: 1,
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center' 
        }}>
          <Spin size="large" />
          <span style={{ marginLeft: '12px', fontSize: '16px' }}>
            載入中...
          </span>
        </div>
      ) : (
        <div style={{ 
          flex: 1, 
          padding: '16px',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {/* 標題輸入 */}
          <Card size="small" style={{ flexShrink: 0 }}>
            <div>
              <label style={{ 
                display: 'block', 
                marginBottom: '8px', 
                fontWeight: 'bold',
                fontSize: '16px'
              }}>
                標題 *
              </label>
              <Input
                value={formData.title}
                onChange={handleTitleChange}
                placeholder="請輸入標題..."
                size="large"
                style={{ fontSize: '16px' }}
              />
            </div>
          </Card>

          {/* Markdown 編輯器 */}
          <Card 
            title="內容編輯 (支援 Markdown 語法)" 
            size="small" 
            style={{ 
              flex: 1, 
              display: 'flex', 
              flexDirection: 'column' 
            }}
            bodyStyle={{ 
              flex: 1, 
              padding: '16px',
              display: 'flex',
              flexDirection: 'column'
            }}
          >
            <div style={{ flex: 1, minHeight: '500px' }}>
              <MdEditor
                value={formData.content}
                style={{ height: '100%' }}
                renderHTML={(text) => mdParser.render(text)}
                onChange={handleEditorChange}
                placeholder="請輸入 Markdown 格式的內容..."
                config={{
                  view: {
                    menu: true,
                    md: true,
                    html: true
                  },
                  canView: {
                    menu: true,
                    md: true,
                    html: true,
                    both: true,
                    fullScreen: true,
                    hideMenu: false
                  }
                }}
              />
            </div>
            
            {/* 提示信息 */}
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              backgroundColor: '#f6ffed', 
              border: '1px solid #b7eb8f',
              borderRadius: '6px',
              fontSize: '14px',
              color: '#389e0d'
            }}>
              💡 <strong>提示：</strong>支援 Markdown 語法，包括標題、列表、連結、圖片、表格等。
              使用工具欄按鈕或直接輸入 Markdown 語法。可以切換到預覽模式查看效果。
            </div>
          </Card>
        </div>
      )}
    </div>
  );
};

export default MarkdownEditorPage;