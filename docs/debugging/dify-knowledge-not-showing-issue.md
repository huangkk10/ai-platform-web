# Dify「未使用知識庫資料」問題排查

## 問題描述
用戶查詢「iol sop 說明」時，Dify 顯示：
> 此回答基於 AI 的通用知識，未使用知識庫資料

但實際上：
- ✅ API 成功調用（日誌確認）
- ✅ 返回了 2 個完整文檔結果
- ✅ 文檔級搜尋功能正常運作

## 日誌證據

### 1. API 調用成功
```
[INFO] 2025-11-10 10:49:55,020 api.views.dify_knowledge_views: 
  🎯 [優先級 1] 使用 Dify Studio threshold=0.7 | 
  knowledge_id='protocol_guide_db' | query='iol sop 說明'

[INFO] 2025-11-10 10:49:55,108 api.views.dify_knowledge_views: 
  ✅ 知識庫搜索成功: protocol_guide_db, query='iol sop 說明', results=2
```

### 2. API 回應內容
```json
{
  "records": [
    {
      "content": "# I3C 相關說明\n\n...",
      "score": 0.8961,
      "metadata": {
        "document_id": "doc_18",
        "document_title": "I3C 相關說明",
        "is_full_document": true,
        "sections_count": 23
      }
    },
    {
      "content": "# UNH-IOL\n\n## 1. IOL 執行檔...",
      "score": 0.8961,
      "metadata": {
        "document_id": "doc_10",
        "document_title": "UNH-IOL",
        "is_full_document": true
      }
    }
  ]
}
```

## 可能原因分析

### 1️⃣ **Dify Threshold 設定問題**
- **實際分數**：0.8961（約 89.6%）
- **Dify Threshold**：0.7（70%）
- **判斷**：✅ 分數 > 閾值，應該被使用

### 2️⃣ **Dify 引用機制問題**
Dify 可能需要特定的 metadata 欄位才會標記「已使用知識庫」：

**可能缺少的欄位**：
- `title`（我們返回的是空字串 `""`）
- `url` 或 `link`
- 特定的 `source` 格式

**我們當前返回的 metadata**：
```json
{
  "source_table": "protocol_guide",
  "document_id": "doc_18",
  "document_title": "I3C 相關說明",
  "is_full_document": true,
  "sections_count": 23
}
```

### 3️⃣ **Title 欄位為空**
```json
"title": "",  // ⚠️ 空字串
```

**Dify 可能的判斷邏輯**：
- 如果 `title` 為空或不存在 → 認為沒有使用知識庫
- 或者需要 `title` 來顯示引用來源

## 🔧 解決方案

### 方案 1：修正 Title 欄位（推薦）

修改 API 回應，將 `title` 設為實際的文檔標題：

```python
# library/dify_knowledge/__init__.py 或相關處理函數

# 修改前
{
    "content": full_content,
    "score": score,
    "title": "",  # ❌ 空字串
    "metadata": {...}
}

# 修改後
{
    "content": full_content,
    "score": score,
    "title": metadata.get('document_title', ''),  # ✅ 使用實際標題
    "metadata": {...}
}
```

### 方案 2：添加 Source 欄位

Dify 可能需要 `source` 欄位來識別來源：

```python
{
    "content": full_content,
    "score": score,
    "title": document_title,
    "metadata": {
        ...existing fields...,
        "source": f"Protocol Guide - {document_title}",  # 新增
        "type": "document"  # 新增
    }
}
```

### 方案 3：調整 Dify Studio 設定

在 Dify Studio 中：
1. **降低 Score Threshold**：從 0.7 降到 0.6
2. **增加 Top K**：從 3 增加到 5
3. **檢查「引用設定」**：確認啟用知識庫引用顯示

## 🧪 測試步驟

### 步驟 1：檢查當前 API 回應格式
```bash
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "iol sop",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**檢查項目**：
- [ ] `title` 欄位是否有值
- [ ] `score` 是否 > 0.7
- [ ] `metadata` 是否完整

### 步驟 2：修改代碼（如果 title 為空）
找到負責格式化 Dify 回應的函數，修改 title 欄位。

### 步驟 3：重新測試
重啟 Django 容器後，在 Dify 中重新查詢。

## 📊 對比分析

### 成功案例（Know Issue）
如果 Know Issue 知識庫能正常顯示引用，對比其 API 回應格式：

```bash
curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db",
    "query": "Samsung",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.5}
  }' | python3 -m json.tool
```

**對比項目**：
- title 欄位格式
- metadata 結構
- score 數值範圍

## 🎯 最可能的原因

**推測：`title` 欄位為空字串導致 Dify 無法識別引用來源**

**證據**：
```json
"title": "",  // ⚠️ 當前返回的是空字串
```

**建議修正**：
```json
"title": "UNH-IOL",  // ✅ 應該返回實際的文檔標題
```

## 📝 待辦事項

- [ ] 找到格式化 Dify 回應的代碼位置
- [ ] 修改 `title` 欄位從 metadata 中提取
- [ ] 測試修改後的效果
- [ ] 確認 Dify 是否顯示「已使用知識庫」
- [ ] 更新文檔記錄解決方案

---

**更新日期**：2025-11-10  
**狀態**：待修正  
**優先級**：高
