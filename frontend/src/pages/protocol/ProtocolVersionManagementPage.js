import React, { useState, useEffect, useCallback } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Space,
  Tag,
  message,
  Tooltip,
  Row,
  Col,
  Statistic,
  Badge,
  Descriptions
} from 'antd';
import {
  ReloadOutlined,
  StarOutlined,
  StarFilled,
  SyncOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import protocolGuideApi from '../../services/protocolGuideApi';

const ProtocolVersionManagementPage = () => {
  const [versions, setVersions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [baselineVersion, setBaselineVersion] = useState(null);

  // 獲取版本列表
  const fetchVersions = useCallback(async () => {
    setLoading(true);
    try {
      const response = await protocolGuideApi.getProtocolVersions();
      const versionData = response.data.results || response.data;
      setVersions(versionData);
      
      // 找出 Baseline 版本
      const baseline = versionData.find(v => v.is_baseline);
      setBaselineVersion(baseline);
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

  // 設定為 Baseline
  const handleSetBaseline = async (version) => {
    const isDynamic = version.rag_settings?.stage1?.use_dynamic_threshold || 
                     version.rag_settings?.stage2?.use_dynamic_threshold;
    const isHybrid = version.rag_settings?.stage1?.use_hybrid_search;
    
    Modal.confirm({
      title: '設定為 Baseline 版本',
      width: 550,
      content: (
        <div>
          <p>確定要將 <strong>{version.version_name}</strong> 設定為 Baseline 版本嗎？</p>
          
          {/* 混合搜尋提示 */}
          {isHybrid && (
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              background: '#e6f7ff', 
              border: '1px solid #91d5ff',
              borderRadius: '4px' 
            }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <StarFilled style={{ color: '#1890ff', marginRight: '8px' }} />
                  <strong style={{ color: '#1890ff' }}>此版本使用混合搜尋</strong>
                </div>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  • 向量搜尋 + 關鍵字搜尋<br />
                  • RRF 融合（k={version.rag_settings?.stage1?.rrf_k || 60}）<br />
                  • Title Boost (+{version.rag_settings?.stage1?.title_match_bonus || 15}%)
                </div>
              </Space>
            </div>
          )}
          
          {/* 動態 Threshold 提示 */}
          {isDynamic && (
            <div style={{ 
              marginTop: '12px', 
              padding: '12px', 
              background: '#fff7e6', 
              border: '1px solid #ffd591',
              borderRadius: '4px' 
            }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <div>
                  <SyncOutlined spin style={{ color: '#fa8c16', marginRight: '8px' }} />
                  <strong style={{ color: '#fa8c16' }}>此版本使用動態 Threshold</strong>
                </div>
                <div style={{ fontSize: '13px', color: '#666' }}>
                  • 配置將從資料庫即時載入（SearchThresholdSetting）<br />
                  • 可在 Threshold Setting 頁面調整參數
                </div>
              </Space>
            </div>
          )}
          
          <p style={{ marginTop: '12px', color: '#666', fontSize: '13px' }}>
            <InfoCircleOutlined style={{ marginRight: '6px' }} />
            <strong>注意</strong>：設定為 Baseline 後，Protocol Assistant 將使用此版本的配置進行檢索。
          </p>
        </div>
      ),
      okText: '確定設定',
      cancelText: '取消',
      onOk: async () => {
        setLoading(true);
        try {
          await protocolGuideApi.setProtocolBaseline(version.id);
          message.success('✅ Baseline 版本設定成功');
          fetchVersions();
        } catch (error) {
          message.error('設定 Baseline 失敗');
          console.error('設定 Baseline 失敗:', error);
        } finally {
          setLoading(false);
        }
      }
    });
  };

  // 表格欄位定義
  const columns = [
    {
      title: '版本代碼',
      dataIndex: 'version_code',
      key: 'version_code',
      width: 200,
      fixed: 'left',
      render: (text, record) => (
        <Space>
          {record.is_baseline && (
            <StarFilled style={{ color: '#faad14', fontSize: '16px' }} />
          )}
          <span style={{ fontWeight: record.is_baseline ? 'bold' : 'normal' }}>
            {text}
          </span>
        </Space>
      ),
    },
    {
      title: '版本名稱',
      dataIndex: 'version_name',
      key: 'version_name',
      width: 300,
    },
    {
      title: '檢索模式',
      dataIndex: 'retrieval_mode',
      key: 'retrieval_mode',
      width: 180,
      render: (mode, record) => {
        const isHybrid = record.rag_settings?.stage1?.use_hybrid_search;
        const isDynamic = record.rag_settings?.stage1?.use_dynamic_threshold || 
                         record.rag_settings?.stage2?.use_dynamic_threshold;
        
        let color = 'default';
        let text = mode || 'two_stage';
        
        if (isHybrid) {
          color = 'blue';
          text = '混合搜尋';
        } else if (isDynamic) {
          color = 'orange';
          text = '動態 Threshold';
        } else {
          color = 'green';
          text = '二階段搜尋';
        }
        
        return <Tag color={color}>{text}</Tag>;
      },
    },
    {
      title: '核心配置',
      key: 'core_config',
      width: 300,
      render: (_, record) => {
        const stage1 = record.rag_settings?.stage1 || {};
        const isHybrid = stage1.use_hybrid_search;
        const isDynamic = stage1.use_dynamic_threshold;
        
        return (
          <Space direction="vertical" size="small">
            {isHybrid && (
              <Tag color="blue">
                RRF k={stage1.rrf_k || 60} | Title Boost +{stage1.title_match_bonus || 15}%
              </Tag>
            )}
            {isDynamic && (
              <Tag color="orange">動態 Threshold</Tag>
            )}
            {!isHybrid && !isDynamic && (
              <Tag color="green">
                Title {stage1.title_weight || 10}% / Content {stage1.content_weight || 90}%
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: '狀態',
      key: 'status',
      width: 120,
      render: (_, record) => (
        <Space direction="vertical" size="small">
          {record.is_active ? (
            <Badge status="success" text="啟用" />
          ) : (
            <Badge status="default" text="停用" />
          )}
          {record.is_baseline && (
            <Badge status="processing" text="Baseline" />
          )}
        </Space>
      ),
    },
    {
      title: '操作',
      key: 'action',
      width: 150,
      fixed: 'right',
      render: (_, record) => (
        <Space size="small">
          {!record.is_baseline && record.is_active && (
            <Tooltip title="設為 Baseline">
              <Button
                type="link"
                size="small"
                icon={<StarOutlined />}
                onClick={() => handleSetBaseline(record)}
              >
                設為 Baseline
              </Button>
            </Tooltip>
          )}
          {record.is_baseline && (
            <Tag color="gold" icon={<StarFilled />}>
              當前 Baseline
            </Tag>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* 頁面標題與操作按鈕 */}
      <Row justify="space-between" align="middle" style={{ marginBottom: '24px' }}>
        <Col>
          <h2 style={{ margin: 0 }}>Protocol Guide 版本管理</h2>
          <p style={{ margin: '8px 0 0 0', color: '#666' }}>
            管理 Protocol Assistant 的 Dify 配置版本和 Baseline 設定
          </p>
        </Col>
        <Col>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchVersions}
            loading={loading}
          >
            重新整理
          </Button>
        </Col>
      </Row>

      {/* Baseline 版本卡片 */}
      {baselineVersion && (
        <Card
          size="small"
          style={{ marginBottom: '24px', background: '#fffbe6', borderColor: '#ffe58f' }}
          title={
            <Space>
              <StarFilled style={{ color: '#faad14' }} />
              <span>當前 Baseline 版本</span>
            </Space>
          }
        >
          <Descriptions column={3} size="small">
            <Descriptions.Item label="版本名稱">
              <strong>{baselineVersion.version_name}</strong>
            </Descriptions.Item>
            <Descriptions.Item label="版本代碼">
              {baselineVersion.version_code}
            </Descriptions.Item>
            <Descriptions.Item label="檢索模式">
              {baselineVersion.rag_settings?.stage1?.use_hybrid_search ? (
                <Tag color="blue">混合搜尋</Tag>
              ) : (
                <Tag color="green">二階段搜尋</Tag>
              )}
            </Descriptions.Item>
          </Descriptions>
          {baselineVersion.description && (
            <p style={{ margin: '12px 0 0 0', color: '#666', fontSize: '13px' }}>
              {baselineVersion.description}
            </p>
          )}
        </Card>
      )}

      {/* 版本列表 */}
      <Card>
        <Table
          columns={columns}
          dataSource={versions}
          rowKey="id"
          loading={loading}
          pagination={{
            defaultPageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 個版本`,
          }}
          scroll={{ x: 1400 }}
        />
      </Card>
    </div>
  );
};

export default ProtocolVersionManagementPage;
