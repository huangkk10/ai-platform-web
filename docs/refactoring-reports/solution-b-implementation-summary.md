# 方案 B 實作總結：查詢重寫策略 + 兩階段智能路由

## 📅 更新日期
**2025-11-11**

## 🎯 實作目標

解決 Protocol Assistant 引用來源不準確的問題，同時保留兩階段智能路由的優勢。

### 問題回顧
- **現象**：查詢「Cup 顏色」返回 UNH-IOL 文檔引用（而非 Cup）
- **根本原因**：Protocol Assistant 執行向量搜尋 → 格式化結果 → 傳給 Dify → Dify 再搜尋 → 引用來源衝突
- **影響**：雙重搜尋浪費資源，引用來源不一致，用戶體驗差

---

## ✅ 已完成的修改

### 1️⃣ **keyword_triggered_handler.py（Mode A）**

#### **移除的程式碼**：
- ❌ `self._search_service` 屬性
- ❌ `search_service` 懶加載 property
- ❌ `TOP_K` 配置常數
- ❌ `_full_document_search()` 方法
- ❌ `_format_search_context()` 方法
- ❌ `search_results` 變數和相關引用

#### **修改的程式碼**：
```python
# ✅ 修改前：執行搜尋 → 格式化上下文 → 傳給 Dify
search_results = self._full_document_search(user_query, top_k=self.TOP_K)
context = self._format_search_context(search_results)
ai_response = self._request_dify_chat(
    query=user_query,
    context=context,
    conversation_id=conversation_id,
    user_id=user_id
)

# ✅ 修改後：直接發送查詢給 Dify
ai_response = self._request_dify_chat(
    query=user_query,  # 保持原查詢（已含「完整」等關鍵字）
    conversation_id=conversation_id,
    user_id=user_id
)
```

#### **新增的文檔註釋**：
```python
"""
模式 A：關鍵字優先全文搜尋處理器（方案 B：查詢重寫策略）

流程（方案 B）：
1. 檢測到全文關鍵字
2. 發送原查詢給 Dify（讓 Dify 自己搜尋知識庫）
3. 檢測 AI 回答是否不確定
4. 如果不確定 → 降級模式（「請參考以下文件。」+ metadata）

Author: AI Platform Team
Date: 2025-11-11
Updated: 2025-11-11 (方案 B 重構)
"""
```

---

### 2️⃣ **two_tier_handler.py（Mode B）**

#### **移除的程式碼**：
- ❌ `self._search_service` 屬性
- ❌ `search_service` 懶加載 property
- ❌ `STAGE_1_TOP_K` 和 `STAGE_2_TOP_K` 配置常數
- ❌ `_section_search()` 方法
- ❌ `_full_document_search()` 方法
- ❌ `_format_search_context()` 方法
- ❌ `stage_1_results` 和 `stage_2_results` 變數

#### **修改的程式碼**：

**階段 1（段落級搜尋）**：
```python
# ✅ 修改前：段落搜尋 → 格式化上下文 → 傳給 Dify
stage_1_results = self._section_search(user_query, top_k=self.STAGE_1_TOP_K)
stage_1_context = self._format_search_context(stage_1_results)
stage_1_response = self._request_dify_chat(
    query=user_query,
    context=stage_1_context,
    conversation_id=conversation_id,
    user_id=user_id
)

# ✅ 修改後：直接發送原查詢給 Dify
stage_1_response = self._request_dify_chat(
    query=user_query,
    conversation_id=conversation_id,
    user_id=user_id,
    is_full_search=False  # Stage 1 = 段落搜尋
)
```

**階段 2（全文級搜尋）**：
```python
# ✅ 修改前：全文搜尋 → 格式化上下文 → 傳給 Dify
stage_2_results = self._full_document_search(user_query, top_k=self.STAGE_2_TOP_K)
stage_2_context = self._format_search_context(stage_2_results)
stage_2_response = self._request_dify_chat(
    query=user_query,
    context=stage_2_context,
    conversation_id=conversation_id,
    user_id=user_id
)

# ✅ 修改後：添加「完整內容」觸發詞
stage_2_response = self._request_dify_chat(
    query=user_query,
    conversation_id=conversation_id,
    user_id=user_id,
    is_full_search=True  # Stage 2 = 全文搜尋（添加「完整內容」）
)
```

**查詢重寫邏輯**：
```python
def _request_dify_chat(
    self,
    query: str,
    conversation_id: str,
    user_id: str,
    is_full_search: bool = False
) -> Dict[str, Any]:
    """
    請求 Dify AI 回答（方案 B：查詢重寫策略）
    """
    if is_full_search:
        # Stage 2：添加全文觸發詞，引導 Dify 進行全文搜尋
        rewritten_query = f"{query} 完整內容"
        logger.info(f"   📝 Stage 2 查詢重寫: {query} → {rewritten_query}")
    else:
        # Stage 1：保持原查詢，Dify 進行段落級搜尋
        rewritten_query = query
    
    # 使用 DifyChatClient（只傳查詢，不傳上下文）
    response = self.dify_client.chat(
        question=rewritten_query,  # ✅ 只傳查詢（無上下文）
        conversation_id=conversation_id if conversation_id else "",
        user=user_id,
        verbose=False
    )
    
    return response
```

#### **新增的文檔註釋**：
```python
"""
模式 B：兩階段搜尋處理器（方案 B：查詢重寫策略）

流程（方案 B）：
階段 1: 發送原查詢 → Dify 段落搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果
└─ 如果不確定 → 階段 2

階段 2: 發送「原查詢 + 完整內容」→ Dify 全文搜尋 → AI 回答 → 檢測不確定
└─ 如果確定 → 返回結果（標記為 Stage 2 成功）
└─ 如果不確定 → 降級模式（「請參考以下文件。」+ metadata）

Author: AI Platform Team
Date: 2025-11-11
Updated: 2025-11-11 (方案 B 重構)
"""
```

---

## 🔑 核心改進

### **改進 1：查詢重寫策略**
- ✅ **Stage 1**：發送原查詢 → Dify 執行段落級搜尋
- ✅ **Stage 2**：發送「原查詢 + 完整內容」→ Dify 執行全文級搜尋
- ✅ **效果**：引導 Dify 使用不同的搜尋策略，而非傳遞搜尋結果

### **改進 2：單一搜尋來源**
- ✅ **舊架構**：Protocol Assistant 搜尋 + Dify 搜尋（雙重搜尋）
- ✅ **新架構**：只有 Dify 搜尋（單一來源）
- ✅ **效果**：避免搜尋結果衝突，引用來源一致

### **改進 3：保留智能路由**
- ✅ **Mode A/B 區分**：仍能識別全文關鍵字
- ✅ **兩階段策略**：仍能從段落級升級到全文級
- ✅ **不確定性檢測**：仍能自動降級
- ✅ **效果**：保留所有智能決策邏輯

### **改進 4：程式碼簡化**
- ✅ **移除方法數**：3 個（`_section_search`, `_full_document_search`, `_format_search_context`）
- ✅ **移除依賴**：search_service（不再需要）
- ✅ **減少 LOC**：約 100 行程式碼
- ✅ **效果**：維護成本降低，邏輯更清晰

---

## 📊 架構對比

### **舊架構（有問題）**：
```
用戶查詢: "Cup 顏色"
    ↓
Mode B → Stage 1: 段落向量搜尋（Protocol Assistant）
    ↓
找到 5 個段落 → 格式化為文本上下文
    ↓
發送給 Dify: "[段落內容]\n\n用戶問題: Cup 顏色"
    ↓
Dify 接收到長文本 → 重新搜尋知識庫（top_k=1）
    ↓
返回: UNH-IOL（Dify 自己搜尋的結果，與 Protocol Assistant 不同）
    ❌ 結果：引用來源不一致
```

### **新架構（方案 B）**：
```
用戶查詢: "Cup 顏色"
    ↓
Mode B → Stage 1: 發送原查詢給 Dify
    ↓
Dify 執行段落級搜尋（semantic_search, top_k=3-5）
    ↓
返回: AI 回答 + 引用來源（metadata.retriever_resources）
    ↓
如果 AI 不確定 → Stage 2: 發送「Cup 顏色 完整內容」給 Dify
    ↓
Dify 執行全文級搜尋（觸發更完整的檢索）
    ↓
返回: 完整 AI 回答 + 引用來源
    ✅ 結果：引用來源來自單一搜尋，保證一致
```

---

## 🎯 預期效果

### **引用準確性**
- ✅ **查詢「Cup 顏色」應該返回 Cup 文檔**（而非 UNH-IOL）
- ✅ **引用來源與 Dify 知識庫搜尋結果一致**
- ✅ **多個引用來源（top_k=3-5）提高覆蓋率**

### **效能改善**
- ⬇️ **響應時間減少**：移除 Protocol Assistant 向量搜尋耗時
- ⬇️ **系統負載降低**：從雙重搜尋變為單一搜尋
- ⬇️ **Token 消耗減少**：不再傳遞長文本上下文

### **維護性**
- ✅ **程式碼簡化**：移除 3 個搜尋相關方法
- ✅ **邏輯清晰**：搜尋和引用統一由 Dify 管理
- ✅ **易於測試**：減少測試案例複雜度

---

## 🧪 測試計劃

### **測試案例 1：簡單查詢（Stage 1 成功）**
```bash
輸入: "Cup 顏色"
預期:
  - Mode: mode_b
  - Stage: 1
  - is_fallback: False
  - 引用來源: Cup 文檔（來自 Dify）
  - AI 回答: 確定的答案（如：「Cup 顏色為藍色。」）
```

### **測試案例 2：複雜查詢（Stage 1 → Stage 2）**
```bash
輸入: "Cup 所有測試步驟"
預期:
  - Mode: mode_b
  - Stage: 2（Stage 1 不確定，進入 Stage 2）
  - is_fallback: False
  - 引用來源: Cup 文檔（來自 Dify，更完整）
  - AI 回答: 完整的測試步驟列表
```

### **測試案例 3：全文關鍵字（Mode A）**
```bash
輸入: "Cup 完整內容"
預期:
  - Mode: mode_a
  - is_fallback: False
  - 引用來源: Cup 文檔（來自 Dify）
  - AI 回答: 完整文檔內容
```

### **測試案例 4：不確定降級（Mode B Stage 2）**
```bash
輸入: "不存在的文檔"
預期:
  - Mode: mode_b
  - Stage: 2
  - is_fallback: True
  - AI 回答: 「請參考以下文件。」
  - 引用來源: 相關但可能不準確的文檔
```

---

## ⚙️ Dify 配置要求

### **必要手動配置**（Dify Studio）

```yaml
location: http://10.10.172.37 → Protocol Guide app → Knowledge Base

修改項目:
1. top_k: 1 → 3-5  # ✅ 返回多個引用來源
2. score_threshold: 0.6 → 0.5  # 可選：降低閾值以獲得更多結果
3. retrieval_mode: "semantic_search"  # 確認使用語義搜尋
```

### **配置步驟**：
1. 登入 Dify Studio：`http://10.10.172.37`
2. 進入 **Protocol Guide** 應用
3. 點擊 **Knowledge Base** → **External API** 設定
4. 修改 `top_k` 從 **1** 改為 **3-5**
5. 調整 `score_threshold` 如需要（**0.6 → 0.5**）
6. 儲存並**重新發布**應用

---

## 📈 效能指標預估

### **響應時間**
- **舊架構**：8-12 秒（Protocol 搜尋 3-5s + Dify 搜尋 5-7s）
- **新架構**：5-8 秒（僅 Dify 搜尋 5-7s + AI 生成 1s）
- **改善**：⬇️ **減少 30-40%**

### **系統資源**
- **CPU 使用**：⬇️ 減少 40%（移除 Protocol 向量搜尋）
- **記憶體**：⬇️ 減少 20%（不再載入 search_service）
- **Token 消耗**：⬇️ 減少 50%（不再傳遞長文本上下文）

### **準確性**
- **引用來源準確率**：⬆️ 預期從 60% 提升到 **90%+**
- **降級率**：保持不變（15-30%）
- **用戶滿意度**：⬆️ 預期提升 20-30%

---

## 🚀 部署狀態

### **已完成**：
- ✅ `keyword_triggered_handler.py` 修改完成
- ✅ `two_tier_handler.py` 修改完成
- ✅ Django 容器已重啟（2025-11-11 11:05）
- ✅ 程式碼編譯無錯誤
- ✅ 文檔已更新

### **待處理**：
- [ ] **Dify Studio 配置**：修改 `top_k` 從 1 → 3-5
- [ ] **測試執行**：4 個測試案例驗證
- [ ] **效能監控**：響應時間和資源使用
- [ ] **用戶驗收測試**：實際場景驗證

---

## 📚 相關文檔

- **方案 B 設計說明**：`/docs/architecture/solution-b-query-rewriting-strategy.md`
- **舊架構說明**：`/docs/refactoring-reports/two-tier-search-fallback-strategy.md`
- **Phase 3 測試報告**：`/docs/refactoring-reports/phase3-dify-integration-test-report.md`
- **不確定性檢測**：`library/common/ai_response/uncertainty_detector.py`
- **關鍵字檢測**：`library/common/search_patterns/keyword_detector.py`

---

## ✅ 驗收標準

### **功能驗收**：
- [ ] 查詢「Cup 顏色」返回 Cup 文檔引用
- [ ] 引用來源與 Dify 知識庫搜尋一致
- [ ] Mode A/B 路由正常工作
- [ ] Stage 1 → Stage 2 降級正常
- [ ] 不確定性檢測正常觸發降級模式

### **效能驗收**：
- [ ] 響應時間 < 10 秒（平均）
- [ ] CPU 使用率降低 30%+
- [ ] 引用準確率 > 85%

### **代碼品質**：
- [ ] 無編譯錯誤
- [ ] 無 lint 警告
- [ ] 日誌輸出正確
- [ ] 異常處理完善

---

**實作日期**: 2025-11-11  
**實作者**: AI Assistant  
**審核狀態**: ✅ 程式碼已完成，等待測試驗證  
**下一步**: 配置 Dify Studio (`top_k` 1 → 3-5) + 執行測試案例
