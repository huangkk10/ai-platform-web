import React from 'react';
import { Card } from 'antd';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { markdownComponents } from '../markdown/MarkdownComponents';

/**
 * 表格測試組件 - 用於調試表格渲染問題
 */
const TableTest = () => {
  const testTableMarkdown = `# 表格測試

這是一個簡單的表格：

| 功能項目 | 說明 | 狀態 |
|----------|------|------|
| UART 檢查 | 顯示目前裝置對應的 UART 接線器與測試程序 | ✅ 完成 |
| Log Folder | 按這個有: UART 日誌儲存位置 | 🔄 進行中 |
| All Scan | 掃描所有可連接的 UART | ❌ 待處理 |

表格結束。

---

另一個表格：

| 項目 | 描述 | 進度 | 圖片 |
|------|------|------|------|  
| 功能A | 這是功能A [IMG:1] | 90% | 📷 |
| 功能B | 功能B說明 | 75% | - |
`;

  return (
    <div style={{ padding: '20px', maxWidth: '800px' }}>
      <Card title="React Markdown 表格測試" style={{ marginBottom: '20px' }}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={markdownComponents}
        >
          {testTableMarkdown}
        </ReactMarkdown>
      </Card>

      <Card title="調試資訊">
        <pre style={{ fontSize: '12px', backgroundColor: '#f5f5f5', padding: '10px' }}>
          {`測試內容：
${testTableMarkdown}`}
        </pre>
      </Card>
    </div>
  );
};

export default TableTest;