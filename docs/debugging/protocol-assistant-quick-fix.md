# Protocol Assistant 不回答問題 - 快速修復指南

**問題**：AI 找到資料但說「不清楚」  
**影響**：用戶無法獲得正確答案  
**修復時間**：5-10 分鐘

---

## 🎯 根本原因（90% 確定）

**Dify 工作室的 Score 閾值設定過高，覆蓋了 Django 代碼的設定。**

---

## ✅ 快速修復步驟

### 步驟 1：登入 Dify 工作室（2 分鐘）

```
網址：http://10.10.172.37
使用者：admin / 你的密碼
```

### 步驟 2：調整 Protocol Guide 設定（3 分鐘）

1. 進入 **Protocol Guide** 應用
2. 點擊 **編排**
3. 找到 **知識庫 → 外部知識庫 → Protocol Guide**
4. 檢查 **檢索設定**

**修改方式**：

#### 選項 A：關閉 Score 閾值（推薦）
```
☐ 啟用 Score 閾值過濾
```
取消勾選此選項

#### 選項 B：降低閾值
```
☑ 啟用 Score 閾值過濾
   Score 閾值: 0.5
```
設定為 0.5（與 Django 一致）

### 步驟 3：調整提示詞（可選，5 分鐘）

在 **編排 → 提示詞** 部分，確認：

**❌ 移除這些指令**：
- "如果不確定，請說不知道"
- "只有在完全確定時才回答"
- "寧可不答，也不要錯答"

**✅ 添加這些指令**：
- "優先使用提供的知識庫資料"
- "如果資料完整，直接提供詳細答案"
- "只有在完全沒有相關資料時才說我不清楚"

### 步驟 4：驗證修復（2 分鐘）

```bash
# 運行測試腳本
cd /home/user/codes/ai-platform-web
./test_protocol_assistant_fix.sh
```

**預期結果**：
```
✅ 成功：找到 3 筆資料
✅ 成功：AI 提供了詳細回答
✅ 成功：觸發文檔級搜尋，提供完整 SOP
通過測試: 3 / 3
🎉 太棒了！所有測試通過！
```

---

## 🔍 診斷工具

### 快速測試外部 API
```bash
curl -s -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "crystaldiskmark",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

### 快速測試 Chat API
```bash
curl -s -X POST "http://localhost/api/protocol-guide/chat/" \
  -H "Content-Type: application/json" \
  -d '{"message": "crystaldiskmark 完整說明", "conversation_id": ""}' \
  | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('answer', '')[:500])"
```

### 查看 Django 日誌
```bash
docker logs ai-django | grep "Protocol" | tail -20
```

---

## 📊 成功指標

| 指標 | 目標 | 如何檢查 |
|------|------|---------|
| 外部 API 返回資料 | ≥ 3 筆 | 運行測試腳本 |
| AI 回答長度 | ≥ 500 字元 | 運行測試腳本 |
| AI 使用知識庫 | ✓ 包含關鍵字 | 查看回答內容 |
| 無「不清楚」回應 | 0 次 | 測試多次查詢 |

---

## 🚨 如果仍然失敗

### 檢查 1：Django 配置
```bash
# 確認 score_threshold_enabled = False
grep -A 5 "score_threshold_enabled" \
  /home/user/codes/ai-platform-web/library/common/knowledge_base/base_api_handler.py
```

應該看到：
```python
'score_threshold_enabled': False,  # ✅
```

### 檢查 2：Dify 服務狀態
```bash
curl http://10.10.172.37/health
```

### 檢查 3：完整日誌
```bash
docker logs ai-django | grep -A 10 "ProtocolGuide.*chat request"
```

---

## 📚 完整文檔

- **根本原因分析**：`docs/debugging/protocol-assistant-root-cause-analysis.md`
- **問題診斷指南**：`docs/debugging/protocol-assistant-no-answer-issue.md`
- **測試腳本**：`test_protocol_assistant_fix.sh`

---

## 💡 推薦提示詞模板

```
你是專業的 Protocol 測試助手。

核心任務：
- 優先使用提供的知識庫資料回答問題
- 如果資料完整，直接提供詳細答案
- 如果資料部分相關，說明「根據現有資料...」並給出答案
- 只有在完全沒有相關資料時才說「我找不到相關資訊」

回答格式：
- 使用清晰的段落或條列式
- 引用具體的文檔來源
- 重要資訊使用粗體強調
```

---

**作者**：AI Platform Team  
**更新**：2025-11-10  
**版本**：v1.0  
**狀態**：✅ 待驗證
