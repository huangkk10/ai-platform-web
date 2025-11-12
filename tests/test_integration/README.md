# 🔗 Integration Tests - 整合測試

## 📋 目的

驗證系統各組件之間的整合和協作。

## 📁 測試檔案

### `test_web_frontend_chat.py` (8.4 KB)
**前端聊天介面整合測試**

**測試內容**：
- React 前端與 Django 後端的整合
- WebSocket 連線測試
- 聊天訊息傳遞
- UI 互動功能

**測試方法**：
```bash
docker exec ai-django python tests/test_integration/test_web_frontend_chat.py
```

---

### `test_dify_chat_with_knowledge.py` (3.6 KB)
**Dify AI 與知識庫整合測試**

**測試內容**：
- Dify API 連線
- 外部知識庫查詢
- RAG（檢索增強生成）功能
- 知識庫回應整合

**測試場景**：
1. 基礎知識庫查詢
2. 複雜問題的知識檢索
3. 多輪對話中的知識整合

---

### `verify_integration.py` (6.4 KB)
**系統整合驗證腳本**

**驗證項目**：
- 資料庫連接
- API 端點可用性
- 服務間通訊
- 配置正確性

**執行方式**：
```bash
docker exec ai-django python tests/test_integration/verify_integration.py
```

**檢查清單**：
- [ ] PostgreSQL 連接正常
- [ ] Dify API 可連接
- [ ] Nginx 反向代理正常
- [ ] 向量搜尋服務可用
- [ ] 所有 API 端點回應正常

---

## 🎯 執行所有整合測試

```bash
# 執行所有整合測試
docker exec ai-django python -m pytest tests/test_integration/ -v

# 快速驗證系統整合
docker exec ai-django python tests/test_integration/verify_integration.py
```

---

## 🏗️ 整合架構

```
┌─────────────────────────────────────────┐
│           Web Frontend (React)          │
│         http://localhost:3000           │
└──────────────────┬──────────────────────┘
                   │ HTTP/REST API
┌──────────────────▼──────────────────────┐
│         Nginx Reverse Proxy             │
│           http://localhost              │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────▼──────────────────────┐
│       Django Backend (REST API)         │
│           http://localhost:8000         │
└─────┬──────────────────────────┬────────┘
      │                          │
      │                          │
┌─────▼─────────┐      ┌─────────▼────────┐
│  PostgreSQL   │      │   Dify AI API    │
│   (pgvector)  │      │ (External RAG)   │
└───────────────┘      └──────────────────┘
```

---

## ✅ 整合測試檢查清單

完成以下驗證：

- [ ] 前端能正常載入
- [ ] API 端點回應正常
- [ ] 資料庫查詢功能正常
- [ ] Dify AI 整合正常
- [ ] 向量搜尋功能正常
- [ ] 聊天功能端對端測試通過
- [ ] 錯誤處理機制正常

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team  
**執行頻率**：每次部署前必須執行
