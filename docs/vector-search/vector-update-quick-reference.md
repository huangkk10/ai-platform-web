# RVT Assistant 向量資料庫定時更新 - 快速參考

## 🎯 **核心設計**

RVT Assistant 使用 **Celery Beat 定時任務** 來處理聊天向量化，而非即時生成。

### **為什麼選擇定時處理？**
- 聊天過程中不會自動生成向量
- 需要定期處理累積的未向量化消息
- 批量處理比即時處理更高效
- 不影響聊天功能的穩定性

## ⏰ **定時排程**

| 任務 | 頻率 | 說明 |
|------|------|------|
| 用戶問題向量化 | 每小時 | 高優先級，確保及時性 |
| 助手回覆向量化 | 每6小時 | 低優先級 |
| 預載入服務 | 每天凌晨3:00 | 系統維護 |
| 問題統計更新 | 每天凌晨3:30 | 分析更新 |
| 快取清理 | 每天凌晨2:00 | 資源清理 |

## 📁 **關鍵檔案**

```
backend/ai_platform/celery.py              # 定時任務配置
library/rvt_analytics/tasks.py             # 向量處理任務
library/rvt_analytics/chat_vector_service.py  # 向量生成服務
```

## 🚀 **快速檢查指令**

```bash
# 檢查向量統計
docker exec ai-django python -c "
from django.db import connection
with connection.cursor() as cursor:
    cursor.execute('SELECT COUNT(*) FROM chat_messages')
    total = cursor.fetchone()[0]
    cursor.execute('SELECT COUNT(*) FROM chat_message_embeddings_1024')  
    vectorized = cursor.fetchone()[0]
    print(f'向量化率: {vectorized}/{total} ({vectorized/total*100:.1f}%)')
"

# 手動執行向量化
docker exec ai-django python -c "
from library.rvt_analytics.tasks import rebuild_chat_vectors
result = rebuild_chat_vectors.apply(kwargs={'user_role': 'user', 'min_length': 5})
print(f'處理結果: {result.result}')
"

# 檢查 Celery Beat 狀態
docker logs ai-celery-beat --tail 10
```

## 📊 **預期效果**

- **24小時內**: 90%+ 消息完成向量化
- **熱門問題分析**: 反映最新用戶關注點  
- **系統負載**: 分散在定時週期，低峰期執行
- **處理效能**: ~5 消息/秒

## ⚠️ **注意事項**

1. **重複內容會被跳過** - 這是正常行為，不是錯誤
2. **向量表使用 content_hash 唯一約束** - 避免重複存儲
3. **任務有過期時間** - 防止任務堆疊
4. **使用 1024 維向量** - 基於 multilingual-e5-large 模型

---

**詳細文檔**: `/docs/vector-database-scheduled-update-architecture.md`  
**實施日期**: 2025-10-09  
**驗證狀態**: ✅ 已測試並運行