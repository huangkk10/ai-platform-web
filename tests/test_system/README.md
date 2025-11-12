# 🧪 System Tests - 綜合系統測試

## 📋 目的

驗證 Protocol Assistant 系統的整體功能和穩定性。

## 📁 測試檔案

### `test_comprehensive_protocol_system.py`
**最新綜合測試套件**（23 KB）

**測試範圍**：
1. **外部知識庫 API** - Dify 端點測試
2. **Django 搜尋服務** - 向量、關鍵字、混合搜尋
3. **搜尋模式切換** - auto、section_only、document_only
4. **閾值敏感度** - 0.3 ~ 0.95 的閾值測試
5. **邊界案例處理** - 空查詢、極短、極長、特殊字元
6. **資料庫完整性** - 向量資料、段落資料完整性

**執行方式**：
```bash
docker exec ai-django python /app/tests/test_system/test_comprehensive_protocol_system.py
```

**最後測試結果**：
- ✅ 資料庫完整性：4/4 通過
- ✅ Django 搜尋服務：4/4 通過
- ✅ 搜尋模式切換：3/3 通過
- ✅ 邊界案例處理：6/6 通過
- ⚠️ 外部 API：0/5（環境問題，容器內無法連接 localhost）

**總體評估**：✅ **核心功能 100% 通過**

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team
