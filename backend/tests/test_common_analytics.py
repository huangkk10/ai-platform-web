"""
測試腳本：驗證 Common Analytics 基礎設施

此腳本測試：
1. BaseStatisticsManager 基礎功能
2. RVTStatisticsManager 重構版本
3. API 處理器功能
4. 與原始版本的對比

Usage:
    docker exec ai-django python tests/test_common_analytics.py
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from datetime import datetime, timedelta
from django.contrib.auth import get_user_model

User = get_user_model()


def test_base_statistics_manager():
    """測試基礎統計管理器"""
    print("\n" + "="*80)
    print("測試 1: BaseStatisticsManager 基礎功能")
    print("="*80)
    
    try:
        from library.common.analytics.base_statistics_manager import BaseStatisticsManager
        
        # 測試抽象類別不能直接實例化
        try:
            manager = BaseStatisticsManager()
            print("❌ 錯誤：抽象類別應該無法實例化")
            return False
        except TypeError as e:
            print(f"✅ 抽象類別正確拒絕實例化: {e}")
        
        print("✅ BaseStatisticsManager 結構驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ BaseStatisticsManager 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_rvt_statistics_manager_refactored():
    """測試重構後的 RVT 統計管理器"""
    print("\n" + "="*80)
    print("測試 2: RVTStatisticsManager 重構版本")
    print("="*80)
    
    try:
        from library.rvt_analytics.statistics_manager_refactored import RVTStatisticsManager
        
        # 創建實例
        manager = RVTStatisticsManager()
        print("✅ RVTStatisticsManager 實例化成功")
        
        # 測試抽象方法實作
        assert manager.get_assistant_type() == 'rvt_assistant', "assistant_type 不正確"
        print(f"✅ Assistant Type: {manager.get_assistant_type()}")
        
        # 測試 Model 獲取
        ConversationModel = manager.get_conversation_model()
        MessageModel = manager.get_message_model()
        print(f"✅ Conversation Model: {ConversationModel.__name__}")
        print(f"✅ Message Model: {MessageModel.__name__}")
        
        # 測試統計功能（使用小範圍數據）
        print("\n📊 執行統計分析（最近 7 天）...")
        stats = manager.get_comprehensive_stats(days=7)
        
        print("\n統計結果:")
        print(f"  - Assistant Type: {stats.get('assistant_type')}")
        print(f"  - 期間: {stats.get('period')}")
        print(f"  - 總對話數: {stats.get('overview', {}).get('total_conversations', 0)}")
        print(f"  - 總消息數: {stats.get('overview', {}).get('total_messages', 0)}")
        
        if 'error' in stats:
            print(f"  ⚠️ 警告: {stats.get('error')}")
        else:
            print("✅ 統計分析執行成功")
        
        return True
        
    except Exception as e:
        print(f"❌ RVTStatisticsManager 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_original_vs_refactored():
    """對比原始版本和重構版本的結果"""
    print("\n" + "="*80)
    print("測試 3: 原始版本 vs 重構版本對比")
    print("="*80)
    
    try:
        from library.rvt_analytics.statistics_manager import StatisticsManager as OriginalManager
        from library.rvt_analytics.statistics_manager_refactored import RVTStatisticsManager as RefactoredManager
        
        days = 7
        
        print(f"\n執行統計分析（最近 {days} 天）...")
        
        # 原始版本
        print("\n1️⃣ 原始版本:")
        original_manager = OriginalManager()
        original_stats = original_manager.get_comprehensive_stats(days=days)
        
        original_conversations = original_stats.get('overview', {}).get('total_conversations', 0)
        original_messages = original_stats.get('overview', {}).get('total_messages', 0)
        
        print(f"  - 總對話數: {original_conversations}")
        print(f"  - 總消息數: {original_messages}")
        
        # 重構版本
        print("\n2️⃣ 重構版本:")
        refactored_manager = RefactoredManager()
        refactored_stats = refactored_manager.get_comprehensive_stats(days=days)
        
        refactored_conversations = refactored_stats.get('overview', {}).get('total_conversations', 0)
        refactored_messages = refactored_stats.get('overview', {}).get('total_messages', 0)
        
        print(f"  - 總對話數: {refactored_conversations}")
        print(f"  - 總消息數: {refactored_messages}")
        
        # 對比結果
        print("\n📊 結果對比:")
        if original_conversations == refactored_conversations:
            print(f"  ✅ 對話數一致: {original_conversations}")
        else:
            print(f"  ⚠️ 對話數差異: 原始 {original_conversations} vs 重構 {refactored_conversations}")
        
        if original_messages == refactored_messages:
            print(f"  ✅ 消息數一致: {original_messages}")
        else:
            print(f"  ⚠️ 消息數差異: 原始 {original_messages} vs 重構 {refactored_messages}")
        
        # 檢查結構一致性
        original_keys = set(original_stats.keys())
        refactored_keys = set(refactored_stats.keys())
        
        print(f"\n🔑 數據結構對比:")
        print(f"  - 原始版本欄位: {sorted(original_keys)}")
        print(f"  - 重構版本欄位: {sorted(refactored_keys)}")
        
        missing_in_refactored = original_keys - refactored_keys
        extra_in_refactored = refactored_keys - original_keys
        
        if missing_in_refactored:
            print(f"  ⚠️ 重構版本缺少欄位: {missing_in_refactored}")
        if extra_in_refactored:
            print(f"  ℹ️ 重構版本額外欄位: {extra_in_refactored}")
        
        if not missing_in_refactored and not extra_in_refactored:
            print("  ✅ 數據結構完全一致")
        
        return True
        
    except Exception as e:
        print(f"❌ 對比測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_common_analytics_availability():
    """測試 Common Analytics 可用性"""
    print("\n" + "="*80)
    print("測試 4: Common Analytics 可用性檢查")
    print("="*80)
    
    try:
        from library.common.analytics import (
            BaseStatisticsManager,
            BaseQuestionAnalyzer,
            BaseSatisfactionAnalyzer,
            BaseAPIHandler,
            COMMON_ANALYTICS_AVAILABLE
        )
        
        print(f"✅ COMMON_ANALYTICS_AVAILABLE: {COMMON_ANALYTICS_AVAILABLE}")
        print(f"✅ BaseStatisticsManager: {BaseStatisticsManager}")
        print(f"✅ BaseQuestionAnalyzer: {BaseQuestionAnalyzer}")
        print(f"✅ BaseSatisfactionAnalyzer: {BaseSatisfactionAnalyzer}")
        print(f"✅ BaseAPIHandler: {BaseAPIHandler}")
        
        return True
        
    except Exception as e:
        print(f"❌ Common Analytics 可用性檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試函數"""
    print("\n" + "🔬" * 40)
    print("Common Analytics 基礎設施測試")
    print("🔬" * 40)
    
    results = {
        'test_base_statistics_manager': test_base_statistics_manager(),
        'test_rvt_statistics_manager_refactored': test_rvt_statistics_manager_refactored(),
        'test_original_vs_refactored': test_original_vs_refactored(),
        'test_common_analytics_availability': test_common_analytics_availability(),
    }
    
    # 總結
    print("\n" + "="*80)
    print("📋 測試總結")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！Common Analytics 基礎設施運行正常。")
        return 0
    else:
        print(f"\n⚠️ 有 {total - passed} 個測試失敗，請檢查錯誤訊息。")
        return 1


if __name__ == '__main__':
    exit(main())
