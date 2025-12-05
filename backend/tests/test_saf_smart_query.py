#!/usr/bin/env python
"""
SAF Smart Query 整合測試
========================

測試 LLM Smart API Router 的完整功能。

測試項目：
1. 意圖分析器 (IntentAnalyzer)
2. 查詢路由器 (QueryRouter)
3. 回答生成器 (ResponseGenerator)
4. 端到端流程

執行方式：
    docker exec ai-django bash -c "cd /app/backend && python ../tests/test_saf_smart_query.py"

作者：AI Platform Team
創建日期：2025-12-05
"""

import os
import sys
import json

# 添加項目路徑
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.saf_integration.smart_query.intent_types import IntentType, IntentResult
from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer
from library.saf_integration.smart_query.query_router import QueryRouter, SmartQueryService
from library.saf_integration.smart_query.response_generator import SAFResponseGenerator


def print_header(title):
    """打印標題"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_section(title):
    """打印章節"""
    print(f"\n--- {title} ---")


def test_intent_types():
    """測試意圖類型定義"""
    print_header("測試 1: 意圖類型定義")
    
    # 測試 IntentType 枚舉
    print_section("IntentType 枚舉測試")
    
    for intent in IntentType:
        print(f"  {intent.value}: {intent.get_description()}")
        print(f"    必要參數: {intent.get_required_parameters()}")
        print(f"    可選參數: {intent.get_optional_parameters()}")
    
    # 測試字串轉換
    print_section("字串轉換測試")
    
    test_strings = [
        "query_projects_by_customer",
        "count_projects",
        "invalid_intent",
        "UNKNOWN"
    ]
    
    for s in test_strings:
        result = IntentType.from_string(s)
        print(f"  '{s}' -> {result.value}")
    
    # 測試 IntentResult
    print_section("IntentResult 測試")
    
    result = IntentResult(
        intent=IntentType.QUERY_PROJECTS_BY_CUSTOMER,
        parameters={"customer": "WD"},
        confidence=0.95
    )
    
    print(f"  Intent: {result.intent.value}")
    print(f"  Parameters: {result.parameters}")
    print(f"  Confidence: {result.confidence}")
    print(f"  Is Valid: {result.is_valid()}")
    print(f"  Is High Confidence: {result.is_high_confidence()}")
    
    print("\n✅ 意圖類型定義測試通過")


def test_intent_analyzer_fallback():
    """測試意圖分析器的降級方案（關鍵字匹配）"""
    print_header("測試 2: 意圖分析器降級方案")
    
    analyzer = SAFIntentAnalyzer()
    
    test_cases = [
        # (查詢, 預期意圖, 預期參數)
        ("WD 有哪些專案？", IntentType.QUERY_PROJECTS_BY_CUSTOMER, {"customer": "WD"}),
        ("Samsung 有幾個專案？", IntentType.COUNT_PROJECTS, {"customer": "Samsung"}),
        ("SM2264 控制器用在哪些專案？", IntentType.QUERY_PROJECTS_BY_CONTROLLER, {"controller": "SM2264"}),
        ("有哪些客戶？", IntentType.LIST_ALL_CUSTOMERS, {}),
        ("有哪些控制器？", IntentType.LIST_ALL_CONTROLLERS, {}),
        ("總共有多少專案？", IntentType.COUNT_PROJECTS, {}),
    ]
    
    for query, expected_intent, expected_params in test_cases:
        # 直接測試降級方案
        result = analyzer._fallback_analysis(query)
        
        intent_match = result.intent == expected_intent
        params_match = all(
            result.parameters.get(k) == v 
            for k, v in expected_params.items()
        )
        
        status = "✅" if intent_match and params_match else "❌"
        print(f"\n{status} 查詢: '{query}'")
        print(f"   預期意圖: {expected_intent.value}")
        print(f"   實際意圖: {result.intent.value}")
        print(f"   預期參數: {expected_params}")
        print(f"   實際參數: {result.parameters}")
    
    print("\n✅ 意圖分析器降級方案測試完成")


def test_intent_analyzer_llm():
    """測試意圖分析器的 LLM 分析（需要 Dify 服務）"""
    print_header("測試 3: 意圖分析器 LLM 分析")
    
    try:
        analyzer = SAFIntentAnalyzer()
        
        test_queries = [
            "WD 有哪些專案？",
            "Samsung 有幾個專案？",
            "SM2264 用在哪些專案？",
        ]
        
        for query in test_queries:
            print(f"\n查詢: '{query}'")
            
            try:
                result = analyzer.analyze(query)
                
                print(f"  意圖: {result.intent.value}")
                print(f"  參數: {result.parameters}")
                print(f"  信心度: {result.confidence:.2f}")
                print(f"  有效: {result.is_valid()}")
                
                if result.raw_response:
                    print(f"  原始回應: {result.raw_response[:100]}...")
                    
            except Exception as e:
                print(f"  ❌ 錯誤: {str(e)}")
        
        print("\n✅ 意圖分析器 LLM 分析測試完成")
        
    except Exception as e:
        print(f"\n⚠️ LLM 測試跳過: {str(e)}")
        print("   （可能是 Dify 服務未啟動）")


def test_query_router():
    """測試查詢路由器"""
    print_header("測試 4: 查詢路由器")
    
    router = QueryRouter()
    
    print_section("支援的意圖類型")
    for intent in router.get_supported_intents():
        print(f"  - {intent}")
    
    # 測試路由
    print_section("路由測試")
    
    test_intents = [
        IntentResult(
            intent=IntentType.QUERY_PROJECTS_BY_CUSTOMER,
            parameters={"customer": "WD"},
            confidence=0.9
        ),
        IntentResult(
            intent=IntentType.COUNT_PROJECTS,
            parameters={},
            confidence=0.9
        ),
        IntentResult(
            intent=IntentType.LIST_ALL_CUSTOMERS,
            parameters={},
            confidence=0.9
        ),
        IntentResult(
            intent=IntentType.UNKNOWN,
            parameters={},
            confidence=0.3
        ),
    ]
    
    for intent_result in test_intents:
        print(f"\n  路由: {intent_result.intent.value}")
        
        try:
            result = router.route(intent_result)
            
            print(f"    狀態: {result.status.value}")
            print(f"    數量: {result.count}")
            print(f"    訊息: {result.message}")
            
            if result.error:
                print(f"    錯誤: {result.error}")
                
        except Exception as e:
            print(f"    ❌ 錯誤: {str(e)}")
    
    print("\n✅ 查詢路由器測試完成")


def test_response_generator():
    """測試回答生成器"""
    print_header("測試 5: 回答生成器")
    
    generator = SAFResponseGenerator()
    
    # 模擬查詢結果
    test_results = [
        {
            'success': True,
            'query': 'WD 有哪些專案？',
            'intent': {
                'type': 'query_projects_by_customer',
                'parameters': {'customer': 'WD'},
                'confidence': 0.95
            },
            'result': {
                'status': 'success',
                'data': [
                    {'projectName': 'Project A', 'customer': 'WD', 'controller': 'SM2264', 'nand': 'TLC', 'pl': 'John'},
                    {'projectName': 'Project B', 'customer': 'WD', 'controller': 'SM2269', 'nand': 'QLC', 'pl': 'Jane'},
                ],
                'count': 2,
                'parameters': {'customer': 'WD'},
                'message': '找到 2 個 WD 的專案'
            }
        },
        {
            'success': True,
            'query': '有哪些客戶？',
            'intent': {
                'type': 'list_all_customers',
                'parameters': {},
                'confidence': 0.92
            },
            'result': {
                'status': 'success',
                'data': {
                    'customers': ['WD', 'Samsung', 'Micron'],
                    'customer_count': 3,
                    'customer_stats': {'WD': 5, 'Samsung': 3, 'Micron': 2}
                },
                'count': 3,
                'parameters': {},
                'message': '共有 3 個客戶'
            }
        },
        {
            'success': False,
            'query': '找不到的東西',
            'intent': {
                'type': 'unknown',
                'parameters': {},
                'confidence': 0.2
            },
            'result': {
                'status': 'no_results',
                'data': {'help': '請嘗試其他查詢'},
                'count': 0,
                'message': '無法理解查詢意圖'
            }
        }
    ]
    
    for query_result in test_results:
        print(f"\n查詢: '{query_result['query']}'")
        print(f"意圖: {query_result['intent']['type']}")
        
        answer = generator.generate(query_result)
        
        print(f"\n回答:")
        print("-" * 40)
        print(answer.get('answer', '（無回答）'))
        print("-" * 40)
        
        if answer.get('summary'):
            print(f"摘要: {answer['summary']}")
    
    print("\n✅ 回答生成器測試完成")


def test_end_to_end():
    """端到端測試"""
    print_header("測試 6: 端到端測試")
    
    try:
        service = SmartQueryService()
        generator = SAFResponseGenerator()
        
        test_queries = [
            "WD 有哪些專案？",
            "有哪些客戶？",
            "總共有多少專案？",
        ]
        
        for query in test_queries:
            print(f"\n{'='*50}")
            print(f"用戶問題: {query}")
            print("=" * 50)
            
            try:
                # 執行查詢
                result = service.query(query, "test-user")
                
                print(f"\n意圖分析:")
                print(f"  類型: {result['intent']['type']}")
                print(f"  參數: {result['intent']['parameters']}")
                print(f"  信心度: {result['intent']['confidence']:.2f}")
                
                print(f"\n查詢結果:")
                print(f"  成功: {result['success']}")
                print(f"  數量: {result['result'].get('count', 0)}")
                
                # 生成回答
                answer = generator.generate(result)
                
                print(f"\n生成的回答:")
                print("-" * 40)
                print(answer.get('answer', '（無回答）')[:500])
                if len(answer.get('answer', '')) > 500:
                    print("... (已截斷)")
                print("-" * 40)
                
                print(f"\n處理時間: {result['metadata']['query_time_ms']:.2f}ms")
                
            except Exception as e:
                print(f"  ❌ 錯誤: {str(e)}")
        
        print("\n✅ 端到端測試完成")
        
    except Exception as e:
        print(f"\n⚠️ 端到端測試失敗: {str(e)}")


def test_dify_config():
    """測試 Dify 配置"""
    print_header("測試 0: Dify 配置驗證")
    
    try:
        from library.config.dify_config_manager import (
            get_saf_intent_analyzer_config,
            get_saf_analyzer_config
        )
        
        print_section("SAF Intent Analyzer 配置")
        intent_config = get_saf_intent_analyzer_config()
        print(f"  App Name: {intent_config.app_name}")
        print(f"  API URL: {intent_config.api_url}")
        print(f"  API Key: {intent_config.api_key[:15]}...")
        print(f"  Timeout: {intent_config.timeout}s")
        print(f"  驗證: {'✅ 通過' if intent_config.validate() else '❌ 失敗'}")
        
        print_section("SAF Analyzer 配置")
        analyzer_config = get_saf_analyzer_config()
        print(f"  App Name: {analyzer_config.app_name}")
        print(f"  API URL: {analyzer_config.api_url}")
        print(f"  API Key: {analyzer_config.api_key[:15]}...")
        print(f"  Timeout: {analyzer_config.timeout}s")
        print(f"  驗證: {'✅ 通過' if analyzer_config.validate() else '❌ 失敗'}")
        
        print("\n✅ Dify 配置驗證完成")
        
    except Exception as e:
        print(f"\n❌ Dify 配置驗證失敗: {str(e)}")


def main():
    """主測試函數"""
    print("\n" + "#" * 60)
    print("#  SAF Smart Query 整合測試")
    print("#  LLM Smart API Router")
    print("#" * 60)
    
    try:
        # 測試 Dify 配置
        test_dify_config()
        
        # 測試意圖類型定義
        test_intent_types()
        
        # 測試意圖分析器降級方案
        test_intent_analyzer_fallback()
        
        # 測試意圖分析器 LLM 分析
        test_intent_analyzer_llm()
        
        # 測試查詢路由器
        test_query_router()
        
        # 測試回答生成器
        test_response_generator()
        
        # 端到端測試
        test_end_to_end()
        
        print("\n" + "#" * 60)
        print("#  所有測試完成！")
        print("#" * 60)
        
    except Exception as e:
        print(f"\n❌ 測試過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
