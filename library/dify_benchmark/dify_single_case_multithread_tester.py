"""
Dify 單一測試案例多執行緒版本測試器 (Dify Single Case Multithread Tester)
=========================================================================

用於對單一 VSA 測試案例，使用多執行緒並行測試指定的 DifyConfigVersion 版本。

使用場景：
- 快速測試單一問題在多個 Dify 版本的表現
- 需要用戶選擇特定版本測試
- 需要並行執行以加速測試

與 Protocol Benchmark 的 SingleCaseMultithreadTester 不同：
- 使用 DifyConfigVersion 而非 SearchAlgorithmVersion
- 使用 Dify API 執行測試而非本地搜尋策略
- 使用 DifyTestRun/DifyTestResult 儲存結果
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import uuid

logger = logging.getLogger(__name__)


class DifySingleCaseMultithreadTester:
    """Dify 單一測試案例多執行緒版本測試器"""
    
    def __init__(
        self, 
        test_case_id: int, 
        version_ids: List[int], 
        max_workers: int = 3,
        verbose: bool = False,
        api_timeout: int = 75
    ):
        """
        初始化測試器
        
        Args:
            test_case_id: 測試案例 ID (DifyBenchmarkTestCase)
            version_ids: 要測試的版本 ID 列表 (DifyConfigVersion)
            max_workers: 最大並行執行緒數（預設 3，建議 1-5）
            verbose: 是否輸出詳細日誌
            api_timeout: Dify API 超時時間（秒）
        """
        if not version_ids:
            raise ValueError("version_ids 不能為空，必須指定要測試的版本")
        
        self.test_case_id = test_case_id
        self.version_ids = version_ids
        self.max_workers = min(max_workers, len(version_ids), 5)  # 限制最大 5 個執行緒
        self.verbose = verbose
        self.api_timeout = api_timeout
        self.test_case = None
        self.versions = []
        
        # 執行緒安全的結果收集
        self._results_lock = threading.Lock()
        self._results = []
        self._test_run_ids = []
    
    def run_test(self) -> Dict[str, Any]:
        """
        執行多執行緒測試
        
        Returns:
            Dict: 測試結果
        """
        try:
            self._log(f"\n{'='*80}")
            self._log(f"🚀 開始 Dify 多執行緒版本測試")
            self._log(f"{'='*80}")
            
            # 1. 準備測試案例和版本
            self._log(f"📋 準備測試案例 (ID: {self.test_case_id})...")
            self._prepare_test_case()
            
            self._log(f"📋 準備測試版本 (指定 {len(self.version_ids)} 個)...")
            self._prepare_versions()
            
            if not self.test_case:
                return {
                    'success': False,
                    'error': f'找不到測試案例 ID: {self.test_case_id}'
                }
            
            if not self.versions:
                return {
                    'success': False,
                    'error': '沒有找到指定的版本，請確認版本 ID 是否正確'
                }
            
            self._log(f"✅ 測試案例: {self.test_case.question[:80]}...")
            self._log(f"✅ 共 {len(self.versions)} 個版本: {[v.version_name for v in self.versions]}")
            self._log(f"✅ 最大並行數: {self.max_workers}")
            
            # 2. 使用 ThreadPoolExecutor 並行執行測試
            start_time = datetime.now()
            
            self._log(f"\n{'─'*80}")
            self._log(f"⚡ 開始並行測試（{self.max_workers} 個執行緒）")
            self._log(f"{'─'*80}")
            
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有版本的測試任務
                future_to_version = {
                    executor.submit(self._test_single_version_safe, version): version
                    for version in self.versions
                }
                
                # 收集結果
                completed_count = 0
                for future in as_completed(future_to_version):
                    version = future_to_version[future]
                    completed_count += 1
                    
                    try:
                        result = future.result(timeout=120)  # 2 分鐘超時
                        with self._results_lock:
                            self._results.append(result)
                            if result.get('test_run_id'):
                                self._test_run_ids.append(result['test_run_id'])
                        
                        status_icon = "✅" if result.get('status') == 'success' else "❌"
                        score = result.get('metrics', {}).get('score', 0)
                        self._log(f"  [{completed_count}/{len(self.versions)}] {status_icon} {version.version_name}: Score={score:.2f}")
                        
                    except Exception as e:
                        error_result = {
                            'version_id': version.id,
                            'version_name': version.version_name,
                            'version_code': version.version_code,
                            'status': 'error',
                            'error_message': str(e),
                            'metrics': {
                                'score': 0.0,
                                'precision': 0.0,
                                'recall': 0.0,
                                'f1_score': 0.0
                            },
                            'response_time': 0.0,
                            'matched_keywords': [],
                            'total_keywords': 0
                        }
                        with self._results_lock:
                            self._results.append(error_result)
                        
                        self._log(f"  [{completed_count}/{len(self.versions)}] ❌ {version.version_name}: {str(e)}", level='error')
            
            total_time = (datetime.now() - start_time).total_seconds()
            
            # 3. 生成摘要
            summary = self._generate_summary(total_time)
            
            self._log(f"\n{'='*80}")
            self._log(f"✅ Dify 多執行緒測試完成！")
            self._log(f"   總時間: {total_time:.2f} 秒")
            self._log(f"   成功: {summary['successful_tests']}/{summary['total_versions']}")
            if summary.get('best_version'):
                self._log(f"   最佳版本: {summary['best_version']['version_name']} (Score: {summary['best_version']['metrics']['score']:.2f})")
            self._log(f"{'='*80}")
            
            return {
                'success': True,
                'test_case': {
                    'id': self.test_case.id,
                    'question': self.test_case.question,
                    'difficulty_level': self.test_case.difficulty_level,
                    'expected_keywords': self.test_case.answer_keywords
                },
                'results': self._results,
                'summary': summary
            }
            
        except Exception as e:
            error_msg = f"Dify 多執行緒版本測試失敗: {str(e)}"
            self._log(error_msg, level='error')
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg
            }
    
    def _prepare_test_case(self):
        """準備測試案例"""
        from api.models import DifyBenchmarkTestCase
        
        try:
            self.test_case = DifyBenchmarkTestCase.objects.get(
                id=self.test_case_id,
                is_active=True
            )
        except DifyBenchmarkTestCase.DoesNotExist:
            self._log(f"測試案例不存在或已停用: {self.test_case_id}", level='warning')
            self.test_case = None
    
    def _prepare_versions(self):
        """準備要測試的版本"""
        from api.models import DifyConfigVersion
        
        # 只獲取指定且啟用的版本
        self.versions = list(
            DifyConfigVersion.objects.filter(
                id__in=self.version_ids,
                is_active=True
            ).order_by('id')
        )
        
        # 檢查是否有找不到的版本
        found_ids = {v.id for v in self.versions}
        missing_ids = set(self.version_ids) - found_ids
        if missing_ids:
            self._log(f"⚠️ 以下版本 ID 未找到或已停用: {missing_ids}", level='warning')
    
    def _test_single_version_safe(self, version) -> Dict[str, Any]:
        """
        測試單一版本（執行緒安全版本）
        
        確保每個執行緒都有獨立的資料庫連接
        """
        # 確保 Django 資料庫連接在新執行緒中正確初始化
        from django.db import connection
        connection.ensure_connection()
        
        try:
            return self._test_single_version(version)
        finally:
            # 清理執行緒的資料庫連接
            connection.close()
    
    def _test_single_version(self, version) -> Dict[str, Any]:
        """
        測試單一版本
        
        Args:
            version: DifyConfigVersion 實例
            
        Returns:
            Dict: 測試結果
        """
        from .dify_api_client import DifyAPIClient
        from .evaluators import KeywordEvaluator
        from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
        
        start_time = datetime.now()
        thread_name = threading.current_thread().name
        
        self._log(f"[{thread_name}] 🧪 開始測試版本：{version.version_name}")
        
        try:
            # 1. 載入版本配置（支援動態 Threshold）
            if DynamicThresholdLoader.is_dynamic_version(version.rag_settings):
                rag_settings = DynamicThresholdLoader.load_full_rag_settings(version.rag_settings)
            else:
                rag_settings = version.rag_settings
            
            version_config = {
                'version_code': version.version_code,
                'version_name': version.version_name,
                'rag_settings': rag_settings
            }
            
            # 2. 初始化 API Client 和評分器
            api_client = DifyAPIClient(timeout=self.api_timeout)
            evaluator = KeywordEvaluator()
            
            # 3. 呼叫 Dify API 獲取答案
            # 注意：新對話不傳遞 conversation_id，讓 Dify 自動生成
            api_response = api_client.send_question(
                question=self.test_case.question,
                conversation_id=None,  # 新對話不傳遞 conversation_id
                user_id=f"benchmark_test_{self.test_case.id}",
                version_config=version_config
            )
            
            # 4. 提取答案
            answer = api_response.get('answer', '')
            response_time = (datetime.now() - start_time).total_seconds()
            
            # 5. 評估答案
            eval_result = evaluator.evaluate(
                question=self.test_case.question,
                expected_answer=self.test_case.expected_answer or '',
                actual_answer=answer,
                keywords=self.test_case.answer_keywords or []
            )
            
            # 6. 儲存結果到資料庫
            test_run = self._save_test_result(
                version=version,
                answer=answer,
                eval_result=eval_result,
                response_time=response_time,
                api_response=api_response
            )
            
            self._log(f"[{thread_name}] ✅ {version.version_name} 完成 - Score: {eval_result['score']}, 耗時: {response_time:.2f}s")
            
            # 將 score (0-100) 轉換為 precision/recall/f1 (0-1)
            # KeywordEvaluator 的 score 本質上就是 recall（匹配關鍵字數 / 總關鍵字數）
            score_ratio = float(eval_result['score']) / 100.0
            
            return {
                'version_id': version.id,
                'version_name': version.version_name,
                'version_code': version.version_code,
                'strategy_type': rag_settings.get('retrieval_mode', version.retrieval_mode or '-'),
                'metrics': {
                    'score': float(eval_result['score']),
                    'precision': score_ratio,  # 關鍵字評分模式下，precision = recall = score
                    'recall': score_ratio,
                    'f1_score': score_ratio
                },
                'response_time': response_time,
                'matched_keywords': eval_result.get('matched_keywords', []),
                'total_keywords': len(self.test_case.answer_keywords or []),
                'answer': answer[:500],  # 截斷答案
                'status': 'success',
                'test_run_id': test_run.id if test_run else None
            }
            
        except Exception as e:
            self._log(f"[{thread_name}] ❌ {version.version_name} 失敗: {str(e)}", level='error')
            return {
                'version_id': version.id,
                'version_name': version.version_name,
                'version_code': version.version_code,
                'strategy_type': version.retrieval_mode or '-',
                'status': 'error',
                'error_message': str(e),
                'metrics': {
                    'score': 0.0,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0
                },
                'response_time': (datetime.now() - start_time).total_seconds(),
                'matched_keywords': [],
                'total_keywords': 0
            }
    
    def _save_test_result(
        self,
        version,
        answer: str,
        eval_result: Dict[str, Any],
        response_time: float,
        api_response: Dict[str, Any]
    ):
        """
        儲存測試結果到資料庫
        """
        from api.models import DifyTestRun, DifyTestResult
        
        try:
            # 創建測試運行記錄
            test_run = DifyTestRun.objects.create(
                version=version,
                run_name=f"選擇版本測試 - {self.test_case.question[:30]}...",
                batch_id=f"selected_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                total_cases=1,
                passed_cases=1 if eval_result.get('is_passed', False) else 0,
                failed_cases=0 if eval_result.get('is_passed', False) else 1,
                average_score=Decimal(str(eval_result['score'])),
                pass_rate=Decimal('100.0') if eval_result.get('is_passed', False) else Decimal('0'),
                status='completed'
            )
            
            # 創建測試結果記錄
            DifyTestResult.objects.create(
                test_run=test_run,
                test_case=self.test_case,
                dify_answer=answer,
                dify_conversation_id=api_response.get('conversation_id', ''),
                score=Decimal(str(eval_result['score'])),
                is_passed=eval_result.get('is_passed', False),
                response_time_ms=int(response_time * 1000),
                metadata={
                    'matched_keywords': eval_result.get('matched_keywords', []),
                    'total_keywords': eval_result.get('total_keywords', 0),
                    'version_name': version.version_name,
                    'test_type': 'selected_version_multithread'
                }
            )
            
            return test_run
            
        except Exception as e:
            self._log(f"儲存測試結果失敗: {str(e)}", level='error')
            return None
    
    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """生成測試摘要"""
        successful_results = [r for r in self._results if r.get('status') == 'success']
        failed_results = [r for r in self._results if r.get('status') == 'error']
        
        # 找出最佳版本（依據 score）
        best_version = None
        if successful_results:
            best_version = max(
                successful_results,
                key=lambda x: x['metrics']['score']
            )
        
        # 計算平均回應時間
        avg_response_time = 0.0
        if successful_results:
            avg_response_time = sum(
                r['response_time'] for r in successful_results
            ) / len(successful_results)
        
        return {
            'total_versions': len(self._results),
            'successful_tests': len(successful_results),
            'failed_tests': len(failed_results),
            'best_version': best_version,
            'avg_response_time': round(avg_response_time, 2),
            'total_execution_time': round(total_time, 2),
            'test_run_ids': self._test_run_ids,
            'max_workers_used': self.max_workers
        }
    
    def _log(self, message: str, level: str = 'info'):
        """輸出日誌"""
        if self.verbose:
            print(f"[DifyMultithreadTester] {message}")
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[DifySingleCaseMultithreadTester] {message}")


# ===================== 便利函數 =====================

def test_dify_single_case_selected_versions_multithread(
    test_case_id: int,
    version_ids: List[int],
    max_workers: int = 3,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    使用多執行緒測試單一 Dify 案例的指定版本
    
    Args:
        test_case_id: 測試案例 ID (DifyBenchmarkTestCase)
        version_ids: 版本 ID 列表 (DifyConfigVersion)
        max_workers: 最大並行數（預設 3）
        verbose: 是否輸出詳細日誌
        
    Returns:
        Dict: 測試結果
    """
    tester = DifySingleCaseMultithreadTester(
        test_case_id=test_case_id,
        version_ids=version_ids,
        max_workers=max_workers,
        verbose=verbose
    )
    return tester.run_test()
