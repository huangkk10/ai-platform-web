# 💬 Conversation Tests - 對話管理測試

## 📋 目的

驗證 AI 對話管理、對話歷史處理和穩定性。

## 📁 測試檔案

### `test_conversation_history_pollution.py` (17 KB)
**對話歷史污染測試**

**測試場景**：
- 長對話中的歷史污染問題
- 不相關對話對當前查詢的影響
- 對話隔離機制驗證

**測試方法**：
```bash
docker exec ai-django python tests/test_conversation/test_conversation_history_pollution.py
```

**關鍵指標**：
- 對話污染率
- 答案準確度下降比例
- 隔離機制效果

---

### `test_dify_memory_interval_effect.py` (13 KB)
**Dify 記憶間隔效果測試**

**測試內容**：
- Dify AI 記憶間隔設定
- 記憶保持時間測試
- 不同間隔對回答品質的影響

**測試配置**：
- 短期記憶：5 分鐘
- 中期記憶：30 分鐘
- 長期記憶：2 小時

---

### `test_protocol_crystaldiskmark_stability.py` (19 KB)
**CrystalDiskMark 穩定性測試**

**測試內容**：
- 相同問題的連續查詢穩定性
- 對話 ID 持久性測試
- 長時間對話的穩定性

**測試模式**：
1. 新對話模式 - 每次新建對話 ID
2. 持續對話模式 - 使用固定對話 ID
3. 同一對話模式 - 連續使用同一對話
4. 清除對話模式 - 測試對話清除

**執行方式**：
```bash
docker exec ai-django python tests/test_conversation/test_protocol_crystaldiskmark_stability.py
```

---

## 🎯 執行所有對話測試

```bash
# 執行所有對話管理測試
docker exec ai-django python -m pytest tests/test_conversation/ -v
```

---

## 📊 測試指標

| 測試項目 | 目標值 | 測試結果 |
|---------|-------|---------|
| 對話污染率 | < 5% | ✅ 通過 |
| 記憶保持準確度 | > 90% | ✅ 通過 |
| 穩定性測試通過率 | > 95% | ✅ 通過 |

---

**創建日期**：2025-11-13  
**維護者**：AI Platform Team  
**相關組件**：Dify AI、Conversation Management
