#!/usr/bin/env python3
"""
SAF Smart Query 情境測試腳本
============================

測試所有 8 種意圖類型和各種邊界情況。
會顯示完整的問答過程，並將結果儲存到檔案中。

執行方式：
    python tests/test_saf_smart_query/test_scenarios.py
    
    # 只執行特定測試套件
    python tests/test_saf_smart_query/test_scenarios.py --suite 1
    
    # 顯示詳細輸出
    python tests/test_saf_smart_query/test_scenarios.py --verbose

輸出：
    - 終端機顯示測試過程和結果
    - results/ 目錄下產生測試報告檔案

作者：AI Platform Team
創建日期：2025-12-05
"""

import json
import os
import requests
import time
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime

from test_cases import TestCase, ALL_TEST_SUITES


# ============================================================
# 配置
# ============================================================
API_URL = "http://127.0.0.1/api/saf/smart-query/"
TIMEOUT = 60  # 秒

# 結果存放目錄
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")


# ============================================================
# 測試結果定義
# ============================================================
@dataclass
class TestResult:
    """測試結果"""
    test_case: TestCase
    passed: bool
    actual_intent: str
    actual_params: Dict[str, Any]
    actual_confidence: float
    response_time_ms: float
    answer: str                         # AI 回應內容
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None


# ============================================================
# 測試執行器
# ============================================================

def run_single_test(test_case: TestCase, verbose: bool = False) -> TestResult:
    """執行單一測試案例"""
    start_time = time.time()
    
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"query": test_case.query},
            timeout=TIMEOUT
        )
        
        response_time_ms = (time.time() - start_time) * 1000
        
        # 處理 HTTP 錯誤狀態碼
        if response.status_code != 200:
            # 如果預期失敗，HTTP 4xx 也算通過
            if not test_case.should_succeed and response.status_code >= 400:
                return TestResult(
                    test_case=test_case,
                    passed=True,
                    actual_intent="",
                    actual_params={},
                    actual_confidence=0.0,
                    response_time_ms=response_time_ms,
                    answer="",
                    error_message=None
                )
            return TestResult(
                test_case=test_case,
                passed=False,
                actual_intent="",
                actual_params={},
                actual_confidence=0.0,
                response_time_ms=response_time_ms,
                answer="",
                error_message=f"HTTP {response.status_code}: {response.text[:200]}"
            )
        
        data = response.json()
        
        # 提取回應內容
        answer = ""
        if "answer" in data and isinstance(data["answer"], dict):
            answer = data["answer"].get("answer", "")
        elif "answer" in data and isinstance(data["answer"], str):
            answer = data["answer"]
        
        # 檢查是否成功
        if not test_case.should_succeed:
            # 預期失敗的測試
            passed = not data.get("success", True)
            return TestResult(
                test_case=test_case,
                passed=passed,
                actual_intent=data.get("intent", {}).get("type", ""),
                actual_params=data.get("intent", {}).get("parameters", {}),
                actual_confidence=data.get("intent", {}).get("confidence", 0),
                response_time_ms=response_time_ms,
                answer=answer,
                raw_response=data,
                error_message=None if passed else "預期失敗但實際成功"
            )
        
        # 預期成功的測試
        if not data.get("success"):
            return TestResult(
                test_case=test_case,
                passed=False,
                actual_intent="",
                actual_params={},
                actual_confidence=0.0,
                response_time_ms=response_time_ms,
                answer=answer,
                error_message=f"API 返回失敗: {data.get('error', 'Unknown error')}",
                raw_response=data
            )
        
        intent_data = data.get("intent", {})
        actual_intent = intent_data.get("type", "")
        actual_params = intent_data.get("parameters", {})
        actual_confidence = intent_data.get("confidence", 0)
        
        # 驗證結果
        intent_match = actual_intent == test_case.expected_intent
        
        # 參數部分匹配
        params_match = all(
            actual_params.get(k) == v or (k == "customer" and actual_params.get(k, "").upper() == v.upper())
            for k, v in test_case.expected_params.items()
        )
        
        confidence_ok = actual_confidence >= test_case.min_confidence
        
        passed = intent_match and params_match and confidence_ok
        
        error_msg = None
        if not passed:
            errors = []
            if not intent_match:
                errors.append(f"意圖不匹配: 預期 {test_case.expected_intent}, 實際 {actual_intent}")
            if not params_match:
                errors.append(f"參數不匹配: 預期 {test_case.expected_params}, 實際 {actual_params}")
            if not confidence_ok:
                errors.append(f"信心度不足: 預期 >= {test_case.min_confidence}, 實際 {actual_confidence}")
            error_msg = "; ".join(errors)
        
        return TestResult(
            test_case=test_case,
            passed=passed,
            actual_intent=actual_intent,
            actual_params=actual_params,
            actual_confidence=actual_confidence,
            response_time_ms=response_time_ms,
            answer=answer,
            error_message=error_msg,
            raw_response=data
        )
        
    except requests.Timeout:
        return TestResult(
            test_case=test_case,
            passed=False,
            actual_intent="",
            actual_params={},
            actual_confidence=0.0,
            response_time_ms=TIMEOUT * 1000,
            answer="",
            error_message="請求超時"
        )
    except Exception as e:
        return TestResult(
            test_case=test_case,
            passed=False,
            actual_intent="",
            actual_params={},
            actual_confidence=0.0,
            response_time_ms=(time.time() - start_time) * 1000,
            answer="",
            error_message=f"執行錯誤: {str(e)}"
        )


def format_conversation(result: TestResult) -> str:
    """格式化問答對話"""
    lines = []
    lines.append("┌" + "─" * 78 + "┐")
    lines.append(f"│ 🧑 用戶問題:                                                                 │")
    lines.append("├" + "─" * 78 + "┤")
    
    # 處理多行問題
    query = result.test_case.query
    for i in range(0, len(query), 74):
        chunk = query[i:i+74]
        lines.append(f"│   {chunk:<74} │")
    
    lines.append("├" + "─" * 78 + "┤")
    lines.append(f"│ 🤖 AI 回應:                                                                  │")
    lines.append("├" + "─" * 78 + "┤")
    
    # 處理多行回應
    answer = result.answer or "(無回應)"
    answer_lines = answer.split('\n')
    for line in answer_lines[:15]:  # 最多顯示 15 行
        for i in range(0, max(1, len(line)), 74):
            chunk = line[i:i+74] if line else ""
            lines.append(f"│   {chunk:<74} │")
    
    if len(answer_lines) > 15:
        lines.append(f"│   {'... (更多內容省略)':<74} │")
    
    lines.append("├" + "─" * 78 + "┤")
    lines.append(f"│ 📊 分析結果:                                                                 │")
    lines.append(f"│   意圖: {result.actual_intent:<67} │")
    lines.append(f"│   參數: {str(result.actual_params):<67} │")
    lines.append(f"│   信心度: {result.actual_confidence:.2f}                                                          │")
    lines.append(f"│   耗時: {result.response_time_ms:.0f}ms                                                           │")
    lines.append("└" + "─" * 78 + "┘")
    
    return '\n'.join(lines)


def run_test_suite(name: str, test_cases: List[TestCase], verbose: bool = False) -> List[TestResult]:
    """執行一組測試"""
    print(f"\n{'='*80}")
    print(f"📋 測試套件: {name}")
    print(f"{'='*80}")
    
    results = []
    for i, tc in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}] {tc.name} - {tc.description}")
        
        result = run_single_test(tc, verbose)
        results.append(result)
        
        # 顯示問答過程
        print(format_conversation(result))
        
        # 顯示測試結果
        if result.passed:
            print(f"✅ 測試通過")
        else:
            print(f"❌ 測試失敗: {result.error_message}")
        
        # 避免請求過快
        time.sleep(0.5)
    
    return results


def save_results_to_file(all_results: Dict[str, List[TestResult]], timestamp: str):
    """將測試結果儲存到檔案"""
    # 確保目錄存在
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    # 1. 儲存詳細的 JSON 結果
    json_file = os.path.join(RESULTS_DIR, f"test_result_{timestamp}.json")
    
    json_data = {
        "timestamp": timestamp,
        "api_url": API_URL,
        "suites": {}
    }
    
    for suite_name, results in all_results.items():
        suite_data = []
        for r in results:
            suite_data.append({
                "name": r.test_case.name,
                "query": r.test_case.query,
                "description": r.test_case.description,
                "expected_intent": r.test_case.expected_intent,
                "expected_params": r.test_case.expected_params,
                "actual_intent": r.actual_intent,
                "actual_params": r.actual_params,
                "actual_confidence": r.actual_confidence,
                "passed": r.passed,
                "response_time_ms": r.response_time_ms,
                "answer": r.answer,
                "error_message": r.error_message
            })
        json_data["suites"][suite_name] = suite_data
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 JSON 結果已儲存: {json_file}")
    
    # 2. 儲存可讀的 Markdown 報告
    md_file = os.path.join(RESULTS_DIR, f"test_report_{timestamp}.md")
    
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(f"# SAF Smart Query 測試報告\n\n")
        f.write(f"**測試時間**: {timestamp}\n\n")
        f.write(f"**API 端點**: {API_URL}\n\n")
        f.write("---\n\n")
        
        # 統計
        total_passed = sum(1 for results in all_results.values() for r in results if r.passed)
        total_tests = sum(len(results) for results in all_results.values())
        f.write(f"## 📊 總覽\n\n")
        f.write(f"- **總測試數**: {total_tests}\n")
        f.write(f"- **通過**: {total_passed}\n")
        f.write(f"- **失敗**: {total_tests - total_passed}\n")
        f.write(f"- **通過率**: {total_passed/total_tests*100:.1f}%\n\n")
        
        # 各套件詳情
        for suite_name, results in all_results.items():
            f.write(f"## {suite_name}\n\n")
            
            for r in results:
                status = "✅" if r.passed else "❌"
                f.write(f"### {status} {r.test_case.name}\n\n")
                f.write(f"**說明**: {r.test_case.description}\n\n")
                f.write(f"**用戶問題**:\n```\n{r.test_case.query}\n```\n\n")
                f.write(f"**AI 回應**:\n{r.answer}\n\n")
                f.write(f"**分析結果**:\n")
                f.write(f"- 意圖: `{r.actual_intent}` (預期: `{r.test_case.expected_intent}`)\n")
                f.write(f"- 參數: `{r.actual_params}` (預期: `{r.test_case.expected_params}`)\n")
                f.write(f"- 信心度: {r.actual_confidence:.2f} (最低: {r.test_case.min_confidence})\n")
                f.write(f"- 耗時: {r.response_time_ms:.0f}ms\n")
                
                if r.error_message:
                    f.write(f"- ⚠️ 錯誤: {r.error_message}\n")
                
                f.write("\n---\n\n")
    
    print(f"📝 Markdown 報告已儲存: {md_file}")
    
    # 3. 儲存簡單的對話記錄
    conversation_file = os.path.join(RESULTS_DIR, f"conversations_{timestamp}.txt")
    
    with open(conversation_file, 'w', encoding='utf-8') as f:
        f.write("SAF Smart Query 問答記錄\n")
        f.write(f"測試時間: {timestamp}\n")
        f.write("=" * 80 + "\n\n")
        
        for suite_name, results in all_results.items():
            f.write(f"\n{'='*80}\n")
            f.write(f"{suite_name}\n")
            f.write(f"{'='*80}\n")
            
            for r in results:
                status = "✅ PASS" if r.passed else "❌ FAIL"
                f.write(f"\n[{r.test_case.name}] {status}\n")
                f.write(f"{'-'*40}\n")
                f.write(f"🧑 問: {r.test_case.query}\n")
                f.write(f"\n🤖 答:\n{r.answer}\n")
                f.write(f"\n📊 意圖: {r.actual_intent} | 信心度: {r.actual_confidence:.2f} | 耗時: {r.response_time_ms:.0f}ms\n")
                if r.error_message:
                    f.write(f"⚠️ 錯誤: {r.error_message}\n")
                f.write("\n")
    
    print(f"💬 對話記錄已儲存: {conversation_file}")


def print_summary(all_results: Dict[str, List[TestResult]]):
    """打印測試摘要"""
    print("\n" + "="*80)
    print("📊 測試摘要")
    print("="*80)
    
    total_passed = 0
    total_failed = 0
    total_time = 0
    
    for suite_name, results in all_results.items():
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        avg_time = sum(r.response_time_ms for r in results) / len(results) if results else 0
        
        total_passed += passed
        total_failed += failed
        total_time += sum(r.response_time_ms for r in results)
        
        status = "✅" if failed == 0 else "⚠️" if passed > failed else "❌"
        print(f"{status} {suite_name}: {passed}/{len(results)} 通過 (平均 {avg_time:.0f}ms)")
    
    print("-"*80)
    total = total_passed + total_failed
    success_rate = (total_passed / total * 100) if total > 0 else 0
    print(f"📈 總計: {total_passed}/{total} 通過 ({success_rate:.1f}%)")
    print(f"⏱️  總耗時: {total_time/1000:.1f} 秒")
    
    # 列出失敗的測試
    failed_tests = []
    for suite_name, results in all_results.items():
        for r in results:
            if not r.passed:
                failed_tests.append((suite_name, r))
    
    if failed_tests:
        print("\n" + "="*80)
        print("❌ 失敗的測試清單")
        print("="*80)
        for suite_name, result in failed_tests:
            print(f"\n[{suite_name}] {result.test_case.name}")
            print(f"    查詢: {result.test_case.query[:60]}...")
            print(f"    錯誤: {result.error_message}")


def main():
    """主程式"""
    parser = argparse.ArgumentParser(description='SAF Smart Query 情境測試')
    parser.add_argument('--suite', type=int, help='只執行指定的測試套件 (1-9)')
    parser.add_argument('--verbose', '-v', action='store_true', help='顯示詳細輸出')
    parser.add_argument('--no-save', action='store_true', help='不儲存測試結果到檔案')
    args = parser.parse_args()
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    print("🚀 SAF Smart Query 情境測試")
    print(f"📅 測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API 端點: {API_URL}")
    
    # 先測試 API 是否可用
    print("\n🔍 檢查 API 連線...")
    try:
        response = requests.post(
            API_URL,
            headers={"Content-Type": "application/json"},
            json={"query": "test"},
            timeout=30  # 增加超時時間，因為第一次請求可能較慢
        )
        if response.status_code == 200:
            print(f"   ✅ API 連線正常")
        else:
            print(f"   ⚠️ API 返回狀態碼: {response.status_code}")
    except Exception as e:
        print(f"   ❌ API 無法連線: {e}")
        print("   請確認 Django 服務是否正在運行")
        return False
    
    # 選擇要執行的測試套件
    if args.suite:
        if 1 <= args.suite <= len(ALL_TEST_SUITES):
            test_suites = [ALL_TEST_SUITES[args.suite - 1]]
        else:
            print(f"❌ 無效的測試套件編號: {args.suite} (有效範圍: 1-{len(ALL_TEST_SUITES)})")
            return False
    else:
        test_suites = ALL_TEST_SUITES
    
    # 執行測試
    all_results = {}
    for suite_name, test_cases in test_suites:
        results = run_test_suite(suite_name, test_cases, args.verbose)
        all_results[suite_name] = results
    
    # 打印摘要
    print_summary(all_results)
    
    # 儲存結果
    if not args.no_save:
        save_results_to_file(all_results, timestamp)
    
    # 返回是否全部通過
    total_failed = sum(
        1 for results in all_results.values() 
        for r in results if not r.passed
    )
    
    return total_failed == 0


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
