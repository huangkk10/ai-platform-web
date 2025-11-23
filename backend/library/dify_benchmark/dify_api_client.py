"""
Dify API Client - 封裝 Dify Chat API 呼叫

用途：
1. 直接呼叫 Dify Chat API（不經過後端搜尋）
2. 發送問題到 Dify，讓 Dify 自己執行 RAG 檢索
3. 接收並解析 Dify 回應
4. 處理錯誤和超時

注意：
- 不使用 ProtocolGuideSearchService
- 不整合後端搜尋
- 讓 Dify 完全自主處理 RAG
"""

import logging
import time
from typing import Dict, Any, Optional

from library.dify_integration.request_manager import DifyRequestManager
from library.config.dify_config_manager import get_protocol_guide_config

logger = logging.getLogger(__name__)


class DifyAPIClient:
    """
    Dify API Client for Benchmark Testing
    
    直接呼叫 Dify API，不經過後端搜尋系統
    
    使用方式：
        client = DifyAPIClient()
        result = client.send_question(
            question="什麼是 I3C?",
            user_id="benchmark_user",
            conversation_id=None  # 或指定特定對話 ID
        )
        
        # 返回：
        # {
        #     'success': True,
        #     'answer': "I3C 是...",
        #     'message_id': "msg_xxx",
        #     'conversation_id': "conv_xxx",
        #     'response_time': 1.23,
        #     'retrieved_documents': [...],
        #     'tokens': {...}
        # }
    """
    
    def __init__(self, timeout: int = 75):
        """
        初始化 Dify API Client
        
        Args:
            timeout: API 請求超時時間（秒），預設 75 秒
        """
        self.timeout = timeout
        
        # 獲取 Protocol Guide 的 Dify 配置
        try:
            dify_config = get_protocol_guide_config()
            self.api_url = dify_config.api_url
            self.api_key = dify_config.api_key
            
            logger.info(f"Dify API Client 初始化成功: url={self.api_url}")
            
        except Exception as e:
            logger.error(f"Dify 配置獲取失敗: {str(e)}")
            raise
        
        # 初始化 Dify Request Manager（不傳 api_url 和 api_key）
        self.request_manager = DifyRequestManager(
            default_timeout=self.timeout,
            max_retries=3,
            retry_delay=1.0,
            backoff_factor=2.0
        )
    
    def send_question(
        self,
        question: str,
        user_id: str = "benchmark_tester",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        發送問題到 Dify API（直接呼叫，不經過後端搜尋）
        
        Args:
            question: 測試問題
            user_id: 用戶 ID（預設為 benchmark_tester）
            conversation_id: 對話 ID（可選，用於連續對話）
        
        Returns:
            API 回應字典：
            {
                'success': bool,
                'answer': str,
                'message_id': str,
                'conversation_id': str,
                'response_time': float,
                'retrieved_documents': List[Dict],
                'tokens': Dict[str, int],
                'error': str (if failed)
            }
        """
        try:
            logger.info(f"發送問題到 Dify: question={question[:100]}")
            
            # 記錄開始時間
            start_time = time.time()
            
            # 構建請求 headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # 構建請求 payload
            payload = {
                'query': question,
                'user': user_id,
                'response_mode': 'blocking',  # 使用 blocking 模式等待完整回應
                'inputs': {}
            }
            
            if conversation_id:
                payload['conversation_id'] = conversation_id
            
            # 呼叫 Dify Request Manager
            response = self.request_manager.make_dify_request(
                api_url=self.api_url,
                headers=headers,
                payload=payload,
                timeout=self.timeout
            )
            
            # 計算回應時間
            response_time = time.time() - start_time
            
            # 解析回應
            if response.status_code == 200:
                data = response.json()
                
                # 提取答案（處理可能的 answer 格式）
                answer = data.get('answer', '')
                if isinstance(answer, list):
                    # 如果 answer 是列表，取第一個元素或合併
                    answer = ' '.join(str(a) for a in answer) if answer else ''
                
                # 提取其他資訊
                message_id = data.get('message_id', '')
                conversation_id = data.get('conversation_id', '')
                metadata = data.get('metadata', {})
                retrieved_documents = metadata.get('retriever_resources', [])
                
                # Token 使用情況
                tokens = {
                    'prompt_tokens': metadata.get('usage', {}).get('prompt_tokens', 0),
                    'completion_tokens': metadata.get('usage', {}).get('completion_tokens', 0),
                    'total_tokens': metadata.get('usage', {}).get('total_tokens', 0)
                }
                
                logger.info(
                    f"Dify API 回應成功: "
                    f"answer_length={len(answer)}, "
                    f"retrieved_docs={len(retrieved_documents)}, "
                    f"response_time={response_time:.2f}s"
                )
                
                return {
                    'success': True,
                    'answer': answer,
                    'message_id': message_id,
                    'conversation_id': conversation_id,
                    'response_time': round(response_time, 2),
                    'retrieved_documents': retrieved_documents,
                    'tokens': tokens
                }
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Dify API 回應失敗: {error_msg}")
                return {
                    'success': False,
                    'answer': '',
                    'error': error_msg,
                    'response_time': round(response_time, 2)
                }
            
        except Exception as e:
            logger.error(f"Dify API 呼叫失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'answer': '',
                'error': str(e),
                'response_time': 0
            }
    
    def send_questions_batch(
        self,
        questions: list[str],
        user_id: str = "benchmark_tester",
        use_same_conversation: bool = False
    ) -> list[Dict[str, Any]]:
        """
        批量發送問題（支援獨立對話或連續對話）
        
        Args:
            questions: 問題列表
            user_id: 用戶 ID
            use_same_conversation: 是否使用同一個對話 ID（預設 False）
        
        Returns:
            回應列表
        """
        results = []
        conversation_id = None
        
        for i, question in enumerate(questions, 1):
            try:
                logger.info(f"批量測試進度: {i}/{len(questions)}")
                
                # 發送問題
                result = self.send_question(
                    question=question,
                    user_id=user_id,
                    conversation_id=conversation_id if use_same_conversation else None
                )
                
                # 如果使用同一對話，保留 conversation_id
                if use_same_conversation and result.get('success'):
                    conversation_id = result.get('conversation_id')
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"批量測試失敗 (問題 {i}): {str(e)}")
                results.append({
                    'success': False,
                    'answer': '',
                    'error': str(e),
                    'response_time': 0
                })
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """
        測試 Dify API 連線
        
        Returns:
            測試結果：
            {
                'success': bool,
                'response_time': float,
                'message': str
            }
        """
        try:
            test_question = "Hello"
            result = self.send_question(
                question=test_question,
                user_id="connection_test"
            )
            
            if result.get('success'):
                return {
                    'success': True,
                    'response_time': result.get('response_time', 0),
                    'message': 'Dify API 連線成功'
                }
            else:
                return {
                    'success': False,
                    'response_time': 0,
                    'message': f"Dify API 連線失敗: {result.get('error', 'Unknown')}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': 0,
                'message': f"Dify API 連線測試異常: {str(e)}"
            }
