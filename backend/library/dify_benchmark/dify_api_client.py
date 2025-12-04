"""
Dify API Client - 封裝 Dify Chat API 呼叫

用途：
1. 呼叫 Dify Chat API（支援後端搜尋整合）✅ v1.2 更新
2. 可選：執行後端搜尋並傳遞上下文給 Dify ✅ 新增
3. 接收並解析 Dify 回應
4. 處理錯誤和超時

v1.2 更新（2025-01-20）：
- ✅ 支援版本配置驅動的後端搜尋
- ✅ 整合 ProtocolGuideSearchService 和 Title Boost
- ✅ 向後相容：version_config 為可選參數
- ✅ 無 version_config 時保持原有行為（Dify 自主 RAG）

v1.3 更新（2025-01-21）：
- ✅ 新增 use_smart_router 選項 - 使用與 Web 完全一致的兩階段搜尋
- ✅ 當 use_smart_router=True 時，呼叫 SmartSearchRouter.handle_smart_search()
- ✅ 解決 Benchmark 測試通過率為 0% 的問題
- ✅ 確保 Benchmark 測試結果與真實用戶體驗一致
"""

import logging
import time
from typing import Dict, Any, Optional

from library.dify_integration.request_manager import DifyRequestManager
from library.config.dify_config_manager import get_protocol_guide_config

logger = logging.getLogger(__name__)


class DifyAPIClient:
    """
    Dify API Client for Benchmark Testing (支援後端搜尋整合 v1.2)
    
    ✅ v1.2 更新：支援版本配置驅動的後端搜尋
    
    使用方式 1（原有方式 - Dify 自主 RAG）：
        client = DifyAPIClient()
        result = client.send_question(
            question="什麼是 I3C?",
            user_id="benchmark_user",
            conversation_id=None
        )
    
    使用方式 2（v1.2 新增 - 後端搜尋 + Title Boost）：
        client = DifyAPIClient()
        result = client.send_question(
            question="IOL SOP",
            user_id="benchmark_user",
            conversation_id=None,
            version_config={  # ✅ 傳遞版本配置
                'version_code': 'v1.2',
                'rag_settings': {...}
            }
        )
        
        # 返回：
        # {
        #     'success': True,
        #     'answer': "I3C 是...",
        #     'message_id': "msg_xxx",
        #     'conversation_id': "conv_xxx",
        #     'response_time': 1.23,
        #     'retrieved_documents': [...],
        #     'tokens': {...},
        #     'backend_search_used': True,  # ✅ 新增欄位
        #     'search_results_count': 3     # ✅ 新增欄位
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
        conversation_id: Optional[str] = None,
        version_config: Optional[Dict[str, Any]] = None  # ✅ v1.2 新增參數
    ) -> Dict[str, Any]:
        """
        發送問題到 Dify API（支援後端搜尋整合 v1.2）
        
        Args:
            question: 測試問題
            user_id: 用戶 ID（預設為 benchmark_tester）
            conversation_id: 對話 ID（可選，用於連續對話）
            version_config: 版本配置字典（可選，v1.2 新增）
                {
                    'version_code': 'v1.2',
                    'version_name': 'Dify 二階搜尋 v1.2',
                    'rag_settings': {...}
                }
        
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
                'backend_search_used': bool,  # ✅ v1.2 新增
                'search_results_count': int,  # ✅ v1.2 新增
                'error': str (if failed)
            }
        """
        try:
            logger.info(f"發送問題到 Dify: question={question[:100]}")
            
            # ✅ v1.2: 執行後端搜尋（如果有版本配置）
            search_context = None
            search_results_count = 0
            backend_search_used = False
            
            if version_config:
                search_context, search_results_count = self._perform_backend_search(
                    question, 
                    version_config
                )
                if search_context:
                    backend_search_used = True
                    logger.info(
                        f"✅ 後端搜尋完成: "
                        f"version={version_config.get('version_code')}, "
                        f"results={search_results_count}"
                    )
            
            # 記錄開始時間
            start_time = time.time()
            
            # 構建請求 headers
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            # ✅ v1.2: 構建請求 payload（包含後端搜尋上下文）
            payload = {
                'query': question,
                'user': user_id,
                'response_mode': 'blocking',  # 使用 blocking 模式等待完整回應
                'inputs': {'context': search_context} if search_context else {}  # ✅ 傳遞搜尋上下文
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
                    f"backend_search={backend_search_used}, "  # ✅ v1.2 新增
                    f"response_time={response_time:.2f}s"
                )
                
                return {
                    'success': True,
                    'answer': answer,
                    'message_id': message_id,
                    'conversation_id': conversation_id,
                    'response_time': round(response_time, 2),
                    'retrieved_documents': retrieved_documents,
                    'tokens': tokens,
                    'backend_search_used': backend_search_used,  # ✅ v1.2 新增
                    'search_results_count': search_results_count  # ✅ v1.2 新增
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
    
    def send_question_with_smart_router(
        self,
        question: str,
        user_id: str = "benchmark_tester",
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ✅ v1.3 新增：使用 SmartSearchRouter 發送問題（與 Web 完全一致）
        
        此方法使用與 Web Protocol Assistant 完全相同的搜尋邏輯：
        1. 智能路由：根據查詢決定使用 Mode A 或 Mode B
        2. 兩階段搜尋：Stage 1 段落搜尋 → Stage 2 全文搜尋（fallback）
        3. 不確定回答檢測：自動觸發更深入的搜尋
        
        使用場景：
        - Benchmark 測試需要與真實用戶體驗一致時
        - 測試 "iol root 密碼" 這類需要 Stage 2 才能回答的問題
        
        Args:
            question: 測試問題
            user_id: 用戶 ID
            conversation_id: 對話 ID（可選）
            
        Returns:
            Dict: 與 send_question 相同格式的回應
            {
                'success': bool,
                'answer': str,
                'message_id': str,
                'conversation_id': str,
                'response_time': float,
                'retrieved_documents': List,
                'tokens': Dict,
                'smart_router_used': True,  # ✅ 標記使用了 SmartRouter
                'search_mode': str,         # ✅ 'mode_a' 或 'mode_b'
                'search_stage': int,        # ✅ 1 或 2
                'is_fallback': bool         # ✅ 是否為降級模式
            }
        """
        import time
        
        try:
            # 延遲導入避免循環引用
            from library.protocol_guide.smart_search_router import SmartSearchRouter
            
            logger.info(f"🔄 使用 SmartSearchRouter 發送問題: {question[:50]}...")
            
            start_time = time.time()
            
            # 創建 SmartSearchRouter 實例
            router = SmartSearchRouter()
            
            # 使用與 Web 完全一致的邏輯
            result = router.handle_smart_search(
                user_query=question,
                conversation_id=conversation_id or "",
                user_id=user_id
            )
            
            response_time = time.time() - start_time
            
            # 提取 metadata 中的引用文件
            metadata = result.get('metadata', {})
            retriever_resources = metadata.get('retriever_resources', [])
            
            # 轉換為標準格式
            return {
                'success': True,
                'answer': result.get('answer', ''),
                'message_id': result.get('message_id', ''),
                'conversation_id': result.get('conversation_id', ''),
                'response_time': round(response_time, 2),
                'retrieved_documents': retriever_resources,
                'tokens': result.get('tokens', {}),
                # ✅ SmartRouter 特有欄位
                'smart_router_used': True,
                'search_mode': result.get('mode', 'unknown'),
                'search_stage': result.get('stage', 0),
                'is_fallback': result.get('is_fallback', False),
                'backend_search_used': True,
                'search_results_count': len(retriever_resources)
            }
            
        except Exception as e:
            logger.error(f"❌ SmartSearchRouter 呼叫失敗: {str(e)}", exc_info=True)
            return {
                'success': False,
                'answer': '',
                'error': str(e),
                'response_time': 0,
                'smart_router_used': True
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
                'message': f'連線測試異常: {str(e)}'
            }
    
    def _perform_backend_search(
        self, 
        query: str, 
        version_config: Dict[str, Any]
    ) -> tuple[Optional[str], int]:
        """
        執行後端搜尋並格式化結果為上下文（v1.2 新增）
        
        Args:
            query: 用戶查詢
            version_config: 版本配置字典
                {
                    'version_code': 'v1.2',
                    'version_name': 'Dify 二階搜尋 v1.2',
                    'rag_settings': {...}
                }
        
        Returns:
            tuple: (搜尋上下文字串, 結果數量)
                - None, 0: 搜尋失敗或無結果
                - str, int: 格式化的上下文和結果數量
        """
        try:
            from library.protocol_guide.search_service import ProtocolGuideSearchService
            
            logger.info(
                f"🔍 執行後端搜尋: "
                f"query={query[:50]}..., "
                f"version={version_config.get('version_code')}"
            )
            
            # 執行搜尋
            search_service = ProtocolGuideSearchService()
            results = search_service.search_knowledge(
                query=query,
                threshold=0.5,
                limit=3,
                use_vector=True,
                stage='stage1',
                version_config=version_config  # ✅ 傳遞版本配置
            )
            
            if not results:
                logger.warning("⚠️ 後端搜尋無結果")
                return None, 0
            
            # 格式化結果為上下文字串
            context_parts = []
            for i, result in enumerate(results, 1):
                title = result.get('title', 'Untitled')
                content = result.get('content', '')[:500]  # 限制長度
                score = result.get('score', 0.0) * 100
                
                # 檢查是否有 Title Boost
                boost_flag = ""
                if result.get('title_boost_applied'):
                    boost_flag = " 🌟 [Title Boost]"
                    boost_amount = result.get('boost_amount', 0) * 100
                    logger.info(
                        f"  [{i}] Title Boost 加分: "
                        f"title={title[:30]}..., "
                        f"bonus=+{boost_amount:.1f}%"
                    )
                
                context_parts.append(
                    f"[{i}] {title} (相關度: {score:.1f}%){boost_flag}\n"
                    f"{content}..."
                )
            
            context = "\n\n".join(context_parts)
            
            logger.info(
                f"✅ 後端搜尋完成: "
                f"results={len(results)}, "
                f"context_length={len(context)}"
            )
            
            return context, len(results)
            
        except Exception as e:
            logger.error(f"❌ 後端搜尋失敗: {str(e)}", exc_info=True)
            return None, 0
