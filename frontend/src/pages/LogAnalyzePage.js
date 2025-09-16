import React, { useState } from 'react';
import {
  Card,
  Button,
  Row,
  Col,
  Typography,
  Space,
  Tag,
  Upload,
  Progress,
  Divider,
  message
} from 'antd';
import {
  FileTextOutlined,
  UploadOutlined
} from '@ant-design/icons';

const { Title, Text, Paragraph } = Typography;

const LogAnalyzePage = () => {
  const [analyzing, setAnalyzing] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [analysisResult, setAnalysisResult] = useState(null);

  // 文件上傳處理
  const handleFileUpload = (file) => {
    setSelectedFile(file);
    message.success(`已選擇文件: ${file.name}`);
    return false; // 阻止自動上傳
  };

  // 分析日誌
  const handleAnalyze = async () => {
    if (!selectedFile) {
      message.warning('請先選擇要分析的日誌文件');
      return;
    }

    setAnalyzing(true);
    try {
      // 模擬分析過程
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const analysisResult = {
        totalLines: 1247,
        errorCount: 23,
        warningCount: 67,
        infoCount: 892,
        debugCount: 265,
        criticalIssues: [
          'Database connection failures (15 occurrences)',
          'Memory usage warnings (8 occurrences)',
          'Authentication errors (5 occurrences)'
        ],
        suggestions: [
          '建議檢查數據庫連接配置',
          '監控系統內存使用情況',
          '加強用戶認證安全措施'
        ]
      };
      
      setAnalysisResult(analysisResult);
      message.success('日誌分析完成！');
    } catch (error) {
      message.error('分析失敗：' + error.message);
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div style={{ padding: '24px' }}>
      {/* 頁面標題 */}
      <div style={{ marginBottom: '24px' }}>
        <Title level={2} style={{ margin: 0 }}>
          <FileTextOutlined style={{ marginRight: '8px', color: '#1890ff' }} />
          Log Analyze
        </Title>
        <Paragraph style={{ marginTop: '8px', color: '#666' }}>
          智能日誌分析工具，幫助您快速定位和診斷系統問題（所有用戶可用）
        </Paragraph>
      </div>

      <Row gutter={[24, 24]}>
        {/* 文件上傳和分析 */}
        <Col xs={24}>
          <Card title="文件上傳與分析">
            <Space direction="vertical" style={{ width: '100%' }} size="large">
              {/* 文件上傳 */}
              <div>
                <Text strong>選擇日誌文件：</Text>
                <Upload
                  beforeUpload={handleFileUpload}
                  accept=".log,.txt"
                  showUploadList={false}
                  style={{ width: '100%', marginTop: '8px' }}
                >
                  <Button icon={<UploadOutlined />} block>
                    選擇文件
                  </Button>
                </Upload>
                {selectedFile && (
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    已選擇：{selectedFile.name}
                  </Text>
                )}
              </div>

              {/* 分析按鈕 */}
              <Button 
                type="primary" 
                onClick={handleAnalyze}
                loading={analyzing}
                disabled={!selectedFile}
                block
              >
                {analyzing ? '分析中...' : '開始分析'}
              </Button>

              {/* 分析進度 */}
              {analyzing && (
                <Progress percent={75} status="active" />
              )}

              {/* 分析結果 */}
              {analysisResult && (
                <div>
                  <Divider orientation="left">分析結果</Divider>
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text strong>總行數：</Text>
                      <Text>{analysisResult.totalLines.toLocaleString()}</Text>
                    </div>
                    <div>
                      <Text strong>錯誤：</Text>
                      <Tag color="red">{analysisResult.errorCount}</Tag>
                      <Text strong>警告：</Text>
                      <Tag color="orange">{analysisResult.warningCount}</Tag>
                    </div>
                    <div>
                      <Text strong>關鍵問題：</Text>
                      <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                        {analysisResult.criticalIssues.map((issue, index) => (
                          <li key={index} style={{ color: '#ff4d4f' }}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                    <div>
                      <Text strong>建議：</Text>
                      <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
                        {analysisResult.suggestions.map((suggestion, index) => (
                          <li key={index} style={{ color: '#52c41a' }}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  </Space>
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default LogAnalyzePage;