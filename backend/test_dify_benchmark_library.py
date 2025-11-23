#!/usr/bin/env python
"""
測試 Dify Benchmark Library

驗證：
1. Library 組件是否正確導入
2. KeywordEvaluator 是否正常工作
3. DifyAPIClient 連線是否正常

用法：
    cd /home/user/codes/ai-platform-web/backend
    docker exec ai-django python test_dify_benchmark_library.py
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.dify_benchmark import (
    DifyBatchTester,
    DifyTestRunner,
    DifyAPIClient,
    KeywordEvaluator
)


def test_keyword_evaluator():
    """測試關鍵字評分器"""
    print("\n" + "=" * 60)
    print("測試 1: KeywordEvaluator")
    print("=" * 60)
    
    evaluator = KeywordEvaluator()
    
    # 測試案例 1：高分案例（80%）
    result1 = evaluator.evaluate(
        question="什麼是 I3C?",
        expected_answer="I3C 是一種通訊協定",
        actual_answer="I3C 是 MIPI 聯盟定義的新一代通訊協定，用於感測器和主控制器之間的連接。",
        keywords=["I3C", "MIPI", "通訊協定", "感測器", "主控制器"]
    )
    
    print(f"\n案例 1（高分案例）:")
    print(f"  問題: 什麼是 I3C?")
    print(f"  關鍵字: ['I3C', 'MIPI', '通訊協定', '感測器', '主控制器']")
    print(f"  分數: {result1['score']}")
    print(f"  及格: {'✅ 是' if result1['is_passed'] else '❌ 否'}")
    print(f"  匹配關鍵字: {result1['matched_keywords']}")
    print(f"  遺漏關鍵字: {result1['missing_keywords']}")
    
    # 測試案例 2：低分案例（40%）
    result2 = evaluator.evaluate(
        question="什麼是 CUP?",
        expected_answer="CUP 是 Protocol 的測試方法",
        actual_answer="這是一種協定測試。",
        keywords=["CUP", "Protocol", "測試", "方法", "連線"]
    )
    
    print(f"\n案例 2（低分案例）:")
    print(f"  問題: 什麼是 CUP?")
    print(f"  關鍵字: ['CUP', 'Protocol', '測試', '方法', '連線']")
    print(f"  分數: {result2['score']}")
    print(f"  及格: {'✅ 是' if result2['is_passed'] else '❌ 否'}")
    print(f"  匹配關鍵字: {result2['matched_keywords']}")
    print(f"  遺漏關鍵字: {result2['missing_keywords']}")
    
    # 批量評分測試
    print(f"\n批量評分測試:")
    test_cases = [
        {
            'question': 'Q1',
            'expected_answer': 'A1',
            'actual_answer': 'I3C MIPI 協定',
            'keywords': ['I3C', 'MIPI', '協定']
        },
        {
            'question': 'Q2',
            'expected_answer': 'A2',
            'actual_answer': 'CUP 測試',
            'keywords': ['CUP', 'Protocol', '測試']
        }
    ]
    
    batch_results = evaluator.batch_evaluate(test_cases)
    statistics = evaluator.get_statistics(batch_results)
    
    print(f"  總案例數: {statistics['total_cases']}")
    print(f"  及格數: {statistics['passed_cases']}")
    print(f"  不及格數: {statistics['failed_cases']}")
    print(f"  通過率: {statistics['pass_rate']}%")
    print(f"  平均分數: {statistics['average_score']}")
    
    return True


def test_dify_api_client():
    """測試 Dify API Client"""
    print("\n" + "=" * 60)
    print("測試 2: DifyAPIClient")
    print("=" * 60)
    
    try:
        client = DifyAPIClient()
        
        # 測試連線
        print("\n測試 Dify API 連線...")
        connection_test = client.test_connection()
        
        print(f"  連線結果: {'✅ 成功' if connection_test['success'] else '❌ 失敗'}")
        print(f"  回應時間: {connection_test['response_time']}s")
        print(f"  訊息: {connection_test['message']}")
        
        if connection_test['success']:
            # 測試實際問題
            print("\n測試實際問題查詢...")
            result = client.send_question(
                question="什麼是 I3C?",
                user_id="test_user"
            )
            
            if result['success']:
                print(f"  查詢成功:")
                print(f"    回應長度: {len(result['answer'])} 字元")
                print(f"    回應時間: {result['response_time']}s")
                print(f"    檢索文檔數: {len(result.get('retrieved_documents', []))}")
                print(f"    回應預覽: {result['answer'][:100]}...")
            else:
                print(f"  查詢失敗: {result.get('error', 'Unknown')}")
        
        return connection_test['success']
        
    except Exception as e:
        print(f"  ❌ 測試失敗: {str(e)}")
        return False


def test_library_imports():
    """測試 Library 導入"""
    print("\n" + "=" * 60)
    print("測試 3: Library 導入")
    print("=" * 60)
    
    imports = [
        ('DifyBatchTester', DifyBatchTester),
        ('DifyTestRunner', DifyTestRunner),
        ('DifyAPIClient', DifyAPIClient),
        ('KeywordEvaluator', KeywordEvaluator),
    ]
    
    all_success = True
    for name, obj in imports:
        try:
            print(f"  ✅ {name}: {obj}")
        except Exception as e:
            print(f"  ❌ {name}: 導入失敗 - {str(e)}")
            all_success = False
    
    return all_success


def main():
    """主測試函數"""
    print("\n" + "=" * 60)
    print("Dify Benchmark Library 測試")
    print("=" * 60)
    
    results = {
        'library_imports': False,
        'keyword_evaluator': False,
        'dify_api_client': False
    }
    
    # 測試 1: Library 導入
    results['library_imports'] = test_library_imports()
    
    # 測試 2: KeywordEvaluator
    results['keyword_evaluator'] = test_keyword_evaluator()
    
    # 測試 3: DifyAPIClient
    results['dify_api_client'] = test_dify_api_client()
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    
    for test_name, success in results.items():
        status = "✅ 通過" if success else "❌ 失敗"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有測試通過！Library 已準備就緒。")
    else:
        print("⚠️ 部分測試失敗，請檢查錯誤訊息。")
    print("=" * 60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
