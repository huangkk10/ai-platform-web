#!/usr/bin/env python
"""
向量搜尋效能專項測試

功能：
1. 測試單次搜尋耗時
2. 測試批量搜尋耗時
3. 測試不同參數對效能的影響
4. 壓力測試（連續/並發搜尋）
5. 生成效能報告

使用方式：
    python tests/test_vector_search/test_search_performance.py

輸出：
    - reports/performance_YYYYMMDD.json (詳細數據)
    - reports/performance_YYYYMMDD.md (總結報告)
"""

import os
import sys
import json
import time
import statistics
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 添加專案根目錄到 Python 路徑
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Django 環境設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
import django
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService


class SearchPerformanceTest:
    """搜尋效能測試類別"""
    
    def __init__(self):
        self.service = SectionSearchService()
        self.test_queries = []
        self.results = {
            'single_search': [],
            'batch_search': [],
            'parameter_impact': {},
            'stress_test': {},
        }
    
    def load_test_queries(self):
        """載入測試查詢"""
        test_data_file = Path(__file__).parent / 'test_data' / 'test_queries.json'
        
        if test_data_file.exists():
            with open(test_data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for category in ['basic_queries', 'technical_queries', 'semantic_queries']:
                    if category in data:
                        self.test_queries.extend(data[category][:5])  # 每類取 5 個
        else:
            self.test_queries = [
                "ULINK 連接失敗",
                "測試環境準備",
                "OpenCV 版本相容性",
                "pytest fixture 使用",
                "如何除錯程式",
            ]
        
        print(f"✅ 載入 {len(self.test_queries)} 個測試查詢")
        return self.test_queries
    
    def test_single_search(self, query, top_k=3, threshold=0.7, iterations=10):
        """測試單次搜尋效能（多次測量取平均）"""
        times = []
        
        for i in range(iterations):
            start_time = time.time()
            results = self.service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=top_k,
                threshold=threshold
            )
            elapsed = (time.time() - start_time) * 1000  # 毫秒
            times.append(elapsed)
        
        # 計算統計指標
        result = {
            'query': query,
            'iterations': iterations,
            'times_ms': times,
            'avg_ms': round(statistics.mean(times), 2),
            'median_ms': round(statistics.median(times), 2),
            'min_ms': round(min(times), 2),
            'max_ms': round(max(times), 2),
            'std_ms': round(statistics.stdev(times), 2) if len(times) > 1 else 0,
            'found_count': len(results),
        }
        
        self.results['single_search'].append(result)
        
        print(f"  ✓ {query}: 平均 {result['avg_ms']:.2f}ms (中位數 {result['median_ms']:.2f}ms)")
        
        return result
    
    def test_batch_search(self, queries, top_k=3, threshold=0.7):
        """測試批量搜尋效能"""
        print(f"\n📦 測試批量搜尋 ({len(queries)} 個查詢)")
        
        start_time = time.time()
        results_list = []
        
        for query in queries:
            results = self.service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=top_k,
                threshold=threshold
            )
            results_list.append(results)
        
        total_time = (time.time() - start_time) * 1000
        avg_time = total_time / len(queries)
        
        result = {
            'total_queries': len(queries),
            'total_time_ms': round(total_time, 2),
            'avg_time_per_query_ms': round(avg_time, 2),
            'queries_per_second': round(1000 / avg_time, 2),
        }
        
        self.results['batch_search'] = result
        
        print(f"  ✓ 總耗時: {total_time:.2f}ms")
        print(f"  ✓ 平均每個查詢: {avg_time:.2f}ms")
        print(f"  ✓ 吞吐量: {result['queries_per_second']:.2f} queries/sec")
        
        return result
    
    def test_parameter_impact(self, query="ULINK 連接失敗"):
        """測試不同參數對效能的影響"""
        print(f"\n⚙️ 測試參數影響")
        
        # 測試不同 top_k
        print(f"  測試不同 top_k 值...")
        top_k_results = {}
        for k in [1, 3, 5, 10]:
            times = []
            for _ in range(5):
                start_time = time.time()
                results = self.service.search_sections(query=query, source_table='protocol_guide', limit=k, threshold=0.7)
                times.append((time.time() - start_time) * 1000)
            
            avg_time = statistics.mean(times)
            top_k_results[k] = {
                'avg_time_ms': round(avg_time, 2),
                'found_count': len(results),
            }
            print(f"    top_k={k}: {avg_time:.2f}ms ({len(results)} 個結果)")
        
        self.results['parameter_impact']['top_k'] = top_k_results
        
        # 測試不同 threshold
        print(f"  測試不同 threshold 值...")
        threshold_results = {}
        for t in [0.5, 0.6, 0.7, 0.8, 0.9]:
            times = []
            for _ in range(5):
                start_time = time.time()
                results = self.service.search_sections(query=query, source_table='protocol_guide', limit=3, threshold=t)
                times.append((time.time() - start_time) * 1000)
            
            avg_time = statistics.mean(times)
            threshold_results[t] = {
                'avg_time_ms': round(avg_time, 2),
                'found_count': len(results),
            }
            print(f"    threshold={t}: {avg_time:.2f}ms ({len(results)} 個結果)")
        
        self.results['parameter_impact']['threshold'] = threshold_results
        
        return self.results['parameter_impact']
    
    def test_stress_continuous(self, query="ULINK 連接失敗", iterations=100):
        """壓力測試：連續搜尋"""
        print(f"\n🔥 壓力測試：連續執行 {iterations} 次")
        
        times = []
        errors = 0
        
        start_time = time.time()
        
        for i in range(iterations):
            try:
                search_start = time.time()
                results = self.service.search_sections(query=query, source_table='protocol_guide', limit=3, threshold=0.7)
                search_time = (time.time() - search_start) * 1000
                times.append(search_time)
                
                if (i + 1) % 20 == 0:
                    print(f"  進度: {i+1}/{iterations}")
                    
            except Exception as e:
                errors += 1
                print(f"  ✗ 錯誤: {str(e)}")
        
        total_time = (time.time() - start_time) * 1000
        
        result = {
            'iterations': iterations,
            'successful': len(times),
            'errors': errors,
            'total_time_ms': round(total_time, 2),
            'avg_time_ms': round(statistics.mean(times), 2) if times else 0,
            'median_time_ms': round(statistics.median(times), 2) if times else 0,
            'p95_time_ms': round(statistics.quantiles(times, n=20)[18], 2) if len(times) >= 20 else 0,
            'p99_time_ms': round(statistics.quantiles(times, n=100)[98], 2) if len(times) >= 100 else 0,
            'min_time_ms': round(min(times), 2) if times else 0,
            'max_time_ms': round(max(times), 2) if times else 0,
            'std_time_ms': round(statistics.stdev(times), 2) if len(times) > 1 else 0,
            'throughput_qps': round(len(times) / (total_time / 1000), 2) if total_time > 0 else 0,
        }
        
        self.results['stress_test']['continuous'] = result
        
        print(f"  ✓ 成功: {result['successful']}/{iterations}")
        print(f"  ✓ 平均耗時: {result['avg_time_ms']:.2f}ms")
        print(f"  ✓ P95 耗時: {result['p95_time_ms']:.2f}ms")
        print(f"  ✓ P99 耗時: {result['p99_time_ms']:.2f}ms")
        print(f"  ✓ 吞吐量: {result['throughput_qps']:.2f} QPS")
        
        return result
    
    def test_stress_concurrent(self, query="ULINK 連接失敗", workers=10, iterations_per_worker=10):
        """壓力測試：並發搜尋"""
        print(f"\n🔥 壓力測試：{workers} 個並發 worker，每個執行 {iterations_per_worker} 次")
        
        def worker_task(worker_id):
            times = []
            for i in range(iterations_per_worker):
                try:
                    start = time.time()
                    results = self.service.search_sections(query=query, source_table='protocol_guide', limit=3, threshold=0.7)
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
                except Exception as e:
                    pass
            return times
        
        start_time = time.time()
        all_times = []
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(worker_task, i) for i in range(workers)]
            
            for future in as_completed(futures):
                try:
                    times = future.result()
                    all_times.extend(times)
                except Exception as e:
                    print(f"  ✗ Worker 錯誤: {str(e)}")
        
        total_time = (time.time() - start_time) * 1000
        
        result = {
            'workers': workers,
            'iterations_per_worker': iterations_per_worker,
            'total_requests': workers * iterations_per_worker,
            'successful': len(all_times),
            'total_time_ms': round(total_time, 2),
            'avg_time_ms': round(statistics.mean(all_times), 2) if all_times else 0,
            'median_time_ms': round(statistics.median(all_times), 2) if all_times else 0,
            'p95_time_ms': round(statistics.quantiles(all_times, n=20)[18], 2) if len(all_times) >= 20 else 0,
            'min_time_ms': round(min(all_times), 2) if all_times else 0,
            'max_time_ms': round(max(all_times), 2) if all_times else 0,
            'throughput_qps': round(len(all_times) / (total_time / 1000), 2) if total_time > 0 else 0,
        }
        
        self.results['stress_test']['concurrent'] = result
        
        print(f"  ✓ 成功: {result['successful']}/{result['total_requests']}")
        print(f"  ✓ 總耗時: {result['total_time_ms']:.2f}ms")
        print(f"  ✓ 平均耗時: {result['avg_time_ms']:.2f}ms")
        print(f"  ✓ P95 耗時: {result['p95_time_ms']:.2f}ms")
        print(f"  ✓ 吞吐量: {result['throughput_qps']:.2f} QPS")
        
        return result
    
    def run_all_tests(self):
        """執行所有效能測試"""
        print(f"\n{'='*70}")
        print(f"⚡ 開始執行搜尋效能測試")
        print(f"{'='*70}\n")
        
        # 1. 單次搜尋測試
        print(f"🔍 測試 1: 單次搜尋效能")
        print(f"-" * 70)
        for query in self.test_queries[:3]:  # 測試前 3 個
            self.test_single_search(query, iterations=10)
        
        # 2. 批量搜尋測試
        print(f"\n")
        self.test_batch_search(self.test_queries)
        
        # 3. 參數影響測試
        print(f"\n")
        self.test_parameter_impact()
        
        # 4. 壓力測試：連續
        print(f"\n")
        self.test_stress_continuous(iterations=100)
        
        # 5. 壓力測試：並發
        print(f"\n")
        self.test_stress_concurrent(workers=5, iterations_per_worker=10)
        
        print(f"\n{'='*70}")
        print(f"✅ 所有效能測試完成")
        print(f"{'='*70}")
    
    def save_json_report(self):
        """儲存 JSON 詳細數據"""
        timestamp = datetime.now().strftime('%Y%m%d')
        report_file = Path(__file__).parent / 'reports' / f'performance_{timestamp}.json'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        print(f"✅ JSON 報告已生成: {report_file}")
        return report_file
    
    def generate_markdown_report(self):
        """生成 Markdown 報告"""
        timestamp = datetime.now().strftime('%Y%m%d')
        report_file = Path(__file__).parent / 'reports' / f'performance_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"# 向量搜尋效能測試報告\n\n")
            f.write(f"**測試時間**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**測試版本**: Protocol Guide Section Search System\n\n")
            f.write(f"---\n\n")
            
            # 1. 單次搜尋效能
            f.write(f"## 🔍 單次搜尋效能\n\n")
            f.write(f"| 查詢 | 平均耗時 | 中位數 | 最小值 | 最大值 | 標準差 |\n")
            f.write(f"|------|----------|--------|--------|--------|--------|\n")
            
            for result in self.results['single_search']:
                f.write(f"| {result['query']} | {result['avg_ms']:.2f}ms | {result['median_ms']:.2f}ms | {result['min_ms']:.2f}ms | {result['max_ms']:.2f}ms | {result['std_ms']:.2f}ms |\n")
            
            f.write(f"\n")
            
            # 2. 批量搜尋效能
            batch = self.results['batch_search']
            f.write(f"## 📦 批量搜尋效能\n\n")
            f.write(f"- 總查詢數: {batch['total_queries']}\n")
            f.write(f"- 總耗時: {batch['total_time_ms']:.2f}ms\n")
            f.write(f"- 平均每個查詢: {batch['avg_time_per_query_ms']:.2f}ms\n")
            f.write(f"- 吞吐量: **{batch['queries_per_second']:.2f} queries/sec**\n\n")
            
            # 3. 參數影響
            f.write(f"## ⚙️ 參數影響分析\n\n")
            
            f.write(f"### top_k 參數影響\n\n")
            f.write(f"| top_k | 平均耗時 | 結果數量 |\n")
            f.write(f"|-------|----------|----------|\n")
            for k, data in self.results['parameter_impact']['top_k'].items():
                f.write(f"| {k} | {data['avg_time_ms']:.2f}ms | {data['found_count']} |\n")
            f.write(f"\n")
            
            f.write(f"### threshold 參數影響\n\n")
            f.write(f"| threshold | 平均耗時 | 結果數量 |\n")
            f.write(f"|-----------|----------|----------|\n")
            for t, data in self.results['parameter_impact']['threshold'].items():
                f.write(f"| {t} | {data['avg_time_ms']:.2f}ms | {data['found_count']} |\n")
            f.write(f"\n")
            
            # 4. 壓力測試
            f.write(f"## 🔥 壓力測試結果\n\n")
            
            continuous = self.results['stress_test']['continuous']
            f.write(f"### 連續搜尋測試\n\n")
            f.write(f"- 執行次數: {continuous['iterations']}\n")
            f.write(f"- 成功次數: {continuous['successful']}\n")
            f.write(f"- 平均耗時: {continuous['avg_time_ms']:.2f}ms\n")
            f.write(f"- 中位數耗時: {continuous['median_time_ms']:.2f}ms\n")
            f.write(f"- P95 耗時: {continuous['p95_time_ms']:.2f}ms\n")
            f.write(f"- P99 耗時: {continuous['p99_time_ms']:.2f}ms\n")
            f.write(f"- 吞吐量: **{continuous['throughput_qps']:.2f} QPS**\n\n")
            
            concurrent = self.results['stress_test']['concurrent']
            f.write(f"### 並發搜尋測試\n\n")
            f.write(f"- 並發數: {concurrent['workers']}\n")
            f.write(f"- 每個 worker 執行: {concurrent['iterations_per_worker']} 次\n")
            f.write(f"- 總請求數: {concurrent['total_requests']}\n")
            f.write(f"- 成功次數: {concurrent['successful']}\n")
            f.write(f"- 平均耗時: {concurrent['avg_time_ms']:.2f}ms\n")
            f.write(f"- P95 耗時: {concurrent['p95_time_ms']:.2f}ms\n")
            f.write(f"- 吞吐量: **{concurrent['throughput_qps']:.2f} QPS**\n\n")
            
            # 5. 結論
            f.write(f"---\n\n")
            f.write(f"## 🎯 結論與建議\n\n")
            
            avg_single = statistics.mean([r['avg_ms'] for r in self.results['single_search']])
            
            if avg_single < 100:
                f.write(f"✅ **搜尋效能優秀**（平均 {avg_single:.2f}ms）\n\n")
            elif avg_single < 200:
                f.write(f"⚠️ **搜尋效能良好**（平均 {avg_single:.2f}ms），可接受\n\n")
            else:
                f.write(f"❌ **搜尋效能需要優化**（平均 {avg_single:.2f}ms）\n\n")
            
            f.write(f"**最佳實踐建議**:\n\n")
            f.write(f"1. **建議 top_k**: 3-5（效能與準確度的平衡點）\n")
            f.write(f"2. **建議 threshold**: 0.7（覆蓋率與精確度的平衡點）\n")
            f.write(f"3. **並發處理能力**: 系統可承受 {concurrent['workers']} 個並發請求\n")
            f.write(f"4. **預期吞吐量**: {continuous['throughput_qps']:.2f} QPS\n\n")
            
            f.write(f"---\n\n")
            f.write(f"## 📝 測試環境\n\n")
            f.write(f"- 資料庫: PostgreSQL + pgvector\n")
            f.write(f"- Embedding 模型: intfloat/multilingual-e5-large (1024 維)\n")
            f.write(f"- 索引類型: IVFFlat (cosine similarity)\n")
            f.write(f"- 測試數據: Protocol Guide 段落向量（document_section_embeddings）\n\n")
        
        print(f"✅ Markdown 報告已生成: {report_file}")
        return report_file


def main():
    """主程式"""
    tester = SearchPerformanceTest()
    
    # 載入測試查詢
    tester.load_test_queries()
    
    # 執行所有測試
    tester.run_all_tests()
    
    # 生成報告
    json_file = tester.save_json_report()
    md_file = tester.generate_markdown_report()
    
    print(f"\n{'='*70}")
    print(f"🎉 效能測試完成！")
    print(f"{'='*70}")
    print(f"📄 JSON 報告: {json_file}")
    print(f"📄 Markdown 報告: {md_file}")
    print(f"{'='*70}\n")


if __name__ == '__main__':
    main()
