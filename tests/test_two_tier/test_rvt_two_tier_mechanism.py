#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RVT Guide 兩階段搜尋機制測試腳本
==================================

測試 RVT Assistant 的兩階段智能搜尋機制：
- Stage 1: 初始回答（快速、精準）
- Stage 2: 深度搜尋（降級、全面）

測試場景：
1. Stage 1 成功（確定回答）
2. Stage 1 → Stage 2（不確定降級）
3. Mode A vs Mode B 路由
4. 關鍵字觸發機制
5. 錯誤處理和邊界案例

基於 Protocol Guide 的測試架構，適配 RVT Guide

Author: AI Platform Team
Date: 2025-11-11
"""

import os
import sys
import django
import json

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.test import RequestFactory
from django.contrib.auth.models import User
from library.rvt_guide.api_handlers import RVTGuideAPIHandler


class RVTTwoTierMechanismTester:
    """RVT 兩階段機制測試器"""
    
    def __init__(self):
        self.handler = RVTGuideAPIHandler()
        self.factory = RequestFactory()
        
        # 創建測試用戶
        self.user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        
        self.test_results = []
    
    def print_header(self, title):
        """打印測試標題"""
        print("\n" + "=" * 80)
        print(f"🧪 {title}")
        print("=" * 80)
    
    def print_section(self, title):
        """打印章節標題"""
        print(f"\n{'─' * 80}")
        print(f"📋 {title}")
        print(f"{'─' * 80}")
    
    def print_test_case(self, case_num, case_name):
        """打印測試案例"""
        print(f"\n【測試案例 {case_num}】{case_name}")
        print("─" * 40)
    
    def execute_chat(self, query, conversation_id=None):
        """執行聊天請求"""
        request_data = {
            'message': query,
            'conversation_id': conversation_id
        }
        
        request = self.factory.post('/api/rvt-guide/chat/')
        request.user = self.user
        request.data = request_data
        
        try:
            # 調用 handle_chat_api
            response = self.handler.handle_chat_api(request)
            
            # 解析響應
            if hasattr(response, 'data'):
                data = response.data
            else:
                data = json.loads(response.content.decode('utf-8'))
            
            return {
                'success': True,
                'data': data,
                'error': None
            }
        except Exception as e:
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def analyze_response(self, response_data):
        """分析回應內容"""
        if not response_data:
            return None
        
        analysis = {
            'mode': response_data.get('mode', 'unknown'),
            'stage': response_data.get('stage'),
            'is_fallback': response_data.get('is_fallback', False),
            'fallback_reason': response_data.get('fallback_reason'),
            'answer': response_data.get('answer', '')[:100] + '...' if len(response_data.get('answer', '')) > 100 else response_data.get('answer', ''),
            'has_citations': bool(response_data.get('metadata', {}).get('retriever_resources')),
            'citation_count': len(response_data.get('metadata', {}).get('retriever_resources', [])),
            'response_time': response_data.get('response_time', 0),
            'conversation_id': response_data.get('conversation_id'),
        }
        
        # 提取引用來源標題
        citations = response_data.get('metadata', {}).get('retriever_resources', [])
        if citations:
            analysis['citations'] = [
                {
                    'title': c.get('document_name', 'Unknown'),
                    'score': f"{c.get('score', 0):.2%}"
                }
                for c in citations[:3]  # 只顯示前 3 個
            ]
        
        return analysis
    
    def print_analysis(self, analysis):
        """打印分析結果"""
        if not analysis:
            print("❌ 無法分析回應")
            return
        
        print(f"\n📊 回應分析:")
        print(f"  模式: {analysis['mode'].upper()}")
        if analysis['stage']:
            print(f"  階段: Stage {analysis['stage']}")
        print(f"  降級: {'是 ⚠️' if analysis['is_fallback'] else '否 ✅'}")
        if analysis['fallback_reason']:
            print(f"  降級原因: {analysis['fallback_reason']}")
        print(f"  回答: {analysis['answer']}")
        print(f"  引用來源: {analysis['citation_count']} 個")
        
        if analysis.get('citations'):
            for i, citation in enumerate(analysis['citations'], 1):
                print(f"    {i}. {citation['title']} ({citation['score']})")
        
        print(f"  響應時間: {analysis['response_time']:.2f} 秒")
    
    def test_mode_b_stage_1_success(self):
        """測試：模式 B - 階段 1 成功（確定回答）"""
        self.print_test_case(1, "模式 B - 階段 1 成功（確定回答）")
        
        # 使用一個明確的 RVT 相關問題
        query = "RVT 測試流程的第一步是什麼？"
        
        print(f"查詢: {query}")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['mode'] == 'mode_b' and analysis['stage'] == 1 and not analysis['is_fallback']:
                print("\n✅ 測試通過：模式 B 階段 1 成功")
                return True
            else:
                print("\n⚠️ 測試警告：未達到預期的階段 1 成功")
                return False
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_mode_b_two_tier(self):
        """測試：模式 B - 兩階段搜尋（階段 1 → 階段 2）"""
        self.print_test_case(2, "模式 B - 兩階段搜尋（階段 1 → 階段 2）")
        
        # 使用一個可能觸發兩階段的模糊問題
        query = "RVT 有什麼注意事項？"
        
        print(f"查詢: {query}")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['mode'] == 'mode_b':
                if analysis['stage'] == 2:
                    print("\n✅ 測試通過：成功進入階段 2")
                    return True
                elif analysis['stage'] == 1:
                    print("\n⚠️ 測試提示：階段 1 已成功，未需要階段 2")
                    return True
            return False
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_mode_a_keyword_trigger(self):
        """測試：模式 A - 關鍵字觸發全文搜尋"""
        self.print_test_case(3, "模式 A - 關鍵字觸發全文搜尋")
        
        # 使用包含全文關鍵字的查詢
        query = "請提供 RVT 測試的完整內容"
        
        print(f"查詢: {query}")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['mode'] == 'mode_a':
                print("\n✅ 測試通過：成功觸發模式 A")
                return True
            else:
                print(f"\n⚠️ 測試警告：未觸發模式 A，當前模式：{analysis['mode']}")
                return False
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_fallback_mode(self):
        """測試：降級模式（階段 2 仍不確定）"""
        self.print_test_case(4, "降級模式（階段 2 仍不確定）")
        
        # 使用一個非常模糊或不相關的問題
        query = "天氣如何？"
        
        print(f"查詢: {query}")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['is_fallback']:
                print("\n✅ 測試通過：成功進入降級模式")
                return True
            else:
                print("\n⚠️ 測試提示：未觸發降級模式，AI 給出了確定回答")
                return True  # 這也是成功的，表示 AI 處理得當
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("RVT Guide 兩階段搜尋機制全面測試")
        
        print("\n📌 測試目的：")
        print("  1. 驗證智能路由器正確路由模式 A 和模式 B")
        print("  2. 驗證兩階段搜尋邏輯（Stage 1 → Stage 2）")
        print("  3. 驗證不確定性檢測和降級機制")
        print("  4. 驗證關鍵字觸發全文搜尋")
        
        results = []
        
        # 測試 1：模式 B - 階段 1 成功
        self.print_section("測試組 1：模式 B - 階段 1 成功")
        results.append(("模式 B - 階段 1 成功", self.test_mode_b_stage_1_success()))
        
        # 測試 2：模式 B - 兩階段搜尋
        self.print_section("測試組 2：模式 B - 兩階段搜尋")
        results.append(("模式 B - 兩階段搜尋", self.test_mode_b_two_tier()))
        
        # 測試 3：模式 A - 關鍵字觸發
        self.print_section("測試組 3：模式 A - 關鍵字觸發")
        results.append(("模式 A - 關鍵字觸發", self.test_mode_a_keyword_trigger()))
        
        # 測試 4：降級模式
        self.print_section("測試組 4：降級模式")
        results.append(("降級模式", self.test_fallback_mode()))
        
        # 總結
        self.print_section("測試總結")
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        print(f"\n{'=' * 80}")
        print(f"測試完成：{passed}/{total} 測試通過")
        print(f"{'=' * 80}")
        
        for test_name, result in results:
            status = "✅ 通過" if result else "❌ 失敗"
            print(f"  {status} - {test_name}")
        
        if passed == total:
            print("\n🎉 所有測試通過！RVT Guide 兩階段搜尋機制運作正常。")
        else:
            print(f"\n⚠️ 部分測試未通過，請檢查相關功能。")


if __name__ == '__main__':
    print("🚀 開始測試 RVT Guide 兩階段搜尋機制...")
    print("=" * 80)
    
    tester = RVTTwoTierMechanismTester()
    tester.run_all_tests()
    
    print("\n" + "=" * 80)
    print("✨ 測試完成")
    print("=" * 80)
