/**
 * Benchmark Dashboard Page
 * 
 * 提供 Benchmark 系統的全局概覽，包含：
 * - 關鍵指標卡片（Overall Score、Pass Rate、Avg Time、Total Tests）
 * - 趨勢圖表（分數趨勢、通過率趨勢）
 * - 最近測試執行列表
 * - 基準版本資訊
 */

import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Tag,
  Space,
  Button,
  Typography,
  Spin,
  Alert,
  Empty,
  Tooltip,
} from 'antd';
import {
  ReloadOutlined,
  TrophyOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ExperimentOutlined,
  ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import benchmarkApi from '../../services/benchmarkApi';
import ScoreTrendChart from '../../components/charts/ScoreTrendChart';
import PassRateTrendChart from '../../components/charts/PassRateTrendChart';
import './BenchmarkDashboardPage.css';

const { Title, Text } = Typography;

const BenchmarkDashboardPage = () => {
  const navigate = useNavigate();
  
  // 狀態管理
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [recentTests, setRecentTests] = useState([]);
  const [baselineVersion, setBaselineVersion] = useState(null);
  const [chartData, setChartData] = useState({
    scoreData: [],
    passRateData: [],
  });
  const [statistics, setStatistics] = useState({
    totalTests: 0,
    avgScore: 0,
    avgPassRate: 0,
    avgResponseTime: 0,
    todayTests: 0,
    weekTests: 0,
  });

  // 載入數據
  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // 並行獲取多個資料
      const [testsResponse, baselineResponse] = await Promise.all([
        benchmarkApi.getTestRuns({ days: 30 }),
        benchmarkApi.getBaselineVersion().catch(() => null), // 可能沒有基準版本
      ]);

      // 處理 API 回應數據（可能是分頁或直接陣列）
      let tests = [];
      if (Array.isArray(testsResponse.data)) {
        tests = testsResponse.data;
      } else if (testsResponse.data?.results && Array.isArray(testsResponse.data.results)) {
        tests = testsResponse.data.results;
      } else if (testsResponse.data?.data && Array.isArray(testsResponse.data.data)) {
        tests = testsResponse.data.data;
      }
      
      // 計算統計資訊
      const completedTests = tests.filter(t => t.status === 'completed');
      const todayTests = tests.filter(t => {
        const testDate = new Date(t.created_at);
        const today = new Date();
        return testDate.toDateString() === today.toDateString();
      });
      const weekTests = tests.filter(t => {
        const testDate = new Date(t.created_at);
        const weekAgo = new Date();
        weekAgo.setDate(weekAgo.getDate() - 7);
        return testDate >= weekAgo;
      });

      // 計算平均值（確保類型轉換）
      const avgScore = completedTests.length > 0
        ? completedTests.reduce((sum, t) => sum + (parseFloat(t.overall_score) || 0), 0) / completedTests.length
        : 0;
      
      const avgPassRate = completedTests.length > 0
        ? completedTests.reduce((sum, t) => {
            // 使用 API 提供的 pass_rate 欄位
            const rate = parseFloat(t.pass_rate) || 0;
            return sum + rate;
          }, 0) / completedTests.length
        : 0;

      const avgResponseTime = completedTests.length > 0
        ? completedTests.reduce((sum, t) => sum + (parseFloat(t.avg_response_time) || 0), 0) / completedTests.length
        : 0;

      setStatistics({
        totalTests: tests.length,
        avgScore: parseFloat(avgScore.toFixed(2)),
        avgPassRate: parseFloat(avgPassRate.toFixed(1)),
        avgResponseTime: parseFloat(avgResponseTime.toFixed(0)),
        todayTests: todayTests.length,
        weekTests: weekTests.length,
      });

      // 準備圖表數據（只使用已完成的測試）
      const chartDataPoints = completedTests
        .sort((a, b) => new Date(a.created_at) - new Date(b.created_at)) // 按時間排序
        .map(test => ({
          date: new Date(test.created_at).toLocaleDateString('zh-TW', {
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
          }),
          overall_score: parseFloat(test.overall_score) || 0,
          precision: (parseFloat(test.avg_precision) || 0) * 100, // 轉換為百分比
          recall: (parseFloat(test.avg_recall) || 0) * 100,
          f1_score: (parseFloat(test.avg_f1_score) || 0) * 100,
          pass_rate: parseFloat(test.pass_rate) || 0,
        }));

      setChartData({
        scoreData: chartDataPoints,
        passRateData: chartDataPoints,
      });

      // 設置最近 10 次測試
      setRecentTests(tests.slice(0, 10));
      setBaselineVersion(baselineResponse?.data || null);

    } catch (err) {
      console.error('載入 Dashboard 數據失敗:', err);
      setError(err.response?.data?.error || err.message || '載入數據失敗');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // 狀態標籤渲染
  const renderStatusTag = (status) => {
    const statusConfig = {
      'completed': { color: 'success', text: '已完成' },
      'running': { color: 'processing', text: '執行中' },
      'failed': { color: 'error', text: '失敗' },
      'stopped': { color: 'warning', text: '已停止' },
      'pending': { color: 'default', text: '等待中' },
    };
    
    const config = statusConfig[status] || statusConfig['pending'];
    return <Tag color={config.color}>{config.text}</Tag>;
  };

  // 表格欄位定義
  const columns = [
    {
      title: '執行名稱',
      dataIndex: 'run_name',
      key: 'run_name',
      width: 250,
      ellipsis: true,
      render: (text, record) => (
        <Tooltip title={text}>
          <a onClick={() => navigate(`/benchmark/results?run_id=${record.id}`)}>
            {text}
          </a>
        </Tooltip>
      ),
    },
    {
      title: '版本',
      dataIndex: ['version', 'version_name'],
      key: 'version',
      width: 120,
      render: (text, record) => (
        <Tooltip title={record.version?.description}>
          <Tag color="blue">{text}</Tag>
        </Tooltip>
      ),
    },
    {
      title: '整體分數',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 100,
      align: 'center',
      sorter: (a, b) => (parseFloat(a.overall_score) || 0) - (parseFloat(b.overall_score) || 0),
      render: (score) => {
        const numScore = parseFloat(score);
        if (isNaN(numScore)) return <Text>N/A</Text>;
        return (
          <Text strong style={{ fontSize: '16px', color: numScore >= 70 ? '#52c41a' : numScore >= 50 ? '#faad14' : '#f5222d' }}>
            {numScore.toFixed(1)}
          </Text>
        );
      },
    },
    {
      title: '通過率',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 100,
      align: 'center',
      render: (rate) => {
        const numRate = parseFloat(rate) || 0;
        return (
          <Text style={{ color: numRate >= 80 ? '#52c41a' : numRate >= 60 ? '#faad14' : '#f5222d' }}>
            {numRate.toFixed(1)}%
          </Text>
        );
      },
    },
    {
      title: '測試數',
      dataIndex: 'total_test_cases',
      key: 'total_test_cases',
      width: 80,
      align: 'center',
      render: (total, record) => (
        <Text>{record.passed_count || 0}/{total}</Text>
      ),
    },
    {
      title: '平均時間',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      width: 100,
      align: 'center',
      render: (time) => {
        const numTime = parseFloat(time);
        if (isNaN(numTime)) return <Text>N/A</Text>;
        return <Text>{numTime.toFixed(0)}ms</Text>;
      },
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      align: 'center',
      render: renderStatusTag,
    },
    {
      title: '執行時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      render: (time) => new Date(time).toLocaleString('zh-TW', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      }),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      render: (_, record) => (
        <Button
          type="link"
          size="small"
          icon={<ArrowRightOutlined />}
          onClick={() => navigate(`/benchmark/results?run_id=${record.id}`)}
        >
          查看詳情
        </Button>
      ),
    },
  ];

  // Loading 狀態
  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh' }}>
        <Spin size="large" tip="載入 Dashboard 數據中..." />
      </div>
    );
  }

  // Error 狀態
  if (error) {
    return (
      <Alert
        message="載入失敗"
        description={error}
        type="error"
        showIcon
        action={
          <Button size="small" onClick={loadData}>
            重試
          </Button>
        }
        style={{ margin: '24px' }}
      />
    );
  }

  return (
    <div className="benchmark-dashboard">
      {/* 頁面標題 */}
      <div className="dashboard-header">
        <Title level={2}>
          <ExperimentOutlined /> Benchmark Dashboard
        </Title>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={loadData}>
            刷新數據
          </Button>
          <Button
            type="primary"
            onClick={() => navigate('/benchmark/test-execution')}
          >
            開始新測試
          </Button>
        </Space>
      </div>

      {/* 基準版本資訊（如果有） */}
      {baselineVersion && (
        <Alert
          message={
            <Space>
              <TrophyOutlined />
              <Text strong>當前基準版本：</Text>
              <Tag color="gold">{baselineVersion.version_name}</Tag>
              <Text type="secondary">{baselineVersion.description}</Text>
            </Space>
          }
          type="info"
          showIcon={false}
          style={{ marginBottom: '24px' }}
        />
      )}

      {/* 關鍵指標卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="整體平均分數"
              value={statistics.avgScore}
              precision={1}
              valueStyle={{ color: '#3f8600' }}
              prefix={<TrophyOutlined />}
              suffix="/ 100"
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              基於最近 30 天的測試
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均通過率"
              value={statistics.avgPassRate}
              precision={1}
              valueStyle={{ color: statistics.avgPassRate >= 80 ? '#3f8600' : '#cf1322' }}
              prefix={<CheckCircleOutlined />}
              suffix="%"
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              成功通過的測試案例比例
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="平均回應時間"
              value={statistics.avgResponseTime}
              precision={0}
              valueStyle={{ color: '#1890ff' }}
              prefix={<ClockCircleOutlined />}
              suffix="ms"
            />
            <Text type="secondary" style={{ fontSize: '12px' }}>
              每次搜尋的平均耗時
            </Text>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="總測試執行數"
              value={statistics.totalTests}
              valueStyle={{ color: '#722ed1' }}
              prefix={<ExperimentOutlined />}
            />
            <Space style={{ fontSize: '12px', marginTop: '8px' }}>
              <Text type="secondary">今日: {statistics.todayTests}</Text>
              <Text type="secondary">本週: {statistics.weekTests}</Text>
            </Space>
          </Card>
        </Col>
      </Row>

      {/* 最近測試執行列表 */}
      <Card
        title={
          <Space>
            <Text strong style={{ fontSize: '16px' }}>最近測試執行</Text>
            <Tag color="blue">{recentTests.length} 筆</Tag>
          </Space>
        }
        extra={
          <Button
            type="link"
            onClick={() => navigate('/benchmark/results')}
          >
            查看全部 →
          </Button>
        }
      >
        {recentTests.length > 0 ? (
          <Table
            dataSource={recentTests}
            columns={columns}
            rowKey="id"
            pagination={false}
            size="middle"
            scroll={{ x: 1200 }}
          />
        ) : (
          <Empty
            description="尚無測試執行記錄"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/benchmark/test-execution')}>
              開始第一次測試
            </Button>
          </Empty>
        )}
      </Card>

      {/* 圖表區域 */}
      <Row gutter={[16, 16]} style={{ marginTop: '24px' }}>
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <Text strong>分數趨勢圖</Text>
                <Text type="secondary" style={{ fontSize: '12px', fontWeight: 'normal' }}>
                  （最近 30 天）
                </Text>
              </Space>
            }
          >
            <ScoreTrendChart data={chartData.scoreData} />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card 
            title={
              <Space>
                <Text strong>通過率趨勢圖</Text>
                <Text type="secondary" style={{ fontSize: '12px', fontWeight: 'normal' }}>
                  （最近 30 天）
                </Text>
              </Space>
            }
          >
            <PassRateTrendChart data={chartData.passRateData} />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default BenchmarkDashboardPage;
