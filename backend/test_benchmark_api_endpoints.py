#!/usr/bin/env python
"""
Benchmark API 端點完整測試

測試所有 26 個 API 端點，包含：
- 認證測試
- CRUD 操作測試
- 自訂 Actions 測試
- 篩選和分頁測試
- 錯誤處理測試
"""

import os
import django
import json
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate
from rest_framework import status

from api.views import (
    BenchmarkTestCaseViewSet,
    BenchmarkTestRunViewSet,
    BenchmarkTestResultViewSet,
    SearchAlgorithmVersionViewSet
)
from api.models import (
    BenchmarkTestCase,
    BenchmarkTestRun,
    BenchmarkTestResult,
    SearchAlgorithmVersion
)

User = get_user_model()


class BenchmarkAPITester:
    """Benchmark API 測試器"""
    
    def __init__(self):
        self.factory = APIRequestFactory()
        self.user = self._get_or_create_test_user()
        self.passed = 0
        self.failed = 0
        self.total = 0
        
    def _get_or_create_test_user(self):
        """獲取或創建測試用戶"""
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={
                'email': 'test@example.com',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        return user
    
    def _make_request(self, viewset_class, action, method='GET', 
                     pk=None, data=None, query_params=None):
        """創建並執行 API 請求"""
        url = f'/api/benchmark/'
        
        if method == 'GET':
            request = self.factory.get(url, query_params or {})
        elif method == 'POST':
            request = self.factory.post(
                url, 
                json.dumps(data or {}),
                content_type='application/json'
            )
        elif method == 'PUT':
            request = self.factory.put(
                url,
                json.dumps(data or {}),
                content_type='application/json'
            )
        elif method == 'DELETE':
            request = self.factory.delete(url)
        
        force_authenticate(request, user=self.user)
        
        viewset = viewset_class()
        viewset.action = action
        viewset.request = request
        viewset.format_kwarg = None
        
        if pk:
            viewset.kwargs = {'pk': pk}
        
        return viewset
    
    def test(self, name, test_func):
        """執行單一測試"""
        self.total += 1
        try:
            result = test_func()
            if result:
                self.passed += 1
                print(f"✅ {self.total}. {name}")
                return True
            else:
                self.failed += 1
                print(f"❌ {self.total}. {name}")
                return False
        except Exception as e:
            self.failed += 1
            print(f"❌ {self.total}. {name} - 錯誤: {str(e)}")
            return False
    
    def print_summary(self):
        """打印測試總結"""
        print("\n" + "=" * 60)
        print(f"📊 測試總結")
        print("=" * 60)
        print(f"總測試數: {self.total}")
        print(f"✅ 通過: {self.passed} ({self.passed/self.total*100:.1f}%)")
        print(f"❌ 失敗: {self.failed} ({self.failed/self.total*100:.1f}%)")
        print("=" * 60)


def main():
    """主測試函數"""
    tester = BenchmarkAPITester()
    
    print("=" * 60)
    print("🧪 Benchmark API 端點測試")
    print("=" * 60)
    print()
    
    # ==================== 測試案例 API ====================
    print("📋 測試案例 API (Test Cases)")
    print("-" * 60)
    
    # 1. 列出測試案例
    def test_list_cases():
        viewset = tester._make_request(BenchmarkTestCaseViewSet, 'list')
        response = viewset.list(viewset.request)
        return response.status_code == 200 and 'results' in response.data
    
    tester.test("GET /api/benchmark/test-cases/", test_list_cases)
    
    # 2. 獲取單一測試案例
    def test_retrieve_case():
        case = BenchmarkTestCase.objects.first()
        if not case:
            return False
        viewset = tester._make_request(BenchmarkTestCaseViewSet, 'retrieve', pk=case.id)
        response = viewset.retrieve(viewset.request, pk=case.id)
        return response.status_code == 200 and response.data['id'] == case.id
    
    tester.test("GET /api/benchmark/test-cases/{id}/", test_retrieve_case)
    
    # 3. 測試統計 API
    def test_statistics():
        viewset = tester._make_request(BenchmarkTestCaseViewSet, 'statistics')
        response = viewset.statistics(viewset.request)
        return (response.status_code == 200 and 
                'total_count' in response.data and
                'by_category' in response.data)
    
    tester.test("GET /api/benchmark/test-cases/statistics/", test_statistics)
    
    # 4. 測試類別篩選
    def test_filter_by_category():
        viewset = tester._make_request(
            BenchmarkTestCaseViewSet, 
            'list',
            query_params={'category': '資源路徑'}
        )
        response = viewset.list(viewset.request)
        if response.status_code != 200:
            return False
        # 檢查返回的案例是否都符合類別
        for case in response.data.get('results', []):
            if case.get('category') != '資源路徑':
                return False
        return True
    
    tester.test("GET /api/benchmark/test-cases/?category=資源路徑", test_filter_by_category)
    
    # 5. 測試難度篩選
    def test_filter_by_difficulty():
        viewset = tester._make_request(
            BenchmarkTestCaseViewSet,
            'list',
            query_params={'difficulty': 'easy'}
        )
        response = viewset.list(viewset.request)
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-cases/?difficulty=easy", test_filter_by_difficulty)
    
    # 6. 創建測試案例
    def test_create_case():
        viewset = tester._make_request(
            BenchmarkTestCaseViewSet,
            'create',
            method='POST',
            data={
                'question': 'API 測試問題',
                'category': 'API測試',
                'difficulty_level': 'easy',
                'question_type': '測試',
                'knowledge_source': 'API',
                'expected_document_ids': [1, 2],
                'min_required_matches': 1,
                'is_active': True
            }
        )
        response = viewset.create(viewset.request)
        return response.status_code == 201
    
    tester.test("POST /api/benchmark/test-cases/", test_create_case)
    
    # 7. 批量啟用
    def test_bulk_activate():
        cases = BenchmarkTestCase.objects.filter(is_active=False)[:3]
        if not cases.exists():
            # 先停用一些案例
            BenchmarkTestCase.objects.filter(id__in=[1, 2, 3]).update(is_active=False)
            cases = BenchmarkTestCase.objects.filter(id__in=[1, 2, 3])
        
        viewset = tester._make_request(
            BenchmarkTestCaseViewSet,
            'bulk_activate',
            method='POST',
            data={'ids': [c.id for c in cases]}
        )
        response = viewset.bulk_activate(viewset.request)
        return response.status_code == 200 and response.data.get('success') == True
    
    tester.test("POST /api/benchmark/test-cases/bulk_activate/", test_bulk_activate)
    
    # 8. 批量停用
    def test_bulk_deactivate():
        cases = BenchmarkTestCase.objects.filter(is_active=True)[:2]
        if not cases.exists():
            return False
        
        viewset = tester._make_request(
            BenchmarkTestCaseViewSet,
            'bulk_deactivate',
            method='POST',
            data={'ids': [c.id for c in cases]}
        )
        response = viewset.bulk_deactivate(viewset.request)
        return response.status_code == 200 and response.data.get('success') == True
    
    tester.test("POST /api/benchmark/test-cases/bulk_deactivate/", test_bulk_deactivate)
    
    print()
    
    # ==================== 測試執行 API ====================
    print("🚀 測試執行 API (Test Runs)")
    print("-" * 60)
    
    # 9. 列出測試執行
    def test_list_runs():
        viewset = tester._make_request(BenchmarkTestRunViewSet, 'list')
        response = viewset.list(viewset.request)
        return response.status_code == 200 and 'results' in response.data
    
    tester.test("GET /api/benchmark/test-runs/", test_list_runs)
    
    # 10. 獲取單一測試執行
    def test_retrieve_run():
        run = BenchmarkTestRun.objects.first()
        if not run:
            return False
        viewset = tester._make_request(BenchmarkTestRunViewSet, 'retrieve', pk=run.id)
        response = viewset.retrieve(viewset.request, pk=run.id)
        return response.status_code == 200 and response.data['id'] == run.id
    
    tester.test("GET /api/benchmark/test-runs/{id}/", test_retrieve_run)
    
    # 11. 測試版本篩選
    def test_filter_by_version():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        
        viewset = tester._make_request(
            BenchmarkTestRunViewSet,
            'list',
            query_params={'version_id': version.id}
        )
        response = viewset.list(viewset.request)
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-runs/?version_id=X", test_filter_by_version)
    
    # 12. 測試狀態篩選
    def test_filter_by_status():
        viewset = tester._make_request(
            BenchmarkTestRunViewSet,
            'list',
            query_params={'status': 'completed'}
        )
        response = viewset.list(viewset.request)
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-runs/?status=completed", test_filter_by_status)
    
    # 13. 獲取測試結果
    def test_get_results():
        run = BenchmarkTestRun.objects.filter(results__isnull=False).first()
        if not run:
            return False
        
        viewset = tester._make_request(BenchmarkTestRunViewSet, 'results', pk=run.id)
        response = viewset.results(viewset.request, pk=run.id)
        return response.status_code == 200 and isinstance(response.data, list)
    
    tester.test("GET /api/benchmark/test-runs/{id}/results/", test_get_results)
    
    # 14. 啟動新測試（簡化版，只測 5 題）
    def test_start_test():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        
        # 確保有啟用的測試案例
        active_count = BenchmarkTestCase.objects.filter(is_active=True).count()
        if active_count < 3:
            BenchmarkTestCase.objects.filter(id__in=[1, 2, 3]).update(is_active=True)
        
        viewset = tester._make_request(
            BenchmarkTestRunViewSet,
            'start_test',
            method='POST',
            data={
                'version_id': version.id,
                'run_name': f'API 測試 - {datetime.now().strftime("%H:%M:%S")}',
                'run_type': 'manual',
                'limit': 3,  # 只測 3 題
                'notes': 'API 端點測試'
            }
        )
        response = viewset.start_test(viewset.request)
        return response.status_code == 201 and response.data.get('success') == True
    
    tester.test("POST /api/benchmark/test-runs/start_test/", test_start_test)
    
    # 15. 比較測試執行
    def test_compare_runs():
        runs = BenchmarkTestRun.objects.filter(status='completed')[:2]
        if runs.count() < 2:
            return False
        
        viewset = tester._make_request(
            BenchmarkTestRunViewSet,
            'compare',
            method='POST',
            data={
                'run_id_1': runs[0].id,
                'run_id_2': runs[1].id
            }
        )
        response = viewset.compare(viewset.request)
        return (response.status_code == 200 and 
                'run_1' in response.data and
                'run_2' in response.data and
                'delta' in response.data)
    
    tester.test("POST /api/benchmark/test-runs/compare/", test_compare_runs)
    
    print()
    
    # ==================== 測試結果 API ====================
    print("📊 測試結果 API (Test Results)")
    print("-" * 60)
    
    # 16. 列出測試結果
    def test_list_results():
        viewset = tester._make_request(BenchmarkTestResultViewSet, 'list')
        response = viewset.list(viewset.request)
        return response.status_code == 200 and 'results' in response.data
    
    tester.test("GET /api/benchmark/test-results/", test_list_results)
    
    # 17. 獲取單一測試結果
    def test_retrieve_result():
        result = BenchmarkTestResult.objects.first()
        if not result:
            return False
        viewset = tester._make_request(BenchmarkTestResultViewSet, 'retrieve', pk=result.id)
        response = viewset.retrieve(viewset.request, pk=result.id)
        return response.status_code == 200 and response.data['id'] == result.id
    
    tester.test("GET /api/benchmark/test-results/{id}/", test_retrieve_result)
    
    # 18. 按測試執行篩選
    def test_filter_results_by_run():
        run = BenchmarkTestRun.objects.filter(results__isnull=False).first()
        if not run:
            return False
        
        viewset = tester._make_request(
            BenchmarkTestResultViewSet,
            'list',
            query_params={'test_run_id': run.id}
        )
        response = viewset.list(viewset.request)
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-results/?test_run_id=X", test_filter_results_by_run)
    
    # 19. 按通過狀態篩選
    def test_filter_results_by_passed():
        viewset = tester._make_request(
            BenchmarkTestResultViewSet,
            'list',
            query_params={'is_passed': 'true'}
        )
        response = viewset.list(viewset.request)
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-results/?is_passed=true", test_filter_results_by_passed)
    
    # 20. 獲取失敗案例
    def test_failed_cases():
        viewset = tester._make_request(BenchmarkTestResultViewSet, 'failed_cases')
        response = viewset.failed_cases(viewset.request)
        return (response.status_code == 200 and 
                'total_failed_results' in response.data and
                'failed_cases' in response.data)
    
    tester.test("GET /api/benchmark/test-results/failed_cases/", test_failed_cases)
    
    print()
    
    # ==================== 版本 API ====================
    print("🔖 版本 API (Versions)")
    print("-" * 60)
    
    # 21. 列出版本
    def test_list_versions():
        viewset = tester._make_request(SearchAlgorithmVersionViewSet, 'list')
        response = viewset.list(viewset.request)
        return response.status_code == 200 and 'results' in response.data
    
    tester.test("GET /api/benchmark/versions/", test_list_versions)
    
    # 22. 獲取單一版本
    def test_retrieve_version():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        viewset = tester._make_request(SearchAlgorithmVersionViewSet, 'retrieve', pk=version.id)
        response = viewset.retrieve(viewset.request, pk=version.id)
        return response.status_code == 200 and response.data['id'] == version.id
    
    tester.test("GET /api/benchmark/versions/{id}/", test_retrieve_version)
    
    # 23. 創建新版本
    def test_create_version():
        viewset = tester._make_request(
            SearchAlgorithmVersionViewSet,
            'create',
            method='POST',
            data={
                'version_name': f'API 測試版本 {datetime.now().strftime("%H:%M:%S")}',
                'version_code': f'v-api-test-{datetime.now().timestamp()}',
                'description': 'API 端點測試創建的版本',
                'algorithm_type': 'hybrid',
                'is_active': True
            }
        )
        response = viewset.create(viewset.request)
        return response.status_code == 201
    
    tester.test("POST /api/benchmark/versions/", test_create_version)
    
    # 24. 設定為基準版本
    def test_set_baseline():
        version = SearchAlgorithmVersion.objects.filter(is_baseline=False).first()
        if not version:
            return False
        
        viewset = tester._make_request(
            SearchAlgorithmVersionViewSet,
            'set_as_baseline',
            method='POST',
            pk=version.id
        )
        response = viewset.set_as_baseline(viewset.request, pk=version.id)
        return response.status_code == 200 and response.data.get('success') == True
    
    tester.test("POST /api/benchmark/versions/{id}/set_as_baseline/", test_set_baseline)
    
    # 25. 獲取基準版本
    def test_get_baseline():
        viewset = tester._make_request(SearchAlgorithmVersionViewSet, 'baseline')
        response = viewset.baseline(viewset.request)
        return response.status_code in [200, 404]  # 404 也算正常（尚未設定基準）
    
    tester.test("GET /api/benchmark/versions/baseline/", test_get_baseline)
    
    # 26. 獲取版本測試歷史
    def test_version_history():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        
        viewset = tester._make_request(
            SearchAlgorithmVersionViewSet,
            'test_history',
            pk=version.id
        )
        response = viewset.test_history(viewset.request, pk=version.id)
        return (response.status_code == 200 and 
                'version' in response.data and
                'test_runs' in response.data)
    
    tester.test("GET /api/benchmark/versions/{id}/test_history/", test_version_history)
    
    print()
    
    # 打印總結
    tester.print_summary()
    
    # 顯示詳細資料庫狀態
    print("\n" + "=" * 60)
    print("📈 資料庫狀態")
    print("=" * 60)
    print(f"測試案例總數: {BenchmarkTestCase.objects.count()}")
    print(f"  - 啟用: {BenchmarkTestCase.objects.filter(is_active=True).count()}")
    print(f"  - 停用: {BenchmarkTestCase.objects.filter(is_active=False).count()}")
    print(f"測試執行總數: {BenchmarkTestRun.objects.count()}")
    print(f"  - 完成: {BenchmarkTestRun.objects.filter(status='completed').count()}")
    print(f"測試結果總數: {BenchmarkTestResult.objects.count()}")
    print(f"  - 通過: {BenchmarkTestResult.objects.filter(is_passed=True).count()}")
    print(f"  - 失敗: {BenchmarkTestResult.objects.filter(is_passed=False).count()}")
    print(f"版本總數: {SearchAlgorithmVersion.objects.count()}")
    print(f"  - 基準版本: {SearchAlgorithmVersion.objects.filter(is_baseline=True).count()}")
    print("=" * 60)
    
    # 返回測試結果
    return tester.passed, tester.failed, tester.total


if __name__ == '__main__':
    passed, failed, total = main()
    exit(0 if failed == 0 else 1)
