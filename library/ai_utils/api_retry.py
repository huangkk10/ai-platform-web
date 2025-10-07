"""
API 重試機制 - API Retry Utilities

提供各種 API 請求的重試機制，包含智能退避策略、錯誤分類處理和詳細的日誌記錄。

Author: AI Platform Team  
Created: 2024-10-08
"""

import logging
import time
import functools
from typing import Callable, List, Optional, Union, Any, Dict
from enum import Enum

logger = logging.getLogger(__name__)


class RetryableErrorType(Enum):
    """可重試錯誤類型"""
    TIMEOUT = "timeout"
    CONNECTION = "connection" 
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    TRANSIENT = "transient"


class RetryStrategy(Enum):
    """重試策略"""
    FIXED = "fixed"           # 固定間隔
    LINEAR = "linear"         # 線性增長
    EXPONENTIAL = "exponential"  # 指數退避
    FIBONACCI = "fibonacci"   # 斐波那契數列


class APIRetryConfig:
    """API 重試配置"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        strategy: RetryStrategy = RetryStrategy.EXPONENTIAL,
        retryable_status_codes: List[int] = None,
        retryable_exceptions: List[type] = None,
        jitter: bool = True
    ):
        """
        初始化重試配置
        
        Args:
            max_retries: 最大重試次數
            base_delay: 基礎延遲時間（秒）
            max_delay: 最大延遲時間（秒）
            backoff_factor: 退避係數
            strategy: 重試策略
            retryable_status_codes: 可重試的HTTP狀態碼
            retryable_exceptions: 可重試的異常類型
            jitter: 是否加入隨機抖動
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.strategy = strategy
        self.retryable_status_codes = retryable_status_codes or [400, 429, 502, 503, 504, 520, 521, 522, 523, 524]
        self.retryable_exceptions = retryable_exceptions or []
        self.jitter = jitter


class APIRetryHandler:
    """API 重試處理器"""
    
    def __init__(self, config: APIRetryConfig = None):
        """
        初始化重試處理器
        
        Args:
            config: 重試配置
        """
        self.config = config or APIRetryConfig()
        self._fibonacci_cache = {}
    
    def _calculate_delay(self, attempt: int) -> float:
        """
        計算延遲時間
        
        Args:
            attempt: 當前嘗試次數
            
        Returns:
            float: 延遲時間（秒）
        """
        if self.config.strategy == RetryStrategy.FIXED:
            delay = self.config.base_delay
            
        elif self.config.strategy == RetryStrategy.LINEAR:
            delay = self.config.base_delay * attempt
            
        elif self.config.strategy == RetryStrategy.EXPONENTIAL:
            delay = self.config.base_delay * (self.config.backoff_factor ** attempt)
            
        elif self.config.strategy == RetryStrategy.FIBONACCI:
            delay = self.config.base_delay * self._get_fibonacci(attempt)
            
        else:
            delay = self.config.base_delay
        
        # 限制最大延遲時間
        delay = min(delay, self.config.max_delay)
        
        # 加入隨機抖動避免雷同效應
        if self.config.jitter:
            import random
            jitter = random.uniform(0.8, 1.2)
            delay *= jitter
        
        return delay
    
    def _get_fibonacci(self, n: int) -> int:
        """
        計算斐波那契數列
        
        Args:
            n: 位置
            
        Returns:
            int: 斐波那契數值
        """
        if n in self._fibonacci_cache:
            return self._fibonacci_cache[n]
        
        if n <= 1:
            result = 1
        else:
            result = self._get_fibonacci(n - 1) + self._get_fibonacci(n - 2)
        
        self._fibonacci_cache[n] = result
        return result
    
    def _is_retryable_error(self, exception: Exception) -> tuple[bool, RetryableErrorType]:
        """
        判斷是否為可重試錯誤
        
        Args:
            exception: 異常對象
            
        Returns:
            tuple[bool, RetryableErrorType]: (是否可重試, 錯誤類型)
        """
        # 檢查標準庫中的常見可重試錯誤
        if isinstance(exception, TimeoutError):
            return True, RetryableErrorType.TIMEOUT
        
        if isinstance(exception, ConnectionError):
            return True, RetryableErrorType.CONNECTION
        
        # 檢查 OSError 相關錯誤 (網路相關)
        if isinstance(exception, (OSError, IOError)):
            return True, RetryableErrorType.CONNECTION
        
        try:
            import requests
            
            # 超時錯誤
            if isinstance(exception, requests.exceptions.Timeout):
                return True, RetryableErrorType.TIMEOUT
            
            # 連接錯誤
            if isinstance(exception, requests.exceptions.ConnectionError):
                return True, RetryableErrorType.CONNECTION
            
            # HTTP 錯誤
            if isinstance(exception, requests.exceptions.RequestException):
                if hasattr(exception, 'response') and exception.response is not None:
                    status_code = exception.response.status_code
                    
                    # 速率限制
                    if status_code == 429:
                        return True, RetryableErrorType.RATE_LIMIT
                    
                    # 服務器錯誤
                    if status_code in self.config.retryable_status_codes:
                        return True, RetryableErrorType.SERVER_ERROR
                    
                    # 其他不可重試的 HTTP 錯誤
                    return False, None
            
        except ImportError:
            # 如果沒有 requests 庫，繼續檢查其他異常
            pass
        
        # 檢查自定義可重試異常
        for exc_type in self.config.retryable_exceptions:
            if isinstance(exception, exc_type):
                return True, RetryableErrorType.TRANSIENT
        
        return False, None
    
    def retry_request(self, func: Callable, *args, **kwargs) -> Any:
        """
        執行帶重試的 API 請求
        
        Args:
            func: 要執行的函數
            *args: 函數參數
            **kwargs: 函數關鍵字參數
            
        Returns:
            Any: 函數執行結果
            
        Raises:
            Exception: 最後一個失敗的異常
        """
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                
                # 如果不是第一次嘗試，記錄重試成功
                if attempt > 0:
                    logger.info(f"✅ 重試成功 - 函數: {func.__name__}, 嘗試次數: {attempt + 1}")
                
                return result
                
            except Exception as e:
                last_exception = e
                
                # 檢查是否可重試
                is_retryable, error_type = self._is_retryable_error(e)
                
                if not is_retryable or attempt >= self.config.max_retries:
                    # 不可重試或已達到最大重試次數
                    if attempt >= self.config.max_retries:
                        logger.error(f"❌ 重試 {self.config.max_retries} 次後仍然失敗 - 函數: {func.__name__}")
                    else:
                        logger.error(f"❌ 不可重試錯誤 - 函數: {func.__name__}, 錯誤: {str(e)}")
                    break
                
                # 計算延遲時間
                delay = self._calculate_delay(attempt + 1)
                
                # 記錄重試信息
                logger.warning(
                    f"🔄 準備重試 - 函數: {func.__name__}, "
                    f"錯誤類型: {error_type.value}, "
                    f"第 {attempt + 1} 次重試, "
                    f"延遲 {delay:.2f} 秒, "
                    f"錯誤: {str(e)}"
                )
                
                # 等待後重試
                time.sleep(delay)
        
        # 拋出最後一個異常
        raise last_exception


class RetryableAPI:
    """可重試的 API 裝飾器類"""
    
    def __init__(self, config: APIRetryConfig = None):
        """
        初始化可重試 API
        
        Args:
            config: 重試配置
        """
        self.handler = APIRetryHandler(config)
    
    def __call__(self, func: Callable) -> Callable:
        """
        裝飾器調用
        
        Args:
            func: 被裝飾的函數
            
        Returns:
            Callable: 包裝後的函數
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.handler.retry_request(func, *args, **kwargs)
        
        return wrapper


# 預定義的重試配置
DEFAULT_CONFIG = APIRetryConfig()

AGGRESSIVE_CONFIG = APIRetryConfig(
    max_retries=5,
    base_delay=0.5,
    max_delay=30.0,
    strategy=RetryStrategy.EXPONENTIAL
)

CONSERVATIVE_CONFIG = APIRetryConfig(
    max_retries=2,
    base_delay=2.0,
    max_delay=10.0,
    strategy=RetryStrategy.FIXED
)

RATE_LIMIT_CONFIG = APIRetryConfig(
    max_retries=10,
    base_delay=5.0,
    max_delay=300.0,
    strategy=RetryStrategy.FIBONACCI,
    retryable_status_codes=[429, 503, 520]
)


# 便利函數
def retry_api_request(
    func: Callable, 
    max_retries: int = 3, 
    retry_delay: float = 1.0, 
    backoff_factor: float = 2.0,
    **kwargs
) -> Any:
    """
    便利函數：執行帶重試的 API 請求（保持向後兼容性）
    
    Args:
        func: 要執行的函數
        max_retries: 最大重試次數
        retry_delay: 初始重試延遲（秒）
        backoff_factor: 退避係數
        **kwargs: 其他參數
        
    Returns:
        Any: 函數執行結果
    """
    config = APIRetryConfig(
        max_retries=max_retries,
        base_delay=retry_delay,
        backoff_factor=backoff_factor
    )
    handler = APIRetryHandler(config)
    return handler.retry_request(func, **kwargs)


def create_retry_handler(config: APIRetryConfig = None) -> APIRetryHandler:
    """
    創建重試處理器
    
    Args:
        config: 重試配置
        
    Returns:
        APIRetryHandler: 重試處理器實例
    """
    return APIRetryHandler(config)


def retryable_api(config: APIRetryConfig = None):
    """
    可重試 API 裝飾器
    
    Args:
        config: 重試配置
        
    Returns:
        裝飾器函數
    """
    return RetryableAPI(config)


# 預定義裝飾器
@retryable_api(DEFAULT_CONFIG)
def default_retry(func: Callable) -> Callable:
    """默認重試裝飾器"""
    return func


@retryable_api(AGGRESSIVE_CONFIG)  
def aggressive_retry(func: Callable) -> Callable:
    """激進重試裝飾器（更多重試次數）"""
    return func


@retryable_api(CONSERVATIVE_CONFIG)
def conservative_retry(func: Callable) -> Callable:
    """保守重試裝飾器（較少重試次數）"""
    return func


@retryable_api(RATE_LIMIT_CONFIG)
def rate_limit_retry(func: Callable) -> Callable:
    """速率限制重試裝飾器"""
    return func