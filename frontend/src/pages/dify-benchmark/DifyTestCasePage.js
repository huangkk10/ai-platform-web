/**
 * Dify 測試案例管理頁面
 * 
 * 功能：
 * - 顯示所有 Dify 測試案例的完整列表
 * - 支援 CRUD 操作（新增、編輯、刪除）
 * - 支援批量導入/匯出測試案例
 * - 支援篩選（難度、分類）
 * - 支援搜尋（問題內容）
 * - 啟用/停用測試案例
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
  Form,
  message,
  Statistic,
  Row,
  Col,
  Popconfirm,
  Upload,
  Divider,
} from 'antd';
import {
  SearchOutlined,
  ReloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UploadOutlined,
  DownloadOutlined,
  PoweroffOutlined,
  CheckCircleOutlined,
  FileTextOutlined,
} from '@ant-design/icons';
import * as difyBenchmarkApi from '../../services/difyBenchmarkApi';

const { Option } = Select;
const { TextArea } = Input;

const DifyTestCasePage = () => {
  const [loading, setLoading] = useState(false);
  const [testCases, setTestCases] = useState([]);
  const [filteredTestCases, setFilteredTestCases] = useState([]);
  const [searchText, setSearchText] = useState('');
  const [selectedDifficulty, setSelectedDifficulty] = useState('all');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [categories, setCategories] = useState([]);
  
  // Modal 狀態
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [selectedTestCase, setSelectedTestCase] = useState(null);
  const [isEditMode, setIsEditMode] = useState(false);
  
  const [form] = Form.useForm();

  // 統計資料
  const [statistics, setStatistics] = useState({
    total: 0,
    active: 0,
    inactive: 0,
    easy: 0,
    medium: 0,
    hard: 0,
    categories: 0,
  });

  // 載入測試案例
  const loadTestCases = async () => {
    setLoading(true);
    try {
      const response = await difyBenchmarkApi.getDifyTestCases({ page_size: 1000 });
      
      let cases = [];
      if (response.data) {
        if (Array.isArray(response.data)) {
          cases = response.data;
        } else if (response.data.results && Array.isArray(response.data.results)) {
          cases = response.data.results;
        }
      }
      
      setTestCases(cases);
      setFilteredTestCases(cases);

      // 提取所有類別
      const uniqueCategories = [...new Set(cases.map(c => c.category).filter(Boolean))];
      setCategories(uniqueCategories);

      // 計算統計
      const stats = {
        total: cases.length,
        active: cases.filter(c => c.is_active).length,
        inactive: cases.filter(c => !c.is_active).length,
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
      
      if (error.response) {
        if (error.response.status === 401 || error.response.status === 403) {
          message.error('您沒有權限訪問此功能，請聯繫管理員');
        } else {
          message.error(`載入失敗 (${error.response.status}): ${error.response.data?.detail || '未知錯誤'}`);
        }
      } else {
        message.error(`載入測試案例失敗: ${error.message || '未知錯誤'}`);
      }
      
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
      filtered = filtered.filter(tc => tc.category === selectedCategory);
    }

    // 搜尋
    if (searchText) {
      const searchLower = searchText.toLowerCase();
      filtered = filtered.filter(tc =>
        tc.question?.toLowerCase().includes(searchLower) ||
        tc.category?.toLowerCase().includes(searchLower) ||
        tc.expected_answer?.toLowerCase().includes(searchLower)
      );
    }

    setFilteredTestCases(filtered);
  }, [testCases, searchText, selectedDifficulty, selectedCategory]);

  // 顯示新增 Modal
  const showAddModal = () => {
    setIsEditMode(false);
    setSelectedTestCase(null);
    form.resetFields();
    setEditModalVisible(true);
  };

  // 顯示編輯 Modal
  const showEditModal = (testCase) => {
    setIsEditMode(true);
    setSelectedTestCase(testCase);
    form.setFieldsValue({
      question: testCase.question,
      expected_answer: testCase.expected_answer,
      category: testCase.category,
      difficulty_level: testCase.difficulty_level,
      tags: testCase.tags || [],
      notes: testCase.notes,
      is_active: testCase.is_active,
    });
    setEditModalVisible(true);
  };

  // 顯示詳細資訊
  const showDetail = (testCase) => {
    setSelectedTestCase(testCase);
    setDetailModalVisible(true);
  };

  // 處理表單提交
  const handleSubmit = async () => {
    try {
      const values = await form.validateFields();
      
      setLoading(true);
      
      if (isEditMode && selectedTestCase) {
        // 更新
        await difyBenchmarkApi.updateDifyTestCase(selectedTestCase.id, values);
        message.success('測試案例更新成功');
      } else {
        // 新增
        await difyBenchmarkApi.createDifyTestCase(values);
        message.success('測試案例新增成功');
      }
      
      setEditModalVisible(false);
      loadTestCases();
    } catch (error) {
      console.error('保存失敗:', error);
      if (error.errorFields) {
        message.error('請檢查表單欄位');
      } else {
        message.error(`保存失敗: ${error.response?.data?.detail || error.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  // 刪除測試案例
  const handleDelete = async (id) => {
    setLoading(true);
    try {
      await difyBenchmarkApi.deleteDifyTestCase(id);
      message.success('測試案例刪除成功');
      loadTestCases();
    } catch (error) {
      console.error('刪除失敗:', error);
      message.error(`刪除失敗: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 切換啟用狀態
  const handleToggleActive = async (testCase) => {
    setLoading(true);
    try {
      await difyBenchmarkApi.toggleDifyTestCase(testCase.id);
      message.success(`測試案例已${testCase.is_active ? '停用' : '啟用'}`);
      loadTestCases();
    } catch (error) {
      console.error('切換狀態失敗:', error);
      message.error(`操作失敗: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // 批量匯出
  const handleExport = async () => {
    try {
      const blob = await difyBenchmarkApi.bulkExportDifyTestCases();
      
      // 創建下載連結
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `dify_test_cases_${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('匯出成功');
    } catch (error) {
      console.error('匯出失敗:', error);
      message.error(`匯出失敗: ${error.response?.data?.detail || error.message}`);
    }
  };

  // 批量匯入
  const handleImport = async (file) => {
    const reader = new FileReader();
    
    reader.onload = async (e) => {
      try {
        const content = e.target.result;
        const testCases = JSON.parse(content);
        
        setLoading(true);
        await difyBenchmarkApi.bulkImportDifyTestCases({ test_cases: testCases });
        message.success(`成功匯入 ${testCases.length} 個測試案例`);
        setImportModalVisible(false);
        loadTestCases();
      } catch (error) {
        console.error('匯入失敗:', error);
        message.error(`匯入失敗: ${error.response?.data?.detail || error.message}`);
      } finally {
        setLoading(false);
      }
    };
    
    reader.readAsText(file);
    return false; // 阻止自動上傳
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
      title: 'ID',
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
      width: 350,
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
      title: '分類',
      dataIndex: 'category',
      key: 'category',
      width: 120,
      filters: categories.map(cat => ({ text: cat, value: cat })),
      onFilter: (value, record) => record.category === value,
      render: (text) => <Tag color="blue">{text || '未分類'}</Tag>,
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
      title: '標籤',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags) => (
        <>
          {Array.isArray(tags) && tags.slice(0, 2).map((tag, index) => (
            <Tag key={index} color="cyan" style={{ marginBottom: '4px' }}>
              {tag}
            </Tag>
          ))}
          {Array.isArray(tags) && tags.length > 2 && (
            <Tag color="default">+{tags.length - 2}</Tag>
          )}
        </>
      ),
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
        <Tag color={isActive ? 'success' : 'default'} icon={isActive ? <CheckCircleOutlined /> : null}>
          {isActive ? '啟用' : '停用'}
        </Tag>
      ),
    },
    {
      title: '創建時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 160,
      sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
      render: (date) => date ? new Date(date).toLocaleString('zh-TW') : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 180,
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
          <Tooltip title="編輯">
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => showEditModal(record)}
              size="small"
            />
          </Tooltip>
          <Tooltip title={record.is_active ? '停用' : '啟用'}>
            <Popconfirm
              title={`確定要${record.is_active ? '停用' : '啟用'}此測試案例？`}
              onConfirm={() => handleToggleActive(record)}
              okText="確定"
              cancelText="取消"
            >
              <Button
                type="link"
                icon={<PoweroffOutlined />}
                size="small"
                danger={record.is_active}
              />
            </Popconfirm>
          </Tooltip>
          <Tooltip title="刪除">
            <Popconfirm
              title="確定要刪除此測試案例？此操作不可恢復"
              onConfirm={() => handleDelete(record.id)}
              okText="確定"
              cancelText="取消"
            >
              <Button
                type="link"
                icon={<DeleteOutlined />}
                danger
                size="small"
              />
            </Popconfirm>
          </Tooltip>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 統計卡片 */}
      <Row gutter={16} style={{ marginBottom: '24px' }}>
        <Col span={4}>
          <Card>
            <Statistic
              title="總測試案例"
              value={statistics.total}
              prefix={<FileTextOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="啟用中"
              value={statistics.active}
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="已停用"
              value={statistics.inactive}
              valueStyle={{ color: '#8c8c8c' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="簡單"
              value={statistics.easy}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="中等"
              value={statistics.medium}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={4}>
          <Card>
            <Statistic
              title="困難"
              value={statistics.hard}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 主要內容卡片 */}
      <Card
        title={
          <Space>
            <FileTextOutlined />
            <span>Dify 測試案例管理</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              disabled={testCases.length === 0}
            >
              匯出
            </Button>
            <Button
              icon={<UploadOutlined />}
              onClick={() => setImportModalVisible(true)}
            >
              匯入
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={showAddModal}
            >
              新增測試案例
            </Button>
          </Space>
        }
      >
        {/* 篩選區域 */}
        <Space size="middle" style={{ marginBottom: '16px', width: '100%' }} wrap>
          <Input
            placeholder="搜尋問題內容..."
            prefix={<SearchOutlined />}
            value={searchText}
            onChange={(e) => setSearchText(e.target.value)}
            style={{ width: 300 }}
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
            style={{ width: 150 }}
          >
            <Option value="all">所有分類</Option>
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

        <Divider />

        {/* 測試案例表格 */}
        <Table
          columns={columns}
          dataSource={filteredTestCases}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400, y: 'calc(100vh - 480px)' }}
          pagination={{
            defaultPageSize: 20,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={isEditMode ? '編輯測試案例' : '新增測試案例'}
        open={editModalVisible}
        onOk={handleSubmit}
        onCancel={() => setEditModalVisible(false)}
        width={800}
        confirmLoading={loading}
        okText="儲存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            difficulty_level: 'medium',
            is_active: true,
          }}
        >
          <Form.Item
            name="question"
            label="測試問題"
            rules={[{ required: true, message: '請輸入測試問題' }]}
          >
            <TextArea
              rows={3}
              placeholder="請輸入要測試的問題內容..."
              maxLength={1000}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="expected_answer"
            label="期望答案"
            rules={[{ required: true, message: '請輸入期望答案' }]}
          >
            <TextArea
              rows={4}
              placeholder="請輸入期望的答案內容..."
              maxLength={2000}
              showCount
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="category"
                label="分類"
                rules={[{ required: true, message: '請選擇或輸入分類' }]}
              >
                <Select
                  placeholder="選擇或輸入分類"
                  mode="tags"
                  maxCount={1}
                >
                  {categories.map(cat => (
                    <Option key={cat} value={cat}>{cat}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="difficulty_level"
                label="難度"
                rules={[{ required: true, message: '請選擇難度' }]}
              >
                <Select placeholder="選擇難度">
                  <Option value="easy">簡單</Option>
                  <Option value="medium">中等</Option>
                  <Option value="hard">困難</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="tags"
            label="標籤"
          >
            <Select
              mode="tags"
              placeholder="輸入標籤並按 Enter"
              tokenSeparators={[',']}
            />
          </Form.Item>

          <Form.Item
            name="notes"
            label="備註"
          >
            <TextArea
              rows={2}
              placeholder="選填：測試案例的額外說明..."
              maxLength={500}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="狀態"
            valuePropName="checked"
          >
            <Select>
              <Option value={true}>啟用</Option>
              <Option value={false}>停用</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* 詳細資訊 Modal */}
      <Modal
        title="測試案例詳情"
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            關閉
          </Button>,
          <Button
            key="edit"
            type="primary"
            icon={<EditOutlined />}
            onClick={() => {
              setDetailModalVisible(false);
              showEditModal(selectedTestCase);
            }}
          >
            編輯
          </Button>,
        ]}
        width={800}
      >
        {selectedTestCase && (
          <div>
            <div style={{ marginBottom: '16px' }}>
              <strong>ID：</strong>{selectedTestCase.id}
              <Divider type="vertical" />
              <strong>狀態：</strong>
              <Tag color={selectedTestCase.is_active ? 'success' : 'default'}>
                {selectedTestCase.is_active ? '啟用' : '停用'}
              </Tag>
            </div>

            <Divider />

            <div style={{ marginBottom: '16px' }}>
              <strong>測試問題：</strong>
              <div style={{ 
                marginTop: '8px', 
                padding: '12px', 
                background: '#f5f5f5', 
                borderRadius: '4px',
                whiteSpace: 'pre-wrap'
              }}>
                {selectedTestCase.question}
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <strong>期望答案：</strong>
              <div style={{ 
                marginTop: '8px', 
                padding: '12px', 
                background: '#f5f5f5', 
                borderRadius: '4px',
                whiteSpace: 'pre-wrap'
              }}>
                {selectedTestCase.expected_answer}
              </div>
            </div>

            <Row gutter={16} style={{ marginBottom: '16px' }}>
              <Col span={8}>
                <strong>分類：</strong>
                <Tag color="blue" style={{ marginLeft: '8px' }}>
                  {selectedTestCase.category || '未分類'}
                </Tag>
              </Col>
              <Col span={8}>
                <strong>難度：</strong>
                <span style={{ marginLeft: '8px' }}>
                  {getDifficultyTag(selectedTestCase.difficulty_level)}
                </span>
              </Col>
              <Col span={8}>
                <strong>標籤：</strong>
                {Array.isArray(selectedTestCase.tags) && selectedTestCase.tags.map((tag, index) => (
                  <Tag key={index} color="cyan" style={{ marginLeft: '8px' }}>
                    {tag}
                  </Tag>
                ))}
              </Col>
            </Row>

            {selectedTestCase.notes && (
              <div style={{ marginBottom: '16px' }}>
                <strong>備註：</strong>
                <div style={{ 
                  marginTop: '8px', 
                  padding: '12px', 
                  background: '#fffbe6', 
                  borderRadius: '4px',
                  border: '1px solid #ffe58f'
                }}>
                  {selectedTestCase.notes}
                </div>
              </div>
            )}

            <Divider />

            <Row gutter={16}>
              <Col span={12}>
                <strong>創建時間：</strong>
                <div>{selectedTestCase.created_at ? new Date(selectedTestCase.created_at).toLocaleString('zh-TW') : '-'}</div>
              </Col>
              <Col span={12}>
                <strong>更新時間：</strong>
                <div>{selectedTestCase.updated_at ? new Date(selectedTestCase.updated_at).toLocaleString('zh-TW') : '-'}</div>
              </Col>
            </Row>
          </div>
        )}
      </Modal>

      {/* 匯入 Modal */}
      <Modal
        title="批量匯入測試案例"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setImportModalVisible(false)}>
            取消
          </Button>,
        ]}
      >
        <div style={{ marginBottom: '16px' }}>
          <p>請上傳 JSON 格式的測試案例檔案。檔案格式範例：</p>
          <pre style={{ 
            background: '#f5f5f5', 
            padding: '12px', 
            borderRadius: '4px',
            fontSize: '12px',
            overflow: 'auto'
          }}>
{`[
  {
    "question": "測試問題內容",
    "expected_answer": "期望答案",
    "category": "分類名稱",
    "difficulty_level": "medium",
    "tags": ["標籤1", "標籤2"],
    "notes": "備註說明",
    "is_active": true
  }
]`}
          </pre>
        </div>
        <Upload
          accept=".json"
          beforeUpload={handleImport}
          showUploadList={false}
        >
          <Button icon={<UploadOutlined />} block>
            選擇 JSON 檔案
          </Button>
        </Upload>
      </Modal>
    </div>
  );
};

export default DifyTestCasePage;
