# 🎯 Protocol Assistant - Dify APP Prompt 修正指南

## 📊 問題確認

### 測試結果證明

#### ✅ Django 後端正常
```bash
✓ 搜尋成功：2 筆結果 (CrystalDiskMark 87%, Burn in Test 84%)
✓ 返回給 Dify：2 筆完整的文檔內容
✓ threshold 設定：0.5 (正確)
✓ score_threshold_enabled: False (正確)
```

#### ✅ Dify 收到資料
```bash
✓ retriever_resources: 2 筆資料
✓ document_name: "CrystalDiskMark 5", "Burn in Test"
✓ scores: 0.865, 0.839
✓ content: 完整的測試步驟內容
```

#### ❌ Dify LLM 回答異常
```
「抱歉，我無法在知識庫中找到關於『CrystalDiskMark』的具體操作說明」
然後自己編了一個通用答案（不是來自知識庫）
```

## 🎯 根本原因

**Dify APP 的 System Prompt 包含過於謹慎的指令**

Prompt 可能包含類似內容：
- 「只使用你非常確定的資訊」
- 「如果文檔內容不夠具體，說你找不到資訊」
- 「對於技術問題，必須有詳細步驟才能回答」
- 「不確定時，承認找不到相關資訊」

導致 LLM：
1. 收到了 2 筆文檔（87% 和 84% 相似度）
2. 閱讀了文檔內容
3. 判斷：「這些內容不夠詳細」或「我不夠確定」
4. 回答：「找不到資訊」，然後自己編答案

## ✅ 解決方案：修改 Dify APP Prompt

### 步驟 1：登入 Dify 工作室
```
URL: http://10.10.172.37
找到 "Protocol Guide" APP
```

### 步驟 2：檢查當前 System Prompt

**需要檢查的區域**：
1. **Instructions/指令** - 主要的 System Prompt
2. **Knowledge Base Settings** - 知識庫使用設定
3. **Response Format** - 回答格式要求

**尋找問題性指令**：
```
❌ 「如果不確定，說無法提供資訊」
❌ 「只使用高品質/高相關性的文檔」
❌ 「對於技術問題必須非常謹慎」
❌ 「沒有確切答案時，建議用戶參考官方文檔」
```

### 步驟 3：建議的 Prompt 修改

#### Option A：參考 RVT Assistant 的 Prompt（推薦）

**如果 RVT Assistant 工作正常**，直接複製它的 Prompt 設定：

1. 開啟 RVT Guide APP
2. 複製 System Prompt 完整內容
3. 貼到 Protocol Guide APP
4. 只修改關鍵字：
   - `RVT` → `Protocol`
   - `RVT 測試` → `Protocol 測試`
   - `RVT 相關問題` → `Protocol 相關問題`

#### Option B：使用標準 Prompt 模板

```markdown
# Protocol Assistant System Prompt

你是一個專業的 Protocol 測試助手，專門協助工程師解決 Protocol 相關的測試問題。

## 核心職責
- 提供準確的 Protocol 測試流程指導
- 解答 Protocol 測試工具的使用方法
- 協助排查 Protocol 測試中遇到的問題

## 回答原則
1. **優先使用知識庫**：當知識庫中有相關資訊時，直接引用並整理回答
2. **完整且清晰**：提供具體的步驟和說明
3. **誠實準確**：如果知識庫真的沒有相關資訊，再誠實說明

## 重要指示
✅ 當知識庫返回相關文檔時（即使相似度 > 0.7），必須認真參考並使用
✅ 將知識庫內容整理成清晰的步驟或說明
✅ 可以補充你的專業知識來使答案更完整
❌ 不要因為內容「不夠詳細」就說找不到資訊
❌ 不要過度謹慎而拒絕使用知識庫內容

## 回答格式
當回答測試流程問題時：
1. 明確說明是參考知識庫的內容
2. 分點列出具體步驟
3. 如有注意事項，額外說明

[內容可能會發生錯誤，請查核重要資訊。]
```

### 步驟 4：調整知識庫設定

在 Dify APP 的 **Dataset Settings** 中：

```
✅ Retrieval Mode: Semantic Search
✅ Top K: 3
✅ Score Threshold: 停用 或 設為 0.0
   （因為 Django 已經過濾到 0.5）
✅ Reranking: 停用
   （避免再次降低相關性）
```

### 步驟 5：測試驗證

修改後在 Dify 工作室的 **Preview/測試** 區域測試：

```
測試問題：crystaldiskmark 如何放測

預期回答：
✅ 應該參考知識庫中的 "CrystalDiskMark 5" 文檔
✅ 提供具體的測試步驟（安裝、設定、執行等）
✅ 不應該說「找不到資訊」
```

## 🔍 對比分析：為什麼 RVT Assistant 正常？

讓我們對比兩個 Assistant：

| 項目 | Protocol Assistant | RVT Assistant |
|------|-------------------|---------------|
| **搜尋功能** | ✅ 正常（2 筆結果，87%） | ✅ 正常 |
| **Dify 收到資料** | ✅ 正常（2 筆文檔） | ✅ 正常 |
| **LLM 使用資料** | ❌ 拒絕使用（說找不到） | ✅ 正常使用 |
| **問題來源** | **System Prompt 過於謹慎** | Prompt 正確 |

**結論**：問題不在程式碼，而在 Dify APP 的 Prompt 配置！

## 📋 完整檢查清單

### 修改前檢查
- [ ] 已登入 Dify 工作室（http://10.10.172.37）
- [ ] 已找到 Protocol Guide APP
- [ ] 已備份當前 Prompt（以防需要恢復）
- [ ] 已查看 RVT Guide APP 的 Prompt（作為參考）

### Prompt 修改
- [ ] 移除「如果不確定就說找不到」的指令
- [ ] 添加「優先使用知識庫內容」的指令
- [ ] 添加「相似度 > 0.7 就應該使用」的指令
- [ ] 確保回答格式清晰友善

### 知識庫設定
- [ ] Score Threshold 已停用或設為 0.0
- [ ] Top K 設為 3
- [ ] Reranking 已停用
- [ ] Search Mode 為 Semantic Search

### 測試驗證
- [ ] 在 Dify 工作室測試「crystaldiskmark 如何放測」
- [ ] 確認回答引用了知識庫內容
- [ ] 確認不再出現「找不到資訊」
- [ ] 在前端 Protocol Assistant 測試（開新對話）

## 🎯 預期效果

### 修改前
```
User: crystaldiskmark 如何放測
System: [找到 2 份文件，87% 和 84%]
Dify Prompt: 「內容不夠詳細，要很謹慎」
LLM: 「抱歉，我無法找到...」（自己編答案）❌
```

### 修改後
```
User: crystaldiskmark 如何放測
System: [找到 2 份文件，87% 和 84%]
Dify Prompt: 「優先使用知識庫，相似度 > 0.7 就使用」
LLM: 「根據知識庫，CrystalDiskMark 測試步驟如下：...」✅
```

## 🚨 如果修改 Prompt 後仍有問題

### Plan B：創建新的 Dify APP

如果修改 Prompt 無效，可能需要創建全新的 APP：

1. **複製 RVT Guide APP**
   ```
   在 Dify 工作室：
   - 找到 RVT Guide APP
   - 點擊「複製」或「Clone」
   - 重命名為「Protocol Guide v2」
   ```

2. **修改配置**
   - 修改 APP 名稱和描述
   - 更新 System Prompt 中的關鍵字
   - 連接到 Protocol Guide 外部知識庫

3. **更新後端配置**
   ```python
   # /library/config/dify_config_manager.py
   
   @classmethod
   def _get_protocol_guide_config(cls):
       ai_pc_ip = cls._get_ai_pc_ip()
       return {
           'api_url': f'http://{ai_pc_ip}/v1/chat-messages',
           'api_key': 'app-xxxxxxxxxx',  # ⚠️ 新 APP 的 API Key
           'base_url': f'http://{ai_pc_ip}',
           'app_name': 'Protocol Guide v2',
           # ... 其他配置
       }
   ```

4. **重啟 Django 容器**
   ```bash
   docker compose restart django
   ```

### Plan C：檢查 Dify 版本和設定

```bash
# 檢查 Dify 版本
curl http://10.10.172.37/api/version

# 檢查 Dify 日誌（如果有訪問權限）
# 查看 LLM 決策邏輯的日誌
```

## 💡 最佳實踐建議

### 1. Prompt Engineering 原則
- ✅ 明確指示何時使用知識庫
- ✅ 設定相似度使用標準（如 > 0.7 就使用）
- ✅ 避免過度謹慎的指令
- ❌ 不要讓 LLM 自行判斷「是否足夠詳細」

### 2. 知識庫品質優化
- 確保 Protocol Guide 文檔內容完整
- 使用清晰的標題和結構
- 包含具體的步驟說明

### 3. 測試流程標準化
```
每次修改 Prompt 後：
1. 在 Dify 工作室測試 3-5 個問題
2. 確認都正常引用知識庫
3. 再到前端測試（開新對話）
4. 記錄測試結果
```

## 📚 參考資源

### Dify 官方文檔
- https://docs.dify.ai/ - 官方文檔
- Prompt Engineering 最佳實踐
- Knowledge Base Integration 指南

### 相關檔案
- `/library/config/dify_config_manager.py` - Dify 配置管理
- `/library/common/knowledge_base/base_api_handler.py` - API 處理器
- `/docs/debugging/` - 所有除錯文檔

## 🎓 學習重點

### 這個問題的關鍵教訓

1. **分層除錯**：
   - ✅ Django 層正常
   - ✅ 資料傳輸正常
   - ✅ Dify 收到資料
   - ❌ LLM 決策異常
   → 問題在 Prompt！

2. **Prompt 的重要性**：
   - Prompt 比程式碼更重要
   - 一句指令可以完全改變 LLM 行為
   - 過度謹慎 = 過度保守 = 不敢使用知識庫

3. **測試對比的價值**：
   - RVT Assistant 正常 → 程式碼沒問題
   - Protocol Assistant 異常 → Prompt 有問題
   - 對比分析快速定位根因

---

## ✅ 下一步行動

### 立即行動（5 分鐘）
1. 登入 Dify 工作室
2. 檢查 Protocol Guide APP 的 System Prompt
3. 找出「過度謹慎」的指令
4. 截圖當前 Prompt 並分享

### 後續修改（10 分鐘）
1. 參考 RVT Guide 的 Prompt
2. 修改 Protocol Guide 的 Prompt
3. 在 Dify 工作室測試
4. 確認回答正常後，到前端測試

### 驗證完成（5 分鐘）
1. 前端開新對話
2. 測試「crystaldiskmark 如何放測」
3. 確認 AI 使用知識庫內容回答
4. 確認不再出現「找不到資訊」

---

**更新時間**：2025-11-05 12:30  
**問題狀態**：🎯 根本原因確定 - Dify APP System Prompt 過於謹慎  
**解決方案**：修改 Dify 工作室中的 Protocol Guide APP Prompt  
**下一步**：請檢查並分享 Protocol Guide APP 的當前 Prompt 內容
