#!/usr/bin/env python
"""
🚀 Dify Benchmark 真實問題測試
測試多線程功能是否能真正發送問題並獲得答案

執行方式：
docker exec ai-django python /app/test_dify_real_questions.py
"""

import os
import sys
import django

# Django 設置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion, DifyBenchmarkTestCase, DifyTestRun
from library.dify_benchmark.dify_test_runner import DifyTestRunner
from library.dify_benchmark.dify_api_client import DifyAPIClient
import time
from datetime import datetime

def print_header(title):
    """打印標題"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_test_case(test_case):
    """打印測試案例詳情"""
    print(f"\n📝 測試案例 #{test_case.id}")
    print(f"   問題: {test_case.question}")
    print(f"   期望答案: {test_case.expected_answer[:100]}...")
    print(f"   關鍵字: {test_case.answer_keywords}")
    print(f"   難度: {test_case.difficulty_level}")

def test_single_question_directly():
    """
    測試 1: 直接發送單個問題到 Dify
    驗證 API 連接和問題回答功能
    """
    print_header("🧪 測試 1: 直接發送問題到 Dify")
    
    # 獲取測試版本
    try:
        version = DifyConfigVersion.objects.get(version_name="Dify 二階搜尋 v1.1")
        print(f"✅ 找到測試版本: {version.version_name}")
        print(f"   API Key: {version.dify_api_key[:20]}...")
        print(f"   API URL: {version.dify_api_url}")
    except DifyConfigVersion.DoesNotExist:
        print("❌ 找不到測試版本")
        return False
    
    # 初始化 API Client
    api_client = DifyAPIClient(
        api_key=version.dify_api_key,
        api_url=version.dify_api_url
    )
    
    # 測試問題
    test_question = "ULINK 測試的安裝程式和測試腳本存放在 NAS 的哪個路徑？"
    user_id = f"real_test_{int(time.time())}"
    
    print(f"\n📤 發送問題...")
    print(f"   問題: {test_question}")
    print(f"   User ID: {user_id}")
    
    try:
        start_time = time.time()
        response = api_client.send_question(
            question=test_question,
            user_id=user_id,
            conversation_id=None  # 新對話
        )
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ 收到回應（耗時 {elapsed_time:.2f} 秒）")
        print(f"\n📥 Dify 回答：")
        print("-" * 80)
        print(response.get('answer', 'No answer')[:500])
        print("-" * 80)
        
        print(f"\n📊 回應詳情:")
        print(f"   Message ID: {response.get('message_id', 'N/A')}")
        print(f"   Conversation ID: {response.get('conversation_id', 'N/A')}")
        print(f"   檢索文檔數: {len(response.get('retrieved_documents', []))}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_parallel_real_questions():
    """
    測試 2: 使用多線程並行發送真實問題
    驗證完整的測試流程
    """
    print_header("🧪 測試 2: 並行執行真實測試案例")
    
    # 獲取測試版本
    try:
        version = DifyConfigVersion.objects.get(version_name="Dify 二階搜尋 v1.1")
        print(f"✅ 找到測試版本: {version.version_name}")
    except DifyConfigVersion.DoesNotExist:
        print("❌ 找不到測試版本")
        return False
    
    # 獲取測試案例
    test_cases = DifyBenchmarkTestCase.objects.filter(is_active=True)[:3]
    
    if not test_cases:
        print("❌ 沒有找到活躍的測試案例")
        return False
    
    print(f"\n📋 找到 {len(test_cases)} 個測試案例:")
    for i, tc in enumerate(test_cases, 1):
        print(f"   {i}. {tc.question[:60]}...")
    
    # 初始化 TestRunner (使用並行模式)
    runner = DifyTestRunner(
        version=version,
        use_ai_evaluator=False,  # 使用關鍵字評分
        max_workers=3  # 3 個並行線程
    )
    
    print(f"\n🚀 開始並行測試 (3 個線程)...")
    
    try:
        start_time = time.time()
        
        # 執行測試 (使用並行方法)
        test_run = runner.run_batch_tests_parallel(
            test_cases=list(test_cases),
            run_name=f"真實問題測試 {datetime.now().strftime('%H:%M:%S')}",
            batch_id=f"real_test_{int(time.time())}"
        )
        
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ 測試完成（耗時 {elapsed_time:.2f} 秒）")
        print(f"\n📊 測試結果:")
        print(f"   Test Run ID: {test_run.id}")
        print(f"   總測試數: {test_run.total_test_cases}")
        print(f"   通過數: {test_run.passed_cases}")
        print(f"   失敗數: {test_run.failed_cases}")
        print(f"   通過率: {test_run.pass_rate}%")
        print(f"   平均分數: {test_run.average_score}")
        
        # 顯示每個測試的結果
        results = test_run.results.all()
        print(f"\n📝 詳細結果:")
        
        for i, result in enumerate(results, 1):
            print(f"\n   測試 {i}: {result.test_case.question[:50]}...")
            print(f"      是否通過: {'✅ 是' if result.is_passed else '❌ 否'}")
            print(f"      分數: {result.score}/{result.test_case.max_score}")
            print(f"      回應時間: {result.response_time}s")
            print(f"      Dify 回答: {result.dify_answer[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_conversation_isolation():
    """
    測試 3: 驗證 Conversation ID 隔離
    確保每個測試使用獨立對話
    """
    print_header("🧪 測試 3: Conversation ID 隔離驗證")
    
    try:
        version = DifyConfigVersion.objects.get(version_name="Dify 二階搜尋 v1.1")
    except DifyConfigVersion.DoesNotExist:
        print("❌ 找不到測試版本")
        return False
    
    api_client = DifyAPIClient(
        api_key=version.dify_api_key,
        api_url=version.dify_api_url
    )
    
    test_question = "請問 Protocol 測試有哪些類別？"
    
    print("\n發送 3 次相同問題，每次使用不同 user_id 和 conversation_id=None")
    conversation_ids = []
    
    for i in range(1, 4):
        user_id = f"isolation_test_{int(time.time())}_{i}"
        
        print(f"\n📤 測試 {i}:")
        print(f"   User ID: {user_id}")
        
        try:
            response = api_client.send_question(
                question=test_question,
                user_id=user_id,
                conversation_id=None  # 強制新對話
            )
            
            conv_id = response.get('conversation_id')
            conversation_ids.append(conv_id)
            
            print(f"   ✅ Conversation ID: {conv_id}")
            
        except Exception as e:
            print(f"   ❌ 失敗: {str(e)}")
            return False
    
    # 驗證所有 conversation_id 都不同
    print(f"\n📊 隔離性驗證:")
    print(f"   收集到的 Conversation IDs: {len(conversation_ids)}")
    print(f"   唯一 Conversation IDs: {len(set(conversation_ids))}")
    
    if len(set(conversation_ids)) == len(conversation_ids):
        print(f"   ✅ 所有 Conversation ID 都不同，隔離性驗證通過！")
        return True
    else:
        print(f"   ❌ 發現重複的 Conversation ID，隔離性驗證失敗！")
        return False

def main():
    """主測試流程"""
    
    print("\n" + "=" * 80)
    print("  🚀 Dify Benchmark 真實問題測試")
    print("  測試多線程功能是否能真正發送問題並獲得答案")
    print("=" * 80)
    print(f"\n測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'test1': False,
        'test2': False,
        'test3': False
    }
    
    # 測試 1: 直接發送單個問題
    results['test1'] = test_single_question_directly()
    time.sleep(2)
    
    # 測試 2: 並行執行真實測試案例
    results['test2'] = test_parallel_real_questions()
    time.sleep(2)
    
    # 測試 3: Conversation ID 隔離
    results['test3'] = test_conversation_isolation()
    
    # 測試總結
    print_header("✅ 測試完成")
    
    print("\n測試結果統計:")
    print(f"   測試 1 (直接發送問題): {'✅ 通過' if results['test1'] else '❌ 失敗'}")
    print(f"   測試 2 (並行測試): {'✅ 通過' if results['test2'] else '❌ 失敗'}")
    print(f"   測試 3 (隔離驗證): {'✅ 通過' if results['test3'] else '❌ 失敗'}")
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n總計: {passed}/{total} 個測試通過 ({passed/total*100:.1f}%)")
    
    if all(results.values()):
        print("\n🎉 所有測試通過！多線程功能完全正常，可以真正發送問題並獲得答案！")
        return 0
    else:
        print("\n⚠️  有測試失敗，請檢查錯誤訊息。")
        return 1

if __name__ == '__main__':
    sys.exit(main())
