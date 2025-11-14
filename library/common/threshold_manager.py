"""
Threshold Manager - 統一管理搜尋 Threshold 設定
==================================================

此模組提供 Singleton 模式的 Threshold 管理器，用於：
1. 從資料庫讀取 threshold 設定（帶快取）
2. 提供三層優先順序：Dify Studio > Database > Default
3. 自動計算衍生 threshold（文檔、關鍵字）

使用方式：
```python
from library.common.threshold_manager import get_threshold_manager

manager = get_threshold_manager()

# 獲取 threshold（三層優先順序）
threshold = manager.get_threshold(
    assistant_type='protocol_assistant',
    dify_threshold=None  # 如果 Dify 沒傳，會使用資料庫或預設
)
```

三層優先順序：
1. dify_threshold（Dify Studio 設定）- 最高優先
2. Database threshold（Web 管理介面設定）- 中等優先
3. DEFAULT_THRESHOLD (0.7) - 最低優先
"""

import logging
import time
from threading import Lock
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# 預設 threshold 值
DEFAULT_THRESHOLD = 0.7
CACHE_TTL = 300  # 快取存活時間（秒）= 5 分鐘


class ThresholdManager:
    """
    Threshold 管理器（Singleton 模式）
    
    功能：
    1. 從資料庫讀取 threshold 設定
    2. 快取機制（5 分鐘 TTL）
    3. 三層優先順序處理
    4. 自動計算衍生 threshold
    
    快取策略：
    - 每 5 分鐘自動重新整理
    - 可手動觸發重新整理
    - 避免每次查詢都存取資料庫
    """
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton 模式實作"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化（只執行一次）"""
        if self._initialized:
            return
        
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._cache = {}
        self._cache_timestamp = 0
        self._initialized = True
        
        self.logger.info("✅ ThresholdManager Singleton 初始化完成")
    
    def _is_cache_valid(self) -> bool:
        """檢查快取是否有效"""
        if not self._cache:
            return False
        
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp
        
        is_valid = cache_age < CACHE_TTL
        
        if not is_valid:
            self.logger.debug(f"快取已過期（{cache_age:.0f} 秒 > {CACHE_TTL} 秒）")
        
        return is_valid
    
    def _load_from_database(self) -> Dict[str, dict]:
        """從資料庫載入 threshold 設定（擴充為載入完整配置）"""
        try:
            # 延遲導入避免循環依賴
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
    
    def _refresh_cache(self):
        """重新整理快取"""
        self.logger.info("🔄 重新整理 threshold 快取...")
        self._cache = self._load_from_database()
        self._cache_timestamp = time.time()
        self.logger.info(f"✅ 快取重新整理完成（{len(self._cache)} 項設定）")
    
    def get_threshold(
        self,
        assistant_type: str,
        dify_threshold: Optional[float] = None,
        threshold_type: str = 'master',
        stage: int = 1  # 🆕 新增階段參數
    ) -> float:
        """
        獲取 threshold 值（支援兩階段配置）
        
        優先順序：
        1. dify_threshold（Dify Studio 設定）- 最高優先
        2. Database threshold（Web 管理介面設定）- 中等優先
        3. DEFAULT_THRESHOLD - 最低優先
        
        Args:
            assistant_type: Assistant 類型 ('protocol_assistant', 'rvt_assistant')
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
    
    def get_all_thresholds(
        self,
        assistant_type: str,
        dify_threshold: Optional[float] = None
    ) -> Dict[str, float]:
        """
        獲取所有類型的 threshold
        
        Args:
            assistant_type: Assistant 類型
            dify_threshold: Dify Studio 傳來的 threshold（可選）
        
        Returns:
            dict: 包含所有 threshold 類型
                {
                    'master': 0.75,
                    'document': 0.64,
                    'keyword': 0.38
                }
        """
        master = self.get_threshold(assistant_type, dify_threshold, 'master')
        
        return {
            'master': master,
            'document': round(master * 0.85, 2),
            'keyword': round(master * 0.5, 2)
        }
    
    def refresh_cache(self):
        """手動重新整理快取（公開方法）"""
        self._refresh_cache()
    
    def clear_cache(self):
        """清除快取"""
        self.logger.info("🗑️ 清除 threshold 快取")
        self._cache = {}
        self._cache_timestamp = 0
    
    def get_cache_info(self) -> Dict:
        """獲取快取資訊（用於除錯）"""
        current_time = time.time()
        cache_age = current_time - self._cache_timestamp if self._cache_timestamp > 0 else 0
        
        return {
            'cache_size': len(self._cache),
            'cache_age_seconds': cache_age,
            'is_valid': self._is_cache_valid(),
            'cached_assistants': list(self._cache.keys()),
            'ttl': CACHE_TTL
        }


# 全域實例（Singleton）
_threshold_manager_instance = None
_instance_lock = Lock()


def get_threshold_manager() -> ThresholdManager:
    """
    獲取 ThresholdManager 實例（Singleton）
    
    Returns:
        ThresholdManager: Threshold 管理器實例
    """
    global _threshold_manager_instance
    
    if _threshold_manager_instance is None:
        with _instance_lock:
            if _threshold_manager_instance is None:
                _threshold_manager_instance = ThresholdManager()
    
    return _threshold_manager_instance


# 便利函數

def get_threshold(
    assistant_type: str,
    dify_threshold: Optional[float] = None,
    threshold_type: str = 'master',
    stage: int = 1  # 🆕 新增
) -> float:
    """
    獲取 threshold 值（便利函數）
    
    Args:
        assistant_type: Assistant 類型
        dify_threshold: Dify Studio 傳來的 threshold（可選）
        threshold_type: 已廢棄，保留以向後相容
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        float: Threshold 值
    """
    manager = get_threshold_manager()
    return manager.get_threshold(assistant_type, dify_threshold, threshold_type, stage)


def get_weights(
    assistant_type: str,
    stage: int = 1
) -> tuple:
    """
    獲取權重配置（便利函數）
    
    Args:
        assistant_type: Assistant 類型
        stage: 搜尋階段 (1=段落, 2=全文)
    
    Returns:
        (title_weight, content_weight) 元組 (0.0-1.0)
    """
    manager = get_threshold_manager()
    return manager.get_weights(assistant_type, stage)


def get_all_thresholds(
    assistant_type: str,
    dify_threshold: Optional[float] = None
) -> Dict[str, float]:
    """
    獲取所有 threshold 值（便利函數）
    
    Args:
        assistant_type: Assistant 類型
        dify_threshold: Dify Studio 傳來的 threshold（可選）
    
    Returns:
        dict: 所有 threshold 值
    """
    manager = get_threshold_manager()
    return manager.get_all_thresholds(assistant_type, dify_threshold)


def refresh_threshold_cache():
    """重新整理 threshold 快取（便利函數）"""
    manager = get_threshold_manager()
    manager.refresh_cache()


# 導出
__all__ = [
    'ThresholdManager',
    'get_threshold_manager',
    'get_threshold',
    'get_weights',  # 🆕 新增
    'get_all_thresholds',
    'refresh_threshold_cache',
    'DEFAULT_THRESHOLD',
    'CACHE_TTL'
]
