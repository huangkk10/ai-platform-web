# 診斷工具目錄

本目錄包含系統診斷和問題排查工具。

## 診斷工具

### rvt_assistant_diagnostic.py
**用途**: RVT Assistant 系統診斷工具

**功能**:
- 分析 RVT Assistant 聊天功能的 API 問題
- 檢查 Dify 整合狀態
- 驗證知識庫連接
- 診斷回應時間和效能問題
- 分析錯誤日誌

**執行方式**:
```bash
# 在容器內執行
docker exec ai-django python tests/test_diagnostics/rvt_assistant_diagnostic.py

# 或在宿主機執行
python tests/test_diagnostics/rvt_assistant_diagnostic.py
```

**診斷項目**:
- ✅ API 端點連通性
- ✅ Dify 服務狀態
- ✅ 知識庫向量數據
- ✅ 回應時間分析
- ✅ 錯誤率統計
- ✅ 配置正確性檢查

**輸出**:
- 詳細的診斷報告
- 問題建議和修復方案
- 效能指標統計

---

## 使用場景

### 1. 功能異常排查
當 RVT Assistant 出現問題時，運行診斷工具快速定位問題：
```bash
docker exec ai-django python tests/test_diagnostics/rvt_assistant_diagnostic.py
```

### 2. 定期健康檢查
建議定期執行診斷工具，確保系統正常運作：
```bash
# 每日健康檢查腳本
#!/bin/bash
docker exec ai-django python tests/test_diagnostics/rvt_assistant_diagnostic.py > /logs/health_check_$(date +%Y%m%d).log
```

### 3. 問題回報
當需要提交問題報告時，附上診斷工具的完整輸出。

---

## 相關文檔

- RVT Assistant 文檔：`/docs/features/rvt-assistant-*.md`
- 系統架構：`/docs/architecture/`
- 故障排除指南：`/docs/troubleshooting/`
