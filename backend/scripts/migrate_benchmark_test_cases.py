#!/usr/bin/env python
"""
資料遷移腳本：將現有的 BenchmarkTestCase 和 DifyBenchmarkTestCase 
遷移到統一的 UnifiedBenchmarkTestCase 表

使用方式：
    docker exec ai-django python scripts/migrate_benchmark_test_cases.py
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.db import transaction
from api.models import BenchmarkTestCase, DifyBenchmarkTestCase, UnifiedBenchmarkTestCase


def migrate_protocol_test_cases():
    """遷移 Protocol Test Cases"""
    print("\n" + "="*60)
    print("開始遷移 Protocol Benchmark Test Cases")
    print("="*60)
    
    old_cases = BenchmarkTestCase.objects.all()
    total = old_cases.count()
    success_count = 0
    error_count = 0
    
    print(f"📊 找到 {total} 筆 Protocol Test Cases")
    
    with transaction.atomic():
        for i, old_case in enumerate(old_cases, 1):
            try:
                # 檢查是否已存在（防止重複遷移）
                exists = UnifiedBenchmarkTestCase.objects.filter(
                    test_type='protocol',
                    question=old_case.question,
                    category=old_case.category
                ).exists()
                
                if exists:
                    print(f"  ⏭️  [{i}/{total}] 已存在，跳過: {old_case.question[:50]}...")
                    continue
                
                # 創建新記錄
                UnifiedBenchmarkTestCase.objects.create(
                    test_type='protocol',
                    question=old_case.question,
                    test_class_name=old_case.category,  # 使用 category 作為 test_class_name
                    difficulty_level=old_case.difficulty_level or 'medium',
                    question_type=old_case.question_type,
                    category=old_case.category,
                    tags=old_case.tags,
                    is_active=old_case.is_active,
                    
                    # Protocol 專用欄位
                    expected_document_ids=old_case.expected_document_ids,
                    min_required_matches=old_case.min_required_matches,
                    acceptable_document_ids=old_case.acceptable_document_ids,
                    expected_keywords=old_case.expected_keywords,
                    expected_answer_summary=old_case.expected_answer_summary,
                    
                    # 統計欄位
                    is_validated=old_case.is_validated,
                    total_runs=old_case.total_runs,
                    avg_score=old_case.avg_score,
                    
                    # 管理欄位
                    source=old_case.source,
                    created_at=old_case.created_at,
                    updated_at=old_case.updated_at,
                    created_by=old_case.created_by,
                )
                
                success_count += 1
                print(f"  ✅ [{i}/{total}] 成功: {old_case.question[:50]}...")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ [{i}/{total}] 失敗: {old_case.question[:50]}... | 錯誤: {str(e)}")
    
    print(f"\n📊 Protocol 遷移完成:")
    print(f"   - 成功: {success_count} 筆")
    print(f"   - 失敗: {error_count} 筆")
    print(f"   - 跳過: {total - success_count - error_count} 筆")
    
    return success_count, error_count


def migrate_vsa_test_cases():
    """遷移 VSA (Dify) Test Cases"""
    print("\n" + "="*60)
    print("開始遷移 VSA (Dify) Test Cases")
    print("="*60)
    
    old_cases = DifyBenchmarkTestCase.objects.all()
    total = old_cases.count()
    success_count = 0
    error_count = 0
    
    print(f"📊 找到 {total} 筆 VSA Test Cases")
    
    with transaction.atomic():
        for i, old_case in enumerate(old_cases, 1):
            try:
                # 檢查是否已存在（防止重複遷移）
                exists = UnifiedBenchmarkTestCase.objects.filter(
                    test_type='vsa',
                    question=old_case.question,
                    test_class_name=old_case.test_class_name
                ).exists()
                
                if exists:
                    print(f"  ⏭️  [{i}/{total}] 已存在，跳過: {old_case.question[:50]}...")
                    continue
                
                # 創建新記錄
                UnifiedBenchmarkTestCase.objects.create(
                    test_type='vsa',
                    question=old_case.question,
                    test_class_name=old_case.test_class_name,
                    difficulty_level=old_case.difficulty_level,
                    question_type=old_case.question_type,
                    is_active=old_case.is_active,
                    
                    # VSA 專用欄位
                    expected_answer=old_case.expected_answer,
                    answer_keywords=old_case.answer_keywords,
                    evaluation_criteria=old_case.evaluation_criteria,
                    max_score=old_case.max_score,
                    
                    # 管理欄位
                    created_at=old_case.created_at,
                    updated_at=old_case.updated_at,
                )
                
                success_count += 1
                print(f"  ✅ [{i}/{total}] 成功: {old_case.question[:50]}...")
                
            except Exception as e:
                error_count += 1
                print(f"  ❌ [{i}/{total}] 失敗: {old_case.question[:50]}... | 錯誤: {str(e)}")
    
    print(f"\n📊 VSA 遷移完成:")
    print(f"   - 成功: {success_count} 筆")
    print(f"   - 失敗: {error_count} 筆")
    print(f"   - 跳過: {total - success_count - error_count} 筆")
    
    return success_count, error_count


def validate_migration():
    """驗證遷移結果"""
    print("\n" + "="*60)
    print("驗證遷移結果")
    print("="*60)
    
    old_protocol_count = BenchmarkTestCase.objects.count()
    old_vsa_count = DifyBenchmarkTestCase.objects.count()
    new_protocol_count = UnifiedBenchmarkTestCase.objects.filter(test_type='protocol').count()
    new_vsa_count = UnifiedBenchmarkTestCase.objects.filter(test_type='vsa').count()
    new_total_count = UnifiedBenchmarkTestCase.objects.count()
    
    print(f"\n📊 資料統計:")
    print(f"   舊 Protocol Test Cases: {old_protocol_count} 筆")
    print(f"   舊 VSA Test Cases: {old_vsa_count} 筆")
    print(f"   新 Protocol Test Cases: {new_protocol_count} 筆")
    print(f"   新 VSA Test Cases: {new_vsa_count} 筆")
    print(f"   新表總計: {new_total_count} 筆")
    
    # 驗證數量是否匹配
    all_match = (
        new_protocol_count >= old_protocol_count and 
        new_vsa_count >= old_vsa_count
    )
    
    if all_match:
        print(f"\n✅ 資料遷移驗證通過！")
        print(f"   - Protocol: {new_protocol_count}/{old_protocol_count} 筆")
        print(f"   - VSA: {new_vsa_count}/{old_vsa_count} 筆")
    else:
        print(f"\n⚠️  資料遷移可能有問題，請檢查！")
        if new_protocol_count < old_protocol_count:
            print(f"   ❌ Protocol: 遺失 {old_protocol_count - new_protocol_count} 筆")
        if new_vsa_count < old_vsa_count:
            print(f"   ❌ VSA: 遺失 {old_vsa_count - new_vsa_count} 筆")
    
    return all_match


def main():
    """主函數"""
    print("\n" + "🚀 "*30)
    print("統一測試案例資料遷移工具")
    print("🚀 "*30)
    
    try:
        # 檢查目標表是否為空
        existing_count = UnifiedBenchmarkTestCase.objects.count()
        if existing_count > 0:
            print(f"\n⚠️  警告: 統一表已存在 {existing_count} 筆資料")
            response = input("是否繼續遷移？(y/N): ")
            if response.lower() != 'y':
                print("❌ 遷移已取消")
                return
        
        # 執行遷移
        protocol_success, protocol_error = migrate_protocol_test_cases()
        vsa_success, vsa_error = migrate_vsa_test_cases()
        
        # 驗證結果
        validation_passed = validate_migration()
        
        # 總結
        print("\n" + "="*60)
        print("遷移總結")
        print("="*60)
        print(f"✅ Protocol 成功: {protocol_success} 筆")
        print(f"❌ Protocol 失敗: {protocol_error} 筆")
        print(f"✅ VSA 成功: {vsa_success} 筆")
        print(f"❌ VSA 失敗: {vsa_error} 筆")
        print(f"📊 驗證狀態: {'✅ 通過' if validation_passed else '❌ 失敗'}")
        
        if validation_passed and (protocol_error + vsa_error) == 0:
            print("\n🎉 所有資料遷移成功！")
        else:
            print("\n⚠️  遷移完成但有錯誤，請檢查日誌")
        
    except Exception as e:
        print(f"\n❌ 遷移過程發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
