#!/usr/bin/env python
"""
Phase 3: 實際測試與 Dify AI 整合

測試智能搜尋路由器與真實 Dify AI 的整合，
驗證兩種模式和降級邏輯的實際運作。

使用方式：
    docker exec ai-django python /app/library/protocol_guide/test_phase3_dify_integration.py

Author: AI Platform Team
Date: 2025-11-11
"""

import os
import sys
import django
import json

# 設置 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.smart_search_router import SmartSearchRouter
from library.protocol_guide.smart_search_config import get_default_config
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_section(title):
    """打印區段標題"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def print_result(result, test_name):
    """格式化打印測試結果"""
    print(f"\n{'─' * 70}")
    print(f"測試: {test_name}")
    print(f"{'─' * 70}")
    
    if result.get('mode') == 'error':
        print(f"❌ 錯誤: {result.get('error')}")
        return
    
    # 基本資訊
    print(f"📊 搜尋模式: {result.get('mode')}")
    if result.get('stage'):
        print(f"   階段: {result.get('stage')}")
    print(f"   是否降級: {'是 ⚠️' if result.get('is_fallback') else '否 ✅'}")
    if result.get('fallback_reason'):
        print(f"   降級原因: {result.get('fallback_reason')}")
    
    # AI 回答
    print(f"\n💬 AI 回答:")
    answer = result.get('answer', '')
    if len(answer) > 200:
        print(f"   {answer[:200]}...")
        print(f"   （回答長度：{len(answer)} 字元）")
    else:
        print(f"   {answer}")
    
    # 搜尋資訊
    search_count = len(result.get('search_results', []))
    print(f"\n🔍 搜尋結果: {search_count} 個文檔")
    
    # 對話資訊
    if result.get('conversation_id'):
        print(f"\n🗨️  對話 ID: {result.get('conversation_id')}")
    if result.get('message_id'):
        print(f"   訊息 ID: {result.get('message_id')}")
    
    # 效能資訊
    response_time = result.get('response_time')
    if response_time:
        print(f"\n⏱️  響應時間: {response_time:.2f} 秒")
    
    tokens = result.get('tokens', {})
    if tokens:
        print(f"   Token 使用: {tokens}")


def test_mode_a_with_keyword():
    """測試模式 A：含全文關鍵字的查詢"""
    print_section("測試 1: 模式 A - 關鍵字優先全文搜尋")
    
    router = SmartSearchRouter()
    
    test_queries = [
        "Cup 完整內容是什麼？",
        "UNH-IOL 全文說明",
        "I3C 的所有步驟怎麼做？",
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n🔍 查詢: {query}")
        print("   預期模式: mode_a (關鍵字優先全文搜尋)")
        
        try:
            result = router.handle_smart_search(
                user_query=query,
                conversation_id="",
                user_id="test_user_phase3"
            )
            
            print_result(result, f"模式 A - {query}")
            results.append({
                'query': query,
                'mode': result.get('mode'),
                'success': result.get('mode') != 'error',
                'is_fallback': result.get('is_fallback', False)
            })
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            results.append({
                'query': query,
                'mode': 'error',
                'success': False,
                'error': str(e)
            })
    
    return results


def test_mode_b_without_keyword():
    """測試模式 B：不含全文關鍵字的標準查詢"""
    print_section("測試 2: 模式 B - 標準兩階段搜尋")
    
    router = SmartSearchRouter()
    
    test_queries = [
        "Cup 的顏色是什麼？",
        "UNH-IOL 是什麼？",
        "I3C 的用途？",
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n🔍 查詢: {query}")
        print("   預期模式: mode_b (標準兩階段搜尋)")
        
        try:
            result = router.handle_smart_search(
                user_query=query,
                conversation_id="",
                user_id="test_user_phase3"
            )
            
            print_result(result, f"模式 B - {query}")
            results.append({
                'query': query,
                'mode': result.get('mode'),
                'stage': result.get('stage'),
                'success': result.get('mode') != 'error',
                'is_fallback': result.get('is_fallback', False)
            })
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            results.append({
                'query': query,
                'mode': 'error',
                'success': False,
                'error': str(e)
            })
    
    return results


def test_fallback_mechanism():
    """測試降級機制：查詢不存在的內容"""
    print_section("測試 3: 降級機制 - 不存在的內容")
    
    router = SmartSearchRouter()
    
    test_queries = [
        "新產品 XYZ 的完整測試流程是什麼？",  # 不存在的產品 + 全文關鍵字
        "如何測試 ABC123 產品？",  # 不存在的產品，無全文關鍵字
    ]
    
    results = []
    
    for query in test_queries:
        print(f"\n🔍 查詢: {query}")
        print("   預期: 可能觸發降級機制")
        
        try:
            result = router.handle_smart_search(
                user_query=query,
                conversation_id="",
                user_id="test_user_phase3"
            )
            
            print_result(result, f"降級測試 - {query}")
            results.append({
                'query': query,
                'mode': result.get('mode'),
                'success': result.get('mode') != 'error',
                'is_fallback': result.get('is_fallback', False),
                'fallback_reason': result.get('fallback_reason')
            })
            
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
            results.append({
                'query': query,
                'mode': 'error',
                'success': False,
                'error': str(e)
            })
    
    return results


def test_conversation_continuity():
    """測試對話連續性"""
    print_section("測試 4: 對話連續性")
    
    router = SmartSearchRouter()
    
    print("\n第一輪對話:")
    print("🔍 查詢: Cup 是什麼？")
    
    try:
        result1 = router.handle_smart_search(
            user_query="Cup 是什麼？",
            conversation_id="",
            user_id="test_user_continuity"
        )
        
        print_result(result1, "第一輪對話")
        
        conversation_id = result1.get('conversation_id')
        
        if conversation_id:
            print(f"\n✅ 獲得對話 ID: {conversation_id}")
            
            print("\n第二輪對話（使用相同 conversation_id）:")
            print("🔍 查詢: 它的完整內容呢？")
            
            result2 = router.handle_smart_search(
                user_query="它的完整內容呢？",
                conversation_id=conversation_id,
                user_id="test_user_continuity"
            )
            
            print_result(result2, "第二輪對話")
            
            return [{
                'test': 'conversation_continuity',
                'success': True,
                'conversation_id': conversation_id,
                'round_1_mode': result1.get('mode'),
                'round_2_mode': result2.get('mode')
            }]
        else:
            print("❌ 未獲得 conversation_id")
            return [{'test': 'conversation_continuity', 'success': False}]
    
    except Exception as e:
        print(f"\n❌ 對話連續性測試失敗: {str(e)}")
        return [{'test': 'conversation_continuity', 'success': False, 'error': str(e)}]


def test_configuration():
    """測試配置管理"""
    print_section("測試 5: 配置管理")
    
    config = get_default_config()
    
    print("📋 當前配置:")
    print(f"   模式 A:")
    print(f"     - Top K: {config.mode_a_top_k}")
    print(f"     - 閾值: {config.mode_a_threshold}")
    print(f"   模式 B 階段 1:")
    print(f"     - Top K: {config.mode_b_stage_1_top_k}")
    print(f"     - 閾值: {config.mode_b_stage_1_threshold}")
    print(f"   模式 B 階段 2:")
    print(f"     - Top K: {config.mode_b_stage_2_top_k}")
    print(f"     - 閾值: {config.mode_b_stage_2_threshold}")
    print(f"   Dify 超時: {config.dify_timeout} 秒")
    
    is_valid = config.validate()
    print(f"\n✅ 配置驗證: {'通過' if is_valid else '失敗'}")
    
    return [{'test': 'configuration', 'success': is_valid}]


def generate_summary(all_results):
    """生成測試總結"""
    print_section("Phase 3 測試總結")
    
    total_tests = sum(len(results) for results in all_results.values())
    successful_tests = sum(
        sum(1 for r in results if r.get('success', False))
        for results in all_results.values()
    )
    
    print(f"📊 測試統計:")
    print(f"   總測試數: {total_tests}")
    print(f"   成功: {successful_tests}")
    print(f"   失敗: {total_tests - successful_tests}")
    print(f"   成功率: {successful_tests / total_tests * 100:.1f}%")
    
    print(f"\n📋 各測試組結果:")
    for test_name, results in all_results.items():
        success_count = sum(1 for r in results if r.get('success', False))
        total = len(results)
        print(f"   {test_name}: {success_count}/{total} 通過")
    
    # 模式分佈
    print(f"\n🔍 搜尋模式分佈:")
    mode_a_count = sum(
        sum(1 for r in results if r.get('mode') == 'mode_a')
        for results in all_results.values()
    )
    mode_b_count = sum(
        sum(1 for r in results if r.get('mode') == 'mode_b')
        for results in all_results.values()
    )
    print(f"   模式 A: {mode_a_count} 次")
    print(f"   模式 B: {mode_b_count} 次")
    
    # 降級率
    fallback_count = sum(
        sum(1 for r in results if r.get('is_fallback', False))
        for results in all_results.values()
    )
    if total_tests > 0:
        fallback_rate = fallback_count / total_tests * 100
        print(f"\n⚠️  降級率: {fallback_rate:.1f}% ({fallback_count}/{total_tests})")
    
    print("\n" + "=" * 70)
    if successful_tests == total_tests:
        print("🎉 所有測試通過！智能搜尋路由器運作正常。")
    else:
        print(f"⚠️  部分測試失敗，請檢查錯誤訊息。")
    print("=" * 70)


def main():
    """主測試函數"""
    print("\n" + "=" * 70)
    print("  Phase 3: 實際測試與 Dify AI 整合")
    print("=" * 70)
    
    all_results = {}
    
    # 測試 1: 模式 A（關鍵字優先全文搜尋）
    try:
        all_results['test_mode_a'] = test_mode_a_with_keyword()
    except Exception as e:
        print(f"\n❌ 測試 1 執行失敗: {str(e)}")
        all_results['test_mode_a'] = []
    
    # 測試 2: 模式 B（標準兩階段搜尋）
    try:
        all_results['test_mode_b'] = test_mode_b_without_keyword()
    except Exception as e:
        print(f"\n❌ 測試 2 執行失敗: {str(e)}")
        all_results['test_mode_b'] = []
    
    # 測試 3: 降級機制
    try:
        all_results['test_fallback'] = test_fallback_mechanism()
    except Exception as e:
        print(f"\n❌ 測試 3 執行失敗: {str(e)}")
        all_results['test_fallback'] = []
    
    # 測試 4: 對話連續性
    try:
        all_results['test_conversation'] = test_conversation_continuity()
    except Exception as e:
        print(f"\n❌ 測試 4 執行失敗: {str(e)}")
        all_results['test_conversation'] = []
    
    # 測試 5: 配置管理
    try:
        all_results['test_config'] = test_configuration()
    except Exception as e:
        print(f"\n❌ 測試 5 執行失敗: {str(e)}")
        all_results['test_config'] = []
    
    # 生成總結
    generate_summary(all_results)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ Phase 3 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
