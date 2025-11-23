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
        api_timeout: int = 75
    ):
        """
        初始化測試執行器
        
        Args:
            version: Dify 配置版本實例
            use_ai_evaluator: 是否使用 AI 評分（預設 False，使用關鍵字評分）
            api_timeout: Dify API 超時時間（秒）
        """
        self.version = version
        self.use_ai_evaluator = use_ai_evaluator
        
        # 初始化 Dify API Client
        self.api_client = DifyAPIClient(timeout=api_timeout)
        
        # 初始化評分器
        self.keyword_evaluator = KeywordEvaluator()
        
        logger.info(
            f"DifyTestRunner 初始化完成: "
            f"version={version.version_name}, "
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
        
        # 生成預設描述
        if not description:
            description = f"測試 {len(test_cases)} 個案例，使用 {'AI 評分' if self.use_ai_evaluator else '關鍵字評分'}"
        
        test_run = DifyTestRun.objects.create(
            version=self.version,
            run_name=run_name,
            batch_id=batch_id,
            total_cases=len(test_cases),
            description=description,
            status='running'
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
        keywords = test_case.get_answer_keywords()  # 從 JSON 欄位解析
        
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
            actual_answer=actual_answer,
            score=score,
            is_passed=is_passed,
            response_time=response_time,
            dify_conversation_id=dify_conversation_id,
            dify_message_id=dify_message_id,
            retrieved_documents_count=len(retrieved_documents)
        )
        
        # 4. 儲存 AnswerEvaluation
        DifyAnswerEvaluation.objects.create(
            test_result=test_result,
            evaluation_method='keyword',
            score=score,
            is_passed=is_passed,
            matched_keywords=matched_keywords,
            missing_keywords=missing_keywords,
            evaluation_details={
                'match_details': evaluation_result.get('match_details', {}),
                'total_keywords': len(keywords),
                'matched_count': len(matched_keywords),
                'missing_count': len(missing_keywords)
            }
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
        test_run.status = 'completed'
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
            'total_cases': test_run.total_cases,
            'passed_cases': test_run.passed_cases,
            'failed_cases': test_run.failed_cases,
            'pass_rate': test_run.pass_rate,
            'average_score': test_run.average_score,
            'duration': round(duration, 2),
            'status': test_run.status
        }
