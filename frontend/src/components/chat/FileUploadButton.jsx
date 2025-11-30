/**
 * FileUploadButton 元件
 * =======================
 * 
 * 檔案上傳按鈕，用於 Assistant 聊天頁面
 * 
 * 功能：
 * - 點擊觸發檔案選擇對話框
 * - 支援圖片和文字檔
 * - 顯示 loading 狀態
 */

import React, { useRef } from 'react';
import { Button, Tooltip } from 'antd';
import { PlusOutlined } from '@ant-design/icons';

// 接受的檔案類型
const ACCEPTED_TYPES = [
  'image/jpeg',
  'image/png',
  'image/gif',
  'image/bmp',
  'image/webp',
  'text/plain',
  '.txt',
  '.log',
  '.md'
].join(',');

const FileUploadButton = ({ 
  onFileSelect, 
  disabled = false, 
  loading = false,
  className = '',
  style = {}
}) => {
  const fileInputRef = useRef(null);
  
  const handleClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file && onFileSelect) {
      onFileSelect(file);
    }
    // 清除 input 以便重複選擇相同檔案
    e.target.value = '';
  };
  
  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept={ACCEPTED_TYPES}
        style={{ display: 'none' }}
      />
      <Tooltip title="上傳圖片或文字檔（支援 OCR 辨識）">
        <Button
          type="text"
          icon={<PlusOutlined />}
          onClick={handleClick}
          disabled={disabled || loading}
          loading={loading}
          className={`file-upload-btn ${className}`}
          style={{
            // 🎨 樣式參考 Web AI OCR 的 image-upload-btn-inside
            border: '1px solid #1890ff',
            background: '#e6f7ff',
            color: '#1890ff',
            borderRadius: '50%',
            width: '34px',
            height: '34px',
            minWidth: '34px',
            padding: 0,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 2px 6px rgba(24, 144, 255, 0.25)',
            fontSize: '15px',
            transition: 'all 0.2s ease',
            flexShrink: 0,
            ...style
          }}
        />
      </Tooltip>
    </>
  );
};

export default FileUploadButton;
