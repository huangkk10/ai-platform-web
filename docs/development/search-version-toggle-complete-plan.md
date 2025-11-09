# 🚀 搜尋版本切換完整實作計畫

**專案名稱**: V1/V2 搜尋版本切換功能  
**建立日期**: 2025-11-09  
**預計完成**: 2-3 天  
**實作範圍**: RVT Assistant, Protocol Assistant  
**設計方式**: Toggle Bar (樣式 1)

---

## 📋 目錄

- [專案概述](#專案概述)
- [Phase 0: 環境準備與檢查](#phase-0-環境準備與檢查)
- [Phase 1: 後端 API 實作](#phase-1-後端-api-實作)
- [Phase 2: 前端 Hook 實作](#phase-2-前端-hook-實作)
- [Phase 3: 前端 UI 實作](#phase-3-前端-ui-實作)
- [Phase 4: 測試與驗證](#phase-4-測試與驗證)
- [Phase 5: 部署與監控](#phase-5-部署與監控)
- [附錄](#附錄)

---

## 專案概述

### 🎯 功能目標

實作一個簡單易用的版本切換功能：
- **V1 (基礎搜尋)**: 單純的段落向量搜尋
- **V2 (上下文增強)**: 包含前後文的完整上下文搜尋

### 📐 UI 設計（最終效果）

```
┌────────────────────────────────────────────────────────────┐
│ RVT Assistant         [切換搜尋版本] V1 ⚫━━━━⚪ V2       │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  💬 輸入訊息...                                [發送]      │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 👤 User: 請說明軟體配置流程                         │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ 🤖 Assistant  [V2: 上下文增強] ⏱️ 85ms              │ │
│  │                                                      │ │
│  │ 根據文檔，軟體配置流程包含以下步驟...                │ │
│  │                                                      │ │
│  │ 📍 主要匹配段落 (相似度: 0.85)                      │ │
│  │ ├─ 3.2 軟體配置                                     │ │
│  │ └─ 內容: 配置流程說明...                            │ │
│  │                                                      │ │
│  │ ⬆️ 前置段落 (1 個)                                  │ │
│  │ └─ 3.1 硬體準備                                     │ │
│  │                                                      │ │
│  │ ⬇️ 後續段落 (1 個)                                  │ │
│  │ └─ 3.3 系統啟動                                     │ │
│  └──────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────┘
```

### 📊 實作範圍矩陣

| 項目 | 檔案 | 修改內容 | 優先級 | 預計時間 |
|------|------|---------|--------|----------|
| **後端 API** | `knowledge_viewsets.py` | 添加 version 參數支援 | 🔴 P0 | 2h |
| **RVT Hook** | `useRvtChat.js` | 版本狀態管理 | 🔴 P0 | 1h |
| **Protocol Hook** | `useProtocolAssistantChat.js` | 版本狀態管理 | 🟡 P1 | 1h |
| **Toggle 組件** | `SearchVersionToggle.jsx` | 新建切換控制 | 🔴 P0 | 2h |
| **RVT 頁面** | `RvtAssistantChatPage.js` | 整合 Toggle | 🔴 P0 | 30min |
| **Protocol 頁面** | `ProtocolAssistantChatPage.js` | 整合 Toggle | 🟡 P1 | 30min |
| **訊息顯示** | `MessageList.jsx` | 版本標記 + 上下文展示 | 🔴 P0 | 2h |
| **樣式** | `SearchVersionToggle.css` | 動畫和樣式 | 🟢 P2 | 1h |

---

## Phase 0: 環境準備與檢查

### ⏱️ 預計時間：30 分鐘

### 0.1 驗證現有功能

#### Step 0.1.1: 檢查 V1 搜尋功能

```bash
# 進入 Django 容器
docker exec -it ai-django bash

# 啟動 Django shell
python manage.py shell
```

```python
# 在 Django shell 中執行
from library.common.knowledge_base.section_search_service import SectionSearchService

search_service = SectionSearchService()

# 測試 V1 基礎搜尋
v1_results = search_service.search_sections(
    query="軟體配置",
    source_table='rvt_guide',
    limit=5,
    threshold=0.7
)

print(f"✅ V1 搜尋結果數量: {len(v1_results)}")
for i, result in enumerate(v1_results[:3], 1):
    print(f"{i}. {result.get('title', 'N/A')} (相似度: {result.get('similarity', 0):.2f})")
```

**預期輸出**:
```
✅ V1 搜尋結果數量: 3
1. 3.2 軟體配置 (相似度: 0.85)
2. 2.1 系統要求 (相似度: 0.78)
3. 4.1 配置檢查 (相似度: 0.72)
```

#### Step 0.1.2: 檢查 V2 方法是否存在

```python
# 繼續在 Django shell 中
import inspect

# 檢查是否有 search_sections_with_expanded_context 方法
has_v2_method = hasattr(search_service, 'search_sections_with_expanded_context')

if has_v2_method:
    print("✅ V2 方法已存在")
    
    # 查看方法簽名
    sig = inspect.signature(search_service.search_sections_with_expanded_context)
    print(f"方法簽名: {sig}")
    
    # 測試 V2 搜尋
    v2_results = search_service.search_sections_with_expanded_context(
        query="軟體配置",
        source_table='rvt_guide',
        limit=5,
        threshold=0.7,
        context_window=1,
        context_mode='adjacent'
    )
    print(f"✅ V2 搜尋結果數量: {len(v2_results)}")
else:
    print("❌ V2 方法尚未實作")
    print("⚠️ 需要先實作 search_sections_with_expanded_context 方法")
    print("參考文檔: /docs/development/context-window-implementation-plan.md")
```

#### Step 0.1.3: 檢查前端 API 調用

```bash
# 退出 Django shell (Ctrl+D)
exit

# 檢查前端是否有現有的搜尋 API 調用
grep -r "search_sections" frontend/src/hooks/
```

**預期輸出**:
```
frontend/src/hooks/useRvtChat.js:    const response = await api.post('/api/rvt-guides/search_sections/', {
frontend/src/hooks/useProtocolAssistantChat.js:    const response = await api.post('/api/protocol-guides/search_sections/', {
```

### 0.2 創建功能分支

```bash
# 確認當前分支
cd /home/user/codes/ai-platform-web
git branch

# 如果在 context_window 分支，拉取最新代碼
git checkout context_window
git pull origin context_window

# 創建功能分支
git checkout -b feature/search-version-toggle

# 確認分支創建成功
git branch
# 應該看到 * feature/search-version-toggle
```

### 0.3 備份現有檔案（安全措施）

```bash
# 備份即將修改的關鍵檔案
mkdir -p backups/search-toggle-$(date +%Y%m%d)

# 後端檔案
cp backend/api/views/viewsets/knowledge_viewsets.py \
   backups/search-toggle-$(date +%Y%m%d)/

# 前端檔案
cp frontend/src/hooks/useRvtChat.js \
   backups/search-toggle-$(date +%Y%m%d)/
cp frontend/src/hooks/useProtocolAssistantChat.js \
   backups/search-toggle-$(date +%Y%m%d)/
cp frontend/src/pages/RvtAssistantChatPage.js \
   backups/search-toggle-$(date +%Y%m%d)/
cp frontend/src/pages/ProtocolAssistantChatPage.js \
   backups/search-toggle-$(date +%Y%m%d)/

echo "✅ 檔案備份完成: backups/search-toggle-$(date +%Y%m%d)/"
ls -lh backups/search-toggle-$(date +%Y%m%d)/
```

### ✅ Phase 0 檢查點

完成後確認：
- [ ] V1 搜尋功能正常運作
- [ ] V2 方法狀態已確認（存在/需實作）
- [ ] 功能分支已創建 (`feature/search-version-toggle`)
- [ ] 關鍵檔案已備份
- [ ] Docker 容器運行正常
- [ ] 前端可以正常連接後端 API

---

## Phase 1: 後端 API 實作

### ⏱️ 預計時間：2-3 小時

### 1.1 修改 RVTGuideViewSet

**檔案**: `backend/api/views/viewsets/knowledge_viewsets.py`

#### Step 1.1.1: 找到 search_sections action

```bash
# 查看現有實作
grep -A 30 "def search_sections" backend/api/views/viewsets/knowledge_viewsets.py
```

#### Step 1.1.2: 添加 version 參數支援

**修改方案** (使用 `replace_string_in_file` 或手動編輯):

**原始代碼** (假設):
```python
@action(detail=False, methods=['post'])
def search_sections(self, request):
    """段落搜尋 API"""
    try:
        query = request.data.get('query', '')
        limit = request.data.get('limit', 5)
        threshold = request.data.get('threshold', 0.7)
        
        # 執行搜尋
        search_service = SectionSearchService()
        results = search_service.search_sections(
            query=query,
            source_table='rvt_guide',
            limit=limit,
            threshold=threshold
        )
        
        return Response({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)
```

**修改為**:
```python
@action(detail=False, methods=['post'])
def search_sections(self, request):
    """
    段落搜尋 API (支援 V1/V2 切換)
    
    Request Body:
    {
        "query": "搜尋查詢",
        "limit": 5,
        "threshold": 0.7,
        "version": "v1",  // 新增: 'v1' 或 'v2'，預設 'v1'
        "context_window": 1,  // V2 專用
        "context_mode": "adjacent"  // V2 專用
    }
    """
    try:
        from library.common.knowledge_base.section_search_service import SectionSearchService
        import time
        
        # 解析參數
        query = request.data.get('query', '')
        limit = request.data.get('limit', 5)
        threshold = request.data.get('threshold', 0.7)
        version = request.data.get('version', 'v1')  # ✅ 新增版本參數
        
        # V2 專用參數
        context_window = request.data.get('context_window', 1)
        context_mode = request.data.get('context_mode', 'adjacent')
        
        # 初始化服務
        search_service = SectionSearchService()
        
        # 開始計時
        start_time = time.time()
        
        # ✅ 根據版本執行不同搜尋
        if version == 'v2':
            # V2: 上下文增強搜尋
            results = search_service.search_sections_with_expanded_context(
                query=query,
                source_table='rvt_guide',
                limit=limit,
                threshold=threshold,
                context_window=context_window,
                context_mode=context_mode
            )
        else:
            # V1: 基礎搜尋 (預設)
            results = search_service.search_sections(
                query=query,
                source_table='rvt_guide',
                limit=limit,
                threshold=threshold
            )
        
        # 計算執行時間
        execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒
        
        # 返回結果
        return Response({
            'success': True,
            'version': version,  # ✅ 返回實際使用的版本
            'results': results,
            'count': len(results),
            'execution_time': f'{execution_time:.0f}ms'  # ✅ 返回執行時間
        })
        
    except Exception as e:
        logger.error(f"搜尋失敗 (version={version}): {str(e)}", exc_info=True)
        return Response({
            'error': str(e),
            'version': version
        }, status=500)
```

#### Step 1.1.3: 同樣修改 ProtocolGuideViewSet

**檔案**: `backend/api/views/viewsets/knowledge_viewsets.py`

在 `ProtocolGuideViewSet` 類別中，做完全相同的修改（只需將 `source_table='rvt_guide'` 改為 `source_table='protocol_guide'`）。

### 1.2 測試後端 API

#### Step 1.2.1: 重啟 Django 容器

```bash
# 重啟 Django 容器以載入修改
docker compose restart ai-django

# 等待 5 秒
sleep 5

# 檢查容器狀態
docker compose ps | grep django
```

#### Step 1.2.2: 使用 curl 測試 V1

```bash
# 測試 V1 搜尋 (RVT Assistant)
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "query": "軟體配置",
    "limit": 3,
    "threshold": 0.7,
    "version": "v1"
  }' | jq .
```

**預期輸出**:
```json
{
  "success": true,
  "version": "v1",
  "results": [
    {
      "id": 123,
      "title": "3.2 軟體配置",
      "content": "...",
      "similarity": 0.85
    }
  ],
  "count": 3,
  "execution_time": "45ms"
}
```

#### Step 1.2.3: 使用 curl 測試 V2

```bash
# 測試 V2 搜尋 (RVT Assistant)
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "query": "軟體配置",
    "limit": 3,
    "threshold": 0.7,
    "version": "v2",
    "context_window": 1,
    "context_mode": "adjacent"
  }' | jq .
```

**預期輸出**:
```json
{
  "success": true,
  "version": "v2",
  "results": [
    {
      "id": 123,
      "title": "3.2 軟體配置",
      "content": "...",
      "similarity": 0.85,
      "has_context": true,
      "context": {
        "before_sections": [
          {
            "id": 122,
            "title": "3.1 硬體準備",
            "content": "..."
          }
        ],
        "after_sections": [
          {
            "id": 124,
            "title": "3.3 系統啟動",
            "content": "..."
          }
        ],
        "parent_section": null,
        "child_sections": []
      }
    }
  ],
  "count": 3,
  "execution_time": "82ms"
}
```

### ✅ Phase 1 檢查點

完成後確認：
- [ ] `RVTGuideViewSet.search_sections` 已修改
- [ ] `ProtocolGuideViewSet.search_sections` 已修改
- [ ] Django 容器重啟成功
- [ ] V1 API 測試通過（回應時間 < 100ms）
- [ ] V2 API 測試通過（回應時間 < 200ms）
- [ ] V2 結果包含 `context` 欄位
- [ ] 無 500 錯誤

---

## Phase 2: 前端 Hook 實作

### ⏱️ 預計時間：2 小時

### 2.1 修改 useRvtChat Hook

**檔案**: `frontend/src/hooks/useRvtChat.js`

#### Step 2.1.1: 添加版本狀態

**在現有 state 區域添加**:
```javascript
// 現有 state
const [messages, setMessages] = useState([]);
const [inputMessage, setInputMessage] = useState('');
const [isLoading, setIsLoading] = useState(false);

// ✅ 新增：搜尋版本狀態
const [searchVersion, setSearchVersion] = useState('v1'); // 'v1' 或 'v2'
```

#### Step 2.1.2: 添加切換函數

**在現有函數後添加**:
```javascript
// ✅ 新增：切換搜尋版本
const toggleVersion = useCallback(() => {
  setSearchVersion(prev => prev === 'v1' ? 'v2' : 'v1');
}, []);
```

#### Step 2.1.3: 修改 sendMessage 函數

**找到 sendMessage 函數中的 API 調用部分**，將：
```javascript
// 原始代碼
const response = await api.post('/api/rvt-guides/chat/', {
  message: message,
  conversation_id: currentConversationId
});
```

**修改為**:
```javascript
// ✅ 修改：添加 search_version 參數
const response = await api.post('/api/rvt-guides/chat/', {
  message: message,
  conversation_id: currentConversationId,
  search_version: searchVersion,  // 傳遞版本資訊
  context_window: searchVersion === 'v2' ? 1 : undefined,  // V2 專用參數
  context_mode: searchVersion === 'v2' ? 'adjacent' : undefined  // V2 專用參數
});
```

#### Step 2.1.4: 更新 return 值

**在 Hook 的 return 語句中添加**:
```javascript
return {
  // ... 現有返回值
  messages,
  inputMessage,
  isLoading,
  sendMessage,
  
  // ✅ 新增返回值
  searchVersion,
  toggleVersion
};
```

### 2.2 修改 useProtocolAssistantChat Hook

**檔案**: `frontend/src/hooks/useProtocolAssistantChat.js`

**執行完全相同的修改** (只需將 API 端點從 `/api/rvt-guides/` 改為 `/api/protocol-guides/`)。

### 2.3 測試 Hook 修改

#### Step 2.3.1: 檢查語法錯誤

```bash
# 重啟前端容器以檢查語法錯誤
docker compose restart ai-react

# 查看日誌，確認沒有編譯錯誤
docker logs ai-react --tail 50
```

**預期輸出** (應該看到):
```
Compiled successfully!
...
webpack compiled with 0 errors
```

### ✅ Phase 2 檢查點

完成後確認：
- [ ] `useRvtChat.js` 已添加 `searchVersion` 和 `toggleVersion`
- [ ] `useProtocolAssistantChat.js` 已添加相同功能
- [ ] API 調用已包含 `search_version` 參數
- [ ] 前端容器無編譯錯誤
- [ ] Console 無錯誤訊息

---

## Phase 3: 前端 UI 實作

### ⏱️ 預計時間：3-4 小時

### 3.1 創建 SearchVersionToggle 組件

#### Step 3.1.1: 創建組件檔案

**檔案**: `frontend/src/components/SearchVersionToggle.jsx`

```javascript
import React from 'react';
import { Card, Switch, Tag, Tooltip, Space } from 'antd';
import { ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons';
import './SearchVersionToggle.css';

/**
 * 搜尋版本切換組件
 * 
 * Props:
 * - version: 'v1' | 'v2' (當前版本)
 * - onToggle: () => void (切換回調函數)
 */
const SearchVersionToggle = ({ version, onToggle }) => {
  const isV2 = version === 'v2';
  
  return (
    <div className="search-version-toggle">
      <Card 
        size="small" 
        className="toggle-card"
        bodyStyle={{ padding: '8px 16px' }}
      >
        <Space size="middle" align="center">
          {/* 標籤說明 */}
          <span className="toggle-label">切換搜尋版本:</span>
          
          {/* V1 標記 */}
          <Tooltip title="基礎搜尋 - 僅搜尋匹配段落">
            <Tag 
              icon={<ThunderboltOutlined />} 
              color={!isV2 ? 'blue' : 'default'}
              className={`version-tag ${!isV2 ? 'active' : ''}`}
            >
              V1 基礎
            </Tag>
          </Tooltip>
          
          {/* 切換開關 */}
          <Switch
            checked={isV2}
            onChange={onToggle}
            checkedChildren="V2"
            unCheckedChildren="V1"
            className="version-switch"
          />
          
          {/* V2 標記 */}
          <Tooltip title="上下文增強 - 包含前後段落和父子段落">
            <Tag 
              icon={<ExperimentOutlined />} 
              color={isV2 ? 'green' : 'default'}
              className={`version-tag ${isV2 ? 'active' : ''}`}
            >
              V2 增強
            </Tag>
          </Tooltip>
        </Space>
      </Card>
    </div>
  );
};

export default SearchVersionToggle;
```

#### Step 3.1.2: 創建樣式檔案

**檔案**: `frontend/src/components/SearchVersionToggle.css`

```css
/* 搜尋版本切換組件樣式 */
.search-version-toggle {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 100;
  animation: fadeIn 0.3s ease-in;
}

.toggle-card {
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.toggle-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.toggle-label {
  font-size: 14px;
  font-weight: 500;
  color: #595959;
}

.version-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 4px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.version-tag.active {
  transform: scale(1.05);
  font-weight: 600;
}

.version-tag:hover {
  transform: scale(1.1);
}

.version-switch {
  min-width: 50px;
}

/* 動畫效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 響應式設計 */
@media (max-width: 768px) {
  .search-version-toggle {
    top: 10px;
    right: 10px;
  }
  
  .toggle-label {
    display: none; /* 小螢幕隱藏文字 */
  }
}
```

### 3.2 修改聊天頁面

#### Step 3.2.1: RVT Assistant 頁面

**檔案**: `frontend/src/pages/RvtAssistantChatPage.js`

**在檔案開頭添加 import**:
```javascript
import SearchVersionToggle from '../components/SearchVersionToggle';
```

**在組件中整合** (找到頁面的主要容器):
```javascript
const RvtAssistantChatPage = () => {
  // ✅ 從 Hook 中取得版本相關函數
  const {
    messages,
    inputMessage,
    isLoading,
    sendMessage,
    searchVersion,      // ✅ 新增
    toggleVersion       // ✅ 新增
  } = useRvtChat();
  
  return (
    <div className="chat-container" style={{ position: 'relative' }}>
      {/* ✅ 添加 Toggle Bar */}
      <SearchVersionToggle 
        version={searchVersion} 
        onToggle={toggleVersion} 
      />
      
      {/* 原有的聊天介面組件 */}
      <MessageList messages={messages} />
      <InputArea 
        value={inputMessage} 
        onSend={sendMessage} 
        isLoading={isLoading} 
      />
    </div>
  );
};
```

#### Step 3.2.2: Protocol Assistant 頁面

**檔案**: `frontend/src/pages/ProtocolAssistantChatPage.js`

**執行完全相同的修改**。

### 3.3 修改 MessageList 組件

**檔案**: `frontend/src/components/chat/MessageList.jsx`

#### Step 3.3.1: 添加版本標記顯示

**在 assistant 訊息中添加版本標記**:

```javascript
import { Tag } from 'antd';
import { ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons';

const MessageList = ({ messages }) => {
  return (
    <div className="message-list">
      {messages.map((msg, index) => (
        <div key={index} className={`message ${msg.role}`}>
          {msg.role === 'assistant' && (
            <div className="message-header">
              <span className="message-author">🤖 Assistant</span>
              
              {/* ✅ 新增：顯示版本標記 */}
              {msg.search_version && (
                <Tag 
                  icon={msg.search_version === 'v2' ? <ExperimentOutlined /> : <ThunderboltOutlined />}
                  color={msg.search_version === 'v2' ? 'green' : 'blue'}
                  size="small"
                  style={{ marginLeft: 8 }}
                >
                  {msg.search_version === 'v2' ? 'V2: 上下文增強' : 'V1: 基礎搜尋'}
                </Tag>
              )}
              
              {/* ✅ 新增：顯示執行時間 */}
              {msg.execution_time && (
                <Tag color="orange" size="small" style={{ marginLeft: 4 }}>
                  ⏱️ {msg.execution_time}
                </Tag>
              )}
            </div>
          )}
          
          <div className="message-content">
            {msg.content}
          </div>
          
          {/* ✅ 新增：顯示上下文段落（僅 V2） */}
          {msg.role === 'assistant' && msg.search_version === 'v2' && msg.context_sections && (
            <ContextDisplay context={msg.context_sections} />
          )}
        </div>
      ))}
    </div>
  );
};
```

#### Step 3.3.2: 創建上下文展示組件

**在 MessageList.jsx 中添加**:

```javascript
import { Collapse, Card, Space } from 'antd';
import { UpOutlined, DownOutlined } from '@ant-design/icons';

const { Panel } = Collapse;

/**
 * 上下文段落展示組件（僅 V2 使用）
 */
const ContextDisplay = ({ context }) => {
  if (!context || !context.length) return null;
  
  const beforeSections = context.filter(c => c.position === 'before');
  const afterSections = context.filter(c => c.position === 'after');
  const parentSections = context.filter(c => c.position === 'parent');
  const childSections = context.filter(c => c.position === 'child');
  
  return (
    <div className="context-display" style={{ marginTop: 12 }}>
      <Collapse 
        size="small" 
        ghost
        expandIconPosition="end"
      >
        {/* 前置段落 */}
        {beforeSections.length > 0 && (
          <Panel 
            header={
              <Space>
                <UpOutlined style={{ color: '#1890ff' }} />
                <span>前置段落 ({beforeSections.length})</span>
              </Space>
            }
            key="before"
          >
            {beforeSections.map((section, idx) => (
              <Card 
                key={idx} 
                size="small" 
                title={section.title}
                style={{ marginBottom: 8 }}
              >
                {section.content.substring(0, 200)}...
              </Card>
            ))}
          </Panel>
        )}
        
        {/* 後續段落 */}
        {afterSections.length > 0 && (
          <Panel 
            header={
              <Space>
                <DownOutlined style={{ color: '#52c41a' }} />
                <span>後續段落 ({afterSections.length})</span>
              </Space>
            }
            key="after"
          >
            {afterSections.map((section, idx) => (
              <Card 
                key={idx} 
                size="small" 
                title={section.title}
                style={{ marginBottom: 8 }}
              >
                {section.content.substring(0, 200)}...
              </Card>
            ))}
          </Panel>
        )}
      </Collapse>
    </div>
  );
};
```

### ✅ Phase 3 檢查點

完成後確認：
- [ ] `SearchVersionToggle.jsx` 已創建
- [ ] `SearchVersionToggle.css` 已創建
- [ ] RVT 頁面已整合 Toggle Bar
- [ ] Protocol 頁面已整合 Toggle Bar
- [ ] `MessageList.jsx` 顯示版本標記
- [ ] V2 訊息顯示上下文段落
- [ ] 前端編譯無錯誤
- [ ] UI 顯示正常

---

## Phase 4: 測試與驗證

### ⏱️ 預計時間：2 小時

### 4.1 功能測試

#### Test 4.1.1: 版本切換測試

```markdown
測試步驟：
1. 打開 RVT Assistant 頁面
2. 確認右上角顯示 Toggle Bar
3. 預設應該是 V1（藍色 Tag 高亮）
4. 點擊 Switch 切換到 V2
5. 確認 V2 Tag 變為綠色高亮
6. 再次點擊切換回 V1
7. 確認切換流暢，無延遲

預期結果：✅ 切換正常，UI 即時更新
```

#### Test 4.1.2: V1 搜尋測試

```markdown
測試步驟：
1. 確保 Toggle 在 V1 位置
2. 輸入查詢：「軟體配置」
3. 發送訊息
4. 等待 AI 回應

預期結果：
✅ Assistant 訊息顯示 [V1: 基礎搜尋] 標記
✅ 顯示執行時間 (< 100ms)
✅ 訊息內容正確
✅ 無上下文段落顯示
```

#### Test 4.1.3: V2 搜尋測試

```markdown
測試步驟：
1. 切換 Toggle 到 V2 位置
2. 輸入查詢：「軟體配置」
3. 發送訊息
4. 等待 AI 回應

預期結果：
✅ Assistant 訊息顯示 [V2: 上下文增強] 標記
✅ 顯示執行時間 (< 200ms)
✅ 訊息內容正確
✅ 顯示「前置段落」和「後續段落」可摺疊面板
✅ 點擊面板可展開查看上下文
```

#### Test 4.1.4: 跨 Assistant 測試

```markdown
測試步驟：
1. 在 RVT Assistant 測試 V1 和 V2
2. 切換到 Protocol Assistant
3. 同樣測試 V1 和 V2
4. 返回 RVT Assistant

預期結果：
✅ 兩個 Assistant 都正常運作
✅ 版本狀態獨立（不會互相影響）
✅ 無 Console 錯誤
```

### 4.2 效能測試

#### Test 4.2.1: 回應時間測試

```bash
# 使用瀏覽器 DevTools Network 面板
# 或使用 curl 測試

# 測試 V1 (10 次)
for i in {1..10}; do
  curl -X POST http://localhost/api/rvt-guides/search_sections/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Token YOUR_TOKEN" \
    -d '{"query": "測試", "version": "v1"}' \
    -w "\n執行時間: %{time_total}s\n"
done

# 測試 V2 (10 次)
for i in {1..10}; do
  curl -X POST http://localhost/api/rvt-guides/search_sections/ \
    -H "Content-Type: application/json" \
    -H "Authorization: Token YOUR_TOKEN" \
    -d '{"query": "測試", "version": "v2", "context_window": 1}' \
    -w "\n執行時間: %{time_total}s\n"
done
```

**成功標準**：
- ✅ V1 平均回應時間 < 100ms
- ✅ V2 平均回應時間 < 200ms
- ✅ V2 / V1 比例 < 2.5

### 4.3 錯誤處理測試

#### Test 4.3.1: 無效版本參數

```bash
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"query": "測試", "version": "v999"}'
```

**預期結果**：✅ 應該 fallback 到 V1，不應該報錯

#### Test 4.3.2: V2 缺少參數

```bash
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"query": "測試", "version": "v2"}'
  # 缺少 context_window 和 context_mode
```

**預期結果**：✅ 應該使用預設值，正常返回

### ✅ Phase 4 檢查點

完成後確認：
- [ ] V1/V2 切換功能正常
- [ ] V1 搜尋結果正確
- [ ] V2 搜尋結果包含上下文
- [ ] 執行時間符合標準
- [ ] 跨 Assistant 功能正常
- [ ] 錯誤處理正確
- [ ] 無 Console 錯誤
- [ ] UI 顯示美觀

---

## Phase 5: 部署與監控

### ⏱️ 預計時間：1 小時

### 5.1 代碼提交

```bash
# 檢查修改的檔案
git status

# 添加修改的檔案
git add backend/api/views/viewsets/knowledge_viewsets.py
git add frontend/src/hooks/useRvtChat.js
git add frontend/src/hooks/useProtocolAssistantChat.js
git add frontend/src/components/SearchVersionToggle.jsx
git add frontend/src/components/SearchVersionToggle.css
git add frontend/src/pages/RvtAssistantChatPage.js
git add frontend/src/pages/ProtocolAssistantChatPage.js
git add frontend/src/components/chat/MessageList.jsx

# 提交
git commit -m "feat: 實作搜尋版本切換功能 (V1/V2 Toggle)

- 新增後端 API 版本參數支援
- 實作前端 Toggle Bar 組件
- 添加版本標記和上下文顯示
- 支援 RVT 和 Protocol Assistant

Refs: #XXX"

# 推送到遠端
git push origin feature/search-version-toggle
```

### 5.2 創建 Pull Request

```markdown
PR 標題: feat: 搜尋版本切換功能 (V1 基礎 vs V2 上下文增強)

描述:
## 功能概述
實作簡單的 V1/V2 搜尋版本切換功能，讓用戶可以自由選擇：
- V1: 基礎段落搜尋（快速，< 100ms）
- V2: 上下文增強搜尋（完整，< 200ms）

## 主要變更
- ✅ 後端 API 支援 `version` 參數
- ✅ 前端 Toggle Bar 組件
- ✅ 版本標記和執行時間顯示
- ✅ V2 上下文段落展示
- ✅ RVT + Protocol Assistant 支援

## 測試結果
- ✅ V1 平均回應時間: 45ms
- ✅ V2 平均回應時間: 82ms
- ✅ 功能測試: 全部通過
- ✅ 跨 Assistant 測試: 正常

## 截圖
[添加 Toggle Bar 和訊息顯示的截圖]

## 檢查清單
- [x] 功能測試通過
- [x] 效能測試通過
- [x] 無 Console 錯誤
- [x] UI 顯示正常
- [x] 文檔已更新
```

### 5.3 部署到生產環境

```bash
# 合併到 context_window 分支
git checkout context_window
git merge feature/search-version-toggle

# 重新建構 Docker 容器
docker compose build

# 重啟服務
docker compose down
docker compose up -d

# 檢查容器狀態
docker compose ps

# 檢查日誌
docker logs ai-django --tail 100
docker logs ai-react --tail 100
```

### 5.4 清除瀏覽器緩存

```markdown
重要：部署後請所有用戶執行以下步驟：

1. 打開瀏覽器
2. 按 Ctrl+Shift+Delete (Windows) 或 Cmd+Shift+Delete (Mac)
3. 選擇「清除快取的圖片和檔案」
4. 點擊「清除資料」
5. 重新整理頁面 (F5 或 Cmd+R)
6. 確認右上角顯示 Toggle Bar
```

### 5.5 監控指標

**第 1 週觀察事項**：
1. 📊 V1/V2 使用比例
2. ⏱️ 平均回應時間
3. 🐛 錯誤率
4. 💬 用戶反饋

**收集方式**（輕量級）：
- 觀察團隊成員使用習慣
- 詢問是否覺得 V2 更有幫助
- 記錄任何問題或建議

### ✅ Phase 5 檢查點

完成後確認：
- [ ] 代碼已提交到 feature 分支
- [ ] Pull Request 已創建
- [ ] 代碼已合併到主分支
- [ ] Docker 容器已重新建構
- [ ] 生產環境運行正常
- [ ] 團隊成員已通知清除緩存
- [ ] 開始收集使用反饋

---

## 附錄

### A. 常見問題排除

#### 問題 1: Toggle Bar 沒有顯示

**症狀**: 頁面正常但看不到 Toggle Bar

**檢查步驟**:
```bash
# 1. 檢查組件是否正確導入
grep -r "SearchVersionToggle" frontend/src/pages/

# 2. 檢查 CSS 是否載入
ls -l frontend/src/components/SearchVersionToggle.css

# 3. 檢查瀏覽器 Console
# 打開開發者工具 (F12)，查看是否有錯誤
```

**解決方案**:
- 確認 import 語句正確
- 清除瀏覽器緩存
- 檢查 CSS 檔案路徑

#### 問題 2: V2 沒有顯示上下文

**症狀**: 切換到 V2 但訊息中沒有上下文段落

**檢查步驟**:
```bash
# 1. 檢查後端是否返回 context
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"query": "測試", "version": "v2"}' | jq .

# 2. 檢查是否有 context 欄位
# 應該看到 results[].context 欄位

# 3. 檢查前端是否正確處理
grep -A 10 "context_sections" frontend/src/components/chat/MessageList.jsx
```

**解決方案**:
- 確認後端返回包含 `context` 欄位
- 檢查前端 ContextDisplay 組件是否渲染
- 查看 Console 是否有錯誤

#### 問題 3: 回應時間過長

**症狀**: V2 回應時間 > 500ms

**檢查步驟**:
```bash
# 1. 檢查資料庫查詢效能
docker exec ai-django python manage.py shell

# 在 Django shell 中
import time
from library.common.knowledge_base.section_search_service import SectionSearchService

search_service = SectionSearchService()

start = time.time()
results = search_service.search_sections_with_expanded_context(
    query="測試",
    source_table='rvt_guide',
    limit=5,
    threshold=0.7,
    context_window=1
)
print(f"執行時間: {(time.time() - start) * 1000:.0f}ms")
```

**解決方案**:
- 減少 `context_window` 參數（從 2 改為 1）
- 檢查資料庫索引
- 考慮添加快取機制

### B. 效能優化建議（可選）

#### B.1 添加快取

如果 V2 效能仍需改善，可以考慮添加簡單的快取：

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_cached_context(section_id, source_table, context_window):
    """快取上下文查詢結果"""
    # ... 查詢邏輯
    return context_sections
```

#### B.2 前端狀態持久化

如果希望用戶的版本選擇在重新整理後保留：

```javascript
// 在 useRvtChat.js 中
const [searchVersion, setSearchVersion] = useState(() => {
  return localStorage.getItem('searchVersion') || 'v1';
});

const toggleVersion = useCallback(() => {
  setSearchVersion(prev => {
    const newVersion = prev === 'v1' ? 'v2' : 'v1';
    localStorage.setItem('searchVersion', newVersion);
    return newVersion;
  });
}, []);
```

### C. 未來擴展方向

#### C.1 使用統計（1 小時實作）

如果需要收集使用數據：

```sql
-- 創建簡單的統計表
CREATE TABLE search_version_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    assistant_type VARCHAR(50),  -- 'rvt_assistant', 'protocol_assistant'
    version VARCHAR(10),  -- 'v1', 'v2'
    query TEXT,
    execution_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 查詢統計
SELECT 
    assistant_type,
    version,
    COUNT(*) as usage_count,
    AVG(execution_time_ms) as avg_time
FROM search_version_usage
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY assistant_type, version;
```

#### C.2 完整 A/B 測試

如果簡化版試用後需要更嚴謹的評估，參考：
`/docs/development/context-window-ab-testing-plan.md`

---

## 📊 實作時程總覽

| Phase | 任務 | 預計時間 | 累計時間 |
|-------|------|---------|---------|
| Phase 0 | 環境準備與檢查 | 30 分鐘 | 0.5 小時 |
| Phase 1 | 後端 API 實作 | 2-3 小時 | 3.5 小時 |
| Phase 2 | 前端 Hook 實作 | 2 小時 | 5.5 小時 |
| Phase 3 | 前端 UI 實作 | 3-4 小時 | 9.5 小時 |
| Phase 4 | 測試與驗證 | 2 小時 | 11.5 小時 |
| Phase 5 | 部署與監控 | 1 小時 | 12.5 小時 |
| **總計** | | **12-13 小時** | **約 2 天** |

---

## 🎯 成功標準總結

完成本實作計畫後，應該達成以下目標：

### 功能性
- ✅ 用戶可以輕鬆切換 V1/V2 搜尋模式
- ✅ V1 提供快速的基礎搜尋
- ✅ V2 提供包含上下文的完整搜尋
- ✅ RVT 和 Protocol Assistant 都支援

### 效能性
- ✅ V1 平均回應時間 < 100ms
- ✅ V2 平均回應時間 < 200ms
- ✅ 切換操作流暢，無延遲

### 用戶體驗
- ✅ Toggle Bar 位置明顯，易於操作
- ✅ 版本標記清晰，一目了然
- ✅ 上下文展示美觀，易於閱讀
- ✅ 無 Console 錯誤或警告

### 可維護性
- ✅ 代碼結構清晰，易於理解
- ✅ 組件可重用（RVT 和 Protocol 共用）
- ✅ 文檔完整，便於後續維護

---

## 📞 聯絡方式

如有任何問題或需要協助，請：
1. 查看本文檔的「常見問題排除」章節
2. 查看相關文檔：
   - `/docs/development/context-window-implementation-plan.md` (V2 實作細節)
   - `/docs/development/context-window-ab-testing-plan.md` (完整 A/B 測試)
3. 透過專案 issue 追蹤進度

---

**文檔版本**: v1.0  
**建立日期**: 2025-11-09  
**最後更新**: 2025-11-09  
**負責人**: AI Platform Team  
**狀態**: ✅ 準備實作
