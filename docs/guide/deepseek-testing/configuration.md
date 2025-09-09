# ⚙️ DeepSeek AI 測試配置說明

本文件詳細說明 DeepSeek AI 測試系統的配置選項和自定義設定。

## 🔧 基本配置

### SSH 連接配置
```python
# 連接參數
SSH_CONFIG = {
    "host": "10.10.172.5",       # DeepSeek AI 服務器 IP
    "username": "svd",           # SSH 用戶名
    "password": "1234",          # SSH 密碼
    "port": 22,                  # SSH 端口 (預設)
    "timeout": 10                # 連接超時 (秒)
}
```

### Ollama 模型配置
```python
# 模型參數
OLLAMA_CONFIG = {
    "model_name": "deepseek-r1:14b",    # 使用的模型
    "command_timeout": 30,              # 命令執行超時 (秒)
    "stream": False,                    # 是否使用串流回應
    "temperature": 0.7,                 # 回應創造性 (0-1)
    "max_tokens": 1000                  # 最大回應長度
}
```

## 🎯 測試配置

### 英文測試問題配置
```python
ENGLISH_QUESTIONS = [
    {
        "question": "Hello",
        "category": "greeting",
        "expected_response_time": 5,    # 預期回應時間 (秒)
        "min_response_length": 10       # 最小回應長度
    },
    {
        "question": "What is your name?",
        "category": "identity",
        "expected_response_time": 10,
        "min_response_length": 20
    },
    {
        "question": "Can you analyze data?",
        "category": "capability",
        "expected_response_time": 15,
        "min_response_length": 30
    },
    {
        "question": "Explain machine learning in simple terms",
        "category": "explanation",
        "expected_response_time": 30,
        "min_response_length": 100
    }
]
```

### 中文測試配置
```python
CHINESE_TESTS = {
    "method1": {
        "question": "Please introduce yourself in Traditional Chinese",
        "description": "英文指令要求中文回應",
        "expected_chinese_chars": True
    },
    "method2": {
        "question": "你好，請自我介紹",
        "description": "直接中文問題",
        "encoding": "utf-8"
    }
}
```

## 🔐 安全配置

### 環境變數配置
建議使用環境變數管理敏感資訊：

```bash
# .env 檔案 (不要提交到版本控制)
DEEPSEEK_HOST=10.10.172.5
DEEPSEEK_USER=svd
DEEPSEEK_PASS=1234
DEEPSEEK_MODEL=deepseek-r1:14b
```

```python
# 在 Python 中讀取環境變數
import os
from dotenv import load_dotenv

load_dotenv()

SSH_CONFIG = {
    "host": os.getenv('DEEPSEEK_HOST', '10.10.172.5'),
    "username": os.getenv('DEEPSEEK_USER', 'svd'),
    "password": os.getenv('DEEPSEEK_PASS', '1234'),
    "timeout": int(os.getenv('SSH_TIMEOUT', '10'))
}
```

### SSH 金鑰認證配置
```python
# 使用 SSH 金鑰替代密碼
import paramiko

def ssh_key_connect():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    # 使用私鑰檔案
    private_key = paramiko.RSAKey.from_private_key_file('/path/to/private_key')
    
    ssh.connect(
        hostname="10.10.172.5",
        username="svd",
        pkey=private_key,
        timeout=10
    )
    
    return ssh
```

## 📊 日誌配置

### 基本日誌設定
```python
import logging
from datetime import datetime

# 日誌配置
LOG_CONFIG = {
    "level": logging.INFO,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "filename": f"deepseek_test_{datetime.now().strftime('%Y%m%d')}.log",
    "filemode": "a",
    "encoding": "utf-8"
}

# 設定日誌
logging.basicConfig(**LOG_CONFIG)
logger = logging.getLogger("DeepSeekTest")

# 同時輸出到控制台
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
```

### 結構化日誌配置
```python
import json
import logging

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加額外資訊
        if hasattr(record, 'test_type'):
            log_entry['test_type'] = record.test_type
        if hasattr(record, 'response_time'):
            log_entry['response_time'] = record.response_time
        if hasattr(record, 'success'):
            log_entry['success'] = record.success
            
        return json.dumps(log_entry, ensure_ascii=False)

# 使用 JSON 格式日誌
json_handler = logging.FileHandler('deepseek_test.json', encoding='utf-8')
json_handler.setFormatter(JSONFormatter())
logger.addHandler(json_handler)
```

## ⚡ 效能配置

### 超時設定
```python
TIMEOUT_CONFIG = {
    "ssh_connect": 10,          # SSH 連接超時
    "command_execute": 30,      # 命令執行超時
    "simple_question": 15,      # 簡單問題超時
    "complex_question": 60,     # 複雜問題超時
    "batch_test_interval": 1    # 批量測試間隔 (秒)
}
```

### 重試配置
```python
RETRY_CONFIG = {
    "max_retries": 3,           # 最大重試次數
    "retry_delay": 2,           # 重試間隔 (秒)
    "backoff_factor": 2,        # 退避係數
    "retry_on_errors": [        # 需要重試的錯誤類型
        "Connection refused",
        "timeout",
        "Network is unreachable"
    ]
}

import time
import random

def retry_on_failure(func, max_retries=3, delay=2, backoff_factor=2):
    """重試裝飾器"""
    def wrapper(*args, **kwargs):
        retries = 0
        while retries < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                retries += 1
                if retries >= max_retries:
                    raise e
                
                wait_time = delay * (backoff_factor ** (retries - 1))
                jitter = random.uniform(0, 0.1) * wait_time  # 添加隨機抖動
                
                logger.warning(f"嘗試 {retries}/{max_retries} 失敗: {e}")
                logger.info(f"等待 {wait_time + jitter:.2f} 秒後重試...")
                
                time.sleep(wait_time + jitter)
        
        return None
    return wrapper
```

## 📈 監控配置

### 效能指標配置
```python
PERFORMANCE_METRICS = {
    "response_time_thresholds": {
        "excellent": 5,      # 優秀: < 5秒
        "good": 15,          # 良好: 5-15秒
        "acceptable": 30,    # 可接受: 15-30秒
        "poor": 60           # 需優化: > 30秒
    },
    "success_rate_thresholds": {
        "excellent": 99,     # 優秀: >= 99%
        "good": 95,          # 良好: 95-99%
        "acceptable": 90,    # 可接受: 90-95%
        "poor": 80           # 需改善: < 90%
    },
    "alert_conditions": {
        "consecutive_failures": 3,       # 連續失敗次數警告
        "response_time_spike": 60,       # 回應時間異常 (秒)
        "success_rate_drop": 85          # 成功率下降警告 (%)
    }
}
```

### 報告配置
```python
REPORT_CONFIG = {
    "output_formats": ["json", "html", "csv"],
    "report_frequency": "daily",        # daily, weekly, monthly
    "include_charts": True,
    "send_email": False,
    "email_recipients": ["admin@example.com"],
    "retention_days": 30                # 報告保留天數
}
```

## 🔄 自動化配置

### 定時測試配置
```python
# 使用 crontab 設定定時測試
CRON_CONFIG = """
# 每小時執行基本測試
0 * * * * cd /home/user/codes/ai-platform-web && source venv/bin/activate && python tests/test_ssh_communication/deepseek_ssh_test.py >> logs/hourly.log 2>&1

# 每日執行完整測試
0 2 * * * cd /home/user/codes/ai-platform-web && source venv/bin/activate && python tests/comprehensive_test.py >> logs/daily.log 2>&1

# 每週執行效能測試
0 3 * * 0 cd /home/user/codes/ai-platform-web && source venv/bin/activate && python tests/performance_test.py >> logs/weekly.log 2>&1
"""
```

### CI/CD 整合配置
```yaml
# .github/workflows/deepseek-test.yml
name: DeepSeek AI Test

on:
  schedule:
    - cron: '0 */4 * * *'  # 每 4 小時執行一次
  workflow_dispatch:        # 手動觸發

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m venv venv
          source venv/bin/activate
          pip install -r requirements.txt
      
      - name: Run DeepSeek Tests
        env:
          DEEPSEEK_HOST: ${{ secrets.DEEPSEEK_HOST }}
          DEEPSEEK_USER: ${{ secrets.DEEPSEEK_USER }}
          DEEPSEEK_PASS: ${{ secrets.DEEPSEEK_PASS }}
        run: |
          source venv/bin/activate
          python tests/test_ssh_communication/deepseek_ssh_test.py
      
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: logs/
```

## 🎛️ 自定義配置範例

### 創建配置檔案
```python
# config/deepseek_config.py
import os
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class SSHConfig:
    host: str = "10.10.172.5"
    username: str = "svd"
    password: str = "1234"
    port: int = 22
    timeout: int = 10

@dataclass
class OllamaConfig:
    model_name: str = "deepseek-r1:14b"
    command_timeout: int = 30
    temperature: float = 0.7
    max_tokens: int = 1000

@dataclass
class TestConfig:
    english_questions: List[str] = None
    chinese_questions: List[str] = None
    batch_size: int = 1
    test_interval: float = 1.0
    max_retries: int = 3

@dataclass
class DeepSeekTestConfig:
    ssh: SSHConfig = SSHConfig()
    ollama: OllamaConfig = OllamaConfig()
    test: TestConfig = TestConfig()
    
    @classmethod
    def from_env(cls):
        """從環境變數載入配置"""
        ssh_config = SSHConfig(
            host=os.getenv('DEEPSEEK_HOST', '10.10.172.5'),
            username=os.getenv('DEEPSEEK_USER', 'svd'),
            password=os.getenv('DEEPSEEK_PASS', '1234'),
            timeout=int(os.getenv('SSH_TIMEOUT', '10'))
        )
        
        ollama_config = OllamaConfig(
            model_name=os.getenv('DEEPSEEK_MODEL', 'deepseek-r1:14b'),
            command_timeout=int(os.getenv('COMMAND_TIMEOUT', '30'))
        )
        
        test_config = TestConfig(
            max_retries=int(os.getenv('MAX_RETRIES', '3'))
        )
        
        return cls(ssh=ssh_config, ollama=ollama_config, test=test_config)
    
    def to_dict(self) -> Dict[str, Any]:
        """轉換為字典格式"""
        return {
            'ssh': self.ssh.__dict__,
            'ollama': self.ollama.__dict__,
            'test': self.test.__dict__
        }

# 使用配置
config = DeepSeekTestConfig.from_env()
```

### 配置驗證
```python
def validate_config(config: DeepSeekTestConfig) -> List[str]:
    """驗證配置有效性"""
    errors = []
    
    # 驗證 SSH 配置
    if not config.ssh.host:
        errors.append("SSH host 不能為空")
    
    if not config.ssh.username:
        errors.append("SSH username 不能為空")
    
    if config.ssh.timeout <= 0:
        errors.append("SSH timeout 必須大於 0")
    
    # 驗證 Ollama 配置
    if not config.ollama.model_name:
        errors.append("Ollama model name 不能為空")
    
    if config.ollama.command_timeout <= 0:
        errors.append("Command timeout 必須大於 0")
    
    # 驗證測試配置
    if config.test.max_retries < 0:
        errors.append("Max retries 不能小於 0")
    
    return errors

# 使用驗證
config = DeepSeekTestConfig.from_env()
validation_errors = validate_config(config)

if validation_errors:
    print("❌ 配置驗證失敗:")
    for error in validation_errors:
        print(f"  - {error}")
    exit(1)
else:
    print("✅ 配置驗證通過")
```

## 📚 相關文件

- [SSH 連線測試指南](ssh-connection-guide.md)
- [故障排除指南](troubleshooting.md)
- [測試範例](examples/)
- [主要 README](README.md)

---

**建立時間**: 2025-09-09  
**配置版本**: v1.0  
**相容性**: Python 3.8+, paramiko 4.0+