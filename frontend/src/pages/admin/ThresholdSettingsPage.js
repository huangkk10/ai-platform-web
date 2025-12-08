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
  Divider,
  Checkbox,
  Radio
} from 'antd';
import {
  EditOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  StarOutlined,
  ExpandOutlined
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

  // 開啟編輯 Modal（統一編輯所有欄位）
  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({
      // 一階設定
      stage1_threshold: parseFloat(record.stage1_threshold) * 100,
      stage1_title_weight: record.stage1_title_weight,
      stage1_content_weight: record.stage1_content_weight,
      stage1_rrf_k: record.stage1_rrf_k || 60,  // 🆕 RRF K 值
      // 二階設定
      stage2_threshold: parseFloat(record.stage2_threshold) * 100,
      stage2_title_weight: record.stage2_title_weight,
      stage2_content_weight: record.stage2_content_weight,
      // Window 擴展設定
      context_window: record.context_window || 0,
      include_siblings: record.include_siblings || false,
      context_mode: record.context_mode || 'hierarchical'
    });
    setEditModalVisible(true);
  };

  // 儲存編輯（更新所有欄位）
  const handleSave = async () => {
    try {
      const values = await form.validateFields();

      setLoading(true);
      // 使用 assistant_type 而不是 id 作為 lookup 欄位
      await axios.patch(`/api/search-threshold-settings/${editingRecord.assistant_type}/`, {
        stage1_threshold: (values.stage1_threshold / 100).toFixed(2),
        stage1_title_weight: values.stage1_title_weight,
        stage1_content_weight: values.stage1_content_weight,
        stage1_rrf_k: values.stage1_rrf_k,  // 🆕 RRF K 值
        stage2_threshold: (values.stage2_threshold / 100).toFixed(2),
        stage2_title_weight: values.stage2_title_weight,
        stage2_content_weight: values.stage2_content_weight,
        // Window 擴展設定
        context_window: values.context_window,
        include_siblings: values.include_siblings,
        context_mode: values.context_mode
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
        },
        {
          title: (
            <Space>
              RRF K 值
              <Tooltip title="RRF 融合常數（30-120）。影響向量與關鍵字搜尋的融合權重。較小值讓頂部結果更突出；較大值讓結果更平均。業界標準: 60">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'stage1_rrf_k',
          key: 'stage1_rrf_k',
          width: 100,
          render: (value) => (
            <Tag color="purple" style={{ fontSize: '14px' }}>
              {value || 60}
            </Tag>
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
      title: (
        <Space>
          <ExpandOutlined style={{ color: '#52c41a' }} />
          <span style={{ fontWeight: 'bold', color: '#52c41a' }}>Window 擴展</span>
        </Space>
      ),
      children: [
        {
          title: (
            <Space>
              擴展範圍
              <Tooltip title="向上下各擴展的段落數量（0 表示不擴展）">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'context_window',
          key: 'context_window',
          width: 100,
          render: (value) => (
            <Text style={{ fontSize: '14px', color: '#52c41a' }}>
              {value === 0 ? '關閉' : `±${value}`}
            </Text>
          )
        },
        {
          title: (
            <Space>
              擴展模式
              <Tooltip title="層級結構：同一父節點下的段落；線性視窗：相鄰段落">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'context_mode',
          key: 'context_mode',
          width: 110,
          render: (value) => {
            const modeMap = {
              'hierarchical': { text: '層級', color: 'blue' },
              'adjacent': { text: '線性', color: 'orange' },
              'both': { text: '兩者', color: 'purple' }
            };
            const mode = modeMap[value] || { text: value, color: 'default' };
            return <Tag color={mode.color}>{mode.text}</Tag>;
          }
        },
        {
          title: (
            <Space>
              包含同層
              <Tooltip title="是否包含同一父節點下的兄弟段落">
                <InfoCircleOutlined />
              </Tooltip>
            </Space>
          ),
          dataIndex: 'include_siblings',
          key: 'include_siblings',
          width: 90,
          render: (value) => (
            <Tag color={value ? 'green' : 'default'}>
              {value ? '是' : '否'}
            </Tag>
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
          scroll={{ x: 1700 }}
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
              style={{ marginBottom: 16 }}
            />

            {/* 🆕 RRF K 值設定 */}
            <Form.Item
              label={
                <Space>
                  <span>RRF 融合 K 值</span>
                  <Tooltip title="影響向量與關鍵字搜尋的融合權重。較小值(30-50)讓頂部結果更突出；較大值(80-120)讓結果更平均。業界標準: 60">
                    <InfoCircleOutlined />
                  </Tooltip>
                </Space>
              }
              name="stage1_rrf_k"
              rules={[
                { required: true, message: '請設定 RRF K 值' },
                { type: 'number', min: 30, max: 120, message: 'RRF K 值必須在 30 到 120 之間' }
              ]}
            >
              <Slider
                min={30}
                max={120}
                step={5}
                marks={{
                  30: '30',
                  60: '60 (標準)',
                  90: '90',
                  120: '120'
                }}
                tooltip={{
                  formatter: (value) => `K = ${value}`
                }}
              />
            </Form.Item>

            <Alert
              message={
                <Space direction="vertical" size={2}>
                  <span><strong>💡 RRF K 值說明（向量 + 關鍵字融合）：</strong></span>
                  <span>• <strong>K 值較小 (30-50)</strong>：排名靠前的結果權重更高</span>
                  <span style={{ paddingLeft: 16, color: '#666' }}>
                    → 關鍵字精確匹配的結果更容易排到前面，適合已知精確術語的查詢
                  </span>
                  <span>• <strong>K 值較大 (80-120)</strong>：排名差異對分數的影響減小</span>
                  <span style={{ paddingLeft: 16, color: '#666' }}>
                    → 向量語義搜尋的結果有更多機會出現，適合探索性或模糊查詢
                  </span>
                  <span style={{ marginTop: 4, color: '#1890ff' }}>
                    📐 公式：RRF_score = 1/(K + rank)，K 越大分數差異越小
                  </span>
                </Space>
              }
              type="info"
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

          <Divider />

          {/* Window 擴展設定 */}
          <Card 
            title={
              <Space>
                <ExpandOutlined style={{ color: '#52c41a' }} />
                <span>Window 擴展設定</span>
              </Space>
            }
            size="small"
          >
            <Row gutter={16}>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>擴展範圍</span>
                      <Tooltip title="向上下各擴展的段落數量，0 表示不擴展">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="context_window"
                  rules={[
                    { required: true, message: '請設定擴展範圍' }
                  ]}
                >
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    marks={{
                      0: '關閉',
                      1: '1',
                      2: '2',
                      3: '3',
                      5: '5'
                    }}
                    tooltip={{
                      formatter: (value) => value === 0 ? '關閉' : `±${value} 段落`
                    }}
                  />
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>擴展模式</span>
                      <Tooltip title="層級結構：同一父節點下的段落；線性視窗：相鄰段落">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="context_mode"
                  rules={[
                    { required: true, message: '請選擇擴展模式' }
                  ]}
                >
                  <Radio.Group>
                    <Radio.Button value="hierarchical">層級結構</Radio.Button>
                    <Radio.Button value="adjacent">線性視窗</Radio.Button>
                    <Radio.Button value="both">兩者兼具</Radio.Button>
                  </Radio.Group>
                </Form.Item>
              </Col>
              <Col span={8}>
                <Form.Item
                  label={
                    <Space>
                      <span>包含同層段落</span>
                      <Tooltip title="是否包含同一父節點下的所有兄弟段落">
                        <InfoCircleOutlined />
                      </Tooltip>
                    </Space>
                  }
                  name="include_siblings"
                  valuePropName="checked"
                >
                  <Checkbox>啟用</Checkbox>
                </Form.Item>
              </Col>
            </Row>

            <Alert
              message="💡 提示：擴展範圍設為 0 表示不進行上下文擴展，直接返回原始搜尋結果"
              type="info"
              showIcon
            />
          </Card>
        </Form>
      </Modal>
    </div>
  );
};

export default ThresholdSettingsPage;
