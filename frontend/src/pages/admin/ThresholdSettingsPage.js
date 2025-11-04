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
      const response = await axios.get('/api/threshold-settings/get-cache-info/', { withCredentials: true });
      setCacheInfo(response.data);
    } catch (error) {
      console.error('載入快取資訊失敗:', error);
    }
  };

  useEffect(() => {
    fetchSettings();
    fetchCacheInfo();
  }, []);

  // 開啟編輯 Modal
  const handleEdit = (record) => {
    setEditingRecord(record);
    form.setFieldsValue({
      master_threshold: parseFloat(record.master_threshold) * 100 // 轉換為百分比
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
        master_threshold: thresholdValue.toFixed(2)
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
      width: 200,
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
      width: 200,
      render: (value) => (
        <Text strong style={{ fontSize: '16px', color: '#1890ff' }}>
          {(parseFloat(value) * 100).toFixed(0)}%
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
        title={`編輯 ${editingRecord?.assistant_type_display} 搜尋閾值`}
        open={editModalVisible}
        onOk={handleSave}
        onCancel={() => setEditModalVisible(false)}
        okText="儲存"
        cancelText="取消"
        width={600}
        confirmLoading={loading}
      >
        <Form form={form} layout="vertical">
          <Alert
            message="說明"
            description="設定語義搜尋的相似度閾值。值越高，搜尋結果越精準但數量越少；值越低，結果越多但相關性可能較低。"
            type="info"
            showIcon
            style={{ marginBottom: '24px' }}
          />

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

          {/* 即時預覽 */}
          <Card title="即時預覽" size="small" style={{ marginTop: '16px', backgroundColor: '#f0f5ff' }}>
            <Statistic
              title="設定值"
              value={currentThreshold}
              suffix="%"
              valueStyle={{ color: '#1890ff', fontSize: '24px' }}
            />
            <Paragraph type="secondary" style={{ marginTop: '8px', marginBottom: 0 }}>
              只有相似度 ≥ {currentThreshold}% 的結果會被返回
            </Paragraph>
          </Card>
        </Form>
      </Modal>
    </div>
  );
};

export default ThresholdSettingsPage;
