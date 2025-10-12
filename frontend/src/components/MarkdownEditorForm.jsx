import React, { useState, useEffect, useRef } from 'react';
import { Modal, Button, Input, message, Spin, Drawer, Tooltip } from 'antd';
import { SaveOutlined, CloseOutlined, PictureOutlined } from '@ant-design/icons';
import MdEditor from 'react-markdown-editor-lite';
import MarkdownIt from 'markdown-it';
import axios from 'axios';
import ContentImageManager from './ContentImageManager';
import 'react-markdown-editor-lite/lib/index.css';
import './MarkdownEditorForm.css';

const { TextArea } = Input;

// 初始化 Markdown 解析器
const mdParser = new MarkdownIt();

// 基礎樣式優化 - 全屏模式已經能完美解決工具欄固定問題

/**
 * Markdown 編輯器表單組件 (整頁模式)
 * 用於編輯 RVT Guide 內容
 */
const MarkdownEditorForm = ({ 
  visible, 
  onClose, 
  record = null, 
  onSave 
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    title: '',
    content: ''
  });
  
  // 圖片管理相關狀態
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [images, setImages] = useState([]);
  const [cursorPosition, setCursorPosition] = useState(0);
  const mdEditorRef = useRef(null);

  // 當 record 改變時，載入數據
  useEffect(() => {
    const loadData = async () => {
      if (record) {
        setLoading(true);
        
        try {
          // 載入現有記錄的數據
          setFormData({
            title: record.title || '',
            content: record.content || ''
          });
          
          // 載入圖片數據
          if (record.id) {
            const imagesResponse = await axios.get(`/api/content-images/?content_type=rvt-guide&content_id=${record.id}`);
            if (imagesResponse.data.results) {
              setImages(imagesResponse.data.results);
            } else if (Array.isArray(imagesResponse.data)) {
              setImages(imagesResponse.data);
            }
          }
        } catch (error) {
          console.error('載入圖片數據失敗:', error);
        } finally {
          setLoading(false);
        }
      } else {
        // 新建記錄，重置表單
        setFormData({
          title: '',
          content: ''
        });
        setImages([]);
      }
    };
    
    loadData();
  }, [record, visible]);

  // 編輯器初始化 - 全屏模式提供最佳編輯體驗
  useEffect(() => {
    if (visible) {
      // 可以在這裡添加其他編輯器初始化邏輯
      console.log('💡 提示：點擊工具欄右側的全屏按鈕 🔍 獲得最佳編輯體驗！');
    }
  }, [visible]);

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
      const url = record 
        ? `/api/rvt-guides/${record.id}/`  // 更新現有記錄
        : '/api/rvt-guides/';              // 創建新記錄

      const method = record ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({
          title: formData.title.trim(),
          content: formData.content.trim(),
          // 如果是新建記錄，設置默認值
          ...(record ? {} : {
            category: 'general',
            issue_type: 'guide',
            description: formData.title.trim()
          })
        })
      });

      const data = await response.json();

      if (response.ok && data.success !== false) {
        message.success(record ? '更新成功！' : '創建成功！');
        
        // 通知父組件刷新數據
        if (onSave) {
          onSave();
        }
        
        // 關閉編輯器
        onClose();
      } else {
        throw new Error(data.error || '儲存失敗');
      }
    } catch (error) {
      console.error('儲存錯誤:', error);
      message.error(`儲存失敗: ${error.message}`);
    } finally {
      setSaving(false);
    }
  };

  // 處理關閉
  const handleClose = () => {
    if (formData.title || formData.content) {
      Modal.confirm({
        title: '確認關閉',
        content: '有未儲存的更改，確定要關閉嗎？',
        onOk: onClose,
      });
    } else {
      onClose();
    }
  };

  // 圖片管理相關函數
  const handleImagesChange = (newImages) => {
    setImages(newImages);
    console.log('Markdown 編輯器圖片已更新:', newImages);
  };

  // 處理游標位置變更 (適配 MdEditor)
  const handleEditorCursorChange = () => {
    if (mdEditorRef.current) {
      try {
        // 獲取當前游標位置 (簡化版本，使用字符串方法)
        const editor = mdEditorRef.current;
        const textArea = editor.nodeMdText?.current;
        if (textArea) {
          setCursorPosition(textArea.selectionStart || 0);
        }
      } catch (error) {
        console.warn('無法獲取游標位置:', error);
      }
    }
  };

  // 在指定位置插入圖片資訊 (適配 MdEditor)
  const insertImageAtCursor = (imageInfo) => {
    const currentContent = formData.content || '';
    const beforeCursor = currentContent.slice(0, cursorPosition);
    const afterCursor = currentContent.slice(cursorPosition);
    
    // 插入圖片資訊
    const newContent = beforeCursor + imageInfo + afterCursor;
    
    // 更新內容
    setFormData(prev => ({
      ...prev,
      content: newContent
    }));
    
    // 更新編輯器內容
    if (mdEditorRef.current) {
      mdEditorRef.current.setText(newContent);
    }
    
    // 更新游標位置
    const newCursorPos = cursorPosition + imageInfo.length;
    setCursorPosition(newCursorPos);
    
    message.success('圖片已插入到編輯器中');
  };

  const handleContentUpdate = (updatedContent) => {
    // 當圖片操作導致內容更新時，更新編輯器內容
    setFormData(prev => ({
      ...prev,
      content: updatedContent
    }));
    
    if (mdEditorRef.current) {
      mdEditorRef.current.setText(updatedContent);
    }
    console.log('Markdown 編輯器內容已自動更新圖片引用');
  };

  return (
    <>
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>編輯 RVT Guide (Markdown 編輯器)</span>
            {record && <span style={{ color: '#666', fontSize: '14px' }}>ID: {record.id}</span>}
          </div>
        }
        open={visible}
        onCancel={handleClose}
        width="95vw"
        style={{ top: 20 }}
        bodyStyle={{ 
          height: 'calc(90vh - 108px)', 
          padding: '16px',
          display: 'flex',
          flexDirection: 'column'
        }}
      footer={[
        <Button 
          key="cancel" 
          onClick={handleClose}
          icon={<CloseOutlined />}
        >
          取消
        </Button>,
        <Tooltip key="images" title="圖片管理">
          <Button 
            icon={<PictureOutlined />}
            onClick={() => setDrawerVisible(!drawerVisible)}
            disabled={!record?.id}
            style={{ 
              color: drawerVisible ? '#1890ff' : '#666',
              borderColor: drawerVisible ? '#1890ff' : '#d9d9d9'
            }}
          >
            圖片管理
          </Button>
        </Tooltip>,
        <Button 
          key="save" 
          type="primary" 
          loading={saving}
          onClick={handleSave}
          icon={<SaveOutlined />}
        >
          {record ? '更新' : '儲存'}
        </Button>,
      ]}
    >
      {loading ? (
        <div style={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          height: '200px' 
        }}>
          <Spin size="large" />
        </div>
      ) : (
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
          {/* 標題輸入 */}
          <div style={{ marginBottom: '16px' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '4px', 
              fontWeight: 'bold' 
            }}>
              標題 *
            </label>
            <Input
              value={formData.title}
              onChange={handleTitleChange}
              placeholder="請輸入標題..."
              size="large"
            />
          </div>

          {/* Markdown 編輯器 */}
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <label style={{ 
              display: 'block', 
              marginBottom: '8px', 
              fontWeight: 'bold' 
            }}>
              內容編輯 (支援 Markdown 語法) *
            </label>
            
            <div className="markdown-editor-container" style={{ 
              flex: 1, 
              minHeight: '400px',
              position: 'relative',
              display: 'flex',
              flexDirection: 'column'
            }}>
              <MdEditor
                ref={mdEditorRef}
                value={formData.content}
                style={{ 
                  height: '100%',
                  width: '100%',
                  border: 'none',
                  position: 'relative'
                }}
                renderHTML={(text) => mdParser.render(text)}
                onChange={handleEditorChange}
                onFocus={handleEditorCursorChange}
                onClick={handleEditorCursorChange}
                onKeyUp={handleEditorCursorChange}
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
                    fullScreen: true,   // 🎯 重點：啟用全屏模式
                    hideMenu: false
                  },
                  htmlClass: 'markdown-preview-custom',
                  markdownClass: 'markdown-editor-custom',
                  syncScrollMode: ['leftFollowRight', 'rightFollowLeft'],
                  logger: {
                    debug: false,
                    info: false,
                    warn: false,
                    error: true
                  },
                  // 自定義工具欄按鈕順序，讓全屏按鈕更顯眼
                  shortcuts: true
                }}
              />
            </div>
          </div>
          
          {/* 提示信息 */}
          <div style={{ 
            marginTop: '12px', 
            padding: '12px', 
            backgroundColor: '#e6f7ff', 
            border: '1px solid #91d5ff',
            borderRadius: '6px',
            fontSize: '13px',
            color: '#1890ff'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>
              💡 編輯技巧提示：
            </div>
            <div style={{ marginBottom: '6px' }}>
              • <strong>全屏編輯</strong>：點擊工具欄右側的 <strong>🔍</strong> 按鈕進入全屏模式，工具欄將固定在頂部，提供最佳編輯體驗
            </div>
            <div style={{ marginBottom: '6px' }}>
              • <strong>Markdown 語法</strong>：支援標題 (#)、列表 (-)、連結 ([text](url))、圖片、表格等
            </div>
            <div>
              • <strong>即時預覽</strong>：右側面板可以即時查看 Markdown 渲染效果
            </div>
          </div>
        </div>
      )}
    </Modal>

    {/* 圖片管理側拉面板 */}
    <Drawer
      className="image-manager-drawer"
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <PictureOutlined style={{ color: '#1890ff' }} />
          <span>圖片管理</span>
          {record && (
            <span style={{ 
              fontSize: '12px', 
              color: '#666', 
              backgroundColor: '#f5f5f5',
              padding: '2px 6px',
              borderRadius: '4px'
            }}>
              ID: {record.id}
            </span>
          )}
        </div>
      }
      placement="right"
      width={450}
      open={drawerVisible && record?.id}
      onClose={() => setDrawerVisible(false)}
      bodyStyle={{ padding: '12px' }}
      headerStyle={{ 
        borderBottom: '1px solid #e8e8e8',
        backgroundColor: '#fafafa'
      }}
      extra={
        <Tooltip title="關閉圖片管理">
          <Button 
            type="text" 
            icon={<CloseOutlined />}
            onClick={() => setDrawerVisible(false)}
          />
        </Tooltip>
      }
    >
      {record?.id ? (
        <ContentImageManager
          contentType="rvt-guide"
          contentId={record.id}
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
    </>
  );
};

export default MarkdownEditorForm;