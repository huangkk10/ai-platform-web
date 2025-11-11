#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
兩階段搜尋機制全面測試
======================

測試 Protocol Assistant 的兩階段智能搜尋機制：
- Stage 1: 初始回答（快速、精準）
- Stage 2: 深度搜尋（降級、全面）

測試場景：
1. Stage 1 成功（確定回答）
2. Stage 1 → Stage 2（不確定降級）
3. Mode A vs Mode B 路由
4. 關鍵字觸發機制
5. 錯誤處理和邊界案例

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
from library.protocol_guide.api_handlers import ProtocolGuideAPIHandler


class TwoTierMechanismTester:
    """兩階段機制測試器"""
    
    def __init__(self):
        self.handler = ProtocolGuideAPIHandler()
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
        
        request = self.factory.post('/api/protocol-guide/chat/')
        request.user = self.user
        request.data = request_data
        
        try:
            # 正確的方法名稱是 handle_chat_api
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
    
    def record_result(self, test_name, expected, actual, passed):
        """記錄測試結果"""
        self.test_results.append({
            'test': test_name,
            'expected': expected,
            'actual': actual,
            'passed': passed
        })
    
    # ===== 測試案例 =====
    
    def test_stage1_success(self):
        """測試案例 1: Stage 1 成功（確定回答）"""
        self.print_test_case("1", "Stage 1 成功 - 簡單查詢")
        
        query = "Cup 顏色"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("Stage 1 成功", "mode_b, stage=1", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證
        expected_mode = 'mode_b'
        expected_stage = '1'
        expected_fallback = False
        
        passed = (
            analysis['mode'] == expected_mode and
            analysis['stage'] == expected_stage and
            analysis['is_fallback'] == expected_fallback
        )
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: Mode B, Stage 1, 不降級")
        print(f"實際: Mode {analysis['mode'].upper()}, Stage {analysis['stage']}, {'降級' if analysis['is_fallback'] else '不降級'}")
        
        self.record_result(
            "Stage 1 成功",
            f"mode_b, stage=1, fallback=False",
            f"mode={analysis['mode']}, stage={analysis['stage']}, fallback={analysis['is_fallback']}",
            passed
        )
    
    def test_stage1_to_stage2(self):
        """測試案例 2: Stage 1 → Stage 2（不確定降級）"""
        self.print_test_case("2", "Stage 1 → Stage 2 - 複雜查詢觸發降級")
        
        query = "Cup 所有測試步驟詳細說明"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("Stage 1→2 降級", "stage=2", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證：應該觸發 Stage 2 或降級
        expected_stage_2_or_fallback = (
            analysis['stage'] == '2' or 
            analysis['is_fallback']
        )
        
        status = "✅ PASS" if expected_stage_2_or_fallback else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: Stage 2 或降級模式")
        print(f"實際: Stage {analysis['stage']}, {'降級' if analysis['is_fallback'] else '不降級'}")
        
        self.record_result(
            "Stage 1→2 降級",
            "stage=2 or fallback=True",
            f"stage={analysis['stage']}, fallback={analysis['is_fallback']}",
            expected_stage_2_or_fallback
        )
    
    def test_mode_a_keyword_trigger(self):
        """測試案例 3: Mode A - 關鍵字觸發全文搜尋"""
        self.print_test_case("3", "Mode A - 關鍵字觸發 ('完整內容')")
        
        query = "Cup 完整內容"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("Mode A 觸發", "mode_a", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證：應該是 Mode A
        expected_mode = 'mode_a'
        passed = analysis['mode'] == expected_mode
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: Mode A（全文搜尋）")
        print(f"實際: Mode {analysis['mode'].upper()}")
        
        self.record_result(
            "Mode A 觸發",
            "mode_a",
            f"mode={analysis['mode']}",
            passed
        )
    
    def test_mode_a_multiple_keywords(self):
        """測試案例 4: Mode A - 多個關鍵字"""
        self.print_test_case("4", "Mode A - 多個關鍵字 ('全文' + '所有')")
        
        query = "給我 Cup 的全文和所有資訊"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("Mode A 多關鍵字", "mode_a", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        expected_mode = 'mode_a'
        passed = analysis['mode'] == expected_mode
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        
        self.record_result(
            "Mode A 多關鍵字",
            "mode_a",
            f"mode={analysis['mode']}",
            passed
        )
    
    def test_fallback_mode(self):
        """測試案例 5: 降級模式 - AI 無法回答"""
        self.print_test_case("5", "降級模式 - 不存在的文檔")
        
        query = "XYZ_NOT_EXIST 的測試流程"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("降級模式", "fallback=True", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證：應該降級或返回「找不到」類型的回答
        expected_fallback_or_uncertain = (
            analysis['is_fallback'] or
            '找不到' in analysis['answer'] or
            '沒有' in analysis['answer'] or
            '不清楚' in analysis['answer']
        )
        
        status = "✅ PASS" if expected_fallback_or_uncertain else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: 降級或表達無法回答")
        print(f"實際: {'降級模式' if analysis['is_fallback'] else '正常回答'}")
        
        self.record_result(
            "降級模式",
            "fallback=True or uncertain_answer",
            f"fallback={analysis['is_fallback']}",
            expected_fallback_or_uncertain
        )
    
    def test_conversation_continuity(self):
        """測試案例 6: 對話連續性"""
        self.print_test_case("6", "對話連續性 - 多輪對話")
        
        # 第一輪
        query1 = "Cup 是什麼？"
        print(f"第 1 輪查詢: '{query1}'")
        result1 = self.execute_chat(query1)
        
        if not result1['success']:
            print(f"❌ 第 1 輪請求失敗: {result1['error']}")
            self.record_result("對話連續性", "same_conversation_id", "ERROR", False)
            return
        
        analysis1 = self.analyze_response(result1['data'])
        conversation_id = analysis1['conversation_id']
        print(f"  Conversation ID: {conversation_id}")
        print(f"  回答: {analysis1['answer']}")
        
        # 第二輪（使用相同 conversation_id）
        query2 = "它的顏色是什麼？"
        print(f"\n第 2 輪查詢: '{query2}'")
        print(f"  使用 Conversation ID: {conversation_id}")
        result2 = self.execute_chat(query2, conversation_id=conversation_id)
        
        if not result2['success']:
            print(f"❌ 第 2 輪請求失敗: {result2['error']}")
            self.record_result("對話連續性", "same_conversation_id", "ERROR", False)
            return
        
        analysis2 = self.analyze_response(result2['data'])
        print(f"  回答: {analysis2['answer']}")
        
        # 驗證：兩輪對話應該有相同的 conversation_id
        passed = (
            conversation_id and
            analysis2['conversation_id'] == conversation_id
        )
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: 相同的 conversation_id")
        print(f"實際: {analysis1['conversation_id']} == {analysis2['conversation_id']}")
        
        self.record_result(
            "對話連續性",
            "same_conversation_id",
            f"id1={conversation_id}, id2={analysis2['conversation_id']}",
            passed
        )
    
    def test_citation_accuracy(self):
        """測試案例 7: 引用來源準確性"""
        self.print_test_case("7", "引用來源準確性 - Cup 查詢應返回 Cup 文檔")
        
        query = "Cup 的用途是什麼？"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("引用準確性", "Cup in citations", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證：引用來源中應該有 Cup 文檔
        has_cup_citation = False
        if analysis.get('citations'):
            for citation in analysis['citations']:
                if 'Cup' in citation['title']:
                    has_cup_citation = True
                    break
        
        status = "✅ PASS" if has_cup_citation else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: 引用來源包含 'Cup' 文檔")
        print(f"實際: {'找到 Cup 文檔' if has_cup_citation else '未找到 Cup 文檔'}")
        
        self.record_result(
            "引用準確性",
            "Cup in citations",
            f"has_cup={has_cup_citation}",
            has_cup_citation
        )
    
    def test_empty_query(self):
        """測試案例 8: 邊界案例 - 空查詢"""
        self.print_test_case("8", "邊界案例 - 空查詢")
        
        query = ""
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        # 應該返回錯誤或提示
        expected_error = not result['success'] or (
            result['data'] and '請輸入' in result['data'].get('answer', '')
        )
        
        status = "✅ PASS" if expected_error else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: 錯誤或提示訊息")
        print(f"實際: {'錯誤處理正確' if expected_error else '未正確處理'}")
        
        self.record_result(
            "空查詢處理",
            "error or prompt",
            f"success={result['success']}",
            expected_error
        )
    
    def test_performance(self):
        """測試案例 9: 效能測試 - 響應時間"""
        self.print_test_case("9", "效能測試 - 響應時間 < 15 秒")
        
        query = "Cup 的測試流程"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("響應時間", "< 15s", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        response_time = analysis['response_time']
        
        # 驗證：響應時間應該 < 15 秒（合理範圍）
        passed = response_time < 15.0
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        print(f"預期: 響應時間 < 15 秒")
        print(f"實際: {response_time:.2f} 秒")
        
        self.record_result(
            "響應時間",
            "< 15s",
            f"{response_time:.2f}s",
            passed
        )
    
    def test_special_characters(self):
        """測試案例 10: 特殊字符處理"""
        self.print_test_case("10", "特殊字符處理")
        
        query = "Cup & USB 3.0 的差異？"
        print(f"查詢: '{query}'")
        
        result = self.execute_chat(query)
        
        if not result['success']:
            print(f"❌ 請求失敗: {result['error']}")
            self.record_result("特殊字符", "handled", "ERROR", False)
            return
        
        analysis = self.analyze_response(result['data'])
        self.print_analysis(analysis)
        
        # 驗證：能正常處理，不報錯
        passed = result['success'] and analysis is not None
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"\n{status}")
        
        self.record_result(
            "特殊字符",
            "handled",
            f"success={result['success']}",
            passed
        )
    
    # ===== 主測試流程 =====
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("兩階段搜尋機制全面測試")
        
        print("\n📌 測試目標:")
        print("  1. ✅ Stage 1 成功（確定回答）")
        print("  2. ✅ Stage 1 → Stage 2 降級（不確定回答）")
        print("  3. ✅ Mode A 關鍵字觸發（全文搜尋）")
        print("  4. ✅ Mode B 兩階段路由（智能搜尋）")
        print("  5. ✅ 降級模式（無法回答）")
        print("  6. ✅ 對話連續性（conversation_id）")
        print("  7. ✅ 引用來源準確性（Cup → Cup 文檔）")
        print("  8. ✅ 邊界案例處理（空查詢、特殊字符）")
        print("  9. ✅ 效能測試（響應時間）")
        print("  10. ✅ 錯誤處理（異常情況）")
        
        # 執行測試
        try:
            self.print_section("階段 1: 基礎功能測試")
            self.test_stage1_success()
            self.test_stage1_to_stage2()
            
            self.print_section("階段 2: 模式路由測試")
            self.test_mode_a_keyword_trigger()
            self.test_mode_a_multiple_keywords()
            
            self.print_section("階段 3: 降級與連續性測試")
            self.test_fallback_mode()
            self.test_conversation_continuity()
            
            self.print_section("階段 4: 準確性與效能測試")
            self.test_citation_accuracy()
            self.test_performance()
            
            self.print_section("階段 5: 邊界案例測試")
            self.test_empty_query()
            self.test_special_characters()
            
        except Exception as e:
            print(f"\n❌ 測試執行錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 打印總結
        self.print_summary()
    
    def print_summary(self):
        """打印測試總結"""
        self.print_header("測試總結")
        
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['passed'])
        failed = total - passed
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        print(f"\n📊 統計:")
        print(f"  總測試數: {total}")
        print(f"  ✅ 通過: {passed}")
        print(f"  ❌ 失敗: {failed}")
        print(f"  通過率: {pass_rate:.1f}%")
        
        if failed > 0:
            print(f"\n❌ 失敗案例詳情:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"\n  測試: {result['test']}")
                    print(f"    預期: {result['expected']}")
                    print(f"    實際: {result['actual']}")
        
        print("\n" + "🎉" * 40)
        if failed == 0:
            print("🎉 恭喜！所有測試通過！")
            print("🎉 兩階段搜尋機制運作正常！")
        else:
            print(f"⚠️ 發現 {failed} 個問題，請檢查上述失敗案例")
        print("🎉" * 40 + "\n")


def main():
    """主函數"""
    print("\n" + "🚀" * 40)
    print("啟動兩階段搜尋機制測試...")
    print("🚀" * 40)
    
    tester = TwoTierMechanismTester()
    tester.run_all_tests()


if __name__ == '__main__':
    try:
        main()
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 測試程式錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
