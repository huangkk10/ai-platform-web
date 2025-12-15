/**
 * RadarChart - 雷達圖組件
 * 
 * 用於多維度數據對比（如測試類別分佈）
 * 基於 Recharts RadarChart
 * 
 * 資料格式：
 * {
 *   labels: ['Functionality', 'MANDi', 'Performance', ...],
 *   datasets: [
 *     { name: 'FW_v1', data: [4, 8, 12, 3], color: '#1890ff' },
 *     { name: 'FW_v2', data: [5, 6, 12, 4], color: '#52c41a' }
 *   ]
 * }
 * 
 * @author AI Platform Team
 * @version 1.0.0
 */

import React from 'react';
import {
  Radar,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Legend,
  ResponsiveContainer,
  Tooltip
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
 *   labels: ['Cat1', 'Cat2', 'Cat3'],
 *   datasets: [
 *     { name: 'Series1', data: [10, 20, 30] },
 *     { name: 'Series2', data: [15, 25, 35] }
 *   ]
 * }
 * 
 * 輸出格式：
 * [
 *   { category: 'Cat1', Series1: 10, Series2: 15 },
 *   { category: 'Cat2', Series1: 20, Series2: 25 },
 *   { category: 'Cat3', Series1: 30, Series2: 35 }
 * ]
 */
const transformData = (data) => {
  if (!data?.labels || !data?.datasets) {
    return [];
  }

  return data.labels.map((label, index) => {
    const point = { category: label };
    data.datasets.forEach(ds => {
      point[ds.name] = ds.data?.[index] ?? 0;
    });
    return point;
  });
};

/**
 * 驗證資料
 */
const validateData = (data) => {
  if (!data) return false;
  if (!data.labels || !Array.isArray(data.labels) || data.labels.length === 0) return false;
  if (!data.datasets || !Array.isArray(data.datasets) || data.datasets.length === 0) return false;
  return true;
};

/**
 * 將 hex 顏色轉為 rgba（用於填充色）
 */
const hexToRgba = (hex, alpha = 0.3) => {
  // 移除 # 符號
  hex = hex.replace('#', '');
  
  // 解析 RGB 值
  const r = parseInt(hex.substring(0, 2), 16);
  const g = parseInt(hex.substring(2, 4), 16);
  const b = parseInt(hex.substring(4, 6), 16);
  
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
};

/**
 * RadarChart 組件
 */
const RadarChart = ({ data, options = {} }) => {
  const {
    showLegend = true,
    showScale = true,
    showGrid = true,
    height = 400,
    fillOpacity = 0.3,
    strokeWidth = 2,
    dotRadius = 4
  } = options;

  // 驗證資料
  if (!validateData(data)) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <Empty description="無效的圖表資料" />
      </div>
    );
  }

  // 轉換資料格式
  const chartData = transformData(data);
  const { datasets } = data;

  // 計算最大值（用於設定雷達圖的範圍）
  let maxValue = 0;
  datasets.forEach(ds => {
    const max = Math.max(...(ds.data || []));
    if (max > maxValue) maxValue = max;
  });

  // 取得顏色
  const getColor = (index, providedColor) => {
    if (providedColor) return providedColor;
    return CHART_COLORS.series[index % CHART_COLORS.series.length];
  };

  return (
    <div className="radar-chart-container" style={{ width: '100%', height: height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart
          data={chartData}
          margin={{ top: 20, right: 30, bottom: 20, left: 30 }}
        >
          {/* 極坐標網格 */}
          {showGrid && (
            <PolarGrid
              stroke="#e8e8e8"
              strokeDasharray="3 3"
            />
          )}

          {/* 角度軸（類別標籤） */}
          <PolarAngleAxis
            dataKey="category"
            tick={{
              fill: '#666',
              fontSize: 12,
              fontWeight: 500
            }}
            tickLine={false}
          />

          {/* 徑向軸（數值刻度） */}
          {showScale && (
            <PolarRadiusAxis
              angle={90}
              domain={[0, Math.ceil(maxValue * 1.1)]}
              tick={{
                fill: '#999',
                fontSize: 10
              }}
              tickCount={5}
              axisLine={false}
            />
          )}

          {/* 繪製每個資料系列 */}
          {datasets.map((ds, index) => {
            const color = getColor(index, ds.color);
            const fillColor = ds.backgroundColor || hexToRgba(color, fillOpacity);

            return (
              <Radar
                key={ds.name}
                name={ds.name}
                dataKey={ds.name}
                stroke={color}
                strokeWidth={strokeWidth}
                fill={fillColor}
                fillOpacity={1}
                dot={{
                  r: dotRadius,
                  fill: color,
                  strokeWidth: 0
                }}
                activeDot={{
                  r: dotRadius + 2,
                  fill: color,
                  stroke: '#fff',
                  strokeWidth: 2
                }}
              />
            );
          })}

          {/* Tooltip */}
          <Tooltip content={<CustomTooltip />} />

          {/* 圖例 */}
          {showLegend && (
            <Legend
              wrapperStyle={{
                paddingTop: '10px'
              }}
              iconType="circle"
              iconSize={10}
              formatter={(value) => (
                <span style={{ color: '#333', fontSize: '13px' }}>{value}</span>
              )}
            />
          )}
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
};

export default React.memo(RadarChart);
