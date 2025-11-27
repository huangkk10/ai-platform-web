# VSA 測試案例新增 - 獨立頁面設計方案

## 📋 設計概述

將目前 Modal 彈窗中的新增測試案例表單，改造為**獨立的全頁面**，提供更好的用戶體驗和更大的操作空間。

---

## 🎯 設計目標

### 優點分析

✅ **更大的操作空間**
- 表單不受 Modal 寬度限制
- 可以顯示更多輔助資訊和提示
- 適合長文本內容（問題、答案）輸入

✅ **更好的用戶體驗**
- 不用擔心 Modal 遮擋其他內容
- 可以有獨立的頁面標題和導航
- 支援瀏覽器前進/後退

✅ **獨立的 URL 路徑**
- 可以直接分享新增頁面連結
- 支援書籤收藏
- 便於權限控制

✅ **更好的表單驗證體驗**
- 有更多空間顯示錯誤訊息
- 可以使用步驟式表單（Step Form）
- 支援即時預覽

---

## 🏗️ 頁面架構設計

### 方案 A：單頁表單（推薦）

```
┌─────────────────────────────────────────────────┐
│  ← 返回列表    新增 VSA 測試案例           [儲存] │ ← TopHeader
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  📝 基本資訊                              │ │
│  │  ┌──────────────────────────────────┐    │ │
│  │  │ 測試問題 *                        │    │ │
│  │  │ [TextArea - 大文本框]             │    │ │
│  │  └──────────────────────────────────┘    │ │
│  │  ┌─────────┐                             │ │
│  │  │ 難度等級 │ [下拉選單: 中等]           │ │
│  │  └─────────┘                             │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  🎯 VSA 測試配置                          │ │
│  │  ┌──────────────────────────────────┐    │ │
│  │  │ 期望答案 *                        │    │ │
│  │  │ [TextArea - 大文本框]             │    │ │
│  │  └──────────────────────────────────┘    │ │
│  │  ┌──────────────────────────────────┐    │ │
│  │  │ 答案關鍵字 * [輸入框] [+ 添加]   │    │ │
│  │  │ ┌────────────────────────────┐   │    │ │
│  │  │ │ 已添加: [tag1] [tag2] ...   │   │    │ │
│  │  │ └────────────────────────────┘   │    │ │
│  │  └──────────────────────────────────┘    │ │
│  │  滿分: [100]                              │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  ⚙️ 進階選項                              │ │
│  │  標籤: [mode="tags" 輸入框]              │ │
│  │  來源: [輸入框]                           │ │
│  │  備註: [TextArea]                         │ │
│  │  啟用狀態: [Switch]                       │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
│  [取消]                              [儲存測試案例] │
└─────────────────────────────────────────────────┘
```

### 方案 B：步驟式表單（進階版）

```
┌─────────────────────────────────────────────────┐
│  ← 返回列表    新增 VSA 測試案例                │
├─────────────────────────────────────────────────┤
│                                                 │
│  Step 1: 基本資訊 → Step 2: VSA 配置 → Step 3: 完成 │
│  ●━━━━━━━━━━━━━  ○━━━━━━━━━━━━━  ○━━━━━━━━    │
│                                                 │
│  ┌───────────────────────────────────────────┐ │
│  │  📝 步驟 1：輸入基本資訊                  │ │
│  │                                           │ │
│  │  測試問題 *                               │ │
│  │  [大文本框]                               │ │
│  │                                           │ │
│  │  難度等級 *                               │ │
│  │  [下拉選單]                               │ │
│  │                                           │ │
│  │               [上一步]      [下一步 →]    │ │
│  └───────────────────────────────────────────┘ │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 📁 檔案結構

### 新建檔案

```
frontend/src/pages/dify-benchmark/
├── DifyTestCasePage.js           # 現有的列表頁面
├── DifyTestCaseCreatePage.js     # 🆕 新增測試案例頁面（單頁表單）
├── DifyTestCaseEditPage.js       # 🆕 編輯測試案例頁面（可共用組件）
└── components/                    # 🆕 共用組件目錄
    ├── TestCaseFormBasic.jsx      # 基本資訊表單組件
    ├── TestCaseFormVSA.jsx        # VSA 配置表單組件
    ├── TestCaseFormAdvanced.jsx   # 進階選項表單組件
    └── KeywordManager.jsx         # 關鍵字管理組件（獨立）
```

---

## 🛣️ 路由配置

### App.js 路由添加

```javascript
// App.js 中添加新路由

// Dify Benchmark 頁面
import DifyTestCasePage from './pages/dify-benchmark/DifyTestCasePage';
import DifyTestCaseCreatePage from './pages/dify-benchmark/DifyTestCaseCreatePage'; // 🆕
import DifyTestCaseEditPage from './pages/dify-benchmark/DifyTestCaseEditPage';     // 🆕

// ... 在 Routes 中添加
<Route path="/benchmark/dify/test-cases" element={
  <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
    <DifyTestCasePage />
  </ProtectedRoute>
} />

{/* 🆕 新增測試案例頁面 */}
<Route path="/benchmark/dify/test-cases/create" element={
  <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
    <DifyTestCaseCreatePage />
  </ProtectedRoute>
} />

{/* 🆕 編輯測試案例頁面 */}
<Route path="/benchmark/dify/test-cases/edit/:id" element={
  <ProtectedRoute permission="isStaff" fallbackTitle="Benchmark 系統存取受限">
    <DifyTestCaseEditPage />
  </ProtectedRoute>
} />
```

### 頁面標題配置

```javascript
// App.js - getPageTitle 函數中添加
case '/benchmark/dify/test-cases/create':
  return '新增 VSA 測試案例';

default:
  if (pathname.startsWith('/benchmark/dify/test-cases/edit/')) {
    const id = pathname.split('/').pop();
    return { text: '編輯 VSA 測試案例', id: id };
  }
```

### 頂部按鈕配置

```javascript
// App.js - getExtraActions 函數中添加
if (pathname === '/benchmark/dify/test-cases/create' || 
    pathname.startsWith('/benchmark/dify/test-cases/edit/')) {
  return (
    <div style={{ display: 'flex', gap: '12px' }}>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate('/benchmark/dify/test-cases')}
        size="large"
      >
        返回列表
      </Button>
      <Button
        type="primary"
        size="large"
        icon={<SaveOutlined />}
        onClick={() => {
          window.dispatchEvent(new CustomEvent('test-case-form-save'));
        }}
      >
        儲存測試案例
      </Button>
    </div>
  );
}
```

---

## 💻 核心代碼實作

### 1. DifyTestCaseCreatePage.js（完整頁面）

```javascript
import React, { useState, useEffect } from 'react';
import { Form, Input, Select, Button, Card, Divider, Space, Tag, message } from 'antd';
import { useNavigate } from 'react-router-dom';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';
import difyBenchmarkApi from '../../services/difyBenchmarkApi';
import KeywordManager from './components/KeywordManager';

const { TextArea } = Input;
const { Option } = Select;

const DifyTestCaseCreatePage = () => {
  const navigate = useNavigate();
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [keywords, setKeywords] = useState([]);

  // 監聽保存事件（來自 TopHeader 按鈕）
  useEffect(() => {
    const handleSaveEvent = () => {
      form.submit();
    };

    window.addEventListener('test-case-form-save', handleSaveEvent);
    return () => {
      window.removeEventListener('test-case-form-save', handleSaveEvent);
    };
  }, [form]);

  // 處理表單提交
  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const payload = {
        ...values,
        answer_keywords: keywords, // 使用 state 中的關鍵字
        test_type: 'vsa',
      };

      await difyBenchmarkApi.createDifyTestCase(payload);
      message.success('測試案例新增成功');
      navigate('/benchmark/dify/test-cases'); // 返回列表頁
    } catch (error) {
      console.error('新增失敗:', error);
      message.error(`新增失敗: ${error.response?.data?.detail || error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ 
      padding: '24px', 
      maxWidth: '1200px', 
      margin: '0 auto',
      background: '#f5f5f5'
    }}>
      {/* 基本資訊卡片 */}
      <Card 
        title="📝 基本資訊" 
        style={{ marginBottom: '24px' }}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{
            difficulty_level: 'medium',
            is_active: true,
            max_score: 100,
          }}
        >
          <Form.Item
            name="question"
            label="測試問題"
            rules={[{ required: true, message: '請輸入測試問題' }]}
          >
            <TextArea
              rows={6}
              placeholder="輸入測試問題內容..."
              maxLength={1000}
              showCount
            />
          </Form.Item>

          <Form.Item
            name="difficulty_level"
            label="難度等級"
            rules={[{ required: true, message: '請選擇難度等級' }]}
          >
            <Select placeholder="選擇難度" size="large">
              <Option value="easy">簡單</Option>
              <Option value="medium">中等</Option>
              <Option value="hard">困難</Option>
            </Select>
          </Form.Item>
        </Form>
      </Card>

      {/* VSA 測試配置卡片 */}
      <Card 
        title="🎯 VSA 測試配置" 
        style={{ marginBottom: '24px' }}
      >
        <Form.Item
          name="expected_answer"
          label="期望答案"
          rules={[{ required: true, message: '請輸入期望答案' }]}
          tooltip="定義標準答案或答案範例，用於評估 AI 回應品質"
        >
          <TextArea
            rows={8}
            placeholder="輸入期望的答案內容..."
            maxLength={2000}
            showCount
          />
        </Form.Item>

        {/* 關鍵字管理組件 */}
        <KeywordManager 
          keywords={keywords} 
          onChange={setKeywords}
        />

        <Form.Item
          name="max_score"
          label="滿分"
          tooltip="測試案例的最高分數"
        >
          <Input 
            type="number" 
            min={1} 
            max={1000} 
            size="large"
            style={{ width: '200px' }}
          />
        </Form.Item>
      </Card>

      {/* 進階選項卡片 */}
      <Card 
        title="⚙️ 進階選項" 
        style={{ marginBottom: '24px' }}
      >
        <Form.Item
          name="tags"
          label="標籤"
          tooltip="多個標籤可用逗號分隔或按 Enter 新增"
        >
          <Select
            mode="tags"
            size="large"
            placeholder="輸入標籤（例如：Kingston, Linux, 葉卡）"
            tokenSeparators={[',']}
          />
        </Form.Item>

        <Form.Item label="來源" name="source">
          <Input 
            size="large"
            placeholder="例如：實際測試案例、文檔範例、客戶反饋" 
          />
        </Form.Item>

        <Form.Item name="notes" label="備註">
          <TextArea
            rows={4}
            placeholder="其他說明或注意事項..."
            maxLength={500}
            showCount
          />
        </Form.Item>

        <Form.Item 
          name="is_active" 
          label="啟用狀態" 
          valuePropName="checked"
        >
          <Switch checkedChildren="啟用" unCheckedChildren="停用" />
        </Form.Item>
      </Card>

      {/* 底部操作按鈕 */}
      <div style={{ 
        textAlign: 'right', 
        padding: '16px 0',
        background: '#fff',
        position: 'sticky',
        bottom: 0,
        borderTop: '1px solid #f0f0f0',
        zIndex: 10
      }}>
        <Space size="middle">
          <Button 
            size="large"
            onClick={() => navigate('/benchmark/dify/test-cases')}
          >
            取消
          </Button>
          <Button 
            type="primary" 
            size="large"
            loading={loading}
            onClick={() => form.submit()}
          >
            儲存測試案例
          </Button>
        </Space>
      </div>
    </div>
  );
};

export default DifyTestCaseCreatePage;
```

### 2. KeywordManager.jsx（關鍵字管理組件）

```javascript
import React, { useState } from 'react';
import { Input, Button, Tag, Space } from 'antd';
import { PlusOutlined, DeleteOutlined } from '@ant-design/icons';

const KeywordManager = ({ keywords = [], onChange }) => {
  const [keywordInput, setKeywordInput] = useState('');

  // 添加關鍵字
  const handleAddKeyword = () => {
    const trimmed = keywordInput.trim();
    if (trimmed && !keywords.includes(trimmed)) {
      onChange([...keywords, trimmed]);
      setKeywordInput('');
    }
  };

  // 移除關鍵字
  const handleRemoveKeyword = (keyword) => {
    onChange(keywords.filter(k => k !== keyword));
  };

  // 清空所有關鍵字
  const handleClearAll = () => {
    onChange([]);
  };

  return (
    <div style={{ marginBottom: '24px' }}>
      <label style={{ 
        display: 'block', 
        marginBottom: '8px',
        fontWeight: 500 
      }}>
        <span style={{ color: 'red' }}>* </span>
        答案關鍵字
      </label>

      {/* 輸入區域 */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
        <Input
          size="large"
          value={keywordInput}
          onChange={(e) => setKeywordInput(e.target.value)}
          onPressEnter={handleAddKeyword}
          placeholder="輸入關鍵字後按 Enter 或點擊添加..."
          style={{ flex: 1 }}
        />
        <Button 
          type="primary" 
          size="large"
          icon={<PlusOutlined />} 
          onClick={handleAddKeyword}
        >
          添加
        </Button>
      </div>

      {/* 關鍵字展示區域 */}
      <div style={{ 
        padding: '16px', 
        background: '#fafafa', 
        borderRadius: '8px',
        border: '1px solid #d9d9d9',
        minHeight: '100px'
      }}>
        <div style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          marginBottom: keywords.length > 0 ? '12px' : '0'
        }}>
          <span style={{ color: '#666', fontSize: '14px' }}>
            已添加的關鍵字 ({keywords.length})
          </span>
          {keywords.length > 0 && (
            <Button 
              type="link" 
              danger 
              size="small"
              onClick={handleClearAll}
              icon={<DeleteOutlined />}
            >
              清空全部
            </Button>
          )}
        </div>

        {keywords.length > 0 ? (
          <Space size={[8, 8]} wrap>
            {keywords.map((keyword, index) => (
              <Tag 
                key={index} 
                closable 
                onClose={() => handleRemoveKeyword(keyword)}
                color="purple"
                style={{ 
                  fontSize: '14px', 
                  padding: '8px 12px',
                }}
              >
                {keyword}
              </Tag>
            ))}
          </Space>
        ) : (
          <div style={{ 
            textAlign: 'center', 
            color: '#bfbfbf',
            padding: '24px 0',
            fontSize: '14px'
          }}>
            尚未添加關鍵字
          </div>
        )}
      </div>

      {/* 提示文字 */}
      <div style={{ 
        marginTop: '8px', 
        color: '#8c8c8c', 
        fontSize: '12px'
      }}>
        💡 提示：輸入關鍵字後按 <Tag style={{ margin: '0 4px' }}>Enter</Tag> 也可快速添加
      </div>
    </div>
  );
};

export default KeywordManager;
```

### 3. 修改列表頁面按鈕（DifyTestCasePage.js）

```javascript
// 修改「新增測試案例」按鈕，導航到新頁面
<Button
  type="primary"
  icon={<PlusOutlined />}
  onClick={() => navigate('/benchmark/dify/test-cases/create')}
>
  新增測試案例
</Button>

// 修改頂部「新增問題」按鈕事件
const handleCreateEvent = () => {
  console.log('收到新增問題事件 - 導航到新增頁面');
  navigate('/benchmark/dify/test-cases/create');
};
```

---

## 🎨 樣式優化建議

### CSS 樣式（可選）

```css
/* DifyTestCaseCreatePage.css */

.test-case-create-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
  background: #f5f5f5;
  min-height: calc(100vh - 64px);
}

.form-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.form-card .ant-card-head-title {
  font-size: 18px;
  font-weight: 600;
}

.sticky-footer {
  position: sticky;
  bottom: 0;
  background: #fff;
  padding: 16px 24px;
  border-top: 1px solid #f0f0f0;
  text-align: right;
  z-index: 10;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.05);
}

/* 大文本框優化 */
.test-case-create-page .ant-input-textarea {
  font-size: 15px;
  line-height: 1.6;
}

/* 關鍵字標籤優化 */
.keyword-tag {
  font-size: 14px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
}

.keyword-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

---

## 📊 優缺點對比

### 對比表格

| 特性 | Modal 彈窗 | 獨立頁面 |
|------|-----------|---------|
| **操作空間** | 受限（固定寬度 900px） | ✅ 無限制（可達 1200px+） |
| **文本輸入** | 較小的 TextArea | ✅ 更大的輸入區域 |
| **用戶體驗** | 需要滾動 Modal | ✅ 自然的頁面滾動 |
| **URL 分享** | ❌ 無法直接分享 | ✅ 可分享創建頁面 URL |
| **瀏覽器導航** | ❌ 不支援前進/後退 | ✅ 支援瀏覽器導航 |
| **表單驗證** | 空間有限 | ✅ 可顯示更多提示 |
| **開發成本** | 低（已實現） | 中（需要新建頁面） |
| **維護成本** | 中（與列表頁耦合） | ✅ 低（組件解耦） |
| **響應式設計** | 較難實現 | ✅ 易於實現 |

---

## 🚀 實作步驟（待執行）

### Phase 1：創建基礎頁面（2-3 小時）
1. ✅ 創建 `DifyTestCaseCreatePage.js`
2. ✅ 創建 `KeywordManager.jsx` 組件
3. ✅ 在 App.js 中添加路由
4. ✅ 配置頁面標題和頂部按鈕

### Phase 2：表單功能實作（2 小時）
1. ✅ 複製現有表單邏輯
2. ✅ 實作表單提交
3. ✅ 實作表單驗證
4. ✅ 實作關鍵字管理

### Phase 3：樣式優化（1 小時）
1. ✅ 調整卡片布局
2. ✅ 優化間距和字體
3. ✅ 添加響應式設計
4. ✅ 添加動畫效果

### Phase 4：整合測試（1 小時）
1. ✅ 測試新增功能
2. ✅ 測試導航流程
3. ✅ 測試表單驗證
4. ✅ 跨瀏覽器測試

### Phase 5：編輯頁面（可選，2 小時）
1. ✅ 創建 `DifyTestCaseEditPage.js`
2. ✅ 實作載入現有資料
3. ✅ 實作更新功能
4. ✅ 添加路由和導航

---

## ✅ 驗收標準

### 功能驗收
- [ ] 可以從列表頁導航到新增頁面
- [ ] 表單所有欄位正常顯示
- [ ] 關鍵字添加/移除/清空功能正常
- [ ] 表單驗證正確（必填欄位檢查）
- [ ] 提交成功後返回列表頁
- [ ] 頂部「返回列表」按鈕正常
- [ ] 頂部「儲存」按鈕觸發表單提交

### UX 驗收
- [ ] 頁面載入速度 < 1 秒
- [ ] 表單輸入流暢無卡頓
- [ ] 錯誤訊息清晰易懂
- [ ] 按鈕 loading 狀態正確
- [ ] 成功/失敗訊息正確顯示

### 響應式驗證
- [ ] 1920x1080 顯示正常
- [ ] 1366x768 顯示正常
- [ ] 平板（768px）顯示正常

---

## 🎯 推薦方案

### 建議使用：方案 A（單頁表單）

**理由**：
1. ✅ 實作簡單，開發成本低
2. ✅ 用戶已熟悉表單結構
3. ✅ 不需要學習新的互動模式
4. ✅ 易於維護和擴展
5. ✅ 與現有 Modal 邏輯一致

**預計工時**：6-8 小時完整實作

---

## 📝 後續優化建議

### 短期優化（1-2 週內）
- [ ] 添加表單自動儲存（localStorage）
- [ ] 添加離開頁面確認提示
- [ ] 優化關鍵字輸入（智能提示）
- [ ] 添加表單預覽功能

### 長期優化（1-2 個月內）
- [ ] 改為步驟式表單（如果需要）
- [ ] 添加批量匯入功能
- [ ] 添加範本功能
- [ ] 添加表單歷史記錄

---

## 📅 設計文檔資訊

**文檔創建日期**：2024-11-27  
**設計者**：AI Assistant  
**狀態**：設計階段（待執行）  
**預計完成時間**：1 個工作日

---

**注意事項**：
- 此文檔為設計方案，**尚未執行任何程式碼修改**
- 建議先與團隊討論後再開始實作
- 可以根據實際需求調整設計細節
