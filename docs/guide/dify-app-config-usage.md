# Dify App Config 使用指南

這個指南說明如何使用專案中的 Dify 應用配置管理系統。

## 📁 配置文件位置

主要配置文件：
- `/library/config/dify_app_configs.py` - Dify 應用配置管理
- `/library/config/dify_config.py` - 基礎 Dify 配置管理

## 🔧 可用的應用配置

### 1. Protocol Known Issue System
- **應用名稱**：Protocol Known Issue System
- **工作室**：Protocol_known_issue_system
- **用途**：查詢 Know Issue 知識庫
- **功能**：知識庫查詢、員工資訊、Know Issue 管理

## 🚀 使用方法

### 方法 1：獲取配置字典
```python
from library.config.dify_app_configs import get_protocol_known_issue_config

# 獲取完整配置
config = get_protocol_known_issue_config()

# 配置內容包含：
# {
#     'api_url': 'http://10.10.172.5/v1/chat-messages',
#     'api_key': 'app-Sql11xracJ71PtZThNJ4ZQQW',
#     'base_url': 'http://10.10.172.5',
#     'app_name': 'Protocol Known Issue System',
#     'workspace': 'Protocol_known_issue_system',
#     'timeout': 60,
#     'response_mode': 'blocking',
#     ...
# }

# 使用配置
print(f"API URL: {config['api_url']}")
print(f"應用名稱: {config['app_name']}")
```

### 方法 2：直接創建客戶端（推薦）
```python
from library.config.dify_app_configs import create_protocol_chat_client

# 直接創建配置好的客戶端
client = create_protocol_chat_client()

# 測試連接
if client.test_connection():
    print("✅ 連接成功")
    
    # 發送聊天請求
    result = client.chat("ULINK 相關問題")
    if result['success']:
        print(f"回應: {result['answer']}")
```

### 方法 3：使用配置類別
```python
from library.config.dify_app_configs import DifyAppConfigs

# 獲取配置
config = DifyAppConfigs.get_protocol_known_issue_config()

# 創建客戶端
client = DifyAppConfigs.create_protocol_chat_client()

# 驗證配置
is_valid = DifyAppConfigs.validate_config('protocol_known_issue_system')
```

## 🌍 環境變數支援

可以透過環境變數覆蓋配置：

```bash
# 設定環境變數
export DIFY_PROTOCOL_API_URL="http://new-dify-server/v1/chat-messages"
export DIFY_PROTOCOL_API_KEY="app-NewApiKey123"
export DIFY_PROTOCOL_BASE_URL="http://new-dify-server"
export DIFY_PROTOCOL_TIMEOUT=120

# 然後正常使用配置，會自動使用環境變數的值
```

支援的環境變數：
- `DIFY_PROTOCOL_API_URL` - Chat API 端點 URL
- `DIFY_PROTOCOL_API_KEY` - API Key (app-開頭)
- `DIFY_PROTOCOL_BASE_URL` - Dify 基礎 URL
- `DIFY_PROTOCOL_TIMEOUT` - 請求超時時間（秒）

## 🧪 在測試腳本中使用

完整的測試腳本範例：

```python
#!/usr/bin/env python3
import sys
import os

# 添加 library 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

# 導入必要模組
from library.dify_integration.chat_client import DifyChatClient
from library.dify_integration.chat_testing import DifyChatTester
from library.ai_utils.test_analyzer import TestAnalyzer
from library.config.dify_app_configs import (
    get_protocol_known_issue_config, 
    create_protocol_chat_client
)

def main():
    # 方法 1: 獲取配置資訊
    config = get_protocol_known_issue_config()
    print(f"🔗 API 端點: {config['api_url']}")
    print(f"📱 應用名稱: {config['app_name']}")
    print(f"🏢 工作室: {config['workspace']}")
    
    # 方法 2: 直接創建客戶端（推薦）
    client = create_protocol_chat_client()
    
    # 測試連接
    if not client.test_connection():
        print("❌ 連接失敗")
        return
    
    # 使用客戶端進行聊天
    result = client.chat("ULINK")
    if result['success']:
        print(f"✅ 回應: {result['answer'][:100]}...")
    
    # 使用測試工具
    tester = DifyChatTester(client)
    test_results = tester.batch_test(["ULINK", "測試問題"])
    
    # 分析結果
    analyzer = TestAnalyzer()
    analyzer.add_results(test_results, "Know Issue 測試")
    analyzer.print_summary_report()

if __name__ == "__main__":
    main()
```

## ⚠️ 重要注意事項

1. **路徑設定**：確保正確設定 library 路徑
   ```python
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
   ```

2. **配置驗證**：使用前可以驗證配置
   ```python
   from library.config.dify_app_configs import validate_protocol_config
   
   try:
       is_valid = validate_protocol_config()
       print("✅ 配置有效")
   except ValueError as e:
       print(f"❌ 配置錯誤: {e}")
   ```

3. **錯誤處理**：記得處理連接和 API 調用錯誤
   ```python
   if not client.test_connection():
       print("❌ API 連接失敗，請檢查配置")
       return
   ```

## 🔄 更新配置

如果需要更新 API Key 或其他配置：

1. **方法 1**：修改配置文件
   編輯 `/library/config/dify_app_configs.py`

2. **方法 2**：使用環境變數（推薦）
   ```bash
   export DIFY_PROTOCOL_API_KEY="app-NewApiKey"
   ```

3. **方法 3**：程式中動態設定
   ```python
   # 創建自定義配置的客戶端
   from library.dify_integration.chat_client import create_chat_client
   
   client = create_chat_client(
       api_url="http://custom-server/v1/chat-messages",
       api_key="app-CustomKey",
       base_url="http://custom-server"
   )
   ```

## 📊 配置資訊摘要

當前 Protocol Known Issue System 配置：
- **API URL**: `http://10.10.172.5/v1/chat-messages`
- **API Key**: `app-Sql11xracJ71PtZThNJ4ZQQW`
- **Base URL**: `http://10.10.172.5`
- **Timeout**: 60 秒
- **知識庫**: Know Issue Knowledge Base
- **功能**: ULINK 查詢、Know Issue 管理

## 🎯 快速開始模板

```python
# 最簡單的使用方式
from library.config.dify_app_configs import create_protocol_chat_client

# 創建客戶端並使用
client = create_protocol_chat_client()
result = client.chat("您的問題")
print(result['answer'])
```

這就是完整的 Dify App Config 使用指南！