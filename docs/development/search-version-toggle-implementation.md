# 🎯 搜尋版本切換功能實作指南

**功能**: V1/V2 搜尋版本切換（樣式 1 - 頂部 Toggle Bar）  
**實作日期**: 2025-11-09  
**預計完成**: 1-2 天  
**適用於**: RVT Assistant, Protocol Assistant

---

## 📋 目錄

1. [功能概述](#1-功能概述)
2. [後端實作](#2-後端實作)
3. [前端實作](#3-前端實作)
4. [測試指南](#4-測試指南)
5. [部署檢查清單](#5-部署檢查清單)

---

## 1. 功能概述

### 🎯 功能描述

在 RVT Assistant 和 Protocol Assistant 的聊天介面中，添加一個 **Toggle 切換開關**，讓用戶可以自由切換：
- **V1 (基礎搜尋)**: 現有的向量搜尋方法
- **V2 (上下文增強)**: 新的上下文視窗方法

### 📐 UI 設計

```
┌──────────────────────────────────────────────────────────┐
│ RVT Assistant                    🔄 [V1] ⚫ [V2]         │ ← 右上角 Toggle Bar
│                                     ↑                    │
│                             固定在頂部，z-index: 100     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  [搜尋輸入框]                                            │
│  [發送按鈕]                                              │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 👤 User: 請說明軟體配置流程                        │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │ 🤖 Assistant  [V2: 上下文增強]  ← 版本標記          │ │
│  │                                                    │ │
│  │ 📍 主要結果:                                       │ │
│  │ 段落 3.2: 軟體配置步驟...                         │ │
│  │                                                    │ │
│  │ ⬆️ 前置段落: (可展開/收起)                        │ │
│  │   段落 3.1: 準備工作...                           │ │
│  │                                                    │ │
│  │ ⬇️ 後續段落: (可展開/收起)                        │ │
│  │   段落 3.3: 驗證步驟...                           │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 🎨 Toggle Bar 樣式

```jsx
// 視覺效果
┌─────────────────────────────────────────────┐
│  🔵 V1: 基礎搜尋    [  ⚪ →  ]    ⭕ V2: 上下文增強  │
│      (當前選擇)       Toggle       (未選擇)  │
└─────────────────────────────────────────────┘

// 切換後
┌─────────────────────────────────────────────┐
│  ⭕ V1: 基礎搜尋    [  ⚫ ←  ]    🟢 V2: 上下文增強  │
│      (未選擇)       Toggle        (當前選擇) │
└─────────────────────────────────────────────┘
```

---

## 2. 後端實作

### 📂 檔案位置

```
backend/api/views/viewsets/knowledge_viewsets.py
library/common/knowledge_base/section_search_service.py
```

### 2.1 修改 API 端點

#### 選項 A：修改現有 API（推薦）

```python
# backend/api/views/viewsets/knowledge_viewsets.py

class RVTGuideViewSet(LibraryManagerMixin, FallbackLogicMixin, 
                      VectorManagementMixin, viewsets.ModelViewSet):
    """RVT Assistant 知識庫 ViewSet"""
    
    @action(detail=False, methods=['post'])
    def search_sections(self, request):
        """
        段落搜尋 API（支援 V1/V2 切換）
        
        POST /api/rvt-guides/search_sections/
        
        Request Body:
        {
            "query": "軟體配置",
            "limit": 5,
            "threshold": 0.7,
            "version": "v1",           // ✅ 新增：'v1' 或 'v2' (預設 'v1')
            "context_window": 2,       // V2 專用參數
            "context_mode": "both"     // V2 專用參數: 'adjacent', 'parent_child', 'both'
        }
        
        Response:
        {
            "success": true,
            "version": "v1",           // 實際使用的版本
            "results": [...],          // 搜尋結果
            "execution_time": "45ms"   // 執行時間（用於效能比較）
        }
        """
        try:
            # 1. 解析參數
            query = request.data.get('query', '')
            version = request.data.get('version', 'v1')  # ✅ 預設 V1
            limit = request.data.get('limit', 5)
            threshold = request.data.get('threshold', 0.7)
            
            if not query:
                return Response({
                    'success': False,
                    'error': '查詢內容不能為空'
                }, status=400)
            
            # 2. 導入搜尋服務
            from library.common.knowledge_base.section_search_service import SectionSearchService
            search_service = SectionSearchService()
            
            # 3. 記錄開始時間（用於效能測量）
            import time
            start_time = time.time()
            
            # 4. 根據版本執行搜尋
            if version == 'v2':
                # V2: 上下文增強搜尋
                context_window = request.data.get('context_window', 1)
                context_mode = request.data.get('context_mode', 'adjacent')
                
                results = search_service.search_sections_with_expanded_context(
                    query=query,
                    source_table='rvt_guide',
                    limit=limit,
                    threshold=threshold,
                    context_window=context_window,
                    context_mode=context_mode
                )
            else:
                # V1: 基礎搜尋（現有方法）
                results = search_service.search_sections(
                    query=query,
                    source_table='rvt_guide',
                    limit=limit,
                    threshold=threshold
                )
            
            # 5. 計算執行時間
            execution_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            # 6. 返回結果
            return Response({
                'success': True,
                'version': version,
                'results': results,
                'execution_time': f'{execution_time:.0f}ms'
            })
            
        except Exception as e:
            logger.error(f"段落搜尋失敗: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': str(e)
            }, status=500)
```

#### 選項 B：創建新 API 端點（備選）

如果不想修改現有 API，可以創建新端點：

```python
@action(detail=False, methods=['post'])
def search_sections_v2(self, request):
    """V2: 上下文增強搜尋 API"""
    # ... V2 專用實作
```

### 2.2 Protocol Assistant 同步修改

```python
# backend/api/views/viewsets/knowledge_viewsets.py

class ProtocolGuideViewSet(LibraryManagerMixin, FallbackLogicMixin,
                           VectorManagementMixin, viewsets.ModelViewSet):
    """Protocol Assistant 知識庫 ViewSet"""
    
    @action(detail=False, methods=['post'])
    def search_sections(self, request):
        """
        段落搜尋 API（支援 V1/V2 切換）
        
        ⚠️ 實作與 RVTGuideViewSet 相同，只需修改 source_table
        """
        # ... 複製上面的實作
        # 唯一差異：source_table='protocol_guide'
```

---

## 3. 前端實作

### 📂 檔案結構

```
frontend/src/
├── hooks/
│   ├── useRvtChat.js              ← 修改：添加版本狀態
│   └── useProtocolAssistantChat.js ← 修改：添加版本狀態
├── pages/
│   ├── RvtAssistantChatPage.js    ← 修改：添加 Toggle Bar
│   └── ProtocolAssistantChatPage.js ← 修改：添加 Toggle Bar
└── components/
    └── SearchVersionToggle.jsx     ← 新增：Toggle Bar 組件
```

### 3.1 創建 Toggle 組件

```jsx
// frontend/src/components/SearchVersionToggle.jsx

import React from 'react';
import { Switch, Space, Tag, Tooltip, Card } from 'antd';
import { ThunderboltOutlined, ExperimentOutlined } from '@ant-design/icons';
import './SearchVersionToggle.css';

const SearchVersionToggle = ({ version, onToggle }) => {
  return (
    <Card
      className="search-version-toggle"
      size="small"
      style={{
        position: 'absolute',
        top: 20,
        right: 20,
        zIndex: 100,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
        borderRadius: 8,
        minWidth: 300
      }}
    >
      <Space size="middle" align="center">
        {/* V1 標籤 */}
        <Tooltip title="基礎向量搜尋，快速回應">
          <Tag 
            color={version === 'v1' ? 'blue' : 'default'}
            style={{ 
              fontSize: 13, 
              padding: '4px 12px',
              cursor: 'pointer'
            }}
            onClick={() => version !== 'v1' && onToggle()}
          >
            <ThunderboltOutlined /> V1: 基礎搜尋
          </Tag>
        </Tooltip>
        
        {/* Toggle Switch */}
        <Tooltip 
          title={
            version === 'v1' 
              ? '切換到 V2：自動提供上下文段落' 
              : '切換到 V1：僅顯示匹配結果'
          }
        >
          <Switch
            checked={version === 'v2'}
            onChange={onToggle}
            checkedChildren={<ExperimentOutlined />}
            unCheckedChildren={<ThunderboltOutlined />}
            style={{ minWidth: 50 }}
          />
        </Tooltip>
        
        {/* V2 標籤 */}
        <Tooltip title="包含前後段落和父子段落，理解更完整">
          <Tag 
            color={version === 'v2' ? 'green' : 'default'}
            style={{ 
              fontSize: 13, 
              padding: '4px 12px',
              cursor: 'pointer'
            }}
            onClick={() => version !== 'v2' && onToggle()}
          >
            <ExperimentOutlined /> V2: 上下文增強
          </Tag>
        </Tooltip>
      </Space>
    </Card>
  );
};

export default SearchVersionToggle;
```

```css
/* frontend/src/components/SearchVersionToggle.css */

.search-version-toggle {
  animation: fadeIn 0.3s ease-in;
}

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

.search-version-toggle .ant-card-body {
  padding: 12px 16px;
}

.search-version-toggle .ant-tag {
  margin: 0;
  transition: all 0.3s ease;
}

.search-version-toggle .ant-tag:hover {
  transform: scale(1.05);
}

.search-version-toggle .ant-switch {
  transition: all 0.3s ease;
}
```

### 3.2 修改 Hook：`useRvtChat.js`

```javascript
// frontend/src/hooks/useRvtChat.js

import { useState, useCallback } from 'react';
import api from '../services/api';

const useRvtChat = () => {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  
  // ✅ 新增：版本狀態（預設 V1）
  const [searchVersion, setSearchVersion] = useState('v1');

  const sendMessage = async (message) => {
    if (!message.trim() || isLoading) return;

    const userMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setIsLoading(true);
    setError(null);

    try {
      // ✅ 發送請求時帶上版本參數
      const response = await api.post('/api/rvt-guides/search_sections/', {
        query: message,
        limit: 5,
        threshold: 0.7,
        version: searchVersion,  // ✅ 使用當前版本
        context_window: 2,        // V2 參數
        context_mode: 'both'      // V2 參數
      });

      const data = response.data;

      const assistantMessage = {
        role: 'assistant',
        content: data.results,
        version: data.version,        // ✅ 記錄實際使用的版本
        executionTime: data.execution_time,  // ✅ 記錄執行時間
        timestamp: new Date().toISOString()
      };

      setMessages(prev => [...prev, assistantMessage]);

    } catch (error) {
      console.error('搜尋失敗:', error);
      setError('搜尋失敗，請稍後再試');
      
      // 添加錯誤訊息
      const errorMessage = {
        role: 'assistant',
        content: '抱歉，搜尋時發生錯誤，請稍後再試。',
        error: true,
        timestamp: new Date().toISOString()
      };
      setMessages(prev => [...prev, errorMessage]);
      
    } finally {
      setIsLoading(false);
    }
  };

  // ✅ 新增：切換版本的函數
  const toggleVersion = useCallback(() => {
    setSearchVersion(prev => {
      const newVersion = prev === 'v1' ? 'v2' : 'v1';
      console.log(`搜尋版本已切換: ${prev} → ${newVersion}`);
      return newVersion;
    });
  }, []);

  // ✅ 新增：清除對話
  const clearMessages = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    searchVersion,      // ✅ 導出當前版本
    toggleVersion,      // ✅ 導出切換函數
    clearMessages
  };
};

export default useRvtChat;
```

### 3.3 修改聊天頁面：`RvtAssistantChatPage.js`

```javascript
// frontend/src/pages/RvtAssistantChatPage.js

import React from 'react';
import { Layout, Typography } from 'antd';
import useRvtChat from '../hooks/useRvtChat';
import SearchVersionToggle from '../components/SearchVersionToggle';
import MessageList from '../components/chat/MessageList';
import InputBox from '../components/chat/InputBox';
import './RvtAssistantChatPage.css';

const { Content } = Layout;
const { Title } = Typography;

const RvtAssistantChatPage = () => {
  const { 
    messages, 
    isLoading, 
    sendMessage, 
    searchVersion,     // ✅ 獲取當前版本
    toggleVersion      // ✅ 獲取切換函數
  } = useRvtChat();

  return (
    <Layout className="rvt-chat-page" style={{ height: '100vh', position: 'relative' }}>
      {/* ✅ Toggle Bar 組件（固定在右上角） */}
      <SearchVersionToggle 
        version={searchVersion}
        onToggle={toggleVersion}
      />

      <Content style={{ padding: '24px', paddingTop: '80px' }}>
        <div className="chat-container" style={{ 
          maxWidth: 1200, 
          margin: '0 auto',
          height: 'calc(100vh - 120px)',
          display: 'flex',
          flexDirection: 'column'
        }}>
          <Title level={3} style={{ marginBottom: 24 }}>
            RVT Assistant
          </Title>

          {/* 訊息列表 */}
          <MessageList 
            messages={messages} 
            isLoading={isLoading}
            searchVersion={searchVersion}  // ✅ 傳遞版本資訊
          />

          {/* 輸入框 */}
          <InputBox 
            onSend={sendMessage}
            isLoading={isLoading}
            placeholder="請輸入您的問題..."
          />
        </div>
      </Content>
    </Layout>
  );
};

export default RvtAssistantChatPage;
```

### 3.4 修改訊息列表：顯示版本標記

```javascript
// frontend/src/components/chat/MessageList.jsx

import React from 'react';
import { Card, Tag, Typography, Collapse, Space } from 'antd';
import { ThunderboltOutlined, ExperimentOutlined, ClockCircleOutlined } from '@ant-design/icons';

const { Text } = Typography;
const { Panel } = Collapse;

const MessageList = ({ messages, isLoading, searchVersion }) => {
  return (
    <div className="message-list" style={{ 
      flex: 1, 
      overflowY: 'auto', 
      marginBottom: 16 
    }}>
      {messages.map((msg, idx) => (
        <Card 
          key={idx}
          className={`message-card ${msg.role}`}
          style={{ marginBottom: 16 }}
        >
          {/* 訊息頭部：顯示版本標記和執行時間 */}
          {msg.role === 'assistant' && !msg.error && (
            <div style={{ marginBottom: 12 }}>
              <Space>
                {/* ✅ 版本標記 */}
                <Tag 
                  color={msg.version === 'v2' ? 'green' : 'blue'}
                  icon={msg.version === 'v2' ? <ExperimentOutlined /> : <ThunderboltOutlined />}
                >
                  {msg.version === 'v2' ? 'V2: 上下文增強' : 'V1: 基礎搜尋'}
                </Tag>
                
                {/* ✅ 執行時間 */}
                {msg.executionTime && (
                  <Tag icon={<ClockCircleOutlined />}>
                    {msg.executionTime}
                  </Tag>
                )}
              </Space>
            </div>
          )}

          {/* 訊息內容 */}
          {msg.role === 'user' ? (
            <div>
              <Text strong>您：</Text>
              <div style={{ marginTop: 8 }}>{msg.content}</div>
            </div>
          ) : (
            <div>
              <Text strong>🤖 RVT Assistant：</Text>
              
              {/* V2 訊息：顯示上下文 */}
              {msg.version === 'v2' && msg.content?.context ? (
                <div style={{ marginTop: 12 }}>
                  {/* 主要結果 */}
                  <div>
                    <Text type="success">📍 主要結果：</Text>
                    <div style={{ marginTop: 8 }}>
                      {/* 渲染主要搜尋結果 */}
                      {msg.content.main_results?.map((result, i) => (
                        <div key={i} style={{ marginBottom: 16 }}>
                          <Text strong>{result.title}</Text>
                          <div>{result.content}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 上下文段落（可摺疊） */}
                  <Collapse 
                    ghost 
                    style={{ marginTop: 16 }}
                    defaultActiveKey={['before', 'after']}
                  >
                    {/* 前置段落 */}
                    {msg.content.context.before?.length > 0 && (
                      <Panel 
                        header={`⬆️ 前置段落 (${msg.content.context.before.length})`}
                        key="before"
                      >
                        {msg.content.context.before.map((item, i) => (
                          <div key={i} style={{ marginBottom: 12, paddingLeft: 12, borderLeft: '3px solid #1890ff' }}>
                            <Text type="secondary">{item.section_id}</Text>
                            <div>{item.content}</div>
                          </div>
                        ))}
                      </Panel>
                    )}

                    {/* 後續段落 */}
                    {msg.content.context.after?.length > 0 && (
                      <Panel 
                        header={`⬇️ 後續段落 (${msg.content.context.after.length})`}
                        key="after"
                      >
                        {msg.content.context.after.map((item, i) => (
                          <div key={i} style={{ marginBottom: 12, paddingLeft: 12, borderLeft: '3px solid #52c41a' }}>
                            <Text type="secondary">{item.section_id}</Text>
                            <div>{item.content}</div>
                          </div>
                        ))}
                      </Panel>
                    )}
                  </Collapse>
                </div>
              ) : (
                /* V1 訊息：簡單列表 */
                <div style={{ marginTop: 8 }}>
                  {msg.content?.map((result, i) => (
                    <div key={i} style={{ marginBottom: 16 }}>
                      <Text strong>{result.title}</Text>
                      <div>{result.content}</div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </Card>
      ))}

      {/* Loading 指示器 */}
      {isLoading && (
        <Card className="message-card assistant loading">
          <Text type="secondary">正在搜尋...</Text>
        </Card>
      )}
    </div>
  );
};

export default MessageList;
```

### 3.5 Protocol Assistant 同步修改

```javascript
// frontend/src/hooks/useProtocolAssistantChat.js
// ✅ 複製 useRvtChat.js 的完整實作，只需修改 API 端點

// frontend/src/pages/ProtocolAssistantChatPage.js
// ✅ 複製 RvtAssistantChatPage.js 的完整實作
```

---

## 4. 測試指南

### 4.1 功能測試

#### 測試 1：版本切換

```
步驟：
1. 開啟 RVT Assistant 聊天頁面
2. 確認右上角顯示 Toggle Bar
3. 預設應為 V1（藍色標記）
4. 點擊 Switch 切換到 V2
5. 確認切換成功（綠色標記）
6. 再次切換回 V1

預期結果：
✅ Toggle Bar 正常顯示
✅ 版本切換流暢無延遲
✅ 標籤顏色正確變化
```

#### 測試 2：V1 搜尋

```
步驟：
1. 確保選擇 V1
2. 輸入："請說明軟體配置流程"
3. 發送訊息
4. 觀察回應

預期結果：
✅ 顯示 "V1: 基礎搜尋" 標籤
✅ 僅顯示匹配的段落
✅ 無上下文展開面板
✅ 執行時間 < 100ms
```

#### 測試 3：V2 搜尋

```
步驟：
1. 切換到 V2
2. 輸入："請說明軟體配置流程"
3. 發送訊息
4. 觀察回應

預期結果：
✅ 顯示 "V2: 上下文增強" 標籤
✅ 顯示主要結果
✅ 顯示 "⬆️ 前置段落" 摺疊面板
✅ 顯示 "⬇️ 後續段落" 摺疊面板
✅ 執行時間 < 200ms
```

#### 測試 4：切換後搜尋

```
步驟：
1. 在 V1 模式搜尋一次
2. 切換到 V2
3. 搜尋相同問題
4. 比較結果差異

預期結果：
✅ 兩次搜尋的主要結果相同（相同的相似度排序）
✅ V2 多了上下文段落
✅ 兩個版本的回應獨立顯示
```

### 4.2 跨 Assistant 測試

```
測試清單：
□ RVT Assistant - V1 搜尋
□ RVT Assistant - V2 搜尋
□ Protocol Assistant - V1 搜尋
□ Protocol Assistant - V2 搜尋
□ 切換版本後刷新頁面（狀態是否保留）
```

### 4.3 錯誤處理測試

```
測試場景：
1. 空查詢 → 應顯示錯誤提示
2. API 失敗 → 應顯示友善錯誤訊息
3. 網路中斷 → 應提示重試
4. V2 搜尋無上下文 → 應正常顯示主要結果
```

### 4.4 效能測試

```sql
-- 查詢 V1 vs V2 的平均執行時間
SELECT 
    version,
    AVG(execution_time) as avg_time,
    COUNT(*) as search_count
FROM (
    -- 模擬記錄（如果有統計表）
    SELECT 'v1' as version, 45 as execution_time
    UNION ALL
    SELECT 'v2' as version, 85 as execution_time
) t
GROUP BY version;
```

---

## 5. 部署檢查清單

### 5.1 後端部署

```bash
# 1. 確認 Django 容器運行
docker compose ps | grep django

# 2. 測試 API 端點
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "測試",
    "version": "v1"
  }'

# 3. 測試 V2 端點
curl -X POST http://localhost/api/rvt-guides/search_sections/ \
  -H "Content-Type: application/json" \
  -d '{
    "query": "測試",
    "version": "v2",
    "context_window": 2,
    "context_mode": "both"
  }'

# 4. 檢查日誌
docker logs ai-django --tail 50
```

### 5.2 前端部署

```bash
# 1. 重新建構前端
cd frontend
npm run build

# 2. 重啟容器
docker compose restart ai-react

# 3. 清除瀏覽器快取
# Chrome: Ctrl+Shift+Delete

# 4. 測試訪問
# http://localhost:3000/rvt-assistant/chat
```

### 5.3 最終檢查

```
部署檢查清單：
□ 後端 API 正常回應
□ V1 和 V2 都能正常搜尋
□ Toggle Bar 顯示正常
□ 版本切換無延遲
□ RVT Assistant 功能正常
□ Protocol Assistant 功能正常
□ 無 Console 錯誤
□ 無 API 錯誤
□ 效能符合預期（V1 < 100ms, V2 < 200ms）
```

---

## 📊 使用統計（可選）

### 簡單統計表（1 小時實作）

```sql
-- backend/api/models.py

CREATE TABLE search_version_usage (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES auth_user(id),
    assistant_type VARCHAR(50),  -- 'rvt_assistant', 'protocol_assistant'
    version VARCHAR(10),          -- 'v1', 'v2'
    query TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_version_usage_user (user_id),
    INDEX idx_version_usage_version (version, created_at)
);

-- 查詢統計
SELECT 
    version,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as unique_users,
    DATE(created_at) as date
FROM search_version_usage
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY version, DATE(created_at)
ORDER BY date DESC, version;
```

---

## 🎯 成功標準

### 功能完整性
- ✅ Toggle Bar 正常顯示和切換
- ✅ V1 和 V2 搜尋都正常工作
- ✅ 版本標記正確顯示
- ✅ V2 上下文正確展示

### 效能要求
- ✅ V1 搜尋：< 100ms
- ✅ V2 搜尋：< 200ms
- ✅ 版本切換：< 50ms
- ✅ 無記憶體洩漏

### 用戶體驗
- ✅ UI 美觀，符合 Ant Design 規範
- ✅ 切換流暢無卡頓
- ✅ 錯誤提示友善
- ✅ 響應式設計（支援手機）

---

## 📚 相關文檔

- **實作計畫**: `/docs/development/context-window-implementation-plan.md`
- **A/B 測試方案**: `/docs/development/context-window-ab-testing-plan.md`
- **向量搜尋指南**: `/docs/vector-search/vector-search-guide.md`

---

**文檔版本**: v1.0  
**創建日期**: 2025-11-09  
**預計完成**: 1-2 天  
**適用 Assistant**: RVT Assistant, Protocol Assistant

**下一步**：開始實作 → 測試 → 部署 → 收集反饋
