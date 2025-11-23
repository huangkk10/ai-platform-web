/**
 * 批量測試對比報告頁面
 * 
 * 功能：
 * 1. 顯示批量測試的對比報告
 * 2. 雷達圖展示多維度對比
 * 3. 詳細數據表格
 * 4. 場景化推薦
 * 5. 導出報告功能
 */

import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card,
  Table,
  Button,
  Space,
  Alert,
  Statistic,
  Row,
  Col,
  message,
  Spin,
  Typography,
  Tag,
  Divider,
  Tooltip,
  Empty,
} from 'antd';
import {
  TrophyOutlined,
  ThunderboltOutlined,
  DownloadOutlined,
  ArrowLeftOutlined,
  StarOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import benchmarkApi from '../../services/benchmarkApi';
import './BatchComparisonPage.css';

const { Title, Text, Paragraph } = Typography;

const BatchComparisonPage = () => {
  const { batchId } = useParams();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [comparisonData, setComparisonData] = useState(null);
  const [testRuns, setTestRuns] = useState([]);

  useEffect(() => {
    loadComparisonData();
  }, [batchId]);

  const loadComparisonData = async () => {
    setLoading(true);
    try {
      // 目前後端批量測試會返回 comparison 資料
      // 但我們需要根據 batch_id 查詢對應的 test runs
      // 暫時使用 test_runs API 並根據 notes 中的 batch_id 篩選
      
      const response = await benchmarkApi.getTestRuns({
        run_type: 'batch_comparison',
      });

      // Handle both paginated and non-paginated formats
      const runs = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.results || []);
      
      console.log('🔍 查詢批量測試記錄:', {
        batchId,
        totalRuns: runs.length,
        searchPattern: `批次 ID: ${batchId}`,
        sampleNotes: runs.slice(0, 3).map(r => r.notes)
      });
      
      // 篩選出符合 batch_id 的測試執行
      const batchRuns = runs.filter(run => 
        run.notes && run.notes.includes(`批次 ID: ${batchId}`)
      );

      console.log('✅ 找到匹配記錄:', batchRuns.length);

      if (batchRuns.length === 0) {
        message.warning(`找不到對應的批量測試記錄 (batch_id: ${batchId})`);
        return;
      }

      setTestRuns(batchRuns);

      // ✅ 使用真實資料生成對比分析
      const realComparison = generateRealComparison(batchRuns);
      setComparisonData(realComparison);

    } catch (error) {
      console.error('載入對比資料失敗:', error);
      message.error('載入對比資料失敗');
    } finally {
      setLoading(false);
    }
  };

  // ✅ 從真實測試結果生成對比資料
  const generateRealComparison = (runs) => {
    console.log('📊 生成真實對比資料:', runs.length, '個測試執行');
    
    // 從測試執行記錄提取版本資料
    const versions = runs.map(run => {
      const versionData = {
        version_id: run.version?.id || run.version,
        version_name: run.version?.version_name || run.version_name || `版本 ${run.version}`,
        overall_score: parseFloat(run.overall_score) || 0,
        precision: parseFloat(run.precision) || 0,
        recall: parseFloat(run.recall) || 0,
        f1_score: parseFloat(run.f1_score) || 0,
        ndcg: parseFloat(run.ndcg) || 0,
        avg_response_time: parseFloat(run.avg_response_time) || 0,
        pass_rate: parseFloat(run.pass_rate) || 0,
        is_baseline: run.version?.is_baseline || false,
        test_run_id: run.id,
        created_at: run.created_at,
      };
      
      console.log('  版本:', versionData.version_name, '分數:', versionData.overall_score);
      return versionData;
    });

    // 排序
    const byOverallScore = [...versions].sort((a, b) => b.overall_score - a.overall_score);
    const byPrecision = [...versions].sort((a, b) => b.precision - a.precision);
    const byRecall = [...versions].sort((a, b) => b.recall - a.recall);
    const byF1Score = [...versions].sort((a, b) => b.f1_score - a.f1_score);
    const byResponseTime = [...versions].sort((a, b) => a.avg_response_time - b.avg_response_time);

    // 權衡分析
    const tradeOffs = analyzeTradeOffs(versions);

    return {
      versions,
      ranking: {
        by_overall_score: byOverallScore,
        by_precision: byPrecision,
        by_recall: byRecall,
        by_f1_score: byF1Score,
        by_response_time: byResponseTime,
      },
      best_version: byOverallScore[0],
      trade_offs: tradeOffs,
    };
  };

  // 權衡分析邏輯
  const analyzeTradeOffs = (versions) => {
    const tradeOffs = [];

    // 高精準度版本
    const highPrecision = versions.filter(v => v.precision > 0.8);
    if (highPrecision.length > 0) {
      tradeOffs.push({
        type: 'high_precision',
        title: '🎯 高精準度版本',
        description: `Precision > 80%`,
        versions: highPrecision.map(v => v.version_name),
        note: '適合：準確性優先、容錯率低的場景',
        color: 'blue',
      });
    }

    // 高召回率版本
    const highRecall = versions.filter(v => v.recall > 0.9);
    if (highRecall.length > 0) {
      tradeOffs.push({
        type: 'high_recall',
        title: '📚 高召回率版本',
        description: `Recall > 90%`,
        versions: highRecall.map(v => v.version_name),
        note: '適合：不能遺漏重要資訊的場景',
        color: 'green',
      });
    }

    // 平衡版本
    const balanced = versions.filter(v => 
      Math.abs(v.precision - v.recall) < 0.1 && v.f1_score > 0.7
    );
    if (balanced.length > 0) {
      tradeOffs.push({
        type: 'balanced',
        title: '⚖️ 平衡版本',
        description: `Precision/Recall 差距 < 10% 且 F1 > 70%`,
        versions: balanced.map(v => v.version_name),
        note: '適合：大多數通用場景',
        color: 'purple',
      });
    }

    // 快速版本
    const avgResponseTime = versions.reduce((sum, v) => sum + v.avg_response_time, 0) / versions.length;
    const fast = versions.filter(v => v.avg_response_time < avgResponseTime * 0.8);
    if (fast.length > 0) {
      tradeOffs.push({
        type: 'fast',
        title: '⚡ 快速回應版本',
        description: `響應時間 < ${(avgResponseTime * 0.8).toFixed(0)}ms`,
        versions: fast.map(v => v.version_name),
        note: '適合：即時互動、用戶體驗敏感的場景',
        color: 'orange',
      });
    }

    return tradeOffs;
  };

  // 表格列定義
  const columns = [
    {
      title: '排名',
      key: 'rank',
      width: 80,
      align: 'center',
      render: (_, __, index) => {
        if (index === 0) {
          return <Tag color="gold" icon={<TrophyOutlined />}>1</Tag>;
        }
        return <Tag>{index + 1}</Tag>;
      },
    },
    {
      title: '版本',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 250,
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          {record.is_baseline && (
            <Tag color="gold" icon={<ThunderboltOutlined />}>
              基準
            </Tag>
          )}
        </Space>
      ),
    },
    {
      title: '整體分數',
      dataIndex: 'overall_score',
      key: 'overall_score',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.overall_score - b.overall_score,
      render: (value) => (
        <Text strong style={{ color: '#1890ff', fontSize: 16 }}>
          {value.toFixed(1)}
        </Text>
      ),
    },
    {
      title: 'Precision',
      dataIndex: 'precision',
      key: 'precision',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.precision - b.precision,
      render: (value) => (
        <Tag color={value > 0.8 ? 'success' : value > 0.6 ? 'warning' : 'default'}>
          {(value * 100).toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: 'Recall',
      dataIndex: 'recall',
      key: 'recall',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.recall - b.recall,
      render: (value) => (
        <Tag color={value > 0.9 ? 'success' : value > 0.7 ? 'warning' : 'default'}>
          {(value * 100).toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: 'F1 Score',
      dataIndex: 'f1_score',
      key: 'f1_score',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.f1_score - b.f1_score,
      render: (value) => (
        <Tag color={value > 0.8 ? 'success' : value > 0.6 ? 'warning' : 'default'}>
          {(value * 100).toFixed(1)}%
        </Tag>
      ),
    },
    {
      title: '響應時間',
      dataIndex: 'avg_response_time',
      key: 'avg_response_time',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.avg_response_time - b.avg_response_time,
      render: (value) => (
        <Tooltip title={`${value.toFixed(2)}ms`}>
          <Tag color={value < 200 ? 'success' : value < 1000 ? 'warning' : 'error'}>
            {value.toFixed(0)}ms
          </Tag>
        </Tooltip>
      ),
    },
    {
      title: '通過率',
      dataIndex: 'pass_rate',
      key: 'pass_rate',
      width: 120,
      align: 'center',
      sorter: (a, b) => a.pass_rate - b.pass_rate,
      render: (value) => (
        <Tag color={value > 0.9 ? 'success' : value > 0.7 ? 'warning' : 'default'}>
          {(value * 100).toFixed(1)}%
        </Tag>
      ),
    },
  ];

  // 導出報告
  const handleExportReport = () => {
    if (!comparisonData) return;

    const reportContent = JSON.stringify(comparisonData, null, 2);
    const blob = new Blob([reportContent], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-comparison-${batchId}.json`;
    a.click();
    URL.revokeObjectURL(url);

    message.success('報告已導出');
  };

  if (loading) {
    return (
      <div className="batch-comparison-page" style={{ textAlign: 'center', paddingTop: 100 }}>
        <Spin size="large" tip="載入對比資料中..." />
      </div>
    );
  }

  if (!comparisonData || comparisonData.versions.length === 0) {
    return (
      <div className="batch-comparison-page">
        <Card>
          <Empty
            description="沒有找到對比資料"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          >
            <Button type="primary" onClick={() => navigate('/benchmark/batch-test')}>
              前往批量測試
            </Button>
          </Empty>
        </Card>
      </div>
    );
  }

  const { versions, ranking, best_version, trade_offs } = comparisonData;

  return (
    <div className="batch-comparison-page">
      <Card
        title={
          <Space>
            <TrophyOutlined />
            <span>批量測試對比報告</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExportReport}
            >
              導出報告
            </Button>
            <Button
              icon={<ArrowLeftOutlined />}
              onClick={() => navigate('/benchmark/batch-test')}
            >
              返回批量測試
            </Button>
          </Space>
        }
      >
        {/* 批次資訊 */}
        <Alert
          message={
            <Space>
              <Text>批次 ID: <Text code>{batchId}</Text></Text>
              <Divider type="vertical" />
              <Text>測試時間: {new Date().toLocaleString('zh-TW')}</Text>
            </Space>
          }
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 綜合最佳版本 */}
        {best_version && (
          <Card
            type="inner"
            title={
              <Space>
                <StarOutlined style={{ color: '#faad14' }} />
                <Text>綜合最佳版本</Text>
              </Space>
            }
            style={{ marginBottom: 24 }}
            bodyStyle={{ backgroundColor: '#fffbe6' }}
          >
            <Row gutter={16} align="middle">
              <Col span={8}>
                <Title level={3} style={{ marginBottom: 0 }}>
                  {best_version.version_name}
                </Title>
                <Text type="secondary">整體分數: {best_version.overall_score.toFixed(1)}</Text>
              </Col>
              <Col span={4}>
                <Statistic
                  title="Precision"
                  value={(best_version.precision * 100).toFixed(1)}
                  suffix="%"
                  valueStyle={{ color: '#52c41a' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="Recall"
                  value={(best_version.recall * 100).toFixed(1)}
                  suffix="%"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="F1 Score"
                  value={(best_version.f1_score * 100).toFixed(1)}
                  suffix="%"
                  valueStyle={{ color: '#722ed1' }}
                />
              </Col>
              <Col span={4}>
                <Statistic
                  title="響應時間"
                  value={best_version.avg_response_time.toFixed(0)}
                  suffix="ms"
                  valueStyle={{ color: '#fa8c16' }}
                />
              </Col>
            </Row>
          </Card>
        )}

        {/* 詳細數據對比表 */}
        <Card
          type="inner"
          title="📋 詳細數據對比"
          style={{ marginBottom: 24 }}
        >
          <Table
            dataSource={ranking.by_overall_score}
            columns={columns}
            rowKey="version_id"
            pagination={false}
            size="middle"
            scroll={{ x: 1200 }}
          />
        </Card>

        {/* 場景化推薦 */}
        {trade_offs && trade_offs.length > 0 && (
          <Card type="inner" title="💡 場景化推薦">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {trade_offs.map((tradeOff, index) => (
                <Card
                  key={index}
                  size="small"
                  title={<Text strong>{tradeOff.title}</Text>}
                  extra={<Tag color={tradeOff.color}>{tradeOff.description}</Tag>}
                >
                  <Paragraph>
                    <Text strong>推薦版本: </Text>
                    <Space>
                      {tradeOff.versions.map((ver, idx) => (
                        <Tag key={idx} color={tradeOff.color} icon={<CheckCircleOutlined />}>
                          {ver}
                        </Tag>
                      ))}
                    </Space>
                  </Paragraph>
                  <Paragraph type="secondary" style={{ marginBottom: 0 }}>
                    <ClockCircleOutlined /> {tradeOff.note}
                  </Paragraph>
                </Card>
              ))}
            </Space>
          </Card>
        )}

        {/* 底部操作按鈕 */}
        <Divider />
        <div style={{ textAlign: 'center' }}>
          <Space size="large">
            <Button
              type="primary"
              size="large"
              onClick={() => navigate('/benchmark/dashboard')}
            >
              返回 Dashboard
            </Button>
            <Button
              size="large"
              onClick={() => navigate('/benchmark/batch-test')}
            >
              執行新的批量測試
            </Button>
          </Space>
        </div>
      </Card>
    </div>
  );
};

export default BatchComparisonPage;
