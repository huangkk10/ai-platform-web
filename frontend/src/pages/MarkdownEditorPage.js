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
  const getStagedImagesRef = useRef(null); // 🆕 暫存圖片獲取函數引用

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
    setFormData,
    setSaving
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







  // 🆕 處理儲存 - 支援暫存圖片上傳
  const handleSave = async () => {
    try {
      // 先儲存文檔本體
      const result = await saveGuideData(formData, {
        navigateAfterSave: false, // 先不導航，等圖片上傳完成
        redirectPath: '/knowledge/rvt-log'
      });
      
      if (!result) return; // 儲存失敗，不繼續
      
      // 如果是新建模式且有暫存圖片，批量上傳
      if (!isEditMode && getStagedImagesRef.current) {
        const stagedImages = getStagedImagesRef.current();
        
        if (stagedImages && stagedImages.length > 0) {
          console.log('📤 開始上傳暫存圖片:', stagedImages.length, '張');
          setSaving(true);
          
          // 顯示上傳進度提示
          const hideLoading = message.loading(`正在上傳圖片 (0/${stagedImages.length})...`, 0);
          
          try {
            // 逐個上傳暫存圖片
            let successCount = 0;
            let failCount = 0;
            
            for (const stagedImage of stagedImages) {
              try {
                const formData = new FormData();
                formData.append('image', stagedImage.file);
                formData.append('content_type', 'rvt-guide');
                formData.append('content_id', result.id);
                
                if (stagedImage.title) {
                  formData.append('title', stagedImage.title);
                }
                if (stagedImage.description) {
                  formData.append('description', stagedImage.description);
                }
                if (stagedImage.is_primary) {
                  formData.append('is_primary', 'true');
                }
                
                await axios.post('/api/content-images/', formData, {
                  headers: { 'Content-Type': 'multipart/form-data' }
                });
                
                successCount++;
                console.log(`✅ 圖片上傳成功 (${successCount}/${stagedImages.length}):`, stagedImage.filename);
                
                // 更新進度提示
                hideLoading();
                message.loading(`正在上傳圖片 (${successCount}/${stagedImages.length})...`, 0.5);
              } catch (error) {
                failCount++;
                console.error('❌ 圖片上傳失敗:', stagedImage.filename, error);
              }
            }
            
            // 關閉進度提示
            hideLoading();
            
            // 顯示結果
            if (successCount > 0 && failCount === 0) {
              message.success(`文檔和 ${successCount} 張圖片已成功儲存！`);
            } else if (successCount > 0) {
              message.warning(`文檔已儲存，但 ${failCount} 張圖片上傳失敗`);
            } else {
              message.error('文檔已儲存，但所有圖片上傳失敗');
            }
          } catch (error) {
            hideLoading(); // 確保關閉進度提示
            console.error('❌ 批量上傳過程異常:', error);
            message.error('文檔已儲存，但圖片上傳過程發生錯誤');
          } finally {
            setSaving(false);
          }
        }
      }
      
      // 🎯 導航到列表頁 (使用 setTimeout 確保 message 顯示後再跳轉)
      setTimeout(() => {
        navigate('/knowledge/rvt-log');
      }, 300);
      
    } catch (error) {
      console.error('❌ 儲存過程發生錯誤:', error);
      setSaving(false);
    }
  };

  // 處理返回
  const handleBack = () => {
    navigate('/knowledge/rvt-log');
  };

  // 監聽來自 TopHeader 的保存事件
  useEffect(() => {
    const handleSaveEvent = () => {
      handleSave();
    };
    
    window.addEventListener('markdown-editor-save', handleSaveEvent);
    
    return () => {
      window.removeEventListener('markdown-editor-save', handleSaveEvent);
    };
  }, [handleSave]);

  return (
    <div style={{ 
      height: 'calc(100vh - 64px)', 
      display: 'flex', 
      flexDirection: 'column',
      background: '#f5f5f5'
    }}>
      {/* 注入自定義樣式 */}
      <style>{customToolbarStyles}</style>

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
            title="內容編輯" 
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
              <Tooltip title={isEditMode ? "管理文檔圖片" : "暫存圖片（儲存時上傳）"}>
                <Button
                  icon={<PictureOutlined />}
                  onClick={toggleDrawer}
                  size="small"
                  type={drawerVisible ? "primary" : "default"}
                  style={{ 
                    fontSize: '12px',
                    height: '28px'
                  }}
                >
                  📷 圖片管理 {!isEditMode && '(暫存)'}
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
      {isFullScreen && (
        <div style={{ position: 'fixed', top: '60px', right: '20px', zIndex: 9999 }}>
          <Button
            icon={<PictureOutlined />}
            onClick={() => {
              console.log('🖱️ 全螢幕按鈕被點擊');
              toggleDrawer();
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
            📷 圖片管理 {!isEditMode && '(暫存)'}
          </Button>
        </div>
      )}





      {/* 圖片管理側拉面板 */}
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PictureOutlined style={{ color: '#1890ff' }} />
            <span>圖片管理</span>
            {isEditMode ? (
              <span style={{ 
                fontSize: '12px', 
                color: '#666', 
                backgroundColor: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                ID: {id}
              </span>
            ) : (
              <span style={{ 
                fontSize: '12px', 
                color: '#fa8c16', 
                backgroundColor: '#fff7e6',
                padding: '2px 6px',
                borderRadius: '4px',
                border: '1px solid #ffd591'
              }}>
                暫存模式
              </span>
            )}
          </div>
        }
        placement="right"
        width={450}
        open={drawerVisible}
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
          stagingMode={!isEditMode}
          onGetStagedImages={(getterFn) => {
            getStagedImagesRef.current = getterFn;
          }}
        />
      </Drawer>
    </div>
  );
};

export default MarkdownEditorPage;