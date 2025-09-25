# 🧪 基礎測試範例

本文件提供 DeepSeek AI 基礎測試的範例程式碼和最佳實踐。

## 🎯 簡單測試範例

### 單一問題測試
```python
#!/usr/bin/env python3
import paramiko
import time

def single_question_test(question="Hello, how are you?"):
    """測試單一問題"""
    print(f"🧪 測試問題: {question}")
    
    try:
        # 建立 SSH 連接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.37", username="svd", password="1234", timeout=10)
        
        # 執行命令
        command = f'echo "{question}" | ollama run deepseek-r1:14b --'
        start_time = time.time()
        
        stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
        response = stdout.read().decode('utf-8')
        
        elapsed = time.time() - start_time
        
        # 顯示結果
        if response.strip():
            print(f"✅ 回應 (耗時 {elapsed:.1f}s):")
            print("-" * 40)
            print(response)
            print("-" * 40)
        else:
            print("❌ 無回應")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return False

if __name__ == "__main__":
    single_question_test()
```

### 快速連接測試
```python
#!/usr/bin/env python3
import paramiko

def quick_connection_test():
    """快速連接測試"""
    print("⚡ 快速連接測試")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        start_time = time.time()
        ssh.connect("10.10.172.37", username="svd", password="1234", timeout=5)
        connect_time = time.time() - start_time
        
        print(f"✅ 連接成功，耗時: {connect_time:.2f}s")
        
        # 簡單命令測試
        stdin, stdout, stderr = ssh.exec_command("echo 'Connection OK'")
        result = stdout.read().decode('utf-8').strip()
        print(f"✅ 命令測試: {result}")
        
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return False

if __name__ == "__main__":
    quick_connection_test()
```

## 📊 批量測試範例

### 多問題測試
```python
#!/usr/bin/env python3
import paramiko
import time

def multi_question_test():
    """多問題批量測試"""
    questions = [
        "Hello",
        "What is AI?",
        "Tell me a joke",
        "What's the weather like?",
        "Explain quantum computing"
    ]
    
    print(f"📋 開始批量測試 ({len(questions)} 個問題)")
    
    results = []
    ssh = None
    
    try:
        # 建立持久連接
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.37", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接建立")
        
        for i, question in enumerate(questions, 1):
            print(f"\n🧪 測試 {i}/{len(questions)}: {question}")
            
            try:
                command = f'echo "{question}" | ollama run deepseek-r1:14b --'
                start_time = time.time()
                
                stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
                response = stdout.read().decode('utf-8')
                
                elapsed = time.time() - start_time
                success = bool(response.strip())
                
                result = {
                    "question": question,
                    "response": response[:100] + "..." if len(response) > 100 else response,
                    "response_time": elapsed,
                    "success": success
                }
                
                results.append(result)
                
                status = "✅" if success else "❌"
                print(f"{status} 回應時間: {elapsed:.1f}s")
                
                if success:
                    print(f"💬 預覽: {response[:50]}...")
                
                time.sleep(1)  # 避免過於頻繁請求
                
            except Exception as e:
                print(f"❌ 問題 {i} 測試失敗: {e}")
                results.append({
                    "question": question,
                    "response": "",
                    "response_time": 0,
                    "success": False,
                    "error": str(e)
                })
    
    finally:
        if ssh:
            ssh.close()
    
    # 產生統計報告
    generate_summary_report(results)
    return results

def generate_summary_report(results):
    """產生測試統計報告"""
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    successful_times = [r['response_time'] for r in results if r['success']]
    avg_time = sum(successful_times) / len(successful_times) if successful_times else 0
    
    print("\n" + "=" * 50)
    print("📈 測試統計報告")
    print("=" * 50)
    print(f"總測試數: {total_tests}")
    print(f"成功數: {successful_tests}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均回應時間: {avg_time:.2f}s")
    
    if successful_times:
        print(f"最快回應: {min(successful_times):.2f}s")
        print(f"最慢回應: {max(successful_times):.2f}s")
    
    # 顯示失敗的測試
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n❌ 失敗的測試 ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"  - {test['question']}")

if __name__ == "__main__":
    multi_question_test()
```

### 並發測試範例
```python
#!/usr/bin/env python3
import paramiko
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def concurrent_test(max_workers=3):
    """並發測試"""
    questions = [
        "Hello World",
        "What is Python?",
        "Explain machine learning",
        "Tell me about AI",
        "What is the meaning of life?"
    ]
    
    print(f"🔄 並發測試開始 (工作者數: {max_workers})")
    
    results = []
    
    def test_single_question(question, thread_id):
        """單一問題測試函數"""
        try:
            # 每個執行緒建立自己的 SSH 連接
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("10.10.172.37", username="svd", password="1234", timeout=10)
            
            command = f'echo "{question}" | ollama run deepseek-r1:14b --'
            start_time = time.time()
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=45)
            response = stdout.read().decode('utf-8')
            
            elapsed = time.time() - start_time
            ssh.close()
            
            result = {
                "thread_id": thread_id,
                "question": question,
                "response": response[:100] + "..." if len(response) > 100 else response,
                "response_time": elapsed,
                "success": bool(response.strip()),
                "timestamp": time.time()
            }
            
            print(f"✅ 執行緒 {thread_id}: {question} (耗時 {elapsed:.1f}s)")
            return result
            
        except Exception as e:
            print(f"❌ 執行緒 {thread_id}: {question} 失敗 - {e}")
            return {
                "thread_id": thread_id,
                "question": question,
                "response": "",
                "response_time": 0,
                "success": False,
                "error": str(e),
                "timestamp": time.time()
            }
    
    # 使用 ThreadPoolExecutor 進行並發測試
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任務
        future_to_question = {
            executor.submit(test_single_question, question, i): question 
            for i, question in enumerate(questions, 1)
        }
        
        # 收集結果
        for future in as_completed(future_to_question):
            result = future.result()
            results.append(result)
    
    total_time = time.time() - start_time
    
    # 產生並發測試報告
    generate_concurrent_report(results, total_time, max_workers)
    return results

def generate_concurrent_report(results, total_time, max_workers):
    """產生並發測試報告"""
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    successful_times = [r['response_time'] for r in results if r['success']]
    avg_response_time = sum(successful_times) / len(successful_times) if successful_times else 0
    
    print("\n" + "=" * 60)
    print("🔄 並發測試報告")
    print("=" * 60)
    print(f"工作者數量: {max_workers}")
    print(f"總測試數: {total_tests}")
    print(f"成功數: {successful_tests}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"總執行時間: {total_time:.2f}s")
    print(f"平均回應時間: {avg_response_time:.2f}s")
    
    if successful_times:
        print(f"最快回應: {min(successful_times):.2f}s")
        print(f"最慢回應: {max(successful_times):.2f}s")
    
    # 計算理論上的串行執行時間
    theoretical_serial_time = sum(successful_times) if successful_times else 0
    speedup = theoretical_serial_time / total_time if total_time > 0 else 0
    
    print(f"理論串行時間: {theoretical_serial_time:.2f}s")
    print(f"加速比: {speedup:.2f}x")

if __name__ == "__main__":
    concurrent_test(max_workers=2)
```

## 🎯 專項測試範例

### 回應時間測試
```python
#!/usr/bin/env python3
import paramiko
import time
import statistics

def response_time_test(test_question="Hello", iterations=10):
    """回應時間專項測試"""
    print(f"⏱️ 回應時間測試 (問題: '{test_question}', 迭代: {iterations})")
    
    response_times = []
    ssh = None
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.37", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接建立")
        
        for i in range(iterations):
            print(f"🧪 測試 {i+1}/{iterations}")
            
            command = f'echo "{test_question}" | ollama run deepseek-r1:14b --'
            start_time = time.time()
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
            response = stdout.read().decode('utf-8')
            
            elapsed = time.time() - start_time
            
            if response.strip():
                response_times.append(elapsed)
                print(f"  ✅ 回應時間: {elapsed:.2f}s")
            else:
                print(f"  ❌ 無回應")
            
            time.sleep(2)  # 間隔避免過載
    
    finally:
        if ssh:
            ssh.close()
    
    # 統計分析
    if response_times:
        analyze_response_times(response_times, test_question)
    else:
        print("❌ 無有效回應時間數據")
    
    return response_times

def analyze_response_times(times, question):
    """分析回應時間數據"""
    print("\n" + "=" * 50)
    print("📊 回應時間分析")
    print("=" * 50)
    print(f"測試問題: {question}")
    print(f"有效測試次數: {len(times)}")
    print(f"平均時間: {statistics.mean(times):.2f}s")
    print(f"中位數時間: {statistics.median(times):.2f}s")
    print(f"最快時間: {min(times):.2f}s")
    print(f"最慢時間: {max(times):.2f}s")
    
    if len(times) > 1:
        print(f"標準差: {statistics.stdev(times):.2f}s")
        print(f"變異係數: {(statistics.stdev(times) / statistics.mean(times)) * 100:.1f}%")
    
    # 效能分級
    avg_time = statistics.mean(times)
    if avg_time < 5:
        grade = "優秀 🏆"
    elif avg_time < 15:
        grade = "良好 👍"
    elif avg_time < 30:
        grade = "可接受 ⚡"
    else:
        grade = "需優化 ⚠️"
    
    print(f"效能等級: {grade}")

if __name__ == "__main__":
    response_time_test("What is artificial intelligence?", 5)
```

### 穩定性測試
```python
#!/usr/bin/env python3
import paramiko
import time
import random

def stability_test(duration_minutes=10):
    """穩定性測試"""
    print(f"🔄 穩定性測試 (持續時間: {duration_minutes} 分鐘)")
    
    test_questions = [
        "Hello",
        "How are you?",
        "What's your name?",
        "Tell me a fact",
        "What is 2+2?"
    ]
    
    end_time = time.time() + (duration_minutes * 60)
    test_count = 0
    success_count = 0
    failures = []
    
    ssh = None
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.37", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接建立")
        
        while time.time() < end_time:
            test_count += 1
            question = random.choice(test_questions)
            
            try:
                command = f'echo "{question}" | ollama run deepseek-r1:14b --'
                start_time = time.time()
                
                stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
                response = stdout.read().decode('utf-8')
                
                elapsed = time.time() - start_time
                
                if response.strip():
                    success_count += 1
                    status = "✅"
                else:
                    failures.append(f"測試 {test_count}: 無回應")
                    status = "❌"
                
                current_time = time.strftime("%H:%M:%S")
                print(f"{status} [{current_time}] 測試 {test_count}: {question} ({elapsed:.1f}s)")
                
            except Exception as e:
                failures.append(f"測試 {test_count}: {str(e)}")
                print(f"❌ [{time.strftime('%H:%M:%S')}] 測試 {test_count}: 錯誤 - {e}")
            
            # 隨機間隔 (模擬真實使用)
            time.sleep(random.uniform(5, 15))
    
    finally:
        if ssh:
            ssh.close()
    
    # 產生穩定性報告
    generate_stability_report(test_count, success_count, failures, duration_minutes)

def generate_stability_report(total, success, failures, duration):
    """產生穩定性測試報告"""
    success_rate = (success / total) * 100 if total > 0 else 0
    avg_tests_per_minute = total / duration if duration > 0 else 0
    
    print("\n" + "=" * 50)
    print("🔄 穩定性測試報告")
    print("=" * 50)
    print(f"測試持續時間: {duration} 分鐘")
    print(f"總測試次數: {total}")
    print(f"成功次數: {success}")
    print(f"失敗次數: {len(failures)}")
    print(f"成功率: {success_rate:.1f}%")
    print(f"平均測試頻率: {avg_tests_per_minute:.1f} 次/分鐘")
    
    # 穩定性評級
    if success_rate >= 99:
        grade = "極佳 🏆"
    elif success_rate >= 95:
        grade = "優良 👍"
    elif success_rate >= 90:
        grade = "良好 ⚡"
    elif success_rate >= 80:
        grade = "可接受 ⚠️"
    else:
        grade = "需改善 ❌"
    
    print(f"穩定性等級: {grade}")
    
    if failures:
        print(f"\n❌ 失敗記錄 ({len(failures)}):")
        for failure in failures[:5]:  # 只顯示前 5 個失敗
            print(f"  - {failure}")
        if len(failures) > 5:
            print(f"  ... 還有 {len(failures) - 5} 個失敗")

if __name__ == "__main__":
    stability_test(5)  # 5 分鐘穩定性測試
```

## 📚 使用建議

### 最佳實踐
1. **連接管理**: 使用 context manager 確保連接正確關閉
2. **錯誤處理**: 捕獲並記錄詳細的錯誤資訊
3. **超時設定**: 為不同複雜度的問題設定合適的超時時間
4. **測試間隔**: 避免過於頻繁的請求造成服務負載
5. **日誌記錄**: 記錄測試過程和結果以便分析

### 測試策略
- **單一測試**: 驗證基本功能
- **批量測試**: 檢查一致性和穩定性
- **並發測試**: 評估系統負載能力
- **長期測試**: 監控服務穩定性

---

**建立時間**: 2025-09-09  
**範例版本**: v1.0  
**相依檔案**: `tests/test_ssh_communication/deepseek_ssh_test.py`