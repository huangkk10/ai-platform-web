/**
 * 選擇版本跑分 Modal
 * ====================
 * 
 * 功能：讓用戶選擇特定版本，對單一測試案例執行多執行緒跑分
 * 
 * 使用場景：
 * - 需要針對性測試特定版本
 * - 快速驗證某些版本的效能
 * - 使用多執行緒加速測試
 * 
 * 特色：
 * - 支援多選版本
 * - 可調整並行執行緒數
 * - 即時顯示測試進度和結果
 */

import React, { useState, useEffect } from 'react';
import {
  Modal,
  Card,
  Table,
  Checkbox,
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
  Alert,
  InputNumber,
  Divider,
  Progress
} from 'antd';
import {
  ThunderboltOutlined,
  DownloadOutlined,
  ReloadOutlined,
  CloseOutlined,
  TrophyOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  RocketOutlined,
  SettingOutlined
} from '@ant-design/icons';
import unifiedBenchmarkApi from '../../services/unifiedBenchmarkApi';
import * as difyBenchmarkApi from '../../services/difyBenchmarkApi';

const { Title, Text, Paragraph } = Typography;

/**
 * 選擇版本跑分 Modal 組件
 * 
 * Props:
 * - visible: boolean - 是否顯示 Modal
 * - onClose: function - 關閉 Modal 的回調
 * - testCase: object - 測試案例資料
 */
const SelectVersionTestModal = ({ visible, onClose, testCase }) => {
  // 版本選擇狀態
  const [versions, setVersions] = useState([]);
  const [selectedVersionIds, setSelectedVersionIds] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);
  
  // 設定狀態
  const [maxWorkers, setMaxWorkers] = useState(3);
  
  // 測試執行狀態
  const [testing, setTesting] = useState(false);
  const [results, setResults] = useState([]);
  const [summary, setSummary] = useState(null);
  const [testCaseInfo, setTestCaseInfo] = useState(null);
  const [error, setError] = useState(null);
  
  // 顯示模式：'select' | 'results'
  const [viewMode, setViewMode] = useState('select');

  // 當 Modal 打開時，載入版本列表
  useEffect(() => {
    if (visible) {
      loadVersions();
      resetState();
    }
  }, [visible]);

  /**
   * 重置狀態
   */
  const resetState = () => {
    setSelectedVersionIds([]);
    setResults([]);
    setSummary(null);
    setTestCaseInfo(null);
    setError(null);
    setViewMode('select');
    setMaxWorkers(3);
  };

  /**
   * 載入可用的版本列表
   */
  const loadVersions = async () => {
    setLoadingVersions(true);
    try {
      const response = await unifiedBenchmarkApi.getVersions();
      // 處理 DRF 分頁格式（{count, results}）或直接的陣列格式
      const responseData = response.data;
      let versionList = [];
      
      if (Array.isArray(responseData)) {
        // 直接陣列格式
        versionList = responseData;
      } else if (responseData && Array.isArray(responseData.results)) {
        // DRF 分頁格式
        versionList = responseData.results;
      } else if (responseData && typeof responseData === 'object') {
        // 其他物件格式，嘗試取得 results 或轉換為陣列
        versionList = responseData.results || Object.values(responseData);
      }
      
      const activeVersions = versionList.filter(v => v && v.is_active);
      setVersions(activeVersions);
      
      if (activeVersions.length === 0) {
        message.warning('沒有可用的測試版本');
      }
    } catch (err) {
      console.error('載入版本失敗:', err);
      message.error('載入版本列表失敗');
      setVersions([]);
    } finally {
      setLoadingVersions(false);
    }
  };

  /**
   * 處理版本選擇變更
   */
  const handleVersionSelect = (versionId, checked) => {
    if (checked) {
      setSelectedVersionIds(prev => [...prev, versionId]);
    } else {
      setSelectedVersionIds(prev => prev.filter(id => id !== versionId));
    }
  };

  /**
   * 全選/取消全選
   */
  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedVersionIds(versions.map(v => v.id));
    } else {
      setSelectedVersionIds([]);
    }
  };

  /**
   * 開始測試
   */
  const startTest = async () => {
    if (selectedVersionIds.length === 0) {
      message.warning('請至少選擇一個版本');
      return;
    }

    if (!testCase || !testCase.id) {
      message.error('無效的測試案例');
      return;
    }

    setTesting(true);
    setError(null);
    setResults([]);
    setViewMode('results');

    try {
      // 根據測試案例類型選擇 API
      // VSA 測試案例會有 answer_keywords 或 expected_answer 欄位
      // 或者判斷是否有 test_type 欄位為 'vsa'
      const isVsaTestCase = testCase.test_type === 'vsa' || 
                           testCase.answer_keywords !== undefined || 
                           testCase.expected_answer !== undefined;
      
      let response;
      if (isVsaTestCase) {
        // VSA 測試案例：使用 Dify Benchmark API
        response = await difyBenchmarkApi.selectedVersionTest(testCase.id, {
          version_ids: selectedVersionIds,
          max_workers: maxWorkers
        });
      } else {
        // Protocol 測試案例：使用 Unified Benchmark API
        response = await unifiedBenchmarkApi.selectedVersionTest(testCase.id, {
          version_ids: selectedVersionIds,
          max_workers: maxWorkers
        });
      }

      if (response.data.success) {
        setTestCaseInfo(response.data.test_case);
        setResults(response.data.results);
        setSummary(response.data.summary);
        
        message.success(`測試完成！共測試 ${response.data.results.length} 個版本`);
      } else {
        throw new Error(response.data.error || '測試失敗');
      }

    } catch (err) {
      const errorMsg = err.response?.data?.error || err.message || '測試執行失敗';
      setError(errorMsg);
      message.error(errorMsg);
      console.error('選擇版本測試失敗:', err);
    } finally {
      setTesting(false);
    }
  };

  /**
   * 返回選擇頁面
   */
  const backToSelect = () => {
    setViewMode('select');
    setResults([]);
    setSummary(null);
    setError(null);
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
        `並行數: ${summary?.max_workers_used || maxWorkers}`,
        `測試時間: ${new Date().toLocaleString('zh-TW')}`,
        '',
        headers.join(','),
        ...rows.map(row => row.join(','))
      ].join('\n');

      const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `selected_version_test_${testCase.id}_${Date.now()}.csv`;
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
   * 獲取指標顏色
   */
  const getMetricColor = (value, type = 'f1') => {
    if (type === 'recall') {
      return value >= 1.0 ? 'green' : 'orange';
    }
    if (value > 0.3) return 'green';
    if (value > 0.1) return 'orange';
    return 'red';
  };

  /**
   * 版本選擇表格欄位
   */
  const versionColumns = [
    {
      title: (
        <Checkbox
          checked={selectedVersionIds.length === versions.length && versions.length > 0}
          indeterminate={selectedVersionIds.length > 0 && selectedVersionIds.length < versions.length}
          onChange={(e) => handleSelectAll(e.target.checked)}
        >
          全選
        </Checkbox>
      ),
      key: 'select',
      width: 80,
      render: (_, record) => (
        <Checkbox
          checked={selectedVersionIds.includes(record.id)}
          onChange={(e) => handleVersionSelect(record.id, e.target.checked)}
        />
      )
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      render: (text, record) => (
        <Space>
          <Text strong>{text}</Text>
          {record.is_baseline && <Tag color="gold">基準</Tag>}
        </Space>
      )
    },
    {
      title: '策略類型',
      key: 'strategy_type',
      render: (_, record) => {
        // DifyConfigVersion 使用 retrieval_mode 或 rag_settings 中的策略
        const strategy = record.retrieval_mode || 
                        record.rag_settings?.retrieval_strategy || 
                        record.version_code || 
                        '-';
        return <Tag color="blue">{strategy}</Tag>;
      }
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || '-'
    }
  ];

  /**
   * 結果表格欄位
   */
  const resultColumns = [
    {
      title: '#',
      key: 'index',
      width: 50,
      render: (_, __, index) => index + 1
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 220,
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
      title: '策略',
      dataIndex: 'strategy_type',
      key: 'strategy_type',
      width: 130,
      render: (text) => <Tag color="blue">{text}</Tag>
    },
    {
      title: 'Precision',
      key: 'precision',
      width: 100,
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
      width: 90,
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
      width: 100,
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
      title: '耗時',
      dataIndex: 'response_time',
      key: 'response_time',
      width: 90,
      sorter: (a, b) => a.response_time - b.response_time,
      render: (time) => `${time.toFixed(2)}s`
    },
    {
      title: '狀態',
      dataIndex: 'status',
      key: 'status',
      width: 70,
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

  // 渲染版本選擇視圖
  const renderSelectView = () => (
    <>
      {/* 問題資訊 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={18}>
            <Paragraph style={{ marginBottom: 8 }}>
              <Text strong>問題：</Text>
              <Text>{testCase?.question}</Text>
            </Paragraph>
            <Space size="large">
              <span>
                <Text strong>難度：</Text>
                <Tag color={getDifficultyColor(testCase?.difficulty_level)}>
                  {testCase?.difficulty_level || 'N/A'}
                </Tag>
              </span>
              <span>
                <Text strong>ID：</Text>
                <Text>{testCase?.id}</Text>
              </span>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 版本選擇 */}
      <Card 
        size="small" 
        title={
          <Space>
            <Text strong>📋 選擇測試版本</Text>
            <Tag color="blue">{selectedVersionIds.length} / {versions.length} 已選</Tag>
          </Space>
        }
        style={{ marginBottom: 16 }}
      >
        {loadingVersions ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin tip="載入版本列表..." />
          </div>
        ) : versions.length === 0 ? (
          <Empty description="沒有可用的版本" />
        ) : (
          <Table
            columns={versionColumns}
            dataSource={versions}
            rowKey="id"
            pagination={false}
            scroll={{ y: 300 }}
            size="small"
          />
        )}
      </Card>

      {/* 執行設定 */}
      <Card size="small" title={<><SettingOutlined /> 執行設定</>}>
        <Space size="large">
          <span>
            <Text strong>並行執行緒數：</Text>
            <InputNumber
              min={1}
              max={5}
              value={maxWorkers}
              onChange={setMaxWorkers}
              style={{ width: 80, marginLeft: 8 }}
            />
            <Text type="secondary" style={{ marginLeft: 8 }}>（建議 1-5）</Text>
          </span>
        </Space>
      </Card>
    </>
  );

  // 渲染結果視圖
  const renderResultsView = () => (
    <>
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

      {/* 測試資訊 */}
      <Card size="small" style={{ marginBottom: 16 }}>
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
                <Text strong>並行數：</Text>
                <Tag color="purple">{summary?.max_workers_used || maxWorkers}</Tag>
              </span>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* 測試中提示 */}
      {testing && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text strong>⏳ 測試進度</Text>
            <Progress percent={100} status="active" strokeColor={{ '0%': '#108ee9', '100%': '#87d068' }} />
            <Text type="secondary">正在使用 {maxWorkers} 個執行緒並行測試，請稍候...</Text>
          </Space>
        </Card>
      )}

      {/* 摘要統計 */}
      {summary && !testing && (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={16}>
            <Col span={5}>
              <Statistic
                title="測試版本數"
                value={summary.total_versions}
                suffix="個"
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={5}>
              <Statistic
                title="成功測試"
                value={summary.successful_tests}
                suffix={`/ ${summary.total_versions}`}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={5}>
              <Statistic
                title="總執行時間"
                value={summary.total_execution_time}
                suffix="秒"
                valueStyle={{ color: '#faad14' }}
                prefix={<ThunderboltOutlined />}
              />
            </Col>
            <Col span={4}>
              <Statistic
                title="並行數"
                value={summary.max_workers_used}
                valueStyle={{ color: '#722ed1' }}
                prefix={<RocketOutlined />}
              />
            </Col>
            <Col span={5}>
              {summary.best_version && (
                <Statistic
                  title="最佳版本"
                  value={summary.best_version.version_name}
                  valueStyle={{ fontSize: '12px', color: '#fa8c16' }}
                  prefix={<TrophyOutlined />}
                />
              )}
            </Col>
          </Row>
        </Card>
      )}

      {/* 結果表格 */}
      <Card size="small" title={<Text strong>📋 測試結果</Text>} bodyStyle={{ padding: '12px' }}>
        {testing && (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" tip="正在執行多執行緒測試..." />
          </div>
        )}

        {!testing && results.length === 0 && !error && (
          <Empty description="尚無測試結果" image={Empty.PRESENTED_IMAGE_SIMPLE} />
        )}

        {!testing && results.length > 0 && (
          <Table
            columns={resultColumns}
            dataSource={results}
            rowKey="version_id"
            pagination={false}
            scroll={{ x: 900, y: 350 }}
            size="small"
            bordered
          />
        )}
      </Card>
    </>
  );

  return (
    <Modal
      title={
        <Space>
          <ThunderboltOutlined style={{ fontSize: '20px', color: '#722ed1' }} />
          <Text strong style={{ fontSize: '16px' }}>
            {viewMode === 'select' ? '選擇版本跑分' : '測試結果'} - {testCase?.question?.substring(0, 40)}...
          </Text>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      width="85%"
      style={{ top: 20 }}
      footer={viewMode === 'select' ? [
        <Button key="cancel" onClick={onClose}>
          取消
        </Button>,
        <Button
          key="start"
          type="primary"
          icon={<RocketOutlined />}
          onClick={startTest}
          disabled={selectedVersionIds.length === 0 || testing}
          loading={testing}
        >
          開始測試 ({selectedVersionIds.length} 個版本)
        </Button>
      ] : [
        <Button key="export" icon={<DownloadOutlined />} onClick={handleExport} disabled={!results.length}>
          匯出結果
        </Button>,
        <Button key="back" icon={<ReloadOutlined />} onClick={backToSelect} disabled={testing}>
          重新選擇
        </Button>,
        <Button key="close" type="primary" icon={<CloseOutlined />} onClick={onClose}>
          關閉
        </Button>
      ]}
    >
      {viewMode === 'select' ? renderSelectView() : renderResultsView()}
    </Modal>
  );
};

export default SelectVersionTestModal;
