import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Slider,
  message,
  Space,
  Tooltip,
  Typography,
  Row,
  Col,
  Statistic,
  Alert,
  Tag,
  Tabs,
  Input,
  Divider,
  List
} from 'antd';
import {
  EditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  SearchOutlined,
  ThunderboltOutlined,
  SettingOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;
const { TextArea } = Input;

const ThresholdSettingsPage = () => {
  // ===== 統一 State（使用 SearchThresholdSetting API）=====
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();

  // 載入設定資料（使用 SearchThresholdSetting API，包含所有 stage1/stage2 資料）
  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/search-threshold-settings/', { withCredentials: true });
      const data = Array.isArray(response.data) ? response.data : response.data.results || [];
      setSettings(data);
      message.success('設定載入成功');
    } catch (error) {
      console.error('載入設定失敗:', error);
      message.error('載入設定失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 載入快取資訊
  const fetchCacheInfo = async () => {
    try {
      // 使用正確的 URL（DRF 會將底線轉換為破折號）
      const response = await axios.get('/api/threshold-settings/get_cache_info/', { withCredentials: true });
      setCacheInfo(response.data);
    } catch (error) {
      // 快取資訊不是必要的，失敗也不影響主要功能
      console.warn('快取資訊載入失敗（不影響主要功能）:', error.message);
    }
  };

  useEffect(() => {
    fetchSettings();
  }, []);

  // 開啟編輯 Modal
  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({
      master_threshold: parseFloat(record.master_threshold) * 100, // 轉換為百分比
      title_weight: record.title_weight !== null && record.title_weight !== undefined ? record.title_weight : 60,
      content_weight: record.content_weight !== null && record.content_weight !== undefined ? record.content_weight : 40
    });
    setEditModalVisible(true);
  };

  // 儲存編輯
  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      const thresholdValue = values.master_threshold / 100; // 轉換回 0-1 範圍

      setLoading(true);
      await axios.patch(`/api/threshold-settings/${editingRecord.id}/`, {
        master_threshold: thresholdValue.toFixed(2),
        title_weight: values.title_weight,
        content_weight: values.content_weight
      }, { withCredentials: true });

      // 自動刷新快取
      try {
        await axios.post('/api/threshold-settings/refresh-cache/', {}, { withCredentials: true });
      } catch (cacheError) {
        console.error('自動刷新快取失敗:', cacheError);
        // 不中斷流程，只記錄錯誤
      }

      message.success('設定更新成功！快取已自動刷新。');
      setEditModalVisible(false);
      fetchSettings();
      fetchCacheInfo();
    } catch (error) {
      console.error('更新設定失敗:', error);
      message.error(error.response?.data?.master_threshold?.[0] || '更新失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 計算顯示的 Threshold 值（即時計算）
  const [currentThreshold, setCurrentThreshold] = useState(70);

  const calculateThresholds = (masterThreshold) => {
    const master = masterThreshold / 100;
    return {
      master: master.toFixed(2),
      vector_section: master.toFixed(2),
      vector_document: (master * 0.85).toFixed(2),
      keyword: (master * 0.5).toFixed(2)
    };
  };

  // ========== 搜尋權重配置功能 ==========

  // 載入搜尋權重設定
  const fetchWeightSettings = async () => {
    setWeightLoading(true);
    try {
      const response = await axios.get('/api/search-threshold-settings/', { withCredentials: true });
      const data = Array.isArray(response.data) ? response.data : response.data.results || [];
      setWeightSettings(data);
      message.success('搜尋權重設定載入成功');
    } catch (error) {
      console.error('載入搜尋權重設定失敗:', error);
      message.error('載入搜尋權重設定失敗');
    } finally {
      setWeightLoading(false);
    }
  };

  // 開啟編輯搜尋權重 Modal
  const handleEditWeight = (record) => {
    setEditingWeightRecord(record);
    weightForm.setFieldsValue({
      vector_section_weight: record.vector_section_weight,
      vector_document_weight: record.vector_document_weight,
      keyword_weight: record.keyword_weight
    });
    setEditWeightModalVisible(true);
  };

  // 儲存搜尋權重編輯
  const handleSaveWeight = async () => {
    try {
      const values = await weightForm.validateFields();
      
      // 驗證權重總和是否為 100
      const totalWeight = values.vector_section_weight + values.vector_document_weight + values.keyword_weight;
      if (totalWeight !== 100) {
        message.error(`權重總和必須為 100%，當前為 ${totalWeight}%`);
        return;
      }

      setWeightLoading(true);
      await axios.patch(`/api/search-threshold-settings/${editingWeightRecord.id}/`, values, { 
        withCredentials: true 
      });

      message.success('搜尋權重設定更新成功！');
      setEditWeightModalVisible(false);
      fetchWeightSettings();
    } catch (error) {
      console.error('更新搜尋權重設定失敗:', error);
      message.error(error.response?.data?.detail || '更新失敗，請稍後再試');
    } finally {
      setWeightLoading(false);
    }
  };

  // 測試搜尋功能
  const handleTestSearch = async () => {
    if (!testQuery.trim()) {
      message.warning('請輸入測試查詢');
      return;
    }

    if (!editingWeightRecord) {
      message.error('請先選擇要測試的 Assistant');
      return;
    }

    setTestLoading(true);
    setTestResults(null);

    try {
      const values = weightForm.getFieldsValue();
      
      const response = await axios.post(
        `/api/search-threshold-settings/${editingWeightRecord.id}/test_search/`,
        {
          query: testQuery,
          vector_section_weight: values.vector_section_weight,
          vector_document_weight: values.vector_document_weight,
          keyword_weight: values.keyword_weight
        },
        { withCredentials: true }
      );

      setTestResults(response.data);
      message.success('測試搜尋完成');
    } catch (error) {
      console.error('測試搜尋失敗:', error);
      message.error(error.response?.data?.detail || '測試失敗，請稍後再試');
    } finally {
      setTestLoading(false);
    }
  };

  // 重置為預設值
  const handleResetWeights = () => {
    weightForm.setFieldsValue({
      vector_section_weight: 60,
      vector_document_weight: 30,
      keyword_weight: 10
    });
    message.info('已重置為預設權重：段落 60% / 文檔 30% / 關鍵字 10%');
  };

  // 表格欄位定義
  const columns = [
    {
      title: 'Assistant 類型',
      dataIndex: 'assistant_type_display',
      key: 'assistant_type_display',
      width: 180,
      render: (text) => <Tag color="blue" style={{ fontSize: '14px' }}>{text}</Tag>
    },
    {
      title: (
        <Space>
          段落向量 Threshold
          <Tooltip title="語義搜尋的相似度閾值（0-100%）">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'master_threshold',
      key: 'master_threshold',
      width: 150,
      render: (value) => (
        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
          {(parseFloat(value) * 100).toFixed(0)}%
        </Text>
      )
    },
    {
      title: (
        <Space>
          標題權重
          <Tooltip title="標題向量在多向量搜尋中的權重">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'title_weight',
      key: 'title_weight',
      width: 120,
      render: (value) => (
        <Text style={{ fontSize: '14px', color: '#52c41a' }}>
          {value}%
        </Text>
      )
    },
    {
      title: (
        <Space>
          內容權重
          <Tooltip title="內容向量在多向量搜尋中的權重">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'content_weight',
      key: 'content_weight',
      width: 120,
      render: (value) => (
        <Text style={{ fontSize: '14px', color: '#fa8c16' }}>
          {value}%
        </Text>
      )
    },
    {
      title: '最後更新',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (text) => new Date(text).toLocaleString('zh-TW')
    },
    {
      title: '更新者',
      dataIndex: 'updated_by_username',
      key: 'updated_by_username',
      width: 120,
      render: (text) => text || '-'
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<EditOutlined />}
          onClick={() => handleEdit(record)}
        >
          編輯
        </Button>
      )
    }
  ];

  // ===== 搜尋權重配置表格欄位 =====
  const weightColumns = [
    {
      title: 'Assistant 類型',
      dataIndex: 'assistant_type_display',
      key: 'assistant_type_display',
      width: 180,
      render: (text) => <Tag color="purple" style={{ fontSize: '14px' }}>{text}</Tag>
    },
    {
      title: (
        <Space>
          段落向量權重
          <Tooltip title="段落語義向量在搜尋中的權重">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'vector_section_weight',
      key: 'vector_section_weight',
      width: 140,
      render: (value) => (
        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
          {value}%
        </Text>
      )
    },
    {
      title: (
        <Space>
          文檔向量權重
          <Tooltip title="文檔級別向量在搜尋中的權重">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'vector_document_weight',
      key: 'vector_document_weight',
      width: 140,
      render: (value) => (
        <Text style={{ fontSize: '14px', color: '#52c41a' }}>
          {value}%
        </Text>
      )
    },
    {
      title: (
        <Space>
          關鍵字權重
          <Tooltip title="關鍵字匹配在搜尋中的權重">
            <InfoCircleOutlined />
          </Tooltip>
        </Space>
      ),
      dataIndex: 'keyword_weight',
      key: 'keyword_weight',
      width: 120,
      render: (value) => (
        <Text style={{ fontSize: '14px', color: '#fa8c16' }}>
          {value}%
        </Text>
      )
    },
    {
      title: '最後更新',
      dataIndex: 'updated_at',
      key: 'updated_at',
      width: 180,
      render: (text) => new Date(text).toLocaleString('zh-TW')
    },
    {
      title: '操作',
      key: 'action',
      width: 100,
      fixed: 'right',
      render: (_, record) => (
        <Button
          type="primary"
          icon={<EditOutlined />}
          onClick={() => handleEditWeight(record)}
        >
          編輯
        </Button>
      )
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Tab 導航 */}
      <Card>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          size="large"
          items={[
            {
              key: 'basic',
              label: (
                <span>
                  <SettingOutlined />
                  基礎設定
                </span>
              ),
              children: (
                <>
                  {/* 基礎設定內容 */}
                  <Row justify="end" align="middle" style={{ marginBottom: '16px' }}>
                    <Col>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={() => {
                          fetchSettings();
                          fetchCacheInfo();
                        }}
                      >
                        重新整理
                      </Button>
                    </Col>
                  </Row>

                  {/* 快取狀態卡片 */}
                  {cacheInfo && (
                    <Card
                      title="快取狀態"
                      style={{ marginBottom: '24px' }}
                      extra={<Tag color={cacheInfo.cached_assistants.length > 0 ? 'green' : 'orange'}>
                        {cacheInfo.cached_assistants.length > 0 ? '快取有效' : '快取空'}
                      </Tag>}
                    >
                      <Row gutter={16}>
                        <Col span={8}>
                          <Statistic
                            title="快取的 Assistant 數量"
                            value={cacheInfo.cached_assistants.length}
                            prefix={<CheckCircleOutlined />}
                          />
                        </Col>
                        <Col span={8}>
                          <Statistic
                            title="快取 TTL"
                            value={cacheInfo.cache_ttl}
                            suffix="秒"
                          />
                        </Col>
                        <Col span={8}>
                          <div>
                            <Text strong>已快取:</Text>
                            <div style={{ marginTop: '8px' }}>
                              {cacheInfo.cached_assistants.length > 0 ? (
                                cacheInfo.cached_assistants.map(assistant => (
                                  <Tag key={assistant} color="green" style={{ marginBottom: '4px' }}>
                                    {assistant}
                                  </Tag>
                                ))
                              ) : (
                                <Text type="secondary">無</Text>
                              )}
                            </div>
                          </div>
                        </Col>
                      </Row>
                    </Card>
                  )}

                  {/* 設定列表表格 */}
                  <Card>
                    <Table
                      columns={columns}
                      dataSource={settings}
                      rowKey="id"
                      loading={loading}
                      pagination={false}
                      scroll={{ x: 1400 }}
                    />
                  </Card>
                </>
              )
            },
            {
              key: 'weights',
              label: (
                <span>
                  <ThunderboltOutlined />
                  搜尋權重配置
                </span>
              ),
              children: (
                <>
                  {/* 搜尋權重配置內容 */}
                  <Alert
                    message="搜尋權重配置說明"
                    description="設定不同搜尋方式的權重比例。段落向量：語義搜尋；文檔向量：整體匹配；關鍵字：精確匹配。權重總和必須為 100%。"
                    type="info"
                    showIcon
                    style={{ marginBottom: '16px' }}
                  />

                  <Row justify="end" align="middle" style={{ marginBottom: '16px' }}>
                    <Col>
                      <Button
                        icon={<ReloadOutlined />}
                        onClick={fetchWeightSettings}
                      >
                        重新整理
                      </Button>
                    </Col>
                  </Row>

                  {/* 搜尋權重列表表格 */}
                  <Card>
                    <Table
                      columns={weightColumns}
                      dataSource={weightSettings}
                      rowKey="id"
                      loading={weightLoading}
                      pagination={false}
                      scroll={{ x: 1200 }}
                    />
                  </Card>
                </>
              )
            }
          ]}
        />
      </Card>

      {/* 編輯 Modal */}
      <Modal
        title={`編輯 ${editingRecord?.assistant_type_display} 搜尋參數`}
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
        okText="儲存"
        cancelText="取消"
        width={700}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          <Alert
            message="說明"
            description="設定語義搜尋的相似度閾值和多向量權重。Threshold 值越高搜尋越精準；權重決定標題與內容的重要性比例。"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          {/* Threshold 設定 */}
          <Form.Item
            label={
              <Space>
                <span>段落向量 Threshold</span>
                <Tooltip title="語義搜尋相似度閾值，範圍 0-100%">
                  <InfoCircleOutlined />
                </Tooltip>
              </Space>
            }
            name="master_threshold"
            rules={[
              { required: true, message: '請設定 Threshold' },
              { type: 'number', min: 0, max: 100, message: 'Threshold 必須在 0 到 100 之間' }
            ]}
          >
            <Slider
              min={0}
              max={100}
              step={5}
              marks={{
                0: '0%',
                30: '30%',
                50: '50%',
                70: '70%',
                100: '100%'
              }}
              onChange={(value) => setCurrentThreshold(value)}
              tooltip={{
                formatter: (value) => `${value}%`
              }}
            />
          </Form.Item>

          {/* 多向量權重設定 */}
          <Card 
            title="多向量權重設定" 
            size="small" 
            style={{ marginTop: '24px', marginBottom: '16px' }}
          >
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label={
                    <Space>
                      <span>標題權重</span>
                      <Tooltip title="標題向量在搜尋中的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="title_weight"
                  rules={[
                    { required: true, message: '請設定標題權重' },
                    { type: 'number', min: 0, max: 100, message: '權重必須在 0 到 100 之間' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    onChange={(value) => {
                      // 自動調整內容權重
                      form.setFieldsValue({ content_weight: 100 - value });
                    }}
                    tooltip={{
                      formatter: (value) => `${value}%`
                    }}
                  />
                </Form.Item>
              </Col>
              <Col span={12}>
                <Form.Item
                  label={
                    <Space>
                      <span>內容權重</span>
                      <Tooltip title="內容向量在搜尋中的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="content_weight"
                  rules={[
                    { required: true, message: '請設定內容權重' },
                    { type: 'number', min: 0, max: 100, message: '權重必須在 0 到 100 之間' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    onChange={(value) => {
                      // 自動調整標題權重
                      form.setFieldsValue({ title_weight: 100 - value });
                    }}
                    tooltip={{
                      formatter: (value) => `${value}%`
                    }}
                  />
                </Form.Item>
              </Col>
            </Row>

            <Alert
              message="💡 提示：標題權重 + 內容權重 = 100%"
              type="warning"
              showIcon
              style={{ marginTop: '8px' }}
            />

            {/* 預設場景快速設定 */}
            <div style={{ marginTop: '16px' }}>
              <Text strong>預設場景：</Text>
              <Space style={{ marginTop: '8px' }} wrap>
                <Button
                  size="small"
                  onClick={() => {
                    form.setFieldsValue({ title_weight: 80, content_weight: 20 });
                  }}
                >
                  品牌/型號查詢 (80%/20%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    form.setFieldsValue({ title_weight: 60, content_weight: 40 });
                  }}
                >
                  平衡查詢 (60%/40%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    form.setFieldsValue({ title_weight: 40, content_weight: 60 });
                  }}
                >
                  強調內容 (40%/60%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    form.setFieldsValue({ title_weight: 20, content_weight: 80 });
                  }}
                >
                  深度內容搜索 (20%/80%)
                </Button>
              </Space>
            </div>
          </Card>

          {/* 即時預覽 */}
          <Card title="即時預覽" size="small" style={{ backgroundColor: '#f0f5ff' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Threshold"
                  value={currentThreshold}
                  suffix="%"
                  valueStyle={{ color: '#1890ff', fontSize: '20px' }}
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="權重比例"
                  value={`${form.getFieldValue('title_weight') || 60} : ${form.getFieldValue('content_weight') || 40}`}
                  valueStyle={{ color: '#52c41a', fontSize: '20px' }}
                />
              </Col>
            </Row>
          </Card>
        </Form>
      </Modal>

      {/* 編輯搜尋權重 Modal */}
      <Modal
        title={`編輯 ${editingWeightRecord?.assistant_type_display} 搜尋權重`}
        open={editWeightModalVisible}
        onOk={handleSaveWeight}
        onCancel={() => {
          setEditWeightModalVisible(false);
          setTestResults(null);
          setTestQuery('');
        }}
        okText="儲存"
        cancelText="取消"
        width={900}
        confirmLoading={weightLoading}
      >
        <Form form={weightForm} layout="vertical">
          <Alert
            message="說明"
            description="設定不同搜尋方式的權重比例。三種權重總和必須為 100%。"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          {/* 權重設定 */}
          <Card title="權重配置" size="small" style={{ marginBottom: '16px' }}>
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>段落向量權重</span>
                      <Tooltip title="語義搜尋的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="vector_section_weight"
                  rules={[
                    { required: true, message: '請設定段落向量權重' },
                    { type: 'number', min: 0, max: 100, message: '權重必須在 0 到 100 之間' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    tooltip={{
                      formatter: (value) => `${value}%`
                    }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>文檔向量權重</span>
                      <Tooltip title="文檔級別搜尋的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="vector_document_weight"
                  rules={[
                    { required: true, message: '請設定文檔向量權重' },
                    { type: 'number', min: 0, max: 100, message: '權重必須在 0 到 100 之間' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    tooltip={{
                      formatter: (value) => `${value}%`
                    }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>關鍵字權重</span>
                      <Tooltip title="關鍵字匹配的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="keyword_weight"
                  rules={[
                    { required: true, message: '請設定關鍵字權重' },
                    { type: 'number', min: 0, max: 100, message: '權重必須在 0 到 100 之間' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={100}
                    step={5}
                    marks={{
                      0: '0%',
                      50: '50%',
                      100: '100%'
                    }}
                    tooltip={{
                      formatter: (value) => `${value}%`
                    }}
                  />
                </Form.Item>
              </Col>
            </Row>

            {/* 即時顯示權重總和 */}
            <Alert
              message={
                <span>
                  當前權重總和：
                  <Text strong style={{ 
                    color: (weightForm.getFieldValue('vector_section_weight') || 0) + 
                           (weightForm.getFieldValue('vector_document_weight') || 0) + 
                           (weightForm.getFieldValue('keyword_weight') || 0) === 100 
                      ? '#52c41a' 
                      : '#ff4d4f',
                    fontSize: '16px',
                    marginLeft: '8px'
                  }}>
                    {(weightForm.getFieldValue('vector_section_weight') || 0) + 
                     (weightForm.getFieldValue('vector_document_weight') || 0) + 
                     (weightForm.getFieldValue('keyword_weight') || 0)}%
                  </Text>
                  <Text type="secondary" style={{ marginLeft: '8px' }}>
                    (必須為 100%)
                  </Text>
                </span>
              }
              type={
                (weightForm.getFieldValue('vector_section_weight') || 0) + 
                (weightForm.getFieldValue('vector_document_weight') || 0) + 
                (weightForm.getFieldValue('keyword_weight') || 0) === 100 
                  ? 'success' 
                  : 'warning'
              }
              showIcon
              style={{ marginTop: '8px' }}
            />

            {/* 預設場景快速設定 */}
            <div style={{ marginTop: '16px' }}>
              <Text strong>預設場景：</Text>
              <Space style={{ marginTop: '8px' }} wrap>
                <Button
                  size="small"
                  onClick={handleResetWeights}
                >
                  預設 (60%/30%/10%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    weightForm.setFieldsValue({
                      vector_section_weight: 70,
                      vector_document_weight: 20,
                      keyword_weight: 10
                    });
                  }}
                >
                  強調語義 (70%/20%/10%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    weightForm.setFieldsValue({
                      vector_section_weight: 40,
                      vector_document_weight: 40,
                      keyword_weight: 20
                    });
                  }}
                >
                  平衡搜尋 (40%/40%/20%)
                </Button>
                <Button
                  size="small"
                  onClick={() => {
                    weightForm.setFieldsValue({
                      vector_section_weight: 30,
                      vector_document_weight: 30,
                      keyword_weight: 40
                    });
                  }}
                >
                  強調關鍵字 (30%/30%/40%)
                </Button>
              </Space>
            </div>
          </Card>

          {/* 測試搜尋功能 */}
          <Card title="即時測試" size="small" style={{ backgroundColor: '#f0f5ff' }}>
            <Space.Compact style={{ width: '100%', marginBottom: '16px' }}>
              <Input
                placeholder="輸入測試查詢..."
                value={testQuery}
                onChange={(e) => setTestQuery(e.target.value)}
                onPressEnter={handleTestSearch}
                prefix={<SearchOutlined />}
              />
              <Button
                type="primary"
                loading={testLoading}
                onClick={handleTestSearch}
                icon={<SearchOutlined />}
              >
                測試搜尋
              </Button>
            </Space.Compact>

            {testResults && (
              <>
                <Divider>搜尋結果</Divider>
                <Row gutter={16} style={{ marginBottom: '16px' }}>
                  <Col span={8}>
                    <Statistic
                      title="找到結果數"
                      value={testResults.total_found}
                      prefix={<CheckCircleOutlined />}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="搜尋耗時"
                      value={testResults.search_time}
                      suffix="秒"
                      precision={3}
                    />
                  </Col>
                  <Col span={8}>
                    <Statistic
                      title="使用配置"
                      value={testResults.used_temporary_config ? '臨時' : '資料庫'}
                      valueStyle={{ 
                        color: testResults.used_temporary_config ? '#fa8c16' : '#52c41a' 
                      }}
                    />
                  </Col>
                </Row>

                {testResults.results && testResults.results.length > 0 && (
                  <List
                    size="small"
                    bordered
                    dataSource={testResults.results}
                    renderItem={(item, index) => (
                      <List.Item>
                        <List.Item.Meta
                          title={
                            <Space>
                              <Tag color="blue">#{index + 1}</Tag>
                              <Text strong>{item.title}</Text>
                              <Tag color="green">相似度: {(item.similarity * 100).toFixed(1)}%</Tag>
                            </Space>
                          }
                          description={
                            <Text ellipsis style={{ maxWidth: '100%' }}>
                              {item.content.substring(0, 150)}...
                            </Text>
                          }
                        />
                      </List.Item>
                    )}
                  />
                )}

                {(!testResults.results || testResults.results.length === 0) && (
                  <Alert
                    message="未找到符合條件的結果"
                    type="warning"
                    showIcon
                  />
                )}
              </>
            )}
          </Card>
        </Form>
      </Modal>
    </div>
  );
};

export default ThresholdSettingsPage;
