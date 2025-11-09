# 🎯 搜尋版本切換功能實作報告

## 📋 概述

本報告記錄了在 RVT Assistant 中實現 V1/V2 搜尋版本切換功能的完整過程。

**實作日期**: 2025-11-09  
**功能版本**: v1.0  
**影響範圍**: RVT Assistant, Protocol Assistant (未來可擴展)

---

## 🎯 功能目標

### 主要目標
1. ✅ 讓用戶可以在聊天介面中切換搜尋版本（V1 或 V2）
2. ✅ V1: 基礎搜尋（快速搜尋，僅返回最相關段落）
3. ✅ V2: 上下文增強搜尋（包含前後段落和父子段落）
4. ✅ 提供直觀的 UI 切換開關
5. ✅ 記住用戶的版本選擇（localStorage 持久化）

### 預期效果
- 用戶可以根據需求選擇不同的搜尋策略
- V1 適合快速查找特定資訊
- V2 適合需要深入理解的場景

---

## 🏗️ 架構設計

### 技術架構

```
前端 UI (SearchVersionToggle)
       ↓
前端 Hook (useRvtChat + searchVersion state)
       ↓
後端 API (/api/rvt-guide/chat/)
       ↓
ViewSet (search_sections action + version parameter)
       ↓
搜尋服務 (SectionSearchService)
       ↓
     V1              V2
     ↓               ↓
search_sections()  search_sections_with_expanded_context()
```

### 資料流

```
用戶點擊切換 → setSearchVersion('v2') → localStorage 存儲
                    ↓
發送訊息 → sendMessage({ message, search_version: 'v2' })
                    ↓
後端接收 → request.data.get('version', 'v1')
                    ↓
根據版本選擇搜尋方法 → 返回結果
```

---

## 💻 實作細節

### 1. 後端 API 修改

#### 檔案：`backend/api/views/viewsets/knowledge_viewsets.py`

**修改位置**：`search_sections` action（約第 551 行）

**主要修改**：

```python
# ✅ 新增版本參數
version = request.data.get('version', 'v1')
context_window = request.data.get('context_window', 1)
context_mode = request.data.get('context_mode', 'adjacent')

# ✅ 根據版本執行不同搜尋
if version == 'v2':
    # V2: 上下文增強搜尋
    raw_results = search_service.search_sections_with_expanded_context(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        min_level=min_level,
        max_level=max_level,
        context_window=context_window,
        context_mode=context_mode
    )
else:
    # V1: 基礎搜尋（預設）
    raw_results = search_service.search_sections(
        query=query,
        source_table='rvt_guide',
        limit=limit,
        threshold=threshold,
        min_level=min_level,
        max_level=max_level
    )
```

**新增返回欄位**：

```python
return Response({
    'success': True,
    'version': version,           # ✅ 返回實際使用的版本
    'results': results,
    'total': len(results),
    'query': query,
    'search_type': 'section',
    'execution_time': f'{execution_time:.0f}ms'  # ✅ 返回執行時間
})
```

**API 參數說明**：

| 參數 | 類型 | 預設值 | 說明 |
|------|------|--------|------|
| `query` | string | (必填) | 搜尋查詢 |
| `limit` | int | 5 | 結果數量 |
| `threshold` | float | 0.7 | 相似度閾值 |
| `version` | string | 'v1' | ✅ 搜尋版本 ('v1' 或 'v2') |
| `context_window` | int | 1 | ✅ V2 專用：上下文視窗大小 |
| `context_mode` | string | 'adjacent' | ✅ V2 專用：上下文模式 |

---

### 2. 前端 Hook 修改

#### 檔案：`frontend/src/hooks/useRvtChat.js`

**主要修改**：

1. **新增搜尋版本 State**：

```javascript
// ✅ 新增：搜尋版本狀態（預設 V1）
const [searchVersion, setSearchVersion] = useState(() => {
  // 從 localStorage 載入設定，預設為 'v1'
  return localStorage.getItem('rvt_search_version') || 'v1';
});
```

2. **localStorage 持久化**：

```javascript
// ✅ 新增：同步搜尋版本到 localStorage
useEffect(() => {
  localStorage.setItem('rvt_search_version', searchVersion);
}, [searchVersion]);
```

3. **發送請求時傳遞版本參數**：

```javascript
body: JSON.stringify({
  message: userMessage.content,
  conversation_id: conversationId || '',
  search_version: searchVersion  // ✅ 新增：傳送搜尋版本參數
})
```

4. **導出版本狀態**：

```javascript
return {
  sendMessage,
  loading,
  loadingStartTime,
  stopRequest,
  searchVersion,      // ✅ 新增：導出搜尋版本
  setSearchVersion    // ✅ 新增：導出版本切換函數
};
```

---

### 3. UI 組件實作

#### 檔案：`frontend/src/components/chat/SearchVersionToggle.jsx`（新建）

**組件設計**：

```
┌──────────────────────────────────────────┐
│ 🚀 V1 ⚪──○ V2 🧪 ⓘ                      │
└──────────────────────────────────────────┘
```

**功能特點**：

1. **視覺設計**：
   - V1 藍色（🚀 RocketOutlined）
   - V2 綠色（🧪 ExperimentOutlined）
   - 動態切換顏色和字體粗細

2. **互動功能**：
   - Switch 開關（Ant Design）
   - Tooltip 提示（說明各版本特性）
   - 載入時禁用切換

3. **樣式特性**：
   ```javascript
   style={{ 
     display: 'flex', 
     alignItems: 'center', 
     gap: '8px',
     padding: '8px 12px',
     background: '#f5f5f5',
     borderRadius: '8px'
   }}
   ```

**Tooltip 內容**：

- **V1 - 基礎搜尋**
  - 快速搜尋，僅返回最相關的段落
  - 適合快速查找特定資訊

- **V2 - 上下文增強搜尋**
  - 包含前後段落和父子段落
  - 提供更完整的上下文資訊
  - 適合需要深入理解的場景

---

### 4. CommonAssistantChatPage 整合

#### 檔案：`frontend/src/components/chat/CommonAssistantChatPage.jsx`

**主要修改**：

1. **導入組件**：

```javascript
import SearchVersionToggle from './SearchVersionToggle';  // ✅ 新增
```

2. **解構 Hook 返回值**：

```javascript
const chatHookReturn = useChatHook(...);

const { 
  sendMessage, 
  loading, 
  loadingStartTime, 
  stopRequest,
  searchVersion,      // ✅ 可能為 undefined（向後兼容）
  setSearchVersion    // ✅ 可能為 undefined（向後兼容）
} = chatHookReturn;
```

3. **條件渲染切換組件**：

```javascript
{/* ✅ 新增：搜尋版本切換組件（僅當 Hook 支援時顯示） */}
{searchVersion !== undefined && setSearchVersion && (
  <div style={{ 
    display: 'flex', 
    justifyContent: 'flex-end', 
    marginBottom: '12px',
    maxWidth: '800px',
    margin: '0 auto 12px auto'
  }}>
    <SearchVersionToggle
      searchVersion={searchVersion}
      onVersionChange={setSearchVersion}
      disabled={loading}
    />
  </div>
)}
```

**向後兼容設計**：
- 只有當 Hook 返回 `searchVersion` 和 `setSearchVersion` 時才顯示切換組件
- 未實作搜尋版本的 Assistant 不會顯示切換開關
- 不影響現有功能

---

## 🧪 測試指南

### 手動測試步驟

#### 1. **基本功能測試**

1. 訪問 RVT Assistant 聊天頁面：`http://localhost/rvt-chat`
2. 檢查輸入框上方是否顯示版本切換組件
3. 預設應該是 V1（藍色高亮）

#### 2. **V1 搜尋測試**

1. 確保切換開關在 V1 位置
2. 發送測試訊息：「如何進行 RVT 測試？」
3. 檢查回應是否正常
4. 檢查瀏覽器 Network 面板：
   - 請求 URL：`/api/rvt-guide/chat/`
   - 請求 Body：應該包含 `"search_version": "v1"`

#### 3. **V2 搜尋測試**

1. 點擊切換開關切換到 V2（綠色高亮）
2. 發送相同測試訊息：「如何進行 RVT 測試？」
3. 檢查回應是否正常
4. 檢查瀏覽器 Network 面板：
   - 請求 URL：`/api/rvt-guide/chat/`
   - 請求 Body：應該包含 `"search_version": "v2"`
5. 比較 V1 和 V2 的回應差異（V2 應包含更多上下文）

#### 4. **持久化測試**

1. 切換到 V2
2. 刷新頁面（F5）
3. 檢查切換開關是否仍在 V2 位置
4. 檢查 localStorage：
   ```javascript
   localStorage.getItem('rvt_search_version')  // 應該是 'v2'
   ```

#### 5. **UI 互動測試**

1. 測試 Tooltip：
   - 滑鼠移到 V1 圖標：應顯示基礎搜尋說明
   - 滑鼠移到 V2 圖標：應顯示上下文增強搜尋說明
   - 滑鼠移到 ⓘ：應顯示完整版本說明

2. 測試禁用狀態：
   - 發送訊息（loading = true）
   - 檢查切換開關是否被禁用

#### 6. **對比測試**

發送相同查詢並對比 V1 vs V2 結果：

| 測試場景 | V1 預期結果 | V2 預期結果 |
|---------|-----------|-----------|
| 簡單問題 | 快速返回核心答案 | 提供額外的上下文說明 |
| 複雜問題 | 可能缺少背景資訊 | 包含相關段落的前後文 |
| 執行時間 | 較快（< 2秒） | 稍慢（< 3秒） |

---

### API 測試（使用 curl）

#### 測試 V1 搜尋

```bash
curl -X POST "http://localhost/api/rvt-guides/search_sections/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何進行 RVT 測試",
    "version": "v1",
    "limit": 3
  }'
```

**預期回應**：

```json
{
  "success": true,
  "version": "v1",
  "results": [
    {
      "section_id": 123,
      "section_title": "RVT 測試流程",
      "content": "...",
      "similarity": 0.85
    }
  ],
  "total": 3,
  "execution_time": "1500ms"
}
```

#### 測試 V2 搜尋

```bash
curl -X POST "http://localhost/api/rvt-guides/search_sections/" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "如何進行 RVT 測試",
    "version": "v2",
    "limit": 3,
    "context_window": 1,
    "context_mode": "adjacent"
  }'
```

**預期回應**：

```json
{
  "success": true,
  "version": "v2",
  "results": [
    {
      "section_id": 123,
      "section_title": "RVT 測試流程",
      "content": "...",
      "similarity": 0.85,
      "has_context": true,
      "context": {
        "previous": "...",
        "next": "...",
        "parent": "..."
      }
    }
  ],
  "total": 3,
  "execution_time": "2200ms"
}
```

---

## 📊 效能對比

### 預期效能指標

| 指標 | V1 基礎搜尋 | V2 上下文搜尋 | 說明 |
|------|-----------|-------------|------|
| 平均回應時間 | 1.5-2.0 秒 | 2.0-3.0 秒 | V2 需要額外查詢上下文 |
| 記憶體使用 | ~50MB | ~80MB | V2 需要載入更多資料 |
| 資料庫查詢 | 1-2 次 | 3-5 次 | V2 需要查詢相鄰和父子段落 |
| 結果完整性 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | V2 提供更完整的上下文 |
| 適用場景 | 快速查找 | 深入理解 | 根據需求選擇 |

### 效能優化建議

1. **V2 查詢優化**：
   - 考慮快取常見查詢的上下文
   - 使用資料庫索引優化相鄰段落查詢

2. **前端優化**：
   - 使用 React.memo 優化 SearchVersionToggle 組件
   - 防抖（debounce）切換操作

3. **監控指標**：
   - 記錄 V1 vs V2 的使用比例
   - 追蹤平均回應時間差異
   - 監控錯誤率

---

## 🔄 向後兼容性

### 設計原則

1. **預設 V1**：所有現有功能預設使用 V1 搜尋
2. **條件渲染**：只有支援搜尋版本的 Hook 才顯示切換組件
3. **API 兼容**：後端 API 預設參數為 'v1'，不影響舊客戶端
4. **localStorage**：使用獨立的 key (`rvt_search_version`)，不影響其他存儲

### 影響範圍

- ✅ **RVT Assistant**：完全支援（已實作）
- 🔜 **Protocol Assistant**：可擴展（需複製相同模式）
- ❌ **其他 Assistant**：不受影響（使用預設 V1）

---

## 🚀 未來擴展

### 短期計劃（1-2 週）

1. **Protocol Assistant 支援**：
   - 複製 `useRvtChat.js` 的模式到 `useProtocolAssistantChat.js`
   - 修改 Protocol Guide ViewSet 的 `search_sections` action
   - 測試和驗證

2. **使用統計**：
   - 記錄 V1 vs V2 的使用頻率
   - 追蹤用戶偏好
   - 分析效能差異

### 中期計劃（1 個月）

1. **高級配置**：
   - 允許用戶自訂 `context_window` 大小
   - 提供 `context_mode` 選項（adjacent, hierarchical, both）
   - UI 高級設定面板

2. **效能優化**：
   - 實作 V2 查詢快取
   - 優化資料庫索引
   - 減少不必要的查詢

### 長期計劃（3 個月）

1. **A/B 測試**：
   - 隨機分配用戶到 V1/V2
   - 收集滿意度數據
   - 決定預設版本

2. **智能切換**：
   - 根據問題類型自動推薦版本
   - 機器學習預測最佳搜尋策略

3. **V3 開發**：
   - 混合搜尋（V1 + V2）
   - 動態調整上下文視窗
   - 更智能的段落選擇

---

## 📝 總結

### 實作成果

| 目標 | 狀態 | 說明 |
|------|------|------|
| 後端 API 支援 | ✅ | `search_sections` action 支援 version 參數 |
| 前端 Hook 整合 | ✅ | `useRvtChat` 支援搜尋版本狀態 |
| UI 組件開發 | ✅ | `SearchVersionToggle` 提供直觀切換介面 |
| localStorage 持久化 | ✅ | 記住用戶選擇 |
| 向後兼容 | ✅ | 不影響其他 Assistant |
| 文檔完整性 | ✅ | 實作報告 + 測試指南 |

### 關鍵特點

1. **簡單直觀**：一個 Switch 開關即可切換版本
2. **效能監控**：返回執行時間，方便效能分析
3. **向後兼容**：不影響現有功能，可選擇性啟用
4. **可擴展性**：設計模式可輕鬆應用到其他 Assistant
5. **持久化**：記住用戶偏好，提升體驗

### 下一步行動

1. **立即測試**：按照測試指南進行完整測試
2. **Protocol 支援**：擴展到 Protocol Assistant
3. **使用追蹤**：開始收集使用數據
4. **效能優化**：根據實際使用情況優化 V2 查詢

---

## 📚 相關文檔

- **實作計劃**：`/docs/development/search-version-toggle-complete-plan.md`
- **向量搜尋指南**：`/docs/vector-search/vector-search-guide.md`
- **API 文檔**：`/docs/api/search-sections-api.md`（待建立）
- **UI 組件規範**：`/docs/development/ui-component-guidelines.md`

---

**報告完成日期**: 2025-11-09  
**實作團隊**: AI Platform Development Team  
**審核狀態**: ✅ 實作完成，待測試驗證  
**版本**: v1.0.0
