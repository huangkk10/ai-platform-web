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
  Alert,
  Tag,
  Divider
} from 'antd';
import {
  EditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  StarOutlined
} from '@ant-design/icons';
import axios from 'axios';

const { Text } = Typography;

// 自訂樣式：僅為標題列添加背景色（方案 A）
const tableStyles = `
  .threshold-settings-table thead th.stage1-header {
    background-color: #e6f7ff !important;
  }
  .threshold-settings-table thead th.stage2-header {
    background-color: #fafafa !important;
  }
  .threshold-settings-table thead .stage1-header th {
    background-color: #f0f8ff !important;
  }
  .threshold-settings-table thead .stage2-header th {
    background-color: #f5f5f5 !important;
  }
`;

// 將樣式注入到頁面
if (typeof document !== 'undefined') {
  const styleId = 'threshold-settings-custom-styles';
  if (!document.getElementById(styleId)) {
    const styleTag = document.createElement('style');
    styleTag.id = styleId;
    styleTag.innerHTML = tableStyles;
    document.head.appendChild(styleTag);
  }
}

const ThresholdSettingsPage = () => {
  // ===== State =====
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

  useEffect(() => {
    fetchSettings();
  }, []);

  // 開啟編輯 Modal（統一編輯所有 6 個欄位）
  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({
      // 一階設定
      stage1_threshold: parseFloat(record.stage1_threshold) * 100,
      stage1_title_weight: record.stage1_title_weight,
      stage1_content_weight: record.stage1_content_weight,
      // 二階設定
      stage2_threshold: parseFloat(record.stage2_threshold) * 100,
      stage2_title_weight: record.stage2_title_weight,
      stage2_content_weight: record.stage2_content_weight
    });
    setEditModalVisible(true);
  };

  // 儲存編輯（更新所有 6 個欄位）
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      setLoading(true);
      // 使用 assistant_type 而不是 id 作為 lookup 欄位
      await axios.patch(`/api/search-threshold-settings/${editingRecord.assistant_type}/`, {
        stage1_threshold: (values.stage1_threshold / 100).toFixed(2),
        stage1_title_weight: values.stage1_title_weight,
        stage1_content_weight: values.stage1_content_weight,
        stage2_threshold: (values.stage2_threshold / 100).toFixed(2),
        stage2_title_weight: values.stage2_title_weight,
        stage2_content_weight: values.stage2_content_weight
      }, { withCredentials: true });

      message.success('設定更新成功！');
      setEditModalVisible(false);
      fetchSettings();
    } catch (error) {
      console.error('更新設定失敗:', error);
      message.error(error.response?.data?.detail || '更新失敗，請稍後再試');
    } finally {
      setLoading(false);
    }
  };

  // 統一表格欄位定義（使用 grouped headers）
  const unifiedColumns = [
    {
      title: 'Assistant',
      dataIndex: 'assistant_type_display',
      key: 'assistant_type_display',
      width: 150,
      fixed: 'left',
      render: (text) => <Tag color="blue" style={{ fontSize: '14px' }}>{text}</Tag>
    },
    {
      title: (
        <Space>
          <StarOutlined style={{ color: '#faad14' }} />
          <span style={{ fontWeight: 'bold', color: '#1890ff' }}>一階設定（常用）</span>
        </Space>
      ),
      className: 'stage1-header',
      children: [
        {
          title: (
            <Space>
              段落向量 Threshold
              <Tooltip title="一階搜尋的相似度閾值（0-100%）">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage1_threshold',
          key: 'stage1_threshold',
          width: 160,
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
              <Tooltip title="一階搜尋中標題向量的權重">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage1_title_weight',
          key: 'stage1_title_weight',
          width: 110,
          render: (value) => (
            <Text style={{ fontSize: '14px', color: '#1890ff' }}>
              {value}%
            </Text>
          )
        },
        {
          title: (
            <Space>
              內容權重
              <Tooltip title="一階搜尋中內容向量的權重">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage1_content_weight',
          key: 'stage1_content_weight',
          width: 110,
          render: (value) => (
            <Text style={{ fontSize: '14px', color: '#1890ff' }}>
              {value}%
            </Text>
          )
        }
      ]
    },
    {
      title: (
        <span style={{ color: '#8c8c8c', fontWeight: 'normal' }}>二階設定（進階）</span>
      ),
      className: 'stage2-header',
      children: [
        {
          title: (
            <Space>
              段落向量 Threshold
              <Tooltip title="二階搜尋的相似度閾值（0-100%）">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage2_threshold',
          key: 'stage2_threshold',
          width: 160,
          render: (value) => (
            <Text style={{ fontSize: '14px', color: '#595959' }}>
              {(parseFloat(value) * 100).toFixed(0)}%
            </Text>
          )
        },
        {
          title: (
            <Space>
              標題權重
              <Tooltip title="二階搜尋中標題向量的權重">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage2_title_weight',
          key: 'stage2_title_weight',
          width: 110,
          render: (value) => (
            <Text style={{ fontSize: '13px', color: '#595959' }}>
              {value}%
            </Text>
          )
        },
        {
          title: (
            <Space>
              內容權重
              <Tooltip title="二階搜尋中內容向量的權重">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage2_content_weight',
          key: 'stage2_content_weight',
          width: 110,
          render: (value) => (
            <Text style={{ fontSize: '13px', color: '#595959' }}>
              {value}%
            </Text>
          )
        }
      ]
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
      {/* 頁面標題和操作按鈕 */}
      <Card>
        <Row justify="space-between" align="middle" style={{ marginBottom: '16px' }}>
          <Col>
            <Space direction="vertical" size={0}>
              <Text strong style={{ fontSize: '20px' }}>Threshold 設定管理</Text>
              <Text type="secondary">統一管理一階（常用）和二階（進階）搜尋參數</Text>
            </Space>
          </Col>
          <Col>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchSettings}
              loading={loading}
            >
              重新整理
            </Button>
          </Col>
        </Row>

        {/* 說明 */}
        <Alert
          message="設定說明"
          description={
            <div>
              <p><StarOutlined style={{ color: '#faad14' }} /> <strong>一階設定（常用）</strong>：用於段落級別的語義搜尋，適合精準查詢</p>
              <p style={{ marginBottom: 0 }}><strong>二階設定（進階）</strong>：用於全文級別的深度搜尋，適合探索性查詢</p>
            </div>
          }
          type="info"
          showIcon
          style={{ marginBottom: '16px' }}
        />

        {/* 統一表格 */}
        <Table
          className="threshold-settings-table"
          columns={unifiedColumns}
          dataSource={settings}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ x: 1400 }}
          bordered
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
        width={900}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          <Alert
            message="設定說明"
            description="設定一階（常用）和二階（進階）搜尋參數。Threshold 控制相似度門檻；權重決定標題與內容的重要性比例。"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />

          {/* 一階設定 */}
          <Card 
            title={
              <Space>
                <StarOutlined style={{ color: '#faad14' }} />
                <span>一階設定（常用）</span>
              </Space>
            }
            size="small" 
            style={{ marginBottom: '24px' }}
          >
            {/* 一階 Threshold */}
            <Form.Item
              label={
                <Space>
                  <span>段落向量 Threshold</span>
                  <Tooltip title="一階搜尋的相似度閾值，範圍 0-100%">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
              }
              name="stage1_threshold"
              rules={[
                { required: true, message: '請設定一階 Threshold' },
                { type: 'number', min: 0, max: 100, message: 'Threshold 必須在 0 到 100 之間' }
              ]}
            >
              <Slider
                min={0}
                max={100}
                step={5}
                marks={{
                  0: '0%',
                  50: '50%',
                  70: '70%',
                  100: '100%'
                }}
                tooltip={{
                  formatter: (value) => `${value}%`
                }}
              />
            </Form.Item>

            {/* 一階權重 */}
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label={
                    <Space>
                      <span>標題權重</span>
                      <Tooltip title="一階搜尋中標題向量的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="stage1_title_weight"
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
                      form.setFieldsValue({ stage1_content_weight: 100 - value });
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
                      <Tooltip title="一階搜尋中內容向量的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="stage1_content_weight"
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
                      form.setFieldsValue({ stage1_title_weight: 100 - value });
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
            />
          </Card>

          <Divider />

          {/* 二階設定 */}
          <Card 
            title={<span>二階設定（進階）</span>}
            size="small"
          >
            {/* 二階 Threshold */}
            <Form.Item
              label={
                <Space>
                  <span>段落向量 Threshold</span>
                  <Tooltip title="二階搜尋的相似度閾值，範圍 0-100%">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
              }
              name="stage2_threshold"
              rules={[
                { required: true, message: '請設定二階 Threshold' },
                { type: 'number', min: 0, max: 100, message: 'Threshold 必須在 0 到 100 之間' }
              ]}
            >
              <Slider
                min={0}
                max={100}
                step={5}
                marks={{
                  0: '0%',
                  50: '50%',
                  70: '70%',
                  100: '100%'
                }}
                tooltip={{
                  formatter: (value) => `${value}%`
                }}
              />
            </Form.Item>

            {/* 二階權重 */}
            <Row gutter={16}>
              <Col span={12}>
                <Form.Item
                  label={
                    <Space>
                      <span>標題權重</span>
                      <Tooltip title="二階搜尋中標題向量的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="stage2_title_weight"
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
                      form.setFieldsValue({ stage2_content_weight: 100 - value });
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
                      <Tooltip title="二階搜尋中內容向量的權重">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="stage2_content_weight"
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
                      form.setFieldsValue({ stage2_title_weight: 100 - value });
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
            />
          </Card>
        </Form>
      </Modal>
    </div>
  );
};

export default ThresholdSettingsPage;
