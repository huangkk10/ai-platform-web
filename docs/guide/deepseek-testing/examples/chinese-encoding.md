# 🌏 中文編碼測試範例

本文件提供 DeepSeek AI 中文編碼處理的測試範例和解決方案。

## 🎯 中文編碼問題概述

### 常見問題
- 中文字符在 SSH 傳輸中出現亂碼
- 不同編碼格式導致的顯示異常
- 終端環境編碼設定影響

### 測試目標
- 驗證繁體中文支援
- 測試簡體中文相容性
- 確認特殊字符處理
- 評估編碼轉換效果

## 🧪 基礎中文測試

### 方法一：英文指令中文回應
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文編碼測試 - 方法一：英文指令要求中文回應
"""
import paramiko
import time

def english_request_chinese_response():
    """英文指令要求中文回應"""
    print("🌏 測試方法一: 英文指令要求中文回應")
    print("=" * 50)
    
    # 測試問題 (英文指令)
    test_cases = [
        {
            "question": "Please introduce yourself in Traditional Chinese",
            "description": "自我介紹(繁體中文)",
            "expected_chars": ["您好", "我是", "助手"]
        },
        {
            "question": "Tell me about Taiwan in Traditional Chinese",
            "description": "介紹台灣(繁體中文)",
            "expected_chars": ["台灣", "位於", "亞洲"]
        },
        {
            "question": "Explain machine learning in Simplified Chinese",
            "description": "機器學習說明(簡體中文)",
            "expected_chars": ["机器学习", "人工智能", "算法"]
        },
        {
            "question": "Write a short poem in Traditional Chinese",
            "description": "短詩創作(繁體中文)",
            "expected_chars": ["詩", "美", "心"]
        }
    ]
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接成功")
        
        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📋 測試 {i}/{len(test_cases)}: {test_case['description']}")
            print(f"💬 問題: {test_case['question']}")
            
            command = f'echo "{test_case["question"]}" | ollama run deepseek-r1:14b --'
            start_time = time.time()
            
            stdin, stdout, stderr = ssh.exec_command(command, timeout=45)
            response = stdout.read().decode('utf-8', errors='replace')
            
            elapsed = time.time() - start_time
            
            # 分析回應
            analysis = analyze_chinese_response(response, test_case['expected_chars'])
            
            result = {
                "test_case": test_case['description'],
                "question": test_case['question'],
                "response": response,
                "response_time": elapsed,
                "chinese_detected": analysis['chinese_detected'],
                "expected_chars_found": analysis['expected_chars_found'],
                "encoding_quality": analysis['encoding_quality']
            }
            
            results.append(result)
            
            # 顯示結果
            print(f"⏱️ 回應時間: {elapsed:.1f}s")
            print(f"🌏 中文檢測: {'✅' if analysis['chinese_detected'] else '❌'}")
            print(f"📝 編碼品質: {analysis['encoding_quality']}")
            
            if response.strip():
                print("🤖 回應預覽:")
                print("-" * 40)
                preview = response[:200] + "..." if len(response) > 200 else response
                print(preview)
                print("-" * 40)
            else:
                print("❌ 無回應")
            
            time.sleep(2)
        
        ssh.close()
        
        # 產生測試報告
        generate_chinese_test_report(results)
        return results
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return []

def analyze_chinese_response(response, expected_chars):
    """分析中文回應品質"""
    import re
    
    # 檢測中文字符
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
    chinese_chars = chinese_pattern.findall(response)
    chinese_detected = len(chinese_chars) > 0
    
    # 檢查期望字符
    expected_found = 0
    for expected in expected_chars:
        if expected in response:
            expected_found += 1
    
    expected_chars_found = expected_found / len(expected_chars) if expected_chars else 0
    
    # 編碼品質評估
    encoding_issues = 0
    
    # 檢查常見編碼問題
    if '�' in response:  # 替換字符表示編碼錯誤
        encoding_issues += 1
    
    if re.search(r'\\u[0-9a-fA-F]{4}', response):  # Unicode 轉義序列
        encoding_issues += 1
    
    # 計算編碼品質分數
    if encoding_issues == 0 and chinese_detected:
        encoding_quality = "優秀"
    elif encoding_issues == 0:
        encoding_quality = "良好"
    elif encoding_issues <= 2:
        encoding_quality = "可接受"
    else:
        encoding_quality = "差"
    
    return {
        "chinese_detected": chinese_detected,
        "chinese_char_count": len(chinese_chars),
        "expected_chars_found": expected_chars_found,
        "encoding_quality": encoding_quality,
        "encoding_issues": encoding_issues
    }

if __name__ == "__main__":
    english_request_chinese_response()
```

### 方法二：直接中文問題
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文編碼測試 - 方法二：直接中文問題
"""
import paramiko
import time
import shlex

def direct_chinese_questions():
    """直接中文問題測試"""
    print("🌏 測試方法二: 直接中文問題")
    print("=" * 50)
    
    # 中文測試問題
    chinese_questions = [
        {
            "question": "你好，請自我介紹",
            "type": "繁體中文",
            "encoding": "utf-8"
        },
        {
            "question": "什麼是人工智慧？",
            "type": "繁體中文",
            "encoding": "utf-8"
        },
        {
            "question": "你好，请自我介绍",
            "type": "簡體中文",
            "encoding": "utf-8"
        },
        {
            "question": "什么是机器学习？",
            "type": "簡體中文",
            "encoding": "utf-8"
        },
        {
            "question": "台灣有什麼特色美食？",
            "type": "繁體中文+地區性",
            "encoding": "utf-8"
        }
    ]
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect("10.10.172.5", username="svd", password="1234", timeout=10)
        print("✅ SSH 連接成功")
        
        results = []
        
        for i, test_q in enumerate(chinese_questions, 1):
            print(f"\n📋 測試 {i}/{len(chinese_questions)}: {test_q['type']}")
            print(f"💬 問題: {test_q['question']}")
            
            # 使用不同的編碼方法
            success = False
            methods = [
                ("直接傳送", test_q['question']),
                ("shlex 轉義", shlex.quote(test_q['question'])),
                ("UTF-8 環境", f"LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 echo {shlex.quote(test_q['question'])}")
            ]
            
            for method_name, processed_question in methods:
                try:
                    print(f"  🔧 嘗試方法: {method_name}")
                    
                    if method_name == "UTF-8 環境":
                        command = f'{processed_question} | ollama run deepseek-r1:14b --'
                    else:
                        command = f'echo {processed_question} | ollama run deepseek-r1:14b --'
                    
                    start_time = time.time()
                    stdin, stdout, stderr = ssh.exec_command(command, timeout=45)
                    
                    # 嘗試不同的解碼方法
                    response = None
                    for encoding in ['utf-8', 'utf-8-sig', 'gb2312', 'big5']:
                        try:
                            raw_output = stdout.read()
                            response = raw_output.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if response is None:
                        response = stdout.read().decode('utf-8', errors='replace')
                    
                    elapsed = time.time() - start_time
                    
                    if response.strip():
                        print(f"    ✅ 成功 (耗時 {elapsed:.1f}s)")
                        print(f"    📝 回應預覽: {response[:50]}...")
                        
                        result = {
                            "question": test_q['question'],
                            "question_type": test_q['type'],
                            "method": method_name,
                            "response": response,
                            "response_time": elapsed,
                            "success": True
                        }
                        results.append(result)
                        success = True
                        break
                    else:
                        print(f"    ❌ 無回應")
                        
                except Exception as e:
                    print(f"    ❌ 方法失敗: {e}")
            
            if not success:
                print(f"  ❌ 所有方法都失敗")
                results.append({
                    "question": test_q['question'],
                    "question_type": test_q['type'],
                    "method": "全部失敗",
                    "response": "",
                    "response_time": 0,
                    "success": False
                })
            
            time.sleep(2)
        
        ssh.close()
        
        # 產生測試報告
        generate_direct_chinese_report(results)
        return results
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        return []

def generate_direct_chinese_report(results):
    """產生直接中文測試報告"""
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r['success'])
    success_rate = (successful_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print("\n" + "=" * 60)
    print("📊 直接中文問題測試報告")
    print("=" * 60)
    print(f"總測試數: {total_tests}")
    print(f"成功數: {successful_tests}")
    print(f"成功率: {success_rate:.1f}%")
    
    # 方法成功率統計
    method_stats = {}
    for result in results:
        if result['success']:
            method = result['method']
            if method not in method_stats:
                method_stats[method] = 0
            method_stats[method] += 1
    
    if method_stats:
        print("\n📈 各方法成功次數:")
        for method, count in method_stats.items():
            print(f"  {method}: {count} 次")
    
    # 失敗的測試
    failed_tests = [r for r in results if not r['success']]
    if failed_tests:
        print(f"\n❌ 失敗的測試:")
        for test in failed_tests:
            print(f"  - {test['question']} ({test['question_type']})")

if __name__ == "__main__":
    direct_chinese_questions()
```

## 🔧 編碼處理工具

### 編碼檢測與轉換
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
編碼處理工具
"""
import chardet
import re

class ChineseEncodingHandler:
    """中文編碼處理器"""
    
    def __init__(self):
        self.common_encodings = ['utf-8', 'utf-8-sig', 'gb2312', 'gbk', 'big5', 'cp950']
    
    def detect_encoding(self, raw_bytes):
        """檢測編碼"""
        try:
            detected = chardet.detect(raw_bytes)
            return detected['encoding'], detected['confidence']
        except Exception as e:
            return None, 0.0
    
    def safe_decode(self, raw_bytes, preferred_encoding='utf-8'):
        """安全解碼"""
        # 首先嘗試偏好編碼
        try:
            return raw_bytes.decode(preferred_encoding), preferred_encoding
        except UnicodeDecodeError:
            pass
        
        # 自動檢測編碼
        detected_encoding, confidence = self.detect_encoding(raw_bytes)
        if detected_encoding and confidence > 0.7:
            try:
                return raw_bytes.decode(detected_encoding), detected_encoding
            except UnicodeDecodeError:
                pass
        
        # 嘗試常見編碼
        for encoding in self.common_encodings:
            try:
                return raw_bytes.decode(encoding), encoding
            except UnicodeDecodeError:
                continue
        
        # 最後使用替換模式
        return raw_bytes.decode('utf-8', errors='replace'), 'utf-8-replace'
    
    def is_chinese_text(self, text):
        """檢測是否包含中文"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
        return bool(chinese_pattern.search(text))
    
    def count_chinese_chars(self, text):
        """計算中文字符數量"""
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
        return len(chinese_pattern.findall(text))
    
    def detect_chinese_variant(self, text):
        """檢測中文變體 (簡體/繁體)"""
        # 簡體中文特有字符
        simplified_chars = set(['学', '国', '发', '经', '时', '问', '长', '门', '车', '马'])
        # 繁體中文特有字符
        traditional_chars = set(['學', '國', '發', '經', '時', '問', '長', '門', '車', '馬'])
        
        simplified_count = sum(1 for char in text if char in simplified_chars)
        traditional_count = sum(1 for char in text if char in traditional_chars)
        
        if simplified_count > traditional_count:
            return "簡體中文"
        elif traditional_count > simplified_count:
            return "繁體中文"
        else:
            return "混合/不確定"
    
    def clean_encoding_artifacts(self, text):
        """清理編碼產生的雜訊"""
        # 移除常見的編碼錯誤字符
        text = text.replace('\ufffd', '')  # 替換字符
        text = re.sub(r'\\u[0-9a-fA-F]{4}', '', text)  # Unicode 轉義序列
        text = re.sub(r'\x[0-9a-fA-F]{2}', '', text)   # 十六進制字符
        
        # 清理多餘的空白
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

# 使用範例
def test_encoding_handler():
    """測試編碼處理器"""
    handler = ChineseEncodingHandler()
    
    # 測試文字
    test_texts = [
        "你好，世界！",
        "Hello, 世界！",
        "机器学习是人工智能的一个分支",
        "機器學習是人工智慧的一個分支",
        "This is English text only."
    ]
    
    print("🔧 編碼處理器測試")
    print("=" * 40)
    
    for text in test_texts:
        print(f"\n📝 測試文字: {text}")
        
        # 編碼為 bytes 再解碼 (模擬網路傳輸)
        encoded_bytes = text.encode('utf-8')
        decoded_text, used_encoding = handler.safe_decode(encoded_bytes)
        
        print(f"🔍 使用編碼: {used_encoding}")
        print(f"🌏 包含中文: {'是' if handler.is_chinese_text(decoded_text) else '否'}")
        
        if handler.is_chinese_text(decoded_text):
            char_count = handler.count_chinese_chars(decoded_text)
            variant = handler.detect_chinese_variant(decoded_text)
            print(f"📊 中文字數: {char_count}")
            print(f"🏷️ 中文類型: {variant}")

if __name__ == "__main__":
    test_encoding_handler()
```

### SSH 中文傳輸優化
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SSH 中文傳輸優化
"""
import paramiko
import shlex
import base64

class ChineseSSHClient:
    """優化中文支援的 SSH 客戶端"""
    
    def __init__(self, host, username, password, port=22):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.ssh = None
        self.encoding_handler = ChineseEncodingHandler()
    
    def connect(self, timeout=10):
        """建立連接"""
        try:
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                self.host, 
                username=self.username, 
                password=self.password, 
                port=self.port,
                timeout=timeout
            )
            return True
        except Exception as e:
            print(f"❌ SSH 連接失敗: {e}")
            return False
    
    def execute_chinese_command(self, chinese_text, model="deepseek-r1:14b", timeout=30):
        """執行包含中文的命令"""
        if not self.ssh:
            raise Exception("SSH 未連接")
        
        methods = [
            self._method_direct,
            self._method_quoted,
            self._method_base64,
            self._method_utf8_env
        ]
        
        for method in methods:
            try:
                result = method(chinese_text, model, timeout)
                if result['success']:
                    return result
            except Exception as e:
                print(f"⚠️ 方法失敗: {e}")
        
        return {
            'success': False,
            'response': '',
            'method': 'all_failed',
            'error': '所有方法都失敗'
        }
    
    def _method_direct(self, text, model, timeout):
        """方法1: 直接傳送"""
        command = f'echo "{text}" | ollama run {model} --'
        return self._execute_command(command, timeout, "直接傳送")
    
    def _method_quoted(self, text, model, timeout):
        """方法2: shell 引號轉義"""
        quoted_text = shlex.quote(text)
        command = f'echo {quoted_text} | ollama run {model} --'
        return self._execute_command(command, timeout, "引號轉義")
    
    def _method_base64(self, text, model, timeout):
        """方法3: Base64 編碼"""
        encoded_text = base64.b64encode(text.encode('utf-8')).decode('ascii')
        command = f'echo "{encoded_text}" | base64 -d | ollama run {model} --'
        return self._execute_command(command, timeout, "Base64編碼")
    
    def _method_utf8_env(self, text, model, timeout):
        """方法4: UTF-8 環境變數"""
        quoted_text = shlex.quote(text)
        command = f'LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 echo {quoted_text} | ollama run {model} --'
        return self._execute_command(command, timeout, "UTF-8環境")
    
    def _execute_command(self, command, timeout, method_name):
        """執行命令並處理回應"""
        stdin, stdout, stderr = self.ssh.exec_command(command, timeout=timeout)
        
        # 讀取原始 bytes
        raw_output = stdout.read()
        error_output = stderr.read()
        
        # 安全解碼
        response, encoding_used = self.encoding_handler.safe_decode(raw_output)
        
        # 清理編碼雜訊
        cleaned_response = self.encoding_handler.clean_encoding_artifacts(response)
        
        success = bool(cleaned_response.strip())
        
        return {
            'success': success,
            'response': cleaned_response,
            'method': method_name,
            'encoding': encoding_used,
            'raw_length': len(raw_output),
            'error': error_output.decode('utf-8', errors='replace') if error_output else ''
        }
    
    def close(self):
        """關閉連接"""
        if self.ssh:
            self.ssh.close()

# 使用範例
def test_chinese_ssh_client():
    """測試中文 SSH 客戶端"""
    print("🌏 中文 SSH 客戶端測試")
    print("=" * 50)
    
    client = ChineseSSHClient("10.10.172.5", "svd", "1234")
    
    if not client.connect():
        print("❌ 無法連接到服務器")
        return
    
    print("✅ SSH 連接成功")
    
    # 測試問題
    test_questions = [
        "你好，請自我介紹",
        "什麼是人工智慧？",
        "台灣有什麼特色美食？",
        "請用繁體中文回答：機器學習是什麼？"
    ]
    
    try:
        for i, question in enumerate(test_questions, 1):
            print(f"\n📋 測試 {i}/{len(test_questions)}")
            print(f"💬 問題: {question}")
            
            result = client.execute_chinese_command(question)
            
            if result['success']:
                print(f"✅ 成功 (方法: {result['method']})")
                print(f"🔤 編碼: {result['encoding']}")
                print(f"📝 回應預覽:")
                print("-" * 30)
                preview = result['response'][:150] + "..." if len(result['response']) > 150 else result['response']
                print(preview)
                print("-" * 30)
            else:
                print(f"❌ 失敗: {result.get('error', '未知錯誤')}")
    
    finally:
        client.close()
        print("\n🔚 測試完成，連接已關閉")

if __name__ == "__main__":
    test_chinese_ssh_client()
```

## 📊 中文測試報告生成

### 綜合報告生成器
```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文測試綜合報告生成器
"""
import json
import time
from datetime import datetime

def generate_chinese_test_report(results):
    """產生中文測試綜合報告"""
    if not results:
        print("❌ 無測試資料")
        return
    
    # 統計資料
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r.get('success', False))
    success_rate = (successful_tests / total_tests) * 100
    
    # 中文檢測統計
    chinese_detected_count = sum(1 for r in results if r.get('chinese_detected', False))
    chinese_detection_rate = (chinese_detected_count / total_tests) * 100
    
    # 編碼品質統計
    encoding_quality_stats = {}
    for result in results:
        quality = result.get('encoding_quality', '未知')
        encoding_quality_stats[quality] = encoding_quality_stats.get(quality, 0) + 1
    
    # 回應時間統計
    response_times = [r.get('response_time', 0) for r in results if r.get('success', False)]
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    
    # 產生報告
    report = {
        "測試時間": datetime.now().isoformat(),
        "測試摘要": {
            "總測試數": total_tests,
            "成功測試數": successful_tests,
            "成功率": f"{success_rate:.1f}%",
            "中文檢測率": f"{chinese_detection_rate:.1f}%",
            "平均回應時間": f"{avg_response_time:.2f}秒"
        },
        "編碼品質分布": encoding_quality_stats,
        "詳細結果": results
    }
    
    # 顯示報告
    print("\n" + "=" * 60)
    print("🌏 中文編碼測試綜合報告")
    print("=" * 60)
    print(f"📅 測試時間: {report['測試時間']}")
    print(f"📊 總測試數: {total_tests}")
    print(f"✅ 成功數: {successful_tests} ({success_rate:.1f}%)")
    print(f"🌏 中文檢測: {chinese_detected_count} ({chinese_detection_rate:.1f}%)")
    print(f"⏱️ 平均回應時間: {avg_response_time:.2f}秒")
    
    print(f"\n📈 編碼品質分布:")
    for quality, count in encoding_quality_stats.items():
        percentage = (count / total_tests) * 100
        print(f"  {quality}: {count} ({percentage:.1f}%)")
    
    # 建議
    print(f"\n💡 建議:")
    if success_rate >= 90:
        print("  ✅ 中文支援表現優秀")
    elif success_rate >= 70:
        print("  ⚠️ 中文支援良好，但仍有改善空間")
    else:
        print("  ❌ 中文支援需要改善")
    
    if chinese_detection_rate < 80:
        print("  ⚠️ 建議檢查編碼設定和傳輸方法")
    
    if avg_response_time > 30:
        print("  ⏱️ 回應時間較長，建議優化問題複雜度")
    
    # 儲存 JSON 報告
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chinese_encoding_test_report_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 詳細報告已儲存至: {filename}")
    
    return report

if __name__ == "__main__":
    # 範例使用
    sample_results = [
        {
            "test_case": "自我介紹(繁體中文)",
            "success": True,
            "chinese_detected": True,
            "encoding_quality": "優秀",
            "response_time": 8.5
        },
        {
            "test_case": "機器學習說明(簡體中文)",
            "success": True,
            "chinese_detected": True,
            "encoding_quality": "良好",
            "response_time": 12.3
        }
    ]
    
    generate_chinese_test_report(sample_results)
```

## 🎯 測試建議

### 最佳實踐
1. **多方法測試**: 使用不同的編碼和傳輸方法
2. **編碼檢測**: 自動檢測和處理不同編碼
3. **錯誤處理**: 優雅處理編碼錯誤
4. **品質評估**: 評估中文回應的品質和正確性

### 故障排除
- 檢查終端編碼設定
- 確認 SSH 服務器支援 UTF-8
- 使用 Base64 編碼避免特殊字符問題
- 設定正確的環境變數

---

**建立時間**: 2025-09-09  
**適用範圍**: 中文編碼測試和故障排除  
**相依模組**: paramiko, chardet, base64