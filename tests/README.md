# 🧪 DeepSeek AI 測試模組

本目錄包含用於測試與遠端 DeepSeek AI (10.10.172.37:11434) 通信的程式。

## 📁 檔案結構

```
tests/
├── test_config.py               # 測試配置檔案
├── test_deepseek_ai.py          # 完整測試程式
├── quick_test.py                # 快速測試程式
├── README.md                   # 本說明檔案
├── test_ssh_communication/     # SSH 通信測試模組
│   └── deepseek_ssh_test.py    # SSH 方式的 DeepSeek 測試
└── test_dify_integration/       # Dify AI 平台整合測試
    ├── test_dify_chunwei.py     # Dify chunwei 應用測試
    └── README.md               # Dify 測試說明文件
```

## 🚀 快速開始

### 方法一：快速測試
```bash
cd /home/user/codes/ai-platform-web/tests
python3 quick_test.py
```

### 方法三：Dify 整合測試
```bash
# 測試 Dify AI 平台整合
cd /home/user/codes/ai-platform-web/tests/test_dify_integration
python3 test_dify_chunwei.py
```

### 方法四：SSH 連接測試
```bash
# 使用 SSH 方式測試 DeepSeek
cd /home/user/codes/ai-platform-web/tests/test_ssh_communication
python3 deepseek_ssh_test.py
```

## 📋 測試內容

### 🔗 DeepSeek AI 連接測試
- 驗證與 DeepSeek AI 服務的網路連接
- 確認 API 端點可用性
- 檢查模型載入狀態

### 🔗 Dify 平台整合測試
- 測試 Dify API 連接和認證
- 驗證 chunwei 應用的問答功能
- 測試 RAG (檢索增強生成) 功能
- 員工資料分析和報告生成

### 💬 對話測試
- **英文對話**：測試英文問答能力
- **中文對話**：測試繁體中文支援
- **程式碼生成**：測試編程相關問題
- **分析推理**：測試複雜分析能力

### 📊 效能測試
- 回應時間測量
- 回應品質評估
- 穩定性驗證
- 平台間效能比較

## ⚙️ 配置說明

### DeepSeek AI 設定
```python
DEEPSEEK_CONFIG = {
    "base_url": "http://10.10.172.37:11434",
    "model": "deepseek-r1:14b",
    "timeout": 30,
    "max_retries": 3
}
```

### 測試問題類型
- `basic`: 基礎問答
- `complex`: 複雜分析
- `coding`: 程式碼相關
- `analysis`: 深度分析

## 📈 測試結果

### 成功指標
- ✅ 連接成功率 > 95%
- ✅ 平均回應時間 < 30秒
- ✅ 中文回應品質良好
- ✅ 無錯誤訊息或異常

### 報告格式
```json
{
  "timestamp": "2025-09-09T...",
  "summary": {
    "total_tests": 8,
    "successful_tests": 8,
    "success_rate": 100.0,
    "avg_response_time": 12.5,
    "avg_score": 85.0
  },
  "details": [...],
  "config": {...}
}
```

## 🛠️ 故障排除

### 常見問題

#### 1. 連接失敗
```
❌ 連接異常: Connection refused
```
**解決方案**:
- 確認 DeepSeek AI 服務正在運行
- 檢查網路連接到 `10.10.172.37:11434`
- 驗證防火牆設定

#### 2. 超時錯誤
```
❌ 請求異常: Read timeout
```
**解決方案**:
- 增加 timeout 設定值
- 檢查 AI 模型載入狀態
- 簡化測試問題

#### 3. HTTP 錯誤
```
❌ 請求失敗，狀態碼: 500
```
**解決方案**:
- 檢查 Ollama 服務狀態
- 確認模型 `deepseek-r1:14b` 已下載
- 查看服務端日誌

### 網路測試
```bash
# 測試基本連接
curl -I http://10.10.172.37:11434

# 測試 API 端點
curl -X POST http://10.10.172.37:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-r1:14b","prompt":"Hello","stream":false}'
```

## 📊 效能基準

基於 `deepseek-use-cases` 專案的實際經驗：

| 指標 | 目標值 | 說明 |
|------|--------|------|
| 連接成功率 | ≥ 95% | 網路穩定性 |
| 平均回應時間 | ≤ 30秒 | 包含 AI 推理時間 |
| 中文支援 | 100% | 繁體中文完整支援 |
| 回應準確性 | ≥ 80% | 基於問題類型評估 |

## 🔄 持續集成

### 自動化測試
```bash
#!/bin/bash
# 每日自動測試腳本
cd /home/user/codes/ai-platform-web/tests
python3 test_deepseek_ai.py > daily_test_$(date +%Y%m%d).log 2>&1
```

### 監控告警
- 成功率低於 90% 時發送告警
- 平均回應時間超過 60秒時告警
- 連續失敗超過 3次時告警

## 🚀 進階使用

### 自定義測試問題
```python
# 在 test_config.py 中添加自定義問題
CUSTOM_QUESTIONS = {
    "domain_specific": {
        "chinese": "解釋容器化技術的優勢",
        "english": "Explain containerization benefits"
    }
}
```

### 批量測試
```python
# 批量執行多次測試
for i in range(10):
    tester = DeepSeekAITester()
    report = tester.run_comprehensive_test()
    print(f"測試 {i+1}: {report['summary']['success_rate']}%")
```

---

**建立時間**: 2025-09-09  
**維護者**: AI Platform Team  
**基於**: deepseek-use-cases 專案成功經驗
