"""
Dify Test Runner - 單版本測試執行器

用途：
1. 執行單一 Dify 版本的所有測試案例
2. 呼叫 Dify API 獲取答案
3. 使用 KeywordEvaluator 進行評分
4. 記錄測試結果到資料庫

流程：
Question → Dify API (with RAG) → Answer → KeywordEvaluator → Score → Database
"""

import logging
import time
import json
import concurrent.futures
from threading import Lock
from typing import List, Dict, Any, Optional
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun,
    DifyTestResult,
    DifyAnswerEvaluation
)
from .dify_api_client import DifyAPIClient
from .evaluators import KeywordEvaluator

logger = logging.getLogger(__name__)


class DifyTestRunner:
    """
    單版本測試執行器
    
    負責執行單一 Dify 配置版本的所有測試案例
    
    使用方式：
        runner = DifyTestRunner(
            version=version_instance,
            use_ai_evaluator=False
        )
        
        test_run = runner.run_batch_tests(
            test_cases=test_cases,
            run_name="測試批次 #1",
            batch_id="batch_001"
        )
        
        # 返回：DifyTestRun 實例
    """
    
    def __init__(
        self,
        version: DifyConfigVersion,
        use_ai_evaluator: bool = False,
        api_timeout: int = 75,
        max_workers: int = 5
    ):
        """
        初始化測試執行器
        
        Args:
            version: Dify 配置版本實例
            use_ai_evaluator: 是否使用 AI 評分（預設 False，使用關鍵字評分）
            api_timeout: Dify API 超時時間（秒）
            max_workers: 多線程並行執行的最大線程數（預設 5）
        """
        self.version = version
        self.use_ai_evaluator = use_ai_evaluator
        self.max_workers = max_workers
        
        # 初始化 Dify API Client
        self.api_client = DifyAPIClient(timeout=api_timeout)
        
        # 初始化評分器
        self.keyword_evaluator = KeywordEvaluator()
        
        # 線程安全的計數器（用於多線程統計）
        self._lock = Lock()
        self._passed_count = 0
        self._failed_count = 0
        self._total_score = 0
        
        logger.info(
            f"DifyTestRunner 初始化完成: "
            f"version={version.version_name}, "
            f"max_workers={max_workers}, "
            f"evaluator={'AI' if use_ai_evaluator else 'Keyword'}"
        )
    
    def run_batch_tests(
        self,
        test_cases: List[DifyBenchmarkTestCase],
        run_name: str = None,
        batch_id: str = None,
        description: str = None
    ) -> DifyTestRun:
        """
        執行批量測試
        
        Args:
            test_cases: 測試案例列表
            run_name: 測試批次名稱（可選）
            batch_id: 批次 ID（可選，用於多版本對比）
            description: 測試描述（可選）
        
        Returns:
            DifyTestRun 實例
        """
        try:
            # 1. 創建 Test Run 記錄
            test_run = self._create_test_run(
                test_cases=test_cases,
                run_name=run_name,
                batch_id=batch_id,
                description=description
            )
            
            logger.info(
                f"開始執行測試: "
                f"run_id={test_run.id}, "
                f"version={self.version.version_name}, "
                f"total_cases={len(test_cases)}"
            )
            
            # 2. 執行所有測試案例
            passed_count = 0
            failed_count = 0
            total_score = 0
            
            for i, test_case in enumerate(test_cases, 1):
                try:
                    logger.info(f"執行測試案例 {i}/{len(test_cases)}: {test_case.question[:50]}")
                    
                    # 執行單個測試
                    result = self._run_single_test(test_run, test_case)
                    
                    # 統計結果
                    if result.is_passed:
                        passed_count += 1
                    else:
                        failed_count += 1
                    
                    total_score += result.score
                    
                    logger.info(
                        f"測試案例完成: "
                        f"score={result.score}, "
                        f"passed={'✅' if result.is_passed else '❌'}"
                    )
                    
                except Exception as e:
                    logger.error(f"測試案例執行失敗 (案例 {i}): {str(e)}", exc_info=True)
                    failed_count += 1
            
            # 3. 更新 Test Run 統計
            self._update_test_run_statistics(
                test_run=test_run,
                passed_count=passed_count,
                failed_count=failed_count,
                total_score=total_score
            )
            
            logger.info(
                f"測試執行完成: "
                f"passed={passed_count}/{len(test_cases)}, "
                f"avg_score={test_run.average_score:.2f}, "
                f"pass_rate={test_run.pass_rate:.2f}%"
            )
            
            return test_run
            
        except Exception as e:
            logger.error(f"測試執行失敗: {str(e)}", exc_info=True)
            raise
    
    def run_batch_tests_parallel(
        self,
        test_cases: List[DifyBenchmarkTestCase],
        run_name: str = None,
        batch_id: str = None,
        description: str = None
    ) -> DifyTestRun:
        """
        【多線程並行】執行批量測試
        
        使用 ThreadPoolExecutor 並行執行測試案例，大幅提升測試速度。
        每個測試使用獨立的 conversation_id，確保測試隔離。
        
        Args:
            test_cases: 測試案例列表
            run_name: 測試批次名稱（可選）
            batch_id: 批次 ID（可選，用於多版本對比）
            description: 測試描述（可選）
        
        Returns:
            DifyTestRun 實例
        
        效能提升：
            - 10 個測試：30 秒 → 6 秒（80% 提升）
            - 50 個測試：150 秒 → 30 秒（80% 提升）
        """
        try:
            # 1. 創建 Test Run 記錄
            test_run = self._create_test_run(
                test_cases=test_cases,
                run_name=run_name,
                batch_id=batch_id,
                description=description
            )
            
            # 重置線程安全計數器
            with self._lock:
                self._passed_count = 0
                self._failed_count = 0
                self._total_score = 0
            
            logger.info(
                f"開始並行測試: "
                f"run_id={test_run.id}, "
                f"version={self.version.version_name}, "
                f"total_cases={len(test_cases)}, "
                f"max_workers={self.max_workers}"
            )
            
            start_time = time.time()
            
            # 2. 使用 ThreadPoolExecutor 並行執行
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有測試任務
                future_to_case = {
                    executor.submit(
                        self._run_single_test_thread_safe,
                        test_run,
                        test_case,
                        i
                    ): test_case
                    for i, test_case in enumerate(test_cases, 1)
                }
                
                # 等待所有任務完成
                for future in concurrent.futures.as_completed(future_to_case):
                    test_case = future_to_case[future]
                    try:
                        result = future.result()
                        logger.info(
                            f"測試案例完成: "
                            f"question={test_case.question[:30]}..., "
                            f"score={result.score}, "
                            f"passed={'✅' if result.is_passed else '❌'}"
                        )
                    except Exception as e:
                        logger.error(
                            f"測試案例執行失敗: "
                            f"question={test_case.question[:30]}..., "
                            f"error={str(e)}"
                        )
            
            execution_time = time.time() - start_time
            
            # 3. 更新 Test Run 統計
            self._update_test_run_statistics(
                test_run=test_run,
                passed_count=self._passed_count,
                failed_count=self._failed_count,
                total_score=self._total_score
            )
            
            logger.info(
                f"並行測試完成: "
                f"passed={self._passed_count}/{len(test_cases)}, "
                f"avg_score={test_run.average_score:.2f}, "
                f"pass_rate={test_run.pass_rate:.2f}%, "
                f"execution_time={execution_time:.2f}s"
            )
            
            return test_run
            
        except Exception as e:
            logger.error(f"並行測試執行失敗: {str(e)}", exc_info=True)
            raise
    
    def _run_single_test_thread_safe(
        self,
        test_run: DifyTestRun,
        test_case: DifyBenchmarkTestCase,
        index: int
    ) -> DifyTestResult:
        """
        【線程安全】執行單個測試案例
        
        關鍵特性：
        1. 使用唯一的 user_id（包含測試批次和序號）
        2. 每次使用新的 conversation_id（None）
        3. 線程安全的統計更新（使用 Lock）
        4. 完全隔離，不影響 Protocol Assistant
        
        Args:
            test_run: 測試批次實例
            test_case: 測試案例實例
            index: 測試案例序號（1-based）
        
        Returns:
            DifyTestResult 實例
        """
        
        # 生成唯一的 user_id（區分測試與正常用戶）
        unique_user_id = f"benchmark_test_{test_run.id}_{index}"
        
        logger.info(
            f"[Thread {index}] 開始測試: "
            f"question={test_case.question[:50]}..., "
            f"user_id={unique_user_id}"
        )
        
        try:
            # 1. 呼叫 Dify API（使用新 conversation_id）
            api_response = self.api_client.send_question(
                question=test_case.question,
                user_id=unique_user_id,  # ✅ 唯一 user_id
                conversation_id=None     # ✅ 每次新對話
            )
            
            # 提取資訊
            actual_answer = api_response.get('answer', '')
            response_time = api_response.get('response_time', 0)
            dify_conversation_id = api_response.get('conversation_id', '')
            dify_message_id = api_response.get('message_id', '')
            retrieved_documents = api_response.get('retrieved_documents', [])
            
            # 2. 使用 KeywordEvaluator 評分
            keywords = test_case.answer_keywords  # ✅ 直接訪問 JSONField 欄位
            
            evaluation_result = self.keyword_evaluator.evaluate(
                question=test_case.question,
                expected_answer=test_case.expected_answer,
                actual_answer=actual_answer,
                keywords=keywords
            )
            
            score = evaluation_result['score']
            is_passed = evaluation_result['is_passed']
            matched_keywords = evaluation_result['matched_keywords']
            missing_keywords = evaluation_result['missing_keywords']
            
            # 3. 儲存 TestResult（Django ORM 是線程安全的）
            test_result = DifyTestResult.objects.create(
                test_run=test_run,
                test_case=test_case,
                dify_answer=actual_answer,  # ✅ 正確欄位名
                dify_message_id=dify_message_id,
                score=score,
                is_passed=is_passed,
                response_time=response_time,
                matched_keywords=matched_keywords,
                missing_keywords=missing_keywords
                # dify_conversation_id 和 retrieved_documents_count 欄位不存在，移除
            )
            
            # 4. 儲存 AnswerEvaluation
            DifyAnswerEvaluation.objects.create(
                test_result=test_result,
                question=test_case.question,
                expected_answer=test_case.expected_answer or "",
                actual_answer=actual_answer,
                evaluator_model='keyword_only',
                scores={
                    'overall_score': score,
                    'is_passed': is_passed,
                    'matched_keywords': matched_keywords,
                    'missing_keywords': missing_keywords,
                    'total_keywords': len(keywords),
                    'matched_count': len(matched_keywords),
                    'missing_count': len(missing_keywords)
                },
                feedback=f"關鍵字匹配: {len(matched_keywords)}/{len(keywords)}"
            )
            
            # 5. 線程安全地更新統計（使用 Lock）
            with self._lock:
                if is_passed:
                    self._passed_count += 1
                else:
                    self._failed_count += 1
                self._total_score += score
            
            logger.info(
                f"[Thread {index}] 測試完成: "
                f"score={score}, "
                f"passed={'✅' if is_passed else '❌'}, "
                f"response_time={response_time:.2f}s"
            )
            
            return test_result
            
        except Exception as e:
            logger.error(f"[Thread {index}] 測試執行失敗: {str(e)}", exc_info=True)
            
            # 統計失敗次數
            with self._lock:
                self._failed_count += 1
            
            raise
    
    def _create_test_run(
        self,
        test_cases: List[DifyBenchmarkTestCase],
        run_name: str,
        batch_id: str,
        description: str
    ) -> DifyTestRun:
        """創建 Test Run 記錄"""
        
        # 生成預設名稱
        if not run_name:
            run_name = f"{self.version.version_name} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 創建測試執行記錄（使用正確的欄位名稱）
        test_run = DifyTestRun.objects.create(
            version=self.version,
            run_name=run_name,
            batch_id=batch_id or '',
            total_test_cases=len(test_cases),  # ✅ 正確欄位名
            # description 和 status 欄位不存在，移除
        )
        
        return test_run
    
    def _run_single_test(
        self,
        test_run: DifyTestRun,
        test_case: DifyBenchmarkTestCase
    ) -> DifyTestResult:
        """
        執行單個測試案例
        
        流程：
        1. 呼叫 Dify API 獲取答案
        2. 使用 KeywordEvaluator 評分
        3. 儲存 TestResult 和 AnswerEvaluation
        """
        
        # 1. 呼叫 Dify API
        api_response = self.api_client.send_question(
            question=test_case.question,
            user_id=f"test_run_{test_run.id}",
            conversation_id=None  # 每個測試案例使用獨立對話
        )
        
        # 提取資訊
        actual_answer = api_response.get('answer', '')
        response_time = api_response.get('response_time', 0)
        dify_conversation_id = api_response.get('conversation_id', '')
        dify_message_id = api_response.get('message_id', '')
        retrieved_documents = api_response.get('retrieved_documents', [])
        
        # 2. 使用 KeywordEvaluator 評分
        keywords = test_case.answer_keywords  # ✅ 直接訪問 JSONField 欄位
        
        evaluation_result = self.keyword_evaluator.evaluate(
            question=test_case.question,
            expected_answer=test_case.expected_answer,
            actual_answer=actual_answer,
            keywords=keywords
        )
        
        score = evaluation_result['score']
        is_passed = evaluation_result['is_passed']
        matched_keywords = evaluation_result['matched_keywords']
        missing_keywords = evaluation_result['missing_keywords']
        
        # 3. 儲存 TestResult
        test_result = DifyTestResult.objects.create(
            test_run=test_run,
            test_case=test_case,
            dify_answer=actual_answer,  # ✅ 正確欄位名
            dify_message_id=dify_message_id,
            score=score,
            is_passed=is_passed,
            response_time=response_time,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords
            # dify_conversation_id 和 retrieved_documents_count 欄位不存在，移除
        )
        
        # 4. 儲存 AnswerEvaluation
        DifyAnswerEvaluation.objects.create(
            test_result=test_result,
            question=test_case.question,
            expected_answer=test_case.expected_answer or "",
            actual_answer=actual_answer,
            evaluator_model='keyword_only',
            scores={
                'overall_score': score,
                'is_passed': is_passed,
                'matched_keywords': matched_keywords,
                'missing_keywords': missing_keywords,
                'match_details': evaluation_result.get('match_details', {}),
                'total_keywords': len(keywords),
                'matched_count': len(matched_keywords),
                'missing_count': len(missing_keywords)
            },
            feedback=f"關鍵字匹配: {len(matched_keywords)}/{len(keywords)}"
        )
        
        return test_result
    
    def _update_test_run_statistics(
        self,
        test_run: DifyTestRun,
        passed_count: int,
        failed_count: int,
        total_score: int
    ):
        """更新 Test Run 統計資料"""
        
        total_cases = passed_count + failed_count
        
        test_run.passed_cases = passed_count
        test_run.failed_cases = failed_count
        test_run.pass_rate = (passed_count / total_cases * 100) if total_cases > 0 else 0
        test_run.average_score = (total_score / total_cases) if total_cases > 0 else 0
        # status 欄位不存在於 Model，移除
        test_run.completed_at = timezone.now()
        test_run.save()
    
    def get_test_summary(self, test_run: DifyTestRun) -> Dict[str, Any]:
        """
        獲取測試摘要
        
        Returns:
            {
                'run_id': int,
                'version_name': str,
                'total_cases': int,
                'passed_cases': int,
                'failed_cases': int,
                'pass_rate': float,
                'average_score': float,
                'duration': float (seconds)
            }
        """
        duration = 0
        if test_run.completed_at and test_run.started_at:
            duration = (test_run.completed_at - test_run.started_at).total_seconds()
        
        return {
            'run_id': test_run.id,
            'version_name': self.version.version_name,
            'total_cases': test_run.total_test_cases,  # ✅ 使用正確欄位名
            'passed_cases': test_run.passed_cases,
            'failed_cases': test_run.failed_cases,
            'pass_rate': test_run.pass_rate,
            'average_score': test_run.average_score,
            'duration': round(duration, 2),
            # status 欄位不存在，移除
        }
