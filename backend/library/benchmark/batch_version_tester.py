"""批量版本測試器 (Batch Version Tester)"""
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class BatchVersionTester:
    """批量版本測試器"""
    
    def __init__(self, verbose=False):
        self.verbose = verbose
    
    def run_batch_test(self, version_ids=None, test_case_ids=None, batch_name=None, notes="", force_retest=False):
        """執行批量測試"""
        from api.models import SearchAlgorithmVersion, BenchmarkTestCase
        
        batch_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not batch_name:
            batch_name = "批量測試 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        versions = self._prepare_versions(version_ids, force_retest, test_case_ids)
        if not versions:
            return {"success": False, "error": "沒有版本需要測試", "batch_id": batch_id}
        
        test_cases = self._prepare_test_cases(test_case_ids)
        if not test_cases:
            return {"success": False, "error": "沒有可用的測試案例", "batch_id": batch_id}
        
        print("準備測試 " + str(len(versions)) + " 個版本，" + str(len(test_cases)) + " 個測試案例")
        test_runs, test_run_ids, start_time = [], [], datetime.now()
        
        for idx, version in enumerate(versions, 1):
            print("測試版本 " + str(idx) + "/" + str(len(versions)) + ": " + version.version_name)
            try:
                test_run = self._run_single_version_test(version, test_cases, batch_id, batch_name, notes)
                test_runs.append(test_run)
                test_run_ids.append(test_run.id)
                print("  ✅ 完成")
            except Exception as e:
                print("  ❌ 失敗: " + str(e))
        
        execution_time = (datetime.now() - start_time).total_seconds()
        return {
            "success": True,
            "batch_id": batch_id,
            "batch_name": batch_name,
            "test_runs": test_runs,
            "test_run_ids": test_run_ids,
            "comparison": self._generate_comparison(test_runs),
            "summary": self._generate_summary(test_runs, test_cases, execution_time),
        }
    
    def _prepare_versions(self, version_ids, force_retest, test_case_ids):
        from api.models import SearchAlgorithmVersion
        return list(SearchAlgorithmVersion.objects.filter(id__in=version_ids) if version_ids else SearchAlgorithmVersion.objects.all())
    
    def _prepare_test_cases(self, test_case_ids):
        from api.models import BenchmarkTestCase
        return list(BenchmarkTestCase.objects.filter(id__in=test_case_ids, is_active=True) if test_case_ids else BenchmarkTestCase.objects.filter(is_active=True))
    
    def _run_single_version_test(self, version, test_cases, batch_id, batch_name, notes):
        from library.benchmark.test_runner import BenchmarkTestRunner
        runner = BenchmarkTestRunner(version_id=version.id, verbose=self.verbose)
        run_name = batch_name + " - " + version.version_name
        run_notes = "批次 ID: " + batch_id + "\n" + notes
        return runner.run_batch_tests(test_cases=test_cases, run_name=run_name, run_type="batch_comparison", notes=run_notes)
    
    def _generate_comparison(self, test_runs):
        versions_data = [{"version_id": tr.version.id, "version_name": tr.version.version_name, "overall_score": float(tr.overall_score or 0), "precision": float(tr.precision or 0), "recall": float(tr.recall or 0), "f1_score": float(tr.f1_score or 0)} for tr in test_runs]
        ranking = {"by_overall_score": sorted(versions_data, key=lambda x: x["overall_score"], reverse=True)}
        return {"versions": versions_data, "ranking": ranking, "best_version": ranking["by_overall_score"][0] if ranking["by_overall_score"] else None, "trade_offs": []}
    
    def _generate_summary(self, test_runs, test_cases, execution_time):
        return {"total_versions_tested": len(test_runs), "total_test_cases": len(test_cases), "total_tests_executed": len(test_runs) * len(test_cases), "execution_time": execution_time}


def batch_test_all_versions(test_case_ids=None, force_retest=False, verbose=False):
    return BatchVersionTester(verbose=verbose).run_batch_test(version_ids=None, test_case_ids=test_case_ids, force_retest=force_retest)


def batch_test_selected_versions(version_ids, test_case_ids=None, batch_name=None, notes="", verbose=False):
    return BatchVersionTester(verbose=verbose).run_batch_test(version_ids=version_ids, test_case_ids=test_case_ids, batch_name=batch_name, notes=notes)
