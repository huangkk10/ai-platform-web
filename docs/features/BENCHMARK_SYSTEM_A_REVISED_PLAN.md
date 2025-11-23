# 系統 A：搜尋引擎 Benchmark 重新規劃

## 🎯 核心洞察

**關鍵發現**：「二階段搜尋」不應該作為獨立演算法驗證，因為：

1. **Stage 參數是配合 AI 回應的**：`stage=1` 和 `stage=2` 是用來告訴 Dify 目前在哪個搜尋階段，讓 AI 可以根據不同階段調整回答策略
2. **真正可變的是搜尋策略**：段落向量、全文向量、搜尋模式、權重配置
3. **AI 回應不在系統 A 範圍**：系統 A 只測試「檢索質量」，不測試「AI 回答質量」

因此，**應該拆解成獨立的可測試單元**：

---

## 📊 重新定義：系統 A 測試的演算法單元

### 演算法維度拆解

```
系統 A 測試對象：純檢索策略（不涉及 AI）
│
├── 維度 1：搜尋來源（Search Source）
│   ├── 段落向量（Section Vectors）
│   │   - 表：section_multi_vectors
│   │   - 特性：精準、片段化
│   │   - 搜尋範圍：章節級內容
│   │
│   ├── 全文向量（Document Vectors）
│   │   - 表：document_embeddings
│   │   - 特性：全面、完整文檔
│   │   - 搜尋範圍：整篇文檔
│   │
│   └── 關鍵字（Keyword Search）
│       - 表：protocol_guide (ILIKE)
│       - 特性：傳統、精確匹配
│       - 搜尋範圍：標題+內容
│
├── 維度 2：搜尋模式（Search Mode）
│   ├── 'section_only' - 只用段落向量
│   ├── 'document_only' - 只用全文向量
│   ├── 'auto' - 段落優先，允許降級
│   └── 'hybrid' - 段落+全文混合
│
├── 維度 3：閾值配置（Threshold）
│   ├── 高精準（0.75-0.85）
│   ├── 平衡（0.65-0.75）
│   └── 高召回（0.50-0.65）
│
└── 維度 4：混合權重（Hybrid Weights）⚠️ 新增
    ├── section_weight - 段落結果權重（0.0-1.0）
    ├── document_weight - 全文結果權重（0.0-1.0）
    └── keyword_weight - 關鍵字結果權重（0.0-1.0）
```

---

## 🎨 演算法版本設計範例

### 版本 1：純段落向量（高精準）

```python
{
    "version_name": "段落向量 - 高精準",
    "algorithm_type": "section_vector_only",
    "parameters": {
        "search_mode": "section_only",
        "section_threshold": 0.80,
        "use_document_fallback": False,
        "use_keyword_fallback": False
    },
    "description": "只使用段落向量搜尋，高閾值，適合精確查詢"
}
```

**預期特性**：
- ✅ Precision 高（精準度 > 85%）
- ❌ Recall 可能較低（召回率 60-70%）
- ✅ Response Time 快（< 300ms）

---

### 版本 2：純全文向量（高召回）

```python
{
    "version_name": "全文向量 - 高召回",
    "algorithm_type": "document_vector_only",
    "parameters": {
        "search_mode": "document_only",
        "document_threshold": 0.60,
        "use_section_search": False,
        "use_keyword_fallback": False
    },
    "description": "只使用整篇文檔向量搜尋，低閾值，適合廣泛查詢"
}
```

**預期特性**：
- ❌ Precision 中等（精準度 70-80%）
- ✅ Recall 高（召回率 > 85%）
- ✅ Response Time 快（< 400ms）

---

### 版本 3：混合向量（段落 70% + 全文 30%）⚠️ 新設計

```python
{
    "version_name": "混合向量 - 段落優先",
    "algorithm_type": "hybrid_vector",
    "parameters": {
        "search_mode": "hybrid",
        "section_threshold": 0.75,
        "document_threshold": 0.65,
        "section_weight": 0.7,    # ⚠️ 段落結果權重 70%
        "document_weight": 0.3,   # ⚠️ 全文結果權重 30%
        "hybrid_merge_strategy": "weighted_score"
    },
    "description": "段落向量 70% + 全文向量 30% 混合，平衡精準度與召回率"
}
```

**預期特性**：
- ✅ Precision 高（精準度 80-85%）
- ✅ Recall 高（召回率 80-85%）
- ✅ F1 Score 最高（> 82%）

---

### 版本 4：混合向量（段落 50% + 全文 50%）

```python
{
    "version_name": "混合向量 - 平衡",
    "algorithm_type": "hybrid_vector",
    "parameters": {
        "search_mode": "hybrid",
        "section_threshold": 0.70,
        "document_threshold": 0.70,
        "section_weight": 0.5,    # ⚠️ 段落結果權重 50%
        "document_weight": 0.5,   # ⚠️ 全文結果權重 50%
        "hybrid_merge_strategy": "weighted_score"
    },
    "description": "段落向量與全文向量平衡混合"
}
```

---

### 版本 5：三層混合（段落 + 全文 + 關鍵字）

```python
{
    "version_name": "三層混合 - 完整覆蓋",
    "algorithm_type": "three_layer_hybrid",
    "parameters": {
        "search_mode": "auto",
        "section_threshold": 0.75,
        "document_threshold": 0.65,
        "keyword_threshold": 0.35,
        "section_weight": 0.5,     # 段落 50%
        "document_weight": 0.3,    # 全文 30%
        "keyword_weight": 0.2,     # 關鍵字 20%
        "hybrid_merge_strategy": "weighted_score"
    },
    "description": "段落向量 + 全文向量 + 關鍵字補充，最大化召回率"
}
```

**預期特性**：
- ✅ Recall 極高（召回率 > 90%）
- ❌ Precision 可能降低（精準度 75-80%）
- ⏱️ Response Time 較慢（< 600ms）

---

## 🔧 技術實現：混合權重引擎

### 新功能：Weighted Hybrid Search

```python
# library/common/knowledge_base/hybrid_search_engine.py

class HybridSearchEngine:
    """
    混合搜尋引擎
    
    支援多來源搜尋結果的加權合併
    """
    
    @staticmethod
    def weighted_merge(
        section_results: list,
        document_results: list,
        keyword_results: list,
        section_weight: float = 0.5,
        document_weight: float = 0.3,
        keyword_weight: float = 0.2,
        limit: int = 10
    ) -> list:
        """
        加權合併多來源搜尋結果
        
        策略：
        1. 對每個來源的結果按權重調整 score
        2. 合併所有結果
        3. 按調整後的 score 排序
        4. 去重（保留最高 score）
        5. 返回 Top-K
        
        Args:
            section_results: 段落搜尋結果 [{'id': 1, 'score': 0.85, ...}, ...]
            document_results: 全文搜尋結果
            keyword_results: 關鍵字搜尋結果
            section_weight: 段落權重（預設 0.5）
            document_weight: 全文權重（預設 0.3）
            keyword_weight: 關鍵字權重（預設 0.2）
            limit: 返回結果數量
            
        Returns:
            加權合併後的結果列表
        """
        merged_results = {}  # {doc_id: {'score': weighted_score, 'data': {...}}}
        
        # 1. 處理段落搜尋結果
        for result in section_results:
            doc_id = result.get('metadata', {}).get('id') or result.get('id')
            original_score = result.get('score', 0.0)
            weighted_score = original_score * section_weight
            
            if doc_id not in merged_results or weighted_score > merged_results[doc_id]['score']:
                merged_results[doc_id] = {
                    'score': weighted_score,
                    'original_score': original_score,
                    'source': 'section',
                    'weight': section_weight,
                    'data': result
                }
        
        # 2. 處理全文搜尋結果
        for result in document_results:
            doc_id = result.get('metadata', {}).get('id') or result.get('id')
            original_score = result.get('score', 0.0)
            weighted_score = original_score * document_weight
            
            if doc_id not in merged_results:
                merged_results[doc_id] = {
                    'score': weighted_score,
                    'original_score': original_score,
                    'source': 'document',
                    'weight': document_weight,
                    'data': result
                }
            else:
                # 累加分數（如果來自不同來源）
                merged_results[doc_id]['score'] += weighted_score
                merged_results[doc_id]['source'] = 'hybrid'
        
        # 3. 處理關鍵字搜尋結果
        for result in keyword_results:
            doc_id = result.get('metadata', {}).get('id') or result.get('id')
            original_score = result.get('score', 0.0)
            weighted_score = original_score * keyword_weight
            
            if doc_id not in merged_results:
                merged_results[doc_id] = {
                    'score': weighted_score,
                    'original_score': original_score,
                    'source': 'keyword',
                    'weight': keyword_weight,
                    'data': result
                }
            else:
                merged_results[doc_id]['score'] += weighted_score
                merged_results[doc_id]['source'] = 'hybrid'
        
        # 4. 排序並返回 Top-K
        sorted_results = sorted(
            merged_results.values(), 
            key=lambda x: x['score'], 
            reverse=True
        )[:limit]
        
        # 5. 格式化輸出（保留原始結構 + 加入混合資訊）
        final_results = []
        for item in sorted_results:
            result = item['data'].copy()
            result['hybrid_score'] = item['score']
            result['original_score'] = item['original_score']
            result['source'] = item['source']
            result['weight_applied'] = item['weight']
            final_results.append(result)
        
        return final_results
```

---

### 更新：BaseKnowledgeBaseSearchService

```python
# backend/library/common/knowledge_base/base_search_service.py

def search_knowledge_with_hybrid_weights(
    self, 
    query: str, 
    limit: int = 5, 
    search_mode: str = 'auto',
    section_threshold: float = 0.7,
    document_threshold: float = 0.65,
    keyword_threshold: float = 0.35,
    section_weight: float = 0.5,
    document_weight: float = 0.3,
    keyword_weight: float = 0.2
) -> list:
    """
    使用混合權重的知識庫搜尋（新方法）
    
    ⚠️ 與 search_knowledge() 的差異：
    - search_knowledge(): 串聯式（段落 → 降級 → 全文 → 補充 → 關鍵字）
    - search_knowledge_with_hybrid_weights(): 並聯式（同時搜尋 → 加權合併）
    
    Args:
        query: 查詢字串
        limit: 返回結果數量
        search_mode: 搜尋模式
            - 'section_only': 只段落
            - 'document_only': 只全文
            - 'hybrid': 段落+全文混合
            - 'three_layer': 段落+全文+關鍵字
        section_threshold: 段落搜尋閾值
        document_threshold: 全文搜尋閾值
        keyword_threshold: 關鍵字搜尋閾值
        section_weight: 段落結果權重（0.0-1.0）
        document_weight: 全文結果權重（0.0-1.0）
        keyword_weight: 關鍵字結果權重（0.0-1.0）
    
    Returns:
        加權混合後的搜尋結果
    """
    from .hybrid_search_engine import HybridSearchEngine
    
    section_results = []
    document_results = []
    keyword_results = []
    
    # 1. 根據 search_mode 執行對應的搜尋
    if search_mode == 'section_only':
        section_results = self.search_with_vectors(
            query, limit, section_threshold, 'section_only', stage=1
        )
    
    elif search_mode == 'document_only':
        document_results = self.search_with_vectors(
            query, limit, document_threshold, 'document_only', stage=2
        )
    
    elif search_mode == 'hybrid':
        # 同時搜尋段落和全文
        section_results = self.search_with_vectors(
            query, limit, section_threshold, 'section_only', stage=1
        )
        document_results = self.search_with_vectors(
            query, limit, document_threshold, 'document_only', stage=2
        )
    
    elif search_mode == 'three_layer':
        # 搜尋所有三層
        section_results = self.search_with_vectors(
            query, limit, section_threshold, 'section_only', stage=1
        )
        document_results = self.search_with_vectors(
            query, limit, document_threshold, 'document_only', stage=2
        )
        keyword_results = self.search_with_keywords(
            query, limit, keyword_threshold
        )
    
    # 2. 加權合併
    merged_results = HybridSearchEngine.weighted_merge(
        section_results=section_results,
        document_results=document_results,
        keyword_results=keyword_results,
        section_weight=section_weight,
        document_weight=document_weight,
        keyword_weight=keyword_weight,
        limit=limit
    )
    
    self.logger.info(
        f"🔀 混合搜尋完成: "
        f"段落 {len(section_results)}×{section_weight} + "
        f"全文 {len(document_results)}×{document_weight} + "
        f"關鍵字 {len(keyword_results)}×{keyword_weight} "
        f"→ {len(merged_results)} 結果"
    )
    
    return merged_results
```

---

## 📊 測試對比矩陣

### 實驗設計：權重對比

| 版本 ID | 版本名稱 | 段落權重 | 全文權重 | 關鍵字權重 | 預期 Precision | 預期 Recall | 預期 F1 |
|---------|---------|----------|----------|------------|---------------|------------|---------|
| V1 | 純段落 | 1.0 | 0.0 | 0.0 | 85%+ | 65-70% | 74% |
| V2 | 純全文 | 0.0 | 1.0 | 0.0 | 70-80% | 85%+ | 77% |
| V3 | 段落為主 | 0.7 | 0.3 | 0.0 | 80-85% | 80-85% | **82%+** |
| V4 | 平衡混合 | 0.5 | 0.5 | 0.0 | 75-80% | 85-90% | 80% |
| V5 | 全文為主 | 0.3 | 0.7 | 0.0 | 70-75% | 88-92% | 78% |
| V6 | 三層混合 | 0.5 | 0.3 | 0.2 | 75-80% | 90%+ | 82% |
| V7 | 極致召回 | 0.3 | 0.4 | 0.3 | 65-70% | 95%+ | 77% |

---

## 🎯 系統 A 的測試目標（修正後）

### ✅ 要測試的

1. **搜尋來源效能**
   - 段落向量 vs 全文向量 vs 關鍵字
   - 哪種來源 Precision 最高？
   - 哪種來源 Recall 最高？

2. **權重配置影響**
   - 段落 70% + 全文 30% vs 50%+50%
   - 最佳權重組合是什麼？
   - 權重變化如何影響 F1 Score？

3. **閾值敏感度**
   - 閾值 0.7 vs 0.75 vs 0.8
   - 最優閾值範圍？
   - 閾值對 Precision/Recall 的影響？

4. **混合策略效能**
   - 串聯式（段落→降級→全文）vs 並聯式（同時搜尋→加權）
   - 哪種策略 Response Time 更快？
   - 哪種策略分數更穩定？

### ❌ 不要測試的

1. ~~「二階段搜尋」作為整體演算法~~ → 拆解成獨立維度
2. ~~與 AI 回應相關的指標~~ → 這是系統 B 的範圍
3. ~~Stage 參數的影響~~ → Stage 是給 AI 用的，不影響檢索質量

---

## 🛠️ 資料庫 Schema 更新

### SearchAlgorithmVersion.parameters 結構（新增欄位）

```json
{
  // 原有欄位
  "search_mode": "hybrid",
  "section_threshold": 0.75,
  "document_threshold": 0.65,
  "keyword_threshold": 0.35,
  
  // ⚠️ 新增：混合權重配置
  "section_weight": 0.7,
  "document_weight": 0.3,
  "keyword_weight": 0.0,
  
  // ⚠️ 新增：混合策略
  "hybrid_merge_strategy": "weighted_score",  // weighted_score | max_score | avg_score
  
  // ⚠️ 新增：是否使用新的並聯式搜尋
  "use_parallel_search": true,  // true=並聯（同時搜尋）, false=串聯（降級）
  
  // 原有欄位
  "use_section_search": true,
  "use_document_search": true,
  "use_keyword_search": false
}
```

---

## 📝 實施計畫（修正版）

### Phase 1：開發混合權重引擎（2-3 小時）

1. **創建 HybridSearchEngine**
   - `weighted_merge()` 方法
   - 支援 3 種合併策略（weighted/max/avg）
   - 完整的日誌記錄

2. **更新 BaseKnowledgeBaseSearchService**
   - 新增 `search_knowledge_with_hybrid_weights()` 方法
   - 保留原有 `search_knowledge()` 方法（向後相容）

3. **單元測試**
   ```python
   def test_weighted_merge():
       section_results = [{'id': 1, 'score': 0.9}, {'id': 2, 'score': 0.8}]
       document_results = [{'id': 2, 'score': 0.7}, {'id': 3, 'score': 0.85}]
       
       merged = HybridSearchEngine.weighted_merge(
           section_results, document_results, [],
           section_weight=0.7, document_weight=0.3, keyword_weight=0.0
       )
       
       assert merged[0]['id'] == 1  # 0.9*0.7 = 0.63
       assert merged[1]['id'] == 2  # 0.8*0.7 + 0.7*0.3 = 0.77
       assert merged[2]['id'] == 3  # 0.85*0.3 = 0.255
   ```

---

### Phase 2：更新 BenchmarkTestRunner（1 小時）

```python
# backend/library/benchmark/test_runner.py

def run_single_test(self, test_case):
    params = self.version.parameters or {}
    
    # ⚠️ 檢查是否使用新的混合權重方法
    use_parallel = params.get('use_parallel_search', False)
    
    if use_parallel:
        # 使用新方法：並聯式混合搜尋
        results = self.search_service.search_knowledge_with_hybrid_weights(
            query=test_case.question,
            limit=10,
            search_mode=params.get('search_mode', 'auto'),
            section_threshold=params.get('section_threshold', 0.7),
            document_threshold=params.get('document_threshold', 0.65),
            keyword_threshold=params.get('keyword_threshold', 0.35),
            section_weight=params.get('section_weight', 0.5),
            document_weight=params.get('document_weight', 0.3),
            keyword_weight=params.get('keyword_weight', 0.2)
        )
    else:
        # 使用舊方法：串聯式降級搜尋（向後相容）
        results = self.search_service.search_knowledge(
            query=test_case.question,
            limit=10,
            use_vector=True,
            threshold=params.get('section_threshold', 0.7),
            search_mode=params.get('search_mode', 'auto')
        )
    
    # ... 其餘邏輯不變
```

---

### Phase 3：創建測試版本（30 分鐘）

```python
# backend/create_hybrid_weight_versions.py

from api.models import SearchAlgorithmVersion

# 版本 1：純段落（基準）
SearchAlgorithmVersion.objects.create(
    version_name='V1 - 純段落向量',
    version_code='v-section-only',
    algorithm_type='section_vector_only',
    parameters={
        'search_mode': 'section_only',
        'section_threshold': 0.75,
        'section_weight': 1.0,
        'document_weight': 0.0,
        'keyword_weight': 0.0,
        'use_parallel_search': True
    },
    description='只使用段落向量，高精準度基準版本'
)

# 版本 2：純全文（對比）
SearchAlgorithmVersion.objects.create(
    version_name='V2 - 純全文向量',
    version_code='v-document-only',
    algorithm_type='document_vector_only',
    parameters={
        'search_mode': 'document_only',
        'document_threshold': 0.65,
        'section_weight': 0.0,
        'document_weight': 1.0,
        'keyword_weight': 0.0,
        'use_parallel_search': True
    },
    description='只使用整篇文檔向量，高召回率版本'
)

# 版本 3：段落為主混合（推薦）⭐
SearchAlgorithmVersion.objects.create(
    version_name='V3 - 段落為主混合 (70-30)',
    version_code='v-hybrid-section-70',
    algorithm_type='hybrid_vector',
    parameters={
        'search_mode': 'hybrid',
        'section_threshold': 0.75,
        'document_threshold': 0.65,
        'section_weight': 0.7,
        'document_weight': 0.3,
        'keyword_weight': 0.0,
        'use_parallel_search': True,
        'hybrid_merge_strategy': 'weighted_score'
    },
    description='段落向量 70% + 全文向量 30%，平衡精準度與召回率',
    is_baseline=True  # 設為新基準
)

# 版本 4：平衡混合
SearchAlgorithmVersion.objects.create(
    version_name='V4 - 平衡混合 (50-50)',
    version_code='v-hybrid-balanced',
    algorithm_type='hybrid_vector',
    parameters={
        'search_mode': 'hybrid',
        'section_threshold': 0.70,
        'document_threshold': 0.70,
        'section_weight': 0.5,
        'document_weight': 0.5,
        'keyword_weight': 0.0,
        'use_parallel_search': True,
        'hybrid_merge_strategy': 'weighted_score'
    },
    description='段落向量與全文向量平衡混合'
)

# 版本 5：三層混合（最大召回）
SearchAlgorithmVersion.objects.create(
    version_name='V5 - 三層混合 (50-30-20)',
    version_code='v-three-layer',
    algorithm_type='three_layer_hybrid',
    parameters={
        'search_mode': 'three_layer',
        'section_threshold': 0.70,
        'document_threshold': 0.65,
        'keyword_threshold': 0.35,
        'section_weight': 0.5,
        'document_weight': 0.3,
        'keyword_weight': 0.2,
        'use_parallel_search': True,
        'hybrid_merge_strategy': 'weighted_score'
    },
    description='段落 + 全文 + 關鍵字三層混合，最大化召回率'
)

print("✅ 已創建 5 個混合權重測試版本")
```

---

### Phase 4：前端顯示優化（30 分鐘）

**測試結果表格新增欄位**：

```javascript
// frontend/src/pages/benchmark/BenchmarkTestResultsPage.js

const columns = [
  // ... 現有欄位
  {
    title: '搜尋策略',
    dataIndex: ['version', 'algorithm_type'],
    key: 'algorithm_type',
    render: (type) => {
      const typeMap = {
        'section_vector_only': { color: 'blue', text: '純段落' },
        'document_vector_only': { color: 'green', text: '純全文' },
        'hybrid_vector': { color: 'purple', text: '混合向量' },
        'three_layer_hybrid': { color: 'orange', text: '三層混合' }
      };
      const config = typeMap[type] || { color: 'default', text: type };
      return <Tag color={config.color}>{config.text}</Tag>;
    }
  },
  {
    title: '權重配置',
    key: 'weights',
    render: (_, record) => {
      const params = record.version?.parameters || {};
      const sw = params.section_weight || 0;
      const dw = params.document_weight || 0;
      const kw = params.keyword_weight || 0;
      
      if (sw + dw + kw === 0) return '-';
      
      return (
        <span style={{ fontSize: '12px' }}>
          段落 {(sw * 100).toFixed(0)}% / 
          全文 {(dw * 100).toFixed(0)}% / 
          關鍵字 {(kw * 100).toFixed(0)}%
        </span>
      );
    }
  },
  // ... 其他欄位
];
```

---

## 📊 預期測試結果

### 實驗 1：權重敏感度測試

**測試問題**：「IOL USB 如何測試？」

| 版本 | 權重配置 | Precision | Recall | F1 Score | Response Time |
|------|---------|-----------|--------|----------|---------------|
| V1 純段落 | 1.0 / 0.0 / 0.0 | **0.95** | 0.62 | 0.75 | 280ms |
| V2 純全文 | 0.0 / 1.0 / 0.0 | 0.78 | **0.91** | 0.84 | 350ms |
| V3 段落為主 | 0.7 / 0.3 / 0.0 | **0.89** | **0.85** | **0.87** ⭐ | 320ms |
| V4 平衡 | 0.5 / 0.5 / 0.0 | 0.82 | 0.88 | 0.85 | 340ms |
| V5 三層 | 0.5 / 0.3 / 0.2 | 0.80 | 0.92 | 0.86 | 420ms |

**結論**：V3（段落 70% + 全文 30%）達到最佳 F1 Score

---

### 實驗 2：搜尋模式對比

**固定權重**：段落 0.7 / 全文 0.3

| 搜尋模式 | 閾值配置 | Precision | Recall | F1 Score | 說明 |
|---------|---------|-----------|--------|----------|------|
| section_only | 0.75 / - | 0.92 | 0.64 | 0.75 | 精準但遺漏多 |
| document_only | - / 0.65 | 0.76 | 0.89 | 0.82 | 召回高但雜訊多 |
| hybrid | 0.75 / 0.65 | **0.89** | **0.85** | **0.87** ⭐ | 最佳平衡 |
| three_layer | 0.7 / 0.65 / 0.35 | 0.78 | 0.94 | 0.85 | 最高召回 |

---

## 🎯 總結：重新定義系統 A

### ✅ 正確的定位

**系統 A 不是測試「二階段搜尋」**，而是測試：

1. ✅ **搜尋來源組合**：段落 vs 全文 vs 關鍵字
2. ✅ **權重配置優化**：70-30 vs 50-50 vs 50-30-20
3. ✅ **閾值敏感度**：高精準 vs 高召回
4. ✅ **混合策略效能**：串聯 vs 並聯

### ❌ 不再測試的

1. ❌ ~~二階段搜尋作為整體演算法~~
2. ❌ ~~Stage 參數的影響~~（這是給 AI 用的）
3. ❌ ~~與 AI 回應相關的指標~~（這是系統 B）

### 🎯 新的測試目標

找出最佳的：
- **搜尋來源組合**
- **權重配置**
- **閾值範圍**

使得 **F1 Score** 最高，同時 **Response Time < 500ms**

---

## 📅 實施時間表（修正版）

| 階段 | 時間 | 任務 | 產出 |
|------|------|------|------|
| Phase 1 | 2-3 小時 | 開發混合權重引擎 | HybridSearchEngine + 單元測試 |
| Phase 2 | 1 小時 | 更新 BenchmarkTestRunner | 支援並聯式搜尋 |
| Phase 3 | 30 分鐘 | 創建測試版本 | 5 個權重配置版本 |
| Phase 4 | 30 分鐘 | 前端顯示優化 | 權重配置顯示 |
| **總計** | **4-5 小時** | **完整實現** | **系統 A 重新定義完成** |

---

## 📚 參考資料

- **原規劃文檔**：`BENCHMARK_SYSTEM_ARCHITECTURE_PLAN.md`
- **二階段搜尋實現**：`backend/library/common/knowledge_base/base_search_service.py`
- **Protocol 搜尋服務**：`backend/library/protocol_guide/search_service.py`

---

**📅 創建日期**：2025-11-23  
**📝 作者**：AI Development Team  
**🔖 標籤**：#benchmark #system-a #revised-plan #hybrid-weights  
**🎯 狀態**：規劃完成，待執行
