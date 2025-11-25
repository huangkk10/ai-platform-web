/**
 * Dify 測試歷史頁面
 * 
 * 功能：
 * 1. 顯示從「Dify 版本管理」執行的所有測試記錄
 * 2. 統計卡片：總測試數、平均分數、平均通過率、今日測試數
 * 3. 表格展示：測試時間、版本名稱、問題數、通過率、平均分數等
 * 4. 支援搜尋、篩選和分頁
 * 
 * API:
 * - GET /api/dify-benchmark/test-runs/ - 獲取所有測試記錄
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Statistic,
  Row,
  Col,
  message,
  Input,
  Empty,
  Tooltip
} from 'antd';
import {
  ReloadOutlined,
  SearchOutlined,
  TrophyOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';
import './DifyTestHistoryPage.css';

const { Title, Text } = Typography;

const DifyTestHistoryPage = () => {
  // State
  const [testRuns, setTestRuns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [statistics, setStatistics] = useState({
    total_tests: 0,
    avg_score: 0,
    avg_pass_rate: 0,
    today_tests: 0
  });

  // Load data on mount
  useEffect(() => {
    loadTestHistory();
  }, []);

  // 載入測試歷史
  const loadTestHistory = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/dify-benchmark/test-runs/', {
        withCredentials: true,
        params: {
          page_size: 1000  // 載入所有記錄
        }
      });

      const runs = response.data.results || [];
      setTestRuns(runs);
      
      // 計算統計資料
      calculateStatistics(runs);
      
      message.success(`成功載入 ${runs.length} 筆測試記錄`);
    } catch (error) {
      console.error('Error loading test history:', error);
      message.error('載入測試歷史失敗：' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 計算統計資料
  const calculateStatistics = (runs) => {
    const totalTests = runs.length;
    
    // 計算平均分數（排除 null 值）
    const validScores = runs.filter(run => run.average_score !== null);
    const avgScore = validScores.length > 0
      ? validScores.reduce((sum, run) => sum + run.average_score, 0) / validScores.length
      : 0;
    
    // 計算平均通過率（排除 null 值）
    const validPassRates = runs.filter(run => run.pass_rate !== null);
    const avgPassRate = validPassRates.length > 0
      ? validPassRates.reduce((sum, run) => sum + run.pass_rate, 0) / validPassRates.length
      : 0;
    
    // 計算今日測試數
    const today = new Date().toDateString();
    const todayTests = runs.filter(run => {
      const runDate = new Date(run.created_at).toDateString();
      return runDate === today;
    }).length;

    setStatistics({
      total_tests: totalTests,
      avg_score: avgScore,
      avg_pass_rate: avgPassRate,
      today_tests: todayTests
    });
  };

  // 格式化日期時間
  const formatDateTime = (dateString) => {
    if (!dateString) return '-';
    const date = new Date(dateString);
    const dateStr = date.toLocaleDateString('zh-TW');
    const timeStr = date.toLocaleTimeString('zh-TW', { hour: '2-digit', minute: '2-digit' });
    return { dateStr, timeStr };
  };

  // 獲取分數顏色
  const getScoreColor = (score) => {
    if (score === null || score === undefined) return '#999';
    if (score >= 80) return '#52c41a';
    if (score >= 60) return '#faad14';
    return '#ff4d4f';
  };

  // 獲取通過率標籤顏色
  const getPassRateTagColor = (rate) => {
    if (rate === null || rate === undefined) return 'default';
    if (rate >= 80) return 'success';
    if (rate >= 60) return 'warning';
    return 'error';
  };

  // 表格欄位定義
  const columns = [
    {
      title: '測試時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 150,
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      defaultSortOrder: 'descend',
      render: (dateString) => {
        const { dateStr, timeStr } = formatDateTime(dateString);
        return (
          <div>
            <div>{dateStr}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>{timeStr}</Text>
          </div>
        );
      },
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 250,
      ellipsis: {
        showTitle: false,
      },
      render: (name) => (
        <Tooltip title={name}>
          <Text strong>{name || '未命名版本'}</Text>
        </Tooltip>
      ),
    },
    {
      title: '測試類型',
      dataIndex: 'run_type',
      key: 'run_type',
      width: 120,
      filters: [
        { text: '單次測試', value: 'single' },
        { text: '批量比較', value: 'batch_comparison' },
      ],
      onFilter: (value, record) => record.run_type === value,
      render: (type) => {
        const typeMap = {
          'single': { text: '單次測試', color: 'blue' },
          'batch_comparison': { text: '批量比較', color: 'purple' }
        };
        const config = typeMap[type] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      },
    },
    {
      title: '測試問題數',
      dataIndex: 'total_test_cases',
      key: 'total_test_cases',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.total_test_cases - b.total_test_cases,
    },
    {
      title: '通過數',
      dataIndex: 'passed_cases',
      key: 'passed_cases',
      width: 100,
      align: 'center',
      render: (passed) => (
        <Tag color="success">{passed || 0}</Tag>
      ),
    },
    {
      title: '失敗數',
      dataIndex: 'failed_cases',
      key: 'failed_cases',
      width: 100,
      align: 'center',
      render: (failed) => (
        <Tag color="error">{failed || 0}</Tag>
      ),
    },
    {
      title: '通過率',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 120,
      align: 'center',
      sorter: (a, b) => (a.pass_rate || 0) - (b.pass_rate || 0),
      render: (rate) => {
        const numRate = parseFloat(rate);
        const color = getPassRateTagColor(numRate);
        return (
          <Tag color={color}>
            {!isNaN(numRate) ? `${numRate.toFixed(1)}%` : 'N/A'}
          </Tag>
        );
      },
    },
    {
      title: '平均分數',
      dataIndex: 'average_score',
      key: 'average_score',
      width: 120,
      align: 'center',
      sorter: (a, b) => (a.average_score || 0) - (b.average_score || 0),
      render: (score) => {
        const numScore = parseFloat(score);
        const color = getScoreColor(numScore);
        return (
          <Text strong style={{ color, fontSize: '16px' }}>
            {!isNaN(numScore) ? numScore.toFixed(2) : 'N/A'}
          </Text>
        );
      },
    },
    {
      title: '執行時間',
      dataIndex: 'total_execution_time',
      key: 'total_execution_time',
      width: 120,
      align: 'center',
      render: (time) => {
        const numTime = parseFloat(time);
        if (!time || isNaN(numTime)) return '-';
        return (
          <Space>
            <ClockCircleOutlined />
            <Text>{numTime.toFixed(1)}s</Text>
          </Space>
        );
      },
    },
  ];

  // 篩選資料
  const filteredTestRuns = testRuns.filter(run => {
    if (!searchText) return true;
    const searchLower = searchText.toLowerCase();
    return (
      run.version_name?.toLowerCase().includes(searchLower) ||
      run.run_name?.toLowerCase().includes(searchLower)
    );
  });

  return (
    <div className="dify-test-history-page">
      <Card>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* 頁面標題 */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={2}>VSA 測試歷史</Title>
            <Space>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadTestHistory}
              >
                重新整理
              </Button>
            </Space>
          </div>

          {/* 統計卡片 */}
          <Row gutter={16}>
            <Col span={6}>
              <Card>
                <Statistic
                  title="總測試數"
                  value={statistics.total_tests}
                  suffix="次"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="平均分數"
                  value={(statistics.avg_score || 0).toFixed(2)}
                  suffix="分"
                  valueStyle={{ color: getScoreColor(statistics.avg_score) }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="平均通過率"
                  value={(statistics.avg_pass_rate || 0).toFixed(1)}
                  suffix="%"
                  valueStyle={{ color: getScoreColor(statistics.avg_pass_rate) }}
                />
              </Card>
            </Col>
            <Col span={6}>
              <Card>
                <Statistic
                  title="今日測試數"
                  value={statistics.today_tests}
                  suffix="次"
                  valueStyle={{ color: '#52c41a' }}
                  prefix={<TrophyOutlined />}
                />
              </Card>
            </Col>
          </Row>

          {/* 搜尋框 */}
          <Input
            placeholder="搜尋版本名稱或測試名稱..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />

          {/* 測試歷史表格 */}
          <Table
            columns={columns}
            dataSource={filteredTestRuns}
            rowKey="id"
            loading={loading}
            pagination={{
              defaultPageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
            scroll={{ x: 1400, y: 'calc(100vh - 450px)' }}
            locale={{
              emptyText: (
                <Empty
                  description="尚無測試記錄"
                  image={Empty.PRESENTED_IMAGE_SIMPLE}
                />
              ),
            }}
          />
        </Space>
      </Card>
    </div>
  );
};

export default DifyTestHistoryPage;
