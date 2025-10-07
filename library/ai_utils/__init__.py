"""
AI 相關工具模組
包含 LLM 調用、嵌入模型、提示工程、API 重試機制等功能
"""

from .llm_client import LLMClient
from .embedding_utils import EmbeddingUtils
from .prompt_templates import PromptTemplates
# 🆕 導入 API 重試機制
from .api_retry import (
    APIRetryHandler,
    APIRetryConfig,
    RetryableAPI,
    RetryStrategy,
    RetryableErrorType,
    retry_api_request,
    create_retry_handler,
    retryable_api,
    DEFAULT_CONFIG,
    AGGRESSIVE_CONFIG,
    CONSERVATIVE_CONFIG,
    RATE_LIMIT_CONFIG,
    default_retry,
    aggressive_retry,
    conservative_retry,
    rate_limit_retry
)

__all__ = [
    'LLMClient', 
    'EmbeddingUtils', 
    'PromptTemplates',
    # 🆕 API 重試相關
    'APIRetryHandler',
    'APIRetryConfig',
    'RetryableAPI',
    'RetryStrategy',
    'RetryableErrorType',
    'retry_api_request',
    'create_retry_handler',
    'retryable_api',
    'DEFAULT_CONFIG',
    'AGGRESSIVE_CONFIG',
    'CONSERVATIVE_CONFIG',
    'RATE_LIMIT_CONFIG',
    'default_retry',
    'aggressive_retry',
    'conservative_retry',
    'rate_limit_retry'
]