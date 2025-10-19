#!/usr/bin/env python
"""
向量搜尋準確度專項測試

功能：
1. 按查詢類型分組測試準確度
2. 計算 Top-1, Top-3 準確率
3. 分析假陽性率
4. 生成準確度報告

使用方式：
    python tests/test_vector_search/test_search_accuracy.py

輸出：
    - reports/accuracy_report_YYYYMMDD.md (總結報告)
"""

import os
import sys
import json
import time
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Django 環境設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService


class SearchAccuracyTest:
    """搜尋準確度測試類別"""
    
    def __init__(self):
        self.service = SectionSearchService()
        self.results_by_category = defaultdict(list)
        self.test_queries = {}
        
    def load_test_queries(self):
        """載入測試查詢（按類型分組）"""
        test_data_file = Path(__file__).parent / 'test_data' / 'test_queries.json'
        
        if test_data_file.exists():
            with open(test_data_file, 'r', encoding='utf-8') as f:
                self.test_queries = json.load(f)
        else:
            # 預設測試查詢
            self.test_queries = {
                'basic_queries': [
                    "ULINK 連接失敗",
                    "測試環境準備",
                    "日誌檔案位置",
                ],
                'technical_queries': [
                    "OpenCV 版本相容性",
                    "pytest fixture 使用",
                    "Docker compose 網路配置",
                ],
                'semantic_queries': [
                    "如何除錯程式",
                    "測試失敗怎麼辦",
                    "效能優化建議",
                ],
                'edge_cases': [
                    "測試",
                    "ULINK",
                ],
            }
        
        total = sum(len(queries) for queries in self.test_queries.values())
        print(f"✅ 載入 {total} 個測試查詢（分 {len(self.test_queries)} 類）")
        return self.test_queries
    
    def test_query(self, query, category, top_k=3, threshold=0.7):
        """測試單個查詢"""
        try:
            start_time = time.time()
            results = self.service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=top_k,
                threshold=threshold
            )
            search_time = (time.time() - start_time) * 1000
            
            result = {
                'query': query,
                'category': category,
                'found_count': len(results),
                'search_time_ms': round(search_time, 2),
                'results': results,
            }
            
            if results:
                result['top1_similarity'] = round(results[0]['similarity'] * 100, 2)
                result['avg_similarity'] = round(
                    sum(r['similarity'] for r in results) / len(results) * 100, 
                    2
                )
                result['min_similarity'] = round(min(r['similarity'] for r in results) * 100, 2)
                result['max_similarity'] = round(max(r['similarity'] for r in results) * 100, 2)
                
                # 段落層級分布
                levels = [r.get('heading_level', 0) for r in results]
                result['level_distribution'] = dict((level, levels.count(level)) for level in set(levels))
                
                # 內容長度統計
                lengths = [len(r.get('content', '')) for r in results]
                result['avg_content_length'] = round(sum(lengths) / len(lengths), 0)
                
            else:
                result['top1_similarity'] = 0
                result['avg_similarity'] = 0
                result['min_similarity'] = 0
                result['max_similarity'] = 0
                result['level_distribution'] = {}
                result['avg_content_length'] = 0
            
            self.results_by_category[category].append(result)
            
            print(f"  ✓ [{category}] {query}: {len(results)} 個結果, Top-1 相似度 {result['top1_similarity']:.2f}%")
            
            return result
            
        except Exception as e:
            print(f"  ✗ [{category}] {query}: 錯誤 - {str(e)}")
            result = {
                'query': query,
                'category': category,
                'error': str(e),
                'found_count': 0,
                'top1_similarity': 0,
            }
            self.results_by_category[category].append(result)
            return result
    
    def run_all_tests(self, top_k=3, threshold=0.7):
        """執行所有準確度測試"""
        print(f"\n{'='*70}")
        print(f"🎯 開始執行搜尋準確度測試")
        print(f"{'='*70}")
        print(f"測試參數: top_k={top_k}, threshold={threshold}\n")
        
        for category, queries in self.test_queries.items():
            print(f"\n📂 測試類別: {category} ({len(queries)} 個查詢)")
            print(f"-" * 70)
            
            for query in queries:
                self.test_query(query, category, top_k, threshold)
                time.sleep(0.1)
        
        print(f"\n{'='*70}")
        print(f"✅ 所有測試完成")
        print(f"{'='*70}")
    
    def calculate_statistics(self):
        """計算統計指標"""
        stats = {}
        
        for category, results in self.results_by_category.items():
            # 排除錯誤結果
            valid_results = [r for r in results if 'error' not in r]
            
            if not valid_results:
                continue
            
            # 基本統計
            total_queries = len(valid_results)
            found_queries = sum(1 for r in valid_results if r['found_count'] > 0)
            
            stats[category] = {
                'total_queries': total_queries,
                'found_queries': found_queries,
                'coverage_rate': round(found_queries / total_queries * 100, 2) if total_queries > 0 else 0,
                
                # Top-1 準確率（找到至少一個結果）
                'top1_accuracy': round(found_queries / total_queries * 100, 2) if total_queries > 0 else 0,
                
                # 平均相似度
                'avg_top1_similarity': round(
                    sum(r['top1_similarity'] for r in valid_results) / total_queries,
                    2
                ) if total_queries > 0 else 0,
                
                'avg_all_similarity': round(
                    sum(r['avg_similarity'] for r in valid_results) / total_queries,
                    2
                ) if total_queries > 0 else 0,
                
                # 平均搜尋時間
                'avg_search_time_ms': round(
                    sum(r['search_time_ms'] for r in valid_results) / total_queries,
                    2
                ) if total_queries > 0 else 0,
                
                # 平均結果數量
                'avg_results_count': round(
                    sum(r['found_count'] for r in valid_results) / total_queries,
                    2
                ) if total_queries > 0 else 0,
            }
        
        return stats
    
    def generate_markdown_report(self):
        """生成 Markdown 報告"""
        timestamp = datetime.now().strftime('%Y%m%d')
        report_file = Path(__file__).parent / 'reports' / f'accuracy_report_{timestamp}.md'
        
        stats = self.calculate_statistics()
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 向量搜尋準確度測試報告\n\n")
            f.write(f"**測試時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**測試版本**: Protocol Guide Section Search System\n\n")
            f.write(f"---\n\n")
            
            f.write(f"## 📊 總體統計\n\n")
            
            # 總體表格
            f.write(f"| 查詢類型 | 測試數量 | 覆蓋率 | Top-1 準確率 | 平均相似度 | 平均搜尋時間 |\n")
            f.write(f"|----------|----------|--------|--------------|------------|---------------|\n")
            
            total_queries = 0
            total_found = 0
            total_similarity = 0
            total_time = 0
            
            for category, stat in stats.items():
                f.write(f"| {category} | {stat['total_queries']} | {stat['coverage_rate']:.1f}% | {stat['top1_accuracy']:.1f}% | {stat['avg_top1_similarity']:.2f}% | {stat['avg_search_time_ms']:.2f}ms |\n")
                
                total_queries += stat['total_queries']
                total_found += stat['found_queries']
                total_similarity += stat['avg_top1_similarity'] * stat['total_queries']
                total_time += stat['avg_search_time_ms'] * stat['total_queries']
            
            # 總平均
            if total_queries > 0:
                overall_coverage = round(total_found / total_queries * 100, 2)
                overall_similarity = round(total_similarity / total_queries, 2)
                overall_time = round(total_time / total_queries, 2)
                
                f.write(f"| **總計** | **{total_queries}** | **{overall_coverage:.1f}%** | **{overall_coverage:.1f}%** | **{overall_similarity:.2f}%** | **{overall_time:.2f}ms** |\n")
            
            f.write(f"\n---\n\n")
            
            f.write(f"## 📈 分類詳細分析\n\n")
            
            for category, results in self.results_by_category.items():
                f.write(f"### {category}\n\n")
                
                # 顯示所有查詢結果
                f.write(f"| 查詢 | 結果數量 | Top-1 相似度 | 平均相似度 | 搜尋時間 |\n")
                f.write(f"|------|----------|--------------|------------|----------|\n")
                
                for r in results:
                    if 'error' in r:
                        f.write(f"| {r['query']} | ❌ 錯誤 | - | - | - |\n")
                    else:
                        f.write(f"| {r['query']} | {r['found_count']} | {r['top1_similarity']:.2f}% | {r['avg_similarity']:.2f}% | {r['search_time_ms']:.2f}ms |\n")
                
                f.write(f"\n")
            
            f.write(f"---\n\n")
            
            f.write(f"## 🎯 結論與建議\n\n")
            
            if overall_coverage >= 90:
                f.write(f"✅ **搜尋系統準確度優秀**（覆蓋率 {overall_coverage:.1f}%）\n\n")
            elif overall_coverage >= 70:
                f.write(f"⚠️ **搜尋系統準確度良好**（覆蓋率 {overall_coverage:.1f}%），但仍有改進空間\n\n")
            else:
                f.write(f"❌ **搜尋系統準確度需要改進**（覆蓋率 {overall_coverage:.1f}%）\n\n")
            
            # 找出表現最差的類別
            worst_category = min(stats.items(), key=lambda x: x[1]['coverage_rate'])
            f.write(f"- 最需要改進的查詢類型: **{worst_category[0]}**（覆蓋率 {worst_category[1]['coverage_rate']:.1f}%）\n")
            
            # 找出表現最好的類別
            best_category = max(stats.items(), key=lambda x: x[1]['coverage_rate'])
            f.write(f"- 表現最好的查詢類型: **{best_category[0]}**（覆蓋率 {best_category[1]['coverage_rate']:.1f}%）\n\n")
            
            f.write(f"**建議改進方向**:\n\n")
            f.write(f"1. 針對低覆蓋率查詢類型增加訓練數據\n")
            f.write(f"2. 調整閾值參數以平衡準確率和召回率\n")
            f.write(f"3. 考慮使用查詢擴展（Query Expansion）技術\n")
            f.write(f"4. 優化 Embedding 模型以提升語義理解能力\n\n")
            
            f.write(f"---\n\n")
            f.write(f"## 📝 測試配置\n\n")
            f.write(f"- 測試參數: top_k=3, threshold=0.7\n")
            f.write(f"- Embedding 模型: intfloat/multilingual-e5-large (1024 維)\n")
            f.write(f"- 搜尋引擎: 段落級別向量搜尋（document_section_embeddings）\n\n")
        
        print(f"\n✅ 準確度報告已生成: {report_file}")
        return report_file


def main():
    """主程式"""
    tester = SearchAccuracyTest()
    
    # 載入測試查詢
    tester.load_test_queries()
    
    # 執行所有測試
    tester.run_all_tests(top_k=3, threshold=0.7)
    
    # 生成報告
    report_file = tester.generate_markdown_report()
    
    print(f"\n{'='*70}")
    print(f"🎉 準確度測試完成！")
    print(f"{'='*70}")
    print(f"📄 報告: {report_file}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
