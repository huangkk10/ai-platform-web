"""
Dify API 整合模組
提供知識庫、文檔、聊天和檢索功能的封裝
"""

from typing import Dict, Any
from .client import DifyClient
from .dataset_manager import DatasetManager
from .document_manager import DocumentManager
from .chat_client import DifyChatClient, create_chat_client, quick_chat
from .file_manager import DifyFileManager
from .report_analyzer_client import ReportAnalyzerClient, create_report_analyzer_client, quick_file_analysis
from .request_manager import DifyRequestManager, DifyResponseHandler, make_dify_request, process_dify_answer, handle_conversation_error
from .protocol_chat_handler import ProtocolChatHandler, create_protocol_chat_handler, handle_protocol_chat_api

__all__ = [
    # 原有模組
    'DifyClient', 
    'DatasetManager', 
    'DocumentManager',
    
    # 聊天相關模組
    'DifyChatClient',
    'create_chat_client',
    'quick_chat',
    
    # 文件管理模組
    'DifyFileManager',
    
    # Report Analyzer 專用模組
    'ReportAnalyzerClient',
    'create_report_analyzer_client',
    'quick_file_analysis',
    
    # 請求管理模組
    'DifyRequestManager',
    'DifyResponseHandler', 
    'make_dify_request',
    'process_dify_answer',
    'handle_conversation_error',
    
    # Protocol Chat 模組
    'ProtocolChatHandler',
    'create_protocol_chat_handler',
    'handle_protocol_chat_api',
    'dify_protocol_chat_api'
]


# 便利函數組合
def create_complete_client(api_url: str = None, api_key: str = None, 
                          base_url: str = None, client_type: str = "chat") -> Any:
    """
    創建完整的 Dify 客戶端（包含聊天和文件管理功能）
    
    Args:
        api_url: API URL
        api_key: API 密鑰
        base_url: 基礎 URL
        client_type: 客戶端類型 ("chat", "report_analyzer", "dataset")
        
    Returns:
        對應類型的客戶端實例
    """
    if client_type == "report_analyzer":
        return create_report_analyzer_client(api_url, api_key, base_url)
    elif client_type == "chat":
        return create_chat_client(api_url, api_key, base_url)
    elif client_type == "dataset":
        # 如果需要，可以添加 dataset 客戶端
        return DifyClient(api_url, api_key, base_url)
    else:
        raise ValueError(f"不支援的客戶端類型: {client_type}")


def analyze_files_batch(file_paths: list, queries: list = None, 
                       api_url: str = None, api_key: str = None, 
                       base_url: str = None, user: str = "batch_user",
                       verbose: bool = True) -> Dict[str, Dict[str, Any]]:
    """
    批量文件分析的便利函數
    
    Args:
        file_paths: 文件路徑列表
        queries: 查詢列表（可選）
        api_url: API URL
        api_key: API 密鑰
        base_url: 基礎 URL
        user: 用戶標識
        verbose: 是否顯示詳細日誌
        
    Returns:
        Dict[str, Dict[str, Any]]: 批量分析結果
    """
    client = create_report_analyzer_client(api_url, api_key, base_url)
    return client.batch_file_analysis(file_paths, queries, user, verbose=verbose)


def dify_protocol_chat_api(request):
    """
    Django API 便利函數：處理 Protocol Known Issue 配置的聊天請求
    
    Args:
        request: Django request 對象
        
    Returns:
        Django Response 對象
        
    使用方式：
        from library.dify_integration import dify_protocol_chat_api
        return dify_protocol_chat_api(request)
    """
    return handle_protocol_chat_api(request)