"""
Dify Protocol Chat Handler

專門處理 Protocol Known Issue 配置的聊天功能
提供完整的錯誤處理、重試機制和 Django Response 整合
"""

import requests
import time
import logging
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


class ProtocolChatHandler:
    """
    Protocol Known Issue 聊天處理器
    
    主要功能：
    - Protocol RAG 聊天服務
    - 自動重試機制
    - 對話恢復功能
    - 完整錯誤處理
    """
    
    def __init__(self, config_manager=None):
        """
        初始化 Protocol Chat Handler
        
        Args:
            config_manager: 配置管理器，用於獲取 Protocol Known Issue 配置
        """
        self.config_manager = config_manager
        self.timeout = 120  # 默認超時時間
        self.max_retries = 2  # 最大重試次數
    
    def handle_chat_request(self, request):
        """
        處理聊天請求的主要方法
        
        🆕 支援版本配置：
        - 接收 version_code 參數（可選）
        - 從資料庫讀取 DifyConfigVersion 配置
        - 將版本配置傳遞給搜尋服務（啟用 Title Boost）
        
        Args:
            request: Django request 對象
            
        Returns:
            Django Response 對象
        """
        try:
            # 解析請求數據
            data = request.data
            message = data.get('message', '').strip()
            conversation_id = data.get('conversation_id', '')
            version_code = data.get('version_code', None)  # 🆕 接收版本代碼（可選）
            
            # 驗證輸入
            validation_response = self._validate_input(message)
            if validation_response:
                return validation_response
            
            # 🆕 讀取版本配置（優先使用 Baseline 版本）
            # 如果提供了 version_code，使用指定版本；否則使用 Baseline
            version_config = self._load_version_config(version_code)
            
            # 獲取 Dify 配置
            config_response = self._get_dify_config()
            if isinstance(config_response, Response):
                return config_response
            
            dify_config = config_response
            
            # 執行聊天請求（傳遞版本配置）
            return self._execute_chat_request(
                message, conversation_id, dify_config, request.user,
                version_config=version_config  # 🆕 傳遞版本配置
            )
            
        except Exception as e:
            logger.error(f"Protocol chat handler error: {str(e)}")
            return Response({
                'success': False,
                'error': f'服務器錯誤: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_input(self, message):
        """
        驗證輸入參數
        
        Args:
            message: 用戶訊息
            
        Returns:
            Response 對象（如果有錯誤）或 None（如果驗證通過）
        """
        if not message:
            return Response({
                'success': False,
                'error': '訊息內容不能為空'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        return None
    
    def _load_version_config(self, version_code=None):
        """
        🆕 從資料庫載入版本配置（優先使用 Baseline 版本）
        
        優先順序：
        1. 如果提供了 version_code，使用指定版本
        2. 否則，使用 Baseline 版本（is_baseline=True）
        3. 如果沒有 Baseline，使用預設搜尋模式
        
        Args:
            version_code: 版本代碼（可選，例如 'dify-two-tier-v1.2'）
            
        Returns:
            版本配置字典或 None
        """
        try:
            from api.models import DifyConfigVersion
            
            # 步驟 1：如果提供了 version_code，使用指定版本
            if version_code:
                try:
                    version = DifyConfigVersion.objects.get(
                        version_code=version_code,
                        is_active=True
                    )
                    logger.info(f"📌 使用指定版本: {version.version_name}")
                except DifyConfigVersion.DoesNotExist:
                    logger.warning(f"⚠️ 找不到指定版本: {version_code}，嘗試使用 Baseline")
                    version_code = None
            
            # 步驟 2：如果沒有指定 version_code，使用 Baseline 版本
            if not version_code:
                try:
                    version = DifyConfigVersion.objects.filter(
                        is_baseline=True,
                        is_active=True
                    ).first()
                    
                    if version:
                        logger.info(f"✅ 使用 Baseline 版本: {version.version_name} ({version.version_code})")
                    else:
                        logger.warning("⚠️ 找不到 Baseline 版本，使用預設搜尋模式")
                        return None
                        
                except Exception as e:
                    logger.error(f"❌ 查詢 Baseline 版本失敗: {e}")
                    return None
            
            # 步驟 3：構建版本配置
            version_config = {
                'version_code': version.version_code,
                'version_name': version.version_name,
                'rag_settings': version.rag_settings,
                'retrieval_mode': version.rag_settings.get('retrieval_mode', 'two_stage')
            }
            
            # 記錄詳細配置資訊
            stage1_config = version.rag_settings.get('stage1', {})
            use_hybrid = stage1_config.get('use_hybrid_search', False)
            title_bonus = stage1_config.get('title_match_bonus', 0)
            
            logger.info(
                f"✅ 版本配置已載入: {version.version_name} | "
                f"retrieval_mode={version_config['retrieval_mode']} | "
                f"hybrid_search={use_hybrid} | "
                f"title_boost={title_bonus}%"
            )
            
            return version_config
            
        except Exception as e:
            logger.error(f"❌ 載入版本配置時發生錯誤: {e}")
            return None
    
    def _perform_backend_search(self, query, version_config):
        """
        🆕 執行後端向量搜尋
        
        使用 ProtocolGuideSearchService 執行搜尋，
        並將版本配置傳遞下去（啟用 Title Boost 等功能）
        
        Args:
            query: 用戶查詢
            version_config: 版本配置字典
            
        Returns:
            格式化的搜尋結果字串（作為 Dify 的 Context）
        """
        try:
            from library.protocol_guide.search_service import ProtocolGuideSearchService
            
            logger.info(f"🔍 執行後端搜尋: query='{query}', version={version_config.get('version_name')}")
            
            search_service = ProtocolGuideSearchService()
            
            # 執行搜尋（傳遞版本配置）
            results = search_service.search_knowledge(
                query=query,
                limit=5,
                use_vector=True,
                threshold=0.7,
                version_config=version_config  # 🆕 傳遞版本配置
            )
            
            if not results:
                logger.info("⚠️ 後端搜尋無結果")
                return ""
            
            # 格式化搜尋結果為 Context
            context_parts = []
            for i, result in enumerate(results, 1):
                title = result.get('title', '未知標題')
                content = result.get('content', '')
                score = result.get('score', 0.0)
                
                # 檢查是否使用了 Title Boost
                metadata = result.get('metadata', {})
                title_boost_applied = metadata.get('title_boost_applied', False)
                boost_indicator = " [Title Boost ✨]" if title_boost_applied else ""
                
                context_parts.append(
                    f"[文檔 {i}] {title}{boost_indicator} (相似度: {score:.2%})\n"
                    f"{content[:500]}..."  # 限制長度
                )
            
            context = "\n\n".join(context_parts)
            
            logger.info(f"✅ 後端搜尋完成: 返回 {len(results)} 個結果")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ 後端搜尋失敗: {e}", exc_info=True)
            return ""
    
    def _get_dify_config(self):
        """
        獲取 Dify 配置
        
        Returns:
            配置對象或錯誤 Response
        """
        try:
            if self.config_manager:
                dify_config = self.config_manager()
            else:
                # 動態導入配置管理器
                from library.config.dify_config_manager import get_protocol_known_issue_config
                dify_config = get_protocol_known_issue_config()
            
            # 檢查必要配置
            if not dify_config.api_url or not dify_config.api_key:
                return Response({
                    'success': False,
                    'error': 'Dify API 配置不完整'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return dify_config
            
        except Exception as config_error:
            logger.error(f"Failed to load Protocol Known Issue config: {config_error}")
            return Response({
                'success': False,
                'error': f'配置載入失敗: {str(config_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _execute_chat_request(self, message, conversation_id, dify_config, user, version_config=None):
        """
        執行聊天請求
        
        🆕 整合後端搜尋：
        - 如果提供 version_config，執行後端向量搜尋
        - 將搜尋結果作為 Context 傳遞給 Dify
        - 支援 Title Boost 功能（透過 version_config）
        
        Args:
            message: 用戶訊息
            conversation_id: 對話 ID
            dify_config: Dify 配置
            user: 當前用戶
            version_config: 🆕 版本配置字典（可選）
            
        Returns:
            Django Response 對象
        """
        # 🆕 步驟 1: 執行後端搜尋（如果有版本配置）
        search_context = ""
        if version_config:
            search_context = self._perform_backend_search(message, version_config)
        
        # 步驟 2: 準備請求
        headers = {
            'Authorization': f'Bearer {dify_config.api_key}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'inputs': {'context': search_context} if search_context else {},  # 🆕 傳遞搜尋結果
            'query': message,
            'response_mode': 'blocking',
            'user': f"web_user_{user.id if user.is_authenticated else 'guest'}"
        }
        
        if conversation_id:
            payload['conversation_id'] = conversation_id
        
        start_time = time.time()
        
        # 步驟 3: 執行請求，帶重試機制
        try:
            response = self._make_dify_request(dify_config.api_url, headers, payload)
            elapsed = time.time() - start_time
            
            if response.status_code == 200:
                return self._handle_success_response(response, elapsed, user, message)
            else:
                return self._handle_error_response(
                    response, elapsed, conversation_id, 
                    dify_config.api_url, headers, payload, user
                )
                
        except requests.exceptions.Timeout:
            return Response({
                'success': False,
                'error': 'Dify API 請求超時，請稍後再試'
            }, status=status.HTTP_408_REQUEST_TIMEOUT)
            
        except requests.exceptions.ConnectionError:
            return Response({
                'success': False,
                'error': 'Dify API 連接失敗，請檢查網路連接'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
        except Exception as req_error:
            return Response({
                'success': False,
                'error': f'API 請求錯誤: {str(req_error)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _make_dify_request(self, api_url, headers, payload):
        """
        發送 Dify API 請求
        
        Args:
            api_url: API 地址
            headers: 請求頭
            payload: 請求載荷
            
        Returns:
            requests.Response 對象
        """
        return requests.post(
            api_url,
            headers=headers,
            json=payload,
            timeout=self.timeout
        )
    
    def _handle_success_response(self, response, elapsed, user, message):
        """
        處理成功回應
        
        Args:
            response: requests.Response 對象
            elapsed: 響應時間
            user: 用戶對象
            message: 用戶訊息
            
        Returns:
            Django Response 對象
        """
        result = response.json()
        
        # 記錄成功的聊天
        username = user.username if user.is_authenticated else 'guest'
        logger.info(f"Dify protocol chat success for user {username}: {message[:50]}...")
        
        return Response({
            'success': True,
            'answer': result.get('answer', ''),
            'conversation_id': result.get('conversation_id', ''),
            'message_id': result.get('message_id', ''),
            'response_time': elapsed,
            'metadata': result.get('metadata', {}),
            'usage': result.get('usage', {})
        }, status=status.HTTP_200_OK)
    
    def _handle_error_response(self, response, elapsed, conversation_id, 
                              api_url, headers, payload, user):
        """
        處理錯誤回應，包含自動重試邏輯
        
        Args:
            response: requests.Response 對象
            elapsed: 響應時間
            conversation_id: 對話 ID
            api_url: API 地址
            headers: 請求頭
            payload: 原始請求載荷
            user: 用戶對象
            
        Returns:
            Django Response 對象
        """
        # 特殊處理 404 錯誤（對話不存在）
        if response.status_code == 404:
            retry_response = self._handle_conversation_not_exists(
                response, conversation_id, api_url, headers, payload, user, elapsed
            )
            if retry_response:
                return retry_response
        
        # 處理一般錯誤
        username = user.username if user.is_authenticated else 'guest'
        error_msg = f"Dify API 錯誤: {response.status_code} - {response.text}"
        logger.error(f"Dify protocol chat error for user {username}: {error_msg}")
        
        return Response({
            'success': False,
            'error': error_msg,
            'response_time': elapsed
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_conversation_not_exists(self, response, conversation_id, 
                                       api_url, headers, payload, user, elapsed):
        """
        處理對話不存在的錯誤，嘗試重新開始對話
        
        Args:
            response: 原始響應
            conversation_id: 原始對話 ID
            api_url: API 地址
            headers: 請求頭
            payload: 原始載荷
            user: 用戶對象
            elapsed: 已消耗時間
            
        Returns:
            Django Response 對象或 None
        """
        try:
            response_data = response.json()
            if 'Conversation Not Exists' in response_data.get('message', ''):
                logger.warning(f"Conversation {conversation_id} not exists, retrying without conversation_id")
                
                # 重新發送請求，不帶 conversation_id
                retry_payload = {
                    'inputs': {},
                    'query': payload['query'],
                    'response_mode': 'blocking',
                    'user': payload['user']
                }
                
                retry_response = requests.post(
                    api_url,
                    headers=headers,
                    json=retry_payload,
                    timeout=self.timeout
                )
                
                if retry_response.status_code == 200:
                    retry_result = retry_response.json()
                    username = user.username if user.is_authenticated else 'guest'
                    logger.info(f"Dify protocol chat retry success for user {username}")
                    
                    return Response({
                        'success': True,
                        'answer': retry_result.get('answer', ''),
                        'conversation_id': retry_result.get('conversation_id', ''),
                        'message_id': retry_result.get('message_id', ''),
                        'response_time': elapsed,
                        'metadata': retry_result.get('metadata', {}),
                        'usage': retry_result.get('usage', {}),
                        'warning': '原對話已過期，已開始新對話'
                    }, status=status.HTTP_200_OK)
                    
        except Exception as retry_error:
            logger.error(f"Conversation retry failed: {str(retry_error)}")
        
        return None


# 便利函數：創建 Protocol Chat Handler
def create_protocol_chat_handler(config_manager=None):
    """
    創建 Protocol Chat Handler 實例
    
    Args:
        config_manager: 可選的配置管理器函數
        
    Returns:
        ProtocolChatHandler 實例
    """
    return ProtocolChatHandler(config_manager)


# 便利函數：處理 Protocol Chat API 請求
def handle_protocol_chat_api(request, config_manager=None):
    """
    處理 Protocol Chat API 請求的便利函數
    
    Args:
        request: Django request 對象
        config_manager: 可選的配置管理器函數
        
    Returns:
        Django Response 對象
    """
    handler = create_protocol_chat_handler(config_manager)
    return handler.handle_chat_request(request)