import React, { useState, useEffect } from 'react';
import { Spin, Typography } from 'antd';

const { Text } = Typography;

/**
 * LoadingIndicator 組件
 * 顯示動態載入提示訊息，根據經過的時間顯示不同的訊息
 * 
 * @param {boolean} loading - 是否正在載入
 * @param {number} loadingStartTime - 載入開始時間戳
 * @param {string} serviceName - 服務名稱（預設 'RVT Assistant'）
 */
const LoadingIndicator = ({ 
  loading = false, 
  loadingStartTime = null,
  serviceName = 'RVT Assistant'
}) => {
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  useEffect(() => {
    if (!loading || !loadingStartTime) return;

    const interval = setInterval(() => {
      const elapsed = Math.floor((Date.now() - loadingStartTime) / 1000);
      setElapsedSeconds(elapsed);
    }, 1000);

    return () => clearInterval(interval);
  }, [loading, loadingStartTime]);

  const getMessage = () => {
    if (elapsedSeconds < 5) return `${serviceName} 正在分析您的問題...`;
    if (elapsedSeconds < 15) return `${serviceName} 正在查找相關資料... (${elapsedSeconds}s)`;
    if (elapsedSeconds < 30) return `${serviceName} 正在深度分析... (${elapsedSeconds}s)`;
    return `${serviceName} 仍在處理，請耐心等待... (${elapsedSeconds}s)`;
  };

  return (
    <div style={{ display: 'flex', alignItems: 'center' }}>
      <Spin size="small" />
      <Text style={{ marginLeft: '8px', color: '#666' }}>
        {getMessage()}
      </Text>
    </div>
  );
};

export default LoadingIndicator;
