/**
 * 批量測試歷史記錄頁面
 * 
 * 功能：
 * - 查看所有批量測試記錄
 * - 按日期、batch_id、狀態篩選
 * - 快速跳轉到對比頁面
 */

import React, { useState, useEffect } from 'react';
import { 
  Table, 
  Card, 
  Button, 
  Space, 
  Tag, 
  message,
  Input,
  DatePicker,
  Tooltip,
  Typography
} from 'antd';
import { 
  EyeOutlined, 
  ReloadOutlined,
  SearchOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import benchmarkApi from '../../services/benchmarkApi';
import './BatchTestHistoryPage.css';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const BatchTestHistoryPage = () => {
  const navigate = useNavigate();
  
  const [loading, setLoading] = useState(false);
  const [testRuns, setTestRuns] = useState([]);
  const [batchGroups, setBatchGroups] = useState([]);
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    loadBatchTestHistory();
  }, []);

  const loadBatchTestHistory = async () => {
    setLoading(true);
    try {
      const response = await benchmarkApi.getTestRuns({
        run_type: 'batch_comparison',
      });

      const runs = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.results || []);

      console.log('📜 載入批量測試歷史:', runs.length, '筆記錄');

      // 按 batch_id 分組
      const grouped = groupByBatchId(runs);
      setBatchGroups(grouped);
      setTestRuns(runs);

    } catch (error) {
      console.error('載入批量測試歷史失敗:', error);
      message.error('載入批量測試歷史失敗');
    } finally {
      setLoading(false);
    }
  };

  // 按 batch_id 分組測試執行
  const groupByBatchId = (runs) => {
    const groups = {};

    runs.forEach(run => {
      // 從 notes 中提取 batch_id
      const match = run.notes?.match(/批次 ID:\s*(\S+)/);
      if (match) {
        const batchId = match[1];
        if (!groups[batchId]) {
          groups[batchId] = {
            batch_id: batchId,
            runs: [],
            created_at: run.created_at,
            total_versions: 0,
            avg_score: 0,
            best_version: null,
          };
        }
        groups[batchId].runs.push(run);
      }
    });

    // 計算統計資料
    Object.values(groups).forEach(group => {
      group.total_versions = group.runs.length;
      
      const scores = group.runs.map(r => parseFloat(r.overall_score) || 0);
      group.avg_score = scores.reduce((a, b) => a + b, 0) / scores.length;
      
      // 找出最佳版本
      const bestRun = group.runs.reduce((best, run) => {
        const bestScore = parseFloat(best.overall_score) || 0;
        const runScore = parseFloat(run.overall_score) || 0;
        return runScore > bestScore ? run : best;
      });
      
      group.best_version = {
        name: bestRun.version?.version_name || bestRun.version_name,
        score: parseFloat(bestRun.overall_score) || 0,
      };
    });

    // 轉換為陣列並按時間排序
    return Object.values(groups).sort((a, b) => 
      new Date(b.created_at) - new Date(a.created_at)
    );
  };

  // 表格欄位定義
  const columns = [
    {
      title: '批次 ID',
      dataIndex: 'batch_id',
      key: 'batch_id',
      width: 200,
      render: (batchId) => (
        <Text code copyable>{batchId}</Text>
      ),
      filteredValue: searchText ? [searchText] : null,
      onFilter: (value, record) => 
        record.batch_id.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: '測試時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => new Date(date).toLocaleString('zh-TW'),
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
    },
    {
      title: '測試版本數',
      dataIndex: 'total_versions',
      key: 'total_versions',
      width: 120,
      align: 'center',
      render: (count) => <Tag color="blue">{count} 個版本</Tag>,
    },
    {
      title: '平均分數',
      dataIndex: 'avg_score',
      key: 'avg_score',
      width: 120,
      align: 'center',
      render: (score) => (
        <Text strong style={{ color: getScoreColor(score) }}>
          {score.toFixed(2)}
        </Text>
      ),
      sorter: (a, b) => a.avg_score - b.avg_score,
    },
    {
      title: '最佳版本',
      dataIndex: 'best_version',
      key: 'best_version',
      width: 200,
      render: (best) => (
        <Space direction="vertical" size={0}>
          <Text>{best.name}</Text>
          <Text type="secondary" style={{ fontSize: '12px' }}>
            分數: {best.score.toFixed(2)}
          </Text>
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Tooltip title="查看對比結果">
            <Button
              type="primary"
              icon={<BarChartOutlined />}
              size="small"
              onClick={() => navigate(`/benchmark/comparison/${record.batch_id}`)}
            >
              查看對比
            </Button>
          </Tooltip>
        </Space>
      ),
    },
  ];

  // 根據分數返回顏色
  const getScoreColor = (score) => {
    if (score >= 0.8) return '#52c41a';
    if (score >= 0.6) return '#faad14';
    return '#ff4d4f';
  };

  return (
    <div className="batch-test-history-page">
      <Card 
        title={
          <Space>
            <BarChartOutlined />
            <span>批量測試歷史記錄</span>
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="搜尋 Batch ID"
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 200 }}
              allowClear
            />
            <Button 
              icon={<ReloadOutlined />} 
              onClick={loadBatchTestHistory}
            >
              重新整理
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={batchGroups}
          rowKey="batch_id"
          loading={loading}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 個批量測試`,
          }}
          scroll={{ x: 1200 }}
        />
      </Card>
    </div>
  );
};

export default BatchTestHistoryPage;
