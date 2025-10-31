import React, { useState } from 'react';
import { Card, Space, Typography, Badge } from 'antd';
import { DatabaseOutlined } from '@ant-design/icons';
import SourceCard from './SourceCard';
import SourceDetailModal from './SourceDetailModal';
import './RetrievalSourcesDisplay.css';

const { Text } = Typography;

/**
 * RetrievalSourcesDisplay 組件
 * 顯示 AI 回覆引用的知識庫來源列表
 * 
 * @param {Array} retrieverResources - 引用來源資料陣列
 * @param {number} maxDisplay - 最多顯示幾個來源（默認 5）
 */
const RetrievalSourcesDisplay = ({ 
  retrieverResources = [],
  maxDisplay = 5 
}) => {
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedSource, setSelectedSource] = useState(null);

  // 兼容不同的命名方式
  const sources = retrieverResources || [];
  
  // 如果沒有引用來源，顯示提示訊息
  if (!sources || sources.length === 0) {
    return (
      <div className="no-sources-container">
        <Text type="secondary" style={{ fontSize: '13px' }}>
          💡 此回答基於 AI 的通用知識，未使用知識庫資料
        </Text>
      </div>
    );
  }

  /**
   * 處理來源卡片點擊
   */
  const handleSourceClick = (source) => {
    setSelectedSource(source);
    setModalVisible(true);
  };

  /**
   * 關閉 Modal
   */
  const handleCloseModal = () => {
    setModalVisible(false);
    // 延遲清空選中的來源，避免 Modal 關閉動畫時看到空白內容
    setTimeout(() => {
      setSelectedSource(null);
    }, 300);
  };

  /**
   * 過濾和排序來源
   */
  const validSources = sources
    .filter(source => 
      source && 
      source.document_name && 
      source.content &&
      typeof source.score === 'number'
    )
    .sort((a, b) => b.score - a.score)  // 按相似度降序排列
    .slice(0, maxDisplay);  // 限制顯示數量

  // 如果過濾後沒有有效來源
  if (validSources.length === 0) {
    return (
      <div className="no-sources-container">
        <Text type="secondary" style={{ fontSize: '13px' }}>
          💡 此回答基於 AI 的通用知識，未使用知識庫資料
        </Text>
      </div>
    );
  }

  return (
    <div className="retrieval-sources-container">
      <Card
        title={
          <Space>
            <DatabaseOutlined style={{ color: '#1890ff' }} />
            <Text strong>引用來源</Text>
            <Badge 
              count={validSources.length} 
              style={{ backgroundColor: '#1890ff' }}
              showZero={false}
            />
          </Space>
        }
        size="small"
        className="retrieval-sources-card"
        bodyStyle={{ padding: '12px' }}
      >
        {/* Grid 布局顯示引用來源卡片 */}
        <div className="sources-list">
          {validSources.map((source, index) => (
            <SourceCard
              key={`source-${index}-${source.document_id || index}`}
              source={source}
              onClick={() => handleSourceClick(source)}
              index={index}
            />
          ))}
        </div>
        
        {/* 如果實際來源數量超過顯示數量，顯示提示 */}
        {sources.length > maxDisplay && (
          <div style={{ marginTop: '8px', textAlign: 'center' }}>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              還有 {sources.length - maxDisplay} 個引用來源未顯示
            </Text>
          </div>
        )}
      </Card>

      {/* 來源詳細內容 Modal */}
      <SourceDetailModal
        visible={modalVisible}
        source={selectedSource}
        onClose={handleCloseModal}
      />
    </div>
  );
};

export default RetrievalSourcesDisplay;
