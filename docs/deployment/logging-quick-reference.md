# 日誌系統快速參考卡

## 📁 日誌檔案速查

| 檔案 | 內容 | 保留 | 用途 |
|------|------|------|------|
| `django.log` | 一般日誌 | 30天 | 所有模組的 INFO+ |
| `django_error.log` | 錯誤日誌 | 60天 | 所有模組的 ERROR+ |
| `dify_requests.log` | Dify 請求 | 20天 | AI 請求追蹤 |
| `rvt_analytics.log` | RVT 分析 | 15天 | RVT 系統記錄 |
| `vector_operations.log` | 向量操作 | 15天 | 向量生成/搜尋 |
| `api_access.log` | API 訪問 | 7天 | HTTP 請求記錄 |
| `celery.log` | Celery 任務 | 10天 | 背景任務 |

## 🔍 常用命令

### 即時查看
```bash
tail -f logs/django.log                    # 一般日誌
tail -f logs/django_error.log              # 只看錯誤
tail -f logs/dify_requests.log             # Dify 請求
```

### 搜尋
```bash
grep "ERROR" logs/django.log               # 搜尋錯誤
grep "用戶名稱" logs/django.log            # 搜尋特定內容
grep -i "dify" logs/dify_requests.log      # 不區分大小寫
```

### 統計
```bash
wc -l logs/*.log                           # 各檔案行數
grep -c "ERROR" logs/django.log            # 錯誤數量
du -h logs/*                               # 檔案大小
```

### 按日期查詢
```bash
cat logs/django.log.2025-01-20             # 查看特定日期
grep "ERROR" logs/django.log.2025-01-20    # 特定日期的錯誤
```

### 範圍查詢
```bash
# 查看最後 100 行
tail -n 100 logs/django.log

# 查看前 50 行
head -n 50 logs/django.log

# 查看第 100-200 行
sed -n '100,200p' logs/django.log
```

## 🛠️ 管理工具

### 驗證系統
```bash
./scripts/verify_logging.sh
```

### 分析報告
```bash
./scripts/analyze_logs.sh
./scripts/analyze_logs.sh > report_$(date +%Y%m%d).txt
```

### 清理舊日誌
```bash
./scripts/clean_old_logs.sh              # 預設 30 天
./scripts/clean_old_logs.sh 60           # 保留 60 天
```

## 🎯 日誌級別

| 級別 | 說明 | 使用時機 |
|------|------|---------|
| `DEBUG` | 詳細調試 | Dify 請求詳情 |
| `INFO` | 一般資訊 | 正常業務流程 |
| `WARNING` | 警告 | 需注意但不致命 |
| `ERROR` | 錯誤 | 需處理的錯誤 |
| `CRITICAL` | 嚴重錯誤 | 系統崩潰級別 |

## 📊 分析範例

### 錯誤分析
```bash
# 今天的錯誤數量
grep -c "ERROR" logs/django.log

# 最近 10 筆錯誤
grep "ERROR" logs/django.log | tail -10

# 按錯誤類型統計
grep "ERROR" logs/django.log | awk -F'|' '{print $NF}' | sort | uniq -c
```

### API 分析
```bash
# API 訪問總數
wc -l < logs/api_access.log

# 最常訪問的端點
grep -oP 'GET [^ ]+' logs/api_access.log | sort | uniq -c | sort -rn
```

### 時間範圍
```bash
# 最早和最新的記錄
head -1 logs/django.log
tail -1 logs/django.log

# 特定時間段（使用 grep）
grep "2025-01-20 15:" logs/django.log
```

## 🚨 故障排查

### 日誌不生成
```bash
# 1. 檢查目錄權限
ls -la logs/

# 2. 檢查容器內目錄
docker exec ai-django ls -la /app/logs/

# 3. 檢查 Django 日誌配置
docker exec ai-django python -c "from django.conf import settings; print(settings.LOGGING)"

# 4. 重啟服務
docker compose restart django
```

### 磁碟空間不足
```bash
# 檢查磁碟使用
df -h
du -sh logs/

# 清理舊日誌
./scripts/clean_old_logs.sh 7
```

### 找不到特定日誌
```bash
# 搜尋所有日誌檔案
grep -r "搜尋內容" logs/

# 包含歷史檔案
grep "搜尋內容" logs/django.log*
```

## 💡 最佳實踐

### 1. 定期檢查
```bash
# 每週檢查
./scripts/analyze_logs.sh

# 檢查錯誤
grep ERROR logs/django_error.log
```

### 2. 保持清潔
```bash
# 每月清理
./scripts/clean_old_logs.sh 30
```

### 3. 監控空間
```bash
# 檢查總大小
du -sh logs/

# 設定告警（如 > 1GB）
[ $(du -s logs/ | cut -f1) -gt 1048576 ] && echo "⚠️  日誌過大"
```

### 4. 備份重要日誌
```bash
# 壓縮備份
tar -czf logs_backup_$(date +%Y%m%d).tar.gz logs/

# 複製到備份位置
cp logs_backup_*.tar.gz /backup/location/
```

## 📞 緊急情況

### 系統錯誤
```bash
# 即時查看錯誤
tail -f logs/django_error.log

# 查看最近 50 筆錯誤
tail -n 50 logs/django_error.log
```

### 效能問題
```bash
# 查看 WARNING 級別
grep WARNING logs/django.log | tail -20

# 查看特定時間的日誌
grep "2025-01-20 15:" logs/django.log
```

### API 異常
```bash
# 查看 API 訪問
tail -f logs/api_access.log

# 查看 4xx/5xx 錯誤
grep -E "(40[0-9]|50[0-9])" logs/api_access.log
```

## 🔗 相關文件

- 完整說明：`logs/README.md`
- 階段 1 報告：`docs/deployment/logging-phase1-implementation-report.md`
- 階段 2 報告：`docs/deployment/logging-phase2-implementation-report.md`
- 配置檔案：`backend/ai_platform/settings.py`

---
**版本**：v2.0  
**最後更新**：2025-10-21  
**維護者**：AI Platform Team
