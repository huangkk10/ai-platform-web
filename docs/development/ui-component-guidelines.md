# UI 組件開發規範 - Ant Design First

## 🎯 核心原則

**首要原則**: 所有前端 UI 開發必須優先使用 Ant Design of React (antd) 作為主要 UI 框架

## 📦 組件選擇優先順序

### 1. 🥇 第一選擇：Ant Design 原生組件
```javascript
// ✅ 優先使用 antd 原生組件
import { Table, Form, Button, Card, Modal } from 'antd';
```

### 2. 🥈 第二選擇：Ant Design 組件組合
```javascript
// ✅ 組合多個 antd 組件實現複雜功能
import { Card, List, Avatar, Button, Space } from 'antd';

const CustomUserList = () => (
  <Card title="用戶列表">
    <List
      dataSource={users}
      renderItem={item => (
        <List.Item
          actions={[
            <Button type="link">編輯</Button>,
            <Button type="link" danger>刪除</Button>
          ]}
        >
          <List.Item.Meta
            avatar={<Avatar src={item.avatar} />}
            title={item.name}
            description={item.email}
          />
        </List.Item>
      )}
    />
  </Card>
);
```

### 3. 🥉 第三選擇：基於 antd 的自定義組件
```javascript
// ✅ 在 antd 組件基礎上擴展
import { Button } from 'antd';
import styled from 'styled-components';

const CustomButton = styled(Button)`
  // 保持 antd 基礎樣式，只添加必要的自定義
  border-radius: ${props => props.theme.borderRadius}px;
`;
```

### 4. ❌ 避免：其他 UI 框架組件
```javascript
// ❌ 禁止使用其他 UI 框架
import { Button } from 'react-bootstrap';  // 禁止
import { TextField } from '@mui/material';  // 禁止
import { Input } from 'semantic-ui-react';  // 禁止
```

## 🎨 設計系統標準

### 色彩規範
```javascript
// ✅ 使用 Ant Design 預設色彩系統
const colors = {
  primary: '#1890ff',    // 主要色
  success: '#52c41a',    // 成功色
  warning: '#faad14',    // 警告色
  error: '#f5222d',      // 錯誤色
  info: '#1890ff',       // 信息色
};

// 在 Tag 組件中使用
<Tag color="blue">信息</Tag>
<Tag color="green">成功</Tag>
<Tag color="orange">警告</Tag>
<Tag color="red">錯誤</Tag>
```

### 間距規範
```javascript
// ✅ 使用 Ant Design 的間距系統
import { theme } from 'antd';

const {
  token: { margin, padding, marginSM, paddingLG },
} = theme.useToken();

// 標準間距值
const spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
};
```

### 響應式布局
```javascript
// ✅ 使用 Ant Design Grid 系統
import { Row, Col } from 'antd';

const ResponsiveLayout = () => (
  <Row gutter={[16, 16]}>
    <Col xs={24} sm={12} md={8} lg={6}>
      <Card>響應式內容</Card>
    </Col>
    <Col xs={24} sm={12} md={8} lg={6}>
      <Card>響應式內容</Card>
    </Col>
  </Row>
);
```

## 📋 常用場景最佳實踐

### 1. 資料展示頁面
```javascript
// ✅ RVT Guide 頁面範例 (已實現)
import {
  Card,
  Table,
  Button,
  Space,
  Typography,
  Tag,
  Input,
  Select,
  Row,
  Col,
  Modal,
  Form,
  Tooltip
} from 'antd';

const DataDisplayPage = () => {
  return (
    <Card
      title="資料列表"
      extra={
        <Space>
          <Button icon={<ReloadOutlined />}>重新整理</Button>
          <Button type="primary" icon={<PlusOutlined />}>新增</Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={data}
        rowKey="id"
        pagination={{
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `第 ${range[0]}-${range[1]} 項，共 ${total} 項`,
        }}
      />
    </Card>
  );
};
```

### 2. 表單頁面
```javascript
// ✅ 標準表單佈局
import { Form, Input, Select, Button, Card, Row, Col } from 'antd';

const FormPage = () => {
  const [form] = Form.useForm();
  
  return (
    <Card title="資料編輯">
      <Form
        form={form}
        layout="vertical"
        onFinish={onFinish}
      >
        <Row gutter={16}>
          <Col span={12}>
            <Form.Item
              name="title"
              label="標題"
              rules={[{ required: true, message: '請輸入標題' }]}
            >
              <Input placeholder="請輸入標題" />
            </Form.Item>
          </Col>
          <Col span={12}>
            <Form.Item
              name="category"
              label="分類"
              rules={[{ required: true, message: '請選擇分類' }]}
            >
              <Select placeholder="請選擇分類">
                <Option value="option1">選項1</Option>
                <Option value="option2">選項2</Option>
              </Select>
            </Form.Item>
          </Col>
        </Row>
        
        <Form.Item>
          <Space>
            <Button type="primary" htmlType="submit">提交</Button>
            <Button>取消</Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );
};
```

### 3. 彈窗和抽屜
```javascript
// ✅ 使用 Modal 和 Drawer
import { Modal, Drawer, Form, message } from 'antd';

// 簡單確認彈窗
const showDeleteConfirm = (record) => {
  Modal.confirm({
    title: '確認刪除',
    content: `確定要刪除 "${record.title}" 嗎？`,
    okText: '確認',
    cancelText: '取消',
    onOk: () => handleDelete(record),
  });
};

// 表單彈窗
const EditModal = ({ visible, onCancel, onOk, record }) => (
  <Modal
    title="編輯資料"
    open={visible}
    onCancel={onCancel}
    footer={null}
    width={800}
  >
    <Form onFinish={onOk}>
      {/* 表單內容 */}
    </Form>
  </Modal>
);
```

### 4. 消息和通知
```javascript
// ✅ 使用 message 和 notification
import { message, notification } from 'antd';

// 簡單消息
message.success('操作成功');
message.error('操作失敗');
message.warning('警告消息');
message.info('信息提示');

// 複雜通知
notification.success({
  message: '操作成功',
  description: '資料已成功保存到資料庫',
  duration: 3,
});
```

## 🚫 常見錯誤與避免方式

### ❌ 錯誤示範：混用 UI 框架
```javascript
// ❌ 不要這樣做
import { Button as AntButton } from 'antd';
import { Button as BootstrapButton } from 'react-bootstrap';
import { TextField } from '@mui/material';

const MixedComponent = () => (
  <div>
    <AntButton>Ant Design 按鈕</AntButton>
    <BootstrapButton>Bootstrap 按鈕</BootstrapButton>  {/* 禁止 */}
    <TextField label="Material UI 輸入框" />           {/* 禁止 */}
  </div>
);
```

### ✅ 正確示範：統一使用 Ant Design
```javascript
// ✅ 推薦做法
import { Button, Input, Space } from 'antd';

const UnifiedComponent = () => (
  <Space direction="vertical" style={{ width: '100%' }}>
    <Button type="primary">主要按鈕</Button>
    <Button>次要按鈕</Button>
    <Input placeholder="請輸入內容" />
  </Space>
);
```

### ❌ 錯誤示範：過度自定義樣式
```javascript
// ❌ 不要完全覆蓋 Ant Design 的樣式
const OverCustomizedButton = styled(Button)`
  background: linear-gradient(45deg, red, blue);
  border: 5px solid purple;
  border-radius: 50px;
  font-size: 24px;
  /* 完全破壞了 antd 的設計語言 */
`;
```

### ✅ 正確示範：適度自定義
```javascript
// ✅ 在 Ant Design 基礎上適度調整
const CustomButton = styled(Button)`
  /* 保持 antd 基本樣式，只調整必要部分 */
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  
  &:hover {
    transform: translateY(-1px);
    transition: all 0.3s;
  }
`;
```

## 🔧 開發工具配置

### ESLint 規則建議
```json
// .eslintrc.js
{
  "rules": {
    "no-restricted-imports": [
      "error",
      {
        "patterns": [
          {
            "group": ["react-bootstrap", "@mui/*", "semantic-ui-react"],
            "message": "請使用 Ant Design 替代其他 UI 框架"
          }
        ]
      }
    ]
  }
}
```

### VS Code 擴展建議
```json
// .vscode/extensions.json
{
  "recommendations": [
    "antfu.iconify",
    "bradlc.vscode-tailwindcss",
    "ms-vscode.vscode-typescript-next"
  ]
}
```

## 📚 學習資源

### 官方文檔
- [Ant Design 官方文檔](https://ant.design/docs/react/introduce-cn)
- [Ant Design 設計規範](https://ant.design/docs/spec/introduce-cn)
- [Ant Design Pro](https://pro.ant.design/zh-CN/)

### 最佳實踐範例
- 當前專案的 `RvtGuidePage.js` - 完整的 CRUD 頁面實現
- 當前專案的 `KnowIssuePage.js` - 複雜表單和資料管理

### 社群資源
- [Ant Design GitHub](https://github.com/ant-design/ant-design)
- [Awesome Ant Design](https://github.com/websemantics/awesome-ant-design)

## 🎯 檢查清單

在開發新功能時，請確認：
- [ ] 所有 UI 組件都來自 `antd`
- [ ] 使用 Ant Design 的顏色規範
- [ ] 響應式布局使用 `Row` 和 `Col`
- [ ] 表單使用 `Form` 組件
- [ ] 狀態反饋使用 `message` 或 `notification`
- [ ] Icon 使用 `@ant-design/icons`
- [ ] 保持設計風格一致性
- [ ] 沒有引入其他 UI 框架組件

---
**版本**: v1.0  
**更新日期**: 2024-09-24  
**適用範圍**: AI Platform Web Frontend  
**負責人**: AI Platform Team