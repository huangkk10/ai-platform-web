# API 測試目錄

本目錄包含所有 API 端點和連通性相關的測試。

## 測試檔案

### api_connectivity_test.py
**用途**: 測試 AI Platform 各種 API 端點的連通性和基本功能

**測試範圍**:
- Django REST API 端點
- Dify AI 服務連接
- 外部知識庫 API
- 認證和授權機制

**執行方式**:
```bash
# 在容器內執行
docker exec ai-django python tests/test_api/api_connectivity_test.py

# 或在宿主機執行（需要配置環境）
python tests/test_api/api_connectivity_test.py
```

**測試項目**:
- ✅ API 伺服器連通性
- ✅ 認證 Token 驗證
- ✅ 基本 CRUD 操作
- ✅ 錯誤處理機制
- ✅ 回應時間測試

---

### test_section_search_api.py
**用途**: 測試段落搜尋 API 的功能和效能

**測試範圍**:
- 段落向量搜尋 API
- 語義相似度計算
- 搜尋結果排序
- API 參數驗證

**執行方式**:
```bash
docker exec ai-django python tests/test_api/test_section_search_api.py
```

**測試項目**:
- ✅ 基本搜尋功能
- ✅ 參數驗證（top_k, threshold）
- ✅ 搜尋結果格式
- ✅ 錯誤處理
- ✅ 邊界條件測試

---

## 測試數據

測試使用的配置來自：
- `tests/test_config.py` - 測試配置工具
- `config/settings.yaml` - 系統配置

## 相關文檔

- API 文檔：`/docs/api/`
- 系統架構：`/docs/architecture/`
