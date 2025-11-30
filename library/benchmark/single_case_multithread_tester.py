"""
單一測試案例多執行緒版本測試器 (Single Case Multithread Tester)
================================================================

用於對單一測試案例，使用多執行緒並行測試指定的搜尋版本。

使用場景：
- 快速測試單一問題在多個版本的表現
- 需要用戶選擇特定版本測試
- 需要並行執行以加速測試

時間優勢（相比順序執行）：
- 3 個版本：~9 秒 → ~3 秒 (3x 加速)
- 5 個版本：~15 秒 → ~5 秒 (3x 加速)
- 10 個版本：~30 秒 → ~10 秒 (3x 加速)
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

logger = logging.getLogger(__name__)

# 執行緒本地存儲，用於 Django 資料庫連接管理
_thread_local = threading.local()


class SingleCaseMultithreadTester:
    """單一測試案例多執行緒版本測試器"""
    
    def __init__(
        self, 
        test_case_id: int, 
        version_ids: List[int], 
        max_workers: int = 3,
        verbose: bool = False
    ):
        """
        初始化測試器
        
        Args:
            test_case_id: 測試案例 ID
            version_ids: 要測試的版本 ID 列表（必須指定）
            max_workers: 最大並行執行緒數（預設 3，建議 1-5）
            verbose: 是否輸出詳細日誌
        """
        if not version_ids:
            raise ValueError("version_ids 不能為空，必須指定要測試的版本")
        
        self.test_case_id = test_case_id
        self.version_ids = version_ids
        self.max_workers = min(max_workers, len(version_ids), 5)  # 限制最大 5 個執行緒
        self.verbose = verbose
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
                {
                    'success': bool,
                    'test_case': {...},
                    'results': [
                        {
                            'version_id': int,
                            'version_name': str,
                            'strategy_type': str,
                            'metrics': {
                                'precision': float,
                                'recall': float,
                                'f1_score': float
                            },
                            'response_time': float,
                            'matched_keywords': List[str],
                            'total_keywords': int,
                            'status': 'success' | 'error',
                            'test_run_id': int (if success)
                        },
                        ...
                    ],
                    'summary': {
                        'total_versions': int,
                        'successful_tests': int,
                        'failed_tests': int,
                        'best_version': {...},
                        'avg_response_time': float,
                        'total_execution_time': float,
                        'test_run_ids': List[int],
                        'max_workers_used': int
                    }
                }
        """
        try:
            self._log(f"\n{'='*80}")
            self._log(f"🚀 開始多執行緒版本測試")
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
                        
                        status = "✅" if result.get('status') == 'success' else "❌"
                        f1 = result.get('metrics', {}).get('f1_score', 0)
                        self._log(f"  [{completed_count}/{len(self.versions)}] {status} {version.version_name}: F1={f1:.2%}")
                        
                    except Exception as e:
                        error_result = {
                            'version_id': version.id,
                            'version_name': version.version_name,
                            'strategy_type': version.parameters.get('strategy', version.algorithm_type),
                            'status': 'error',
                            'error_message': str(e),
                            'metrics': {
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
            self._log(f"✅ 多執行緒測試完成！")
            self._log(f"   總時間: {total_time:.2f} 秒")
            self._log(f"   成功: {summary['successful_tests']}/{summary['total_versions']}")
            if summary.get('best_version'):
                self._log(f"   最佳版本: {summary['best_version']['version_name']} (F1: {summary['best_version']['metrics']['f1_score']:.2%})")
            self._log(f"{'='*80}")
            
            return {
                'success': True,
                'test_case': {
                    'id': self.test_case.id,
                    'question': self.test_case.question,
                    'difficulty_level': self.test_case.difficulty_level,
                    'expected_keywords': self.test_case.expected_keywords
                },
                'results': self._results,
                'summary': summary
            }
            
        except Exception as e:
            error_msg = f"多執行緒版本測試失敗: {str(e)}"
            self._log(error_msg, level='error')
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'error': error_msg
            }
    
    def _prepare_test_case(self):
        """準備測試案例"""
        from api.models import BenchmarkTestCase
        
        try:
            self.test_case = BenchmarkTestCase.objects.get(
                id=self.test_case_id,
                is_active=True
            )
        except BenchmarkTestCase.DoesNotExist:
            self._log(f"測試案例不存在或已停用: {self.test_case_id}", level='warning')
            self.test_case = None
    
    def _prepare_versions(self):
        """準備要測試的版本"""
        from api.models import SearchAlgorithmVersion
        
        # 只獲取指定且啟用的版本
        self.versions = list(
            SearchAlgorithmVersion.objects.filter(
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
        
        Args:
            version: SearchAlgorithmVersion 實例
            
        Returns:
            Dict: 測試結果
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
            version: SearchAlgorithmVersion 實例
            
        Returns:
            Dict: 測試結果
        """
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        from library.benchmark.search_strategies import get_strategy
        
        start_time = datetime.now()
        thread_name = threading.current_thread().name
        
        self._log(f"[{thread_name}] 🧪 開始測試版本：{version.version_name}")
        
        # 1. 獲取策略類型
        strategy_type = version.parameters.get('strategy') or version.algorithm_type
        if not strategy_type:
            raise ValueError(f"版本 {version.version_name} 缺少策略類型配置")
        
        # 2. 準備策略參數
        strategy_params = {k: v for k, v in version.parameters.items() if k != 'strategy'}
        
        # 3. 獲取搜尋策略
        strategy = get_strategy(
            strategy_type,
            ProtocolGuideSearchService()
        )
        
        # 4. 執行搜尋
        search_results = strategy.execute(
            query=self.test_case.question,
            limit=10,
            **strategy_params
        )
        
        # 5. 評估結果
        metrics = self._evaluate_results(search_results)
        
        response_time = (datetime.now() - start_time).total_seconds()
        
        # 6. 儲存結果到資料庫
        test_run = self._save_test_result(
            version=version,
            metrics=metrics,
            response_time=response_time,
            search_results=search_results
        )
        
        self._log(f"[{thread_name}] ✅ {version.version_name} 完成 - F1: {metrics['f1_score']:.2%}, 耗時: {response_time:.2f}s")
        
        return {
            'version_id': version.id,
            'version_name': version.version_name,
            'strategy_type': strategy_type,
            'metrics': {
                'precision': float(metrics['precision']),
                'recall': float(metrics['recall']),
                'f1_score': float(metrics['f1_score'])
            },
            'response_time': response_time,
            'matched_keywords': metrics.get('matched_keywords', []),
            'total_keywords': metrics.get('total_keywords', 0),
            'status': 'success',
            'test_run_id': test_run.id if test_run else None
        }
    
    def _evaluate_results(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        評估搜尋結果
        
        Args:
            search_results: 搜尋結果列表
            
        Returns:
            Dict: 評估指標
        """
        if not search_results:
            return {
                'precision': Decimal('0'),
                'recall': Decimal('0'),
                'f1_score': Decimal('0'),
                'matched_keywords': [],
                'total_keywords': len(self.test_case.expected_keywords) if self.test_case.expected_keywords else 0
            }
        
        # 獲取答案關鍵字
        answer_keywords = self.test_case.expected_keywords or []
        if not answer_keywords:
            return {
                'precision': Decimal('0'),
                'recall': Decimal('0'),
                'f1_score': Decimal('0'),
                'matched_keywords': [],
                'total_keywords': 0
            }
        
        # 提取搜尋結果的內容
        result_texts = []
        for result in search_results:
            text = ""
            if 'title' in result:
                text += result['title'] + " "
            if 'content' in result:
                text += result['content']
            result_texts.append(text)
        
        combined_text = " ".join(result_texts)
        
        # 計算匹配的關鍵字
        matched_keywords = []
        for keyword in answer_keywords:
            if keyword.lower() in combined_text.lower():
                matched_keywords.append(keyword)
        
        # 計算指標
        total_keywords = len(answer_keywords)
        matched_count = len(matched_keywords)
        
        recall = Decimal(matched_count) / Decimal(total_keywords) if total_keywords > 0 else Decimal('0')
        precision = recall
        
        if precision + recall > 0:
            f1_score = (2 * precision * recall) / (precision + recall)
        else:
            f1_score = Decimal('0')
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'matched_keywords': matched_keywords,
            'total_keywords': total_keywords
        }
    
    def _save_test_result(
        self,
        version,
        metrics: Dict[str, Any],
        response_time: float,
        search_results: List[Dict[str, Any]]
    ):
        """
        儲存測試結果到資料庫
        
        Args:
            version: SearchAlgorithmVersion 實例
            metrics: 評估指標
            response_time: 回應時間（秒）
            search_results: 搜尋結果
            
        Returns:
            BenchmarkTestRun: 測試運行記錄
        """
        from api.models import BenchmarkTestRun, BenchmarkTestResult
        
        try:
            # 創建測試運行記錄
            test_run = BenchmarkTestRun.objects.create(
                version=version,
                run_name=f"選擇版本測試 - {self.test_case.question[:30]}...",
                run_type='selected_version_test',
                total_test_cases=1,
                completed_test_cases=1,
                status='completed',
                avg_precision=metrics['precision'],
                avg_recall=metrics['recall'],
                avg_f1_score=metrics['f1_score'],
                overall_score=metrics['f1_score'],
                avg_response_time=Decimal(str(response_time))
            )
            
            # 創建測試結果記錄
            matched_keywords = metrics.get('matched_keywords', [])
            total_keywords = metrics.get('total_keywords', 0)
            
            BenchmarkTestResult.objects.create(
                test_run=test_run,
                test_case=self.test_case,
                search_query=self.test_case.question,
                returned_document_ids=[r.get('id', 0) for r in search_results[:10]],
                returned_document_scores=[float(r.get('score', 0)) for r in search_results[:10]],
                precision_score=metrics['precision'],
                recall_score=metrics['recall'],
                f1_score=metrics['f1_score'],
                response_time=Decimal(str(response_time * 1000)),  # 毫秒
                true_positives=len(matched_keywords),
                false_negatives=total_keywords - len(matched_keywords),
                is_passed=metrics['f1_score'] > Decimal('0.5'),
                pass_reason=f"匹配 {len(matched_keywords)}/{total_keywords} 個關鍵字",
                detailed_results={
                    'search_results': search_results[:5],
                    'matched_keywords': matched_keywords,
                    'total_keywords': total_keywords,
                    'version_name': version.version_name,
                    'strategy_type': version.parameters.get('strategy', version.algorithm_type),
                    'test_type': 'selected_version_multithread'
                }
            )
            
            return test_run
            
        except Exception as e:
            self._log(f"儲存測試結果失敗: {str(e)}", level='error')
            return None
    
    def _generate_summary(self, total_time: float) -> Dict[str, Any]:
        """
        生成測試摘要
        
        Args:
            total_time: 總執行時間（秒）
            
        Returns:
            Dict: 測試摘要
        """
        successful_results = [r for r in self._results if r.get('status') == 'success']
        failed_results = [r for r in self._results if r.get('status') == 'error']
        
        # 找出最佳版本
        best_version = None
        if successful_results:
            best_version = max(
                successful_results,
                key=lambda x: x['metrics']['f1_score']
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
            print(f"[MultithreadTester] {message}")
        
        log_func = getattr(logger, level, logger.info)
        log_func(f"[SingleCaseMultithreadTester] {message}")


# ===================== 便利函數 =====================

def test_single_case_selected_versions_multithread(
    test_case_id: int,
    version_ids: List[int],
    max_workers: int = 3,
    verbose: bool = False
) -> Dict[str, Any]:
    """
    使用多執行緒測試單一案例的指定版本
    
    Args:
        test_case_id: 測試案例 ID
        version_ids: 版本 ID 列表
        max_workers: 最大並行數（預設 3）
        verbose: 是否輸出詳細日誌
        
    Returns:
        Dict: 測試結果
    """
    tester = SingleCaseMultithreadTester(
        test_case_id=test_case_id,
        version_ids=version_ids,
        max_workers=max_workers,
        verbose=verbose
    )
    return tester.run_test()
