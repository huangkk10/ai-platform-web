import React, { useState } from 'react';
import { Modal, Descriptions, Tag, Button, Typography, Divider, message, Space } from 'antd';
import { 
  FileTextOutlined, 
  StarFilled, 
  CopyOutlined, 
  DatabaseOutlined,
  FileOutlined,
  PercentageOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import { convertImageReferencesToMarkdown } from '../../utils/imageReferenceConverter';
import useMessageFormatter from '../../hooks/useMessageFormatter';
import '../markdown/ReactMarkdown.css';
import './SourceDetailModal.css';

const { Text, Title } = Typography;

/**
 * SourceDetailModal 組件
 * 顯示引用來源的完整詳細資訊
 * 
 * @param {boolean} visible - Modal 顯示狀態
 * @param {Object} source - 選中的來源資料
 * @param {Function} onClose - 關閉回調
 */
const SourceDetailModal = ({ visible, source, onClose }) => {
  const [copying, setCopying] = useState(false);
  
  // 🎯 獲取 Markdown 配置（包含 CustomImage 組件）
  const { markdownConfig } = useMessageFormatter();

  // 如果沒有 source，不渲染
  if (!source) {
    return null;
  }

  /**
   * 獲取相似度分數顏色
   */
  const getScoreColor = (score) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'gold';
    return 'default';
  };

  /**
   * 獲取相關度標籤
   */
  const getRelevanceLabel = (score) => {
    if (score >= 0.8) return '高度相關';
    if (score >= 0.6) return '中度相關';
    return '低度相關';
  };

  /**
   * 格式化相似度分數
   */
  const formatScore = (score) => {
    return `${Math.round(score * 100)}%`;
  };

  /**
   * 複製內容到剪貼簿
   */
  const handleCopyContent = async () => {
    try {
      setCopying(true);
      await navigator.clipboard.writeText(source.content);
      message.success('內容已複製到剪貼簿');
    } catch (error) {
      message.error('複製失敗，請手動複製');
      console.error('Copy failed:', error);
    } finally {
      setCopying(false);
    }
  };

  /**
   * Modal 標題
   */
  const modalTitle = (
    <Space>
      <FileTextOutlined style={{ color: '#1890ff', fontSize: '18px' }} />
      <Text strong style={{ fontSize: '16px' }}>{source.document_name}</Text>
      <Tag 
        color={getScoreColor(source.score)}
        icon={<StarFilled />}
      >
        {formatScore(source.score)}
      </Tag>
    </Space>
  );

  /**
   * Modal Footer
   */
  const modalFooter = [
    <Button 
      key="copy" 
      icon={<CopyOutlined />}
      onClick={handleCopyContent}
      loading={copying}
    >
      複製內容
    </Button>,
    <Button key="close" type="primary" onClick={onClose}>
      關閉
    </Button>
  ];

  return (
    <Modal
      title={modalTitle}
      open={visible}
      onCancel={onClose}
      width={800}
      footer={modalFooter}
      className="source-detail-modal"
      destroyOnClose
      maskClosable={true}
    >
      {/* Metadata 區域 */}
      <div className="source-metadata">
        <Descriptions column={2} size="small" bordered>
          <Descriptions.Item 
            label={<><DatabaseOutlined /> 知識庫</>}
            span={2}
          >
            {source.dataset_name || source.knowledge_base || 'Protocol Knowledge Base'}
          </Descriptions.Item>
          
          <Descriptions.Item 
            label={<><PercentageOutlined /> 相似度</>}
          >
            <Space>
              <Tag color={getScoreColor(source.score)}>
                {formatScore(source.score)}
              </Tag>
              <Text type="secondary">({getRelevanceLabel(source.score)})</Text>
            </Space>
          </Descriptions.Item>
          
          <Descriptions.Item 
            label={<><FileOutlined /> 位置</>}
          >
            {source.position ? `第 ${source.position} 名` : 'N/A'}
          </Descriptions.Item>
          
          {source.document_id && (
            <Descriptions.Item label="文件 ID" span={2}>
              <Text code copyable>{source.document_id}</Text>
            </Descriptions.Item>
          )}
          
          {source.segment_id && (
            <Descriptions.Item label="片段 ID" span={2}>
              <Text code copyable>{source.segment_id}</Text>
            </Descriptions.Item>
          )}
        </Descriptions>
      </div>
      
      <Divider />
      
      {/* 內容區域 */}
      <div className="source-content">
        <Title level={5} style={{ marginBottom: '12px' }}>
          📝 引用內容：
        </Title>
        
        <div className="markdown-content-container">
          {source.content ? (
            <div className="markdown-preview-content">
              <ReactMarkdown {...markdownConfig}>
                {convertImageReferencesToMarkdown(source.content)}
              </ReactMarkdown>
            </div>
          ) : (
            <Text type="secondary">無內容</Text>
          )}
        </div>
      </div>
    </Modal>
  );
};

export default SourceDetailModal;
