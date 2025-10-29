/**
 * 通用 Markdown 編輯器佈局組件
 * 支援多種內容類型的 Markdown 編輯
 * 
 * 使用範例：
 * <MarkdownEditorLayout 
 *   contentType="rvt-guide"
 *   contentId={id}
 *   navigate={navigate}
 * />
 */

import React, { useEffect, useRef, useCallback } from 'react';
import { Input, Spin, Card, Drawer, Tooltip, Button } from 'antd';
import { PictureOutlined, CloseOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import 'react-markdown-editor-lite/lib/index.css';

// 組件導入
import ContentImageManager from '../ContentImageManager';

// Hook 導入
import useContentEditor from '../../hooks/useContentEditor';
import useMarkdownCursor from '../../hooks/useMarkdownCursor';
import useFullScreenDetection from '../../hooks/useFullScreenDetection';
import useImageManager from '../../hooks/useImageManager';

// 工具導入
import { uploadStagedImages } from '../../utils/uploadStagedImages';

// 存儲圖片管理器回調的全局變數（使用閉包）
let globalImageManagerHandler = null;

// 自定義圖片管理插件
class ImageManagerPlugin extends React.Component {
  static pluginName = 'image-manager';
  static align = 'left';

  constructor(props) {
    super(props);
    this.handleClick = this.handleClick.bind(this);
  }

  handleClick() {
    console.log('🖼️ 圖片管理按鈕被點擊');

    if (globalImageManagerHandler && typeof globalImageManagerHandler === 'function') {
      console.log('✅ 執行 globalImageManagerHandler');
      globalImageManagerHandler();
    } else {
      console.error('❌ globalImageManagerHandler 未定義');
      console.log('Handler type:', typeof globalImageManagerHandler);
    }
  }

  render() {
    return (
      <span
        className="button button-type-image-manager"
        title="圖片管理"
        onClick={this.handleClick}
        style={{
          cursor: 'pointer',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '4px 8px',
          fontSize: '14px',
          userSelect: 'none'
        }}
      >
        📷
      </span>
    );
  }
}

// 註冊插件
MdEditor.use(ImageManagerPlugin);

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

  /* 圖片管理按鈕樣式 */
  .rc-md-editor .button.button-type-image-manager {
    display: inline-flex !important;
    align-items: center;
    justify-content: center;
    min-width: 30px;
    height: 30px;
    padding: 4px 8px;
    border: 1px solid #d9d9d9;
    border-radius: 4px;
    background: #fff;
    transition: all 0.2s;
    margin: 0 2px;
    cursor: pointer;
    font-size: 16px;
  }
  
  .rc-md-editor .button.button-type-image-manager:hover {
    border-color: #1890ff;
    background: #f0f8ff;
  }
  
  .rc-md-editor .button.button-type-image-manager.active {
    border-color: #1890ff;
    background: #1890ff;
    filter: brightness(1.1);
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
 * Markdown 編輯器佈局組件
 */
const MarkdownEditorLayout = ({
  contentType = 'rvt-guide',
  contentId,
  navigate,
  customConfig = {},
  onBeforeSave,       // 儲存前鉤子
  onAfterSave,        // 儲存後鉤子
  onSavingChange,     // 儲存狀態變更回調
  renderExtraFields,  // 渲染額外欄位的插槽
  renderToolbarExtra, // 渲染工具欄額外按鈕的插槽
}) => {
  const mdEditorRef = useRef(null);
  const getStagedImagesRef = useRef(null);

  // 使用通用內容編輯器 Hook
  const {
    config,
    loading,
    // saving, // 未使用，註釋掉避免警告
    formData,
    images,
    isEditMode,
    loadData,
    saveData,
    handleTitleChange,
    handleContentChange,
    setFormData,
    setSaving
  } = useContentEditor(contentType, contentId, navigate, customConfig);

  // 使用圖片管理 Hook
  const {
    drawerVisible,
    toggleDrawer,
    handleImagesChange: handleImageManagerChange,
    handleContentUpdate,
  } = useImageManager(mdEditorRef, setFormData);

  // 組合圖片變更處理
  const handleImagesChange = (newImages) => {
    handleImageManagerChange(newImages);
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
    // toggleFullScreen // 未使用，註釋掉避免警告
  } = useFullScreenDetection();

  // 調試：確認 toggleDrawer 函數
  useEffect(() => {
    console.log('🔧 MarkdownEditorLayout 初始化');
    console.log('📷 toggleDrawer 函數:', typeof toggleDrawer);
    console.log('📂 drawerVisible:', drawerVisible);
    console.log('📝 contentType:', contentType);
    console.log('🎨 isEditMode:', isEditMode);

    // 設置全局圖片管理處理函數
    globalImageManagerHandler = toggleDrawer;
    console.log('✅ 已設置 globalImageManagerHandler');

    // 清理函數
    return () => {
      globalImageManagerHandler = null;
      console.log('🧹 已清除 globalImageManagerHandler');
    };
  }, [toggleDrawer, drawerVisible, contentType, isEditMode]);

  // 載入現有記錄數據（編輯模式）
  useEffect(() => {
    if (isEditMode && contentId) {
      loadData();
    }
  }, [contentId, isEditMode]); // 只依賴 contentId 和 isEditMode，loadData 函數穩定

  // 處理儲存 - 支援暫存圖片上傳
  const handleSave = useCallback(async () => {
    try {
      // 通知父組件開始儲存
      if (onSavingChange) onSavingChange(true);

      // 執行儲存前鉤子
      let dataToSave = { ...formData };
      if (onBeforeSave) {
        dataToSave = await onBeforeSave(dataToSave);
        if (!dataToSave) {
          if (onSavingChange) onSavingChange(false);
          return; // 如果返回 falsy，取消儲存
        }
      }

      // 先儲存文檔本體
      const result = await saveData(dataToSave, {
        navigateAfterSave: false, // 先不導航，等圖片上傳完成
        redirectPath: config.listRoute
      });

      if (!result) {
        if (onSavingChange) onSavingChange(false);
        return; // 儲存失敗，不繼續
      }

      // 如果是新建模式且有暫存圖片，批量上傳
      if (!isEditMode && getStagedImagesRef.current) {
        const stagedImages = getStagedImagesRef.current();

        if (stagedImages && stagedImages.length > 0) {
          setSaving(true);

          try {
            await uploadStagedImages(
              result.id,
              contentType,
              stagedImages,
              config.imageEndpoint
            );
          } catch (error) {
            console.error('❌ 圖片上傳過程異常:', error);
          } finally {
            setSaving(false);
          }
        }
      }

      // 執行儲存後鉤子
      if (onAfterSave) {
        await onAfterSave(result);
      }

      // 通知父組件儲存完成
      if (onSavingChange) onSavingChange(false);

      // 導航到列表頁 (使用 setTimeout 確保 message 顯示後再跳轉)
      setTimeout(() => {
        navigate(config.listRoute);
      }, 300);

    } catch (error) {
      console.error('❌ 儲存過程發生錯誤:', error);
      setSaving(false);
      if (onSavingChange) onSavingChange(false);
    }
  }, [formData, onBeforeSave, onSavingChange, saveData, config.listRoute, isEditMode, getStagedImagesRef, contentType, config.imageEndpoint, setSaving, onAfterSave, navigate]);

  // 使用 ref 保存最新的 handleSave 函數
  const handleSaveRef = useRef(handleSave);

  useEffect(() => {
    handleSaveRef.current = handleSave;
  }, [handleSave]);

  // 監聽來自 TopHeader 的保存事件
  useEffect(() => {
    const eventName = config.saveEventName || 'topheader-save';

    const handleSaveEvent = () => {
      console.log('🎯 收到儲存事件:', eventName);
      if (handleSaveRef.current) {
        handleSaveRef.current();
      }
    };

    console.log('📡 註冊儲存事件監聽器:', eventName);
    window.addEventListener(eventName, handleSaveEvent);

    return () => {
      console.log('🔌 移除儲存事件監聽器:', eventName);
      window.removeEventListener(eventName, handleSaveEvent);
    };
  }, [config.saveEventName]);

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
          gap: '16px',
          overflow: 'hidden'  // 防止外層產生滾動，確保 toolbar sticky 生效
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
                {config.labels.title}
              </label>
              <Input
                value={typeof formData.title === 'string' ? formData.title : ''}
                onChange={handleTitleChange}
                placeholder={`請輸入${config.labels.title}...`}
                size="large"
                style={{ fontSize: '16px' }}
              />
            </div>

            {/* 額外欄位插槽 */}
            {renderExtraFields && (
              <div style={{ marginTop: '16px' }}>
                {renderExtraFields(formData, setFormData)}
              </div>
            )}
          </Card>

          {/* Markdown 編輯器 */}
          <Card
            title={config.labels.content}
            size="small"
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              minHeight: 0  // 重要：允許 flex 子元素正確收縮
            }}
            bodyStyle={{
              flex: 1,
              padding: '16px',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden',  // 防止 Card 內部產生外層滾動
              minHeight: 0         // 確保高度受控
            }}
          >
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
                  },
                  imageManager: {
                    onImageManagerClick: toggleDrawer,
                    isActive: drawerVisible,
                    label: isEditMode ? config.labels.imageManager : config.labels.imageManagerStaging
                  }
                }}
                plugins={[...config.editorPlugins, 'image-manager']}
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
              {config.hints.markdown}
            </div>
          </Card>
        </div>
      )}

      {/* 全螢幕模式下的浮動圖片管理按鈕 */}
      {isFullScreen && (
        <div style={{ position: 'fixed', top: '60px', right: '20px', zIndex: 9999 }}>
          <Button
            icon={<PictureOutlined />}
            onClick={toggleDrawer}
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
            📷 {isEditMode ? config.labels.imageManager : config.labels.imageManagerStaging}
          </Button>
        </div>
      )}

      {/* 圖片管理側拉面板 */}
      <Drawer
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <PictureOutlined style={{ color: '#1890ff' }} />
            <span>{config.labels.imageManager}</span>
            {isEditMode ? (
              <span style={{
                fontSize: '12px',
                color: '#666',
                backgroundColor: '#f5f5f5',
                padding: '2px 6px',
                borderRadius: '4px'
              }}>
                ID: {contentId}
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
          contentType={contentType}
          contentId={contentId}
          images={images}
          onImagesChange={handleImagesChange}
          onContentUpdate={handleContentUpdate}
          onImageInsert={insertImageAtCursor}
          cursorPosition={cursorPosition}
          maxImages={config.imageConfig.maxImages}
          maxSizeMB={config.imageConfig.maxSizeMB}
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

export default MarkdownEditorLayout;
