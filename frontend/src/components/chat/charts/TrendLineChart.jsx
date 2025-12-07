/**
 * TrendLineChart - 趨勢折線圖
 * 
 * 用於顯示 FW 版本趨勢分析結果
 * 基於 recharts 實現
 * 
 * 資料格式：
 * {
 *   labels: ['FW1', 'FW2', 'FW3'],
 *   datasets: [
 *     { name: 'Read IOPS', data: [100, 120, 115], color: '#1890ff' },
 *     { name: 'Write IOPS', data: [90, 95, 100], color: '#52c41a' }
 *   ]
 * }
 */

import React from 'react';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { Empty } from 'antd';
import { CHART_COLORS } from './index';

/**
 * 自訂 Tooltip 組件
 */
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="chart-custom-tooltip" style={{
        backgroundColor: 'white',
        padding: '10px 14px',
        border: '1px solid #e8e8e8',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <p style={{ 
          margin: '0 0 8px 0', 
          fontWeight: 'bold',
          color: '#333',
          borderBottom: '1px solid #e8e8e8',
          paddingBottom: '6px'
        }}>
          {label}
        </p>
        {payload.map((entry, index) => (
          <p key={index} style={{ 
            margin: '4px 0', 
            color: entry.color,
            fontSize: '13px'
          }}>
            {entry.name}: <strong>{entry.value?.toLocaleString()}</strong>
            {entry.payload?.unit && ` ${entry.payload.unit}`}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

/**
 * 轉換資料格式為 recharts 格式
 * 
 * 輸入格式：
 * {
 *   labels: ['FW1', 'FW2', 'FW3'],
 *   datasets: [
 *     { name: 'Read', data: [100, 120, 115] },
 *     { name: 'Write', data: [90, 95, 100] }
 *   ]
 * }
 * 
 * 輸出格式：
 * [
 *   { name: 'FW1', Read: 100, Write: 90 },
 *   { name: 'FW2', Read: 120, Write: 95 },
 *   { name: 'FW3', Read: 115, Write: 100 }
 * ]
 */
const transformData = (data) => {
  if (!data || !data.labels || !data.datasets) {
    return [];
  }
  
  return data.labels.map((label, index) => {
    const point = { name: label };
    data.datasets.forEach(dataset => {
      point[dataset.name] = dataset.data[index];
    });
    return point;
  });
};

/**
 * TrendLineChart 組件
 */
const TrendLineChart = ({ data, options = {} }) => {
  // 驗證資料
  if (!data || !data.labels || !data.datasets || data.labels.length === 0) {
    return <Empty description="沒有可用的圖表資料" />;
  }
  
  // 轉換資料格式
  const chartData = transformData(data);
  
  // 預設選項
  const {
    height = 300,
    showGrid = true,
    showLegend = true,
    showDots = true,
    strokeWidth = 2,
    yAxisLabel = '',
    animate = true
  } = options;
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart 
        data={chartData}
        margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
      >
        {/* 網格線 */}
        {showGrid && (
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#e8e8e8"
            vertical={false}
          />
        )}
        
        {/* X 軸 */}
        <XAxis 
          dataKey="name" 
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#d9d9d9' }}
          tickLine={{ stroke: '#d9d9d9' }}
        />
        
        {/* Y 軸 */}
        <YAxis 
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#d9d9d9' }}
          tickLine={{ stroke: '#d9d9d9' }}
          label={yAxisLabel ? { 
            value: yAxisLabel, 
            angle: -90, 
            position: 'insideLeft',
            style: { fontSize: 12, fill: '#666' }
          } : null}
          tickFormatter={(value) => {
            // 大數字格式化 (如 1000 -> 1K)
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            return value;
          }}
        />
        
        {/* Tooltip */}
        <Tooltip content={<CustomTooltip />} />
        
        {/* 圖例 */}
        {showLegend && (
          <Legend 
            verticalAlign="top"
            height={36}
            iconType="line"
            wrapperStyle={{ fontSize: '12px' }}
          />
        )}
        
        {/* 資料線 */}
        {data.datasets.map((dataset, index) => (
          <Line
            key={dataset.name}
            type="monotone"
            dataKey={dataset.name}
            stroke={dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length]}
            strokeWidth={strokeWidth}
            dot={showDots ? {
              r: 4,
              strokeWidth: 2,
              fill: 'white'
            } : false}
            activeDot={{ r: 6, strokeWidth: 0 }}
            isAnimationActive={animate}
            animationDuration={800}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default React.memo(TrendLineChart);
