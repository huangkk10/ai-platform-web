#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
不確定性檢測機制全面測試
========================

測試各種情境下的 uncertainty_detector 是否正常工作
包括：正常回答、不確定回答、邊界案例、免責聲明等
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.ai_response.uncertainty_detector import is_uncertain_response


def print_test_result(test_name, response, expected_uncertain, result_uncertain, keyword):
    """格式化輸出測試結果"""
    status = "✅ PASS" if (result_uncertain == expected_uncertain) else "❌ FAIL"
    
    print(f"\n{'='*80}")
    print(f"測試: {test_name}")
    print(f"{'='*80}")
    print(f"回應內容:")
    print(f"  「{response}」")
    print(f"\n預期結果: {'不確定' if expected_uncertain else '確定'}")
    print(f"實際結果: {'不確定' if result_uncertain else '確定'}")
    if keyword:
        print(f"觸發關鍵字: {keyword}")
    print(f"\n{status}")
    
    return result_uncertain == expected_uncertain


def run_all_tests():
    """執行所有測試案例"""
    
    print("\n" + "🧪" * 40)
    print("不確定性檢測機制 - 全面情境測試")
    print("🧪" * 40 + "\n")
    
    test_cases = [
        # ===== 分類 1: 正常確定的回答 (應該 Pass) =====
        {
            'name': '1-1. 簡單明確回答',
            'response': 'Cup 的顏色是紅色。',
            'expected': False
        },
        {
            'name': '1-2. 帶 Dify 免責聲明的回答 (核心案例)',
            'response': 'Cup 的顏色是紅色。[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': False
        },
        {
            'name': '1-3. 多句確定回答',
            'response': 'Cup 的顏色是紅色。它用於測試目的。測試流程包含三個步驟。',
            'expected': False
        },
        {
            'name': '1-4. 含技術細節的回答',
            'response': 'USB 3.0 的傳輸速度最高可達 5 Gbps，向下相容 USB 2.0。',
            'expected': False
        },
        {
            'name': '1-5. 引用來源的回答',
            'response': '根據文檔，Cup 測試需要進行三個步驟：初始化、執行測試、驗證結果。',
            'expected': False
        },
        
        # ===== 分類 2: 不確定的回答 (應該被檢測) =====
        {
            'name': '2-1. 明確說不知道',
            'response': '我不知道 Cup 的顏色是什麼。',
            'expected': True
        },
        {
            'name': '2-2. 表達不確定',
            'response': '我不確定 Cup 的顏色。',
            'expected': True
        },
        {
            'name': '2-3. 找不到資訊',
            'response': '抱歉，我找不到關於 Cup 顏色的資訊。',
            'expected': True
        },
        {
            'name': '2-4. 無法回答',
            'response': '無法回答您的問題，因為文檔中沒有提供相關資訊。',
            'expected': True
        },
        {
            'name': '2-5. 使用「也許」',
            'response': 'Cup 的顏色也許是紅色。',
            'expected': True
        },
        {
            'name': '2-6. 使用「大概」',
            'response': 'Cup 的顏色大概是紅色。',
            'expected': True
        },
        {
            'name': '2-7. 使用「似乎」',
            'response': 'Cup 似乎是紅色的。',
            'expected': True
        },
        {
            'name': '2-8. 使用「或許」',
            'response': 'Cup 或許是紅色的。',
            'expected': True
        },
        
        # ===== 分類 3: 邊界案例 =====
        {
            'name': '3-1. 多重不確定關鍵字',
            'response': '我不太確定，也許 Cup 是紅色的，或許需要進一步確認。',
            'expected': True
        },
        {
            'name': '3-2. 部分確定+部分不確定',
            'response': 'Cup 用於測試，但我不確定它的顏色。',
            'expected': True
        },
        {
            'name': '3-3. 建議參考文檔 (無明確答案)',
            'response': '請參考以下文件以獲取更多資訊。',
            'expected': True
        },
        {
            'name': '3-4. 空回答',
            'response': '',
            'expected': True
        },
        {
            'name': '3-5. 只有免責聲明',
            'response': '[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': False  # 免責聲明本身不算不確定
        },
        
        # ===== 分類 4: 可能造成誤判的案例 (應該 Pass) =====
        {
            'name': '4-1. 描述可能性的正常句子 (含「可能」但非免責聲明)',
            'response': 'USB 3.0 可能受到電磁干擾影響。',
            'expected': False  # 「可能」已從關鍵字列表移除
        },
        {
            'name': '4-2. 技術文件中的「可能」',
            'response': '這個測試可能需要 5-10 分鐘完成。',
            'expected': False  # 「可能」已從關鍵字列表移除
        },
        {
            'name': '4-3. 引用來源中包含「似乎」',
            'response': '根據文檔記錄，測試結果似乎顯示了性能問題。但實際原因已確認是配置錯誤。',
            'expected': True  # 含有「似乎」，應該檢測為不確定
        },
        {
            'name': '4-4. 完整回答+免責聲明+建議',
            'response': 'Cup 的顏色是紅色。[內容可能會發生錯誤，請查核重要資訊。]建議參考官方文檔。',
            'expected': True  # 含有「建議參考」，應該檢測為不確定
        },
        
        # ===== 分類 5: 特殊格式 =====
        {
            'name': '5-1. 多行回答',
            'response': '''Cup 的顏色是紅色。

測試步驟：
1. 初始化
2. 執行測試
3. 驗證結果

[內容可能會發生錯誤，請查核重要資訊。]''',
            'expected': False
        },
        {
            'name': '5-2. 含 Markdown 格式',
            'response': '**Cup 的顏色**: 紅色\n\n*用途*: 測試\n\n[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': False
        },
        {
            'name': '5-3. 含程式碼片段',
            'response': 'Cup 測試範例：\n```python\ntest_cup(color="red")\n```\n結果確認為紅色。',
            'expected': False
        },
        
        # ===== 分類 6: 真實 Dify 回應格式 =====
        {
            'name': '6-1. Dify 標準格式 (有答案)',
            'response': 'Cup 的顏色是紅色。\n\n[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': False
        },
        {
            'name': '6-2. Dify 標準格式 (無法回答)',
            'response': '抱歉，我無法在文檔中找到關於 Cup 顏色的資訊。\n\n[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': True  # 含有「無法」
        },
        {
            'name': '6-3. Dify 建議參考文檔',
            'response': '請參考以下文件：\n1. Cup 測試規範\n2. 測試流程說明\n\n[內容可能會發生錯誤，請查核重要資訊。]',
            'expected': True  # 含有「請參考」
        },
    ]
    
    # 執行所有測試
    passed = 0
    failed = 0
    failed_cases = []
    
    for i, test_case in enumerate(test_cases, 1):
        result_uncertain, keyword = is_uncertain_response(test_case['response'])
        
        if print_test_result(
            f"{i}. {test_case['name']}", 
            test_case['response'], 
            test_case['expected'], 
            result_uncertain, 
            keyword
        ):
            passed += 1
        else:
            failed += 1
            failed_cases.append({
                'name': test_case['name'],
                'response': test_case['response'][:50] + '...' if len(test_case['response']) > 50 else test_case['response'],
                'expected': test_case['expected'],
                'actual': result_uncertain,
                'keyword': keyword
            })
    
    # 輸出測試總結
    print("\n" + "=" * 80)
    print("📊 測試總結")
    print("=" * 80)
    print(f"總測試數: {len(test_cases)}")
    print(f"✅ 通過: {passed}")
    print(f"❌ 失敗: {failed}")
    print(f"通過率: {passed/len(test_cases)*100:.1f}%")
    
    if failed_cases:
        print("\n" + "=" * 80)
        print("❌ 失敗案例詳情")
        print("=" * 80)
        for case in failed_cases:
            print(f"\n測試: {case['name']}")
            print(f"  回應: {case['response']}")
            print(f"  預期: {'不確定' if case['expected'] else '確定'}")
            print(f"  實際: {'不確定' if case['actual'] else '確定'}")
            if case['keyword']:
                print(f"  觸發關鍵字: {case['keyword']}")
    
    print("\n" + "🎉" * 40)
    if failed == 0:
        print("恭喜！所有測試通過！")
    else:
        print(f"請檢查 {failed} 個失敗案例")
    print("🎉" * 40 + "\n")
    
    return passed, failed


if __name__ == '__main__':
    try:
        passed, failed = run_all_tests()
        sys.exit(0 if failed == 0 else 1)
    except Exception as e:
        print(f"\n❌ 測試執行錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
