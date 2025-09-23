"""
Django 管理命令：比較 768 維 vs 1024 維向量搜索效能
"""
from django.core.management.base import BaseCommand
from api.services.embedding_service import (
    get_embedding_service, 
    search_rvt_guide_with_vectors,
    search_rvt_guide_with_vectors_1024
)
from django.db import connection
import time
import json
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '比較 768 維 vs 1024 維向量搜索效能'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--queries',
            nargs='+',
            default=[
                "Jenkins 測試階段",
                "RVT 系統架構",
                "Ansible 配置參數",
                "系統安裝要求",
                "常見問題排除",
                "測試環境設定"
            ],
            help='測試查詢列表',
        )
        parser.add_argument(
            '--iterations',
            type=int,
            default=3,
            help='每個查詢的測試次數（預設: 3）',
        )
    
    def handle(self, *args, **options):
        queries = options['queries']
        iterations = options['iterations']
        
        self.stdout.write(
            self.style.HTTP_INFO("🔍 開始向量搜索效能比較測試")
        )
        self.stdout.write(f"📊 測試配置:")
        self.stdout.write(f"   - 測試查詢數量: {len(queries)}")
        self.stdout.write(f"   - 每查詢測試次數: {iterations}")
        self.stdout.write(f"   - 總測試次數: {len(queries) * iterations * 2}")
        
        # 檢查資料完整性
        self._check_data_availability()
        
        # 執行比較測試
        results_768 = []
        results_1024 = []
        
        self.stdout.write("\n" + "="*60)
        self.stdout.write("🚀 開始效能測試...")
        
        for i, query in enumerate(queries, 1):
            self.stdout.write(f"\n📝 測試查詢 {i}/{len(queries)}: \"{query}\"")
            
            # 測試 768 維搜索
            times_768, accuracy_768 = self._test_search_performance(
                query, search_rvt_guide_with_vectors, "768維", iterations
            )
            results_768.extend(times_768)
            
            # 測試 1024 維搜索
            times_1024, accuracy_1024 = self._test_search_performance(
                query, search_rvt_guide_with_vectors_1024, "1024維", iterations
            )
            results_1024.extend(times_1024)
            
            # 顯示此次查詢的比較結果
            avg_768 = sum(times_768) / len(times_768)
            avg_1024 = sum(times_1024) / len(times_1024)
            
            self.stdout.write(f"   📊 平均響應時間比較:")
            self.stdout.write(f"      - 768維: {avg_768:.3f}秒 (找到 {len(accuracy_768)} 個結果)")
            self.stdout.write(f"      - 1024維: {avg_1024:.3f}秒 (找到 {len(accuracy_1024)} 個結果)")
            
            if avg_1024 < avg_768:
                improvement = ((avg_768 - avg_1024) / avg_768) * 100
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ 1024維快 {improvement:.1f}%")
                )
            elif avg_1024 > avg_768:
                degradation = ((avg_1024 - avg_768) / avg_768) * 100
                self.stdout.write(
                    self.style.WARNING(f"   ⚠️ 1024維慢 {degradation:.1f}%")
                )
            else:
                self.stdout.write("   ⚖️ 性能相當")
        
        # 生成最終報告
        self._generate_final_report(results_768, results_1024, queries)
        
        # 檢查儲存空間差異
        self._check_storage_usage()
    
    def _check_data_availability(self):
        """檢查資料可用性"""
        self.stdout.write("\n🔍 檢查資料可用性...")
        
        with connection.cursor() as cursor:
            # 檢查 768 維資料
            cursor.execute("SELECT COUNT(*) FROM document_embeddings WHERE source_table = 'rvt_guide'")
            count_768 = cursor.fetchone()[0]
            
            # 檢查 1024 維資料
            cursor.execute("SELECT COUNT(*) FROM document_embeddings_1024 WHERE source_table = 'rvt_guide'")
            count_1024 = cursor.fetchone()[0]
            
            self.stdout.write(f"   - 768維資料: {count_768} 筆")
            self.stdout.write(f"   - 1024維資料: {count_1024} 筆")
            
            if count_768 == 0 or count_1024 == 0:
                self.stdout.write(
                    self.style.ERROR("❌ 缺少必要的向量資料，請先執行嵌入生成命令")
                )
                raise Exception("資料不完整，無法進行比較測試")
            
            self.stdout.write(
                self.style.SUCCESS("✅ 資料檢查通過")
            )
    
    def _test_search_performance(self, query, search_function, version, iterations):
        """測試搜索效能"""
        times = []
        results = []
        
        for i in range(iterations):
            start_time = time.time()
            
            try:
                search_results = search_function(query, limit=5, threshold=0.2)
                end_time = time.time()
                
                execution_time = end_time - start_time
                times.append(execution_time)
                results = search_results  # 保存最後一次結果用於準確度分析
                
                self.stdout.write(f"      {version} 第{i+1}次: {execution_time:.3f}秒")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"      {version} 第{i+1}次: 錯誤 - {str(e)}")
                )
                times.append(float('inf'))  # 錯誤時記錄無限大時間
        
        return times, results
    
    def _generate_final_report(self, results_768, results_1024, queries):
        """生成最終比較報告"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("📊 最終效能比較報告")
        self.stdout.write("="*60)
        
        # 過濾無效結果
        valid_768 = [t for t in results_768 if t != float('inf')]
        valid_1024 = [t for t in results_1024 if t != float('inf')]
        
        if not valid_768 or not valid_1024:
            self.stdout.write(
                self.style.ERROR("❌ 測試資料不足，無法生成報告")
            )
            return
        
        # 計算統計數據
        avg_768 = sum(valid_768) / len(valid_768)
        avg_1024 = sum(valid_1024) / len(valid_1024)
        
        min_768 = min(valid_768)
        min_1024 = min(valid_1024)
        
        max_768 = max(valid_768)
        max_1024 = max(valid_1024)
        
        # 顯示統計結果
        self.stdout.write("⏱️  響應時間統計:")
        self.stdout.write(f"   768維模型 (paraphrase-multilingual-mpnet-base-v2):")
        self.stdout.write(f"      - 平均時間: {avg_768:.3f}秒")
        self.stdout.write(f"      - 最快時間: {min_768:.3f}秒")
        self.stdout.write(f"      - 最慢時間: {max_768:.3f}秒")
        self.stdout.write(f"      - 有效測試: {len(valid_768)}/{len(results_768)} 次")
        
        self.stdout.write(f"   1024維模型 (multilingual-e5-large):")
        self.stdout.write(f"      - 平均時間: {avg_1024:.3f}秒")
        self.stdout.write(f"      - 最快時間: {min_1024:.3f}秒")
        self.stdout.write(f"      - 最慢時間: {max_1024:.3f}秒")
        self.stdout.write(f"      - 有效測試: {len(valid_1024)}/{len(results_1024)} 次")
        
        # 計算改進幅度
        if avg_1024 < avg_768:
            improvement = ((avg_768 - avg_1024) / avg_768) * 100
            self.stdout.write("\n🎉 效能結論:")
            self.stdout.write(
                self.style.SUCCESS(f"✅ 1024維模型平均快 {improvement:.1f}%")
            )
        elif avg_1024 > avg_768:
            degradation = ((avg_1024 - avg_768) / avg_768) * 100
            self.stdout.write("\n⚠️  效能結論:")
            self.stdout.write(
                self.style.WARNING(f"⚠️ 1024維模型平均慢 {degradation:.1f}%")
            )
        else:
            self.stdout.write("\n⚖️  效能結論:")
            self.stdout.write("⚖️ 兩個模型效能相當")
        
        # 模型品質比較
        self.stdout.write("\n🎯 模型特性比較:")
        self.stdout.write("   768維模型 (paraphrase-multilingual-mpnet-base-v2):")
        self.stdout.write("      ✅ 更快的推理速度")
        self.stdout.write("      ✅ 更小的儲存空間需求")
        self.stdout.write("      ⚖️ 標準的多語言支援")
        
        self.stdout.write("   1024維模型 (multilingual-e5-large):")
        self.stdout.write("      ✅ 更高的語義理解能力")
        self.stdout.write("      ✅ 更好的長文本處理")
        self.stdout.write("      ✅ 更先進的模型架構")
        self.stdout.write("      ⚠️ 更大的資源消耗")
    
    def _check_storage_usage(self):
        """檢查儲存空間使用情況"""
        self.stdout.write("\n💾 儲存空間使用情況:")
        
        with connection.cursor() as cursor:
            # 檢查表格大小
            cursor.execute("""
                SELECT 
                    schemaname,
                    tablename,
                    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
                    pg_total_relation_size(schemaname||'.'||tablename) as bytes
                FROM pg_tables 
                WHERE tablename IN ('document_embeddings', 'document_embeddings_1024')
                ORDER BY bytes DESC;
            """)
            
            for row in cursor.fetchall():
                schema, table, size, bytes_size = row
                if table == 'document_embeddings':
                    self.stdout.write(f"   📊 768維表格 ({table}): {size}")
                elif table == 'document_embeddings_1024':
                    self.stdout.write(f"   📊 1024維表格 ({table}): {size}")
            
            # 計算向量欄位大小差異
            vector_768_size = 768 * 4  # 4 bytes per float
            vector_1024_size = 1024 * 4  # 4 bytes per float
            
            self.stdout.write(f"\n🔢 向量資料大小比較:")
            self.stdout.write(f"   - 768維向量: {vector_768_size} bytes ({vector_768_size/1024:.2f} KB)")
            self.stdout.write(f"   - 1024維向量: {vector_1024_size} bytes ({vector_1024_size/1024:.2f} KB)")
            
            size_increase = ((vector_1024_size - vector_768_size) / vector_768_size) * 100
            self.stdout.write(f"   - 儲存空間增加: {size_increase:.1f}%")