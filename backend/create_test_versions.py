#!/usr/bin/env python
"""
創建 Benchmark 測試版本（V1-V6）
================================

目的：
創建 6 個使用新策略引擎的 SearchAlgorithmVersion，用於測試不同的搜尋策略。

版本設計：
- V1: 純段落搜尋（section_only）- 高精準度
- V2: 純全文搜尋（document_only）- 高召回率
- V3: 混合 70-30（hybrid_weighted）⭐ 預期最佳
- V4: 混合 50-50（hybrid_weighted）- 平衡
- V5: 混合 80-20（hybrid_weighted）- 高精準
- V6: 混合 RRF（hybrid_rrf）🔄 向量+關鍵字+RRF 融合（來自 Dify v1.2.2）

所有版本都使用：
- use_strategy_engine: True（使用新策略引擎）
- 四維權重系統自動整合
"""

import os
import sys
import django
from decimal import Decimal

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import SearchAlgorithmVersion
from django.utils import timezone

def create_test_versions():
    """創建 5 個測試版本"""
    
    print("\n" + "="*80)
    print("🚀 創建 Benchmark 測試版本（V1-V5）")
    print("="*80)
    
    # 版本配置
    versions_config = [
        {
            'version_name': 'V1 - 純段落向量搜尋 🎯',
            'version_code': 'v3.1-section-only',
            'algorithm_type': 'section_only',
            'description': '純段落向量搜尋（高精準度，title=95%/content=5%）',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'section_only',
                'section_threshold': 0.75,
            },
        },
        {
            'version_name': 'V2 - 純全文向量搜尋 📚',
            'version_code': 'v3.2-document-only',
            'algorithm_type': 'document_only',
            'description': '純全文向量搜尋（高召回率，title=10%/content=90%）',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'document_only',
                'document_threshold': 0.65,
            },
        },
        {
            'version_name': 'V3 - 混合權重 70-30 ⭐',
            'version_code': 'v3.3-hybrid-70-30',
            'algorithm_type': 'hybrid_weighted',
            'description': '混合權重搜尋（section=70%, document=30%）- 預期最佳',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'hybrid_weighted',
                'section_weight': 0.7,
                'document_weight': 0.3,
                'section_threshold': 0.75,
                'document_threshold': 0.65,
            },
        },
        {
            'version_name': 'V4 - 混合權重 50-50 ⚖️',
            'version_code': 'v3.4-hybrid-50-50',
            'algorithm_type': 'hybrid_weighted',
            'description': '混合權重搜尋（section=50%, document=50%）- 平衡型',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'hybrid_weighted',
                'section_weight': 0.5,
                'document_weight': 0.5,
                'section_threshold': 0.75,
                'document_threshold': 0.65,
            },
        },
        {
            'version_name': 'V5 - 混合權重 80-20 🎯',
            'version_code': 'v3.5-hybrid-80-20',
            'algorithm_type': 'hybrid_weighted',
            'description': '混合權重搜尋（section=80%, document=20%）- 高精準型',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'hybrid_weighted',
                'section_weight': 0.8,
                'document_weight': 0.2,
                'section_threshold': 0.75,
                'document_threshold': 0.65,
            },
        },
        # 🆕 V6 - 混合 RRF 搜尋（來自 Dify v1.2.2 一階搜尋）
        {
            'version_name': 'V6 - 混合RRF搜尋（向量+關鍵字）🔄',
            'version_code': 'v3.6-hybrid-rrf',
            'algorithm_type': 'hybrid_rrf',
            'description': '混合搜尋（向量 + 關鍵字 + RRF 融合）- 來自 Dify v1.2.2 一階搜尋',
            'parameters': {
                'use_strategy_engine': True,
                'strategy': 'hybrid_rrf',
                # RRF 配置
                'use_hybrid_search': True,
                'rrf_k': 60,  # 業界標準
                # Title Boost 配置
                'title_match_bonus': 0.15,  # 15%
                'min_keyword_length': 2,
                # 搜尋配置
                'section_threshold': 0.80,
                'title_weight': 95,
                'content_weight': 5,
                'top_k': 20,
            },
        },
    ]
    
    created_versions = []
    
    for config in versions_config:
        try:
            # 檢查是否已存在
            existing = SearchAlgorithmVersion.objects.filter(
                version_code=config['version_code']
            ).first()
            
            if existing:
                print(f"\n⚠️  版本已存在: {config['version_name']}")
                print(f"   ID: {existing.id}")
                print(f"   代碼: {existing.version_code}")
                
                # 更新參數
                existing.parameters = config['parameters']
                existing.description = config['description']
                existing.algorithm_type = config['algorithm_type']
                existing.save()
                
                print(f"   ✅ 已更新參數")
                created_versions.append(existing)
                continue
            
            # 創建新版本
            version = SearchAlgorithmVersion.objects.create(
                version_name=config['version_name'],
                version_code=config['version_code'],
                algorithm_type=config['algorithm_type'],
                description=config['description'],
                parameters=config['parameters'],
                is_active=True,
            )
            
            print(f"\n✅ 創建成功: {config['version_name']}")
            print(f"   ID: {version.id}")
            print(f"   代碼: {version.version_code}")
            print(f"   策略: {config['parameters']['strategy']}")
            print(f"   參數: {config['parameters']}")
            
            created_versions.append(version)
            
        except Exception as e:
            print(f"\n❌ 創建失敗: {config['version_name']}")
            print(f"   錯誤: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 顯示摘要
    print("\n" + "="*80)
    print("📊 創建摘要")
    print("="*80)
    
    print(f"\n總計: {len(created_versions)} 個版本")
    
    for version in created_versions:
        params = version.parameters or {}
        strategy = params.get('strategy', 'unknown')
        
        print(f"\n📦 {version.version_name}")
        print(f"   ID: {version.id}")
        print(f"   代碼: {version.version_code}")
        print(f"   策略: {strategy}")
        
        if strategy == 'section_only':
            print(f"   配置: threshold={params.get('section_threshold', 0.75)}")
        elif strategy == 'document_only':
            print(f"   配置: threshold={params.get('document_threshold', 0.65)}")
        elif strategy == 'hybrid_weighted':
            section_w = params.get('section_weight', 0.7)
            document_w = params.get('document_weight', 0.3)
            print(f"   配置: section={section_w}, document={document_w}")
    
    print("\n" + "="*80)
    print("✅ 所有版本創建完成！")
    print("="*80)
    
    # 驗證 use_strategy_engine
    print("\n🔍 驗證策略引擎配置:")
    for version in created_versions:
        params = version.parameters or {}
        use_engine = params.get('use_strategy_engine', False)
        status = "✅" if use_engine else "❌"
        print(f"{status} {version.version_name}: use_strategy_engine={use_engine}")
    
    print("\n" + "="*80)
    print("📝 下一步:")
    print("1. 在 Benchmark Dashboard 中查看新版本")
    print("2. 執行測試運行（Run Test）")
    print("3. 對比不同策略的效能差異")
    print("="*80 + "\n")
    
    return created_versions


def verify_versions():
    """驗證所有版本"""
    print("\n" + "="*80)
    print("🔍 驗證現有版本")
    print("="*80)
    
    all_versions = SearchAlgorithmVersion.objects.all().order_by('id')
    
    print(f"\n總共 {len(all_versions)} 個版本:\n")
    
    for version in all_versions:
        params = version.parameters or {}
        use_engine = params.get('use_strategy_engine', False)
        strategy = params.get('strategy', 'N/A')
        
        print(f"ID={version.id:2d} | {version.version_name:40s} | "
              f"Engine={use_engine:5} | Strategy={strategy:20s}")
    
    # 統計
    engine_enabled = sum(1 for v in all_versions 
                        if (v.parameters or {}).get('use_strategy_engine', False))
    
    print("\n" + "-"*80)
    print(f"統計:")
    print(f"  - 使用策略引擎: {engine_enabled} 個")
    print(f"  - 使用舊路徑: {len(all_versions) - engine_enabled} 個")
    print("="*80 + "\n")


def main():
    """主流程"""
    try:
        # 創建測試版本
        created_versions = create_test_versions()
        
        # 驗證所有版本
        verify_versions()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
