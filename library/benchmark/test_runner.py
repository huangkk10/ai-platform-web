"""Benchmark Test Runner"""
import time
from typing import List, Dict, Any
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from api.models import SearchAlgorithmVersion, BenchmarkTestCase, BenchmarkTestRun, BenchmarkTestResult
from library.protocol_guide.search_service import ProtocolGuideSearchService
from .scoring_engine import ScoringEngine

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
            results = self.search_service.search_knowledge(query=test_case.question, limit=10, use_vector=True)
            rt = (time.time() - start) * 1000
            ids = [r.get('metadata', {}).get('id') or r.get('id') for r in results if r.get('metadata', {}).get('id') or r.get('id')]
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
            version=self.version, run_name=run_name, run_type=run_type,
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
        test_run.precision_pct = Decimal(str(round(ap * 100, 2)))
        test_run.recall_pct = Decimal(str(round(ar * 100, 2)))
        test_run.f1_score_pct = Decimal(str(round(af * 100, 2)))
        test_run.ndcg_pct = Decimal(str(round(an * 100, 2)))
        test_run.speed_score_pct = Decimal(str(round(asp, 2)))
        test_run.avg_time_ms = Decimal(str(round(sum(r.get('response_time', 0) for r in results) / n, 2)))
        test_run.status = 'completed'
        test_run.completed_at = timezone.now()
        test_run.duration_seconds = int((test_run.completed_at - test_run.started_at).total_seconds())
        test_run.save()
        self._log(f"✅ 完成！分數: {os:.2f} | 通過: {passed}/{len(test_cases)}")
        return test_run
