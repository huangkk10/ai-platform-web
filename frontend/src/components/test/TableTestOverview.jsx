import React from 'react';
import { Card, Row, Col, Typography, Divider } from 'antd';

const { Title, Text } = Typography;

/**
 * Markdown 表格測試總覽頁面
 */
const TableTestOverview = () => {
  return (
    <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>🔧 Markdown 表格渲染測試總覽</Title>
      <Text type="secondary">
        以下是所有可用的測試頁面，用於調試和修復表格渲染問題
      </Text>
      
      <Divider />
      
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="基本表格測試"
            hoverable
            onClick={() => window.open('/test/basic-table', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>測試最基本的 ReactMarkdown + remarkGfm 表格渲染，不使用自定義組件</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/basic-table</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="AST 調試器"
            hoverable
            onClick={() => window.open('/test/ast-debugger', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>查看 react-markdown 解析的 AST 結構，觀察表格元素的組織方式</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/ast-debugger</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="簡化診斷器"
            hoverable
            onClick={() => window.open('/test/simple-diagnostic', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>🆕 最簡化的表格問題診斷，帶有調試 Console 輸出</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/simple-diagnostic</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="表格調試器"
            hoverable
            onClick={() => window.open('/test/table-debugger', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>完整的表格測試，包含簡單表格、帶圖片表格和複雜表格</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/table-debugger</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="RVT Assistant"
            hoverable
            onClick={() => window.open('/rvt-assistant-chat', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>實際的 RVT Assistant 頁面，可以測試真實的表格渲染場景</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /rvt-assistant-chat</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="RVT Guide 頁面"
            hoverable
            onClick={() => window.open('/rvt-guide', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>RVT Guide 管理頁面，可以查看現有的 markdown 內容和表格</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /rvt-guide</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="真實場景測試"
            hoverable
            onClick={() => window.open('/test/real-scenario', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>使用與用戶遇到問題完全相同的表格內容和圖片進行測試</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/real-scenario</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="完整聊天消息測試"
            hoverable
            onClick={() => window.open('/test/full-chat', '_blank')}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>模擬真實 RVT Assistant 聊天回應，包含完整圖片數據的表格測試</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">路徑: /test/full-chat ⭐</Text>
            </div>
          </Card>
        </Col>
        
        <Col xs={24} sm={12} md={8}>
          <Card 
            title="開發者工具"
            hoverable
            onClick={() => {
              alert('請按 F12 打開開發者工具，然後查看 Console 標籤以查看調試資訊');
            }}
            style={{ cursor: 'pointer', height: '100%' }}
          >
            <Text>開啟瀏覽器開發者工具查看 Console 日誌和網路請求</Text>
            <div style={{ marginTop: '10px' }}>
              <Text type="secondary">快捷鍵: F12</Text>
            </div>
          </Card>
        </Col>
      </Row>
      
      <Divider />
      
      <Card title="🐛 已知問題和調試重點" style={{ marginTop: '20px' }}>
        <ul>
          <li><Text strong>問題描述：</Text>表格格式跑掉，內容顯示在單一儲存格中</li>
          <li><Text strong>可能原因：</Text>
            <ul style={{ marginTop: '8px' }}>
              <li>自定義組件映射不正確</li>
              <li>CSS 樣式衝突</li>
              <li>react-markdown 和 remark-gfm 版本兼容性</li>
              <li>表格 AST 解析問題</li>
            </ul>
          </li>
          <li><Text strong>調試步驟：</Text>
            <ol style={{ marginTop: '8px' }}>
              <li>先測試基本表格（無自定義組件）</li>
              <li>使用 AST 調試器查看解析結構</li>
              <li>比較簡化組件和完整組件的差異</li>
              <li>檢查 Console 日誌中的錯誤</li>
            </ol>
          </li>
        </ul>
      </Card>
    </div>
  );
};

export default TableTestOverview;