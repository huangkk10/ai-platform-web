#!/usr/bin/env python
"""
Benchmark API 端點測試（使用 Django Test Client）

測試所有 26 個 API 端點
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from datetime import datetime
import json

User = get_user_model()


class BenchmarkAPITester:
    """Benchmark API 測試器"""
    
    def __init__(self):
        self.client = Client()
        self.user = self._get_or_create_test_user()
        self.client.force_login(self.user)
        self.passed = 0
        self.failed = 0
        self.total = 0
        
    def _get_or_create_test_user(self):
        """獲取或創建測試用戶"""
        user, created = User.objects.get_or_create(
            username='test_api_user',
            defaults={
                'email': 'testapi@example.com',
                'is_staff': True,
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        return user
    
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
    from api.models import (
        BenchmarkTestCase,
        BenchmarkTestRun,
        BenchmarkTestResult,
        SearchAlgorithmVersion
    )
    
    tester = BenchmarkAPITester()
    
    print("=" * 60)
    print("🧪 Benchmark API 端點測試（真實 HTTP 請求）")
    print("=" * 60)
    print()
    
    # ==================== 測試案例 API ====================
    print("📋 測試案例 API (Test Cases)")
    print("-" * 60)
    
    # 1. 列出測試案例
    def test_list_cases():
        response = tester.client.get('/api/benchmark/test-cases/')
        return response.status_code == 200 and 'results' in response.json()
    
    tester.test("GET /api/benchmark/test-cases/", test_list_cases)
    
    # 2. 獲取單一測試案例
    def test_retrieve_case():
        case = BenchmarkTestCase.objects.first()
        if not case:
            return False
        response = tester.client.get(f'/api/benchmark/test-cases/{case.id}/')
        return response.status_code == 200 and response.json()['id'] == case.id
    
    tester.test("GET /api/benchmark/test-cases/{id}/", test_retrieve_case)
    
    # 3. 測試統計 API
    def test_statistics():
        response = tester.client.get('/api/benchmark/test-cases/statistics/')
        data = response.json()
        return (response.status_code == 200 and 
                'total_count' in data and
                'by_category' in data)
    
    tester.test("GET /api/benchmark/test-cases/statistics/", test_statistics)
    
    # 4. 測試類別篩選
    def test_filter_by_category():
        response = tester.client.get('/api/benchmark/test-cases/?category=資源路徑')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-cases/?category=資源路徑", test_filter_by_category)
    
    # 5. 測試難度篩選
    def test_filter_by_difficulty():
        response = tester.client.get('/api/benchmark/test-cases/?difficulty=easy')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-cases/?difficulty=easy", test_filter_by_difficulty)
    
    # 6. 創建測試案例
    def test_create_case():
        data = {
            'question': f'API 測試問題 {datetime.now().strftime("%H:%M:%S")}',
            'category': 'API測試',
            'difficulty_level': 'easy',
            'question_type': '測試',
            'knowledge_source': 'API',
            'expected_document_ids': [1, 2],
            'min_required_matches': 1,
            'is_active': True
        }
        response = tester.client.post(
            '/api/benchmark/test-cases/',
            data=json.dumps(data),
            content_type='application/json'
        )
        return response.status_code == 201
    
    tester.test("POST /api/benchmark/test-cases/", test_create_case)
    
    # 7. 批量啟用
    def test_bulk_activate():
        # 先停用一些案例
        BenchmarkTestCase.objects.filter(id__in=[1, 2, 3]).update(is_active=False)
        
        response = tester.client.post(
            '/api/benchmark/test-cases/bulk_activate/',
            data=json.dumps({'ids': [1, 2, 3]}),
            content_type='application/json'
        )
        return response.status_code == 200 and response.json().get('success') == True
    
    tester.test("POST /api/benchmark/test-cases/bulk_activate/", test_bulk_activate)
    
    # 8. 批量停用
    def test_bulk_deactivate():
        response = tester.client.post(
            '/api/benchmark/test-cases/bulk_deactivate/',
            data=json.dumps({'ids': [4, 5]}),
            content_type='application/json'
        )
        return response.status_code == 200 and response.json().get('success') == True
    
    tester.test("POST /api/benchmark/test-cases/bulk_deactivate/", test_bulk_deactivate)
    
    print()
    
    # ==================== 測試執行 API ====================
    print("🚀 測試執行 API (Test Runs)")
    print("-" * 60)
    
    # 9. 列出測試執行
    def test_list_runs():
        response = tester.client.get('/api/benchmark/test-runs/')
        return response.status_code == 200 and 'results' in response.json()
    
    tester.test("GET /api/benchmark/test-runs/", test_list_runs)
    
    # 10. 獲取單一測試執行
    def test_retrieve_run():
        run = BenchmarkTestRun.objects.first()
        if not run:
            return False
        response = tester.client.get(f'/api/benchmark/test-runs/{run.id}/')
        return response.status_code == 200 and response.json()['id'] == run.id
    
    tester.test("GET /api/benchmark/test-runs/{id}/", test_retrieve_run)
    
    # 11. 測試版本篩選
    def test_filter_by_version():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        response = tester.client.get(f'/api/benchmark/test-runs/?version_id={version.id}')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-runs/?version_id=X", test_filter_by_version)
    
    # 12. 測試狀態篩選
    def test_filter_by_status():
        response = tester.client.get('/api/benchmark/test-runs/?status=completed')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-runs/?status=completed", test_filter_by_status)
    
    # 13. 獲取測試結果
    def test_get_results():
        run = BenchmarkTestRun.objects.filter(results__isnull=False).first()
        if not run:
            return False
        response = tester.client.get(f'/api/benchmark/test-runs/{run.id}/results/')
        return response.status_code == 200 and isinstance(response.json(), list)
    
    tester.test("GET /api/benchmark/test-runs/{id}/results/", test_get_results)
    
    # 14. 啟動新測試（簡化版，只測 3 題）
    def test_start_test():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        
        # 確保有啟用的測試案例
        BenchmarkTestCase.objects.filter(id__in=[1, 2, 3]).update(is_active=True)
        
        data = {
            'version_id': version.id,
            'run_name': f'API 測試 - {datetime.now().strftime("%H:%M:%S")}',
            'run_type': 'manual',
            'limit': 3,
            'notes': 'API 端點測試'
        }
        response = tester.client.post(
            '/api/benchmark/test-runs/start_test/',
            data=json.dumps(data),
            content_type='application/json'
        )
        return response.status_code == 201 and response.json().get('success') == True
    
    tester.test("POST /api/benchmark/test-runs/start_test/", test_start_test)
    
    # 15. 比較測試執行
    def test_compare_runs():
        runs = list(BenchmarkTestRun.objects.filter(status='completed')[:2])
        if len(runs) < 2:
            return False
        
        data = {
            'run_id_1': runs[0].id,
            'run_id_2': runs[1].id
        }
        response = tester.client.post(
            '/api/benchmark/test-runs/compare/',
            data=json.dumps(data),
            content_type='application/json'
        )
        result = response.json()
        return (response.status_code == 200 and 
                'run_1' in result and
                'run_2' in result and
                'delta' in result)
    
    tester.test("POST /api/benchmark/test-runs/compare/", test_compare_runs)
    
    print()
    
    # ==================== 測試結果 API ====================
    print("📊 測試結果 API (Test Results)")
    print("-" * 60)
    
    # 16. 列出測試結果
    def test_list_results():
        response = tester.client.get('/api/benchmark/test-results/')
        return response.status_code == 200 and 'results' in response.json()
    
    tester.test("GET /api/benchmark/test-results/", test_list_results)
    
    # 17. 獲取單一測試結果
    def test_retrieve_result():
        result = BenchmarkTestResult.objects.first()
        if not result:
            return False
        response = tester.client.get(f'/api/benchmark/test-results/{result.id}/')
        return response.status_code == 200 and response.json()['id'] == result.id
    
    tester.test("GET /api/benchmark/test-results/{id}/", test_retrieve_result)
    
    # 18. 按測試執行篩選
    def test_filter_results_by_run():
        run = BenchmarkTestRun.objects.filter(results__isnull=False).first()
        if not run:
            return False
        response = tester.client.get(f'/api/benchmark/test-results/?test_run_id={run.id}')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-results/?test_run_id=X", test_filter_results_by_run)
    
    # 19. 按通過狀態篩選
    def test_filter_results_by_passed():
        response = tester.client.get('/api/benchmark/test-results/?is_passed=true')
        return response.status_code == 200
    
    tester.test("GET /api/benchmark/test-results/?is_passed=true", test_filter_results_by_passed)
    
    # 20. 獲取失敗案例
    def test_failed_cases():
        response = tester.client.get('/api/benchmark/test-results/failed_cases/')
        data = response.json()
        return (response.status_code == 200 and 
                'total_failed_results' in data and
                'failed_cases' in data)
    
    tester.test("GET /api/benchmark/test-results/failed_cases/", test_failed_cases)
    
    print()
    
    # ==================== 版本 API ====================
    print("🔖 版本 API (Versions)")
    print("-" * 60)
    
    # 21. 列出版本
    def test_list_versions():
        response = tester.client.get('/api/benchmark/versions/')
        return response.status_code == 200 and 'results' in response.json()
    
    tester.test("GET /api/benchmark/versions/", test_list_versions)
    
    # 22. 獲取單一版本
    def test_retrieve_version():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        response = tester.client.get(f'/api/benchmark/versions/{version.id}/')
        return response.status_code == 200 and response.json()['id'] == version.id
    
    tester.test("GET /api/benchmark/versions/{id}/", test_retrieve_version)
    
    # 23. 創建新版本
    def test_create_version():
        data = {
            'version_name': f'API 測試版本 {datetime.now().strftime("%H:%M:%S")}',
            'version_code': f'v-api-test-{int(datetime.now().timestamp())}',
            'description': 'API 端點測試創建的版本',
            'algorithm_type': 'hybrid',
            'is_active': True
        }
        response = tester.client.post(
            '/api/benchmark/versions/',
            data=json.dumps(data),
            content_type='application/json'
        )
        return response.status_code == 201
    
    tester.test("POST /api/benchmark/versions/", test_create_version)
    
    # 24. 設定為基準版本
    def test_set_baseline():
        version = SearchAlgorithmVersion.objects.filter(is_baseline=False).first()
        if not version:
            # 創建一個新版本
            version = SearchAlgorithmVersion.objects.create(
                version_name='Baseline Test',
                version_code='v-baseline-test',
                algorithm_type='hybrid'
            )
        
        response = tester.client.post(f'/api/benchmark/versions/{version.id}/set_as_baseline/')
        return response.status_code == 200 and response.json().get('success') == True
    
    tester.test("POST /api/benchmark/versions/{id}/set_as_baseline/", test_set_baseline)
    
    # 25. 獲取基準版本
    def test_get_baseline():
        response = tester.client.get('/api/benchmark/versions/baseline/')
        return response.status_code in [200, 404]  # 404 也算正常
    
    tester.test("GET /api/benchmark/versions/baseline/", test_get_baseline)
    
    # 26. 獲取版本測試歷史
    def test_version_history():
        version = SearchAlgorithmVersion.objects.first()
        if not version:
            return False
        response = tester.client.get(f'/api/benchmark/versions/{version.id}/test_history/')
        data = response.json()
        return (response.status_code == 200 and 
                'version' in data and
                'test_runs' in data)
    
    tester.test("GET /api/benchmark/versions/{id}/test_history/", test_version_history)
    
    print()
    
    # 打印總結
    tester.print_summary()
    
    # 顯示資料庫狀態
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
    
    return tester.passed, tester.failed, tester.total


if __name__ == '__main__':
    passed, failed, total = main()
    exit(0 if failed == 0 else 1)
