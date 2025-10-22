import React, { useState, useEffect } from 'react';
import { Card, Typography, Row, Col, Statistic, DatePicker, Spin, Alert, Button } from 'antd';
import { MessageOutlined, FileTextOutlined, ReloadOutlined, BarChartOutlined } from '@ant-design/icons';
import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { getChatStatistics } from '../utils/chatUsage';

const { Title, Paragraph } = Typography;

const DashboardPage = () => {
  const [statistics, setStatistics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dateRange, setDateRange] = useState(null); // 預設為 null（全部歷史資料）

  // 載入統計數據
  const loadStatistics = async (days = null) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await getChatStatistics(days);
      if (data) {
        console.log('Dashboard統計數據:', data);
        console.log('文件上傳次數:', data.summary.total_file_uploads);
        setStatistics(data);
        setError(null);
      } else {
        setError('獲取統計數據失敗');
      }
    } catch (err) {
      setError('載入統計數據失敗: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadStatistics(dateRange);
  }, [dateRange]);

  // 處理日期範圍變更
  const handleDateRangeChange = (value) => {
    if (value) {
      const now = new Date();
      const selectedDate = new Date(value);
      const days = Math.ceil((now - selectedDate) / (1000 * 60 * 60 * 24)) + 1;
      setDateRange(days);
    }
  };

  // 功能颜色映射 - 统一颜色配置
  const FUNCTION_COLORS = {
    'RVT Assistant': '#1890ff',     // 蓝色
    'AI OCR': '#52c41a',           // 绿色  
    'Protocol RAG': '#faad14'       // 橙色
  };

  // 根据功能名称获取颜色
  const getFunctionColor = (functionName) => {
    return FUNCTION_COLORS[functionName] || '#d9d9d9'; // 默认灰色
  };

  // 準備圓餅圖數據
  const preparePieData = () => {
    if (!statistics?.pie_chart) return [];
    return statistics.pie_chart.map((item) => ({
      ...item,
      color: getFunctionColor(item.name)
    }));
  };

  // 準備曲線圖數據
  const prepareLineData = () => {
    if (!statistics?.daily_chart) return [];
    
    return statistics.daily_chart.map(day => ({
      date: day.date,
      'Protocol RAG': day.know_issue_chat,
      'AI OCR': day.log_analyze_chat,
      'RVT Assistant': day.rvt_assistant_chat || 0,
      total: day.total
    }));
  };

  if (loading) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: '16px' }}>載入統計數據中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '24px' }}>
        <Alert
          message="載入失敗"
          description={error}
          type="error"
          action={
            <Button 
              size="small" 
              type="primary" 
              onClick={() => loadStatistics(dateRange)}
              icon={<ReloadOutlined />}
            >
              重試
            </Button>
          }
        />
      </div>
    );
  }

  return (
    <div style={{ padding: '24px', background: '#f5f5f5', minHeight: '100vh' }}>
      {/* 總詢問次數 - 單獨一行 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col span={24}>
          <Card style={{ textAlign: 'center' }}>
            <Statistic
              title="總詢問次數"
              value={statistics?.summary.total_chats || 0}
              prefix={<MessageOutlined style={{ color: '#1890ff' }} />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 其他統計卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="活躍用戶數"
              value={statistics?.summary.total_users || 0}
              suffix="人"
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="文件上傳次數"
              value={statistics?.summary.total_file_uploads || 0}
              prefix={<FileTextOutlined style={{ color: '#faad14' }} />}
              suffix="次"
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="平均響應時間"
              value={statistics?.summary.avg_response_time || 0}
              suffix="秒"
              precision={1}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 圖表區域 */}
      <Row gutter={[16, 16]}>
        {/* 圓餅圖 - 各功能使用比例 */}
        <Col xs={24} lg={12}>
          <Card 
            title="功能使用分佈" 
            extra={
              <span style={{ fontSize: '12px', color: '#666' }}>
                {
                  dateRange 
                    ? `最近 ${dateRange} 天` 
                    : '全部歷史'
                }
              </span>
            }
          >
            <div style={{ height: '400px' }}>
              {preparePieData().length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={preparePieData()}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={120}
                      dataKey="value"
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    >
                      {preparePieData().map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip formatter={(value) => [`${value} 次`, '使用次數']} />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ 
                  height: '400px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999'
                }}>
                  暫無數據
                </div>
              )}
            </div>
          </Card>
        </Col>

        {/* 曲線圖 - 每日使用趨勢 */}
        <Col xs={24} lg={12}>
          <Card 
            title="每日使用趨勢" 
            extra={
              <DatePicker 
                placeholder="選擇開始日期"
                onChange={handleDateRangeChange}
                disabledDate={(current) => current && current > new Date()}
                style={{ width: '150px' }}
              />
            }
          >
            <div style={{ height: '400px' }}>
              {prepareLineData().length > 0 ? (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={prepareLineData()}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 12 }}
                    />
                    <YAxis 
                      tick={{ fontSize: 12 }}
                      label={{ value: '使用次數', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      formatter={(value, name) => [`${value} 次`, name]}
                      labelFormatter={(date) => `日期: ${date}`}
                    />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="Protocol RAG" 
                      stroke={FUNCTION_COLORS['Protocol RAG']} 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="AI OCR" 
                      stroke={FUNCTION_COLORS['AI OCR']} 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="RVT Assistant" 
                      stroke={FUNCTION_COLORS['RVT Assistant']} 
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div style={{ 
                  height: '400px', 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  color: '#999'
                }}>
                  暫無數據
                </div>
              )}
            </div>
          </Card>
        </Col>
      </Row>

      {/* 詳細統計表格 */}
      <Row style={{ marginTop: '24px' }}>
        <Col span={24}>
          <Card title="功能詳細統計">
            <Row gutter={[16, 16]}>
              {statistics?.pie_chart?.map((item, index) => {
                const functionColor = getFunctionColor(item.name);
                const lightBackgroundColor = {
                  '#1890ff': '#e6f7ff',  // RVT Assistant 蓝色背景
                  '#52c41a': '#f6ffed',  // AI OCR 绿色背景
                  '#faad14': '#fff7e6'   // Protocol RAG 橙色背景
                }[functionColor] || '#f5f5f5';
                
                const borderColor = {
                  '#1890ff': '#91d5ff',  // RVT Assistant 蓝色边框
                  '#52c41a': '#b7eb8f',  // AI OCR 绿色边框  
                  '#faad14': '#ffd591'   // Protocol RAG 橙色边框
                }[functionColor] || '#d9d9d9';

                return (
                <Col xs={24} md={8} key={index}>
                  <Card 
                    size="small"
                    style={{ 
                      background: lightBackgroundColor,
                      border: `1px solid ${borderColor}`
                    }}
                  >
                    <Statistic
                      title={item.name}
                      value={item.value}
                      suffix="次"
                      valueStyle={{ 
                        color: functionColor
                      }}
                    />
                    <div style={{ fontSize: '12px', color: '#666', marginTop: '8px' }}>
                      平均響應時間: {item.avg_response_time}秒
                    </div>
                  </Card>
                </Col>
                );
              }) || []}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default DashboardPage;