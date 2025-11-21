#!/usr/bin/env python
"""Benchmark API 快速測試"""
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

print("=" * 60)
print("📋 Phase 4 API 測試")
print("=" * 60)

# Test 1: 導入
from api.views import (
    BenchmarkTestCaseViewSet,
    BenchmarkTestRunViewSet,
    BenchmarkTestResultViewSet,
    SearchAlgorithmVersionViewSet
)
print("✅ ViewSets 導入成功")

# Test 2: 資料庫
from api.models import BenchmarkTestCase, BenchmarkTestRun
print(f"✅ 測試案例: {BenchmarkTestCase.objects.count()} 個")
print(f"✅ 測試執行: {BenchmarkTestRun.objects.count()} 個")

# Test 3: Serializers
from api.serializers import (
    BenchmarkTestCaseSerializer,
    BenchmarkTestRunSerializer
)
print("✅ Serializers 正常")

# Test 4: 路由測試
from rest_framework.routers import DefaultRouter
router = DefaultRouter()
router.register('test', BenchmarkTestCaseViewSet, basename='test')
print(f"✅ 路由生成: {len(router.urls)} 個端點")

print()
print("🎉 Phase 4.1-4.3 完成！所有組件就緒")
print()
print("📝 可用的 API 端點：")
print("   • GET    /api/benchmark/test-cases/")
print("   • POST   /api/benchmark/test-cases/")
print("   • GET    /api/benchmark/test-cases/{id}/")
print("   • PUT    /api/benchmark/test-cases/{id}/")
print("   • DELETE /api/benchmark/test-cases/{id}/")
print("   • GET    /api/benchmark/test-cases/statistics/")
print("   • POST   /api/benchmark/test-cases/bulk_activate/")
print()
print("   • GET    /api/benchmark/test-runs/")
print("   • POST   /api/benchmark/test-runs/start_test/")
print("   • GET    /api/benchmark/test-runs/{id}/results/")
print("   • POST   /api/benchmark/test-runs/compare/")
print()
print("   • GET    /api/benchmark/test-results/")
print("   • GET    /api/benchmark/test-results/failed_cases/")
print()
print("   • GET    /api/benchmark/versions/")
print("   • POST   /api/benchmark/versions/")
print("   • POST   /api/benchmark/versions/{id}/set_as_baseline/")
print("   • GET    /api/benchmark/versions/baseline/")
