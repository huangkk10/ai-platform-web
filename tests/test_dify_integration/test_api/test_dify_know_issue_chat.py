#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dify Know Issue Chat 應用測試腳本
測試與 Dify 平台中配置了 Know Issue Knowledge Base 的 Chat 應用整合
使用 library 模組重構版本
"""

import sys
import os
import time

# 添加 library 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from library.dify_integration.chat_client import DifyChatClient, create_chat_client
from library.dify_integration.chat_testing import DifyChatTester, TestSuiteBuilder
from library.ai_utils.test_analyzer import TestAnalyzer, analyze_results

# Dify API 配置
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.5/v1/chat-messages',
    'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
    'base_url': 'http://10.10.172.5'
}

def main():
    """主測試函數 - 使用 library 模組重構版本"""
    print("� Dify Know Issue Chat 應用測試 (Library版本)")
    print("=" * 60)
    print(f"🔗 Chat API 端點: {DIFY_CONFIG['api_url']}")
    print(f"� API Key: {DIFY_CONFIG['api_key'][:20]}...")
    print("=" * 60)
    
    # 創建 Chat 客戶端
    client = create_chat_client(
        api_url=DIFY_CONFIG['api_url'],
        api_key=DIFY_CONFIG['api_key'],
        base_url=DIFY_CONFIG['base_url']
    )
    
    # 1. 測試 API 連接
    if not client.test_connection():
        print("\n❌ Dify Chat API 連接失敗，請檢查配置")
        return
    
    # 創建測試器
    tester = DifyChatTester(client, delay_between_requests=1.5)
    
    # 創建分析器
    analyzer = TestAnalyzer()
    
    # 2. Know Issue 查詢測試
    know_issue_questions = ["ULINK"]
    
    print("\n🔍 執行 Know Issue 查詢測試...")
    know_issue_results = tester.batch_test(
        know_issue_questions, 
        test_name="Know Issue 查詢測試",
        user="know_issue_test_user"
    )
    analyzer.add_results(know_issue_results, "Know Issue 查詢")
    
    # 3. 對話上下文測試
    conversation_flow = [
        "請告訴我技術部有哪些員工？",
        "他們的職位分別是什麼？",
        "剛才提到的第一個人的詳細資訊是什麼？",
        "謝謝你的幫助"
    ]
    
    print("\n� 執行對話上下文測試...")
    context_results = tester.context_test(
        conversation_flow,
        test_name="對話上下文測試",
        user="context_test_user"
    )
    analyzer.add_results(context_results, "對話上下文")
    
    # 4. 知識庫整合測試
    knowledge_questions = [
        "請列出所有 Python 相關的員工",
        "誰負責更新 Know Issue？",
        "最近更新的問題有哪些？",
        "技術部門的薪資結構如何？",
        "有沒有關於測試的 Know Issue？"
    ]
    
    knowledge_keywords = ['python', '工程師', '技術部', '員工', 'know issue', '問題', 'ulink']
    
    print("\n� 執行知識庫整合測試...")
    knowledge_results = tester.knowledge_integration_test(
        knowledge_questions,
        knowledge_keywords,
        test_name="知識庫整合測試",
        user="knowledge_test_user"
    )
    analyzer.add_results(knowledge_results, "知識庫整合")
    
    # 5. 使用 TestSuiteBuilder 進行額外測試
    print("\n🧪 執行綜合測試套件...")
    suite = TestSuiteBuilder()
    suite.add_batch_test(
        ["Hello", "你好", "測試訊息"], 
        "基本聊天測試"
    ).add_context_test(
        ["你是誰？", "你能做什麼？", "再說一次"], 
        "身份確認對話"
    ).add_knowledge_test(
        ["ULINK 相關問題", "技術人員查詢"],
        ["ulink", "技術", "員工"],
        "專項知識測試"
    )
    
    suite_results = suite.run_all(tester, verbose=True)
    
    # 將套件結果添加到分析器
    for test_name, results in suite_results.items():
        analyzer.add_results(results, test_name)
    
    # 6. 生成綜合分析報告
    print("\n📊 生成測試分析報告...")
    analyzer.print_summary_report(detailed=True)
    
    # 7. 各項測試的詳細分析
    print("\n📋 各項測試詳細分析:")
    for test_name in analyzer.get_test_names():
        print(f"\n🔸 {test_name}:")
        test_stats = analyzer.generate_summary_report(test_name)
        basic = test_stats['basic_stats']
        print(f"  成功率: {basic['success_rate']:.1%} ({basic['successful_tests']}/{basic['total_tests']})")
        
        if test_stats['performance_stats']['mean'] > 0:
            perf = test_stats['performance_stats']
            print(f"  平均回應時間: {perf['mean']:.2f}s")
        
        if test_stats['knowledge_analysis']['total_tests'] > 0:
            knowledge = test_stats['knowledge_analysis']
            print(f"  知識庫使用率: {knowledge['knowledge_usage_rate']:.1%}")
    
    # 8. 導出詳細結果
    timestamp = time.strftime('%Y%m%d_%H%M%S')
    export_filename = f"dify_chat_test_results_{timestamp}.json"
    analyzer.export_to_json(export_filename)
    
    print("\n✅ Know Issue Chat 應用測試完成！")
    print("💡 Chat 應用已成功整合 Know Issue Knowledge Base")
    print(f"📁 詳細結果已保存至: {export_filename}")


if __name__ == "__main__":
    main()