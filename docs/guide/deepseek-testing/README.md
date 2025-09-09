# 🤖 DeepSeek AI 測試指南

本目錄包含 DeepSeek AI 連線測試的完整指南和工具。

## 📁 目錄結構

```
docs/guide/deepseek-testing/
├── README.md                    # 本說明檔案
├── ssh-connection-guide.md      # SSH 連線測試指南
├── troubleshooting.md          # 故障排除指南
├── configuration.md            # 配置說明
└── examples/                   # 測試範例
    ├── basic-test.md           # 基礎測試範例
    ├── chinese-encoding.md     # 中文編碼測試
    └── performance-test.md     # 效能測試
```

## 🎯 快速開始

### 1. 環境準備
```bash
cd /home/user/codes/ai-platform-web
source venv/bin/activate  # 啟動虛擬環境
```

### 2. 執行基本測試
```bash
python tests/test_ssh_communication/deepseek_ssh_test.py
```

### 3. 查看詳細指南
- [SSH 連線測試指南](ssh-connection-guide.md)
- [故障排除指南](troubleshooting.md)
- [配置說明](configuration.md)

## 📊 測試項目

### 🔗 連線測試
- SSH 連接到 DeepSeek AI 服務器
- 驗證 Ollama 服務狀態
- 確認模型可用性

### 💬 功能測試
- 英文對話測試
- 中文編碼測試
- 複雜問題推理測試

### ⚡ 效能測試
- 回應時間測量
- 並發請求測試
- 穩定性驗證

## 🛠️ 工具和腳本

- `tests/test_ssh_communication/deepseek_ssh_test.py` - 主要測試腳本
- `activate_dev.sh` - 開發環境啟動腳本
- `requirements.txt` - Python 依賴管理

## 📈 測試結果分析

### 成功指標
- ✅ SSH 連接成功率 > 95%
- ✅ 平均回應時間 < 30秒
- ✅ 中文回應正常顯示
- ✅ 無異常錯誤

### 警告指標
- ⚠️ 回應時間 > 60秒
- ⚠️ 連接失敗率 > 5%
- ⚠️ 中文編碼異常

### 錯誤指標
- ❌ 無法建立 SSH 連接
- ❌ Ollama 服務未運行
- ❌ 模型加載失敗

## 🔄 持續監控

建議設定定期測試來監控 DeepSeek AI 服務狀態：

```bash
# 每小時執行一次基本測試
0 * * * * cd /home/user/codes/ai-platform-web && source venv/bin/activate && python tests/test_ssh_communication/deepseek_ssh_test.py >> logs/deepseek_hourly.log 2>&1
```

## 📞 支援聯絡

如遇到問題，請參考：
1. [故障排除指南](troubleshooting.md)
2. [配置說明](configuration.md)
3. 檢查服務器狀態：`ssh user@10.10.172.5 "systemctl status ollama"`

---

**最後更新**: 2025-09-09  
**維護者**: AI Platform Team