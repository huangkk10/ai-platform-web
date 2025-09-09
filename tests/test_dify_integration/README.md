# 🔗 Dify 整合測試

本目錄包含與 Dify AI 平台整合的測試腳本。

## 📁 檔案說明

### `test_dify_chunwei.py`
- **功能**: 測試與 Dify 平台中 chunwei 應用的整合
- **測試內容**:
  - API 連接測試
  - 基本問答功能測試
  - 員工資料分析測試 (RAG 功能)
  - 與 DeepSeek 直接調用的比較測試

### `test_vector_rag.py`
- **功能**: 測試向量化 RAG 系統，將資料庫資料轉換為向量並進行智能搜尋
- **測試內容**:
  - 資料向量化處理
  - 向量相似度搜尋
  - 基於向量搜尋的 AI 問答
  - 向量化 RAG vs 傳統 RAG 效能比較

### `test_simple_vector_rag.py`
- **功能**: 簡化版向量化 RAG 測試，無需額外依賴
- **特點**:
  - 使用內建函式庫實現向量化
  - 基於字元頻率和關鍵詞的簡化算法
  - 快速部署，適合初步測試
  - 包含完整的搜尋和比較功能

## ⚙️ 配置說明

### API 設定
```python
DIFY_CONFIG = {
    'api_url': 'http://10.10.172.5/v1/chat-messages',
    'api_key': 'app-R5nTTZw6jSQX75sDvyUMxLgo',
    'base_url': 'http://10.10.172.5'
}
```

### 必要依賴
```bash
# 基本依賴安裝
pip install requests numpy

# 向量化增強功能（可選）
pip install sentence-transformers chromadb

# 或一次安裝所有依賴
pip install -r tests/test_dify_integration/requirements.txt
```

## 🚀 使用方法

### 基本測試
```bash
# 啟動虛擬環境
source venv/bin/activate

# 執行 Dify chunwei 測試
python tests/test_dify_integration/test_dify_chunwei.py

# 執行向量化 RAG 測試
python tests/test_dify_integration/test_vector_rag.py

# 執行簡化版向量化 RAG 測試（無需額外依賴）
python tests/test_dify_integration/test_simple_vector_rag.py
```

### 測試功能說明

#### 1. API 連接測試
- 驗證 Dify API 端點的可用性
- 測試認證金鑰的有效性
- 檢查網路連通性

#### 2. 基本問答測試
- 英文問題測試
- 中文問題測試
- 回應時間和品質評估

#### 3. 員工資料分析測試
- 從 SQLite 資料庫讀取員工資料
- 將資料作為上下文傳遞給 Dify
- 測試 RAG (Retrieval-Augmented Generation) 功能
- 驗證資料分析和計算能力

#### 4. 比較測試
- 同時測試 Dify chunwei 和 DeepSeek SSH
- 比較回應時間和品質
- 評估不同平台的優勢

#### 5. 向量化 RAG 測試
- 將員工資料轉換為向量表示
- 使用向量相似度進行智能搜尋
- 測試基於向量搜尋的問答品質
- 比較向量化 RAG 與傳統 RAG 的效能差異

## 📊 測試結果

測試腳本會提供詳細的報告，包括：
- 成功率統計
- 平均回應時間
- 錯誤分析
- 效能比較

## 🔧 故障排除

### 常見問題

1. **API 連接失敗**
   - 檢查網路連通性: `ping 10.10.172.5`
   - 驗證 API 端點: `curl http://10.10.172.5/v1/chat-messages`
   - 確認 API 金鑰有效性

2. **資料庫錯誤**
   - 確保 `company.db` 檔案存在
   - 檢查資料庫結構和資料
   - 驗證 SQLite 連接權限

3. **編碼問題**
   - 確保終端支援 UTF-8
   - 檢查 Python 環境的編碼設定
   - 驗證資料庫的中文資料編碼

4. **向量化依賴問題**
   - 缺少 sentence-transformers: `pip install sentence-transformers`
   - 缺少 chromadb: `pip install chromadb`
   - 缺少 numpy: `pip install numpy`
   - 系統會自動回退到簡化版實現

### 依賴問題
```bash
# 如果缺少 requests 套件
pip install requests

# 如果缺少向量化相關套件
pip install sentence-transformers chromadb numpy

# 如果缺少 paramiko 套件  
pip install paramiko

# 或者一次安裝所有依賴
pip install -r tests/test_dify_integration/requirements.txt
```

## 🔄 整合建議

1. **環境變數配置**
   - 將 API 金鑰移至環境變數
   - 使用配置檔案管理不同環境的設定

2. **錯誤處理增強**
   - 實施重試機制
   - 添加更詳細的錯誤日誌
   - 設定超時和限流

3. **效能優化**
   - 實施連接池
   - 批量處理請求
   - 快取重複查詢

4. **向量化優化**
   - 選擇合適的嵌入模型
   - 調整向量維度和相似度閾值
   - 實施向量資料的持久化存儲
   - 使用更高效的向量資料庫（如 Pinecone、Weaviate）

## 📚 相關文件

- [DeepSeek 測試文件](../test_ssh_communication/)
- [主要 README](../../README.md)
- [API 整合指南](../../docs/guide/api-integration.md)

---

**建立時間**: 2025-09-09  
**測試平台**: Dify AI Platform  
**相依性**: requests, paramiko, sqlite3