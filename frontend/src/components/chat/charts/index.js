/**
 * 圖表組件模組導出
 * 
 * 用於 AI Assistant 回應中渲染各類圖表
 * 支援：折線圖 (LineChart)、柱狀圖 (BarChart)、圓餅圖 (PieChart)
 * 
 * @author AI Platform Team
 * @version 1.0.0
 */

export { default as ChartRenderer } from './ChartRenderer';
export { default as TrendLineChart } from './TrendLineChart';
export { default as ComparisonBarChart } from './ComparisonBarChart';
export { default as DistributionPieChart } from './DistributionPieChart';

// 圖表類型常量
export const CHART_TYPES = {
  LINE: 'line',
  BAR: 'bar',
  PIE: 'pie',
};

// 預設配色方案
export const CHART_COLORS = {
  primary: '#1890ff',    // Ant Design 主色
  success: '#52c41a',    // 綠色 - 成功
  warning: '#faad14',    // 橙色 - 警告
  error: '#ff4d4f',      // 紅色 - 錯誤
  purple: '#722ed1',     // 紫色
  cyan: '#13c2c2',       // 青色
  magenta: '#eb2f96',    // 洋紅
  lime: '#a0d911',       // 青檸
  gold: '#faad14',       // 金色
  blue: '#1890ff',       // 藍色
  // 漸變系列
  series: [
    '#1890ff', '#52c41a', '#faad14', '#ff4d4f', '#722ed1',
    '#13c2c2', '#eb2f96', '#a0d911', '#2f54eb', '#fa8c16'
  ]
};
