# Benchmark System API Reference

**版本**: v1.0.0  
**更新日期**: 2025-11-22  
**狀態**: ✅ Phase 4 完成，所有 API 端點已就緒

---

## 📋 概述

Protocol Assistant Benchmark 系統提供完整的 REST API，用於測試案例管理、測試執行、結果分析和版本控制。

### 基礎 URL
```
http://localhost/api/benchmark/
```

### 認證方式
- **Session Authentication** (推薦：Web 應用)
- **Token Authentication** (推薦：API 整合)

---

## 🧪 測試案例 API (`/test-cases/`)

### 1. 列出所有測試案例
```http
GET /api/benchmark/test-cases/
```

**查詢參數**:
- `category` (string): 類別篩選（如：資源路徑、安裝設定）
- `difficulty` (string): 難度篩選（easy, medium, hard）
- `question_type` (string): 題型篩選（如：單一事實查詢、多步驟查詢）
- `knowledge_source` (string): 知識源篩選（如：ULINK、UNH-IOL）
- `is_active` (boolean): 啟用狀態篩選

**回應範例**:
```json
{
  "count": 50,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "question": "ULINK 測試的安裝程式和測試腳本存放在 NAS 的哪個路徑？",
      "category": "資源路徑",
      "difficulty_level": "easy",
      "question_type": "單一事實查詢",
      "knowledge_source": "ULINK",
      "expected_document_ids": [1, 5],
      "min_required_matches": 1,
      "is_active": true,
      "created_at": "2025-10-20T10:00:00Z"
    }
  ]
}
```

---

### 2. 獲取測試案例統計
```http
GET /api/benchmark/test-cases/statistics/
```

**回應範例**:
```json
{
  "total_count": 50,
  "active_count": 48,
  "inactive_count": 2,
  "by_category": [
    {"category": "資源路徑", "count": 8},
    {"category": "安裝設定", "count": 10}
  ],
  "by_difficulty": [
    {"difficulty_level": "easy", "count": 13},
    {"difficulty_level": "medium", "count": 27},
    {"difficulty_level": "hard", "count": 10}
  ],
  "by_question_type": [
    {"question_type": "單一事實查詢", "count": 15},
    {"question_type": "多步驟查詢", "count": 12}
  ]
}
```

---

### 3. 創建測試案例
```http
POST /api/benchmark/test-cases/
Content-Type: application/json

{
  "question": "如何執行 ULINK 測試？",
  "category": "測試流程",
  "difficulty_level": "medium",
  "question_type": "流程查詢",
  "knowledge_source": "ULINK",
  "expected_document_ids": [1, 2, 3],
  "min_required_matches": 2,
  "is_active": true
}
```

---

### 4. 批量啟用測試案例
```http
POST /api/benchmark/test-cases/bulk_activate/
Content-Type: application/json

{
  "ids": [1, 2, 3, 4, 5]
}
```

**回應**:
```json
{
  "success": true,
  "updated_count": 5,
  "message": "已啟用 5 個測試案例"
}
```

---

### 5. 批量停用測試案例
```http
POST /api/benchmark/test-cases/bulk_deactivate/
Content-Type: application/json

{
  "ids": [10, 11, 12]
}
```

---

## 🚀 測試執行 API (`/test-runs/`)

### 1. 列出測試執行記錄
```http
GET /api/benchmark/test-runs/
```

**查詢參數**:
- `version_id` (int): 版本 ID 篩選
- `status` (string): 狀態篩選（pending, running, completed, stopped, failed）
- `run_type` (string): 類型篩選（manual, scheduled, ci）
- `days` (int): 時間範圍（最近 N 天）

**回應範例**:
```json
{
  "count": 4,
  "results": [
    {
      "id": 4,
      "version": 3,
      "version_name": "Baseline Version",
      "version_code": "v2.1.0-baseline",
      "run_name": "首次完整測試 - 2025-11-22 04:09",
      "run_type": "manual",
      "status": "completed",
      "total_test_cases": 10,
      "completed_test_cases": 10,
      "passed_test_cases": 8,
      "failed_test_cases": 2,
      "overall_score": 48.20,
      "precision_pct": 19.8,
      "recall_pct": 80.0,
      "f1_score_pct": 31.4,
      "ndcg_pct": 57.6,
      "avg_time_ms": 803,
      "started_at": "2025-11-22T04:09:31Z",
      "completed_at": "2025-11-22T04:09:39Z"
    }
  ]
}
```

---

### 2. 啟動新測試 ⭐️
```http
POST /api/benchmark/test-runs/start_test/
Content-Type: application/json

{
  "version_id": 3,
  "run_name": "自動測試 - 2025-11-22",
  "run_type": "manual",
  "category": "資源路徑",
  "difficulty": "easy",
  "limit": 10,
  "notes": "測試新版本搜尋功能"
}
```

**回應**:
```json
{
  "success": true,
  "test_run": {
    "id": 5,
    "run_name": "自動測試 - 2025-11-22",
    "status": "completed",
    "total_test_cases": 10,
    "passed_test_cases": 9,
    "overall_score": 65.30
  },
  "message": "測試執行完成，ID: 5"
}
```

---

### 3. 獲取測試結果
```http
GET /api/benchmark/test-runs/{id}/results/
```

**查詢參數**:
- `passed_only` (boolean): 只顯示通過的結果

**回應範例**:
```json
[
  {
    "id": 41,
    "test_case": 1,
    "test_case_question": "ULINK 測試的安裝程式...",
    "test_case_difficulty": "easy",
    "search_query": "ULINK 測試的安裝程式...",
    "returned_document_ids": [1, 2, 3, 4, 5],
    "precision_score": 0.20,
    "recall_score": 1.00,
    "f1_score": 0.33,
    "ndcg_score": 0.39,
    "response_time": 7018.35,
    "is_passed": true,
    "created_at": "2025-11-22T04:09:32Z"
  }
]
```

---

### 4. 比較兩次測試執行 ⭐️
```http
POST /api/benchmark/test-runs/compare/
Content-Type: application/json

{
  "run_id_1": 3,
  "run_id_2": 4
}
```

**回應**:
```json
{
  "run_1": {
    "id": 3,
    "name": "測試執行 3",
    "version": "v2.1.0-baseline",
    "overall_score": 0.00,
    "precision": 0.0,
    "recall": 0.0,
    "pass_rate": 0.0
  },
  "run_2": {
    "id": 4,
    "name": "首次完整測試",
    "version": "v2.1.0-baseline",
    "overall_score": 48.20,
    "precision": 19.8,
    "recall": 80.0,
    "pass_rate": 80.0
  },
  "delta": {
    "overall_score": 48.20,
    "precision": 19.8,
    "recall": 80.0
  }
}
```

---

### 5. 停止執行中的測試
```http
POST /api/benchmark/test-runs/{id}/stop_test/
```

---

## 📊 測試結果 API (`/test-results/`)

### 1. 查詢測試結果
```http
GET /api/benchmark/test-results/
```

**查詢參數**:
- `test_run_id` (int): 測試執行 ID
- `test_case_id` (int): 測試案例 ID
- `is_passed` (boolean): 通過狀態

---

### 2. 獲取所有失敗案例 ⭐️
```http
GET /api/benchmark/test-results/failed_cases/
```

**回應範例**:
```json
{
  "total_failed_results": 2,
  "unique_failed_cases": 2,
  "failed_cases": [
    {
      "test_case_id": 4,
      "question": "ULINK 測試工具的完整名稱是什麼？",
      "category": "工具介紹",
      "difficulty": "easy",
      "failed_count": 1,
      "recent_failures": [
        {
          "test_run_id": 4,
          "test_run_name": "首次完整測試",
          "precision": 0.0,
          "recall": 0.0,
          "created_at": "2025-11-22T04:09:33Z"
        }
      ]
    }
  ]
}
```

---

## 🔖 演算法版本 API (`/versions/`)

### 1. 列出所有版本
```http
GET /api/benchmark/versions/
```

**回應範例**:
```json
{
  "count": 1,
  "results": [
    {
      "id": 3,
      "version_name": "Baseline Version",
      "version_code": "v2.1.0-baseline",
      "description": "Protocol Assistant 基準版本",
      "algorithm_type": "hybrid",
      "is_active": true,
      "is_baseline": true,
      "created_at": "2025-11-22T03:52:58Z",
      "created_by_username": null,
      "test_runs_count": 4
    }
  ]
}
```

---

### 2. 創建新版本
```http
POST /api/benchmark/versions/
Content-Type: application/json

{
  "version_name": "優化版本 v2.2.0",
  "version_code": "v2.2.0-optimized",
  "description": "提高 threshold 到 0.75，優化權重配置",
  "algorithm_type": "hybrid",
  "parameters": {
    "threshold": 0.75,
    "weights": {
      "title": 0.95,
      "content": 0.05
    }
  },
  "is_active": true
}
```

---

### 3. 設定為基準版本
```http
POST /api/benchmark/versions/{id}/set_as_baseline/
```

**回應**:
```json
{
  "success": true,
  "message": "版本 優化版本 v2.2.0 已設定為基準版本"
}
```

---

### 4. 獲取版本測試歷史
```http
GET /api/benchmark/versions/{id}/test_history/
```

---

### 5. 獲取當前基準版本
```http
GET /api/benchmark/versions/baseline/
```

---

## 📈 完整 API 端點總覽

### 測試案例 (7 個端點)
- `GET /api/benchmark/test-cases/` - 列表
- `POST /api/benchmark/test-cases/` - 創建
- `GET /api/benchmark/test-cases/{id}/` - 詳情
- `PUT /api/benchmark/test-cases/{id}/` - 更新
- `DELETE /api/benchmark/test-cases/{id}/` - 刪除
- `GET /api/benchmark/test-cases/statistics/` - 統計
- `POST /api/benchmark/test-cases/bulk_activate/` - 批量啟用
- `POST /api/benchmark/test-cases/bulk_deactivate/` - 批量停用

### 測試執行 (8 個端點)
- `GET /api/benchmark/test-runs/` - 列表
- `POST /api/benchmark/test-runs/` - 創建
- `GET /api/benchmark/test-runs/{id}/` - 詳情
- `PUT /api/benchmark/test-runs/{id}/` - 更新
- `DELETE /api/benchmark/test-runs/{id}/` - 刪除
- `POST /api/benchmark/test-runs/start_test/` - **啟動測試**
- `GET /api/benchmark/test-runs/{id}/results/` - 獲取結果
- `POST /api/benchmark/test-runs/compare/` - **比較測試**
- `POST /api/benchmark/test-runs/{id}/stop_test/` - 停止測試

### 測試結果 (3 個端點)
- `GET /api/benchmark/test-results/` - 列表
- `GET /api/benchmark/test-results/{id}/` - 詳情
- `GET /api/benchmark/test-results/failed_cases/` - **失敗案例分析**

### 演算法版本 (8 個端點)
- `GET /api/benchmark/versions/` - 列表
- `POST /api/benchmark/versions/` - 創建
- `GET /api/benchmark/versions/{id}/` - 詳情
- `PUT /api/benchmark/versions/{id}/` - 更新
- `DELETE /api/benchmark/versions/{id}/` - 刪除
- `POST /api/benchmark/versions/{id}/set_as_baseline/` - **設為基準**
- `GET /api/benchmark/versions/{id}/test_history/` - 測試歷史
- `GET /api/benchmark/versions/baseline/` - **當前基準版本**

**總計**: 26 個 API 端點（12 個標準 REST + 14 個自訂 Actions）

---

## 🧪 測試範例

### 使用 curl 測試

```bash
# 1. 獲取統計資訊
curl -X GET "http://localhost/api/benchmark/test-cases/statistics/" \
  -H "Authorization: Token YOUR_TOKEN"

# 2. 啟動測試（前 5 題，Easy 難度）
curl -X POST "http://localhost/api/benchmark/test-runs/start_test/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{
    "version_id": 3,
    "run_name": "Quick Test",
    "difficulty": "easy",
    "limit": 5
  }'

# 3. 查看測試結果
curl -X GET "http://localhost/api/benchmark/test-runs/5/results/" \
  -H "Authorization: Token YOUR_TOKEN"

# 4. 比較兩次測試
curl -X POST "http://localhost/api/benchmark/test-runs/compare/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Token YOUR_TOKEN" \
  -d '{"run_id_1": 3, "run_id_2": 4}'
```

---

## 🔒 權限控制

所有 API 端點都需要認證：

- **IsAuthenticated**: 所有端點都需要登入
- **Create/Update/Delete**: 需要有相應權限的用戶

---

## 📝 錯誤處理

### 標準錯誤格式
```json
{
  "error": "錯誤訊息描述",
  "detail": "詳細錯誤資訊（可選）"
}
```

### 常見 HTTP 狀態碼
- `200 OK` - 請求成功
- `201 Created` - 創建成功
- `400 Bad Request` - 請求參數錯誤
- `401 Unauthorized` - 未認證
- `403 Forbidden` - 無權限
- `404 Not Found` - 資源不存在
- `500 Internal Server Error` - 伺服器錯誤

---

## 🎉 Phase 4 完成狀態

✅ **Phase 4.1**: Serializers 已存在且完整  
✅ **Phase 4.2**: 4 個 ViewSets 全部創建（570 行代碼）  
✅ **Phase 4.3**: API 路由已註冊，26 個端點可用  
⏳ **Phase 4.4**: API 測試待進行  

**下一步**: Phase 5 前端介面開發

---

**文檔版本**: v1.0.0  
**作者**: AI Platform Team  
**最後更新**: 2025-11-22
