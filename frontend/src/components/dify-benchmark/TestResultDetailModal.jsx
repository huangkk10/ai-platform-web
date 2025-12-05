/**
 * 測試結果詳情 Modal
 * 
 * 功能：
 * 1. 顯示測試執行的每題詳細結果
 * 2. 展示 AI 回覆內容、預期答案、評分詳情
 * 3. 支援搜尋和篩選（通過/失敗）
 * 4. 可展開/收合查看每題詳細資訊
 */

import React, { useState, useEffect, useMemo } from 'react';
import {
  Modal,
  Table,
  Card,
  Row,
  Col,
  Statistic,
  Tag,
  Space,
  Input,
  Select,
  Typography,
  Spin,
  Empty,
  message,
  Descriptions,
  Divider,
  Tooltip
} from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SearchOutlined,
  ClockCircleOutlined,
  FileTextOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Text, Paragraph } = Typography;
const { Option } = Select;

/**
 * 測試結果詳情 Modal
 * @param {boolean} visible - Modal 是否顯示
 * @param {number} testRunId - 測試執行 ID
 * @param {string} testRunName - 測試執行名稱
 * @param {function} onClose - 關閉 Modal 回調
 */
const TestResultDetailModal = ({ visible, testRunId, testRunName, onClose }) => {
  // State
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [testRunInfo, setTestRunInfo] = useState(null);
  const [searchText, setSearchText] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [expandedRowKeys, setExpandedRowKeys] = useState([]);

  // 載入測試結果
  useEffect(() => {
    if (visible && testRunId) {
      loadTestResults();
    }
  }, [visible, testRunId]);

  // 重置狀態
  useEffect(() => {
    if (!visible) {
      setSearchText('');
      setStatusFilter('all');
      setExpandedRowKeys([]);
    }
  }, [visible]);

  const loadTestResults = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/dify-benchmark/test-runs/${testRunId}/results/`, {
        withCredentials: true
      });

      const data = response.data;
      setResults(data.results || []);
      setTestRunInfo({
        id: data.test_run_id,
        name: data.test_run_name,
        totalResults: data.total_results
      });

    } catch (error) {
      console.error('Error loading test results:', error);
      message.error('載入測試結果失敗：' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  // 計算統計資料
  const statistics = useMemo(() => {
    if (!results.length) {
      return { total: 0, passed: 0, failed: 0, passRate: 0, avgScore: 0 };
    }

    const total = results.length;
    const passed = results.filter(r => r.is_passed).length;
    const failed = total - passed;
    const passRate = total > 0 ? (passed / total * 100) : 0;
    
    const validScores = results.filter(r => r.score !== null && r.score !== undefined);
    const avgScore = validScores.length > 0
      ? validScores.reduce((sum, r) => sum + parseFloat(r.score), 0) / validScores.length
      : 0;

    return { total, passed, failed, passRate, avgScore };
  }, [results]);

  // 篩選資料
  const filteredResults = useMemo(() => {
    return results.filter(result => {
      // 搜尋過濾
      if (searchText) {
        const searchLower = searchText.toLowerCase();
        const questionMatch = result.test_case_question?.toLowerCase().includes(searchLower);
        const answerMatch = result.dify_answer?.toLowerCase().includes(searchLower);
        if (!questionMatch && !answerMatch) {
          return false;
        }
      }

      // 狀態過濾
      if (statusFilter === 'passed' && !result.is_passed) {
        return false;
      }
      if (statusFilter === 'failed' && result.is_passed) {
        return false;
      }

      return true;
    });
  }, [results, searchText, statusFilter]);

  // 獲取分數顏色
  const getScoreColor = (score) => {
    if (score === null || score === undefined) return '#999';
    const numScore = parseFloat(score);
    if (numScore >= 80) return '#52c41a';
    if (numScore >= 60) return '#faad14';
    return '#ff4d4f';
  };

  // 展開行的渲染
  const expandedRowRender = (record) => {
    return (
      <Card size="small" style={{ margin: '8px 0' }}>
        <Descriptions column={1} size="small" bordered>
          <Descriptions.Item 
            label={<><FileTextOutlined /> 問題</>}
            labelStyle={{ width: '120px', fontWeight: 'bold' }}
          >
            <Text>{record.test_case_question}</Text>
          </Descriptions.Item>
          
          <Descriptions.Item 
            label={<><FileTextOutlined /> 預期答案</>}
            labelStyle={{ width: '120px', fontWeight: 'bold' }}
          >
            <Paragraph 
              style={{ margin: 0, whiteSpace: 'pre-wrap' }}
              ellipsis={{ rows: 5, expandable: true, symbol: '展開更多' }}
            >
              {record.test_case_expected_answer || '無預期答案'}
            </Paragraph>
          </Descriptions.Item>
          
          <Descriptions.Item 
            label={<><span role="img" aria-label="robot">🤖</span> AI 回覆</>}
            labelStyle={{ width: '120px', fontWeight: 'bold' }}
          >
            <Paragraph 
              style={{ margin: 0, whiteSpace: 'pre-wrap' }}
              ellipsis={{ rows: 10, expandable: true, symbol: '展開更多' }}
            >
              {record.dify_answer || '無回覆'}
            </Paragraph>
          </Descriptions.Item>
        </Descriptions>

        <Divider style={{ margin: '12px 0' }} />

        {/* 評分詳情 */}
        <Row gutter={16}>
          <Col span={6}>
            <Statistic 
              title="完整性" 
              value={record.completeness_score ?? '-'} 
              precision={2}
              valueStyle={{ fontSize: '16px', color: getScoreColor(record.completeness_score) }}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="準確性" 
              value={record.accuracy_score ?? '-'} 
              precision={2}
              valueStyle={{ fontSize: '16px', color: getScoreColor(record.accuracy_score) }}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="相關性" 
              value={record.relevance_score ?? '-'} 
              precision={2}
              valueStyle={{ fontSize: '16px', color: getScoreColor(record.relevance_score) }}
            />
          </Col>
          <Col span={6}>
            <Statistic 
              title="響應時間" 
              value={record.response_time ? `${parseFloat(record.response_time).toFixed(2)}s` : '-'} 
              valueStyle={{ fontSize: '16px' }}
              prefix={<ClockCircleOutlined />}
            />
          </Col>
        </Row>

        {/* 關鍵字匹配 */}
        {(record.matched_keywords?.length > 0 || record.missing_keywords?.length > 0) && (
          <>
            <Divider style={{ margin: '12px 0' }} />
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              {record.matched_keywords?.length > 0 && (
                <div>
                  <Text type="secondary">✅ 匹配關鍵字：</Text>
                  <Space wrap style={{ marginLeft: '8px' }}>
                    {record.matched_keywords.map((keyword, index) => (
                      <Tag key={index} color="success">{keyword}</Tag>
                    ))}
                  </Space>
                </div>
              )}
              {record.missing_keywords?.length > 0 && (
                <div>
                  <Text type="secondary">❌ 缺失關鍵字：</Text>
                  <Space wrap style={{ marginLeft: '8px' }}>
                    {record.missing_keywords.map((keyword, index) => (
                      <Tag key={index} color="error">{keyword}</Tag>
                    ))}
                  </Space>
                </div>
              )}
            </Space>
          </>
        )}
      </Card>
    );
  };

  // 表格欄位定義
  const columns = [
    {
      title: '#',
      dataIndex: 'index',
      key: 'index',
      width: 60,
      align: 'center',
      render: (_, __, index) => index + 1,
    },
    {
      title: '問題',
      dataIndex: 'test_case_question',
      key: 'test_case_question',
      ellipsis: {
        showTitle: false,
      },
      render: (text) => (
        <Tooltip title={text} placement="topLeft">
          <Text>{text}</Text>
        </Tooltip>
      ),
    },
    {
      title: '分數',
      dataIndex: 'score',
      key: 'score',
      width: 100,
      align: 'center',
      sorter: (a, b) => (parseFloat(a.score) || 0) - (parseFloat(b.score) || 0),
      render: (score) => {
        const numScore = parseFloat(score);
        return (
          <Text strong style={{ color: getScoreColor(numScore), fontSize: '14px' }}>
            {!isNaN(numScore) ? numScore.toFixed(2) : 'N/A'}
          </Text>
        );
      },
    },
    {
      title: '狀態',
      dataIndex: 'is_passed',
      key: 'is_passed',
      width: 80,
      align: 'center',
      render: (isPassed) => (
        isPassed ? (
          <Tag icon={<CheckCircleOutlined />} color="success">通過</Tag>
        ) : (
          <Tag icon={<CloseCircleOutlined />} color="error">失敗</Tag>
        )
      ),
    },
    {
      title: '響應時間',
      dataIndex: 'response_time',
      key: 'response_time',
      width: 100,
      align: 'center',
      sorter: (a, b) => (parseFloat(a.response_time) || 0) - (parseFloat(b.response_time) || 0),
      render: (time) => {
        if (!time) return '-';
        return `${parseFloat(time).toFixed(2)}s`;
      },
    },
  ];

  return (
    <Modal
      title={
        <Space>
          <FileTextOutlined />
          <span>測試結果詳情</span>
          {testRunName && <Text type="secondary">- {testRunName}</Text>}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={1200}
      style={{ top: 20 }}
      destroyOnClose
    >
      <Spin spinning={loading}>
        {/* 統計摘要 */}
        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="總題數"
                value={statistics.total}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="通過"
                value={statistics.passed}
                valueStyle={{ color: '#52c41a' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={4}>
            <Card size="small">
              <Statistic
                title="失敗"
                value={statistics.failed}
                valueStyle={{ color: '#ff4d4f' }}
                prefix={<CloseCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="通過率"
                value={statistics.passRate.toFixed(1)}
                suffix="%"
                valueStyle={{ color: getScoreColor(statistics.passRate) }}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card size="small">
              <Statistic
                title="平均分數"
                value={statistics.avgScore.toFixed(2)}
                valueStyle={{ color: getScoreColor(statistics.avgScore) }}
              />
            </Card>
          </Col>
        </Row>

        {/* 搜尋和篩選 */}
        <Space style={{ marginBottom: '16px' }}>
          <Input
            placeholder="搜尋問題或回覆內容..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
            allowClear
          />
          <Select
            value={statusFilter}
            onChange={setStatusFilter}
            style={{ width: 120 }}
          >
            <Option value="all">全部</Option>
            <Option value="passed">✅ 通過</Option>
            <Option value="failed">❌ 失敗</Option>
          </Select>
          <Text type="secondary">
            顯示 {filteredResults.length} / {results.length} 筆
          </Text>
        </Space>

        {/* 結果表格 */}
        <Table
          columns={columns}
          dataSource={filteredResults}
          rowKey="id"
          expandable={{
            expandedRowRender,
            expandedRowKeys,
            onExpandedRowsChange: setExpandedRowKeys,
            expandRowByClick: true,
          }}
          pagination={{
            defaultPageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ y: 'calc(100vh - 500px)' }}
          locale={{
            emptyText: (
              <Empty
                description="無測試結果"
                image={Empty.PRESENTED_IMAGE_SIMPLE}
              />
            ),
          }}
          size="middle"
        />
      </Spin>
    </Modal>
  );
};

export default TestResultDetailModal;
