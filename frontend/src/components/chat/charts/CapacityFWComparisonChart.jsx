/**
 * CapacityFWComparisonChart - 容量×FW版本 分組柱狀圖
 * 
 * 用於顯示不同容量下各 FW 版本的通過率比較
 * X 軸為容量，每組顯示各 FW 版本的通過率柱狀圖
 * 
 * 資料格式：
 * {
 *   capacities: ['512GB', '1024GB', '2048GB', '4096GB'],
 *   fwVersions: ['G210X74A', 'G210Y1NA', 'G210Y33A', 'G210Y37B'],
 *   matrix: [
 *     {
 *       capacity: '512GB',
 *       stats: {
 *         'G210X74A': { pass: 15, fail: 2, total: 17, passRate: 88.2 },
 *         'G210Y1NA': { pass: 18, fail: 0, total: 18, passRate: 100 },
 *         ...
 *       }
 *     },
 *     ...
 *   ]
 * }
 * 
 * @author AI Platform Team
 * @date 2025-12-18
 */

import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
  ReferenceLine
} from 'recharts';
import { Empty, Typography } from 'antd';

const { Text } = Typography;

/**
 * FW 版本對應的顏色
 * 使用明確區分的顏色方案
 */
const FW_COLORS = [
  '#1890ff',  // 藍色
  '#52c41a',  // 綠色
  '#faad14',  // 橙色
  '#722ed1',  // 紫色
  '#eb2f96',  // 粉紅色
  '#13c2c2',  // 青色
  '#fa541c',  // 紅橙色
  '#2f54eb',  // 靛藍色
];

/**
 * 自訂 Tooltip 組件
 */
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div style={{
        backgroundColor: 'white',
        padding: '12px 16px',
        border: '1px solid #e8e8e8',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        minWidth: '180px'
      }}>
        <p style={{
          margin: '0 0 10px 0',
          fontWeight: 'bold',
          color: '#333',
          borderBottom: '1px solid #e8e8e8',
          paddingBottom: '8px',
          fontSize: '14px'
        }}>
          📦 {label}
        </p>
        {payload.map((entry, index) => {
          const stats = entry.payload[`${entry.dataKey}_stats`];
          return (
            <div key={index} style={{
              margin: '8px 0',
              padding: '6px 0',
              borderBottom: index < payload.length - 1 ? '1px dashed #f0f0f0' : 'none'
            }}>
              <p style={{
                margin: '0 0 4px 0',
                color: entry.color,
                fontWeight: 'bold',
                fontSize: '13px'
              }}>
                {entry.name}
              </p>
              <p style={{ margin: '2px 0', fontSize: '12px', color: '#666' }}>
                通過率: <strong style={{ color: entry.color }}>{entry.value?.toFixed(1)}%</strong>
              </p>
              {stats && (
                <>
                  <p style={{ margin: '2px 0', fontSize: '12px', color: '#52c41a' }}>
                    ✅ Pass: {stats.pass}
                  </p>
                  <p style={{ margin: '2px 0', fontSize: '12px', color: '#ff4d4f' }}>
                    ❌ Fail: {stats.fail}
                  </p>
                  <p style={{ margin: '2px 0', fontSize: '12px', color: '#999' }}>
                    總計: {stats.total}
                  </p>
                </>
              )}
            </div>
          );
        })}
      </div>
    );
  }
  return null;
};

/**
 * 自訂 Legend 組件
 */
const CustomLegend = ({ payload }) => {
  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      flexWrap: 'wrap',
      gap: '16px',
      marginTop: '12px',
      padding: '8px 0'
    }}>
      {payload.map((entry, index) => (
        <div key={index} style={{
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <div style={{
            width: '14px',
            height: '14px',
            backgroundColor: entry.color,
            borderRadius: '3px'
          }} />
          <span style={{ fontSize: '12px', color: '#666' }}>
            {entry.value}
          </span>
        </div>
      ))}
    </div>
  );
};

/**
 * 轉換資料格式為 recharts 格式
 */
const transformData = (data) => {
  if (!data || !data.matrix || !data.fwVersions) {
    return [];
  }

  return data.matrix.map(item => {
    const point = { capacity: item.capacity };

    data.fwVersions.forEach(fw => {
      const stats = item.stats?.[fw];
      if (stats) {
        // 通過率作為主要數值
        point[fw] = stats.passRate || 0;
        // 保存詳細統計供 tooltip 使用
        point[`${fw}_stats`] = stats;
      } else {
        point[fw] = null; // 沒有資料時設為 null
      }
    });

    return point;
  });
};

/**
 * CapacityFWComparisonChart 組件
 */
const CapacityFWComparisonChart = ({ data, options = {} }) => {
  // 轉換資料格式 - 必須在所有條件判斷之前呼叫 Hook
  const chartData = useMemo(() => transformData(data), [data]);

  // 預設選項
  const {
    height = 350,
    showGrid = true,
    showLegend = true,
    barSize = 'auto',
    yAxisDomain = [0, 100],
  } = options;

  // 驗證資料 - 在 Hook 之後進行條件判斷
  if (!data || !data.matrix || data.matrix.length === 0 || !data.fwVersions || data.fwVersions.length === 0) {
    return <Empty description="沒有可用的圖表資料" />;
  }

  // 計算柱狀圖寬度
  const capacityCount = data.matrix.length;
  const fwCount = data.fwVersions.length;
  
  // 動態計算柱寬：容量越多、FW 越多，柱子越細
  let calculatedBarSize;
  if (barSize === 'auto') {
    if (capacityCount <= 3 && fwCount <= 3) {
      calculatedBarSize = 35;
    } else if (capacityCount <= 5 && fwCount <= 4) {
      calculatedBarSize = 25;
    } else {
      calculatedBarSize = 18;
    }
  } else {
    calculatedBarSize = barSize;
  }

  return (
    <div className="capacity-fw-comparison-chart">
      {/* 圖表標題 */}
      <div style={{ 
        textAlign: 'center', 
        marginBottom: '12px',
        padding: '8px 0'
      }}>
        <Text strong style={{ fontSize: '14px', color: '#333' }}>
          📊 各容量 FW 版本通過率比較
        </Text>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          滑鼠懸停可查看詳細 Pass/Fail 數量
        </Text>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
          barCategoryGap="20%"
        >
          {showGrid && (
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke="#f0f0f0"
              vertical={false}
            />
          )}

          <XAxis
            dataKey="capacity"
            tick={{ fontSize: 12, fill: '#666' }}
            tickLine={{ stroke: '#d9d9d9' }}
            axisLine={{ stroke: '#d9d9d9' }}
          />

          <YAxis
            domain={yAxisDomain}
            tick={{ fontSize: 12, fill: '#666' }}
            tickLine={{ stroke: '#d9d9d9' }}
            axisLine={{ stroke: '#d9d9d9' }}
            tickFormatter={(value) => `${value}%`}
            label={{
              value: '通過率 (%)',
              angle: -90,
              position: 'insideLeft',
              style: { textAnchor: 'middle', fontSize: 12, fill: '#999' }
            }}
          />

          <Tooltip content={<CustomTooltip />} />

          {showLegend && (
            <Legend content={<CustomLegend />} />
          )}

          {/* 90% 參考線 - 優良基準 */}
          <ReferenceLine
            y={90}
            stroke="#52c41a"
            strokeDasharray="5 5"
            strokeWidth={1}
            label={{
              value: '90%',
              position: 'right',
              fill: '#52c41a',
              fontSize: 10
            }}
          />

          {/* 為每個 FW 版本創建柱狀圖 */}
          {data.fwVersions.map((fw, index) => (
            <Bar
              key={fw}
              dataKey={fw}
              name={fw}
              fill={FW_COLORS[index % FW_COLORS.length]}
              barSize={calculatedBarSize}
              radius={[4, 4, 0, 0]}
            >
              {/* 根據通過率設置顏色深淺 */}
              {chartData.map((entry, cellIndex) => {
                const value = entry[fw];
                let opacity = 1;
                if (value === null) {
                  opacity = 0.2; // 無資料
                } else if (value < 70) {
                  opacity = 0.6; // 低通過率稍暗
                } else if (value < 90) {
                  opacity = 0.8;
                }
                return (
                  <Cell
                    key={`cell-${cellIndex}`}
                    fillOpacity={opacity}
                  />
                );
              })}
            </Bar>
          ))}
        </BarChart>
      </ResponsiveContainer>

      {/* 圖例說明 */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '20px',
        marginTop: '8px',
        fontSize: '11px',
        color: '#999'
      }}>
        <span>🟢 ≥90%: 優良</span>
        <span>🟡 70-89%: 一般</span>
        <span>🔴 &lt;70%: 需關注</span>
      </div>
    </div>
  );
};

export default React.memo(CapacityFWComparisonChart);
