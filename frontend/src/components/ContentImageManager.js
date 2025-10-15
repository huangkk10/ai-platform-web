import React, { useState, useEffect } from 'react';
import {
  Upload, Card, Button, Space, Modal, Form, Input, message,
  Row, Col, Image, Tag, Tooltip, Popconfirm
} from 'antd';
import {
  PlusOutlined, DeleteOutlined, EditOutlined, EyeOutlined,
  StarOutlined, StarFilled, DragOutlined
} from '@ant-design/icons';
import { DragDropContext, Droppable, Draggable } from 'react-beautiful-dnd';
import axios from 'axios';
import './ContentImageManager.css';

const { TextArea } = Input;

/**
 * 通用內容圖片管理組件
 * 可用於不同類型的內容（RVT Guide、Know Issue 等）
 */
const ContentImageManager = ({ 
  contentType = 'rvt-guide',  // 內容類型：'rvt-guide', 'know-issue' 等
  contentId,                   // 內容 ID
  images = [],                 // 現有圖片列表
  onImagesChange,             // 圖片變更回調
  onContentUpdate,            // 內容更新回調 (用於重新載入父組件資料)
  onImageInsert,              // 圖片插入回調 (新增：在游標位置插入)
  cursorPosition = 0,         // 當前游標位置 (新增)
  maxImages = 10,             // 最大圖片數量
  maxSizeMB = 2,              // 單個圖片最大大小 (MB)
  title = "圖片管理",          // 組件標題
  readonly = false             // 是否只讀模式
}) => {
  const [imageList, setImageList] = useState(images);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingImage, setEditingImage] = useState(null);
  const [uploadLoading, setUploadLoading] = useState(false);
  const [form] = Form.useForm();
  
  // 同步外部 images 變更
  useEffect(() => {
    setImageList(images);
  }, [images]);
  
  // 獲取 API 端點
  const getApiEndpoint = () => {
    switch (contentType) {
      case 'rvt-guide':
        return '/api/content-images/';
      case 'know-issue':
        return '/api/content-images/';
      default:
        return '/api/content-images/';
    }
  };
  
  // 產生圖片資訊字串 (包含圖片 ID 引用)
  const generateImageInfo = (image) => {
    const imageInfo = [];
    if (image.is_primary) {
      imageInfo.push("📌 主要圖片");
    }
    if (image.title) {
      imageInfo.push(`標題: ${image.title}`);
    }
    if (image.description) {
      imageInfo.push(`說明: ${image.description}`);
    }
    
    // 新格式：加入 [IMG:ID] 標記以支援圖片編號引用
    let imageLine = `🖼️ [IMG:${image.id}] ${image.filename}`;
    if (imageInfo.length > 0) {
      imageLine += ` (${imageInfo.join(', ')})`;
    }
    
    return `\n${imageLine}\n`;
  };

  // 在游標位置插入圖片資訊
  const insertImageAtCursor = (image) => {
    if (onImageInsert) {
      const imageInfo = generateImageInfo(image);
      onImageInsert(imageInfo);
      console.log(`✅ 在游標位置插入圖片資訊: ${image.filename}`);
    }
  };

  // 自動更新內容以包含圖片引用 (舊方法，保留以向後兼容)
  const updateContentWithImages = async () => {
    if (contentType === 'rvt-guide' && contentId) {
      try {
        const response = await axios.post(`/api/rvt-guides/${contentId}/update_content_with_images/`);
        
        // 通知父組件內容已更新，需要重新載入
        if (onContentUpdate && response.data.updated_content) {
          onContentUpdate(response.data.updated_content);
        }
      } catch (error) {
        console.warn('更新內容圖片引用失敗:', error);
        // 不影響主要功能，僅記錄警告
      }
    }
  };
  
  // 上傳圖片
  const handleUpload = async (file) => {
    if (readonly) {
      message.warning('唯讀模式下無法上傳圖片');
      return false;
    }
    
    // 檢查數量限制
    if (imageList.length >= maxImages) {
      message.error(`最多只能上傳 ${maxImages} 張圖片`);
      return false;
    }
    
    // 檢查檔案大小
    const maxSizeBytes = maxSizeMB * 1024 * 1024;
    if (file.size > maxSizeBytes) {
      message.error(`檔案大小不能超過 ${maxSizeMB}MB`);
      return false;
    }
    
    // 檢查檔案類型
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    if (!allowedTypes.includes(file.type)) {
      message.error('只支援 JPEG、PNG、GIF 格式的圖片');
      return false;
    }
    
    setUploadLoading(true);
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('content_type', contentType);
    formData.append('content_id', contentId);
    
    try {
      const response = await axios.post(getApiEndpoint(), formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const newImage = response.data;
      const updatedList = [...imageList, newImage];
      setImageList(updatedList);
      onImagesChange && onImagesChange(updatedList);
      
      // 優先使用游標位置插入，否則使用舊方法
      if (onImageInsert) {
        insertImageAtCursor(newImage);
        message.success('圖片上傳成功，已在游標位置插入圖片資訊');
      } else {
        await updateContentWithImages();
        message.success('圖片上傳成功，已自動更新內容引用');
      }
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          error.response?.data?.message ||
                          '上傳過程中發生錯誤';
      message.error(errorMessage);
    } finally {
      setUploadLoading(false);
    }
    
    return false; // 阻止預設上傳行為
  };
  
  // 刪除圖片
  const handleDelete = async (imageId) => {
    if (readonly) {
      message.warning('唯讀模式下無法刪除圖片');
      return;
    }
    
    try {
      await axios.delete(`${getApiEndpoint()}${imageId}/`);
      
      const updatedList = imageList.filter(img => img.id !== imageId);
      setImageList(updatedList);
      onImagesChange && onImagesChange(updatedList);
      
      // 圖片刪除時仍使用舊方法更新整個文檔 (因為需要移除現有引用)
      await updateContentWithImages();
      
      message.success('圖片刪除成功，已更新內容引用');
    } catch (error) {
      console.error('Delete error:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          '刪除過程中發生錯誤';
      message.error(errorMessage);
    }
  };
  
  // 設為主要圖片
  const handleSetPrimary = async (imageId) => {
    if (readonly) {
      message.warning('唯讀模式下無法修改主要圖片');
      return;
    }
    
    try {
      const endpoint = contentType === 'rvt-guide' 
        ? `/api/rvt-guides/${contentId}/set_primary_image/`
        : `${getApiEndpoint()}${imageId}/set_primary/`;
        
      await axios.post(endpoint, { image_id: imageId });
      
      const updatedList = imageList.map(img => ({
        ...img,
        is_primary: img.id === imageId
      }));
      setImageList(updatedList);
      onImagesChange && onImagesChange(updatedList);
      
      // 主圖片變更時使用舊方法更新整個文檔 (確保主圖標記正確)
      await updateContentWithImages();
      
      message.success('主要圖片設定成功，已更新內容引用');
    } catch (error) {
      console.error('Set primary error:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          '設定過程中發生錯誤';
      message.error(errorMessage);
    }
  };
  
    // 編輯圖片資訊
  const handleEdit = async (values) => {
    if (readonly) {
      message.warning('唯讀模式下無法編輯圖片');
      return;
    }
    
    try {
      const response = await axios.patch(`${getApiEndpoint()}${editingImage.id}/`, values);
      
      const updatedImage = response.data;
      const updatedList = imageList.map(img => 
        img.id === editingImage.id ? updatedImage : img
      );
      setImageList(updatedList);
      onImagesChange && onImagesChange(updatedList);
      setEditModalVisible(false);
      setEditingImage(null);
      form.resetFields();
      
      // 圖片資訊更新時使用舊方法 (確保所有引用都正確更新)
      await updateContentWithImages();
      
      message.success('圖片資訊更新成功，已更新內容引用');
    } catch (error) {
      console.error('Edit error:', error);
      const errorMessage = error.response?.data?.detail || 
                          error.response?.data?.error || 
                          '更新過程中發生錯誤';
      message.error(errorMessage);
    }
  };
  
  // 拖拽排序
  const handleDragEnd = async (result) => {
    if (readonly) {
      message.warning('唯讀模式下無法調整順序');
      return;
    }
    
    if (!result.destination) return;
    
    const reorderedImages = Array.from(imageList);
    const [moved] = reorderedImages.splice(result.source.index, 1);
    reorderedImages.splice(result.destination.index, 0, moved);
    
    // 更新本地狀態
    setImageList(reorderedImages);
    
    // 發送排序到後端
    try {
      const imageIds = reorderedImages.map(img => img.id);
      const endpoint = contentType === 'rvt-guide'
        ? `/api/rvt-guides/${contentId}/reorder_images/`
        : `${getApiEndpoint()}reorder/`;
        
      await axios.post(endpoint, { 
        image_ids: imageIds,
        content_type: contentType,
        content_id: contentId
      });
    } catch (error) {
      console.error('Reorder error:', error);
      setImageList(imageList);
      message.error('排序更新失敗');
    }
  };
  
  // 批量上傳
  const handleBatchUpload = async (fileList) => {
    if (readonly) {
      message.warning('唯讀模式下無法上傳圖片');
      return;
    }
    
    if (imageList.length + fileList.length > maxImages) {
      message.error(`總圖片數量不能超過 ${maxImages} 張`);
      return;
    }
    
    setUploadLoading(true);
    
    const formData = new FormData();
    fileList.forEach(file => {
      formData.append('images', file);
    });
    formData.append('content_type', contentType);
    formData.append('content_id', contentId);
    
    try {
      const response = await axios.post(`${getApiEndpoint()}batch-upload/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
      
      const result = response.data;
      if (result.created_images && result.created_images.length > 0) {
        const updatedList = [...imageList, ...result.created_images];
        setImageList(updatedList);
        onImagesChange && onImagesChange(updatedList);
        message.success(`成功上傳 ${result.success} 張圖片`);
        
        if (result.errors && result.errors.length > 0) {
          message.warning(`部分上傳失敗: ${result.errors.join(', ')}`);
        }
      }
    } catch (error) {
      console.error('Batch upload error:', error);
      message.error('批量上傳過程中發生錯誤');
    } finally {
      setUploadLoading(false);
    }
  };
  
  return (
    <Card title={title} className="content-image-manager">
      {/* 使用提示 */}
      {onImageInsert && !readonly && (
        <div style={{
          padding: '12px',
          backgroundColor: '#f0f9ff',
          border: '1px solid #bae7ff',
          borderRadius: '6px',
          marginBottom: '16px',
          fontSize: '14px',
          color: '#0958d9'
        }}>
          <Space>
            <span>💡</span>
            <span>
              <strong>游標插入模式：</strong>
              上傳圖片時會在文字編輯區域的游標位置插入圖片資訊，而不是在文檔末尾添加
            </span>
          </Space>
        </div>
      )}
      
      {/* 上傳區域 */}
      {!readonly && (
        <div className="upload-area">
          <Space className="batch-actions">
            <Upload
              accept="image/*"
              beforeUpload={handleUpload}
              showUploadList={false}
              loading={uploadLoading}
            >
              <Button icon={<PlusOutlined />} type="dashed" loading={uploadLoading}>
                上傳圖片
              </Button>
            </Upload>
          </Space>
          
          <div className="batch-info">
            支援 JPEG、PNG、GIF 格式，單檔不超過 {maxSizeMB}MB，最多 {maxImages} 張
          </div>
        </div>
      )}
      
      {/* 圖片列表 - 支援拖拽排序 */}
      {imageList.length > 0 ? (
        <DragDropContext onDragEnd={handleDragEnd}>
          <Droppable droppableId="images" direction="horizontal">
            {(provided) => (
              <div
                ref={provided.innerRef}
                {...provided.droppableProps}
                style={{ display: 'flex', flexWrap: 'wrap', gap: '12px' }}
              >
                {imageList.map((image, index) => (
                  <Draggable
                    key={image.id}
                    draggableId={image.id.toString()}
                    index={index}
                    isDragDisabled={readonly}
                  >
                    {(provided, snapshot) => (
                      <div
                        ref={provided.innerRef}
                        {...provided.draggableProps}
                        style={{
                          ...provided.draggableProps.style,
                          opacity: snapshot.isDragging ? 0.8 : 1,
                        }}
                      >
                        <Card
                          hoverable
                          className={`image-card ${snapshot.isDragging ? 'dragging' : ''}`}
                          cover={
                            <div className="image-container">
                              <Image
                                src={image.data_url}
                                alt={image.title || image.filename}
                                height={120}
                                style={{ objectFit: 'cover' }}
                                preview={{
                                  mask: <EyeOutlined />
                                }}
                              />
                              
                              {/* 拖拽手柄 */}
                              {!readonly && (
                                <div
                                  {...provided.dragHandleProps}
                                  className="drag-handle"
                                >
                                  <DragOutlined />
                                </div>
                              )}
                              
                              {/* 主要圖片標記 */}
                              {image.is_primary && (
                                <div className="primary-badge">
                                  <StarFilled /> 主要
                                </div>
                              )}
                            </div>
                          }
                        >
                          <Card.Meta
                            title={
                              <Tooltip title={image.filename}>
                                <div style={{ 
                                  whiteSpace: 'nowrap',
                                  overflow: 'hidden',
                                  textOverflow: 'ellipsis'
                                }}>
                                  {image.title || image.filename}
                                </div>
                              </Tooltip>
                            }
                            description={
                              <div>
                                <div>{image.dimensions_display || '未知'}</div>
                                <div>{image.size_display || '未知大小'}</div>
                              </div>
                            }
                          />
                          
                          {/* 操作按鈕 */}
                          {!readonly && (
                            <div className="image-actions">
                              <Space size="small">
                                <Tooltip title="編輯資訊">
                                  <Button
                                    size="small"
                                    icon={<EditOutlined />}
                                    onClick={() => {
                                      setEditingImage(image);
                                      form.setFieldsValue({
                                        title: image.title,
                                        description: image.description
                                      });
                                      setEditModalVisible(true);
                                    }}
                                  />
                                </Tooltip>
                                
                                <Tooltip title={image.is_primary ? "已是主要圖片" : "設為主要圖片"}>
                                  <Button
                                    size="small"
                                    icon={image.is_primary ? <StarFilled /> : <StarOutlined />}
                                    type={image.is_primary ? "primary" : "default"}
                                    disabled={image.is_primary}
                                    onClick={() => handleSetPrimary(image.id)}
                                  />
                                </Tooltip>
                                
                                <Popconfirm
                                  title="確定要刪除這張圖片嗎？"
                                  onConfirm={() => handleDelete(image.id)}
                                >
                                  <Button
                                    size="small"
                                    danger
                                    icon={<DeleteOutlined />}
                                  />
                                </Popconfirm>
                              </Space>
                            </div>
                          )}
                        </Card>
                      </div>
                    )}
                  </Draggable>
                ))}
                {provided.placeholder}
              </div>
            )}
          </Droppable>
        </DragDropContext>
      ) : (
        <div className="empty-state">
          {readonly ? '暫無圖片' : '尚未上傳任何圖片'}
        </div>
      )}
      
      {/* 編輯 Modal */}
      <Modal
        title="編輯圖片資訊"
        open={editModalVisible}
        onCancel={() => {
          setEditModalVisible(false);
          setEditingImage(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        okText="更新"
        cancelText="取消"
        className="edit-modal"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleEdit}
        >
          <Form.Item
            name="title"
            label="圖片標題"
          >
            <Input placeholder="輸入圖片標題（可選）" />
          </Form.Item>
          
          <Form.Item
            name="description"
            label="圖片描述"
          >
            <TextArea 
              rows={3}
              placeholder="輸入圖片描述（可選）"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Card>
  );
};

export default ContentImageManager;