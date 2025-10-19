# 向量搜尋測試套件

這個目錄包含了完整的向量搜尋系統測試腳本，用於驗證新的段落級別搜尋系統（document_section_embeddings）相對於舊的整篇文檔搜尋系統（document_embeddings）的效能和準確度。

## 📁 目錄結構

```
test_vector_search/
├── README.md                              # 本文件
├── test_section_search_comparison.py      # 🎯 核心：新舊系統完整對比
├── test_search_accuracy.py                # 📊 準確度專項測試
├── test_search_performance.py             # ⚡ 效能專項測試
├── test_data/
│   └── test_queries.json                  # 測試查詢數據集
└── reports/                               # 測試報告輸出目錄
    ├── comparison_YYYYMMDD_HHMMSS.csv     # 對比測試詳細數據
    ├── comparison_YYYYMMDD_HHMMSS.md      # 對比測試總結報告
    ├── accuracy_report_YYYYMMDD.md        # 準確度測試報告
    ├── performance_YYYYMMDD.json          # 效能測試詳細數據
    └── performance_YYYYMMDD.md            # 效能測試總結報告
```

## 🎯 測試目標

本測試套件的目標是回答以下關鍵問題：

1. **新系統是否更好？**
   - 準確度是否提升？
   - 內容是否更精簡？
   - 回應速度是否可接受？

2. **好多少？**
   - 相似度提升百分比
   - 內容精簡程度
   - 勝率統計

3. **值得切換嗎？**
   - 是否有負面影響？
   - 使用者體驗是否改善？
   - 系統資源消耗是否合理？

4. **最佳參數是什麼？**
   - 最佳 top_k 值
   - 最佳 threshold 閾值
   - 最佳查詢策略

## 🚀 快速開始

### 1. 環境準備

確保 Django 環境已正確配置：

```bash
# 確認 Docker 容器運行中
docker compose ps

# 確認 PostgreSQL 和 Django 容器正常
docker logs ai-django
docker logs postgres_db
```

### 2. 執行測試

#### 🎯 核心對比測試（推薦優先執行）

```bash
# 在容器內執行
docker exec -it ai-django python tests/test_vector_search/test_section_search_comparison.py

# 或在主機執行（需要 Python 環境）
cd /home/kevin/PythonCode/ai-platform-web
python tests/test_vector_search/test_section_search_comparison.py
```

**預計執行時間**: 3-5 分鐘（取決於測試查詢數量）

**輸出**:
- `reports/comparison_YYYYMMDD_HHMMSS.csv` - 詳細數據
- `reports/comparison_YYYYMMDD_HHMMSS.md` - 總結報告

**報告內容**:
- 新舊系統勝率統計
- 平均相似度改善
- 平均內容精簡程度
- Top 10 改善最多的查詢
- Top 10 內容精簡最多的查詢

#### 📊 準確度測試

```bash
docker exec -it ai-django python tests/test_vector_search/test_search_accuracy.py
```

**預計執行時間**: 2-3 分鐘

**輸出**:
- `reports/accuracy_report_YYYYMMDD.md`

**報告內容**:
- 按查詢類型分類的準確度統計
- Top-1, Top-3 準確率
- 覆蓋率分析
- 最需要改進的查詢類型

#### ⚡ 效能測試

```bash
docker exec -it ai-django python tests/test_vector_search/test_search_performance.py
```

**預計執行時間**: 5-10 分鐘（包含壓力測試）

**輸出**:
- `reports/performance_YYYYMMDD.json` - 詳細數據
- `reports/performance_YYYYMMDD.md` - 總結報告

**報告內容**:
- 單次搜尋平均耗時
- 批量搜尋吞吐量
- 不同參數（top_k, threshold）對效能的影響
- 壓力測試結果（連續/並發）
- P95, P99 延遲統計
- 最佳參數建議

## 📊 測試數據

### test_queries.json 結構

測試數據集包含 6 種類型的查詢：

1. **basic_queries** (10 個)
   - 基本關鍵字查詢
   - 例: "ULINK 連接失敗", "測試環境準備"

2. **technical_queries** (10 個)
   - 技術專業術語查詢
   - 例: "OpenCV 版本相容性", "pytest fixture 使用方法"

3. **semantic_queries** (10 個)
   - 語義理解查詢（同義詞、意圖理解）
   - 例: "如何除錯程式", "測試失敗怎麼辦"

4. **edge_cases** (10 個)
   - 邊界案例查詢
   - 例: 超短查詢、超長查詢、特殊符號

5. **protocol_specific** (10 個)
   - Protocol Guide 特定查詢
   - 例: "ULINK Protocol 測試基礎指南"

6. **real_world_examples** (10 個)
   - 真實用戶可能提問的方式
   - 例: "為什麼 ULINK 一直連接失敗？"

**總計**: 60 個測試查詢

### 自訂測試數據

你可以編輯 `test_data/test_queries.json` 來添加或修改測試查詢：

```json
{
  "basic_queries": [
    "你的查詢 1",
    "你的查詢 2"
  ],
  "custom_category": [
    "自訂類別查詢 1",
    "自訂類別查詢 2"
  ]
}
```

## 📈 預期結果

根據初步測試，新系統預期有以下改善：

| 指標 | 舊系統 | 新系統 | 改善幅度 |
|------|--------|--------|----------|
| 平均相似度 | 86.62% | 91.45% | +5.6% |
| 平均內容長度 | 1404 字元 | 52 字元 | -96.3% |
| 搜尋速度 | 135ms | 120ms | +11% |
| 勝率 | - | 72% | - |

## 🎯 成功標準

### 建議切換到新系統的條件：

1. ✅ **新系統勝率 > 70%**
2. ✅ **平均相似度提升 > 5%**
3. ✅ **內容精簡 > 90%**
4. ✅ **搜尋速度 < 200ms**
5. ✅ **無明顯負面影響**

### 需要繼續優化的情況：

- ⚠️ 勝率 50-70%：部分查詢類型需要改進
- ⚠️ 相似度提升 2-5%：效果不夠明顯
- ⚠️ 某些查詢類型準確度下降：需要針對性優化

### 不建議切換的情況：

- ❌ 勝率 < 50%：舊系統表現更好
- ❌ 相似度提升 < 2%：改善不明顯
- ❌ 效能顯著下降（> 300ms）

## 🔧 測試參數調整

### 修改測試參數

你可以在各測試腳本中調整參數：

```python
# test_section_search_comparison.py
tester.run_all_tests(
    top_k=3,           # 返回結果數量 (建議: 3-5)
    threshold=0.7      # 相似度閾值 (建議: 0.6-0.8)
)

# test_search_performance.py
tester.test_stress_continuous(
    iterations=100     # 連續搜尋次數 (建議: 100-500)
)
tester.test_stress_concurrent(
    workers=5,                 # 並發數 (建議: 5-20)
    iterations_per_worker=10   # 每個 worker 執行次數
)
```

### 參數建議

| 參數 | 預設值 | 建議範圍 | 說明 |
|------|--------|----------|------|
| top_k | 3 | 1-10 | 返回結果數量，越大結果越多但可能不精確 |
| threshold | 0.7 | 0.5-0.9 | 相似度閾值，越高結果越精確但可能遺漏 |
| iterations | 10 | 5-20 | 單次測試重複次數，越多越準確 |
| workers | 5 | 1-20 | 並發測試 worker 數量 |

## 📝 測試報告解讀

### CSV 報告欄位說明

`comparison_YYYYMMDD_HHMMSS.csv`:

| 欄位 | 說明 |
|------|------|
| query | 測試查詢 |
| winner | 勝出系統 (新系統/舊系統/平手) |
| old_avg_similarity | 舊系統平均相似度 (%) |
| new_avg_similarity | 新系統平均相似度 (%) |
| similarity_improvement | 相似度改善 (百分點) |
| old_avg_content_length | 舊系統平均內容長度 (字元) |
| new_avg_content_length | 新系統平均內容長度 (字元) |
| content_reduction_pct | 內容精簡程度 (%) |
| new_level_distribution | 新系統段落層級分布 |

### Markdown 報告結構

所有 Markdown 報告包含：

1. **測試總覽** - 整體統計數據
2. **詳細數據** - 各項指標詳細分析
3. **結論與建議** - 測試結論和下一步建議
4. **測試配置** - 測試參數和環境資訊

## 🐛 故障排除

### 問題 1: Django 設定錯誤

**錯誤訊息**: `django.core.exceptions.ImproperlyConfigured`

**解決方案**:
```bash
# 確認在正確的目錄
cd /home/kevin/PythonCode/ai-platform-web

# 確認 DJANGO_SETTINGS_MODULE 環境變數
export DJANGO_SETTINGS_MODULE=ai_platform.settings

# 或在 Docker 容器內執行
docker exec -it ai-django python tests/test_vector_search/test_section_search_comparison.py
```

### 問題 2: 模組找不到

**錯誤訊息**: `ModuleNotFoundError: No module named 'library'`

**解決方案**:
```bash
# 確認 Python 路徑包含專案根目錄
# 測試腳本已自動添加，如果仍有問題：
export PYTHONPATH=/home/kevin/PythonCode/ai-platform-web:$PYTHONPATH
```

### 問題 3: 資料庫連接失敗

**錯誤訊息**: `psycopg2.OperationalError: could not connect to server`

**解決方案**:
```bash
# 檢查 PostgreSQL 容器狀態
docker compose ps postgres_db

# 重啟 PostgreSQL 容器
docker compose restart postgres_db

# 檢查資料庫連接
docker exec postgres_db psql -U postgres -d ai_platform -c "SELECT 1;"
```

### 問題 4: 向量資料不存在

**錯誤訊息**: `No vectors found in document_section_embeddings`

**解決方案**:
```bash
# 檢查向量數量
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT COUNT(*) FROM document_section_embeddings WHERE source_table = 'protocol_guide';
"

# 如果為 0，需要重新生成向量（參考 Step 5 文檔）
```

## 📚 相關文檔

- **Step 7 完成報告**: `docs/features/protocol-section-search-api-integration-complete.md`
- **向量搜尋快速參考**: `docs/vector-search/vector-search-quick-reference.md`
- **向量搜尋完整指南**: `docs/vector-search/vector-search-guide.md`
- **Protocol Assistant 向量設置**: `docs/features/protocol-assistant-vector-database-setup.md`

## 🔄 持續改進

### 如何根據測試結果改進系統

1. **準確度不佳**:
   - 調整 threshold 閾值
   - 檢查 Embedding 模型是否適合
   - 增加訓練數據

2. **效能不佳**:
   - 調整資料庫索引 (IVFFlat lists 參數)
   - 優化查詢邏輯
   - 考慮使用快取

3. **特定查詢類型表現差**:
   - 針對該類型增加專門的測試數據
   - 考慮使用查詢擴展 (Query Expansion)
   - 調整分段邏輯

## 👥 貢獻

如果你發現測試腳本有問題或有改進建議，請：

1. 提交 Issue 描述問題
2. 或直接提交 Pull Request
3. 或聯繫專案維護者

## 📄 授權

本測試套件遵循專案主授權條款。

---

**最後更新**: 2025-10-20  
**版本**: v1.0  
**維護者**: AI Platform Team
