# 🖼️ Web Assistant 檔案上傳與 OCR 整合規劃

> **建立日期**: 2025-11-30  
> **狀態**: 📋 規劃中（尚未執行）  
> **目標**: 讓 Web RVT Assistant 和 Web Protocol Assistant 支援圖片/文字檔上傳，並整合 OCR 功能

---

## 📋 需求摘要

### 功能目標
1. **UI 增強**：在聊天輸入框旁新增「添加檔案」按鈕（參考 Web AI OCR 的設計）
2. **檔案上傳**：支援上傳圖片（jpg, png, gif, bmp, webp）和文字檔（txt, log, md）
3. **OCR 整合**：上傳圖片後，自動呼叫 OCR Function API 取得文字內容
4. **AI 分析**：將 OCR 結果或文字檔內容作為上下文，傳給對應的 Dify AI 進行分析

### 適用頁面
- `RvtAssistantChatPage.js` - RVT Assistant 聊天頁面
- `ProtocolAssistantChatPage.js` - Protocol Assistant 聊天頁面

---

## 🎯 參考範本：Web AI OCR

### 現有 AI OCR 頁面結構
```
frontend/src/pages/
├── AiOcrPage.js              # AI OCR 主頁面（參考用）
├── RvtAssistantChatPage.js   # ✅ 待修改
└── ProtocolAssistantChatPage.js  # ✅ 待修改
```

---

## 🏗️ 整體架構設計

### 資料流程圖
```
┌─────────────────────────────────────────────────────────────────┐
│                         使用者操作                               │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. 點擊「+」按鈕，選擇上傳檔案（圖片或文字檔）                    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. 前端判斷檔案類型                                             │
│     ├─ 圖片 (jpg/png/...) → 呼叫 OCR API                        │
│     └─ 文字檔 (txt/log/md) → 直接讀取內容                        │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. 後端處理                                                     │
│     ├─ OCR API: /api/ocr/analyze/                               │
│     │   └─ 呼叫 OCR Function (Dify) 取得圖片文字                 │
│     └─ 文字檔: 前端直接讀取，不需後端處理                         │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. 組合訊息                                                     │
│     ├─ 使用者問題 + OCR 文字結果                                 │
│     └─ 或 使用者問題 + 文字檔內容                                │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. 發送到對應的 Dify AI                                         │
│     ├─ RVT Assistant → RVT Guide Dify App                       │
│     └─ Protocol Assistant → Protocol Guide Dify App             │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. 顯示 AI 回應                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 檔案修改清單

### 前端修改

#### 1. 新增共用元件
```
frontend/src/components/chat/
├── FileUploadButton.jsx      # ✅ 新增：檔案上傳按鈕元件
├── FilePreview.jsx           # ✅ 新增：已上傳檔案預覽元件
└── ChatInputWithUpload.jsx   # ✅ 新增：帶上傳功能的輸入框元件
```

#### 2. 修改現有頁面
```
frontend/src/pages/
├── RvtAssistantChatPage.js       # ✅ 修改：整合檔案上傳
├── RvtAssistantChatPage.css      # ✅ 修改：新增樣式
├── ProtocolAssistantChatPage.js  # ✅ 修改：整合檔案上傳
└── ProtocolAssistantChatPage.css # ✅ 修改：新增樣式
```

#### 3. 新增/修改 Hooks
```
frontend/src/hooks/
├── useFileUpload.js          # ✅ 新增：檔案上傳邏輯
├── useOcrService.js          # ✅ 新增：OCR 服務呼叫
├── useRvtChat.js             # ✅ 修改：整合檔案內容
└── useProtocolAssistantChat.js  # ✅ 修改：整合檔案內容
```

#### 4. 新增 API 服務
```
frontend/src/services/
└── ocrService.js             # ✅ 新增：OCR API 呼叫服務
```

### 後端修改

#### 1. 新增 OCR API ViewSet
```
backend/api/views/
└── ocr_views.py              # ✅ 新增：OCR API 端點
```

#### 2. 修改 URL 路由
```
backend/api/urls.py           # ✅ 修改：新增 OCR 路由
```

#### 3. OCR 服務（已完成）
```
backend/library/ocr_function/
├── __init__.py               # ✓ 已完成
└── ocr_service.py            # ✓ 已完成
```

---

## 🔧 詳細實作規劃

### Phase 1：後端 OCR API 端點

#### 1.1 建立 OCR ViewSet (`backend/api/views/ocr_views.py`)
```python
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework import status
from library.ocr_function import ocr_image_from_bytes

class OCRAnalyzeView(APIView):
    """
    OCR 圖片分析 API
    
    POST /api/ocr/analyze/
    - 接收圖片檔案
    - 呼叫 OCR Function 取得文字
    - 回傳辨識結果
    """
    parser_classes = [MultiPartParser]
    
    def post(self, request):
        file = request.FILES.get('file')
        if not file:
            return Response({'error': '請上傳檔案'}, status=400)
        
        # 檢查檔案類型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp']
        if file.content_type not in allowed_types:
            return Response({'error': '不支援的檔案格式'}, status=400)
        
        # 呼叫 OCR 服務
        result = ocr_image_from_bytes(
            image_data=file.read(),
            filename=file.name
        )
        
        if result['success']:
            return Response({
                'success': True,
                'text': result['text'],
                'filename': file.name
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=500)
```

#### 1.2 註冊路由 (`backend/api/urls.py`)
```python
from api.views.ocr_views import OCRAnalyzeView

urlpatterns = [
    # ... 現有路由
    path('ocr/analyze/', OCRAnalyzeView.as_view(), name='ocr-analyze'),
]
```

---

### Phase 2：前端共用元件

#### 2.1 FileUploadButton 元件 (`frontend/src/components/chat/FileUploadButton.jsx`)
```jsx
import React, { useRef } from 'react';
import { Button, Tooltip } from 'antd';
import { PlusOutlined, PaperClipOutlined } from '@ant-design/icons';

const FileUploadButton = ({ onFileSelect, disabled, loading }) => {
  const fileInputRef = useRef(null);
  
  const acceptedTypes = [
    'image/jpeg',
    'image/png', 
    'image/gif',
    'image/bmp',
    'image/webp',
    'text/plain',
    '.txt',
    '.log',
    '.md'
  ].join(',');
  
  const handleClick = () => {
    fileInputRef.current?.click();
  };
  
  const handleFileChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFileSelect(file);
    }
    // 清除 input 以便重複選擇相同檔案
    e.target.value = '';
  };
  
  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleFileChange}
        accept={acceptedTypes}
        style={{ display: 'none' }}
      />
      <Tooltip title="上傳圖片或文字檔">
        <Button
          type="text"
          icon={<PlusOutlined />}
          onClick={handleClick}
          disabled={disabled || loading}
          loading={loading}
        />
      </Tooltip>
    </>
  );
};

export default FileUploadButton;
```

#### 2.2 FilePreview 元件 (`frontend/src/components/chat/FilePreview.jsx`)
```jsx
import React from 'react';
import { Card, Image, Typography, Button, Tag, Spin } from 'antd';
import { 
  FileTextOutlined, 
  FileImageOutlined, 
  CloseOutlined,
  CheckCircleOutlined,
  LoadingOutlined
} from '@ant-design/icons';

const { Text } = Typography;

const FilePreview = ({ 
  file,           // 上傳的檔案
  ocrText,        // OCR 辨識結果（圖片用）
  textContent,    // 文字檔內容
  isProcessing,   // 是否正在處理中
  onRemove        // 移除檔案回調
}) => {
  const isImage = file?.type?.startsWith('image/');
  const isTextFile = file?.type === 'text/plain' || 
                     file?.name?.endsWith('.txt') ||
                     file?.name?.endsWith('.log') ||
                     file?.name?.endsWith('.md');
  
  return (
    <Card 
      size="small" 
      style={{ marginBottom: 8 }}
      extra={
        <Button 
          type="text" 
          size="small" 
          icon={<CloseOutlined />} 
          onClick={onRemove}
          disabled={isProcessing}
        />
      }
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        {/* 檔案圖示 */}
        {isImage ? (
          <Image
            src={URL.createObjectURL(file)}
            width={60}
            height={60}
            style={{ objectFit: 'cover', borderRadius: 4 }}
          />
        ) : (
          <FileTextOutlined style={{ fontSize: 32, color: '#1890ff' }} />
        )}
        
        {/* 檔案資訊 */}
        <div style={{ flex: 1 }}>
          <Text strong ellipsis style={{ maxWidth: 200 }}>
            {file.name}
          </Text>
          <br />
          <Text type="secondary" style={{ fontSize: 12 }}>
            {(file.size / 1024).toFixed(1)} KB
          </Text>
          
          {/* 處理狀態 */}
          {isProcessing && (
            <Tag icon={<LoadingOutlined spin />} color="processing">
              {isImage ? 'OCR 辨識中...' : '讀取中...'}
            </Tag>
          )}
          {!isProcessing && (ocrText || textContent) && (
            <Tag icon={<CheckCircleOutlined />} color="success">
              已處理
            </Tag>
          )}
        </div>
      </div>
      
      {/* 預覽文字內容（可選） */}
      {!isProcessing && (ocrText || textContent) && (
        <div style={{ 
          marginTop: 8, 
          padding: 8, 
          background: '#f5f5f5', 
          borderRadius: 4,
          maxHeight: 100,
          overflow: 'auto'
        }}>
          <Text style={{ fontSize: 12, whiteSpace: 'pre-wrap' }}>
            {(ocrText || textContent)?.substring(0, 300)}
            {(ocrText || textContent)?.length > 300 && '...'}
          </Text>
        </div>
      )}
    </Card>
  );
};

export default FilePreview;
```

#### 2.3 useFileUpload Hook (`frontend/src/hooks/useFileUpload.js`)
```javascript
import { useState, useCallback } from 'react';
import { message } from 'antd';
import { analyzeImageOCR } from '../services/ocrService';

const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

export const useFileUpload = () => {
  const [uploadedFile, setUploadedFile] = useState(null);
  const [fileContent, setFileContent] = useState(null); // OCR 文字或文字檔內容
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState(null);
  
  // 處理檔案選擇
  const handleFileSelect = useCallback(async (file) => {
    // 檢查檔案大小
    if (file.size > MAX_FILE_SIZE) {
      message.error('檔案大小不能超過 10MB');
      return;
    }
    
    setUploadedFile(file);
    setFileContent(null);
    setError(null);
    setIsProcessing(true);
    
    try {
      const isImage = file.type.startsWith('image/');
      
      if (isImage) {
        // 圖片：呼叫 OCR API
        const result = await analyzeImageOCR(file);
        if (result.success) {
          setFileContent(result.text);
          message.success('圖片 OCR 辨識完成');
        } else {
          throw new Error(result.error || 'OCR 辨識失敗');
        }
      } else {
        // 文字檔：直接讀取
        const text = await readTextFile(file);
        setFileContent(text);
        message.success('文字檔讀取完成');
      }
    } catch (err) {
      console.error('檔案處理失敗:', err);
      setError(err.message);
      message.error(`檔案處理失敗: ${err.message}`);
    } finally {
      setIsProcessing(false);
    }
  }, []);
  
  // 讀取文字檔
  const readTextFile = (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error('讀取檔案失敗'));
      reader.readAsText(file);
    });
  };
  
  // 清除上傳的檔案
  const clearFile = useCallback(() => {
    setUploadedFile(null);
    setFileContent(null);
    setError(null);
  }, []);
  
  // 取得要附加到訊息的內容
  const getFileContextForMessage = useCallback(() => {
    if (!fileContent) return null;
    
    const isImage = uploadedFile?.type?.startsWith('image/');
    const prefix = isImage 
      ? `【以下是從上傳圖片中 OCR 辨識出的文字內容】\n`
      : `【以下是上傳的文字檔 ${uploadedFile?.name} 的內容】\n`;
    
    return `${prefix}---\n${fileContent}\n---\n\n`;
  }, [fileContent, uploadedFile]);
  
  return {
    uploadedFile,
    fileContent,
    isProcessing,
    error,
    handleFileSelect,
    clearFile,
    getFileContextForMessage,
    hasFile: !!uploadedFile,
    hasContent: !!fileContent
  };
};

export default useFileUpload;
```

#### 2.4 OCR API 服務 (`frontend/src/services/ocrService.js`)
```javascript
import api from './api';

/**
 * 呼叫 OCR API 分析圖片
 * @param {File} file - 圖片檔案
 * @returns {Promise<{success: boolean, text?: string, error?: string}>}
 */
export const analyzeImageOCR = async (file) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/ocr/analyze/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // OCR 可能需要較長時間
    });
    
    return response.data;
  } catch (error) {
    console.error('OCR API 錯誤:', error);
    return {
      success: false,
      error: error.response?.data?.error || error.message || 'OCR 服務錯誤'
    };
  }
};
```

---

### Phase 3：整合到 Assistant 頁面

#### 3.1 修改 RvtAssistantChatPage.js
```jsx
// 新增 imports
import FileUploadButton from '../components/chat/FileUploadButton';
import FilePreview from '../components/chat/FilePreview';
import { useFileUpload } from '../hooks/useFileUpload';

// 在元件中使用
const RvtAssistantChatPage = () => {
  // 現有的 hooks
  const { messages, sendMessage, isLoading, ... } = useRvtChat();
  
  // 新增：檔案上傳 hook
  const {
    uploadedFile,
    fileContent,
    isProcessing,
    handleFileSelect,
    clearFile,
    getFileContextForMessage,
    hasContent
  } = useFileUpload();
  
  // 修改：發送訊息邏輯
  const handleSendMessage = async () => {
    if (!inputMessage.trim() && !hasContent) return;
    
    // 組合訊息：檔案內容 + 使用者問題
    let fullMessage = inputMessage;
    const fileContext = getFileContextForMessage();
    if (fileContext) {
      fullMessage = fileContext + '使用者問題：' + inputMessage;
    }
    
    // 發送訊息
    await sendMessage(fullMessage);
    
    // 清除檔案（可選：根據需求決定是否保留）
    clearFile();
    setInputMessage('');
  };
  
  return (
    <div className="chat-container">
      {/* 訊息列表 */}
      <MessageList messages={messages} />
      
      {/* 檔案預覽區 */}
      {uploadedFile && (
        <FilePreview
          file={uploadedFile}
          ocrText={uploadedFile?.type?.startsWith('image/') ? fileContent : null}
          textContent={!uploadedFile?.type?.startsWith('image/') ? fileContent : null}
          isProcessing={isProcessing}
          onRemove={clearFile}
        />
      )}
      
      {/* 輸入區 */}
      <div className="input-area">
        {/* 新增：檔案上傳按鈕 */}
        <FileUploadButton
          onFileSelect={handleFileSelect}
          disabled={isLoading}
          loading={isProcessing}
        />
        
        {/* 現有：文字輸入框 */}
        <Input.TextArea
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          placeholder="請描述你的日誌問題或上傳檔案..."
          disabled={isLoading || isProcessing}
          ...
        />
        
        {/* 現有：發送按鈕 */}
        <Button
          type="primary"
          onClick={handleSendMessage}
          disabled={isLoading || isProcessing || (!inputMessage.trim() && !hasContent)}
          loading={isLoading}
        >
          發送
        </Button>
      </div>
    </div>
  );
};
```

#### 3.2 Protocol Assistant 同樣的修改模式

---

## 📊 任務清單

### Phase 1：後端 API（預估 30 分鐘）
- [ ] 建立 `backend/api/views/ocr_views.py`
- [ ] 在 `backend/api/urls.py` 註冊路由
- [ ] 測試 OCR API 端點

### Phase 2：前端共用元件（預估 1 小時）
- [ ] 建立 `FileUploadButton.jsx`
- [ ] 建立 `FilePreview.jsx`
- [ ] 建立 `useFileUpload.js` Hook
- [ ] 建立 `ocrService.js` API 服務

### Phase 3：整合 RVT Assistant（預估 1 小時）
- [ ] 修改 `RvtAssistantChatPage.js` 整合檔案上傳
- [ ] 修改 `RvtAssistantChatPage.css` 新增樣式
- [ ] 修改 `useRvtChat.js` 支援檔案內容（如需要）
- [ ] 測試完整流程

### Phase 4：整合 Protocol Assistant（預估 30 分鐘）
- [ ] 修改 `ProtocolAssistantChatPage.js` 整合檔案上傳
- [ ] 修改 `ProtocolAssistantChatPage.css` 新增樣式
- [ ] 測試完整流程

### Phase 5：測試與優化（預估 30 分鐘）
- [ ] 端對端測試
- [ ] 錯誤處理優化
- [ ] UI/UX 微調

---

## 🎨 UI 設計參考

### 輸入區域佈局
```
┌────────────────────────────────────────────────────────────┐
│ ┌──────────────────────────────────────────────────────┐   │
│ │ [已上傳檔案預覽]                              [X 移除]│   │
│ │ 📷 screenshot.png  156 KB  ✓ OCR 已完成              │   │
│ │ ┌──────────────────────────────────────────────────┐ │   │
│ │ │ 辨識文字預覽：Jenkins CI/CD 的 Console Log...    │ │   │
│ │ └──────────────────────────────────────────────────┘ │   │
│ └──────────────────────────────────────────────────────┘   │
│                                                            │
│ ┌──┐ ┌────────────────────────────────────────────┐ ┌────┐│
│ │ + │ │ 請描述你的日誌問題或上傳檔案...            │ │發送││
│ └──┘ └────────────────────────────────────────────┘ └────┘│
└────────────────────────────────────────────────────────────┘
```

### 按鈕位置（參考 Web AI OCR）
- `+` 按鈕放在輸入框左側
- 點擊後彈出檔案選擇對話框
- 支援拖放上傳（可選功能）

---

## ⚠️ 注意事項

### 1. 檔案大小限制
- 圖片：最大 10MB
- 文字檔：最大 5MB

### 2. 支援的檔案格式
| 類型 | 格式 | 處理方式 |
|------|------|----------|
| 圖片 | jpg, jpeg, png, gif, bmp, webp | 呼叫 OCR API |
| 文字檔 | txt, log, md | 前端直接讀取 |

### 3. OCR 處理時間
- 預估 10-30 秒，需顯示 loading 狀態
- 設定 120 秒超時

### 4. 錯誤處理
- 檔案格式不支援
- 檔案太大
- OCR 辨識失敗
- 網路錯誤

### 5. 安全性考量
- 後端驗證檔案類型
- 限制檔案大小
- 不儲存上傳的檔案（僅處理後丟棄）

---

## 📚 相關文件

- `docs/development/ocr-function-api-integration-plan.md` - OCR Function API 整合規劃
- `library/ocr_function/ocr_service.py` - OCR 服務模組
- `frontend/src/pages/AiOcrPage.js` - AI OCR 頁面（UI 參考）

---

**預估總工時：3.5-4 小時**

**下一步**：確認規劃後開始執行 Phase 1（後端 API）
