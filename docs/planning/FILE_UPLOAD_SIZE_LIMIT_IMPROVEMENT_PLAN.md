# 📋 Protocol Assistant 檔案上傳大小限制改善計畫

## 📅 文檔資訊

| 項目 | 內容 |
|------|------|
| **建立日期** | 2025-12-02 |
| **問題來源** | 用戶上傳 5.75MB 的 Jenkins 日誌檔導致系統當機 |
| **影響範圍** | Protocol Assistant、RVT Assistant（所有啟用檔案上傳的 Assistant） |
| **優先級** | 🔴 高（影響系統穩定性） |
| **狀態** | ✅ Phase 1 已完成 |
| **完成日期** | 2025-12-02 |

---

## 🔥 問題描述

### 事件經過

用戶在 Protocol Assistant 上傳了一個 Jenkins CI/CD 日誌檔案 `28.txt`：

| 項目 | 數值 |
|------|------|
| 檔案大小 | **5.75 MB** |
| 字元數 | **6,033,590 字元** |
| 行數 | 17,900 行 |
| 預估 Token 數 | ~150 萬 tokens |

上傳後系統變得非常繁忙，最終導致瀏覽器當機。

### 問題根因分析

```
用戶上傳 28.txt (5.75MB)
         │
         ▼
┌─────────────────────────────────────────┐
│ 1. FileReader.readAsText()              │
│    載入 6MB 文字到瀏覽器記憶體           │ ← 🔴 記憶體暴增
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 2. 組合 prompt (6MB+)                   │
│    字串操作消耗大量 CPU/記憶體           │ ← 🔴 瀏覽器開始卡頓
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 3. React setMessages()                  │
│    嘗試渲染 6MB 訊息內容                 │ ← 🔴 UI 凍結
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│ 4. fetch() POST 6MB+ body               │
│    網路傳輸/伺服器處理超時               │ ← 🔴 請求失敗
└─────────────────────────────────────────┘
         │
         ▼
      💥 系統當機
```

### 現有架構的問題

目前的檔案處理完全在**前端**進行：

```javascript
// frontend/src/components/chat/CommonAssistantChatPage.jsx
// 問題代碼位置：約第 255-262 行

ocrText = await new Promise((resolve, reject) => {
  const reader = new FileReader();
  reader.onload = (e) => resolve(e.target.result);  // ⚠️ 載入全部內容到記憶體
  reader.onerror = () => reject(new Error('讀取檔案失敗'));
  reader.readAsText(fileToProcess.file);
});
```

**問題點：**
1. 前端 `MAX_FILE_SIZE = 10MB`（太大）
2. 沒有字元數限制
3. 所有內容直接載入瀏覽器記憶體
4. 大內容直接渲染到 React 組件
5. 大 JSON body 直接發送到後端

---

## 🎯 改善目標

| 目標 | 說明 |
|------|------|
| **防止瀏覽器當機** | 大檔案不應該導致前端凍結或崩潰 |
| **友善的錯誤提示** | 用戶應該在上傳時就知道檔案是否可以處理 |
| **智能內容處理** | 對於大型日誌檔，自動擷取關鍵內容 |
| **維持功能完整** | 小檔案的處理流程不受影響 |

---

## 📐 限制值設計

### 各層級限制考量

| 層級 | 限制因素 | 建議值 |
|------|----------|--------|
| **LLM Token** | GPT-4: 128K, Claude: 200K | ~50K tokens 安全 |
| **Dify API** | 模型 context window | ~30K tokens |
| **瀏覽器效能** | 記憶體/渲染 | < 500KB 文字 |
| **Nginx** | client_max_body_size | 預設 1MB |
| **Django** | DATA_UPLOAD_MAX_MEMORY_SIZE | 預設 2.5MB |

### Token 換算參考

```
中文：約 1.5-2 字元 = 1 token
英文：約 4 字元 = 1 token  
混合：約 3 字元 = 1 token（保守估計）
```

### 建議的限制值

| 項目 | 限制值 | 說明 |
|------|--------|------|
| **前端檔案大小** | **500 KB** | 防止上傳過大檔案 |
| **前端字元數警告** | **100,000 字元** | 超過顯示警告 |
| **後端內容截斷** | **30,000 字元** | 發送給 AI 的最大內容 |
| **發送給 Dify** | **~50,000 字元** | 包含 prompt + 檔案內容 |

---

## 🏗️ 改善方案

### 方案概覽

採用**兩階段改善**策略：

| 階段 | 內容 | 複雜度 | 效果 |
|------|------|--------|------|
| **Phase 1** | 前端限制 + 友善提示 | 低 | 防止當機 |
| **Phase 2** | 後端處理 + 智能摘要 | 中 | 支援大檔案 |

---

## 📦 Phase 1：前端限制與友善提示

### 目標
- 防止瀏覽器當機
- 給用戶清楚的錯誤提示
- 最小化代碼變更

### 修改檔案清單

| 檔案 | 修改內容 |
|------|----------|
| `frontend/src/hooks/useFileUpload.js` | 降低 `MAX_FILE_SIZE`、新增字元數檢查 |
| `frontend/src/components/chat/CommonAssistantChatPage.jsx` | 讀取後檢查內容長度、超限顯示錯誤 |

### 詳細修改內容

#### 1. `useFileUpload.js` - 修改檔案大小限制

```javascript
// 修改前
const MAX_FILE_SIZE = 10 * 1024 * 1024; // 10MB

// 修改後
const MAX_FILE_SIZE = 500 * 1024; // 500KB（文字檔）
const MAX_IMAGE_SIZE = 5 * 1024 * 1024; // 5MB（圖片，因為要 OCR）
```

#### 2. `useFileUpload.js` - 新增常數定義

```javascript
// 新增內容長度限制常數
const MAX_TEXT_CONTENT_LENGTH = 100000; // 10 萬字元
const RECOMMENDED_CONTENT_LENGTH = 30000; // 建議 3 萬字元以內
```

#### 3. `CommonAssistantChatPage.jsx` - 讀取後檢查內容長度

```javascript
// 在讀取文字檔後添加長度檢查
if (!fileToProcess.isImage) {
  console.log('📄 [CommonAssistantChatPage] 讀取文字檔...');
  ocrText = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (e) => resolve(e.target.result);
    reader.onerror = () => reject(new Error('讀取檔案失敗'));
    reader.readAsText(fileToProcess.file);
  });
  
  // 🆕 新增：檢查內容長度
  const MAX_CONTENT_LENGTH = 100000; // 10 萬字元
  if (ocrText.length > MAX_CONTENT_LENGTH) {
    message.error(`檔案內容過大（${(ocrText.length / 1000).toFixed(0)}K 字元），最大支援 100K 字元。建議上傳較小的檔案或擷取關鍵內容。`);
    setLoading(false);
    setLoadingStartTime(null);
    return; // 中止處理
  }
  
  // 🆕 新增：超過建議值顯示警告
  const RECOMMENDED_LENGTH = 30000; // 3 萬字元
  if (ocrText.length > RECOMMENDED_LENGTH) {
    message.warning(`檔案內容較大（${(ocrText.length / 1000).toFixed(0)}K 字元），處理可能需要較長時間。`);
  }
  
  console.log('✅ [CommonAssistantChatPage] 讀取成功，文字長度:', ocrText?.length);
}
```

### Phase 1 預期效果

| 場景 | 修改前 | 修改後 |
|------|--------|--------|
| 上傳 28.txt (5.75MB) | 💥 瀏覽器當機 | ❌ 上傳時被拒絕「檔案過大」 |
| 上傳 200KB 文字檔 | ✅ 正常 | ✅ 正常 |
| 上傳 600KB 文字檔 | 💥 可能卡頓 | ❌ 上傳時被拒絕「檔案過大」 |

---

## 📦 Phase 2：後端處理與智能摘要（進階）

### 目標
- 支援更大的檔案（如 Jenkins 日誌）
- 後端智能擷取關鍵內容
- 瀏覽器只負責上傳，不處理內容

### 架構變更

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端（瀏覽器）                             │
├─────────────────────────────────────────────────────────────────┤
│  1. 用戶選擇檔案                                                 │
│  2. FormData 串流上傳（不讀取全部內容）                           │
│  3. 顯示「已上傳 xxx.txt」簡短訊息                                │
│  4. 等待後端回應                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ (multipart/form-data)
┌─────────────────────────────────────────────────────────────────┐
│                        後端（Django）                            │
├─────────────────────────────────────────────────────────────────┤
│  1. 接收檔案                                                     │
│  2. 檢查大小限制（5MB）                                          │
│  3. 讀取內容並智能處理：                                          │
│     - 小檔案（< 30K 字元）→ 完整保留                             │
│     - 大檔案（> 30K 字元）→ 智能摘要                             │
│  4. 組合 prompt 發送給 Dify                                      │
│  5. 返回 AI 回答                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 新增檔案清單

| 檔案 | 說明 |
|------|------|
| `library/common/file_processing/text_file_processor.py` | **新增** 文字檔處理器（摘要、截斷） |
| `library/common/file_processing/__init__.py` | **新增** 模組初始化 |
| `library/protocol_guide/api_handlers.py` | **修改** 新增 `handle_chat_with_file_api()` |
| `backend/api/urls.py` | **修改** 新增路由 |
| `backend/api/views/dify_chat_views.py` | **修改** 新增視圖函數 |
| `frontend/src/hooks/useProtocolAssistantChat.js` | **修改** 新增 `sendMessageWithFile()` |
| `frontend/src/components/chat/CommonAssistantChatPage.jsx` | **修改** 改用後端處理 |

### 智能摘要邏輯

```python
# library/common/file_processing/text_file_processor.py

class TextFileProcessor:
    """文字檔處理器 - 智能摘要大型檔案"""
    
    # 限制常數
    MAX_OUTPUT_LENGTH = 30000  # 輸出最大 3 萬字元
    HEADER_LENGTH = 3000      # 保留開頭
    FOOTER_LENGTH = 3000      # 保留結尾
    
    # 關鍵字（用於提取重要行）
    ERROR_KEYWORDS = ['error', 'fail', 'exception', 'critical', 'fatal']
    WARNING_KEYWORDS = ['warning', 'warn', 'caution']
    
    def process(self, content: str, filename: str) -> dict:
        """
        處理文字檔案內容
        
        Args:
            content: 檔案內容
            filename: 檔案名稱
            
        Returns:
            {
                'processed_content': str,  # 處理後的內容
                'is_truncated': bool,      # 是否被截斷
                'original_length': int,    # 原始長度
                'processed_length': int,   # 處理後長度
                'summary_info': str        # 摘要說明
            }
        """
        original_length = len(content)
        
        # 小檔案：直接返回
        if original_length <= self.MAX_OUTPUT_LENGTH:
            return {
                'processed_content': content,
                'is_truncated': False,
                'original_length': original_length,
                'processed_length': original_length,
                'summary_info': None
            }
        
        # 大檔案：智能摘要
        summary_parts = []
        
        # 1. 檔案開頭
        summary_parts.append("=== 檔案開頭 ===")
        summary_parts.append(content[:self.HEADER_LENGTH])
        
        # 2. 提取錯誤/警告行
        lines = content.split('\n')
        error_lines = []
        warning_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in self.ERROR_KEYWORDS):
                error_lines.append(line)
            elif any(kw in line_lower for kw in self.WARNING_KEYWORDS):
                warning_lines.append(line)
        
        if error_lines:
            summary_parts.append("\n=== 錯誤訊息 ===")
            summary_parts.append('\n'.join(error_lines[:50]))  # 最多 50 行
        
        if warning_lines:
            summary_parts.append("\n=== 警告訊息 ===")
            summary_parts.append('\n'.join(warning_lines[:30]))  # 最多 30 行
        
        # 3. 檔案結尾
        summary_parts.append("\n=== 檔案結尾 ===")
        summary_parts.append(content[-self.FOOTER_LENGTH:])
        
        # 組合結果
        processed_content = '\n'.join(summary_parts)
        
        # 確保不超過限制
        if len(processed_content) > self.MAX_OUTPUT_LENGTH:
            processed_content = processed_content[:self.MAX_OUTPUT_LENGTH] + "\n...(內容已截斷)"
        
        summary_info = (
            f"[系統自動摘要] 原始檔案 {filename} 共 {original_length:,} 字元，"
            f"已擷取關鍵內容（錯誤: {len(error_lines)} 行, 警告: {len(warning_lines)} 行）"
        )
        
        return {
            'processed_content': processed_content,
            'is_truncated': True,
            'original_length': original_length,
            'processed_length': len(processed_content),
            'summary_info': summary_info
        }
```

### 新 API 端點

```python
# POST /api/protocol-guide/chat-with-file/

# 請求（multipart/form-data）:
{
    "file": <上傳的檔案>,
    "message": "請分析這個日誌中的錯誤",
    "conversation_id": "xxx-xxx-xxx"
}

# 回應:
{
    "success": true,
    "answer": "根據日誌分析，發現以下錯誤...",
    "file_info": {
        "filename": "28.txt",
        "original_size": 6033590,
        "processed_size": 28500,
        "is_truncated": true
    },
    "conversation_id": "xxx-xxx-xxx",
    "message_id": "yyy-yyy-yyy"
}
```

### Phase 2 預期效果

| 場景 | Phase 1 | Phase 2 |
|------|---------|---------|
| 上傳 28.txt (5.75MB) | ❌ 被拒絕 | ✅ 後端摘要處理，返回分析結果 |
| 上傳 200KB 文字檔 | ✅ 正常 | ✅ 正常 |
| 上傳 2MB 日誌檔 | ❌ 被拒絕 | ✅ 後端摘要處理 |
| 瀏覽器負載 | 輕量 | 更輕量（只上傳） |

---

## 📅 實施計畫

### 時程估計

| 階段 | 工作項目 | 預估時間 |
|------|----------|----------|
| **Phase 1** | 前端限制 + 友善提示 | 1-2 小時 |
| **Phase 2** | 後端處理 + 智能摘要 | 4-6 小時 |
| **測試** | 功能測試 + 壓力測試 | 1-2 小時 |

### 建議實施順序

1. ✅ **Phase 1**（優先）
   - 立即防止系統當機
   - 代碼變更最小
   - 向後兼容

2. ⏳ **Phase 2**（後續）
   - 提供更好的用戶體驗
   - 支援大型日誌檔分析
   - 需要更多開發時間

---

## 🧪 測試計畫

### Phase 1 測試案例

| 測試案例 | 預期結果 |
|----------|----------|
| 上傳 100KB 文字檔 | ✅ 正常處理 |
| 上傳 400KB 文字檔 | ✅ 正常處理 |
| 上傳 600KB 文字檔 | ❌ 顯示「檔案過大」錯誤 |
| 上傳 5MB 文字檔 | ❌ 顯示「檔案過大」錯誤 |
| 上傳 5MB 圖片 | ✅ 正常處理（圖片限制較大） |

### Phase 2 測試案例

| 測試案例 | 預期結果 |
|----------|----------|
| 上傳 28.txt (5.75MB) | ✅ 後端摘要處理，返回 AI 分析 |
| 上傳 10MB 文字檔 | ❌ 顯示「檔案過大」錯誤（超過 5MB 限制） |
| 上傳空檔案 | ❌ 顯示「檔案內容為空」錯誤 |
| 併發上傳多個大檔案 | ✅ 系統穩定，逐一處理 |

---

## 📝 附錄

### A. 相關檔案路徑

```
frontend/
├── src/
│   ├── hooks/
│   │   ├── useFileUpload.js          # 檔案上傳 Hook
│   │   └── useProtocolAssistantChat.js  # Protocol 聊天 Hook
│   └── components/
│       └── chat/
│           └── CommonAssistantChatPage.jsx  # 通用聊天頁面

backend/
├── api/
│   ├── urls.py                       # API 路由
│   └── views/
│       └── dify_chat_views.py        # 聊天視圖

library/
├── common/
│   └── file_processing/              # 🆕 新增：檔案處理模組
│       ├── __init__.py
│       └── text_file_processor.py
└── protocol_guide/
    └── api_handlers.py               # Protocol API 處理器
```

### B. 問題檔案資訊

```
檔案名稱: 28.txt
檔案類型: Jenkins CI/CD 日誌
檔案大小: 5.75 MB (6,033,629 bytes)
字元數: 6,033,590
行數: 17,900
內容特徵: 時間戳記 + Pipeline 執行日誌
```

### C. 參考的限制值

| 服務 | 限制 | 說明 |
|------|------|------|
| GPT-4 | 128K tokens | ~400K 字元 |
| Claude 3 | 200K tokens | ~600K 字元 |
| Dify | 依模型 | 通常 < 100K tokens |
| Nginx | 1MB | client_max_body_size 預設值 |
| Django | 2.5MB | DATA_UPLOAD_MAX_MEMORY_SIZE 預設值 |

---

## ✅ 決策記錄

| 日期 | 決策 | 原因 |
|------|------|------|
| 2025-12-02 | 採用兩階段改善策略 | 快速解決問題 + 後續提升體驗 |
| 2025-12-02 | Phase 1 前端限制 500KB | 平衡功能與安全性 |
| 2025-12-02 | Phase 2 後端摘要 30K 字元 | 符合 LLM token 限制 |

---

**文檔結束**
