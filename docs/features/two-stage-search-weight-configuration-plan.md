# Protocol Assistant 二階段搜尋權重配置規劃

## 📋 專案資訊
- **建立日期**: 2024-11-14
- **目的**: 規劃將第一階段和第二階段搜尋的權重設定獨立配置
- **狀態**: 規劃中（未執行）

---

## 🎯 目標

將 Protocol Assistant 的二階段搜尋系統中的權重參數**全部可配置化**，包括：

### 當前已實現
- ✅ **標題權重** (`title_weight`): 60%（可設定）
- ✅ **內容權重** (`content_weight`): 40%（可設定）
- ✅ 兩者總和必須為 100%

### 規劃新增
- 🎯 **第一階段搜尋權重配置**（段落向量搜尋）
  - 標題向量權重
  - 內容向量權重
  - Threshold 閾值

- 🎯 **第二階段搜尋權重配置**（全文向量搜尋）
  - 文檔級標題權重
  - 文檔級內容權重
  - Threshold 閾值（目前為 master * 0.85）

---

## 📊 當前架構分析

### 1. 資料庫層 - `SearchThresholdSetting` Model

**檔案位置**: `/backend/api/models.py` (Line 1118)

```python
class SearchThresholdSetting(models.Model):
    assistant_type = models.CharField(max_length=50, unique=True)  # 如 'protocol_assistant'
    
    # 主 Threshold（目前用於段落搜尋）
    master_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.70,
        verbose_name="主 Threshold"
    )
    
    # 多向量權重（已實現）
    title_weight = models.IntegerField(default=60)      # 標題權重 (%)
    content_weight = models.IntegerField(default=40)    # 內容權重 (%)
    
    # 其他欄位...
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

**問題分析**:
- ❌ 只有一組 `title_weight` 和 `content_weight`
- ❌ 第一階段和第二階段**共用相同權重**
- ❌ 文檔級 threshold 是硬編碼 `master * 0.85`

---

### 2. 搜尋服務層

#### 2.1 段落搜尋服務 (`SectionSearchService`)
**檔案位置**: `/library/common/knowledge_base/section_search_service.py`

**核心邏輯**:
```python
def search_sections(self, query, source_table, limit=5, threshold=0.7):
    # 步驟 1: 從資料庫讀取權重配置
    title_weight, content_weight = self._get_weights_for_assistant(source_table)
    
    # 步驟 2: 生成查詢向量
    query_embedding = self.embedding_service.generate_embedding(query)
    
    # 步驟 3: SQL 查詢（多向量加權）
    sql = f"""
        SELECT 
            ({title_weight} * (1 - (dse.title_embedding <=> %s::vector))) + 
            ({content_weight} * (1 - (dse.content_embedding <=> %s::vector))) as similarity
        FROM document_section_embeddings dse
        WHERE dse.source_table = %s
          AND similarity >= %s  -- threshold 過濾
    """
```

**特點**:
- ✅ 使用多向量搜尋（title + content）
- ✅ 權重可從資料庫動態載入
- ✅ Threshold 可參數化
- ❌ 第二階段搜尋沒有獨立配置

---

#### 2.2 全文文檔搜尋 (`full_document_search`)
**檔案位置**: `/library/protocol_guide/search_service.py` (Line 302)

**核心邏輯**:
```python
def full_document_search(self, query, top_k=3, threshold=0.5):
    # 步驟 1: 執行段落搜尋（使用段落權重）
    section_results = super().search_knowledge(
        query=cleaned_query,
        limit=top_k * 3,
        use_vector=True,
        threshold=threshold  # ⚠️ 使用傳入的 threshold
    )
    
    # 步驟 2: 擴展為完整文檔
    full_documents = self._expand_to_full_document(section_results)
```

**問題**:
- ❌ 全文搜尋**依賴段落搜尋**的權重配置
- ❌ 沒有獨立的文檔級權重設定
- ❌ 文檔級 threshold 由呼叫者決定，沒有統一配置

---

#### 2.3 基礎搜尋服務 (`BaseKnowledgeBaseSearchService`)
**檔案位置**: `/library/common/knowledge_base/base_search_service.py`

**多模式搜尋支援**:
```python
def search_with_vectors(self, query, limit=5, threshold=0.7, search_mode='auto'):
    if search_mode == 'document_only':
        # 文檔級搜尋：使用 master * 0.85 threshold
        doc_threshold = max(threshold * 0.85, 0.5)
        results = search_with_vectors_generic(...)
    
    elif search_mode == 'section_only':
        # 段落級搜尋：使用 master threshold
        section_results = section_service.search_sections(threshold=threshold)
    
    else:  # 'auto'
        # 自動模式：段落優先，失敗則降級到文檔
        # ...
```

**特點**:
- ✅ 支援三種搜尋模式 (`auto`, `section_only`, `document_only`)
- ❌ 文檔級 threshold 是**硬編碼的 0.85 倍數**
- ❌ 文檔級權重繼承段落權重

---

### 3. API 層 - Dify 外部知識庫端點

**檔案位置**: `/backend/api/views/dify_knowledge_views.py` (Line 318)

**二階段搜尋標記檢測**:
```python
def dify_knowledge_search(request):
    # 檢測 Dify 傳來的特殊標記
    if '__FULL_SEARCH__' in query:
        search_mode = 'document_only'  # 第二階段：全文搜尋
        query = query.replace('__FULL_SEARCH__', '').strip()
    else:
        search_mode = 'auto'  # 第一階段：段落優先
    
    # 三層優先順序 Threshold 管理
    if dify_threshold is not None and dify_threshold > 0:
        score_threshold = dify_threshold  # Dify Studio 設定（最高優先）
    else:
        # 使用 ThresholdManager（資料庫或預設值）
        score_threshold = manager.get_threshold(assistant_type)
```

**流程**:
1. Dify 發送查詢（可能包含 `__FULL_SEARCH__` 標記）
2. 根據標記決定 `search_mode`
3. 傳遞 `threshold` 和 `search_mode` 到搜尋服務
4. 返回結果給 Dify

---

### 4. Threshold 管理器

**檔案位置**: `/library/common/threshold_manager.py`

**核心功能**:
```python
class ThresholdManager:
    def get_threshold(self, assistant_type, dify_threshold=None, threshold_type='master'):
        # 優先級 1: Dify Studio 設定
        if dify_threshold is not None:
            master_threshold = dify_threshold
        else:
            # 優先級 2: 資料庫設定
            if assistant_type in self._cache:
                master_threshold = self._cache[assistant_type]
            else:
                # 優先級 3: 預設值 0.7
                master_threshold = DEFAULT_THRESHOLD
        
        # 根據類型計算衍生 threshold
        if threshold_type == 'document':
            return round(master_threshold * 0.85, 2)  # ⚠️ 硬編碼 0.85
        elif threshold_type == 'keyword':
            return round(master_threshold * 0.5, 2)   # ⚠️ 硬編碼 0.5
        else:
            return master_threshold
```

**問題**:
- ❌ 文檔級和關鍵字級 threshold 的**倍數是硬編碼**（0.85, 0.5）
- ❌ 沒有獨立的權重配置

---

### 5. 前端管理介面

**檔案位置**: `/frontend/src/pages/admin/ThresholdSettingsPage.js`

**當前功能**:
```javascript
const columns = [
  { title: 'Assistant 類型', dataIndex: 'assistant_type_display' },
  { title: '段落向量 Threshold', dataIndex: 'master_threshold' },
  { title: '標題權重', dataIndex: 'title_weight' },  // ✅ 可編輯
  { title: '內容權重', dataIndex: 'content_weight' }, // ✅ 可編輯
  { title: '操作', render: () => <Button onClick={handleEdit}>編輯</Button> }
];
```

**編輯表單**:
- ✅ Master Threshold (Slider 0-100%)
- ✅ 標題權重 (Slider 0-100%)
- ✅ 內容權重 (Slider 0-100%)
- ❌ 缺少第一階段/第二階段獨立配置

---

## 🎯 規劃方案

### 方案一：獨立配置兩階段權重（推薦）

#### 1. 資料庫架構調整

**擴充 `SearchThresholdSetting` Model**:
```python
class SearchThresholdSetting(models.Model):
    # === 現有欄位 ===
    assistant_type = models.CharField(max_length=50, unique=True)
    master_threshold = models.DecimalField(...)  # 保留作為預設值
    
    # === 第一階段搜尋配置（段落向量） ===
    stage1_title_weight = models.IntegerField(
        default=60, 
        verbose_name="第一階段標題權重",
        help_text="段落向量搜尋時的標題權重（0-100）"
    )
    stage1_content_weight = models.IntegerField(
        default=40,
        verbose_name="第一階段內容權重"
    )
    stage1_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.70,
        verbose_name="第一階段 Threshold",
        help_text="段落向量搜尋的相似度閾值"
    )
    
    # === 第二階段搜尋配置（全文向量） ===
    stage2_title_weight = models.IntegerField(
        default=50,
        verbose_name="第二階段標題權重",
        help_text="全文向量搜尋時的標題權重（0-100）"
    )
    stage2_content_weight = models.IntegerField(
        default=50,
        verbose_name="第二階段內容權重"
    )
    stage2_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.60,
        verbose_name="第二階段 Threshold",
        help_text="全文向量搜尋的相似度閾值（建議比第一階段低）"
    )
    
    # === 配置策略 ===
    use_unified_weights = models.BooleanField(
        default=True,
        verbose_name="使用統一權重",
        help_text="若啟用，第一、二階段使用相同權重（向後相容）"
    )
    
    # 原有欄位...
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
```

**向後相容性**:
- 保留 `title_weight` 和 `content_weight`（已廢棄，但保留以免資料遺失）
- 新增 `use_unified_weights` 開關：
  - `True`：第一、二階段使用 `stage1_*` 配置（預設）
  - `False`：第一、二階段使用各自獨立配置

---

#### 2. 搜尋服務層調整

**2.1 `SectionSearchService` 調整**:
```python
class SectionSearchService:
    def _get_weights_for_assistant(self, source_table: str, stage: int = 1) -> tuple:
        """
        獲取權重配置
        
        Args:
            source_table: 來源表 ('protocol_guide', 'rvt_guide')
            stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)
        
        Returns:
            (title_weight, content_weight, threshold) 元組
        """
        from api.models import SearchThresholdSetting
        
        assistant_type = table_to_type.get(source_table)
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        
        if setting.use_unified_weights or stage == 1:
            # 使用第一階段配置
            return (
                setting.stage1_title_weight / 100.0,
                setting.stage1_content_weight / 100.0,
                float(setting.stage1_threshold)
            )
        else:
            # 使用第二階段配置
            return (
                setting.stage2_title_weight / 100.0,
                setting.stage2_content_weight / 100.0,
                float(setting.stage2_threshold)
            )
    
    def search_sections(self, query, source_table, limit=5, threshold=None, stage=1):
        """
        搜尋段落
        
        Args:
            threshold: 外部傳入的 threshold（如 Dify Studio），優先使用
            stage: 搜尋階段標記（用於選擇配置）
        """
        # 獲取配置（包含 threshold）
        title_weight, content_weight, db_threshold = self._get_weights_for_assistant(
            source_table, stage
        )
        
        # Threshold 優先順序：外部傳入 > 資料庫配置
        final_threshold = threshold if threshold is not None else db_threshold
        
        logger.info(
            f"🔍 段落搜尋配置 (Stage {stage}): "
            f"threshold={final_threshold}, "
            f"weights={int(title_weight*100)}%/{int(content_weight*100)}%"
        )
        
        # 執行搜尋...
```

**2.2 `ProtocolGuideSearchService` 調整**:
```python
class ProtocolGuideSearchService(BaseKnowledgeBaseSearchService):
    def section_search(self, query, top_k=5, threshold=0.5):
        """第一階段：段落搜尋"""
        from .section_search_service import SectionSearchService
        section_service = SectionSearchService()
        
        return section_service.search_sections(
            query=query,
            source_table=self.source_table,
            limit=top_k,
            threshold=threshold,
            stage=1  # ✅ 明確標記為第一階段
        )
    
    def full_document_search(self, query, top_k=3, threshold=0.5):
        """第二階段：全文搜尋"""
        # 獲取第二階段配置
        from api.models import SearchThresholdSetting
        
        try:
            setting = SearchThresholdSetting.objects.get(
                assistant_type='protocol_assistant'
            )
            
            if setting.use_unified_weights:
                # 使用第一階段配置
                stage2_threshold = threshold
            else:
                # 使用第二階段獨立配置
                stage2_threshold = float(setting.stage2_threshold)
            
            logger.info(f"📄 全文搜尋 (Stage 2): threshold={stage2_threshold}")
        
        except Exception as e:
            logger.warning(f"無法讀取第二階段配置: {e}")
            stage2_threshold = threshold * 0.85  # 降級到舊版邏輯
        
        # 執行段落搜尋（使用第二階段配置）
        section_results = super().search_knowledge(
            query=cleaned_query,
            limit=top_k * 3,
            use_vector=True,
            threshold=stage2_threshold,
            stage=2  # ✅ 傳遞階段標記
        )
        
        # 擴展為完整文檔
        return self._expand_to_full_document(section_results)
```

---

#### 3. Threshold Manager 調整

**擴充 `ThresholdManager` 支援階段配置**:
```python
class ThresholdManager:
    def get_threshold(
        self, 
        assistant_type: str, 
        dify_threshold: Optional[float] = None,
        stage: int = 1  # ✅ 新增階段參數
    ) -> float:
        """
        獲取 threshold 值
        
        Args:
            stage: 搜尋階段 (1=段落, 2=全文)
        """
        # 優先級 1: Dify Studio 設定（最高優先）
        if dify_threshold is not None:
            return dify_threshold
        
        # 優先級 2: 資料庫設定
        if not self._is_cache_valid():
            self._refresh_cache()
        
        if assistant_type in self._cache:
            setting = self._cache[assistant_type]
            
            if setting['use_unified_weights'] or stage == 1:
                return float(setting['stage1_threshold'])
            else:
                return float(setting['stage2_threshold'])
        
        # 優先級 3: 預設值
        return 0.7 if stage == 1 else 0.6
    
    def get_weights(
        self,
        assistant_type: str,
        stage: int = 1
    ) -> tuple:
        """
        獲取權重配置
        
        Returns:
            (title_weight, content_weight) 元組 (0.0-1.0)
        """
        if assistant_type in self._cache:
            setting = self._cache[assistant_type]
            
            if setting['use_unified_weights'] or stage == 1:
                return (
                    setting['stage1_title_weight'] / 100.0,
                    setting['stage1_content_weight'] / 100.0
                )
            else:
                return (
                    setting['stage2_title_weight'] / 100.0,
                    setting['stage2_content_weight'] / 100.0
                )
        
        # 預設值
        return (0.6, 0.4)
    
    def _load_from_database(self) -> Dict[str, dict]:
        """從資料庫載入完整配置（包含階段配置）"""
        from api.models import SearchThresholdSetting
        
        settings = SearchThresholdSetting.objects.filter(is_active=True)
        
        cache = {}
        for setting in settings:
            cache[setting.assistant_type] = {
                'stage1_threshold': float(setting.stage1_threshold),
                'stage1_title_weight': setting.stage1_title_weight,
                'stage1_content_weight': setting.stage1_content_weight,
                'stage2_threshold': float(setting.stage2_threshold),
                'stage2_title_weight': setting.stage2_title_weight,
                'stage2_content_weight': setting.stage2_content_weight,
                'use_unified_weights': setting.use_unified_weights
            }
        
        return cache
```

---

#### 4. API 層調整

**`dify_knowledge_search` 函數**:
```python
def dify_knowledge_search(request):
    # 檢測搜尋階段
    stage = 1  # 預設第一階段
    if '__FULL_SEARCH__' in query:
        stage = 2  # 第二階段
        search_mode = 'document_only'
        query = query.replace('__FULL_SEARCH__', '').strip()
    else:
        search_mode = 'auto'
    
    # 獲取對應階段的 threshold
    if dify_threshold is not None and dify_threshold > 0:
        score_threshold = dify_threshold
    else:
        manager = get_threshold_manager()
        score_threshold = manager.get_threshold(
            assistant_type=assistant_type,
            stage=stage  # ✅ 傳遞階段資訊
        )
    
    # 執行搜尋
    result = handler.search(
        knowledge_id=knowledge_id,
        query=query,
        top_k=top_k,
        score_threshold=score_threshold,
        search_mode=search_mode,
        stage=stage  # ✅ 傳遞階段資訊
    )
```

---

#### 5. 前端管理介面調整

**5.1 資料表格欄位調整**:
```javascript
const columns = [
  { title: 'Assistant 類型', dataIndex: 'assistant_type_display' },
  
  // 第一階段配置
  { 
    title: '第一階段 Threshold', 
    dataIndex: 'stage1_threshold',
    render: (value) => `${(value * 100).toFixed(0)}%`
  },
  { 
    title: '第一階段權重', 
    render: (_, record) => `${record.stage1_title_weight}% / ${record.stage1_content_weight}%`
  },
  
  // 第二階段配置
  { 
    title: '第二階段 Threshold', 
    dataIndex: 'stage2_threshold',
    render: (value) => `${(value * 100).toFixed(0)}%`
  },
  { 
    title: '第二階段權重', 
    render: (_, record) => `${record.stage2_title_weight}% / ${record.stage2_content_weight}%`
  },
  
  // 配置策略
  {
    title: '配置模式',
    dataIndex: 'use_unified_weights',
    render: (value) => (
      <Tag color={value ? 'green' : 'blue'}>
        {value ? '統一配置' : '獨立配置'}
      </Tag>
    )
  },
  
  { title: '操作', render: () => <Button onClick={handleEdit}>編輯</Button> }
];
```

**5.2 編輯 Modal 調整**:
```javascript
<Modal title="編輯 Threshold 設定" visible={editModalVisible}>
  <Form form={form}>
    {/* 配置模式選擇 */}
    <Form.Item 
      name="use_unified_weights" 
      label="配置模式"
      valuePropName="checked"
    >
      <Switch 
        checkedChildren="統一配置" 
        unCheckedChildren="獨立配置"
        onChange={(checked) => {
          // 如果切換到統一配置，自動同步第二階段到第一階段
          if (checked) {
            const stage1Values = {
              stage2_threshold: form.getFieldValue('stage1_threshold'),
              stage2_title_weight: form.getFieldValue('stage1_title_weight'),
              stage2_content_weight: form.getFieldValue('stage1_content_weight')
            };
            form.setFieldsValue(stage1Values);
          }
        }}
      />
    </Form.Item>
    
    <Divider>第一階段配置（段落搜尋）</Divider>
    
    {/* 第一階段 Threshold */}
    <Form.Item name="stage1_threshold" label="段落搜尋 Threshold">
      <Slider min={0} max={100} marks={{ 0: '0%', 50: '50%', 100: '100%' }} />
    </Form.Item>
    
    {/* 第一階段標題權重 */}
    <Form.Item name="stage1_title_weight" label="標題權重">
      <Slider 
        min={0} 
        max={100}
        onChange={(value) => {
          // 自動調整內容權重
          form.setFieldsValue({ stage1_content_weight: 100 - value });
        }}
      />
    </Form.Item>
    
    {/* 第一階段內容權重 */}
    <Form.Item name="stage1_content_weight" label="內容權重">
      <Slider 
        min={0} 
        max={100}
        onChange={(value) => {
          form.setFieldsValue({ stage1_title_weight: 100 - value });
        }}
      />
    </Form.Item>
    
    <Divider>第二階段配置（全文搜尋）</Divider>
    
    {/* 第二階段配置（如果啟用獨立配置才顯示） */}
    {!form.getFieldValue('use_unified_weights') && (
      <>
        <Form.Item name="stage2_threshold" label="全文搜尋 Threshold">
          <Slider min={0} max={100} />
        </Form.Item>
        
        <Form.Item name="stage2_title_weight" label="標題權重">
          <Slider 
            min={0} 
            max={100}
            onChange={(value) => {
              form.setFieldsValue({ stage2_content_weight: 100 - value });
            }}
          />
        </Form.Item>
        
        <Form.Item name="stage2_content_weight" label="內容權重">
          <Slider 
            min={0} 
            max={100}
            onChange={(value) => {
              form.setFieldsValue({ stage2_title_weight: 100 - value });
            }}
          />
        </Form.Item>
      </>
    )}
    
    {form.getFieldValue('use_unified_weights') && (
      <Alert 
        message="當前使用統一配置模式" 
        description="第二階段將自動使用第一階段的配置" 
        type="info" 
      />
    )}
  </Form>
</Modal>
```

---

## 📝 實施步驟

### Phase 1: 資料庫遷移（1-2 小時）
1. ✅ 修改 `SearchThresholdSetting` Model
2. ✅ 創建 Django migration
3. ✅ 執行 migration
4. ✅ 更新 Serializer（`api/serializers.py`）

### Phase 2: 後端邏輯調整（2-3 小時）
5. ✅ 擴充 `ThresholdManager`（新增 `stage` 參數）
6. ✅ 修改 `SectionSearchService._get_weights_for_assistant()`
7. ✅ 修改 `ProtocolGuideSearchService.section_search()`
8. ✅ 修改 `ProtocolGuideSearchService.full_document_search()`
9. ✅ 修改 `dify_knowledge_search()` API

### Phase 3: 前端介面調整（2-3 小時）
10. ✅ 修改 `ThresholdSettingsPage.js`
    - 資料表格欄位擴充
    - 編輯 Modal 欄位擴充
    - 表單驗證邏輯調整

### Phase 4: 測試與驗證（2-3 小時）
11. ✅ 單元測試（`test_threshold_manager.py`）
12. ✅ 整合測試（`test_two_stage_search.py`）
13. ✅ Dify 整合測試
14. ✅ 前端 UI 測試

### Phase 5: 文檔與部署（1 小時）
15. ✅ 更新 API 文檔
16. ✅ 更新操作手冊
17. ✅ 部署到測試環境
18. ✅ 部署到生產環境

**預估總時數**: 8-12 小時

---

## 🎯 預期效果

### 1. 靈活性提升
- ✅ 第一階段和第二階段可獨立調整權重
- ✅ 針對不同查詢特性優化搜尋結果
- ✅ A/B 測試不同配置的效果

### 2. 精準度提升
**第一階段（段落搜尋）**:
- 高 threshold（如 0.7）：精準匹配
- 標題權重高（如 70%）：重視標題相關性

**第二階段（全文搜尋）**:
- 低 threshold（如 0.5-0.6）：更寬鬆匹配
- 內容權重高（如 60%）：重視內容完整性

### 3. 使用者體驗改善
- 管理員可以根據實際使用情況調整配置
- 不需要修改程式碼即可優化搜尋效果
- 支援「統一配置」和「獨立配置」模式

---

## ⚠️ 風險與注意事項

### 1. 向後相容性
- ✅ 保留舊的 `title_weight` 和 `content_weight` 欄位
- ✅ 預設啟用 `use_unified_weights`（行為與現有系統一致）
- ✅ Migration 自動填充預設值

### 2. 效能影響
- ⚠️ 快取機制需要擴充以包含階段配置
- ⚠️ 每次搜尋需要額外判斷階段配置
- ✅ 影響可忽略不計（< 1ms）

### 3. UI 複雜度
- ⚠️ 設定頁面欄位增加（可能讓使用者困惑）
- ✅ 解決方案：提供「統一配置」預設模式
- ✅ 提供詳細的說明文字和提示

### 4. 測試成本
- ⚠️ 需要測試多種配置組合
- ⚠️ 需要驗證 Dify 整合是否正常
- ✅ 可透過自動化測試降低成本

---

## 🔄 替代方案

### 方案二：使用倍數配置（簡化版）

**不新增獨立欄位，而是配置倍數**:
```python
class SearchThresholdSetting(models.Model):
    # 第一階段配置（保持不變）
    stage1_threshold = models.DecimalField(default=0.70)
    stage1_title_weight = models.IntegerField(default=60)
    stage1_content_weight = models.IntegerField(default=40)
    
    # 第二階段倍數
    stage2_threshold_multiplier = models.DecimalField(
        default=0.85,
        verbose_name="第二階段 Threshold 倍數",
        help_text="第二階段 threshold = 第一階段 * 倍數"
    )
    stage2_title_weight_delta = models.IntegerField(
        default=0,
        verbose_name="第二階段標題權重調整",
        help_text="第二階段標題權重 = 第一階段 + 調整值"
    )
```

**優點**:
- 實施成本低（2-3 小時）
- UI 簡單（只需調整倍數和增量）
- 向後相容性好

**缺點**:
- 靈活性較低
- 倍數和增量概念可能不直觀

---

## 📊 建議的預設配置

### Protocol Assistant

| 項目 | 第一階段（段落） | 第二階段（全文） | 說明 |
|------|----------------|----------------|------|
| **Threshold** | 0.70 (70%) | 0.60 (60%) | 第二階段較寬鬆 |
| **標題權重** | 60% | 50% | 第二階段標題重要性降低 |
| **內容權重** | 40% | 50% | 第二階段內容重要性提升 |
| **配置模式** | 統一配置 | - | 預設使用統一配置 |

**理由**:
1. **第一階段重視精準度**：高 threshold + 高標題權重
2. **第二階段重視召回率**：低 threshold + 平衡權重
3. **預設統一配置**：向後相容，降低使用門檻

---

## 📚 相關文件

- **當前實作**: `docs/features/protocol-assistant-vector-database-setup.md`
- **Threshold 管理**: `library/common/threshold_manager.py`
- **搜尋服務**: `library/protocol_guide/search_service.py`
- **前端介面**: `frontend/src/pages/admin/ThresholdSettingsPage.js`

---

## ✅ 結論

**推薦採用方案一（獨立配置兩階段權重）**:
- 提供最大靈活性
- 預設統一配置模式保證向後相容
- UI 設計合理，使用者可選擇複雜度
- 實施成本合理（8-12 小時）

**實施優先順序**:
1. 🔥 **高優先級**: Phase 1-2（資料庫 + 後端邏輯）
2. 📊 **中優先級**: Phase 3（前端介面）
3. ✅ **低優先級**: Phase 4-5（測試與文檔）

---

**規劃完成日期**: 2024-11-14  
**規劃狀態**: ✅ 已完成，待決策是否執行  
**預估工作量**: 8-12 小時（1-2 個工作日）
