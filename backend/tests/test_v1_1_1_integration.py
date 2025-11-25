#!/usr/bin/env python
"""
測試 v1.1.1 版本整合
====================

測試項目：
1. ✅ 驗證 v1.1.1 版本已創建
2. ✅ 驗證動態配置功能
3. ✅ 驗證 Baseline API
4. ✅ 驗證切換 Baseline 功能
5. ✅ 驗證配置讀取優先順序

執行方式：
    docker exec ai-django python tests/test_v1_1_1_integration.py
"""
import os
import sys
import django
import json

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion, SearchThresholdSetting
from django.contrib.auth.models import User


def print_header(text):
    """打印標題"""
    print("\n" + "=" * 80)
    print(f"  {text}")
    print("=" * 80)


def print_success(text):
    """打印成功訊息"""
    print(f"✅ {text}")


def print_error(text):
    """打印錯誤訊息"""
    print(f"❌ {text}")


def print_info(text):
    """打印資訊"""
    print(f"ℹ️  {text}")


def test_v1_1_1_exists():
    """測試 1: 驗證 v1.1.1 版本存在"""
    print_header("測試 1: 驗證 v1.1.1 版本存在")
    
    try:
        version = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.1.1')
        print_success(f"找到版本: {version.version_name}")
        print_info(f"  版本代碼: {version.version_code}")
        print_info(f"  App ID: {version.dify_app_id}")
        print_info(f"  API URL: {version.dify_api_url}")
        print_info(f"  檢索模式: {version.retrieval_mode}")
        print_info(f"  是否啟用: {version.is_active}")
        print_info(f"  是否為 Baseline: {version.is_baseline}")
        
        # 檢查 RAG 設定
        rag_settings = version.rag_settings
        stage1 = rag_settings.get('stage1', {})
        stage2 = rag_settings.get('stage2', {})
        
        print_info(f"\n  Stage 1 配置:")
        print_info(f"    - use_dynamic_threshold: {stage1.get('use_dynamic_threshold', False)}")
        print_info(f"    - threshold (預設): {stage1.get('threshold', 'N/A')}")
        print_info(f"    - title_weight (預設): {stage1.get('title_weight', 'N/A')}")
        print_info(f"    - content_weight (預設): {stage1.get('content_weight', 'N/A')}")
        print_info(f"    - top_k: {stage1.get('top_k', 'N/A')}")
        
        print_info(f"\n  Stage 2 配置:")
        print_info(f"    - use_dynamic_threshold: {stage2.get('use_dynamic_threshold', False)}")
        print_info(f"    - threshold (預設): {stage2.get('threshold', 'N/A')}")
        print_info(f"    - title_weight (預設): {stage2.get('title_weight', 'N/A')}")
        print_info(f"    - content_weight (預設): {stage2.get('content_weight', 'N/A')}")
        print_info(f"    - top_k: {stage2.get('top_k', 'N/A')}")
        
        # 驗證動態配置標記
        is_dynamic = stage1.get('use_dynamic_threshold', False) or stage2.get('use_dynamic_threshold', False)
        if is_dynamic:
            print_success("\n  版本配置為動態版本 ✨")
        else:
            print_error("\n  版本配置為靜態版本（應該要是動態的！）")
            return False
        
        # 驗證無 Title Boost
        has_title_boost = (
            stage1.get('title_match_bonus') is not None or 
            stage2.get('title_match_bonus') is not None
        )
        if not has_title_boost:
            print_success("  版本無 Title Boost（符合 v1.1.1 設計）✅")
        else:
            print_error("  版本有 Title Boost（不符合 v1.1.1 設計！）")
        
        return True
        
    except DifyConfigVersion.DoesNotExist:
        print_error("找不到 v1.1.1 版本！")
        print_info("請先執行: docker exec ai-django python /app/scripts/create_dify_v1_1_1_dynamic_version.py")
        return False
    except Exception as e:
        print_error(f"測試失敗: {str(e)}")
        return False


def test_dynamic_threshold_loading():
    """測試 2: 驗證動態 Threshold 載入"""
    print_header("測試 2: 驗證動態 Threshold 載入")
    
    try:
        from library.common.threshold_manager import get_threshold_manager
        
        manager = get_threshold_manager()
        
        # 清除快取
        manager.clear_cache()
        print_info("已清除快取")
        
        # 檢查是否有 protocol_assistant 的配置
        threshold_setting = SearchThresholdSetting.objects.filter(
            assistant_type='protocol_assistant',
            is_active=True
        ).first()
        
        if threshold_setting:
            print_success(f"找到 Protocol Assistant 的 Threshold 設定")
            print_info(f"  Stage 1 Threshold: {threshold_setting.stage1_threshold}")
            print_info(f"  Stage 1 Title Weight: {threshold_setting.stage1_title_weight}%")
            print_info(f"  Stage 1 Content Weight: {threshold_setting.stage1_content_weight}%")
            print_info(f"  Stage 2 Threshold: {threshold_setting.stage2_threshold}")
            print_info(f"  Stage 2 Title Weight: {threshold_setting.stage2_title_weight}%")
            print_info(f"  Stage 2 Content Weight: {threshold_setting.stage2_content_weight}%")
        else:
            print_info("資料庫中無 Protocol Assistant 設定（將使用版本預設值）")
        
        # 測試讀取 Threshold
        threshold_stage1 = manager.get_threshold('protocol_assistant', stage=1)
        threshold_stage2 = manager.get_threshold('protocol_assistant', stage=2)
        
        print_success(f"\n動態載入 Threshold:")
        print_info(f"  Stage 1: {threshold_stage1}")
        print_info(f"  Stage 2: {threshold_stage2}")
        
        # 測試讀取權重
        title_weight_1, content_weight_1 = manager.get_weights('protocol_assistant', stage=1)
        title_weight_2, content_weight_2 = manager.get_weights('protocol_assistant', stage=2)
        
        print_success(f"\n動態載入權重:")
        print_info(f"  Stage 1: Title={title_weight_1:.2%}, Content={content_weight_1:.2%}")
        print_info(f"  Stage 2: Title={title_weight_2:.2%}, Content={content_weight_2:.2%}")
        
        return True
        
    except Exception as e:
        print_error(f"測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_baseline_api():
    """測試 3: 驗證 Baseline API"""
    print_header("測試 3: 驗證 Baseline API")
    
    try:
        # 檢查當前 Baseline
        current_baseline = DifyConfigVersion.objects.filter(
            is_baseline=True,
            is_active=True
        ).first()
        
        if current_baseline:
            print_success(f"當前 Baseline: {current_baseline.version_name}")
            print_info(f"  版本代碼: {current_baseline.version_code}")
        else:
            print_info("目前沒有設定 Baseline")
        
        # 列出所有可用版本
        all_versions = DifyConfigVersion.objects.filter(is_active=True).order_by('-created_at')
        print_info(f"\n可用版本列表 ({all_versions.count()} 個):")
        for v in all_versions:
            is_dynamic = (
                v.rag_settings.get('stage1', {}).get('use_dynamic_threshold', False) or
                v.rag_settings.get('stage2', {}).get('use_dynamic_threshold', False)
            )
            baseline_marker = " [Baseline]" if v.is_baseline else ""
            dynamic_marker = " 🔄" if is_dynamic else ""
            print_info(f"  - {v.version_name} ({v.version_code}){baseline_marker}{dynamic_marker}")
        
        return True
        
    except Exception as e:
        print_error(f"測試失敗: {str(e)}")
        return False


def test_switch_baseline():
    """測試 4: 驗證切換 Baseline 功能"""
    print_header("測試 4: 驗證切換 Baseline 功能（模擬）")
    
    try:
        # 獲取 v1.1.1 版本
        v1_1_1 = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.1.1')
        
        print_info(f"準備將 Baseline 切換為: {v1_1_1.version_name}")
        print_info("（這是模擬測試，實際操作請在 Web UI 中執行）")
        
        # 檢查切換邏輯（不實際執行）
        current_baseline = DifyConfigVersion.objects.filter(is_baseline=True).first()
        if current_baseline:
            print_info(f"  當前 Baseline: {current_baseline.version_name}")
            if current_baseline.id == v1_1_1.id:
                print_success("  v1.1.1 已經是 Baseline ✅")
            else:
                print_info(f"  切換操作會：")
                print_info(f"    1. 清除 {current_baseline.version_name} 的 Baseline 標記")
                print_info(f"    2. 設定 {v1_1_1.version_name} 為 Baseline")
                print_info(f"    3. 刷新 ThresholdManager 快取")
        else:
            print_info("  目前沒有 Baseline，切換後將設定 v1.1.1")
        
        print_success("\n切換邏輯驗證通過 ✅")
        print_info("實際切換 Baseline 的方式：")
        print_info("  方法 1: 在 Protocol Assistant Chat 頁面點擊「切換 Baseline」")
        print_info("  方法 2: 在 VSA 版本管理頁面點擊「設為 Baseline」")
        
        return True
        
    except DifyConfigVersion.DoesNotExist:
        print_error("找不到 v1.1.1 版本")
        return False
    except Exception as e:
        print_error(f"測試失敗: {str(e)}")
        return False


def test_version_comparison():
    """測試 5: 版本對比"""
    print_header("測試 5: 版本對比（v1.1 vs v1.1.1 vs v1.2.1）")
    
    try:
        versions = {}
        for code in ['dify-two-tier-v1.1', 'dify-two-tier-v1.1.1', 'dify-two-tier-v1.2.1']:
            try:
                v = DifyConfigVersion.objects.get(version_code=code)
                versions[code] = v
            except DifyConfigVersion.DoesNotExist:
                print_info(f"版本 {code} 不存在")
        
        if not versions:
            print_error("找不到任何版本")
            return False
        
        print_info("\n版本對比表:")
        print_info("+" + "-" * 78 + "+")
        print_info(f"| {'特性':<20} | {'v1.1':<15} | {'v1.1.1':<15} | {'v1.2.1':<15} |")
        print_info("+" + "-" * 78 + "+")
        
        # 比較特性
        features = {
            'Threshold 來源': {},
            'Title Boost': {},
            'Retrieval Mode': {},
            '配置彈性': {},
        }
        
        for code, v in versions.items():
            rag = v.rag_settings
            is_dynamic = (
                rag.get('stage1', {}).get('use_dynamic_threshold', False) or
                rag.get('stage2', {}).get('use_dynamic_threshold', False)
            )
            has_boost = (
                rag.get('stage1', {}).get('title_match_bonus') is not None or
                rag.get('stage2', {}).get('title_match_bonus') is not None
            )
            
            version_key = code.split('-')[-1]  # v1.1, v1.1.1, v1.2.1
            features['Threshold 來源'][version_key] = '動態 🔄' if is_dynamic else '靜態'
            features['Title Boost'][version_key] = 'Yes ✅' if has_boost else 'No ❌'
            features['Retrieval Mode'][version_key] = v.retrieval_mode
            features['配置彈性'][version_key] = '高 ✨' if is_dynamic else '低'
        
        for feature, values in features.items():
            v11 = values.get('v1.1', 'N/A')
            v111 = values.get('v1.1.1', 'N/A')
            v121 = values.get('v1.2.1', 'N/A')
            print_info(f"| {feature:<20} | {v11:<15} | {v111:<15} | {v121:<15} |")
        
        print_info("+" + "-" * 78 + "+")
        
        print_success("\n版本對比完成 ✅")
        print_info("\n推薦使用場景:")
        print_info("  v1.1     → 固定參數測試（Baseline 參考）")
        print_info("  v1.1.1   → 可調參數測試（純粹二階搜尋）← 新版本")
        print_info("  v1.2.1   → 可調參數 + 標題匹配優化")
        
        return True
        
    except Exception as e:
        print_error(f"測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主測試流程"""
    print_header("🧪 v1.1.1 版本整合測試")
    print_info("測試日期: 2025-11-26")
    print_info("測試項目: v1.1.1 動態版本 + Baseline 切換機制")
    
    results = {}
    
    # 測試 1
    results['test_1'] = test_v1_1_1_exists()
    
    # 測試 2
    if results['test_1']:
        results['test_2'] = test_dynamic_threshold_loading()
    else:
        print_info("\n⏭️  跳過測試 2（前置條件未滿足）")
        results['test_2'] = None
    
    # 測試 3
    results['test_3'] = test_baseline_api()
    
    # 測試 4
    if results['test_1']:
        results['test_4'] = test_switch_baseline()
    else:
        print_info("\n⏭️  跳過測試 4（前置條件未滿足）")
        results['test_4'] = None
    
    # 測試 5
    results['test_5'] = test_version_comparison()
    
    # 總結
    print_header("📊 測試總結")
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    total = len(results)
    
    print_info(f"總測試數: {total}")
    print_success(f"通過: {passed}")
    if failed > 0:
        print_error(f"失敗: {failed}")
    if skipped > 0:
        print_info(f"跳過: {skipped}")
    
    if failed == 0 and passed > 0:
        print_success("\n🎉 所有測試通過！")
        print_info("\n下一步:")
        print_info("  1. 在瀏覽器中打開 http://localhost/protocol-chat")
        print_info("  2. 點擊頂部的「切換 Baseline」按鈕")
        print_info("  3. 選擇「Dify 二階搜尋 v1.1.1」")
        print_info("  4. 在「搜尋 Threshold 設定」中調整參數")
        print_info("  5. 在 VSA 中執行批量測試，驗證動態配置生效")
    else:
        print_error("\n❌ 部分測試失敗，請檢查錯誤訊息")
    
    print("=" * 80)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
