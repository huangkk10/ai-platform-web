/**
 * FilePreviewInline 元件
 * =========================
 * 
 * 內聯版本的檔案預覽元件（在輸入框內部顯示）
 * 參考 Web AI OCR 的 image-preview-item-inline 樣式
 * 
 * 功能：
 * - 小型縮圖顯示（32x32）
 * - 懸停顯示檔名和狀態
 * - 三種狀態：待處理 → 處理中 → 已處理
 * - 移除按鈕（懸停顯示）
 */

import React, { useState, useEffect } from 'react';
import { Image, Button, Spin, Typography } from 'antd';
import { 
  FileTextOutlined, 
  DeleteOutlined,
  LoadingOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';

const { Text } = Typography;

const FilePreviewInline = ({ 
  file,           // 上傳的檔案
  fileContent,    // OCR 結果或文字檔內容（處理完成後才有）
  isProcessing,   // 是否正在處理中
  isProcessed,    // 是否已處理完成（新增）
  onRemove        // 移除檔案回調
}) => {
  const [previewUrl, setPreviewUrl] = useState(null);
  
  // 判斷檔案類型
  const isImage = file?.type?.startsWith('image/');
  
  // 判斷狀態
  const isPending = !isProcessing && !isProcessed && !fileContent;
  const isDone = isProcessed || !!fileContent;
  
  // 生成圖片預覽 URL
  useEffect(() => {
    if (file && isImage) {
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
      return () => URL.revokeObjectURL(url);
    }
    return () => {};
  }, [file, isImage]);
  
  if (!file) return null;
  
  // 狀態提示文字
  const getStatusTooltip = () => {
    if (isProcessing) return ' - 處理中...';
    if (isDone) return ' - 已處理';
    if (isPending) return ' - 送出時處理';
    return '';
  };
  
  return (
    <div 
      className="file-preview-item-inline"
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        background: '#f8f9fa',
        borderRadius: '6px',
        padding: '2px',
        border: `1px solid ${isProcessing ? '#1890ff' : isPending ? '#faad14' : '#52c41a'}`,
        transition: 'border-color 0.2s'
      }}
      title={`${file.name} (${(file.size / 1024).toFixed(1)} KB)${getStatusTooltip()}`}
    >
      {isProcessing ? (
        // 加載狀態的骨架屏
        <div 
          className="file-loading-skeleton"
          style={{
            width: '32px',
            height: '32px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#e6f7ff',
            borderRadius: '4px',
            border: '1px dashed #1890ff',
            animation: 'pulse 1.5s ease-in-out infinite'
          }}
        >
          <Spin size="small" indicator={<LoadingOutlined style={{ fontSize: 12, color: '#1890ff' }} spin />} />
          <Text style={{ fontSize: '8px', color: '#1890ff', marginTop: '2px', fontWeight: 'bold' }}>
            {isImage ? 'OCR' : '讀取'}
          </Text>
        </div>
      ) : (
        // 正常的檔案預覽
        <>
          {isImage && previewUrl ? (
            // 圖片檔案預覽
            <div style={{ position: 'relative' }}>
              <Image
                src={previewUrl}
                alt={file.name}
                width={32}
                height={32}
                style={{ 
                  objectFit: 'cover',
                  borderRadius: '4px',
                  border: `1px solid ${isPending ? '#faad14' : '#52c41a'}`
                }}
                preview={{
                  mask: <div style={{ fontSize: '10px' }}>預覽</div>
                }}
              />
              {/* 🆕 狀態角標 */}
              {isPending && (
                <div 
                  style={{
                    position: 'absolute',
                    bottom: '-2px',
                    right: '-2px',
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#faad14',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid white'
                  }}
                >
                  <ClockCircleOutlined style={{ fontSize: '8px', color: 'white' }} />
                </div>
              )}
              {isDone && (
                <div 
                  style={{
                    position: 'absolute',
                    bottom: '-2px',
                    right: '-2px',
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#52c41a',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid white'
                  }}
                >
                  <CheckCircleOutlined style={{ fontSize: '8px', color: 'white' }} />
                </div>
              )}
            </div>
          ) : (
            // 文字檔案預覽
            <div style={{ position: 'relative' }}>
              <div
                style={{
                  width: 32,
                  height: 32,
                  backgroundColor: isPending ? '#fffbe6' : '#f6ffed',
                  border: `1px solid ${isPending ? '#faad14' : '#52c41a'}`,
                  borderRadius: '4px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  color: isPending ? '#faad14' : '#52c41a'
                }}
              >
                <FileTextOutlined />
              </div>
              {/* 🆕 狀態角標 */}
              {isPending && (
                <div 
                  style={{
                    position: 'absolute',
                    bottom: '-2px',
                    right: '-2px',
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#faad14',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid white'
                  }}
                >
                  <ClockCircleOutlined style={{ fontSize: '8px', color: 'white' }} />
                </div>
              )}
              {isDone && (
                <div 
                  style={{
                    position: 'absolute',
                    bottom: '-2px',
                    right: '-2px',
                    width: '12px',
                    height: '12px',
                    backgroundColor: '#52c41a',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: '1px solid white'
                  }}
                >
                  <CheckCircleOutlined style={{ fontSize: '8px', color: 'white' }} />
                </div>
              )}
            </div>
          )}
          
          {/* 移除按鈕 */}
          <Button
            type="text"
            icon={<DeleteOutlined />}
            size="small"
            onClick={onRemove}
            style={{
              position: 'absolute',
              top: '-6px',
              right: '-6px',
              width: '16px',
              height: '16px',
              minWidth: '16px',
              backgroundColor: '#ff4d4f',
              color: 'white',
              border: '1px solid white',
              borderRadius: '50%',
              padding: 0,
              fontSize: '8px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)'
            }}
            className="file-remove-btn-inline"
          />
        </>
      )}
    </div>
  );
};

export default FilePreviewInline;
