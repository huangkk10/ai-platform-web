import React from 'react';
import { Card, Space, Typography, Button } from 'antd';
import MessageFormatter from '../chat/MessageFormatter';

const { Title, Text } = Typography;

/**
 * React Markdown 測試組件
 * 用於測試從 markdown-it 遷移到 react-markdown 的效果
 */
const ReactMarkdownTest = () => {
  // 測試內容：包含表格和圖片
  const testContent1 = `# 測試表格與圖片渲染

這是一個測試表格：

| 項目 | 描述 | 狀態 |
|------|------|------|
| 功能A | 這是功能A的描述 [IMG:1] | ✅ 完成 |
| 功能B | 這是功能B的描述，包含圖片 | 🔄 進行中 |
| 功能C | 功能C說明 [IMG:2] | ❌ 待處理 |

表格後面應該會顯示相關圖片。

## 程式碼範例

\`\`\`javascript
const test = () => {
  console.log('Hello World');
};
\`\`\`

## 列表測試

1. 第一項
2. 第二項
3. 第三項

- 無序列表項目1
- 無序列表項目2
- 無序列表項目3

> 這是一個引用區塊
> 
> 可能包含多行內容
`;

  // 測試內容：純文字與圖片
  const testContent2 = `# 純文字與圖片測試

這段文字提到了一些截圖 [IMG:3] 和範例圖片。

**粗體文字** 和 *斜體文字* 的測試。

\`inline code\` 的測試。

[連結測試](https://example.com)
`;

  // 測試內容：複雜表格
  const testContent3 = `# 複雜表格測試

| 功能模組 | 負責人 | 進度 | 截圖 | 備註 |
|----------|--------|------|------|------|
| 用戶管理 | 張三 | 90% | [IMG:4] | 需要優化UI |
| 權限系統 | 李四 | 75% | [IMG:5] | 等待測試 |
| 報表功能 | 王五 | 60% | [IMG:6] | 開發中 |
| API整合 | 趙六 | 30% | - | 剛開始 |

以上表格包含了多個圖片引用，應該在表格後統一顯示。
`;

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <Title level={2}>React Markdown 測試頁面</Title>
      <Text type="secondary">
        測試從 markdown-it 遷移到 react-markdown 的效果，特別是表格內圖片的處理
      </Text>

      <Space direction="vertical" size="large" style={{ width: '100%', marginTop: '24px' }}>
        {/* 測試1：表格與圖片 */}
        <Card title="測試1：表格內圖片引用" size="small">
          <MessageFormatter 
            content={testContent1}
            messageType="assistant"
            metadata={{ images: ['test1.png', 'test2.png'] }}
          />
        </Card>

        {/* 測試2：純文字與圖片 */}
        <Card title="測試2：純文字與圖片" size="small">
          <MessageFormatter 
            content={testContent2}
            messageType="assistant"
            metadata={{ images: ['test3.png'] }}
          />
        </Card>

        {/* 測試3：複雜表格 */}
        <Card title="測試3：複雜表格" size="small">
          <MessageFormatter 
            content={testContent3}
            messageType="assistant"
            metadata={{ images: ['screenshot1.png', 'screenshot2.png', 'screenshot3.png'] }}
          />
        </Card>

        {/* 測試4：用戶消息 */}
        <Card title="測試4：用戶消息（純文字）" size="small">
          <MessageFormatter 
            content="這是用戶發送的消息，包含 **粗體** 和 `程式碼`，還有 [連結](https://example.com)。"
            messageType="user"
          />
        </Card>
      </Space>

      <div style={{ marginTop: '24px', padding: '16px', backgroundColor: '#f0f2f5', borderRadius: '6px' }}>
        <Title level={4}>測試說明</Title>
        <ul>
          <li>✅ 表格應該有藍色標題列和整潔的邊框</li>
          <li>✅ 表格內的圖片引用應該顯示為佔位符</li>
          <li>✅ 實際圖片應該在表格後方統一顯示</li>
          <li>✅ 程式碼區塊應該有灰色背景和等寬字體</li>
          <li>✅ 列表應該有正確的縮排和符號</li>
          <li>✅ 引用區塊應該有左側藍色邊框</li>
          <li>✅ 標題應該有藍色顏色和適當的大小</li>
        </ul>
      </div>
    </div>
  );
};

export default ReactMarkdownTest;