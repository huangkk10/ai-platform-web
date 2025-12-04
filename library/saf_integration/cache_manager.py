"""
SAF Cache Manager
=================

SAF API 快取管理器，用於減少對外部 API 的請求頻率。

功能：
- 記憶體快取（TTL 機制）
- 快取失效管理
- 快取統計

作者：AI Platform Team
創建日期：2025-12-04
"""

import logging
import time
from typing import Dict, Any, Optional
from threading import Lock


logger = logging.getLogger(__name__)


class SAFCacheManager:
    """SAF API 快取管理器"""
    
    # 預設快取 TTL（秒）
    DEFAULT_TTL = 300  # 5 分鐘
    
    def __init__(self, ttl: int = DEFAULT_TTL):
        """
        初始化快取管理器
        
        Args:
            ttl: 快取存活時間（秒）
        """
        self.ttl = ttl
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        
        # 統計資訊
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "expirations": 0
        }
        
        logger.debug(f"SAF Cache Manager 初始化: TTL={ttl}s")
    
    def get(self, key: str) -> Optional[Any]:
        """
        獲取快取資料
        
        Args:
            key: 快取鍵
            
        Returns:
            快取的資料，如果不存在或已過期則返回 None
        """
        with self._lock:
            if key not in self._cache:
                self._stats["misses"] += 1
                return None
            
            cache_entry = self._cache[key]
            
            # 檢查是否過期
            if time.time() > cache_entry["expires_at"]:
                del self._cache[key]
                self._stats["expirations"] += 1
                self._stats["misses"] += 1
                logger.debug(f"快取已過期: {key}")
                return None
            
            self._stats["hits"] += 1
            logger.debug(f"快取命中: {key}")
            return cache_entry["data"]
    
    def set(self, key: str, data: Any, ttl: Optional[int] = None) -> None:
        """
        設定快取資料
        
        Args:
            key: 快取鍵
            data: 要快取的資料
            ttl: 自訂 TTL（秒），None 使用預設值
        """
        with self._lock:
            self._cache[key] = {
                "data": data,
                "expires_at": time.time() + (ttl or self.ttl),
                "created_at": time.time()
            }
            self._stats["sets"] += 1
            logger.debug(f"快取已設定: {key}")
    
    def delete(self, key: str) -> bool:
        """
        刪除快取資料
        
        Args:
            key: 快取鍵
            
        Returns:
            是否成功刪除
        """
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"快取已刪除: {key}")
                return True
            return False
    
    def clear(self) -> int:
        """
        清除所有快取
        
        Returns:
            清除的快取數量
        """
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info(f"已清除 {count} 個快取項目")
            return count
    
    def clear_expired(self) -> int:
        """
        清除已過期的快取
        
        Returns:
            清除的快取數量
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if current_time > entry["expires_at"]
            ]
            
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
            
            if expired_keys:
                logger.debug(f"已清除 {len(expired_keys)} 個過期快取")
            
            return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        獲取快取統計資訊
        
        Returns:
            統計資訊字典
        """
        with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = (
                self._stats["hits"] / total_requests * 100
                if total_requests > 0 else 0
            )
            
            return {
                "hits": self._stats["hits"],
                "misses": self._stats["misses"],
                "sets": self._stats["sets"],
                "expirations": self._stats["expirations"],
                "hit_rate": f"{hit_rate:.1f}%",
                "current_size": len(self._cache),
                "ttl": self.ttl
            }
    
    def get_keys(self) -> list:
        """
        獲取所有快取鍵
        
        Returns:
            快取鍵列表
        """
        with self._lock:
            return list(self._cache.keys())
    
    def has_key(self, key: str) -> bool:
        """
        檢查快取鍵是否存在（不檢查過期）
        
        Args:
            key: 快取鍵
            
        Returns:
            是否存在
        """
        return key in self._cache
    
    def get_remaining_ttl(self, key: str) -> Optional[int]:
        """
        獲取快取剩餘 TTL
        
        Args:
            key: 快取鍵
            
        Returns:
            剩餘秒數，如果不存在則返回 None
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            remaining = self._cache[key]["expires_at"] - time.time()
            return max(0, int(remaining))
