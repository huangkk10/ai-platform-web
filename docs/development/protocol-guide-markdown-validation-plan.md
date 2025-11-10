# Protocol Guide Markdown 格式驗證機制規劃

**規劃日期**：2025-11-10  
**目標**：在前端新建/編輯 Protocol Guide 時，儲存前檢查 Markdown 格式，防止無效內容進入系統

---

## 🎯 需求分析

### 核心需求
當用戶在 Web 前端新建或編輯 Protocol Guide 時，按下「儲存」按鈕前：

1. **格式驗證**：檢查內容是否符合 Markdown 標題結構
2. **阻擋儲存**：如果不符合格式，禁止儲存到資料庫
3. **友善提示**：顯示清晰的錯誤訊息，告知使用者問題所在
4. **指引修正**：提供範例或建議，幫助使用者修正內容

### 觸發場景
- ✅ **新建模式**：`/knowledge/protocol-guide/markdown-create`
- ✅ **編輯模式**：`/knowledge/protocol-guide/markdown-edit/:id`

### 驗證標準
根據現有的向量生成機制，內容必須包含：

```markdown
# 一級標題
必須至少有一個一級標題

## 二級標題
建議有二級標題（分段）

### 三級標題（可選）
三級標題為選用
```

**最低要求**：
- ✅ 至少包含 **1 個一級標題** (`# 標題`)
- ✅ 內容長度 ≥ 20 字元（避免過短內容如 "a"）
- ⚠️ 建議包含至少 1 個二級標題 (`## 標題`)（警告級別）

---

## 🏗️ 系統架構分析

### 當前儲存流程

```
用戶點擊「儲存」
    ↓
TopHeader.extraActions.Button (onClick)
    ↓
觸發事件: window.dispatchEvent(new Event('protocol-guide-save'))
    ↓
MarkdownEditorLayout.useEffect (監聽事件)
    ↓
handleSave() 函數
    ↓
onBeforeSave 鉤子（目前未使用） ← 🎯 插入驗證點
    ↓
useContentEditor.saveData()
    ↓
API: POST /api/protocol-guides/ 或 PUT /api/protocol-guides/{id}/
    ↓
Django Backend 儲存
```

### 關鍵組件

| 組件 | 路徑 | 職責 |
|------|------|------|
| **MarkdownEditorPage** | `frontend/src/pages/MarkdownEditorPage.js` | 頁面路由、Top Header 按鈕 |
| **MarkdownEditorLayout** | `frontend/src/components/editor/MarkdownEditorLayout.jsx` | 編輯器佈局、事件監聽 |
| **useContentEditor** | `frontend/src/hooks/useContentEditor.js` | 資料載入、儲存邏輯 |
| **editorConfig** | `frontend/src/config/editorConfig.js` | 配置管理（API 端點、標籤等） |

---

## 🔧 實作方案

### 方案 A：前端驗證（推薦）⭐

**架構設計**：在 `MarkdownEditorLayout.handleSave()` 中添加驗證邏輯

#### 1. 創建驗證工具

```javascript
// frontend/src/utils/markdownValidator.js

/**
 * Markdown 格式驗證工具
 * 檢查內容是否符合 Section 向量生成的最低要求
 */

/**
 * 驗證 Markdown 內容格式
 * @param {string} content - Markdown 內容
 * @returns {Object} 驗證結果
 */
export const validateMarkdownStructure = (content) => {
  const result = {
    valid: false,
    errors: [],      // 阻擋性錯誤（必須修正）
    warnings: [],    // 警告（建議修正，但不阻擋）
    stats: {
      length: 0,
      h1Count: 0,
      h2Count: 0,
      h3Count: 0,
      totalHeadings: 0
    }
  };

  // 檢查 1：內容不能為空
  if (!content || content.trim().length === 0) {
    result.errors.push('內容不能為空');
    return result;
  }

  const trimmedContent = content.trim();
  result.stats.length = trimmedContent.length;

  // 檢查 2：內容長度必須 >= 20 字元
  if (trimmedContent.length < 20) {
    result.errors.push(`內容過短（${trimmedContent.length} 字元），至少需要 20 字元`);
    return result;
  }

  // 檢查 3：統計標題數量
  const h1Matches = trimmedContent.match(/^#\s+.+$/gm);  // # 標題
  const h2Matches = trimmedContent.match(/^##\s+.+$/gm); // ## 標題
  const h3Matches = trimmedContent.match(/^###\s+.+$/gm); // ### 標題

  result.stats.h1Count = h1Matches ? h1Matches.length : 0;
  result.stats.h2Count = h2Matches ? h2Matches.length : 0;
  result.stats.h3Count = h3Matches ? h3Matches.length : 0;
  result.stats.totalHeadings = result.stats.h1Count + result.stats.h2Count + result.stats.h3Count;

  // 檢查 4：必須至少有 1 個一級標題
  if (result.stats.h1Count === 0) {
    result.errors.push('必須包含至少 1 個一級標題（# 標題）');
  }

  // 檢查 5：建議至少有 1 個二級標題（警告級別）
  if (result.stats.h2Count === 0) {
    result.warnings.push('建議添加二級標題（## 標題）來組織內容結構');
  }

  // 檢查 6：檢查標題是否有內容
  if (result.stats.totalHeadings > 0) {
    const allHeadings = [
      ...(h1Matches || []),
      ...(h2Matches || []),
      ...(h3Matches || [])
    ];

    const emptyHeadings = allHeadings.filter(heading => {
      const text = heading.replace(/^#+\s+/, '').trim();
      return text.length === 0;
    });

    if (emptyHeadings.length > 0) {
      result.errors.push(`發現 ${emptyHeadings.length} 個空標題（標題後面沒有文字）`);
    }
  }

  // 判斷是否通過驗證
  result.valid = result.errors.length === 0;

  return result;
};

/**
 * 格式化驗證錯誤訊息（用於 Modal 顯示）
 * @param {Object} validationResult - validateMarkdownStructure 的返回值
 * @returns {string} HTML 格式的錯誤訊息
 */
export const formatValidationMessage = (validationResult) => {
  let message = '<div style="text-align: left;">';

  // 顯示統計資訊
  message += '<p><strong>📊 內容統計：</strong></p>';
  message += '<ul>';
  message += `<li>內容長度：${validationResult.stats.length} 字元</li>`;
  message += `<li>一級標題（#）：${validationResult.stats.h1Count} 個</li>`;
  message += `<li>二級標題（##）：${validationResult.stats.h2Count} 個</li>`;
  message += `<li>三級標題（###）：${validationResult.stats.h3Count} 個</li>`;
  message += '</ul>';

  // 顯示錯誤
  if (validationResult.errors.length > 0) {
    message += '<p style="color: #ff4d4f; font-weight: bold;">❌ 必須修正的問題：</p>';
    message += '<ul style="color: #ff4d4f;">';
    validationResult.errors.forEach(error => {
      message += `<li>${error}</li>`;
    });
    message += '</ul>';
  }

  // 顯示警告
  if (validationResult.warnings.length > 0) {
    message += '<p style="color: #fa8c16; font-weight: bold;">⚠️ 建議改進：</p>';
    message += '<ul style="color: #fa8c16;">';
    validationResult.warnings.forEach(warning => {
      message += `<li>${warning}</li>`;
    });
    message += '</ul>';
  }

  // 顯示標準範例
  message += '<p><strong>✅ 標準格式範例：</strong></p>';
  message += '<pre style="background: #f5f5f5; padding: 12px; border-radius: 4px; overflow-x: auto;">';
  message += '# Protocol 測試指南\n\n';
  message += '## 測試目的\n';
  message += '說明測試的目標和範圍...\n\n';
  message += '## 測試步驟\n';
  message += '1. 步驟一\n';
  message += '2. 步驟二\n\n';
  message += '## 預期結果\n';
  message += '描述預期的測試結果...';
  message += '</pre>';

  message += '</div>';

  return message;
};

/**
 * 獲取內容建議（提供快速修正方案）
 * @param {string} content - 原始內容
 * @param {Object} validationResult - 驗證結果
 * @returns {string} 修正後的內容建議
 */
export const getSuggestedContent = (content, validationResult) => {
  let suggested = content;

  // 如果沒有一級標題，在開頭添加
  if (validationResult.stats.h1Count === 0) {
    suggested = '# Protocol Guide 標題\n\n' + suggested;
  }

  // 如果沒有二級標題，在第一個一級標題後添加
  if (validationResult.stats.h2Count === 0 && validationResult.stats.h1Count > 0) {
    const firstH1Index = suggested.search(/^#\s+.+$/m);
    if (firstH1Index !== -1) {
      const endOfLine = suggested.indexOf('\n', firstH1Index);
      if (endOfLine !== -1) {
        suggested = 
          suggested.slice(0, endOfLine + 1) +
          '\n## 說明\n\n' +
          suggested.slice(endOfLine + 1);
      }
    }
  }

  return suggested;
};
```

#### 2. 修改 MarkdownEditorLayout 組件

```javascript
// frontend/src/components/editor/MarkdownEditorLayout.jsx

import { Modal } from 'antd';
import { ExclamationCircleOutlined } from '@ant-design/icons';
import { 
  validateMarkdownStructure, 
  formatValidationMessage,
  getSuggestedContent 
} from '../../utils/markdownValidator';

// 在 handleSave 函數開頭添加驗證
const handleSave = useCallback(async () => {
  try {
    // 🆕 步驟 1：驗證 Markdown 格式
    console.log('🔍 開始驗證 Markdown 格式...');
    const validationResult = validateMarkdownStructure(formData.content);
    
    console.log('📊 驗證結果:', validationResult);

    // 🆕 步驟 2：如果驗證失敗，顯示錯誤訊息並阻止儲存
    if (!validationResult.valid) {
      console.log('❌ 驗證失敗，阻止儲存');
      
      Modal.error({
        title: '❌ 內容格式不符合要求',
        width: 600,
        content: (
          <div dangerouslySetInnerHTML={{ 
            __html: formatValidationMessage(validationResult) 
          }} />
        ),
        okText: '我知道了',
        onOk: () => {
          console.log('用戶關閉驗證錯誤對話框');
        }
      });
      
      // 🚫 阻止儲存
      return;
    }

    // 🆕 步驟 3：如果有警告，詢問用戶是否繼續
    if (validationResult.warnings.length > 0) {
      console.log('⚠️ 有警告訊息，詢問用戶是否繼續');
      
      const confirmed = await new Promise((resolve) => {
        Modal.confirm({
          title: '⚠️ 內容建議改進',
          width: 600,
          icon: <ExclamationCircleOutlined style={{ color: '#fa8c16' }} />,
          content: (
            <div dangerouslySetInnerHTML={{ 
              __html: formatValidationMessage(validationResult) 
            }} />
          ),
          okText: '繼續儲存',
          cancelText: '返回修改',
          onOk: () => resolve(true),
          onCancel: () => resolve(false)
        });
      });
      
      if (!confirmed) {
        console.log('用戶選擇返回修改');
        return;
      }
    }

    console.log('✅ 驗證通過，繼續儲存流程...');

    // 通知父組件開始儲存
    if (onSavingChange) onSavingChange(true);

    // 執行儲存前鉤子
    let dataToSave = { ...formData };
    if (onBeforeSave) {
      dataToSave = await onBeforeSave(dataToSave);
      if (!dataToSave) {
        if (onSavingChange) onSavingChange(false);
        return;
      }
    }

    // ... 後續原有的儲存邏輯
    
  } catch (error) {
    console.error('❌ 儲存過程發生錯誤:', error);
    setSaving(false);
    if (onSavingChange) onSavingChange(false);
  }
}, [formData, onBeforeSave, onSavingChange, saveData, /* ... 其他依賴 */]);
```

#### 3. 添加「格式檢查」按鈕（可選增強功能）

在 MarkdownEditorPage 的 Top Header 添加一個「檢查格式」按鈕：

```javascript
// frontend/src/pages/MarkdownEditorPage.js

import { CheckOutlined } from '@ant-design/icons';
import { validateMarkdownStructure, formatValidationMessage } from '../utils/markdownValidator';

const MarkdownEditorPage = () => {
  // ... 現有代碼

  // 🆕 添加格式檢查按鈕處理函數
  const handleCheckFormat = () => {
    console.log('🔍 手動檢查格式');
    
    // 觸發格式檢查事件
    const event = new CustomEvent('check-markdown-format', {
      detail: { source: 'topheader-button' }
    });
    window.dispatchEvent(event);
  };

  // 修改 extraActions
  const extraActions = (
    <Space>
      <Button
        icon={<ArrowLeftOutlined />}
        onClick={() => navigate(editorConfig.listPath)}
      >
        返回
      </Button>
      
      {/* 🆕 格式檢查按鈕 */}
      <Button
        icon={<CheckOutlined />}
        onClick={handleCheckFormat}
      >
        檢查格式
      </Button>
      
      <Button
        type="primary"
        icon={<SaveOutlined />}
        onClick={handleSave}
        loading={saving}
      >
        儲存
      </Button>
    </Space>
  );

  // ... 其餘代碼
};
```

在 MarkdownEditorLayout 中監聽格式檢查事件：

```javascript
// frontend/src/components/editor/MarkdownEditorLayout.jsx

useEffect(() => {
  const handleCheckFormatEvent = () => {
    console.log('🎯 收到格式檢查事件');
    
    const validationResult = validateMarkdownStructure(formData.content);
    
    if (validationResult.valid) {
      Modal.success({
        title: '✅ 格式檢查通過',
        width: 600,
        content: (
          <div dangerouslySetInnerHTML={{ 
            __html: formatValidationMessage(validationResult) 
          }} />
        )
      });
    } else {
      Modal.error({
        title: '❌ 格式檢查失敗',
        width: 600,
        content: (
          <div dangerouslySetInnerHTML={{ 
            __html: formatValidationMessage(validationResult) 
          }} />
        )
      });
    }
  };

  window.addEventListener('check-markdown-format', handleCheckFormatEvent);
  
  return () => {
    window.removeEventListener('check-markdown-format', handleCheckFormatEvent);
  };
}, [formData.content]);
```

---

### 方案 B：後端驗證（備援方案）

**適用場景**：如果前端驗證被繞過（直接 API 呼叫），後端作為第二道防線

#### 修改 Django Serializer

```python
# backend/api/serializers/protocol_guide_serializer.py

import re
from rest_framework import serializers
from api.models import ProtocolGuide

class ProtocolGuideSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProtocolGuide
        fields = ['id', 'title', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
    
    def validate_content(self, value):
        """
        驗證內容是否符合 Markdown 格式要求
        """
        if not value or not value.strip():
            raise serializers.ValidationError("內容不能為空")
        
        content = value.strip()
        
        # 檢查長度
        if len(content) < 20:
            raise serializers.ValidationError(
                f"內容過短（{len(content)} 字元），至少需要 20 字元"
            )
        
        # 檢查是否有一級標題
        h1_pattern = r'^#\s+.+$'
        h1_matches = re.findall(h1_pattern, content, re.MULTILINE)
        
        if len(h1_matches) == 0:
            raise serializers.ValidationError(
                "內容必須包含至少 1 個一級標題（# 標題），"
                "以便系統生成向量索引。\n\n"
                "範例格式：\n"
                "# Protocol 測試指南\n\n"
                "## 測試步驟\n"
                "..."
            )
        
        return value
```

---

## 📊 實作步驟

### Phase 1：基礎驗證（必要）

**預估時間**：1-2 小時

1. ✅ **創建驗證工具**
   - 檔案：`frontend/src/utils/markdownValidator.js`
   - 功能：
     - `validateMarkdownStructure()` - 核心驗證邏輯
     - `formatValidationMessage()` - 格式化錯誤訊息
     - `getSuggestedContent()` - 內容修正建議

2. ✅ **整合到儲存流程**
   - 檔案：`frontend/src/components/editor/MarkdownEditorLayout.jsx`
   - 位置：`handleSave()` 函數開頭
   - 功能：
     - 儲存前自動驗證
     - 驗證失敗阻止儲存
     - 顯示友善錯誤訊息

3. ✅ **測試驗證**
   - 測試案例 1：空內容 → 阻擋
   - 測試案例 2：只有 "a" → 阻擋
   - 測試案例 3：沒有標題 → 阻擋
   - 測試案例 4：有一級標題，無二級標題 → 警告但可儲存
   - 測試案例 5：完整格式 → 通過

### Phase 2：增強功能（建議）

**預估時間**：1 小時

4. ✅ **添加「檢查格式」按鈕**
   - 檔案：`frontend/src/pages/MarkdownEditorPage.js`
   - 位置：Top Header 按鈕組
   - 功能：手動觸發格式檢查

5. ✅ **實時提示（可選）**
   - 在編輯器下方顯示格式狀態指示器
   - 綠色：格式正確
   - 黃色：有警告
   - 紅色：有錯誤

### Phase 3：後端防護（可選）

**預估時間**：30 分鐘

6. ✅ **後端驗證**
   - 檔案：`backend/api/serializers/protocol_guide_serializer.py`
   - 功能：作為第二道防線，防止 API 直接呼叫繞過前端驗證

---

## 🧪 測試計畫

### 測試案例

| 案例 | 內容 | 預期結果 |
|------|------|----------|
| TC1 | 空白內容 | ❌ 阻擋儲存，錯誤訊息：「內容不能為空」 |
| TC2 | 只有 "a" | ❌ 阻擋儲存，錯誤訊息：「內容過短」 |
| TC3 | 只有純文字，無標題 | ❌ 阻擋儲存，錯誤訊息：「必須包含至少 1 個一級標題」 |
| TC4 | 有空標題 `#\n` | ❌ 阻擋儲存，錯誤訊息：「發現空標題」 |
| TC5 | 有 `# 標題`，無二級標題 | ⚠️ 警告，但允許儲存 |
| TC6 | 完整 Markdown 結構 | ✅ 通過驗證，直接儲存 |
| TC7 | 包含圖片 `[IMG:123]` | ✅ 通過驗證（不影響標題檢查） |
| TC8 | 包含表格 | ✅ 通過驗證（不影響標題檢查） |

### 手動測試步驟

1. **進入新建頁面**
   ```
   http://localhost/knowledge/protocol-guide/markdown-create
   ```

2. **測試空內容儲存**
   - 不輸入任何內容
   - 點擊「儲存」
   - 預期：顯示錯誤 Modal，無法儲存

3. **測試過短內容**
   - 輸入 "a"
   - 點擊「儲存」
   - 預期：顯示「內容過短」錯誤

4. **測試無標題內容**
   - 輸入純文字（無 `#` 標題）
   ```
   這是一段測試內容，沒有任何標題結構。
   ```
   - 點擊「儲存」
   - 預期：顯示「必須包含至少 1 個一級標題」錯誤

5. **測試警告級別（無二級標題）**
   - 輸入內容
   ```markdown
   # Protocol 測試
   
   這是測試內容。
   ```
   - 點擊「儲存」
   - 預期：顯示警告 Modal，詢問是否繼續儲存

6. **測試正確格式**
   - 輸入完整 Markdown
   ```markdown
   # Protocol 測試指南
   
   ## 測試目的
   驗證 Protocol 功能。
   
   ## 測試步驟
   1. 步驟一
   2. 步驟二
   ```
   - 點擊「儲存」
   - 預期：直接儲存成功，無任何提示

7. **測試「檢查格式」按鈕**
   - 輸入各種格式的內容
   - 點擊「檢查格式」按鈕
   - 預期：顯示格式檢查結果（包含統計資訊）

### 自動化測試（可選）

```javascript
// frontend/src/utils/__tests__/markdownValidator.test.js

import { validateMarkdownStructure } from '../markdownValidator';

describe('Markdown 格式驗證', () => {
  test('空內容應該失敗', () => {
    const result = validateMarkdownStructure('');
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('內容不能為空');
  });

  test('過短內容應該失敗', () => {
    const result = validateMarkdownStructure('a');
    expect(result.valid).toBe(false);
    expect(result.errors.length).toBeGreaterThan(0);
  });

  test('無標題內容應該失敗', () => {
    const content = '這是一段沒有標題的純文字內容，超過二十個字元。';
    const result = validateMarkdownStructure(content);
    expect(result.valid).toBe(false);
    expect(result.errors).toContain('必須包含至少 1 個一級標題（# 標題）');
  });

  test('有一級標題應該通過', () => {
    const content = '# 測試標題\n\n這是內容，超過二十個字元。';
    const result = validateMarkdownStructure(content);
    expect(result.valid).toBe(true);
    expect(result.stats.h1Count).toBe(1);
  });

  test('無二級標題應該有警告', () => {
    const content = '# 測試標題\n\n這是內容，超過二十個字元。';
    const result = validateMarkdownStructure(content);
    expect(result.valid).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
  });

  test('完整格式應該通過且無警告', () => {
    const content = '# 測試標題\n\n## 章節一\n\n內容...\n\n## 章節二\n\n更多內容...';
    const result = validateMarkdownStructure(content);
    expect(result.valid).toBe(true);
    expect(result.warnings.length).toBe(0);
    expect(result.stats.h1Count).toBe(1);
    expect(result.stats.h2Count).toBe(2);
  });
});
```

---

## 🎨 UI/UX 設計

### 錯誤 Modal 範例

```
╔══════════════════════════════════════════════════════╗
║  ❌ 內容格式不符合要求                        [×]  ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  📊 內容統計：                                       ║
║  • 內容長度：15 字元                                 ║
║  • 一級標題（#）：0 個                               ║
║  • 二級標題（##）：0 個                              ║
║  • 三級標題（###）：0 個                             ║
║                                                      ║
║  ❌ 必須修正的問題：                                 ║
║  • 內容過短（15 字元），至少需要 20 字元             ║
║  • 必須包含至少 1 個一級標題（# 標題）               ║
║                                                      ║
║  ✅ 標準格式範例：                                   ║
║  ┌────────────────────────────────────────────┐    ║
║  │ # Protocol 測試指南                        │    ║
║  │                                            │    ║
║  │ ## 測試目的                                │    ║
║  │ 說明測試的目標和範圍...                    │    ║
║  │                                            │    ║
║  │ ## 測試步驟                                │    ║
║  │ 1. 步驟一                                  │    ║
║  │ 2. 步驟二                                  │    ║
║  │                                            │    ║
║  │ ## 預期結果                                │    ║
║  │ 描述預期的測試結果...                      │    ║
║  └────────────────────────────────────────────┘    ║
║                                                      ║
║                              [ 我知道了 ]            ║
╚══════════════════════════════════════════════════════╝
```

### 警告 Modal 範例

```
╔══════════════════════════════════════════════════════╗
║  ⚠️ 內容建議改進                              [×]  ║
╠══════════════════════════════════════════════════════╣
║                                                      ║
║  📊 內容統計：                                       ║
║  • 內容長度：50 字元                                 ║
║  • 一級標題（#）：1 個 ✅                            ║
║  • 二級標題（##）：0 個                              ║
║                                                      ║
║  ⚠️ 建議改進：                                       ║
║  • 建議添加二級標題（## 標題）來組織內容結構        ║
║                                                      ║
║  雖然目前格式符合最低要求，但添加二級標題能讓       ║
║  AI 助手更好地理解和檢索您的內容。                  ║
║                                                      ║
║                   [ 返回修改 ]  [ 繼續儲存 ]        ║
╚══════════════════════════════════════════════════════╝
```

---

## 📈 效益分析

### 預期效果

1. **防止無效內容** ✅
   - 100% 阻擋空白或過短內容（如 "a"）
   - 100% 阻擋無標題結構的內容

2. **提升內容質量** ✅
   - 強制用戶使用 Markdown 標題結構
   - 促使用戶組織內容層次

3. **改善 AI 檢索** ✅
   - 確保所有 Protocol Guide 都能生成 Section 向量
   - 減少「引用來源缺失」問題

4. **提升用戶體驗** ✅
   - 友善的錯誤提示
   - 提供範例和建議
   - 即時反饋

### 相容性

- ✅ **不影響現有資料**：只對新建和編輯時生效
- ✅ **不影響其他 Assistant**：只針對 Protocol Guide
- ✅ **向下相容**：現有的正確格式內容不受影響

---

## 🔄 未來擴展

### 可能的增強功能

1. **實時格式提示**
   - 在編輯器下方顯示格式狀態條
   - 實時顯示標題統計

2. **自動修正建議**
   - 點擊「自動修正」按鈕
   - 系統自動添加基礎標題結構

3. **範本系統**
   - 提供多種預設範本
   - 用戶選擇範本快速開始

4. **AI 輔助格式化**
   - 使用 AI 分析內容
   - 自動建議標題結構

5. **批量修正工具**
   - 掃描所有現有 Protocol Guide
   - 批量修正不符合格式的內容

---

## 📚 相關文檔

- **問題分析**：`/docs/debugging/protocol-assistant-citation-missing-corrected.md`
- **解決方案比較**：`/docs/features/protocol-guide-citation-missing-all-solutions.md`
- **向量生成機制**：`/docs/vector-search/protocol-guide-vector-auto-generation.md`
- **內容驗證指南**：`/docs/features/protocol-guide-content-validation-guide.md`

---

## ✅ 規劃檢查清單

### 技術可行性
- [x] 前端驗證邏輯設計完成
- [x] 錯誤訊息格式設計完成
- [x] UI/UX 設計完成
- [x] 測試計畫制定完成

### 實作準備
- [ ] 創建驗證工具檔案 `markdownValidator.js`
- [ ] 修改 MarkdownEditorLayout 組件
- [ ] 添加「檢查格式」按鈕（可選）
- [ ] 編寫單元測試

### 測試驗證
- [ ] 手動測試所有案例
- [ ] 自動化測試（可選）
- [ ] 用戶接受度測試

### 文檔更新
- [ ] 更新用戶手冊
- [ ] 更新開發文檔
- [ ] 記錄實作細節

---

**規劃完成日期**：2025-11-10  
**規劃者**：AI Platform Team  
**狀態**：✅ 規劃完成，等待用戶確認後開始實作

**下一步**：
1. 用戶確認規劃方案
2. 開始 Phase 1 實作（1-2 小時）
3. 測試驗證
4. 部署上線
