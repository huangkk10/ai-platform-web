/**
 * RVT Guide 編輯頁面（重構版）
 * 
 * 使用通用 MarkdownEditorLayout 組件
 * 從 500+ 行簡化為 30 行
 * 
 * 使用說明：
 * 1. 測試確認無誤後，將此檔案重新命名為 MarkdownEditorPage.js
 * 2. 刪除舊的 MarkdownEditorPage.js
 * 3. 或保留舊檔案作為備份 (MarkdownEditorPage.old.js)
 */

import React, { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Space } from 'antd';
import { ArrowLeftOutlined, SaveOutlined } from '@ant-design/icons';
import TopHeader from '../components/TopHeader';
import MarkdownEditorLayout from '../components/editor/MarkdownEditorLayout';

const MarkdownEditorPage = () => {
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = !!id;
  const [saving, setSaving] = useState(false);

  // 處理儲存事件
  const handleSave = () => {
    console.log('💾 TopHeader 儲存按鈕被點擊');
    // 觸發全局事件，讓 MarkdownEditorLayout 接收
    // 注意：事件名稱必須與 editorConfig 中的 saveEventName 一致
    const event = new Event('markdown-editor-save');
    window.dispatchEvent(event);
    console.log('📤 已觸發 markdown-editor-save 事件');
  };

  // 額外操作按鈕
  const extraActions = (
    <Space>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/knowledge/rvt-log')}
      >
        返回
      </Button>
      <Button
        type="primary"
        icon={<SaveOutlined />}
        onClick={handleSave}
        loading={saving}
      >
        儲存
      </Button>
    </Space>
  );

  return (
    <div>
      <TopHeader
        pageTitle={isEditMode ? '編輯 RVT Guide' : '新增 RVT Guide'}
        extraActions={extraActions}
      />
      
      <MarkdownEditorLayout 
        contentType="rvt-guide"
        contentId={id}
        navigate={navigate}
        onSavingChange={setSaving}
      />
    </div>
  );
};

export default MarkdownEditorPage;
