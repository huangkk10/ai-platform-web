/**
 * 版本比較測試 Modal
 * ===================
 * 
 * 功能：對單一測試案例執行多個搜尋版本的比較測試
 * 
 * 使用場景：
 * - 快速診斷單一問題在不同版本的表現
 * - 驗證關鍵字調整效果
 * - 評估新增問題的品質
 * 
 * 時間優勢：
 * - 單問題 × 5 版本 = 20-30 秒
 * - 完整批量測試 = 40-50 分鐘
 * - 節省 99.2% 時間 ⚡
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Table,
  Progress,
  Button,
  Tag,
  Space,
  Typography,
  Spin,
  message,
  Tooltip,
  Empty,
  Statistic,
  Row,
  Col,
  Alert
} from 'antd';
import {
  ExperimentOutlined,
  DownloadOutlined,
  ReloadOutlined,
  CloseOutlined,
  TrophyOutlined,
  ThunderboltOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import unifiedBenchmarkApi from '../../services/unifiedBenchmarkApi';

const { Title, Text, Paragraph } = Typography;

/**
 * 版本比較 Modal 組件
 * 
 * Props:
 * - visible: boolean - 是否顯示 Modal
 * - onClose: function - 關閉 Modal 的回調
 * - testCase: object - 測試案例資料
 */
const VersionComparisonModal = ({ visible, onClose, testCase }) => {
  // 狀態管理
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const [progress, setProgress] = useState(0);
  const [testCaseInfo, setTestCaseInfo] = useState(null);
  const [error, setError] = useState(null);

  // 當 Modal 打開時，自動開始測試
  useEffect(() => {
    if (visible && testCase) {
      startTest();
    }
    
    // 當 Modal 關閉時，重置狀態
    if (!visible) {
      resetState();
    }
  }, [visible, testCase]);

  /**
   * 重置所有狀態
   */
  const resetState = () => {
    setLoading(false);
    setResults([]);
    setSummary(null);
    setProgress(0);
    setTestCaseInfo(null);
    setError(null);
  };

  /**
   * 開始版本比較測試
   */
  const startTest = async () => {
    if (!testCase || !testCase.id) {
      message.error('無效的測試案例');
      return;
    }

    setLoading(true);
    setError(null);
    setProgress(0);
    setResults([]);

    try {
      // 調用 API 執行測試
      const response = await unifiedBenchmarkApi.versionComparison(testCase.id, {
        version_ids: null,  // null = 測試所有啟用版本
        force_retest: false
      });

      if (response.data.success) {
        // 設定測試結果
        setTestCaseInfo(response.data.test_case);
        setResults(response.data.results);
        setSummary(response.data.summary);
        setProgress(100);
        
        message.success(`測試完成！共測試 ${response.data.results.length} 個版本`);
      } else {
        throw new Error(response.data.error || '測試失敗');
      }

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || '測試執行失敗';
      setError(errorMsg);
      message.error(errorMsg);
      console.error('版本比較測試失敗:', err);
    } finally {
      setLoading(false);
    }
  };

  /**
   * 重新測試
   */
  const handleRetest = () => {
    startTest();
  };

  /**
   * 匯出結果為 CSV
   */
  const handleExport = () => {
    if (!results || results.length === 0) {
      message.warning('沒有可匯出的資料');
      return;
    }

    try {
      // 準備 CSV 資料
      const headers = ['版本名稱', '策略類型', 'Precision', 'Recall', 'F1 Score', '回應時間(秒)', '狀態'];
      const rows = results.map(r => [
        r.version_name,
        r.strategy_type,
        (r.metrics.precision * 100).toFixed(2) + '%',
        (r.metrics.recall * 100).toFixed(2) + '%',
        (r.metrics.f1_score * 100).toFixed(2) + '%',
        r.response_time.toFixed(2),
        r.status === 'success' ? '成功' : '失敗'
      ]);

      const csvContent = [
        `問題: ${testCaseInfo?.question || testCase?.question}`,
        `難度: ${testCaseInfo?.difficulty_level || testCase?.difficulty_level || 'N/A'}`,
        `測試時間: ${new Date().toLocaleString('zh-TW')}`,
        '',
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');

      // 下載 CSV
      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `version_comparison_${testCase.id}_${Date.now()}.csv`;
      link.click();
      URL.revokeObjectURL(url);

      message.success('結果已匯出');
    } catch (err) {
      message.error('匯出失敗: ' + err.message);
    }
  };

  /**
   * 獲取難度顏色
   */
  const getDifficultyColor = (difficulty) => {
    const colors = {
      'easy': 'green',
      'medium': 'orange',
      'hard': 'red'
    };
    return colors[difficulty] || 'default';
  };

  /**
   * 獲取指標顏色（根據數值）
   */
  const getMetricColor = (value, type = 'f1') => {
    if (type === 'recall') {
      return value >= 1.0 ? 'green' : 'orange';
    }
    // Precision 和 F1
    if (value > 0.3) return 'green';
    if (value > 0.1) return 'orange';
    return 'red';
  };

  /**
   * 表格欄位定義
   */
  const columns = [
    {
      title: '#',
      key: 'index',
      width: 50,
      render: (_, __, index) => index + 1,
      fixed: 'left'
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 250,
      fixed: 'left',
      render: (text, record) => (
        <Space>
          {record.status === 'success' ? (
            <CheckCircleOutlined style={{ color: '#52c41a' }} />
          ) : (
            <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
          )}
          <Text strong>{text}</Text>
          {summary?.best_version?.version_id === record.version_id && (
            <Tooltip title="最佳版本">
              <TrophyOutlined style={{ color: '#faad14' }} />
            </Tooltip>
          )}
        </Space>
      )
    },
    {
      title: '策略類型',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      width: 150,
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: 'Precision',
      key: 'precision',
      width: 110,
      sorter: (a, b) => a.metrics.precision - b.metrics.precision,
      render: (_, record) => {
        const value = record.metrics.precision;
        return (
          <Tag color={getMetricColor(value, 'precision')}>
            {(value * 100).toFixed(0)}%
          </Tag>
        );
      }
    },
    {
      title: 'Recall',
      key: 'recall',
      width: 100,
      sorter: (a, b) => a.metrics.recall - b.metrics.recall,
      render: (_, record) => {
        const value = record.metrics.recall;
        return (
          <Tag color={getMetricColor(value, 'recall')}>
            {(value * 100).toFixed(0)}%
          </Tag>
        );
      }
    },
    {
      title: 'F1 Score',
      key: 'f1_score',
      width: 110,
      defaultSortOrder: 'descend',
      sorter: (a, b) => a.metrics.f1_score - b.metrics.f1_score,
      render: (_, record) => {
        const value = record.metrics.f1_score;
        return (
          <Tag color={getMetricColor(value, 'f1')}>
            {(value * 100).toFixed(0)}%
          </Tag>
        );
      }
    },
    {
      title: '回應時間',
      dataIndex: 'response_time',
      key: 'response_time',
      width: 110,
      sorter: (a, b) => a.response_time - b.response_time,
      render: (time) => `${time.toFixed(2)}s`
    },
    {
      title: '匹配關鍵字',
      key: 'matched',
      width: 120,
      render: (_, record) => {
        if (record.status !== 'success') return '-';
        const matched = record.matched_keywords?.length || 0;
        const total = record.total_keywords || 0;
        return (
          <Tooltip title={`匹配: ${record.matched_keywords?.join(', ') || '無'}`}>
            <Text>{matched} / {total}</Text>
          </Tooltip>
        );
      }
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      filters: [
        { text: '成功', value: 'success' },
        { text: '失敗', value: 'error' }
      ],
      onFilter: (value, record) => record.status === value,
      render: (status, record) => {
        if (status === 'success') {
          return <Tag color="success">成功</Tag>;
        }
        return (
          <Tooltip title={record.error_message}>
            <Tag color="error">失敗</Tag>
          </Tooltip>
        );
      }
    }
  ];

  return (
    <Modal
      title={
        <Space>
          <ExperimentOutlined style={{ fontSize: '20px', color: '#1890ff' }} />
          <Text strong style={{ fontSize: '16px' }}>
            版本比較測試 - {testCase?.question?.substring(0, 50)}...
          </Text>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="90%"
      style={{ top: 20 }}
      footer={[
        <Button key="export" icon={<DownloadOutlined />} onClick={handleExport} disabled={!results.length}>
          匯出結果
        </Button>,
        <Button 
          key="retest" 
          icon={<ReloadOutlined />} 
          onClick={handleRetest} 
          disabled={loading}
        >
          重新測試
        </Button>,
        <Button key="close" type="primary" icon={<CloseOutlined />} onClick={onClose}>
          關閉
        </Button>
      ]}
    >
      {/* 錯誤訊息 */}
      {error && (
        <Alert
          message="測試失敗"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 測試資訊卡片 */}
      <Card 
        size="small" 
        style={{ marginBottom: 16 }}
        title={<Text strong>📊 測試資訊</Text>}
      >
        <Row gutter={16}>
          <Col span={18}>
            <Paragraph style={{ marginBottom: 8 }}>
              <Text strong>問題：</Text>
              <Text>{testCaseInfo?.question || testCase?.question}</Text>
            </Paragraph>
            <Space size="large">
              <span>
                <Text strong>難度：</Text>
                <Tag color={getDifficultyColor(testCaseInfo?.difficulty_level || testCase?.difficulty_level)}>
                  {testCaseInfo?.difficulty_level || testCase?.difficulty_level || 'N/A'}
                </Tag>
              </span>
              <span>
                <Text strong>答案關鍵字：</Text>
                {(testCaseInfo?.expected_keywords || testCase?.expected_keywords || []).map((keyword, idx) => (
                  <Tag key={idx} color="blue">{keyword}</Tag>
                ))}
              </span>
            </Space>
          </Col>
          <Col span={6}>
            {summary && (
              <Space direction="vertical" style={{ width: '100%' }}>
                <Statistic
                  title="平均回應時間"
                  value={summary.avg_response_time}
                  suffix="秒"
                  prefix={<ThunderboltOutlined />}
                  valueStyle={{ fontSize: '20px' }}
                />
              </Space>
            )}
          </Col>
        </Row>
      </Card>

      {/* 進度條 */}
      {loading && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>⏳ 測試進度</Text>
            <Progress
              percent={progress}
              status={loading ? 'active' : 'success'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068',
              }}
            />
            <Text type="secondary">
              {loading ? '正在執行測試，請稍候...' : '測試完成！'}
            </Text>
          </Space>
        </Card>
      )}

      {/* 摘要統計 */}
      {summary && !loading && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="測試版本數"
                value={summary.total_versions}
                suffix="個"
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="成功測試"
                value={summary.successful_tests}
                suffix={`/ ${summary.total_versions}`}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="總執行時間"
                value={summary.total_execution_time}
                suffix="秒"
                valueStyle={{ color: '#faad14' }}
                prefix={<ThunderboltOutlined />}
              />
            </Col>
            <Col span={6}>
              {summary.best_version && (
                <Statistic
                  title="最佳版本"
                  value={summary.best_version.version_name}
                  valueStyle={{ fontSize: '14px', color: '#fa8c16' }}
                  prefix={<TrophyOutlined />}
                />
              )}
            </Col>
          </Row>
        </Card>
      )}

      {/* 結果表格 */}
      <Card 
        size="small"
        title={<Text strong>📋 測試結果</Text>}
        bodyStyle={{ padding: '12px' }}
      >
        {loading && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在執行測試..." />
          </div>
        )}

        {!loading && results.length === 0 && (
          <Empty
            description="尚無測試結果"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}

        {!loading && results.length > 0 && (
          <Table
            columns={columns}
            dataSource={results}
            rowKey="version_id"
            pagination={false}
            scroll={{ x: 1200, y: 400 }}
            size="small"
            bordered
          />
        )}
      </Card>
    </Modal>
  );
};

export default VersionComparisonModal;
