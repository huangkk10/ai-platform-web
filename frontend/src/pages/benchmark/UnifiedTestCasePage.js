/**
 * 統一測試案例管理頁面
 * 整合 Protocol Benchmark 和 VSA Test Case
 */

import React, { useState, useEffect } from 'react';
import {
  Tabs, Table, Button, Space, Tag, Tooltip, message, Modal, 
  Card, Statistic, Row, Col, Input, Select, Spin, Popconfirm
} from 'antd';
import {
  FileTextOutlined, RobotOutlined, PlusOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, ReloadOutlined, ExportOutlined,
  ImportOutlined, SearchOutlined, FilterOutlined
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import unifiedBenchmarkApi from '../../services/unifiedBenchmarkApi';
import './UnifiedTestCasePage.css';

const { TabPane } = Tabs;
const { Search } = Input;
const { Option } = Select;

const UnifiedTestCasePage = ({ defaultTab = 'protocol' }) => {
  const navigate = useNavigate();
  
  // State 管理
  const [activeTab, setActiveTab] = useState(defaultTab);
  const [testCases, setTestCases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState({});
  const [searchText, setSearchText] = useState('');
  const [filters, setFilters] = useState({
    difficulty_level: null,
    category: null,
    test_class_name: null,
    is_active: null,
  });
  
  // Modal 控制
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  
  // 分類列表
  const [categories, setCategories] = useState([]);
  const [testClasses, setTestClasses] = useState([]);

  // 載入測試案例
  const loadTestCases = async () => {
    setLoading(true);
    try {
      const params = {
        test_type: activeTab,
        search: searchText || undefined,
        ...filters,
      };
      
      // 移除 null 值
      Object.keys(params).forEach(key => {
        if (params[key] === null || params[key] === undefined) {
          delete params[key];
        }
      });
      
      const response = await unifiedBenchmarkApi.getTestCases(params);
      setTestCases(response.data.results || response.data);
      
    } catch (error) {
      console.error('載入測試案例失敗:', error);
      message.error('載入測試案例失敗');
    } finally {
      setLoading(false);
    }
  };

  // 載入統計資料
  const loadStatistics = async () => {
    try {
      const response = await unifiedBenchmarkApi.getStatistics(activeTab);
      setStatistics(response.data);
    } catch (error) {
      console.error('載入統計資料失敗:', error);
    }
  };

  // 載入分類列表
  const loadCategories = async () => {
    try {
      const response = await unifiedBenchmarkApi.getCategories(activeTab);
      setCategories(response.data || []);
    } catch (error) {
      console.error('載入分類失敗:', error);
    }
  };

  // 載入測試類別列表
  const loadTestClasses = async () => {
    try {
      const response = await unifiedBenchmarkApi.getTestClasses(activeTab);
      setTestClasses(response.data || []);
    } catch (error) {
      console.error('載入測試類別失敗:', error);
    }
  };

  // Tab 切換處理
  const handleTabChange = (key) => {
    setActiveTab(key);
    setSearchText('');
    setFilters({
      difficulty_level: null,
      category: null,
      test_class_name: null,
      is_active: null,
    });
  };

  // 查看詳情
  const handleViewDetail = (record) => {
    setSelectedCase(record);
    setDetailModalVisible(true);
  };

  // 編輯
  const handleEdit = (record) => {
    setSelectedCase(record);
    setEditModalVisible(true);
  };

  // 刪除
  const handleDelete = async (id) => {
    try {
      await unifiedBenchmarkApi.deleteTestCase(id);
      message.success('刪除成功');
      loadTestCases();
      loadStatistics();
    } catch (error) {
      console.error('刪除失敗:', error);
      message.error('刪除失敗');
    }
  };

  // 切換啟用狀態
  const handleToggleActive = async (id) => {
    try {
      await unifiedBenchmarkApi.toggleActive(id);
      message.success('狀態更新成功');
      loadTestCases();
      loadStatistics();
    } catch (error) {
      console.error('狀態更新失敗:', error);
      message.error('狀態更新失敗');
    }
  };

  // 批量匯出
  const handleExport = async () => {
    try {
      const response = await unifiedBenchmarkApi.bulkExport(activeTab);
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${activeTab}_test_cases_${new Date().getTime()}.json`;
      link.click();
      window.URL.revokeObjectURL(url);
      message.success('匯出成功');
    } catch (error) {
      console.error('匯出失敗:', error);
      message.error('匯出失敗');
    }
  };

  // 重新整理
  const handleRefresh = () => {
    loadTestCases();
    loadStatistics();
    loadCategories();
    loadTestClasses();
  };

  // 初始化和 Tab 切換時載入資料
  useEffect(() => {
    handleRefresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // 搜尋和篩選變化時重新載入
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTestCases();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText, filters]);

  // 動態欄位配置
  const getColumns = () => {
    // 共用欄位
    const baseColumns = [
      {
        title: 'ID',
        dataIndex: 'id',
        key: 'id',
        width: 80,
        fixed: 'left',
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
          <Tooltip title={text}>
            <span>{text}</span>
          </Tooltip>
        ),
      },
      {
        title: '測試類別',
        dataIndex: 'test_class_name',
        key: 'test_class_name',
        width: 150,
        filters: testClasses.map(tc => ({ text: tc, value: tc })),
        onFilter: (value, record) => record.test_class_name === value,
      },
      {
        title: '難度',
        dataIndex: 'difficulty_level',
        key: 'difficulty_level',
        width: 100,
        render: (level) => {
          const colorMap = {
            easy: 'green',
            medium: 'orange',
            hard: 'red',
          };
          const textMap = {
            easy: '簡單',
            medium: '中等',
            hard: '困難',
          };
          return <Tag color={colorMap[level]}>{textMap[level] || level}</Tag>;
        },
      },
      {
        title: '狀態',
        dataIndex: 'is_active',
        key: 'is_active',
        width: 100,
        render: (isActive) => (
          <Tag color={isActive ? 'success' : 'default'}>
            {isActive ? '啟用' : '停用'}
          </Tag>
        ),
      },
    ];

    // Protocol 專用欄位
    const protocolColumns = [
      {
        title: '關鍵字',
        dataIndex: 'expected_keywords',
        key: 'expected_keywords',
        width: 200,
        render: (keywords) => {
          if (!keywords || keywords.length === 0) return '-';
          const displayKeywords = keywords.slice(0, 3);
          const remaining = keywords.length - 3;
          return (
            <Space size={[0, 4]} wrap>
              {displayKeywords.map((kw, index) => (
                <Tag key={index} color="blue">{kw}</Tag>
              ))}
              {remaining > 0 && (
                <Tooltip title={keywords.slice(3).join(', ')}>
                  <Tag color="cyan">+{remaining}</Tag>
                </Tooltip>
              )}
            </Space>
          );
        },
      },
      {
        title: '判斷條件',
        key: 'criteria_summary',
        dataIndex: 'criteria_summary',
        width: 250,
        render: (summary) => (
          <Tooltip title={summary} placement="left">
            <Tag color="purple">{summary}</Tag>
          </Tooltip>
        ),
      },
    ];

    // VSA 專用欄位
    const vsaColumns = [
      {
        title: '標籤',
        dataIndex: 'tags',
        key: 'tags',
        width: 200,
        render: (tags) => {
          if (!tags || tags.length === 0) return '-';
          return (
            <Space size={[0, 4]} wrap>
              {tags.map((tag, index) => (
                <Tag key={index} color="blue">{tag}</Tag>
              ))}
            </Space>
          );
        },
      },
      {
        title: '滿分',
        dataIndex: 'max_score',
        key: 'max_score',
        width: 100,
        render: (score) => <Tag color="gold">{score}</Tag>,
      },
      {
        title: '創建時間',
        dataIndex: 'created_at',
        key: 'created_at',
        width: 180,
        render: (time) => time ? new Date(time).toLocaleString('zh-TW') : '-',
      },
    ];

    // 操作欄位（動態）
    const actionColumn = {
      title: '操作',
      key: 'actions',
      width: activeTab === 'protocol' ? 120 : 220,
      fixed: 'right',
      render: (_, record) => {
        if (activeTab === 'protocol') {
          // Protocol 模式：只有查看
          return (
            <Space>
              <Tooltip title="查看詳情">
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetail(record)}
                />
              </Tooltip>
            </Space>
          );
        } else {
          // VSA 模式：完整 CRUD
          return (
            <Space>
              <Tooltip title="查看詳情">
                <Button
                  type="link"
                  icon={<EyeOutlined />}
                  onClick={() => handleViewDetail(record)}
                />
              </Tooltip>
              <Tooltip title="編輯">
                <Button
                  type="link"
                  icon={<EditOutlined />}
                  onClick={() => handleEdit(record)}
                />
              </Tooltip>
              <Tooltip title={record.is_active ? '停用' : '啟用'}>
                <Button
                  type="link"
                  onClick={() => handleToggleActive(record.id)}
                >
                  {record.is_active ? '停用' : '啟用'}
                </Button>
              </Tooltip>
              <Popconfirm
                title="確定要刪除此測試案例嗎？"
                onConfirm={() => handleDelete(record.id)}
                okText="確定"
                cancelText="取消"
              >
                <Tooltip title="刪除">
                  <Button
                    type="link"
                    danger
                    icon={<DeleteOutlined />}
                  />
                </Tooltip>
              </Popconfirm>
            </Space>
          );
        }
      },
    };

    // 根據測試類型組合欄位
    if (activeTab === 'protocol') {
      return [...baseColumns, ...protocolColumns, actionColumn];
    } else {
      return [...baseColumns, ...vsaColumns, actionColumn];
    }
  };

  // 統計卡片組件
  const StatisticsCards = () => (
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col span={6}>
        <Card>
          <Statistic
            title="總測試案例"
            value={statistics.total || 0}
            prefix={<FileTextOutlined />}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="啟用中"
            value={statistics.active || 0}
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="簡單"
            value={statistics.by_difficulty?.easy || 0}
            valueStyle={{ color: '#52c41a' }}
          />
        </Card>
      </Col>
      <Col span={6}>
        <Card>
          <Statistic
            title="困難"
            value={statistics.by_difficulty?.hard || 0}
            valueStyle={{ color: '#cf1322' }}
          />
        </Card>
      </Col>
    </Row>
  );

  // 篩選區域組件
  const FilterArea = () => (
    <div style={{ marginBottom: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
      <Search
        placeholder="搜尋問題內容"
        allowClear
        style={{ width: 300 }}
        value={searchText}
        onChange={(e) => setSearchText(e.target.value)}
        prefix={<SearchOutlined />}
      />
      
      <Select
        placeholder="選擇難度"
        allowClear
        style={{ width: 150 }}
        value={filters.difficulty_level}
        onChange={(value) => setFilters({ ...filters, difficulty_level: value })}
      >
        <Option value="easy">簡單</Option>
        <Option value="medium">中等</Option>
        <Option value="hard">困難</Option>
      </Select>
      
      <Select
        placeholder="選擇狀態"
        allowClear
        style={{ width: 150 }}
        value={filters.is_active}
        onChange={(value) => setFilters({ ...filters, is_active: value })}
      >
        <Option value="true">啟用</Option>
        <Option value="false">停用</Option>
      </Select>
      
      {activeTab === 'protocol' && (
        <Select
          placeholder="選擇類別"
          allowClear
          style={{ width: 200 }}
          value={filters.category}
          onChange={(value) => setFilters({ ...filters, category: value })}
          showSearch
        >
          {categories.map(cat => (
            <Option key={cat} value={cat}>{cat}</Option>
          ))}
        </Select>
      )}
      
      <Select
        placeholder="選擇測試類別"
        allowClear
        style={{ width: 200 }}
        value={filters.test_class_name}
        onChange={(value) => setFilters({ ...filters, test_class_name: value })}
        showSearch
      >
        {testClasses.map(tc => (
          <Option key={tc} value={tc}>{tc}</Option>
        ))}
      </Select>
      
      <Button
        icon={<FilterOutlined />}
        onClick={() => setFilters({
          difficulty_level: null,
          category: null,
          test_class_name: null,
          is_active: null,
        })}
      >
        清除篩選
      </Button>
    </div>
  );

  return (
    <div className="unified-test-case-page">
      <div className="page-header">
        <h2>統一測試案例管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            重新整理
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            匯出
          </Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={handleTabChange} size="large">
        {/* Protocol Test Cases Tab */}
        <TabPane
          tab={
            <span>
              <FileTextOutlined />
              Protocol Test Cases
              <Tag style={{ marginLeft: 8 }}>{statistics.by_type?.protocol || 0}</Tag>
            </span>
          }
          key="protocol"
        >
          <StatisticsCards />
          <FilterArea />
          <Table
            columns={getColumns()}
            dataSource={testCases}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1600, y: 'calc(100vh - 420px)' }}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 項`,
              defaultPageSize: 20,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
          />
        </TabPane>

        {/* VSA Test Cases Tab */}
        <TabPane
          tab={
            <span>
              <RobotOutlined />
              VSA Test Cases
              <Tag style={{ marginLeft: 8 }}>{statistics.by_type?.vsa || 0}</Tag>
            </span>
          }
          key="vsa"
        >
          <StatisticsCards />
          <FilterArea />
          <Table
            columns={getColumns()}
            dataSource={testCases}
            rowKey="id"
            loading={loading}
            scroll={{ x: 1800, y: 'calc(100vh - 420px)' }}
            pagination={{
              showSizeChanger: true,
              showQuickJumper: true,
              showTotal: (total) => `共 ${total} 項`,
              defaultPageSize: 20,
              pageSizeOptions: ['10', '20', '50', '100'],
            }}
          />
        </TabPane>
      </Tabs>

      {/* 詳情 Modal */}
      <Modal
        title="測試案例詳情"
        visible={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedCase && (
          <div>
            <p><strong>問題：</strong>{selectedCase.question}</p>
            <p><strong>測試類別：</strong>{selectedCase.test_class_name}</p>
            <p><strong>難度：</strong>{selectedCase.difficulty_level}</p>
            {activeTab === 'protocol' && (
              <>
                <p><strong>預期文檔IDs：</strong>{JSON.stringify(selectedCase.expected_document_ids)}</p>
                <p><strong>最少匹配數：</strong>{selectedCase.min_required_matches}</p>
                <p><strong>預期關鍵字：</strong>{JSON.stringify(selectedCase.expected_keywords)}</p>
              </>
            )}
            {activeTab === 'vsa' && (
              <>
                <p><strong>期望答案：</strong>{selectedCase.expected_answer}</p>
                <p><strong>答案關鍵字：</strong>{JSON.stringify(selectedCase.answer_keywords)}</p>
                <p><strong>滿分：</strong>{selectedCase.max_score}</p>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default UnifiedTestCasePage;
