/**
 * BatchTestProgressModal 組件
 * 
 * 顯示批量測試的即時進度
 * 
 * 功能：
 * - 整體進度條（0-100%）
 * - 連接狀態指示器
 * - 當前執行資訊（版本、測試案例）
 * - 已完成/總數、預估剩餘時間
 * - 各版本詳細進度（子進度條）
 * - 測試完成後自動顯示結果摘要
 * 
 * Props:
 * - visible: 是否顯示 Modal
 * - batchId: 批次 ID（用於追蹤進度）
 * - onComplete: 測試完成回調
 * - onCancel: 取消/關閉回調
 * 
 * 作者: AI Platform Team
 * 日期: 2025-11-24
 */

import React, { useEffect, useState } from 'react';
import { Modal, Progress, Space, Tag, Typography, Alert, Divider, Card, Row, Col, Statistic } from 'antd';
import {
  CheckCircleOutlined,
  CloseCircleOutlined,
  SyncOutlined,
  RocketOutlined,
  ClockCircleOutlined,
  FireOutlined
} from '@ant-design/icons';
import useBatchTestProgress from '../../hooks/useBatchTestProgress';

const { Title, Text } = Typography;

const BatchTestProgressModal = ({ visible, batchId, onComplete, onCancel }) => {
  const { progress, progressData, isConnected, error } = useBatchTestProgress(batchId);
  const [hasCompleted, setHasCompleted] = useState(false);
  
  // 監聽測試完成
  useEffect(() => {
    if (progressData && progressData.status === 'completed' && !hasCompleted) {
      setHasCompleted(true);
      
      // 延遲 2 秒後觸發完成回調（讓用戶看到 100% 進度）
      setTimeout(() => {
        if (onComplete) {
          onComplete(progressData);
        }
      }, 2000);
    }
  }, [progressData, hasCompleted, onComplete]);
  
  // 格式化時間（秒 → 分:秒）
  const formatTime = (seconds) => {
    if (!seconds || seconds < 0) return '計算中...';
    
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    
    if (mins > 0) {
      return `${mins} 分 ${secs} 秒`;
    }
    return `${secs} 秒`;
  };
  
  // 獲取狀態標籤
  const getStatusTag = (status) => {
    const statusConfig = {
      'pending': { color: 'default', icon: <ClockCircleOutlined />, text: '等待中' },
      'running': { color: 'processing', icon: <SyncOutlined spin />, text: '執行中' },
      'completed': { color: 'success', icon: <CheckCircleOutlined />, text: '已完成' },
      'error': { color: 'error', icon: <CloseCircleOutlined />, text: '失敗' }
    };
    
    const config = statusConfig[status] || statusConfig['pending'];
    
    return (
      <Tag color={config.color} icon={config.icon}>
        {config.text}
      </Tag>
    );
  };
  
  // Modal 標題
  const modalTitle = (
    <Space>
      <RocketOutlined />
      <span>批量測試進度</span>
      {isConnected && <Tag color="green">即時同步</Tag>}
      {error && <Tag color="red">連接錯誤</Tag>}
    </Space>
  );
  
  return (
    <Modal
      title={modalTitle}
      open={visible}
      onCancel={onCancel}
      footer={null}
      width={800}
      maskClosable={false}
      keyboard={false}
    >
      {/* 錯誤提示 */}
      {error && (
        <Alert
          message="連接錯誤"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 16 }}
        />
      )}
      
      {/* 載入中（無進度資料） */}
      {!progressData && !error && (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <SyncOutlined spin style={{ fontSize: 48, color: '#1890ff' }} />
          <div style={{ marginTop: 16 }}>
            <Text type="secondary">正在啟動測試...</Text>
          </div>
        </div>
      )}
      
      {/* 進度資料顯示 */}
      {progressData && (
        <div>
          {/* 批次資訊 */}
          <Card size="small" style={{ marginBottom: 16, background: '#f0f2f5' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text strong>批次名稱: </Text>
                <Text>{progressData.batch_name}</Text>
              </Col>
              <Col span={12}>
                <Text strong>批次 ID: </Text>
                <Text code style={{ fontSize: 12 }}>{progressData.batch_id}</Text>
              </Col>
            </Row>
          </Card>
          
          {/* 整體進度 */}
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
              <Text strong>整體進度</Text>
              <Text strong style={{ fontSize: 16, color: '#1890ff' }}>
                {progress.toFixed(1)}%
              </Text>
            </div>
            <Progress
              percent={progress}
              status={progressData.status === 'error' ? 'exception' : 'active'}
              strokeColor={{
                '0%': '#108ee9',
                '100%': '#87d068'
              }}
              strokeWidth={12}
            />
          </div>
          
          {/* 統計資訊 */}
          <Row gutter={16} style={{ marginBottom: 24 }}>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="已完成"
                  value={progressData.completed_tests}
                  suffix={`/ ${progressData.total_tests}`}
                  valueStyle={{ color: '#3f8600', fontSize: 20 }}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="失敗"
                  value={progressData.failed_tests}
                  valueStyle={{ color: progressData.failed_tests > 0 ? '#cf1322' : '#666', fontSize: 20 }}
                  prefix={progressData.failed_tests > 0 ? <CloseCircleOutlined /> : null}
                />
              </Card>
            </Col>
            <Col span={8}>
              <Card size="small">
                <Statistic
                  title="預估剩餘"
                  value={formatTime(progressData.estimated_remaining_time)}
                  valueStyle={{ fontSize: 16 }}
                  prefix={<ClockCircleOutlined />}
                />
              </Card>
            </Col>
          </Row>
          
          {/* 當前執行資訊 */}
          {progressData.status === 'running' && progressData.current_version && (
            <Alert
              message="當前執行"
              description={
                <div>
                  <div>
                    <FireOutlined style={{ color: '#ff4d4f', marginRight: 8 }} />
                    <Text strong>版本: </Text>
                    <Text>{progressData.current_version}</Text>
                  </div>
                  {progressData.current_test_case && (
                    <div style={{ marginTop: 4 }}>
                      <Text strong>測試案例: </Text>
                      <Text>{progressData.current_test_case}</Text>
                    </div>
                  )}
                </div>
              }
              type="info"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}
          
          {/* 版本詳細進度 */}
          {progressData.versions && progressData.versions.length > 0 && (
            <>
              <Divider orientation="left">各版本進度</Divider>
              <div style={{ maxHeight: 300, overflowY: 'auto', padding: '0 8px' }}>
                {progressData.versions.map((version) => (
                  <div
                    key={version.version_id}
                    style={{
                      marginBottom: 16,
                      padding: 12,
                      background: version.status === 'running' ? '#f0f5ff' : '#fafafa',
                      borderRadius: 4,
                      border: version.status === 'running' ? '1px solid #91d5ff' : '1px solid #d9d9d9'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Space>
                        <Text strong>{version.version_name}</Text>
                        {getStatusTag(version.status)}
                      </Space>
                      <Space>
                        {version.status === 'completed' && version.average_score !== null && (
                          <Tag color="blue">
                            分數: {version.average_score.toFixed(2)}
                          </Tag>
                        )}
                        {version.status === 'completed' && version.pass_rate !== null && (
                          <Tag color="green">
                            通過率: {version.pass_rate.toFixed(1)}%
                          </Tag>
                        )}
                      </Space>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center' }}>
                      <Progress
                        percent={version.progress}
                        size="small"
                        status={version.status === 'error' ? 'exception' : undefined}
                        style={{ flex: 1, marginRight: 16 }}
                      />
                      <Text type="secondary" style={{ fontSize: 12 }}>
                        {version.completed_tests}/{version.total_tests}
                      </Text>
                    </div>
                  </div>
                ))}
              </div>
            </>
          )}
          
          {/* 完成狀態 */}
          {progressData.status === 'completed' && (
            <Alert
              message="測試完成！"
              description="所有版本的測試已成功完成。即將關閉此視窗..."
              type="success"
              showIcon
              icon={<CheckCircleOutlined />}
              style={{ marginTop: 16 }}
            />
          )}
          
          {/* 錯誤狀態 */}
          {progressData.status === 'error' && (
            <Alert
              message="測試失敗"
              description={progressData.error_message || '批量測試執行過程中發生錯誤'}
              type="error"
              showIcon
              icon={<CloseCircleOutlined />}
              style={{ marginTop: 16 }}
            />
          )}
        </div>
      )}
    </Modal>
  );
};

export default BatchTestProgressModal;
