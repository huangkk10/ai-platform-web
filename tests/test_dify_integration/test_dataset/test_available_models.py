#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 Dify 系統可用的嵌入模型
"""

import sys
import os
import pytest
import requests

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


class TestAvailableModels:
    """測試可用模型"""
    
    @pytest.fixture
    def real_client(self):
        """創建真實的 DifyClient"""
        return DifyClient(
            api_key=REAL_API_CONFIG['dataset_api_key'],
            base_url=REAL_API_CONFIG['base_url']
        )
    
    @pytest.fixture
    def dataset_manager(self, real_client):
        """創建 DatasetManager 實例（使用真實客戶端）"""
        return DatasetManager(real_client)
    
    def test_common_embedding_models(self, dataset_manager):
        """測試常見的嵌入模型"""
        test_models = [
            # 常見的開源模型
            {"model": "bge-m3", "provider": "xinference"},
            {"model": "bge-large-zh", "provider": "xinference"},
            {"model": "text-embedding-ada-002", "provider": "openai"},
            {"model": "m3e-base", "provider": "xinference"},
            # 空值（默認）
            {"model": "", "provider": ""},
        ]
        
        successful_models = []
        failed_models = []
        
        print(f"\n🧪 測試不同嵌入模型的支援性:")
        print("=" * 60)
        
        for i, config in enumerate(test_models):
            model_name = config["model"] or "默認模型"
            provider = config["provider"] or "默認提供者"
            
            print(f"\n{i+1}. 測試模型: {model_name} (提供者: {provider})")
            
            try:
                result = dataset_manager.create_team_dataset(
                    name=f"測試模型_{i+1}",
                    description=f"測試 {model_name} 模型",
                    permission="all_team_members",
                    embedding_model=config["model"],
                    embedding_model_provider=config["provider"]
                )
                
                if result.get('id'):
                    print(f"   ✅ 成功！知識庫 ID: {result['id']}")
                    successful_models.append({
                        'model': model_name,
                        'provider': provider,
                        'dataset_id': result['id']
                    })
                    
                    # 立即清理
                    try:
                        dataset_manager.delete_dataset(result['id'])
                        print(f"   🗑️ 已清理")
                    except:
                        pass
                else:
                    print(f"   ❌ 創建失敗：無效回應")
                    failed_models.append({'model': model_name, 'provider': provider, 'error': '無效回應'})
                    
            except Exception as e:
                print(f"   ❌ 失敗：{str(e)}")
                failed_models.append({'model': model_name, 'provider': provider, 'error': str(e)})
        
        # 輸出總結
        print(f"\n📊 測試總結:")
        print("=" * 40)
        print(f"✅ 成功的模型 ({len(successful_models)} 個):")
        for model in successful_models:
            print(f"   - {model['model']} ({model['provider']})")
        
        print(f"\n❌ 失敗的模型 ({len(failed_models)} 個):")
        for model in failed_models:
            print(f"   - {model['model']} ({model['provider']}): {model['error'][:50]}...")
        
        # 至少要有一個成功的模型
        assert len(successful_models) > 0, "沒有任何模型可以使用"
        
        return successful_models, failed_models


if __name__ == "__main__":
    # 允許直接執行此文件進行測試
    pytest.main([__file__, "-v", "-s"])