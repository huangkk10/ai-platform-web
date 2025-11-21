# 🔄 搜尋演算法版本管理系統設計

**日期**: 2025-11-21  
**狀態**: 📋 規劃中  
**目標**: 建立搜尋演算法的版本控制和對比系統，支援新舊版本並存

---

## 🎯 問題定義

### 現況分析
Protocol Assistant 目前使用的搜尋系統包含：

1. **智能路由器** (`SmartSearchRouter`)
   - 模式 A：關鍵字觸發全文搜尋
   - 模式 B：兩階段搜尋（段落 → 全文）

2. **多層次搜尋機制**
   - 段落級向量搜尋（Stage 1）
   - 全文級向量搜尋（Stage 2）
   - 關鍵字降級搜尋

3. **動態權重系統** (`SearchThresholdSetting`)
   - 第一階段：標題 60% / 內容 40% / threshold 0.70
   - 第二階段：標題 50% / 內容 50% / threshold 0.60

### 核心問題
❌ **當前系統無版本控制**：
- 改進搜尋演算法時，直接覆蓋原有實作
- 無法回滾到舊版本
- 難以進行 A/B 測試
- 無法量化改進效果

---

## 💡 解決方案：搜尋演算法版本管理系統

### 核心概念

**不覆蓋原有搜尋方式，而是建立版本分支**：
- 每個版本是一個完整的搜尋配置快照
- 可以在不同版本之間切換
- 保留歷史版本用於對比和回滾
- 支援跑分系統對比不同版本

---

## 📊 系統架構設計

### 1. 資料庫設計

#### 1.1 搜尋演算法版本表 (`search_algorithm_version`)

```sql
CREATE TABLE search_algorithm_version (
    id SERIAL PRIMARY KEY,
    
    -- 版本識別
    version_name VARCHAR(100) NOT NULL,           -- 版本名稱 (如 "智能路由 v2.1")
    version_code VARCHAR(50) NOT NULL UNIQUE,     -- 版本代碼 (如 "v2.1.0")
    assistant_type VARCHAR(50) NOT NULL,          -- 'protocol_assistant', 'rvt_assistant'
    
    -- 版本描述
    description TEXT,                             -- 版本說明
    changelog TEXT,                               -- 變更記錄
    
    -- 演算法類型
    algorithm_type VARCHAR(50),                   -- 'smart_router', 'vector_only', 'hybrid', 'keyword_only'
    
    -- 路由配置 (JSON)
    router_config JSONB,                          -- 智能路由器配置
    /*
    範例:
    {
        "enable_smart_router": true,
        "mode_a_enabled": true,
        "mode_b_enabled": true,
        "full_document_keywords": ["sop", "完整", "全部"],
        "uncertainty_detection": {
            "enabled": true,
            "strict_mode": false,
            "min_response_length": 20
        }
    }
    */
    
    -- 搜尋配置 (JSON)
    search_config JSONB,                          -- 搜尋參數配置
    /*
    範例:
    {
        "mode_a": {
            "top_k": 3,
            "threshold": 0.5,
            "search_type": "full_document"
        },
        "mode_b": {
            "stage_1": {
                "top_k": 5,
                "threshold": 0.5,
                "search_type": "section"
            },
            "stage_2": {
                "top_k": 3,
                "threshold": 0.5,
                "search_type": "full_document"
            }
        }
    }
    */
    
    -- 權重配置 (JSON)
    weight_config JSONB,                          -- 向量權重配置
    /*
    範例:
    {
        "stage_1": {
            "title_weight": 0.6,
            "content_weight": 0.4,
            "threshold": 0.7
        },
        "stage_2": {
            "title_weight": 0.5,
            "content_weight": 0.5,
            "threshold": 0.6
        },
        "use_unified_weights": true
    }
    */
    
    -- Dify 整合配置 (JSON)
    dify_config JSONB,                            -- Dify 請求配置
    /*
    範例:
    {
        "timeout": 75,
        "verbose": false,
        "use_inputs_search_mode": true,
        "use_query_rewriting": false
    }
    */
    
    -- 版本狀態
    is_active BOOLEAN DEFAULT TRUE,               -- 是否啟用
    is_default BOOLEAN DEFAULT FALSE,             -- 是否為預設版本
    is_baseline BOOLEAN DEFAULT FALSE,            -- 是否為基準版本（用於對比）
    
    -- 部署狀態
    deployment_status VARCHAR(30) DEFAULT 'draft',  -- draft, testing, production, deprecated
    deployed_at TIMESTAMP,                        -- 部署時間
    
    -- 效能快照 (自動更新)
    avg_precision DECIMAL(5,4),                   -- 平均精準度
    avg_recall DECIMAL(5,4),                      -- 平均召回率
    avg_f1_score DECIMAL(5,4),                    -- 平均 F1 分數
    avg_response_time DECIMAL(10,2),              -- 平均響應時間 (ms)
    total_queries INTEGER DEFAULT 0,              -- 總查詢次數
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by_id INTEGER REFERENCES auth_user(id),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一約束
    CONSTRAINT unique_assistant_version_code UNIQUE (assistant_type, version_code)
);

-- 索引
CREATE INDEX idx_search_algo_version_assistant ON search_algorithm_version(assistant_type);
CREATE INDEX idx_search_algo_version_active ON search_algorithm_version(is_active, is_default);
CREATE INDEX idx_search_algo_version_status ON search_algorithm_version(deployment_status);
CREATE INDEX idx_search_algo_version_created ON search_algorithm_version(created_at DESC);
```

**範例版本資料**:
```json
{
  "version_name": "Protocol Assistant - 智能路由 v2.1",
  "version_code": "v2.1.0",
  "assistant_type": "protocol_assistant",
  "algorithm_type": "smart_router",
  "description": "智能路由器 + 兩階段搜尋，優化全文檢索",
  "changelog": "1. 新增智能路由判斷\n2. 優化第二階段閾值\n3. 改進不確定性檢測",
  
  "router_config": {
    "enable_smart_router": true,
    "mode_a_enabled": true,
    "mode_b_enabled": true,
    "full_document_keywords": ["sop", "完整", "全部", "教學", "指南"]
  },
  
  "search_config": {
    "mode_a": {
      "top_k": 3,
      "threshold": 0.5
    },
    "mode_b": {
      "stage_1": {"top_k": 5, "threshold": 0.5},
      "stage_2": {"top_k": 3, "threshold": 0.5}
    }
  },
  
  "weight_config": {
    "stage_1": {"title_weight": 0.6, "content_weight": 0.4, "threshold": 0.7},
    "stage_2": {"title_weight": 0.5, "content_weight": 0.5, "threshold": 0.6}
  },
  
  "is_default": true,
  "deployment_status": "production"
}
```

---

#### 1.2 版本切換記錄表 (`search_version_switch_log`)

```sql
CREATE TABLE search_version_switch_log (
    id SERIAL PRIMARY KEY,
    
    -- 切換資訊
    assistant_type VARCHAR(50) NOT NULL,          -- Assistant 類型
    from_version_id INTEGER REFERENCES search_algorithm_version(id),
    to_version_id INTEGER REFERENCES search_algorithm_version(id),
    
    -- 切換原因
    switch_reason VARCHAR(20),                    -- manual, ab_test, performance_issue, rollback
    notes TEXT,                                   -- 詳細說明
    
    -- 執行資訊
    switched_by_id INTEGER REFERENCES auth_user(id),
    switched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 影響範圍
    affected_users INTEGER,                       -- 受影響用戶數（如 A/B 測試）
    effective_immediately BOOLEAN DEFAULT TRUE     -- 是否立即生效
);

-- 索引
CREATE INDEX idx_version_switch_assistant ON search_version_switch_log(assistant_type);
CREATE INDEX idx_version_switch_time ON search_version_switch_log(switched_at DESC);
```

---

#### 1.3 查詢路由記錄表 (`search_query_routing_log`)

```sql
CREATE TABLE search_query_routing_log (
    id SERIAL PRIMARY KEY,
    
    -- 查詢資訊
    version_id INTEGER REFERENCES search_algorithm_version(id),
    assistant_type VARCHAR(50) NOT NULL,
    user_id INTEGER REFERENCES auth_user(id),
    conversation_id UUID,
    
    -- 查詢內容
    user_query TEXT NOT NULL,
    
    -- 路由決策
    router_mode VARCHAR(10),                      -- 'mode_a', 'mode_b'
    search_stage INTEGER,                         -- 1, 2 (for mode_b)
    is_fallback BOOLEAN DEFAULT FALSE,            -- 是否降級
    fallback_reason TEXT,                         -- 降級原因
    
    -- 搜尋結果
    returned_document_count INTEGER,              -- 返回文檔數量
    top_similarity_score DECIMAL(5,4),            -- 最高相似度
    
    -- 效能指標
    response_time DECIMAL(10,2),                  -- 響應時間 (ms)
    dify_response_time DECIMAL(10,2),             -- Dify API 響應時間
    
    -- 詳細資料 (JSON)
    search_results JSONB,                         -- 搜尋結果詳情
    metadata JSONB,                               -- 額外資料
    
    -- 時間戳記
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_query_routing_version ON search_query_routing_log(version_id);
CREATE INDEX idx_query_routing_assistant ON search_query_routing_log(assistant_type);
CREATE INDEX idx_query_routing_user ON search_query_routing_log(user_id);
CREATE INDEX idx_query_routing_time ON search_query_routing_log(created_at DESC);
CREATE INDEX idx_query_routing_mode ON search_query_routing_log(router_mode);
```

---

### 2. 版本管理邏輯設計

#### 2.1 版本創建流程

```python
# backend/api/services/search_version_manager.py

class SearchVersionManager:
    """搜尋演算法版本管理器"""
    
    def create_version_from_current(
        self,
        assistant_type: str,
        version_name: str,
        version_code: str,
        description: str,
        user_id: int
    ) -> SearchAlgorithmVersion:
        """
        從當前運行配置創建新版本
        
        Args:
            assistant_type: Assistant 類型
            version_name: 版本名稱
            version_code: 版本代碼
            description: 版本說明
            user_id: 創建者 ID
            
        Returns:
            SearchAlgorithmVersion: 新版本實例
        """
        # 讀取當前 SearchThresholdSetting
        current_threshold = SearchThresholdSetting.objects.get(
            assistant_type=assistant_type
        )
        
        # 讀取當前 SmartSearchConfig
        from library.protocol_guide.smart_search_config import get_default_config
        current_search_config = get_default_config()
        
        # 組裝版本配置
        version = SearchAlgorithmVersion.objects.create(
            version_name=version_name,
            version_code=version_code,
            assistant_type=assistant_type,
            algorithm_type='smart_router',
            description=description,
            
            # 路由配置
            router_config={
                "enable_smart_router": True,
                "mode_a_enabled": True,
                "mode_b_enabled": True,
                "full_document_keywords": [
                    "sop", "完整", "全部", "教學", "指南"
                ],
            },
            
            # 搜尋配置
            search_config={
                "mode_a": {
                    "top_k": current_search_config.mode_a_top_k,
                    "threshold": float(current_search_config.mode_a_threshold),
                },
                "mode_b": {
                    "stage_1": {
                        "top_k": current_search_config.mode_b_stage_1_top_k,
                        "threshold": float(current_search_config.mode_b_stage_1_threshold),
                    },
                    "stage_2": {
                        "top_k": current_search_config.mode_b_stage_2_top_k,
                        "threshold": float(current_search_config.mode_b_stage_2_threshold),
                    }
                }
            },
            
            # 權重配置
            weight_config={
                "stage_1": {
                    "title_weight": float(current_threshold.stage1_title_weight) / 100,
                    "content_weight": float(current_threshold.stage1_content_weight) / 100,
                    "threshold": float(current_threshold.stage1_threshold),
                },
                "stage_2": {
                    "title_weight": float(current_threshold.stage2_title_weight) / 100,
                    "content_weight": float(current_threshold.stage2_content_weight) / 100,
                    "threshold": float(current_threshold.stage2_threshold),
                },
                "use_unified_weights": current_threshold.use_unified_weights,
            },
            
            # Dify 配置
            dify_config={
                "timeout": current_search_config.dify_timeout,
                "verbose": current_search_config.dify_verbose,
            },
            
            created_by_id=user_id,
            deployment_status='draft'
        )
        
        return version
    
    def create_version_from_template(
        self,
        assistant_type: str,
        template_type: str,
        user_id: int
    ) -> SearchAlgorithmVersion:
        """
        從預設範本創建版本
        
        Args:
            assistant_type: Assistant 類型
            template_type: 範本類型 (conservative, balanced, aggressive)
            user_id: 創建者 ID
            
        Returns:
            SearchAlgorithmVersion: 新版本實例
        """
        templates = {
            'conservative': {
                'version_name': 'Conservative Search',
                'version_code': 'v1.0.0-conservative',
                'search_config': {
                    'mode_a': {'top_k': 2, 'threshold': 0.7},
                    'mode_b': {
                        'stage_1': {'top_k': 3, 'threshold': 0.7},
                        'stage_2': {'top_k': 2, 'threshold': 0.7}
                    }
                },
                'weight_config': {
                    'stage_1': {'title_weight': 0.7, 'content_weight': 0.3, 'threshold': 0.75},
                    'stage_2': {'title_weight': 0.6, 'content_weight': 0.4, 'threshold': 0.70}
                }
            },
            'balanced': {
                'version_name': 'Balanced Search',
                'version_code': 'v1.0.0-balanced',
                'search_config': {
                    'mode_a': {'top_k': 3, 'threshold': 0.5},
                    'mode_b': {
                        'stage_1': {'top_k': 5, 'threshold': 0.5},
                        'stage_2': {'top_k': 3, 'threshold': 0.5}
                    }
                },
                'weight_config': {
                    'stage_1': {'title_weight': 0.6, 'content_weight': 0.4, 'threshold': 0.70},
                    'stage_2': {'title_weight': 0.5, 'content_weight': 0.5, 'threshold': 0.60}
                }
            },
            'aggressive': {
                'version_name': 'Aggressive Search',
                'version_code': 'v1.0.0-aggressive',
                'search_config': {
                    'mode_a': {'top_k': 5, 'threshold': 0.3},
                    'mode_b': {
                        'stage_1': {'top_k': 8, 'threshold': 0.3},
                        'stage_2': {'top_k': 5, 'threshold': 0.3}
                    }
                },
                'weight_config': {
                    'stage_1': {'title_weight': 0.5, 'content_weight': 0.5, 'threshold': 0.60},
                    'stage_2': {'title_weight': 0.4, 'content_weight': 0.6, 'threshold': 0.50}
                }
            }
        }
        
        template = templates.get(template_type, templates['balanced'])
        
        # 使用範本創建版本
        # ... (實作邏輯)
```

---

#### 2.2 版本切換流程

```python
class SearchVersionManager:
    
    def switch_version(
        self,
        assistant_type: str,
        to_version_id: int,
        user_id: int,
        reason: str = 'manual',
        notes: str = ''
    ) -> dict:
        """
        切換搜尋演算法版本
        
        Args:
            assistant_type: Assistant 類型
            to_version_id: 目標版本 ID
            user_id: 操作者 ID
            reason: 切換原因
            notes: 詳細說明
            
        Returns:
            dict: 切換結果
        """
        # 獲取當前預設版本
        try:
            current_version = SearchAlgorithmVersion.objects.get(
                assistant_type=assistant_type,
                is_default=True
            )
        except SearchAlgorithmVersion.DoesNotExist:
            current_version = None
        
        # 獲取目標版本
        target_version = SearchAlgorithmVersion.objects.get(id=to_version_id)
        
        # 驗證版本
        if target_version.assistant_type != assistant_type:
            raise ValueError("版本類型不匹配")
        
        # 開始事務
        with transaction.atomic():
            # 取消舊版本的預設狀態
            if current_version:
                current_version.is_default = False
                current_version.save()
            
            # 設定新版本為預設
            target_version.is_default = True
            target_version.deployment_status = 'production'
            target_version.deployed_at = timezone.now()
            target_version.save()
            
            # 記錄切換日誌
            SearchVersionSwitchLog.objects.create(
                assistant_type=assistant_type,
                from_version_id=current_version.id if current_version else None,
                to_version_id=target_version.id,
                switch_reason=reason,
                notes=notes,
                switched_by_id=user_id
            )
        
        return {
            'success': True,
            'from_version': current_version.version_code if current_version else None,
            'to_version': target_version.version_code,
            'message': f'已切換至版本 {target_version.version_code}'
        }
```

---

#### 2.3 版本應用邏輯（核心改動）

```python
# library/protocol_guide/smart_search_router.py (修改)

class SmartSearchRouter:
    """智能搜尋路由器（支援版本管理）"""
    
    def __init__(self, version_id: int = None):
        """
        初始化路由器
        
        Args:
            version_id: 指定版本 ID（None 則使用預設版本）
        """
        # 載入版本配置
        self.version = self._load_version(version_id)
        
        # 根據版本配置初始化處理器
        self._initialize_handlers()
    
    def _load_version(self, version_id: int = None) -> SearchAlgorithmVersion:
        """
        載入版本配置
        
        Args:
            version_id: 版本 ID（None 則使用預設版本）
            
        Returns:
            SearchAlgorithmVersion: 版本實例
        """
        if version_id:
            # 載入指定版本
            version = SearchAlgorithmVersion.objects.get(id=version_id)
        else:
            # 載入預設版本
            try:
                version = SearchAlgorithmVersion.objects.get(
                    assistant_type='protocol_assistant',
                    is_default=True
                )
            except SearchAlgorithmVersion.DoesNotExist:
                # 沒有預設版本，使用當前配置
                logger.warning("沒有預設版本，使用程式碼預設配置")
                return None
        
        logger.info(f"✅ 載入搜尋演算法版本: {version.version_code}")
        return version
    
    def _initialize_handlers(self):
        """根據版本配置初始化處理器"""
        if self.version is None:
            # 使用預設邏輯
            self.mode_a_handler = KeywordTriggeredSearchHandler()
            self.mode_b_handler = TwoTierSearchHandler()
            return
        
        # 從版本配置中讀取參數
        router_config = self.version.router_config or {}
        search_config = self.version.search_config or {}
        
        # 初始化處理器（傳入版本配置）
        self.mode_a_handler = KeywordTriggeredSearchHandler(
            config=search_config.get('mode_a', {})
        )
        self.mode_b_handler = TwoTierSearchHandler(
            config=search_config.get('mode_b', {})
        )
        
        logger.info(f"   Mode A: top_k={search_config.get('mode_a', {}).get('top_k')}, "
                   f"threshold={search_config.get('mode_a', {}).get('threshold')}")
        logger.info(f"   Mode B Stage 1: top_k={search_config.get('mode_b', {}).get('stage_1', {}).get('top_k')}, "
                   f"threshold={search_config.get('mode_b', {}).get('stage_1', {}).get('threshold')}")
```

---

### 3. API 設計

#### 3.1 版本管理 API

```python
# GET /api/search-versions/
# 列出所有版本
{
    "data": [
        {
            "id": 1,
            "version_name": "智能路由 v2.1",
            "version_code": "v2.1.0",
            "assistant_type": "protocol_assistant",
            "algorithm_type": "smart_router",
            "is_default": true,
            "deployment_status": "production",
            "avg_precision": 0.85,
            "avg_response_time": 245.5,
            "created_at": "2025-11-21T10:00:00Z"
        }
    ]
}

# POST /api/search-versions/
# 創建新版本
{
    "version_name": "智能路由 v2.2",
    "version_code": "v2.2.0",
    "assistant_type": "protocol_assistant",
    "description": "優化第二階段閾值",
    "create_from": "current",  # 'current', 'template', 'copy'
    "template_type": "balanced"  # 'conservative', 'balanced', 'aggressive'
}

# GET /api/search-versions/{id}/
# 獲取版本詳情
{
    "id": 1,
    "version_name": "智能路由 v2.1",
    "version_code": "v2.1.0",
    "router_config": {...},
    "search_config": {...},
    "weight_config": {...},
    "dify_config": {...}
}

# PATCH /api/search-versions/{id}/
# 更新版本配置
{
    "search_config": {
        "mode_b": {
            "stage_2": {
                "threshold": 0.55  # 調整閾值
            }
        }
    }
}

# POST /api/search-versions/{id}/set-default/
# 設定為預設版本
{
    "reason": "performance_improvement",
    "notes": "測試效果良好，正式部署"
}

# POST /api/search-versions/{id}/duplicate/
# 複製版本
{
    "new_version_code": "v2.1.1",
    "new_version_name": "智能路由 v2.1.1（測試）"
}
```

---

### 4. 前端介面設計

#### 4.1 版本管理主頁面 (`/admin/search-versions`)

```
┌─────────────────────────────────────────────────────────────┐
│  🔄 搜尋演算法版本管理                   [+ 新增版本] [對比版本] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  篩選: [Assistant: Protocol ▾] [狀態: 全部 ▾] [🔍 搜尋...]  │
│                                                               │
│  📋 版本列表                                                  │
│  ┌───┬──────┬─────────┬────────┬────┬───────┬────────┬────┐│
│  │ ✓ │ 版本 │ 演算法  │ 狀態   │ P  │ R     │ 時間   │ 操作││
│  ├───┼──────┼─────────┼────────┼────┼───────┼────────┼────┤│
│  │ ● │v2.1.0│智能路由 │生產中  │0.85│ 0.82  │ 245ms  │ ⚙️ ││
│  │   │      │         │✅預設  │    │       │        │    ││
│  ├───┼──────┼─────────┼────────┼────┼───────┼────────┼────┤│
│  │ ○ │v2.0.5│智能路由 │已棄用  │0.80│ 0.78  │ 312ms  │ 📋 ││
│  ├───┼──────┼─────────┼────────┼────┼───────┼────────┼────┤│
│  │ ○ │v2.2.0│智能路由 │測試中  │0.88│ 0.84  │ 228ms  │ 🚀 ││
│  │   │      │(Beta)   │        │    │       │        │    ││
│  └───┴──────┴─────────┴────────┴────┴───────┴────────┴────┘│
│                                                               │
│  操作說明:                                                    │
│  ● = 當前生產版本  ○ = 歷史/測試版本                          │
│  ⚙️ = 配置詳情  📋 = 複製版本  🚀 = 部署到生產環境            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

#### 4.2 版本詳細配置頁面

```
┌─────────────────────────────────────────────────────────────┐
│  🔧 版本配置 - v2.1.0 智能路由                      [儲存變更] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  基本資訊:                                                    │
│  版本代碼: v2.1.0                                             │
│  版本名稱: [智能路由 v2.1                    ]                │
│  演算法類型: [智能路由器 ▾]                                   │
│  狀態: [生產中 ▾]  ☑️ 預設版本  ☐ 基準版本                   │
│                                                               │
│  ─────────────────────────────────────────────────────       │
│                                                               │
│  🔀 路由器配置:                                               │
│  ☑️ 啟用智能路由                                              │
│  ☑️ 模式 A (關鍵字優先全文搜尋)                               │
│  ☑️ 模式 B (兩階段搜尋)                                       │
│                                                               │
│  全文關鍵字: [sop, 完整, 全部, 教學, 指南                ]    │
│                                                               │
│  ─────────────────────────────────────────────────────       │
│                                                               │
│  🔍 搜尋配置:                                                 │
│                                                               │
│  📌 模式 A (全文搜尋)                                         │
│    Top K: [3]   Threshold: [0.50]                            │
│                                                               │
│  📌 模式 B 階段 1 (段落搜尋)                                  │
│    Top K: [5]   Threshold: [0.50]                            │
│                                                               │
│  📌 模式 B 階段 2 (全文搜尋)                                  │
│    Top K: [3]   Threshold: [0.50]                            │
│                                                               │
│  ─────────────────────────────────────────────────────       │
│                                                               │
│  ⚖️ 權重配置:                                                 │
│                                                               │
│  📌 第一階段 (段落搜尋)                                       │
│    標題權重: [60]%  內容權重: [40]%                          │
│    Threshold: [0.70]                                          │
│                                                               │
│  📌 第二階段 (全文搜尋)                                       │
│    標題權重: [50]%  內容權重: [50]%                          │
│    Threshold: [0.60]                                          │
│                                                               │
│  ☑️ 使用統一權重模式                                          │
│                                                               │
│  ─────────────────────────────────────────────────────       │
│                                                               │
│  🔌 Dify 整合配置:                                            │
│    超時時間: [75] 秒                                          │
│    ☐ 詳細日誌模式                                             │
│                                                               │
│  [儲存變更] [重置] [刪除版本] [執行跑分測試]                  │
└─────────────────────────────────────────────────────────────┘
```

#### 4.3 版本切換確認對話框

```
┌─────────────────────────────────────────────────────────────┐
│  ⚠️ 確認切換搜尋演算法版本                           [✕ 關閉] │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  您即將切換 Protocol Assistant 的搜尋演算法版本：             │
│                                                               │
│  當前版本: v2.1.0 - 智能路由 (生產中)                         │
│  目標版本: v2.2.0 - 智能路由 Beta                             │
│                                                               │
│  📊 版本對比:                                                 │
│  ┌──────────────┬────────┬────────┐                         │
│  │ 指標         │ v2.1.0 │ v2.2.0 │                         │
│  ├──────────────┼────────┼────────┤                         │
│  │ Precision    │ 0.85   │ 0.88 ↗ │                         │
│  │ Recall       │ 0.82   │ 0.84 ↗ │                         │
│  │ 響應時間     │ 245ms  │ 228ms↗ │                         │
│  └──────────────┴────────┴────────┘                         │
│                                                               │
│  ⚠️ 注意事項:                                                 │
│  • 切換後將立即對所有用戶生效                                 │
│  • 建議在低峰時段進行切換                                     │
│  • 可隨時回滾到舊版本                                         │
│                                                               │
│  切換原因: [效能改善測試           ▾]                         │
│  備註: [___________________________________]                  │
│                                                               │
│  [確認切換] [取消]                                            │
└─────────────────────────────────────────────────────────────┘
```

---

### 5. 整合跑分系統

#### 5.1 版本跑分結果關聯

```sql
-- 在 benchmark_test_run 表中新增版本關聯
ALTER TABLE benchmark_test_run 
ADD COLUMN search_version_id INTEGER REFERENCES search_algorithm_version(id);

-- 索引
CREATE INDEX idx_benchmark_run_version ON benchmark_test_run(search_version_id);
```

#### 5.2 自動跑分測試

```python
class SearchVersionManager:
    
    def run_benchmark_for_version(
        self,
        version_id: int,
        test_case_filters: dict = None
    ) -> dict:
        """
        為特定版本執行跑分測試
        
        Args:
            version_id: 版本 ID
            test_case_filters: 測試案例篩選條件
            
        Returns:
            dict: 測試結果
        """
        version = SearchAlgorithmVersion.objects.get(id=version_id)
        
        # 暫時切換到測試版本
        with temporary_version_switch(version_id):
            # 執行跑分測試
            from library.benchmark import BenchmarkRunner
            runner = BenchmarkRunner(
                assistant_type=version.assistant_type,
                version_id=version_id
            )
            
            results = runner.run_tests(
                test_case_filters=test_case_filters
            )
            
            # 更新版本效能指標
            version.avg_precision = results['avg_precision']
            version.avg_recall = results['avg_recall']
            version.avg_f1_score = results['avg_f1_score']
            version.avg_response_time = results['avg_response_time']
            version.save()
        
        return results
```

---

### 6. A/B 測試支援

#### 6.1 A/B 測試配置

```python
class ABTestManager:
    """A/B 測試管理器"""
    
    def create_ab_test(
        self,
        assistant_type: str,
        version_a_id: int,
        version_b_id: int,
        traffic_split: float = 0.5,  # 50% 流量給 B 版本
        duration_hours: int = 24
    ) -> dict:
        """
        創建 A/B 測試
        
        Args:
            assistant_type: Assistant 類型
            version_a_id: A 版本 ID（當前版本）
            version_b_id: B 版本 ID（測試版本）
            traffic_split: 流量分配比例（0.0-1.0）
            duration_hours: 測試持續時間（小時）
            
        Returns:
            dict: A/B 測試配置
        """
        # 驗證版本
        version_a = SearchAlgorithmVersion.objects.get(id=version_a_id)
        version_b = SearchAlgorithmVersion.objects.get(id=version_b_id)
        
        # 創建 A/B 測試記錄
        ab_test = ABTest.objects.create(
            assistant_type=assistant_type,
            version_a=version_a,
            version_b=version_b,
            traffic_split=traffic_split,
            start_time=timezone.now(),
            end_time=timezone.now() + timedelta(hours=duration_hours),
            status='active'
        )
        
        return {
            'ab_test_id': ab_test.id,
            'version_a': version_a.version_code,
            'version_b': version_b.version_code,
            'traffic_split': traffic_split,
            'duration_hours': duration_hours
        }
    
    def route_user_to_version(
        self,
        assistant_type: str,
        user_id: int
    ) -> int:
        """
        根據 A/B 測試配置路由用戶到特定版本
        
        Args:
            assistant_type: Assistant 類型
            user_id: 用戶 ID
            
        Returns:
            int: 版本 ID
        """
        # 檢查是否有活躍的 A/B 測試
        ab_test = ABTest.objects.filter(
            assistant_type=assistant_type,
            status='active',
            start_time__lte=timezone.now(),
            end_time__gte=timezone.now()
        ).first()
        
        if not ab_test:
            # 沒有 A/B 測試，返回預設版本
            default_version = SearchAlgorithmVersion.objects.get(
                assistant_type=assistant_type,
                is_default=True
            )
            return default_version.id
        
        # 使用用戶 ID 的哈希值決定版本
        import hashlib
        hash_value = int(hashlib.md5(str(user_id).encode()).hexdigest(), 16)
        user_bucket = (hash_value % 100) / 100.0  # 0.00 - 0.99
        
        if user_bucket < ab_test.traffic_split:
            return ab_test.version_b.id  # 測試版本
        else:
            return ab_test.version_a.id  # 對照版本
```

---

## 📌 實作優先級

### Phase 1: 基礎版本管理 (Week 1)
1. ✅ 創建資料庫表（version, switch_log, routing_log）
2. ✅ 實作 SearchVersionManager
3. ✅ 實作版本 CRUD API
4. ✅ 修改 SmartSearchRouter 支援版本載入

### Phase 2: 前端介面 (Week 2)
1. ✅ 版本列表頁面
2. ✅ 版本配置編輯頁面
3. ✅ 版本切換確認對話框
4. ✅ 版本對比頁面

### Phase 3: 跑分系統整合 (Week 3)
1. ✅ 關聯跑分結果與版本
2. ✅ 自動執行版本跑分
3. ✅ 版本效能對比視覺化

### Phase 4: A/B 測試 (Week 4)
1. ✅ A/B 測試配置表
2. ✅ 用戶路由邏輯
3. ✅ A/B 測試結果分析
4. ✅ 自動化決策支援

---

## 🎯 預期效益

### 開發效益
- ✅ **安全試驗**：新演算法不會覆蓋舊版本
- ✅ **快速回滾**：發現問題可立即切回舊版本
- ✅ **並行測試**：A/B 測試評估真實效果

### 維護效益
- ✅ **歷史追溯**：查看每個版本的配置和效能
- ✅ **量化對比**：精確知道每次改動的影響
- ✅ **知識累積**：保留最佳配置組合

### 業務效益
- ✅ **持續優化**：基於數據迭代改進搜尋品質
- ✅ **風險控制**：漸進式部署降低風險
- ✅ **用戶滿意度**：確保搜尋品質穩定提升

---

## 📊 使用情境

### 情境 1：測試新演算法
```
1. 開發人員改進搜尋邏輯
2. 創建新版本 v2.2.0（狀態: 測試中）
3. 執行跑分測試（對比 baseline v2.1.0）
4. 發現 Precision +3%, Recall +2%, 響應時間 -17ms
5. 部署到生產環境
6. v2.2.0 成為新的預設版本
```

### 情境 2：A/B 測試
```
1. 創建 A/B 測試（v2.1.0 vs v2.2.0）
2. 50% 用戶使用 v2.2.0
3. 收集 24 小時數據
4. 分析：v2.2.0 用戶滿意度 +8%
5. 全量切換到 v2.2.0
```

### 情境 3：緊急回滾
```
1. v2.2.0 部署後發現回應時間異常
2. 立即切換回 v2.1.0（1 分鐘內完成）
3. 問題排查完成後再次部署 v2.2.1
```

---

**下一步**: 確認設計後開始實作 Phase 1 🚀
