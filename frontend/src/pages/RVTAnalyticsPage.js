import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Space,
  Typography,
  Button,
  Row,
  Col,
  Statistic,
  Progress,
  Select,
  DatePicker,
  message,
  Spin,
  Tag,
  Alert,
  Tabs,
  Empty,
  List
} from 'antd';
import {
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  TrophyOutlined,
  MessageOutlined,
  LikeOutlined,
  DislikeOutlined,
  QuestionCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CalendarOutlined
} from '@ant-design/icons';
import { 
  PieChart, 
  Pie, 
  Cell, 
  BarChart, 
  Bar, 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

const RVTAnalyticsPage = () => {
  const { user, isAuthenticated } = useAuth();
  const [loading, setLoading] = useState(false);
  const [overviewData, setOverviewData] = useState(null);
  const [questionData, setQuestionData] = useState(null);
  const [satisfactionData, setSatisfactionData] = useState(null);
  const [selectedDays, setSelectedDays] = useState(30);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [dateRange, setDateRange] = useState([]);
  const [networkError, setNetworkError] = useState(false);

  useEffect(() => {
    console.log('🔥 RVTAnalyticsPage useEffect 觸發');
    console.log('🔥 認證狀態:', { isAuthenticated, user });
    console.log('🔥 用戶權限:', { is_staff: user?.is_staff, is_superuser: user?.is_superuser });
    
    // 只有管理員才能訪問分析功能
    if (user?.is_staff || user?.is_superuser) {
      console.log('🔥 用戶有權限，開始載入分析資料');
      // 延遲加載，避免頁面載入時立即發送請求
      const timer = setTimeout(() => {
        fetchAnalyticsData();
      }, 100);
      
      return () => clearTimeout(timer);
    } else {
      console.log('🔥 用戶無權限或未登入，跳過載入分析資料');
    }
  }, [user, selectedDays, selectedUserId]);

  // 檢查管理員權限
  if (!user?.is_staff && !user?.is_superuser) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Card>
          <Space direction="vertical" size="large">
            <BarChartOutlined style={{ fontSize: '64px', color: '#ff4d4f' }} />
            <Title level={3}>權限不足</Title>
            <Text type="secondary">
              只有管理員才能訪問 RVT Assistant 分析功能
            </Text>
          </Space>
        </Card>
      </div>
    );
  }

  const fetchAnalyticsData = async () => {
    setLoading(true);
    setNetworkError(false);
    try {
      // 並行獲取所有分析數據
      const [overviewResponse, questionResponse, satisfactionResponse] = await Promise.all([
        fetch(`/api/rvt-analytics/overview/?days=${selectedDays}${selectedUserId ? `&user_id=${selectedUserId}` : ''}`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          }
        }),
        fetch(`/api/rvt-analytics/questions/?days=${selectedDays <= 30 ? selectedDays : 7}`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          }
        }),
        fetch(`/api/rvt-analytics/satisfaction/?days=${selectedDays}&detail=true`, {
          credentials: 'include',
          headers: {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
          }
        })
      ]);

      // 檢查 HTTP 狀態碼
      if (!overviewResponse.ok) {
        throw new Error(`概覽 API 錯誤: ${overviewResponse.status} ${overviewResponse.statusText}`);
      }
      if (!questionResponse.ok) {
        console.warn(`問題分析 API 錯誤: ${questionResponse.status} ${questionResponse.statusText}`);
      }
      if (!satisfactionResponse.ok) {
        console.warn(`滿意度 API 錯誤: ${satisfactionResponse.status} ${satisfactionResponse.statusText}`);
      }

      const [overview, questions, satisfaction] = await Promise.all([
        overviewResponse.json(),
        questionResponse.ok ? questionResponse.json() : { success: false, error: `HTTP ${questionResponse.status}` },
        satisfactionResponse.ok ? satisfactionResponse.json() : { success: false, error: `HTTP ${satisfactionResponse.status}` }
      ]);

      if (overview.success) {
        setOverviewData(overview.data);
        message.success('分析數據載入成功！');
      } else {
        message.error(`概覽數據載入失敗: ${overview.error || '未知錯誤'}`);
      }

      if (questions.success) {
        console.log('🔥 問題分析 API 回應:', questions);
        console.log('🔥 popular_questions 資料:', questions.data?.popular_questions);
        setQuestionData(questions.data);
      } else {
        console.warn(`問題分析載入失敗: ${questions.error || '未知錯誤'}`);
        message.warning('問題分析數據載入失敗，僅顯示基本統計');
      }

      if (satisfaction.success) {
        setSatisfactionData(satisfaction.data);
      } else {
        console.warn(`滿意度分析載入失敗: ${satisfaction.error || '未知錯誤'}`);
        message.warning('滿意度分析數據載入失敗，僅顯示基本統計');
      }

    } catch (error) {
      console.error('Analytics data fetch error:', error);
      setNetworkError(true);
      
      // 檢查錯誤類型
      if (error.message.includes('502') || error.message.includes('Bad Gateway')) {
        message.error('服務器暫時不可用 (502)，請稍後重試');
      } else if (error.message.includes('404')) {
        message.error('API 端點未找到 (404)，請檢查服務器配置');
      } else if (error.message.includes('403')) {
        message.error('權限不足 (403)，請重新登入');
      } else {
        message.error(`分析數據載入失敗: ${error.message}`);
      }
      
    } finally {
      setLoading(false);
    }
  };

  const renderOverviewCards = () => {
    if (!overviewData?.overview) return null;

    const { overview } = overviewData;
    const satisfactionStats = satisfactionData?.basic_stats || {};

    return (
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="總對話數"
              value={overview.total_conversations || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="滿意度"
              value={satisfactionStats.satisfaction_rate ? (satisfactionStats.satisfaction_rate * 100).toFixed(1) : 0}
              suffix="%"
              prefix={<LikeOutlined />}
              valueStyle={{ 
                color: satisfactionStats.satisfaction_rate > 0.7 ? '#52c41a' : 
                       satisfactionStats.satisfaction_rate > 0.5 ? '#faad14' : '#ff4d4f' 
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="反饋率"
              value={satisfactionStats.feedback_rate ? (satisfactionStats.feedback_rate * 100).toFixed(1) : 0}
              suffix="%"
              prefix={<QuestionCircleOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>
    );
  };

  // 圖表數據處理函數
  const prepareCategoryPieData = () => {
    if (!questionData?.category_distribution) return [];
    
    const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#13c2c2'];
    return Object.entries(questionData.category_distribution).map(([category, count], index) => ({
      name: category,
      value: count,
      color: colors[index % colors.length]
    }));
  };

  const prepareSatisfactionBarData = () => {
    if (!satisfactionData?.basic_stats) return [];
    
    const { helpful_count, unhelpful_count, unrated_count } = satisfactionData.basic_stats;
    return [
      { name: '正面反饋', value: helpful_count || 0, color: '#52c41a' },
      { name: '負面反饋', value: unhelpful_count || 0, color: '#ff4d4f' },
      { name: '無反饋', value: unrated_count || 0, color: '#d9d9d9' }
    ];
  };

  const prepareResponseTimeData = () => {
    if (!satisfactionData?.response_time_analysis) return [];
    
    const { fast, medium, slow } = satisfactionData.response_time_analysis;
    return [
      { name: '快速 (< 3s)', messages: fast?.total_messages || 0, satisfaction: (fast?.satisfaction_rate || 0) * 100 },
      { name: '中等 (3-10s)', messages: medium?.total_messages || 0, satisfaction: (medium?.satisfaction_rate || 0) * 100 },
      { name: '較慢 (> 10s)', messages: slow?.total_messages || 0, satisfaction: (slow?.satisfaction_rate || 0) * 100 }
    ];
  };

  const preparePopularQuestionsData = () => {
    console.log('🔥 preparePopularQuestionsData 被呼叫');
    console.log('🔥 questionData:', questionData);
    console.log('🔥 questionData?.popular_questions:', questionData?.popular_questions);
    
    if (!questionData?.popular_questions || questionData.popular_questions.length === 0) {
      console.log('🔥 返回空陣列，因為沒有 popular_questions 資料');
      return [];
    }
    
    // 將 popular_questions 數據轉換為圖表格式
    const result = questionData.popular_questions
      .slice(0, 5) // 顯示前5個熱門問題
      .map((item, index) => ({
        rank: `#${index + 1}`,
        question: item.pattern || item.question || '未知問題',
        count: item.count || 0,
        examples: item.examples || [],
        is_vector_based: item.is_vector_based,
        cluster_id: item.cluster_id,
        confidence: item.confidence
      }))
      .sort((a, b) => b.count - a.count); // 按次數降序排列
      
    console.log('🔥 preparePopularQuestionsData 結果:', result);
    console.log('🔥 每個項目的 count 值:', result.map(r => ({ question: r.question, count: r.count })));
    return result;
  };

  const renderQuestionAnalysis = () => {
    if (!questionData) {
      return (
        <Card title="問題分析" loading={loading}>
          <Empty description="暫無問題分析數據" />
        </Card>
      );
    }

    const { total_questions, top_keywords, category_distribution } = questionData;
    const pieData = prepareCategoryPieData();
    const popularQuestionsData = preparePopularQuestionsData();

    return (
      <Space direction="vertical" style={{ width: '100%' }} size="large">
        {/* 第一行：問題類型分布和統計信息 */}
        <Card title="問題分析" extra={<Tag color="blue">{questionData.period}</Tag>}>
          <Row gutter={[16, 16]}>
            {/* 問題類型分布圓餅圖 - 放大版本 */}
            <Col xs={24} lg={16}>
              <div style={{ height: '450px', padding: '16px' }}>
                {pieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={pieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={140}
                        label={({ name, percent }) => `${name} (${(percent * 100).toFixed(1)}%)`}
                        labelLine={false}
                        fontSize={12}
                      >
                        {pieData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip />
                      <Legend />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'center', 
                    height: '100%' 
                  }}>
                    <Empty description="暫無分類數據" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                  </div>
                )}
              </div>
            </Col>

            {/* 統計信息 - 縮小 */}
            <Col xs={24} lg={8}>
              <Empty description="更多統計功能開發中" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </Col>
          </Row>
          
          {/* 詳細分類統計 */}
          {category_distribution && Object.keys(category_distribution).length > 0 && (
            <Card size="small" title="詳細分類統計" style={{ marginTop: 16 }}>
              <Row gutter={[8, 8]}>
                {Object.entries(category_distribution).map(([category, count]) => (
                  <Col key={category}>
                    <Tag color="processing">
                      {category}: {count}
                    </Tag>
                  </Col>
                ))}
              </Row>
            </Card>
          )}
        </Card>

        {/* 第二行：熱門問題排名長條圖 */}
        <Card 
          title="🔥 熱門問題排名" 
          extra={
            <Space>
              {questionData?.is_vector_enhanced && (
                <Tag color="cyan" icon="🚀">
                  AI向量分析
                </Tag>
              )}
              {questionData?.is_vector_enhanced === false && (
                <Tag color="orange" icon="📝">
                  關鍵詞統計
                </Tag>
              )}
              <Tag color="volcano">最受關注</Tag>
            </Space>
          }
        >
          {popularQuestionsData.length > 0 ? (
            <div style={{ height: '450px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={popularQuestionsData} 
                  margin={{ top: 20, right: 30, left: 20, bottom: 120 }}
                >
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="question" 
                    angle={-45}
                    textAnchor="end"
                    height={120}
                    interval={0}
                    tick={{ fontSize: 12 }}
                    tickFormatter={(value) => {
                      // 限制顯示長度，避免 X 軸文字過長
                      return value.length > 15 ? value.substring(0, 15) + '...' : value;
                    }}
                  />
                  <YAxis 
                    label={{ value: '被問次數', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    content={({ active, payload, label }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload;
                        return (
                          <div style={{
                            backgroundColor: '#fff',
                            padding: '12px',
                            border: '1px solid #ccc',
                            borderRadius: '6px',
                            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
                            maxWidth: '350px'
                          }}>
                            <div style={{ marginBottom: '8px' }}>
                              <p style={{ margin: 0, fontWeight: 'bold', fontSize: '14px' }}>
                                {data.rank}: {data.question}
                              </p>
                              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                                <span style={{ color: '#1890ff', fontWeight: 'bold' }}>
                                  被問次數: {data.count}
                                </span>
                                {data.is_vector_based && (
                                  <span style={{ 
                                    fontSize: '10px', 
                                    backgroundColor: '#e6f7ff', 
                                    color: '#0050b3', 
                                    padding: '2px 6px', 
                                    borderRadius: '10px' 
                                  }}>
                                    🚀 AI分析
                                  </span>
                                )}
                              </div>
                            </div>
                            
                            {data.cluster_id !== undefined && (
                              <p style={{ margin: '4px 0', fontSize: '11px', color: '#666' }}>
                                聚類ID: {data.cluster_id} | 信心度: {data.confidence?.toFixed(3) || 'N/A'}
                              </p>
                            )}
                            
                            {data.examples && data.examples.length > 0 && (
                              <div style={{ marginTop: '8px' }}>
                                <p style={{ margin: '0 0 4px 0', fontSize: '12px', color: '#666', fontWeight: 'bold' }}>
                                  相關問題範例:
                                </p>
                                {data.examples.slice(0, 3).map((example, idx) => (
                                  <p key={idx} style={{ 
                                    margin: '2px 0', 
                                    fontSize: '11px', 
                                    color: '#999',
                                    maxWidth: '300px',
                                    overflow: 'hidden',
                                    textOverflow: 'ellipsis',
                                    whiteSpace: 'nowrap',
                                    paddingLeft: '8px'
                                  }}>
                                    • {example}
                                  </p>
                                ))}
                                {data.examples.length > 3 && (
                                  <p style={{ 
                                    margin: '2px 0', 
                                    fontSize: '10px', 
                                    color: '#ccc',
                                    fontStyle: 'italic'
                                  }}>
                                    ... 還有 {data.examples.length - 3} 個相似問題
                                  </p>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      }
                      return null;
                    }}
                  />
                  <Bar 
                    dataKey="count" 
                    fill="#1890ff"
                    radius={[4, 4, 0, 0]}
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <Empty 
              description="暫無熱門問題數據" 
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              style={{ padding: '40px 0' }}
            >
              <Text type="secondary">
                隨著用戶使用增加，這裡將顯示最受關注的問題排名
              </Text>
            </Empty>
          )}
        </Card>
      </Space>
    );
  };

  const renderTrendAnalysis = () => {
    if (!overviewData?.trends) {
      return (
        <Card title="趨勢分析" loading={loading}>
          <Empty description="暫無趨勢數據" />
        </Card>
      );
    }

    const { trends, performance_metrics } = overviewData;

    // 準備趨勢圖表數據
    const prepareTrendData = () => {
      const { daily_conversations = {}, daily_messages = {} } = trends;
      
      // 合併對話和消息數據
      const allDates = new Set([
        ...Object.keys(daily_conversations),
        ...Object.keys(daily_messages)
      ]);

      return Array.from(allDates)
        .sort()
        .map(date => ({
          date: dayjs(date).format('MM/DD'),
          conversations: daily_conversations[date] || 0,
          messages: daily_messages[date] || 0
        }));
    };

    // 準備響應時間分布數據
    const prepareResponseTimeDistribution = () => {
      if (!performance_metrics?.response_time_distribution) return [];
      
      const { response_time_distribution } = performance_metrics;
      return Object.entries(response_time_distribution).map(([range, count]) => ({
        range,
        count
      }));
    };

    const trendData = prepareTrendData();
    const responseTimeDistData = prepareResponseTimeDistribution();

    return (
      <Row gutter={[16, 16]}>
        {/* 對話和消息趨勢 */}
        <Col span={24}>
          <Card title="對話與消息趨勢" extra={<Tag color="blue">{selectedDays} 天趨勢</Tag>}>
            {trendData.length > 0 ? (
              <div style={{ height: '300px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="date" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Line 
                      type="monotone" 
                      dataKey="conversations" 
                      stroke="#1890ff" 
                      name="對話數"
                      strokeWidth={2}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="messages" 
                      stroke="#52c41a" 
                      name="消息數"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <Empty description="暫無趨勢數據" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>

        {/* 性能指標 */}
        <Col xs={24} lg={12}>
          <Card title="響應性能指標">
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="平均響應時間"
                  value={performance_metrics?.avg_response_time || 0}
                  suffix="秒"
                  precision={2}
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="最大響應時間"
                  value={performance_metrics?.max_response_time || 0}
                  suffix="秒"
                  precision={2}
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Col>
            </Row>
          </Card>
        </Col>

        {/* 響應時間分布 */}
        <Col xs={24} lg={12}>
          <Card title="響應時間分布">
            {responseTimeDistData.length > 0 ? (
              <div style={{ height: '200px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={responseTimeDistData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="range" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#722ed1" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <Empty description="暫無響應時間數據" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
          </Card>
        </Col>
      </Row>
    );
  };

  const renderSatisfactionAnalysis = () => {
    if (!satisfactionData?.basic_stats) {
      return (
        <Card title="滿意度分析" loading={loading}>
          <Empty description="暫無滿意度數據" />
        </Card>
      );
    }

    const { basic_stats, recommendations } = satisfactionData;
    const { 
      total_messages, 
      helpful_count, 
      unhelpful_count, 
      satisfaction_rate,
      feedback_rate 
    } = basic_stats;

    const barData = prepareSatisfactionBarData();
    const responseTimeData = prepareResponseTimeData();

    return (
      <Card 
        title="滿意度詳細分析" 
        extra={<Tag color="green">{satisfactionData.analysis_period}</Tag>}
      >
        <Row gutter={[16, 16]}>
          {/* 反饋分布柱狀圖 */}
          <Col xs={24} lg={12}>
            <Card size="small" title="反饋分布">
              <div style={{ height: '250px' }}>
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={barData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#1890ff">
                      {barData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </Card>
          </Col>

          {/* 滿意度指標 */}
          <Col xs={24} lg={12}>
            <Card size="small" title="滿意度指標">
              <Space direction="vertical" style={{ width: '100%' }}>
                <Row gutter={16}>
                  <Col span={8}>
                    <Statistic
                      title="正面反饋"
                      value={helpful_count || 0}
                      valueStyle={{ color: '#52c41a' }}
                      prefix={<LikeOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="負面反饋"
                      value={unhelpful_count || 0}
                      valueStyle={{ color: '#ff4d4f' }}
                      prefix={<DislikeOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="總消息數"
                      value={total_messages || 0}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Col>
                </Row>
                
                <div style={{ marginTop: 16 }}>
                  <Text strong>整體滿意度</Text>
                  <Progress
                    percent={satisfaction_rate ? Math.round(satisfaction_rate * 100) : 0}
                    status={satisfaction_rate > 0.7 ? 'success' : satisfaction_rate > 0.5 ? 'active' : 'exception'}
                    strokeColor={satisfaction_rate > 0.7 ? '#52c41a' : satisfaction_rate > 0.5 ? '#faad14' : '#ff4d4f'}
                  />
                </div>
                <div>
                  <Text strong>用戶反饋率</Text>
                  <Progress
                    percent={feedback_rate ? Math.round(feedback_rate * 100) : 0}
                    strokeColor="#722ed1"
                  />
                </div>
              </Space>
            </Card>
          </Col>
        </Row>

        {/* 響應時間分析圖表 */}
        {responseTimeData.length > 0 && (
          <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
            <Col span={24}>
              <Card size="small" title="響應時間與滿意度關係">
                <div style={{ height: '200px' }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={responseTimeData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis yAxisId="left" />
                      <YAxis yAxisId="right" orientation="right" />
                      <Tooltip />
                      <Legend />
                      <Bar yAxisId="left" dataKey="messages" fill="#8884d8" name="消息數量" />
                      <Bar yAxisId="right" dataKey="satisfaction" fill="#82ca9d" name="滿意度 %" />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </Card>
            </Col>
          </Row>
        )}

        {/* 改進建議 */}
        {recommendations && recommendations.length > 0 && (
          <Alert
            message="改進建議"
            description={
              <ul style={{ marginBottom: 0, paddingLeft: 20 }}>
                {recommendations.map((rec, index) => (
                  <li key={index}>{rec}</li>
                ))}
              </ul>
            }
            type="info"
            showIcon
            style={{ marginTop: 16 }}
          />
        )}
      </Card>
    );
  };

  // 檢查用戶認證和權限
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Card>
          <Alert
            message="需要登入"
            description="請先登入以查看 RVT Assistant 分析數據。"
            type="warning"
            showIcon
          />
        </Card>
      </div>
    );
  }

  if (!(user?.is_staff || user?.is_superuser)) {
    return (
      <div style={{ padding: '24px', textAlign: 'center' }}>
        <Card>
          <Alert
            message="權限不足"
            description="只有管理員才能查看 RVT Assistant 分析數據。"
            type="error"
            showIcon
          />
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* 頁面標題和控制項 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
        </Col>
        <Col>
          <Space>
            <Select
              value={selectedDays}
              onChange={setSelectedDays}
              style={{ width: 120 }}
            >
              <Option value={7}>最近 7 天</Option>
              <Option value={30}>最近 30 天</Option>
              <Option value={90}>最近 90 天</Option>
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchAnalyticsData}
              loading={loading}
            >
              重新載入
            </Button>
            <Button
              icon={<DownloadOutlined />}
              type="primary"
              onClick={() => message.info('導出功能開發中...')}
            >
              導出報告
            </Button>
          </Space>
        </Col>
      </Row>

      <Spin spinning={loading}>
        {/* 網絡錯誤提示 */}
        {networkError && (
          <Alert
            message="連接錯誤"
            description={
              <div>
                <p>無法載入分析數據，可能的原因：</p>
                <ul style={{ marginBottom: '12px', paddingLeft: '20px' }}>
                  <li>網絡連接不穩定</li>
                  <li>服務器暫時不可用</li>
                  <li>需要重新登入</li>
                </ul>
                <Button type="primary" size="small" onClick={fetchAnalyticsData}>
                  重新載入
                </Button>
              </div>
            }
            type="error"
            showIcon
            closable
            onClose={() => setNetworkError(false)}
            style={{ marginBottom: '24px' }}
          />
        )}
        
        {/* 概覽卡片 */}
        {renderOverviewCards()}

        {/* 詳細分析標籤頁 */}
        <Tabs defaultActiveKey="satisfaction" style={{ marginTop: 24 }}>
          <TabPane 
            tab={
              <span>
                <TrophyOutlined />
                滿意度分析
              </span>
            } 
            key="satisfaction"
          >
            {renderSatisfactionAnalysis()}
          </TabPane>

          <TabPane 
            tab={
              <span>
                <PieChartOutlined />
                問題分析
              </span>
            } 
            key="questions"
          >
            {renderQuestionAnalysis()}
          </TabPane>

          <TabPane 
            tab={
              <span>
                <LineChartOutlined />
                趨勢分析
              </span>
            } 
            key="trends"
          >
            {renderTrendAnalysis()}
          </TabPane>
        </Tabs>
      </Spin>
    </div>
  );
};

export default RVTAnalyticsPage;