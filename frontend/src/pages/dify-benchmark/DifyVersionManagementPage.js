import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Switch,
  Space,
  Tag,
  message,
  Popconfirm,
  Tooltip,
  Row,
  Col,
  Statistic,
  Badge,
  Descriptions
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  RocketOutlined,
  StarOutlined,
  StarFilled,
  LineChartOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import difyBenchmarkApi from '../../services/difyBenchmarkApi';
import './DifyVersionManagementPage.css';

const { TextArea } = Input;

const DifyVersionManagementPage = () => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [statisticsModalVisible, setStatisticsModalVisible] = useState(false);
  const [editingVersion, setEditingVersion] = useState(null);
  const [versionStatistics, setVersionStatistics] = useState(null);
  const [form] = Form.useForm();

  // 獲取版本列表
  const fetchVersions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await difyBenchmarkApi.getDifyVersions();
      setVersions(response.data.results || response.data);
    } catch (error) {
      message.error('獲取版本列表失敗');
      console.error('獲取版本失敗:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchVersions();
  }, [fetchVersions]);

  // 開啟新增/編輯 Modal
  const handleOpenModal = (version = null) => {
    setEditingVersion(version);
    if (version) {
      form.setFieldsValue({
        version_name: version.version_name,
        version_code: version.version_code,
        description: version.description,
        dify_app_id: version.dify_app_id,
        dify_api_key: version.dify_api_key,
        dify_api_url: version.dify_api_url,
        is_active: version.is_active
      });
    } else {
      form.resetFields();
      form.setFieldsValue({
        is_active: true,
        dify_api_url: 'http://10.10.172.37/v1/chat-messages'
      });
    }
    setModalVisible(true);
  };

  // 儲存版本
  const handleSaveVersion = async () => {
    try {
      const values = await form.validateFields();
      setLoading(true);

      if (editingVersion) {
        // 更新
        await difyBenchmarkApi.updateDifyVersion(editingVersion.id, values);
        message.success('版本更新成功');
      } else {
        // 新增
        await difyBenchmarkApi.createDifyVersion(values);
        message.success('版本創建成功');
      }

      setModalVisible(false);
      fetchVersions();
    } catch (error) {
      if (error.errorFields) {
        message.error('請填寫所有必填欄位');
      } else {
        message.error(editingVersion ? '更新版本失敗' : '創建版本失敗');
        console.error('儲存版本失敗:', error);
      }
    } finally {
      setLoading(false);
    }
  };

  // 刪除版本
  const handleDeleteVersion = async (versionId) => {
    setLoading(true);
    try {
      await difyBenchmarkApi.deleteDifyVersion(versionId);
      message.success('版本刪除成功');
      fetchVersions();
    } catch (error) {
      message.error('刪除版本失敗');
      console.error('刪除版本失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 設定為 Baseline
  const handleSetBaseline = async (versionId) => {
    setLoading(true);
    try {
      await difyBenchmarkApi.setDifyBaseline(versionId);
      message.success('Baseline 版本設定成功');
      fetchVersions();
    } catch (error) {
      message.error('設定 Baseline 失敗');
      console.error('設定 Baseline 失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 執行測試
  const handleRunTest = async (versionId) => {
    Modal.confirm({
      title: '執行測試',
      content: '是否對此版本執行完整測試？（將使用所有啟用的測試案例）',
      okText: '執行',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true);
        try {
          const response = await difyBenchmarkApi.runDifyBenchmark(versionId, {
            run_name: `測試執行 ${new Date().toLocaleString()}`
          });
          
          if (response.data.success) {
            message.success('測試執行完成！');
            // 可以導航到測試結果頁面
            // navigate(`/dify-benchmark/test-runs/${response.data.test_run_id}`);
          } else {
            message.error(response.data.error || '測試執行失敗');
          }
        } catch (error) {
          message.error('執行測試失敗');
          console.error('執行測試失敗:', error);
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 查看統計
  const handleViewStatistics = async (versionId) => {
    setLoading(true);
    try {
      const response = await difyBenchmarkApi.getDifyVersionStatistics(versionId);
      setVersionStatistics(response.data);
      setStatisticsModalVisible(true);
    } catch (error) {
      message.error('獲取統計資料失敗');
      console.error('獲取統計失敗:', error);
    } finally {
      setLoading(false);
    }
  };

  // 表格欄位定義
  const columns = [
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 250,
      render: (text, record) => (
        <Space>
          {record.is_baseline && (
            <Tooltip title="Baseline 版本">
              <StarFilled style={{ color: '#faad14' }} />
            </Tooltip>
          )}
          <span style={{ fontWeight: record.is_baseline ? 'bold' : 'normal' }}>
            {text}
          </span>
        </Space>
      )
    },
    {
      title: '版本代碼',
      dataIndex: 'version_code',
      key: 'version_code',
      width: 200
    },
    {
      title: 'Dify App ID',
      dataIndex: 'dify_app_id',
      key: 'dify_app_id',
      width: 180,
      render: (text) => (
        <code style={{ fontSize: '12px', color: '#666' }}>{text}</code>
      )
    },
    {
      title: '狀態',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive) => (
        <Badge 
          status={isActive ? 'success' : 'default'} 
          text={isActive ? '啟用' : '停用'} 
        />
      )
    },
    {
      title: '測試次數',
      dataIndex: 'test_run_count',
      key: 'test_run_count',
      width: 100,
      align: 'center',
      render: (count) => (
        <Tag color="blue">{count || 0} 次</Tag>
      )
    },
    {
      title: '創建時間',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (text) => new Date(text).toLocaleString('zh-TW')
    },
    {
      title: '操作',
      key: 'action',
      width: 280,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {!record.is_baseline && (
            <Tooltip title="設為 Baseline">
              <Button
                type="link"
                size="small"
                icon={<StarOutlined />}
                onClick={() => handleSetBaseline(record.id)}
              >
                Baseline
              </Button>
            </Tooltip>
          )}
          <Tooltip title="執行測試">
            <Button
              type="link"
              size="small"
              icon={<RocketOutlined />}
              onClick={() => handleRunTest(record.id)}
            >
              測試
            </Button>
          </Tooltip>
          <Tooltip title="查看統計">
            <Button
              type="link"
              size="small"
              icon={<LineChartOutlined />}
              onClick={() => handleViewStatistics(record.id)}
            >
              統計
            </Button>
          </Tooltip>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleOpenModal(record)}
          >
            編輯
          </Button>
          <Popconfirm
            title="確定要刪除此版本嗎？"
            description="刪除後將無法恢復，所有相關測試記錄也將被刪除。"
            onConfirm={() => handleDeleteVersion(record.id)}
            okText="確定"
            cancelText="取消"
          >
            <Button
              type="link"
              size="small"
              danger
              icon={<DeleteOutlined />}
            >
              刪除
            </Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div className="dify-version-management-page">
      <Card
        title={
          <Space>
            <RocketOutlined />
            <span>Dify 配置版本管理</span>
          </Space>
        }
        extra={
          <Space>
            <Button
              icon={<ReloadOutlined />}
              onClick={fetchVersions}
            >
              重新整理
            </Button>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => handleOpenModal()}
            >
              新增版本
            </Button>
          </Space>
        }
      >
        <Table
          columns={columns}
          dataSource={versions}
          rowKey="id"
          loading={loading}
          scroll={{ x: 1400 }}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showTotal: (total) => `共 ${total} 個版本`
          }}
        />
      </Card>

      {/* 新增/編輯 Modal */}
      <Modal
        title={editingVersion ? '編輯版本' : '新增版本'}
        open={modalVisible}
        onOk={handleSaveVersion}
        onCancel={() => setModalVisible(false)}
        width={800}
        confirmLoading={loading}
        okText="儲存"
        cancelText="取消"
      >
        <Form
          form={form}
          layout="vertical"
          initialValues={{
            is_active: true,
            dify_api_url: 'http://10.10.172.37/v1/chat-messages'
          }}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="版本名稱"
                name="version_name"
                rules={[{ required: true, message: '請輸入版本名稱' }]}
              >
                <Input placeholder="例如：Dify 二階搜尋 v1.1" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="版本代碼"
                name="version_code"
                rules={[{ required: true, message: '請輸入版本代碼' }]}
              >
                <Input placeholder="例如：dify-two-tier-v1.1" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="描述"
            name="description"
          >
            <TextArea
              rows={4}
              placeholder="詳細描述此版本的配置和特點..."
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="Dify App ID"
                name="dify_app_id"
                rules={[{ required: true, message: '請輸入 Dify App ID' }]}
              >
                <Input placeholder="app-xxxxxxxxxxxxx" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="Dify API Key"
                name="dify_api_key"
                rules={[{ required: true, message: '請輸入 Dify API Key' }]}
              >
                <Input.Password placeholder="app-xxxxxxxxxxxxx" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="Dify API URL"
            name="dify_api_url"
            rules={[{ required: true, message: '請輸入 Dify API URL' }]}
          >
            <Input placeholder="http://10.10.172.37/v1/chat-messages" />
          </Form.Item>

          <Form.Item
            label="啟用狀態"
            name="is_active"
            valuePropName="checked"
          >
            <Switch checkedChildren="啟用" unCheckedChildren="停用" />
          </Form.Item>
        </Form>
      </Modal>

      {/* 統計 Modal */}
      <Modal
        title="版本統計資料"
        open={statisticsModalVisible}
        onCancel={() => setStatisticsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setStatisticsModalVisible(false)}>
            關閉
          </Button>
        ]}
        width={700}
      >
        {versionStatistics && (
          <>
            <Row gutter={16} style={{ marginBottom: '24px' }}>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="測試次數"
                    value={versionStatistics.total_test_runs}
                    suffix="次"
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="平均分數"
                    value={versionStatistics.average_score || 0}
                    precision={2}
                    suffix="分"
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card>
                  <Statistic
                    title="平均通過率"
                    value={versionStatistics.average_pass_rate || 0}
                    precision={2}
                    suffix="%"
                  />
                </Card>
              </Col>
            </Row>

            <Descriptions
              title="詳細統計"
              bordered
              column={2}
              size="small"
            >
              <Descriptions.Item label="版本名稱" span={2}>
                {versionStatistics.version_name}
              </Descriptions.Item>
              <Descriptions.Item label="最高分數">
                {(() => {
                  const score = versionStatistics.best_score;
                  const numScore = typeof score === 'string' ? parseFloat(score) : score;
                  return numScore ? `${numScore.toFixed(2)} 分` : 'N/A';
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="最低分數">
                {(() => {
                  const score = versionStatistics.worst_score;
                  const numScore = typeof score === 'string' ? parseFloat(score) : score;
                  return numScore ? `${numScore.toFixed(2)} 分` : 'N/A';
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="測試次數" span={2}>
                {versionStatistics.total_test_runs} 次
              </Descriptions.Item>
            </Descriptions>

            {versionStatistics.recent_runs && versionStatistics.recent_runs.length > 0 && (
              <>
                <h4 style={{ marginTop: '24px', marginBottom: '12px' }}>最近測試記錄</h4>
                <Table
                  dataSource={versionStatistics.recent_runs}
                  columns={[
                    {
                      title: '測試名稱',
                      dataIndex: 'run_name',
                      key: 'run_name'
                    },
                    {
                      title: '分數',
                      dataIndex: 'average_score',
                      key: 'average_score',
                      render: (score) => {
                        const numScore = typeof score === 'string' ? parseFloat(score) : score;
                        return `${numScore?.toFixed(2) || 0} 分`;
                      }
                    },
                    {
                      title: '通過率',
                      dataIndex: 'pass_rate',
                      key: 'pass_rate',
                      render: (rate) => {
                        const numRate = typeof rate === 'string' ? parseFloat(rate) : rate;
                        return `${numRate?.toFixed(2) || 0}%`;
                      }
                    },
                    {
                      title: '測試時間',
                      dataIndex: 'created_at',
                      key: 'created_at',
                      render: (text) => new Date(text).toLocaleString('zh-TW')
                    }
                  ]}
                  rowKey="id"
                  size="small"
                  pagination={false}
                />
              </>
            )}
          </>
        )}
      </Modal>
    </div>
  );
};

export default DifyVersionManagementPage;
