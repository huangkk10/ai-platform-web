/**
 * Markdown 測試頁面
 * ==================
 * 
 * 功能：
 * - 左側：Markdown 編輯器（TextArea）
 * - 右側：即時預覽（使用 ReactMarkdown）
 * - 使用與 RVT Assistant 相同的 Markdown 渲染邏輯
 * 
 * 訪問路徑：/dev/markdown-test
 * 權限限制：僅管理員可訪問
 */

import React, { useState, useEffect } from 'react';
import { Row, Col, Input, Button, Card, Space, message, Typography, Divider } from 'antd';
import {
    ClearOutlined,
    CopyOutlined,
    DownloadOutlined,
    FileTextOutlined,
    BulbOutlined
} from '@ant-design/icons';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeRaw from 'rehype-raw';  // ✅ 添加 rehype-raw 以支援 HTML 標籤
import { markdownComponents } from '../components/markdown/MarkdownComponents';
import { fixAllMarkdownTables } from '../utils/markdownTableFixer';
import { convertImageReferencesToMarkdown } from '../utils/imageReferenceConverter';
import '../components/markdown/ReactMarkdown.css';
import './DevMarkdownTestPage.css';

const { TextArea } = Input;
const { Title, Text } = Typography;

// 預設範例 Markdown
const DEFAULT_MARKDOWN = `# 🧪 Markdown 測試範例

## 基本格式測試

這是一個 **粗體文字** 和 *斜體文字* 的範例。

你也可以使用 ~~刪除線~~ 和 \`inline code\` 語法。

---

## 列表功能

### 無序列表
- 項目 1
- 項目 2
  - 子項目 2.1
  - 子項目 2.2
- 項目 3

### 有序列表
1. 第一步
2. 第二步
   1. 子步驟 2.1
   2. 子步驟 2.2
3. 第三步

### 任務列表
- [x] 已完成的任務
- [ ] 待辦事項 1
- [ ] 待辦事項 2

---

## 表格功能

| 欄位 1 | 欄位 2 | 欄位 3 |
|-------|-------|-------|
| A1    | B1    | C1    |
| A2    | B2    | C2    |
| A3    | B3    | C3    |

### 對齊表格
| 左對齊 | 置中 | 右對齊 |
|:------|:----:|------:|
| Left  | Center | Right |
| 文字  | 文字 | 文字 |

---

## 程式碼區塊

### Python 範例
\`\`\`python
def hello_world():
    print("Hello, World!")
    
# 迴圈範例
for i in range(10):
    print(f"Number: {i}")
\`\`\`

### JavaScript 範例
\`\`\`javascript
const greeting = (name) => {
  console.log(\`Hello, \${name}!\`);
};

greeting('World');
\`\`\`

---

## 引用區塊

> 這是一段引用文字
> 
> 可以多行顯示
> 
> > 也支援巢狀引用

---

## 連結和圖片

這是一個 [連結範例](https://www.example.com)

### 圖片引用格式
您可以使用 \`[IMG:ID]\` 格式來引用資料庫中的圖片：

🖼️ [IMG:1] (範例圖片引用)

**注意**：圖片會自動從 API 載入並顯示。如果看不到圖片，請確認：
- 圖片 ID 是否存在於資料庫中
- 您是否有權限訪問該圖片

---

## 標題層級

# H1 標題
## H2 標題
### H3 標題
#### H4 標題
##### H5 標題
###### H6 標題
`;

const DevMarkdownTestPage = () => {
    // State
    const [markdownText, setMarkdownText] = useState('');
    const [processedMarkdown, setProcessedMarkdown] = useState('');

    // 初始化：從 localStorage 載入或使用預設範例
    useEffect(() => {
        const saved = localStorage.getItem('dev_markdown_test');
        if (saved) {
            setMarkdownText(saved);
        } else {
            setMarkdownText(DEFAULT_MARKDOWN);
        }
    }, []);

    // 處理 Markdown 內容（修復表格等）
    useEffect(() => {
        // 步驟 1：修復表格格式
        let processed = fixAllMarkdownTables(markdownText);

        // 步驟 2：將 [IMG:ID] 轉換為 Markdown 圖片格式 ![IMG:ID](IMG:ID)
        // 這樣 ReactMarkdown 才會調用 CustomImage 組件來顯示實際圖片
        processed = convertImageReferencesToMarkdown(processed);

        setProcessedMarkdown(processed);

        // 自動保存到 localStorage（防抖處理）
        const timer = setTimeout(() => {
            localStorage.setItem('dev_markdown_test', markdownText);
        }, 500);

        return () => clearTimeout(timer);
    }, [markdownText]);

    // React Markdown 配置
    const markdownConfig = {
        remarkPlugins: [remarkGfm],
        rehypePlugins: [rehypeRaw],  // ✅ 啟用 HTML 標籤支援（包含 <br>）
        components: markdownComponents,
        disallowedElements: ['script', 'iframe', 'object', 'embed'],
        unwrapDisallowed: true
    };

    // 清除內容
    const handleClear = () => {
        setMarkdownText('');
        message.success('已清除內容');
    };

    // 載入範例
    const handleLoadExample = () => {
        setMarkdownText(DEFAULT_MARKDOWN);
        message.success('已載入範例 Markdown');
    };

    // 複製 Markdown
    const handleCopyMarkdown = () => {
        if (!markdownText.trim()) {
            message.warning('內容為空，無法複製');
            return;
        }
        navigator.clipboard.writeText(markdownText)
            .then(() => {
                message.success('已複製 Markdown 到剪貼簿');
            })
            .catch(() => {
                message.error('複製失敗，請重試');
            });
    };

    // 匯出 HTML
    const handleExportHTML = () => {
        if (!markdownText.trim()) {
            message.warning('內容為空，無法匯出');
            return;
        }

        const previewElement = document.querySelector('.markdown-preview-content');
        if (previewElement) {
            const html = `<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Markdown Preview</title>
  <style>
    body {
      font-family: 'Microsoft JhengHei', '微軟正黑體', sans-serif;
      line-height: 1.6;
      max-width: 900px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f9f9f9;
    }
    .content {
      background-color: white;
      padding: 30px;
      border-radius: 8px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
  </style>
</head>
<body>
  <div class="content">
    ${previewElement.innerHTML}
  </div>
</body>
</html>`;

            const blob = new Blob([html], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `markdown-preview-${new Date().getTime()}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);

            message.success('已匯出 HTML 文件');
        } else {
            message.error('預覽內容未找到');
        }
    };

    return (
        <div className="dev-markdown-test-page">
            {/* 頁面標題 */}
            <div className="page-header">
                <Title level={3}>
                    🧪 Markdown 測試頁面
                </Title>
                <Text type="secondary">
                    左側編輯，右側即時預覽（使用與 RVT Assistant 相同的渲染邏輯）
                </Text>
                <Divider style={{ margin: '12px 0' }} />
                <Space wrap>
                    <Text type="warning">
                        <BulbOutlined /> 提示：內容會自動保存到瀏覽器本地存儲
                    </Text>
                </Space>
            </div>

            {/* 雙面板佈局 */}
            <Row gutter={16} style={{ height: 'calc(100vh - 200px)', marginTop: '16px' }}>
                {/* 左側編輯器 */}
                <Col xs={24} lg={12}>
                    <Card
                        title="📝 Markdown 編輯器"
                        bordered={false}
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column' }}
                        extra={
                            <Space>
                                <Button
                                    icon={<FileTextOutlined />}
                                    onClick={handleLoadExample}
                                    size="small"
                                >
                                    載入範例
                                </Button>
                                <Button
                                    icon={<ClearOutlined />}
                                    onClick={handleClear}
                                    danger
                                    size="small"
                                >
                                    清除
                                </Button>
                            </Space>
                        }
                    >
                        <TextArea
                            value={markdownText}
                            onChange={(e) => setMarkdownText(e.target.value)}
                            placeholder="在此輸入 Markdown 內容...&#10;&#10;支援的語法：&#10;- 標題：# H1, ## H2, ### H3&#10;- 粗體：**文字**&#10;- 斜體：*文字*&#10;- 列表：- 項目 或 1. 項目&#10;- 表格：| 欄位 | 欄位 |&#10;- 程式碼：```language&#10;- 引用：> 文字"
                            style={{
                                flex: 1,
                                fontFamily: 'Consolas, Monaco, "Courier New", monospace',
                                fontSize: '14px',
                                lineHeight: '1.5',
                                resize: 'none'
                            }}
                            autoSize={false}
                        />
                        <div style={{ marginTop: '8px', textAlign: 'right' }}>
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                                字數：{markdownText.length} | 行數：{markdownText.split('\n').length}
                            </Text>
                        </div>
                    </Card>
                </Col>

                {/* 右側預覽區 */}
                <Col xs={24} lg={12}>
                    <Card
                        title="👁️ 即時預覽"
                        bordered={false}
                        style={{ height: '100%', display: 'flex', flexDirection: 'column' }}
                        bodyStyle={{ flex: 1, padding: '16px', display: 'flex', flexDirection: 'column' }}
                        extra={
                            <Space>
                                <Button
                                    icon={<CopyOutlined />}
                                    onClick={handleCopyMarkdown}
                                    size="small"
                                >
                                    複製 MD
                                </Button>
                                <Button
                                    icon={<DownloadOutlined />}
                                    onClick={handleExportHTML}
                                    type="primary"
                                    size="small"
                                >
                                    匯出 HTML
                                </Button>
                            </Space>
                        }
                    >
                        <div
                            className="markdown-preview-wrapper"
                            style={{
                                flex: 1,
                                overflowY: 'auto',
                                padding: '20px',
                                backgroundColor: '#ffffff',
                                borderRadius: '4px',
                                border: '1px solid #e8e8e8'
                            }}
                        >
                            {markdownText.trim() ? (
                                <div className="markdown-preview-content markdown-content">
                                    <ReactMarkdown {...markdownConfig}>
                                        {processedMarkdown}
                                    </ReactMarkdown>
                                </div>
                            ) : (
                                <div style={{
                                    textAlign: 'center',
                                    padding: '60px 20px',
                                    color: '#999'
                                }}>
                                    <FileTextOutlined style={{ fontSize: '48px', marginBottom: '16px' }} />
                                    <div>在左側輸入 Markdown 內容，這裡會即時顯示預覽</div>
                                    <Button
                                        type="link"
                                        onClick={handleLoadExample}
                                        style={{ marginTop: '12px' }}
                                    >
                                        載入範例試試
                                    </Button>
                                </div>
                            )}
                        </div>
                    </Card>
                </Col>
            </Row>
        </div>
    );
};

export default DevMarkdownTestPage;
