/**
 * Score Trend Chart Component
 * 
 * 顯示測試分數趨勢的折線圖，包含：
 * - Overall Score（整體分數）
 * - Precision（精確度）
 * - Recall（召回率）
 * - F1 Score（F1 分數）
 * 
 * 功能特性：
 * - 多線顯示，可切換顯示/隱藏
 * - 互動式 Tooltip
 * - 響應式設計
 * - 時間軸格式化
 */

import React, { useState } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { Empty } from 'antd';

const ScoreTrendChart = ({ data = [] }) => {
  // 控制每條線的顯示/隱藏
  const [visibleLines, setVisibleLines] = useState({
    overall_score: true,
    precision: true,
    recall: true,
    f1_score: true,
  });

  // 如果沒有數據，顯示空狀態
  if (!data || data.length === 0) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
        <Empty description="暫無測試數據" />
      </div>
    );
  }

  // 處理圖例點擊事件（切換線條顯示）
  const handleLegendClick = (dataKey) => {
    setVisibleLines((prev) => ({
      ...prev,
      [dataKey]: !prev[dataKey],
    }));
  };

  // 自訂 Tooltip 內容
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
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
          {payload.map((entry) => (
            <p
              key={entry.dataKey}
              style={{ margin: '4px 0', color: entry.color, fontSize: '14px' }}
            >
              <span style={{ fontWeight: 'bold' }}>{entry.name}:</span>{' '}
              {typeof entry.value === 'number' ? entry.value.toFixed(2) : entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  // 自訂圖例渲染（支援點擊切換）
  const CustomLegend = ({ payload }) => {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', gap: '20px', marginTop: '10px' }}>
        {payload.map((entry) => {
          const isVisible = visibleLines[entry.dataKey];
          return (
            <div
              key={entry.dataKey}
              onClick={() => handleLegendClick(entry.dataKey)}
              style={{
                cursor: 'pointer',
                opacity: isVisible ? 1 : 0.3,
                display: 'flex',
                alignItems: 'center',
                gap: '4px',
              }}
            >
              <div
                style={{
                  width: '12px',
                  height: '12px',
                  backgroundColor: entry.color,
                  borderRadius: '2px',
                }}
              />
              <span style={{ fontSize: '14px' }}>{entry.value}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
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
          label={{ value: '分數', angle: -90, position: 'insideLeft' }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend content={<CustomLegend />} />

        {/* Overall Score 線 */}
        {visibleLines.overall_score && (
          <Line
            type="monotone"
            dataKey="overall_score"
            name="Overall Score"
            stroke="#1890ff"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}

        {/* Precision 線 */}
        {visibleLines.precision && (
          <Line
            type="monotone"
            dataKey="precision"
            name="Precision"
            stroke="#52c41a"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}

        {/* Recall 線 */}
        {visibleLines.recall && (
          <Line
            type="monotone"
            dataKey="recall"
            name="Recall"
            stroke="#faad14"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}

        {/* F1 Score 線 */}
        {visibleLines.f1_score && (
          <Line
            type="monotone"
            dataKey="f1_score"
            name="F1 Score"
            stroke="#722ed1"
            strokeWidth={2}
            dot={{ r: 4 }}
            activeDot={{ r: 6 }}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
};

export default ScoreTrendChart;
