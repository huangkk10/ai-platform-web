# ⚡ 效能測試範例

本文件提供 DeepSeek AI 效能評估和壓力測試的完整範例。

## 🎯 效能測試目標

### 測試維度
- **回應時間**: 不同問題複雜度的回應時間
- **吞吐量**: 系統處理請求的能力
- **並發能力**: 多使用者同時使用的表現
- **穩定性**: 長時間運行的穩定性
- **資源使用**: 記憶體和 CPU 使用情況

### 效能指標
- 平均回應時間 (Average Response Time)
- 95 百分位回應時間 (95th Percentile)
- 每秒處理請求數 (RPS - Requests Per Second)
- 錯誤率 (Error Rate)
- 資源使用率 (Resource Utilization)

## 🧪 基礎效能測試

### 回應時間基準測試
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek AI 回應時間基準測試
"""
import paramiko
import time
import statistics
import json
from datetime import datetime

class ResponseTimeBenchmark:
    """回應時間基準測試"""
    
    def __init__(self, host="10.10.172.5", username="svd", password="1234"):
        self.host = host
        self.username = username
        self.password = password
        self.ssh = None
        
    def connect(self):
        """建立 SSH 連接"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(self.host, username=self.username, password=self.password, timeout=10)
            return True
        except Exception as e:
            print(f"❌ 連接失敗: {e}")
            return False
    
    def run_benchmark(self):
        """執行基準測試"""
        print("⚡ DeepSeek AI 回應時間基準測試")
        print("=" * 50)
        
        if not self.connect():
            return None
        
        # 不同複雜度的測試問題
        test_categories = {
            "simple": {
                "questions": [
                    "Hello",
                    "Hi there",
                    "Good morning",
                    "How are you?",
                    "What's your name?"
                ],
                "description": "簡單問候",
                "expected_time": 5
            },
            "medium": {
                "questions": [
                    "What is artificial intelligence?",
                    "Explain machine learning",
                    "What is Python programming?",
                    "Tell me about neural networks",
                    "What is data science?"
                ],
                "description": "中等複雜度問題",
                "expected_time": 15
            },
            "complex": {
                "questions": [
                    "Explain the differences between supervised and unsupervised learning in detail",
                    "Describe the architecture and training process of a transformer model",
                    "Compare different optimization algorithms used in deep learning",
                    "Explain the concept of gradient descent and its variants",
                    "Discuss the challenges and solutions in natural language processing"
                ],
                "description": "複雜技術問題",
                "expected_time": 30
            }
        }
        
        all_results = {}
        
        try:
            for category, config in test_categories.items():
                print(f"\n📋 測試類別: {config['description']}")
                print(f"預期回應時間: < {config['expected_time']}秒")
                
                category_results = []
                
                for i, question in enumerate(config['questions'], 1):
                    print(f"\n  🧪 測試 {i}/{len(config['questions'])}: {question[:50]}...")
                    
                    result = self._test_single_question(question)
                    category_results.append(result)
                    
                    status = "✅" if result['success'] else "❌"
                    print(f"  {status} 回應時間: {result['response_time']:.2f}s")
                    
                    time.sleep(1)  # 避免過載
                
                # 分析類別結果
                analysis = self._analyze_category_results(category_results, config)
                all_results[category] = {
                    "config": config,
                    "results": category_results,
                    "analysis": analysis
                }
                
                self._print_category_summary(category, analysis)
        
        finally:
            if self.ssh:
                self.ssh.close()
        
        # 生成完整報告
        self._generate_benchmark_report(all_results)
        return all_results
    
    def _test_single_question(self, question):
        """測試單一問題"""
        try:
            command = f'echo "{question}" | ollama run deepseek-r1:14b --'
            start_time = time.time()
            
            stdin, stdout, stderr = self.ssh.exec_command(command, timeout=60)
            response = stdout.read().decode('utf-8')
            
            elapsed = time.time() - start_time
            success = bool(response.strip())
            
            return {
                "question": question,
                "response_time": elapsed,
                "success": success,
                "response_length": len(response.strip()),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "question": question,
                "response_time": 0,
                "success": False,
                "response_length": 0,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def _analyze_category_results(self, results, config):
        """分析類別結果"""
        successful_results = [r for r in results if r['success']]
        
        if not successful_results:
            return {
                "success_rate": 0,
                "avg_response_time": 0,
                "median_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0,
                "std_deviation": 0,
                "performance_grade": "F"
            }
        
        response_times = [r['response_time'] for r in successful_results]
        
        analysis = {
            "success_rate": len(successful_results) / len(results) * 100,
            "avg_response_time": statistics.mean(response_times),
            "median_response_time": statistics.median(response_times),
            "min_response_time": min(response_times),
            "max_response_time": max(response_times),
            "std_deviation": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "total_tests": len(results),
            "successful_tests": len(successful_results)
        }
        
        # 效能評級
        avg_time = analysis['avg_response_time']
        expected_time = config['expected_time']
        
        if avg_time <= expected_time * 0.5:
            grade = "A+"
        elif avg_time <= expected_time * 0.7:
            grade = "A"
        elif avg_time <= expected_time:
            grade = "B"
        elif avg_time <= expected_time * 1.5:
            grade = "C"
        else:
            grade = "D"
        
        analysis['performance_grade'] = grade
        
        return analysis
    
    def _print_category_summary(self, category, analysis):
        """列印類別摘要"""
        print(f"\n  📊 {category.upper()} 類別摘要:")
        print(f"    成功率: {analysis['success_rate']:.1f}%")
        print(f"    平均回應時間: {analysis['avg_response_time']:.2f}s")
        print(f"    中位數回應時間: {analysis['median_response_time']:.2f}s")
        print(f"    最快/最慢: {analysis['min_response_time']:.2f}s / {analysis['max_response_time']:.2f}s")
        print(f"    效能評級: {analysis['performance_grade']}")
    
    def _generate_benchmark_report(self, all_results):
        """生成基準測試報告"""
        print("\n" + "=" * 60)
        print("📈 回應時間基準測試總報告")
        print("=" * 60)
        
        for category, data in all_results.items():
            analysis = data['analysis']
            config = data['config']
            
            print(f"\n🏷️ {config['description']} ({category.upper()})")
            print(f"  📊 成功率: {analysis['success_rate']:.1f}%")
            print(f"  ⏱️ 平均時間: {analysis['avg_response_time']:.2f}s (預期: <{config['expected_time']}s)")
            print(f"  🏆 效能評級: {analysis['performance_grade']}")
        
        # 儲存詳細報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"response_time_benchmark_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 詳細報告已儲存至: {filename}")

if __name__ == "__main__":
    benchmark = ResponseTimeBenchmark()
    benchmark.run_benchmark()
```

### 壓力測試
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek AI 壓力測試
"""
import paramiko
import time
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import List
import statistics

@dataclass
class StressTestConfig:
    """壓力測試配置"""
    concurrent_users: int = 5          # 並發用戶數
    test_duration_minutes: int = 10    # 測試持續時間(分鐘)
    ramp_up_time_seconds: int = 30     # 升壓時間(秒)
    think_time_seconds: int = 3        # 思考時間(秒)

class StressTestRunner:
    """壓力測試執行器"""
    
    def __init__(self, config: StressTestConfig):
        self.config = config
        self.results_queue = queue.Queue()
        self.stop_event = threading.Event()
        
        # 測試問題池
        self.question_pool = [
            "Hello, how are you?",
            "What is AI?",
            "Explain machine learning",
            "Tell me about Python",
            "What is data science?",
            "How does neural network work?",
            "What is deep learning?",
            "Explain natural language processing",
            "What is computer vision?",
            "Tell me about robotics"
        ]
    
    def run_stress_test(self):
        """執行壓力測試"""
        print("🔥 DeepSeek AI 壓力測試")
        print("=" * 50)
        print(f"並發用戶數: {self.config.concurrent_users}")
        print(f"測試時間: {self.config.test_duration_minutes} 分鐘")
        print(f"升壓時間: {self.config.ramp_up_time_seconds} 秒")
        
        start_time = time.time()
        end_time = start_time + (self.config.test_duration_minutes * 60)
        
        # 啟動監控線程
        monitor_thread = threading.Thread(target=self._monitor_progress, args=(start_time, end_time))
        monitor_thread.daemon = True
        monitor_thread.start()
        
        # 使用 ThreadPoolExecutor 模擬並發用戶
        with ThreadPoolExecutor(max_workers=self.config.concurrent_users) as executor:
            # 提交用戶任務
            futures = []
            for user_id in range(self.config.concurrent_users):
                # 計算每個用戶的啟動延遲 (漸進式升壓)
                delay = (user_id * self.config.ramp_up_time_seconds) / self.config.concurrent_users
                future = executor.submit(self._simulate_user, user_id, start_time + delay, end_time)
                futures.append(future)
            
            # 等待所有用戶完成
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    print(f"✅ 用戶 {user_results['user_id']} 完成: {user_results['total_requests']} 請求")
                except Exception as e:
                    print(f"❌ 用戶執行失敗: {e}")
        
        # 收集和分析結果
        all_results = self._collect_results()
        analysis = self._analyze_stress_test_results(all_results)
        self._generate_stress_test_report(analysis)
        
        return analysis
    
    def _simulate_user(self, user_id, start_delay, end_time):
        """模擬單一用戶行為"""
        # 等待啟動時間
        time.sleep(start_delay - time.time())
        
        user_results = {
            "user_id": user_id,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "response_times": [],
            "errors": []
        }
        
        # 建立 SSH 連接
        ssh = None
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
            
            # 持續發送請求直到測試結束
            while time.time() < end_time and not self.stop_event.is_set():
                request_start = time.time()
                
                try:
                    # 隨機選擇問題
                    import random
                    question = random.choice(self.question_pool)
                    
                    # 發送請求
                    command = f'echo "{question}" | ollama run deepseek-r1:14b --'
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=30)
                    response = stdout.read().decode('utf-8')
                    
                    response_time = time.time() - request_start
                    
                    # 記錄結果
                    result = {
                        "user_id": user_id,
                        "question": question,
                        "response_time": response_time,
                        "success": bool(response.strip()),
                        "response_length": len(response.strip()),
                        "timestamp": time.time()
                    }
                    
                    self.results_queue.put(result)
                    
                    user_results["total_requests"] += 1
                    
                    if result["success"]:
                        user_results["successful_requests"] += 1
                        user_results["response_times"].append(response_time)
                    else:
                        user_results["failed_requests"] += 1
                    
                except Exception as e:
                    user_results["total_requests"] += 1
                    user_results["failed_requests"] += 1
                    user_results["errors"].append(str(e))
                
                # 思考時間
                time.sleep(self.config.think_time_seconds)
        
        except Exception as e:
            print(f"❌ 用戶 {user_id} SSH 連接失敗: {e}")
        
        finally:
            if ssh:
                ssh.close()
        
        return user_results
    
    def _monitor_progress(self, start_time, end_time):
        """監控測試進度"""
        while time.time() < end_time:
            elapsed = time.time() - start_time
            remaining = end_time - time.time()
            progress = (elapsed / (end_time - start_time)) * 100
            
            print(f"\r🔄 測試進度: {progress:.1f}% | 剩餘時間: {remaining/60:.1f}分鐘", end="", flush=True)
            time.sleep(10)
        
        print("\n⏹️ 測試時間結束")
        self.stop_event.set()
    
    def _collect_results(self):
        """收集所有測試結果"""
        results = []
        while not self.results_queue.empty():
            try:
                result = self.results_queue.get_nowait()
                results.append(result)
            except queue.Empty:
                break
        return results
    
    def _analyze_stress_test_results(self, results):
        """分析壓力測試結果"""
        if not results:
            return {"error": "無測試結果"}
        
        successful_results = [r for r in results if r['success']]
        total_requests = len(results)
        successful_requests = len(successful_results)
        
        # 基本統計
        success_rate = (successful_requests / total_requests) * 100 if total_requests > 0 else 0
        
        # 時間統計
        if successful_results:
            response_times = [r['response_time'] for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
            min_response_time = min(response_times)
            max_response_time = max(response_times)
        else:
            avg_response_time = median_response_time = p95_response_time = 0
            min_response_time = max_response_time = 0
        
        # 吞吐量計算
        test_duration = self.config.test_duration_minutes * 60
        rps = successful_requests / test_duration if test_duration > 0 else 0
        
        # 並發效能分析
        user_stats = {}
        for result in results:
            user_id = result['user_id']
            if user_id not in user_stats:
                user_stats[user_id] = {"requests": 0, "successes": 0}
            
            user_stats[user_id]["requests"] += 1
            if result['success']:
                user_stats[user_id]["successes"] += 1
        
        analysis = {
            "test_config": self.config.__dict__,
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": total_requests - successful_requests,
                "success_rate": success_rate,
                "requests_per_second": rps
            },
            "response_time_stats": {
                "average": avg_response_time,
                "median": median_response_time,
                "p95": p95_response_time,
                "minimum": min_response_time,
                "maximum": max_response_time
            },
            "user_statistics": user_stats,
            "detailed_results": results
        }
        
        return analysis
    
    def _generate_stress_test_report(self, analysis):
        """生成壓力測試報告"""
        print("\n" + "=" * 60)
        print("🔥 壓力測試報告")
        print("=" * 60)
        
        summary = analysis['summary']
        response_stats = analysis['response_time_stats']
        
        print(f"📊 測試摘要:")
        print(f"  總請求數: {summary['total_requests']}")
        print(f"  成功請求數: {summary['successful_requests']}")
        print(f"  失敗請求數: {summary['failed_requests']}")
        print(f"  成功率: {summary['success_rate']:.1f}%")
        print(f"  吞吐量: {summary['requests_per_second']:.2f} RPS")
        
        print(f"\n⏱️ 回應時間統計:")
        print(f"  平均時間: {response_stats['average']:.2f}s")
        print(f"  中位數時間: {response_stats['median']:.2f}s")
        print(f"  95百分位: {response_stats['p95']:.2f}s")
        print(f"  最快/最慢: {response_stats['minimum']:.2f}s / {response_stats['maximum']:.2f}s")
        
        print(f"\n👥 用戶統計:")
        for user_id, stats in analysis['user_statistics'].items():
            user_success_rate = (stats['successes'] / stats['requests']) * 100 if stats['requests'] > 0 else 0
            print(f"  用戶 {user_id}: {stats['requests']} 請求, {user_success_rate:.1f}% 成功率")
        
        # 效能評級
        if summary['success_rate'] >= 99 and response_stats['p95'] <= 30:
            grade = "優秀 🏆"
        elif summary['success_rate'] >= 95 and response_stats['p95'] <= 45:
            grade = "良好 👍"
        elif summary['success_rate'] >= 90 and response_stats['p95'] <= 60:
            grade = "可接受 ⚡"
        else:
            grade = "需改善 ⚠️"
        
        print(f"\n🏆 整體效能評級: {grade}")
        
        # 儲存報告
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"stress_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 詳細報告已儲存至: {filename}")

# 使用範例
if __name__ == "__main__":
    # 配置壓力測試
    config = StressTestConfig(
        concurrent_users=3,         # 3個並發用戶
        test_duration_minutes=5,    # 測試5分鐘
        ramp_up_time_seconds=30,    # 30秒升壓
        think_time_seconds=5        # 5秒思考時間
    )
    
    # 執行測試
    runner = StressTestRunner(config)
    results = runner.run_stress_test()
```

### 長期穩定性測試
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek AI 長期穩定性測試
"""
import paramiko
import time
import json
import threading
from datetime import datetime, timedelta
import statistics

class LongTermStabilityTest:
    """長期穩定性測試"""
    
    def __init__(self, test_duration_hours=24, check_interval_minutes=30):
        self.test_duration_hours = test_duration_hours
        self.check_interval_minutes = check_interval_minutes
        self.results = []
        self.stop_event = threading.Event()
        
    def run_stability_test(self):
        """執行長期穩定性測試"""
        print("🔄 DeepSeek AI 長期穩定性測試")
        print("=" * 50)
        print(f"測試時長: {self.test_duration_hours} 小時")
        print(f"檢查間隔: {self.check_interval_minutes} 分鐘")
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=self.test_duration_hours)
        
        print(f"開始時間: {start_time}")
        print(f"預計結束: {end_time}")
        
        check_count = 0
        
        try:
            while datetime.now() < end_time and not self.stop_event.is_set():
                check_count += 1
                current_time = datetime.now()
                elapsed_hours = (current_time - start_time).total_seconds() / 3600
                
                print(f"\n🧪 檢查 #{check_count} (已運行 {elapsed_hours:.1f} 小時)")
                
                # 執行健康檢查
                health_result = self._perform_health_check(check_count)
                self.results.append(health_result)
                
                # 顯示即時結果
                self._print_check_result(health_result)
                
                # 等待下一次檢查
                if not self.stop_event.is_set():
                    time.sleep(self.check_interval_minutes * 60)
        
        except KeyboardInterrupt:
            print("\n⏹️ 收到中斷信號，正在停止測試...")
            self.stop_event.set()
        
        # 生成最終報告
        self._generate_stability_report(start_time, datetime.now())
        
    def _perform_health_check(self, check_number):
        """執行健康檢查"""
        result = {
            "check_number": check_number,
            "timestamp": datetime.now().isoformat(),
            "connection_test": False,
            "response_test": False,
            "performance_test": False,
            "connection_time": 0,
            "response_time": 0,
            "response_quality": 0,
            "errors": []
        }
        
        ssh = None
        
        try:
            # 1. 連接測試
            connect_start = time.time()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("10.10.172.5", username="svd", password="1234", timeout=15)
            result["connection_time"] = time.time() - connect_start
            result["connection_test"] = True
            
            # 2. 基本回應測試
            test_question = "Hello, please respond briefly"
            command = f'echo "{test_question}" | ollama run deepseek-r1:14b --'
            
            response_start = time.time()
            stdin, stdout, stderr = ssh.exec_command(command, timeout=45)
            response = stdout.read().decode('utf-8')
            result["response_time"] = time.time() - response_start
            
            if response.strip():
                result["response_test"] = True
                result["response_quality"] = self._evaluate_response_quality(response)
            
            # 3. 效能測試 (簡化版)
            if result["response_time"] <= 30 and result["response_quality"] >= 0.7:
                result["performance_test"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
        
        finally:
            if ssh:
                ssh.close()
        
        return result
    
    def _evaluate_response_quality(self, response):
        """評估回應品質"""
        # 簡單的品質評估
        if not response.strip():
            return 0.0
        
        quality_score = 0.5  # 基礎分數
        
        # 長度檢查
        if len(response.strip()) >= 10:
            quality_score += 0.2
        
        # 是否包含常見問候回應
        common_responses = ["hello", "hi", "good", "thank", "help", "assist"]
        if any(word in response.lower() for word in common_responses):
            quality_score += 0.2
        
        # 是否有明顯的編碼問題
        if '�' not in response and not response.count('\\'):
            quality_score += 0.1
        
        return min(quality_score, 1.0)
    
    def _print_check_result(self, result):
        """列印檢查結果"""
        status_indicators = {
            "connection_test": "✅" if result["connection_test"] else "❌",
            "response_test": "✅" if result["response_test"] else "❌",
            "performance_test": "✅" if result["performance_test"] else "❌"
        }
        
        print(f"  連接測試: {status_indicators['connection_test']} ({result['connection_time']:.2f}s)")
        print(f"  回應測試: {status_indicators['response_test']} ({result['response_time']:.2f}s)")
        print(f"  效能測試: {status_indicators['performance_test']}")
        
        if result["errors"]:
            print(f"  ❌ 錯誤: {', '.join(result['errors'][:2])}")
        
        # 健康分數
        health_score = sum([
            result["connection_test"],
            result["response_test"],
            result["performance_test"]
        ]) / 3 * 100
        
        print(f"  🏥 健康分數: {health_score:.0f}%")
    
    def _generate_stability_report(self, start_time, end_time):
        """生成穩定性報告"""
        if not self.results:
            print("❌ 無測試資料")
            return
        
        # 計算統計資料
        total_checks = len(self.results)
        successful_connections = sum(1 for r in self.results if r['connection_test'])
        successful_responses = sum(1 for r in self.results if r['response_test'])
        successful_performance = sum(1 for r in self.results if r['performance_test'])
        
        connection_rate = (successful_connections / total_checks) * 100
        response_rate = (successful_responses / total_checks) * 100
        performance_rate = (successful_performance / total_checks) * 100
        
        # 時間統計
        response_times = [r['response_time'] for r in self.results if r['response_test']]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
        else:
            avg_response_time = median_response_time = 0
        
        # 生成報告
        report = {
            "test_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_hours": (end_time - start_time).total_seconds() / 3600
            },
            "summary": {
                "total_checks": total_checks,
                "connection_success_rate": connection_rate,
                "response_success_rate": response_rate,
                "performance_success_rate": performance_rate,
                "overall_availability": min(connection_rate, response_rate)
            },
            "performance_metrics": {
                "avg_response_time": avg_response_time,
                "median_response_time": median_response_time
            },
            "detailed_results": self.results
        }
        
        # 顯示報告
        print("\n" + "=" * 60)
        print("🔄 長期穩定性測試報告")
        print("=" * 60)
        
        duration_hours = (end_time - start_time).total_seconds() / 3600
        print(f"📅 測試期間: {start_time.strftime('%Y-%m-%d %H:%M')} - {end_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"⏱️ 測試時長: {duration_hours:.1f} 小時")
        print(f"🔍 檢查次數: {total_checks}")
        
        print(f"\n📊 可用性統計:")
        print(f"  連接成功率: {connection_rate:.1f}%")
        print(f"  回應成功率: {response_rate:.1f}%")
        print(f"  效能達標率: {performance_rate:.1f}%")
        print(f"  整體可用性: {min(connection_rate, response_rate):.1f}%")
        
        if response_times:
            print(f"\n⏱️ 效能統計:")
            print(f"  平均回應時間: {avg_response_time:.2f}s")
            print(f"  中位數回應時間: {median_response_time:.2f}s")
        
        # 穩定性評級
        overall_availability = min(connection_rate, response_rate)
        if overall_availability >= 99.9:
            stability_grade = "極佳 🏆"
        elif overall_availability >= 99.0:
            stability_grade = "優秀 👍"
        elif overall_availability >= 95.0:
            stability_grade = "良好 ⚡"
        elif overall_availability >= 90.0:
            stability_grade = "可接受 ⚠️"
        else:
            stability_grade = "需改善 ❌"
        
        print(f"\n🏆 穩定性評級: {stability_grade}")
        
        # 儲存報告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stability_test_report_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 詳細報告已儲存至: {filename}")

# 使用範例
if __name__ == "__main__":
    # 執行 2 小時穩定性測試，每 10 分鐘檢查一次
    stability_test = LongTermStabilityTest(
        test_duration_hours=2,
        check_interval_minutes=10
    )
    
    stability_test.run_stability_test()
```

## 📊 效能監控儀表板

### 即時監控腳本
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek AI 即時效能監控
"""
import paramiko
import time
import threading
import json
from datetime import datetime
from collections import deque

class PerformanceMonitor:
    """效能監控器"""
    
    def __init__(self, update_interval=30):
        self.update_interval = update_interval
        self.metrics_history = deque(maxlen=100)  # 保留最近100次記錄
        self.is_running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """開始監控"""
        if self.is_running:
            print("⚠️ 監控已在運行中")
            return
        
        self.is_running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        print("🔍 效能監控已啟動")
        print(f"更新間隔: {self.update_interval} 秒")
        print("按 Ctrl+C 停止監控")
        
    def stop_monitoring(self):
        """停止監控"""
        self.is_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("⏹️ 效能監控已停止")
        
    def _monitor_loop(self):
        """監控循環"""
        while self.is_running:
            try:
                metrics = self._collect_metrics()
                self.metrics_history.append(metrics)
                self._display_dashboard(metrics)
                time.sleep(self.update_interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 監控錯誤: {e}")
                time.sleep(self.update_interval)
    
    def _collect_metrics(self):
        """收集效能指標"""
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "connection_status": False,
            "connection_time": 0,
            "response_time": 0,
            "service_status": "unknown",
            "error": None
        }
        
        ssh = None
        try:
            # 測試連接
            connect_start = time.time()
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
            metrics["connection_time"] = time.time() - connect_start
            metrics["connection_status"] = True
            
            # 測試回應
            test_start = time.time()
            stdin, stdout, stderr = ssh.exec_command('echo "test" | ollama run deepseek-r1:14b --', timeout=30)
            response = stdout.read().decode('utf-8')
            metrics["response_time"] = time.time() - test_start
            
            if response.strip():
                metrics["service_status"] = "healthy"
            else:
                metrics["service_status"] = "degraded"
                
        except Exception as e:
            metrics["error"] = str(e)
            metrics["service_status"] = "error"
        
        finally:
            if ssh:
                ssh.close()
        
        return metrics
    
    def _display_dashboard(self, current_metrics):
        """顯示儀表板"""
        # 清除螢幕 (可選)
        # import os
        # os.system('clear' if os.name == 'posix' else 'cls')
        
        print("\n" + "=" * 60)
        print("📊 DeepSeek AI 效能監控儀表板")
        print("=" * 60)
        print(f"🕒 更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 當前狀態
        status_icon = "🟢" if current_metrics["service_status"] == "healthy" else "🔴"
        print(f"{status_icon} 服務狀態: {current_metrics['service_status']}")
        
        if current_metrics["connection_status"]:
            print(f"🔗 連接時間: {current_metrics['connection_time']:.2f}s")
            print(f"⏱️ 回應時間: {current_metrics['response_time']:.2f}s")
        else:
            print("❌ 連接失敗")
        
        if current_metrics["error"]:
            print(f"🚨 錯誤: {current_metrics['error'][:50]}...")
        
        # 歷史統計 (如果有足夠資料)
        if len(self.metrics_history) >= 5:
            self._display_historical_stats()
    
    def _display_historical_stats(self):
        """顯示歷史統計"""
        recent_metrics = list(self.metrics_history)[-10:]  # 最近10次
        
        # 計算成功率
        successful_connections = sum(1 for m in recent_metrics if m["connection_status"])
        healthy_services = sum(1 for m in recent_metrics if m["service_status"] == "healthy")
        
        connection_rate = (successful_connections / len(recent_metrics)) * 100
        health_rate = (healthy_services / len(recent_metrics)) * 100
        
        print(f"\n📈 最近統計 (基於最近 {len(recent_metrics)} 次檢查):")
        print(f"  連接成功率: {connection_rate:.0f}%")
        print(f"  服務健康率: {health_rate:.0f}%")
        
        # 平均回應時間
        response_times = [m["response_time"] for m in recent_metrics if m["connection_status"]]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            print(f"  平均回應時間: {avg_response_time:.2f}s")

# 使用範例
if __name__ == "__main__":
    monitor = PerformanceMonitor(update_interval=30)
    
    try:
        monitor.start_monitoring()
        
        # 保持主線程運行
        while monitor.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n收到中斷信號...")
        monitor.stop_monitoring()
```

## 🎯 效能優化建議

### 最佳實踐
1. **連接池管理**: 重用 SSH 連接減少建立時間
2. **批量測試**: 一次連接執行多個測試
3. **超時設定**: 合理設定超時避免長時間等待
4. **負載控制**: 避免過度請求造成服務過載
5. **監控告警**: 設定效能閾值和告警機制

### 效能調優
- 根據問題複雜度調整超時時間
- 使用更簡單的問題進行健康檢查
- 實施請求限流避免系統過載
- 監控服務器資源使用情況

---

**建立時間**: 2025-09-09  
**測試類型**: 效能測試、壓力測試、穩定性測試  
**依賴套件**: paramiko, threading, statistics