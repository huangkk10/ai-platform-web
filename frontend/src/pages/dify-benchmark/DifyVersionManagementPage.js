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
import BatchTestProgressModal from '../../components/dify-benchmark/BatchTestProgressModal';
import './DifyVersionManagementPage.css';

const { TextArea } = Input;

const DifyVersionManagementPage = () => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [statisticsModalVisible, setStatisticsModalVisible] = useState(false);
  const [batchTestModalVisible, setBatchTestModalVisible] = useState(false);
  const [progressModalVisible, setProgressModalVisible] = useState(false);
  const [currentBatchId, setCurrentBatchId] = useState(null);
  const [editingVersion, setEditingVersion] = useState(null);
  const [versionStatistics, setVersionStatistics] = useState(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [form] = Form.useForm();
  const [batchTestForm] = Form.useForm();

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

  // 開啟批量測試 Modal
  const handleOpenBatchTest = () => {
    if (selectedRowKeys.length === 0) {
      message.warning('請至少選擇一個版本進行測試');
      return;
    }
    
    // 設定預設批次名稱
    batchTestForm.setFieldsValue({
      batch_name: `批量測試 ${new Date().toLocaleString('zh-TW')}`,
      notes: '',
      force_retest: false,
      use_parallel: true,
      max_workers: 10
    });
    
    setBatchTestModalVisible(true);
  };

  // 執行批量測試
  const handleExecuteBatchTest = async () => {
    console.log('🚀 ========== 批量測試開始 ==========');
    console.log('🚀 handleExecuteBatchTest 被調用');
    console.log('📊 選中的版本 IDs:', selectedRowKeys);
    console.log('📊 選中的版本數量:', selectedRowKeys.length);
    
    try {
      // 步驟 1: 驗證表單
      console.log('📝 步驟 1: 開始驗證表單...');
      const values = await batchTestForm.validateFields();
      console.log('✅ 表單驗證通過');
      console.log('📋 表單數據:', JSON.stringify(values, null, 2));
      
      // 步驟 2: 生成批次 ID
      console.log('📝 步驟 2: 生成批次 ID...');
      const batchId = `batch_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
      console.log('✅ 生成批次 ID:', batchId);
      
      // 步驟 3: 關閉配置 Modal
      console.log('📝 步驟 3: 關閉配置 Modal...');
      setBatchTestModalVisible(false);
      console.log('✅ 配置 Modal 已關閉');
      
      // 步驟 4: 準備請求數據
      console.log('📝 步驟 4: 準備 API 請求數據...');
      const requestData = {
        version_ids: selectedRowKeys,
        test_case_ids: null,  // null = 使用所有啟用的測試案例
        batch_name: values.batch_name,
        notes: values.notes,
        force_retest: values.force_retest,
        use_parallel: values.use_parallel,
        max_workers: values.max_workers,
        batch_id: batchId  // 傳遞 batch_id 用於進度追蹤
      };
      console.log('✅ 請求數據準備完成');
      console.log('📤 完整請求數據:', JSON.stringify(requestData, null, 2));
      
      // 步驟 5: 檢查 API 方法是否存在
      console.log('📝 步驟 5: 檢查 API 方法...');
      console.log('🔍 difyBenchmarkApi 對象:', difyBenchmarkApi);
      console.log('🔍 batchTestDifyVersions 方法:', typeof difyBenchmarkApi.batchTestDifyVersions);
      
      if (typeof difyBenchmarkApi.batchTestDifyVersions !== 'function') {
        console.error('❌ batchTestDifyVersions 不是一個函數！');
        throw new Error('API 方法不存在');
      }
      
      // 步驟 6: 發送 API 請求（⚠️ 必須先發送，再打開進度 Modal）
      console.log('📝 步驟 6: 發送 API 請求...');
      console.log('🌐 準備呼叫 difyBenchmarkApi.batchTestDifyVersions()');
      
      // 發送批量測試請求，等待請求發送成功後才打開進度 Modal
      difyBenchmarkApi.batchTestDifyVersions(requestData)
        .then((response) => {
          console.log('✅ ========== API 呼叫成功 ==========');
          console.log('📥 回應狀態:', response.status);
          console.log('📥 回應數據:', response.data);
          console.log('📥 完整回應:', response);
          
          // ✅ POST 成功後才打開進度 Modal（確保後端已初始化 ProgressTracker）
          console.log('📝 步驟 7: API 成功，現在設定 batch_id 並打開 Modal...');
          console.log('🔍 [批次 ID] 當前新生成的 batch_id:', batchId);
          console.log('🔍 [State] 設定前的 currentBatchId:', currentBatchId);
          
          // 先設定 batch_id
          setCurrentBatchId(batchId);
          console.log('✅ [State] setCurrentBatchId() 已調用，新值:', batchId);
          
          // ✅ 延遲 500ms 後再打開 Modal，確保後端完全初始化 ProgressTracker
          setTimeout(() => {
            console.log('🔍 [渲染] 延遲後準備打開 Modal');
            setProgressModalVisible(true);
            console.log('✅ [Modal] 進度 Modal 已設為可見');
            console.log('✅ [確認] BatchTestProgressModal 應該會收到 batchId:', batchId);
          }, 500);  // ⚠️ 改為 500ms 延遲
          
          message.success('批量測試已啟動');
        })
        .catch((error) => {
          console.error('❌ ========== API 呼叫失敗 ==========');
          console.error('❌ 錯誤對象:', error);
          console.error('❌ 錯誤類型:', error.constructor.name);
          console.error('❌ 錯誤訊息:', error.message);
          
          if (error.response) {
            // 伺服器回應錯誤（4xx, 5xx）
            console.error('🔴 伺服器回應錯誤:');
            console.error('   - 狀態碼:', error.response.status);
            console.error('   - 狀態文字:', error.response.statusText);
            console.error('   - 回應頭:', error.response.headers);
            console.error('   - 回應數據:', error.response.data);
          } else if (error.request) {
            // 請求已發送但沒有收到回應
            console.error('🔴 沒有收到伺服器回應:');
            console.error('   - 請求:', error.request);
          } else {
            // 其他錯誤（請求配置錯誤等）
            console.error('🔴 請求配置錯誤:', error.message);
          }
          
          console.error('🔴 錯誤堆疊:', error.stack);
          
          message.error(`批量測試執行失敗: ${error.response?.data?.error || error.message || '未知錯誤'}`);
          // ❌ 失敗時不打開進度 Modal
        });
      
      console.log('📝 API 請求已發送，等待回應中...');
      console.log('✅ ========== 批量測試初始化完成 ==========');
      
    } catch (error) {
      console.error('❌ ========== 批量測試初始化失敗 ==========');
      console.error('❌ 捕獲異常:', error);
      console.error('❌ 異常類型:', error.constructor.name);
      console.error('❌ 異常訊息:', error.message);
      console.error('❌ 異常堆疊:', error.stack);
      
      if (error.errorFields) {
        console.error('❌ 表單驗證錯誤:', error.errorFields);
        message.error('請填寫所有必填欄位');
      } else {
        message.error(`初始化失敗: ${error.message}`);
      }
    }
  };
  
  // 批量測試完成回調
  const handleBatchTestComplete = (progressData) => {
    console.log('批量測試完成:', progressData);
    
    // 顯示成功訊息
    message.success(
      `批量測試已完成！共執行 ${progressData.total_tests} 個測試，` +
      `成功 ${progressData.completed_tests - progressData.failed_tests} 個，` +
      `失敗 ${progressData.failed_tests} 個`
    );
    
    // 重新載入版本列表
    fetchVersions();
    
    // 清空選擇
    setSelectedRowKeys([]);
    
    // 延遲關閉進度 Modal（讓用戶看到完成狀態）
    setTimeout(() => {
      setProgressModalVisible(false);
      setCurrentBatchId(null);
    }, 2500);
  };
  
  // 取消/關閉進度 Modal
  const handleProgressModalCancel = () => {
    Modal.confirm({
      title: '確定要關閉進度視窗嗎？',
      content: '測試仍在後台執行，關閉視窗不會停止測試。',
      okText: '確定關閉',
      cancelText: '繼續查看',
      onOk: () => {
        setProgressModalVisible(false);
        setCurrentBatchId(null);
      }
    });
  };

  // Table rowSelection 配置
  const rowSelection = {
    selectedRowKeys,
    onChange: (newSelectedRowKeys) => {
      setSelectedRowKeys(newSelectedRowKeys);
    },
    getCheckboxProps: (record) => ({
      disabled: !record.is_active,  // 停用的版本無法選擇
      name: record.version_name,
    }),
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
            <span>VSA 配置版本管理</span>
            {selectedRowKeys.length > 0 && (
              <Tag color="blue">已選擇 {selectedRowKeys.length} 個版本</Tag>
            )}
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
              icon={<RocketOutlined />}
              onClick={handleOpenBatchTest}
              disabled={selectedRowKeys.length === 0}
            >
              批量測試 ({selectedRowKeys.length})
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
          rowSelection={rowSelection}
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

      {/* 批量測試 Modal */}
      <Modal
        title="批量測試配置"
        open={batchTestModalVisible}
        onOk={handleExecuteBatchTest}
        onCancel={() => setBatchTestModalVisible(false)}
        width={600}
        okText="開始測試"
        cancelText="取消"
        confirmLoading={loading}
      >
        <Form
          form={batchTestForm}
          layout="vertical"
        >
          <Form.Item
            label="批次名稱"
            name="batch_name"
            rules={[{ required: true, message: '請輸入批次名稱' }]}
          >
            <Input placeholder="例如：效能對比測試 v1" />
          </Form.Item>

          <Form.Item
            label="備註"
            name="notes"
          >
            <TextArea 
              rows={3} 
              placeholder="測試目的、預期結果等備註資訊（可選）" 
            />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                label="並行線程數"
                name="max_workers"
                rules={[{ required: true, message: '請輸入線程數' }]}
                tooltip="建議設定為 5-10，數值越大測試越快，但會增加系統負載"
              >
                <Input type="number" min={1} max={20} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                label="是否強制重測"
                name="force_retest"
                valuePropName="checked"
                tooltip="啟用後，即使已有測試結果也會重新執行"
              >
                <Switch checkedChildren="是" unCheckedChildren="否" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            label="啟用並行執行"
            name="use_parallel"
            valuePropName="checked"
            tooltip="建議保持啟用，可大幅提升測試速度（約 60-80%）"
          >
            <Switch checkedChildren="啟用" unCheckedChildren="停用" />
          </Form.Item>

          <div style={{ 
            marginTop: '16px', 
            padding: '12px', 
            background: '#f0f2f5', 
            borderRadius: '4px' 
          }}>
            <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
              <strong>測試配置摘要：</strong>
            </p>
            <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px', fontSize: '13px' }}>
              <li>選擇版本數：<strong>{selectedRowKeys.length}</strong> 個</li>
              <li>測試案例：<strong>所有啟用的案例</strong></li>
              <li>預估時間：約 {Math.ceil(selectedRowKeys.length * 15 / 10)} 秒（10 線程並行）</li>
            </ul>
          </div>
        </Form>
      </Modal>
      
      {/* 批量測試進度 Modal */}
      <BatchTestProgressModal
        visible={progressModalVisible}
        batchId={currentBatchId}
        onComplete={handleBatchTestComplete}
        onCancel={handleProgressModalCancel}
      />
    </div>
  );
};

export default DifyVersionManagementPage;
