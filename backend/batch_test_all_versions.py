"""
批量版本測試執行腳本

一次性測試所有搜尋演算法版本並生成對比報告

使用方式：
    # 測試所有版本
    python backend/batch_test_all_versions.py

    # 測試指定版本
    python backend/batch_test_all_versions.py --versions 5,6,7

    # 強制重新測試
    python backend/batch_test_all_versions.py --force

    # 只測試前 10 個案例（快速測試）
    python backend/batch_test_all_versions.py --limit 10

作者：AI Platform Team
日期：2025-11-23
"""

import os
import sys
import django
import argparse

# 設定 Django 環境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.benchmark.batch_version_tester import (
    BatchVersionTester,
    batch_test_all_versions,
    batch_test_selected_versions
)
from api.models import BenchmarkTestCase
import json


def main():
    parser = argparse.ArgumentParser(description='批量版本測試')
    
    parser.add_argument(
        '--versions',
        type=str,
        help='要測試的版本 ID，逗號分隔（例如：5,6,7）。不指定則測試所有版本'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='強制重新測試（即使已有測試結果）'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='限制測試案例數量（用於快速測試）'
    )
    
    parser.add_argument(
        '--category',
        type=str,
        help='只測試特定類別的案例'
    )
    
    parser.add_argument(
        '--difficulty',
        type=str,
        choices=['easy', 'medium', 'hard'],
        help='只測試特定難度的案例'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='顯示詳細日誌'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        help='將結果保存到 JSON 檔案'
    )
    
    args = parser.parse_args()
    
    # 準備測試案例 ID
    test_case_ids = None
    if args.limit or args.category or args.difficulty:
        queryset = BenchmarkTestCase.objects.filter(is_active=True)
        
        if args.category:
            queryset = queryset.filter(category=args.category)
        
        if args.difficulty:
            queryset = queryset.filter(difficulty_level=args.difficulty)
        
        if args.limit:
            queryset = queryset[:args.limit]
        
        test_case_ids = list(queryset.values_list('id', flat=True))
        
        if not test_case_ids:
            print("❌ 沒有符合條件的測試案例")
            return
        
        print(f"📋 已選擇 {len(test_case_ids)} 個測試案例")
    
    # 執行測試
    if args.versions:
        # 測試指定版本
        version_ids = [int(v.strip()) for v in args.versions.split(',')]
        print(f"🎯 測試指定版本: {version_ids}")
        
        result = batch_test_selected_versions(
            version_ids=version_ids,
            test_case_ids=test_case_ids,
            verbose=args.verbose
        )
    else:
        # 測試所有版本
        print("🎯 測試所有版本")
        
        result = batch_test_all_versions(
            test_case_ids=test_case_ids,
            force_retest=args.force,
            verbose=args.verbose
        )
    
    # 檢查結果
    if not result.get('success'):
        print(f"\n❌ 測試失敗: {result.get('message')}")
        return
    
    # 保存結果到檔案
    if args.output:
        # 準備可序列化的結果
        serializable_result = {
            'batch_id': result['batch_id'],
            'batch_name': result['batch_name'],
            'test_run_ids': result['test_run_ids'],
            'comparison': result['comparison'],
            'summary': result['summary'],
            'created_at': result['created_at'].isoformat()
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(serializable_result, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 結果已保存到: {args.output}")
    
    print("\n" + "="*80)
    print("✅ 批量測試完成！")
    print("="*80)
    
    # 打印快速訪問資訊
    print(f"\n📊 查看詳細結果:")
    print(f"   批次 ID: {result['batch_id']}")
    print(f"   測試執行 ID: {', '.join(map(str, result['test_run_ids']))}")
    print(f"\n💡 您可以在 Benchmark Dashboard 中查看這些測試執行的詳細結果")


if __name__ == '__main__':
    main()
