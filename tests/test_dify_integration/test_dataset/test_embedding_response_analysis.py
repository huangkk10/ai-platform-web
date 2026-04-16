#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試不同 embedding_model 設定的 API 回應
"""

import sys
import os
import pytest
import json

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


class TestEmbeddingModelResponse:
    """測試 embedding_model 在 API 回應中的表現"""
    
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
    
    def test_embedding_model_in_response(self, dataset_manager):
        """測試不同 embedding_model 設定在 API 回應中的表現"""
        
        test_cases = [
            {
                "name": "默認模型",
                "embedding_model": "",
                "description": "使用默認嵌入模型"
            },
            {
                "name": "bge-m3模型",
                "embedding_model": "bge-m3",
                "description": "嘗試使用 bge-m3 模型"
            }
        ]
        
        results = []
        
        print(f"\n🔬 測試不同 embedding_model 設定的 API 回應:")
        print("=" * 70)
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. 測試案例: {case['name']}")
            print(f"   embedding_model: '{case['embedding_model']}'")
            
            try:
                result = dataset_manager.create_team_dataset(
                    name=f"模型測試_{i}",
                    description=case['description'],
                    permission="all_team_members",
                    embedding_model=case['embedding_model']
                )
                
                if result.get('id'):
                    print(f"   ✅ 創建成功！")
                    
                    # 檢查回應中的 embedding 相關欄位
                    embedding_fields = {
                        'embedding_model': result.get('embedding_model'),
                        'embedding_model_provider': result.get('embedding_model_provider'),
                        'embedding_available': result.get('embedding_available'),
                        'indexing_technique': result.get('indexing_technique')
                    }
                    
                    print(f"   📊 回應中的 embedding 相關欄位:")
                    for field, value in embedding_fields.items():
                        print(f"      {field}: {value}")
                    
                    # 儲存結果
                    results.append({
                        'case': case,
                        'success': True,
                        'dataset_id': result['id'],
                        'embedding_fields': embedding_fields,
                        'full_response': result
                    })
                    
                    # 獲取知識庫詳情來比較
                    try:
                        details = dataset_manager.get_dataset(result['id'])
                        detail_embedding_fields = {
                            'embedding_model': details.get('embedding_model'),
                            'embedding_model_provider': details.get('embedding_model_provider'),
                            'embedding_available': details.get('embedding_available'),
                            'indexing_technique': details.get('indexing_technique')
                        }
                        
                        print(f"   📄 詳情中的 embedding 相關欄位:")
                        for field, value in detail_embedding_fields.items():
                            print(f"      {field}: {value}")
                        
                        results[-1]['detail_embedding_fields'] = detail_embedding_fields
                        
                    except Exception as e:
                        print(f"   ⚠️ 獲取詳情失敗: {e}")
                    
                    # 立即清理
                    try:
                        dataset_manager.delete_dataset(result['id'])
                        print(f"   🗑️ 已清理")
                    except Exception as e:
                        print(f"   ⚠️ 清理失敗: {e}")
                        
                else:
                    print(f"   ❌ 創建失敗：無效回應")
                    results.append({
                        'case': case,
                        'success': False,
                        'error': '無效回應'
                    })
                    
            except Exception as e:
                print(f"   ❌ 創建失敗：{str(e)}")
                results.append({
                    'case': case,
                    'success': False,
                    'error': str(e)
                })
        
        # 比較分析
        print(f"\n📊 分析結果:")
        print("=" * 50)
        
        successful_results = [r for r in results if r['success']]
        
        if len(successful_results) >= 2:
            default_result = successful_results[0]
            bge_result = successful_results[1]
            
            print(f"\n🔍 比較默認模型 vs bge-m3 模型:")
            print(f"默認模型 embedding_model: {default_result['embedding_fields']['embedding_model']}")
            print(f"bge-m3 模型 embedding_model: {bge_result['embedding_fields']['embedding_model']}")
            
            if default_result['embedding_fields']['embedding_model'] == bge_result['embedding_fields']['embedding_model']:
                print(f"⚠️ 兩者的 embedding_model 回應相同，可能系統忽略了 bge-m3 設定")
            else:
                print(f"✅ 兩者的 embedding_model 回應不同，設定有效")
        
        # 輸出完整的第一個成功結果用於檢查
        if successful_results:
            first_result = successful_results[0]
            print(f"\n📋 完整的 API 回應結構（第一個成功案例）:")
            print(json.dumps(first_result['full_response'], indent=2, ensure_ascii=False))
        
        return results


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])