# Dify SAF 外部知識庫 API 設計文檔

**文檔版本**：v2.0  
**創建日期**：2025-12-04  
**更新日期**：2025-12-04  
**作者**：AI Platform Team  
**狀態**：✅ 已完成實作

---

## 🎉 實作完成摘要

### API 端點
- **健康檢查**: `GET /api/dify/saf/health/`
- **知識庫檢索**: `POST /api/dify/saf/retrieval/`
- **端點資訊**: `GET /api/dify/saf/endpoints/`

### 支援的 Knowledge ID
| Knowledge ID | 功能 | 狀態 |
|-------------|------|------|
| `saf_projects` | 專案搜尋（完整資訊） | ✅ 完成 |
| `saf_project_names` | 專案名稱清單（輕量級） | ✅ 完成 |
| `saf_summary` | 專案統計（待 SAF API 支援） | � 待完善 |
| `saf_db` | 向後兼容別名 | ✅ 完成 |

### 程式碼結構
```
library/saf_integration/
├── __init__.py           # 模組入口
├── endpoint_registry.py  # API 端點定義
├── api_client.py         # SAF API 客戶端
├── auth_manager.py       # 認證管理
├── cache_manager.py      # 快取管理
├── data_transformer.py   # 資料轉換
├── search_service.py     # 搜尋服務
└── handler.py            # Dify 處理器

backend/api/views/
└── dify_saf_views.py     # API Views
```

---

## 📋 目錄

1. [專案概述](#1-專案概述)
2. [系統架構設計](#2-系統架構設計)
3. [SAF API Server 分析](#3-saf-api-server-分析)
4. [獨立入口 API 設計](#4-獨立入口-api-設計) ← 🆕 新增
5. [後端 API 定義架構](#5-後端-api-定義架構)
6. [資料轉換層設計](#6-資料轉換層設計)
7. [實作計畫](#7-實作計畫)
8. [測試策略](#8-測試策略)
9. [安全考量](#9-安全考量)

---

## 1. 專案概述

### 1.1 背景

目前 AI Platform 已有完整的 Dify 外部知識庫整合架構，支援多種知識源：
- Know Issue Database
- RVT Guide Database
- Protocol Guide Database
- OCR Storage Benchmark
- Employee Database

現在需要新增 **SAF (Silicon Motion)** 外部資料源整合，透過 SAF API Server（`http://10.252.170.171:8080`）取得專案相關資訊，並提供給 Dify AI Assistant 使用。

### 1.2 目標

1. **🆕 獨立入口 API**：建立專屬的 `/api/dify/saf/retrieval/` 入口，與現有知識庫 API 分離
2. **可配置 API 定義**：在後端定義不同的 API 源（endpoint），支援動態切換
3. **資料轉換層**：將外部 API 回傳的資料轉換為 Dify 知識庫格式
4. **擴展性設計**：未來可輕鬆新增其他外部 API 源

### 1.3 架構選擇：獨立入口 vs 統一入口

| 比較項目 | 統一入口 (`/api/dify/knowledge/retrieval/`) | 🆕 獨立入口 (`/api/dify/saf/retrieval/`) |
|---------|-------------------------------------------|------------------------------------------|
| **優點** | 現有架構，改動小 | 清晰分離，易於管理和擴展 |
| **API 定義** | 混在一起 | 獨立定義，可自訂參數格式 |
| **未來擴展** | 需要修改現有 handler | 獨立模組，不影響現有功能 |
| **Dify 配置** | 共用同一個外部知識 API | 專屬 API 端點 |
| **選擇** | - | ✅ **採用此方案** |

### 1.4 需求分析

### 1.4 需求分析

| 需求項目 | 說明 | 優先級 |
|---------|------|--------|
| 🆕 獨立入口 API | `/api/dify/saf/retrieval/` 專屬端點 | 🔴 高 |
| SAF 專案查詢 | 整合 SAF API 的專案列表和統計 | 🔴 高 |
| API 定義管理 | 後端可配置的 endpoint 定義 | 🔴 高 |
| 認證管理 | 管理 SAF API 的認證資訊 | � 高 |
| 快取機制 | 減少對外部 API 的請求頻率 | 🟡 中 |
| 錯誤處理 | 完善的錯誤處理和降級機制 | 🔴 高 |

---

## 2. 系統架構設計

### 2.1 整體架構圖

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Dify AI Studio                               │
│                    (External Knowledge Base)                         │
└───────────────────┬─────────────────────────┬───────────────────────┘
                    │                         │
        現有知識庫   │                         │ 🆕 SAF 知識庫
                    ▼                         ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    AI Platform Django Backend                        │
│                                                                      │
│  ┌─────────────────────────┐    ┌─────────────────────────────────┐ │
│  │  /api/dify/knowledge/   │    │  🆕 /api/dify/saf/retrieval/    │ │
│  │      retrieval/         │    │       (獨立入口 API)            │ │
│  │   (現有統一入口)         │    └───────────────┬─────────────────┘ │
│  └─────────────────────────┘                    │                    │
│                                                 ▼                    │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              🆕 SAF Knowledge Router                           │  │
│  │                   (SAF 路由分發器)                             │  │
│  │                                                                 │  │
│  │  endpoint 參數路由:                                            │  │
│  │  ├── projects      → SAFProjectSearchService (專案搜尋)        │  │
│  │  ├── summary       → SAFSummarySearchService (統計資訊)        │  │
│  │  ├── project_detail → SAFProjectDetailService (專案詳情) 🔮    │  │
│  │  └── (未來擴展...)                                             │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              🆕 SAF Endpoint Registry                          │  │
│  │                 (SAF API 端點註冊表)                           │  │
│  │                                                                 │  │
│  │  endpoints = {                                                  │  │
│  │    "projects": {                                               │  │
│  │      "path": "/api/v1/projects",                               │  │
│  │      "method": "GET",                                          │  │
│  │      "description": "查詢專案列表"                              │  │
│  │    },                                                          │  │
│  │    "summary": {                                                │  │
│  │      "path": "/api/v1/projects/summary",                       │  │
│  │      "method": "GET",                                          │  │
│  │      "description": "查詢專案統計"                              │  │
│  │    }                                                           │  │
│  │  }                                                              │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
│                              │                                       │
│                              ▼                                       │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              SAF API Client + Data Transformer                 │  │
│  │  - 認證管理 (Header: Authorization, Authorization-Name)        │  │
│  │  - 請求快取 (TTL: 5 分鐘)                                      │  │
│  │  - 資料轉換 (SAF Format → Dify Format)                        │  │
│  │  - 錯誤處理                                                    │  │
│  └───────────────────────────┬───────────────────────────────────┘  │
└──────────────────────────────┼───────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     SAF API Server                                   │
│                  http://10.252.170.171:8080                         │
│                                                                      │
│  Endpoints:                                                          │
│  - POST /api/v1/auth/login-with-config  (認證)                      │
│  - GET  /api/v1/projects                (專案列表)                  │
│  - GET  /api/v1/projects/summary        (專案統計)                  │
│  - GET  /health                         (健康檢查)                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 2.2 模組結構設計

```
backend/
├── api/
│   └── views/
│       └── dify_saf_views.py           # 🆕 SAF 獨立入口 Views
│
└── library/
    └── saf_integration/                 # 🆕 SAF 整合模組
        ├── __init__.py                  # 模組入口，導出主要類別
        ├── handler.py                   # SAFKnowledgeHandler (請求處理)
        ├── api_client.py                # SAF API 客戶端
        ├── endpoint_registry.py         # Endpoint 定義註冊表
        ├── auth_manager.py              # 認證管理
        ├── data_transformer.py          # 資料轉換器
        ├── search_service.py            # 搜尋服務
        └── cache_manager.py             # 快取管理

tests/
└── test_saf_integration/               # 🆕 SAF 測試
    ├── __init__.py
    ├── test_api_client.py
    ├── test_handler.py
    ├── test_data_transformer.py
    └── test_search_service.py
```

---

## 3. SAF API Server 分析

### 3.1 API Server 資訊

| 項目 | 值 |
|------|-----|
| **Base URL** | `http://10.252.170.171:8080` |
| **API 版本** | v0.1.0 |
| **文檔位置** | `/docs` (Swagger UI), `/redoc` (ReDoc) |
| **健康檢查** | `/health` |

### 3.2 可用 API 端點

#### 3.2.1 認證 API

```bash
# 使用帳密登入
POST /api/v1/auth/login
Content-Type: application/json
{
    "username": "your_username",
    "password": "your_password"
}

# 使用設定檔登入（推薦）
POST /api/v1/auth/login-with-config
# 無需 body，使用 .env 中的 SAF_USERNAME 和 SAF_PASSWORD
```

**回應格式**：
```json
{
    "success": true,
    "data": {
        "user_id": 150,
        "user_name": "Chunwei.Huang",
        "email": "chunwei.huang@example.com"
    },
    "message": null,
    "timestamp": "2025-12-04T06:58:33.933835Z"
}
```

#### 3.2.2 專案列表 API

```bash
GET /api/v1/projects?page=1&size=50
Headers:
  Authorization: {user_id}
  Authorization-Name: {user_name}
```

**回應格式**：
```json
{
    "success": true,
    "data": {
        "items": [
            {
                "key": "b77416d3547548fc8d332248744bf2d1",
                "projectUid": "b77416d3547548fc8d332248744bf2d1",
                "projectId": "5ccbc1dfd5e1493681c1a42bf39fe136",
                "projectName": "DEMETER",
                "productCategory": "Automotive_PCIe",
                "customer": "WD",
                "controller": "SM2264XT",
                "subVersion": "AC",
                "nand": "WDC BiCS5 TLC",
                "fw": "[MR1.2][Y1114B_629fa1a_Y1114A_8572096]",
                "pl": "ryder.lin, bruce.zhang",
                "visible": true,
                "status": 0,
                "createdBy": "bruce.zhang",
                "taskId": "SM2264AUTO-4809",
                "nasLogFolder": "SVD_15Y",
                "children": [...]  // 子專案
            }
        ],
        "total": 642,
        "page": 1,
        "size": 50
    }
}
```

#### 3.2.3 專案統計 API

```bash
GET /api/v1/projects/summary
Headers:
  Authorization: {user_id}
  Authorization-Name: {user_name}
```

**回應格式**：
```json
{
    "success": true,
    "data": {
        "total": 642,
        "by_customer": {
            "WD": 150,
            "Samsung": 200,
            ...
        },
        "by_controller": {
            "SM2264XT": 100,
            "SM2267": 80,
            ...
        }
    }
}
```

### 3.3 專案資料欄位分析

| 欄位名 | 類型 | 說明 | Dify 用途 |
|--------|------|------|-----------|
| `projectName` | string | 專案名稱 | 🔴 主要搜尋欄位 |
| `customer` | string | 客戶名稱 | 🔴 主要搜尋欄位 |
| `controller` | string | 控制器型號 | 🔴 主要搜尋欄位 |
| `nand` | string | NAND 類型 | 🟡 次要搜尋欄位 |
| `fw` | string | 韌體版本 | 🟡 次要搜尋欄位 |
| `productCategory` | string | 產品類別 | 🟡 過濾欄位 |
| `pl` | string | 負責人 | 🟢 附加資訊 |
| `taskId` | string | 任務 ID | 🟢 附加資訊 |
| `status` | int | 狀態 | 🟢 過濾欄位 |

---

## 4. 獨立入口 API 設計

### 4.1 API 端點規劃

建立專屬的 SAF 外部知識庫 API 入口：

| API 端點 | 說明 | Dify 配置 |
|---------|------|-----------|
| `POST /api/dify/saf/retrieval/` | 🆕 SAF 知識庫主入口 | 外部知識 API |
| `GET /api/dify/saf/endpoints/` | 🆕 列出可用的 endpoint 定義 | 管理用 |
| `GET /api/dify/saf/health/` | 🆕 檢查 SAF API 連線狀態 | 監控用 |

### 4.2 主入口 API 規格

#### 請求格式

```bash
POST /api/dify/saf/retrieval/
Content-Type: application/json

{
    "knowledge_id": "saf_db",           # 固定值，用於 Dify 識別
    "query": "WD SM2264",               # 搜尋查詢
    "retrieval_setting": {
        "top_k": 5,                     # 返回結果數量
        "score_threshold": 0.3          # 分數閾值
    },
    "endpoint": "projects"              # 🆕 指定要查詢的 SAF API endpoint
}
```

#### 支援的 endpoint 參數

| endpoint 值 | 對應 SAF API | 說明 |
|-------------|-------------|------|
| `projects` (預設) | `GET /api/v1/projects` | 搜尋專案列表（完整資訊） |
| `summary` | `GET /api/v1/projects/summary` | 取得專案統計 |
| `project_names` | `GET /api/v1/projects` → 轉換 | 🆕 取得所有專案名稱清單（輕量級） |
| `project_detail` | `GET /api/v1/projects/{id}` | 取得單一專案詳情 (🔮 未來擴展) |

#### 回應格式

符合 Dify 外部知識庫標準格式：

```json
{
    "records": [
        {
            "content": "專案名稱: DEMETER\n客戶: WD\n控制器: SM2264XT\nNAND: WDC BiCS5 TLC\n韌體版本: [MR1.2][Y1114B_629fa1a]\n負責人: ryder.lin, bruce.zhang\n任務 ID: SM2264AUTO-4809",
            "score": 0.85,
            "title": "DEMETER - WD",
            "metadata": {
                "source": "saf_projects",
                "endpoint": "projects",
                "project_uid": "b77416d3547548fc8d332248744bf2d1",
                "project_name": "DEMETER",
                "customer": "WD",
                "controller": "SM2264XT"
            }
        }
    ]
}
```

### 4.3 Endpoint 定義管理

後端可配置的 API endpoint 定義，支援未來擴展：

```python
# library/saf_integration/endpoint_registry.py

SAF_ENDPOINTS = {
    "projects": {
        "path": "/api/v1/projects",
        "method": "GET",
        "description": "查詢 SAF 專案列表",
        "params": {
            "page": 1,
            "size": 100
        },
        "search_fields": ["projectName", "customer", "controller", "nand", "fw"],
        "transformer": "project_to_dify_record",
        "enabled": True
    },
    "summary": {
        "path": "/api/v1/projects/summary",
        "method": "GET",
        "description": "查詢 SAF 專案統計摘要",
        "params": {},
        "search_fields": [],
        "transformer": "summary_to_dify_record",
        "enabled": True
    },
    # 🆕 新增：專案名稱清單
    "project_names": {
        "path": "/api/v1/projects",
        "method": "GET",
        "description": "取得所有專案名稱清單（輕量級）",
        "params": {
            "page": 1,
            "size": 1000  # 取得所有專案
        },
        "search_fields": ["projectName"],
        "transformer": "project_names_to_dify_record",
        "enabled": True,
        "extract_fields": ["projectName", "customer", "controller"]  # 只提取需要的欄位
    },
    # 🔮 未來擴展
    "project_detail": {
        "path": "/api/v1/projects/{project_id}",
        "method": "GET",
        "description": "查詢單一專案詳情",
        "params": {},
        "path_params": ["project_id"],
        "transformer": "project_detail_to_dify_record",
        "enabled": False  # 尚未啟用
    }
}
```

### 4.4 與現有架構的關係

```
┌─────────────────────────────────────────────────────────────────┐
│                    Django URL 路由                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  # 現有路由（保持不變）                                          │
│  path('dify/knowledge/retrieval/', dify_knowledge_search)       │
│  path('dify/protocol/knowledge/retrieval/', dify_know_issue_search) │
│  path('dify/rvt/knowledge/retrieval/', dify_rvt_guide_search)   │
│                                                                  │
│  # 🆕 新增 SAF 獨立路由                                         │
│  path('dify/saf/retrieval/', dify_saf_search)          # 主入口  │
│  path('dify/saf/retrieval', dify_saf_search)           # 無斜線  │
│  path('dify/saf/endpoints/', dify_saf_list_endpoints)  # 端點列表│
│  path('dify/saf/health/', dify_saf_health_check)       # 健康檢查│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 4.5 View 函數設計

```python
# backend/api/views/dify_saf_views.py

@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def dify_saf_search(request):
    """
    SAF 外部知識庫搜尋 API - 獨立入口
    
    這是 SAF 專屬的 Dify 外部知識庫 API，
    透過 endpoint 參數路由到不同的 SAF API。
    
    請求格式：
        POST /api/dify/saf/retrieval/
        {
            "knowledge_id": "saf_db",
            "query": "WD SM2264",
            "retrieval_setting": {
                "top_k": 5,
                "score_threshold": 0.3
            },
            "endpoint": "projects"  # projects | summary
        }
    """
    try:
        from library.saf_integration import SAFKnowledgeHandler
        
        handler = SAFKnowledgeHandler()
        return handler.handle_request(request)
        
    except Exception as e:
        logger.error(f"SAF 知識庫搜尋失敗: {str(e)}")
        return Response(
            {"records": [], "error": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([])
def dify_saf_list_endpoints(request):
    """
    列出所有可用的 SAF API endpoint 定義
    
    返回格式：
        {
            "endpoints": {
                "projects": {"description": "...", "enabled": true},
                "summary": {"description": "...", "enabled": true}
            }
        }
    """
    from library.saf_integration import get_available_endpoints
    
    return Response({
        "endpoints": get_available_endpoints()
    })


@api_view(['GET'])
@permission_classes([])
def dify_saf_health_check(request):
    """
    檢查 SAF API Server 連線狀態
    
    返回格式：
        {
            "status": "healthy",
            "saf_server": "http://10.252.170.171:8080",
            "latency_ms": 50
        }
    """
    from library.saf_integration import check_saf_health
    
    return Response(check_saf_health())
```

### 4.6 Dify Studio 配置

在 Dify Studio 中配置 SAF 外部知識庫：

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dify Studio 設定                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  外部知識 API 配置：                                             │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ API Endpoint: http://your-server/api/dify/saf/retrieval/  │  │
│  │ API Key: (可選)                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  知識庫設定：                                                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Knowledge ID: saf_db                                      │  │
│  │ Top K: 5                                                  │  │
│  │ Score Threshold: 0.3                                      │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  💡 提示：在 Dify 工作流中可以動態設定 endpoint 參數             │
│     - "projects" → 搜尋專案                                     │
│     - "summary" → 取得統計                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 5. 後端 API 定義架構

### 5.1 外部 API 配置模型

建立可配置的 API 定義機制，支援從資料庫或配置檔讀取：

```python
# library/external_api/registry.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum


class AuthMethod(Enum):
    """認證方式"""
    NONE = "none"
    HEADER = "header"
    BASIC = "basic"
    BEARER = "bearer"
    API_KEY = "api_key"


@dataclass
class EndpointConfig:
    """API 端點配置"""
    path: str                          # 端點路徑
    method: str = "GET"                # HTTP 方法
    params: Dict[str, Any] = field(default_factory=dict)  # 預設參數
    headers: Dict[str, str] = field(default_factory=dict) # 額外 headers
    response_mapping: Dict[str, str] = field(default_factory=dict)  # 回應欄位映射
    

@dataclass  
class ExternalAPIConfig:
    """外部 API 配置"""
    name: str                          # API 名稱
    base_url: str                      # 基礎 URL
    auth_method: AuthMethod            # 認證方式
    auth_config: Dict[str, Any] = field(default_factory=dict)  # 認證配置
    endpoints: Dict[str, EndpointConfig] = field(default_factory=dict)  # 端點配置
    timeout: int = 30                  # 超時時間（秒）
    cache_ttl: int = 300               # 快取時間（秒）
    retry_count: int = 3               # 重試次數
    enabled: bool = True               # 是否啟用


class ExternalAPIRegistry:
    """外部 API 註冊表"""
    
    _instance = None
    _configs: Dict[str, ExternalAPIConfig] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_default_configs()
        return cls._instance
    
    def _load_default_configs(self):
        """載入預設配置"""
        # SAF API 配置
        self.register(ExternalAPIConfig(
            name="saf",
            base_url="http://10.252.170.171:8080",
            auth_method=AuthMethod.HEADER,
            auth_config={
                "user_id_header": "Authorization",
                "user_name_header": "Authorization-Name",
                "default_user_id": "150",
                "default_user_name": "Chunwei.Huang"
            },
            endpoints={
                "projects": EndpointConfig(
                    path="/api/v1/projects",
                    method="GET",
                    params={"page": 1, "size": 100},
                    response_mapping={
                        "items": "data.items",
                        "total": "data.total"
                    }
                ),
                "summary": EndpointConfig(
                    path="/api/v1/projects/summary",
                    method="GET",
                    response_mapping={
                        "total": "data.total",
                        "by_customer": "data.by_customer",
                        "by_controller": "data.by_controller"
                    }
                ),
                "health": EndpointConfig(
                    path="/health",
                    method="GET"
                )
            },
            timeout=30,
            cache_ttl=300  # 5 分鐘快取
        ))
    
    def register(self, config: ExternalAPIConfig):
        """註冊外部 API 配置"""
        self._configs[config.name] = config
    
    def get(self, name: str) -> Optional[ExternalAPIConfig]:
        """獲取 API 配置"""
        return self._configs.get(name)
    
    def list_all(self) -> List[str]:
        """列出所有已註冊的 API"""
        return list(self._configs.keys())
```

### 5.2 Django Model 定義（可選）

如果需要從資料庫管理 API 配置：

```python
# backend/api/models.py

class ExternalAPISource(models.Model):
    """外部 API 來源定義"""
    
    class AuthMethod(models.TextChoices):
        NONE = 'none', '無認證'
        HEADER = 'header', 'Header 認證'
        BASIC = 'basic', 'Basic Auth'
        BEARER = 'bearer', 'Bearer Token'
        API_KEY = 'api_key', 'API Key'
    
    name = models.CharField(max_length=100, unique=True, verbose_name="API 名稱")
    display_name = models.CharField(max_length=200, verbose_name="顯示名稱")
    base_url = models.URLField(verbose_name="基礎 URL")
    auth_method = models.CharField(
        max_length=20, 
        choices=AuthMethod.choices, 
        default=AuthMethod.NONE,
        verbose_name="認證方式"
    )
    auth_config = models.JSONField(default=dict, verbose_name="認證配置")
    timeout = models.IntegerField(default=30, verbose_name="超時時間(秒)")
    cache_ttl = models.IntegerField(default=300, verbose_name="快取時間(秒)")
    is_enabled = models.BooleanField(default=True, verbose_name="是否啟用")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'external_api_source'
        verbose_name = "外部 API 來源"
        verbose_name_plural = "外部 API 來源"


class ExternalAPIEndpoint(models.Model):
    """外部 API 端點定義"""
    
    class HttpMethod(models.TextChoices):
        GET = 'GET', 'GET'
        POST = 'POST', 'POST'
        PUT = 'PUT', 'PUT'
        DELETE = 'DELETE', 'DELETE'
    
    api_source = models.ForeignKey(
        ExternalAPISource, 
        on_delete=models.CASCADE,
        related_name='endpoints',
        verbose_name="API 來源"
    )
    name = models.CharField(max_length=100, verbose_name="端點名稱")
    path = models.CharField(max_length=500, verbose_name="端點路徑")
    method = models.CharField(
        max_length=10,
        choices=HttpMethod.choices,
        default=HttpMethod.GET,
        verbose_name="HTTP 方法"
    )
    default_params = models.JSONField(default=dict, verbose_name="預設參數")
    response_mapping = models.JSONField(default=dict, verbose_name="回應映射")
    description = models.TextField(blank=True, verbose_name="說明")
    
    class Meta:
        db_table = 'external_api_endpoint'
        unique_together = ['api_source', 'name']
        verbose_name = "外部 API 端點"
        verbose_name_plural = "外部 API 端點"
```

---

## 6. 資料轉換層設計

### 6.1 Dify 知識庫回應格式

Dify 外部知識庫 API 要求的回應格式：

```json
{
    "records": [
        {
            "content": "文檔內容...",
            "score": 0.85,
            "title": "文檔標題",
            "metadata": {
                "source": "saf_projects",
                "project_id": "xxx",
                ...
            }
        }
    ]
}
```

### 6.2 SAF 資料轉換器

```python
# library/saf_integration/data_transformer.py

from typing import List, Dict, Any
import re


class SAFDataTransformer:
    """SAF 資料轉換器"""
    
    @staticmethod
    def project_to_dify_record(project: Dict[str, Any], score: float = 1.0) -> Dict[str, Any]:
        """
        將 SAF 專案資料轉換為 Dify 知識庫記錄格式
        
        Args:
            project: SAF 專案資料
            score: 相關性分數 (0.0 ~ 1.0)
            
        Returns:
            Dify 知識庫記錄格式
        """
        # 組合專案描述內容
        content_parts = []
        
        # 專案基本資訊
        content_parts.append(f"專案名稱: {project.get('projectName', 'N/A')}")
        content_parts.append(f"客戶: {project.get('customer', 'N/A')}")
        content_parts.append(f"控制器: {project.get('controller', 'N/A')}")
        
        # 產品資訊
        if project.get('productCategory'):
            content_parts.append(f"產品類別: {project['productCategory']}")
        if project.get('nand'):
            content_parts.append(f"NAND: {project['nand']}")
        if project.get('fw'):
            content_parts.append(f"韌體版本: {project['fw']}")
        if project.get('subVersion'):
            content_parts.append(f"子版本: {project['subVersion']}")
        
        # 負責人和任務資訊
        if project.get('pl'):
            content_parts.append(f"負責人: {project['pl']}")
        if project.get('taskId'):
            content_parts.append(f"任務 ID: {project['taskId']}")
        
        # 組合完整內容
        content = "\n".join(content_parts)
        
        # 建立標題
        title = f"{project.get('projectName', 'Unknown')} - {project.get('customer', 'Unknown')}"
        
        return {
            "content": content,
            "score": score,
            "title": title,
            "metadata": {
                "source": "saf_projects",
                "project_uid": project.get('projectUid', ''),
                "project_id": project.get('projectId', ''),
                "project_name": project.get('projectName', ''),
                "customer": project.get('customer', ''),
                "controller": project.get('controller', ''),
                "product_category": project.get('productCategory', ''),
                "task_id": project.get('taskId', ''),
                "created_by": project.get('createdBy', '')
            }
        }
    
    @staticmethod
    def calculate_relevance_score(project: Dict[str, Any], query: str) -> float:
        """
        計算專案與查詢的相關性分數
        
        Args:
            project: 專案資料
            query: 搜尋查詢
            
        Returns:
            相關性分數 (0.0 ~ 1.0)
        """
        if not query:
            return 0.5
        
        query_lower = query.lower()
        score = 0.0
        
        # 定義搜尋欄位和權重
        search_fields = {
            'projectName': 0.30,
            'customer': 0.25,
            'controller': 0.20,
            'nand': 0.10,
            'fw': 0.10,
            'productCategory': 0.05
        }
        
        for field, weight in search_fields.items():
            field_value = str(project.get(field, '')).lower()
            
            # 完全匹配
            if query_lower == field_value:
                score += weight * 1.0
            # 部分匹配
            elif query_lower in field_value or field_value in query_lower:
                score += weight * 0.7
            # 單詞匹配
            else:
                query_words = re.findall(r'\w+', query_lower)
                field_words = re.findall(r'\w+', field_value)
                matching_words = len(set(query_words) & set(field_words))
                if matching_words > 0:
                    score += weight * (matching_words / max(len(query_words), 1)) * 0.5
        
        return min(score, 1.0)
    
    @staticmethod
    def summary_to_dify_record(summary: Dict[str, Any]) -> Dict[str, Any]:
        """
        將 SAF 專案統計轉換為 Dify 知識庫記錄格式
        
        Args:
            summary: SAF 統計資料
            
        Returns:
            Dify 知識庫記錄格式
        """
        content_parts = []
        
        # 總數統計
        content_parts.append(f"專案總數: {summary.get('total', 0)}")
        
        # 客戶分佈
        by_customer = summary.get('by_customer', {})
        if by_customer:
            content_parts.append("\n客戶分佈:")
            for customer, count in sorted(by_customer.items(), key=lambda x: -x[1])[:10]:
                content_parts.append(f"  - {customer}: {count} 個專案")
        
        # 控制器分佈
        by_controller = summary.get('by_controller', {})
        if by_controller:
            content_parts.append("\n控制器分佈:")
            for controller, count in sorted(by_controller.items(), key=lambda x: -x[1])[:10]:
                content_parts.append(f"  - {controller}: {count} 個專案")
        
        return {
            "content": "\n".join(content_parts),
            "score": 1.0,
            "title": "SAF 專案統計摘要",
            "metadata": {
                "source": "saf_summary",
                "total_projects": summary.get('total', 0),
                "customer_count": len(by_customer),
                "controller_count": len(by_controller)
            }
        }
    
    # 🆕 新增：專案名稱清單轉換器
    @staticmethod
    def project_names_to_dify_record(
        projects: List[Dict[str, Any]], 
        query: str = "",
        group_by: str = None
    ) -> Dict[str, Any]:
        """
        將 SAF 專案列表轉換為專案名稱清單格式
        
        Args:
            projects: SAF 專案列表
            query: 搜尋查詢（用於過濾）
            group_by: 分組方式（customer, controller, None）
            
        Returns:
            Dify 知識庫記錄格式（專案名稱清單）
        """
        # 提取所有專案名稱（去重）
        project_names = set()
        project_info = []  # 儲存更多資訊以供過濾
        
        for project in projects:
            name = project.get('projectName', '')
            if name:
                project_names.add(name)
                project_info.append({
                    'name': name,
                    'customer': project.get('customer', ''),
                    'controller': project.get('controller', '')
                })
        
        # 如果有查詢，進行過濾
        if query:
            query_lower = query.lower()
            filtered_info = [
                p for p in project_info 
                if query_lower in p['name'].lower() 
                or query_lower in p['customer'].lower()
                or query_lower in p['controller'].lower()
            ]
        else:
            filtered_info = project_info
        
        # 根據 group_by 組織內容
        if group_by == 'customer':
            content = SAFDataTransformer._group_by_field(filtered_info, 'customer')
        elif group_by == 'controller':
            content = SAFDataTransformer._group_by_field(filtered_info, 'controller')
        else:
            # 預設：按名稱排序的清單
            unique_names = sorted(set(p['name'] for p in filtered_info))
            content = f"專案名稱清單（共 {len(unique_names)} 個）：\n\n"
            content += "\n".join(f"- {name}" for name in unique_names)
        
        return {
            "content": content,
            "score": 1.0,
            "title": f"SAF 專案名稱清單" + (f" ({query})" if query else ""),
            "metadata": {
                "source": "saf_project_names",
                "total_unique_names": len(set(p['name'] for p in filtered_info)),
                "query": query,
                "group_by": group_by
            }
        }
    
    @staticmethod
    def _group_by_field(project_info: List[Dict], field: str) -> str:
        """按指定欄位分組"""
        from collections import defaultdict
        
        groups = defaultdict(set)
        for p in project_info:
            groups[p.get(field, 'Unknown')].add(p['name'])
        
        content_parts = [f"專案名稱清單（按 {field} 分組）：\n"]
        
        for group_name in sorted(groups.keys()):
            names = sorted(groups[group_name])
            content_parts.append(f"\n【{group_name}】（{len(names)} 個專案）")
            for name in names:
                content_parts.append(f"  - {name}")
        
        return "\n".join(content_parts)
```

### 6.3 搜尋服務實作

```python
# library/saf_integration/search_service.py

import logging
from typing import List, Dict, Any, Optional
from .api_client import SAFAPIClient
from .data_transformer import SAFDataTransformer


logger = logging.getLogger(__name__)


class SAFProjectSearchService:
    """SAF 專案搜尋服務"""
    
    def __init__(self):
        self.client = SAFAPIClient()
        self.transformer = SAFDataTransformer()
    
    def search_knowledge(
        self, 
        query: str, 
        limit: int = 5, 
        threshold: float = 0.3,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        搜尋 SAF 專案知識庫
        
        Args:
            query: 搜尋查詢
            limit: 返回結果數量限制
            threshold: 分數閾值
            
        Returns:
            Dify 格式的搜尋結果列表
        """
        try:
            logger.info(f"🔍 SAF 專案搜尋: query='{query}', limit={limit}, threshold={threshold}")
            
            # 從 SAF API 獲取專案列表
            projects = self.client.get_projects(page=1, size=200)
            
            if not projects:
                logger.warning("SAF API 未返回任何專案")
                return []
            
            # 計算相關性分數並轉換格式
            results = []
            for project in projects:
                score = self.transformer.calculate_relevance_score(project, query)
                
                if score >= threshold:
                    record = self.transformer.project_to_dify_record(project, score)
                    results.append(record)
            
            # 按分數排序並限制數量
            results.sort(key=lambda x: -x['score'])
            results = results[:limit]
            
            logger.info(f"✅ SAF 專案搜尋完成: 找到 {len(results)} 筆結果")
            return results
            
        except Exception as e:
            logger.error(f"❌ SAF 專案搜尋失敗: {str(e)}")
            return []


class SAFSummarySearchService:
    """SAF 專案統計搜尋服務"""
    
    def __init__(self):
        self.client = SAFAPIClient()
        self.transformer = SAFDataTransformer()
    
    def search_knowledge(
        self, 
        query: str, 
        limit: int = 1, 
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        獲取 SAF 專案統計資訊
        
        Args:
            query: 搜尋查詢（用於此服務時通常忽略）
            limit: 返回結果數量限制
            
        Returns:
            Dify 格式的統計結果
        """
        try:
            logger.info(f"📊 SAF 統計查詢: query='{query}'")
            
            # 獲取統計資料
            summary = self.client.get_summary()
            
            if not summary:
                logger.warning("SAF API 未返回統計資料")
                return []
            
            # 轉換為 Dify 格式
            record = self.transformer.summary_to_dify_record(summary)
            
            logger.info(f"✅ SAF 統計查詢完成")
            return [record]
            
        except Exception as e:
            logger.error(f"❌ SAF 統計查詢失敗: {str(e)}")
            return []


# 🆕 新增：專案名稱清單搜尋服務
class SAFProjectNamesSearchService:
    """SAF 專案名稱清單搜尋服務"""
    
    def __init__(self):
        self.client = SAFAPIClient()
        self.transformer = SAFDataTransformer()
        self._cache = None
        self._cache_time = None
        self._cache_ttl = 300  # 5 分鐘快取
    
    def search_knowledge(
        self, 
        query: str = "", 
        limit: int = 1,
        group_by: str = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        獲取 SAF 專案名稱清單
        
        Args:
            query: 搜尋查詢（用於過濾專案名稱）
            limit: 返回結果數量限制
            group_by: 分組方式（customer, controller, None）
            
        Returns:
            Dify 格式的專案名稱清單
        """
        try:
            logger.info(f"📋 SAF 專案名稱查詢: query='{query}', group_by={group_by}")
            
            # 獲取專案列表（使用快取）
            projects = self._get_projects_cached()
            
            if not projects:
                logger.warning("SAF API 未返回任何專案")
                return []
            
            # 轉換為專案名稱清單格式
            record = self.transformer.project_names_to_dify_record(
                projects=projects,
                query=query,
                group_by=group_by
            )
            
            logger.info(f"✅ SAF 專案名稱查詢完成: 共 {record['metadata']['total_unique_names']} 個專案")
            return [record]
            
        except Exception as e:
            logger.error(f"❌ SAF 專案名稱查詢失敗: {str(e)}")
            return []
    
    def _get_projects_cached(self) -> List[Dict[str, Any]]:
        """獲取專案列表（帶快取）"""
        import time
        
        current_time = time.time()
        
        # 檢查快取是否有效
        if (self._cache is not None and 
            self._cache_time is not None and 
            current_time - self._cache_time < self._cache_ttl):
            logger.debug("使用快取的專案列表")
            return self._cache
        
        # 從 API 獲取新資料
        logger.debug("從 SAF API 獲取專案列表")
        projects = self.client.get_projects(page=1, size=1000)
        
        # 更新快取
        self._cache = projects
        self._cache_time = current_time
        
        return projects
    
    def get_all_project_names(self) -> List[str]:
        """
        獲取所有專案名稱（簡化版，只返回名稱列表）
        
        Returns:
            專案名稱列表（去重、排序）
        """
        projects = self._get_projects_cached()
        names = set()
        
        for project in projects:
            name = project.get('projectName', '')
            if name:
                names.add(name)
        
        return sorted(names)
    
    def get_project_names_by_customer(self) -> Dict[str, List[str]]:
        """
        按客戶分組獲取專案名稱
        
        Returns:
            {客戶名稱: [專案名稱列表]}
        """
        from collections import defaultdict
        
        projects = self._get_projects_cached()
        result = defaultdict(set)
        
        for project in projects:
            name = project.get('projectName', '')
            customer = project.get('customer', 'Unknown')
            if name:
                result[customer].add(name)
        
        return {k: sorted(v) for k, v in result.items()}
```

---

## 7. 實作計畫

### 7.1 分階段開發總覽

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SAF 整合實作分階段計畫                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: 基礎架構 (1.5 天)                                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 1.1 模組結構 → 1.2 API Client → 1.3 認證管理 → 1.4 快取機制    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 2: 核心功能 - projects + summary (1 天)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 2.1 資料轉換器 → 2.2 搜尋服務 (projects/summary) → 2.3 Handler │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  Phase 3: API 入口 + 基本測試 (0.5 天)                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 3.1 Views → 3.2 URL 路由 → 3.3 端點列表/健康檢查 → 3.4 基本測試│   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  🎉 里程碑 A: 基本功能完成 (可用 projects + summary)                   │
│                              │                                          │
│                              ▼                                          │
│  Phase 4: 🆕 project_names 功能 (0.5 天)                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 4.1 名稱轉換器 → 4.2 名稱搜尋服務 → 4.3 Handler 整合 → 4.4 測試│   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  🎉 里程碑 B: 三個 endpoint 全部完成                                   │
│                              │                                          │
│                              ▼                                          │
│  Phase 5: Dify Studio 配置 + 完整測試 (0.5 天)                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 5.1 Dify 知識庫設定 → 5.2 整合測試 → 5.3 文檔完善               │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  🎉 里程碑 C: 正式上線                                                 │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### 7.2 Phase 1: 基礎架構 (預估 1.5 天)

**目標**：建立 SAF 整合模組的基礎架構，包含 API 客戶端和認證機制。

| 步驟 | 任務 | 預估時間 | 產出檔案 | 依賴 |
|------|------|----------|----------|------|
| 1.1 | 建立模組結構 | 0.5h | `library/saf_integration/__init__.py` | - |
| 1.2 | 實作 Endpoint Registry | 1h | `library/saf_integration/endpoint_registry.py` | 1.1 |
| 1.3 | 實作 SAF API Client | 2h | `library/saf_integration/api_client.py` | 1.1, 1.2 |
| 1.4 | 實作認證管理 | 1.5h | `library/saf_integration/auth_manager.py` | 1.3 |
| 1.5 | 實作快取機制 | 1.5h | `library/saf_integration/cache_manager.py` | 1.3 |
| 1.6 | 基礎單元測試 | 1.5h | `tests/test_saf_integration/test_api_client.py` | 1.3-1.5 |

**Phase 1 驗收標準**：
```bash
# 可以成功連接 SAF API 並取得資料
docker exec ai-django python -c "
from library.saf_integration.api_client import SAFAPIClient
client = SAFAPIClient()
print(client.health_check())
print(len(client.get_projects()))
"
```

### 7.3 Phase 2: 核心功能 - projects + summary (預估 1 天)

**目標**：實作資料轉換和搜尋服務，支援 `projects` 和 `summary` 兩個 endpoint。

| 步驟 | 任務 | 預估時間 | 產出檔案 | 依賴 |
|------|------|----------|----------|------|
| 2.1 | 實作 project 資料轉換器 | 1.5h | `library/saf_integration/data_transformer.py` | Phase 1 |
| 2.2 | 實作 summary 資料轉換器 | 1h | (同上) | 2.1 |
| 2.3 | 實作 SAFProjectSearchService | 1.5h | `library/saf_integration/search_service.py` | 2.1 |
| 2.4 | 實作 SAFSummarySearchService | 1h | (同上) | 2.2 |
| 2.5 | 實作 SAFKnowledgeHandler | 1.5h | `library/saf_integration/handler.py` | 2.3, 2.4 |
| 2.6 | 搜尋服務單元測試 | 1.5h | `tests/test_saf_integration/test_search_service.py` | 2.3-2.5 |

**Phase 2 驗收標準**：
```bash
# 可以執行搜尋並得到 Dify 格式的結果
docker exec ai-django python -c "
from library.saf_integration.search_service import SAFProjectSearchService
service = SAFProjectSearchService()
results = service.search_knowledge('WD', limit=3)
print(f'找到 {len(results)} 筆結果')
for r in results:
    print(f'  - {r[\"title\"]}: {r[\"score\"]:.2f}')
"
```

### 7.4 Phase 3: API 入口 + 基本測試 (預估 0.5 天)

**目標**：建立獨立的 Dify SAF API 入口，可透過 HTTP 存取。

| 步驟 | 任務 | 預估時間 | 產出/修改檔案 | 依賴 |
|------|------|----------|---------------|------|
| 3.1 | 建立 Views | 1.5h | `backend/api/views/dify_saf_views.py` | Phase 2 |
| 3.2 | 新增 URL 路由 | 0.5h | `backend/api/urls.py` (修改) | 3.1 |
| 3.3 | 導出 Views | 0.5h | `backend/api/views/__init__.py` (修改) | 3.1 |
| 3.4 | API 基本測試 | 1.5h | curl 測試 + 日誌檢查 | 3.2 |

**Phase 3 驗收標準**：
```bash
# HTTP API 可正常存取
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "saf_projects",
    "query": "WD",
    "retrieval_setting": {"top_k": 3, "score_threshold": 0.3}
  }'

# 健康檢查
curl "http://localhost/api/dify/saf/health/"

# 端點列表
curl "http://localhost/api/dify/saf/endpoints/"
```

---

### 🎉 里程碑 A：基本功能完成

**達成條件**：
- ✅ `projects` endpoint 可用（專案搜尋）
- ✅ `summary` endpoint 可用（統計資訊）
- ✅ HTTP API 可正常存取
- ✅ 基本測試通過

**可交付項目**：
- 可以開始在 Dify Studio 中配置外部知識 API
- 可以進行初步的功能驗證

---

### 7.5 Phase 4: 🆕 project_names 功能 (預估 0.5 天)

**目標**：新增 `project_names` endpoint，支援取得專案名稱清單。

| 步驟 | 任務 | 預估時間 | 產出/修改檔案 | 依賴 |
|------|------|----------|---------------|------|
| 4.1 | 實作名稱清單轉換器 | 1h | `data_transformer.py` (新增方法) | Phase 3 |
| 4.2 | 實作 SAFProjectNamesSearchService | 1h | `search_service.py` (新增類別) | 4.1 |
| 4.3 | 更新 Handler 支援 project_names | 0.5h | `handler.py` (修改) | 4.2 |
| 4.4 | 更新 Endpoint Registry | 0.5h | `endpoint_registry.py` (修改) | 4.1 |
| 4.5 | project_names 單元測試 | 1h | `test_search_service.py` (新增) | 4.2, 4.3 |

**Phase 4 驗收標準**：
```bash
# project_names endpoint 可正常存取
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "saf_project_names",
    "query": "",
    "retrieval_setting": {"top_k": 1, "score_threshold": 0}
  }'

# 應返回專案名稱清單
```

---

### 🎉 里程碑 B：三個 endpoint 全部完成

**達成條件**：
- ✅ `projects` endpoint 可用
- ✅ `summary` endpoint 可用
- ✅ `project_names` endpoint 可用（🆕）
- ✅ 所有單元測試通過

---

### 7.6 Phase 5: Dify Studio 配置 + 完整測試 (預估 0.5 天)

**目標**：在 Dify Studio 中完成配置，進行端到端整合測試。

| 步驟 | 任務 | 預估時間 | 說明 | 依賴 |
|------|------|----------|------|------|
| 5.1 | 新增外部知識 API | 0.5h | 在 Dify 設定 API 端點 | Phase 4 |
| 5.2 | 建立 saf_projects 知識庫 | 0.5h | 配置描述和參數 | 5.1 |
| 5.3 | 建立 saf_summary 知識庫 | 0.5h | 配置描述和參數 | 5.1 |
| 5.4 | 建立 saf_project_names 知識庫 | 0.5h | 配置描述和參數 | 5.1 |
| 5.5 | 端到端測試 | 1h | 在 Dify App 中測試問答 | 5.2-5.4 |
| 5.6 | 文檔完善 | 1h | 更新設計文檔，加入實作細節 | 5.5 |

**Phase 5 驗收標準**：
```
在 Dify App 中測試以下問題，確認 AI 自動選擇正確的知識庫：

1. 「WD 有哪些專案？」 → 應使用 saf_projects
2. 「目前有多少專案？」 → 應使用 saf_summary
3. 「列出所有專案名稱」 → 應使用 saf_project_names
4. 「SM2264 的專案有哪些？」 → 應使用 saf_projects
5. 「各客戶的專案分佈？」 → 應使用 saf_summary
```

---

### 🎉 里程碑 C：正式上線

**達成條件**：
- ✅ 所有 endpoint 功能正常
- ✅ Dify Studio 配置完成
- ✅ 端到端測試通過
- ✅ 文檔完善

---

### 7.7 開發時程總覽

| Phase | 任務 | 預估時間 | 累計時間 | 里程碑 |
|-------|------|----------|----------|--------|
| Phase 1 | 基礎架構 | 1.5 天 | 1.5 天 | - |
| Phase 2 | 核心功能 (projects + summary) | 1 天 | 2.5 天 | - |
| Phase 3 | API 入口 + 基本測試 | 0.5 天 | 3 天 | 🎉 里程碑 A |
| Phase 4 | project_names 功能 | 0.5 天 | 3.5 天 | 🎉 里程碑 B |
| Phase 5 | Dify 配置 + 完整測試 | 0.5 天 | 4 天 | 🎉 里程碑 C |

**總計：約 4 天**

### 7.8 風險與應對

| 風險 | 可能性 | 影響 | 應對措施 |
|------|--------|------|----------|
| SAF API 不穩定 | 中 | 高 | 實作重試機制和快取 |
| SAF API 回應格式變更 | 低 | 中 | 使用彈性的資料映射設計 |
| 網路延遲過高 | 中 | 中 | 實作快取，設定合理超時 |
| Dify 外部知識 API 限制 | 低 | 中 | 預先測試 Dify API 相容性 |

### 7.9 檔案清單

#### 需要新增的檔案

```
# SAF 整合模組（Phase 1-2）
library/saf_integration/
├── __init__.py                 # 模組入口，導出主要類別
├── endpoint_registry.py        # Endpoint 定義註冊表
├── api_client.py               # SAF API 客戶端
├── auth_manager.py             # 認證管理
├── cache_manager.py            # 快取管理
├── data_transformer.py         # 資料轉換器（Phase 2 + Phase 4 擴充）
├── search_service.py           # 搜尋服務（Phase 2 + Phase 4 擴充）
└── handler.py                  # SAFKnowledgeHandler

# 獨立入口 Views（Phase 3）
backend/api/views/dify_saf_views.py

# 測試檔案（各 Phase 持續新增）
tests/test_saf_integration/
├── __init__.py
├── test_api_client.py          # Phase 1
├── test_data_transformer.py    # Phase 2
├── test_search_service.py      # Phase 2 + Phase 4
└── test_handler.py             # Phase 3
```

#### 需要修改的檔案

```
# Phase 3：URL 路由
backend/api/urls.py                     # 新增 SAF API 路由

# Phase 3：Views 導出
backend/api/views/__init__.py           # 導出 dify_saf_views
```

#### 不需要修改的檔案（與現有架構隔離）

```
# ✅ 現有 Dify 知識庫不受影響
library/dify_knowledge/__init__.py      # 不需修改
backend/api/views/dify_knowledge_views.py  # 不需修改
```

---

### 7.10 快速開始指令

**Phase 1 完成後可執行**：
```bash
# 測試 SAF API 連接
docker exec ai-django python -c "
from library.saf_integration.api_client import SAFAPIClient
client = SAFAPIClient()
health = client.health_check()
print(f'SAF API 狀態: {health}')
projects = client.get_projects(page=1, size=5)
print(f'取得 {len(projects)} 個專案')
"
```

**Phase 3 完成後可執行**：
```bash
# 測試 HTTP API
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "saf_projects", "query": "WD", "retrieval_setting": {"top_k": 3}}'
```

**Phase 4 完成後可執行**：
```bash
# 測試專案名稱清單
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{"knowledge_id": "saf_project_names", "query": "", "retrieval_setting": {"top_k": 1}}'
```

---

## 8. 測試策略

### 8.1 單元測試

```python
# tests/test_saf_integration/test_api_client.py

import pytest
from unittest.mock import patch, MagicMock
from library.saf_integration.api_client import SAFAPIClient


class TestSAFAPIClient:
    """SAF API 客戶端測試"""
    
    def test_health_check(self):
        """測試健康檢查"""
        client = SAFAPIClient()
        result = client.health_check()
        assert result.get('status') == 'healthy'
    
    @patch('requests.get')
    def test_get_projects(self, mock_get):
        """測試獲取專案列表"""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'success': True,
            'data': {
                'items': [{'projectName': 'Test'}],
                'total': 1
            }
        }
        mock_get.return_value = mock_response
        
        client = SAFAPIClient()
        projects = client.get_projects()
        
        assert len(projects) == 1
        assert projects[0]['projectName'] == 'Test'
```

### 8.2 整合測試

```python
# tests/test_saf_integration/test_search_service.py

import pytest
from library.saf_integration.search_service import SAFProjectSearchService


class TestSAFProjectSearchService:
    """SAF 專案搜尋服務測試"""
    
    @pytest.mark.integration
    def test_search_by_customer(self):
        """測試按客戶名稱搜尋"""
        service = SAFProjectSearchService()
        results = service.search_knowledge(
            query="WD",
            limit=5,
            threshold=0.3
        )
        
        assert isinstance(results, list)
        for result in results:
            assert 'content' in result
            assert 'score' in result
            assert 'title' in result
            assert 'metadata' in result
```

### 8.3 API 測試

```bash
# 🆕 測試 SAF 知識庫搜尋（獨立入口）
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "saf_db",
    "query": "WD SM2264",
    "retrieval_setting": {
      "top_k": 5,
      "score_threshold": 0.3
    },
    "endpoint": "projects"
  }'

# 測試統計端點
curl -X POST "http://localhost/api/dify/saf/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "saf_db",
    "query": "",
    "retrieval_setting": {
      "top_k": 1,
      "score_threshold": 0
    },
    "endpoint": "summary"
  }'

# 列出可用端點
curl -X GET "http://localhost/api/dify/saf/endpoints/"

# 健康檢查
curl -X GET "http://localhost/api/dify/saf/health/"
```

---

## 9. 安全考量

### 9.1 認證資訊管理

**推薦方式**：
1. 將 SAF 認證資訊存放在環境變數中
2. 不要在程式碼中硬編碼認證資訊
3. 使用 Django settings 管理敏感配置

```python
# backend/ai_platform/settings.py

# SAF API 配置
SAF_API_CONFIG = {
    'BASE_URL': os.environ.get('SAF_API_BASE_URL', 'http://10.252.170.171:8080'),
    'USER_ID': os.environ.get('SAF_API_USER_ID', '150'),
    'USER_NAME': os.environ.get('SAF_API_USER_NAME', 'Chunwei.Huang'),
    'TIMEOUT': int(os.environ.get('SAF_API_TIMEOUT', '30')),
    'CACHE_TTL': int(os.environ.get('SAF_API_CACHE_TTL', '300')),
}
```

### 9.2 網路安全

- SAF API Server 位於內網 (`10.252.170.171`)
- 建議透過 VPN 或內網環境存取
- 考慮使用 HTTPS（如果 SAF Server 支援）

### 9.3 錯誤處理

- 實作超時處理
- 實作重試機制
- 實作降級方案（當 SAF API 不可用時）

---

## 附錄 A：Dify Studio 配置

### A.1 新增外部知識 API

在 Dify Studio 中新增 SAF 外部知識 API（只需設定一次）：

```
API Endpoint: http://your-django-server/api/dify/saf/retrieval/
API Key: (可選)
```

### A.2 多知識庫配置（推薦方式）

透過配置**多個知識庫**並設定適當的**描述/前後文**，讓 Dify 自動根據用戶問題選擇正確的 API endpoint。

#### 🎯 核心概念

```
┌─────────────────────────────────────────────────────────────────┐
│                    Dify Studio 知識庫配置                        │
│                                                                  │
│  📚 知識庫 1：SAF 專案搜尋 (saf_projects)                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 描述：「搜尋 SAF 專案資料，包含專案名稱、客戶、控制器...」 │  │
│  │        → 當用戶問專案相關問題時，Dify 會選擇此知識庫       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  📊 知識庫 2：SAF 專案統計 (saf_summary)                        │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ 描述：「查詢 SAF 專案統計資訊，包含總數、分佈情況...」     │  │
│  │        → 當用戶問統計相關問題時，Dify 會選擇此知識庫       │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  💡 Dify 會根據用戶問題 + 知識庫描述，自動選擇最相關的知識庫！ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### 📚 知識庫 1：SAF 專案搜尋

| 設定項目 | 值 |
|---------|-----|
| **名稱** | SAF 專案搜尋 |
| **Knowledge ID** | `saf_projects` |
| **Top K** | 5-10 |
| **Score Threshold** | 0.3 |

**描述/前後文內容**（複製以下內容到 Dify 知識庫描述欄位）：

```
用於搜尋 SAF 專案資料，包含專案名稱、客戶、控制器、NAND 類型等詳細資訊。

當用戶詢問以下類型的問題時，應該使用此知識庫：
- 查詢特定客戶的專案（例如：WD、Samsung、Micron、SK Hynix、Intel、Kioxia）
- 查詢特定控制器的專案（例如：SM2264、SM2267、SM2269）
- 查詢特定 NAND 類型的專案（例如：BiCS5、TLC、QLC）
- 根據專案名稱搜尋
- 查詢專案負責人
- 查詢特定韌體版本的專案
- 列出符合條件的專案清單

範例問題：
- 「WD 有哪些專案？」
- 「SM2264 控制器的專案有哪些？」
- 「BiCS5 NAND 的專案列表」
- 「找一下 DEMETER 專案」
- 「bruce.zhang 負責的專案」
```

#### 📊 知識庫 2：SAF 專案統計

| 設定項目 | 值 |
|---------|-----|
| **名稱** | SAF 專案統計 |
| **Knowledge ID** | `saf_summary` |
| **Top K** | 1-3 |
| **Score Threshold** | 0.3 |

**描述/前後文內容**（複製以下內容到 Dify 知識庫描述欄位）：

```
用於查詢 SAF 專案的統計資訊和總覽數據。

當用戶詢問以下類型的問題時，應該使用此知識庫：
- 專案總數量
- 各客戶的專案數量分佈
- 各控制器型號的專案統計
- 整體概況、總覽、摘要
- 數量相關的統計問題

範例問題：
- 「目前有多少專案？」
- 「專案總數是多少？」
- 「各客戶的專案分佈情況？」
- 「哪個客戶的專案最多？」
- 「SM2264 和 SM2267 各有多少專案？」
- 「給我一個專案總覽」
```

#### 🔄 自動選擇流程

```
用戶問題：「WD 有哪些專案？」
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Dify AI 引擎                                  │
│                                                                  │
│  分析用戶問題，比對知識庫描述：                                  │
│                                                                  │
│  📚 saf_projects 描述提到：                                     │
│     「查詢特定客戶的專案（例如：WD...）」 ← ✅ 匹配！           │
│                                                                  │
│  📊 saf_summary 描述提到：                                      │
│     「專案總數量、分佈情況」 ← ❌ 不太匹配                      │
│                                                                  │
│  決策：使用 saf_projects 知識庫                                 │
└─────────────────────────────────┬───────────────────────────────┘
                                  │
                                  ▼
POST /api/dify/saf/retrieval/
{
    "knowledge_id": "saf_projects",  ← Dify 自動選擇的
    "query": "WD 有哪些專案？"
}
                                  │
                                  ▼
後端根據 knowledge_id="saf_projects" → 使用 projects API
```

#### 🔧 後端對應邏輯

後端會根據 `knowledge_id` 自動映射到對應的 `endpoint`：

```python
# library/saf_integration/handler.py

KNOWLEDGE_ID_TO_ENDPOINT = {
    "saf_projects": "projects",        # 專案搜尋 → projects API
    "saf_summary": "summary",          # 專案統計 → summary API
    "saf_project_names": "project_names",  # 🆕 專案名稱清單
}
```

### A.3 🆕 知識庫 3：SAF 專案名稱清單（新增）

| 設定項目 | 值 |
|---------|-----|
| **名稱** | SAF 專案名稱清單 |
| **Knowledge ID** | `saf_project_names` |
| **Top K** | 1 |
| **Score Threshold** | 0.3 |

**描述/前後文內容**（複製以下內容到 Dify 知識庫描述欄位）：

```
用於獲取 SAF 所有專案名稱的清單。這是一個輕量級的查詢，只返回專案名稱，不包含詳細資訊。

當用戶詢問以下類型的問題時，應該使用此知識庫：
- 列出所有專案名稱
- 有哪些專案？（不需要詳細資訊時）
- 專案名稱清單
- 按客戶/控制器分組的專案名稱
- 快速查看專案列表

範例問題：
- 「列出所有專案名稱」
- 「有哪些專案？」
- 「給我專案清單」
- 「按客戶列出專案名稱」
- 「WD 有哪些專案名稱？」（只要名稱）
```

### A.4 使用範例

```
使用者：請查詢 WD 的專案有哪些？
AI：（Dify 自動選擇 saf_projects → endpoint=projects）
    → 返回完整專案資訊（含 NAND、韌體、負責人等）

使用者：目前有多少專案？
AI：（Dify 自動選擇 saf_summary → endpoint=summary）
    → 返回統計數據

使用者：SM2264 控制器有哪些專案？
AI：（Dify 自動選擇 saf_projects → endpoint=projects）
    → 返回完整專案資訊

使用者：各客戶的專案分佈？
AI：（Dify 自動選擇 saf_summary → endpoint=summary）
    → 返回統計數據

使用者：列出所有專案名稱
AI：（Dify 自動選擇 saf_project_names → endpoint=project_names）🆕
    → 返回專案名稱清單（輕量級）

使用者：有哪些專案？給我清單就好
AI：（Dify 自動選擇 saf_project_names → endpoint=project_names）🆕
    → 返回專案名稱清單
```

### A.5 配置檢查清單

完成 Dify Studio 配置後，請確認以下項目：

| 檢查項目 | 說明 |
|---------|------|
| ✅ 外部知識 API 已設定 | `http://your-server/api/dify/saf/retrieval/` |
| ✅ saf_projects 知識庫已建立 | Knowledge ID 為 `saf_projects` |
| ✅ saf_summary 知識庫已建立 | Knowledge ID 為 `saf_summary` |
| ✅ saf_project_names 知識庫已建立 | 🆕 Knowledge ID 為 `saf_project_names` |
| ✅ 描述/前後文已填寫 | 每個知識庫都有詳細的描述 |
| ✅ 三個知識庫都已加入 Prompt | 在 App 的 Prompt 中引用三個知識庫 |

### A.6 進階：在 Dify 工作流中動態切換 endpoint

如果使用 Dify 工作流，可以根據用戶意圖動態設定 `endpoint` 參數：

```yaml
# 工作流範例
nodes:
  - name: "意圖識別"
    type: "llm"
    prompt: "判斷用戶是要查詢專案列表還是統計資訊"
    
  - name: "SAF 知識庫查詢"
    type: "knowledge_retrieval"
    inputs:
      endpoint: "{{ intent == 'statistics' ? 'summary' : 'projects' }}"
```

---

## 附錄 B：擴展指南

### B.1 新增其他外部 API

如果未來需要新增其他外部 API（如 JIRA、Confluence 等），可以遵循相同的模式：

1. 在 `library/` 下建立新的整合模組
2. 實作 API Client 和資料轉換器
3. 實作搜尋服務（符合 Dify 格式）
4. 在 `KNOWLEDGE_ID_MAPPING` 中註冊
5. 在搜尋函數註冊表中添加

### B.2 自定義搜尋邏輯

如果需要更複雜的搜尋邏輯（如向量搜尋），可以：

1. 定期同步 SAF 資料到本地 PostgreSQL
2. 使用 pgvector 建立向量索引
3. 實作混合搜尋（關鍵字 + 語義）

---

**文檔結束**

📅 更新日期：2025-12-04  
📝 版本：v1.4  
✍️ 作者：AI Platform Team  
🎯 狀態：規劃完成，待實作

---

## 變更記錄

| 版本 | 日期 | 變更內容 |
|------|------|----------|
| v1.0 | 2025-12-04 | 初版：使用統一入口架構 |
| v1.1 | 2025-12-04 | 改為獨立入口架構 (`/api/dify/saf/retrieval/`)，新增 endpoint 參數設計 |
| v1.2 | 2025-12-04 | 新增「透過知識庫描述自動選擇 API」配置指南（附錄 A.2） |
| v1.3 | 2025-12-04 | 新增 `project_names` endpoint 設計，支援取得所有專案名稱清單（輕量級） |
| v1.4 | 2025-12-04 | 重新規劃分階段實作計畫，加入里程碑、驗收標準和快速開始指令 |
