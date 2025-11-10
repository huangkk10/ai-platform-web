/**
 * 通用 Markdown 編輯頁面（支援多知識庫）
 * 
 * 使用通用 MarkdownEditorLayout 組件
 * 從 500+ 行簡化為 30 行
 * 
 * 支援的知識庫：
 * - RVT Guide (/knowledge/rvt-guide/markdown-*)
 * - Protocol Guide (/knowledge/protocol-guide/markdown-*)
 */

import React, { useState, useMemo } from 'react';
import { useNavigate, useParams, useLocation } from 'react-router-dom';
import { Button, Space } from 'antd';
import { ArrowLeftOutlined, SaveOutlined, CheckOutlined } from '@ant-design/icons';
import TopHeader from '../components/TopHeader';
import MarkdownEditorLayout from '../components/editor/MarkdownEditorLayout';
import { getEditorConfig } from '../config/editorConfig';

const MarkdownEditorPage = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { id } = useParams();
  const isEditMode = !!id;
  const [saving, setSaving] = useState(false);

  // 根據 URL 路徑自動識別知識庫類型
  const editorConfig = useMemo(() => {
    const pathname = location.pathname;
    
    if (pathname.includes('/protocol-guide/')) {
      const config = getEditorConfig('protocol-guide');
      return {
        contentType: 'protocol-guide',
        listPath: config.listRoute,
        pageTitle: isEditMode ? config.labels.editTitle : config.labels.createTitle,
        saveEventName: config.saveEventName,
      };
    }
    
    // 預設為 RVT Guide
    const config = getEditorConfig('rvt-guide');
    return {
      contentType: 'rvt-guide',
      listPath: config.listRoute,
      pageTitle: isEditMode ? config.labels.editTitle : config.labels.createTitle,
      saveEventName: config.saveEventName,
    };
  }, [location.pathname, isEditMode]);

  // 處理儲存事件
  const handleSave = () => {
    console.log(`💾 TopHeader 儲存按鈕被點擊 (${editorConfig.contentType})`);
    // 觸發對應知識庫的事件
    const event = new Event(editorConfig.saveEventName);
    window.dispatchEvent(event);
    console.log(`📤 已觸發 ${editorConfig.saveEventName} 事件`);
  };

  // 🆕 處理格式檢查事件
  const handleCheckFormat = () => {
    console.log('🔍 手動檢查格式');
    
    // 觸發格式檢查事件
    const event = new CustomEvent('check-markdown-format', {
      detail: { source: 'topheader-button' }
    });
    window.dispatchEvent(event);
  };

  // 額外操作按鈕
  const extraActions = (
    <Space>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(editorConfig.listPath)}
      >
        返回
      </Button>
      
      {/* 🆕 格式檢查按鈕（僅 Protocol Guide 顯示） */}
      {editorConfig.contentType === 'protocol-guide' && (
        <Button
          icon={<CheckOutlined />}
          onClick={handleCheckFormat}
        >
          檢查格式
        </Button>
      )}
      
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
        pageTitle={editorConfig.pageTitle}
        extraActions={extraActions}
      />
      
      <MarkdownEditorLayout 
        contentType={editorConfig.contentType}
        contentId={id}
        navigate={navigate}
        onSavingChange={setSaving}
      />
    </div>
  );
};

export default MarkdownEditorPage;
