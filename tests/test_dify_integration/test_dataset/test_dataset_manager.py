#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DatasetManager 的 pytest 測試（使用真實 API）
測試 library/dify_integration/dataset_manager.py 的功能
"""

import sys
import os
import pytest
from unittest.mock import MagicMock, patch, Mock
import time

# 添加 library 路徑
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
library_path = os.path.join(repo_root, "library")
if library_path not in sys.path:
    sys.path.insert(0, library_path)

from dify_integration.dataset_manager import DatasetManager
from dify_integration.client import DifyClient

# 真實 API 配置
REAL_API_CONFIG = {
    'base_url': 'http://10.10.172.5',
    'dataset_api_key': 'dataset-JLa32OwILQHkgPqYStTCW4sC'
}


class TestDatasetManagerReal:
    """DatasetManager 真實 API 測試類"""
    
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
    
    def test_real_list_datasets(self, dataset_manager):
        """測試真實獲取知識庫列表"""
        result = dataset_manager.list_datasets(page=1, limit=5)
        
        # 驗證回應結構
        assert isinstance(result, dict)
        assert 'data' in result
        assert isinstance(result['data'], list)
        
        print(f"\n📋 找到 {len(result['data'])} 個知識庫:")
        for dataset in result['data'][:3]:  # 只顯示前3個
            print(f"  📝 {dataset['name']}")
            print(f"  🆔 ID: {dataset['id']}")
            print(f"  🔒 權限: {dataset.get('permission', 'unknown')}")
    
    
    def test_real_create_team_dataset(self, dataset_manager):
        """測試真實創建團隊知識庫（包含資料上傳）"""
        base_name = "pytest團隊測試"
        
        result = dataset_manager.create_team_dataset(
            name=base_name,
            description="pytest 團隊測試知識庫",
            permission="all_team_members"
        )
        
        # 驗證創建成功
        assert 'id' in result
        assert base_name in result['name']  # 名稱包含基礎名稱
        assert '_' in result['name']  # 包含時間戳分隔符
        assert result.get('permission') == 'all_team_members'
        
        print(f"\n✅ 成功創建團隊知識庫:")
        print(f"  🆔 ID: {result['id']}")
        print(f"  📝 名稱: {result['name']}")
        print(f"  🔒 權限: {result.get('permission')}")
        print(f"  🌐 直接 URL: {dataset_manager.get_dataset_direct_url(result['id'])}")
        
        # 插入測試資料
        try:
            upload_success = self._upload_test_data_to_dataset(dataset_manager, result['id'], result['name'])
            if upload_success:
                print(f"  📄 已成功上傳測試資料")
            else:
                print(f"  ⚠️ 資料上傳失敗")
        except Exception as e:
            print(f"  ❌ 資料上傳異常: {e}")
        
        # 清理：刪除測試知識庫
        try:
            dataset_manager.delete_dataset(result['id'])
            print(f"  🗑️ 已清理測試知識庫")
        except Exception as e:
            print(f"  ⚠️ 清理失敗: {e}")
        
        return result
    
    def _upload_test_data_to_dataset(self, dataset_manager, dataset_id, dataset_name):
        """向指定知識庫上傳測試資料"""
        print(f"\n📤 向 {dataset_name} 上傳員工資料...")
        
        # 測試員工資料
        employee_data = """
# AI 平台公司員工資訊

## 技術部門
- 張小明：後端工程師，薪資 75000，擅長 Python 和 Django
- 李美華：前端工程師，薪資 70000，擅長 React 和 Vue.js
- 劉志強：全端工程師，薪資 80000，擅長 React、Django、Docker
- 周小雅：UI/UX 設計師，薪資 65000，負責使用者介面設計

## 業務部門  
- 王大成：業務經理，薪資 65000，負責客戶關係管理
- 陳小芳：業務專員，薪資 50000，負責市場開發
- 林志明：業務總監，薪資 85000，負責整體業務策略

## 管理部門
- 黃執行長：執行長，薪資 120000，負責公司整體營運
- 吳財務長：財務長，薪資 100000，負責財務規劃

## 常見問題
Q: 公司有多少員工？
A: 目前公司共有 9 名員工。

Q: 技術部門有哪些人？
A: 技術部門有張小明（後端）、李美華（前端）、劉志強（全端）、周小雅（UI/UX）。

Q: 公司薪資結構如何？
A: 薪資範圍從 50000 到 120000，依據職位和經驗而定。

Q: 誰負責 AI 平台的技術開發？
A: 主要由技術部門負責，包括後端、前端和全端工程師。
"""
        
        # 使用 client 直接發送請求
        import requests
        
        headers = {
            'Authorization': f'Bearer {dataset_manager.client.api_key}',
            'Content-Type': 'application/json'
        }
        
        upload_config = {
            'name': f'pytest員工資料_{int(time.time())}',
            'text': employee_data,
            'indexing_technique': 'economy',
            'process_rule': {
                'mode': 'automatic'
            }
        }
        
        try:
            response = requests.post(
                f'{dataset_manager.client.base_url}/v1/datasets/{dataset_id}/document/create_by_text',
                headers=headers,
                json=upload_config,
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"    📄 文檔 ID: {data.get('document', {}).get('id')}")
                print(f"    📊 處理狀態: {data.get('document', {}).get('indexing_status')}")
                return True
            else:
                print(f"    ❌ 上傳失敗: {response.text}")
                return False
                
        except Exception as e:
            print(f"    ❌ 上傳異常: {e}")
            return False
    
    def test_real_create_multiple_datasets(self, dataset_manager):
        """測試真實創建多個不同權限的知識庫"""
        base_name = "pytest批量測試"
        
        results = dataset_manager.create_multiple_datasets_with_permissions(
            base_name=base_name,
            description_prefix="pytest 批量測試 - "
        )
        
        # 驗證結果
        assert len(results) >= 1  # 至少創建成功一個
        
        print(f"\n✅ 批量創建結果:")
        print(f"  📊 成功創建 {len(results)} 個知識庫")
        
        created_ids = []
        for dataset in results:
            print(f"  📝 {dataset['name']}")
            print(f"     🆔 ID: {dataset['id']}")
            print(f"     🔒 權限: {dataset['permission']}")
            print(f"     🌐 URL: {dataset_manager.get_dataset_direct_url(dataset['id'])}")
            created_ids.append(dataset['id'])
        
        # 清理：刪除所有測試知識庫
        for dataset_id in created_ids:
            try:
                dataset_manager.delete_dataset(dataset_id)
                print(f"  🗑️ 已清理知識庫 {dataset_id}")
            except Exception as e:
                print(f"  ⚠️ 清理知識庫 {dataset_id} 失敗: {e}")
        
        return results
    
    def test_real_search_datasets(self, dataset_manager):
        """測試真實搜尋知識庫"""
        # 搜尋包含 "pytest" 的知識庫
        result = dataset_manager.search_datasets_by_name("pytest", limit=10)
        
        # 驗證回應結構
        assert isinstance(result, dict)
        assert 'data' in result
        
        print(f"\n🔍 搜尋 'pytest' 結果:")
        print(f"  📊 找到 {len(result['data'])} 個匹配的知識庫")
        
        for dataset in result['data'][:5]:  # 只顯示前5個
            print(f"  📝 {dataset['name']}")
            print(f"     🆔 ID: {dataset['id']}")
            print(f"     🔒 權限: {dataset.get('permission', 'unknown')}")
    
    def test_real_get_dataset_details(self, dataset_manager):
        """測試真實獲取知識庫詳情"""
        # 首先獲取知識庫列表
        list_result = dataset_manager.list_datasets(limit=1)
        
        if not list_result.get('data'):
            pytest.skip("沒有可用的知識庫進行測試")
        
        # 取第一個知識庫的詳情
        first_dataset = list_result['data'][0]
        dataset_id = first_dataset['id']
        
        result = dataset_manager.get_dataset(dataset_id)
        
        # 驗證詳情
        assert result['id'] == dataset_id
        assert 'name' in result
        
        print(f"\n📄 知識庫詳情:")
        print(f"  🆔 ID: {result['id']}")
        print(f"  📝 名稱: {result['name']}")
        print(f"  📋 描述: {result.get('description', '無描述')}")
        print(f"  🔒 權限: {result.get('permission', 'unknown')}")
        print(f"  👤 創建者: {result.get('created_by', 'unknown')}")
    
    def test_real_update_dataset(self, dataset_manager):
        """測試真實更新知識庫"""
        # 首先創建一個測試知識庫
        test_name = f"pytest更新測試_{int(time.time())}"
        
        create_result = dataset_manager.create_dataset(
            name=test_name,
            description="原始描述",
            permission="only_me"
        )
        
        dataset_id = create_result['id']
        
        try:
            # 更新知識庫
            updated_name = f"pytest更新後_{int(time.time())}"
            updated_description = "更新後的描述"
            
            update_result = dataset_manager.update_dataset(
                dataset_id,
                name=updated_name,
                description=updated_description
            )
            
            # 驗證更新成功
            assert update_result['id'] == dataset_id
            
            print(f"\n✅ 成功更新知識庫:")
            print(f"  🆔 ID: {dataset_id}")
            print(f"  📝 新名稱: {updated_name}")
            print(f"  📋 新描述: {updated_description}")
            
        finally:
            # 清理：刪除測試知識庫
            try:
                dataset_manager.delete_dataset(dataset_id)
                print(f"  🗑️ 已清理測試知識庫")
            except Exception as e:
                print(f"  ⚠️ 清理失敗: {e}")


class TestDatasetManagerMock:
    """DatasetManager Mock 測試類（快速單元測試）"""
    """DatasetManager 測試類"""
    
    @pytest.fixture
    def mock_client(self):
        """創建 mock DifyClient"""
        client = MagicMock(spec=DifyClient)
        client.base_url = "http://test.dify.ai"
        return client
    
    @pytest.fixture
    def dataset_manager(self, mock_client):
        """創建 DatasetManager 實例（使用 mock 客戶端）"""
        return DatasetManager(mock_client)
    
    def test_init(self, mock_client):
        """測試 DatasetManager 初始化"""
        manager = DatasetManager(mock_client)
        assert manager.client == mock_client
    
    def test_create_dataset_basic(self, dataset_manager, mock_client):
        """測試基本知識庫創建"""
        # 設定模擬回應
        expected_response = {
            "id": "dataset-123",
            "name": "test_dataset",
            "description": "test description",
            "permission": "only_me"
        }
        mock_client.post.return_value = expected_response
        
        # 執行測試
        result = dataset_manager.create_dataset(
            name="test_dataset",
            description="test description",
            permission="only_me"
        )
        
        # 驗證結果
        assert result == expected_response
        
        # 驗證 API 呼叫
        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/datasets"
        
        # 驗證請求數據
        request_data = call_args[0][1]
        assert request_data["name"] == "test_dataset"
        assert request_data["description"] == "test description"
        assert request_data["permission"] == "only_me"
        assert request_data["indexing_technique"] == "economy"
        assert request_data["embedding_model"] == ""
        assert "retrieval_model" in request_data
    
    def test_create_dataset_default_params(self, dataset_manager, mock_client):
        """測試使用默認參數創建知識庫"""
        mock_client.post.return_value = {"id": "dataset-456"}
        
        result = dataset_manager.create_dataset("test_name")
        
        call_args = mock_client.post.call_args
        request_data = call_args[0][1]
        assert request_data["name"] == "test_name"
        assert request_data["description"] == ""
        assert request_data["permission"] == "only_me"
    
    def test_list_datasets(self, dataset_manager, mock_client):
        """測試獲取知識庫列表"""
        expected_response = {
            "data": [
                {"id": "1", "name": "dataset1"},
                {"id": "2", "name": "dataset2"}
            ],
            "total": 2,
            "page": 1
        }
        mock_client.get.return_value = expected_response
        
        result = dataset_manager.list_datasets(page=1, limit=10)
        
        assert result == expected_response
        mock_client.get.assert_called_once_with(
            "/v1/datasets", 
            {"page": 1, "limit": 10}
        )
    
    def test_list_datasets_default_params(self, dataset_manager, mock_client):
        """測試使用默認參數獲取知識庫列表"""
        mock_client.get.return_value = {"data": []}
        
        dataset_manager.list_datasets()
        
        mock_client.get.assert_called_once_with(
            "/v1/datasets", 
            {"page": 1, "limit": 20}
        )
    
    def test_get_dataset(self, dataset_manager, mock_client):
        """測試獲取單個知識庫詳情"""
        expected_response = {
            "id": "dataset-123",
            "name": "test_dataset",
            "description": "test description"
        }
        mock_client.get.return_value = expected_response
        
        result = dataset_manager.get_dataset("dataset-123")
        
        assert result == expected_response
        mock_client.get.assert_called_once_with("/v1/datasets/dataset-123")
    
    def test_update_dataset_name_only(self, dataset_manager, mock_client):
        """測試只更新知識庫名稱"""
        expected_response = {"id": "dataset-123", "name": "new_name"}
        mock_client.put.return_value = expected_response
        
        result = dataset_manager.update_dataset("dataset-123", name="new_name")
        
        assert result == expected_response
        mock_client.put.assert_called_once_with(
            "/v1/datasets/dataset-123",
            {"name": "new_name"}
        )
    
    def test_update_dataset_description_only(self, dataset_manager, mock_client):
        """測試只更新知識庫描述"""
        expected_response = {"id": "dataset-123", "description": "new description"}
        mock_client.put.return_value = expected_response
        
        result = dataset_manager.update_dataset("dataset-123", description="new description")
        
        assert result == expected_response
        mock_client.put.assert_called_once_with(
            "/v1/datasets/dataset-123",
            {"description": "new description"}
        )
    
    def test_update_dataset_both_params(self, dataset_manager, mock_client):
        """測試同時更新名稱和描述"""
        expected_response = {"id": "dataset-123", "name": "new_name", "description": "new desc"}
        mock_client.put.return_value = expected_response
        
        result = dataset_manager.update_dataset(
            "dataset-123", 
            name="new_name", 
            description="new desc"
        )
        
        assert result == expected_response
        mock_client.put.assert_called_once_with(
            "/v1/datasets/dataset-123",
            {"name": "new_name", "description": "new desc"}
        )
    
    def test_update_dataset_no_params(self, dataset_manager, mock_client):
        """測試不傳更新參數"""
        expected_response = {"id": "dataset-123"}
        mock_client.put.return_value = expected_response
        
        result = dataset_manager.update_dataset("dataset-123")
        
        assert result == expected_response
        mock_client.put.assert_called_once_with(
            "/v1/datasets/dataset-123",
            {}
        )
    
    def test_delete_dataset(self, dataset_manager, mock_client):
        """測試刪除知識庫"""
        expected_response = {"success": True, "message": "Dataset deleted"}
        mock_client.delete.return_value = expected_response
        
        result = dataset_manager.delete_dataset("dataset-123")
        
        assert result == expected_response
        mock_client.delete.assert_called_once_with("/v1/datasets/dataset-123")
    
    @patch('dify_integration.dataset_manager.time')
    def test_create_team_dataset_with_timestamp(self, mock_time, dataset_manager, mock_client):
        """測試創建團隊知識庫時添加時間戳"""
        # 模擬固定時間戳
        mock_time.time.return_value = 1234567890
        
        expected_response = {
            "id": "dataset-789",
            "name": "team_dataset_1234567890",
            "permission": "all_team_members"
        }
        mock_client.post.return_value = expected_response
        
        result = dataset_manager.create_team_dataset(
            name="team_dataset",
            description="team description",
            permission="all_team_members"
        )
        
        assert result == expected_response
        
        # 驗證 API 呼叫
        call_args = mock_client.post.call_args
        request_data = call_args[0][1]
        assert request_data["name"] == "team_dataset_1234567890"
        assert request_data["description"] == "team description"
        assert request_data["permission"] == "all_team_members"
    
    def test_create_team_dataset_default_permission(self, dataset_manager, mock_client):
        """測試創建團隊知識庫的默認權限"""
        mock_client.post.return_value = {"id": "dataset-999"}
        
        with patch('dify_integration.dataset_manager.time') as mock_time:
            mock_time.time.return_value = 9999999999
            dataset_manager.create_team_dataset("test_team")
        
        call_args = mock_client.post.call_args
        request_data = call_args[0][1]
        assert request_data["permission"] == "all_team_members"
    
    def test_create_multiple_datasets_with_permissions(self, dataset_manager, mock_client):
        """測試創建多個不同權限的知識庫"""
        # 模擬成功回應
        mock_client.post.side_effect = [
            {
                "id": "dataset-team",
                "name": "test_團隊共享_1234567890",
                "permission": "all_team_members",
                "created_by": "user-123"
            },
            {
                "id": "dataset-private", 
                "name": "test_僅限自己_1234567890",
                "permission": "only_me",
                "created_by": "user-123"
            }
        ]
        
        with patch('dify_integration.dataset_manager.time') as mock_time:
            mock_time.time.return_value = 1234567890
            
            result = dataset_manager.create_multiple_datasets_with_permissions(
                base_name="test",
                description_prefix="測試用"
            )
        
        # 驗證結果
        assert len(result) == 2
        
        # 驗證第一個知識庫（團隊共享）
        team_dataset = result[0]
        assert team_dataset["id"] == "dataset-team"
        assert team_dataset["permission"] == "all_team_members"
        
        # 驗證第二個知識庫（僅限自己）
        private_dataset = result[1]
        assert private_dataset["id"] == "dataset-private"
        assert private_dataset["permission"] == "only_me"
        
        # 驗證 API 被呼叫兩次
        assert mock_client.post.call_count == 2
    
    def test_create_multiple_datasets_with_error(self, dataset_manager, mock_client, capsys):
        """測試創建多個知識庫時的錯誤處理"""
        # 第一個成功，第二個失敗
        mock_client.post.side_effect = [
            {"id": "dataset-success", "name": "success", "permission": "all_team_members"},
            Exception("API Error")
        ]
        
        with patch('dify_integration.dataset_manager.time') as mock_time:
            mock_time.time.return_value = 1234567890
            
            result = dataset_manager.create_multiple_datasets_with_permissions("test")
        
        # 應該只有一個成功的結果
        assert len(result) == 1
        assert result[0]["id"] == "dataset-success"
        
        # 驗證錯誤訊息被打印
        captured = capsys.readouterr()
        assert "❌ 創建知識庫失敗" in captured.out
        assert "API Error" in captured.out
    
    def test_get_dataset_direct_url_with_client_base_url(self, dataset_manager, mock_client):
        """測試使用客戶端 base_url 生成直接 URL"""
        mock_client.base_url = "https://api.dify.ai"
        
        url = dataset_manager.get_dataset_direct_url("dataset-123")
        
        assert url == "https://api.dify.ai/datasets/dataset-123"
    
    def test_get_dataset_direct_url_with_custom_base_url(self, dataset_manager, mock_client):
        """測試使用自定義 base_url 生成直接 URL"""
        url = dataset_manager.get_dataset_direct_url(
            "dataset-456", 
            base_url="https://custom.dify.ai"
        )
        
        assert url == "https://custom.dify.ai/datasets/dataset-456"
    
    def test_search_datasets_by_name(self, dataset_manager, mock_client):
        """測試按名稱搜尋知識庫"""
        expected_response = {
            "data": [
                {"id": "1", "name": "search_result_1"},
                {"id": "2", "name": "search_result_2"}
            ],
            "total": 2
        }
        mock_client.get.return_value = expected_response
        
        result = dataset_manager.search_datasets_by_name(
            keyword="test_keyword",
            page=2,
            limit=5
        )
        
        assert result == expected_response
        mock_client.get.assert_called_once_with(
            "/v1/datasets",
            {
                "page": 2,
                "limit": 5,
                "keyword": "test_keyword"
            }
        )
    
    def test_search_datasets_by_name_default_params(self, dataset_manager, mock_client):
        """測試使用默認參數搜尋知識庫"""
        mock_client.get.return_value = {"data": []}
        
        dataset_manager.search_datasets_by_name("keyword")
        
        mock_client.get.assert_called_once_with(
            "/v1/datasets",
            {
                "page": 1,
                "limit": 20,
                "keyword": "keyword"
            }
        )


class TestDatasetManagerIntegration:
    """DatasetManager 整合測試（需要真實 API）"""
    
    @pytest.mark.integration
    def test_real_api_connection(self):
        """測試真實 API 連接（需要真實憑證）"""
        # 這個測試需要真實的 API 金鑰和網路連接
        # 在 CI/CD 中可以跳過，只在本地手動測試
        pytest.skip("需要真實 API 憑證，跳過整合測試")


if __name__ == "__main__":
    # 允許直接執行此文件進行測試
    pytest.main([__file__, "-v"])
