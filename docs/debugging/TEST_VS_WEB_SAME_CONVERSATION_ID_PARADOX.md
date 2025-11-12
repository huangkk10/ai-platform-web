# 🔍 測試腳本 vs Web：相同 conversation_id，為何結果不同？

## 🎯 **用戶的關鍵質疑**

> "測試腳本不是也有用相同的 conversation_id 去測試嗎？為什麼測試腳本 80% 成功，Web 只有 14.3% 成功？"

## ✅ **你說得對！讓我們重新分析**

---

## 📊 **事實核對：兩者都使用持續的 conversation_id**

### **測試腳本模式 1**

```python
# backend/test_protocol_crystaldiskmark_stability.py (Line 442-450)

# 執行測試模式 1（模擬 Web 前端實際行為：持續使用相同 ID）
print("📌 測試模式 1：持續使用相同 ID（模擬 Web 前端實際行為）")
print("   ✅ 自動持久化 conversation_id（localStorage）")
tester.run_stability_test(
    query=test_query,
    test_count=10,
    use_same_conversation=True,  # ✅ 持續使用相同 ID
    delay_between_tests=1.0
)
```

**實際執行邏輯**：

```python
def run_stability_test(self, ..., use_same_conversation=True):
    conversation_id = None  # ✅ 初始為 None
    
    for i in range(1, 11):  # 測試 10 次
        result = self.run_single_query(
            query="crystaldiskmark",
            conversation_id=conversation_id if conversation_id is not None else ""
        )
        
        # ✅ 第一次查詢後，儲存 conversation_id
        if use_same_conversation and conversation_id is None:
            conversation_id = result.get('conversation_id', "")
        
        # ✅ 後續查詢都使用這個 conversation_id
```

**測試結果**：
- ✅ 成功率：8/10 (80%)
- ⚠️ 測試 #7-8 失敗（I3C 出現）
- ✅ 測試 #9-10 恢復成功

---

### **Web 前端（用戶實際使用）**

```javascript
// frontend/src/hooks/useMessageStorage.js

// 自動載入 conversation_id（從 localStorage）
const conversationId = loadConversationId(storageKey, currentUserId);

// 每次發送訊息都使用這個 conversation_id
const requestBody = {
  message: userMessage.content,
  conversation_id: conversationId,  // ✅ 持續使用相同 ID
  user_id: currentUserId,
  search_version: 'v2'
};
```

**實際使用情況**：
- Conversation ID: `4f5510ae-8df5-452e-903f-87aa6ca691b2`
- 查詢次數：7 次（用戶提供的截圖）
- 查詢間隔：15-85 秒

**測試結果**：
- ❌ 成功率：1/7 (14.3%)
- ✅ 查詢 #1 成功（CrystalDiskMark）
- ❌ 查詢 #2-7 全部失敗（I3C 85.32%）

---

## 🤔 **為什麼相同條件下結果不同？**

### **關鍵差異分析**

| 因素 | 測試腳本模式 1 | Web 前端 | 影響程度 |
|------|--------------|---------|---------|
| **使用相同 conversation_id** | ✅ 是 | ✅ 是 | ➡️ **相同** |
| **Threshold 設定** | 0.85 | 0.85 | ➡️ **相同** |
| **Top K 設定** | 3 | 3 | ➡️ **相同** |
| **搜尋模式** | Mode B (Two-Tier) | Mode B (Two-Tier) | ➡️ **相同** |
| **查詢內容** | "crystaldiskmark" | "crystaldiskmark" | ➡️ **相同** |
| **查詢間隔** | 1 秒 | 15-85 秒 | ⚠️ **不同**（但更長的間隔應該更好）|
| **測試次數** | 10 次（短期） | 7 次（但可能是更長對話的一部分） | ⚠️ **不同** |
| **對話歷史長度** | 10 輪（測試範圍） | **未知**（可能 > 100 輪）| 🔥 **關鍵差異！** |
| **環境狀態** | 全新 Python 進程 | 持續運行的瀏覽器 | 🔥 **關鍵差異！** |
| **Dify 記憶累積** | 短期（10 輪） | **長期（可能數十/數百輪）** | 🔥 **關鍵差異！** |

---

## 💡 **真正的差異：Dify 對話歷史長度**

### **假設 1：測試腳本是「乾淨」的短對話**

```
測試腳本執行時間線：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T=0s    → 生成新的 conversation_id: xxx-123
T=1s    → 查詢 #1: crystaldiskmark (CrystalDiskMark ✅)
T=2s    → 查詢 #2: crystaldiskmark (CrystalDiskMark ✅)
T=3s    → 查詢 #3: crystaldiskmark (CrystalDiskMark ✅)
...
T=7s    → 查詢 #7: crystaldiskmark (I3C ❌ 開始出錯)
T=8s    → 查詢 #8: crystaldiskmark (I3C ❌)
T=9s    → 查詢 #9: crystaldiskmark (CrystalDiskMark ✅ 恢復！)
T=10s   → 查詢 #10: crystaldiskmark (CrystalDiskMark ✅)
T=11s   → 測試結束，Python 進程關閉
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

總對話輪數：10 輪（5 user + 5 assistant 回應）
Dify 記憶狀態：短期、乾淨、容易糾正
```

**為什麼會恢復？**
- 對話歷史短（只有 10 輪）
- 錯誤關聯的權重還不夠強
- 新的正確檢索結果可以覆蓋錯誤
- 向量搜尋的隨機性在短對話中影響較小

---

### **假設 2：Web 前端是「污染」的長對話**

```
用戶實際使用時間線（推測）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
T=-3600s  → 數小時前開始使用 Protocol Assistant
           → 可能累積了大量對話歷史（Protocol、IOL、ULINK、I3C...）
           → conversation_id: 4f5510ae-8df5-452e-903f-87aa6ca691b2
           → Dify 記憶中可能已經包含 I3C 的相關討論
...
T=0s      → 用戶開始測試 crystaldiskmark（截圖記錄開始）
T=0s      → 查詢 #1: crystaldiskmark (CrystalDiskMark 90.74% ✅ 首次成功)
T=16s     → 查詢 #2: crystaldiskmark (I3C 85.32% ❌ 開始錯誤)
T=47s     → 查詢 #3: crystaldiskmark (I3C 85.32% ❌)
T=62s     → 查詢 #4: crystaldiskmark (I3C 85.32% ❌)
T=147s    → 查詢 #5: crystaldiskmark (I3C 85.32% ❌)
T=162s    → 查詢 #6: crystaldiskmark (I3C 85.32% ❌)
T=177s    → 查詢 #7: crystaldiskmark (I3C 85.32% ❌)
...
T=後續    → 用戶可能繼續使用，錯誤持續...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

總對話輪數：可能 > 100 輪（我們只看到最後 7 次 crystaldiskmark 查詢）
Dify 記憶狀態：長期、複雜、錯誤關聯已深度建立
```

**為什麼無法恢復？**
- ✅ 對話歷史很長（可能 > 100 輪）
- ✅ Dify 記憶中可能已經累積大量上下文
- ✅ 錯誤關聯（I3C）的權重很強
- ✅ 新的正確檢索被錯誤關聯壓制
- ✅ 長對話中的「慣性」效應

---

## 🔬 **驗證假設：檢查 Web 對話的真實長度**

### **方法 1：查詢 Dify 平台的對話記錄**

```bash
# 如果有 Dify 資料庫訪問權限
# 查詢這個 conversation_id 的所有訊息

SELECT COUNT(*) as message_count
FROM conversations
WHERE conversation_id = '4f5510ae-8df5-452e-903f-87aa6ca691b2';

# 預期結果：可能遠大於 7 條
```

### **方法 2：檢查 localStorage 的其他資料**

```javascript
// 在瀏覽器 Console 執行
const conversationId = '4f5510ae-8df5-452e-903f-87aa6ca691b2';
const messages = JSON.parse(localStorage.getItem('protocol-assistant-messages-1'));
console.log('總訊息數:', messages.length);
console.log('訊息內容:', messages);
```

### **方法 3：詢問用戶**

**關鍵問題**：
1. 在這 7 次 crystaldiskmark 查詢之前，你有使用過這個 Protocol Assistant 嗎？
2. 這個對話是全新開始的，還是已經使用了一段時間？
3. 在查詢 crystaldiskmark 之前，有沒有討論過 I3C 相關的內容？

---

## 🎯 **最可能的真相**

### **場景重建**

```
用戶的實際使用情況（推測）：
════════════════════════════════════════════════════════════

階段 1：早期使用（數小時前）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
用戶查詢 1: "Protocol 測試流程"
AI 回應: [提供 Protocol 相關資訊]

用戶查詢 2: "IOL 放測步驟"
AI 回應: [提供 IOL 相關資訊]

用戶查詢 3: "I3C 相關說明"  ⚠️ 關鍵！
AI 回應: [檢索到 I3C 相關說明文檔]
         → Dify 記憶中建立了 I3C 的關聯

... 更多查詢 ...
（累積 > 50 輪對話）

階段 2：測試 crystaldiskmark（截圖記錄）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
查詢 #1: "crystaldiskmark"
→ 向量搜尋: CrystalDiskMark (90.74%), I3C (85.32%), ...
→ Dify 選擇: CrystalDiskMark ✅ （首次查詢，記憶權重低）

查詢 #2: "crystaldiskmark"（16 秒後）
→ 向量搜尋: CrystalDiskMark (90.74%), I3C (85.32%), ...
→ Dify 記憶: "我記得用戶之前問過 I3C" ⚠️
→ Dify 選擇: I3C ❌ （記憶權重開始影響）

查詢 #3-7: "crystaldiskmark"
→ Dify 記憶: "用戶一直在問 I3C 相關問題" ⚠️⚠️⚠️
→ Dify 選擇: I3C ❌❌❌（記憶權重主導）
→ 錯誤循環無法打破

════════════════════════════════════════════════════════════
```

---

## 🔍 **測試腳本為什麼能恢復？**

### **測試腳本的「乾淨」環境**

```python
# 測試腳本每次執行都是全新的
$ python test_protocol_crystaldiskmark_stability.py

[執行開始]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 新的 Python 進程
2. 新的 conversation_id（首次查詢時生成）
3. 無歷史記憶（Dify 對話為空）
4. 只有 10 輪對話（user + assistant）
5. 單一主題：crystaldiskmark（無其他干擾）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

查詢 #1-6: CrystalDiskMark ✅
  → Dify 記憶：空 → 輕量級
  → 向量搜尋主導決策

查詢 #7-8: I3C ❌ (短暫錯誤)
  → 向量搜尋隨機性 + Score 接近
  → 暫時選錯

查詢 #9-10: CrystalDiskMark ✅ (恢復！)
  → Dify 記憶：仍然輕量級（只有 10 輪）
  → 新的檢索結果可以糾正錯誤
  → **沒有深度污染**

[執行結束]
Python 進程關閉 → 所有記憶清空
```

**關鍵差異**：
- ✅ **對話歷史短**（10 輪）
- ✅ **記憶權重低**（Dify 內部機制）
- ✅ **單一主題**（無干擾）
- ✅ **可糾正**（錯誤關聯未固化）

---

## 📊 **實驗驗證**

### **實驗 A：測試「對話長度」的影響**

修改測試腳本，增加對話輪數：

```python
# 新測試腳本：test_long_conversation_effect.py

# 測試 1：10 輪對話（現有測試）
tester.run_stability_test(test_count=10)  # 預期: 80% 成功

# 測試 2：50 輪對話
tester.run_stability_test(test_count=50)  # 預期: 成功率下降？

# 測試 3：100 輪對話
tester.run_stability_test(test_count=100)  # 預期: 成功率進一步下降？
```

**預期結果**：
- 如果對話長度是關鍵因素
- 則隨著輪數增加，成功率應該下降
- 且錯誤後更難恢復

---

### **實驗 B：測試「干擾查詢」的影響**

```python
# 新測試腳本：test_interference_effect.py

# 階段 1：先詢問 I3C 相關問題（建立錯誤關聯）
for i in range(10):
    tester.run_single_query("I3C 相關說明", i)

# 階段 2：再詢問 crystaldiskmark（測試是否受干擾）
for i in range(10):
    tester.run_single_query("crystaldiskmark", i+10)
```

**預期結果**：
- 如果 Dify 記憶是關鍵因素
- 則階段 2 的 crystaldiskmark 查詢會優先選擇 I3C
- 成功率應該顯著下降（接近 Web 的 14.3%）

---

## 🎯 **結論**

### **測試腳本 80% vs Web 14.3% 的真正原因**

| 原因 | 可能性 | 證據 |
|------|--------|------|
| **對話歷史長度不同** | 🔥🔥🔥 極高 | 測試腳本只有 10 輪，Web 可能 > 100 輪 |
| **Dify 記憶累積程度** | 🔥🔥🔥 極高 | 長對話中錯誤關聯更難糾正 |
| **環境狀態差異** | 🔥🔥 高 | 測試腳本全新進程，Web 持續運行 |
| **查詢間隔時間** | ❌ 低 | Web 間隔更長（15-85s），應該更有利 |
| **Score Threshold 0.85** | 🔥🔥🔥 極高 | **根本原因**（兩者都受影響） |

### **最終答案**

**雖然測試腳本和 Web 都使用相同的 conversation_id，但它們的「對話上下文複雜度」完全不同**：

1. **測試腳本**：
   - 乾淨的短對話（10 輪）
   - 單一主題（crystaldiskmark）
   - 記憶權重低，錯誤可糾正
   - **成功率 80%**

2. **Web 前端**：
   - 複雜的長對話（可能 > 100 輪）
   - 多主題混合（Protocol, IOL, I3C, crystaldiskmark...）
   - 記憶權重高，錯誤關聯固化
   - **成功率 14.3%**

3. **根本問題**：
   - **Score Threshold 0.85 太低**
   - CrystalDiskMark (90.74%) vs I3C (85.32%)
   - 只差 5.42%，當 Dify 記憶介入時，排名易翻轉

---

## 🚀 **解決方案（不變）**

```sql
-- 提高 Threshold 到 0.88
UPDATE search_threshold_settings 
SET threshold = 0.88 
WHERE assistant_type = 'protocol_assistant';
```

**為什麼這個方案有效？**
- ✅ 過濾掉 I3C (85.32%)
- ✅ 只保留 CrystalDiskMark (90.74%)
- ✅ **無論對話多長，都不會檢索到錯誤文檔**
- ✅ Dify 記憶無法影響（因為 I3C 根本不在檢索結果中）

---

## 📅 **更新記錄**

**2025-11-12 18:30**：
- ✅ 確認測試腳本模式 1 也使用持續的 conversation_id
- ✅ 識別真正差異：對話歷史長度和複雜度
- ✅ 提出實驗方案驗證假設
- ✅ 重申 Threshold 提高的解決方案

**關鍵洞察**：
> "相同的 conversation_id ≠ 相同的對話上下文。測試腳本 10 輪 vs Web 可能 100+ 輪，Dify 記憶權重完全不同，導致成功率差異巨大。"

