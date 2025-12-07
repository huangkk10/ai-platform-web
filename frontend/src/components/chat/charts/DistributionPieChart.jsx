/**
 * DistributionPieChart - 分佈圓餅圖
 * 
 * 用於顯示各項目的佔比分佈
 * 基於 recharts 實現
 * 
 * 資料格式：
 * {
 *   items: [
 *     { name: 'Read', value: 100, color: '#1890ff' },
 *     { name: 'Write', value: 90, color: '#52c41a' }
 *   ]
 * }
 */

import React, { useState, useCallback } from 'react';
import { 
  PieChart, 
  Pie, 
  Cell, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Sector
} from 'recharts';
import { Empty } from 'antd';
import { CHART_COLORS } from './index';

/**
 * 自訂 Tooltip 組件
 */
const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const percentage = ((data.value / data.payload.total) * 100).toFixed(1);
    
    return (
      <div className="chart-custom-tooltip" style={{
        backgroundColor: 'white',
        padding: '10px 14px',
        border: '1px solid #e8e8e8',
        borderRadius: '6px',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <p style={{ 
          margin: '0 0 4px 0', 
          fontWeight: 'bold',
          color: data.payload.fill
        }}>
          {data.name}
        </p>
        <p style={{ margin: '4px 0', fontSize: '13px', color: '#333' }}>
          數值: <strong>{data.value?.toLocaleString()}</strong>
        </p>
        <p style={{ margin: '4px 0', fontSize: '13px', color: '#666' }}>
          佔比: <strong>{percentage}%</strong>
        </p>
      </div>
    );
  }
  return null;
};

/**
 * 活動扇區渲染（hover 效果）
 */
const renderActiveShape = (props) => {
  const {
    cx, cy, innerRadius, outerRadius, startAngle, endAngle,
    fill, payload, value, percent
  } = props;
  
  return (
    <g>
      <Sector
        cx={cx}
        cy={cy}
        innerRadius={innerRadius}
        outerRadius={outerRadius + 6}
        startAngle={startAngle}
        endAngle={endAngle}
        fill={fill}
        style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.2))' }}
      />
      <text 
        x={cx} 
        y={cy - 10} 
        textAnchor="middle" 
        fill="#333"
        style={{ fontWeight: 'bold', fontSize: 14 }}
      >
        {payload.name}
      </text>
      <text 
        x={cx} 
        y={cy + 10} 
        textAnchor="middle" 
        fill="#666"
        style={{ fontSize: 12 }}
      >
        {value?.toLocaleString()}
      </text>
      <text 
        x={cx} 
        y={cy + 28} 
        textAnchor="middle" 
        fill="#999"
        style={{ fontSize: 11 }}
      >
        {`(${(percent * 100).toFixed(1)}%)`}
      </text>
    </g>
  );
};

/**
 * 準備資料（添加總計和顏色）
 */
const prepareData = (data) => {
  if (!data || !data.items || data.items.length === 0) {
    return [];
  }
  
  const total = data.items.reduce((sum, item) => sum + (item.value || 0), 0);
  
  return data.items.map((item, index) => ({
    ...item,
    total,
    fill: item.color || CHART_COLORS.series[index % CHART_COLORS.series.length]
  }));
};

/**
 * DistributionPieChart 組件
 */
const DistributionPieChart = ({ data, options = {} }) => {
  const [activeIndex, setActiveIndex] = useState(null);
  
  // Hover 處理 (必須在條件判斷之前定義)
  const onPieEnter = useCallback((_, index) => {
    setActiveIndex(index);
  }, []);
  
  const onPieLeave = useCallback(() => {
    setActiveIndex(null);
  }, []);
  
  // 驗證資料 (早期返回必須在 hooks 之後)
  if (!data || !data.items || data.items.length === 0) {
    return <Empty description="沒有可用的圖表資料" />;
  }
  
  // 準備資料
  const chartData = prepareData(data);
  
  // 預設選項
  const {
    height = 300,
    showLegend = true,
    showLabels = true,
    innerRadius = 0,  // 0 = 圓餅圖, > 0 = 甜甜圈圖
    outerRadius = 'auto',
    animate = true
  } = options;
  
  // 計算半徑
  const calculatedOuterRadius = outerRadius === 'auto' 
    ? Math.min(height / 2 - 40, 100)
    : outerRadius;
  
  // 標籤渲染
  const renderLabel = ({ name, percent }) => {
    if (!showLabels || percent < 0.05) return null;
    return `${name} ${(percent * 100).toFixed(0)}%`;
  };
  
  return (
    <ResponsiveContainer width="100%" height={height}>
      <PieChart>
        <Pie
          data={chartData}
          cx="50%"
          cy="50%"
          innerRadius={innerRadius}
          outerRadius={calculatedOuterRadius}
          dataKey="value"
          nameKey="name"
          activeIndex={activeIndex}
          activeShape={renderActiveShape}
          onMouseEnter={onPieEnter}
          onMouseLeave={onPieLeave}
          label={showLabels && activeIndex === null ? renderLabel : false}
          labelLine={showLabels && activeIndex === null}
          isAnimationActive={animate}
          animationDuration={600}
        >
          {chartData.map((entry, index) => (
            <Cell 
              key={`cell-${index}`} 
              fill={entry.fill}
              style={{ cursor: 'pointer' }}
            />
          ))}
        </Pie>
        
        {/* Tooltip */}
        <Tooltip content={<CustomTooltip />} />
        
        {/* 圖例 */}
        {showLegend && (
          <Legend 
            verticalAlign="bottom"
            height={36}
            iconType="circle"
            wrapperStyle={{ fontSize: '12px' }}
            formatter={(value, entry) => (
              <span style={{ color: '#333' }}>{value}</span>
            )}
          />
        )}
      </PieChart>
    </ResponsiveContainer>
  );
};

export default React.memo(DistributionPieChart);
