# 🔍 搜尋系統優化建議

## 📊 當前系統狀態

### ✅ 已完成的功能
1. **空內容段落展開** - 自動展開章節標題的子段落
2. **多向量搜尋** - 標題向量 60% + 內容向量 40%
3. **V2 上下文視窗** - 完整實現 adjacent/hierarchical/both 三種模式
4. **動態權重配置** - 從資料庫讀取不同 Assistant 的權重設定

---

## 🎯 建議優化項目

### 優化 1：混合搜尋（Hybrid Search）⭐⭐⭐⭐⭐
**優先級**：🔥 高

#### 問題分析
當前純向量搜尋可能遺漏：
- 精確詞彙匹配（如產品型號、專有名詞）
- 縮寫和全名的對應（IOL vs UNH-IOL）
- 同義詞和變體

**範例**：
```
查詢: "IOL 是什麼"
純向量結果: 可能只有 65% 相似度（低於閾值 70%）❌
混合搜尋: 向量 65% + 關鍵字匹配 "IOL" = 提升到 75% ✅
```

#### 實作方案

```python
def hybrid_search_sections(
    self,
    query: str,
    source_table: str,
    limit: int = 5,
    threshold: float = 0.7,
    keyword_boost: float = 0.15  # 關鍵字匹配加成
) -> List[Dict[str, Any]]:
    """
    混合搜尋：向量相似度 + 關鍵字匹配
    
    評分公式：
    final_score = vector_similarity + (keyword_boost if keyword_match else 0)
    """
    
    # 1. 向量搜尋（現有邏輯）
    vector_results = self.search_sections(query, source_table, limit=limit*2, threshold=0.6)
    
    # 2. 關鍵字匹配檢測
    query_keywords = set(query.lower().split())
    
    for result in vector_results:
        # 檢查標題和內容中的關鍵字
        text = f"{result['heading_text']} {result['content']}".lower()
        
        # 精確匹配加成
        exact_matches = sum(1 for kw in query_keywords if kw in text)
        match_ratio = exact_matches / len(query_keywords)
        
        # 加成分數
        keyword_score = keyword_boost * match_ratio
        result['original_similarity'] = result['similarity']
        result['keyword_score'] = keyword_score
        result['similarity'] = min(1.0, result['similarity'] + keyword_score)
    
    # 3. 重新排序和過濾
    vector_results.sort(key=lambda x: x['similarity'], reverse=True)
    final_results = [r for r in vector_results if r['similarity'] >= threshold]
    
    return final_results[:limit]
```

**預期效果**：
- ✅ 提升 10-15% 的召回率
- ✅ 更好處理專有名詞、型號、縮寫
- ✅ 降低遺漏高相關結果的機率

**工作量**：2-3 小時

---

### 優化 2：搜尋結果重排序（Reranking）⭐⭐⭐⭐
**優先級**：中高

#### 問題分析
當前排序僅基於相似度分數，未考慮：
- 段落長度（過短或過長的段落品質可能較低）
- 內容品質（是否有程式碼、圖片、範例）
- 文檔新鮮度（最近更新的可能更準確）

#### 實作方案

```python
def rerank_results(
    self,
    results: List[Dict],
    query: str,
    weights: Dict[str, float] = None
) -> List[Dict]:
    """
    結果重排序：綜合多個因素
    
    評分因素：
    - similarity: 向量相似度（60%）
    - content_quality: 內容品質（20%）
    - length_score: 長度適中性（10%）
    - freshness: 新鮮度（10%）
    """
    if weights is None:
        weights = {
            'similarity': 0.6,
            'content_quality': 0.2,
            'length_score': 0.1,
            'freshness': 0.1
        }
    
    for result in results:
        # 內容品質分數
        quality_score = 0
        if result.get('has_code'):
            quality_score += 0.3
        if result.get('has_images'):
            quality_score += 0.2
        if result.get('word_count', 0) > 50:
            quality_score += 0.3
        quality_score = min(1.0, quality_score)
        
        # 長度適中性（50-500 字最理想）
        word_count = result.get('word_count', 0)
        if 50 <= word_count <= 500:
            length_score = 1.0
        elif word_count < 50:
            length_score = word_count / 50
        else:
            length_score = max(0.5, 1.0 - (word_count - 500) / 1000)
        
        # 綜合評分
        final_score = (
            weights['similarity'] * result['similarity'] +
            weights['content_quality'] * quality_score +
            weights['length_score'] * length_score
        )
        
        result['rerank_score'] = final_score
        result['quality_breakdown'] = {
            'similarity': result['similarity'],
            'content_quality': quality_score,
            'length_score': length_score
        }
    
    # 按新分數排序
    results.sort(key=lambda x: x['rerank_score'], reverse=True)
    return results
```

**預期效果**：
- ✅ 提升結果的整體品質
- ✅ 更準確地排序同等相似度的結果
- ✅ 優先顯示內容豐富的段落

**工作量**：2-3 小時

---

### 優化 3：智能閾值調整⭐⭐⭐
**優先級**：中

#### 問題分析
當前使用固定閾值（0.7），可能導致：
- 熱門問題：找到大量結果（> 10 個）
- 冷門問題：找不到任何結果（0 個）

#### 實作方案

```python
def adaptive_threshold_search(
    self,
    query: str,
    source_table: str,
    limit: int = 5,
    min_threshold: float = 0.5,
    max_threshold: float = 0.8,
    target_count: int = 3
) -> List[Dict]:
    """
    自適應閾值搜尋：動態調整閾值確保合理的結果數量
    
    策略：
    1. 從 max_threshold 開始搜尋
    2. 如果結果 < target_count，降低閾值重試
    3. 最多降低到 min_threshold
    """
    threshold = max_threshold
    step = 0.05
    
    while threshold >= min_threshold:
        results = self.search_sections(
            query, source_table, 
            limit=limit, threshold=threshold
        )
        
        if len(results) >= target_count:
            logger.info(f"✅ 自適應閾值: {threshold:.2f} -> {len(results)} 個結果")
            return results
        
        threshold -= step
    
    # 最終降到最低閾值
    results = self.search_sections(
        query, source_table, 
        limit=limit, threshold=min_threshold
    )
    logger.warning(f"⚠️ 使用最低閾值 {min_threshold} -> {len(results)} 個結果")
    return results
```

**預期效果**：
- ✅ 確保每次搜尋都有合理數量的結果
- ✅ 降低「找不到任何結果」的機率
- ✅ 動態平衡精確度和召回率

**工作量**：1-2 小時

---

### 優化 4：查詢擴展（Query Expansion）⭐⭐⭐
**優先級**：中

#### 問題分析
用戶輸入可能：
- 過於簡短（"IOL"）
- 使用縮寫（"NVMe" 而非 "Non-Volatile Memory Express"）
- 缺少關鍵上下文

#### 實作方案

```python
def expand_query(self, query: str, source_table: str) -> str:
    """
    查詢擴展：補充同義詞和相關詞彙
    
    方法：
    1. 縮寫擴展（IOL -> UNH-IOL, Interoperability Lab）
    2. 同義詞添加（測試 -> 驗證, test）
    3. 領域詞彙（從知識庫學習）
    """
    # 縮寫對照表（可從配置讀取）
    abbreviations = {
        'IOL': 'UNH-IOL Interoperability Lab',
        'NVMe': 'NVMe Non-Volatile Memory Express',
        'SOP': 'SOP Standard Operating Procedure',
    }
    
    expanded_terms = [query]
    
    # 檢查是否包含已知縮寫
    for abbr, full in abbreviations.items():
        if abbr in query:
            expanded_terms.append(query.replace(abbr, full))
    
    # 組合擴展查詢
    expanded_query = ' '.join(expanded_terms)
    
    logger.info(f"🔍 查詢擴展: '{query}' -> '{expanded_query}'")
    return expanded_query
```

**預期效果**：
- ✅ 提升短查詢的搜尋效果
- ✅ 更好處理縮寫和專有名詞
- ✅ 增加 5-10% 召回率

**工作量**：2-3 小時

---

### 優化 5：搜尋分析和日誌⭐⭐
**優先級**：低

#### 功能
記錄搜尋查詢和結果，用於分析和優化：

```python
class SearchAnalytics(models.Model):
    """搜尋分析記錄"""
    query = models.TextField()
    source_table = models.CharField(max_length=50)
    result_count = models.IntegerField()
    top_similarity = models.FloatField()
    search_version = models.CharField(max_length=10)
    user_id = models.IntegerField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

**用途**：
- 分析常見查詢
- 發現搜尋盲點
- 評估不同版本效果
- 優化閾值設定

**工作量**：3-4 小時

---

## 📊 優化優先級總結

| 優化項目 | 優先級 | 預期提升 | 工作量 | 實作難度 |
|---------|-------|---------|--------|---------|
| 1. 混合搜尋 | 🔥🔥🔥🔥🔥 | 召回率 +15% | 2-3h | 中 |
| 2. 結果重排序 | 🔥🔥🔥🔥 | 結果品質 +20% | 2-3h | 中 |
| 3. 自適應閾值 | 🔥🔥🔥 | 用戶體驗 +10% | 1-2h | 簡單 |
| 4. 查詢擴展 | 🔥🔥🔥 | 召回率 +10% | 2-3h | 中 |
| 5. 搜尋分析 | 🔥🔥 | 長期優化價值 | 3-4h | 簡單 |

---

## 🎯 建議實施順序

### Phase 1（本週）：快速見效
1. **自適應閾值** - 1-2 小時，立即改善用戶體驗
2. **混合搜尋** - 2-3 小時，顯著提升準確度

### Phase 2（下週）：深度優化
3. **結果重排序** - 2-3 小時，提升結果品質
4. **查詢擴展** - 2-3 小時，處理縮寫和同義詞

### Phase 3（未來）：數據驅動
5. **搜尋分析** - 3-4 小時，建立長期優化基礎

---

## 💡 快速測試建議

### 測試案例 1：專有名詞
```python
# 當前可能表現不佳
queries = [
    "IOL 是什麼",           # 過於簡短
    "UNH 測試流程",         # 縮寫
    "NVMe SPEC 版本",       # 專有名詞
]

# 優化後應該能找到
expected = [
    "UNH-IOL 文檔",
    "IOL 放測 SOP",
    "IOL 版本對應 NVMe SPEC",
]
```

### 測試案例 2：長尾查詢
```python
# 當前可能找不到結果（< 0.7 閾值）
queries = [
    "如何安裝",             # 過於通用
    "常見問題",             # 過於通用
    "需要注意什麼",         # 問句形式
]

# 自適應閾值應該能找到相關段落
```

---

## 📚 相關文檔

- **V2 上下文視窗狀態**：`/docs/features/V2_CONTEXT_WINDOW_STATUS.md`
- **向量搜尋指南**：`/docs/vector-search/vector-search-guide.md`
- **搜尋配置說明**：`/docs/development/search-configuration.md`

---

**更新日期**：2025-11-09  
**版本**：v1.0  
**狀態**：✅ 當前系統已完善，建議優化方向明確  
**下一步**：選擇 1-2 個高優先級項目開始實施
