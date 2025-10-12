import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Button, Input, message, Spin, Card, Space, Drawer, Tooltip } from 'antd';
import { SaveOutlined, ArrowLeftOutlined, PictureOutlined, CloseOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';
import axios from 'axios';
import ContentImageManager from '../components/ContentImageManager';
import useMarkdownCursor from '../hooks/useMarkdownCursor';
import useFullScreenDetection from '../hooks/useFullScreenDetection';
import useRvtGuideData from '../hooks/useRvtGuideData';
import useImageManager from '../hooks/useImageManager';

// 自定義工具欄按鈕樣式
const customToolbarStyles = `
  .rc-md-editor .button.custom-image-manager {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 30px;
    height: 30px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    background: #fff;
    transition: all 0.2s;
    margin: 0 2px;
    cursor: pointer;
    font-size: 14px;
  }
  
  .rc-md-editor .button.custom-image-manager:hover {
    border-color: #1890ff;
    background: #f0f8ff;
  }
  
  .rc-md-editor .button.custom-image-manager.active {
    border-color: #1890ff;
    background: #1890ff;
    color: white;
  }
  
  .rc-md-editor .button.custom-image-manager.disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  /* 全螢幕模式下的浮動按鈕 */
  .fullscreen-image-manager-btn {
    position: fixed !important;
    top: 60px !important;
    right: 20px !important;
    z-index: 9999 !important;
    background: #1890ff !important;
    color: white !important;
    border: none !important;
    border-radius: 6px !important;
    padding: 8px 12px !important;
    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.3) !important;
    font-size: 14px !important;
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
  }
  
  .fullscreen-image-manager-btn:hover {
    background: #40a9ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(24, 144, 255, 0.4) !important;
  }

  /* 全螢幕模式檢測 */
  .rc-md-editor.full {
    .fullscreen-image-manager-btn {
      display: flex !important;
    }
  }
`;



// 初始化 Markdown 解析器
const mdParser = new MarkdownIt();

/**
 * 整頁 Markdown 編輯器頁面
 * 路由: /knowledge/rvt-guide/markdown-edit/:id 或 /knowledge/rvt-guide/markdown-create
 */
const MarkdownEditorPage = () => {
  const navigate = useNavigate();
  const { id } = useParams(); // 如果是編輯模式，會有 id
  const mdEditorRef = useRef(null);

  // 使用 RVT Guide 資料管理 Hook
  const {
    loading,
    saving,
    formData,
    images,
    isEditMode,
    loadGuideData,
    saveGuideData,
    handleTitleChange,
    handleContentChange,
    setFormData
  } = useRvtGuideData(id, navigate);

  // 使用圖片管理 Hook
  const {
    drawerVisible,
    toggleDrawer,
    handleImagesChange: handleImageManagerChange,
    handleContentUpdate,
  } = useImageManager(mdEditorRef, setFormData);

  // 組合圖片變更處理 (同步兩個 Hook 的狀態)
  const handleImagesChange = (newImages) => {
    handleImageManagerChange(newImages);
    // 也需要更新 RvtGuideData Hook 中的圖片狀態
    // 這裡可以根據需要添加額外的邏輯
  };

  // 使用游標管理 Hook
  const {
    cursorPosition,
    handleEditorCursorChange,
    handleEditorBlur,
    handleEditorFocus,
    insertImageAtCursor,
  } = useMarkdownCursor(mdEditorRef, formData, setFormData);

  // 使用全螢幕偵測 Hook
  const {
    isFullScreen,
    isFullScreenSupported,
    enterFullScreen,
    exitFullScreen,
    toggleFullScreen
  } = useFullScreenDetection();

  // 載入現有記錄數據（編輯模式）
  useEffect(() => {
    if (isEditMode) {
      loadGuideData();
    }
  }, [id, isEditMode, loadGuideData]);







  // 處理儲存 - 使用 Hook 的方法
  const handleSave = async () => {
    await saveGuideData(formData);
  };

  // 處理返回
  const handleBack = () => {
    navigate('/knowledge/rvt-log');
  };

  return (
    <div style={{ 
      height: '100vh', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f5f5f5'
    }}>
      {/* 注入自定義樣式 */}
      <style>{customToolbarStyles}</style>
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
              onClick={handleBack}
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
            {/* 自定義工具欄擴展 */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'flex-start', 
              marginBottom: '8px',
              padding: '4px 8px',
              backgroundColor: '#fafafa',
              border: '1px solid #d9d9d9',
              borderBottom: 'none',
              borderRadius: '6px 6px 0 0'
            }}>
              <Tooltip title={isEditMode ? "管理文檔圖片" : "儲存後可管理圖片"}>
                <Button
                  icon={<PictureOutlined />}
                  onClick={() => {
                    if (isEditMode) {
                      toggleDrawer();
                    } else {
                      message.warning('請先儲存文檔後才能管理圖片');
                    }
                  }}
                  disabled={!isEditMode}
                  size="small"
                  type={drawerVisible ? "primary" : "default"}
                  style={{ 
                    fontSize: '12px',
                    height: '28px'
                  }}
                >
                  📷 圖片管理
                </Button>
              </Tooltip>
            </div>

            <div style={{ flex: 1, minHeight: '500px' }}>
              <MdEditor
                ref={mdEditorRef}
                value={formData.content}
                style={{ height: '100%' }}
                renderHTML={(text) => mdParser.render(text)}
                onChange={handleContentChange}
                onFocus={handleEditorFocus}
                onBlur={handleEditorBlur}
                onClick={handleEditorCursorChange}
                onKeyUp={handleEditorCursorChange}
                onSelect={handleEditorCursorChange}
                onMouseUp={handleEditorCursorChange}
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
                plugins={[
                  'header',
                  'font-bold',
                  'font-italic',
                  'font-underline',
                  'font-strikethrough',
                  'list-unordered',
                  'list-ordered',
                  'block-quote',
                  'block-wrap',
                  'block-code-inline',
                  'block-code-block',
                  'table',
                  'image',
                  'link',
                  'clear',
                  'logger',
                  'mode-toggle',
                  'full-screen'
                ]}
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

      {/* 全螢幕模式下的浮動圖片管理按鈕 */}
      {isFullScreen && isEditMode && (
        <div style={{ position: 'fixed', top: '60px', right: '20px', zIndex: 9999 }}>
          <Button
            icon={<PictureOutlined />}
            onClick={() => {
              console.log('🖱️ 全螢幕按鈕被點擊');
              toggleDrawer();
              // 可以使用 Hook 提供的方法: exitFullScreen(), toggleFullScreen() 等
            }}
            type="primary"
            size="large"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              borderRadius: '8px',
              boxShadow: '0 4px 12px rgba(24, 144, 255, 0.4)',
              background: drawerVisible ? '#52c41a' : '#1890ff',
              borderColor: drawerVisible ? '#52c41a' : '#1890ff'
            }}
          >
            📷 圖片管理
          </Button>
        </div>
      )}





      {/* 圖片管理側拉面板 */}
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PictureOutlined style={{ color: '#1890ff' }} />
            <span>圖片管理</span>
            {isEditMode && (
              <span style={{ 
                fontSize: '12px', 
                color: '#666', 
                backgroundColor: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                ID: {id}
              </span>
            )}
          </div>
        }
        placement="right"
        width={450}
        open={drawerVisible && isEditMode}
        onClose={toggleDrawer}
        bodyStyle={{ padding: '12px' }}
        headerStyle={{ 
          borderBottom: '1px solid #e8e8e8',
          backgroundColor: '#fafafa'
        }}
        style={{ zIndex: isFullScreen ? 10000 : 1000 }}
        getContainer={isFullScreen ? () => document.fullscreenElement || document.body : false}
        extra={
          <Tooltip title="關閉圖片管理">
            <Button 
              type="text" 
              icon={<CloseOutlined />}
              onClick={toggleDrawer}
            />
          </Tooltip>
        }
      >
        {isEditMode ? (
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
            title=""
          />
        ) : (
          <div style={{ 
            textAlign: 'center', 
            padding: '40px 20px',
            color: '#999'
          }}>
            <PictureOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
            <div>請先儲存文檔後才能管理圖片</div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default MarkdownEditorPage;