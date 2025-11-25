#!/usr/bin/env python
"""
測試 Title Boost 功能
=====================

驗證 v1.2 Title Boost 模組的核心功能。

執行方式：
    docker exec ai-django python /app/tests/test_search/test_title_boost.py
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()


def test_title_matcher():
    """測試 TitleMatcher 功能"""
    print("\n" + "=" * 80)
    print("📋 測試 1: TitleMatcher 關鍵詞提取與匹配")
    print("=" * 80)
    
    from library.common.knowledge_base.title_boost import TitleMatcher
    
    matcher = TitleMatcher(min_keyword_length=2)
    
    # 測試案例
    test_cases = [
        {
            'query': '如何完整測試 IOL SOP',
            'title': 'IOL USB-IF 測試規範',
            'expected_match': True
        },
        {
            'query': 'USB 3.0 連接測試',
            'title': 'USB 3.0 完整測試指南',
            'expected_match': True
        },
        {
            'query': 'random text',
            'title': 'IOL SOP 文檔',
            'expected_match': False
        },
        {
            'query': 'iol sop',  # 小寫測試
            'title': 'IOL 測試規範',
            'expected_match': True
        }
    ]
    
    passed = 0
    failed = 0
    
    for i, case in enumerate(test_cases, 1):
        query = case['query']
        title = case['title']
        expected = case['expected_match']
        
        # 提取關鍵詞
        keywords = matcher.extract_keywords(query)
        
        # 檢查匹配
        is_match = matcher.check_title_match(query, title)
        
        # 計算匹配分數
        match_score = matcher.calculate_match_score(query, title)
        
        # 驗證結果
        status = "✅ PASS" if is_match == expected else "❌ FAIL"
        if is_match == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"\n測試 {i}: {status}")
        print(f"  查詢: '{query}'")
        print(f"  標題: '{title}'")
        print(f"  關鍵詞: {keywords}")
        print(f"  匹配: {is_match} (預期: {expected})")
        print(f"  匹配分數: {match_score:.2f}")
    
    print(f"\n總結: {passed} 通過, {failed} 失敗")
    return failed == 0


def test_title_boost_processor():
    """測試 TitleBoostProcessor 功能"""
    print("\n" + "=" * 80)
    print("📋 測試 2: TitleBoostProcessor 加分處理")
    print("=" * 80)
    
    from library.common.knowledge_base.title_boost import TitleBoostProcessor
    
    processor = TitleBoostProcessor(title_match_bonus=0.15)
    
    # 模擬搜尋結果
    mock_results = [
        {
            'final_score': 0.80,
            'title': 'IOL USB-IF 測試規範',
            'content': '這是 IOL 測試的完整說明...',
            'source_id': 1
        },
        {
            'final_score': 0.85,
            'title': '其他測試指南',
            'content': '這是其他測試的說明...',
            'source_id': 2
        },
        {
            'final_score': 0.75,
            'title': 'USB 3.0 連接測試 SOP',
            'content': 'USB 連接測試步驟...',
            'source_id': 3
        }
    ]
    
    # 測試查詢
    query = "IOL SOP 測試"
    
    print(f"\n查詢: '{query}'")
    print("\n原始結果（按 final_score 排序）:")
    for i, result in enumerate(mock_results, 1):
        print(f"  {i}. {result['title']} (分數: {result['final_score']:.2f})")
    
    # 應用 Title Boost
    boosted_results = processor.apply_title_boost(
        query=query,
        vector_results=mock_results,
        title_field='title'
    )
    
    print("\n加分後結果（重新排序）:")
    for i, result in enumerate(boosted_results, 1):
        boost_status = "✨ +Boost" if result.get('title_boost_applied', False) else ""
        original = result.get('original_score', result['final_score'])
        boost_value = result.get('title_boost_value', 0)
        
        print(f"  {i}. {result['title']}")
        print(f"     分數: {original:.2f} → {result['final_score']:.2f} {boost_status}")
        if boost_value > 0:
            print(f"     加分: +{boost_value:.2f}")
    
    # 統計資訊
    stats = processor.get_boost_statistics(boosted_results)
    print(f"\n統計資訊:")
    print(f"  • 總結果數: {stats['total_results']}")
    print(f"  • 獲得加分: {stats['boosted_count']} ({stats['boost_ratio']:.1%})")
    print(f"  • 平均加分: {stats['average_boost']:.2%}")
    print(f"  • 最大加分: {stats['max_boost']:.2%}")
    
    # 驗證：IOL 相關文檔應該排第一
    first_result = boosted_results[0]
    is_iol_first = 'IOL' in first_result['title']
    
    print(f"\n驗證: IOL 文檔是否排第一? {'✅ PASS' if is_iol_first else '❌ FAIL'}")
    
    return is_iol_first


def test_config_parsing():
    """測試配置解析功能"""
    print("\n" + "=" * 80)
    print("📋 測試 3: TitleBoostConfig 配置解析")
    print("=" * 80)
    
    from library.common.knowledge_base.title_boost import TitleBoostConfig
    
    # 模擬 v1.2 配置
    rag_settings = {
        "stage1": {
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
            "title_match_bonus": 15,
            "min_keyword_length": 2
        },
        "stage2": {
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
            "title_match_bonus": 10
        },
        "retrieval_mode": "two_stage_with_title_boost"
    }
    
    # 解析第一階段配置
    config_stage1 = TitleBoostConfig.from_rag_settings(rag_settings, stage=1)
    
    print("\nStage 1 配置:")
    print(f"  • 啟用: {config_stage1['enabled']}")
    print(f"  • 加分值: {config_stage1['title_match_bonus']:.2%}")
    print(f"  • 最小關鍵詞長度: {config_stage1['min_keyword_length']}")
    
    # 解析第二階段配置
    config_stage2 = TitleBoostConfig.from_rag_settings(rag_settings, stage=2)
    
    print("\nStage 2 配置:")
    print(f"  • 啟用: {config_stage2['enabled']}")
    print(f"  • 加分值: {config_stage2['title_match_bonus']:.2%}")
    
    # 驗證
    is_valid = (
        config_stage1['enabled'] == True and
        config_stage1['title_match_bonus'] == 0.15 and
        config_stage2['title_match_bonus'] == 0.10
    )
    
    print(f"\n驗證: 配置解析正確? {'✅ PASS' if is_valid else '❌ FAIL'}")
    
    return is_valid


def test_version_config():
    """測試從資料庫讀取 v1.2 版本配置"""
    print("\n" + "=" * 80)
    print("📋 測試 4: 從資料庫讀取 v1.2 版本配置")
    print("=" * 80)
    
    try:
        from api.models import DifyConfigVersion
        from library.common.knowledge_base.title_boost import TitleBoostConfig
        
        # 查詢 v1.2 版本
        version = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.2')
        
        print(f"\n版本資訊:")
        print(f"  • 版本名稱: {version.version_name}")
        print(f"  • 版本代碼: {version.version_code}")
        print(f"  • 檢索模式: {version.retrieval_mode}")
        print(f"  • 是否啟用: {version.is_active}")
        
        # 解析 Title Boost 配置
        config = TitleBoostConfig.from_rag_settings(version.rag_settings, stage=1)
        
        print(f"\nTitle Boost 配置:")
        print(f"  • 啟用: {config['enabled']}")
        print(f"  • Stage 1 加分: {config['title_match_bonus']:.2%}")
        
        config_stage2 = TitleBoostConfig.from_rag_settings(version.rag_settings, stage=2)
        print(f"  • Stage 2 加分: {config_stage2['title_match_bonus']:.2%}")
        
        # 驗證
        is_valid = config['enabled'] and 'title_boost' in version.retrieval_mode.lower()
        
        print(f"\n驗證: v1.2 版本配置正確? {'✅ PASS' if is_valid else '❌ FAIL'}")
        
        return is_valid
        
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """執行所有測試"""
    print("\n" + "🎯" * 40)
    print("Title Boost 功能測試套件")
    print("🎯" * 40)
    
    results = {
        '關鍵詞提取與匹配': test_title_matcher(),
        '加分處理器': test_title_boost_processor(),
        '配置解析': test_config_parsing(),
        'v1.2 版本配置': test_version_config()
    }
    
    # 總結
    print("\n" + "=" * 80)
    print("📊 測試總結")
    print("=" * 80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！Title Boost 功能正常運作。")
        print("\n下一步：")
        print("  1. 在 VSA 前端刷新版本列表")
        print("  2. 選擇 v1.2 版本進行測試")
        print("  3. 使用測試查詢：'IOL SOP', 'USB 測試', 'CrystalDiskMark'")
        return 0
    else:
        print("\n⚠️ 部分測試失敗，請檢查錯誤訊息。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
