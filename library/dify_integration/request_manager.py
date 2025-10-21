"""
Dify API 請求管理器
提供統一的 Dify API 請求處理、重試機制和錯誤處理
"""

import requests
import time
import logging
from typing import Dict, Optional, Callable, Any
from requests.exceptions import Timeout, ConnectionError, RequestException

logger = logging.getLogger(__name__)


class DifyRequestManager:
    """Dify API 請求管理器"""
    
    def __init__(self, default_timeout: int = 60, max_retries: int = 3, retry_delay: float = 1.0, backoff_factor: float = 2.0):
        """
        初始化請求管理器
        
        Args:
            default_timeout: 默認超時時間（秒）
            max_retries: 最大重試次數
            retry_delay: 初始重試延遲（秒）
            backoff_factor: 退避係數
        """
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
    
    def make_dify_request(self, 
                         api_url: str, 
                         headers: Dict[str, str], 
                         payload: Dict[str, Any], 
                         timeout: Optional[int] = None,
                         handle_400_answer_format_error: bool = True) -> requests.Response:
        """
        發送 Dify API 請求，包含智能重試機制
        
        Args:
            api_url: API URL
            headers: 請求標頭
            payload: 請求負載
            timeout: 超時時間（秒），如果為 None 則使用默認值
            handle_400_answer_format_error: 是否處理 HTTP 400 answer 格式錯誤
            
        Returns:
            requests.Response: HTTP 響應
            
        Raises:
            requests.exceptions.Timeout: 請求超時
            requests.exceptions.ConnectionError: 連接錯誤
            requests.exceptions.RequestException: 其他請求錯誤
        """
        if timeout is None:
            timeout = self.default_timeout
            
        def _make_single_request() -> requests.Response:
            """單次請求函數"""
            response = requests.post(
                api_url,
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # 處理 HTTP 400 answer 格式錯誤（如果啟用）
            if handle_400_answer_format_error and response.status_code == 400:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', '')
                    # 檢查是否是 answer 字段格式問題
                    if 'answer' in error_message and 'string' in error_message and 'list' in error_message:
                        logger.warning(f"Dify API 返回 answer 格式錯誤，觸發重試: {error_message}")
                        # 拋出 RequestException 以觸發重試機制
                        raise RequestException(f"Answer format error: {error_message}", response=response)
                except (ValueError, KeyError):
                    # JSON 解析失敗，正常處理
                    pass
            
            return response
        
        # 使用重試機制
        return self.retry_request(_make_single_request)
    
    def retry_request(self, request_func: Callable[[], requests.Response]) -> requests.Response:
        """
        請求重試機制
        
        Args:
            request_func: 請求函數
            
        Returns:
            requests.Response: HTTP 響應
            
        Raises:
            requests.exceptions.Timeout: 所有重試都超時
            requests.exceptions.ConnectionError: 所有重試都連接失敗
            requests.exceptions.RequestException: 其他請求錯誤
        """
        last_exception = None
        delay = self.retry_delay
        
        for attempt in range(self.max_retries + 1):
            try:
                response = request_func()
                if attempt > 0:
                    logger.info(f"重試成功，嘗試次數: {attempt + 1}")
                return response
                
            except Timeout as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"請求超時，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                    time.sleep(delay)
                    delay *= self.backoff_factor
                    continue
                    
            except ConnectionError as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"連接錯誤，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                    time.sleep(delay)
                    delay *= self.backoff_factor
                    continue
                    
            except RequestException as e:
                # 檢查是否是可重試的 HTTP 錯誤
                if hasattr(e, 'response') and e.response is not None:
                    status_code = e.response.status_code
                    
                    # HTTP 400: Bad Request - 可能是暫時性問題（如 answer 格式錯誤）
                    # HTTP 429: Too Many Requests - 速率限制
                    # HTTP 502, 503, 504: 服務器錯誤
                    if status_code in [400, 429, 502, 503, 504]:
                        last_exception = e
                        if attempt < self.max_retries:
                            logger.warning(f"HTTP {status_code} 錯誤，第 {attempt + 1} 次重試，延遲 {delay} 秒")
                            time.sleep(delay)
                            delay *= self.backoff_factor
                            continue
                            
                # 其他 HTTP 錯誤不重試
                raise e
                
            except Exception as e:
                # 其他異常不重試
                raise e
        
        # 所有重試都失敗，拋出最後一個異常
        logger.error(f"重試 {self.max_retries} 次後仍然失敗")
        raise last_exception


class DifyResponseHandler:
    """Dify 響應處理器"""
    
    @staticmethod
    def process_answer_field(raw_answer: Any) -> str:
        """
        處理 Dify API 返回的 answer 字段，兼容不同格式
        
        ⚠️ 設計原則：後端不做任何清理，只做格式轉換
        - 前端負責所有 Markdown 和圖片引用的處理
        - 這樣和 DevMarkdownTestPage 保持一致的架構
        
        Args:
            raw_answer: 原始 answer 數據
            
        Returns:
            str: 處理後的 answer 字符串（不做清理，只做格式轉換）
        """
        if isinstance(raw_answer, list):
            # 如果 answer 是數組，將其轉換為字符串
            if len(raw_answer) == 0:
                answer = "抱歉，目前無法提供回答，請稍後再試或重新描述問題。"
                logger.warning("Dify API returned empty array for answer")
            else:
                answer = ' '.join(str(item) for item in raw_answer)
                logger.warning("Dify API returned array for answer, converted to string")
        elif isinstance(raw_answer, str):
            answer = raw_answer
        else:
            # 處理其他異常情況
            answer = str(raw_answer) if raw_answer else "抱歉，回答格式異常，請稍後再試。"
            logger.warning(f"Dify API returned unexpected answer type: {type(raw_answer)}")
        
        # 🎯 不做任何清理，直接返回原始內容
        # 前端會使用 imageReferenceConverter.js 處理 [IMG:ID] 轉換
        return answer
    
    @staticmethod
    def handle_conversation_not_exists(response: requests.Response, 
                                     api_url: str, 
                                     headers: Dict[str, str], 
                                     payload: Dict[str, Any], 
                                     timeout: int = 60) -> Optional[Dict[str, Any]]:
        """
        處理 "Conversation Not Exists" 錯誤，自動重試不帶 conversation_id
        
        Args:
            response: 404 響應
            api_url: API URL
            headers: 請求標頭
            payload: 原始請求負載
            timeout: 超時時間
            
        Returns:
            Dict: 重試成功的響應數據，失敗則返回 None
        """
        try:
            response_data = response.json()
            if 'Conversation Not Exists' in response_data.get('message', ''):
                conversation_id = payload.get('conversation_id', '')
                logger.warning(f"Conversation {conversation_id} not exists, retrying without conversation_id")
                
                # 重新發送請求，不帶 conversation_id
                retry_payload = payload.copy()
                retry_payload.pop('conversation_id', None)
                
                retry_response = requests.post(
                    api_url,
                    headers=headers,
                    json=retry_payload,
                    timeout=timeout
                )
                
                if retry_response.status_code == 200:
                    retry_result = retry_response.json()
                    logger.info("Conversation retry request success")
                    return retry_result
                    
        except Exception as retry_error:
            logger.error(f"Conversation retry request failed: {str(retry_error)}")
            
        return None


# 創建全局請求管理器實例
default_request_manager = DifyRequestManager()

# 便利函數
def make_dify_request(api_url: str, 
                     headers: Dict[str, str], 
                     payload: Dict[str, Any], 
                     timeout: Optional[int] = None,
                     handle_400_answer_format_error: bool = True) -> requests.Response:
    """
    便利函數：發送 Dify API 請求
    
    使用全局默認的請求管理器發送請求
    """
    return default_request_manager.make_dify_request(
        api_url, headers, payload, timeout, handle_400_answer_format_error
    )


def process_dify_answer(raw_answer: Any) -> str:
    """
    便利函數：處理 Dify answer 字段
    """
    return DifyResponseHandler.process_answer_field(raw_answer)


def handle_conversation_error(response: requests.Response, 
                            api_url: str, 
                            headers: Dict[str, str], 
                            payload: Dict[str, Any], 
                            timeout: int = 60) -> Optional[Dict[str, Any]]:
    """
    便利函數：處理對話不存在錯誤
    """
    return DifyResponseHandler.handle_conversation_not_exists(
        response, api_url, headers, payload, timeout
    )