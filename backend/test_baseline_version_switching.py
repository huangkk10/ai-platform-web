#!/usr/bin/env python3
"""
測試動態 Baseline 版本切換功能
========================================

測試目標：
1. 驗證 get_baseline_version_code() 正確讀取資料庫的 is_baseline=True 版本
2. 驗證緩存機制正常工作
3. 驗證 clear_baseline_version_cache() 清除緩存
4. 驗證 VSA set_baseline API 切換版本後，Dify API 使用新版本

測試場景：
- 場景 1：初始狀態（v1.2.1 是 Baseline）
- 場景 2：切換到 v1.1.1
- 場景 3：再切換回 v1.2.1
- 場景 4：模擬 Dify API 調用

Created: 2025-11-26
Author: AI Platform Team
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

import json
import requests
from django.test import RequestFactory
from api.models import DifyConfigVersion
from api.views.dify_knowledge_views import (
    get_baseline_version_code,
    clear_baseline_version_cache,
    _baseline_version_cache
)


class Colors:
    """終端顏色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_section(title):
    """打印章節標題"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(message):
    """打印成功訊息"""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")


def print_error(message):
    """打印錯誤訊息"""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")


def print_info(message):
    """打印資訊訊息"""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def print_warning(message):
    """打印警告訊息"""
    print(f"{Colors.WARNING}⚠️  {message}{Colors.ENDC}")


def get_current_baseline():
    """獲取當前 Baseline 版本"""
    try:
        baseline = DifyConfigVersion.objects.filter(
            is_baseline=True,
            is_active=True
        ).first()
        return baseline.version_code if baseline else None
    except Exception as e:
        print_error(f"獲取 Baseline 失敗: {str(e)}")
        return None


def set_baseline_in_db(version_code):
    """在資料庫中設置 Baseline（不透過 API）"""
    try:
        # 清除所有 Baseline
        DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
        
        # 設置新 Baseline
        version = DifyConfigVersion.objects.get(
            version_code=version_code,
            is_active=True
        )
        version.is_baseline = True
        version.save()
        
        print_success(f"資料庫中設置 Baseline: {version_code}")
        return True
    except DifyConfigVersion.DoesNotExist:
        print_error(f"版本不存在: {version_code}")
        return False
    except Exception as e:
        print_error(f"設置 Baseline 失敗: {str(e)}")
        return False


def test_baseline_version_function():
    """測試 1：get_baseline_version_code() 函數"""
    print_section("測試 1：get_baseline_version_code() 函數")
    
    # 獲取當前資料庫中的 Baseline
    db_baseline = get_current_baseline()
    print_info(f"資料庫中的 Baseline 版本: {db_baseline}")
    
    # 清除緩存
    clear_baseline_version_cache()
    print_info("緩存已清除")
    
    # 調用函數
    function_result = get_baseline_version_code()
    print_info(f"函數返回的版本: {function_result}")
    
    # 驗證結果
    if function_result == db_baseline:
        print_success("測試通過：函數返回版本與資料庫一致")
        return True
    else:
        print_error(f"測試失敗：函數返回 {function_result}，資料庫是 {db_baseline}")
        return False


def test_cache_mechanism():
    """測試 2：緩存機制"""
    print_section("測試 2：緩存機制")
    
    # 清除緩存
    clear_baseline_version_cache()
    print_info("緩存已清除")
    print_info(f"緩存狀態: {_baseline_version_cache}")
    
    # 第一次調用（應該查詢資料庫）
    print_info("\n第一次調用 get_baseline_version_code()...")
    result1 = get_baseline_version_code()
    print_info(f"返回版本: {result1}")
    print_info(f"緩存狀態: {_baseline_version_cache}")
    
    # 第二次調用（應該使用緩存）
    print_info("\n第二次調用 get_baseline_version_code()...")
    result2 = get_baseline_version_code()
    print_info(f"返回版本: {result2}")
    print_info(f"緩存狀態: {_baseline_version_cache}")
    
    # 驗證結果
    if result1 == result2 and _baseline_version_cache['version_code'] == result1:
        print_success("測試通過：緩存機制正常工作")
        return True
    else:
        print_error("測試失敗：緩存機制異常")
        return False


def test_cache_clearing():
    """測試 3：緩存清除"""
    print_section("測試 3：緩存清除")
    
    # 確保緩存有值
    get_baseline_version_code()
    print_info(f"調用前緩存狀態: {_baseline_version_cache}")
    
    # 清除緩存
    clear_baseline_version_cache()
    print_info("調用 clear_baseline_version_cache()")
    print_info(f"調用後緩存狀態: {_baseline_version_cache}")
    
    # 驗證結果
    if _baseline_version_cache['version_code'] is None:
        print_success("測試通過：緩存已清除")
        return True
    else:
        print_error("測試失敗：緩存未清除")
        return False


def test_version_switching():
    """測試 4：版本切換（完整流程）"""
    print_section("測試 4：版本切換完整流程")
    
    # 記錄原始 Baseline
    original_baseline = get_current_baseline()
    print_info(f"原始 Baseline: {original_baseline}")
    
    # 確定測試版本
    test_versions = ['dify-two-tier-v1.1.1', 'dify-two-tier-v1.2.1']
    if original_baseline == test_versions[0]:
        test_versions.reverse()  # 如果當前是 v1.1.1，先切到 v1.2.1
    
    print_info(f"測試切換順序: {test_versions[0]} → {test_versions[1]}")
    
    results = []
    
    for target_version in test_versions:
        print(f"\n{Colors.BOLD}--- 切換到 {target_version} ---{Colors.ENDC}")
        
        # 步驟 1：設置資料庫
        if not set_baseline_in_db(target_version):
            print_error(f"無法設置 {target_version}")
            results.append(False)
            continue
        
        # 步驟 2：清除緩存（模擬 VSA API 的行為）
        clear_baseline_version_cache()
        print_info("緩存已清除（模擬 VSA API）")
        
        # 步驟 3：調用函數（模擬 Dify API 的行為）
        function_result = get_baseline_version_code()
        print_info(f"函數返回版本: {function_result}")
        
        # 步驟 4：驗證
        if function_result == target_version:
            print_success(f"✅ 切換成功：{target_version}")
            results.append(True)
        else:
            print_error(f"❌ 切換失敗：期望 {target_version}，實際 {function_result}")
            results.append(False)
    
    # 恢復原始 Baseline
    if original_baseline:
        print(f"\n{Colors.BOLD}--- 恢復原始 Baseline ---{Colors.ENDC}")
        set_baseline_in_db(original_baseline)
        clear_baseline_version_cache()
        print_info(f"已恢復到: {original_baseline}")
    
    # 驗證整體結果
    if all(results):
        print_success("測試通過：版本切換流程正常")
        return True
    else:
        print_error("測試失敗：版本切換流程異常")
        return False


def test_dify_api_integration():
    """測試 5：模擬 Dify API 調用"""
    print_section("測試 5：模擬 Dify API 調用")
    
    try:
        from api.views.dify_knowledge_views import dify_knowledge_search
        from django.test import RequestFactory
        
        # 記錄當前 Baseline
        current_baseline = get_current_baseline()
        print_info(f"當前 Baseline: {current_baseline}")
        
        # 清除緩存
        clear_baseline_version_cache()
        
        # 創建模擬請求
        factory = RequestFactory()
        request_data = {
            "knowledge_id": "protocol_guide_db",
            "query": "test query",
            "retrieval_setting": {
                "top_k": 3,
                "score_threshold": 0.7
            },
            "inputs": {}  # 不提供 version_code，應該使用 Baseline
        }
        
        request = factory.post(
            '/api/dify/knowledge/retrieval/',
            data=json.dumps(request_data),
            content_type='application/json'
        )
        
        print_info("發送模擬請求...")
        print_info(f"請求數據: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
        
        # 調用 API
        response = dify_knowledge_search(request)
        
        print_info(f"回應狀態碼: {response.status_code}")
        
        # 檢查日誌輸出（需要手動查看）
        print_warning("請查看 Django 日誌，確認是否有以下訊息：")
        print_warning(f"  '🎯 使用 Baseline 版本: {current_baseline}'")
        print_warning(f"  '✅ 載入版本配置: {current_baseline}'")
        
        if response.status_code == 200:
            print_success("測試通過：API 調用成功")
            return True
        else:
            print_error(f"測試失敗：API 返回狀態碼 {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"測試失敗：{str(e)}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """執行所有測試"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'#'*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}#  動態 Baseline 版本切換功能測試{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'#'*60}{Colors.ENDC}")
    
    tests = [
        ("Baseline 版本讀取", test_baseline_version_function),
        ("緩存機制", test_cache_mechanism),
        ("緩存清除", test_cache_clearing),
        ("版本切換流程", test_version_switching),
        ("Dify API 整合", test_dify_api_integration),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print_error(f"{test_name} 測試異常: {str(e)}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # 總結
    print_section("測試總結")
    
    passed = sum(1 for r in results.values() if r)
    total = len(results)
    
    for test_name, result in results.items():
        if result:
            print_success(f"{test_name}: 通過")
        else:
            print_error(f"{test_name}: 失敗")
    
    print(f"\n{Colors.BOLD}總計: {passed}/{total} 測試通過{Colors.ENDC}")
    
    if passed == total:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}🎉 所有測試通過！{Colors.ENDC}")
        return True
    else:
        print(f"\n{Colors.FAIL}{Colors.BOLD}❌ 部分測試失敗{Colors.ENDC}")
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
