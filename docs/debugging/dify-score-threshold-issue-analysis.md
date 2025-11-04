# Dify Score Threshold 不生效問題分析與解決方案

## 📋 問題描述

**現象**：用戶在 Dify 工作室設定 `threshold = 0.75`，但前端仍然顯示 **50%** 相似度的資料。

**影響範圍**：Protocol Assistant（以及所有使用外部知識庫的 Assistant）

## 🔍 根本原因分析

### 問題根源：兩個獨立的 threshold 系統

| Threshold 位置 | 作用範圍 | 當前值 | 是否生效 | 控制者 |
|---------------|---------|--------|---------|--------|
| **Dify 工作室設定** | Dify 內部知識庫 | 0.75 | ✅ | Dify 工作室 UI |
| **後端 Chat API** | 發送給 Dify 的請求參數 | 0.75 | ✅ | `base_api_handler.py` |
| **外部知識庫 API** | 返回給 Dify 的結果 | ❌ **未檢查** | ❌ | **問題所在！** |

### 詳細流程分析

```
用戶查詢 "sop"
    ↓
[1] Protocol Assistant Chat API
    ├── 構建 payload
    ├── retrieval_model.score_threshold = 0.75 ✅ 已設定
    ├── 發送到 Dify: POST http://10.10.172.37/v1/chat-messages
    ↓
[2] Dify 系統處理
    ├── 接收 query="sop"
    ├── 檢查 retrieval_model.score_threshold = 0.75
    ├── 調用外部知識庫 API: POST /api/dify/knowledge/retrieval
    │   └── 請求參數：
    │       {
    │         "knowledge_id": "protocol_guide_db",
    │         "query": "sop",
    │         "retrieval_setting": {
    │           "top_k": 5,
    │           "score_threshold": 0.75  ← ⚠️ Dify 會傳這個參數嗎？
    │         }
    │       }
    ↓
[3] 外部知識庫 API (/api/dify/knowledge/retrieval)
    ├── 接收請求
    ├── 解析參數: score_threshold = ???
    ├── 調用 DifyKnowledgeSearchHandler.search()
    │   ├── 參數: score_threshold = retrieval_setting.get('score_threshold', 0.0)
    │   ├── 調用 ProtocolGuideSearchService.search_knowledge()
    │   │   ├── 段落向量搜尋: threshold = 0.7 (硬編碼) ✅
    │   │   ├── 整篇向量搜尋: threshold = 0.6 (硬編碼) ✅
    │   │   └── 關鍵字搜尋: threshold = None ❌ **問題在這裡！**
    │   │       └── 返回 50% 相似度的結果
    │   └── 過濾結果: filter_results_by_score(results, score_threshold)
    │       └── 如果 score_threshold = 0.0，則不過濾 ❌
    ↓
[4] 返回結果給 Dify
    ├── 返回 3 條結果（包含 50% 的）
    ├── Dify 收到結果後：
    │   ├── 選項 A：再次應用 threshold 過濾 ✅ (如果實現了)
    │   └── 選項 B：直接使用所有結果 ❌ (如果沒實現)
    ↓
[5] 最終顯示給用戶
    └── 顯示 50% 相似度的 UNH-IOL 資料
```

### 關鍵證據（從日誌）

1. **後端確實設定了 0.75**：
```log
Payload: {'inputs': {}, 'query': 'sop', 'response_mode': 'blocking', 
'user': 'protocol_guide_user_1', 'retrieval_model': {
  'search_method': 'semantic_search', 
  'reranking_enable': False, 
  'reranking_mode': None, 
  'top_k': 3, 
  'score_threshold_enabled': True, 
  'score_threshold': 0.75  ← ✅ 確認設定
}}
```

2. **外部 API 返回了 3 條結果**：
```log
[INFO] library.common.knowledge_base.base_search_service: ✅ 段落向量搜尋成功: 5 個結果
[INFO] library.common.knowledge_base.base_search_service: 向量搜索返回 2 條結果
[INFO] library.common.knowledge_base.base_search_service: 關鍵字搜索補充 1 條結果 ← ⚠️ 這是問題！
[INFO] library.dify_knowledge.DifyKnowledgeSearchHandler: Protocol Guide 搜索結果: 3 條
```

**分析**：
- 向量搜尋返回 2 條高分結果（> 0.7）
- 關鍵字搜尋補充 1 條低分結果（50%，來自 UNH-IOL）
- **關鍵字搜尋沒有分數門檻，導致低相關性結果被納入**

## 🎯 問題定位

### 問題 1：關鍵字搜尋沒有相似度評分

**位置**：`library/common/knowledge_base/base_search_service.py` - `search_with_keywords()`

```python
def search_with_keywords(self, query, limit=5):
    """關鍵字搜索"""
    # ... 執行資料庫查詢
    
    for item in items:
        results.append(self._format_item_to_result(item))
        # ❌ 問題：沒有計算相似度分數！
        # _format_item_to_result() 會設定固定的 score = 0.5
```

### 問題 2：外部知識庫 API 可能沒有接收 Dify 的 score_threshold

**位置**：`backend/api/views/dify_knowledge_views.py` - `dify_knowledge_search()`

```python
@api_view(['POST'])
def dify_knowledge_search(request):
    # 解析請求資料
    data = json.loads(request.body)
    retrieval_setting = data.get('retrieval_setting', {})
    
    # 執行搜索
    result = handler.search(
        knowledge_id=knowledge_id,
        query=query,
        top_k=retrieval_setting.get('top_k', 5),
        score_threshold=retrieval_setting.get('score_threshold', 0.0)  # ✅ 有接收
    )
```

**但是**，需要確認 Dify 是否真的會在外部知識庫請求中傳遞 `retrieval_setting`！

### 問題 3：DifyKnowledgeSearchHandler 過濾邏輯

**位置**：`library/dify_knowledge/__init__.py` - `filter_results_by_score()`

```python
def filter_results_by_score(self, results, score_threshold):
    """根據分數閾值過濾結果"""
    if score_threshold <= 0:
        return results  # ❌ 如果 threshold = 0，不過濾任何結果！
        
    filtered_results = [
        result for result in results 
        if result.get('score', 0) >= score_threshold
    ]
    
    return filtered_results
```

## 💡 解決方案設計

### 方案 1：在外部知識庫 API 層面強制過濾（推薦）

**優點**：
- 在返回給 Dify 之前就過濾掉低分結果
- 不依賴 Dify 的二次過濾
- 可以確保結果質量

**修改位置**：
1. `backend/api/views/dify_knowledge_views.py` - 確保接收並傳遞 `score_threshold`
2. `library/dify_knowledge/__init__.py` - 改進過濾邏輯
3. `library/common/knowledge_base/base_search_service.py` - 為關鍵字搜尋添加分數計算

**具體修改**：

#### 修改 1：確保 Dify 的 score_threshold 被正確接收

```python
# backend/api/views/dify_knowledge_views.py

@api_view(['POST'])
def dify_knowledge_search(request):
    try:
        data = json.loads(request.body) if request.body else {}
        
        knowledge_id = data.get('knowledge_id', 'employee_database')
        query = data.get('query', '')
        retrieval_setting = data.get('retrieval_setting', {})
        
        # ✅ 改進：記錄完整的 retrieval_setting
        logger.info(f"📥 Dify 外部知識庫請求:")
        logger.info(f"  - knowledge_id: {knowledge_id}")
        logger.info(f"  - query: {query}")
        logger.info(f"  - retrieval_setting: {retrieval_setting}")
        
        # ✅ 改進：設定最低閾值（如果 Dify 沒傳或傳 0）
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        if score_threshold <= 0:
            # 設定預設最低閾值，避免返回過多不相關結果
            score_threshold = 0.5  # 或從配置讀取
            logger.info(f"  ⚠️ score_threshold 過低或未設定，使用預設值: {score_threshold}")
        
        # 執行搜索
        result = handler.search(
            knowledge_id=knowledge_id,
            query=query,
            top_k=retrieval_setting.get('top_k', 5),
            score_threshold=score_threshold  # 使用處理後的閾值
        )
        
        logger.info(f"✅ 知識庫搜索成功: {knowledge_id}, results={len(result.get('records', []))}")
        return Response(result)
```

#### 修改 2：改進 DifyKnowledgeSearchHandler 的過濾邏輯

```python
# library/dify_knowledge/__init__.py

def filter_results_by_score(self, results, score_threshold):
    """
    根據分數閾值過濾結果
    
    ✨ 改進：
    1. 如果 threshold <= 0，使用預設閾值 0.5
    2. 記錄過濾前後的結果數量
    3. 記錄被過濾掉的結果信息（調試用）
    """
    # ✅ 改進：設定最低閾值
    if score_threshold <= 0:
        score_threshold = 0.5  # 預設最低閾值
        self.logger.info(f"⚠️ score_threshold 未設定或過低，使用預設值: {score_threshold}")
    
    # 過濾結果
    filtered_results = []
    rejected_results = []
    
    for result in results:
        score = result.get('score', 0)
        if score >= score_threshold:
            filtered_results.append(result)
        else:
            rejected_results.append({
                'title': result.get('title', 'N/A')[:50],
                'score': score
            })
    
    # 記錄過濾信息
    self.logger.info(
        f"分數過濾: {len(results)} → {len(filtered_results)} "
        f"(threshold: {score_threshold}, 拒絕: {len(rejected_results)})"
    )
    
    if rejected_results:
        self.logger.debug(f"被拒絕的結果: {rejected_results}")
    
    return filtered_results
```

#### 修改 3：為關鍵字搜尋添加分數計算

```python
# library/common/knowledge_base/base_search_service.py

def search_with_keywords(self, query, limit=5):
    """
    使用關鍵字進行搜索
    
    ✨ 改進：為關鍵字搜尋結果計算相似度分數
    """
    try:
        from django.db.models import Q
        
        # 構建搜索條件
        q_objects = Q()
        for field in self.default_search_fields:
            if hasattr(self.model_class, field):
                q_objects |= Q(**{f"{field}__icontains": query})
        
        # 執行搜索
        items = self.model_class.objects.filter(q_objects)[:limit * 2]  # 多取一些，供後續過濾
        
        results = []
        for item in items:
            # ✅ 改進：計算關鍵字匹配分數
            score = self._calculate_keyword_score(item, query)
            result = self._format_item_to_result(item, score=score)
            results.append(result)
        
        # 按分數排序
        results.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        return results[:limit]
        
    except Exception as e:
        self.logger.error(f"關鍵字搜索錯誤: {str(e)}")
        return []

def _calculate_keyword_score(self, item, query):
    """
    計算關鍵字匹配分數
    
    計算邏輯：
    1. 檢查各個欄位是否包含查詢關鍵字
    2. 計算匹配次數
    3. 根據匹配位置（標題 > 內容）調整權重
    
    Returns:
        float: 0.0 ~ 1.0 的分數
    """
    try:
        query_lower = query.lower()
        total_score = 0.0
        max_score = 0.0
        
        # 權重設定
        field_weights = {
            'title': 0.5,      # 標題匹配權重高
            'content': 0.3,    # 內容匹配權重中等
        }
        
        for field, weight in field_weights.items():
            if hasattr(item, field):
                field_value = str(getattr(item, field, '')).lower()
                
                if query_lower in field_value:
                    # 計算出現次數
                    count = field_value.count(query_lower)
                    
                    # 計算位置因素（越早出現分數越高）
                    position = field_value.find(query_lower)
                    position_factor = 1.0 - (position / max(len(field_value), 1))
                    
                    # 計算該欄位的分數
                    field_score = min(weight * (1 + count * 0.1) * (0.5 + position_factor * 0.5), weight)
                    total_score += field_score
                    max_score += weight
        
        # 正規化到 0-1 範圍
        final_score = total_score / max_score if max_score > 0 else 0.3  # 預設 0.3 分
        
        # 限制最低分數為 0.3（表示有匹配，但相關性低）
        final_score = max(final_score, 0.3)
        
        return final_score
        
    except Exception as e:
        self.logger.warning(f"分數計算失敗: {str(e)}")
        return 0.3  # 預設低分

def _format_item_to_result(self, item, score=None):
    """
    格式化項目為結果
    
    Args:
        item: Model 實例
        score: 預設分數（如果為 None，使用固定值）
    """
    try:
        content = self._get_item_content(item)
        title = getattr(item, 'title', str(item))
        
        # ✅ 改進：接受傳入的分數
        if score is None:
            score = 0.5  # 預設分數（表示中等相關性）
        
        return {
            'content': content,
            'score': score,
            'title': title,
            'metadata': {
                'id': item.id,
                'source': self.source_table,
                'created_at': getattr(item, 'created_at', None),
            }
        }
    except Exception as e:
        self.logger.error(f"格式化結果錯誤: {str(e)}")
        return {
            'content': str(item),
            'score': score if score is not None else 0.3,
            'title': str(item),
            'metadata': {'id': getattr(item, 'id', None)}
        }
```

### 方案 2：調整搜尋策略（輔助方案）

**修改 `search_knowledge()` 邏輯**：

```python
# library/common/knowledge_base/base_search_service.py

def search_knowledge(self, query, limit=5, use_vector=True, min_score_threshold=0.5):
    """
    搜索知識庫
    
    ✨ 改進：
    1. 添加 min_score_threshold 參數
    2. 只有當向量搜尋結果少於 limit/2 時才補充關鍵字搜尋
    3. 確保所有結果的分數都高於閾值
    """
    try:
        results = []
        
        # 嘗試向量搜索
        if use_vector:
            try:
                vector_results = self.search_with_vectors(query, limit)
                if vector_results:
                    results.extend(vector_results)
                    self.logger.info(f"向量搜索返回 {len(vector_results)} 條結果")
            except Exception as e:
                self.logger.warning(f"向量搜索失敗: {str(e)}")
        
        # ✅ 改進：只有在向量結果嚴重不足時才補充關鍵字搜尋
        min_vector_threshold = max(2, limit // 2)  # 至少要有 limit 的一半
        
        if len(results) < min_vector_threshold:
            self.logger.info(
                f"⚠️ 向量搜尋結果不足 ({len(results)} < {min_vector_threshold})，"
                f"使用關鍵字搜尋補充"
            )
            remaining = limit - len(results)
            keyword_results = self.search_with_keywords(query, remaining)
            
            # 過濾低分結果並去重
            existing_ids = {r.get('metadata', {}).get('id') for r in results}
            for kr in keyword_results:
                kr_id = kr.get('metadata', {}).get('id')
                kr_score = kr.get('score', 0)
                
                # ✅ 改進：檢查分數閾值
                if kr_id not in existing_ids and kr_score >= min_score_threshold:
                    results.append(kr)
                    existing_ids.add(kr_id)
                elif kr_score < min_score_threshold:
                    self.logger.debug(
                        f"拒絕低分關鍵字結果: {kr.get('title', 'N/A')[:50]} "
                        f"(score: {kr_score:.2f})"
                    )
            
            self.logger.info(f"關鍵字搜索補充 {len(keyword_results)} 條結果")
        else:
            self.logger.info(f"向量搜尋結果充足 ({len(results)} >= {min_vector_threshold})，跳過關鍵字搜尋")
        
        return results[:limit]
        
    except Exception as e:
        self.logger.error(f"搜索失敗: {str(e)}")
        return []
```

## 🧪 測試驗證步驟

### 1. 添加詳細日誌

在修改前，先添加日誌來確認 Dify 是否傳遞 `score_threshold`：

```python
# backend/api/views/dify_knowledge_views.py

@api_view(['POST'])
def dify_knowledge_search(request):
    # 添加完整請求日誌
    raw_body = request.body.decode('utf-8')
    logger.info(f"🔍 Dify 外部知識庫 API 原始請求:")
    logger.info(f"  Raw body: {raw_body}")
    
    data = json.loads(request.body)
    logger.info(f"  Parsed data: {data}")
```

### 2. 測試查詢

```bash
# 發送測試請求
curl -X POST "http://localhost/api/dify/knowledge/retrieval" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide_db",
    "query": "sop",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.75
    }
  }'
```

### 3. 檢查日誌

```bash
# 查看完整的請求和響應日誌
docker logs ai-django --tail 100 | grep -A 20 "Dify 外部知識庫"
```

### 4. 驗證分數過濾

修改後，應該看到：
```log
[INFO] 分數過濾: 3 → 2 (threshold: 0.75, 拒絕: 1)
[DEBUG] 被拒絕的結果: [{'title': 'UNH-IOL...', 'score': 0.5}]
```

## 📊 預期效果

### 修改前

```
向量搜索: 2 條 (score > 0.7)
關鍵字搜索: 1 條 (score = 0.5) ← UNH-IOL
總共返回: 3 條
過濾後: 3 條 (因為 threshold = 0 或未檢查)
```

### 修改後

```
向量搜索: 2 條 (score > 0.7)
關鍵字搜索: 1 條 (score = 0.5) ← UNH-IOL
總共返回: 3 條
過濾後: 2 條 (threshold = 0.75，拒絕 0.5 的結果) ✅
```

## 🎯 建議的實施順序

1. **先驗證**：添加日誌確認 Dify 是否傳遞 `score_threshold` ✅
2. **修改過濾邏輯**：改進 `filter_results_by_score()` ✅
3. **添加分數計算**：為關鍵字搜尋添加 `_calculate_keyword_score()` ✅
4. **調整搜尋策略**：修改 `search_knowledge()` 減少低分結果 ✅
5. **測試驗證**：確保修改生效 ✅

## 📚 相關文件

- `backend/api/views/dify_knowledge_views.py` - 外部知識庫 API 入口
- `library/dify_knowledge/__init__.py` - Dify 知識搜尋處理器
- `library/common/knowledge_base/base_search_service.py` - 搜尋服務基類
- `library/protocol_guide/search_service.py` - Protocol Guide 搜尋服務

---

**更新日期**: 2025-11-03  
**分析者**: AI Assistant  
**狀態**: ✅ 分析完成，等待實施
