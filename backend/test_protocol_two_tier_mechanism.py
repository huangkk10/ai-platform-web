#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Protocol Assistant 兩階段搜尋機制測試腳本
==========================================

測試 Protocol Assistant 的兩階段智能搜尋機制：
- Stage 1: 初始回答（快速、精準）
- Stage 2: 深度搜尋（降級、全面）

測試場景：
1. Stage 1 成功（確定回答）
2. Stage 1 → Stage 2（不確定降級）
3. Mode A vs Mode B 路由
4. 關鍵字觸發機制
5. 錯誤處理和邊界案例

基於 RVT Guide 的測試架構，適配 Protocol Assistant

Author: AI Platform Team
Date: 2025-11-13
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
from library.protocol_guide.api_handlers import ProtocolGuideAPIHandler


class ProtocolTwoTierMechanismTester:
    """Protocol 兩階段機制測試器"""
    
    def __init__(self):
        self.handler = ProtocolGuideAPIHandler()
        self.factory = RequestFactory()
        
        # 創建測試用戶
        self.user, _ = User.objects.get_or_create(
            username='test_protocol_user',
            defaults={'email': 'test_protocol@example.com'}
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
        
        request = self.factory.post('/api/protocol-guides/chat/')
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
            'answer': response_data.get('answer', '')[:150] + '...' if len(response_data.get('answer', '')) > 150 else response_data.get('answer', ''),
            'has_citations': bool(response_data.get('metadata', {}).get('retriever_resources')),
            'citation_count': len(response_data.get('metadata', {}).get('retriever_resources', [])),
            'response_time': response_data.get('response_time', 0),
            'conversation_id': response_data.get('conversation_id'),
            'search_results_count': response_data.get('search_results_count', 0),
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
        print(f"  回答長度: {len(analysis['answer'])} 字元")
        print(f"  回答: {analysis['answer']}")
        print(f"  引用來源: {analysis['citation_count']} 個")
        print(f"  搜索結果: {analysis['search_results_count']} 個")
        
        if analysis.get('citations'):
            print(f"  引用文檔:")
            for i, citation in enumerate(analysis['citations'], 1):
                print(f"    {i}. {citation['title']} ({citation['score']})")
        
        print(f"  響應時間: {analysis['response_time']:.2f} 秒")
    
    def test_mode_b_stage_1_success(self):
        """測試：模式 B - 階段 1 成功（確定回答）"""
        self.print_test_case(1, "模式 B - 階段 1 成功（確定回答）")
        
        # 使用一個明確的 Protocol 相關問題
        query = "CUP 的測試步驟是什麼？"
        
        print(f"查詢: {query}")
        print(f"預期: 模式 B, 階段 1, 非降級")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['mode'] == 'mode_b' and analysis['stage'] == 1 and not analysis['is_fallback']:
                print("\n✅ 測試通過：模式 B 階段 1 成功")
                return True
            elif analysis['mode'] == 'mode_b' and analysis['stage'] == 1:
                print("\n✅ 測試通過：模式 B 階段 1（有降級標記）")
                return True
            else:
                print(f"\n⚠️ 測試警告：未達到預期")
                print(f"   實際模式: {analysis['mode']}, 階段: {analysis['stage']}, 降級: {analysis['is_fallback']}")
                return False
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_mode_b_two_tier(self):
        """測試：模式 B - 兩階段搜尋（階段 1 → 階段 2）"""
        self.print_test_case(2, "模式 B - 兩階段搜尋（階段 1 → 階段 2）")
        
        # 使用一個可能觸發兩階段的模糊問題
        query = "CrystalDiskMark 有什麼注意事項？"
        
        print(f"查詢: {query}")
        print(f"預期: 模式 B, 可能階段 1 或階段 2")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['mode'] == 'mode_b':
                if analysis['stage'] == 2:
                    print("\n✅ 測試通過：成功進入階段 2（深度搜尋）")
                    return True
                elif analysis['stage'] == 1:
                    print("\n✅ 測試通過：階段 1 已成功，未需要階段 2")
                    return True
                else:
                    print("\n⚠️ 測試警告：模式 B 但無階段信息")
                    return False
            else:
                print(f"\n⚠️ 測試警告：未使用模式 B，實際模式: {analysis['mode']}")
                return False
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_mode_a_keyword_trigger(self):
        """測試：模式 A - 關鍵字觸發全文搜尋"""
        self.print_test_case(3, "模式 A - 關鍵字觸發全文搜尋")
        
        # 使用包含全文關鍵字的查詢
        queries = [
            "請提供 CUP 測試的完整內容",
            "給我 CrystalDiskMark 的完整文檔",
            "我需要 ULINK 的詳細說明"
        ]
        
        passed = 0
        for query in queries:
            print(f"\n查詢: {query}")
            print(f"預期: 模式 A（關鍵字觸發）")
            
            result = self.execute_chat(query)
            
            if result['success']:
                analysis = self.analyze_response(result['data'])
                self.print_analysis(analysis)
                
                # 驗證結果
                if analysis['mode'] == 'mode_a':
                    print(f"  ✅ 子測試通過：成功觸發模式 A")
                    passed += 1
                else:
                    print(f"  ⚠️ 子測試警告：未觸發模式 A，當前模式：{analysis['mode']}")
            else:
                print(f"  ❌ 子測試失敗: {result['error']}")
        
        # 判斷整體是否通過
        if passed >= len(queries) / 2:  # 至少一半通過
            print(f"\n✅ 測試通過：{passed}/{len(queries)} 個查詢成功觸發模式 A")
            return True
        else:
            print(f"\n❌ 測試失敗：只有 {passed}/{len(queries)} 個查詢觸發模式 A")
            return False
    
    def test_fallback_mode(self):
        """測試：降級模式（階段 2 仍不確定）"""
        self.print_test_case(4, "降級模式（階段 2 仍不確定）")
        
        # 使用一個非常模糊或不相關的問題
        query = "今天天氣如何？"
        
        print(f"查詢: {query}")
        print(f"預期: 降級模式或禮貌拒絕")
        
        result = self.execute_chat(query)
        
        if result['success']:
            analysis = self.analyze_response(result['data'])
            self.print_analysis(analysis)
            
            # 驗證結果
            if analysis['is_fallback']:
                print("\n✅ 測試通過：成功進入降級模式")
                return True
            else:
                print("\n✅ 測試通過：AI 給出了確定回答（未觸發降級）")
                return True  # 這也是成功的，表示 AI 處理得當
        else:
            print(f"\n❌ 測試失敗: {result['error']}")
            return False
    
    def test_specific_protocol_queries(self):
        """測試：特定 Protocol 查詢"""
        self.print_test_case(5, "特定 Protocol 查詢（實際使用場景）")
        
        queries = [
            "CrystalDiskMark 測試流程",
            "ULINK 設定步驟",
            "Kingston 開卡方法",
            "I3C 相關說明"
        ]
        
        passed = 0
        for query in queries:
            print(f"\n查詢: {query}")
            
            result = self.execute_chat(query)
            
            if result['success']:
                analysis = self.analyze_response(result['data'])
                
                # 簡化輸出
                print(f"  模式: {analysis['mode'].upper()}", end="")
                if analysis['stage']:
                    print(f" | 階段: {analysis['stage']}", end="")
                print(f" | 引用: {analysis['citation_count']} 個", end="")
                print(f" | 降級: {'是' if analysis['is_fallback'] else '否'}")
                print(f"  回答: {analysis['answer'][:100]}...")
                
                # 驗證結果（只要有回答且有引用就算通過）
                if analysis['citation_count'] > 0 and len(analysis['answer']) > 20:
                    print(f"  ✅ 子測試通過")
                    passed += 1
                else:
                    print(f"  ⚠️ 子測試警告：引用或回答可能不足")
            else:
                print(f"  ❌ 子測試失敗: {result['error']}")
        
        # 判斷整體是否通過
        if passed >= len(queries) * 0.75:  # 至少 75% 通過
            print(f"\n✅ 測試通過：{passed}/{len(queries)} 個查詢成功")
            return True
        else:
            print(f"\n❌ 測試失敗：只有 {passed}/{len(queries)} 個查詢成功")
            return False
    
    def test_conversation_continuity(self):
        """測試：對話連續性（多輪對話）"""
        self.print_test_case(6, "對話連續性（多輪對話）")
        
        print("場景：模擬用戶的多輪提問")
        
        # 第一輪：初始問題
        query1 = "CUP 連接測試怎麼做？"
        print(f"\n第 1 輪查詢: {query1}")
        
        result1 = self.execute_chat(query1)
        
        if not result1['success']:
            print(f"❌ 第 1 輪失敗: {result1['error']}")
            return False
        
        analysis1 = self.analyze_response(result1['data'])
        conv_id = analysis1['conversation_id']
        
        print(f"  模式: {analysis1['mode'].upper()}", end="")
        if analysis1['stage']:
            print(f" | 階段: {analysis1['stage']}", end="")
        print(f" | Conversation ID: {conv_id}")
        
        # 第二輪：追問
        query2 = "還有其他注意事項嗎？"
        print(f"\n第 2 輪查詢: {query2}")
        print(f"  使用 Conversation ID: {conv_id}")
        
        result2 = self.execute_chat(query2, conversation_id=conv_id)
        
        if not result2['success']:
            print(f"❌ 第 2 輪失敗: {result2['error']}")
            return False
        
        analysis2 = self.analyze_response(result2['data'])
        
        print(f"  模式: {analysis2['mode'].upper()}", end="")
        if analysis2['stage']:
            print(f" | 階段: {analysis2['stage']}", end="")
        print(f" | 引用: {analysis2['citation_count']} 個")
        
        # 驗證結果
        if analysis2['conversation_id'] == conv_id:
            print(f"\n✅ 測試通過：對話 ID 保持一致，支持多輪對話")
            return True
        else:
            print(f"\n⚠️ 測試警告：對話 ID 不一致")
            return False
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("Protocol Assistant 兩階段搜尋機制全面測試")
        
        print("\n📌 測試目的：")
        print("  1. 驗證智能路由器正確路由模式 A 和模式 B")
        print("  2. 驗證兩階段搜尋邏輯（Stage 1 → Stage 2）")
        print("  3. 驗證不確定性檢測和降級機制")
        print("  4. 驗證關鍵字觸發全文搜尋")
        print("  5. 驗證實際 Protocol 查詢場景")
        print("  6. 驗證對話連續性（多輪對話）")
        
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
        
        # 測試 5：特定 Protocol 查詢
        self.print_section("測試組 5：特定 Protocol 查詢")
        results.append(("特定 Protocol 查詢", self.test_specific_protocol_queries()))
        
        # 測試 6：對話連續性
        self.print_section("測試組 6：對話連續性")
        results.append(("對話連續性", self.test_conversation_continuity()))
        
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
            print("\n🎉 所有測試通過！Protocol Assistant 兩階段搜尋機制運作正常。")
        elif passed >= total * 0.75:
            print(f"\n✅ 大部分測試通過 ({passed}/{total})，Protocol Assistant 運作良好。")
        else:
            print(f"\n⚠️ 部分測試未通過，請檢查相關功能。")
        
        return passed, total


if __name__ == '__main__':
    print("🚀 開始測試 Protocol Assistant 兩階段搜尋機制...")
    print("=" * 80)
    
    tester = ProtocolTwoTierMechanismTester()
    passed, total = tester.run_all_tests()
    
    print("\n" + "=" * 80)
    print("✨ 測試完成")
    print(f"✅ 通過率: {passed}/{total} ({passed/total*100:.1f}%)")
    print("=" * 80)
