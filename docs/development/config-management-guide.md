# AI Platform Web - 配置管理系統

## 概述

本專案已引入統一的配置管理系統，使用 YAML 文件來管理所有配置參數，特別是 AI PC IP 地址等重要設定。

## 配置文件結構

### 主配置文件：`config/settings.yaml`

```yaml
# AI 服務器配置
ai_server:
  ai_pc_ip: "10.10.172.37"

# 其他配置區塊
database:
  # 資料庫相關配置

api:
  # API 相關配置

frontend:
  # 前端相關配置

logging:
  # 日誌相關配置
```

## 使用方法

### 1. Python 代碼中使用

```python
# 方法1: 使用便利函數（推薦）
from config.config_loader import get_ai_pc_ip, get_config

# 獲取 AI PC IP
ip = get_ai_pc_ip()
print(f"AI PC IP: {ip}")

# 獲取其他配置
timeout = get_config('api.timeout', 60)  # 預設值 60
```

```python
# 方法2: 使用配置載入器類
from config.config_loader import ConfigLoader

config = ConfigLoader()
ip = config.get_ai_pc_ip()
full_config = config.get_full_config()
```

### 2. 在測試文件中使用

```python
# 導入測試配置輔助工具
from tests.test_config import get_dify_test_config, get_ai_pc_ip

# 獲取完整的 Dify 測試配置
config = get_dify_test_config()
print(f"API URL: {config['api_url']}")
print(f"Base URL: {config['base_url']}")

# 或直接獲取 IP
ip = get_ai_pc_ip()
```

### 3. 環境變數支持

系統支持使用環境變數覆蓋配置文件中的設定：

```bash
# 設置 AI PC IP
export AI_PC_IP="192.168.1.100"

# 設置其他 Dify 配置
export DIFY_API_KEY="app-YourNewApiKey"
export DIFY_TIMEOUT=120
```

```python
# 在代碼中使用（會自動使用環境變數）
from config.config_loader import get_ai_pc_ip_with_env

ip = get_ai_pc_ip_with_env()  # 會優先使用 AI_PC_IP 環境變數
```

## 配置優先級

配置載入的優先級順序：
1. **環境變數** - 最高優先級
2. **YAML 配置文件** - 中等優先級  
3. **程式預設值** - 最低優先級

## 更新現有代碼

### 舊方式（已淘汰）
```python
# ❌ 舊的硬編碼方式
api_url = 'http://10.10.172.37/v1/chat-messages'
base_url = 'http://10.10.172.37'
```

### 新方式（推薦）
```python
# ✅ 新的配置管理方式
from config.config_loader import get_ai_pc_ip

ip = get_ai_pc_ip()
api_url = f'http://{ip}/v1/chat-messages'
base_url = f'http://{ip}'
```

```python
# ✅ 或使用測試配置工具
from tests.test_config import get_dify_test_config

config = get_dify_test_config()
api_url = config['api_url']
base_url = config['base_url']
```

## Dify 應用配置整合

`library/config/dify_app_configs.py` 已更新為使用新的配置系統：

```python
# 自動使用配置文件中的 IP
from library.config.dify_app_configs import get_protocol_known_issue_config

config = get_protocol_known_issue_config()
# 配置中的 URL 會自動使用 settings.yaml 中的 ai_pc_ip
```

## 檔案位置

```
ai-platform-web/
├── config/
│   ├── settings.yaml          # 主配置文件
│   └── config_loader.py       # 配置載入器
├── tests/
│   └── test_config.py         # 測試配置輔助工具
├── library/config/
│   └── dify_app_configs.py    # Dify 配置（已更新）
└── requirements.txt           # 已添加 PyYAML 依賴
```

## 環境變數列表

支援的環境變數：

### 通用配置
- `AI_PC_IP` - AI PC IP 地址

### Dify 專門配置
- `DIFY_API_KEY` - 預設 API Key
- `DIFY_TIMEOUT` - 請求超時時間
- `DIFY_PROTOCOL_API_KEY` - Protocol Known Issue 系統 API Key
- `DIFY_REPORT_ANALYZER_API_KEY` - Report Analyzer API Key  
- `DIFY_RVT_GUIDE_API_KEY` - RVT Guide API Key

## 注意事項

1. **向後兼容性**: 現有代碼在過渡期間仍可正常運作
2. **預設值**: 如果配置文件不存在或讀取失敗，系統會使用預設值
3. **安全性**: 敏感資訊（如 API Key）建議使用環境變數而不是配置文件
4. **重載**: 配置可以在運行時重新載入，無需重新啟動應用

## 測試配置

執行測試時建議設置適當的環境變數：

```bash
# 測試環境設定
export AI_PC_IP="10.10.172.37"
export DIFY_API_KEY="app-Sql11xracJ71PtZThNJ4ZQQW"

# 運行測試
python tests/test_config.py
```

## 故障排除

如果遇到配置載入問題：

1. 檢查 `config/settings.yaml` 文件是否存在且格式正確
2. 確認 PyYAML 依賴已安裝：`pip install PyYAML==6.0.2`
3. 查看程式輸出中的配置載入訊息
4. 使用環境變數作為備用方案

---

更新日期：2025-09-25
版本：1.0.0