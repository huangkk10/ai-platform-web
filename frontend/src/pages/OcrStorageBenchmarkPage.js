import React, { useState, useEffect, useCallback } from 'react';
import { 
  Card, 
  Table, 
  Button, 
  Modal, 
  Form, 
  Input, 
  InputNumber, 
  DatePicker, 
  Select, 
  Tag, 
  Space, 
  Typography,
  message,
  Tooltip,
  Statistic,
  Row,
  Col
} from 'antd';
import { 
  DatabaseOutlined, 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  ReloadOutlined,
  EyeOutlined,
  BarChartOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';
import dayjs from 'dayjs';

const { Title } = Typography;

const OcrStorageBenchmarkPage = () => {
  const { user, isAuthenticated, loading: authLoading, initialized } = useAuth();
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [previewModalVisible, setPreviewModalVisible] = useState(false);
  const [previewRecord, setPreviewRecord] = useState(null);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();
  const [statistics, setStatistics] = useState({});

  // OCR 測試類別相關狀態
  const [ocrTestClasses, setOcrTestClasses] = useState([]);
  const [selectedOcrTestClass, setSelectedOcrTestClass] = useState(null);
  const [testClassLoading, setTestClassLoading] = useState(false);

  // 表格欄位定義 - 根據用戶需求顯示指定欄位
  const columns = [
    {
      title: '預覽',
      key: 'preview',
      width: 80,
      fixed: 'left',
      render: (_, record) => (
        <Button 
          icon={<EyeOutlined />}
          size="small"
          type="text"
          onClick={() => handlePreview(record)}
          title="查看詳細資料"
          style={{ color: '#1890ff' }}
        />
      ),
    },
    {
      title: 'Project',
      dataIndex: 'project_name',
      key: 'project_name',
      width: 200,
      fixed: 'left',
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <Tooltip title={text}>
          <Tag color="blue" style={{ cursor: 'help', maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {text}
          </Tag>
        </Tooltip>
      ),
      sorter: (a, b) => a.project_name.localeCompare(b.project_name),
    },
    {
      title: 'Storage Benchmark Score',
      dataIndex: 'benchmark_score',
      key: 'benchmark_score',
      width: 180,
      align: 'center',
      render: (score) => (
        <div style={{ textAlign: 'center' }}>
          <Statistic 
            value={score} 
            valueStyle={{ 
              fontSize: '16px', 
              color: score >= 6000 ? '#52c41a' : score >= 4000 ? '#faad14' : '#f5222d'
            }}
          />
        </div>
      ),
      sorter: (a, b) => a.benchmark_score - b.benchmark_score,
    },
    {
      title: '平均帶寬',
      dataIndex: 'average_bandwidth',
      key: 'average_bandwidth',
      width: 150,
      align: 'center',
      render: (bandwidth) => (
        <Tag color="green" style={{ fontSize: '14px', padding: '4px 8px' }}>
          {bandwidth}
        </Tag>
      ),
    },
    {
      title: '裝置型號',
      dataIndex: 'device_model',
      key: 'device_model',
      width: 200,
      ellipsis: {
        showTitle: true,
      },
      render: (text) => (
        <Tooltip title={text}>
          <div style={{ maxWidth: '180px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
            {text}
          </div>
        </Tooltip>
      ),
      sorter: (a, b) => a.device_model.localeCompare(b.device_model),
    },
    {
      title: '固件版本',
      dataIndex: 'firmware_version',
      key: 'firmware_version',
      width: 130,
      render: (version) => (
        <Tag color="orange" style={{ fontFamily: 'monospace' }}>
          {version}
        </Tag>
      ),
    },
    {
      title: '測試時間',
      dataIndex: 'test_datetime',
      key: 'test_datetime',
      width: 180,
      render: (datetime) => {
        if (!datetime) return '-';
        const date = new Date(datetime);
        return (
          <div style={{ fontSize: '13px' }}>
            <div>{date.toLocaleDateString('zh-TW')}</div>
            <div style={{ color: '#666' }}>{date.toLocaleTimeString('zh-TW')}</div>
          </div>
        );
      },
      sorter: (a, b) => new Date(a.test_datetime) - new Date(b.test_datetime),
    },
    {
      title: '3DMark版本',
      dataIndex: 'mark_version_3d',
      key: 'mark_version_3d',
      width: 140,
      render: (version) => version ? (
        <Tag color="purple" style={{ fontFamily: 'monospace' }}>
          {version}
        </Tag>
      ) : (
        <span style={{ color: '#ccc' }}>-</span>
      ),
    },
    {
      title: '操作',
      key: 'actions',
      width: 120,
      fixed: 'right',
      render: (_, record) => (
        <Space>
          <Button 
            icon={<EditOutlined />} 
            size="small" 
            onClick={() => handleEdit(record)}
            title="編輯"
          />
          <Button 
            icon={<DeleteOutlined />} 
            size="small" 
            danger
            onClick={() => handleDelete(record.id)}
            title="刪除"
          />
        </Space>
      ),
    },
  ];

  // 載入資料
  const fetchRecords = useCallback(async () => {
    try {
      setLoading(true);
      console.log('Fetching OCR storage benchmark records, authenticated:', isAuthenticated, 'user:', user);
      
      if (!isAuthenticated) {
        message.error('請先登入');
        return;
      }
      
      if (!user) {
        message.error('用戶資訊載入失敗');
        return;
      }
      
      const params = {};
      
      // 如果有選擇測試類別，添加過濾參數
      if (selectedOcrTestClass) {
        params.test_class = selectedOcrTestClass;
        console.log('添加測試類別過濾參數:', selectedOcrTestClass);
      }
      
      const response = await axios.get('/api/ocr-storage-benchmarks/', {
        params: params,
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }
      });
      
      console.log('API Response:', response.data);
      const recordsData = response.data.results || [];
      setRecords(recordsData);
      
    } catch (error) {
      console.error('載入 OCR Storage Benchmark 記錄失敗:', error);
      console.error('Error response:', error.response);
      console.error('Error status:', error.response?.status);
      console.error('Error data:', error.response?.data);
      
      if (error.response?.status === 401) {
        message.error('認證已過期，請重新登入');
      } else if (error.response?.status === 403) {
        message.error('權限不足，請檢查您的帳戶狀態');
      } else {
        message.error('載入資料失敗: ' + (error.response?.data?.detail || error.message));
      }
    } finally {
      setLoading(false);
    }
  }, [isAuthenticated, user, selectedOcrTestClass]);

  // 載入統計資料
  const fetchStatistics = useCallback(async () => {
    try {
      const params = {};
      
      // 如果有選擇測試類別，添加過濾參數
      if (selectedOcrTestClass) {
        params.test_class = selectedOcrTestClass;
      }
      
      const response = await axios.get('/api/ocr-storage-benchmarks/statistics/', {
        params: params,
        withCredentials: true,
      });
      setStatistics(response.data);
    } catch (error) {
      console.error('載入統計資料失敗:', error);
    }
  }, [selectedOcrTestClass]);

  // 載入 OCR 測試類別
  const fetchOcrTestClasses = async () => {
    setTestClassLoading(true);
    try {
      console.log('🔄 開始載入 OCR 測試類別...');
      const response = await axios.get('/api/ocr-test-classes/', {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        }
      });
      
      console.log('📡 API 響應狀態:', response.status);
      console.log('📊 API 響應資料:', response.data);
      console.log('📊 資料類型:', typeof response.data, Array.isArray(response.data));
      
      // 處理分頁格式的 API 響應
      let testClasses = [];
      if (response.data && response.data.results && Array.isArray(response.data.results)) {
        testClasses = response.data.results;
        console.log('✅ 從分頁響應設置 OCR 測試類別:', testClasses);
      } else if (response.data && Array.isArray(response.data)) {
        testClasses = response.data;
        console.log('✅ 從數組響應設置 OCR 測試類別:', testClasses);
      } else {
        console.warn('⚠️ API 響應格式不正確:', response.data);
        testClasses = [];
      }
      
      setOcrTestClasses(testClasses);
      console.log('📋 載入 OCR 測試類別成功:', testClasses.length, '個類別');
    } catch (error) {
      console.error('❌ 載入 OCR 測試類別失敗:', error);
      if (error.response?.status === 403) {
        console.warn('🚫 權限不足：無法載入 OCR 測試類別列表，請聯繫管理員');
      } else if (error.response?.status === 401) {
        console.warn('🔐 未授權：請重新登入');
      } else {
        console.error('💥 載入 OCR 測試類別時發生未知錯誤:', error.message);
      }
      // 設置空的測試類別列表，避免程式崩潰
      setOcrTestClasses([]);
    } finally {
      setTestClassLoading(false);
      console.log('🏁 OCR 測試類別載入完成');
    }
  };

  // 處理 OCR 測試類別選擇
  const handleOcrTestClassFilter = (testClassId) => {
    console.log('OCR 測試類別選擇變更:', testClassId);
    setSelectedOcrTestClass(testClassId);
    
    if (testClassId) {
      // 保存選擇到 localStorage
      localStorage.setItem('selected-ocr-test-class-id', testClassId.toString());
      console.log('保存 OCR 測試類別選擇到 localStorage:', testClassId);
    } else {
      // 移除 localStorage 中的選擇
      localStorage.removeItem('selected-ocr-test-class-id');
      console.log('從 localStorage 移除 OCR 測試類別選擇');
    }
  };

  useEffect(() => {
    console.log('OcrStorageBenchmarkPage mounted, isAuthenticated:', isAuthenticated, 'user:', user, 'initialized:', initialized);
    
    if (initialized && isAuthenticated && user) {
      fetchRecords();
      fetchStatistics();
    } else if (initialized && !isAuthenticated) {
      console.log('User not authenticated');
      message.warning('請先登入以查看OCR Storage Benchmark資料');
    }
  }, [isAuthenticated, user, initialized, fetchRecords]);

  // 載入 OCR 測試類別
  useEffect(() => {
    fetchOcrTestClasses();
  }, []);

  // 載入統計資料 - 當測試類別選擇變更時同步更新
  useEffect(() => {
    if (isAuthenticated && user && initialized) {
      fetchStatistics();
    }
  }, [isAuthenticated, user, initialized, fetchStatistics]);

  // 恢復 OCR 測試類別選擇
  useEffect(() => {
    if (ocrTestClasses.length > 0) {
      try {
        const savedId = localStorage.getItem('selected-ocr-test-class-id');
        if (savedId) {
          const parsedId = parseInt(savedId, 10);
          const validClass = ocrTestClasses.find(cls => cls.id === parsedId);
          if (validClass) {
            setSelectedOcrTestClass(parsedId);
            console.log('恢復 OCR 測試類別選擇:', validClass.name, validClass.id);
          } else {
            console.warn('保存的 OCR 測試類別ID無效:', savedId);
            localStorage.removeItem('selected-ocr-test-class-id');
          }
        }
      } catch (error) {
        console.warn('恢復 OCR 測試類別選擇失敗:', error);
      }
    }
  }, [ocrTestClasses]);

  // 預覽處理
  const handlePreview = (record) => {
    setPreviewRecord(record);
    setPreviewModalVisible(true);
  };

  // 編輯處理
  const handleEdit = (record) => {
    setEditingRecord(record);
    
    // 處理日期時間格式
    const formValues = { 
      ...record,
      test_datetime: record.test_datetime ? dayjs(record.test_datetime) : null
    };
    
    form.setFieldsValue(formValues);
    setModalVisible(true);
  };

  // 刪除處理
  const handleDelete = async (id) => {
    Modal.confirm({
      title: '確認刪除',
      content: '確定要刪除這個測試記錄嗎？',
      onOk: async () => {
        try {
          await axios.delete(`/api/ocr-storage-benchmarks/${id}/`, {
            withCredentials: true
          });
          message.success('刪除成功');
          fetchRecords();
          fetchStatistics();
        } catch (error) {
          message.error('刪除失敗');
        }
      },
    });
  };

  // 新增/編輯提交
  const handleSubmit = async (values) => {
    try {
      // 處理日期時間格式
      const submitData = {
        ...values,
        test_datetime: values.test_datetime ? values.test_datetime.toISOString() : null
      };
      
      const config = {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      };
      
      if (editingRecord) {
        await axios.put(`/api/ocr-storage-benchmarks/${editingRecord.id}/`, submitData, config);
        message.success('更新成功');
      } else {
        await axios.post('/api/ocr-storage-benchmarks/', submitData, config);
        message.success('新增成功');
      }
      
      setModalVisible(false);
      form.resetFields();
      setEditingRecord(null);
      fetchRecords();
      fetchStatistics();
    } catch (error) {
      message.error('操作失敗: ' + (error.response?.data?.detail || error.message));
    }
  };

  // 如果還未初始化，顯示載入狀態
  if (!initialized) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>載入中...</Title>
            <p>正在檢查認證狀態，請稍候</p>
          </div>
        </Card>
      </div>
    );
  }

  // 如果未認證，顯示提示
  if (!isAuthenticated) {
    return (
      <div style={{ padding: '24px' }}>
        <Card>
          <div style={{ textAlign: 'center', padding: '50px 0' }}>
            <Title level={3}>需要登入</Title>
            <p>請登入後才能查看 OCR Storage Benchmark 資料</p>
          </div>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: '24px' }}>
      {/* AI OCR 標題和測試類別下拉選單 */}
      <div style={{
        marginBottom: '16px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <Title level={2} style={{ margin: 0 }}>
          <DatabaseOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          AI OCR 存儲基準測試
        </Title>
        
        {/* OCR 測試類別過濾器 */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '16px', color: '#666', fontWeight: '500' }}>測試類別：</span>
          <Select
            allowClear
            style={{ minWidth: 280, fontSize: '16px' }}
            value={selectedOcrTestClass}
            placeholder="請選擇測試類別"
            onChange={(value) => {
              handleOcrTestClassFilter(value);
            }}
            showSearch
            size="large"
            disabled={ocrTestClasses.length === 0}
            notFoundContent={
              ocrTestClasses.length === 0 
                ? "無測試類別數據，請聯繫管理員" 
                : "無匹配結果"
            }
            filterOption={(input, option) =>
              (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
            }
            loading={testClassLoading}
            options={[
              { key: 'all', value: null, label: '全部' },
              ...ocrTestClasses.map(testClass => ({
                key: testClass.id,
                value: testClass.id,
                label: testClass.name
              }))
            ]}
          />
        </div>
      </div>

      {/* 操作按鈕區域 */}
      <div style={{ 
        marginBottom: '16px', 
        display: 'flex', 
        justifyContent: 'flex-end', 
        alignItems: 'center' 
      }}>
        <Space>
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => {
              fetchRecords();
              fetchStatistics();
              fetchOcrTestClasses();
            }}
            loading={loading}
          >
            重新載入
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingRecord(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            新增測試記錄
          </Button>
        </Space>
      </div>

      {/* 統計卡片 */}
      {statistics.total_records > 0 && (
        <Row gutter={16} style={{ marginBottom: '16px' }}>
          <Col span={8}>
            <Card>
              <Statistic
                title="總記錄數"
                value={statistics.total_records}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="平均分數"
                value={statistics.score_statistics?.avg_score || 0}
                precision={0}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
          <Col span={8}>
            <Card>
              <Statistic
                title="最高分數"
                value={statistics.score_statistics?.max_score || 0}
                prefix={<BarChartOutlined />}
                valueStyle={{ color: '#faad14' }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={records}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
          }}
          bordered
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={editingRecord ? '編輯測試記錄' : '新增測試記錄'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingRecord(null);
        }}
        onOk={() => form.submit()}
        width={800}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="project_name"
                label="Project"
                rules={[{ required: true, message: '請輸入專案名稱' }]}
              >
                <Input placeholder="例如: Storage Performance Test" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="benchmark_score"
                label="Storage Benchmark Score"
                rules={[{ required: true, message: '請輸入基準分數' }]}
              >
                <InputNumber 
                  style={{ width: '100%' }}
                  min={0}
                  max={50000}
                  placeholder="例如: 6883"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="average_bandwidth"
                label="平均帶寬"
                rules={[{ required: true, message: '請輸入平均帶寬' }]}
              >
                <Input placeholder="例如: 1174.89 MB/s" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="device_model"
                label="裝置型號"
                rules={[{ required: true, message: '請輸入裝置型號' }]}
              >
                <Input placeholder="例如: KINGSTON SFYR2S1TO" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="firmware_version"
                label="固件版本"
                rules={[{ required: true, message: '請輸入固件版本' }]}
              >
                <Input placeholder="例如: SGW0904A" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="test_datetime"
                label="測試時間"
                rules={[{ required: true, message: '請選擇測試時間' }]}
              >
                <DatePicker 
                  showTime 
                  style={{ width: '100%' }}
                  format="YYYY-MM-DD HH:mm:ss"
                  placeholder="選擇測試時間"
                />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="mark_version_3d"
                label="3DMark版本"
              >
                <Input placeholder="例如: 2.28.8228" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 預覽 Modal */}
      <Modal
        title={
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChartOutlined style={{ color: '#1890ff' }} />
            <span>測試記錄詳情</span>
            {previewRecord && (
              <Tag color="blue" style={{ marginLeft: '8px' }}>
                {previewRecord.project_name}
              </Tag>
            )}
          </div>
        }
        open={previewModalVisible}
        onCancel={() => {
          setPreviewModalVisible(false);
          setPreviewRecord(null);
        }}
        footer={[
          <Button key="close" onClick={() => {
            setPreviewModalVisible(false);
            setPreviewRecord(null);
          }}>
            關閉
          </Button>,
          <Button 
            key="edit" 
            type="primary" 
            icon={<EditOutlined />}
            onClick={() => {
              setPreviewModalVisible(false);
              handleEdit(previewRecord);
            }}
          >
            編輯
          </Button>
        ]}
        width={900}
      >
        {previewRecord && (
          <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
            {/* 基本測試資訊 */}
            <div style={{ 
              marginBottom: '20px',
              padding: '16px',
              backgroundColor: '#f8f9fa',
              borderRadius: '8px',
              border: '1px solid #e9ecef'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#1890ff' }}>
                📊 測試資訊
              </Title>
              <Row gutter={16}>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📁 Project：</strong>
                    <Tag color="blue" style={{ marginLeft: '8px' }}>{previewRecord.project_name}</Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📈 Storage Benchmark Score：</strong>
                    <Tag color="green" style={{ marginLeft: '8px', fontSize: '16px', padding: '4px 8px' }}>
                      {previewRecord.benchmark_score}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🚀 平均帶寬：</strong>
                    <Tag color="orange" style={{ marginLeft: '8px' }}>{previewRecord.average_bandwidth}</Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>💿 裝置型號：</strong>
                    <span style={{ marginLeft: '8px' }}>{previewRecord.device_model}</span>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🔧 固件版本：</strong>
                    <Tag color="purple" style={{ marginLeft: '8px', fontFamily: 'monospace' }}>
                      {previewRecord.firmware_version}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>⏰ 測試時間：</strong>
                    <span style={{ marginLeft: '8px' }}>
                      {previewRecord.test_datetime ? 
                        new Date(previewRecord.test_datetime).toLocaleString('zh-TW') : '-'}
                    </span>
                  </div>
                </Col>
                <Col span={12}>
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🎮 3DMark版本：</strong>
                    {previewRecord.mark_version_3d ? (
                      <Tag color="cyan" style={{ marginLeft: '8px', fontFamily: 'monospace' }}>
                        {previewRecord.mark_version_3d}
                      </Tag>
                    ) : (
                      <span style={{ marginLeft: '8px', color: '#999' }}>未指定</span>
                    )}
                  </div>
                </Col>
              </Row>
            </div>

            {/* 系統資訊 */}
            <div style={{ 
              padding: '16px',
              backgroundColor: '#fafafa',
              borderRadius: '8px',
              border: '1px solid #d9d9d9'
            }}>
              <Title level={4} style={{ margin: '0 0 12px 0', color: '#666' }}>
                📊 系統資訊
              </Title>
              <div style={{ fontSize: '13px', color: '#666', lineHeight: '1.8' }}>
                <div style={{ marginBottom: '8px' }}>
                  <strong>🆔 記錄ID：</strong> 
                  <span style={{ marginLeft: '8px', fontFamily: 'monospace' }}>{previewRecord.id}</span>
                </div>
                {previewRecord.uploaded_by_name && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>👤 上傳者：</strong> 
                    <Tag color="blue" size="small" style={{ marginLeft: '8px' }}>
                      {previewRecord.uploaded_by_name}
                    </Tag>
                  </div>
                )}
                {previewRecord.performance_grade && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🎯 效能等級：</strong> 
                    <Tag 
                      color={
                        previewRecord.performance_grade === '優秀' ? 'green' :
                        previewRecord.performance_grade === '良好' ? 'blue' :
                        previewRecord.performance_grade === '一般' ? 'orange' : 'red'
                      } 
                      style={{ marginLeft: '8px' }}
                    >
                      {previewRecord.performance_grade}
                    </Tag>
                  </div>
                )}
                {previewRecord.created_at && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>📅 建立時間：</strong> 
                    <span style={{ marginLeft: '8px' }}>
                      {new Date(previewRecord.created_at).toLocaleString('zh-TW')}
                    </span>
                  </div>
                )}
                {previewRecord.updated_at && (
                  <div style={{ marginBottom: '8px' }}>
                    <strong>🔄 更新時間：</strong> 
                    <span style={{ marginLeft: '8px' }}>
                      {new Date(previewRecord.updated_at).toLocaleString('zh-TW')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};

export default OcrStorageBenchmarkPage;