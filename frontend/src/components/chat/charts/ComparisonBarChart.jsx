/**
 * ComparisonBarChart - 比較柱狀圖
 * 
 * 用於顯示多版本性能對比
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
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell
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
 * ComparisonBarChart 組件
 */
const ComparisonBarChart = ({ data, options = {} }) => {
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
    barSize = 'auto',
    layout = 'horizontal',  // 'horizontal' | 'vertical'
    yAxisLabel = '',
    animate = true,
    stacked = false  // 是否堆疊
  } = options;
  
  // 計算柱狀寬度
  const calculatedBarSize = barSize === 'auto' 
    ? Math.max(20, Math.min(60, 300 / (data.labels.length * data.datasets.length)))
    : barSize;
  
  // 計算左邊距：vertical layout 時需要更多空間給 Y 軸標籤
  const leftMargin = layout === 'vertical' ? 150 : 10;
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart 
        data={chartData}
        layout={layout}
        margin={{ top: 10, right: 30, left: leftMargin, bottom: 10 }}
      >
        {/* 網格線 */}
        {showGrid && (
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke="#e8e8e8"
            vertical={layout === 'horizontal' ? false : true}
            horizontal={layout === 'horizontal' ? true : false}
          />
        )}
        
        {/* X 軸 */}
        <XAxis 
          dataKey={layout === 'horizontal' ? 'name' : undefined}
          type={layout === 'horizontal' ? 'category' : 'number'}
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#d9d9d9' }}
          tickLine={{ stroke: '#d9d9d9' }}
          tickFormatter={layout === 'vertical' ? (value) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            return value;
          } : undefined}
        />
        
        {/* Y 軸 */}
        <YAxis 
          dataKey={layout === 'vertical' ? 'name' : undefined}
          type={layout === 'vertical' ? 'category' : 'number'}
          tick={{ fontSize: 12, fill: '#666' }}
          axisLine={{ stroke: '#d9d9d9' }}
          tickLine={{ stroke: '#d9d9d9' }}
          label={yAxisLabel ? { 
            value: yAxisLabel, 
            angle: -90, 
            position: 'insideLeft',
            style: { fontSize: 12, fill: '#666' }
          } : null}
          tickFormatter={layout === 'horizontal' ? (value) => {
            if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
            if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
            return value;
          } : undefined}
        />
        
        {/* Tooltip */}
        <Tooltip content={<CustomTooltip />} />
        
        {/* 圖例 */}
        {showLegend && (
          <Legend 
            verticalAlign="top"
            height={36}
            iconType="square"
            wrapperStyle={{ fontSize: '12px' }}
          />
        )}
        
        {/* 資料柱 */}
        {data.datasets.map((dataset, index) => (
          <Bar
            key={dataset.name}
            dataKey={dataset.name}
            fill={dataset.color || CHART_COLORS.series[index % CHART_COLORS.series.length]}
            barSize={calculatedBarSize}
            radius={[4, 4, 0, 0]}  // 圓角
            stackId={stacked ? 'stack' : undefined}
            isAnimationActive={animate}
            animationDuration={600}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
};

export default React.memo(ComparisonBarChart);
