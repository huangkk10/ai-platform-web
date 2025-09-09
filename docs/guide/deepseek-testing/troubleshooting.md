# 🛠️ DeepSeek AI 測試故障排除指南

本指南提供 DeepSeek AI SSH 連線測試中常見問題的診斷和解決方案。

## 🔍 問題診斷流程

### 1. 連接層面問題

#### ❌ SSH 連接失敗
```
❌ 測試失敗: [Errno 111] Connection refused
❌ 測試失敗: No route to host
❌ 測試失敗: Network is unreachable
```

**診斷步驟**：
```bash
# 1. 檢查網路連通性
ping 10.10.172.5

# 2. 檢查 SSH 服務是否運行
nmap -p 22 10.10.172.5

# 3. 測試手動 SSH 連接
ssh svd@10.10.172.5

# 4. 檢查防火牆設定
sudo ufw status
```

**解決方案**：
- 確認目標服務器運行中
- 檢查網路設定和 DNS 解析
- 驗證防火牆規則
- 確認 SSH 服務狀態

#### ❌ 認證失敗
```
❌ 測試失敗: Authentication failed
❌ 測試失敗: Invalid username or password
```

**診斷步驟**：
```bash
# 手動測試認證
ssh svd@10.10.172.5

# 檢查用戶是否存在
ssh-keyscan 10.10.172.5
```

**解決方案**：
- 確認用戶名和密碼正確
- 檢查帳戶是否被鎖定
- 驗證 SSH 配置是否允許密碼登入

#### ❌ 連接超時
```
❌ 測試失敗: timeout during negotiation
❌ 測試失敗: Socket is closed
```

**診斷和解決**：
```python
# 增加連接超時時間
ssh.connect(
    "10.10.172.5", 
    username="svd", 
    password="1234", 
    timeout=30  # 從 10 增加到 30 秒
)
```

### 2. DeepSeek AI 服務問題

#### ❌ Ollama 服務未運行
```
❌ 無回應
❌ 測試失敗: command not found: ollama
```

**診斷步驟**：
```bash
# SSH 登入後檢查 Ollama 狀態
ssh svd@10.10.172.5

# 檢查服務狀態
systemctl status ollama
ps aux | grep ollama

# 檢查 Ollama 是否在 PATH 中
which ollama
echo $PATH
```

**解決方案**：
```bash
# 啟動 Ollama 服務
sudo systemctl start ollama
sudo systemctl enable ollama

# 如果 Ollama 未安裝
curl -fsSL https://ollama.ai/install.sh | sh

# 手動啟動 Ollama
ollama serve &
```

#### ❌ 模型未載入
```
❌ 測試失敗: model 'deepseek-r1:14b' not found
```

**診斷和解決**：
```bash
# 檢查已安裝的模型
ollama list

# 下載 DeepSeek 模型
ollama pull deepseek-r1:14b

# 測試模型是否正常工作
echo "hello" | ollama run deepseek-r1:14b
```

### 3. Python 環境問題

#### ❌ 模組導入失敗
```
❌ ImportError: No module named 'paramiko'
❌ ModuleNotFoundError: No module named 'paramiko'
```

**診斷步驟**：
```bash
# 檢查是否在虛擬環境中
echo $VIRTUAL_ENV

# 檢查已安裝的套件
pip list | grep paramiko
```

**解決方案**：
```bash
# 啟動虛擬環境
cd /home/user/codes/ai-platform-web
source venv/bin/activate

# 安裝依賴套件
pip install paramiko

# 或使用 requirements.txt
pip install -r requirements.txt
```

#### ❌ Python 版本不相容
```
❌ SyntaxError: invalid syntax
❌ AttributeError: module has no attribute
```

**診斷和解決**：
```bash
# 檢查 Python 版本
python --version
python3 --version

# 確保使用 Python 3.8+
which python3
python3 tests/test_ssh_communication/deepseek_ssh_test.py
```

### 4. 編碼問題

#### ❌ 中文亂碼
```
🤖 回應: ������������
```

**診斷步驟**：
```python
# 檢查系統編碼
import locale
print(locale.getpreferredencoding())

# 檢查 SSH 終端編碼
ssh svd@10.10.172.5 "echo $LANG"
```

**解決方案**：
```python
# 強制使用 UTF-8 解碼
response = stdout.read().decode('utf-8', errors='replace')

# 或使用 UTF-8 編碼發送命令
command = f'LANG=en_US.UTF-8 echo "{question}" | ollama run deepseek-r1:14b --'
```

#### ❌ 特殊字符問題
```python
# 轉義特殊字符
import shlex
safe_question = shlex.quote(question)
command = f'echo {safe_question} | ollama run deepseek-r1:14b --'
```

### 5. 效能問題

#### ⚠️ 回應時間過長
```
🤖 DeepSeek 回應 (耗時 120.5s):
```

**診斷步驟**：
```bash
# 檢查服務器負載
ssh svd@10.10.172.5 "top -bn1 | head -10"

# 檢查記憶體使用
ssh svd@10.10.172.5 "free -h"

# 檢查 GPU 使用 (如果有)
ssh svd@10.10.172.5 "nvidia-smi"
```

**解決方案**：
- 簡化測試問題
- 增加命令超時時間
- 檢查服務器資源使用
- 考慮使用更小的模型

#### ⚠️ 記憶體不足
```bash
# 檢查模型大小和可用記憶體
ollama show deepseek-r1:14b
free -h
```

## 🧪 診斷工具腳本

### 快速診斷腳本
```python
#!/usr/bin/env python3
"""
DeepSeek AI 快速診斷工具
"""
import paramiko
import subprocess
import time

def network_test():
    """網路連通性測試"""
    print("🌐 網路連通性測試")
    try:
        result = subprocess.run(['ping', '-c', '3', '10.10.172.5'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ 網路連通正常")
            return True
        else:
            print("❌ 網路連通失敗")
            return False
    except Exception as e:
        print(f"❌ 網路測試異常: {e}")
        return False

def ssh_test():
    """SSH 連接測試"""
    print("\n🔐 SSH 連接測試")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        start_time = time.time()
        ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
        connect_time = time.time() - start_time
        
        print(f"✅ SSH 連接成功 (耗時: {connect_time:.2f}s)")
        
        # 檢查基本命令
        stdin, stdout, stderr = ssh.exec_command("echo 'SSH 測試'")
        response = stdout.read().decode('utf-8').strip()
        print(f"✅ 命令執行正常: {response}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ SSH 連接失敗: {e}")
        return False

def ollama_test():
    """Ollama 服務測試"""
    print("\n🤖 Ollama 服務測試")
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
        
        # 檢查 Ollama 是否可用
        stdin, stdout, stderr = ssh.exec_command("which ollama")
        ollama_path = stdout.read().decode('utf-8').strip()
        
        if ollama_path:
            print(f"✅ Ollama 路徑: {ollama_path}")
        else:
            print("❌ 找不到 Ollama")
            ssh.close()
            return False
        
        # 檢查模型列表
        stdin, stdout, stderr = ssh.exec_command("ollama list")
        models = stdout.read().decode('utf-8')
        print(f"📋 可用模型:\n{models}")
        
        # 測試簡單回應
        stdin, stdout, stderr = ssh.exec_command('echo "test" | ollama run deepseek-r1:14b --', timeout=30)
        response = stdout.read().decode('utf-8')
        
        if response.strip():
            print("✅ DeepSeek 模型回應正常")
        else:
            print("❌ DeepSeek 模型無回應")
            ssh.close()
            return False
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ Ollama 測試失敗: {e}")
        return False

def main():
    """主診斷流程"""
    print("🔍 DeepSeek AI 診斷工具")
    print("=" * 40)
    
    tests = [
        ("網路連通性", network_test),
        ("SSH 連接", ssh_test),
        ("Ollama 服務", ollama_test)
    ]
    
    results = []
    for test_name, test_func in tests:
        result = test_func()
        results.append((test_name, result))
    
    print("\n📊 診斷結果總結")
    print("=" * 30)
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    if all_passed:
        print("\n🎉 所有測試通過！DeepSeek AI 服務正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查上述錯誤訊息")

if __name__ == "__main__":
    main()
```

### 效能監控腳本
```python
#!/usr/bin/env python3
"""
DeepSeek AI 效能監控工具
"""
import paramiko
import time
import json
from datetime import datetime

def performance_monitor(duration_minutes=10):
    """效能監控"""
    print(f"📈 開始 {duration_minutes} 分鐘效能監控")
    
    results = []
    end_time = time.time() + (duration_minutes * 60)
    
    while time.time() < end_time:
        try:
            start_time = time.time()
            
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
            
            # 執行簡單測試
            stdin, stdout, stderr = ssh.exec_command('echo "Hello" | ollama run deepseek-r1:14b --', timeout=30)
            response = stdout.read().decode('utf-8')
            
            elapsed = time.time() - start_time
            success = bool(response.strip())
            
            result = {
                "timestamp": datetime.now().isoformat(),
                "response_time": elapsed,
                "success": success,
                "response_length": len(response) if success else 0
            }
            
            results.append(result)
            status = "✅" if success else "❌"
            print(f"{status} {datetime.now().strftime('%H:%M:%S')} - 回應時間: {elapsed:.2f}s")
            
            ssh.close()
            
        except Exception as e:
            result = {
                "timestamp": datetime.now().isoformat(),
                "response_time": 0,
                "success": False,
                "error": str(e)
            }
            results.append(result)
            print(f"❌ {datetime.now().strftime('%H:%M:%S')} - 錯誤: {e}")
        
        time.sleep(30)  # 每 30 秒測試一次
    
    # 產生報告
    generate_performance_report(results)

def generate_performance_report(results):
    """產生效能報告"""
    if not results:
        print("❌ 無測試資料")
        return
    
    successful_tests = [r for r in results if r['success']]
    total_tests = len(results)
    success_rate = len(successful_tests) / total_tests * 100
    
    if successful_tests:
        response_times = [r['response_time'] for r in successful_tests]
        avg_response_time = sum(response_times) / len(response_times)
        min_response_time = min(response_times)
        max_response_time = max(response_times)
    else:
        avg_response_time = min_response_time = max_response_time = 0
    
    report = {
        "summary": {
            "total_tests": total_tests,
            "successful_tests": len(successful_tests),
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time
        },
        "details": results
    }
    
    # 輸出報告
    print("\n📊 效能測試報告")
    print("=" * 40)
    print(f"總測試次數: {total_tests}")
    print(f"成功次數: {len(successful_tests)}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均回應時間: {avg_response_time:.2f}s")
    print(f"最快回應時間: {min_response_time:.2f}s")
    print(f"最慢回應時間: {max_response_time:.2f}s")
    
    # 儲存詳細報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"deepseek_performance_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細報告已儲存至: {filename}")

if __name__ == "__main__":
    performance_monitor(5)  # 5 分鐘測試
```

## 📞 獲取協助

### 自助檢查清單
1. ✅ 虛擬環境已啟動
2. ✅ 網路連接正常
3. ✅ SSH 認證成功
4. ✅ Ollama 服務運行
5. ✅ DeepSeek 模型可用
6. ✅ Python 依賴完整

### 聯絡支援
如果問題仍未解決：
1. 執行診斷工具腳本
2. 收集錯誤日誌和診斷結果
3. 查看相關文件：
   - [SSH 連線指南](ssh-connection-guide.md)
   - [配置說明](configuration.md)
   - [測試範例](examples/)

---

**建立時間**: 2025-09-09  
**適用版本**: deepseek_ssh_test.py v1.0