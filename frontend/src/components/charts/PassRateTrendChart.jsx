/**
 * Pass Rate Trend Chart Component
 * 
 * 顯示測試通過率趨勢的折線圖
 * 
 * 功能特性：
 * - 綠色漸層區域填充
 * - 互動式 Tooltip
 * - 響應式設計
 * - 百分比顯示
 */

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import { Empty } from 'antd';

const PassRateTrendChart = ({ data = [] }) => {
  // 如果沒有數據，顯示空狀態
  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Empty description="暫無測試數據" />
      </div>
    );
  }

  // 自訂 Tooltip 內容
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      const value = payload[0].value;
      const color = value >= 80 ? '#52c41a' : value >= 60 ? '#faad14' : '#f5222d';
      
      return (
        <div
          style={{
            backgroundColor: '#fff',
            padding: '12px',
            border: '1px solid #ccc',
            borderRadius: '4px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          }}
        >
          <p style={{ margin: 0, marginBottom: '8px', fontWeight: 'bold' }}>
            {label}
          </p>
          <p style={{ margin: 0, color: color, fontSize: '16px', fontWeight: 'bold' }}>
            通過率: {typeof value === 'number' ? value.toFixed(1) : value}%
          </p>
        </div>
      );
    }
    return null;
  };

  // 計算顏色（根據通過率）
  const getColor = (value) => {
    if (value >= 80) return '#52c41a'; // 綠色
    if (value >= 60) return '#faad14'; // 黃色
    return '#f5222d'; // 紅色
  };

  // 為每個數據點添加顏色
  const dataWithColors = data.map(item => ({
    ...item,
    color: getColor(item.pass_rate),
  }));

  return (
    <ResponsiveContainer width="100%" height={300}>
      <AreaChart
        data={dataWithColors}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        <defs>
          <linearGradient id="colorPassRate" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#52c41a" stopOpacity={0.8} />
            <stop offset="95%" stopColor="#52c41a" stopOpacity={0.1} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 12 }}
          stroke="#8884d8"
        />
        <YAxis
          domain={[0, 100]}
          tick={{ fontSize: 12 }}
          stroke="#8884d8"
          label={{ value: '通過率 (%)', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Area
          type="monotone"
          dataKey="pass_rate"
          stroke="#52c41a"
          strokeWidth={2}
          fillOpacity={1}
          fill="url(#colorPassRate)"
          dot={{ r: 4, fill: '#52c41a' }}
          activeDot={{ r: 6, fill: '#389e0d' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default PassRateTrendChart;
