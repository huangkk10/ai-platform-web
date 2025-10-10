/**
 * ContentImageManager 組件使用範例
 * 展示如何在 RVT Guide 編輯頁面中整合圖片管理功能
 */

import React, { useState, useEffect } from 'react';
import { Form, Input, Button, message } from 'antd';
import ContentImageManager from '../components/ContentImageManager';

const RvtGuideEditPageExample = ({ guideId, isEdit = false }) => {
  const [form] = Form.useForm();
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(false);

  // 載入現有資料（編輯模式）
  useEffect(() => {
    if (isEdit && guideId) {
      loadGuideData();
    }
  }, [isEdit, guideId]);

  const loadGuideData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`/api/rvt-guides/${guideId}/`, {
        credentials: 'include'
      });
      
      if (response.ok) {
        const data = await response.json();
        // 設定表單值
        form.setFieldsValue({
          title: data.title,
          content: data.content
        });
        
        // 設定圖片資料
        setImages(data.active_images || []);
      }
    } catch (error) {
      message.error('載入資料失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (values) => {
    try {
      setLoading(true);
      
      const url = isEdit ? `/api/rvt-guides/${guideId}/` : '/api/rvt-guides/';
      const method = isEdit ? 'PUT' : 'POST';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(values)
      });
      
      if (response.ok) {
        message.success(isEdit ? '更新成功' : '建立成功');
        // 如果是新建，取得新的 ID 以便管理圖片
        if (!isEdit) {
          const newGuide = await response.json();
          // 可以導航到編輯頁面或做其他處理
          console.log('新建的 Guide ID:', newGuide.id);
        }
      } else {
        message.error(isEdit ? '更新失敗' : '建立失敗');
      }
    } catch (error) {
      message.error('操作失敗');
    } finally {
      setLoading(false);
    }
  };

  const handleImagesChange = (newImages) => {
    setImages(newImages);
    // 這裡可以做額外的處理，比如更新表單狀態等
    console.log('圖片清單已更新:', newImages);
  };

  return (
    <div style={{ maxWidth: 1200, margin: '0 auto', padding: '24px' }}>
      <Form
        form={form}
        layout="vertical"
        onFinish={handleSubmit}
        loading={loading}
      >
        {/* 基本資料表單 */}
        <Form.Item
          name="title"
          label="標題"
          rules={[{ required: true, message: '請輸入標題' }]}
        >
          <Input placeholder="請輸入 RVT Guide 標題" />
        </Form.Item>

        <Form.Item
          name="content"
          label="內容"
          rules={[{ required: true, message: '請輸入內容' }]}
        >
          <Input.TextArea 
            rows={10}
            placeholder="請輸入詳細內容"
          />
        </Form.Item>

        {/* 圖片管理區域 */}
        {/* 只有在編輯模式或已有 guideId 時才顯示圖片管理 */}
        {(isEdit && guideId) && (
          <ContentImageManager
            contentType="rvt-guide"
            contentId={guideId}
            images={images}
            onImagesChange={handleImagesChange}
            maxImages={10}
            maxSizeMB={2}
            title="相關圖片"
          />
        )}

        {/* 操作按鈕 */}
        <Form.Item style={{ marginTop: '24px' }}>
          <Button type="primary" htmlType="submit" loading={loading}>
            {isEdit ? '更新' : '建立'}
          </Button>
        </Form.Item>
      </Form>

      {/* 新建模式的提示 */}
      {!isEdit && (
        <div style={{ 
          marginTop: '16px', 
          padding: '12px', 
          background: '#e6f7ff', 
          border: '1px solid #91d5ff', 
          borderRadius: '6px',
          color: '#0050b3'
        }}>
          📝 提示：請先儲存基本資料，之後即可管理相關圖片
        </div>
      )}
    </div>
  );
};

export default RvtGuideEditPageExample;


/**
 * 在其他類型內容中使用的範例
 */

// 用於 Know Issue 的範例
const KnowIssueWithImages = ({ issueId }) => {
  const [images, setImages] = useState([]);

  return (
    <div>
      {/* 其他 Know Issue 表單內容... */}
      
      <ContentImageManager
        contentType="know-issue"
        contentId={issueId}
        images={images}
        onImagesChange={setImages}
        maxImages={5}
        maxSizeMB={3}
        title="相關截圖"
      />
    </div>
  );
};

// 唯讀模式範例（用於詳細檢視頁面）
const ContentViewWithImages = ({ contentType, contentId, images }) => {
  return (
    <div>
      {/* 其他內容顯示... */}
      
      <ContentImageManager
        contentType={contentType}
        contentId={contentId}
        images={images}
        onImagesChange={() => {}} // 唯讀模式不需要處理變更
        readonly={true}
        title="相關圖片"
      />
    </div>
  );
};