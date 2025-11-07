# 多向量搜索使用範例

## 📖 概述
本文檔提供多向量搜索的實際使用範例，包括 Python API 調用、不同場景的權重配置建議。

---

## 🔧 基本使用

### 1. 導入服務

```python
from api.services.embedding_service import get_embedding_service

# 獲取 embedding 服務實例
service = get_embedding_service('ultra_high')
```

### 2. 多向量搜索（標準用法）

```python
# 執行多向量搜索
results = service.search_similar_documents_multi(
    query="UNH-IOL Protocol 測試",
    source_table='protocol_guide',
    limit=5,
    threshold=0.5,
    title_weight=0.6,      # 標題權重 60%
    content_weight=0.4     # 內容權重 40%
)

# 處理結果
for result in results:
    print(f"ID: {result['source_id']}")
    print(f"標題分數: {result['title_score']:.3f}")
    print(f"內容分數: {result['content_score']:.3f}")
    print(f"最終分數: {result['final_score']:.3f}")
    print(f"匹配類型: {result['match_type']}")
    print(f"標題: {result.get('title', 'N/A')}")
    print(f"權重設定: title={result['weights']['title']}, content={result['weights']['content']}")
    print("-" * 80)
```

---

## 🎯 不同場景的權重配置

### 場景 1：品牌/型號查詢（強調標題）

**使用時機**：用戶查詢特定品牌名、型號、產品名稱

```python
# 範例：搜索 "Samsung Galaxy S21"
results = service.search_similar_documents_multi(
    query="Samsung Galaxy S21",
    source_table='protocol_guide',
    limit=5,
    threshold=0.5,
    title_weight=0.8,      # 標題權重 80%（強調）
    content_weight=0.2     # 內容權重 20%
)
```

**原因**：品牌和型號通常出現在標題中，提高標題權重能更精準地找到相關文檔。

---

### 場景 2：步驟/方法查詢（強調內容）

**使用時機**：用戶查詢操作步驟、測試方法、問題解決方案

```python
# 範例：搜索 "如何重置網路設定"
results = service.search_similar_documents_multi(
    query="如何重置網路設定",
    source_table='rvt_guide',
    limit=5,
    threshold=0.5,
    title_weight=0.3,      # 標題權重 30%
    content_weight=0.7     # 內容權重 70%（強調）
)
```

**原因**：操作步驟和方法詳情通常在內容中，提高內容權重能找到更詳細的指南。

---

### 場景 3：混合查詢（平衡權重）

**使用時機**：通用搜索、用戶意圖不明確

```python
# 範例：搜索 "Protocol 測試"
results = service.search_similar_documents_multi(
    query="Protocol 測試",
    source_table='protocol_guide',
    limit=5,
    threshold=0.5,
    title_weight=0.6,      # 標題權重 60%
    content_weight=0.4     # 內容權重 40%（平衡）
)
```

**原因**：當查詢意圖不明確時，使用平衡權重能獲得較均衡的結果。

---

### 場景 4：深度內容搜索（極重內容）

**使用時機**：搜索詳細說明、技術細節、故障排除

```python
# 範例：搜索 "錯誤代碼 0x8007000E 解決方法"
results = service.search_similar_documents_multi(
    query="錯誤代碼 0x8007000E 解決方法",
    source_table='protocol_guide',
    limit=5,
    threshold=0.5,
    title_weight=0.2,      # 標題權重 20%
    content_weight=0.8     # 內容權重 80%（極重）
)
```

**原因**：錯誤代碼和解決方法的詳細資訊通常在內容中，需要強調內容匹配。

---

## 🧠 智能權重選擇（建議實作）

### 自動識別查詢類型

```python
def smart_search(query: str, source_table: str) -> list:
    """
    智能搜索：根據查詢內容自動調整權重
    """
    service = get_embedding_service('ultra_high')
    
    # 規則 1：包含品牌名或型號 -> 強調標題
    brand_keywords = ['Samsung', 'Apple', 'UNH-IOL', 'NVIDIA', 'Intel']
    if any(keyword.lower() in query.lower() for keyword in brand_keywords):
        return service.search_similar_documents_multi(
            query=query,
            source_table=source_table,
            limit=5,
            threshold=0.5,
            title_weight=0.8,
            content_weight=0.2
        )
    
    # 規則 2：包含「如何」、「步驟」等關鍵字 -> 強調內容
    method_keywords = ['如何', '步驟', '方法', '解決', '排查']
    if any(keyword in query for keyword in method_keywords):
        return service.search_similar_documents_multi(
            query=query,
            source_table=source_table,
            limit=5,
            threshold=0.5,
            title_weight=0.3,
            content_weight=0.7
        )
    
    # 規則 3：預設使用平衡權重
    return service.search_similar_documents_multi(
        query=query,
        source_table=source_table,
        limit=5,
        threshold=0.5,
        title_weight=0.6,
        content_weight=0.4
    )

# 使用範例
results = smart_search("Samsung Galaxy 測試步驟", 'protocol_guide')
```

---

## 📊 結果分析與利用

### 1. 使用 match_type 優化顯示

```python
def display_results_with_context(results):
    """
    根據匹配類型顯示不同的提示
    """
    for result in results:
        match_type = result['match_type']
        
        if match_type == 'title_primary':
            print(f"✨ 標題高度相關：{result.get('title', 'N/A')}")
            print(f"   (標題分數 {result['title_score']:.3f} > 內容分數 {result['content_score']:.3f})")
        
        elif match_type == 'content_primary':
            print(f"📄 內容高度相關：{result.get('title', 'N/A')}")
            print(f"   (內容分數 {result['content_score']:.3f} > 標題分數 {result['title_score']:.3f})")
        
        else:  # balanced
            print(f"🎯 全面匹配：{result.get('title', 'N/A')}")
            print(f"   (標題 {result['title_score']:.3f}, 內容 {result['content_score']:.3f})")
        
        print(f"   最終分數: {result['final_score']:.3f}")
        print()
```

### 2. 根據分數調整回應策略

```python
def get_response_strategy(result):
    """
    根據匹配分數和類型決定回應策略
    """
    final_score = result['final_score']
    match_type = result['match_type']
    
    if final_score > 0.9:
        return "高度相關，直接返回完整內容"
    
    elif final_score > 0.7:
        if match_type == 'title_primary':
            return "標題匹配，返回摘要 + 完整內容連結"
        elif match_type == 'content_primary':
            return "內容匹配，返回相關段落 + 完整內容連結"
        else:
            return "全面匹配，返回摘要"
    
    elif final_score > 0.5:
        return "部分相關，返回標題和摘要"
    
    else:
        return "相關性低，可能不符合需求"

# 使用範例
for result in results:
    strategy = get_response_strategy(result)
    print(f"{result.get('title')}: {strategy}")
```

---

## 🔍 進階技巧

### 1. 動態閾值調整

```python
def adaptive_threshold_search(query: str, source_table: str):
    """
    自適應閾值搜索：先嚴格搜索，無結果則降低閾值
    """
    service = get_embedding_service('ultra_high')
    
    thresholds = [0.8, 0.6, 0.5, 0.3]
    
    for threshold in thresholds:
        results = service.search_similar_documents_multi(
            query=query,
            source_table=source_table,
            limit=5,
            threshold=threshold,
            title_weight=0.6,
            content_weight=0.4
        )
        
        if results:
            print(f"找到 {len(results)} 個結果（閾值 {threshold}）")
            return results
    
    return []  # 無結果
```

### 2. 多階段搜索

```python
def multi_stage_search(query: str, source_table: str):
    """
    多階段搜索：先找標題相關，再找內容相關
    """
    service = get_embedding_service('ultra_high')
    
    # 第一階段：強調標題
    print("第一階段：搜索標題相關文檔...")
    title_results = service.search_similar_documents_multi(
        query=query,
        source_table=source_table,
        limit=3,
        threshold=0.6,
        title_weight=0.9,
        content_weight=0.1
    )
    
    # 第二階段：強調內容
    print("第二階段：搜索內容相關文檔...")
    content_results = service.search_similar_documents_multi(
        query=query,
        source_table=source_table,
        limit=3,
        threshold=0.6,
        title_weight=0.1,
        content_weight=0.9
    )
    
    # 合併結果並去重
    all_results = {r['source_id']: r for r in title_results}
    all_results.update({r['source_id']: r for r in content_results})
    
    return list(all_results.values())
```

---

## 📝 Django ViewSet 整合範例

### 在 API 中使用多向量搜索

```python
# backend/api/views/viewsets/knowledge_viewsets.py

from rest_framework.decorators import action
from rest_framework.response import Response
from api.services.embedding_service import get_embedding_service

class ProtocolGuideViewSet(viewsets.ModelViewSet):
    # ... 其他代碼
    
    @action(detail=False, methods=['post'])
    def search(self, request):
        """
        多向量語義搜索 API
        
        請求參數:
        - query: 搜索查詢字串
        - limit: 返回結果數量（預設 5）
        - threshold: 相似度閾值（預設 0.5）
        - title_weight: 標題權重（預設 0.6）
        - content_weight: 內容權重（預設 0.4）
        """
        query = request.data.get('query')
        limit = request.data.get('limit', 5)
        threshold = request.data.get('threshold', 0.5)
        title_weight = request.data.get('title_weight', 0.6)
        content_weight = request.data.get('content_weight', 0.4)
        
        if not query:
            return Response({'error': '缺少查詢參數'}, status=400)
        
        # 執行多向量搜索
        service = get_embedding_service('ultra_high')
        results = service.search_similar_documents_multi(
            query=query,
            source_table='protocol_guide',
            limit=limit,
            threshold=threshold,
            title_weight=title_weight,
            content_weight=content_weight
        )
        
        # 格式化結果
        formatted_results = []
        for result in results:
            formatted_results.append({
                'id': result['source_id'],
                'title': result.get('title', 'N/A'),
                'content_preview': result.get('content', '')[:200] + '...',
                'scores': {
                    'title': round(result['title_score'], 3),
                    'content': round(result['content_score'], 3),
                    'final': round(result['final_score'], 3)
                },
                'match_type': result['match_type'],
                'weights': result['weights']
            })
        
        return Response({
            'query': query,
            'total_results': len(formatted_results),
            'results': formatted_results
        })
```

### API 調用範例（前端）

```javascript
// frontend/src/api/protocolGuide.js

export const searchProtocolGuides = async (query, options = {}) => {
  const {
    limit = 5,
    threshold = 0.5,
    title_weight = 0.6,
    content_weight = 0.4
  } = options;
  
  const response = await api.post('/api/protocol-guides/search/', {
    query,
    limit,
    threshold,
    title_weight,
    content_weight
  });
  
  return response.data;
};

// 使用範例
const results = await searchProtocolGuides('UNH-IOL', {
  title_weight: 0.8,  // 強調標題匹配
  content_weight: 0.2
});

console.log(`找到 ${results.total_results} 個結果`);
results.results.forEach(result => {
  console.log(`${result.title} (分數: ${result.scores.final})`);
});
```

---

## ⚠️ 注意事項

### 1. 權重配置建議

- ✅ **標題權重 + 內容權重 = 1.0**（必須相加為 1）
- ✅ **標題權重範圍**：0.2 ~ 0.8（極端值謹慎使用）
- ✅ **預設平衡權重**：0.6 / 0.4 或 0.5 / 0.5

### 2. 閾值選擇

- **高精準度**：threshold = 0.7 ~ 0.8（可能結果較少）
- **平衡**：threshold = 0.5 ~ 0.6（推薦）
- **廣泛搜索**：threshold = 0.3 ~ 0.4（結果較多但相關性可能較低）

### 3. 性能考量

- 多向量搜索性能與單向量幾乎相同（增加 < 2%）
- 批量搜索時建議複用 service 實例
- 搜索結果會包含額外的分數資訊，返回資料量略增

---

## 📚 參考資料

- **實施指南**: `/docs/features/multi-vector-implementation-guide.md`
- **測試結果**: `/docs/features/multi-vector-search-test-results.md`
- **向量搜索指南**: `/docs/vector-search/vector-search-guide.md`

---

**文檔更新時間**: 2025-11-06  
**版本**: v1.0
