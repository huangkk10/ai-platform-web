# IOL Root 密碼搜尋問題完整分析

## 📋 問題描述

用戶查詢「iol root 密碼」時，AI 回答「找不到相關資訊」，但實際上 UNH-IOL 文檔中確實包含密碼資訊（「密碼為1」）。

## 🔍 根本原因分析

### 問題 1：`use_unified_weights = TRUE`（已修正✅）

**原始配置**：
```sql
Protocol Assistant:
- use_unified_weights: TRUE
- Stage 1: 標題 90% / 內容 10%
- Stage 2: 標題 5% / 內容 95%
```

**問題**：當 `use_unified_weights = TRUE` 時，系統強制所有階段使用 Stage1 權重，導致：
- ✅ 階段 1（段落搜尋）：使用 90% / 10% ✅ 預期
- ❌ 階段 2（全文搜尋）：也使用 90% / 10% ❌ 錯誤！

**影響**：調整 Stage1 權重時，會同時影響 Stage2 的搜尋結果排名。

**解決方案**：
```sql
UPDATE search_threshold_settings
SET use_unified_weights = FALSE
WHERE assistant_type = 'protocol_assistant';
```

### 問題 2：Auto 模式備用文檔搜尋使用錯誤的 stage（已修正✅）

**原始程式碼**：
```python
# base_search_service.py 第 207 行
results = search_with_vectors_generic(
    ...
    stage=stage  # ❌ 使用調用者傳入的 stage（預設=1）
)
```

**問題**：當 Auto 模式降級到文檔搜尋時，仍使用 `stage=1` 的權重配置（90% / 10%），而不是 `stage=2` 的配置（5% / 95%）。

**解決方案**：
```python
# 修正後
results = search_with_vectors_generic(
    ...
    stage=2  # ✅ 備用文檔搜尋應使用 stage=2
)
```

### 問題 3：段落向量品質問題（待改善⚠️）

**段落相似度排名**（查詢「iol root 密碼」）：
```
1. sec_8: 5.IOL 安裝需求 (0.847) ❌ 不包含密碼
2. sec_7: 4.IOL 版本對應 (0.837) ❌ 不包含密碼
3. sec_1: 1.IOL 執行檔路徑 (0.835) ❌ 不包含密碼
4. sec_5: 3.2 執行指令 (??.???) ✅ 包含密碼（但未進入 Top 5）
```

**問題**：
- `sec_5` 內容：「對該目錄點右鍵 → 開啟終端機... (2) 密碼為1...」
- 向量沒有很好地捕捉「密碼」這個關鍵資訊
- 標題「3.2 執行指令」與查詢「密碼」的語義距離較遠

**深層原因**：
1. **標題權重過高（90%）**：
   - 查詢「iol root 密碼」
   - 標題「3.2 執行指令」與「密碼」語義相似度低
   - 標題「5.IOL 安裝需求」反而與「iol」高度相關

2. **段落內容較短**：
   - `sec_5` 只有 186 字元
   - 向量模型難以從短文本中捕捉所有語義

3. **上下文缺失**：
   - 段落「3.2 執行指令」缺少父級上下文「3. IOL 放測 SOP」
   - 獨立段落的語義不夠完整

## 💡 解決方案

### 已實施✅

1. **關閉 `use_unified_weights`**
   - ✅ 兩階段使用獨立權重配置
   - ✅ Stage1: 90%/10% (段落標題優先)
   - ✅ Stage2: 5%/95% (全文內容優先)

2. **修正 Auto 模式備用搜尋**
   - ✅ 備用文檔搜尋自動使用 `stage=2`

### 待改善⚠️

#### 方案 A：調整階段 1 段落搜尋權重

**當前**：標題 90% / 內容 10%
**建議**：標題 70% / 內容 30%

**理由**：
- 降低標題權重，讓內容有更多影響力
- 「密碼為1」等關鍵資訊在內容中
- 仍保持標題主導（70%），快速定位段落

**風險**：
- 可能影響其他查詢的段落定位精準度
- 需要 A/B 測試驗證

#### 方案 B：增強段落向量（推薦⭐）

**策略 1：段落內容包含父級標題**
```python
# 生成段落向量時
content_for_embedding = f"{parent_heading} → {section_heading}\n{content}"
```

**效果**：
- `sec_5` 向量會包含「3. IOL 放測 SOP → 3.2 執行指令」
- 提升段落的上下文完整性

**策略 2：關鍵字提取和元數據**
```python
# 從內容中提取關鍵資訊
if re.search(r'密碼.*?[:：]?\s*(\d+|[a-zA-Z]+)', content):
    metadata['contains_password'] = True
```

#### 方案 C：改進 Auto 模式降級邏輯

**當前邏輯**：階段 1 有結果 → 直接返回

**改進邏輯**：
```python
if section_results:
    # 檢查結果質量
    top_score = section_results[0]['score']
    if top_score < 0.85:  # 質量不夠好
        logger.info("段落結果質量不足，嘗試全文搜尋")
        # 進入階段 2
    else:
        return section_results
```

**效果**：
- 低質量段落結果不會阻止全文搜尋
- 提升整體召回率

#### 方案 D：實施 Cross-Encoder Reranking

**流程**：
```
1. 階段 1：段落向量搜尋（快速，Top 20）
2. 階段 2：Cross-Encoder 重排（精準，Top 5）
3. 返回最終結果
```

**效果**：
- 15-20% 精準度提升
- 更好地理解查詢和段落的語義匹配

## 📊 測試結果對比

### 修正前
```
查詢：iol root 密碼
階段 1：找到 2 個段落結果（都不包含密碼）
階段 2：未執行（因階段 1 有結果）
AI 回答：找不到相關資訊 ❌
```

### 修正後（use_unified_weights = FALSE）
```
查詢：iol root 密碼
階段 1：找到 2 個段落結果（都不包含密碼）
階段 2：仍未執行（因階段 1 有結果）
AI 回答：找不到相關資訊 ❌（問題仍存在）
```

### 修正後（手動指定 stage=2）
```
查詢：iol root 密碼 (search_mode='document_only', stage=2)
階段 2：找到 5 個全文結果
  1. UNH-IOL (0.848) ✅ 包含密碼
  2. I3C 相關說明 (0.845)
  3. Kingston Linux (0.840)
AI 回答：可以找到密碼資訊 ✅
```

## 🎯 推薦執行順序

1. ✅ **已完成**：關閉 `use_unified_weights`，修正 Auto 模式 stage
2. ⭐ **優先推薦**：實施方案 B - 增強段落向量（包含父級標題）
3. 🔄 **次要推薦**：調整階段 1 權重到 70%/30%（需測試）
4. 🚀 **長期優化**：實施 Cross-Encoder Reranking

## 📅 更新記錄

- **2025-11-19**：初步分析，修正 `use_unified_weights` 和 Auto 模式 stage 問題
- **待續**：實施段落向量增強方案

---

**結論**：修正 `use_unified_weights` 和 Auto 模式是必要的，但要徹底解決「iol root 密碼」問題，還需要改善段落向量的品質或調整搜尋策略。
