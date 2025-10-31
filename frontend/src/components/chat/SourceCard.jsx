import React from 'react';
import { Card, Typography, Tag, Space } from 'antd';
import { FileTextOutlined, StarFilled, RightOutlined } from '@ant-design/icons';
import './SourceCard.css';

const { Text } = Typography;

/**
 * SourceCard 組件
 * 顯示單個引用來源的預覽卡片，可點擊查看詳情
 * 
 * @param {Object} source - 來源資料
 * @param {Function} onClick - 點擊回調
 * @param {number} index - 索引位置
 */
const SourceCard = ({ source, onClick, index }) => {
  if (!source) return null;

  /**
   * 獲取相似度分數顏色
   */
  const getScoreColor = (score) => {
    if (score >= 0.8) return 'green';
    if (score >= 0.6) return 'gold';
    return 'default';
  };

  /**
   * 格式化相似度分數
   */
  const formatScore = (score) => {
    return `${Math.round(score * 100)}%`;
  };

  /**
   * 處理卡片點擊
   */
  const handleClick = () => {
    if (onClick) {
      onClick(source, index);
    }
  };

  return (
    <div className="source-card" onClick={handleClick}>
      <div className="source-card-header">
        <div className="source-card-title">
          <FileTextOutlined style={{ marginRight: '6px', color: '#1890ff' }} />
          <span>{source.document_name}</span>
        </div>
        <Tag 
          color={getScoreColor(source.score)}
          icon={<StarFilled />}
          className="source-card-score"
        >
          {formatScore(source.score)}
        </Tag>
      </div>
      
      <div className="source-card-footer">
        <span className="footer-hint">點擊查看完整內容 →</span>
      </div>
    </div>
  );
};

export default SourceCard;
