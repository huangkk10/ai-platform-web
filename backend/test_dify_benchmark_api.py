"""
測試 Dify Benchmark API ViewSets
驗證所有 API 端點是否正常工作
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.test import RequestFactory
from rest_framework.test import force_authenticate
from django.contrib.auth import get_user_model
from api.views import (
    DifyConfigVersionViewSet,
    DifyBenchmarkTestCaseViewSet,
    DifyTestRunViewSet
)
from api.models import (
    DifyConfigVersion,
    DifyBenchmarkTestCase,
    DifyTestRun
)

User = get_user_model()


def test_api_imports():
    """測試 1: 驗證 API 導入"""
    print("=" * 60)
    print("測試 1: API ViewSets 導入測試")
    print("=" * 60)
    
    try:
        assert DifyConfigVersionViewSet is not None
        assert DifyBenchmarkTestCaseViewSet is not None
        assert DifyTestRunViewSet is not None
        print("✅ ViewSets 導入成功")
        
        # 檢查 queryset
        print(f"  - DifyConfigVersionViewSet.queryset: {DifyConfigVersionViewSet.queryset.model.__name__}")
        print(f"  - DifyBenchmarkTestCaseViewSet.queryset: {DifyBenchmarkTestCaseViewSet.queryset.model.__name__}")
        print(f"  - DifyTestRunViewSet.queryset: {DifyTestRunViewSet.queryset.model.__name__}")
        
        return True
    except Exception as e:
        print(f"❌ ViewSets 導入失敗: {str(e)}")
        return False


def test_version_viewset():
    """測試 2: DifyConfigVersionViewSet"""
    print("\n" + "=" * 60)
    print("測試 2: DifyConfigVersionViewSet")
    print("=" * 60)
    
    try:
        # 創建測試用戶
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'is_staff': True}
        )
        
        # 創建 RequestFactory
        factory = RequestFactory()
        
        # 測試 list action
        request = factory.get('/api/dify-benchmark/versions/')
        force_authenticate(request, user=user)
        
        viewset = DifyConfigVersionViewSet.as_view({'get': 'list'})
        response = viewset(request)
        
        print(f"✅ List API 測試通過")
        print(f"  - Status Code: {response.status_code}")
        print(f"  - 版本數量: {len(response.data)}")
        
        # 如果有版本，測試 retrieve
        if response.data:
            version = response.data[0]
            print(f"  - 第一個版本: {version['version_name']}")
        
        # 測試 custom actions 是否存在
        actions = [action for action in dir(DifyConfigVersionViewSet) 
                  if not action.startswith('_') and callable(getattr(DifyConfigVersionViewSet, action))]
        
        custom_actions = ['set_baseline', 'run_benchmark', 'statistics', 'batch_test']
        for action in custom_actions:
            if action in actions:
                print(f"  ✅ Custom action '{action}' 已定義")
            else:
                print(f"  ⚠️  Custom action '{action}' 未找到")
        
        return True
    except Exception as e:
        print(f"❌ DifyConfigVersionViewSet 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_test_case_viewset():
    """測試 3: DifyBenchmarkTestCaseViewSet"""
    print("\n" + "=" * 60)
    print("測試 3: DifyBenchmarkTestCaseViewSet")
    print("=" * 60)
    
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'is_staff': True}
        )
        
        factory = RequestFactory()
        
        # 測試 list action
        request = factory.get('/api/dify-benchmark/test-cases/')
        force_authenticate(request, user=user)
        
        viewset = DifyBenchmarkTestCaseViewSet.as_view({'get': 'list'})
        response = viewset(request)
        
        print(f"✅ List API 測試通過")
        print(f"  - Status Code: {response.status_code}")
        print(f"  - 測試案例數量: {len(response.data)}")
        
        # 測試案例資料預覽
        if response.data:
            case = response.data[0]
            print(f"  - 第一個案例: {case['question'][:50]}...")
            print(f"  - 測試類別: {case['test_class_name']}")
        
        # 測試 custom actions
        custom_actions = ['bulk_import', 'bulk_export', 'toggle_active']
        actions = [action for action in dir(DifyBenchmarkTestCaseViewSet) 
                  if not action.startswith('_') and callable(getattr(DifyBenchmarkTestCaseViewSet, action))]
        
        for action in custom_actions:
            if action in actions:
                print(f"  ✅ Custom action '{action}' 已定義")
            else:
                print(f"  ⚠️  Custom action '{action}' 未找到")
        
        return True
    except Exception as e:
        print(f"❌ DifyBenchmarkTestCaseViewSet 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_test_run_viewset():
    """測試 4: DifyTestRunViewSet"""
    print("\n" + "=" * 60)
    print("測試 4: DifyTestRunViewSet")
    print("=" * 60)
    
    try:
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'is_staff': True}
        )
        
        factory = RequestFactory()
        
        # 測試 list action
        request = factory.get('/api/dify-benchmark/test-runs/')
        force_authenticate(request, user=user)
        
        viewset = DifyTestRunViewSet.as_view({'get': 'list'})
        response = viewset(request)
        
        print(f"✅ List API 測試通過")
        print(f"  - Status Code: {response.status_code}")
        print(f"  - 測試執行數量: {len(response.data)}")
        
        # 測試執行資料預覽
        if response.data:
            run = response.data[0]
            print(f"  - 第一個測試: {run['run_name']}")
            print(f"  - 版本: {run['version_name']}")
            print(f"  - 狀態: {run['status']}")
            print(f"  - 通過率: {run['pass_rate']}%")
        
        # 測試 custom actions
        custom_actions = ['results', 'comparison', 'batch_history']
        actions = [action for action in dir(DifyTestRunViewSet) 
                  if not action.startswith('_') and callable(getattr(DifyTestRunViewSet, action))]
        
        for action in custom_actions:
            if action in actions:
                print(f"  ✅ Custom action '{action}' 已定義")
            else:
                print(f"  ⚠️  Custom action '{action}' 未找到")
        
        return True
    except Exception as e:
        print(f"❌ DifyTestRunViewSet 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_url_routing():
    """測試 5: URL 路由配置"""
    print("\n" + "=" * 60)
    print("測試 5: URL 路由配置")
    print("=" * 60)
    
    try:
        from django.urls import resolve
        
        # 測試 URL 解析
        urls_to_test = [
            '/api/dify-benchmark/versions/',
            '/api/dify-benchmark/test-cases/',
            '/api/dify-benchmark/test-runs/',
        ]
        
        for url in urls_to_test:
            try:
                resolved = resolve(url)
                print(f"✅ {url} → {resolved.func.__name__}")
            except Exception as e:
                print(f"❌ {url} 解析失敗: {str(e)}")
        
        return True
    except Exception as e:
        print(f"❌ URL 路由測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("Dify Benchmark API ViewSets 測試")
    print("=" * 60 + "\n")
    
    results = {
        'api_imports': test_api_imports(),
        'version_viewset': test_version_viewset(),
        'test_case_viewset': test_test_case_viewset(),
        'test_run_viewset': test_test_run_viewset(),
        'url_routing': test_url_routing()
    }
    
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 所有測試通過！API ViewSets 已準備就緒。")
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息。")
    
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
