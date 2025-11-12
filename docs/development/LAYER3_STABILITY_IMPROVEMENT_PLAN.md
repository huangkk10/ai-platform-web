# Layer 3 智能選擇機制穩定度提升方案

## 📋 目標
在不影響對話體驗的前提下，提升 Protocol Assistant 的檢索穩定度，確保「相同查詢返回相同結果」。

---

## 🎯 核心問題分析

### 當前問題
```
Layer 3 的「智能」特性導致不穩定：
├─ 對話記憶權重（±30%）> 向量分數差距（5.42%）
├─ 多樣化策略干擾選擇
├─ 主題連貫性優先於準確性
└─ 時間窗口效應造成選擇波動
```

### 目標定義
```
理想狀態：
├─ 檢索準確率：≥ 95%
├─ 穩定性：相同查詢返回相同結果
├─ 對話體驗：保持流暢（可接受的權衡）
└─ 響應時間：≤ 3 秒（不增加）
```

---

## 🔧 方案分類

### 方案 A：**無侵入性調整（推薦）**
- **特點**：只調整 Dify 工作室設定，不改程式碼
- **風險**：低
- **成本**：低
- **效果**：中-高（80-95% 改善）

### 方案 B：**輕度侵入性調整**
- **特點**：修改 conversation_id 傳遞邏輯
- **風險**：中
- **成本**：中
- **效果**：高（90-98% 改善）

### 方案 C：**中度侵入性調整**
- **特點**：實現自訂選擇邏輯，覆蓋 Dify 選擇
- **風險**：中-高
- **成本**：高
- **效果**：很高（95-100% 改善）

### 方案 D：**完全重構（不推薦）**
- **特點**：移除 Dify，自建全套系統
- **風險**：高
- **成本**：很高
- **效果**：100% 可控

---

## 📊 方案 A：無侵入性調整（推薦首選）

### A1. **提高 Score Threshold（最優先）**

#### 設定位置
```
Dify 工作室 → Protocol Guide 應用 → 檢索設置
```

#### 調整建議
```yaml
當前設定:
  Score threshold: 0.85
  Top K: 3

建議設定:
  Score threshold: 0.88  # ✅ 優先修改
  Top K: 3              # 保持不變

進階設定（如需更高穩定度）:
  Score threshold: 0.90  # 更嚴格過濾
  Top K: 2              # 減少候選數量
```

#### 預期效果
```
Threshold 0.85 → 0.88:
├─ CrystalDiskMark: 90.74% ✅ 通過
├─ I3C: 85.32% ❌ 過濾掉
└─ 預期改善：80-90% 成功率 → 95-98% 成功率

Threshold 0.88 → 0.90:
├─ CrystalDiskMark: 90.74% ✅ 通過
├─ I3C: 85.32% ❌ 過濾掉
├─ 其他低分文檔: < 90% ❌ 全部過濾
└─ 預期改善：95-98% → 98-100% 成功率
```

#### 實施步驟
```
1. 登入 Dify 工作室
2. 選擇 Protocol Guide 應用
3. 進入「編排」模式
4. 找到「知識檢索」節點
5. 修改 Score threshold: 0.85 → 0.88
6. 發布新版本
7. 測試驗證（crystaldiskmark × 10）
```

#### 優點
- ✅ 零程式碼修改
- ✅ 即時生效
- ✅ 可隨時回退
- ✅ 風險極低

#### 缺點
- ⚠️ 可能過濾掉一些邊緣相關的文檔
- ⚠️ 無法完全消除對話記憶影響（如果候選 ≥ 2）

---

### A2. **調整 Rerank 模型（進階）**

#### 設定位置
```
Dify 工作室 → 知識庫 → Protocol Guide 知識庫 → Rerank 設定
```

#### 調整建議
```yaml
當前設定:
  Rerank 模型: Jina Rerank v1
  Top N: 5

建議設定:
  Rerank 模型: Jina Rerank v2  # 更準確的重排序
  Top N: 3                      # 減少候選數量
  
或（如果效果不佳）:
  關閉 Rerank: False            # 完全依賴向量分數
```

#### 預期效果
```
Rerank v1 → v2:
├─ 更準確的語義理解
├─ 減少「主題連貫性」干擾
└─ 預期改善：2-5% 成功率提升

關閉 Rerank:
├─ 純粹基於向量分數（確定性）
├─ 消除 Rerank 的「智能調整」
└─ 預期改善：5-10% 成功率提升
```

#### 實施步驟
```
1. Dify 工作室 → 知識庫
2. Protocol Guide 知識庫 → 設定
3. 修改 Rerank 設定
4. 保存
5. 測試驗證
```

---

### A3. **調整檢索模式（實驗性）**

#### 設定位置
```
Dify 工作室 → Protocol Guide 應用 → 檢索設置 → 檢索模式
```

#### 調整建議
```yaml
當前設定:
  檢索模式: 混合檢索（向量 + 全文）
  向量權重: 0.7
  全文權重: 0.3

建議設定 1（提高向量權重）:
  檢索模式: 混合檢索
  向量權重: 0.9  # ✅ 更依賴向量分數
  全文權重: 0.1

建議設定 2（純向量檢索）:
  檢索模式: 向量檢索  # ✅ 完全確定性
  向量權重: 1.0
  全文權重: 0.0
```

#### 預期效果
```
混合檢索 → 純向量檢索:
├─ 完全確定性演算法
├─ 消除全文搜尋的不確定性
├─ 但可能降低部分查詢的召回率
└─ 預期改善：5-8% 成功率提升
```

---

## 📊 方案 B：輕度侵入性調整

### B1. **動態 conversation_id 管理（推薦）**

#### 核心概念
```
當前行為：
├─ 每次查詢都傳遞相同的 conversation_id
├─ Dify 累積對話記憶
└─ 記憶干擾選擇

改進方案：
├─ 檢索查詢：不傳 conversation_id（或傳空字串）
├─ 對話查詢：正常傳遞 conversation_id
└─ 分離「檢索」和「對話」兩種模式
```

#### 程式碼修改

**修改位置**：`library/protocol_guide/two_tier_handler.py`

```python
# 當前代碼（Line 77-87）
stage_1_response = self._request_dify_chat(
    query=user_query,
    conversation_id=conversation_id,  # ⚠️ 總是傳遞
    is_full_search=False
)

# ✅ 修改後（方案 B1-1：完全分離）
stage_1_response = self._request_dify_chat(
    query=user_query,
    conversation_id="",  # ✅ 檢索時不傳 conversation_id
    is_full_search=False
)

# ✅ 修改後（方案 B1-2：部分分離，保留回答記憶）
# 檢索階段使用「檢索專用 ID」，回答階段使用「用戶 ID」
retrieval_conversation_id = ""  # 檢索時為空
stage_1_response = self._request_dify_chat(
    query=user_query,
    conversation_id=retrieval_conversation_id,
    is_full_search=False
)

# ✅ 修改後（方案 B1-3：智能判斷）
# 根據查詢類型決定是否傳遞 conversation_id
def should_use_conversation_memory(query: str) -> bool:
    """
    判斷是否應該使用對話記憶
    
    不使用記憶的場景：
    - 簡短查詢（≤ 10 字）
    - 單一名詞查詢（如 "crystaldiskmark"）
    - 技術詞彙查詢
    
    使用記憶的場景：
    - 複雜查詢（> 20 字）
    - 包含上下文的查詢（"剛才提到的..."）
    - 多輪對話查詢
    """
    # 簡單規則
    if len(query) <= 10:
        return False  # 簡短查詢不需要記憶
    
    # 檢查上下文關鍵字
    context_keywords = ['剛才', '之前', '上面', '那個', '這個']
    if any(kw in query for kw in context_keywords):
        return True  # 需要上下文記憶
    
    return False  # 預設不使用記憶

# 使用智能判斷
use_memory = should_use_conversation_memory(user_query)
active_conversation_id = conversation_id if use_memory else ""

stage_1_response = self._request_dify_chat(
    query=user_query,
    conversation_id=active_conversation_id,  # ✅ 動態決定
    is_full_search=False
)
```

#### 預期效果
```
方案 B1-1（完全分離）:
├─ 檢索準確率：98-100%
├─ 對話體驗：下降（無記憶）
└─ 適用場景：純檢索系統

方案 B1-2（部分分離）:
├─ 檢索準確率：95-98%
├─ 對話體驗：中等（保留回答記憶）
└─ 適用場景：混合系統

方案 B1-3（智能判斷）:
├─ 檢索準確率：92-96%
├─ 對話體驗：良好（動態平衡）
└─ 適用場景：自適應系統（推薦）
```

#### 實施步驟
```
1. 備份當前代碼
2. 修改 two_tier_handler.py
3. 測試簡單查詢（"crystaldiskmark"）
4. 測試複雜查詢（"請說明 crystaldiskmark 的使用方法"）
5. 測試上下文查詢（"剛才提到的工具"）
6. 調整智能判斷邏輯
7. 部署到生產環境
```

#### 優點
- ✅ 精準控制記憶使用
- ✅ 保留對話體驗
- ✅ 提升檢索穩定度
- ✅ 可回退

#### 缺點
- ⚠️ 需要修改程式碼
- ⚠️ 需要測試驗證
- ⚠️ 可能影響部分對話功能

---

### B2. **記憶清理機制（補充方案）**

#### 核心概念
```
當前行為：
├─ conversation_id 永久保留
├─ 對話記憶無限累積
└─ 舊記憶干擾新查詢

改進方案：
├─ 定期清理對話記憶
├─ 檢測「主題切換」自動清理
└─ 提供「清除記憶」API
```

#### 程式碼修改

**新增功能**：`library/protocol_guide/memory_manager.py`

```python
"""
對話記憶管理器
"""

import time
from typing import Dict, Optional

class ConversationMemoryManager:
    """管理對話記憶的生命週期"""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Args:
            ttl_seconds: 記憶存活時間（秒）
                預設 300 秒 = 5 分鐘
        """
        self.ttl_seconds = ttl_seconds
        self.memory_store: Dict[str, dict] = {}
    
    def should_clear_memory(
        self,
        conversation_id: str,
        current_query: str
    ) -> bool:
        """
        判斷是否應該清除記憶
        
        清除條件：
        1. 超過 TTL 時間
        2. 檢測到主題切換
        3. 用戶明確請求清除
        """
        # 條件 1：超過 TTL
        if conversation_id in self.memory_store:
            last_active = self.memory_store[conversation_id].get('last_active', 0)
            if time.time() - last_active > self.ttl_seconds:
                return True
        
        # 條件 2：主題切換檢測
        if self._detect_topic_switch(conversation_id, current_query):
            return True
        
        # 條件 3：清除關鍵字
        clear_keywords = ['清除', '重新', '新問題', 'clear', 'reset']
        if any(kw in current_query for kw in clear_keywords):
            return True
        
        return False
    
    def _detect_topic_switch(
        self,
        conversation_id: str,
        current_query: str
    ) -> bool:
        """
        檢測主題是否切換
        
        簡單策略：
        - 當前查詢與最近 N 次查詢的語義相似度 < 0.3
        - 連續 3 次查詢不同主題
        """
        if conversation_id not in self.memory_store:
            return False
        
        history = self.memory_store[conversation_id].get('queries', [])
        
        # 至少有 3 次歷史查詢
        if len(history) < 3:
            return False
        
        # 檢查最近 3 次查詢的主題
        recent_topics = [q.get('topic') for q in history[-3:]]
        current_topic = self._extract_topic(current_query)
        
        # 如果當前主題與最近 3 次都不同
        if current_topic not in recent_topics:
            return True
        
        return False
    
    def _extract_topic(self, query: str) -> str:
        """
        提取查詢主題（簡化版）
        
        範例：
        - "crystaldiskmark" → "crystaldiskmark"
        - "I3C 相關說明" → "i3c"
        - "如何使用 ULINK" → "ulink"
        """
        # 簡單提取第一個技術詞彙
        keywords = [
            'crystaldiskmark', 'i3c', 'ulink', 'iol', 'cup',
            'protocol', 'burn', 'test'
        ]
        
        query_lower = query.lower()
        for keyword in keywords:
            if keyword in query_lower:
                return keyword
        
        return 'unknown'
    
    def update_memory(
        self,
        conversation_id: str,
        query: str,
        response: dict
    ):
        """更新記憶存儲"""
        if conversation_id not in self.memory_store:
            self.memory_store[conversation_id] = {
                'queries': [],
                'created_at': time.time()
            }
        
        self.memory_store[conversation_id]['queries'].append({
            'query': query,
            'topic': self._extract_topic(query),
            'timestamp': time.time()
        })
        
        self.memory_store[conversation_id]['last_active'] = time.time()
        
        # 保留最近 10 次查詢
        if len(self.memory_store[conversation_id]['queries']) > 10:
            self.memory_store[conversation_id]['queries'] = \
                self.memory_store[conversation_id]['queries'][-10:]
    
    def clear_memory(self, conversation_id: str):
        """清除指定對話的記憶"""
        if conversation_id in self.memory_store:
            del self.memory_store[conversation_id]

# 全局實例
memory_manager = ConversationMemoryManager(ttl_seconds=300)
```

**整合到 two_tier_handler.py**：

```python
from .memory_manager import memory_manager

def handle_two_tier_search(self, user_query, conversation_id, user_id):
    """處理兩階段搜尋（加入記憶管理）"""
    
    # ✅ 檢查是否應該清除記憶
    if memory_manager.should_clear_memory(conversation_id, user_query):
        logger.info(f"🧹 清除對話記憶: {conversation_id}")
        memory_manager.clear_memory(conversation_id)
        # 使用新的 conversation_id
        conversation_id = ""  # 或生成新 ID
    
    # 原有邏輯...
    stage_1_response = self._request_dify_chat(
        query=user_query,
        conversation_id=conversation_id,
        is_full_search=False
    )
    
    # ✅ 更新記憶
    memory_manager.update_memory(conversation_id, user_query, stage_1_response)
    
    return stage_1_response
```

#### 預期效果
```
記憶清理機制:
├─ 5 分鐘自動清理 → 減少長期污染
├─ 主題切換自動清理 → 提升跨主題準確率
├─ 手動清除選項 → 用戶可控
└─ 預期改善：3-5% 成功率提升
```

---

## 📊 方案 C：中度侵入性調整

### C1. **自訂選擇邏輯覆蓋（高級）**

#### 核心概念
```
當前流程：
Dify 向量搜尋 → Dify Layer 3 選擇 → 返回結果

改進流程：
Dify 向量搜尋 → 獲取所有候選 → 自訂選擇邏輯 → 返回結果
                                   ↓
                              覆蓋 Dify 選擇
```

#### 程式碼修改

**新增模組**：`library/protocol_guide/custom_selector.py`

```python
"""
自訂文檔選擇器
覆蓋 Dify AI 的 Layer 3 選擇機制
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class CustomDocumentSelector:
    """
    自訂文檔選擇器
    
    選擇策略：
    1. 純分數優先（確定性）
    2. 查詢詞匹配加權
    3. 最小差距檢查
    """
    
    def __init__(self, min_score_gap: float = 0.05):
        """
        Args:
            min_score_gap: 最小分數差距
                如果最高分與次高分差距 < min_score_gap
                則認為不確定，返回降級模式
        """
        self.min_score_gap = min_score_gap
    
    def select_best_document(
        self,
        candidates: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """
        從候選文檔中選擇最佳文檔
        
        Args:
            candidates: 候選文檔列表（來自 Dify metadata.retriever_resources）
            query: 用戶查詢
            
        Returns:
            選中的文檔
        """
        if not candidates:
            return None
        
        # Step 1: 提取分數並排序
        scored_candidates = []
        for doc in candidates:
            score = doc.get('score', 0.0)
            scored_candidates.append({
                'document': doc,
                'base_score': score,
                'adjusted_score': score
            })
        
        # Step 2: 查詢詞匹配加權
        for candidate in scored_candidates:
            doc = candidate['document']
            title = doc.get('document_name', '').lower()
            
            # 如果標題包含查詢詞，獎勵 +5%
            if query.lower() in title:
                candidate['adjusted_score'] += 0.05
                logger.info(f"   查詢詞匹配加成: {title} +5%")
        
        # Step 3: 按調整後分數排序
        scored_candidates.sort(
            key=lambda x: x['adjusted_score'],
            reverse=True
        )
        
        # Step 4: 檢查分數差距
        if len(scored_candidates) >= 2:
            best = scored_candidates[0]
            second = scored_candidates[1]
            
            score_gap = best['adjusted_score'] - second['adjusted_score']
            
            logger.info(f"   最高分: {best['adjusted_score']:.4f}")
            logger.info(f"   次高分: {second['adjusted_score']:.4f}")
            logger.info(f"   分數差距: {score_gap:.4f}")
            
            # 如果差距太小，標記為不確定
            if score_gap < self.min_score_gap:
                logger.warning(f"   ⚠️ 分數差距 < {self.min_score_gap}，不確定")
                return {
                    'document': best['document'],
                    'is_uncertain': True,
                    'score_gap': score_gap
                }
        
        # Step 5: 返回最高分文檔
        best = scored_candidates[0]
        logger.info(f"   ✅ 選中文檔: {best['document'].get('document_name')}")
        
        return {
            'document': best['document'],
            'is_uncertain': False,
            'score_gap': score_gap if len(scored_candidates) >= 2 else 1.0
        }


# 全局實例
custom_selector = CustomDocumentSelector(min_score_gap=0.05)
```

**整合到 two_tier_handler.py**：

```python
from .custom_selector import custom_selector

def handle_two_tier_search(self, user_query, conversation_id, user_id):
    """處理兩階段搜尋（加入自訂選擇）"""
    
    # 階段 1：請求 Dify
    stage_1_response = self._request_dify_chat(
        query=user_query,
        conversation_id=conversation_id,
        is_full_search=False
    )
    
    # ✅ 攔截 Dify 的選擇結果，使用自訂選擇邏輯
    raw_metadata = stage_1_response.get('raw_response', {}).get('metadata', {})
    all_candidates = raw_metadata.get('retriever_resources', [])
    
    if all_candidates:
        logger.info(f"   🔍 Dify 返回 {len(all_candidates)} 個候選文檔")
        logger.info(f"   🎯 使用自訂選擇器重新選擇...")
        
        # 自訂選擇
        selection_result = custom_selector.select_best_document(
            candidates=all_candidates,
            query=user_query
        )
        
        if selection_result['is_uncertain']:
            logger.warning(f"   ⚠️ 自訂選擇器判斷不確定，進入階段 2")
            # 進入階段 2...
        else:
            # ✅ 覆蓋 Dify 的選擇
            selected_doc = selection_result['document']
            
            # 更新 metadata（只保留選中的文檔）
            raw_metadata['retriever_resources'] = [selected_doc]
            
            logger.info(f"   ✅ 自訂選擇完成: {selected_doc.get('document_name')}")
    
    # 返回結果（metadata 已被覆蓋）
    return stage_1_response
```

#### 預期效果
```
自訂選擇器:
├─ 完全確定性選擇（純分數優先）
├─ 覆蓋 Dify Layer 3 的「智能」選擇
├─ 保留 Dify 的向量搜尋能力
├─ 不影響對話記憶（仍可用於回答生成）
└─ 預期改善：95-100% 成功率
```

#### 實施步驟
```
1. 創建 custom_selector.py
2. 修改 two_tier_handler.py 整合
3. 測試驗證
4. 調整 min_score_gap 參數
5. 部署
```

#### 優點
- ✅ 完全控制選擇邏輯
- ✅ 確定性選擇
- ✅ 保留 Dify 其他功能
- ✅ 可自訂策略

#### 缺點
- ⚠️ 複雜度較高
- ⚠️ 需要維護自訂邏輯
- ⚠️ 可能與 Dify 更新衝突

---

## 📊 方案比較總表

| 方案 | 成本 | 風險 | 效果 | 穩定度 | 對話體驗 | 推薦度 |
|------|------|------|------|--------|---------|--------|
| **A1. 提高 Threshold** | ⭐ | ⭐ | ⭐⭐⭐⭐ | 95-98% | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| A2. 調整 Rerank | ⭐⭐ | ⭐ | ⭐⭐ | 85-90% | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| A3. 調整檢索模式 | ⭐ | ⭐⭐ | ⭐⭐⭐ | 88-93% | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **B1. 動態 conversation_id** | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | 92-96% | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| B2. 記憶清理機制 | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | 88-92% | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **C1. 自訂選擇邏輯** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 95-100% | ⭐⭐⭐ | ⭐⭐⭐ |
| D. 完全重構 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 100% | ⭐ | ⭐ |

---

## 🎯 推薦實施順序

### 階段 1：立即執行（1 小時內）
```
✅ 方案 A1: 提高 Threshold (0.85 → 0.88)
   - 在 Dify 工作室修改
   - 測試驗證
   - 預期效果：80% → 95% 成功率
```

### 階段 2：短期優化（1-2 天）
```
✅ 方案 A3: 調整檢索模式（試驗性）
   - 測試純向量檢索
   - 對比混合檢索效果
   - 選擇最佳配置

✅ 觀察數據
   - 收集 1-2 天的使用數據
   - 分析穩定度改善
   - 決定是否進入階段 3
```

### 階段 3：中期優化（如需要，1 週內）
```
✅ 方案 B1: 動態 conversation_id（智能判斷版本）
   - 實現智能判斷邏輯
   - 測試不同場景
   - 平衡穩定度與體驗

或

✅ 方案 C1: 自訂選擇邏輯
   - 如果階段 1-2 改善不足
   - 實現自訂選擇器
   - 完全控制選擇邏輯
```

### 階段 4：長期優化（可選）
```
✅ 方案 B2: 記憶清理機制
   - 作為補充優化
   - 提升長對話穩定度

✅ 持續監控與調整
   - 收集用戶反饋
   - 分析失敗案例
   - 微調參數
```

---

## 📊 預期改善路徑

```
當前狀態（Threshold 0.85）:
├─ Experiment A: 100% ✅
├─ Experiment B: 80%  ⚠️
├─ Experiment C: 60%  ❌
└─ Web UI 觀察: 33% ❌
   平均穩定度: ~68%

階段 1 後（Threshold 0.88）:
├─ Experiment A: 100% ✅
├─ Experiment B: 95%  ✅
├─ Experiment C: 85%  ⚠️
└─ Web UI: 95%+ ✅
   平均穩定度: ~94% （+26%）

階段 2 後（+ 檢索模式優化）:
├─ Experiment A: 100% ✅
├─ Experiment B: 98%  ✅
├─ Experiment C: 90%  ✅
└─ Web UI: 98%+ ✅
   平均穩定度: ~96% （+28%）

階段 3 後（+ 動態 conversation_id 或自訂選擇）:
├─ Experiment A: 100% ✅
├─ Experiment B: 100% ✅
├─ Experiment C: 95%  ✅
└─ Web UI: 100% ✅
   平均穩定度: ~99% （+31%）
```

---

## 🔍 監控指標

### 關鍵指標
```yaml
穩定度指標:
  - 相同查詢一致性: 目標 ≥ 95%
  - 跨對話一致性: 目標 ≥ 90%
  - 長對話穩定度: 目標 ≥ 85%

準確度指標:
  - Top-1 準確率: 目標 ≥ 95%
  - 相關文檔召回: 目標 ≥ 90%
  - 錯誤引用率: 目標 ≤ 5%

體驗指標:
  - 平均響應時間: 目標 ≤ 3 秒
  - 不確定回答率: 目標 ≤ 10%
  - 用戶滿意度: 目標 ≥ 4.0/5.0
```

### 監控方法
```python
# 創建監控腳本
# backend/monitor_protocol_assistant_stability.py

import time
from collections import Counter

def test_stability(query: str, repeat: int = 10):
    """測試穩定度"""
    results = []
    
    for i in range(repeat):
        response = call_protocol_assistant_api(query)
        doc_name = extract_document_name(response)
        results.append(doc_name)
        time.sleep(2)  # 間隔 2 秒
    
    # 統計
    counter = Counter(results)
    most_common = counter.most_common(1)[0]
    
    stability = most_common[1] / repeat * 100
    
    print(f"查詢: {query}")
    print(f"重複次數: {repeat}")
    print(f"結果分布: {dict(counter)}")
    print(f"穩定度: {stability:.1f}%")
    print(f"判定: {'✅ 通過' if stability >= 95 else '❌ 不通過'}")

# 執行測試
test_stability("crystaldiskmark", repeat=10)
test_stability("I3C", repeat=10)
test_stability("UNH-IOL", repeat=10)
```

---

## 📅 實施時程表

```
Day 0（今天）:
├─ 09:00-10:00: 備份當前配置
├─ 10:00-10:30: Dify 工作室修改 Threshold (0.85 → 0.88)
├─ 10:30-11:00: 測試驗證（crystaldiskmark × 20）
├─ 11:00-12:00: 監控 Web UI 使用情況
└─ 決策：是否需要進入階段 2

Day 1-2:
├─ 收集使用數據
├─ 分析失敗案例
├─ 試驗檢索模式調整
└─ 評估是否需要階段 3

Week 1:
├─ 如需要：實施方案 B1 或 C1
├─ 完整測試驗證
├─ 用戶反饋收集
└─ 文檔更新

Week 2+:
├─ 持續監控
├─ 微調參數
├─ 長期優化
└─ 經驗總結
```

---

## 💡 關鍵建議

### 1. **優先低成本方案**
> 先嘗試 Threshold 調整，可能已經解決 80% 的問題。

### 2. **數據驅動決策**
> 每個階段都收集數據，用數據證明改善效果。

### 3. **漸進式改進**
> 不要一次性實施所有方案，避免無法定位問題。

### 4. **保留回退路徑**
> 每個修改都要能快速回退到穩定狀態。

### 5. **平衡穩定度與體驗**
> 不要為了 100% 穩定度犧牲對話體驗。

---

## 📋 行動清單

### 立即行動（今天）
- [ ] 備份當前 Dify 工作室配置
- [ ] 修改 Score threshold: 0.85 → 0.88
- [ ] 發布新版本
- [ ] 測試驗證（crystaldiskmark × 20）
- [ ] 監控 1 小時

### 短期行動（1-2 天）
- [ ] 收集穩定度數據
- [ ] 分析失敗案例
- [ ] 評估是否需要階段 2

### 中期行動（1 週，如需要）
- [ ] 實施方案 B1 或 C1
- [ ] 完整測試
- [ ] 部署到生產環境

### 長期行動（持續）
- [ ] 監控穩定度指標
- [ ] 收集用戶反饋
- [ ] 持續優化調整

---

## 📅 文檔資訊

- **創建日期**: 2025-11-12
- **版本**: v1.0
- **狀態**: ✅ 規劃完成，待實施
- **下一步**: 執行方案 A1（提高 Threshold）

---

**準備開始實施方案 A1 了嗎？** 🚀
