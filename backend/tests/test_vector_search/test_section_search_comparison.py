#!/usr/bin/env python
"""
向量搜尋系統完整對比測試

功能：
1. 對比新舊系統的搜尋準確度
2. 對比新舊系統的內容長度
3. 對比新舊系統的回應速度
4. 生成詳細的對比報告

使用方式：
    python tests/test_vector_search/test_section_search_comparison.py

輸出：
    - reports/comparison_YYYYMMDD_HHMMSS.csv (詳細數據)
    - reports/comparison_YYYYMMDD_HHMMSS.md (總結報告)
"""

import os
import sys
import json
import time
import csv
from datetime import datetime
from pathlib import Path

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Django 環境設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from library.common.knowledge_base.section_search_service import SectionSearchService


class SearchComparisonTest:
    """搜尋系統對比測試類別"""
    
    def __init__(self):
        self.old_service = ProtocolGuideSearchService()
        self.new_service = SectionSearchService()
        self.results = []
        self.test_queries = []
        
    def load_test_queries(self):
        """載入測試查詢"""
        test_data_file = Path(__file__).parent / 'test_data' / 'test_queries.json'
        
        if test_data_file.exists():
            with open(test_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 合併所有類型的查詢
                for category in ['basic_queries', 'technical_queries', 'semantic_queries', 'edge_cases']:
                    if category in data:
                        self.test_queries.extend(data[category])
        else:
            # 預設測試查詢
            self.test_queries = [
                "ULINK 連接失敗",
                "測試環境準備",
                "日誌檔案位置",
                "OpenCV 版本相容性",
                "pytest fixture 使用",
                "Docker compose 網路配置",
                "錯誤碼查詢",
                "測試腳本執行",
                "如何除錯程式",
                "測試失敗怎麼辦",
            ]
        
        print(f"✅ 載入 {len(self.test_queries)} 個測試查詢")
        return self.test_queries
    
    def run_comparison(self, query, top_k=3, threshold=0.7):
        """執行單次對比測試"""
        print(f"\n🔍 測試查詢: {query}")
        
        result = {
            'query': query,
            'timestamp': datetime.now().isoformat(),
        }
        
        # 測試舊系統
        try:
            start_time = time.time()
            old_results = self.old_service.search_knowledge(
                query=query,
                limit=top_k,
                use_vector=True
            )
            old_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            result['old_count'] = len(old_results)
            result['old_time_ms'] = round(old_time, 2)
            
            if old_results:
                # 舊系統使用 'score' 欄位，不是 'similarity'
                result['old_avg_similarity'] = round(
                    sum(r.get('score', r.get('similarity', 0)) for r in old_results) / len(old_results) * 100, 
                    2
                )
                result['old_avg_content_length'] = round(
                    sum(len(r.get('content', '')) for r in old_results) / len(old_results), 
                    0
                )
                result['old_best_similarity'] = round(old_results[0].get('score', old_results[0].get('similarity', 0)) * 100, 2)
            else:
                result['old_avg_similarity'] = 0
                result['old_avg_content_length'] = 0
                result['old_best_similarity'] = 0
                
            print(f"  舊系統: {len(old_results)} 個結果, 平均相似度 {result['old_avg_similarity']:.2f}%, 耗時 {old_time:.2f}ms")
            
        except Exception as e:
            print(f"  ❌ 舊系統錯誤: {str(e)}")
            result['old_error'] = str(e)
            result['old_count'] = 0
            result['old_time_ms'] = 0
            result['old_avg_similarity'] = 0
            result['old_avg_content_length'] = 0
            result['old_best_similarity'] = 0
        
        # 測試新系統
        try:
            start_time = time.time()
            new_results = self.new_service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=top_k,
                threshold=threshold
            )
            new_time = (time.time() - start_time) * 1000  # 轉換為毫秒
            
            result['new_count'] = len(new_results)
            result['new_time_ms'] = round(new_time, 2)
            
            if new_results:
                result['new_avg_similarity'] = round(
                    sum(r['similarity'] for r in new_results) / len(new_results) * 100, 
                    2
                )
                result['new_avg_content_length'] = round(
                    sum(len(r.get('content', '')) for r in new_results) / len(new_results), 
                    0
                )
                result['new_best_similarity'] = round(new_results[0]['similarity'] * 100, 2)
                
                # 新系統額外資訊：段落層級分布
                levels = [r.get('heading_level', 0) for r in new_results]
                result['new_level_distribution'] = ','.join(map(str, levels))
            else:
                result['new_avg_similarity'] = 0
                result['new_avg_content_length'] = 0
                result['new_best_similarity'] = 0
                result['new_level_distribution'] = ''
                
            print(f"  新系統: {len(new_results)} 個結果, 平均相似度 {result['new_avg_similarity']:.2f}%, 耗時 {new_time:.2f}ms")
            
        except Exception as e:
            print(f"  ❌ 新系統錯誤: {str(e)}")
            result['new_error'] = str(e)
            result['new_count'] = 0
            result['new_time_ms'] = 0
            result['new_avg_similarity'] = 0
            result['new_avg_content_length'] = 0
            result['new_best_similarity'] = 0
            result['new_level_distribution'] = ''
        
        # 計算改善指標
        if result['old_avg_similarity'] > 0:
            result['similarity_improvement'] = round(
                result['new_avg_similarity'] - result['old_avg_similarity'], 
                2
            )
            result['similarity_improvement_pct'] = round(
                (result['new_avg_similarity'] - result['old_avg_similarity']) / result['old_avg_similarity'] * 100,
                2
            )
        else:
            result['similarity_improvement'] = 0
            result['similarity_improvement_pct'] = 0
            
        if result['old_avg_content_length'] > 0:
            result['content_reduction_pct'] = round(
                (1 - result['new_avg_content_length'] / result['old_avg_content_length']) * 100,
                2
            )
        else:
            result['content_reduction_pct'] = 0
            
        result['time_difference_ms'] = round(result['new_time_ms'] - result['old_time_ms'], 2)
        
        # 判斷勝負
        if result['new_avg_similarity'] > result['old_avg_similarity']:
            result['winner'] = '新系統'
        elif result['new_avg_similarity'] < result['old_avg_similarity']:
            result['winner'] = '舊系統'
        else:
            result['winner'] = '平手'
        
        print(f"  📊 結果: {result['winner']} 勝出 (相似度改善 {result['similarity_improvement']:+.2f}%, 內容精簡 {result['content_reduction_pct']:.1f}%)")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self, top_k=3, threshold=0.7):
        """執行所有測試"""
        print(f"\n{'='*70}")
        print(f"🚀 開始執行向量搜尋系統對比測試")
        print(f"{'='*70}")
        print(f"測試參數: top_k={top_k}, threshold={threshold}")
        print(f"測試查詢數量: {len(self.test_queries)}")
        
        for i, query in enumerate(self.test_queries, 1):
            print(f"\n[{i}/{len(self.test_queries)}]", end=" ")
            self.run_comparison(query, top_k, threshold)
            time.sleep(0.1)  # 避免過度查詢
        
        print(f"\n{'='*70}")
        print(f"✅ 所有測試完成")
        print(f"{'='*70}")
    
    def generate_csv_report(self):
        """生成 CSV 詳細報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / 'reports' / f'comparison_{timestamp}.csv'
        
        fieldnames = [
            'query', 'timestamp', 'winner',
            'old_count', 'old_avg_similarity', 'old_best_similarity', 'old_avg_content_length', 'old_time_ms',
            'new_count', 'new_avg_similarity', 'new_best_similarity', 'new_avg_content_length', 'new_time_ms',
            'new_level_distribution',
            'similarity_improvement', 'similarity_improvement_pct',
            'content_reduction_pct', 'time_difference_ms'
        ]
        
        with open(report_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for result in self.results:
                # 只寫入存在的欄位
                row = {k: result.get(k, '') for k in fieldnames}
                writer.writerow(row)
        
        print(f"✅ CSV 報告已生成: {report_file}")
        return report_file
    
    def generate_markdown_report(self):
        """生成 Markdown 總結報告"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = Path(__file__).parent / 'reports' / f'comparison_{timestamp}.md'
        
        # 計算統計指標
        total_tests = len(self.results)
        new_wins = sum(1 for r in self.results if r['winner'] == '新系統')
        old_wins = sum(1 for r in self.results if r['winner'] == '舊系統')
        ties = sum(1 for r in self.results if r['winner'] == '平手')
        
        avg_similarity_improvement = sum(r['similarity_improvement'] for r in self.results) / total_tests if total_tests > 0 else 0
        avg_content_reduction = sum(r['content_reduction_pct'] for r in self.results) / total_tests if total_tests > 0 else 0
        avg_time_diff = sum(r['time_difference_ms'] for r in self.results) / total_tests if total_tests > 0 else 0
        
        # 生成報告內容
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 向量搜尋系統對比測試報告\n\n")
            f.write(f"**測試時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**測試版本**: Protocol Guide Vector Search System v2.0\n\n")
            f.write(f"---\n\n")
            
            f.write(f"## 📊 測試總覽\n\n")
            f.write(f"| 指標 | 數值 |\n")
            f.write(f"|------|------|\n")
            f.write(f"| 測試查詢總數 | {total_tests} |\n")
            f.write(f"| 新系統勝出 | {new_wins} ({new_wins/total_tests*100:.1f}%) |\n")
            f.write(f"| 舊系統勝出 | {old_wins} ({old_wins/total_tests*100:.1f}%) |\n")
            f.write(f"| 平手 | {ties} ({ties/total_tests*100:.1f}%) |\n")
            f.write(f"| 平均相似度改善 | {avg_similarity_improvement:+.2f}% |\n")
            f.write(f"| 平均內容精簡 | {avg_content_reduction:.1f}% |\n")
            f.write(f"| 平均時間差異 | {avg_time_diff:+.2f}ms |\n\n")
            
            f.write(f"---\n\n")
            
            f.write(f"## 🎯 結論\n\n")
            if new_wins > old_wins:
                f.write(f"✅ **新系統（段落級別搜尋）顯著優於舊系統（整篇文檔搜尋）**\n\n")
                f.write(f"- 勝率: {new_wins/total_tests*100:.1f}%\n")
                f.write(f"- 相似度平均提升 {avg_similarity_improvement:.2f}%\n")
                f.write(f"- 內容平均精簡 {avg_content_reduction:.1f}%\n")
                f.write(f"- 建議: **可以考慮將新系統設為預設搜尋引擎**\n\n")
            elif new_wins == old_wins:
                f.write(f"⚖️ **新舊系統表現相當**\n\n")
                f.write(f"- 建議: 繼續並行運行，根據用戶反饋決定\n\n")
            else:
                f.write(f"⚠️ **舊系統仍然表現更好**\n\n")
                f.write(f"- 建議: 繼續優化新系統，暫不切換\n\n")
            
            f.write(f"---\n\n")
            
            f.write(f"## 📈 詳細數據\n\n")
            f.write(f"### Top 10 改善最多的查詢\n\n")
            
            # 排序：相似度改善最多
            sorted_results = sorted(self.results, key=lambda x: x['similarity_improvement'], reverse=True)[:10]
            
            f.write(f"| 排名 | 查詢 | 舊系統相似度 | 新系統相似度 | 改善幅度 |\n")
            f.write(f"|------|------|--------------|--------------|----------|\n")
            for i, r in enumerate(sorted_results, 1):
                f.write(f"| {i} | {r['query']} | {r['old_avg_similarity']:.2f}% | {r['new_avg_similarity']:.2f}% | {r['similarity_improvement']:+.2f}% |\n")
            
            f.write(f"\n### Top 10 內容精簡最多的查詢\n\n")
            
            # 排序：內容精簡最多
            sorted_results = sorted(self.results, key=lambda x: x['content_reduction_pct'], reverse=True)[:10]
            
            f.write(f"| 排名 | 查詢 | 舊系統長度 | 新系統長度 | 精簡幅度 |\n")
            f.write(f"|------|------|------------|------------|----------|\n")
            for i, r in enumerate(sorted_results, 1):
                f.write(f"| {i} | {r['query']} | {r['old_avg_content_length']:.0f} 字元 | {r['new_avg_content_length']:.0f} 字元 | {r['content_reduction_pct']:.1f}% |\n")
            
            f.write(f"\n---\n\n")
            f.write(f"## 📝 備註\n\n")
            f.write(f"- 測試參數: top_k=3, threshold=0.7\n")
            f.write(f"- 舊系統: 整篇文檔向量搜尋 (document_embeddings 表)\n")
            f.write(f"- 新系統: 段落級別向量搜尋 (document_section_embeddings 表)\n")
            f.write(f"- 詳細數據請參考: `comparison_{timestamp}.csv`\n\n")
        
        print(f"✅ Markdown 報告已生成: {report_file}")
        return report_file


def main():
    """主程式"""
    tester = SearchComparisonTest()
    
    # 載入測試查詢
    tester.load_test_queries()
    
    # 執行所有測試
    tester.run_all_tests(top_k=3, threshold=0.7)
    
    # 生成報告
    csv_file = tester.generate_csv_report()
    md_file = tester.generate_markdown_report()
    
    print(f"\n{'='*70}")
    print(f"🎉 測試完成！")
    print(f"{'='*70}")
    print(f"📄 CSV 報告: {csv_file}")
    print(f"📄 Markdown 報告: {md_file}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
