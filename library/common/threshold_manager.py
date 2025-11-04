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
    
    def _load_from_database(self) -> Dict[str, float]:
        """從資料庫載入 threshold 設定"""
        try:
            # 延遲導入避免循環依賴
            from api.models import SearchThresholdSetting
            
            settings = SearchThresholdSetting.objects.filter(is_active=True)
            
            cache = {}
            for setting in settings:
                cache[setting.assistant_type] = float(setting.master_threshold)
                self.logger.debug(
                    f"載入設定: {setting.assistant_type} = {setting.master_threshold}"
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
        threshold_type: str = 'master'
    ) -> float:
        """
        獲取 threshold 值（三層優先順序）
        
        優先順序：
        1. dify_threshold（Dify Studio 設定）- 最高優先
        2. Database threshold（Web 管理介面設定）- 中等優先
        3. DEFAULT_THRESHOLD (0.7) - 最低優先
        
        Args:
            assistant_type: Assistant 類型 ('protocol_assistant', 'rvt_assistant')
            dify_threshold: Dify Studio 傳來的 threshold（可選）
            threshold_type: Threshold 類型
                - 'master': 段落向量 threshold（原始值）
                - 'document': 文檔向量 threshold（master * 0.85）
                - 'keyword': 關鍵字 threshold（master * 0.5）
        
        Returns:
            float: Threshold 值
        """
        # 優先級 1：Dify Studio 設定（最高優先）
        if dify_threshold is not None:
            self.logger.info(
                f"🎯 使用 Dify Studio threshold: {dify_threshold} "
                f"(assistant={assistant_type})"
            )
            master_threshold = dify_threshold
        else:
            # 優先級 2：資料庫設定
            # 檢查快取是否有效
            if not self._is_cache_valid():
                self._refresh_cache()
            
            # 從快取讀取
            if assistant_type in self._cache:
                master_threshold = self._cache[assistant_type]
                self.logger.info(
                    f"📊 使用資料庫 threshold: {master_threshold} "
                    f"(assistant={assistant_type})"
                )
            else:
                # 優先級 3：預設值
                master_threshold = DEFAULT_THRESHOLD
                self.logger.info(
                    f"⚙️ 使用預設 threshold: {master_threshold} "
                    f"(assistant={assistant_type}, 資料庫無設定)"
                )
        
        # 根據類型計算最終 threshold
        if threshold_type == 'master':
            final_threshold = master_threshold
        elif threshold_type == 'document':
            final_threshold = round(master_threshold * 0.85, 2)
            self.logger.debug(
                f"計算文檔 threshold: {master_threshold} * 0.85 = {final_threshold}"
            )
        elif threshold_type == 'keyword':
            final_threshold = round(master_threshold * 0.5, 2)
            self.logger.debug(
                f"計算關鍵字 threshold: {master_threshold} * 0.5 = {final_threshold}"
            )
        else:
            self.logger.warning(f"未知的 threshold_type: {threshold_type}，使用 master")
            final_threshold = master_threshold
        
        return final_threshold
    
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
    threshold_type: str = 'master'
) -> float:
    """
    獲取 threshold 值（便利函數）
    
    Args:
        assistant_type: Assistant 類型
        dify_threshold: Dify Studio 傳來的 threshold（可選）
        threshold_type: Threshold 類型（'master', 'document', 'keyword'）
    
    Returns:
        float: Threshold 值
    """
    manager = get_threshold_manager()
    return manager.get_threshold(assistant_type, dify_threshold, threshold_type)


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
    'get_all_thresholds',
    'refresh_threshold_cache',
    'DEFAULT_THRESHOLD',
    'CACHE_TTL'
]
