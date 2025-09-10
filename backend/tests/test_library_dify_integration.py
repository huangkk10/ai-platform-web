"""
使用 Library 重寫的團隊權限知識庫測試
展示如何使用 library/dify_integration 模組
"""

import sys
import os

# 添加 library 路徑
sys.path.append('/app/library')

from dify_integration import DifyClient, DatasetManager, DifyBatchOperations
from config import DifyConfig


def test_with_library():
    """使用 library 模組測試知識庫功能"""
    print("🚀 使用 Library 模組測試 Dify 知識庫")
    print("=" * 60)
    
    # 1. 初始化配置和客戶端
    try:
        # 使用配置管理器
        config = DifyConfig(
            api_key="dataset-JLa32OwILQHkgPqYStTCW4sC",
            config={'base_url': 'http://10.10.172.5'}
        )
        
        # 創建客戶端
        client = DifyClient(config.api_key, config.get('base_url'))
        
        # 創建管理器
        dataset_manager = DatasetManager(client)
        batch_ops = DifyBatchOperations(client)
        
        print("✅ 初始化成功")
        
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return
    
    # 2. 測試創建多個權限的知識庫
    print("\n📊 測試創建多權限知識庫...")
    try:
        datasets = dataset_manager.create_multiple_datasets_with_permissions(
            base_name="Library測試",
            description_prefix="使用Library創建的"
        )
        
        print(f"✅ 成功創建 {len(datasets)} 個知識庫")
        
        for dataset in datasets:
            print(f"  🆔 ID: {dataset['id']}")
            print(f"  📝 名稱: {dataset['name']}")
            print(f"  🔒 權限: {dataset['permission']}")
            print(f"  🌐 直接 URL: {dataset_manager.get_dataset_direct_url(dataset['id'])}")
            print()
            
    except Exception as e:
        print(f"❌ 創建知識庫失敗: {e}")
        return
    
    # 3. 測試創建帶資料的員工知識庫
    print("👥 測試創建員工知識庫...")
    try:
        employee_kb = batch_ops.create_employee_knowledge_base("Library員工資訊庫")
        
        if employee_kb['success']:
            dataset_info = employee_kb['dataset']
            document_info = employee_kb['document']
            
            print("✅ 員工知識庫創建成功")
            print(f"  🆔 知識庫 ID: {dataset_info['id']}")
            print(f"  📝 知識庫名稱: {dataset_info['name']}")
            
            if document_info:
                doc_id = document_info.get('document', {}).get('id')
                print(f"  📄 文檔 ID: {doc_id}")
                print(f"  📊 處理狀態: {document_info.get('document', {}).get('indexing_status')}")
            
            print(f"  🌐 直接 URL: {dataset_manager.get_dataset_direct_url(dataset_info['id'])}")
            
        else:
            print(f"❌ 員工知識庫創建失敗: {employee_kb['error']}")
            
    except Exception as e:
        print(f"❌ 員工知識庫創建異常: {e}")
    
    # 4. 測試創建測試套件
    print("\n🧪 測試創建測試套件...")
    try:
        test_results = batch_ops.create_test_datasets_suite("Library專案")
        
        successful_count = sum(1 for r in test_results if r['success'])
        print(f"✅ 測試套件創建完成，成功 {successful_count}/{len(test_results)} 個")
        
        for result in test_results:
            suite_name = result['suite_config']['name']
            if result['success']:
                dataset_info = result['dataset']
                print(f"  ✅ {suite_name}")
                print(f"     🆔 ID: {dataset_info['id']}")
                print(f"     🌐 URL: {dataset_manager.get_dataset_direct_url(dataset_info['id'])}")
            else:
                print(f"  ❌ {suite_name}: {result['error']}")
            
    except Exception as e:
        print(f"❌ 測試套件創建異常: {e}")
    
    print("\n🎉 Library 模組測試完成！")
    print("\n💡 測試建議:")
    print("1. 檢查上述 URL 是否能在 Dify UI 中直接訪問")
    print("2. 在 UI 中搜尋 'Library' 關鍵字")
    print("3. 確認 'all_team_members' 權限的知識庫在 UI 中可見")


def test_search_functionality():
    """測試搜尋功能"""
    print("\n🔍 測試搜尋功能...")
    
    try:
        config = DifyConfig(
            api_key="dataset-JLa32OwILQHkgPqYStTCW4sC",
            config={'base_url': 'http://10.10.172.5'}
        )
        
        client = DifyClient(config.api_key, config.get('base_url'))
        dataset_manager = DatasetManager(client)
        
        # 搜尋包含 "Library" 的知識庫
        search_results = dataset_manager.search_datasets_by_name("Library")
        
        if search_results.get('data'):
            print(f"✅ 找到 {len(search_results['data'])} 個包含 'Library' 的知識庫")
            
            for dataset in search_results['data']:
                print(f"  📝 {dataset['name']}")
                print(f"  🆔 ID: {dataset['id']}")
                print(f"  🔒 權限: {dataset.get('permission', 'unknown')}")
                print()
        else:
            print("📭 沒有找到包含 'Library' 的知識庫")
            
    except Exception as e:
        print(f"❌ 搜尋功能測試失敗: {e}")


if __name__ == "__main__":
    test_with_library()
    test_search_functionality()