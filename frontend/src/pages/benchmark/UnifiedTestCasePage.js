/**
 * 統一測試案例管理頁面
 * 整合 Protocol Benchmark 和 VSA Test Case
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Space, Tag, Tooltip, message, Modal, 
  Card, Statistic, Row, Col, Input, Select, Popconfirm
} from 'antd';
import {
  FileTextOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, ReloadOutlined, ExportOutlined,
  SearchOutlined, FilterOutlined
} from '@ant-design/icons';
import unifiedBenchmarkApi from '../../services/unifiedBenchmarkApi';
import './UnifiedTestCasePage.css';

const { Search } = Input;
const { Option } = Select;

const UnifiedTestCasePage = ({ defaultTab = 'vsa' }) => {
  // State 管理
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
  const [selectedCase, setSelectedCase] = useState(null);
  
  // 分類列表（VSA 不需要 categories，但保留變數避免錯誤）
  const [testClasses, setTestClasses] = useState([]);

  // 載入測試案例
  const loadTestCases = async () => {
    setLoading(true);
    try {
      const params = {
        test_type: 'vsa', // 固定使用 VSA 類型
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
      const response = await unifiedBenchmarkApi.getStatistics('vsa'); // 固定使用 VSA 類型
      console.log('=== 統計資料 API 回應 ===');
      console.log('完整回應:', response);
      console.log('response.data:', response.data);
      console.log('by_difficulty:', response.data?.by_difficulty);
      console.log('========================');
      setStatistics(response.data);
    } catch (error) {
      console.error('載入統計資料失敗:', error);
    }
  };

  // 載入分類列表（VSA 不需要，但保留函數避免錯誤）
  const loadCategories = async () => {
    // VSA 模式不需要載入 categories
  };

  // 載入測試類別列表
  const loadTestClasses = async () => {
    try {
      const response = await unifiedBenchmarkApi.getTestClasses('vsa'); // 固定使用 VSA 類型
      setTestClasses(response.data || []);
    } catch (error) {
      console.error('載入測試類別失敗:', error);
    }
  };

  // 查看詳情
  const handleViewDetail = (record) => {
    setSelectedCase(record);
    setDetailModalVisible(true);
  };

  // 編輯（暫時使用詳情 Modal，未來可實作編輯功能）
  const handleEdit = (record) => {
    setSelectedCase(record);
    setDetailModalVisible(true);
    message.info('編輯功能開發中，目前顯示詳情');
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
      const response = await unifiedBenchmarkApi.bulkExport('vsa'); // 固定使用 VSA 類型
      const dataStr = JSON.stringify(response.data, null, 2);
      const dataBlob = new Blob([dataStr], { type: 'application/json' });
      const url = window.URL.createObjectURL(dataBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `vsa_test_cases_${new Date().getTime()}.json`;
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
  }, []); // 移除 activeTab 依賴，因為固定使用 VSA

  // 搜尋和篩選變化時重新載入
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTestCases();
    }, 300);
    return () => clearTimeout(timer);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchText, filters]);

  // 動態欄位配置（VSA 專用）
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

    // VSA 專用欄位
    const vsaColumns = [
      {
        title: 'Keyword 判斷條件',
        dataIndex: 'answer_keywords',
        key: 'answer_keywords',
        width: 300,
        render: (keywords) => {
          if (!keywords || keywords.length === 0) return '-';
          return (
            <Space size={[0, 4]} wrap>
              {keywords.map((keyword, index) => (
                <Tag key={index} color="purple">{keyword}</Tag>
              ))}
            </Space>
          );
        },
      },
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

    // 操作欄位（VSA 完整 CRUD）
    const actionColumn = {
      title: '操作',
      key: 'actions',
      width: 220,
      fixed: 'right',
      render: (_, record) => (
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
      ),
    };

    return [...baseColumns, ...vsaColumns, actionColumn];
  };

  // 統計卡片組件
  const StatisticsCards = () => (
    <>
      {/* 第一行：基本統計 */}
      <Row gutter={16} style={{ marginBottom: 16 }}>
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
              title="停用"
              value={statistics.inactive || 0}
              valueStyle={{ color: '#999' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="平均分數"
              value={statistics.average_score || 0}
              precision={2}
              suffix="分"
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>
      
      {/* 第二行：難度分布 */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="簡單題目"
              value={statistics.by_difficulty?.easy || 0}
              valueStyle={{ color: '#52c41a' }}
              prefix="📗"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="中等題目"
              value={statistics.by_difficulty?.medium || 0}
              valueStyle={{ color: '#faad14' }}
              prefix="📙"
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="困難題目"
              value={statistics.by_difficulty?.hard || 0}
              valueStyle={{ color: '#cf1322' }}
              prefix="📕"
            />
          </Card>
        </Col>
      </Row>
    </>
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
        <h2>VSA 測試案例管理</h2>
        <Space>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            重新整理
          </Button>
          <Button icon={<ExportOutlined />} onClick={handleExport}>
            匯出
          </Button>
        </Space>
      </div>

      <StatisticsCards />
      <FilterArea />
      
      <Table
        columns={getColumns()}
        dataSource={testCases}
        rowKey="id"
        loading={loading}
        scroll={{ x: 2100, y: 'calc(100vh - 480px)' }}
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total) => `共 ${total} 項`,
          defaultPageSize: 20,
          pageSizeOptions: ['10', '20', '50', '100'],
        }}
      />

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
            <p><strong>期望答案：</strong>{selectedCase.expected_answer}</p>
            
            {/* Keyword 判斷條件詳細資訊 */}
            <div style={{ 
              marginTop: '16px', 
              padding: '12px', 
              background: '#f0f5ff', 
              borderLeft: '4px solid #1890ff',
              borderRadius: '4px'
            }}>
              <p style={{ margin: '0 0 8px 0' }}>
                <strong style={{ color: '#1890ff' }}>🔑 Keyword 判斷條件：</strong>
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>條件摘要：</strong>{selectedCase.criteria_summary}
              </p>
              <p style={{ margin: '4px 0' }}>
                <strong>答案關鍵字：</strong>
                {selectedCase.answer_keywords && selectedCase.answer_keywords.length > 0 ? (
                  <Space size={[0, 4]} wrap style={{ marginLeft: '8px' }}>
                    {selectedCase.answer_keywords.map((keyword, index) => (
                      <Tag key={index} color="blue">{keyword}</Tag>
                    ))}
                  </Space>
                ) : ' 無'}
              </p>
            </div>
            
            <p style={{ marginTop: '12px' }}><strong>滿分：</strong>{selectedCase.max_score}</p>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default UnifiedTestCasePage;
