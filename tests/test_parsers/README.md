# 解析器測試目錄

本目錄包含各種解析器和數據處理功能的測試。

## 測試檔案

### test_ai_answer_parsing.py
**用途**: 測試 AI 回答解析功能

**測試範圍**:
- OCR 結果解析
- AI 回答格式化
- 從 Web UI 上傳的圖片解析邏輯
- 多種回答格式處理

**執行方式**:
```bash
docker exec ai-django python tests/test_parsers/test_ai_answer_parsing.py
```

---

### test_improved_ocr_parser.py
**用途**: 測試改進後的 OCR 解析器

**測試範圍**:
- OCR 文本提取
- 表格識別和解析
- 圖片預處理
- 多語言支援

**執行方式**:
```bash
docker exec ai-django python tests/test_parsers/test_improved_ocr_parser.py
```

---

### test_markdown_parser.py
**用途**: 測試 Markdown 結構解析器

**測試範圍**:
- Markdown 標題識別（H1-H6）
- 段落分割
- 代碼區塊處理
- 列表和表格解析
- 段落層級結構

**執行方式**:
```bash
docker exec ai-django python tests/test_parsers/test_markdown_parser.py
```

**測試案例**:
- ✅ 簡單 Markdown 解析
- ✅ 複雜層級結構
- ✅ 代碼區塊保留
- ✅ 中英文混合內容
- ✅ 特殊字元處理

---

### test_benchmark_score_bug.py
**用途**: 測試 Benchmark 分數解析的 Bug 修復

**測試範圍**:
- Benchmark 分數提取邏輯
- 錯誤處理
- 邊界條件測試

**執行方式**:
```bash
docker exec ai-django python tests/test_parsers/test_benchmark_score_bug.py
```

---

### test_fixed_benchmark_score.py
**用途**: 驗證修復後的 Benchmark 分數解析功能

**測試範圍**:
- 正確的分數提取
- 多種格式支援
- 回歸測試

**執行方式**:
```bash
docker exec ai-django python tests/test_parsers/test_fixed_benchmark_score.py
```

---

## 測試數據

測試使用的樣本數據：
- OCR 測試圖片：`tests/test_data/ocr_samples/`
- Markdown 測試檔案：`tests/test_data/markdown_samples/`
- Benchmark 測試資料：測試代碼內嵌

## 開發指南

### 新增解析器測試

1. 創建測試檔案：`test_<parser_name>.py`
2. 實現測試函數
3. 添加測試案例
4. 更新本 README

### 測試命名規範

- 測試函數：`test_<功能描述>()`
- 測試案例：使用描述性變數名
- 斷言訊息：包含詳細的錯誤資訊

---

## 相關組件

這些測試對應的解析器位於：
- `library/data_processing/ocr_analyzer.py` - OCR 分析器
- `library/common/knowledge_base/markdown_parser.py` - Markdown 解析器
- `library/ai_ocr/` - AI OCR 相關功能

---

## 相關文檔

- 解析器文檔：`/docs/development/parsers/`
- AI OCR 整合：`/docs/ai-integration/ai-ocr-*.md`
- 數據處理流程：`/docs/architecture/data-processing.md`
