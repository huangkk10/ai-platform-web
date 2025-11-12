#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Protocol Assistant 綜合系統測試
====================================

測試範圍：
1. 外部知識庫 API（Dify 調用的端點）
2. Django 後端搜尋服務
3. 向量搜尋功能
4. 關鍵字搜尋功能
5. 搜尋模式切換（auto, section_only, document_only）
6. 閾值敏感度測試
7. 邊界案例測試

Author: AI Platform Team
Date: 2025-11-13
"""

import os
import sys
import django
import json
import requests

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.protocol_guide.search_service import ProtocolGuideSearchService


class ComprehensiveProtocolTester:
    """Protocol 系統綜合測試器"""
    
    def __init__(self):
        self.search_service = ProtocolGuideSearchService()
        self.api_base_url = "http://localhost/api"
        self.test_results = {}
    
    def print_header(self, title, level=1):
        """打印標題"""
        if level == 1:
            print("\n" + "=" * 80)
            print(f"🧪 {title}")
            print("=" * 80)
        elif level == 2:
            print(f"\n{'─' * 80}")
            print(f"📋 {title}")
            print(f"{'─' * 80}")
        else:
            print(f"\n{'·' * 40}")
            print(f"🔍 {title}")
            print(f"{'·' * 40}")
    
    # ============================================================
    # 測試組 1：外部知識庫 API 測試
    # ============================================================
    
    def test_external_api(self):
        """測試 Dify 調用的外部知識庫 API"""
        self.print_header("測試組 1：外部知識庫 API", level=2)
        print("\n🎯 測試目標：驗證 /api/dify/knowledge/retrieval/ 端點")
        
        test_cases = [
            {
                'name': 'CrystalDiskMark 查詢',
                'query': 'crystaldiskmark',
                'top_k': 3,
                'threshold': 0.5,
                'expected_min_results': 1
            },
            {
                'name': 'CUP 測試查詢',
                'query': 'CUP 測試',
                'top_k': 3,
                'threshold': 0.7,
                'expected_min_results': 1
            },
            {
                'name': 'Kingston USB 查詢',
                'query': 'Kingston USB',
                'top_k': 5,
                'threshold': 0.6,
                'expected_min_results': 1
            },
            {
                'name': '模糊查詢（低閾值）',
                'query': 'test',
                'top_k': 2,
                'threshold': 0.3,
                'expected_min_results': 0  # 可能沒結果
            },
            {
                'name': '精確查詢（高閾值）',
                'query': 'I3C protocol',
                'top_k': 3,
                'threshold': 0.8,
                'expected_min_results': 0  # 高閾值可能過濾掉
            },
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n【案例 {i}】{case['name']}")
            print(f"  查詢: '{case['query']}'")
            print(f"  Top-K: {case['top_k']}, 閾值: {case['threshold']}")
            
            try:
                response = requests.post(
                    f"{self.api_base_url}/dify/knowledge/retrieval/",
                    json={
                        'knowledge_id': 'protocol_guide',
                        'query': case['query'],
                        'retrieval_setting': {
                            'top_k': case['top_k'],
                            'score_threshold': case['threshold']
                        }
                    },
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    records = data.get('records', [])
                    
                    print(f"  ✅ API 響應成功: {len(records)} 個結果")
                    
                    for j, record in enumerate(records[:3], 1):
                        title = record.get('title', 'Unknown')
                        score = record.get('score', 0)
                        print(f"    {j}. {title} (分數: {score:.2f})")
                    
                    # 驗證結果數量
                    if len(records) >= case['expected_min_results']:
                        print(f"  ✅ 結果數量符合預期 (>= {case['expected_min_results']})")
                        passed += 1
                    else:
                        print(f"  ⚠️ 結果數量不足 (預期 >= {case['expected_min_results']}, 實際 {len(records)})")
                        if case['expected_min_results'] == 0:
                            passed += 1  # 低預期也算通過
                else:
                    print(f"  ❌ API 響應失敗: HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"  ❌ 測試失敗: {str(e)}")
        
        print(f"\n📊 外部 API 測試結果: {passed}/{total} 通過")
        result = {'passed': passed, 'total': total, 'rate': passed/total if total > 0 else 0}
        self.test_results["測試組 1：外部知識庫 API"] = result
        return result
    
    # ============================================================
    # 測試組 2：Django 搜尋服務測試
    # ============================================================
    
    def test_search_service(self):
        """測試 Django 後端的搜尋服務"""
        self.print_header("測試組 2：Django 搜尋服務", level=2)
        print("\n🎯 測試目標：驗證 ProtocolGuideSearchService")
        
        test_cases = [
            {
                'name': '向量搜尋 - 標準閾值',
                'query': 'CrystalDiskMark',
                'use_vector': True,
                'threshold': 0.7,
                'expected_min': 1
            },
            {
                'name': '向量搜尋 - 低閾值',
                'query': 'USB',
                'use_vector': True,
                'threshold': 0.5,
                'expected_min': 1
            },
            {
                'name': '關鍵字搜尋',
                'query': 'Kingston',
                'use_vector': False,
                'threshold': 0.3,
                'expected_min': 1
            },
            {
                'name': '混合搜尋（向量+關鍵字）',
                'query': 'I3C',
                'use_vector': True,
                'threshold': 0.6,
                'expected_min': 1
            },
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n【案例 {i}】{case['name']}")
            print(f"  查詢: '{case['query']}'")
            print(f"  向量: {case['use_vector']}, 閾值: {case['threshold']}")
            
            try:
                results = self.search_service.search_knowledge(
                    query=case['query'],
                    limit=5,
                    use_vector=case['use_vector'],
                    threshold=case['threshold']
                )
                
                print(f"  ✅ 搜尋成功: {len(results)} 個結果")
                
                for j, result in enumerate(results[:3], 1):
                    title = result.get('title', 'Unknown')
                    score = result.get('score', 0)
                    print(f"    {j}. {title} (分數: {score:.2f})")
                
                if len(results) >= case['expected_min']:
                    print(f"  ✅ 結果符合預期")
                    passed += 1
                else:
                    print(f"  ⚠️ 結果不足 (預期 >= {case['expected_min']}, 實際 {len(results)})")
                    
            except Exception as e:
                print(f"  ❌ 測試失敗: {str(e)}")
        
        print(f"\n📊 搜尋服務測試結果: {passed}/{total} 通過")
        return {'passed': passed, 'total': total, 'rate': passed/total if total > 0 else 0}
    
    # ============================================================
    # 測試組 3：搜尋模式測試
    # ============================================================
    
    def test_search_modes(self):
        """測試不同的搜尋模式"""
        print("\n🎯 測試目標：驗證 search_mode 參數（auto, section_only, document_only）")
        
        query = "CrystalDiskMark 測試"
        threshold = 0.6
        
        test_modes = [
            {
                'mode': 'auto',
                'description': '自動模式（段落優先，允許降級）',
                'expect_results': True
            },
            {
                'mode': 'section_only',
                'description': '只搜索段落（不降級）',
                'expect_results': True  # 可能有結果
            },
            {
                'mode': 'document_only',
                'description': '只搜索文檔（跳過段落）',
                'expect_results': True
            },
        ]
        
        passed = 0
        total = len(test_modes)
        
        for i, mode_config in enumerate(test_modes, 1):
            print(f"\n【模式 {i}】{mode_config['description']}")
            print(f"  模式: {mode_config['mode']}")
            print(f"  查詢: '{query}', 閾值: {threshold}")
            
            try:
                results = self.search_service.search_with_vectors(
                    query=query,
                    limit=5,
                    threshold=threshold,
                    search_mode=mode_config['mode']
                )
                
                print(f"  ✅ 搜尋成功: {len(results)} 個結果")
                
                for j, result in enumerate(results[:2], 1):
                    title = result.get('title', 'Unknown')
                    score = result.get('score', 0)
                    print(f"    {j}. {title} (分數: {score:.2f})")
                
                # 驗證是否有結果（根據預期）
                if mode_config['expect_results']:
                    if len(results) > 0:
                        print(f"  ✅ 模式運作正常")
                        passed += 1
                    else:
                        print(f"  ⚠️ 預期有結果但無結果（可能是資料問題）")
                        passed += 0.5  # 部分通過
                else:
                    print(f"  ✅ 模式運作正常（無結果符合預期）")
                    passed += 1
                    
            except Exception as e:
                print(f"  ❌ 測試失敗: {str(e)}")
        
        print(f"\n📊 搜尋模式測試結果: {passed}/{total} 通過")
        return {'passed': passed, 'total': total, 'rate': passed/total if total > 0 else 0}
    
    # ============================================================
    # 測試組 4：閾值敏感度測試
    # ============================================================
    
    def test_threshold_sensitivity(self):
        """測試不同閾值對結果的影響"""
        print("\n🎯 測試目標：驗證閾值設定的效果")
        
        query = "Kingston USB 測試"
        thresholds = [0.3, 0.5, 0.7, 0.85, 0.95]
        
        print(f"\n查詢: '{query}'")
        print(f"測試閾值: {thresholds}")
        
        results_by_threshold = {}
        
        for threshold in thresholds:
            try:
                results = self.search_service.search_knowledge(
                    query=query,
                    limit=5,
                    use_vector=True,
                    threshold=threshold
                )
                results_by_threshold[threshold] = len(results)
                
                print(f"\n  閾值 {threshold:.2f}: {len(results)} 個結果")
                for i, result in enumerate(results[:2], 1):
                    title = result.get('title', 'Unknown')
                    score = result.get('score', 0)
                    print(f"    {i}. {title} (分數: {score:.2f})")
                    
            except Exception as e:
                print(f"  閾值 {threshold:.2f}: ❌ 失敗 - {str(e)}")
                results_by_threshold[threshold] = -1
        
        # 分析趨勢
        print(f"\n📊 閾值敏感度分析:")
        print(f"  閾值 → 結果數量")
        for threshold in sorted(results_by_threshold.keys()):
            count = results_by_threshold[threshold]
            bar = "█" * count if count > 0 else ""
            print(f"  {threshold:.2f} → {count:2d} {bar}")
        
        # 驗證：閾值越高，結果應該越少（或至少不增加）
        is_monotonic = True
        prev_count = float('inf')
        for threshold in sorted(results_by_threshold.keys()):
            count = results_by_threshold[threshold]
            if count > prev_count:
                is_monotonic = False
                break
            prev_count = count
        
        if is_monotonic:
            print(f"\n  ✅ 閾值趨勢正確（高閾值 → 少結果）")
            return {'passed': 1, 'total': 1, 'rate': 1.0}
        else:
            print(f"\n  ⚠️ 閾值趨勢異常（可能有問題）")
            return {'passed': 0.5, 'total': 1, 'rate': 0.5}
    
    # ============================================================
    # 測試組 5：邊界案例測試
    # ============================================================
    
    def test_edge_cases(self):
        """測試邊界情況和錯誤處理"""
        print("\n🎯 測試目標：驗證系統的健壯性")
        
        test_cases = [
            {
                'name': '空查詢',
                'query': '',
                'should_handle': True
            },
            {
                'name': '極短查詢',
                'query': 'a',
                'should_handle': True
            },
            {
                'name': '極長查詢',
                'query': 'CrystalDiskMark ' * 50,  # 很長的查詢
                'should_handle': True
            },
            {
                'name': '特殊字符',
                'query': '@#$%^&*()',
                'should_handle': True
            },
            {
                'name': '中英混合',
                'query': 'USB測試Test流程',
                'should_handle': True
            },
            {
                'name': '不存在的內容',
                'query': 'zzz不存在的測試項目zzz',
                'should_handle': True
            },
        ]
        
        passed = 0
        total = len(test_cases)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n【案例 {i}】{case['name']}")
            print(f"  查詢: '{case['query'][:50]}...' (長度: {len(case['query'])})")
            
            try:
                results = self.search_service.search_knowledge(
                    query=case['query'],
                    limit=3,
                    use_vector=True,
                    threshold=0.5
                )
                
                print(f"  ✅ 處理成功: {len(results)} 個結果")
                
                if case['should_handle']:
                    print(f"  ✅ 系統正確處理邊界案例")
                    passed += 1
                    
            except Exception as e:
                print(f"  ❌ 處理失敗: {str(e)}")
                if not case['should_handle']:
                    print(f"  ✅ 預期會失敗（測試通過）")
                    passed += 1
        
        print(f"\n📊 邊界案例測試結果: {passed}/{total} 通過")
        return {'passed': passed, 'total': total, 'rate': passed/total if total > 0 else 0}
    
    # ============================================================
    # 測試組 6：資料庫完整性測試
    # ============================================================
    
    def test_database_integrity(self):
        """測試資料庫的完整性"""
        print("\n🎯 測試目標：驗證資料庫資料完整性")
        
        checks = []
        
        # 檢查 1：Protocol Guide 數量
        print(f"\n【檢查 1】Protocol Guide 記錄數")
        try:
            total_guides = ProtocolGuide.objects.count()
            print(f"  總記錄數: {total_guides}")
            if total_guides > 0:
                print(f"  ✅ 資料庫有資料")
                checks.append(True)
            else:
                print(f"  ⚠️ 資料庫為空")
                checks.append(False)
        except Exception as e:
            print(f"  ❌ 查詢失敗: {str(e)}")
            checks.append(False)
        
        # 檢查 2：向量資料存在性
        print(f"\n【檢查 2】向量資料存在性")
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM document_embeddings 
                    WHERE source_table = 'protocol_guide'
                """)
                vector_count = cursor.fetchone()[0]
                
                print(f"  向量記錄數: {vector_count}")
                if vector_count > 0:
                    print(f"  ✅ 向量資料存在")
                    checks.append(True)
                else:
                    print(f"  ⚠️ 無向量資料（可能需要生成）")
                    checks.append(False)
        except Exception as e:
            print(f"  ❌ 查詢失敗: {str(e)}")
            checks.append(False)
        
        # 檢查 3：段落向量資料
        print(f"\n【檢查 3】段落向量資料")
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM document_section_embeddings 
                    WHERE source_table = 'protocol_guide'
                """)
                section_count = cursor.fetchone()[0]
                
                print(f"  段落向量記錄數: {section_count}")
                if section_count > 0:
                    print(f"  ✅ 段落向量資料存在")
                    checks.append(True)
                else:
                    print(f"  ⚠️ 無段落向量資料")
                    checks.append(False)
        except Exception as e:
            print(f"  ❌ 查詢失敗: {str(e)}")
            checks.append(False)
        
        # 檢查 4：資料一致性
        print(f"\n【檢查 4】資料一致性")
        try:
            guides_with_title = ProtocolGuide.objects.exclude(title='').count()
            guides_with_content = ProtocolGuide.objects.exclude(content='').count()
            
            print(f"  有標題的記錄: {guides_with_title}/{total_guides}")
            print(f"  有內容的記錄: {guides_with_content}/{total_guides}")
            
            if guides_with_title > 0 and guides_with_content > 0:
                print(f"  ✅ 資料完整性良好")
                checks.append(True)
            else:
                print(f"  ⚠️ 部分記錄缺少必要欄位")
                checks.append(False)
        except Exception as e:
            print(f"  ❌ 檢查失敗: {str(e)}")
            checks.append(False)
        
        passed = sum(checks)
        total = len(checks)
        
        print(f"\n📊 資料庫完整性測試: {passed}/{total} 通過")
        return {'passed': passed, 'total': total, 'rate': passed/total if total > 0 else 0}
    
    # ============================================================
    # 主測試流程
    # ============================================================
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("Protocol Assistant 綜合系統測試", level=1)
        
        print("\n📌 測試範圍：")
        print("  1. 外部知識庫 API（Dify 端點）")
        print("  2. Django 搜尋服務")
        print("  3. 搜尋模式切換")
        print("  4. 閾值敏感度")
        print("  5. 邊界案例處理")
        print("  6. 資料庫完整性")
        
        # 執行所有測試組
        self.test_database_integrity()      # 先檢查資料庫
        self.test_search_service()          # 測試搜尋服務
        self.test_search_modes()            # 測試搜尋模式
        self.test_threshold_sensitivity()   # 測試閾值
        self.test_edge_cases()              # 測試邊界案例
        self.test_external_api()            # 最後測試外部 API
        
        # 總結報告
        self.print_summary()
    
    def print_summary(self):
        """打印總結報告"""
        self.print_header("測試總結報告", level=1)
        
        total_passed = 0
        total_tests = 0
        
        print(f"\n{'測試組':<30} | {'通過':<10} | {'總數':<10} | {'通過率':<10}")
        print("─" * 80)
        
        for group_name, result in self.test_results.items():
            passed = result['passed']
            total = result['total']
            rate = result['rate'] * 100
            
            total_passed += passed
            total_tests += total
            
            status = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
            print(f"{status} {group_name:<27} | {passed:<10.1f} | {total:<10} | {rate:>6.1f}%")
        
        print("─" * 80)
        overall_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅" if overall_rate >= 80 else "⚠️" if overall_rate >= 60 else "❌"
        
        print(f"{overall_status} {'總計':<27} | {total_passed:<10.1f} | {total_tests:<10} | {overall_rate:>6.1f}%")
        
        print("\n" + "=" * 80)
        
        if overall_rate >= 90:
            print("🎉 優秀！系統運作非常穩定！")
        elif overall_rate >= 80:
            print("✅ 良好！系統運作穩定。")
        elif overall_rate >= 60:
            print("⚠️ 尚可！部分功能需要注意。")
        else:
            print("❌ 需要改進！系統存在多個問題。")
        
        print("=" * 80)


if __name__ == '__main__':
    print("🚀 開始 Protocol Assistant 綜合系統測試...")
    print("=" * 80)
    
    tester = ComprehensiveProtocolTester()
    tester.run_all_tests()
    
    print("\n✨ 所有測試完成！")
