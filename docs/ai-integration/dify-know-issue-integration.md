# Dify Know Issue 外部知識庫整合指南

## 🎯 概述
本指南說明如何將 AI Platform 的 Know Issue 資料庫配置為 Dify 的外部知識庫，實現智能問題查詢功能。

## 📋 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dify AI      │────│   Nginx Proxy    │────│   Django API    │
│   (外部系統)    │    │   (Port 80)      │    │   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                ┌─────────────────┐
                                                │  PostgreSQL DB  │
                                                │ (Know Issue)    │
                                                └─────────────────┘
```

## 🔧 API 端點資訊

### Know Issue 專用端點
```
POST /api/dify/know-issue/retrieval/
```

### 請求格式
```json
{
    "knowledge_id": "know_issue_db",
    "query": "搜索關鍵字",
    "retrieval_setting": {
        "top_k": 3,
        "score_threshold": 0.3
    }
}
```

### 響應格式
```json
{
    "records": [
        {
            "content": "問題編號: ULINK_NVMe_Protocol-5\n專案: Samsung_SSV5Q\n測試版本: V5.0\n...",
            "score": 0.9,
            "title": "ULINK_NVMe_Protocol-5 - Samsung_SSV5Q",
            "metadata": {
                "source": "know_issue_database",
                "issue_id": "ULINK_NVMe_Protocol-5",
                "project": "Samsung_SSV5Q",
                "test_version": "V5.0",
                "issue_type": "FW Limit",
                "status": "N/A"
            }
        }
    ]
}
```

## 🔍 搜索功能特色

### 支援的搜索欄位
- **問題編號** (issue_id) - 最高優先級 (分數: 1.0)
- **專案名稱** (project) - 高優先級 (分數: 0.9)
- **測試類別** (test_class_name) - 中高優先級 (分數: 0.8)
- **錯誤訊息** (error_message) - 中優先級 (分數: 0.7)
- **補充說明** (supplement) - 中低優先級 (分數: 0.6)
- **相關腳本** (script) - 低優先級 (分數: 0.5)

### 智能分數計算
系統會根據關鍵字匹配的欄位自動分配相應分數，確保最相關的結果排在前面。

## 🛠️ 在 Dify 中的配置步驟

### 步驟 1：添加外部知識 API
1. 進入 Dify → 知識庫 → 外部知識 API
2. 點擊「添加外部知識 API」
3. 配置如下：
   ```
   名稱: know_issue_api
   API Endpoint: http://10.10.172.127/api/dify/know-issue/
   API Key: know-issue-api-key-2024 (可選)
   ```

⚠️ **重要提醒**：
- API Endpoint 必須以 `/` 結尾：`http://10.10.172.127/api/dify/know-issue/`
- **不要**包含 `/retrieval`，因為 Dify 會自動附加這個路徑
- 錯誤示例：`http://10.10.172.127/api/dify/know-issue/retrieval/` ❌

### 步驟 2：創建外部知識庫
1. 進入 Dify → 知識庫 → 創建知識庫
2. 選擇「外部知識庫」
3. 配置如下：
   ```
   知識庫名稱: know_issue_knowledge_base
   知識庫描述: AI Platform Know Issue 問題知識庫 - 提供測試問題、錯誤訊息、解決方案等查詢功能
   外部知識 API: know_issue_api (選擇剛才建立的 API)
   外部知識 ID: know_issue_db
   ```

### 步驟 3：配置檢索設定 ⚠️ **重要**
```
Top K: 3-5 (建議)
Score 閾值: 0.3-0.5 (重要：不要設太高，否則檢索不會被觸發)
```

### 步驟 4：在應用中使用
1. **添加知識庫到應用**
   - 在應用的「上下文」區域添加 `know_issue_knowledge_base`
   - 確認知識庫已啟用（檢查開關狀態）

2. **配置系統提示詞**
```
你是一個智能測試助手，專門協助查詢 Know Issue 問題知識庫。

重要指令：
1. 當用戶詢問測試問題、錯誤、JIRA、腳本等相關問題時，你必須先搜索知識庫
2. 必須使用知識庫中的實際問題資料來回答
3. 不要提供通用的回答，要提供具體的問題編號和詳細資訊
4. 如果知識庫中沒有找到相關資料，明確說明「知識庫中沒有找到相關問題資料」

回答格式：
- 問題編號：[具體編號]
- 專案：[具體專案]
- 測試版本：[版本資訊]
- 問題類型：[具體類型]
- 錯誤訊息：[具體錯誤]
- 解決方案/補充說明：[具體說明]
```

## 🧪 測試和驗證

### API 直接測試
```bash
# 測試 API 連接
curl -X POST "http://localhost/api/dify/know-issue/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db",
    "query": "Samsung",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.3
    }
  }'
```

### Dify 召回測試
1. 進入知識庫管理 → know_issue_knowledge_base → 召回測試
2. 輸入測試查詢：
   - `Samsung` - 應該返回 Samsung 相關專案的問題
   - `NVMe` - 應該返回 NVMe 協議相關問題
   - `JIRA` - 應該返回有 JIRA 編號的問題
   - `錯誤` - 應該返回有錯誤訊息的問題

### 聊天測試問題
```
- Samsung 專案有什麼已知問題？
- NVMe Protocol 測試中遇到什麼問題？
- ULINK_NVMe_Protocol-5 這個問題的詳細資訊是什麼？
- 有哪些 FW Limit 類型的問題？
- Santize Crypto Erase 腳本有什麼問題？
```

## 📊 知識庫內容概覽

### 資料庫結構
Know Issue 知識庫包含以下主要資訊：
- **問題編號** (issue_id)
- **專案名稱** (project)
- **測試版本** (test_version)
- **JIRA 編號** (jira_number)
- **測試類別** (test_class)
- **問題類型** (issue_type)
- **狀態** (status)
- **錯誤訊息** (error_message)
- **補充說明** (supplement)
- **相關腳本** (script)
- **建立時間** (created_at)

### 範例資料
```
問題編號: ULINK_NVMe_Protocol-5
專案: Samsung_SSV5Q
測試版本: V5.0
測試類別: ULINK NVMe Protocol
JIRA編號: SVDFWV-14740
問題類型: FW Limit
狀態: N/A
錯誤訊息: Santize Crypto Erase 中 FormatNVM timeout
補充說明: Only for SSV5Q Project
相關腳本: Santize Crypto Erase
```

## 🚨 常見問題和解決方案

### 問題 1：URL 路徑重複錯誤
**症狀**：出現 `failed to connect to the endpoint: .../retrieval/retrieval` 錯誤
**原因**：Dify 會自動在配置的 endpoint 後面加上 `/retrieval`，如果配置時已包含此路徑會造成重複
**解決**：
1. ✅ **修正 API Endpoint**：使用 `http://10.10.172.127/api/dify/know-issue/`
2. ✅ **不要包含 /retrieval**：讓 Dify 自動附加路徑
3. ✅ **確保以 / 結尾**：避免路徑連接問題

### 問題 2：外部知識庫不被調用
**症狀**：AI 回答通用信息而不是具體問題資料
**解決**：
1. ✅ **檢查 Score 閾值**：建議設定在 0.3-0.5
2. ✅ **確認知識庫已啟用**：檢查上下文區域的開關狀態
3. ✅ **檢查系統提示詞**：必須包含明確的知識庫查詢指令

### 問題 3：API 連接失敗
**症狀**：出現連接錯誤
**解決**：
1. 檢查 API 端點 URL 是否正確
2. 確認網絡連接和防火牆設定
3. 測試 API 是否正常回應

### 問題 4：返回空結果
**症狀**：API 返回 `{"records":[]}`
**解決**：
1. 降低 score_threshold 到 0.3 或更低
2. 檢查搜索關鍵字是否存在於資料庫中
3. 確認資料庫中有測試資料

## 🔮 進階功能

### 多條件搜索
支援同時搜索多個欄位，系統會自動分配權重：
```json
{
    "query": "Samsung NVMe 錯誤",
    "retrieval_setting": {
        "top_k": 5,
        "score_threshold": 0.3
    }
}
```

### 結果過濾
可以通過 metadata 進行後續過濾：
- 按專案過濾：`metadata.project`
- 按問題類型過濾：`metadata.issue_type`
- 按狀態過濾：`metadata.status`

## 📝 維護指南

### 資料更新
當 Know Issue 資料庫有新增或更新時，外部知識庫會自動反映最新資料，無需額外配置。

### 效能優化
- 建議設定合適的 `top_k` 值 (3-5)
- 調整 `score_threshold` 以平衡結果數量和相關性
- 定期檢查搜索效能和結果品質

### 日誌監控
```bash
# 檢查 API 請求日誌
docker logs ai-django --tail 20 | grep "Know Issue"

# 監控搜索效能
docker logs ai-django --follow | grep "dify_know_issue"
```

## 🎯 成功標準

一個正確配置的 Dify Know Issue 外部知識庫應該滿足：

1. ✅ **API 測試成功**：curl 請求返回問題資料
2. ✅ **Dify 召回測試成功**：在知識庫管理中能看到搜索結果
3. ✅ **聊天測試成功**：AI 回答具體問題資訊而非通用描述
4. ✅ **搜索功能完整**：支援多欄位搜索和智能分數排序
5. ✅ **資料格式正確**：返回的知識片段包含完整的問題資訊

---

**建立日期**: 2025-01-14  
**版本**: v1.0  
**狀態**: ✅ 已驗證可用  
**API 端點**: `/api/dify/know-issue/retrieval/`  
**知識庫類型**: Know Issue 問題知識庫  
**負責人**: AI Platform Team