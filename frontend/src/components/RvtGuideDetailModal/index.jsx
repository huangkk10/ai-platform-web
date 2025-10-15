import React from 'react';
import { Modal, Button, Tag } from 'antd';
import { FileTextOutlined, EditOutlined } from '@ant-design/icons';
import BasicInfoSection from './BasicInfoSection';
import ContentSection from './ContentSection';
import CategorySection from './CategorySection';

/**
 * RVT Guide 詳細內容 Modal 組件
 * 整合所有 Section 子組件，顯示文檔的完整信息
 * 
 * @param {boolean} visible - Modal 是否可見
 * @param {Object} guide - 文檔詳細資料
 * @param {Function} onClose - 關閉 Modal 的回調函數
 * @param {Function} onEdit - 編輯按鈕的回調函數
 */
const RvtGuideDetailModal = ({ 
  visible, 
  guide, 
  onClose, 
  onEdit 
}) => {
  const handleEdit = () => {
    if (guide && onEdit) {
      onEdit(guide.id);
    }
  };

  return (
    <Modal
      title={
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <FileTextOutlined style={{ color: '#1890ff' }} />
          <span>資料預覽</span>
          {guide && (
            <Tag color="blue" style={{ marginLeft: '8px' }}>
              {guide.title}
            </Tag>
          )}
        </div>
      }
      open={visible}
      onCancel={onClose}
      footer={[
        <Button 
          key="edit" 
          type="primary" 
          icon={<EditOutlined />}
          onClick={handleEdit}
        >
          編輯指導文檔
        </Button>,
        <Button key="close" onClick={onClose}>
          關閉
        </Button>
      ]}
      width={900}
    >
      {guide && (
        <div style={{ maxHeight: '70vh', overflowY: 'auto', padding: '0 4px' }}>
          {/* 基本信息區塊 */}
          <BasicInfoSection guide={guide} />
          
          {/* 文檔內容區塊 */}
          <ContentSection content={guide.content} />
          
          {/* 分類路徑區塊（如果有的話）*/}
          {guide.full_category_name && (
            <CategorySection categoryName={guide.full_category_name} />
          )}
        </div>
      )}
    </Modal>
  );
};

export default RvtGuideDetailModal;
