import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Space, 
  Row,
  Col,
  message,
  Spin,
  Tabs 
} from 'antd';
import { useParams, useNavigate } from 'react-router-dom';
import { SaveOutlined, EditOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';
import ContentImageManager from '../components/ContentImageManager';
import ContentRenderer from '../components/ContentRenderer';

const { TextArea } = Input;

const RvtGuideEditPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [initialLoading, setInitialLoading] = useState(!!id);
  const [images, setImages] = useState([]);
  const [formData, setFormData] = useState({ title: '', content: '' }); // 添加本地狀態
  
  // 游標位置追蹤
  const [cursorPosition, setCursorPosition] = useState(0);
  const contentTextAreaRef = React.useRef(null);
  
  const isEdit = !!id;

  // 分類選項


  const loadGuideData = useCallback(async () => {
    try {
      setInitialLoading(true);
      console.log(`🔍 開始載入 RVT Guide ID: ${id}`);
      
      // 載入基本資料和圖片資料
      const [guideResponse, imagesResponse] = await Promise.all([
        axios.get(`/api/rvt-guides/${id}/?include_images=true`),
        axios.get(`/api/content-images/?content_type=rvt-guide&content_id=${id}`)
      ]);
      
      console.log('✅ API 回應:', { 
        guideData: guideResponse.data, 
        imagesData: imagesResponse.data 
      });
      
      if (guideResponse.data) {
        console.log('📝 設定表單資料:', guideResponse.data);
        
        // 設定本地狀態和表單資料
        const formValues = {
          title: guideResponse.data.title || '',
          content: guideResponse.data.content || ''
        };
        
        setFormData(formValues);
        form.setFieldsValue(formValues);
        
        // 驗證表單資料是否正確設定
        console.log('✅ 表單資料已設定:', formValues);
        console.log('✅ 當前表單值:', form.getFieldsValue());
        
        // 設定圖片資料
        if (guideResponse.data.active_images) {
          setImages(guideResponse.data.active_images);
        } else if (imagesResponse.data.results) {
          setImages(imagesResponse.data.results);
        } else if (Array.isArray(imagesResponse.data)) {
          setImages(imagesResponse.data);
        }
      } else {
        message.error('載入資料失敗');
        navigate('/knowledge/rvt-guide');
      }
    } catch (error) {
      console.error('載入失敗:', error);
      message.error('載入資料失敗');
      navigate('/knowledge/rvt-guide');
    } finally {
      setInitialLoading(false);
    }
  }, [id, navigate, form]);

  // 載入資料 (編輯模式)
  useEffect(() => {
    if (id) {
      loadGuideData();
    }
  }, [id, loadGuideData]);

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
      
      navigate('/knowledge/rvt-guide');
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
    navigate('/knowledge/rvt-guide');
  };

  const handleImagesChange = (newImages) => {
    setImages(newImages);
    console.log('RVT Guide 圖片已更新:', newImages);
  };

  // 處理游標位置變更
  const handleCursorPositionChange = (e) => {
    setCursorPosition(e.target.selectionStart || 0);
  };

  // 在指定位置插入圖片資訊
  const insertImageAtCursor = (imageInfo) => {
    const currentContent = form.getFieldValue('content') || '';
    const beforeCursor = currentContent.slice(0, cursorPosition);
    const afterCursor = currentContent.slice(cursorPosition);
    
    // 插入圖片資訊
    const newContent = beforeCursor + imageInfo + afterCursor;
    
    // 更新表單內容
    form.setFieldsValue({ content: newContent });
    
    // 更新游標位置到插入內容之後
    const newCursorPos = cursorPosition + imageInfo.length;
    setCursorPosition(newCursorPos);
    
    // 將焦點設回 TextArea 並設定游標位置
    setTimeout(() => {
      if (contentTextAreaRef.current) {
        const textArea = contentTextAreaRef.current.resizableTextArea.textArea;
        textArea.focus();
        textArea.setSelectionRange(newCursorPos, newCursorPos);
      }
    }, 10);
  };

  const handleContentUpdate = (updatedContent) => {
    // 當圖片操作導致內容更新時，更新表單中的內容
    form.setFieldsValue({ content: updatedContent });
    console.log('RVT Guide 內容已自動更新圖片引用');
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
              initialValues={formData}
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
                <Col span={24}>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ 
                      display: 'block', 
                      marginBottom: '8px', 
                      fontWeight: '600',
                      color: 'rgba(0, 0, 0, 0.85)',
                      fontSize: '14px'
                    }}>
                      內容 <span style={{ color: '#ff4d4f' }}>*</span>
                    </label>
                    <Tabs
                      items={[
                        {
                          key: 'edit',
                          label: (
                            <Space>
                              <EditOutlined />
                              編輯
                            </Space>
                          ),
                          children: (
                            <Form.Item
                              name="content"
                              rules={[{ required: true, message: '請輸入內容' }]}
                              style={{ marginBottom: 0 }}
                            >
                              <TextArea 
                                ref={contentTextAreaRef}
                                rows={20}
                                placeholder="請輸入指導文檔內容&#10;&#10;支援 Markdown 格式：&#10;# 標題&#10;## 副標題&#10;- 項目列表&#10;**粗體文字**&#10;*斜體文字*&#10;`程式碼`&#10;```&#10;程式碼區塊&#10;```&#10;&#10;💡 提示：上傳圖片時會在游標位置插入圖片資訊"
                                showCount
                                style={{ 
                                  fontSize: '14px',
                                  lineHeight: '1.6',
                                  fontFamily: 'Monaco, Menlo, "Ubuntu Mono", monospace'
                                }}
                                onSelect={handleCursorPositionChange}
                                onClick={handleCursorPositionChange}
                                onKeyUp={handleCursorPositionChange}
                              />
                            </Form.Item>
                          ),
                        },
                        {
                          key: 'preview',
                          label: (
                            <Space>
                              <EyeOutlined />
                              預覽
                            </Space>
                          ),
                          children: (
                            <div style={{
                              minHeight: '500px',
                              padding: '16px',
                              border: '1px solid #d9d9d9',
                              borderRadius: '6px',
                              backgroundColor: '#fafafa'
                            }}>
                              <ContentRenderer 
                                content={form.getFieldValue('content') || '尚無內容'}
                                showImageTitles={true}
                                showImageDescriptions={true}
                                imageMaxWidth={400}
                                imageMaxHeight={300}
                              />
                            </div>
                          ),
                        },
                      ]}
                      defaultActiveKey="edit"
                    />
                  </div>
                </Col>
              </Row>
            </Form>
          </Card>

          {/* 圖片管理區域 - 只有在編輯模式且有 ID 時才顯示 */}
          {isEdit && id && (
            <ContentImageManager
              contentType="rvt-guide"
              contentId={id}
              images={images}
              onImagesChange={handleImagesChange}
              onContentUpdate={handleContentUpdate}
              onImageInsert={insertImageAtCursor}
              cursorPosition={cursorPosition}
              maxImages={10}
              maxSizeMB={2}
              title="相關圖片"
            />
          )}

          {/* 新建模式的提示 */}
          {!isEdit && (
            <Card style={{ marginTop: '16px' }}>
              <div style={{ 
                padding: '20px',
                textAlign: 'center',
                background: '#e6f7ff', 
                border: '1px solid #91d5ff', 
                borderRadius: '6px',
                color: '#0050b3'
              }}>
                <Space direction="vertical" size="small">
                  <span style={{ fontSize: '16px', fontWeight: '500' }}>
                    📝 圖片管理功能
                  </span>
                  <span style={{ fontSize: '14px' }}>
                    請先儲存基本資料，之後即可在編輯模式中管理相關圖片
                  </span>
                </Space>
              </div>
            </Card>
          )}
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