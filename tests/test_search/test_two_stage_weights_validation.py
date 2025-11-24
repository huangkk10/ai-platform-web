#!/usr/bin/env python3
"""
兩階段權重機制完整驗證腳本
===============================

測試目標：
1. 驗證 stage=1 和 stage=2 是否使用不同的權重配置
2. 驗證權重差異是否會導致搜尋分數的差異
3. 驗證 use_unified_weights 開關是否正常運作

測試場景：
- Scenario 1: use_unified_weights=True（統一模式）
  預期：兩階段使用相同權重，分數應該相同
  
- Scenario 2: use_unified_weights=False（分階段模式）
  預期：兩階段使用不同權重，分數應該不同
  
- Scenario 3: 手動設置明顯不同的權重
  預期：分數差異應該明顯可見
"""

import os
import sys
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ai_platform.settings")
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import SearchThresholdSetting
from django.db import connection


class TwoStageWeightValidator:
    """兩階段權重驗證器"""
    
    def __init__(self):
        self.service = ProtocolGuideSearchService()
        self.assistant_type = "protocol_assistant"
        self.test_query = "IOL"
        
    def print_header(self, title):
        """列印標題"""
        print("\n" + "="*80)
        print(f"  {title}")
        print("="*80)
    
    def print_section(self, title):
        """列印章節"""
        print("\n" + "-"*80)
        print(f"  {title}")
        print("-"*80)
    
    def get_current_config(self):
        """獲取當前配置"""
        setting = SearchThresholdSetting.objects.get(assistant_type=self.assistant_type)
        return {
            'use_unified_weights': setting.use_unified_weights,
            'stage1_title_weight': setting.stage1_title_weight,
            'stage1_content_weight': setting.stage1_content_weight,
            'stage1_threshold': float(setting.stage1_threshold),
            'stage2_title_weight': setting.stage2_title_weight,
            'stage2_content_weight': setting.stage2_content_weight,
            'stage2_threshold': float(setting.stage2_threshold),
        }
    
    def update_config(self, **kwargs):
        """更新配置"""
        setting = SearchThresholdSetting.objects.get(assistant_type=self.assistant_type)
        for key, value in kwargs.items():
            if hasattr(setting, key):
                setattr(setting, key, value)
        setting.save()
        return setting
    
    def execute_search(self, stage, limit=3):
        """執行搜尋"""
        results = self.service.search_knowledge(
            query=self.test_query,
            limit=limit,
            use_vector=True,
            threshold=0.7,
            stage=stage
        )
        return results
    
    def print_search_results(self, results, stage):
        """列印搜尋結果"""
        print(f"\n【Stage {stage} 搜尋結果】")
        print(f"  結果數量: {len(results)}")
        
        if results:
            for i, r in enumerate(results[:3], 1):
                title = r.get("title", "N/A")
                score = r.get("score", 0)
                print(f"  {i}. {title[:45]:<45} | score={score:.6f}")
            
            return results[0].get('score', 0)
        else:
            print("  ❌ 無結果")
            return None
    
    def compare_scores(self, score1, score2, expected_same=True):
        """比較分數並判斷是否符合預期"""
        if score1 is None or score2 is None:
            print("\n【比較結果】❌ 無法比較（缺少分數）")
            return False
        
        diff = abs(score1 - score2)
        diff_percent = (diff / max(score1, score2)) * 100 if max(score1, score2) > 0 else 0
        
        print(f"\n【比較結果】")
        print(f"  Stage 1 分數: {score1:.6f}")
        print(f"  Stage 2 分數: {score2:.6f}")
        print(f"  絕對差異: {diff:.6f}")
        print(f"  百分比差異: {diff_percent:.2f}%")
        
        if expected_same:
            # 預期相同：差異應該 < 0.001
            is_same = diff < 0.001
            if is_same:
                print(f"  ✅ 符合預期：兩階段分數相同（差異 < 0.001）")
                return True
            else:
                print(f"  ❌ 不符預期：兩階段分數應該相同，但差異為 {diff:.6f}")
                return False
        else:
            # 預期不同：差異應該 > 0.001
            is_different = diff > 0.001
            if is_different:
                print(f"  ✅ 符合預期：兩階段分數不同（差異 > 0.001）")
                return True
            else:
                print(f"  ⚠️  注意：兩階段分數應該不同，但差異僅為 {diff:.6f}")
                print(f"  💡 可能原因：權重差異太小，或查詢詞的標題/內容相似度非常接近")
                return False
    
    def scenario_1_unified_mode(self):
        """場景 1：統一模式測試"""
        self.print_header("場景 1：統一模式測試 (use_unified_weights=True)")
        
        # 設置統一模式
        self.update_config(use_unified_weights=True)
        
        config = self.get_current_config()
        print(f"\n【配置資訊】")
        print(f"  統一模式: {config['use_unified_weights']}")
        print(f"  第一階段: 標題 {config['stage1_title_weight']}% / 內容 {config['stage1_content_weight']}% / threshold {config['stage1_threshold']}")
        print(f"  第二階段: 標題 {config['stage2_title_weight']}% / 內容 {config['stage2_content_weight']}% / threshold {config['stage2_threshold']}")
        print(f"\n💡 預期：兩階段都使用第一階段配置（{config['stage1_title_weight']}%/{config['stage1_content_weight']}%），分數應該相同")
        
        # 執行搜尋
        self.print_section("執行搜尋")
        results_s1 = self.execute_search(stage=1)
        score1 = self.print_search_results(results_s1, stage=1)
        
        results_s2 = self.execute_search(stage=2)
        score2 = self.print_search_results(results_s2, stage=2)
        
        # 比較結果
        return self.compare_scores(score1, score2, expected_same=True)
    
    def scenario_2_separate_mode(self):
        """場景 2：分階段模式測試"""
        self.print_header("場景 2：分階段模式測試 (use_unified_weights=False)")
        
        # 設置分階段模式
        self.update_config(use_unified_weights=False)
        
        config = self.get_current_config()
        print(f"\n【配置資訊】")
        print(f"  統一模式: {config['use_unified_weights']}")
        print(f"  第一階段: 標題 {config['stage1_title_weight']}% / 內容 {config['stage1_content_weight']}% / threshold {config['stage1_threshold']}")
        print(f"  第二階段: 標題 {config['stage2_title_weight']}% / 內容 {config['stage2_content_weight']}% / threshold {config['stage2_threshold']}")
        print(f"\n💡 預期：Stage 1 使用 {config['stage1_title_weight']}%/{config['stage1_content_weight']}%，Stage 2 使用 {config['stage2_title_weight']}%/{config['stage2_content_weight']}%，分數應該不同")
        
        # 執行搜尋
        self.print_section("執行搜尋")
        results_s1 = self.execute_search(stage=1)
        score1 = self.print_search_results(results_s1, stage=1)
        
        results_s2 = self.execute_search(stage=2)
        score2 = self.print_search_results(results_s2, stage=2)
        
        # 比較結果
        return self.compare_scores(score1, score2, expected_same=False)
    
    def scenario_3_extreme_difference(self):
        """場景 3：極端差異測試"""
        self.print_header("場景 3：極端差異測試（誇張權重差異）")
        
        # 設置極端差異的權重
        print("\n【設置極端配置】")
        print("  Stage 1: 標題 90% / 內容 10% (極度重視標題)")
        print("  Stage 2: 標題 10% / 內容 90% (極度重視內容)")
        
        self.update_config(
            use_unified_weights=False,
            stage1_title_weight=90,
            stage1_content_weight=10,
            stage2_title_weight=10,
            stage2_content_weight=90
        )
        
        print(f"\n💡 預期：權重差異極大（90/10 vs 10/90），分數差異應該非常明顯")
        
        # 執行搜尋
        self.print_section("執行搜尋")
        results_s1 = self.execute_search(stage=1)
        score1 = self.print_search_results(results_s1, stage=1)
        
        results_s2 = self.execute_search(stage=2)
        score2 = self.print_search_results(results_s2, stage=2)
        
        # 比較結果（預期差異很大）
        if score1 is not None and score2 is not None:
            diff = abs(score1 - score2)
            diff_percent = (diff / max(score1, score2)) * 100
            
            print(f"\n【比較結果】")
            print(f"  Stage 1 分數: {score1:.6f}")
            print(f"  Stage 2 分數: {score2:.6f}")
            print(f"  絕對差異: {diff:.6f}")
            print(f"  百分比差異: {diff_percent:.2f}%")
            
            if diff > 0.05:  # 期望差異 > 5%
                print(f"  ✅ 極端差異測試成功：分數差異明顯（> 0.05）")
                return True
            else:
                print(f"  ⚠️  差異小於預期：可能標題和內容的相似度本身就很接近")
                return False
        else:
            print("\n【比較結果】❌ 無法比較（缺少分數）")
            return False
    
    def scenario_4_query_analysis(self):
        """場景 4：查詢詞分析（瞭解為什麼權重影響不大）"""
        self.print_header("場景 4：查詢詞分析（瞭解標題/內容相似度）")
        
        print(f"\n【分析查詢】: '{self.test_query}'")
        print("\n💡 目的：直接查詢資料庫，瞭解標題和內容的獨立相似度")
        
        # 使用分階段模式（90/10 vs 10/90）
        self.update_config(
            use_unified_weights=False,
            stage1_title_weight=90,
            stage1_content_weight=10,
            stage2_title_weight=10,
            stage2_content_weight=90
        )
        
        # 直接查詢資料庫，獲取詳細的相似度資訊
        try:
            from api.services.embedding_service import get_embedding_service
            
            embedding_service = get_embedding_service('ultra_high')
            query_embedding = embedding_service.generate_embedding(self.test_query)
            embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
            
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        dse.section_id,
                        dse.heading_text,
                        pg.title as doc_title,
                        (1 - (dse.title_embedding <=> %s::vector)) as title_similarity,
                        (1 - (dse.content_embedding <=> %s::vector)) as content_similarity,
                        (0.9 * (1 - (dse.title_embedding <=> %s::vector))) + 
                        (0.1 * (1 - (dse.content_embedding <=> %s::vector))) as weighted_90_10,
                        (0.1 * (1 - (dse.title_embedding <=> %s::vector))) + 
                        (0.9 * (1 - (dse.content_embedding <=> %s::vector))) as weighted_10_90
                    FROM document_section_embeddings dse
                    LEFT JOIN protocol_guide pg ON pg.id = dse.source_id
                    WHERE dse.source_table = 'protocol_guide'
                      AND dse.title_embedding IS NOT NULL
                      AND dse.content_embedding IS NOT NULL
                    ORDER BY title_similarity DESC
                    LIMIT 5
                """, [embedding_str] * 6)
                
                rows = cursor.fetchall()
                
                print("\n【前 5 個段落的詳細相似度】")
                print(f"{'段落':<30} {'標題相似度':<12} {'內容相似度':<12} {'90/10權重':<12} {'10/90權重':<12} {'差異':<10}")
                print("-" * 100)
                
                for row in rows:
                    section_id, heading, doc_title, title_sim, content_sim, w90_10, w10_90 = row
                    diff = abs(w90_10 - w10_90)
                    
                    display_name = heading[:28] if heading else doc_title[:28]
                    print(f"{display_name:<30} {title_sim:<12.6f} {content_sim:<12.6f} {w90_10:<12.6f} {w10_90:<12.6f} {diff:<10.6f}")
                
                # 分析結果
                if rows:
                    first = rows[0]
                    title_sim = first[3]
                    content_sim = first[4]
                    
                    print(f"\n【分析】")
                    print(f"  最相關段落: {first[1] or first[2]}")
                    print(f"  標題相似度: {title_sim:.6f}")
                    print(f"  內容相似度: {content_sim:.6f}")
                    print(f"  相似度差異: {abs(title_sim - content_sim):.6f}")
                    
                    if abs(title_sim - content_sim) < 0.05:
                        print(f"  💡 結論：標題和內容的相似度非常接近（差異 < 0.05）")
                        print(f"          因此權重改變對最終分數的影響有限")
                    else:
                        print(f"  💡 結論：標題和內容的相似度有明顯差異")
                        print(f"          改變權重應該會顯著影響最終分數")
                
        except Exception as e:
            print(f"\n❌ 分析失敗: {str(e)}")
            return False
        
        return True
    
    def restore_original_config(self):
        """恢復原始配置"""
        print("\n" + "="*80)
        print("  恢復原始配置")
        print("="*80)
        
        self.update_config(
            use_unified_weights=True,
            stage1_title_weight=60,
            stage1_content_weight=40,
            stage2_title_weight=50,
            stage2_content_weight=50
        )
        
        print("✅ 已恢復為預設配置：")
        print("   - use_unified_weights=True")
        print("   - Stage 1: 60%/40%")
        print("   - Stage 2: 50%/50%")
    
    def run_all_tests(self):
        """執行所有測試"""
        self.print_header("🔬 兩階段權重機制完整驗證")
        print(f"\n測試查詢: '{self.test_query}'")
        print(f"助手類型: {self.assistant_type}")
        
        results = {}
        
        # 場景 1：統一模式
        results['scenario_1'] = self.scenario_1_unified_mode()
        
        # 場景 2：分階段模式
        results['scenario_2'] = self.scenario_2_separate_mode()
        
        # 場景 3：極端差異
        results['scenario_3'] = self.scenario_3_extreme_difference()
        
        # 場景 4：查詢分析
        results['scenario_4'] = self.scenario_4_query_analysis()
        
        # 恢復原始配置
        self.restore_original_config()
        
        # 總結
        self.print_header("📊 測試總結")
        
        print("\n【測試結果】")
        for scenario, passed in results.items():
            status = "✅ 通過" if passed else "❌ 失敗"
            scenario_name = {
                'scenario_1': '場景 1: 統一模式',
                'scenario_2': '場景 2: 分階段模式',
                'scenario_3': '場景 3: 極端差異',
                'scenario_4': '場景 4: 查詢分析'
            }.get(scenario, scenario)
            print(f"  {scenario_name:<25} {status}")
        
        total_passed = sum(1 for p in results.values() if p)
        total_tests = len(results)
        
        print(f"\n【通過率】{total_passed}/{total_tests} ({total_passed/total_tests*100:.0f}%)")
        
        if all(results.values()):
            print("\n🎉 所有測試通過！兩階段權重機制運作正常。")
        else:
            print("\n⚠️  部分測試未通過，請檢查日誌分析原因。")
        
        return all(results.values())


def main():
    """主程式"""
    validator = TwoStageWeightValidator()
    
    try:
        success = validator.run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
