/**
 * VersionComparisonChart - FW 版本比較組合圖表
 * 
 * 專為 SAF Assistant 的 FW 版本測試結果比較設計
 * 組合圖表：堆疊柱狀圖 (Pass/Fail) + 折線圖 (通過率)
 * 
 * 基於 recharts 實現，支援雙 Y 軸
 * 
 * 資料格式：
 * {
 *   labels: ['G210X74A', 'G210Y1NA', 'G210Y33A', 'G210Y37B'],
 *   pass: [17, 59, 68, 50],
 *   fail: [14, 5, 4, 15],
 *   passRate: [44.7, 89.4, 93.2, 67.6]  // 百分比數值
 * }
 * 
 * @author AI Platform Team
 * @version 1.0.0
 */

import React from 'react';
import { 
  ComposedChart, 
  Bar, 
  Line,
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  LabelList
} from 'recharts';
import { Empty, Typography } from 'antd';

const { Text } = Typography;

// 預設顏色配置
const COLORS = {
  pass: '#52c41a',      // 綠色 - Pass
  fail: '#ff4d4f',      // 紅色 - Fail
  passRate: '#1890ff',  // 藍色 - 通過率折線
  grid: '#e8e8e8',      // 網格線
  axis: '#d9d9d9'       // 座標軸
};

/**
 * 自訂 Tooltip 組件
 */
const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    // 從 payload 中提取資料
    const passData = payload.find(p => p.dataKey === 'pass');
    const failData = payload.find(p => p.dataKey === 'fail');
    const passRateData = payload.find(p => p.dataKey === 'passRate');
    
    const total = (passData?.value || 0) + (failData?.value || 0);
    
    return (
      <div style={{
        backgroundColor: 'white',
        padding: '12px 16px',
        border: '1px solid #e8e8e8',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        minWidth: '160px'
      }}>
        {/* 版本名稱 */}
        <div style={{ 
          margin: '0 0 10px 0', 
          fontWeight: 'bold',
          color: '#333',
          fontSize: '14px',
          borderBottom: '1px solid #e8e8e8',
          paddingBottom: '8px'
        }}>
          🔖 版本: {label}
        </div>
        
        {/* 總測試項目 */}
        <div style={{ 
          marginBottom: '8px',
          padding: '6px 8px',
          backgroundColor: '#f5f5f5',
          borderRadius: '4px',
          fontSize: '13px'
        }}>
          📊 總測試項目: <strong>{total}</strong>
        </div>
        
        {/* Pass/Fail 詳情 */}
        {passData && (
          <div style={{ 
            margin: '4px 0', 
            color: COLORS.pass,
            fontSize: '13px',
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>✅ Pass:</span>
            <strong>{passData.value}</strong>
          </div>
        )}
        
        {failData && (
          <div style={{ 
            margin: '4px 0', 
            color: COLORS.fail,
            fontSize: '13px',
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>❌ Fail:</span>
            <strong>{failData.value}</strong>
          </div>
        )}
        
        {/* 通過率 */}
        {passRateData && (
          <div style={{ 
            margin: '8px 0 0 0', 
            padding: '6px 8px',
            backgroundColor: 'rgba(24, 144, 255, 0.1)',
            borderRadius: '4px',
            color: COLORS.passRate,
            fontSize: '13px',
            fontWeight: 'bold',
            display: 'flex',
            justifyContent: 'space-between'
          }}>
            <span>📈 通過率:</span>
            <span>{passRateData.value.toFixed(1)}%</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

/**
 * 自訂折線圖標籤（顯示在數據點上）
 */
const CustomLineLabel = ({ x, y, value }) => {
  return (
    <text 
      x={x} 
      y={y - 10} 
      fill={COLORS.passRate} 
      textAnchor="middle"
      fontSize={11}
      fontWeight="bold"
    >
      {value.toFixed(1)}%
    </text>
  );
};

/**
 * 轉換資料格式為 recharts 格式
 */
const transformData = (data) => {
  if (!data || !data.labels) {
    return [];
  }
  
  return data.labels.map((label, index) => ({
    name: label,
    pass: data.pass?.[index] || 0,
    fail: data.fail?.[index] || 0,
    passRate: data.passRate?.[index] || 0
  }));
};

/**
 * 計算 Y 軸最大值（確保柱狀圖有足夠空間）
 */
const calculateMaxValue = (data) => {
  if (!data || data.length === 0) return 100;
  
  const maxTotal = Math.max(...data.map(d => d.pass + d.fail));
  // 增加 20% 空間給標籤
  return Math.ceil(maxTotal * 1.2);
};

/**
 * VersionComparisonChart 組件
 */
const VersionComparisonChart = ({ data, options = {} }) => {
  // 驗證資料
  if (!data || !data.labels || data.labels.length === 0) {
    return <Empty description="沒有可用的圖表資料" />;
  }
  
  // 轉換資料格式
  const chartData = transformData(data);
  
  // 預設選項
  const {
    height = 350,
    showGrid = true,
    showLegend = true,
    animate = true,
    showLineLabels = true,  // 是否顯示折線數據標籤
    barRadius = 4           // 柱狀圖圓角
  } = options;
  
  const maxLeftYAxis = calculateMaxValue(chartData);
  
  return (
    <div className="version-comparison-chart">
      {/* 圖表說明 */}
      <div style={{ 
        marginBottom: '12px', 
        display: 'flex', 
        alignItems: 'center',
        gap: '16px',
        flexWrap: 'wrap'
      }}>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          📊 柱狀圖顯示 Pass/Fail 數量，折線顯示通過率趨勢
        </Text>
      </div>
      
      <ResponsiveContainer width="100%" height={height}>
        <ComposedChart 
          data={chartData}
          margin={{ top: 20, right: 60, left: 20, bottom: 20 }}
        >
          {/* 網格線 */}
          {showGrid && (
            <CartesianGrid 
              strokeDasharray="3 3" 
              stroke={COLORS.grid}
              vertical={false}
            />
          )}
          
          {/* X 軸 - 版本名稱 */}
          <XAxis 
            dataKey="name" 
            tick={{ fontSize: 11, fill: '#666' }}
            axisLine={{ stroke: COLORS.axis }}
            tickLine={{ stroke: COLORS.axis }}
            interval={0}  // 顯示所有標籤
            angle={data.labels.length > 5 ? -30 : 0}  // 標籤過多時傾斜
            textAnchor={data.labels.length > 5 ? 'end' : 'middle'}
            height={data.labels.length > 5 ? 60 : 30}
          />
          
          {/* 左 Y 軸 - 測試數量 */}
          <YAxis 
            yAxisId="left"
            orientation="left"
            tick={{ fontSize: 11, fill: '#666' }}
            axisLine={{ stroke: COLORS.axis }}
            tickLine={{ stroke: COLORS.axis }}
            domain={[0, maxLeftYAxis]}
            label={{ 
              value: '測試數量', 
              angle: -90, 
              position: 'insideLeft',
              style: { fontSize: 11, fill: '#666', textAnchor: 'middle' },
              offset: 10
            }}
          />
          
          {/* 右 Y 軸 - 通過率 (%) */}
          <YAxis 
            yAxisId="right"
            orientation="right"
            tick={{ fontSize: 11, fill: COLORS.passRate }}
            axisLine={{ stroke: COLORS.passRate }}
            tickLine={{ stroke: COLORS.passRate }}
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
            label={{ 
              value: '通過率 (%)', 
              angle: 90, 
              position: 'insideRight',
              style: { fontSize: 11, fill: COLORS.passRate, textAnchor: 'middle' },
              offset: 10
            }}
          />
          
          {/* Tooltip */}
          <Tooltip content={<CustomTooltip />} />
          
          {/* 圖例 */}
          {showLegend && (
            <Legend 
              verticalAlign="top"
              height={40}
              iconType="square"
              wrapperStyle={{ fontSize: '12px', paddingBottom: '10px' }}
              formatter={(value) => {
                const labelMap = {
                  pass: '✅ Pass',
                  fail: '❌ Fail',
                  passRate: '📈 通過率'
                };
                return labelMap[value] || value;
              }}
            />
          )}
          
          {/* 堆疊柱狀圖 - Pass */}
          <Bar
            yAxisId="left"
            dataKey="pass"
            name="pass"
            stackId="stack"
            fill={COLORS.pass}
            radius={[0, 0, 0, 0]}  // 底部不圓角（因為是堆疊）
            isAnimationActive={animate}
            animationDuration={600}
          />
          
          {/* 堆疊柱狀圖 - Fail */}
          <Bar
            yAxisId="left"
            dataKey="fail"
            name="fail"
            stackId="stack"
            fill={COLORS.fail}
            radius={[barRadius, barRadius, 0, 0]}  // 頂部圓角
            isAnimationActive={animate}
            animationDuration={600}
          />
          
          {/* 折線圖 - 通過率 */}
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="passRate"
            name="passRate"
            stroke={COLORS.passRate}
            strokeWidth={3}
            dot={{ 
              r: 6, 
              fill: 'white', 
              stroke: COLORS.passRate, 
              strokeWidth: 2 
            }}
            activeDot={{ 
              r: 8, 
              fill: COLORS.passRate,
              stroke: 'white',
              strokeWidth: 2
            }}
            isAnimationActive={animate}
            animationDuration={800}
          >
            {/* 數據標籤 */}
            {showLineLabels && (
              <LabelList 
                dataKey="passRate" 
                content={<CustomLineLabel />}
              />
            )}
          </Line>
        </ComposedChart>
      </ResponsiveContainer>
      
      {/* 底部說明 */}
      <div style={{ 
        marginTop: '8px', 
        textAlign: 'center',
        display: 'flex',
        justifyContent: 'center',
        gap: '24px',
        flexWrap: 'wrap'
      }}>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          <span style={{ 
            display: 'inline-block', 
            width: '12px', 
            height: '12px', 
            backgroundColor: COLORS.pass, 
            marginRight: '4px',
            borderRadius: '2px',
            verticalAlign: 'middle'
          }}></span>
          Pass 測試通過
        </Text>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          <span style={{ 
            display: 'inline-block', 
            width: '12px', 
            height: '12px', 
            backgroundColor: COLORS.fail, 
            marginRight: '4px',
            borderRadius: '2px',
            verticalAlign: 'middle'
          }}></span>
          Fail 測試失敗
        </Text>
        <Text type="secondary" style={{ fontSize: '11px' }}>
          <span style={{ 
            display: 'inline-block', 
            width: '24px', 
            height: '3px', 
            backgroundColor: COLORS.passRate, 
            marginRight: '4px',
            verticalAlign: 'middle'
          }}></span>
          通過率趨勢
        </Text>
      </div>
    </div>
  );
};

export default VersionComparisonChart;
