/**
 * 統一測試案例管理頁面
 * 整合 Protocol Benchmark 和 VSA Test Case
 */

import React, { useState, useEffect } from 'react';
import {
  Table, Button, Space, Tag, Tooltip, message, Modal, 
  Card, Statistic, Row, Col, Input, Select, Popconfirm, Form, Switch
} from 'antd';
import {
  FileTextOutlined, EditOutlined,
  DeleteOutlined, EyeOutlined, ReloadOutlined, ExportOutlined,
  SearchOutlined, FilterOutlined, PlusOutlined, CloseOutlined
} from '@ant-design/icons';
import unifiedBenchmarkApi from '../../services/unifiedBenchmarkApi';
import './UnifiedTestCasePage.css';

const { Search, TextArea } = Input;
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
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedCase, setSelectedCase] = useState(null);
  const [editForm] = Form.useForm();
  
  // Keyword 管理
  const [keywordInput, setKeywordInput] = useState('');
  const [keywords, setKeywords] = useState([]);
  
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

  // 編輯
  const handleEdit = (record) => {
    setSelectedCase(record);
    // 設置 keywords state
    setKeywords(record.answer_keywords || []);
    // 設置表單初始值
    editForm.setFieldsValue({
      question: record.question,
      difficulty_level: record.difficulty_level,
      is_active: record.is_active,
    });
    setEditModalVisible(true);
  };

  // 添加關鍵字
  const handleAddKeyword = () => {
    const trimmedKeyword = keywordInput.trim();
    if (!trimmedKeyword) {
      message.warning('請輸入關鍵字');
      return;
    }
    if (keywords.includes(trimmedKeyword)) {
      message.warning('此關鍵字已存在');
      return;
    }
    setKeywords([...keywords, trimmedKeyword]);
    setKeywordInput('');
  };

  // 刪除關鍵字
  const handleRemoveKeyword = (keywordToRemove) => {
    setKeywords(keywords.filter(k => k !== keywordToRemove));
  };

  // 清空所有關鍵字
  const handleClearAllKeywords = () => {
    Modal.confirm({
      title: '確認清空',
      content: '確定要清空所有關鍵字嗎？',
      onOk: () => {
        setKeywords([]);
        message.success('已清空所有關鍵字');
      },
    });
  };

  // 保存編輯
  const handleSaveEdit = async () => {
    try {
      // 驗證關鍵字
      if (keywords.length === 0) {
        message.error('請至少添加一個關鍵字');
        return;
      }

      const values = await editForm.validateFields();
      
      // 準備更新數據
      const updateData = {
        question: values.question,
        answer_keywords: keywords, // 使用 keywords state
        difficulty_level: values.difficulty_level,
        is_active: values.is_active,
      };

      // 調用 API 更新（使用 PATCH 只更新指定欄位）
      await unifiedBenchmarkApi.patchTestCase(selectedCase.id, updateData);
      
      message.success('更新成功');
      setEditModalVisible(false);
      editForm.resetFields();
      setKeywords([]); // 清空 keywords
      setKeywordInput(''); // 清空輸入框
      loadTestCases();
      loadStatistics();
    } catch (error) {
      console.error('更新失敗:', error);
      if (error.errorFields) {
        message.error('請檢查表單填寫');
      } else {
        message.error('更新失敗');
      }
    }
  };

  // 取消編輯
  const handleCancelEdit = () => {
    setEditModalVisible(false);
    editForm.resetFields();
    setKeywords([]); // 清空 keywords
    setKeywordInput(''); // 清空輸入框
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
    
    // 監聽來自 TopHeader 的重新整理事件
    const handleReloadEvent = () => {
      handleRefresh();
    };
    
    // 監聽來自 TopHeader 的匯出事件
    const handleExportEvent = () => {
      handleExport();
    };
    
    // 監聽來自 TopHeader 的新增事件
    const handleCreateEvent = () => {
      message.info('新增功能開發中...');
    };
    
    window.addEventListener('vsa-test-case-reload', handleReloadEvent);
    window.addEventListener('vsa-test-case-export', handleExportEvent);
    window.addEventListener('vsa-test-case-create', handleCreateEvent);
    
    return () => {
      window.removeEventListener('vsa-test-case-reload', handleReloadEvent);
      window.removeEventListener('vsa-test-case-export', handleExportEvent);
      window.removeEventListener('vsa-test-case-create', handleCreateEvent);
    };
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
    <Row gutter={16} style={{ marginBottom: 24 }}>
      <Col span={4}>
        <Card>
          <Statistic
            title="總測試案例"
            value={statistics.total || 0}
            prefix={<FileTextOutlined />}
          />
        </Card>
      </Col>
      <Col span={4}>
        <Card>
          <Statistic
            title="啟用中"
            value={statistics.active || 0}
            valueStyle={{ color: '#3f8600' }}
          />
        </Card>
      </Col>
      <Col span={5}>
        <Card>
          <Statistic
            title="簡單題目"
            value={statistics.by_difficulty?.easy || 0}
            valueStyle={{ color: '#52c41a' }}
            prefix="📗"
          />
        </Card>
      </Col>
      <Col span={5}>
        <Card>
          <Statistic
            title="中等題目"
            value={statistics.by_difficulty?.medium || 0}
            valueStyle={{ color: '#faad14' }}
            prefix="📙"
          />
        </Card>
      </Col>
      <Col span={6}>
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
      <StatisticsCards />
      <FilterArea />
      
      <Table
        columns={getColumns()}
        dataSource={testCases}
        rowKey="id"
        loading={loading}
        scroll={{ x: 1750, y: 'calc(100vh - 480px)' }}
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

      {/* 編輯 Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <EditOutlined style={{ marginRight: 8, color: '#1890ff' }} />
            <span>編輯測試案例 #{selectedCase?.id}</span>
          </div>
        }
        visible={editModalVisible}
        onOk={handleSaveEdit}
        onCancel={handleCancelEdit}
        width={800}
        okText="保存修改"
        cancelText="取消"
        destroyOnClose
      >
        <Form
          form={editForm}
          layout="vertical"
        >
          {/* 問題 */}
          <Form.Item
            label={
              <span>
                <span style={{ color: 'red' }}>* </span>
                問題內容
              </span>
            }
            name="question"
            rules={[{ required: true, message: '請輸入問題' }]}
            tooltip="測試案例的問題描述"
          >
            <TextArea
              rows={4}
              placeholder="請輸入測試問題"
              showCount
              maxLength={1000}
            />
          </Form.Item>

          {/* Keyword 判斷條件 - 新版介面 */}
          <Form.Item
            label={
              <span>
                <span style={{ color: 'red' }}>* </span>
                Keyword 判斷條件
              </span>
            }
            tooltip="添加測試案例需要匹配的關鍵字"
          >
            {/* 輸入區域 */}
            <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
              <Input
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onPressEnter={handleAddKeyword}
                placeholder="輸入關鍵字後按 Enter 或點擊添加..."
                style={{ flex: 1 }}
              />
              <Button 
                type="primary" 
                icon={<PlusOutlined />} 
                onClick={handleAddKeyword}
              >
                添加
              </Button>
            </div>
            
            {/* 關鍵字展示區域 */}
            <div style={{ 
              padding: '12px', 
              background: '#fafafa', 
              borderRadius: '6px',
              border: '1px solid #d9d9d9',
              minHeight: '80px'
            }}>
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                marginBottom: keywords.length > 0 ? '12px' : '0'
              }}>
                <span style={{ color: '#666', fontSize: '13px' }}>
                  已添加的關鍵字 ({keywords.length})：
                </span>
                {keywords.length > 0 && (
                  <Button 
                    type="link" 
                    danger 
                    size="small"
                    onClick={handleClearAllKeywords}
                    icon={<DeleteOutlined />}
                  >
                    清空全部
                  </Button>
                )}
              </div>
              
              {keywords.length > 0 ? (
                <Space size={[8, 8]} wrap>
                  {keywords.map((keyword, index) => (
                    <Tag 
                      key={index} 
                      closable 
                      onClose={() => handleRemoveKeyword(keyword)}
                      color="purple"
                      style={{ 
                        fontSize: '14px', 
                        padding: '6px 10px',
                        marginBottom: 0
                      }}
                    >
                      {keyword}
                    </Tag>
                  ))}
                </Space>
              ) : (
                <div style={{ 
                  textAlign: 'center', 
                  color: '#bfbfbf',
                  padding: '20px 0',
                  fontSize: '13px'
                }}>
                  尚未添加關鍵字
                </div>
              )}
            </div>
            
            {/* 提示文字 */}
            <div style={{ 
              marginTop: '8px', 
              color: '#8c8c8c', 
              fontSize: '12px',
              display: 'flex',
              alignItems: 'center',
              gap: '4px'
            }}>
              💡 提示：輸入關鍵字後按 <Tag style={{ margin: '0 4px' }}>Enter</Tag> 也可快速添加
            </div>
          </Form.Item>

          {/* 難度 */}
          <Form.Item
            label={
              <span>
                <span style={{ color: 'red' }}>* </span>
                難度等級
              </span>
            }
            name="difficulty_level"
            rules={[{ required: true, message: '請選擇難度' }]}
          >
            <Select placeholder="選擇難度等級">
              <Option value="easy">
                <Tag color="green">簡單</Tag> - 基礎問題
              </Option>
              <Option value="medium">
                <Tag color="orange">中等</Tag> - 進階問題
              </Option>
              <Option value="hard">
                <Tag color="red">困難</Tag> - 複雜問題
              </Option>
            </Select>
          </Form.Item>

          {/* 是否啟用 */}
          <Form.Item
            label="測試案例狀態"
            name="is_active"
            valuePropName="checked"
            tooltip="停用的測試案例不會被執行"
          >
            <Switch
              checkedChildren="啟用"
              unCheckedChildren="停用"
            />
          </Form.Item>

          {/* 刪除區域 */}
          <div style={{ 
            marginTop: '32px',
            paddingTop: '16px',
            borderTop: '1px solid #f0f0f0'
          }}>
            <p style={{ color: '#999', marginBottom: '12px' }}>
              ⚠️ 危險操作：刪除後無法恢復
            </p>
            <Form.Item style={{ marginBottom: 0 }}>
              <Popconfirm
                title="確定要刪除此測試案例嗎？"
                description="此操作無法恢復，請確認是否繼續。"
                onConfirm={() => {
                  handleDelete(selectedCase.id);
                  handleCancelEdit();
                }}
                okText="確定刪除"
                cancelText="取消"
                okButtonProps={{ danger: true }}
              >
                <Button danger icon={<DeleteOutlined />} block>
                  刪除此測試案例
                </Button>
              </Popconfirm>
            </Form.Item>
          </div>
        </Form>
      </Modal>
    </div>
  );
};

export default UnifiedTestCasePage;
