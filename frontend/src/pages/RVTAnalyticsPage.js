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
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { TabPane } = Tabs;

const RVTAnalyticsPage = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [overviewData, setOverviewData] = useState(null);
  const [questionData, setQuestionData] = useState(null);
  const [satisfactionData, setSatisfactionData] = useState(null);
  const [selectedDays, setSelectedDays] = useState(30);
  const [selectedUserId, setSelectedUserId] = useState(null);
  const [dateRange, setDateRange] = useState([]);

  useEffect(() => {
    // 只有管理員才能訪問分析功能
    if (user?.is_staff || user?.is_superuser) {
      fetchAnalyticsData();
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
    try {
      // 並行獲取所有分析數據
      const [overviewResponse, questionResponse, satisfactionResponse] = await Promise.all([
        fetch(`/api/rvt-analytics/overview/?days=${selectedDays}${selectedUserId ? `&user_id=${selectedUserId}` : ''}`, {
          credentials: 'include'
        }),
        fetch(`/api/rvt-analytics/questions/?days=${selectedDays <= 30 ? selectedDays : 7}`, {
          credentials: 'include'
        }),
        fetch(`/api/rvt-analytics/satisfaction/?days=${selectedDays}&detail=true`, {
          credentials: 'include'
        })
      ]);

      const [overview, questions, satisfaction] = await Promise.all([
        overviewResponse.json(),
        questionResponse.json(), 
        satisfactionResponse.json()
      ]);

      if (overview.success) {
        setOverviewData(overview.data);
      } else {
        message.error(`概覽數據載入失敗: ${overview.error}`);
      }

      if (questions.success) {
        setQuestionData(questions.data);
      } else {
        console.warn(`問題分析載入失敗: ${questions.error}`);
      }

      if (satisfaction.success) {
        setSatisfactionData(satisfaction.data);
      } else {
        console.warn(`滿意度分析載入失敗: ${satisfaction.error}`);
      }

    } catch (error) {
      console.error('Analytics data fetch error:', error);
      message.error('分析數據載入失敗');
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
              title="總消息數"
              value={overview.total_messages || 0}
              prefix={<MessageOutlined />}
              valueStyle={{ color: '#52c41a' }}
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

  const renderQuestionAnalysis = () => {
    if (!questionData) {
      return (
        <Card title="問題分析" loading={loading}>
          <Empty description="暫無問題分析數據" />
        </Card>
      );
    }

    const { total_questions, top_keywords, category_distribution } = questionData;

    return (
      <Card title="問題分析" extra={<Tag color="blue">{questionData.period}</Tag>}>
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={12}>
            <Card size="small" title="總問題數量">
              <Statistic value={total_questions || 0} />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card size="small" title="熱門關鍵詞">
              {top_keywords && top_keywords.length > 0 ? (
                <List
                  size="small"
                  dataSource={top_keywords.slice(0, 5)}
                  renderItem={([keyword, count], index) => (
                    <List.Item>
                      <Space>
                        <Tag color={['red', 'orange', 'gold', 'green', 'blue'][index]}>
                          #{index + 1}
                        </Tag>
                        <Text strong>{keyword}</Text>
                        <Text type="secondary">({count} 次)</Text>
                      </Space>
                    </List.Item>
                  )}
                />
              ) : (
                <Empty description="暫無關鍵詞統計" image={Empty.PRESENTED_IMAGE_SIMPLE} />
              )}
            </Card>
          </Col>
        </Row>
        
        {category_distribution && Object.keys(category_distribution).length > 0 && (
          <Card size="small" title="問題類型分布" style={{ marginTop: 16 }}>
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

    return (
      <Card 
        title="滿意度詳細分析" 
        extra={<Tag color="green">{satisfactionData.analysis_period}</Tag>}
      >
        <Row gutter={[16, 16]}>
          {/* 滿意度概覽 */}
          <Col xs={24} lg={12}>
            <Card size="small" title="反饋統計">
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
            </Card>
          </Col>

          {/* 滿意度進度條 */}
          <Col xs={24} lg={12}>
            <Card size="small" title="滿意度指標">
              <Space direction="vertical" style={{ width: '100%' }}>
                <div>
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

  return (
    <div style={{ padding: '24px' }}>
      {/* 頁面標題和控制項 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: 24 }}>
        <Col>
          <Title level={2}>
            <BarChartOutlined /> RVT Assistant 分析報告
          </Title>
          <Text type="secondary">
            深度分析 RVT Assistant 的使用情況和用戶滿意度
          </Text>
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
            <Card title="趨勢分析">
              <Alert
                message="功能開發中"
                description="時間序列趨勢分析功能正在開發中，敬請期待。"
                type="info"
                showIcon
              />
            </Card>
          </TabPane>
        </Tabs>
      </Spin>
    </div>
  );
};

export default RVTAnalyticsPage;