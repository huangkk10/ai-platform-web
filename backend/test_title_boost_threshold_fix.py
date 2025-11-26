#!/usr/bin/env python3
"""
測試 Title Boost 後二次過濾修復
---------------------------------
驗證目標：
1. Title Boost 加分後，仍低於 threshold 的結果應該被過濾
2. v1.2.1 應該和 v1.1.1 返回相同數量的結果（1 條）
3. 確認返回的是段落內容（~178 字元），而非全文（1231 字元）

預期行為：
---------
修復前（v1.2.1 Bug）：
  - SQL 搜尋找到 2 條（Score 0.89, 0.68）
  - Title Boost 後：Score 變為 1.09, 0.68
  - 返回 2 條（包含低於 threshold 的結果）❌

修復後（v1.2.1 Correct）：
  - SQL 搜尋找到 2 條（Score 0.89, 0.68）
  - Title Boost 後：Score 變為 1.09, 0.68
  - **二次過濾**：移除 0.68 < 0.7 的結果
  - 返回 1 條（與 v1.1.1 一致）✅
"""

import os
import sys
import django

# 設置 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

import requests
from typing import Dict, Any
from django.db import connection


class TitleBoostThresholdFixTester:
    """Title Boost 二次過濾修復測試器"""
    
    def __init__(self):
        self.dify_api_url = "http://localhost/api/dify/knowledge/retrieval/"
        self.test_query = "iol 密碼"
        self.knowledge_id = "protocol_guide_database"
        self.top_k = 20
        self.threshold = 0.7
        
    def _send_dify_request(self, version_code: str) -> Dict[str, Any]:
        """
        發送 Dify API 請求
        
        Args:
            version_code: 版本代號（如 'dify-two-tier-v1.1.1'）
            
        Returns:
            API 回應 JSON
        """
        payload = {
            "knowledge_id": self.knowledge_id,
            "query": self.test_query,
            "retrieval_setting": {
                "top_k": self.top_k,
                "score_threshold": self.threshold
            },
            "inputs": {
                "version_code": version_code
            }
        }
        
        print(f"\n📡 發送 Dify API 請求:")
        print(f"  Version: {version_code}")
        print(f"  Query: '{self.test_query}'")
        print(f"  Threshold: {self.threshold}")
        
        response = requests.post(self.dify_api_url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def _analyze_results(self, results: list, version: str) -> Dict[str, Any]:
        """
        分析搜尋結果
        
        Args:
            results: Dify API 返回的 records
            version: 版本標識（用於顯示）
            
        Returns:
            分析統計資料
        """
        analysis = {
            'version': version,
            'count': len(results),
            'titles': [],
            'scores': [],
            'content_lengths': [],
            'below_threshold': []
        }
        
        print(f"\n📊 {version} 分析:")
        print(f"  總結果數: {len(results)}")
        
        for idx, result in enumerate(results, 1):
            title = result.get('metadata', {}).get('title', 'N/A')
            score = result.get('score', 0)
            content = result.get('content', '')
            content_length = len(content)
            
            analysis['titles'].append(title)
            analysis['scores'].append(score)
            analysis['content_lengths'].append(content_length)
            
            # 檢查是否低於 threshold
            is_below = score < self.threshold
            if is_below:
                analysis['below_threshold'].append({
                    'index': idx,
                    'title': title,
                    'score': score,
                    'content_length': content_length
                })
            
            status = "⚠️ 低於閾值" if is_below else "✅ 通過閾值"
            print(f"  結果 {idx}: Score={score:.4f} {status}")
            print(f"    標題: {title[:60]}...")
            print(f"    內容長度: {content_length} 字元")
        
        return analysis
    
    def _check_log_for_filtering(self):
        """檢查日誌中是否有二次過濾記錄"""
        log_path = "/home/user/PythonCode/ai-platform-web/logs/django.log"
        
        print("\n🔍 檢查日誌中的二次過濾記錄:")
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 找最後 100 行中的過濾記錄
            filter_logs = [
                line for line in lines[-100:]
                if "Title Boost 後二次過濾" in line
            ]
            
            if filter_logs:
                print(f"  ✅ 找到 {len(filter_logs)} 條二次過濾記錄:")
                for log in filter_logs[-3:]:  # 顯示最後 3 條
                    print(f"    {log.strip()}")
            else:
                print("  ⚠️ 沒有找到二次過濾記錄（可能沒有觸發）")
                
        except FileNotFoundError:
            print(f"  ❌ 日誌檔案不存在: {log_path}")
    
    def _compare_versions(self, v1_analysis: Dict, v2_analysis: Dict):
        """
        比較兩個版本的結果
        
        Args:
            v1_analysis: v1.1.1 分析結果
            v2_analysis: v1.2.1 分析結果
        """
        print("\n" + "="*70)
        print("📊 版本比較分析")
        print("="*70)
        
        # 1. 結果數量比較
        print(f"\n1️⃣ 結果數量:")
        print(f"  v1.1.1: {v1_analysis['count']} 條")
        print(f"  v1.2.1: {v2_analysis['count']} 條")
        
        if v1_analysis['count'] == v2_analysis['count']:
            print("  ✅ 結果數量一致（修復成功）")
        else:
            print(f"  ❌ 結果數量不一致（修復失敗）")
        
        # 2. Score 比較
        print(f"\n2️⃣ Score 分佈:")
        for i in range(max(len(v1_analysis['scores']), len(v2_analysis['scores']))):
            v1_score = v1_analysis['scores'][i] if i < len(v1_analysis['scores']) else None
            v2_score = v2_analysis['scores'][i] if i < len(v2_analysis['scores']) else None
            
            if v1_score is not None and v2_score is not None:
                diff = v2_score - v1_score
                status = "✅" if abs(diff) < 0.01 else "⚠️"
                print(f"  結果 {i+1}: v1.1.1={v1_score:.4f}, v1.2.1={v2_score:.4f} (差異: {diff:+.4f}) {status}")
            elif v1_score is not None:
                print(f"  結果 {i+1}: v1.1.1={v1_score:.4f}, v1.2.1=N/A ❌")
            elif v2_score is not None:
                print(f"  結果 {i+1}: v1.1.1=N/A, v1.2.1={v2_score:.4f} ❌")
        
        # 3. 內容長度比較
        print(f"\n3️⃣ 內容長度:")
        for i in range(max(len(v1_analysis['content_lengths']), len(v2_analysis['content_lengths']))):
            v1_len = v1_analysis['content_lengths'][i] if i < len(v1_analysis['content_lengths']) else None
            v2_len = v2_analysis['content_lengths'][i] if i < len(v2_analysis['content_lengths']) else None
            
            if v1_len is not None and v2_len is not None:
                is_similar = abs(v1_len - v2_len) < 100
                status = "✅" if is_similar else "⚠️"
                print(f"  結果 {i+1}: v1.1.1={v1_len} 字元, v1.2.1={v2_len} 字元 {status}")
            elif v1_len is not None:
                print(f"  結果 {i+1}: v1.1.1={v1_len} 字元, v1.2.1=N/A ❌")
            elif v2_len is not None:
                print(f"  結果 {i+1}: v1.1.1=N/A, v1.2.1={v2_len} 字元 ❌")
        
        # 4. 低於 threshold 的結果
        print(f"\n4️⃣ 低於 Threshold ({self.threshold}) 的結果:")
        if not v1_analysis['below_threshold'] and not v2_analysis['below_threshold']:
            print("  ✅ 兩個版本都沒有低於閾值的結果（正確）")
        else:
            if v1_analysis['below_threshold']:
                print(f"  ❌ v1.1.1 有 {len(v1_analysis['below_threshold'])} 條低於閾值:")
                for item in v1_analysis['below_threshold']:
                    print(f"    結果 {item['index']}: Score={item['score']:.4f}")
            
            if v2_analysis['below_threshold']:
                print(f"  ❌ v1.2.1 有 {len(v2_analysis['below_threshold'])} 條低於閾值:")
                for item in v2_analysis['below_threshold']:
                    print(f"    結果 {item['index']}: Score={item['score']:.4f}")
    
    def run_test(self):
        """執行完整測試"""
        print("="*70)
        print("🧪 Title Boost 二次過濾修復測試")
        print("="*70)
        print(f"測試查詢: '{self.test_query}'")
        print(f"Threshold: {self.threshold}")
        print(f"預期修復效果: v1.2.1 應該和 v1.1.1 返回相同數量的結果")
        
        # 測試 v1.1.1（無 Title Boost）
        print("\n" + "-"*70)
        print("📌 測試 v1.1.1（無 Title Boost，作為基準）")
        print("-"*70)
        
        v1_response = self._send_dify_request("dify-two-tier-v1.1.1")
        v1_results = v1_response.get('records', [])
        v1_analysis = self._analyze_results(v1_results, "v1.1.1")
        
        # 測試 v1.2.1（有 Title Boost + 二次過濾）
        print("\n" + "-"*70)
        print("📌 測試 v1.2.1（有 Title Boost + 二次過濾修復）")
        print("-"*70)
        
        v2_response = self._send_dify_request("dify-two-tier-v1.2.1")
        v2_results = v2_response.get('records', [])
        v2_analysis = self._analyze_results(v2_results, "v1.2.1")
        
        # 檢查日誌
        self._check_log_for_filtering()
        
        # 比較分析
        self._compare_versions(v1_analysis, v2_analysis)
        
        # 最終結論
        print("\n" + "="*70)
        print("📝 測試結論")
        print("="*70)
        
        if v1_analysis['count'] == v2_analysis['count']:
            if not v2_analysis['below_threshold']:
                print("✅ 修復成功！")
                print("  - v1.2.1 返回結果數與 v1.1.1 一致")
                print("  - 所有結果的 Score 都 >= threshold")
                print("  - Title Boost 後二次過濾正常運作")
                return True
            else:
                print("⚠️ 部分成功（結果數量一致，但有低於閾值的結果）")
                return False
        else:
            print("❌ 修復失敗！")
            print(f"  - v1.2.1 返回 {v2_analysis['count']} 條")
            print(f"  - v1.1.1 返回 {v1_analysis['count']} 條")
            print("  - Title Boost 後二次過濾可能沒有正確執行")
            return False


if __name__ == "__main__":
    tester = TitleBoostThresholdFixTester()
    
    try:
        success = tester.run_test()
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ 測試執行失敗: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
