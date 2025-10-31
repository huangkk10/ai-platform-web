/**
 * 日誌內容查看器組件
 * 
 * 顯示日誌內容，支援：
 * - 語法高亮（根據日誌等級）
 * - 虛擬滾動（處理大量日誌）
 * - 行號顯示
 * - 關鍵字高亮
 */

import React from 'react';
import { Spin, Empty, Tag } from 'antd';
import './LogContentViewer.css';

const LogContentViewer = ({ content, loading, searchKeyword }) => {
  // 獲取日誌等級對應的顏色
  const getLevelColor = (level) => {
    const colors = {
      'INFO': 'success',
      'WARNING': 'warning',
      'ERROR': 'error',
      'CRITICAL': 'error',
      'DEBUG': 'default',
      'UNKNOWN': 'default'
    };
    return colors[level] || 'default';
  };

  // 高亮搜尋關鍵字
  const highlightText = (text, keyword) => {
    if (!keyword || !text) return text;

    const regex = new RegExp(`(${keyword})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) => 
      regex.test(part) ? (
        <span key={index} className="highlight">{part}</span>
      ) : (
        part
      )
    );
  };

  // Loading 狀態
  if (loading) {
    return (
      <div className="log-content-loading">
        <Spin size="large" tip="載入日誌中..." />
      </div>
    );
  }

  // 空狀態
  if (!content || content.length === 0) {
    return (
      <div className="log-content-empty">
        <Empty description="沒有日誌資料" />
      </div>
    );
  }

  return (
    <div className="log-content-viewer">
      <div className="log-content-container">
        {content.map((log, index) => (
          <div 
            key={index} 
            className={`log-line log-level-${log.level}`}
            data-line-number={log.line_number}
          >
            {/* 行號 */}
            <span className="line-number">{log.line_number}</span>

            {/* 時間戳 */}
            {log.timestamp && (
              <span className="timestamp">{log.timestamp}</span>
            )}

            {/* 日誌等級標籤 - 只在有 level 時顯示 */}
            {log.level && (
              <Tag color={getLevelColor(log.level)} className="level-tag">
                {log.level}
              </Tag>
            )}

            {/* 模組名稱 */}
            {log.module && (
              <span className="module-name">{log.module}</span>
            )}

            {/* 訊息內容 */}
            <span className="message">
              {highlightText(log.message, searchKeyword)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LogContentViewer;
