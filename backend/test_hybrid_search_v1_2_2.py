"""
Dify v1.2.2 混合搜尋驗證測試（10 條驗證問題）
================================================

測試目標：
1. 驗證混合搜尋（RRF + Title Boost）相比 v1.2.1 的準確度提升
2. 確保語義理解能力不被削弱
3. 驗證 Dify 外部知識庫整合正常

執行方式：
    docker exec ai-django python backend/test_hybrid_search_v1_2_2.py

作者：AI Platform Team
日期：2025-11-27
"""

import os
import sys
import django
from datetime import datetime

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import DifyConfigVersion

# ========== 測試題庫定義 ==========

TEST_QUERIES = [
    # ==================== 類型 1: 精確關鍵字查詢（混合搜尋優勢） ====================
    {
        'id': 1,
        'query': 'iol 密碼',
        'type': '精確關鍵字',
        'expected_keywords': ['密碼', 'password', '1'],
        'expected_rank': 1,  # 期望排名第 1
        'baseline_rank': 5,  # v1.2.1 基準排名第 5
        'description': '測試關鍵字「密碼」的精確匹配能力'
    },
    {
        'id': 2,
        'query': 'sudo 密碼',
        'type': '精確關鍵字',
        'expected_keywords': ['sudo', '密碼'],
        'expected_rank': 1,
        'baseline_rank': 3,
        'description': '測試複合關鍵字查詢'
    },
    {
        'id': 3,
        'query': 'IOL 執行檔路徑',
        'type': '精確關鍵字',
        'expected_keywords': ['IOL', '執行檔', '路徑', 'path'],
        'expected_rank': 1,
        'baseline_rank': 1,
        'description': '測試標題完全匹配的情況（基準測試）'
    },
    
    # ==================== 類型 2: 語義查詢（保持向量搜尋優勢） ====================
    {
        'id': 4,
        'query': '如何測試 USB 裝置',
        'type': '語義查詢',
        'expected_keywords': ['USB', '測試', 'test'],
        'expected_rank': 3,  # 允許 Top 3
        'baseline_rank': 2,
        'description': '測試語義理解能力（不應下降）'
    },
    {
        'id': 5,
        'query': '連接測試設備的步驟',
        'type': '語義查詢',
        'expected_keywords': ['連接', '步驟', '設備'],
        'expected_rank': 3,
        'baseline_rank': 3,
        'description': '測試模糊語義查詢'
    },
    
    # ==================== 類型 3: 混合查詢（精確+語義） ====================
    {
        'id': 6,
        'query': 'CrystalDiskMark 測試參數',
        'type': '混合查詢',
        'expected_keywords': ['CrystalDiskMark', '參數', 'parameter'],
        'expected_rank': 1,
        'baseline_rank': 2,
        'description': '測試品牌名稱 + 技術詞彙的混合查詢'
    },
    {
        'id': 7,
        'query': 'UNH-IOL 認證流程',
        'type': '混合查詢',
        'expected_keywords': ['UNH-IOL', '認證', '流程'],
        'expected_rank': 1,
        'baseline_rank': 1,
        'description': '測試機構名稱查詢'
    },
    {
        'id': 8,
        'query': 'Protocol 版本對應 SPEC',
        'type': '混合查詢',
        'expected_keywords': ['Protocol', '版本', 'SPEC', '對應'],
        'expected_rank': 1,
        'baseline_rank': 1,
        'description': '測試專業術語組合查詢'
    },
    
    # ==================== 類型 4: 長尾查詢（邊界情況） ====================
    {
        'id': 9,
        'query': '測試失敗時的錯誤訊息',
        'type': '長尾查詢',
        'expected_keywords': ['錯誤', 'error', '失敗', 'fail'],
        'expected_rank': 3,
        'baseline_rank': 5,
        'description': '測試問題導向的查詢'
    },
    {
        'id': 10,
        'query': 'IOL 完整測試流程',
        'type': '長尾查詢',
        'expected_keywords': ['IOL', '完整', '流程', 'SOP'],
        'expected_rank': 1,
        'baseline_rank': 2,
        'description': '測試文檔級搜尋功能'
    },
]

# ========== 測試執行函數 ==========

def run_single_test(service, test_case, version_code, version_config):
    """執行單個測試案例"""
    print(f"\n{'='*80}")
    print(f"測試 #{test_case['id']}: {test_case['query']}")
    print(f"類型: {test_case['type']} | 期望排名: Top {test_case['expected_rank']}")
    print(f"描述: {test_case['description']}")
    print(f"{'='*80}")
    
    try:
        # 執行搜尋
        results = service.search_knowledge(
            query=test_case['query'],
            limit=10,
            threshold=0.7,
            stage=1,
            version_config=version_config
        )
        
        # 分析結果
        passed = False
        found_rank = None
        matched_result = None
        
        for idx, result in enumerate(results[:10], 1):
            content = result.get('content', '').lower()
            title = result.get('title', '').lower()
            
            # 檢查是否包含預期關鍵字
            matched_keywords = []
            for keyword in test_case['expected_keywords']:
                if keyword.lower() in content or keyword.lower() in title:
                    matched_keywords.append(keyword)
            
            # 如果匹配到至少一半的關鍵字，認為是正確結果
            if len(matched_keywords) >= len(test_case['expected_keywords']) // 2:
                found_rank = idx
                matched_result = result
                if idx <= test_case['expected_rank']:
                    passed = True
                break
        
        # 輸出結果
        print(f"\n結果分析:")
        print(f"  版本: {version_code}")
        print(f"  找到結果: {'是' if found_rank else '否'}")
        if found_rank:
            print(f"  實際排名: 第 {found_rank} 名")
            print(f"  期望排名: Top {test_case['expected_rank']}")
            print(f"  基準排名: 第 {test_case['baseline_rank']} 名 (v1.2.1)")
            
            # 顯示排名變化
            if found_rank < test_case['baseline_rank']:
                improvement = test_case['baseline_rank'] - found_rank
                print(f"  排名提升: ↑ {improvement} 名 🎉")
            elif found_rank == test_case['baseline_rank']:
                print(f"  排名保持: ⏸ 持平")
            else:
                decline = found_rank - test_case['baseline_rank']
                print(f"  排名下降: ↓ {decline} 名 ⚠️")
        
        print(f"  測試結果: {'✅ PASS' if passed else '❌ FAIL'}")
        
        # 顯示 Top 3 結果
        print(f"\nTop 3 搜尋結果:")
        for idx, result in enumerate(results[:3], 1):
            score = result.get('score', 0)
            final_score = result.get('final_score', score)
            rrf_score = result.get('rrf_score', 'N/A')
            title = result.get('title', 'Unknown')[:50]
            content_preview = result.get('content', '')[:80].replace('\n', ' ')
            
            # 標記匹配的結果
            marker = " ⭐" if idx == found_rank else ""
            
            print(f"  [{idx}]{marker} {title}")
            print(f"      Score: {score:.4f} | Final: {final_score:.4f} | RRF: {rrf_score}")
            print(f"      {content_preview}...")
        
        return {
            'test_id': test_case['id'],
            'query': test_case['query'],
            'type': test_case['type'],
            'passed': passed,
            'found_rank': found_rank,
            'expected_rank': test_case['expected_rank'],
            'baseline_rank': test_case['baseline_rank'],
            'result_count': len(results)
        }
    
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'test_id': test_case['id'],
            'query': test_case['query'],
            'type': test_case['type'],
            'passed': False,
            'error': str(e)
        }

def run_all_tests():
    """執行所有測試"""
    print("="*80)
    print("🚀 開始執行 Dify v1.2.2 混合搜尋驗證測試")
    print("="*80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試題數: {len(TEST_QUERIES)} 條")
    print(f"測試版本: v1.2.2 (Hybrid Search + Title Boost + RRF Normalization)")
    
    # 初始化服務
    service = ProtocolGuideSearchService()
    
    # 載入 v1.2.2 版本配置
    try:
        version = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.2.2')
        version_config = {
            'version_code': 'dify-two-tier-v1.2.2',
            'rag_settings': version.rag_settings,
            'retrieval_mode': version.retrieval_mode
        }
        print(f"✅ 成功載入版本配置: {version.version_name}")
        print(f"   混合搜尋: {version.rag_settings.get('stage1', {}).get('use_hybrid_search', False)}")
        print(f"   RRF k: {version.rag_settings.get('stage1', {}).get('rrf_k', 'N/A')}")
        print(f"   Title Boost: {version.rag_settings.get('stage1', {}).get('title_match_bonus', 'N/A')}%")
    except DifyConfigVersion.DoesNotExist:
        print("❌ 找不到 v1.2.2 版本，請先執行創建腳本")
        print("   執行: docker exec ai-django python backend/scripts/create_dify_v1_2_2_hybrid_version.py")
        return
    
    # 執行所有測試
    print(f"\n{'='*80}")
    print("開始執行測試...")
    print(f"{'='*80}")
    
    results = []
    for test_case in TEST_QUERIES:
        result = run_single_test(service, test_case, 'v1.2.2', version_config)
        results.append(result)
    
    # 統計結果
    print(f"\n\n{'='*80}")
    print("📊 測試結果統計")
    print(f"{'='*80}")
    
    total = len(results)
    passed = sum(1 for r in results if r.get('passed', False))
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n總體結果：")
    print(f"  總測試數: {total}")
    print(f"  通過: {passed} ✅")
    print(f"  失敗: {failed} ❌")
    print(f"  通過率: {pass_rate:.1f}%")
    
    # 按類型統計
    type_stats = {}
    for result in results:
        test_type = result.get('type', 'Unknown')
        if test_type not in type_stats:
            type_stats[test_type] = {'total': 0, 'passed': 0}
        type_stats[test_type]['total'] += 1
        if result.get('passed', False):
            type_stats[test_type]['passed'] += 1
    
    print(f"\n分類統計:")
    for test_type, stats in sorted(type_stats.items()):
        type_pass_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
        status = "✅" if type_pass_rate >= 75 else "⚠️" if type_pass_rate >= 60 else "❌"
        print(f"  {status} {test_type}: {stats['passed']}/{stats['total']} ({type_pass_rate:.1f}%)")
    
    # 排名改善分析
    print(f"\n排名改善分析:")
    rank_improvements = []
    for result in results:
        if result.get('found_rank') and result.get('baseline_rank'):
            improvement = result['baseline_rank'] - result['found_rank']
            rank_improvements.append({
                'query': result['query'],
                'improvement': improvement,
                'from': result['baseline_rank'],
                'to': result['found_rank']
            })
    
    if rank_improvements:
        avg_improvement = sum(r['improvement'] for r in rank_improvements) / len(rank_improvements)
        print(f"  平均排名提升: {avg_improvement:+.1f} 名")
        
        improved = [r for r in rank_improvements if r['improvement'] > 0]
        maintained = [r for r in rank_improvements if r['improvement'] == 0]
        declined = [r for r in rank_improvements if r['improvement'] < 0]
        
        print(f"  排名提升案例: {len(improved)}/{len(rank_improvements)} ({len(improved)/len(rank_improvements)*100:.0f}%)")
        print(f"  排名保持案例: {len(maintained)}/{len(rank_improvements)} ({len(maintained)/len(rank_improvements)*100:.0f}%)")
        print(f"  排名下降案例: {len(declined)}/{len(rank_improvements)} ({len(declined)/len(rank_improvements)*100:.0f}%)")
        
        if improved:
            print(f"\n  🎉 排名提升的查詢:")
            for case in improved[:5]:  # 顯示前 5 個提升案例
                print(f"    • \"{case['query']}\": 第 {case['from']} → 第 {case['to']} 名 (↑{case['improvement']})")
        
        if declined:
            print(f"\n  ⚠️  排名下降的查詢:")
            for case in declined[:3]:  # 顯示前 3 個下降案例
                print(f"    • \"{case['query']}\": 第 {case['from']} → 第 {case['to']} 名 (↓{abs(case['improvement'])})")
    
    # 目標達成度評估
    print(f"\n{'='*80}")
    print("🎯 目標達成度評估")
    print(f"{'='*80}")
    
    # 按類型評估
    targets = {
        '精確關鍵字': {'target': 85, 'weight': 40},
        '語義查詢': {'target': 85, 'weight': 20},
        '混合查詢': {'target': 90, 'weight': 30},
        '長尾查詢': {'target': 75, 'weight': 10},
    }
    
    weighted_score = 0
    for test_type, target_info in targets.items():
        if test_type in type_stats:
            stats = type_stats[test_type]
            actual_rate = (stats['passed'] / stats['total'] * 100) if stats['total'] > 0 else 0
            target_rate = target_info['target']
            weight = target_info['weight']
            
            status = "✅ 達標" if actual_rate >= target_rate else "❌ 未達標"
            gap = actual_rate - target_rate
            
            print(f"  {test_type}:")
            print(f"    目標: {target_rate}% | 實際: {actual_rate:.1f}% | 差距: {gap:+.1f}% | {status}")
            
            weighted_score += (actual_rate / 100) * weight
    
    print(f"\n加權綜合分數: {weighted_score:.1f}% (目標: 91%)")
    
    # 最終評估
    print(f"\n{'='*80}")
    print("📈 最終評估")
    print(f"{'='*80}")
    
    if pass_rate >= 90 and weighted_score >= 91:
        print("🎉🎉🎉 測試結果：優秀！")
        print("   v1.2.2 混合搜尋顯著提升準確度，達到所有目標！")
        print("   建議：可以部署到生產環境")
    elif pass_rate >= 85 and weighted_score >= 85:
        print("✅✅ 測試結果：良好！")
        print("   v1.2.2 達到預期目標，準確度顯著提升")
        print("   建議：可以設為 Baseline 版本")
    elif pass_rate >= 75:
        print("⚠️  測試結果：一般")
        print("   準確度有提升但未達最佳狀態")
        print("   建議：調優參數（RRF k 值、Title Boost 比例）")
    else:
        print("❌ 測試結果：不理想")
        print("   需要檢查實作邏輯或調整搜尋策略")
        print("   建議：檢查日誌並分析失敗案例")
    
    print(f"{'='*80}\n")
    
    # 返回結果供後續分析
    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'pass_rate': pass_rate,
        'weighted_score': weighted_score,
        'type_stats': type_stats,
        'results': results
    }

if __name__ == '__main__':
    test_results = run_all_tests()
    
    # 根據測試結果設定退出碼
    exit_code = 0 if test_results['pass_rate'] >= 85 else 1
    sys.exit(exit_code)
