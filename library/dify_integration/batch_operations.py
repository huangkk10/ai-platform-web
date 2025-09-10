"""
Dify 批量操作工具
提供知識庫和文檔的批量操作功能
"""

import time
from typing import Dict, List, Optional, Any
from .client import DifyClient
from .dataset_manager import DatasetManager
from .document_manager import DocumentManager


class DifyBatchOperations:
    """Dify 批量操作工具"""
    
    def __init__(self, client: DifyClient):
        """
        初始化批量操作工具
        
        Args:
            client: Dify API 客戶端
        """
        self.client = client
        self.dataset_manager = DatasetManager(client)
        self.document_manager = DocumentManager(client)
    
    def create_dataset_with_sample_data(self, 
                                      dataset_name: str, 
                                      dataset_description: str = "",
                                      permission: str = "all_team_members",
                                      sample_data: str = None) -> Dict:
        """
        創建知識庫並上傳示例資料
        
        Args:
            dataset_name: 知識庫名稱
            dataset_description: 知識庫描述
            permission: 權限設置
            sample_data: 示例資料內容
            
        Returns:
            操作結果包含知識庫和文檔信息
        """
        result = {
            'dataset': None,
            'document': None,
            'success': False,
            'error': None
        }
        
        try:
            # 1. 創建知識庫
            dataset_result = self.dataset_manager.create_team_dataset(
                dataset_name, 
                dataset_description, 
                permission
            )
            
            if not dataset_result.get('id'):
                result['error'] = "知識庫創建失敗"
                return result
            
            result['dataset'] = dataset_result
            dataset_id = dataset_result['id']
            
            # 2. 上傳示例資料（如果提供）
            if sample_data:
                doc_name = f"{dataset_name}_資料_{int(time.time())}"
                
                document_result = self.document_manager.create_document_by_text(
                    dataset_id,
                    doc_name,
                    sample_data
                )
                
                result['document'] = document_result
            
            result['success'] = True
            
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def create_employee_knowledge_base(self, base_name: str = "員工資訊庫") -> Dict:
        """
        創建包含員工資訊的知識庫
        
        Args:
            base_name: 基礎名稱
            
        Returns:
            創建結果
        """
        employee_data = """
# 公司員工資訊

## 技術部門
- 張小明：後端工程師，薪資 75000，擅長 Python 和 Django
- 李美華：前端工程師，薪資 70000，擅長 React 和 Vue.js
- 劉志強：全端工程師，薪資 80000，擅長 Node.js 和 React
- 周小雅：UI/UX 設計師，薪資 65000，擅長 Figma 和設計思維

## 業務部門  
- 王大成：業務經理，薪資 85000，負責客戶關係管理
- 陳小芳：業務專員，薪資 50000，負責市場開發
- 林大華：業務主管，薪資 90000，負責業務策略規劃

## 行政部門
- 黃小花：人資專員，薪資 55000，負責招聘和員工關係
- 蔡志明：財務會計，薪資 60000，負責財務管理

## 常見問題
Q: 公司有多少員工？
A: 目前公司共有 9 名正職員工。

Q: 技術部門有哪些人？
A: 技術部門有張小明（後端）、李美華（前端）、劉志強（全端）、周小雅（UI/UX）。

Q: 各部門平均薪資是多少？
A: 技術部門平均薪資 72500，業務部門平均薪資 75000，行政部門平均薪資 57500。

Q: 公司的技術棧有哪些？
A: 後端使用 Python/Django，前端使用 React/Vue.js，全端開發使用 Node.js。
"""
        
        return self.create_dataset_with_sample_data(
            dataset_name=base_name,
            dataset_description="包含公司員工基本資訊、部門結構和常見問題的知識庫",
            permission="all_team_members",
            sample_data=employee_data
        )
    
    def create_test_datasets_suite(self, project_name: str = "測試專案") -> List[Dict]:
        """
        創建一套測試用的知識庫
        
        Args:
            project_name: 專案名稱
            
        Returns:
            創建結果列表
        """
        test_suites = [
            {
                'name': f'{project_name}_API文檔',
                'description': 'API 介面文檔和使用說明',
                'permission': 'all_team_members',
                'data': """
# API 文檔

## 用戶管理 API
### 獲取用戶列表
- GET /api/users
- 參數：page, limit
- 回應：用戶列表和分頁資訊

### 創建用戶
- POST /api/users
- 參數：name, email, password
- 回應：創建的用戶資訊

## 認證 API
### 用戶登入
- POST /api/auth/login
- 參數：email, password
- 回應：JWT token
"""
            },
            {
                'name': f'{project_name}_技術文檔',
                'description': '技術架構和開發指南',
                'permission': 'only_me',
                'data': """
# 技術文檔

## 系統架構
- 前端：React + TypeScript
- 後端：Django + PostgreSQL
- 部署：Docker + Nginx

## 開發環境設定
1. 克隆專案：git clone ...
2. 安裝依賴：npm install, pip install -r requirements.txt
3. 啟動服務：docker-compose up

## 代碼規範
- 使用 ESLint 和 Prettier 格式化代碼
- 遵循 PEP 8 Python 代碼規範
- 提交訊息使用 Conventional Commits 格式
"""
            }
        ]
        
        results = []
        
        for suite in test_suites:
            result = self.create_dataset_with_sample_data(
                dataset_name=suite['name'],
                dataset_description=suite['description'],
                permission=suite['permission'],
                sample_data=suite['data']
            )
            
            result['suite_config'] = suite
            results.append(result)
        
        return results
    
    def upload_multiple_documents_to_dataset(self, 
                                           dataset_id: str, 
                                           documents: List[Dict]) -> List[Dict]:
        """
        向知識庫批量上傳文檔
        
        Args:
            dataset_id: 知識庫 ID
            documents: 文檔列表，每個元素包含 name 和 content
            
        Returns:
            上傳結果列表
        """
        results = []
        
        for doc in documents:
            try:
                result = self.document_manager.create_document_by_text(
                    dataset_id,
                    doc.get('name', f'文檔_{int(time.time())}'),
                    doc.get('content', '')
                )
                
                results.append({
                    'success': True,
                    'document': result,
                    'name': doc.get('name')
                })
                
            except Exception as e:
                results.append({
                    'success': False,
                    'error': str(e),
                    'name': doc.get('name')
                })
        
        return results