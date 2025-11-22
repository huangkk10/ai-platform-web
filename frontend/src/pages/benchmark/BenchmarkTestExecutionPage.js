import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Select,
  Button,
  Alert,
  Progress,
  Spin,
  Tag,
  Space,
  Row,
  Col,
  Statistic,
  Divider,
  message,
} from 'antd';
import { PlayCircleOutlined, ThunderboltOutlined, ReloadOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import benchmarkApi from '../../services/benchmarkApi';
import './BenchmarkTestExecutionPage.css';

const { Option } = Select;

const BenchmarkTestExecutionPage = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();

  // 狀態管理
  const [loading, setLoading] = useState(false);
  const [versions, setVersions] = useState([]);
  const [selectedVersion, setSelectedVersion] = useState(null);
  const [totalTestCases, setTotalTestCases] = useState(0);
  const [isTestRunning, setIsTestRunning] = useState(false);
  const [currentTestRun, setCurrentTestRun] = useState(null);
  const [testProgress, setTestProgress] = useState(0);
  const [pollInterval, setPollInterval] = useState(null);
  const [estimatedTime, setEstimatedTime] = useState({ min: 0, max: 0 });

  // 載入版本列表
  useEffect(() => {
    loadVersions();
    loadTotalTestCases();
  }, []);

  const loadVersions = async () => {
    setLoading(true);
    try {
      console.log('🔄 開始載入版本列表...');
      const response = await benchmarkApi.getVersions();
      console.log('✅ API Response:', response);
      console.log('✅ Response Status:', response.status);
      console.log('✅ Response Data:', response.data);
      console.log('✅ Data Type:', typeof response.data);
      console.log('✅ Is Array:', Array.isArray(response.data));
      
      // 🔧 處理分頁格式：API 回傳 {count, results} 或直接陣列
      let versionList = [];
      if (Array.isArray(response.data)) {
        // 如果是直接陣列（無分頁）
        versionList = response.data;
        console.log('✅ 直接陣列格式');
      } else if (response.data && Array.isArray(response.data.results)) {
        // 如果是分頁格式（有 results 欄位）
        versionList = response.data.results;
        console.log('✅ 分頁格式 - 總數:', response.data.count);
      } else {
        console.warn('⚠️ 未知的資料格式');
      }
      
      console.log('✅ Version List Length:', versionList.length);
      console.log('✅ Version List:', versionList);
      setVersions(versionList);

      if (versionList.length === 0) {
        message.warning('沒有找到任何版本資料');
      } else {
        message.success(`成功載入 ${versionList.length} 個版本`);
      }

      // 自動選擇基準版本
      const baselineVersion = versionList.find((v) => v.is_baseline);
      if (baselineVersion) {
        console.log('✅ Baseline Version:', baselineVersion);
        setSelectedVersion(baselineVersion.id);
        form.setFieldsValue({ version_id: baselineVersion.id });
      } else {
        console.warn('⚠️ 沒有找到基準版本');
        if (versionList.length > 0) {
          // 如果沒有基準版本，選擇第一個
          setSelectedVersion(versionList[0].id);
          form.setFieldsValue({ version_id: versionList[0].id });
        }
      }
    } catch (error) {
      console.error('❌ 載入版本失敗:', error);
      console.error('❌ Error Response:', error.response);
      console.error('❌ Error Status:', error.response?.status);
      console.error('❌ Error Data:', error.response?.data);
      
      const errorMsg = error.response?.status === 403 
        ? '權限不足，請確認您已登入'
        : error.response?.data?.detail || error.message;
      
      message.error(`載入版本列表失敗: ${errorMsg}`);
      setVersions([]); // 確保設為空陣列
    } finally {
      setLoading(false);
      console.log('🏁 版本載入完成');
    }
  };

  const loadTotalTestCases = async () => {
    try {
      const response = await benchmarkApi.getTestCaseStatistics();
      const total = response.data.total || 0;
      setTotalTestCases(total);
      // 估算時間：每個測試案例約 2-3 秒
      setEstimatedTime({
        min: Math.ceil((total * 2) / 60),
        max: Math.ceil((total * 3) / 60),
      });
    } catch (error) {
      console.error('載入測試案例統計失敗:', error);
    }
  };

  // 清理輪詢
  useEffect(() => {
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [pollInterval]);

  // 啟動完整測試
  const handleStartFullTest = async () => {
    if (!selectedVersion) {
      message.warning('請選擇演算法版本');
      return;
    }

    // 獲取測試名稱，如果為空則自動生成
    let runName = form.getFieldValue('run_name');
    if (!runName || !runName.trim()) {
      const now = new Date();
      const dateStr = now.toLocaleDateString('zh-TW', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
      }).replace(/\//g, '-');
      const timeStr = now.toLocaleTimeString('zh-TW', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      runName = `測試 - ${dateStr} ${timeStr}`;
      console.log('🔄 自動生成測試名稱:', runName);
    }

    await startTest({
      version_id: selectedVersion,
      run_name: runName.trim(),
      run_type: 'full',
      notes: '完整測試（所有測試案例）',
    });
  };

  // 啟動快速測試
  const handleStartQuickTest = async () => {
    if (!selectedVersion) {
      message.warning('請選擇演算法版本');
      return;
    }

    // 獲取測試名稱，如果為空則自動生成
    let runName = form.getFieldValue('run_name');
    if (!runName || !runName.trim()) {
      const now = new Date();
      const dateStr = now.toLocaleDateString('zh-TW', { 
        year: 'numeric', 
        month: '2-digit', 
        day: '2-digit' 
      }).replace(/\//g, '-');
      const timeStr = now.toLocaleTimeString('zh-TW', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: false 
      });
      runName = `快速測試 - ${dateStr} ${timeStr}`;
      console.log('🔄 自動生成測試名稱:', runName);
    } else {
      runName = `${runName.trim()} (快速測試)`;
    }

    await startTest({
      version_id: selectedVersion,
      run_name: runName,
      run_type: 'quick',
      limit: 5,
      notes: '快速測試（隨機 5 題）',
    });
  };

  // 啟動測試
  const startTest = async (testData) => {
    setIsTestRunning(true);
    setTestProgress(0);

    try {
      console.log('🚀 正在啟動測試，參數:', testData);
      const response = await benchmarkApi.startTest(testData);
      console.log('✅ 測試啟動成功，回應:', response.data);
      
      // 修復：從 response.data.test_run 取得測試執行資料
      const responseData = response.data;
      const testRun = responseData.test_run || responseData;  // 兼容兩種格式
      
      // 驗證 testRun.id 存在
      if (!testRun || !testRun.id) {
        console.error('❌ 測試啟動回應缺少 ID:', testRun);
        console.error('❌ 完整回應:', responseData);
        message.error('測試啟動失敗：未獲取到測試 ID');
        setIsTestRunning(false);
        return;
      }
      
      console.log('✅ Test Run ID:', testRun.id);
      setCurrentTestRun(testRun);

      // 顯示成功訊息（使用後端返回的訊息或預設訊息）
      message.success(responseData.message || '測試已啟動！');

      // 開始輪詢進度
      startPollingProgress(testRun.id);
    } catch (error) {
      console.error('❌ 啟動測試失敗:', error);
      console.error('❌ 錯誤詳情:', error.response?.data);
      message.error(error.response?.data?.error || '啟動測試失敗');
      setIsTestRunning(false);
    }
  };

  // 輪詢測試進度
  const startPollingProgress = (testRunId) => {
    console.log('🔄 開始輪詢測試進度，Test Run ID:', testRunId);
    
    const interval = setInterval(async () => {
      try {
        const response = await benchmarkApi.getTestRun(testRunId);
        const testRun = response.data;
        setCurrentTestRun(testRun);

        console.log('📊 測試進度更新:', {
          status: testRun.status,
          completed: testRun.completed_test_cases,
          total: testRun.total_test_cases
        });

        // 計算進度百分比（修復：使用正確的欄位名稱）
        const progress = testRun.total_test_cases > 0 
          ? Math.round((testRun.completed_test_cases / testRun.total_test_cases) * 100)
          : 0;
        setTestProgress(progress);

        // 如果測試完成，停止輪詢
        if (testRun.status === 'completed' || testRun.status === 'failed') {
          clearInterval(interval);
          setPollInterval(null);
          setIsTestRunning(false);

          if (testRun.status === 'completed') {
            // 安全地格式化分數（處理字串和數字）
            const score = testRun.overall_score 
              ? parseFloat(testRun.overall_score).toFixed(2) 
              : '0.00';
            
            // 顯示測試結果摘要
            message.success({
              content: `測試執行完成！總分：${score}，完成 ${testRun.completed_test_cases}/${testRun.total_test_cases} 題`,
              duration: 5,
            });
            
            // 3 秒後跳轉到 Dashboard
            setTimeout(() => {
              navigate('/benchmark/dashboard');
              message.info('測試結果已保存，您可以在 Dashboard 查看歷史記錄');
            }, 3000);
          } else {
            message.error('測試執行失敗');
          }
        }
      } catch (error) {
        console.error('❌ 獲取測試進度失敗:', error);
        console.error('❌ 錯誤詳情:', {
          message: error.message,
          response: error.response?.data,
          status: error.response?.status
        });
        
        // 如果持續失敗，停止輪詢
        // 但不顯示錯誤訊息給用戶（避免干擾）
      }
    }, 2000); // 每 2 秒輪詢一次

    setPollInterval(interval);
  };

  // 停止測試
  const handleStopTest = () => {
    if (pollInterval) {
      clearInterval(pollInterval);
      setPollInterval(null);
    }
    setIsTestRunning(false);
    setTestProgress(0);
    setCurrentTestRun(null);
    message.info('測試已停止');
  };

  // 處理版本變更
  const handleVersionChange = (value) => {
    setSelectedVersion(value);
  };

  return (
    <div className="benchmark-test-execution-page">
      <Spin spinning={loading} tip="載入中...">
        <Row gutter={[24, 24]}>
          {/* 左側：測試配置 */}
          <Col xs={24} lg={14}>
            <Card
              title={
                <Space>
                  <PlayCircleOutlined />
                  <span>測試執行</span>
                </Space>
              }
              className="config-card"
              extra={
                <Button icon={<ReloadOutlined />} onClick={loadVersions}>
                  重新整理
                </Button>
              }
            >
              <Form form={form} layout="vertical">
                {/* 調試資訊 */}
                {!loading && versions.length === 0 && (
                  <Alert
                    message="無法載入版本列表"
                    description="請檢查網路連接或稍後再試。您可以點擊右上角的「重新整理」按鈕重新載入。"
                    type="warning"
                    showIcon
                    style={{ marginBottom: '16px' }}
                  />
                )}

                {/* 版本選擇 */}
                <Form.Item
                  name="version_id"
                  label="演算法版本"
                  rules={[{ required: true, message: '請選擇演算法版本' }]}
                >
                  <Select
                    size="large"
                    placeholder={loading ? "載入中..." : "選擇版本"}
                    onChange={handleVersionChange}
                    disabled={isTestRunning || loading}
                    notFoundContent={loading ? <Spin size="small" /> : "沒有可用的版本"}
                  >
                    {Array.isArray(versions) && versions.length > 0 ? (
                      versions.map((version) => (
                        <Option key={version.id} value={version.id}>
                          <Space>
                            <span>{version.version_name}</span>
                            {version.is_baseline && <Tag color="blue">基準版本</Tag>}
                          </Space>
                        </Option>
                      ))
                    ) : null}
                  </Select>
                </Form.Item>

                {/* 測試名稱 */}
                <Form.Item
                  name="run_name"
                  label="測試名稱（選填）"
                  tooltip="留空則自動生成測試名稱"
                >
                  <Input
                    size="large"
                    placeholder="留空則自動生成，例如：測試 - 2025-11-22 08:30"
                    maxLength={200}
                    showCount
                    disabled={isTestRunning}
                  />
                </Form.Item>

                <Divider />

                {/* 操作按鈕 */}
                <Space size="large" style={{ width: '100%', justifyContent: 'center' }}>
                  <Button
                    type="primary"
                    size="large"
                    icon={<PlayCircleOutlined />}
                    onClick={handleStartFullTest}
                    disabled={isTestRunning}
                    style={{ width: '200px', height: '60px', fontSize: '16px' }}
                  >
                    開始完整測試
                  </Button>

                  <Button
                    size="large"
                    icon={<ThunderboltOutlined />}
                    onClick={handleStartQuickTest}
                    disabled={isTestRunning}
                    style={{ width: '200px', height: '60px', fontSize: '16px' }}
                  >
                    快速測試 (5題)
                  </Button>
                </Space>
              </Form>

              {/* 測試進度 */}
              {isTestRunning && currentTestRun && (
                <>
                  <Divider />
                  <Alert
                    message="測試執行中"
                    description={
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <div>
                          測試名稱：{currentTestRun.run_name}
                        </div>
                        <div>
                          進度：{currentTestRun.completed_test_cases || 0} / {currentTestRun.total_test_cases || 0} 題
                        </div>
                        <Progress
                          percent={testProgress}
                          status="active"
                          strokeColor={{
                            '0%': '#108ee9',
                            '100%': '#87d068',
                          }}
                        />
                      </Space>
                    }
                    type="info"
                    showIcon
                    action={
                      <Button size="small" danger onClick={handleStopTest}>
                        停止測試
                      </Button>
                    }
                  />
                </>
              )}
            </Card>
          </Col>

          {/* 右側：測試資訊 */}
          <Col xs={24} lg={10}>
            <Card
              title="測試資訊"
              className="info-card"
              style={{ position: 'sticky', top: '20px' }}
            >
              <Space direction="vertical" size="large" style={{ width: '100%' }}>
                {/* 測試案例統計 */}
                <div>
                  <Statistic
                    title="總測試案例數"
                    value={totalTestCases}
                    suffix="題"
                    valueStyle={{ color: '#1890ff' }}
                  />
                  <Divider style={{ margin: '12px 0' }} />
                  <div style={{ color: '#666', fontSize: '14px' }}>
                    <div>• 完整測試：執行所有 {totalTestCases} 個測試案例</div>
                    <div>• 快速測試：隨機執行 5 個測試案例</div>
                  </div>
                </div>

                <Divider />

                {/* 預估時間 */}
                <div>
                  <Statistic
                    title="完整測試預估時間"
                    value={estimatedTime.min}
                    suffix={`- ${estimatedTime.max} 分鐘`}
                    valueStyle={{ color: '#52c41a' }}
                  />
                  <Divider style={{ margin: '12px 0' }} />
                  <div style={{ color: '#666', fontSize: '14px' }}>
                    <div>• 每題約需 2-3 秒鐘</div>
                    <div>• 實際時間視網路狀況而定</div>
                  </div>
                </div>

                <Divider />

                {/* 選擇的版本資訊 */}
                {selectedVersion && Array.isArray(versions) && versions.find((v) => v.id === selectedVersion) && (
                  <div>
                    <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#333' }}>
                      選擇的版本：
                    </div>
                    <Space direction="vertical" style={{ width: '100%' }}>
                      <div>
                        <Tag color="blue" style={{ fontSize: '14px', padding: '4px 12px' }}>
                          {versions.find((v) => v.id === selectedVersion)?.version_name}
                        </Tag>
                        {versions.find((v) => v.id === selectedVersion)?.is_baseline && (
                          <Tag color="green">基準版本</Tag>
                        )}
                      </div>
                      {versions.find((v) => v.id === selectedVersion)?.description && (
                        <div style={{ color: '#666', fontSize: '13px' }}>
                          {versions.find((v) => v.id === selectedVersion)?.description}
                        </div>
                      )}
                    </Space>
                  </div>
                )}

                <Divider />

                {/* 使用說明 */}
                <Alert
                  message="使用說明"
                  description={
                    <div style={{ fontSize: '13px', lineHeight: '1.8' }}>
                      <div>1. 系統已自動選擇基準版本</div>
                      <div>2. 輸入測試名稱（用於識別此次測試）</div>
                      <div>3. 點擊「開始完整測試」執行所有測試案例</div>
                      <div>4. 或點擊「快速測試」隨機測試 5 題</div>
                      <div>5. 測試完成後將自動跳轉到結果頁面</div>
                    </div>
                  }
                  type="info"
                  showIcon
                />
              </Space>
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default BenchmarkTestExecutionPage;
