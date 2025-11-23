/**
 * Test Cases 列表頁面
 * 
 * 功能：
 * - 顯示所有測試案例的完整列表
 * - 支援篩選（難度、測試類別）
 * - 支援搜尋（問題內容）
 * - 顯示案例詳細資訊
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Tag,
  Input,
  Select,
  Space,
  Button,
  Tooltip,
  Modal,
  Descriptions,
  message,
  Statistic,
  Row,
  Col,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  FileTextOutlined,
  EyeOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import * as benchmarkApi from '../../services/benchmarkApi';

const { Option } = Select;
const { TextArea } = Input;

const TestCasesListPage = () => {
  const [loading, setLoading] = useState(false);
  const [testCases, setTestCases] = useState([]);
  const [filteredTestCases, setFilteredTestCases] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState([]);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState(null);

  // 統計資料
  const [statistics, setStatistics] = useState({
    total: 0,
    easy: 0,
    medium: 0,
    hard: 0,
    categories: 0,
  });

  // 載入測試案例
  const loadTestCases = async () => {
    setLoading(true);
    try {
      // 請求所有測試案例（設置大的 page_size）
      const response = await benchmarkApi.getTestCases({ page_size: 1000 });
      
      // 處理資料格式：可能是 {results: [...]} 或直接是 [...]
      let cases = [];
      if (response.data) {
        if (Array.isArray(response.data)) {
          cases = response.data;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          cases = response.data.results;
        } else if (typeof response.data === 'object') {
          // 如果是物件但不是陣列，可能需要轉換
          console.warn('API 返回的資料格式:', response.data);
          cases = [];
        }
      }
      
      setTestCases(cases);
      setFilteredTestCases(cases);

      // 提取所有類別
      const uniqueCategories = [...new Set(cases.map(c => c.test_class_name).filter(Boolean))];
      setCategories(uniqueCategories);

      // 計算統計
      const stats = {
        total: cases.length,
        easy: cases.filter(c => c.difficulty_level === 'easy').length,
        medium: cases.filter(c => c.difficulty_level === 'medium').length,
        hard: cases.filter(c => c.difficulty_level === 'hard').length,
        categories: uniqueCategories.length,
      };
      setStatistics(stats);

      if (cases.length > 0) {
        message.success(`成功載入 ${cases.length} 個測試案例`);
      } else {
        message.info('目前沒有測試案例');
      }
    } catch (error) {
      console.error('載入測試案例失敗:', error);
      
      // 更詳細的錯誤訊息
      if (error.response) {
        if (error.response.status === 401 || error.response.status === 403) {
          message.error('您沒有權限訪問此功能，請聯繫管理員');
        } else {
          message.error(`載入失敗 (${error.response.status}): ${error.response.data?.detail || '未知錯誤'}`);
        }
      } else if (error.request) {
        message.error('網路連接失敗，請檢查網路連接');
      } else {
        message.error(`載入測試案例失敗: ${error.message || '未知錯誤'}`);
      }
      
      // 設置空陣列避免後續錯誤
      setTestCases([]);
      setFilteredTestCases([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTestCases();
  }, []);

  // 篩選和搜尋
  useEffect(() => {
    let filtered = [...testCases];

    // 難度篩選
    if (selectedDifficulty !== 'all') {
      filtered = filtered.filter(tc => tc.difficulty_level === selectedDifficulty);
    }

    // 類別篩選
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(tc => tc.test_class_name === selectedCategory);
    }

    // 搜尋
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(tc =>
        tc.question.toLowerCase().includes(searchLower) ||
        tc.test_class_name?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredTestCases(filtered);
  }, [testCases, searchText, selectedDifficulty, selectedCategory]);

  // 顯示詳細資訊
  const showDetail = (testCase) => {
    setSelectedTestCase(testCase);
    setDetailModalVisible(true);
  };

  // 難度標籤配色
  const getDifficultyTag = (difficulty) => {
    const config = {
      easy: { color: 'success', text: '簡單' },
      medium: { color: 'warning', text: '中等' },
      hard: { color: 'error', text: '困難' },
    };
    const { color, text } = config[difficulty] || { color: 'default', text: difficulty };
    return <Tag color={color}>{text}</Tag>;
  };

  // 表格欄位定義
  const columns = [
    {
      title: '#',
      dataIndex: 'id',
      key: 'id',
      width: 80,
      align: 'center',
      fixed: 'left',
      sorter: (a, b) => a.id - b.id,
      defaultSortOrder: 'ascend',
    },
    {
      title: '問題',
      dataIndex: 'question',
      key: 'question',
      width: 400,
      ellipsis: {
        showTitle: false,
      },
      render: (text) => (
        <Tooltip placement="topLeft" title={text}>
          {text}
        </Tooltip>
      ),
    },
    {
      title: '測試類別',
      dataIndex: 'test_class_name',
      key: 'test_class_name',
      width: 150,
      filters: categories.map(cat => ({ text: cat, value: cat })),
      onFilter: (value, record) => record.test_class_name === value,
      render: (text) => <Tag color="blue">{text}</Tag>,
    },
    {
      title: '難度',
      dataIndex: 'difficulty_level',
      key: 'difficulty_level',
      width: 100,
      align: 'center',
      filters: [
        { text: '簡單', value: 'easy' },
        { text: '中等', value: 'medium' },
        { text: '困難', value: 'hard' },
      ],
      onFilter: (value, record) => record.difficulty_level === value,
      render: (difficulty) => getDifficultyTag(difficulty),
    },
    {
      title: '題型',
      dataIndex: 'question_type',
      key: 'question_type',
      width: 120,
      render: (type) => {
        const typeMap = {
          'single_answer': '單一答案',
          'multiple_answers': '多重答案',
          'open_ended': '開放式',
        };
        return <Tag>{typeMap[type] || type}</Tag>;
      },
    },
    {
      title: '期望文檔數',
      dataIndex: 'expected_document_ids',
      key: 'expected_document_count',
      width: 120,
      align: 'center',
      render: (ids) => (
        <Tag color="cyan">{Array.isArray(ids) ? ids.length : 0} 個</Tag>
      ),
    },
    {
      title: '最少匹配數',
      dataIndex: 'min_required_matches',
      key: 'min_required_matches',
      width: 120,
      align: 'center',
      render: (count) => <Tag color="orange">{count}</Tag>,
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      align: 'center',
      filters: [
        { text: '啟用', value: true },
        { text: '停用', value: false },
      ],
      onFilter: (value, record) => record.is_active === value,
      render: (isActive) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? '啟用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 100,
      align: 'center',
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          <Tooltip title="查看詳情">
            <Button
              type="link"
              icon={<EyeOutlined />}
              onClick={() => showDetail(record)}
              size="small"
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 統計卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="總測試案例"
              value={statistics.total}
              prefix={<FileTextOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="測試類別"
              value={statistics.categories}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="簡單題"
              value={statistics.easy}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="困難題"
              value={statistics.hard}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要內容 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>測試案例列表</span>
          </Space>
        }
        extra={
          <Space>
            <Input
              placeholder="搜尋問題內容..."
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 250 }}
              allowClear
            />
            <Select
              value={selectedDifficulty}
              onChange={setSelectedDifficulty}
              style={{ width: 120 }}
            >
              <Option value="all">所有難度</Option>
              <Option value="easy">簡單</Option>
              <Option value="medium">中等</Option>
              <Option value="hard">困難</Option>
            </Select>
            <Select
              value={selectedCategory}
              onChange={setSelectedCategory}
              style={{ width: 180 }}
            >
              <Option value="all">所有類別</Option>
              {categories.map(cat => (
                <Option key={cat} value={cat}>{cat}</Option>
              ))}
            </Select>
            <Button
              icon={<ReloadOutlined />}
              onClick={loadTestCases}
              loading={loading}
            >
              重新整理
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={filteredTestCases}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
            defaultPageSize: 20,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          scroll={{ x: 1400, y: 'calc(100vh - 400px)' }}
        />
      </Card>

      {/* 詳細資訊 Modal */}
      <Modal
        title={
          <Space>
            <InfoCircleOutlined />
            <span>測試案例詳細資訊</span>
          </Space>
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            關閉
          </Button>,
        ]}
        width={800}
      >
        {selectedTestCase && (
          <Descriptions bordered column={1}>
            <Descriptions.Item label="案例 ID">
              {selectedTestCase.id}
            </Descriptions.Item>
            <Descriptions.Item label="問題">
              {selectedTestCase.question}
            </Descriptions.Item>
            <Descriptions.Item label="測試類別">
              <Tag color="blue">{selectedTestCase.test_class_name}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="難度">
              {getDifficultyTag(selectedTestCase.difficulty_level)}
            </Descriptions.Item>
            <Descriptions.Item label="題型">
              <Tag>{selectedTestCase.question_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="期望文檔 ID">
              <Space wrap>
                {Array.isArray(selectedTestCase.expected_document_ids) &&
                  selectedTestCase.expected_document_ids.map((id) => (
                    <Tag key={id} color="cyan">
                      {id}
                    </Tag>
                  ))}
              </Space>
            </Descriptions.Item>
            <Descriptions.Item label="最少匹配數">
              <Tag color="orange">{selectedTestCase.min_required_matches}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="狀態">
              <Tag color={selectedTestCase.is_active ? 'success' : 'default'}>
                {selectedTestCase.is_active ? '啟用' : '停用'}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="建立時間">
              {new Date(selectedTestCase.created_at).toLocaleString('zh-TW')}
            </Descriptions.Item>
            {selectedTestCase.updated_at && (
              <Descriptions.Item label="更新時間">
                {new Date(selectedTestCase.updated_at).toLocaleString('zh-TW')}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default TestCasesListPage;
