#!/usr/bin/env python
"""
智能搜尋路由器測試腳本

測試兩種搜尋模式：
- 模式 A：關鍵字優先全文搜尋（含全文關鍵字）
- 模式 B：標準兩階段搜尋（無全文關鍵字）

使用方式：
    docker exec ai-django python /app/library/protocol_guide/test_smart_router.py

Author: AI Platform Team
Date: 2025-11-11
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.smart_search_router import SmartSearchRouter


def test_keyword_detection():
    """測試關鍵字檢測與路由決策"""
    print("\n" + "=" * 60)
    print("測試 1: 關鍵字檢測與路由決策")
    print("=" * 60)
    
    router = SmartSearchRouter()
    
    test_cases = [
        # 應該路由到模式 A（含全文關鍵字）
        ("Cup顏色完整內容是什麼？", "mode_a"),
        ("請給我 UNH-IOL 測試的全文說明", "mode_a"),
        ("所有步驟怎麼做？", "mode_a"),
        ("詳細流程是什麼？", "mode_a"),
        ("What's the complete procedure?", "mode_a"),
        
        # 應該路由到模式 B（無全文關鍵字）
        ("Cup顏色是什麼？", "mode_b"),
        ("UNH-IOL 測試要怎麼做？", "mode_b"),
        ("如何測試 USB？", "mode_b"),
        ("Protocol 有哪些分類？", "mode_b"),
    ]
    
    passed = 0
    failed = 0
    
    for query, expected_mode in test_cases:
        actual_mode = router.route_search_strategy(query)
        
        if actual_mode == expected_mode:
            print(f"✅ '{query[:40]}...' → {actual_mode}")
            passed += 1
        else:
            print(f"❌ '{query[:40]}...' → {actual_mode} (期望: {expected_mode})")
            failed += 1
    
    print(f"\n測試結果: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_mode_a_flow():
    """測試模式 A 流程（不實際請求 Dify）"""
    print("\n" + "=" * 60)
    print("測試 2: 模式 A 流程檢查")
    print("=" * 60)
    
    from library.protocol_guide.keyword_triggered_handler import KeywordTriggeredSearchHandler
    
    handler = KeywordTriggeredSearchHandler()
    
    # 檢查方法是否存在
    required_methods = [
        '_full_document_search',
        '_format_search_context',
        '_request_dify_chat',
        'handle_keyword_triggered_search'
    ]
    
    print("檢查必要方法...")
    for method_name in required_methods:
        if hasattr(handler, method_name):
            print(f"✅ {method_name} 存在")
        else:
            print(f"❌ {method_name} 缺失")
            return False
    
    print("\n✅ 模式 A 處理器結構正確")
    return True


def test_mode_b_flow():
    """測試模式 B 流程（不實際請求 Dify）"""
    print("\n" + "=" * 60)
    print("測試 3: 模式 B 流程檢查")
    print("=" * 60)
    
    from library.protocol_guide.two_tier_handler import TwoTierSearchHandler
    
    handler = TwoTierSearchHandler()
    
    # 檢查方法是否存在
    required_methods = [
        '_section_search',
        '_full_document_search',
        '_format_search_context',
        '_request_dify_chat',
        'handle_two_tier_search'
    ]
    
    print("檢查必要方法...")
    for method_name in required_methods:
        if hasattr(handler, method_name):
            print(f"✅ {method_name} 存在")
        else:
            print(f"❌ {method_name} 缺失")
            return False
    
    print("\n✅ 模式 B 處理器結構正確")
    return True


def test_search_service_methods():
    """測試搜尋服務方法"""
    print("\n" + "=" * 60)
    print("測試 4: 搜尋服務方法檢查")
    print("=" * 60)
    
    from library.protocol_guide.search_service import ProtocolGuideSearchService
    
    service = ProtocolGuideSearchService()
    
    # 檢查方法是否存在
    required_methods = [
        'section_search',
        'full_document_search',
        '_classify_and_clean_query',
        '_expand_to_full_document'
    ]
    
    print("檢查必要方法...")
    for method_name in required_methods:
        if hasattr(service, method_name):
            print(f"✅ {method_name} 存在")
        else:
            print(f"❌ {method_name} 缺失")
            return False
    
    print("\n✅ 搜尋服務方法完整")
    return True


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("智能搜尋路由器測試")
    print("=" * 60)
    
    all_passed = True
    
    # 測試 1: 關鍵字檢測與路由
    if not test_keyword_detection():
        all_passed = False
    
    # 測試 2: 模式 A 流程
    if not test_mode_a_flow():
        all_passed = False
    
    # 測試 3: 模式 B 流程
    if not test_mode_b_flow():
        all_passed = False
    
    # 測試 4: 搜尋服務方法
    if not test_search_service_methods():
        all_passed = False
    
    # 總結
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ 所有測試通過！智能路由器結構正確。")
        print("\n下一步：")
        print("1. 整合到 ProtocolGuideViewSet.chat() API")
        print("2. 實際測試與 Dify AI 的整合")
        print("3. 前端 UI 實作")
    else:
        print("❌ 部分測試失敗，請檢查錯誤訊息")
    print("=" * 60)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
