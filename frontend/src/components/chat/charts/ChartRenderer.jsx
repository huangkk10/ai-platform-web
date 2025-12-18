/**
 * ChartRenderer - 圖表渲染器
 * 
 * 根據圖表配置動態選擇和渲染適當的圖表組件
 * 支援 line、bar、pie、radar、heatmap、version-comparison 六種類型
 * 
 * 用法：
 * <ChartRenderer config={{ type: 'line', data: {...}, options: {...} }} />
 */

import React from 'react';
import { Card, Typography, Empty, Alert } from 'antd';
import { 
  LineChartOutlined, 
  BarChartOutlined, 
  PieChartOutlined,
  RadarChartOutlined,
  HeatMapOutlined,
  InfoCircleOutlined,
  FundOutlined  // 🆕 組合圖表圖標
} from '@ant-design/icons';
import TrendLineChart from './TrendLineChart';
import ComparisonBarChart from './ComparisonBarChart';
import DistributionPieChart from './DistributionPieChart';
import RadarChart from './RadarChart';
import HeatmapChart from './HeatmapChart';
import VersionComparisonChart from './VersionComparisonChart';  // 🆕 版本比較組合圖
import './ChartStyles.css';

const { Text, Title } = Typography;

/**
 * 獲取圖表類型對應的圖標
 */
const getChartIcon = (type) => {
  switch (type) {
    case 'line':
      return <LineChartOutlined style={{ color: '#1890ff', marginRight: 8 }} />;
    case 'bar':
      return <BarChartOutlined style={{ color: '#52c41a', marginRight: 8 }} />;
    case 'pie':
      return <PieChartOutlined style={{ color: '#722ed1', marginRight: 8 }} />;
    case 'radar':
      return <RadarChartOutlined style={{ color: '#13c2c2', marginRight: 8 }} />;
    case 'heatmap':
      return <HeatMapOutlined style={{ color: '#eb2f96', marginRight: 8 }} />;
    case 'version-comparison':  // 🆕 版本比較組合圖
      return <FundOutlined style={{ color: '#1890ff', marginRight: 8 }} />;
    default:
      return <InfoCircleOutlined style={{ color: '#faad14', marginRight: 8 }} />;
  }
};

/**
 * 驗證圖表配置
 */
const validateConfig = (config) => {
  if (!config) {
    return { valid: false, error: '圖表配置為空' };
  }
  
  if (!config.type) {
    return { valid: false, error: '缺少圖表類型 (type)' };
  }
  
  if (!config.data) {
    return { valid: false, error: '缺少圖表資料 (data)' };
  }
  
  const validTypes = ['line', 'bar', 'pie', 'radar', 'heatmap', 'version-comparison'];  // 🆕 新增 version-comparison
  if (!validTypes.includes(config.type)) {
    return { valid: false, error: `不支援的圖表類型: ${config.type}` };
  }
  
  return { valid: true };
};

/**
 * 渲染對應類型的圖表
 */
const renderChart = (config) => {
  const { type, data, options = {} } = config;
  
  switch (type) {
    case 'line':
      return <TrendLineChart data={data} options={options} />;
    case 'bar':
      return <ComparisonBarChart data={data} options={options} />;
    case 'pie':
      return <DistributionPieChart data={data} options={options} />;
    case 'radar':
      return <RadarChart data={data} options={options} />;
    case 'heatmap':
      return <HeatmapChart data={data} options={options} />;
    case 'version-comparison':  // 🆕 版本比較組合圖
      return <VersionComparisonChart data={data} options={options} />;
    default:
      return <Empty description="不支援的圖表類型" />;
  }
};

/**
 * ChartRenderer 組件
 */
const ChartRenderer = ({ config, showCard = true, className = '' }) => {
  // 驗證配置
  const validation = validateConfig(config);
  
  if (!validation.valid) {
    return (
      <Alert
        message="圖表渲染錯誤"
        description={validation.error}
        type="warning"
        showIcon
        style={{ margin: '12px 0' }}
      />
    );
  }
  
  const { type, title, description } = config;
  
  // 渲染圖表內容
  const chartContent = (
    <div className={`chart-renderer ${className}`}>
      {/* 圖表標題（可選） */}
      {title && (
        <div className="chart-header">
          {getChartIcon(type)}
          <Text strong className="chart-title">{title}</Text>
        </div>
      )}
      
      {/* 圖表描述（可選） */}
      {description && (
        <Text type="secondary" className="chart-description">
          {description}
        </Text>
      )}
      
      {/* 圖表主體 */}
      <div className="chart-body">
        {renderChart(config)}
      </div>
    </div>
  );
  
  // 是否包裹在 Card 中
  if (showCard) {
    return (
      <Card 
        className="chart-card"
        size="small"
        style={{ margin: '12px 0' }}
        bordered
      >
        {chartContent}
      </Card>
    );
  }
  
  return chartContent;
};

export default React.memo(ChartRenderer);
