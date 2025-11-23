"""Benchmark Test Runner"""
import time
import logging
from typing import List, Dict, Any
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from api.models import SearchAlgorithmVersion, BenchmarkTestCase, BenchmarkTestRun, BenchmarkTestResult
from library.protocol_guide.search_service import ProtocolGuideSearchService
from .scoring_engine import ScoringEngine

logger = logging.getLogger(__name__)

class BenchmarkTestRunner:
    def __init__(self, version_id: int, verbose: bool = False):
        self.version_id = version_id
        self.verbose = verbose
        self.search_service = ProtocolGuideSearchService()
        self.version = SearchAlgorithmVersion.objects.get(id=version_id)
    
    def _log(self, msg: str, level: str = 'INFO'):
        if self.verbose:
            print(f"[{level}] {msg}", flush=True)
    
    def run_single_test(self, test_case, save_to_db=False, test_run=None):
        try:
            start = time.time()
            
            # ✅ 使用版本的搜尋參數配置
            search_params = self.version.parameters or {}
            strategy = search_params.get('strategy', 'hybrid_weighted')
            
            # 根據策略執行搜尋
            if strategy == 'section_only':
                # 純段落搜尋
                search_mode = 'section_only'
                threshold = search_params.get('section_threshold', 0.75)
                
                logger.info(f"🔍 版本 {self.version.version_code} - 策略: section_only, threshold: {threshold}")
                
                results = self.search_service.search_with_vectors(
                    query=test_case.question, 
                    limit=10, 
                    threshold=threshold,
                    search_mode=search_mode,
                    stage=1
                )
                
            elif strategy == 'document_only':
                # 純全文搜尋
                search_mode = 'document_only'
                threshold = search_params.get('document_threshold', 0.65)
                
                logger.info(f"🔍 版本 {self.version.version_code} - 策略: document_only, threshold: {threshold}")
                
                results = self.search_service.search_with_vectors(
                    query=test_case.question, 
                    limit=10, 
                    threshold=threshold,
                    search_mode=search_mode,
                    stage=1
                )
                
            elif strategy == 'hybrid_weighted':
                # ✅ 混合權重搜尋 - 使用 HybridWeightedStrategy
                from library.benchmark.search_strategies import HybridWeightedStrategy
                
                section_weight = search_params.get('section_weight', 0.7)
                document_weight = search_params.get('document_weight', 0.3)
                section_threshold = search_params.get('section_threshold', 0.75)
                document_threshold = search_params.get('document_threshold', 0.65)
                
                logger.info(
                    f"🔍 版本 {self.version.version_code} - 策略: hybrid_weighted | "
                    f"section_weight={section_weight}, document_weight={document_weight} | "
                    f"section_threshold={section_threshold}, document_threshold={document_threshold}"
                )
                
                hybrid_strategy = HybridWeightedStrategy(self.search_service)
                results = hybrid_strategy.execute(
                    query=test_case.question,
                    limit=10,
                    section_weight=section_weight,
                    document_weight=document_weight,
                    section_threshold=section_threshold,
                    document_threshold=document_threshold
                )
                
            else:
                # 未知策略 - 使用 auto 模式
                logger.warning(f"⚠️ 未知策略 '{strategy}'，使用 auto 模式")
                results = self.search_service.search_with_vectors(
                    query=test_case.question, 
                    limit=10, 
                    threshold=0.7,
                    search_mode='auto',
                    stage=1
                )
            
            logger.info(f"   ✅ 搜尋完成，返回 {len(results)} 個結果")
            
            rt = (time.time() - start) * 1000
            ids = [r.get('metadata', {}).get('id') or r.get('id') or r.get('document_id') for r in results if r.get('metadata', {}).get('id') or r.get('id') or r.get('document_id')]
            m = ScoringEngine.calculate_all_metrics(ids, test_case.expected_document_ids, rt, 10)
            passed = m['true_positives'] >= test_case.min_required_matches
            result = {'test_case': test_case, 'search_query': test_case.question,
                     'returned_document_ids': ids, 'returned_document_scores': [r.get('score', 0) for r in results],
                     'response_time': rt, 'is_passed': passed, **m}
            if save_to_db and test_run:
                BenchmarkTestResult.objects.create(
                    test_run=test_run, test_case=test_case, search_query=test_case.question,
                    returned_document_ids=ids, returned_document_scores=result['returned_document_scores'],
                    precision_score=Decimal(str(m['precision'])), recall_score=Decimal(str(m['recall'])),
                    f1_score=Decimal(str(m['f1_score'])), ndcg_score=Decimal(str(m['ndcg'])),
                    response_time=Decimal(str(rt)), true_positives=m['true_positives'],
                    false_positives=m['false_positives'], false_negatives=m['false_negatives'], is_passed=passed)
            return result
        except Exception as e:
            logger.exception(f"測試失敗: {e}")
            self._log(f"測試失敗: {e}", 'ERROR')
            return {'test_case': test_case, 'search_query': test_case.question, 'is_passed': False, 
                   'precision': 0, 'recall': 0, 'f1_score': 0, 'ndcg': 0, 'speed_score': 0, 
                   'overall_score': 0, 'true_positives': 0, 'false_positives': 0,
                   'false_negatives': len(test_case.expected_document_ids), 'response_time': 0,
                   'returned_document_ids': [], 'returned_document_scores': []}
    
    @transaction.atomic
    def run_batch_tests(self, test_cases, run_name, run_type='manual', notes=''):
        self._log(f"開始測試: {run_name}")
        test_run = BenchmarkTestRun.objects.create(
            version=self.version, run_name=run_name, run_type=run_type, notes=notes,
            total_test_cases=len(test_cases), status='running', started_at=timezone.now())
        results, passed = [], 0
        for i, tc in enumerate(test_cases, 1):
            self._log(f"[{i}/{len(test_cases)}] {tc.question[:40]}...")
            r = self.run_single_test(tc, True, test_run)
            results.append(r)
            if r['is_passed']:
                passed += 1
            test_run.completed_test_cases = i
            test_run.passed_test_cases = passed
            test_run.failed_test_cases = i - passed
            test_run.save()
        n = len(results)
        ap = sum(r.get('precision', 0) for r in results) / n
        ar = sum(r.get('recall', 0) for r in results) / n
        af = sum(r.get('f1_score', 0) for r in results) / n
        an = sum(r.get('ndcg', 0) for r in results) / n
        asp = sum(r.get('speed_score', 0) for r in results) / n
        os = ScoringEngine.calculate_overall_score(ap, ar, af, an, asp)
        test_run.overall_score = Decimal(str(os))
        test_run.avg_precision = Decimal(str(round(ap, 4)))
        test_run.avg_recall = Decimal(str(round(ar, 4)))
        test_run.avg_f1_score = Decimal(str(round(af, 4)))
        test_run.avg_response_time = Decimal(str(round(sum(r.get('response_time', 0) for r in results) / n, 2)))
        test_run.status = 'completed'
        test_run.completed_at = timezone.now()
        test_run.duration_seconds = int((test_run.completed_at - test_run.started_at).total_seconds())
        test_run.save()
        self._log(f"✅ 完成！分數: {os:.2f} | 通過: {passed}/{len(test_cases)}")
        return test_run
