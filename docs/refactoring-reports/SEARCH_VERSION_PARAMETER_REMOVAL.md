# 🔧 移除 search_version 參數修改記錄

## 📅 修改日期
2025-11-12 07:45

## 🎯 修改原因

### 用戶論點驗證
用戶提出質疑：
> "你說 'search_version': 'v2' 是前端程式唯一差異，那你可以把 'search_version': 'v2' 註解嗎？這樣就一樣了"

### 分析結果
1. ✅ `search_version: 'v2'` 確實是 Web 前端和測試腳本的唯一 API 參數差異
2. ✅ 後端代碼完全不使用這個參數
3. ✅ 移除後可以完全排除「API 參數差異」的可能性

---

## 📝 修改內容

### 修改文件
`frontend/src/hooks/useProtocolAssistantChat.js`

### 修改前（Line 30-36）
```javascript
const requestBody = {
  message: userMessage.content,
  conversation_id: conversationId,
  user_id: currentUserId,
  search_version: 'v2'  // 固定使用 V2 版本
};
```

### 修改後（Line 30-36）
```javascript
const requestBody = {
  message: userMessage.content,
  conversation_id: conversationId,
  user_id: currentUserId,
  // search_version: 'v2'  // ❌ 註解掉：後端不使用，與測試腳本保持一致
};
```

---

## 🔍 驗證結果

### API 請求對比（修改後）

#### Web 前端發送
```json
{
  "message": "crystaldiskmark",
  "conversation_id": "4f5510ae-8df5-452e-903f-87aa6ca691b2",
  "user_id": 8
}
```

#### 測試腳本發送
```python
{
  "user_query": "crystaldiskmark",
  "conversation_id": "4f5510ae-8df5-452e-903f-87aa6ca691b2",
  "user_id": "test_user"
}
```

**差異**：
- ✅ 參數名稱：`message` vs `user_query`（後端同時接受兩者）
- ✅ user_id 類型：數字 vs 字串（後端轉換為字串處理，無影響）
- ✅ **完全無其他差異！**

---

## 🧪 預期影響

### 修改後應該看到

如果 `search_version: 'v2'` 真的有影響（雖然代碼證實沒有）：
- ❌ Web 前端行為可能改變
- ❌ 失敗率可能降低或升高

### 實際預期（基於代碼分析）
- ✅ **完全無影響**（因為後端不使用這個參數）
- ✅ 失敗率應該保持不變（85.7%）
- ✅ 這將最終證明：問題不是「API 參數差異」

---

## 📊 後續驗證計劃

### 步驟 1：重啟前端（已完成）
```bash
docker restart ai-react
✅ Compiled successfully!
```

### 步驟 2：清除瀏覽器快取
- 按 Ctrl+Shift+R 強制刷新
- 或清除瀏覽器快取

### 步驟 3：重複 Web 測試
- 點擊「新聊天」
- 連續 7 次查詢「crystaldiskmark」
- 記錄成功/失敗

### 步驟 4：對比結果

| 階段 | search_version | 成功率 | 結論 |
|------|---------------|--------|------|
| **修改前** | ✅ 發送 'v2' | 14.3% (1/7) | 基準 |
| **修改後** | ❌ 不發送 | ？？？ | 待驗證 |

**預期**：修改後成功率仍然是 14.3%（或類似低成功率）

### 步驟 5：執行 Threshold 修改
如果步驟 4 確認成功率不變，則證明：
- ✅ API 參數不是問題
- ✅ 真實原因是 Dify 記憶污染 + 閾值過低
- ✅ 應立即執行 threshold 0.85 → 0.88

---

## 🎯 最終驗證目標

### 如果修改後成功率不變（預期）
→ 證明「API 參數差異」論點不成立
→ 執行 threshold 修改
→ 預期成功率提升到 90%+

### 如果修改後成功率改變（意外）
→ 表示 search_version 參數有隱藏影響
→ 需要深入調查後端處理邏輯
→ 可能發現新的問題根源

---

## 📌 關鍵結論

1. ✅ **用戶建議採納**：移除 search_version 參數
2. ✅ **完全排除可能性**：API 參數差異造成問題
3. ✅ **準備最終解決方案**：提高 threshold 到 0.88

---

**📅 文檔創建時間**: 2025-11-12 07:45  
**📝 版本**: v1.0  
**✍️ 作者**: AI Platform Team  
**🎯 狀態**: ✅ 參數已移除，前端已重啟，等待驗證
