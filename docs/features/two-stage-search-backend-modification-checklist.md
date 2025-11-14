# 二階段搜尋權重配置 - 後端修改檢查清單

## 📋 文件資訊
- **建立日期**: 2025-11-14
- **目的**: 列出所有需要修改的後端檔案和具體修改點
- **狀態**: 規劃中（未執行）
- **相關文件**: `two-stage-search-weight-configuration-plan.md`

---

## 🎯 修改概覽

### 核心修改策略
1. **Model 新增欄位**：擴充 `SearchThresholdSetting` Model 支援兩階段配置
2. **權重讀取邏輯**：所有讀取權重的地方需支援 `stage` 參數
3. **Threshold Manager**：擴充支援階段配置和快取
4. **搜尋服務層**：傳遞 `stage` 參數到底層
5. **Serializer 調整**：支援新欄位的序列化和驗證

---

## 📝 詳細修改清單

### 1️⃣ 資料庫層 (1 個檔案)

#### 檔案：`backend/api/models.py`
**位置**：Line 1118 開始的 `SearchThresholdSetting` class

**修改類型**：新增欄位

**需要新增的欄位**：
```python
class SearchThresholdSetting(models.Model):
    # === 現有欄位（保留） ===
    assistant_type = models.CharField(...)
    master_threshold = models.DecimalField(...)  # 保留向後相容
    title_weight = models.IntegerField(default=60)  # 保留向後相容
    content_weight = models.IntegerField(default=40)  # 保留向後相容
    description = models.TextField(...)
    is_active = models.BooleanField(...)
    created_at = models.DateTimeField(...)
    updated_at = models.DateTimeField(...)
    updated_by = models.ForeignKey(...)
    
    # === 🆕 第一階段配置 ===
    stage1_title_weight = models.IntegerField(
        default=60,
        verbose_name="第一階段標題權重",
        help_text="段落向量搜尋時的標題權重（0-100）"
    )
    stage1_content_weight = models.IntegerField(
        default=40,
        verbose_name="第一階段內容權重",
        help_text="段落向量搜尋時的內容權重（0-100）"
    )
    stage1_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.70,
        verbose_name="第一階段 Threshold",
        help_text="段落向量搜尋的相似度閾值（0.00-1.00）"
    )
    
    # === 🆕 第二階段配置 ===
    stage2_title_weight = models.IntegerField(
        default=50,
        verbose_name="第二階段標題權重",
        help_text="全文向量搜尋時的標題權重（0-100）"
    )
    stage2_content_weight = models.IntegerField(
        default=50,
        verbose_name="第二階段內容權重",
        help_text="全文向量搜尋時的內容權重（0-100）"
    )
    stage2_threshold = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.60,
        verbose_name="第二階段 Threshold",
        help_text="全文向量搜尋的相似度閾值（建議比第一階段低）"
    )
    
    # === 🆕 配置策略 ===
    use_unified_weights = models.BooleanField(
        default=True,
        verbose_name="使用統一權重",
        help_text="若啟用，第一、二階段使用相同權重（向後相容）"
    )
```

**需要修改的方法**：
```python
def get_calculated_thresholds(self):
    """計算所有 threshold 值（需要更新以支援兩階段）"""
    # ⚠️ 這個方法可能需要調整或廢棄
    pass

def save(self, *args, **kwargs):
    """儲存前驗證（需要擴充以驗證新欄位）"""
    # ✅ 需要添加 stage1_* 和 stage2_* 的驗證邏輯
    # ✅ 確保兩階段的 title_weight + content_weight = 100
    pass
```

**Migration 步驟**：
```bash
# 1. 創建 migration
docker exec ai-django python manage.py makemigrations

# 2. 檢查 migration 內容
# 應該會創建一個新的 migration 檔案，包含 7 個新欄位

# 3. 執行 migration
docker exec ai-django python manage.py migrate

# 4. 驗證欄位已添加
docker exec postgres_db psql -U postgres -d ai_platform -c "\d search_threshold_settings"
```

**資料遷移腳本（可選）**：
```python
# 將現有的 title_weight/content_weight 複製到 stage1_* 欄位
from api.models import SearchThresholdSetting

for setting in SearchThresholdSetting.objects.all():
    setting.stage1_title_weight = setting.title_weight
    setting.stage1_content_weight = setting.content_weight
    setting.stage1_threshold = setting.master_threshold
    
    # 第二階段使用建議值
    setting.stage2_title_weight = 50
    setting.stage2_content_weight = 50
    setting.stage2_threshold = float(setting.master_threshold) * 0.85
    
    setting.use_unified_weights = True  # 預設統一配置
    setting.save()
```

---

### 2️⃣ Serializer 層 (1 個檔案)

#### 檔案：`backend/api/serializers.py`
**位置**：Line 350 開始的 `SearchThresholdSettingSerializer` class

**修改類型**：擴充欄位和驗證邏輯

**需要修改的部分**：

**1. 擴充 Meta.fields**：
```python
class SearchThresholdSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchThresholdSetting
        fields = [
            'id',
            'assistant_type',
            'assistant_type_display',
            
            # 現有欄位（保留向後相容）
            'master_threshold',
            'title_weight',
            'content_weight',
            
            # 🆕 第一階段配置
            'stage1_threshold',
            'stage1_title_weight',
            'stage1_content_weight',
            
            # 🆕 第二階段配置
            'stage2_threshold',
            'stage2_title_weight',
            'stage2_content_weight',
            
            # 🆕 配置策略
            'use_unified_weights',
            
            # 其他欄位
            'description',
            'is_active',
            'created_at',
            'updated_at',
            'updated_by',
            'updated_by_username'
        ]
        read_only_fields = ['created_at', 'updated_at', 'assistant_type_display', 'updated_by_username']
```

**2. 新增驗證方法**：
```python
def validate_stage1_title_weight(self, value):
    """驗證第一階段標題權重範圍"""
    if not 0 <= value <= 100:
        raise serializers.ValidationError("第一階段標題權重必須在 0 到 100 之間")
    return value

def validate_stage1_content_weight(self, value):
    """驗證第一階段內容權重範圍"""
    if not 0 <= value <= 100:
        raise serializers.ValidationError("第一階段內容權重必須在 0 到 100 之間")
    return value

def validate_stage2_title_weight(self, value):
    """驗證第二階段標題權重範圍"""
    if not 0 <= value <= 100:
        raise serializers.ValidationError("第二階段標題權重必須在 0 到 100 之間")
    return value

def validate_stage2_content_weight(self, value):
    """驗證第二階段內容權重範圍"""
    if not 0 <= value <= 100:
        raise serializers.ValidationError("第二階段內容權重必須在 0 到 100 之間")
    return value

def validate_stage1_threshold(self, value):
    """驗證第一階段 threshold 範圍"""
    if not 0 <= value <= 1:
        raise serializers.ValidationError("第一階段 Threshold 必須在 0.00 到 1.00 之間")
    return value

def validate_stage2_threshold(self, value):
    """驗證第二階段 threshold 範圍"""
    if not 0 <= value <= 1:
        raise serializers.ValidationError("第二階段 Threshold 必須在 0.00 到 1.00 之間")
    return value
```

**3. 修改 validate() 方法**：
```python
def validate(self, attrs):
    """跨欄位驗證（確保權重總和為 100）"""
    # 第一階段權重驗證
    stage1_title = attrs.get('stage1_title_weight', 
                             getattr(self.instance, 'stage1_title_weight', 60) if self.instance else 60)
    stage1_content = attrs.get('stage1_content_weight',
                               getattr(self.instance, 'stage1_content_weight', 40) if self.instance else 40)
    
    if stage1_title + stage1_content != 100:
        raise serializers.ValidationError({
            'non_field_errors': ['第一階段：標題權重與內容權重的總和必須為 100%']
        })
    
    # 如果不使用統一配置，驗證第二階段權重
    use_unified = attrs.get('use_unified_weights',
                           getattr(self.instance, 'use_unified_weights', True) if self.instance else True)
    
    if not use_unified:
        stage2_title = attrs.get('stage2_title_weight',
                                getattr(self.instance, 'stage2_title_weight', 50) if self.instance else 50)
        stage2_content = attrs.get('stage2_content_weight',
                                  getattr(self.instance, 'stage2_content_weight', 50) if self.instance else 50)
        
        if stage2_title + stage2_content != 100:
            raise serializers.ValidationError({
                'non_field_errors': ['第二階段：標題權重與內容權重的總和必須為 100%']
            })
    
    # ⚠️ 保留舊欄位驗證以向後相容（但可能會廢棄）
    title_weight = attrs.get('title_weight', getattr(self.instance, 'title_weight', 60) if self.instance else 60)
    content_weight = attrs.get('content_weight', getattr(self.instance, 'content_weight', 40) if self.instance else 40)
    
    if title_weight + content_weight != 100:
        raise serializers.ValidationError({
            'non_field_errors': ['標題權重與內容權重的總和必須為 100%']
        })
    
    return attrs
```

---

### 3️⃣ Threshold Manager (1 個檔案)

#### 檔案：`library/common/threshold_manager.py`
**位置**：整個檔案需要調整

**修改類型**：擴充方法支援 `stage` 參數

**需要修改的方法**：

**1. `_load_from_database()` 方法**：
```python
def _load_from_database(self) -> Dict[str, dict]:
    """從資料庫載入 threshold 設定（擴充為載入完整配置）"""
    try:
        from api.models import SearchThresholdSetting
        
        settings = SearchThresholdSetting.objects.filter(is_active=True)
        
        cache = {}
        for setting in settings:
            # ✅ 儲存完整配置（包含兩階段）
            cache[setting.assistant_type] = {
                # 第一階段
                'stage1_threshold': float(setting.stage1_threshold),
                'stage1_title_weight': setting.stage1_title_weight,
                'stage1_content_weight': setting.stage1_content_weight,
                
                # 第二階段
                'stage2_threshold': float(setting.stage2_threshold),
                'stage2_title_weight': setting.stage2_title_weight,
                'stage2_content_weight': setting.stage2_content_weight,
                
                # 配置策略
                'use_unified_weights': setting.use_unified_weights,
                
                # 舊欄位（向後相容）
                'master_threshold': float(setting.master_threshold),
                'title_weight': setting.title_weight,
                'content_weight': setting.content_weight
            }
            
            self.logger.debug(
                f"載入設定: {setting.assistant_type} = "
                f"Stage1({setting.stage1_threshold}/{setting.stage1_title_weight}%) "
                f"Stage2({setting.stage2_threshold}/{setting.stage2_title_weight}%)"
            )
        
        self.logger.info(f"📊 從資料庫載入 {len(cache)} 個 threshold 設定")
        return cache
        
    except Exception as e:
        self.logger.error(f"從資料庫載入 threshold 失敗: {e}")
        return {}
```

**2. `get_threshold()` 方法（新增 `stage` 參數）**：
```python
def get_threshold(
    self,
    assistant_type: str,
    dify_threshold: Optional[float] = None,
    threshold_type: str = 'master',  # ⚠️ 這個參數可能需要廢棄
    stage: int = 1  # 🆕 新增階段參數
) -> float:
    """
    獲取 threshold 值（支援兩階段配置）
    
    優先順序：
    1. dify_threshold（Dify Studio 設定）- 最高優先
    2. Database threshold（Web 管理介面設定）- 中等優先
    3. DEFAULT_THRESHOLD - 最低優先
    
    Args:
        assistant_type: Assistant 類型
        dify_threshold: Dify Studio 傳來的 threshold（可選）
        threshold_type: 已廢棄，保留以向後相容
        stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)
    
    Returns:
        float: Threshold 值
    """
    # 優先級 1：Dify Studio 設定（最高優先）
    if dify_threshold is not None:
        self.logger.info(
            f"🎯 使用 Dify Studio threshold: {dify_threshold} "
            f"(assistant={assistant_type}, stage={stage})"
        )
        return dify_threshold
    
    # 優先級 2：資料庫設定
    if not self._is_cache_valid():
        self._refresh_cache()
    
    if assistant_type in self._cache:
        config = self._cache[assistant_type]
        
        # 根據配置策略選擇 threshold
        if config['use_unified_weights'] or stage == 1:
            # 使用第一階段配置
            threshold = config['stage1_threshold']
            self.logger.info(
                f"📊 使用第一階段 threshold: {threshold} "
                f"(assistant={assistant_type}, stage={stage})"
            )
        else:
            # 使用第二階段配置
            threshold = config['stage2_threshold']
            self.logger.info(
                f"📊 使用第二階段 threshold: {threshold} "
                f"(assistant={assistant_type}, stage={stage})"
            )
        
        return threshold
    
    # 優先級 3：預設值
    default_threshold = 0.7 if stage == 1 else 0.6
    self.logger.info(
        f"⚙️ 使用預設 threshold: {default_threshold} "
        f"(assistant={assistant_type}, stage={stage}, 資料庫無設定)"
    )
    return default_threshold
```

**3. 新增 `get_weights()` 方法**：
```python
def get_weights(
    self,
    assistant_type: str,
    stage: int = 1
) -> tuple:
    """
    獲取權重配置
    
    Args:
        assistant_type: Assistant 類型
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        (title_weight, content_weight) 元組 (0.0-1.0)
    """
    # 檢查快取
    if not self._is_cache_valid():
        self._refresh_cache()
    
    if assistant_type in self._cache:
        config = self._cache[assistant_type]
        
        # 根據配置策略選擇權重
        if config['use_unified_weights'] or stage == 1:
            # 使用第一階段配置
            title_weight = config['stage1_title_weight'] / 100.0
            content_weight = config['stage1_content_weight'] / 100.0
            self.logger.debug(
                f"載入第一階段權重: {assistant_type} -> "
                f"{config['stage1_title_weight']}% / {config['stage1_content_weight']}%"
            )
        else:
            # 使用第二階段配置
            title_weight = config['stage2_title_weight'] / 100.0
            content_weight = config['stage2_content_weight'] / 100.0
            self.logger.debug(
                f"載入第二階段權重: {assistant_type} -> "
                f"{config['stage2_title_weight']}% / {config['stage2_content_weight']}%"
            )
        
        return (title_weight, content_weight)
    
    # 預設值
    self.logger.warning(f"找不到 {assistant_type} 的權重配置，使用預設 60/40")
    return (0.6, 0.4)
```

**4. 新增 `get_all_thresholds()` 擴充**：
```python
def get_all_thresholds(
    self,
    assistant_type: str,
    dify_threshold: Optional[float] = None,
    stage: int = 1  # 🆕 新增階段參數
) -> Dict[str, float]:
    """
    獲取所有類型的 threshold（支援兩階段）
    
    Args:
        assistant_type: Assistant 類型
        dify_threshold: Dify Studio 傳來的 threshold（可選）
        stage: 搜尋階段
    
    Returns:
        dict: 包含所有 threshold 類型
            {
                'stage1_threshold': 0.70,
                'stage2_threshold': 0.60,
                'stage1_title_weight': 60,
                'stage1_content_weight': 40,
                'stage2_title_weight': 50,
                'stage2_content_weight': 50
            }
    """
    threshold = self.get_threshold(assistant_type, dify_threshold, stage=stage)
    title_weight, content_weight = self.get_weights(assistant_type, stage)
    
    return {
        'threshold': threshold,
        'title_weight': int(title_weight * 100),
        'content_weight': int(content_weight * 100),
        'stage': stage
    }
```

**5. 便利函數更新**：
```python
# 在檔案末尾更新便利函數

def get_threshold(
    assistant_type: str,
    dify_threshold: Optional[float] = None,
    threshold_type: str = 'master',  # 已廢棄
    stage: int = 1  # 🆕 新增
) -> float:
    """獲取 threshold 值（便利函數）"""
    manager = get_threshold_manager()
    return manager.get_threshold(assistant_type, dify_threshold, threshold_type, stage)


def get_weights(
    assistant_type: str,
    stage: int = 1  # 🆕 新增
) -> tuple:
    """
    獲取權重配置（便利函數）
    
    Returns:
        (title_weight, content_weight) 元組 (0.0-1.0)
    """
    manager = get_threshold_manager()
    return manager.get_weights(assistant_type, stage)
```

---

### 4️⃣ 搜尋服務層 (3 個檔案)

#### 檔案 1：`library/common/knowledge_base/section_search_service.py`
**位置**：`_get_weights_for_assistant()` 和 `search_sections()` 方法

**修改類型**：新增 `stage` 參數支援

**修改 1：`_get_weights_for_assistant()` 方法**：
```python
def _get_weights_for_assistant(self, source_table: str, stage: int = 1) -> tuple:
    """
    根據 source_table 獲取對應的權重配置（支援兩階段）
    
    Args:
        source_table: 來源表名 ('protocol_guide', 'rvt_guide')
        stage: 搜尋階段 (1=段落搜尋, 2=全文搜尋)
    
    Returns:
        tuple: (title_weight, content_weight, threshold) 範圍 0.0-1.0
    """
    from api.models import SearchThresholdSetting
    
    # 映射表名到助手類型
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
    }
    
    assistant_type = table_to_type.get(source_table)
    if not assistant_type:
        logger.warning(f"未知的 source_table: {source_table}，使用預設權重 60/40")
        return (0.6, 0.4, 0.7)
    
    try:
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        
        # 根據配置策略選擇權重
        if setting.use_unified_weights or stage == 1:
            # 使用第一階段配置
            title_weight = setting.stage1_title_weight / 100.0
            content_weight = setting.stage1_content_weight / 100.0
            threshold = float(setting.stage1_threshold)
            logger.info(
                f"📊 載入第一階段搜尋權重配置: {assistant_type} -> "
                f"標題 {setting.stage1_title_weight}% / 內容 {setting.stage1_content_weight}% / "
                f"threshold {threshold}"
            )
        else:
            # 使用第二階段配置
            title_weight = setting.stage2_title_weight / 100.0
            content_weight = setting.stage2_content_weight / 100.0
            threshold = float(setting.stage2_threshold)
            logger.info(
                f"📊 載入第二階段搜尋權重配置: {assistant_type} -> "
                f"標題 {setting.stage2_title_weight}% / 內容 {setting.stage2_content_weight}% / "
                f"threshold {threshold}"
            )
        
        return (title_weight, content_weight, threshold)
        
    except SearchThresholdSetting.DoesNotExist:
        logger.warning(f"找不到 {assistant_type} 的權重配置，使用預設 60/40/0.7")
        return (0.6, 0.4, 0.7)
    except Exception as e:
        logger.error(f"讀取權重配置失敗: {str(e)}，使用預設值")
        return (0.6, 0.4, 0.7)
```

**修改 2：`search_sections()` 方法簽名**：
```python
def search_sections(
    self,
    query: str,
    source_table: str,
    min_level: Optional[int] = None,
    max_level: Optional[int] = None,
    limit: int = 5,
    threshold: Optional[float] = None,  # ⚠️ 改為可選
    stage: int = 1  # 🆕 新增階段參數
) -> List[Dict[str, Any]]:
    """
    搜尋段落（支援兩階段配置）
    
    Args:
        query: 查詢文本
        source_table: 來源表名 (如 'protocol_guide')
        min_level: 最小標題層級 (1-6)
        max_level: 最大標題層級 (1-6)
        limit: 返回結果數量
        threshold: 外部傳入的 threshold（優先使用），如為 None 則使用資料庫配置
        stage: 搜尋階段 (1=段落, 2=全文)
    """
    try:
        # 🆕 獲取配置（包含 threshold）
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
        
        # ... 後續邏輯保持不變，使用 final_threshold
```

---

#### 檔案 2：`library/common/knowledge_base/vector_search_helper.py`
**位置**：`_get_weights_for_assistant()` 函數

**修改類型**：新增 `stage` 參數支援

```python
def _get_weights_for_assistant(source_table: str, stage: int = 1) -> tuple:
    """
    根據 source_table 獲取權重配置（支援兩階段）
    
    Args:
        source_table: 向量表中的 source_table 值 (如 'protocol_guide')
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        (title_weight, content_weight) 元組，值為 0.0-1.0 的浮點數
    """
    from api.models import SearchThresholdSetting
    
    # 映射 source_table 到 assistant_type
    table_to_type = {
        'protocol_guide': 'protocol_assistant',
        'rvt_guide': 'rvt_assistant',
        'know_issue': 'know_issue_assistant',
    }
    
    assistant_type = table_to_type.get(source_table)
    if not assistant_type:
        logger.warning(f"未知的 source_table: {source_table}，使用預設權重 60/40")
        return 0.6, 0.4
    
    try:
        setting = SearchThresholdSetting.objects.get(assistant_type=assistant_type)
        
        # 根據配置策略選擇權重
        if setting.use_unified_weights or stage == 1:
            # 使用第一階段配置
            title_weight = setting.stage1_title_weight / 100.0
            content_weight = setting.stage1_content_weight / 100.0
            logger.info(
                f"載入第一階段權重配置: {assistant_type} -> "
                f"標題 {setting.stage1_title_weight}% / 內容 {setting.stage1_content_weight}%"
            )
        else:
            # 使用第二階段配置
            title_weight = setting.stage2_title_weight / 100.0
            content_weight = setting.stage2_content_weight / 100.0
            logger.info(
                f"載入第二階段權重配置: {assistant_type} -> "
                f"標題 {setting.stage2_title_weight}% / 內容 {setting.stage2_content_weight}%"
            )
        
        return title_weight, content_weight
        
    except SearchThresholdSetting.DoesNotExist:
        logger.warning(f"找不到 {assistant_type} 的權重配置，使用預設值 60/40")
        return 0.6, 0.4
    except Exception as e:
        logger.error(f"讀取權重配置失敗: {str(e)}，使用預設值 60/40")
        return 0.6, 0.4
```

**⚠️ 注意**：`search_with_vectors_generic()` 函數也需要新增 `stage` 參數：
```python
def search_with_vectors_generic(
    query: str,
    model_class: Type[models.Model],
    source_table: str,
    limit: int = 5,
    threshold: float = 0.0,
    use_1024: bool = True,
    content_formatter: Optional[Callable] = None,
    stage: int = 1  # 🆕 新增階段參數
) -> List[Dict[str, Any]]:
    """通用向量搜尋函數（支援兩階段配置）"""
    try:
        # 步驟 1: 讀取權重配置（傳遞 stage）
        title_weight, content_weight = _get_weights_for_assistant(source_table, stage)
        
        # ... 後續邏輯保持不變
```

---

#### 檔案 3：`library/protocol_guide/search_service.py`
**位置**：`section_search()` 和 `full_document_search()` 方法

**修改類型**：明確傳遞 `stage` 參數

**修改 1：`section_search()` 方法**：
```python
def section_search(self, query: str, top_k: int = 5, threshold: float = 0.5) -> list:
    """
    第一階段：段落搜尋
    
    Args:
        query: 搜尋查詢
        top_k: 返回前 K 個結果
        threshold: 相似度閾值
    
    Returns:
        List[Dict]: 段落搜尋結果
    """
    try:
        from .section_search_service import SectionSearchService
        section_service = SectionSearchService()
        
        # ✅ 明確標記為第一階段
        results = section_service.search_sections(
            query=query,
            source_table=self.source_table,
            limit=top_k,
            threshold=threshold,
            stage=1  # 🆕 明確標記為第一階段
        )
        
        # ... 格式化邏輯保持不變
```

**修改 2：`full_document_search()` 方法**：
```python
def full_document_search(self, query: str, top_k: int = 3, threshold: float = 0.5) -> list:
    """
    第二階段：全文搜尋
    
    Args:
        query: 搜尋查詢
        top_k: 返回前 K 個文檔
        threshold: 相似度閾值
    
    Returns:
        List[Dict]: 全文文檔搜尋結果
    """
    try:
        # 🆕 獲取第二階段配置
        from api.models import SearchThresholdSetting
        
        try:
            setting = SearchThresholdSetting.objects.get(
                assistant_type='protocol_assistant'
            )
            
            if setting.use_unified_weights:
                # 使用統一配置（第一階段配置）
                stage2_threshold = threshold
                logger.info(f"📄 全文搜尋 (統一配置): threshold={stage2_threshold}")
            else:
                # 使用第二階段獨立配置
                stage2_threshold = float(setting.stage2_threshold)
                logger.info(f"📄 全文搜尋 (Stage 2 獨立配置): threshold={stage2_threshold}")
        
        except Exception as e:
            # 降級到舊版邏輯
            logger.warning(f"無法讀取第二階段配置: {e}，降級到 threshold * 0.85")
            stage2_threshold = threshold * 0.85
        
        # 強制使用文檔級搜尋
        _, cleaned_query = self._classify_and_clean_query(query)
        
        # 執行向量搜尋（使用第二階段配置）
        section_results = super().search_knowledge(
            query=cleaned_query,
            limit=top_k * 3,
            use_vector=True,
            threshold=stage2_threshold,
            stage=2  # 🆕 傳遞階段標記
        )
        
        # 擴展為完整文檔
        full_documents = self._expand_to_full_document(section_results)
        
        # ... 後續邏輯保持不變
```

---

### 5️⃣ API Views 層 (1 個檔案)

#### 檔案：`backend/api/views/dify_knowledge_views.py`
**位置**：`dify_knowledge_search()` 函數 (Line 318 附近)

**修改類型**：檢測階段並傳遞給搜尋服務

**修改內容**：
```python
def dify_knowledge_search(request):
    """Dify 統一知識庫搜索 API"""
    try:
        # ... 前面邏輯保持不變
        
        # 🔍 檢測特殊標記 __FULL_SEARCH__（二階段搜尋 Stage 2 標記）
        search_mode = 'auto'  # 預設為 'auto'（段落搜尋）
        stage = 1  # 🆕 預設第一階段
        
        if '__FULL_SEARCH__' in query:
            # 檢測到 Stage 2 標記
            search_mode = 'document_only'  # 切換為全文搜尋
            stage = 2  # 🆕 設定為第二階段
            query = query.replace('__FULL_SEARCH__', '').strip()
            logger.info(f"🎯 檢測到 Stage 2 標記，切換到全文搜尋模式")
            logger.info(f"🧹 清理後查詢: '{query}'")
        
        # ... inputs 檢查邏輯保持不變
        
        # 🎯 三層優先順序 Threshold 管理
        dify_threshold = retrieval_setting.get('score_threshold')
        
        if dify_threshold is not None and dify_threshold > 0:
            score_threshold = dify_threshold
            logger.info(
                f"🎯 [優先級 1] 使用 Dify Studio threshold={score_threshold} | "
                f"knowledge_id='{knowledge_id}' | query='{query}' | "
                f"search_mode='{search_mode}' | stage={stage}"  # 🆕 記錄階段
            )
        else:
            try:
                from library.common.threshold_manager import get_threshold_manager
                
                assistant_type_mapping = {
                    'protocol_assistant': 'protocol_assistant',
                    'protocol_guide': 'protocol_assistant',
                    'protocol_guide_db': 'protocol_assistant',
                    'rvt_guide': 'rvt_assistant',
                    'rvt_guide_db': 'rvt_assistant',
                    'rvt_assistant': 'rvt_assistant',
                }
                assistant_type = assistant_type_mapping.get(knowledge_id, 'protocol_assistant')
                
                manager = get_threshold_manager()
                # 🆕 傳遞 stage 參數
                score_threshold = manager.get_threshold(
                    assistant_type=assistant_type,
                    dify_threshold=None,
                    stage=stage  # 🆕 傳遞階段資訊
                )
                
                logger.info(
                    f"📊 [優先級 2/3] Dify 未設定，使用 ThresholdManager threshold={score_threshold} | "
                    f"assistant_type='{assistant_type}' | knowledge_id='{knowledge_id}' | "
                    f"query='{query}' | search_mode='{search_mode}' | stage={stage}"  # 🆕 記錄階段
                )
            except Exception as e:
                score_threshold = 0.7
                logger.warning(f"⚠️ ThresholdManager 失敗，使用硬編碼預設值 0.7: {e}")
        
        # 執行搜索（傳遞 stage）
        result = handler.search(
            knowledge_id=knowledge_id,
            query=query,
            top_k=retrieval_setting.get('top_k', 5),
            score_threshold=score_threshold,
            search_mode=search_mode,
            stage=stage  # 🆕 傳遞階段資訊
        )
        
        logger.info(
            f"✅ 知識庫搜索成功: {knowledge_id}, query='{query}', "
            f"mode='{search_mode}', stage={stage}, results={len(result.get('records', []))}"
        )
        return Response(result)
        
    except Exception as e:
        logger.error(f"Dify knowledge search error: {str(e)}", exc_info=True)
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

---

### 6️⃣ Dify Knowledge Handler (1 個檔案)

#### 檔案：`library/dify_knowledge/__init__.py`
**位置**：`search()` 和 `search_knowledge_by_type()` 方法

**修改類型**：接收並傳遞 `stage` 參數

**修改 1：`search()` 方法**：
```python
def search(
    self, 
    knowledge_id, 
    query, 
    top_k=5, 
    score_threshold=0.7, 
    search_mode='auto', 
    stage=1,  # 🆕 新增階段參數
    metadata_condition=None
):
    """
    統一搜索接口（支援兩階段配置）
    
    Args:
        knowledge_id: 知識庫 ID
        query: 搜尋查詢
        top_k: 返回結果數量
        score_threshold: 相似度閾值
        search_mode: 搜索模式
        stage: 搜尋階段 (1=段落, 2=全文)
        metadata_condition: 元數據條件（可選）
    """
    # ✅ 記錄完整參數（包含 stage）
    self.logger.info(f"🔍 [Stage 6] DifyKnowledgeSearchHandler.search() 接收參數:")
    self.logger.info(f"  knowledge_id={knowledge_id}")
    self.logger.info(f"  query='{query}'")
    self.logger.info(f"  top_k={top_k}")
    self.logger.info(f"  score_threshold={score_threshold}")
    self.logger.info(f"  search_mode={search_mode}")
    self.logger.info(f"  stage={stage}")  # 🆕 記錄階段
    
    # ... 知識庫映射邏輯保持不變
    
    # 🆕 傳遞 stage 到下層
    records = self.search_knowledge_by_type(
        knowledge_type=knowledge_type,
        query=query,
        limit=top_k,
        threshold=score_threshold,
        search_mode=search_mode,
        stage=stage  # 🆕 傳遞階段
    )
    
    # ... 後續邏輯保持不變
```

**修改 2：`search_knowledge_by_type()` 方法**：
```python
def search_knowledge_by_type(
    self, 
    knowledge_type, 
    query, 
    limit=5, 
    threshold=0.7, 
    search_mode='auto',
    stage=1  # 🆕 新增階段參數
):
    """
    根據知識類型執行搜索（支援兩階段配置）
    
    Args:
        knowledge_type: 知識類型
        query: 搜尋查詢
        limit: 結果數量
        threshold: 相似度閾值
        search_mode: 搜索模式
        stage: 搜尋階段
    """
    self.logger.info(
        f"執行搜索: type={knowledge_type}, query='{query}', "
        f"limit={limit}, threshold={threshold}, mode='{search_mode}', stage={stage}"
    )
    
    # RVT Guide 搜尋
    if knowledge_type == 'rvt_guide':
        # ... 省略其他邏輯
        
        # ✅ 傳遞 stage 參數
        results = self.search_functions.get('rvt_guide', lambda *args, **kwargs: [])(
            query,
            limit,
            use_vector=True,
            threshold=threshold,
            search_mode=search_mode,
            stage=stage  # 🆕 傳遞階段
        )
    
    # Protocol Guide 搜尋
    elif knowledge_type == 'protocol_guide':
        # ✅ 傳遞 stage 參數
        results = self.search_functions.get('protocol_guide', lambda *args, **kwargs: [])(
            query,
            limit,
            use_vector=True,
            threshold=threshold,
            search_mode=search_mode,
            stage=stage  # 🆕 傳遞階段
        )
    
    # ... 其他知識類型保持不變
```

---

## ✅ 修改檢查清單總結

### 必須修改的檔案（7 個）

| # | 檔案路徑 | 修改類型 | 預估時間 |
|---|---------|---------|---------|
| 1 | `backend/api/models.py` | 新增 7 個欄位 | 30 分鐘 |
| 2 | `backend/api/serializers.py` | 擴充序列化器 | 30 分鐘 |
| 3 | `library/common/threshold_manager.py` | 擴充方法支援 stage | 1 小時 |
| 4 | `library/common/knowledge_base/section_search_service.py` | 新增 stage 參數 | 30 分鐘 |
| 5 | `library/common/knowledge_base/vector_search_helper.py` | 新增 stage 參數 | 20 分鐘 |
| 6 | `library/protocol_guide/search_service.py` | 傳遞 stage 參數 | 20 分鐘 |
| 7 | `backend/api/views/dify_knowledge_views.py` | 檢測並傳遞 stage | 20 分鐘 |

### 可選修改的檔案（2 個）

| # | 檔案路徑 | 修改目的 | 預估時間 |
|---|---------|---------|---------|
| 8 | `library/dify_knowledge/__init__.py` | 完整的 stage 參數流 | 20 分鐘 |
| 9 | `library/rvt_guide/search_service.py` | RVT Guide 支援（如果需要） | 10 分鐘 |

---

## 🧪 測試驗證步驟

### 1. Model 測試
```bash
# 進入 Django shell
docker exec -it ai-django python manage.py shell

# 測試新欄位
from api.models import SearchThresholdSetting
setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
print(f"Stage 1: {setting.stage1_threshold}, {setting.stage1_title_weight}%")
print(f"Stage 2: {setting.stage2_threshold}, {setting.stage2_title_weight}%")
print(f"Unified: {setting.use_unified_weights}")
```

### 2. Threshold Manager 測試
```python
from library.common.threshold_manager import get_threshold_manager

manager = get_threshold_manager()

# 測試第一階段
threshold_s1 = manager.get_threshold('protocol_assistant', stage=1)
weights_s1 = manager.get_weights('protocol_assistant', stage=1)
print(f"Stage 1: threshold={threshold_s1}, weights={weights_s1}")

# 測試第二階段
threshold_s2 = manager.get_threshold('protocol_assistant', stage=2)
weights_s2 = manager.get_weights('protocol_assistant', stage=2)
print(f"Stage 2: threshold={threshold_s2}, weights={weights_s2}")
```

### 3. 搜尋測試
```python
from library.protocol_guide.search_service import ProtocolGuideSearchService

service = ProtocolGuideSearchService()

# 測試第一階段（段落搜尋）
results_s1 = service.section_search("USB 測試", top_k=3, threshold=0.7)
print(f"Stage 1 結果: {len(results_s1)} 個")

# 測試第二階段（全文搜尋）
results_s2 = service.full_document_search("USB 測試", top_k=2, threshold=0.6)
print(f"Stage 2 結果: {len(results_s2)} 個")
```

### 4. API 測試
```bash
# 測試第一階段（段落搜尋）
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide",
    "query": "USB 測試",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.7}
  }'

# 測試第二階段（全文搜尋）
curl -X POST "http://localhost/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "protocol_guide",
    "query": "__FULL_SEARCH__ USB 測試",
    "retrieval_setting": {"top_k": 2, "score_threshold": 0.6}
  }'
```

---

## 📊 修改影響評估

### 向後相容性
- ✅ **完全相容**：新增欄位不影響現有功能
- ✅ **預設值設定**：`use_unified_weights=True` 保持現有行為
- ✅ **舊欄位保留**：`title_weight`, `content_weight`, `master_threshold` 保留

### 效能影響
- ⚠️ **快取擴充**：需要快取更多欄位（影響可忽略）
- ⚠️ **資料庫查詢**：額外讀取 7 個欄位（< 1ms）
- ✅ **搜尋邏輯**：無額外開銷（只是參數傳遞）

### 測試覆蓋
- ⚠️ **需要新增測試**：兩階段配置的單元測試
- ⚠️ **整合測試**：Dify 端到端測試
- ✅ **現有測試**：不受影響（向後相容）

---

## 🎯 實施建議

### 推薦順序
1. **Phase 1**：資料庫 Model 和 Migration（30 分鐘）
2. **Phase 2**：Serializer 擴充（30 分鐘）
3. **Phase 3**：Threshold Manager 擴充（1 小時）
4. **Phase 4**：搜尋服務層調整（1 小時）
5. **Phase 5**：API Views 調整（20 分鐘）
6. **Phase 6**：測試驗證（1 小時）

### 風險控制
- ✅ 在測試環境先執行
- ✅ 備份資料庫（執行 Migration 前）
- ✅ 保留舊欄位（不刪除）
- ✅ 使用 Feature Flag（`use_unified_weights`）

---

**文檔建立日期**: 2025-11-14  
**預估總工作量**: 3-4 小時（純後端修改）  
**向後相容性**: ✅ 完全相容  
**測試需求**: ⚠️ 中等（需要新增測試）
