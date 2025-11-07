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
  Tag
} from 'antd';
import {
  EditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Title, Text, Paragraph } = Typography;

const ThresholdSettingsPage = () => {
  const [settings, setSettings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState(null);
  const [form] = Form.useForm();
  const [cacheInfo, setCacheInfo] = useState(null);

  // 載入設定資料
  const fetchSettings = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/threshold-settings/', { withCredentials: true });
      // DRF 分頁回應格式：{ count, next, previous, results }
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
    // fetchCacheInfo(); // 暫時註釋掉，這不是核心功能
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

  return (
    <div style={{ padding: '24px' }}>
      {/* 操作按鈕 */}
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
    </div>
  );
};

export default ThresholdSettingsPage;
