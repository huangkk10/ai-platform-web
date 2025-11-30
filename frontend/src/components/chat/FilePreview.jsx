/**
 * FilePreview 元件
 * ==================
 * 
 * 已上傳檔案的預覽元件
 * 
 * 功能：
 * - 顯示檔案縮圖（圖片）或圖示（文字檔）
 * - 顯示檔案名稱和大小
 * - 顯示處理狀態（OCR 中、已完成）
 * - 預覽辨識/讀取的文字內容
 * - 移除按鈕
 */

import React from 'react';
import { Card, Image, Typography, Button, Tag } from 'antd';
import { 
  FileTextOutlined, 
  CloseOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';

const { Text } = Typography;

const FilePreview = ({ 
  file,           // 上傳的檔案
  previewUrl,     // 圖片預覽 URL
  fileContent,    // OCR 結果或文字檔內容
  isProcessing,   // 是否正在處理中
  isImage,        // 是否為圖片
  onRemove,       // 移除檔案回調
  showPreviewText = true,  // 是否顯示文字預覽
  maxPreviewLength = 300   // 預覽文字最大長度
}) => {
  if (!file) return null;
  
  return (
    <Card 
      size="small" 
      style={{ 
        marginBottom: 8,
        background: '#fafafa',
        border: '1px solid #e8e8e8'
      }}
      styles={{ body: { padding: '8px 12px' } }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
        {/* 檔案圖示或縮圖 */}
        {isImage && previewUrl ? (
          <Image
            src={previewUrl}
            width={48}
            height={48}
            style={{ 
              objectFit: 'cover', 
              borderRadius: 4,
              border: '1px solid #d9d9d9'
            }}
            preview={{
              mask: <div style={{ fontSize: '10px' }}>預覽</div>
            }}
          />
        ) : (
          <div style={{
            width: 48,
            height: 48,
            backgroundColor: '#e6f7ff',
            border: '1px solid #91d5ff',
            borderRadius: 4,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}>
            <FileTextOutlined style={{ fontSize: 24, color: '#1890ff' }} />
          </div>
        )}
        
        {/* 檔案資訊 */}
        <div style={{ flex: 1, minWidth: 0 }}>
          <Text 
            strong 
            ellipsis 
            style={{ 
              display: 'block',
              maxWidth: '100%',
              fontSize: 13
            }}
            title={file.name}
          >
            {file.name}
          </Text>
          
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8, 
            marginTop: 4 
          }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              {(file.size / 1024).toFixed(1)} KB
            </Text>
            
            {/* 處理狀態 */}
            {isProcessing && (
              <Tag 
                icon={<LoadingOutlined spin />} 
                color="processing"
                style={{ fontSize: 11, padding: '0 6px' }}
              >
                {isImage ? 'OCR 辨識中...' : '讀取中...'}
              </Tag>
            )}
            {!isProcessing && fileContent && (
              <Tag 
                icon={<CheckCircleOutlined />} 
                color="success"
                style={{ fontSize: 11, padding: '0 6px' }}
              >
                已處理
              </Tag>
            )}
          </div>
        </div>
        
        {/* 移除按鈕 */}
        <Button 
          type="text" 
          size="small" 
          icon={<CloseOutlined />} 
          onClick={onRemove}
          disabled={isProcessing}
          style={{ 
            color: '#999',
            flexShrink: 0
          }}
          title="移除檔案"
        />
      </div>
      
      {/* 預覽文字內容 */}
      {showPreviewText && !isProcessing && fileContent && (
        <div style={{ 
          marginTop: 8, 
          padding: 8, 
          background: '#fff', 
          borderRadius: 4,
          border: '1px solid #e8e8e8',
          maxHeight: 80,
          overflow: 'auto'
        }}>
          <Text style={{ 
            fontSize: 11, 
            whiteSpace: 'pre-wrap',
            color: '#666',
            lineHeight: 1.4
          }}>
            {fileContent.substring(0, maxPreviewLength)}
            {fileContent.length > maxPreviewLength && '...'}
          </Text>
        </div>
      )}
    </Card>
  );
};

export default FilePreview;
