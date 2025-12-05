#!/usr/bin/env python3
"""
SAF Smart Query Phase 3 測試摘要意圖測試
==========================================

專門測試 Phase 3 新增的三種測試摘要意圖：
1. query_project_test_summary - 專案測試總覽
2. query_project_test_by_category - 按類別查詢測試
3. query_project_test_by_capacity - 按容量查詢測試

執行方式：
    # 在容器內執行
    docker exec ai-django python tests/test_saf_smart_query/test_test_summary_intent.py
    
    # 測試特定意圖
    docker exec ai-django python tests/test_saf_smart_query/test_test_summary_intent.py --intent summary
    docker exec ai-django python tests/test_saf_smart_query/test_test_summary_intent.py --intent category
    docker exec ai-django python tests/test_saf_smart_query/test_test_summary_intent.py --intent capacity
    
    # 詳細輸出
    docker exec ai-django python tests/test_saf_smart_query/test_test_summary_intent.py --verbose

作者：AI Platform Team
創建日期：2025-12-06
版本：1.0 (Phase 3)
"""

import os
import sys
import json
import argparse
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 設定 Django 環境
# 注意：在容器中路徑為 /app，在本地為 .../backend
import sys
import os

# 確定 backend 路徑
script_dir = os.path.dirname(os.path.abspath(__file__))
# 嘗試從 tests/test_saf_smart_query 找到 backend
possible_paths = [
    os.path.join(script_dir, '..', '..', 'backend'),  # 本地：tests/test_saf_smart_query -> backend
    '/app',  # 容器內
]

for path in possible_paths:
    if os.path.exists(os.path.join(path, 'manage.py')):
        sys.path.insert(0, path)
        break

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

from library.saf_integration.smart_query.intent_analyzer import SAFIntentAnalyzer
from library.saf_integration.smart_query.intent_types import (
    IntentType, 
    KNOWN_TEST_CATEGORIES, 
    KNOWN_CAPACITIES
)


# ============================================================
# 測試案例定義
# ============================================================

@dataclass
class IntentTestCase:
    """意圖測試案例"""
    name: str                           # 測試名稱
    query: str                          # 用戶問題
    expected_intent: IntentType         # 預期意圖
    expected_params: Dict[str, Any]     # 預期參數
    min_confidence: float = 0.5         # 最低信心度
    description: str = ""               # 測試說明


@dataclass  
class IntentTestResult:
    """意圖測試結果"""
    test_case: IntentTestCase
    passed: bool
    actual_intent: str
    actual_params: Dict[str, Any]
    actual_confidence: float
    intent_matched: bool
    params_matched: bool
    confidence_ok: bool
    error_message: Optional[str] = None


# ============================================================
# 測試案例：query_project_test_summary
# ============================================================
TEST_SUMMARY_CASES = [
    IntentTestCase(
        name="測試摘要_標準查詢",
        query="DEMETER 的測試結果如何？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "DEMETER"},
        min_confidence=0.7,
        description="標準測試結果查詢"
    ),
    IntentTestCase(
        name="測試摘要_通過數量",
        query="APOLLO 有多少測試通過？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "APOLLO"},
        min_confidence=0.7,
        description="詢問通過數量"
    ),
    IntentTestCase(
        name="測試摘要_失敗數量",
        query="TITAN 有多少測試失敗？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "TITAN"},
        min_confidence=0.7,
        description="詢問失敗數量"
    ),
    IntentTestCase(
        name="測試摘要_測試狀況",
        query="Garuda 專案測試狀況如何",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "Garuda"},
        min_confidence=0.6,
        description="測試狀況查詢"
    ),
    IntentTestCase(
        name="測試摘要_測試進度",
        query="PHOENIX 專案的測試進度",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "PHOENIX"},
        min_confidence=0.6,
        description="測試進度查詢"
    ),
    IntentTestCase(
        name="測試摘要_口語化",
        query="想了解一下 VULCAN 測試跑得怎麼樣",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "VULCAN"},
        min_confidence=0.5,
        description="口語化查詢"
    ),
    IntentTestCase(
        name="測試摘要_英文問法",
        query="What's the test status of DEMETER?",
        expected_intent=IntentType.QUERY_PROJECT_TEST_SUMMARY,
        expected_params={"project_name": "DEMETER"},
        min_confidence=0.5,
        description="英文問法"
    ),
]

# ============================================================
# 測試案例：query_project_test_by_category
# ============================================================
TEST_BY_CATEGORY_CASES = [
    IntentTestCase(
        name="類別測試_Compliance",
        query="TITAN 的 Compliance 測試結果",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "TITAN", "category": "Compliance"},
        min_confidence=0.7,
        description="Compliance 類別查詢"
    ),
    IntentTestCase(
        name="類別測試_Performance",
        query="DEMETER 專案的效能測試如何？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "DEMETER", "category": "Performance"},
        min_confidence=0.7,
        description="Performance 類別查詢"
    ),
    IntentTestCase(
        name="類別測試_Interoperability",
        query="APOLLO 的相容性測試結果",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "APOLLO", "category": "Compatibility"},
        min_confidence=0.6,
        description="相容性測試查詢（中文'相容性'對應 Compatibility）"
    ),
    IntentTestCase(
        name="類別測試_Stress",
        query="Garuda 專案壓力測試跑了多少",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "Garuda", "category": "Stress"},
        min_confidence=0.6,
        description="Stress 類別查詢"
    ),
    IntentTestCase(
        name="類別測試_Functional",
        query="PHOENIX 的功能測試結果如何",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "PHOENIX", "category": "Functionality"},
        min_confidence=0.6,
        description="功能測試查詢（中文'功能測試'對應 Functionality）"
    ),
    IntentTestCase(
        name="類別測試_Interop_英文",
        query="VULCAN 專案的 Interoperability 測試狀況",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "VULCAN", "category": "Interoperability"},
        min_confidence=0.6,
        description="Interoperability 英文關鍵字查詢"
    ),
    IntentTestCase(
        name="類別測試_中文相容性",
        query="TITAN 的相容測試做得如何？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "TITAN", "category": "Compatibility"},
        min_confidence=0.5,
        description="中文口語化相容測試查詢"
    ),
    IntentTestCase(
        name="類別測試_帶數量",
        query="DEMETER 的 Compliance 項目通過了幾個？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CATEGORY,
        expected_params={"project_name": "DEMETER", "category": "Compliance"},
        min_confidence=0.6,
        description="帶數量詢問的類別查詢"
    ),
]

# ============================================================
# 測試案例：query_project_test_by_capacity
# ============================================================
TEST_BY_CAPACITY_CASES = [
    IntentTestCase(
        name="容量測試_1TB",
        query="APOLLO 1TB 的測試狀況",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "APOLLO", "capacity": "1TB"},
        min_confidence=0.7,
        description="1TB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_512GB",
        query="TITAN 512GB 測試結果",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "TITAN", "capacity": "512GB"},
        min_confidence=0.7,
        description="512GB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_2TB",
        query="DEMETER 2TB 版本測試如何？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "DEMETER", "capacity": "2TB"},
        min_confidence=0.7,
        description="2TB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_256GB",
        query="Garuda 專案 256GB 的測試進度",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "Garuda", "capacity": "256GB"},
        min_confidence=0.6,
        description="256GB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_4TB",
        query="PHOENIX 4TB 測試結果如何",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "PHOENIX", "capacity": "4TB"},
        min_confidence=0.6,
        description="4TB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_128GB",
        query="VULCAN 128GB 的測試狀況",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "VULCAN", "capacity": "128GB"},
        min_confidence=0.6,
        description="128GB 容量查詢"
    ),
    IntentTestCase(
        name="容量測試_口語一T",
        query="想看 TITAN 一T版本的測試",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "TITAN", "capacity": "1TB"},
        min_confidence=0.5,
        description="口語化（一T = 1TB）"
    ),
    IntentTestCase(
        name="容量測試_帶數量",
        query="APOLLO 2TB 有多少測試通過？",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "APOLLO", "capacity": "2TB"},
        min_confidence=0.6,
        description="帶數量詢問的容量查詢"
    ),
    IntentTestCase(
        name="容量測試_8TB",
        query="DEMETER 8TB 的測試進度",
        expected_intent=IntentType.QUERY_PROJECT_TEST_BY_CAPACITY,
        expected_params={"project_name": "DEMETER", "capacity": "8TB"},
        min_confidence=0.6,
        description="8TB 大容量查詢"
    ),
]


# ============================================================
# 測試執行器
# ============================================================

class TestSummaryIntentTester:
    """測試摘要意圖測試器"""
    
    def __init__(self, verbose: bool = False):
        self.analyzer = SAFIntentAnalyzer()
        self.verbose = verbose
        self.results: List[IntentTestResult] = []
    
    def run_single_test(self, test_case: IntentTestCase) -> IntentTestResult:
        """執行單一測試"""
        try:
            # 執行意圖分析
            analysis_result = self.analyzer.analyze(test_case.query)
            
            # IntentResult 是資料類別，使用屬性而非 dict.get()
            raw_intent = analysis_result.intent if hasattr(analysis_result, 'intent') else ''
            actual_params = analysis_result.parameters if hasattr(analysis_result, 'parameters') else {}
            actual_confidence = analysis_result.confidence if hasattr(analysis_result, 'confidence') else 0.0
            
            # 處理 IntentType 列舉：取其 .value 或轉字串
            if hasattr(raw_intent, 'value'):
                actual_intent = raw_intent.value
            else:
                actual_intent = str(raw_intent)
            
            # 驗證意圖
            intent_matched = actual_intent == test_case.expected_intent.value
            
            # 驗證參數（部分匹配）
            params_matched = all(
                actual_params.get(k) == v 
                for k, v in test_case.expected_params.items()
            )
            
            # 驗證信心度
            confidence_ok = actual_confidence >= test_case.min_confidence
            
            # 整體通過
            passed = intent_matched and params_matched and confidence_ok
            
            return IntentTestResult(
                test_case=test_case,
                passed=passed,
                actual_intent=actual_intent,
                actual_params=actual_params,
                actual_confidence=actual_confidence,
                intent_matched=intent_matched,
                params_matched=params_matched,
                confidence_ok=confidence_ok
            )
            
        except Exception as e:
            return IntentTestResult(
                test_case=test_case,
                passed=False,
                actual_intent="",
                actual_params={},
                actual_confidence=0.0,
                intent_matched=False,
                params_matched=False,
                confidence_ok=False,
                error_message=str(e)
            )
    
    def run_test_suite(self, 
                       suite_name: str, 
                       test_cases: List[IntentTestCase]) -> List[IntentTestResult]:
        """執行測試套件"""
        print(f"\n{'=' * 60}")
        print(f"📋 {suite_name}")
        print(f"{'=' * 60}")
        
        suite_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            result = self.run_single_test(test_case)
            suite_results.append(result)
            self.results.append(result)
            
            # 顯示結果
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"\n{i}. {test_case.name} - {status}")
            print(f"   Query: \"{test_case.query}\"")
            
            if self.verbose or not result.passed:
                print(f"   Expected: {test_case.expected_intent.value}")
                print(f"   Actual:   {result.actual_intent}")
                print(f"   Expected Params: {test_case.expected_params}")
                print(f"   Actual Params:   {result.actual_params}")
                print(f"   Confidence: {result.actual_confidence:.2f} (min: {test_case.min_confidence})")
                
                if not result.intent_matched:
                    print(f"   ⚠️ Intent mismatch!")
                if not result.params_matched:
                    print(f"   ⚠️ Params mismatch!")
                if not result.confidence_ok:
                    print(f"   ⚠️ Confidence too low!")
                if result.error_message:
                    print(f"   ❌ Error: {result.error_message}")
        
        # 套件統計
        passed_count = sum(1 for r in suite_results if r.passed)
        total_count = len(suite_results)
        print(f"\n📊 {suite_name} 結果: {passed_count}/{total_count} 通過")
        
        return suite_results
    
    def run_all_tests(self, intent_filter: Optional[str] = None) -> Dict[str, Any]:
        """執行所有測試"""
        print("\n" + "=" * 70)
        print("🧪 SAF Smart Query Phase 3 - 測試摘要意圖測試")
        print("=" * 70)
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 顯示已知的測試類別和容量
        print(f"\n📁 已知測試類別 ({len(KNOWN_TEST_CATEGORIES)}):")
        print(f"   {', '.join(KNOWN_TEST_CATEGORIES)}")
        print(f"\n💾 已知容量規格 ({len(KNOWN_CAPACITIES)}):")
        print(f"   {', '.join(KNOWN_CAPACITIES)}")
        
        # 根據過濾器選擇測試套件
        test_suites = []
        
        if intent_filter is None or intent_filter == 'summary':
            test_suites.append(("測試摘要（總覽）", TEST_SUMMARY_CASES))
        
        if intent_filter is None or intent_filter == 'category':
            test_suites.append(("按類別查詢測試", TEST_BY_CATEGORY_CASES))
        
        if intent_filter is None or intent_filter == 'capacity':
            test_suites.append(("按容量查詢測試", TEST_BY_CAPACITY_CASES))
        
        # 執行測試
        for suite_name, test_cases in test_suites:
            self.run_test_suite(suite_name, test_cases)
        
        # 總結
        return self.print_summary()
    
    def print_summary(self) -> Dict[str, Any]:
        """打印測試總結"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        
        print("\n" + "=" * 70)
        print("📊 測試總結")
        print("=" * 70)
        print(f"總測試數: {total}")
        print(f"通過: {passed} ({passed/total*100:.1f}%)")
        print(f"失敗: {failed} ({failed/total*100:.1f}%)")
        
        # 按意圖類型分類統計
        intent_stats = {}
        for result in self.results:
            intent = result.test_case.expected_intent.value
            if intent not in intent_stats:
                intent_stats[intent] = {'total': 0, 'passed': 0}
            intent_stats[intent]['total'] += 1
            if result.passed:
                intent_stats[intent]['passed'] += 1
        
        print("\n📈 按意圖類型統計:")
        for intent, stats in intent_stats.items():
            rate = stats['passed'] / stats['total'] * 100
            print(f"   {intent}: {stats['passed']}/{stats['total']} ({rate:.1f}%)")
        
        # 列出失敗的測試
        if failed > 0:
            print("\n❌ 失敗的測試:")
            for result in self.results:
                if not result.passed:
                    print(f"   - {result.test_case.name}: {result.test_case.query}")
                    if result.error_message:
                        print(f"     Error: {result.error_message}")
                    elif not result.intent_matched:
                        print(f"     Expected: {result.test_case.expected_intent.value}, Got: {result.actual_intent}")
                    elif not result.params_matched:
                        print(f"     Expected params: {result.test_case.expected_params}, Got: {result.actual_params}")
        
        print("\n" + "=" * 70)
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'pass_rate': passed / total * 100 if total > 0 else 0,
            'intent_stats': intent_stats
        }
    
    def save_results(self, timestamp: str, intent_filter: Optional[str] = None):
        """將測試結果儲存到檔案"""
        # 確定結果目錄
        script_dir = os.path.dirname(os.path.abspath(__file__))
        results_dir = os.path.join(script_dir, 'results')
        os.makedirs(results_dir, exist_ok=True)
        
        # 檔案名稱包含過濾條件
        filter_suffix = f"_{intent_filter}" if intent_filter else "_all"
        
        # 1. 儲存 JSON 結果
        json_file = os.path.join(results_dir, f"phase3_test_{timestamp}{filter_suffix}.json")
        
        json_data = {
            "test_type": "SAF Smart Query Phase 3 Intent Test",
            "timestamp": timestamp,
            "filter": intent_filter or "all",
            "summary": {
                "total": len(self.results),
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
            },
            "results": []
        }
        
        for r in self.results:
            json_data["results"].append({
                "name": r.test_case.name,
                "query": r.test_case.query,
                "description": r.test_case.description,
                "expected_intent": r.test_case.expected_intent.value,
                "expected_params": r.test_case.expected_params,
                "min_confidence": r.test_case.min_confidence,
                "actual_intent": r.actual_intent,
                "actual_params": r.actual_params,
                "actual_confidence": r.actual_confidence,
                "passed": r.passed,
                "intent_matched": r.intent_matched,
                "params_matched": r.params_matched,
                "confidence_ok": r.confidence_ok,
                "error_message": r.error_message
            })
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"📄 JSON 結果已儲存: {json_file}")
        
        # 2. 儲存 Markdown 報告
        md_file = os.path.join(results_dir, f"phase3_report_{timestamp}{filter_suffix}.md")
        
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write("# SAF Smart Query Phase 3 意圖測試報告\n\n")
            f.write(f"**測試時間**: {timestamp}\n\n")
            f.write(f"**測試範圍**: {intent_filter or '全部'}\n\n")
            f.write("---\n\n")
            
            # 統計
            total = len(self.results)
            passed = sum(1 for r in self.results if r.passed)
            f.write("## 📊 總覽\n\n")
            f.write(f"- **總測試數**: {total}\n")
            f.write(f"- **通過**: {passed}\n")
            f.write(f"- **失敗**: {total - passed}\n")
            f.write(f"- **通過率**: {passed/total*100:.1f}%\n\n")
            
            # 按意圖類型統計
            f.write("## 📈 按意圖類型統計\n\n")
            f.write("| 意圖類型 | 通過 | 失敗 | 通過率 |\n")
            f.write("|---------|------|------|--------|\n")
            
            intent_stats = {}
            for r in self.results:
                intent = r.test_case.expected_intent.value
                if intent not in intent_stats:
                    intent_stats[intent] = {'passed': 0, 'failed': 0}
                if r.passed:
                    intent_stats[intent]['passed'] += 1
                else:
                    intent_stats[intent]['failed'] += 1
            
            for intent, stats in intent_stats.items():
                total_intent = stats['passed'] + stats['failed']
                rate = stats['passed'] / total_intent * 100 if total_intent > 0 else 0
                f.write(f"| `{intent}` | {stats['passed']} | {stats['failed']} | {rate:.1f}% |\n")
            
            f.write("\n---\n\n")
            
            # 詳細測試結果
            f.write("## 📋 詳細測試結果\n\n")
            
            for r in self.results:
                status = "✅" if r.passed else "❌"
                f.write(f"### {status} {r.test_case.name}\n\n")
                f.write(f"**說明**: {r.test_case.description}\n\n")
                f.write(f"**用戶問題**:\n```\n{r.test_case.query}\n```\n\n")
                f.write("**分析結果**:\n")
                f.write(f"- 意圖: `{r.actual_intent}` (預期: `{r.test_case.expected_intent.value}`)\n")
                f.write(f"- 參數: `{r.actual_params}` (預期: `{r.test_case.expected_params}`)\n")
                f.write(f"- 信心度: {r.actual_confidence:.2f} (最低: {r.test_case.min_confidence})\n")
                
                if not r.passed:
                    f.write(f"\n**失敗原因**:\n")
                    if not r.intent_matched:
                        f.write(f"- ⚠️ 意圖不匹配\n")
                    if not r.params_matched:
                        f.write(f"- ⚠️ 參數不匹配\n")
                    if not r.confidence_ok:
                        f.write(f"- ⚠️ 信心度過低\n")
                    if r.error_message:
                        f.write(f"- ❌ 錯誤: {r.error_message}\n")
                
                f.write("\n---\n\n")
        
        print(f"📝 Markdown 報告已儲存: {md_file}")
        
        return json_file, md_file


# ============================================================
# 主程式
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description='SAF Smart Query Phase 3 測試摘要意圖測試'
    )
    parser.add_argument(
        '--intent', 
        choices=['summary', 'category', 'capacity'],
        help='只測試特定意圖類型'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='顯示詳細輸出'
    )
    parser.add_argument(
        '--save', '-s',
        action='store_true',
        help='儲存測試結果到 results/ 目錄'
    )
    parser.add_argument(
        '--no-save',
        action='store_true',
        help='不儲存測試結果（預設會儲存）'
    )
    
    args = parser.parse_args()
    
    # 產生時間戳記
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 執行測試
    tester = TestSummaryIntentTester(verbose=args.verbose)
    results = tester.run_all_tests(intent_filter=args.intent)
    
    # 儲存結果（預設儲存，除非指定 --no-save）
    if not args.no_save:
        tester.save_results(timestamp, intent_filter=args.intent)
    
    # 設定退出碼
    if results['failed'] > 0:
        sys.exit(1)
    sys.exit(0)


if __name__ == '__main__':
    main()
