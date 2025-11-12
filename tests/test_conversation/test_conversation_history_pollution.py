#!/usr/bin/env python
"""
Protocol Assistant 對話歷史污染實驗

實驗目標：
驗證「對話歷史長度和複雜度」是否影響 crystaldiskmark 查詢的成功率

實驗設計：
- 實驗 A：純淨對話（10 輪 crystaldiskmark）
  * 基準測試，無干擾
  * 預期成功率：80%+（與之前測試一致）

- 實驗 B：I3C 污染對話（10 輪 I3C + 10 輪 crystaldiskmark）
  * 先建立 I3C 的記憶關聯
  * 再查詢 crystaldiskmark
  * 預期成功率：顯著下降（接近 Web 的 14.3%？）

- 實驗 C：長對話污染（50 輪混合主題 + 10 輪 crystaldiskmark）
  * 模擬真實使用情境
  * 多種 Protocol 主題混合
  * 預期成功率：中等下降

實驗假設：
如果「對話歷史複雜度」是關鍵因素，則：
- 實驗 A 成功率最高
- 實驗 B 成功率最低（I3C 直接污染）
- 實驗 C 成功率居中

Author: AI Platform Team
Date: 2025-11-12
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


class ConversationHistoryPollutionExperiment:
    """對話歷史污染實驗器"""
    
    def __init__(self):
        """初始化實驗器"""
        self.router = SmartSearchRouter()
        self.test_results = []
    
    def run_single_query(
        self,
        query: str,
        test_number: int,
        conversation_id: str = "",
        phase: str = "test"
    ) -> Dict[str, Any]:
        """
        執行單次查詢
        
        Args:
            query: 查詢字串
            test_number: 測試編號
            conversation_id: 對話 ID
            phase: 階段標記（pollution/test）
            
        Returns:
            Dict: 測試結果
        """
        logger.info(f"🧪 [{phase.upper()}] 測試 #{test_number}: {query}")
        
        start_time = time.time()
        
        try:
            # 執行智能搜尋
            result = self.router.handle_smart_search(
                user_query=query,
                conversation_id=conversation_id,
                user_id="test_user_pollution_experiment"
            )
            
            response_time = time.time() - start_time
            
            # 分析回答
            answer = result.get('answer', '')
            mode = result.get('mode', 'unknown')
            stage = result.get('stage', 'N/A')
            is_fallback = result.get('is_fallback', False)
            
            # 檢測不確定性
            is_uncertain, uncertain_keyword = is_uncertain_response(answer)
            
            # 提取引用來源
            metadata = result.get('metadata', {})
            retriever_resources = metadata.get('retriever_resources', [])
            citation_count = len(retriever_resources)
            
            # 檢測是否引用了錯誤文檔（I3C）
            cited_i3c = any('I3C' in doc.get('document_name', '') for doc in retriever_resources)
            cited_crystaldiskmark = any('CrystalDiskMark' in doc.get('document_name', '') for doc in retriever_resources)
            
            # 分析結果
            test_result = {
                'test_number': test_number,
                'query': query,
                'phase': phase,
                'mode': mode,
                'stage': stage,
                'is_fallback': is_fallback,
                'is_uncertain': is_uncertain,
                'uncertain_keyword': uncertain_keyword,
                'answer_length': len(answer),
                'citation_count': citation_count,
                'response_time': response_time,
                'cited_i3c': cited_i3c,
                'cited_crystaldiskmark': cited_crystaldiskmark,
                'answer': answer,
                'citations': retriever_resources,
                'conversation_id': result.get('conversation_id', '')
            }
            
            self.test_results.append(test_result)
            
            # 簡化輸出
            status_icon = "✅" if cited_crystaldiskmark and not cited_i3c else "❌"
            print(f"  {status_icon} 測試 #{test_number}: {query[:30]}... → ", end="")
            if cited_crystaldiskmark:
                print("CrystalDiskMark ✅")
            elif cited_i3c:
                print("I3C ❌ (錯誤)")
            else:
                print("其他文檔 ⚠️")
            
            return test_result
        
        except Exception as e:
            logger.error(f"❌ 測試 #{test_number} 失敗: {str(e)}")
            return {
                'test_number': test_number,
                'query': query,
                'phase': phase,
                'mode': 'error',
                'is_fallback': True,
                'cited_i3c': False,
                'cited_crystaldiskmark': False,
                'conversation_id': ''
            }
    
    def run_experiment_a_pure(self):
        """
        實驗 A：純淨對話（基準測試）
        只查詢 crystaldiskmark，無任何干擾
        """
        print("\n" + "="*80)
        print("🧪 實驗 A：純淨對話（基準測試）")
        print("="*80)
        print("📌 設計：連續 10 次查詢 crystaldiskmark")
        print("📌 目的：建立基準成功率")
        print("📌 預期：80%+ 成功率\n")
        
        self.test_results = []
        conversation_id = None
        
        for i in range(1, 11):
            result = self.run_single_query(
                query="crystaldiskmark",
                test_number=i,
                conversation_id=conversation_id if conversation_id else "",
                phase="test"
            )
            
            if conversation_id is None:
                conversation_id = result.get('conversation_id', "")
            
            time.sleep(0.5)  # 短暫延遲
        
        self._print_experiment_summary("實驗 A：純淨對話")
    
    def run_experiment_b_i3c_pollution(self):
        """
        實驗 B：I3C 污染對話
        先查詢 10 次 I3C，建立錯誤記憶，再查詢 10 次 crystaldiskmark
        """
        print("\n" + "="*80)
        print("🧪 實驗 B：I3C 污染對話")
        print("="*80)
        print("📌 設計：階段 1：10 次 I3C 查詢（建立污染）")
        print("        階段 2：10 次 crystaldiskmark 查詢（測試影響）")
        print("📌 目的：驗證 I3C 記憶是否污染 crystaldiskmark 查詢")
        print("📌 預期：成功率顯著下降（< 50%？）\n")
        
        self.test_results = []
        conversation_id = None
        
        # 階段 1：建立 I3C 污染
        print("📍 階段 1：建立 I3C 記憶污染")
        for i in range(1, 11):
            result = self.run_single_query(
                query="I3C 相關說明",
                test_number=i,
                conversation_id=conversation_id if conversation_id else "",
                phase="pollution"
            )
            
            if conversation_id is None:
                conversation_id = result.get('conversation_id', "")
            
            time.sleep(0.5)
        
        print(f"\n✅ 污染階段完成，已累積 {len([r for r in self.test_results if r['phase']=='pollution'])} 輪 I3C 對話")
        print(f"📍 階段 2：測試 crystaldiskmark 查詢（使用相同 conversation_id）\n")
        
        # 重置測試結果計數（只保留污染階段的記錄，但清空統計）
        pollution_count = len(self.test_results)
        
        # 階段 2：測試 crystaldiskmark
        for i in range(1, 11):
            result = self.run_single_query(
                query="crystaldiskmark",
                test_number=pollution_count + i,
                conversation_id=conversation_id,
                phase="test"
            )
            
            time.sleep(0.5)
        
        self._print_experiment_summary("實驗 B：I3C 污染對話")
    
    def run_experiment_c_long_conversation(self):
        """
        實驗 C：長對話污染
        模擬真實使用：混合多種 Protocol 主題，最後查詢 crystaldiskmark
        """
        print("\n" + "="*80)
        print("🧪 實驗 C：長對話污染（模擬真實使用）")
        print("="*80)
        print("📌 設計：階段 1：30 輪混合主題查詢（Protocol、IOL、ULINK、I3C 等）")
        print("        階段 2：10 次 crystaldiskmark 查詢")
        print("📌 目的：模擬用戶長期使用的真實情境")
        print("📌 預期：成功率中等下降（50-70%？）\n")
        
        self.test_results = []
        conversation_id = None
        
        # 階段 1：建立複雜對話歷史
        print("📍 階段 1：建立複雜對話歷史（30 輪混合主題）")
        
        mixed_queries = [
            "Protocol 測試流程",
            "IOL 放測步驟",
            "ULINK 相關說明",
            "I3C 相關說明",
            "CUP 測試方法",
            "Protocol 故障排除",
            "測試工具使用",
            "IOL 測試注意事項",
            "ULINK 配置步驟",
            "I3C 測試流程",
        ] * 3  # 重複 3 次，共 30 輪
        
        for i, query in enumerate(mixed_queries, 1):
            result = self.run_single_query(
                query=query,
                test_number=i,
                conversation_id=conversation_id if conversation_id else "",
                phase="pollution"
            )
            
            if conversation_id is None:
                conversation_id = result.get('conversation_id', "")
            
            time.sleep(0.3)  # 更短的延遲
        
        print(f"\n✅ 污染階段完成，已累積 {len([r for r in self.test_results if r['phase']=='pollution'])} 輪混合對話")
        print(f"📍 階段 2：測試 crystaldiskmark 查詢\n")
        
        pollution_count = len(self.test_results)
        
        # 階段 2：測試 crystaldiskmark
        for i in range(1, 11):
            result = self.run_single_query(
                query="crystaldiskmark",
                test_number=pollution_count + i,
                conversation_id=conversation_id,
                phase="test"
            )
            
            time.sleep(0.5)
        
        self._print_experiment_summary("實驗 C：長對話污染")
    
    def _print_experiment_summary(self, experiment_name: str):
        """輸出實驗統計摘要"""
        print("\n" + "="*80)
        print(f"📊 {experiment_name} - 統計摘要")
        print("="*80 + "\n")
        
        # 只統計測試階段的結果
        test_results = [r for r in self.test_results if r['phase'] == 'test']
        pollution_results = [r for r in self.test_results if r['phase'] == 'pollution']
        
        if not test_results:
            print("⚠️ 無測試結果")
            return
        
        total_tests = len(test_results)
        
        # 計算成功率（引用 CrystalDiskMark 且未引用 I3C）
        success_count = sum(1 for r in test_results if r['cited_crystaldiskmark'] and not r['cited_i3c'])
        i3c_error_count = sum(1 for r in test_results if r['cited_i3c'])
        other_error_count = sum(1 for r in test_results if not r['cited_crystaldiskmark'] and not r['cited_i3c'])
        
        success_rate = success_count / total_tests * 100 if total_tests > 0 else 0
        i3c_error_rate = i3c_error_count / total_tests * 100 if total_tests > 0 else 0
        
        print(f"📈 測試階段統計:")
        print(f"  總測試次數: {total_tests}")
        print(f"  ✅ 成功次數: {success_count} ({success_rate:.1f}%)")
        print(f"  ❌ I3C 錯誤: {i3c_error_count} ({i3c_error_rate:.1f}%)")
        print(f"  ⚠️ 其他錯誤: {other_error_count}")
        
        if pollution_results:
            print(f"\n📍 污染階段:")
            print(f"  污染輪數: {len(pollution_results)}")
            print(f"  對話總輪數: {len(self.test_results)}")
        
        # 顯示失敗案例
        failures = [r for r in test_results if not r['cited_crystaldiskmark'] or r['cited_i3c']]
        if failures:
            print(f"\n❌ 失敗案例:")
            for r in failures[:5]:  # 最多顯示 5 個
                print(f"  測試 #{r['test_number']}: {r['query'][:30]}...")
                if r['cited_i3c']:
                    print(f"    → 引用 I3C（錯誤）")
                elif r['citations']:
                    print(f"    → 引用: {r['citations'][0].get('document_name', 'Unknown')}")
                else:
                    print(f"    → 無引用文檔")
        
        print()
    
    def export_results_to_file(self, filename: str):
        """匯出實驗結果"""
        filepath = f"/app/{filename}"
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("Protocol Assistant 對話歷史污染實驗報告\n")
                f.write("="*80 + "\n\n")
                f.write(f"實驗時間: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"總查詢次數: {len(self.test_results)}\n\n")
                
                for result in self.test_results:
                    f.write("-"*80 + "\n")
                    f.write(f"[{result['phase'].upper()}] 測試 #{result['test_number']}\n")
                    f.write("-"*80 + "\n")
                    f.write(f"查詢: {result['query']}\n")
                    f.write(f"引用 CrystalDiskMark: {result.get('cited_crystaldiskmark', False)}\n")
                    f.write(f"引用 I3C: {result.get('cited_i3c', False)}\n")
                    f.write(f"回答長度: {result.get('answer_length', 0)}\n")
                    f.write(f"引用來源數: {result.get('citation_count', 0)}\n\n")
                    
                    if result.get('citations'):
                        f.write(f"引用來源:\n")
                        for i, citation in enumerate(result['citations'], 1):
                            f.write(f"  {i}. {citation.get('document_name', 'Unknown')} ({citation.get('score', 0)*100:.2f}%)\n")
                        f.write("\n")
            
            print(f"✅ 實驗結果已匯出到: {filepath}\n")
        
        except Exception as e:
            print(f"❌ 匯出失敗: {str(e)}\n")


def main():
    """主實驗函數"""
    print("\n" + "="*80)
    print("🔬 Protocol Assistant 對話歷史污染實驗")
    print("="*80)
    print("\n實驗目的：驗證「對話歷史複雜度」是否影響查詢準確性")
    print("實驗假設：長對話和 I3C 污染會降低 crystaldiskmark 查詢成功率\n")
    
    experimenter = ConversationHistoryPollutionExperiment()
    
    # 實驗 A：純淨對話（基準測試）
    experimenter.run_experiment_a_pure()
    experimenter.export_results_to_file("experiment_a_pure_conversation.txt")
    
    # 短暫休息
    print("\n⏸️ 休息 3 秒後開始下一個實驗...\n")
    time.sleep(3)
    
    # 實驗 B：I3C 污染對話
    experimenter.run_experiment_b_i3c_pollution()
    experimenter.export_results_to_file("experiment_b_i3c_pollution.txt")
    
    # 短暫休息
    print("\n⏸️ 休息 3 秒後開始下一個實驗...\n")
    time.sleep(3)
    
    # 實驗 C：長對話污染
    experimenter.run_experiment_c_long_conversation()
    experimenter.export_results_to_file("experiment_c_long_conversation.txt")
    
    # 最終總結
    print("\n" + "="*80)
    print("🎯 實驗總結")
    print("="*80)
    print("\n所有實驗已完成！請查看匯出的結果文件以獲取詳細資訊。")
    print("\n預期結果對比:")
    print("  實驗 A（純淨對話）：成功率 80%+")
    print("  實驗 B（I3C 污染）：成功率 < 50%")
    print("  實驗 C（長對話）：成功率 50-70%")
    print("\n如果實驗 B 和 C 的成功率顯著低於 A，則證明「對話歷史污染」")
    print("是導致 Web 前端失敗率高的關鍵因素！")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
