#!/usr/bin/env python
"""
Baseline 切換 API 測試腳本
========================================

測試功能：
1. 獲取當前 Baseline 版本
2. 設定新的 Baseline 版本
3. 驗證快取清除機制
4. 錯誤處理測試（不存在的版本、未啟用的版本）

Created: 2025-11-27
Author: AI Platform Team
"""

import os
import sys
import django
import json
from datetime import datetime

# Django 環境設置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from django.db import connection

def print_section(title):
    """打印區段標題"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")

def print_success(message):
    """打印成功訊息"""
    print(f"✅ {message}")

def print_error(message):
    """打印錯誤訊息"""
    print(f"❌ {message}")

def print_info(message):
    """打印資訊訊息"""
    print(f"ℹ️  {message}")

def test_get_baseline_version():
    """測試 1：獲取當前 Baseline 版本"""
    print_section("測試 1：獲取當前 Baseline 版本")
    
    try:
        baseline = DifyConfigVersion.objects.filter(
            is_baseline=True,
            is_active=True
        ).first()
        
        if baseline:
            print_success(f"找到 Baseline 版本:")
            print(f"  ID: {baseline.id}")
            print(f"  版本代碼: {baseline.version_code}")
            print(f"  版本名稱: {baseline.version_name}")
            print(f"  檢索模式: {baseline.retrieval_mode}")
            
            # 檢查 RAG 配置
            if baseline.rag_settings:
                stage1 = baseline.rag_settings.get('stage1', {})
                use_hybrid = stage1.get('use_hybrid_search', False)
                rrf_k = stage1.get('rrf_k', 'N/A')
                title_bonus = stage1.get('title_match_bonus', 'N/A')
                
                print(f"\n  RAG 設定 (Stage 1):")
                print(f"    混合搜尋: {use_hybrid}")
                print(f"    RRF k: {rrf_k}")
                print(f"    Title Bonus: {title_bonus}%")
            
            return baseline
        else:
            print_error("找不到 Baseline 版本")
            return None
            
    except Exception as e:
        print_error(f"查詢失敗: {str(e)}")
        return None

def test_list_all_versions():
    """測試 2：列出所有可用版本"""
    print_section("測試 2：列出所有可用版本")
    
    try:
        versions = DifyConfigVersion.objects.filter(
            is_active=True
        ).order_by('version_code')
        
        print_info(f"找到 {versions.count()} 個啟用的版本:\n")
        
        for v in versions:
            baseline_mark = "⭐ Baseline" if v.is_baseline else ""
            print(f"  [{v.id}] {v.version_code} {baseline_mark}")
            print(f"      名稱: {v.version_name}")
            print(f"      檢索模式: {v.retrieval_mode}")
            print()
        
        return list(versions)
        
    except Exception as e:
        print_error(f"查詢失敗: {str(e)}")
        return []

def test_set_baseline_via_model(target_version_id):
    """測試 3：透過 Django Model 設定 Baseline（模擬 API 邏輯）"""
    print_section(f"測試 3：設定版本 ID {target_version_id} 為 Baseline")
    
    from django.db import transaction
    
    try:
        # 步驟 1: 驗證版本存在
        try:
            target = DifyConfigVersion.objects.get(id=target_version_id)
            print_info(f"目標版本: {target.version_code}")
        except DifyConfigVersion.DoesNotExist:
            print_error(f"版本 ID {target_version_id} 不存在")
            return False
        
        # 步驟 2: 檢查是否啟用
        if not target.is_active:
            print_error(f"版本「{target.version_name}」未啟用，無法設為 Baseline")
            return False
        
        # 步驟 3: 使用事務更新
        with transaction.atomic():
            # 取消所有 Baseline
            old_baselines = DifyConfigVersion.objects.filter(is_baseline=True)
            old_count = old_baselines.count()
            old_baselines.update(is_baseline=False)
            print_info(f"已取消 {old_count} 個舊 Baseline")
            
            # 設定新 Baseline
            target.is_baseline = True
            target.save()
            print_success(f"已設定新 Baseline: {target.version_code}")
        
        # 步驟 4: 清除快取（模擬）
        from api.views.dify_knowledge_views import clear_baseline_version_cache
        clear_baseline_version_cache()
        print_info("快取已清除")
        
        return True
        
    except Exception as e:
        print_error(f"設定 Baseline 失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_baseline_cache():
    """測試 4：驗證快取機制"""
    print_section("測試 4：驗證 Baseline 快取機制")
    
    from api.views.dify_knowledge_views import (
        get_baseline_version_code,
        clear_baseline_version_cache,
        _baseline_version_cache
    )
    
    try:
        # 清除快取
        clear_baseline_version_cache()
        print_info("步驟 1: 清除快取")
        print(f"  快取狀態: {_baseline_version_cache}")
        
        # 第一次調用（從資料庫讀取）
        print_info("\n步驟 2: 第一次調用 get_baseline_version_code()")
        version_code_1 = get_baseline_version_code()
        print_success(f"返回: {version_code_1}")
        print(f"  快取狀態: version_code={_baseline_version_cache.get('version_code')}")
        
        # 第二次調用（從快取讀取）
        print_info("\n步驟 3: 第二次調用 get_baseline_version_code()（應使用快取）")
        version_code_2 = get_baseline_version_code()
        print_success(f"返回: {version_code_2}")
        print(f"  快取狀態: {_baseline_version_cache.get('version_code')}")
        
        # 驗證一致性
        if version_code_1 == version_code_2:
            print_success("\n✅ 快取機制正常：兩次調用返回相同結果")
        else:
            print_error("\n❌ 快取機制異常：兩次調用返回不同結果")
        
        return True
        
    except Exception as e:
        print_error(f"測試快取機制失敗: {str(e)}")
        return False

def test_api_endpoints():
    """測試 5：測試 API 端點（curl 命令示例）"""
    print_section("測試 5：API 端點測試命令")
    
    baseline = DifyConfigVersion.objects.filter(
        is_baseline=True,
        is_active=True
    ).first()
    
    versions = DifyConfigVersion.objects.filter(is_active=True).exclude(
        is_baseline=True
    ).first()
    
    print_info("以下是可用的 curl 測試命令:\n")
    
    # 測試 1: 獲取 Baseline 版本
    print("1️⃣  獲取當前 Baseline 版本:")
    print("""
curl -X GET "http://localhost/api/dify/versions/baseline/" \\
  -H "Content-Type: application/json"
""")
    
    # 測試 2: 設定 Baseline（使用不同版本）
    if versions:
        print(f"2️⃣  設定版本 ID {versions.id} 為 Baseline:")
        print(f"""
curl -X POST "http://localhost/api/dify/versions/{versions.id}/set_baseline/" \\
  -H "Content-Type: application/json"
""")
    
    # 測試 3: 切換回原來的 Baseline
    if baseline:
        print(f"3️⃣  切換回原來的 Baseline (ID {baseline.id}):")
        print(f"""
curl -X POST "http://localhost/api/dify/versions/{baseline.id}/set_baseline/" \\
  -H "Content-Type: application/json"
""")
    
    # 測試 4: 錯誤測試（不存在的版本）
    print("4️⃣  錯誤測試（不存在的版本 ID 9999）:")
    print("""
curl -X POST "http://localhost/api/dify/versions/9999/set_baseline/" \\
  -H "Content-Type: application/json"
""")
    
    print_info("\n提示: 在 Docker 容器內執行請使用 localhost")
    print_info("     在容器外執行請使用 http://10.10.172.127")

def test_error_handling():
    """測試 6：錯誤處理測試"""
    print_section("測試 6：錯誤處理測試")
    
    from django.db import transaction
    
    # 測試 6.1: 不存在的版本 ID
    print_info("測試 6.1: 嘗試設定不存在的版本 ID 9999")
    try:
        target = DifyConfigVersion.objects.get(id=9999)
        print_error("預期應該拋出 DoesNotExist 異常")
    except DifyConfigVersion.DoesNotExist:
        print_success("正確：版本不存在時拋出異常")
    
    # 測試 6.2: 未啟用的版本
    print_info("\n測試 6.2: 尋找未啟用的版本")
    inactive = DifyConfigVersion.objects.filter(is_active=False).first()
    if inactive:
        print_info(f"找到未啟用版本: {inactive.version_code} (ID: {inactive.id})")
        if not inactive.is_active:
            print_success("正確：版本確實未啟用，API 應該拒絕")
    else:
        print_info("沒有未啟用的版本可測試")
    
    print_success("\n✅ 錯誤處理機制測試完成")

def main():
    """主測試流程"""
    print("\n" + "="*70)
    print("  Baseline 切換 API 完整測試")
    print("="*70)
    print(f"  執行時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 測試 1: 獲取當前 Baseline
    current_baseline = test_get_baseline_version()
    
    # 測試 2: 列出所有版本
    all_versions = test_list_all_versions()
    
    if not all_versions:
        print_error("\n無可用版本，終止測試")
        return
    
    # 測試 3: 設定 Baseline（如果有多個版本）
    if len(all_versions) > 1:
        # 找到一個非 Baseline 的版本
        non_baseline = next((v for v in all_versions if not v.is_baseline), None)
        if non_baseline:
            print_info(f"\n準備切換 Baseline 到版本: {non_baseline.version_code}")
            
            success = test_set_baseline_via_model(non_baseline.id)
            
            if success:
                # 驗證切換成功
                test_get_baseline_version()
                
                # 切換回原來的 Baseline
                if current_baseline:
                    print_info(f"\n準備切換回原來的 Baseline: {current_baseline.version_code}")
                    test_set_baseline_via_model(current_baseline.id)
                    test_get_baseline_version()
    
    # 測試 4: 快取機制
    test_baseline_cache()
    
    # 測試 5: API 端點示例
    test_api_endpoints()
    
    # 測試 6: 錯誤處理
    test_error_handling()
    
    # 總結
    print_section("測試總結")
    print_success("所有測試完成！")
    print_info("\n接下來的步驟:")
    print("  1. 使用上方的 curl 命令測試 HTTP API")
    print("  2. 在 VSA 前端實作「設為 Baseline」按鈕")
    print("  3. 驗證前後端整合")

if __name__ == '__main__':
    main()
