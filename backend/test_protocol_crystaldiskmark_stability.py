#!/usr/bin/env python
"""
Protocol Assistant CrystalDiskMark 查詢穩定性測試

測試目標：
1. 驗證重複詢問 "crystaldiskmark" 的穩定性
2. 檢測 AI 回答是否會隨著次數增加而降級
3. 分析回答質量變化趨勢
4. 驗證兩階段搜尋機制在重複查詢下的表現

測試方法（模擬 Web 前端實際行為）：
- 模式 1：持續使用相同 conversation_id（模擬 Web 前端 localStorage 行為）
  * 這是 Web 前端的正常使用情況
  * conversation_id 會自動持久化並重用
  * 連續詢問 10 次相同問題
  
- 模式 2：每次使用新 conversation_id（模擬「清除對話」後的場景）
  * 這是特殊情況：用戶點擊「清除對話」或首次使用
  * 每次查詢都傳空的 conversation_id
  * 測試首次查詢的穩定性（最危險的情況）

記錄指標：
- 搜尋模式、階段、是否降級
- 回答內容長度和引用來源數量
- 不確定性關鍵字出現率

Author: AI Platform Team
Date: 2025-11-12
Updated: 2025-11-12 (對齊 Web 前端行為)
"""

import os
import sys
import django
import time
import logging
from typing import Dict, Any, List

# Django 環境設置
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

# 導入必要模組
from library.protocol_guide.smart_search_router import SmartSearchRouter
from library.common.ai_response import is_uncertain_response

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)


class ProtocolCrystalDiskMarkStabilityTester:
    """Protocol Assistant CrystalDiskMark 查詢穩定性測試器"""
    
    def __init__(self):
        """初始化測試器"""
        self.router = SmartSearchRouter()
        self.test_results = []
    
    def run_single_query(
        self,
        query: str,
        test_number: int,
        conversation_id: str = ""
    ) -> Dict[str, Any]:
        """
        執行單次查詢
        
        Args:
            query: 查詢字串
            test_number: 測試編號
            conversation_id: 對話 ID（可選，用於測試對話上下文影響）
            
        Returns:
            Dict: 測試結果
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"🧪 測試 #{test_number}: {query}")
        logger.info(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # 執行智能搜尋
            result = self.router.handle_smart_search(
                user_query=query,
                conversation_id=conversation_id,
                user_id="test_user_crystaldiskmark"
            )
            
            response_time = time.time() - start_time
            
            # 分析回答
            answer = result.get('answer', '')
            mode = result.get('mode', 'unknown')
            stage = result.get('stage', 'N/A')
            is_fallback = result.get('is_fallback', False)
            fallback_reason = result.get('fallback_reason', '')
            
            # 檢測不確定性
            is_uncertain, uncertain_keyword = is_uncertain_response(answer)
            
            # 提取引用來源
            metadata = result.get('metadata', {})
            retriever_resources = metadata.get('retriever_resources', [])
            citation_count = len(retriever_resources)
            
            # 計算回答長度
            answer_length = len(answer)
            
            # 分析結果
            test_result = {
                'test_number': test_number,
                'query': query,
                'mode': mode,
                'stage': stage,
                'is_fallback': is_fallback,
                'fallback_reason': fallback_reason,
                'is_uncertain': is_uncertain,
                'uncertain_keyword': uncertain_keyword,
                'answer_length': answer_length,
                'citation_count': citation_count,
                'response_time': response_time,
                'answer': answer,
                'citations': retriever_resources,
                'conversation_id': result.get('conversation_id', '')
            }
            
            self.test_results.append(test_result)
            
            # 輸出測試結果
            self._print_test_result(test_result)
            
            return test_result
        
        except Exception as e:
            logger.error(f"❌ 測試 #{test_number} 失敗: {str(e)}", exc_info=True)
            
            error_result = {
                'test_number': test_number,
                'query': query,
                'mode': 'error',
                'stage': 'N/A',
                'is_fallback': True,
                'fallback_reason': f'Exception: {str(e)}',
                'is_uncertain': True,
                'uncertain_keyword': 'error',
                'answer_length': 0,
                'citation_count': 0,
                'response_time': time.time() - start_time,
                'answer': f'Error: {str(e)}',
                'citations': [],
                'conversation_id': ''
            }
            
            self.test_results.append(error_result)
            return error_result
    
    def _print_test_result(self, result: Dict[str, Any]):
        """輸出單次測試結果"""
        print(f"\n📊 測試 #{result['test_number']} 結果:")
        print(f"  模式: {result['mode'].upper()}")
        print(f"  階段: Stage {result['stage']}")
        print(f"  降級: {'是 ⚠️' if result['is_fallback'] else '否 ✅'}")
        
        if result['is_fallback']:
            print(f"  降級原因: {result['fallback_reason']}")
        
        print(f"  不確定: {'是 ⚠️' if result['is_uncertain'] else '否 ✅'}")
        
        if result['is_uncertain']:
            print(f"  不確定關鍵字: {result['uncertain_keyword']}")
        
        print(f"  回答長度: {result['answer_length']} 字元")
        print(f"  引用來源: {result['citation_count']} 個")
        print(f"  響應時間: {result['response_time']:.2f} 秒")
        
        # 顯示回答摘要（前 200 字元）
        answer_preview = result['answer'][:200].replace('\n', ' ')
        print(f"  回答摘要: {answer_preview}...")
        
        # 顯示引用來源
        if result['citations']:
            print(f"  引用來源列表:")
            for i, citation in enumerate(result['citations'][:3], 1):
                doc_name = citation.get('document_name', 'Unknown')
                score = citation.get('score', 0) * 100
                print(f"    {i}. {doc_name} ({score:.2f}%)")
    
    def run_stability_test(
        self,
        query: str,
        test_count: int = 10,
        use_same_conversation: bool = False,
        delay_between_tests: float = 1.0
    ):
        """
        執行穩定性測試
        
        Args:
            query: 測試查詢
            test_count: 測試次數
            use_same_conversation: 是否使用相同對話 ID（測試上下文影響）
            delay_between_tests: 測試間延遲（秒）
        """
        print(f"\n{'='*80}")
        print(f"🚀 Protocol Assistant CrystalDiskMark 穩定性測試")
        print(f"{'='*80}\n")
        print(f"📌 測試查詢: {query}")
        print(f"📌 測試次數: {test_count}")
        print(f"📌 使用相同對話: {'是' if use_same_conversation else '否'}")
        print(f"📌 測試間延遲: {delay_between_tests} 秒")
        print(f"\n{'='*80}\n")
        
        conversation_id = "" if not use_same_conversation else None
        
        for i in range(1, test_count + 1):
            result = self.run_single_query(
                query=query,
                test_number=i,
                conversation_id=conversation_id if conversation_id is not None else ""
            )
            
            # 如果使用相同對話，更新 conversation_id
            if use_same_conversation and conversation_id is None:
                conversation_id = result.get('conversation_id', "")
            
            # 延遲（除了最後一次）
            if i < test_count:
                time.sleep(delay_between_tests)
        
        # 輸出統計分析
        self._print_statistics()
    
    def _print_statistics(self):
        """輸出統計分析"""
        print(f"\n{'='*80}")
        print(f"📊 測試統計分析")
        print(f"{'='*80}\n")
        
        total_tests = len(self.test_results)
        
        if total_tests == 0:
            print("⚠️ 無測試結果")
            return
        
        # 統計各項指標
        mode_a_count = sum(1 for r in self.test_results if r['mode'] == 'mode_a')
        mode_b_count = sum(1 for r in self.test_results if r['mode'] == 'mode_b')
        error_count = sum(1 for r in self.test_results if r['mode'] == 'error')
        
        stage_1_count = sum(1 for r in self.test_results if r['stage'] == 1)
        stage_2_count = sum(1 for r in self.test_results if r['stage'] == 2)
        
        fallback_count = sum(1 for r in self.test_results if r['is_fallback'])
        uncertain_count = sum(1 for r in self.test_results if r['is_uncertain'])
        
        avg_response_time = sum(r['response_time'] for r in self.test_results) / total_tests
        avg_answer_length = sum(r['answer_length'] for r in self.test_results) / total_tests
        avg_citation_count = sum(r['citation_count'] for r in self.test_results) / total_tests
        
        # 輸出統計表格
        print(f"📈 總測試次數: {total_tests}")
        print(f"\n🔍 搜尋模式分佈:")
        print(f"  模式 A（關鍵字觸發）: {mode_a_count} 次 ({mode_a_count/total_tests*100:.1f}%)")
        print(f"  模式 B（兩階段搜尋）: {mode_b_count} 次 ({mode_b_count/total_tests*100:.1f}%)")
        print(f"  錯誤: {error_count} 次 ({error_count/total_tests*100:.1f}%)")
        
        if mode_b_count > 0:
            print(f"\n📊 模式 B 階段分佈:")
            print(f"  階段 1 成功: {stage_1_count} 次 ({stage_1_count/mode_b_count*100:.1f}%)")
            print(f"  階段 2 觸發: {stage_2_count} 次 ({stage_2_count/mode_b_count*100:.1f}%)")
        
        print(f"\n⚠️ 異常指標:")
        print(f"  降級次數: {fallback_count} 次 ({fallback_count/total_tests*100:.1f}%)")
        print(f"  不確定次數: {uncertain_count} 次 ({uncertain_count/total_tests*100:.1f}%)")
        
        print(f"\n⏱️ 效能指標:")
        print(f"  平均響應時間: {avg_response_time:.2f} 秒")
        print(f"  平均回答長度: {avg_answer_length:.0f} 字元")
        print(f"  平均引用來源: {avg_citation_count:.1f} 個")
        
        # 趨勢分析
        print(f"\n📉 趨勢分析:")
        self._analyze_trends()
        
        # 問題檢測
        print(f"\n🚨 問題檢測:")
        self._detect_issues()
    
    def _analyze_trends(self):
        """分析趨勢變化"""
        if len(self.test_results) < 5:
            print("  ⚠️ 測試次數不足，無法分析趨勢")
            return
        
        # 比較前半段和後半段
        mid_point = len(self.test_results) // 2
        first_half = self.test_results[:mid_point]
        second_half = self.test_results[mid_point:]
        
        # 計算前後半段指標
        first_fallback_rate = sum(1 for r in first_half if r['is_fallback']) / len(first_half) * 100
        second_fallback_rate = sum(1 for r in second_half if r['is_fallback']) / len(second_half) * 100
        
        first_avg_length = sum(r['answer_length'] for r in first_half) / len(first_half)
        second_avg_length = sum(r['answer_length'] for r in second_half) / len(second_half)
        
        first_avg_citations = sum(r['citation_count'] for r in first_half) / len(first_half)
        second_avg_citations = sum(r['citation_count'] for r in second_half) / len(second_half)
        
        # 輸出趨勢
        print(f"  降級率變化: {first_fallback_rate:.1f}% → {second_fallback_rate:.1f}% ", end="")
        if second_fallback_rate > first_fallback_rate + 10:
            print("❌ 顯著增加（可能有問題）")
        elif second_fallback_rate < first_fallback_rate - 10:
            print("✅ 顯著降低")
        else:
            print("➡️ 穩定")
        
        print(f"  回答長度變化: {first_avg_length:.0f} → {second_avg_length:.0f} 字元 ", end="")
        if second_avg_length < first_avg_length * 0.7:
            print("❌ 顯著縮短（可能品質下降）")
        elif second_avg_length > first_avg_length * 1.3:
            print("✅ 顯著增加")
        else:
            print("➡️ 穩定")
        
        print(f"  引用來源變化: {first_avg_citations:.1f} → {second_avg_citations:.1f} 個 ", end="")
        if second_avg_citations < first_avg_citations * 0.7:
            print("❌ 顯著減少")
        elif second_avg_citations > first_avg_citations * 1.3:
            print("✅ 顯著增加")
        else:
            print("➡️ 穩定")
    
    def _detect_issues(self):
        """檢測潛在問題"""
        issues = []
        
        # 檢測 1：降級率過高
        fallback_rate = sum(1 for r in self.test_results if r['is_fallback']) / len(self.test_results) * 100
        if fallback_rate > 30:
            issues.append(f"降級率過高: {fallback_rate:.1f}% (正常應 < 30%)")
        
        # 檢測 2：連續降級
        consecutive_fallbacks = 0
        max_consecutive_fallbacks = 0
        for result in self.test_results:
            if result['is_fallback']:
                consecutive_fallbacks += 1
                max_consecutive_fallbacks = max(max_consecutive_fallbacks, consecutive_fallbacks)
            else:
                consecutive_fallbacks = 0
        
        if max_consecutive_fallbacks >= 3:
            issues.append(f"連續降級次數過多: {max_consecutive_fallbacks} 次 (可能存在系統性問題)")
        
        # 檢測 3：回答長度異常縮短
        if len(self.test_results) >= 5:
            mid_point = len(self.test_results) // 2
            first_half_length = sum(r['answer_length'] for r in self.test_results[:mid_point]) / mid_point
            second_half_length = sum(r['answer_length'] for r in self.test_results[mid_point:]) / (len(self.test_results) - mid_point)
            
            if second_half_length < first_half_length * 0.5:
                issues.append(f"後半段回答長度顯著縮短: {first_half_length:.0f} → {second_half_length:.0f} 字元")
        
        # 檢測 4：引用來源消失
        zero_citation_count = sum(1 for r in self.test_results if r['citation_count'] == 0)
        if zero_citation_count > len(self.test_results) * 0.3:
            issues.append(f"無引用來源次數過多: {zero_citation_count} 次 ({zero_citation_count/len(self.test_results)*100:.1f}%)")
        
        # 輸出問題
        if issues:
            for i, issue in enumerate(issues, 1):
                print(f"  ❌ 問題 {i}: {issue}")
        else:
            print(f"  ✅ 未檢測到明顯問題")
    
    def export_results_to_file(self, filename: str = "protocol_crystaldiskmark_stability_test.txt"):
        """匯出測試結果到檔案"""
        filepath = f"/app/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("Protocol Assistant CrystalDiskMark 穩定性測試報告\n")
                f.write("="*80 + "\n\n")
                f.write(f"測試時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"測試次數: {len(self.test_results)}\n\n")
                
                for result in self.test_results:
                    f.write("-"*80 + "\n")
                    f.write(f"測試 #{result['test_number']}\n")
                    f.write("-"*80 + "\n")
                    f.write(f"查詢: {result['query']}\n")
                    f.write(f"模式: {result['mode']}\n")
                    f.write(f"階段: {result['stage']}\n")
                    f.write(f"降級: {result['is_fallback']}\n")
                    f.write(f"不確定: {result['is_uncertain']}\n")
                    f.write(f"回答長度: {result['answer_length']}\n")
                    f.write(f"引用來源: {result['citation_count']}\n")
                    f.write(f"響應時間: {result['response_time']:.2f} 秒\n\n")
                    f.write(f"回答內容:\n{result['answer']}\n\n")
                    
                    if result['citations']:
                        f.write(f"引用來源:\n")
                        for i, citation in enumerate(result['citations'], 1):
                            f.write(f"  {i}. {citation.get('document_name', 'Unknown')} ({citation.get('score', 0)*100:.2f}%)\n")
                        f.write("\n")
            
            print(f"\n✅ 測試結果已匯出到: {filepath}")
        
        except Exception as e:
            print(f"\n❌ 匯出失敗: {str(e)}")


def main():
    """主測試函數"""
    print("\n" + "="*80)
    print("✅ Celery 應用初始化完成")
    print("🚀 開始測試 Protocol Assistant CrystalDiskMark 穩定性...")
    print("="*80 + "\n")
    
    tester = ProtocolCrystalDiskMarkStabilityTester()
    
    # 測試配置
    test_query = "crystaldiskmark"
    test_count = 10  # 測試 10 次
    
    # ✅ 修改：兩個測試模式都使用持續的 conversation_id（模擬 Web 前端 localStorage 行為）
    
    # 執行測試模式 1（模擬 Web 前端實際行為：持續使用相同 ID）
    print("\n" + "="*80)
    print("📌 測試模式 1：持續使用相同 ID（模擬 Web 前端實際行為）")
    print("   ✅ 自動持久化 conversation_id（localStorage）")
    print("="*80)
    tester.run_stability_test(
        query=test_query,
        test_count=test_count,
        use_same_conversation=True,  # ✅ 改為 True，模擬 localStorage 持久化
        delay_between_tests=1.0
    )
    
    # 匯出結果
    tester.export_results_to_file("protocol_crystaldiskmark_stability_test_persistent_id.txt")
    
    # 重置測試結果
    tester.test_results = []
    
    # 執行測試模式 2（模擬「清除對話」後的首次查詢場景）
    print("\n\n" + "="*80)
    print("📌 測試模式 2：每次使用新對話 ID（模擬「清除對話」場景）")
    print("   ⚠️ 測試清除對話後首次查詢的穩定性")
    print("="*80)
    tester.run_stability_test(
        query=test_query,
        test_count=test_count,
        use_same_conversation=False,  # ✅ 每次都是新對話，模擬清除對話
        delay_between_tests=1.0
    )
    
    # 匯出結果
    tester.export_results_to_file("protocol_crystaldiskmark_stability_test_clear_conversation.txt")
    
    print("\n" + "="*80)
    print("✨ 所有測試完成")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
