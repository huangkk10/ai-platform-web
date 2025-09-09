# 🔗 DeepSeek AI SSH 連線測試指南

本指南詳細說明如何透過 SSH 連線測試 DeepSeek AI 服務，基於 `tests/test_ssh_communication/deepseek_ssh_test.py` 測試腳本。

## 🎯 測試目標

驗證以下功能：
- SSH 連接穩定性
- DeepSeek AI 模型回應能力
- 中英文對話支援
- 系統整體效能

## 🛠️ 環境要求

### 系統需求
- Python 3.10+
- 虛擬環境 (venv)
- 網路連接到 10.10.172.5

### 依賴套件
```bash
pip install paramiko>=4.0.0
```

## 📋 測試腳本解析

### 主要功能模組

#### 1. SSH 連接配置
```python
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
```

**重要參數說明**：
- `host`: 10.10.172.5 (DeepSeek AI 服務器)
- `username`: svd (服務器用戶名)
- `password`: 1234 (連接密碼)
- `timeout`: 10秒 (連接超時時間)

#### 2. 英文測試模組 (`simple_english_test`)

測試問題清單：
```python
questions = [
    "Hello",                                    # 基本問候
    "What is your name?",                      # 身份詢問
    "Can you analyze data?",                   # 能力詢問
    "Explain machine learning in simple terms" # 複雜解釋
]
```

**命令格式**：
```bash
echo "問題內容" | ollama run deepseek-r1:14b --
```

#### 3. 中文編碼測試模組 (`test_chinese_with_different_methods`)

**方法一：英文指令要求中文回應**
```python
question1 = "Please introduce yourself in Traditional Chinese"
```

**方法二：基本功能驗證**
```python
question2 = "hello"  # 確保基本功能正常
```

## 🚀 執行步驟

### 1. 環境準備
```bash
# 進入專案目錄
cd /home/user/codes/ai-platform-web

# 啟動虛擬環境
source venv/bin/activate

# 確認依賴套件
pip list | grep paramiko
```

### 2. 執行測試
```bash
# 完整測試
python tests/test_ssh_communication/deepseek_ssh_test.py

# 或使用相對路徑
cd tests/test_ssh_communication
python deepseek_ssh_test.py
```

### 3. 預期輸出

#### 成功案例
```
🚀 DeepSeek AI 溝通驗證
確認基本功能正常
==================================================
🎯 簡單英文 DeepSeek 測試
========================================
✅ SSH 連接成功

📋 測試 1/4:
💬 問題: Hello
⏳ 等待回應...
🤖 DeepSeek 回應 (耗時 1.2s):
------------------------------
Hello! How can I assist you today? 😊
------------------------------
✅ 成功
```

#### 失敗案例
```
❌ 測試失敗: [Errno 111] Connection refused
❌ 測試失敗: Authentication failed
❌ 無回應
```

## 📊 效能基準

### 回應時間標準
- **優秀**: < 5秒
- **良好**: 5-15秒  
- **可接受**: 15-30秒
- **需優化**: > 30秒

### 成功率標準
- **優秀**: 100%
- **良好**: 95-99%
- **可接受**: 90-94%
- **需檢查**: < 90%

## 🔧 自定義測試

### 添加新的測試問題
```python
# 在 simple_english_test() 函數中修改
questions = [
    "Hello",
    "What is your name?",
    "Can you analyze data?",
    "Explain machine learning in simple terms",
    # 添加您的自定義問題
    "What is the weather like today?",
    "Tell me a joke",
    "Solve this math problem: 2+2*3"
]
```

### 調整測試參數
```python
# SSH 連接參數
ssh.connect(
    "10.10.172.5", 
    username="svd", 
    password="1234", 
    timeout=20  # 增加超時時間
)

# 命令執行參數
stdin, stdout, stderr = ssh.exec_command(
    command, 
    timeout=60  # 增加命令超時時間
)
```

### 添加日誌記錄
```python
import logging

# 配置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deepseek_test.log'),
        logging.StreamHandler()
    ]
)

# 在測試中添加日誌
logging.info(f"測試問題: {question}")
logging.info(f"回應時間: {elapsed:.1f}s")
```

## 🔍 測試結果分析

### 連接狀態檢查
```python
def check_connection_health():
    """檢查連接健康狀態"""
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        start_time = time.time()
        ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
        connect_time = time.time() - start_time
        
        print(f"✅ 連接建立時間: {connect_time:.2f}s")
        
        # 檢查 Ollama 服務狀態
        stdin, stdout, stderr = ssh.exec_command("systemctl is-active ollama")
        service_status = stdout.read().decode('utf-8').strip()
        print(f"📊 Ollama 服務狀態: {service_status}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ 連接檢查失敗: {e}")
        return False
```

### 批量測試
```python
def batch_test(test_count=5):
    """執行批量測試"""
    success_count = 0
    total_time = 0
    
    for i in range(test_count):
        print(f"\n🔄 批量測試 {i+1}/{test_count}")
        
        start_time = time.time()
        try:
            # 執行單次測試
            simple_english_test()
            success_count += 1
            
        except Exception as e:
            print(f"❌ 測試 {i+1} 失敗: {e}")
            
        elapsed = time.time() - start_time
        total_time += elapsed
        print(f"⏱️ 測試 {i+1} 耗時: {elapsed:.1f}s")
    
    # 統計結果
    success_rate = (success_count / test_count) * 100
    avg_time = total_time / test_count
    
    print(f"\n📈 批量測試結果:")
    print(f"成功率: {success_rate:.1f}% ({success_count}/{test_count})")
    print(f"平均耗時: {avg_time:.1f}s")
    print(f"總耗時: {total_time:.1f}s")
```

## 🚨 注意事項

### 安全考量
- **密碼安全**: 避免在程式碼中硬編碼密碼
- **連接限制**: 避免過於頻繁的連接請求
- **資源清理**: 確保 SSH 連接正確關閉

### 最佳實踐
```python
# 使用環境變數管理敏感資訊
import os

HOST = os.getenv('DEEPSEEK_HOST', '10.10.172.5')
USERNAME = os.getenv('DEEPSEEK_USER', 'svd')
PASSWORD = os.getenv('DEEPSEEK_PASS', '1234')

# 使用 context manager 確保資源清理
class SSHConnection:
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.ssh = None
    
    def __enter__(self):
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.ssh.connect(self.host, username=self.username, password=self.password)
        return self.ssh
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.ssh:
            self.ssh.close()

# 使用方式
with SSHConnection(HOST, USERNAME, PASSWORD) as ssh:
    stdin, stdout, stderr = ssh.exec_command('echo "Hello"')
    response = stdout.read().decode('utf-8')
```

## 📚 相關文件

- [故障排除指南](troubleshooting.md)
- [配置說明](configuration.md)
- [效能測試範例](examples/performance-test.md)
- [中文編碼測試](examples/chinese-encoding.md)

---

**建立時間**: 2025-09-09  
**最後更新**: 2025-09-09  
**測試腳本**: `tests/test_ssh_communication/deepseek_ssh_test.py`