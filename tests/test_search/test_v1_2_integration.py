"""
測試 v1.2 Title Boost 完整整合
================================

測試流程：
1. 從資料庫讀取 v1.2 配置
2. 執行後端搜尋（帶 Title Boost）
3. 驗證搜尋結果包含 Title Boost 標記
"""

import os
import sys
import django

# Django 環境設定
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from library.protocol_guide.search_service import ProtocolGuideSearchService

print("=" * 80)
print("🧪 測試 v1.2 Title Boost 完整整合")
print("=" * 80)

# 測試案例
test_queries = [
    ("IOL SOP", "應該匹配 IOL 相關標題"),
    ("UNH USB 測試", "應該匹配 USB 和 UNH 關鍵字"),
    ("CrystalDiskMark 完整流程", "應該匹配 CrystalDiskMark")
]

try:
    # 步驟 1: 載入 v1.2 配置
    print("\n📋 步驟 1: 載入 v1.2 版本配置")
    version = DifyConfigVersion.objects.get(
        version_code='dify-two-tier-v1.2',
        is_active=True
    )
    
    version_config = {
        'version_code': version.version_code,
        'version_name': version.version_name,
        'rag_settings': version.rag_settings
    }
    
    print(f"  ✅ 版本: {version.version_name}")
    print(f"  ✅ Retrieval Mode: {version.rag_settings.get('retrieval_mode')}")
    print(f"  ✅ Stage 1 Bonus: {version.rag_settings['stage1'].get('title_match_bonus')}%")
    print(f"  ✅ Stage 2 Bonus: {version.rag_settings['stage2'].get('title_match_bonus')}%")
    
    # 步驟 2: 初始化搜尋服務
    print("\n🔍 步驟 2: 初始化搜尋服務")
    search_service = ProtocolGuideSearchService()
    print("  ✅ 搜尋服務已初始化")
    
    # 步驟 3: 執行測試查詢
    print("\n🎯 步驟 3: 執行測試查詢")
    
    for query, expected in test_queries:
        print(f"\n  測試查詢: '{query}'")
        print(f"  預期: {expected}")
        
        try:
            # 執行搜尋（帶 v1.2 配置）
            results = search_service.search_knowledge(
                query=query,
                limit=3,
                use_vector=True,
                threshold=0.7,
                version_config=version_config  # ✅ 傳遞版本配置
            )
            
            if results:
                print(f"    ✅ 找到 {len(results)} 個結果")
                
                # 檢查是否有 Title Boost 標記
                title_boost_count = 0
                for i, result in enumerate(results, 1):
                    title = result.get('title', '未知')
                    score = result.get('score', 0.0)
                    metadata = result.get('metadata', {})
                    title_boost_applied = metadata.get('title_boost_applied', False)
                    
                    boost_indicator = "🌟 [Title Boost]" if title_boost_applied else ""
                    print(f"    [{i}] {title[:50]}... ({score:.2%}) {boost_indicator}")
                    
                    if title_boost_applied:
                        title_boost_count += 1
                        boost_amount = metadata.get('boost_amount', 0)
                        original_score = metadata.get('original_score', 0)
                        print(f"        原始分數: {original_score:.2%} → 加分後: {score:.2%} (+{boost_amount:.2%})")
                
                if title_boost_count > 0:
                    print(f"    ✅ {title_boost_count}/{len(results)} 個結果獲得 Title Boost 加分")
                else:
                    print(f"    ⚠️ 沒有結果獲得 Title Boost 加分（可能標題不匹配）")
            else:
                print(f"    ❌ 無搜尋結果")
                
        except Exception as e:
            print(f"    ❌ 搜尋失敗: {e}")
            import traceback
            traceback.print_exc()
    
    # 步驟 4: 對比 v1.1（無 Title Boost）
    print("\n📊 步驟 4: 對比 v1.1（無 Title Boost）")
    
    try:
        version_v1_1 = DifyConfigVersion.objects.get(
            version_code='dify-two-tier-v1.1',
            is_active=True
        )
        
        version_config_v1_1 = {
            'version_code': version_v1_1.version_code,
            'version_name': version_v1_1.version_name,
            'rag_settings': version_v1_1.rag_settings
        }
        
        print(f"  ✅ 載入 v1.1: {version_v1_1.version_name}")
        
        query = "IOL SOP"
        print(f"\n  測試查詢: '{query}'")
        
        # v1.1 搜尋
        results_v1_1 = search_service.search_knowledge(
            query=query,
            limit=3,
            use_vector=True,
            threshold=0.7,
            version_config=version_config_v1_1
        )
        
        # v1.2 搜尋
        results_v1_2 = search_service.search_knowledge(
            query=query,
            limit=3,
            use_vector=True,
            threshold=0.7,
            version_config=version_config
        )
        
        print(f"\n  📈 結果對比:")
        print(f"    v1.1 結果數: {len(results_v1_1)}")
        print(f"    v1.2 結果數: {len(results_v1_2)}")
        
        if results_v1_1 and results_v1_2:
            print(f"\n    v1.1 第一名: {results_v1_1[0].get('title', '')[:50]} ({results_v1_1[0].get('score', 0):.2%})")
            print(f"    v1.2 第一名: {results_v1_2[0].get('title', '')[:50]} ({results_v1_2[0].get('score', 0):.2%})")
            
            score_diff = results_v1_2[0].get('score', 0) - results_v1_1[0].get('score', 0)
            if score_diff > 0:
                print(f"    ✅ v1.2 分數提升: +{score_diff:.2%}")
            else:
                print(f"    ⚠️ v1.2 分數變化: {score_diff:+.2%}")
        
    except Exception as e:
        print(f"    ⚠️ v1.1 對比失敗: {e}")
    
    print("\n" + "=" * 80)
    print("✅ Title Boost v1.2 整合測試完成")
    print("=" * 80)
    
except Exception as e:
    print(f"\n❌ 測試執行失敗: {e}")
    import traceback
    traceback.print_exc()
