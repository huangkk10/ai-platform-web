/**
 * HeatmapChart - 熱力圖組件
 * 
 * 用於展示矩陣型數據（如測試類別 × FW 版本的通過率/Fail 數）
 * 使用純 CSS 實現（不依賴 Recharts）
 * 
 * 資料格式：
 * {
 *   xLabels: ['FW_v1', 'FW_v2', 'FW_v3'],      // X 軸標籤（FW 版本）
 *   yLabels: ['Category1', 'Category2', ...],  // Y 軸標籤（測試類別）
 *   values: [
 *     [100, 95, 90],   // Category1 在各版本的數值
 *     [80, 85, 88],    // Category2 在各版本的數值
 *     ...
 *   ]
 * }
 * 
 * @author AI Platform Team
 * @version 1.0.0
 */

import React from 'react';
import { Empty, Tooltip } from 'antd';

/**
 * 顏色方案配置
 */
const COLOR_SCALES = {
  // 綠色系（數值越高越綠）- 適合通過率
  'green-red': {
    getColor: (value, max) => {
      // value: 0-100 (百分比) 或 0-max
      const normalizedValue = max > 0 ? value / max : 0;
      
      if (normalizedValue >= 0.95) return { bg: '#f6ffed', text: '#389e0d', border: '#b7eb8f' }; // 深綠
      if (normalizedValue >= 0.8) return { bg: '#d9f7be', text: '#389e0d', border: '#95de64' };  // 綠
      if (normalizedValue >= 0.6) return { bg: '#fffbe6', text: '#d48806', border: '#ffe58f' };  // 黃
      if (normalizedValue >= 0.4) return { bg: '#fff7e6', text: '#d46b08', border: '#ffd591' };  // 橙
      if (normalizedValue > 0) return { bg: '#fff1f0', text: '#cf1322', border: '#ffa39e' };     // 紅
      return { bg: '#f6ffed', text: '#389e0d', border: '#b7eb8f' };                              // 0 值顯示綠色
    }
  },
  
  // 紅色系（0=綠，越大越紅）- 適合 Fail 數量
  'red': {
    getColor: (value, max) => {
      if (value === 0) return { bg: '#f6ffed', text: '#389e0d', border: '#b7eb8f' }; // 0 = 綠色 (無 Fail)
      if (value === 1) return { bg: '#fff7e6', text: '#d46b08', border: '#ffd591' }; // 1 = 橙色
      if (value >= 2) return { bg: '#fff1f0', text: '#cf1322', border: '#ffa39e' };  // >=2 = 紅色
      return { bg: '#fafafa', text: '#8c8c8c', border: '#d9d9d9' };                   // 預設灰
    }
  },
  
  // 藍色系（數值越高越藍）
  'blue': {
    getColor: (value, max) => {
      const normalizedValue = max > 0 ? value / max : 0;
      
      if (normalizedValue >= 0.8) return { bg: '#e6f7ff', text: '#096dd9', border: '#91d5ff' };
      if (normalizedValue >= 0.5) return { bg: '#bae7ff', text: '#0050b3', border: '#69c0ff' };
      if (normalizedValue > 0) return { bg: '#e6f7ff', text: '#1890ff', border: '#91d5ff' };
      return { bg: '#fafafa', text: '#8c8c8c', border: '#d9d9d9' };
    }
  },
  
  // 綠色系（數值越高越綠）- 單純綠色
  'green': {
    getColor: (value, max) => {
      const normalizedValue = max > 0 ? value / max : 0;
      
      if (normalizedValue >= 0.8) return { bg: '#f6ffed', text: '#237804', border: '#b7eb8f' };
      if (normalizedValue >= 0.5) return { bg: '#d9f7be', text: '#389e0d', border: '#95de64' };
      if (normalizedValue > 0) return { bg: '#f6ffed', text: '#52c41a', border: '#b7eb8f' };
      return { bg: '#fafafa', text: '#8c8c8c', border: '#d9d9d9' };
    }
  }
};

/**
 * 格式化數值顯示
 */
const formatValue = (value, valueType) => {
  if (value === null || value === undefined) return '-';
  
  switch (valueType) {
    case 'percent':
      return `${value.toFixed(1)}%`;
    case 'status':
      return value === 0 ? '✓' : value;
    case 'number':
    default:
      return value.toLocaleString();
  }
};

/**
 * 驗證資料
 */
const validateData = (data) => {
  if (!data) return false;
  if (!data.xLabels || !Array.isArray(data.xLabels) || data.xLabels.length === 0) return false;
  if (!data.yLabels || !Array.isArray(data.yLabels) || data.yLabels.length === 0) return false;
  if (!data.values || !Array.isArray(data.values) || data.values.length === 0) return false;
  return true;
};

/**
 * 計算數據最大值（用於顏色標準化）
 */
const getMaxValue = (values, valueType) => {
  if (valueType === 'percent') return 100;
  
  let max = 0;
  values.forEach(row => {
    row.forEach(val => {
      if (val > max) max = val;
    });
  });
  return max || 1;
};

/**
 * HeatmapChart 組件
 */
const HeatmapChart = ({ data, options = {} }) => {
  const {
    colorScale = 'green-red',
    showValues = true,
    valueType = 'number',
    height = 400
  } = options;

  // 驗證資料
  if (!validateData(data)) {
    return (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <Empty description="無效的圖表資料" />
      </div>
    );
  }

  const { xLabels, yLabels, values } = data;
  const colorScaleConfig = COLOR_SCALES[colorScale] || COLOR_SCALES['green-red'];
  const maxValue = getMaxValue(values, valueType);

  // 計算格子大小
  const cellWidth = Math.max(80, Math.floor(600 / xLabels.length));
  const cellHeight = 36;
  const yLabelWidth = 180;

  return (
    <div 
      className="heatmap-chart"
      style={{
        width: '100%',
        maxHeight: height,
        overflowX: 'auto',
        overflowY: 'auto'
      }}
    >
      {/* 表格容器 */}
      <div style={{ 
        display: 'inline-block',
        minWidth: yLabelWidth + (cellWidth * xLabels.length) + 20
      }}>
        {/* X 軸標籤（表頭） */}
        <div style={{ 
          display: 'flex',
          marginLeft: yLabelWidth,
          marginBottom: 4
        }}>
          {xLabels.map((label, index) => (
            <div
              key={index}
              style={{
                width: cellWidth,
                textAlign: 'center',
                fontSize: '12px',
                fontWeight: 600,
                color: '#1890ff',
                padding: '8px 4px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
              title={label}
            >
              {label.length > 12 ? label.substring(0, 12) + '...' : label}
            </div>
          ))}
        </div>

        {/* 資料列 */}
        {yLabels.map((yLabel, rowIndex) => (
          <div
            key={rowIndex}
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 2
            }}
          >
            {/* Y 軸標籤 */}
            <div
              style={{
                width: yLabelWidth,
                paddingRight: 12,
                textAlign: 'right',
                fontSize: '13px',
                color: '#595959',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap'
              }}
              title={yLabel}
            >
              {yLabel}
            </div>

            {/* 資料格子 */}
            {xLabels.map((xLabel, colIndex) => {
              const value = values[rowIndex]?.[colIndex] ?? 0;
              const colors = colorScaleConfig.getColor(value, maxValue);
              
              return (
                <Tooltip
                  key={colIndex}
                  title={
                    <div>
                      <div style={{ fontWeight: 'bold' }}>{yLabel}</div>
                      <div>{xLabel}: {formatValue(value, valueType)}</div>
                    </div>
                  }
                >
                  <div
                    style={{
                      width: cellWidth - 4,
                      height: cellHeight,
                      margin: 2,
                      backgroundColor: colors.bg,
                      border: `1px solid ${colors.border}`,
                      borderRadius: 4,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '13px',
                      fontWeight: 500,
                      color: colors.text,
                      cursor: 'default',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    {showValues && formatValue(value, valueType)}
                  </div>
                </Tooltip>
              );
            })}
          </div>
        ))}

        {/* 圖例 */}
        <div style={{
          marginTop: 16,
          marginLeft: yLabelWidth,
          display: 'flex',
          alignItems: 'center',
          gap: 16,
          fontSize: '12px',
          color: '#8c8c8c'
        }}>
          {colorScale === 'red' ? (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#f6ffed', 
                  border: '1px solid #b7eb8f',
                  borderRadius: 3
                }}></span>
                無 Fail
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#fff7e6', 
                  border: '1px solid #ffd591',
                  borderRadius: 3
                }}></span>
                1 Fail
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#fff1f0', 
                  border: '1px solid #ffa39e',
                  borderRadius: 3
                }}></span>
                ≥2 Fail
              </span>
            </>
          ) : (
            <>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#f6ffed', 
                  border: '1px solid #b7eb8f',
                  borderRadius: 3
                }}></span>
                高 (≥95%)
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#fffbe6', 
                  border: '1px solid #ffe58f',
                  borderRadius: 3
                }}></span>
                中
              </span>
              <span style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                <span style={{ 
                  width: 16, height: 16, 
                  backgroundColor: '#fff1f0', 
                  border: '1px solid #ffa39e',
                  borderRadius: 3
                }}></span>
                低 (&lt;40%)
              </span>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(HeatmapChart);
