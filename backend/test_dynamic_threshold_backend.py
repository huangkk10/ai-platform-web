#!/usr/bin/env python
"""
Dify v1.2.1 動態 Threshold 後端功能測試腳本

測試項目：
1. 驗證 v1.2.1 版本存在
2. 測試 Baseline 切換 API
3. 測試動態配置載入
4. 測試 ThresholdManager 快取
5. 驗證配置記錄功能

執行方式：
    docker exec ai-django python /app/test_dynamic_threshold_backend.py
"""

import os
import sys
import django
import json
from datetime import datetime
from decimal import Decimal

# Django 環境設定
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import transaction
from api.models import DifyConfigVersion, SearchThresholdSetting
from library.dify_integration.dynamic_threshold_loader import DynamicThresholdLoader
from library.common.threshold_manager import ThresholdManager

class Colors:
    """終端顏色"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    """打印標題"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(text):
    """打印成功訊息"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_error(text):
    """打印錯誤訊息"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    """打印資訊"""
    print(f"{Colors.OKCYAN}ℹ️  {text}{Colors.ENDC}")

def print_warning(text):
    """打印警告"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_json(data, indent=2):
    """打印 JSON 資料"""
    print(json.dumps(data, indent=indent, ensure_ascii=False, default=str))


# ============================================================================
# 測試 1: 驗證 v1.2.1 版本存在
# ============================================================================

def test_version_exists():
    """測試 v1.2.1 版本是否存在"""
    print_header("測試 1: 驗證 v1.2.1 版本存在")
    
    try:
        version = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.2.1')
        
        print_success(f"找到版本: {version.version_name}")
        print_info(f"版本 ID: {version.id}")
        print_info(f"版本代碼: {version.version_code}")
        print_info(f"是否啟用: {version.is_active}")
        print_info(f"是否為 Baseline: {version.is_baseline}")
        
        # 檢查 rag_settings
        rag_settings = version.rag_settings
        print_info("\nRAG 設定概覽:")
        print_info(f"  Assistant 類型: {rag_settings.get('assistant_type', 'N/A')}")
        
        stage1 = rag_settings.get('stage1', {})
        print_info(f"  Stage 1 動態 Threshold: {stage1.get('use_dynamic_threshold', False)}")
        print_info(f"  Stage 1 Title Boost: {stage1.get('title_match_bonus', 'N/A')}%")
        
        stage2 = rag_settings.get('stage2', {})
        print_info(f"  Stage 2 動態 Threshold: {stage2.get('use_dynamic_threshold', False)}")
        print_info(f"  Stage 2 Title Boost: {stage2.get('title_match_bonus', 'N/A')}%")
        
        return version
        
    except DifyConfigVersion.DoesNotExist:
        print_error("找不到 v1.2.1 版本！")
        print_warning("請先執行: docker exec ai-django python /app/scripts/create_dify_v1_2_1_dynamic_version.py")
        return None


# ============================================================================
# 測試 2: Baseline 切換功能
# ============================================================================

def test_baseline_switching(version):
    """測試 Baseline 切換功能"""
    print_header("測試 2: Baseline 切換功能")
    
    if not version:
        print_error("無法測試：版本不存在")
        return False
    
    try:
        # 2.1 記錄原始 Baseline
        original_baseline = DifyConfigVersion.objects.filter(is_baseline=True).first()
        print_info(f"原始 Baseline: {original_baseline.version_name if original_baseline else '無'}")
        
        # 2.2 設定 v1.2.1 為 Baseline
        print_info(f"\n嘗試設定 v1.2.1 為 Baseline...")
        
        with transaction.atomic():
            # 清除其他版本的 baseline 標記
            DifyConfigVersion.objects.filter(is_baseline=True).update(is_baseline=False)
            
            # 設定新的 baseline
            version.is_baseline = True
            version.save()
            
            print_success(f"成功設定 {version.version_name} 為 Baseline")
        
        # 2.3 驗證 Baseline 設定
        current_baseline = DifyConfigVersion.objects.get(is_baseline=True)
        
        if current_baseline.id == version.id:
            print_success("Baseline 設定驗證成功")
            print_info(f"當前 Baseline: {current_baseline.version_name}")
        else:
            print_error("Baseline 設定驗證失敗")
            return False
        
        # 2.4 測試獲取 Baseline
        print_info("\n測試獲取 Baseline...")
        baseline = DifyConfigVersion.objects.filter(is_baseline=True, is_active=True).first()
        
        if baseline:
            print_success(f"成功獲取 Baseline: {baseline.version_name}")
            return True
        else:
            print_error("無法獲取 Baseline")
            return False
            
    except Exception as e:
        print_error(f"Baseline 切換測試失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ============================================================================
# 測試 3: 動態配置載入
# ============================================================================

def test_dynamic_loading(version):
    """測試動態配置載入功能"""
    print_header("測試 3: 動態配置載入功能")
    
    if not version:
        print_error("無法測試：版本不存在")
        return False
    
    try:
        rag_settings = version.rag_settings
        
        # 3.1 檢查是否為動態版本
        print_info("檢查動態版本標記...")
        is_dynamic = DynamicThresholdLoader.is_dynamic_version(rag_settings)
        
        if is_dynamic:
            print_success("v1.2.1 是動態版本 ✨")
        else:
            print_error("v1.2.1 不是動態版本（應該要是！）")
            return False
        
        # 3.2 載入 Stage 1 配置
        print_info("\n載入 Stage 1 配置...")
        stage1_config = DynamicThresholdLoader.load_stage_config(
            stage_config=rag_settings['stage1'],
            assistant_type='protocol_assistant'
        )
        
        print_success("Stage 1 配置載入成功")
        print_info("Stage 1 配置內容:")
        print_json(stage1_config, indent=2)
        
        # 3.3 載入 Stage 2 配置
        print_info("\n載入 Stage 2 配置...")
        stage2_config = DynamicThresholdLoader.load_stage_config(
            stage_config=rag_settings['stage2'],
            assistant_type='protocol_assistant'
        )
        
        print_success("Stage 2 配置載入成功")
        print_info("Stage 2 配置內容:")
        print_json(stage2_config, indent=2)
        
        # 3.4 載入完整 RAG 設定
        print_info("\n載入完整 RAG 設定...")
        full_rag_settings = DynamicThresholdLoader.load_full_rag_settings(rag_settings)
        
        print_success("完整 RAG 設定載入成功")
        print_info("完整 RAG 設定概覽:")
        print_info(f"  Assistant 類型: {full_rag_settings.get('assistant_type', 'N/A')}")
        print_info(f"  Stage 1 Threshold: {full_rag_settings['stage1'].get('threshold', 'N/A')}")
        print_info(f"  Stage 1 Title Boost: {full_rag_settings['stage1'].get('title_match_bonus', 'N/A')}%")
        print_info(f"  Stage 2 Threshold: {full_rag_settings['stage2'].get('threshold', 'N/A')}")
        print_info(f"  Stage 2 Title Boost: {full_rag_settings['stage2'].get('title_match_bonus', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print_error(f"動態載入測試失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ============================================================================
# 測試 4: ThresholdManager 快取機制
# ============================================================================

def test_threshold_manager_cache():
    """測試 ThresholdManager 快取機制"""
    print_header("測試 4: ThresholdManager 快取機制")
    
    try:
        # 4.1 清除快取
        print_info("清除 ThresholdManager 快取...")
        from library.common.threshold_manager import get_threshold_manager
        manager = get_threshold_manager()
        manager.clear_cache()
        print_success("快取已清除")
        
        # 4.2 第一次讀取（從資料庫）
        print_info("\n第一次讀取 Protocol Assistant 設定（從資料庫）...")
        import time
        start_time = time.time()
        
        # 觸發資料庫載入
        threshold_settings = manager.get_threshold('protocol_assistant', stage=1)
        weights = manager.get_weights('protocol_assistant', stage=1)
        
        first_read_time = (time.time() - start_time) * 1000  # 毫秒
        print_success(f"讀取成功（耗時: {first_read_time:.2f}ms）")
        
        print_info("Protocol Assistant 設定:")
        print_info(f"  Stage 1 Threshold: {threshold_settings}")
        print_info(f"  Stage 1 Weights: Title={weights[0]*100:.0f}%, Content={weights[1]*100:.0f}%")
        
        # 4.3 第二次讀取（從快取）
        print_info("\n第二次讀取 Protocol Assistant 設定（從快取）...")
        start_time = time.time()
        
        threshold_settings_cached = manager.get_threshold('protocol_assistant', stage=1)
        weights_cached = manager.get_weights('protocol_assistant', stage=1)
        
        second_read_time = (time.time() - start_time) * 1000  # 毫秒
        print_success(f"讀取成功（耗時: {second_read_time:.2f}ms）")
        
        # 4.4 比較讀取時間
        if second_read_time < first_read_time:
            speedup = first_read_time / second_read_time if second_read_time > 0 else float('inf')
            print_success(f"快取加速: {speedup:.2f}x 倍")
        else:
            print_info("快取效能無明顯提升（可能資料庫查詢太快）")
        
        # 4.5 驗證快取內容相同
        if (threshold_settings == threshold_settings_cached and
            weights == weights_cached):
            print_success("快取內容驗證成功（與資料庫一致）")
        else:
            print_error("快取內容與資料庫不一致！")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"ThresholdManager 測試失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ============================================================================
# 測試 5: 配置變更檢測
# ============================================================================

def test_config_change_detection():
    """測試配置變更檢測"""
    print_header("測試 5: 配置變更檢測")
    
    try:
        # 5.1 獲取當前配置
        print_info("獲取當前 Protocol Assistant 配置...")
        threshold_setting = SearchThresholdSetting.objects.filter(
            assistant_type='protocol_assistant'
        ).first()
        
        if not threshold_setting:
            print_warning("找不到 Protocol Assistant 配置，創建預設配置...")
            threshold_setting = SearchThresholdSetting.objects.create(
                assistant_type='protocol_assistant',
                stage1_threshold=Decimal('0.80'),
                stage1_title_weight=95,
                stage1_content_weight=5
            )
        
        original_threshold = threshold_setting.stage1_threshold
        print_info(f"原始 Stage 1 Threshold: {original_threshold}")
        
        # 5.2 模擬配置變更
        print_info("\n模擬配置變更（Stage 1 Threshold 0.80 → 0.85）...")
        threshold_setting.stage1_threshold = Decimal('0.85')
        threshold_setting.save()
        
        print_success("配置已更新到資料庫")
        
        # 5.3 清除快取並重新載入
        print_info("清除快取並重新載入...")
        from library.common.threshold_manager import get_threshold_manager
        manager = get_threshold_manager()
        manager.clear_cache()
        
        new_threshold = manager.get_threshold('protocol_assistant', stage=1)
        
        if abs(new_threshold - 0.85) < 0.01:  # 浮點數比較
            print_success(f"配置變更檢測成功：{new_threshold}")
        else:
            print_error(f"配置變更檢測失敗：期望 0.85，實際 {new_threshold}")
            return False
        
        # 5.4 還原原始配置
        print_info(f"\n還原原始配置（Stage 1 Threshold → {original_threshold}）...")
        threshold_setting.stage1_threshold = original_threshold
        threshold_setting.save()
        manager.clear_cache()
        
        print_success("配置已還原")
        
        return True
        
    except Exception as e:
        print_error(f"配置變更檢測測試失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ============================================================================
# 測試 6: 版本配置合併邏輯
# ============================================================================

def test_config_merge_logic(version):
    """測試版本配置合併邏輯"""
    print_header("測試 6: 版本配置合併邏輯")
    
    if not version:
        print_error("無法測試：版本不存在")
        return False
    
    try:
        rag_settings = version.rag_settings
        
        # 6.1 測試 Stage 1 合併
        print_info("測試 Stage 1 配置合併...")
        stage1_merged = DynamicThresholdLoader.load_stage_config(
            stage_config=rag_settings['stage1'],
            assistant_type='protocol_assistant'
        )
        
        print_info("Stage 1 合併結果:")
        print_info(f"  🔄 動態參數（從 DB）:")
        print_info(f"     - threshold: {stage1_merged.get('threshold', 'N/A')}")
        print_info(f"     - title_weight: {stage1_merged.get('title_weight', 'N/A')}")
        print_info(f"     - content_weight: {stage1_merged.get('content_weight', 'N/A')}")
        print_info(f"  📌 固定參數（從版本定義）:")
        print_info(f"     - title_match_bonus: {stage1_merged.get('title_match_bonus', 'N/A')}%")
        print_info(f"     - top_k: {stage1_merged.get('top_k', 'N/A')}")
        
        # 驗證關鍵參數
        if (stage1_merged.get('threshold') is not None and
            stage1_merged.get('title_match_bonus') == 15):
            print_success("Stage 1 配置合併正確 ✅")
        else:
            print_error("Stage 1 配置合併失敗")
            return False
        
        # 6.2 測試 Stage 2 合併
        print_info("\n測試 Stage 2 配置合併...")
        stage2_merged = DynamicThresholdLoader.load_stage_config(
            stage_config=rag_settings['stage2'],
            assistant_type='protocol_assistant'
        )
        
        print_info("Stage 2 合併結果:")
        print_info(f"  🔄 動態參數（從 DB）:")
        print_info(f"     - threshold: {stage2_merged.get('threshold', 'N/A')}")
        print_info(f"     - title_weight: {stage2_merged.get('title_weight', 'N/A')}")
        print_info(f"     - content_weight: {stage2_merged.get('content_weight', 'N/A')}")
        print_info(f"  📌 固定參數（從版本定義）:")
        print_info(f"     - title_match_bonus: {stage2_merged.get('title_match_bonus', 'N/A')}%")
        print_info(f"     - top_k: {stage2_merged.get('top_k', 'N/A')}")
        
        # 驗證關鍵參數
        if (stage2_merged.get('threshold') is not None and
            stage2_merged.get('title_match_bonus') == 10):
            print_success("Stage 2 配置合併正確 ✅")
        else:
            print_error("Stage 2 配置合併失敗")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"配置合併邏輯測試失敗: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False


# ============================================================================
# 主測試流程
# ============================================================================

def main():
    """主測試流程"""
    print_header("Dify v1.2.1 動態 Threshold 後端功能測試")
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    test_results = {}
    
    # 測試 1: 驗證版本存在
    version = test_version_exists()
    test_results['version_exists'] = version is not None
    
    if not version:
        print_error("\n⚠️  無法繼續測試：v1.2.1 版本不存在")
        return
    
    # 測試 2: Baseline 切換
    test_results['baseline_switching'] = test_baseline_switching(version)
    
    # 測試 3: 動態載入
    test_results['dynamic_loading'] = test_dynamic_loading(version)
    
    # 測試 4: 快取機制
    test_results['cache_mechanism'] = test_threshold_manager_cache()
    
    # 測試 5: 配置變更檢測
    test_results['config_change_detection'] = test_config_change_detection()
    
    # 測試 6: 配置合併邏輯
    test_results['config_merge_logic'] = test_config_merge_logic(version)
    
    # ========================================================================
    # 測試結果總結
    # ========================================================================
    
    print_header("測試結果總結")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results.values() if result)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\n{Colors.BOLD}總計: {passed_tests}/{total_tests} 測試通過{Colors.ENDC}")
    
    if passed_tests == total_tests:
        print_success("\n🎉 所有測試通過！後端功能驗證成功！")
    else:
        print_error(f"\n⚠️  有 {total_tests - passed_tests} 個測試失敗，請檢查錯誤訊息")


if __name__ == '__main__':
    main()
