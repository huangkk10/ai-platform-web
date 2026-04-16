#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 embedding_model_provider 是否必須設定
"""

import sys
import os
import pytest

# 添加 library 路徑
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
library_path = os.path.join(repo_root, "library")
if library_path not in sys.path:
    sys.path.insert(0, library_path)

from dify_integration.dataset_manager import DatasetManager
from dify_integration.client import DifyClient

# 真實 API 配置
REAL_API_CONFIG = {
    'base_url': 'http://10.253.43.244',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}


class TestEmbeddingProviderRequired:
    """測試 embedding_model_provider 是否必須設定"""
    
    @pytest.fixture
    def real_client(self):
        """創建真實的 DifyClient"""
        return DifyClient(
            api_key=REAL_API_CONFIG['dataset_api_key'],
            base_url=REAL_API_CONFIG['base_url']
        )
    
    @pytest.fixture
    def dataset_manager(self, real_client):
        """創建 DatasetManager 實例"""
        return DatasetManager(real_client)
    
    def test_embedding_provider_combinations(self, dataset_manager):
        """測試不同的 embedding_model 和 embedding_model_provider 組合"""
        
        test_cases = [
            {
                "name": "完全默認",
                "embedding_model": "",
                "embedding_model_provider": "",
                "expected": "成功"
            },
            {
                "name": "只設定空模型，空提供者",
                "embedding_model": "",
                "embedding_model_provider": "",
                "expected": "成功"
            },
            {
                "name": "設定模型，不設定提供者",
                "embedding_model": "bge-m3",
                "embedding_model_provider": "",
                "expected": "可能失敗"
            },
            {
                "name": "不設定模型，設定提供者",
                "embedding_model": "",
                "embedding_model_provider": "xinference",
                "expected": "可能失敗"
            },
            {
                "name": "都設定",
                "embedding_model": "bge-m3",
                "embedding_model_provider": "xinference",
                "expected": "可能失敗"
            }
        ]
        
        results = []
        
        print(f"\n🧪 測試不同的 embedding_model_provider 組合:")
        print("=" * 70)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. {case['name']}")
            print(f"   模型: '{case['embedding_model']}'")
            print(f"   提供者: '{case['embedding_model_provider']}'")
            print(f"   預期: {case['expected']}")
            
            try:
                result = dataset_manager.create_team_dataset(
                    name=f"測試組合_{i}",
                    description=f"測試 {case['name']}",
                    permission="all_team_members",
                    embedding_model=case['embedding_model'],
                    embedding_model_provider=case['embedding_model_provider']
                )
                
                if result.get('id'):
                    print(f"   ✅ 成功！ID: {result['id']}")
                    results.append({
                        'case': case,
                        'success': True,
                        'dataset_id': result['id']
                    })
                    
                    # 立即清理
                    try:
                        dataset_manager.delete_dataset(result['id'])
                        print(f"   🗑️ 已清理")
                    except:
                        pass
                else:
                    print(f"   ❌ 失敗：無效回應")
                    results.append({
                        'case': case,
                        'success': False,
                        'error': '無效回應'
                    })
                    
            except Exception as e:
                print(f"   ❌ 失敗：{str(e)[:50]}...")
                results.append({
                    'case': case,
                    'success': False,
                    'error': str(e)
                })
        
        # 分析結果
        print(f"\n📊 測試結果分析:")
        print("=" * 50)
        
        successful_cases = [r for r in results if r['success']]
        failed_cases = [r for r in results if not r['success']]
        
        print(f"\n✅ 成功的組合 ({len(successful_cases)} 個):")
        for result in successful_cases:
            case = result['case']
            print(f"   - {case['name']}: 模型='{case['embedding_model']}', 提供者='{case['embedding_model_provider']}'")
        
        print(f"\n❌ 失敗的組合 ({len(failed_cases)} 個):")
        for result in failed_cases:
            case = result['case']
            print(f"   - {case['name']}: {result['error'][:30]}...")
        
        # 結論
        print(f"\n🎯 結論:")
        if len(successful_cases) == 1 and successful_cases[0]['case']['name'] == "完全默認":
            print("   embedding_model_provider 不需要設定，使用默認值即可")
        elif len(successful_cases) > 1:
            print("   embedding_model_provider 可以彈性設定")
        else:
            print("   需要進一步分析")
        
        return results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])