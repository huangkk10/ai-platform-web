/**
 * 批量測試執行頁面
 * 
 * 功能：
 * 1. 選擇要測試的版本（支援全選、只選新版本）
 * 2. 選擇測試案例（全部或自訂篩選）
 * 3. 一鍵執行批量測試
 * 4. 顯示測試進度和結果
 * 5. 跳轉到對比報告頁面
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Card,
  Checkbox,
  Button,
  Radio,
  Space,
  Divider,
  Alert,
  Statistic,
  Row,
  Col,
  message,
  Spin,
  Typography,
  InputNumber,
  Select,
  Tag,
} from 'antd';
import {
  RocketOutlined,
  CheckOutlined,
  CloseOutlined,
  ThunderboltOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import benchmarkApi from '../../services/benchmarkApi';
import './BatchTestExecutionPage.css';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const BatchTestExecutionPage = () => {
  const navigate = useNavigate();

  // 版本相關狀態
  const [versions, setVersions] = useState([]);
  const [selectedVersionIds, setSelectedVersionIds] = useState([]);
  const [loadingVersions, setLoadingVersions] = useState(false);

  // 測試案例相關狀態
  const [testCases, setTestCases] = useState([]);
  const [testCaseMode, setTestCaseMode] = useState('all'); // 'all' or 'custom'
  const [customLimit, setCustomLimit] = useState(10);
  const [categoryFilter, setCategoryFilter] = useState(null);
  const [difficultyFilter, setDifficultyFilter] = useState(null);
  const [loadingTestCases, setLoadingTestCases] = useState(false);

  // 執行相關狀態
  const [executing, setExecuting] = useState(false);
  const [forceRetest, setForceRetest] = useState(false);
  const [testResult, setTestResult] = useState(null);

  // 統計資訊
  const [statistics, setStatistics] = useState(null);

  // 載入版本列表
  useEffect(() => {
    loadVersions();
    loadTestCases();
  }, []);

  const loadVersions = async () => {
    setLoadingVersions(true);
    try {
      const response = await benchmarkApi.getVersions();
      // 處理分頁和非分頁兩種格式
      const versionList = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.results || []);
      setVersions(versionList);
      
      // 預設選擇所有版本
      setSelectedVersionIds(versionList.map(v => v.id));
    } catch (error) {
      console.error('載入版本列表失敗:', error);
      message.error('載入版本列表失敗');
    } finally {
      setLoadingVersions(false);
    }
  };

  const loadTestCases = async () => {
    setLoadingTestCases(true);
    try {
      const response = await benchmarkApi.getTestCases({ is_active: true });
      // 處理分頁和非分頁兩種格式
      const testCaseList = Array.isArray(response.data) 
        ? response.data 
        : (response.data?.results || []);
      setTestCases(testCaseList);
      
      // 載入統計資訊
      const statsResponse = await benchmarkApi.getTestCaseStatistics();
      setStatistics(statsResponse.data);
    } catch (error) {
      console.error('載入測試案例失敗:', error);
      message.error('載入測試案例失敗');
    } finally {
      setLoadingTestCases(false);
    }
  };

  // 計算預計測試數量
  const calculateEstimate = () => {
    let caseCount = testCases.length;
    
    if (testCaseMode === 'custom') {
      if (customLimit) {
        caseCount = Math.min(customLimit, caseCount);
      }
      // 應用篩選器
      if (categoryFilter || difficultyFilter) {
        caseCount = testCases.filter(tc => {
          const matchCategory = !categoryFilter || tc.category === categoryFilter;
          const matchDifficulty = !difficultyFilter || tc.difficulty === difficultyFilter;
          return matchCategory && matchDifficulty;
        }).length;
        
        if (customLimit) {
          caseCount = Math.min(customLimit, caseCount);
        }
      }
    }

    const versionCount = selectedVersionIds.length;
    const totalTests = versionCount * caseCount;
    const estimatedTime = Math.ceil(totalTests * 0.5 / 60); // 假設每個測試 0.5 秒

    return { versionCount, caseCount, totalTests, estimatedTime };
  };

  // 處理版本選擇
  const handleVersionCheckChange = (versionId, checked) => {
    if (checked) {
      setSelectedVersionIds([...selectedVersionIds, versionId]);
    } else {
      setSelectedVersionIds(selectedVersionIds.filter(id => id !== versionId));
    }
  };

  const handleSelectAll = () => {
    setSelectedVersionIds(versions.map(v => v.id));
  };

  const handleDeselectAll = () => {
    setSelectedVersionIds([]);
  };

  const handleSelectNewVersionsOnly = () => {
    // 選擇非 baseline 的版本
    const newVersions = versions.filter(v => !v.is_baseline);
    setSelectedVersionIds(newVersions.map(v => v.id));
  };

  // 執行批量測試
  const handleStartBatchTest = async () => {
    if (selectedVersionIds.length === 0) {
      message.warning('請至少選擇一個版本進行測試');
      return;
    }

    const estimate = calculateEstimate();
    if (estimate.caseCount === 0) {
      message.warning('沒有符合條件的測試案例');
      return;
    }

    setExecuting(true);
    setTestResult(null);

    try {
      // 準備請求資料
      const requestData = {
        version_ids: selectedVersionIds,
        batch_name: `批量測試 ${new Date().toLocaleString('zh-TW')}`,
        notes: `測試 ${estimate.versionCount} 個版本，${estimate.caseCount} 個測試案例`,
        force_retest: forceRetest,
      };

      // 如果是自訂模式，添加篩選條件（暫時不支援，API 需要擴展）
      // 目前 API 只支援 version_ids 和 test_case_ids

      console.log('開始批量測試:', requestData);
      message.loading('正在執行批量測試，請稍候...', 0);

      const response = await benchmarkApi.batchTest(requestData);
      
      message.destroy();
      message.success('批量測試完成！');
      
      setTestResult(response.data);

      // 自動跳轉到批量測試歷史頁面
      setTimeout(() => {
        navigate('/benchmark/batch-history');
      }, 1500);

    } catch (error) {
      message.destroy();
      console.error('批量測試失敗:', error);
      
      const errorMsg = error.response?.data?.error || '批量測試執行失敗';
      message.error(errorMsg);
    } finally {
      setExecuting(false);
    }
  };

  const estimate = calculateEstimate();

  // 獲取唯一的類別和難度選項
  const categories = [...new Set(testCases.map(tc => tc.category))].filter(Boolean);
  const difficulties = [...new Set(testCases.map(tc => tc.difficulty))].filter(Boolean);

  return (
    <div className="batch-test-execution-page">
      <Card
        title={
          <Space>
            <RocketOutlined />
            <span>批量版本測試</span>
          </Space>
        }
        extra={
          <Button icon={<ReloadOutlined />} onClick={loadVersions}>
            重新整理
          </Button>
        }
      >
        {/* 說明資訊 */}
        <Alert
          message="批量測試功能"
          description="一次執行多個版本的測試，自動生成對比報告。系統會智能判斷是否需要重新測試，避免重複執行。"
          type="info"
          showIcon
          style={{ marginBottom: 24 }}
        />

        {/* 版本選擇區域 */}
        <Card
          type="inner"
          title="🎯 選擇要測試的版本"
          style={{ marginBottom: 24 }}
          extra={
            <Space>
              <Button size="small" onClick={handleSelectAll}>
                全選
              </Button>
              <Button size="small" onClick={handleDeselectAll}>
                取消全選
              </Button>
              <Button size="small" type="dashed" onClick={handleSelectNewVersionsOnly}>
                只選新版本
              </Button>
            </Space>
          }
        >
          {loadingVersions ? (
            <Spin tip="載入版本列表..." />
          ) : (
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              {versions.map(version => (
                <Card
                  key={version.id}
                  size="small"
                  className={`version-card ${
                    selectedVersionIds.includes(version.id) ? 'selected' : ''
                  }`}
                >
                  <Checkbox
                    checked={selectedVersionIds.includes(version.id)}
                    onChange={(e) => handleVersionCheckChange(version.id, e.target.checked)}
                  >
                    <Space>
                      <Text strong>{version.version_name}</Text>
                      <Text type="secondary">({version.version_code})</Text>
                      {version.is_baseline && (
                        <Tag color="gold" icon={<ThunderboltOutlined />}>
                          基準
                        </Tag>
                      )}
                    </Space>
                  </Checkbox>
                  {version.description && (
                    <Paragraph
                      type="secondary"
                      style={{ marginLeft: 24, marginTop: 8, marginBottom: 0 }}
                    >
                      {version.description}
                    </Paragraph>
                  )}
                </Card>
              ))}
            </Space>
          )}
        </Card>

        {/* 測試案例選擇區域 */}
        <Card
          type="inner"
          title="🎯 選擇測試案例"
          style={{ marginBottom: 24 }}
        >
          <Radio.Group
            value={testCaseMode}
            onChange={(e) => setTestCaseMode(e.target.value)}
            style={{ marginBottom: 16 }}
          >
            <Space direction="vertical">
              <Radio value="all">
                使用所有啟用的測試案例
                {statistics && (
                  <Text type="secondary"> ({statistics.active_count} 個)</Text>
                )}
              </Radio>
              <Radio value="custom">自訂選擇</Radio>
            </Space>
          </Radio.Group>

          {testCaseMode === 'custom' && (
            <Card size="small" style={{ backgroundColor: '#fafafa' }}>
              <Space direction="vertical" style={{ width: '100%' }} size="middle">
                <Row gutter={16}>
                  <Col span={8}>
                    <Text>類別:</Text>
                    <Select
                      placeholder="全部類別"
                      allowClear
                      style={{ width: '100%', marginTop: 8 }}
                      value={categoryFilter}
                      onChange={setCategoryFilter}
                    >
                      {categories.map(cat => (
                        <Option key={cat} value={cat}>
                          {cat}
                        </Option>
                      ))}
                    </Select>
                  </Col>
                  <Col span={8}>
                    <Text>難度:</Text>
                    <Select
                      placeholder="全部難度"
                      allowClear
                      style={{ width: '100%', marginTop: 8 }}
                      value={difficultyFilter}
                      onChange={setDifficultyFilter}
                    >
                      {difficulties.map(diff => (
                        <Option key={diff} value={diff}>
                          {diff}
                        </Option>
                      ))}
                    </Select>
                  </Col>
                  <Col span={8}>
                    <Text>限制數量:</Text>
                    <InputNumber
                      min={1}
                      max={testCases.length}
                      value={customLimit}
                      onChange={setCustomLimit}
                      style={{ width: '100%', marginTop: 8 }}
                      placeholder="不限制"
                    />
                    <Text type="secondary" style={{ fontSize: 12 }}>
                      （用於快速測試）
                    </Text>
                  </Col>
                </Row>
              </Space>
            </Card>
          )}
        </Card>

        {/* 其他選項 */}
        <Card type="inner" title="⚙️ 其他選項" style={{ marginBottom: 24 }}>
          <Checkbox
            checked={forceRetest}
            onChange={(e) => setForceRetest(e.target.checked)}
          >
            強制重新測試
          </Checkbox>
          <Paragraph type="secondary" style={{ marginLeft: 24, marginTop: 8 }}>
            勾選後將重新執行所有測試，即使已有測試結果
          </Paragraph>
        </Card>

        {/* 預計測試資訊 */}
        <Card
          type="inner"
          title="💡 預計測試"
          style={{ marginBottom: 24 }}
          bodyStyle={{ backgroundColor: '#f0f5ff' }}
        >
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="版本數"
                value={estimate.versionCount}
                suffix="個"
                valueStyle={{ color: '#1890ff' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="案例數"
                value={estimate.caseCount}
                suffix="個"
                valueStyle={{ color: '#52c41a' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="總測試"
                value={estimate.totalTests}
                suffix="次"
                valueStyle={{ color: '#722ed1' }}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="預計時間"
                value={estimate.estimatedTime}
                suffix="分鐘"
                valueStyle={{ color: '#fa8c16' }}
              />
            </Col>
          </Row>
        </Card>

        {/* 執行按鈕 */}
        <div style={{ textAlign: 'center' }}>
          <Button
            type="primary"
            size="large"
            icon={<RocketOutlined />}
            loading={executing}
            onClick={handleStartBatchTest}
            disabled={selectedVersionIds.length === 0}
            style={{ minWidth: 200, height: 50, fontSize: 18 }}
          >
            {executing ? '測試執行中...' : '開始批量測試'}
          </Button>
        </div>

        {/* 測試結果（成功後顯示） */}
        {testResult && (
          <Card
            type="inner"
            title="✅ 測試完成"
            style={{ marginTop: 24 }}
            bodyStyle={{ backgroundColor: '#f6ffed' }}
          >
            <Space direction="vertical" style={{ width: '100%' }} size="middle">
              <Row gutter={16}>
                <Col span={8}>
                  <Statistic
                    title="批次 ID"
                    value={testResult.batch_id}
                    valueStyle={{ fontSize: 16 }}
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="測試版本"
                    value={testResult.summary?.total_versions_tested || 0}
                    suffix="個"
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="執行時間"
                    value={testResult.summary?.execution_time || 0}
                    suffix="秒"
                    precision={1}
                  />
                </Col>
              </Row>

              <Divider />

              <div style={{ textAlign: 'center' }}>
                <Space size="large">
                  <Button
                    type="primary"
                    size="large"
                    icon={<CheckOutlined />}
                    onClick={() => navigate('/benchmark/batch-history')}
                  >
                    查看批量測試歷史
                  </Button>
                  <Button
                    size="large"
                    onClick={() => navigate('/benchmark/dashboard')}
                  >
                    返回 Dashboard
                  </Button>
                </Space>
              </div>
            </Space>
          </Card>
        )}
      </Card>
    </div>
  );
};

export default BatchTestExecutionPage;
