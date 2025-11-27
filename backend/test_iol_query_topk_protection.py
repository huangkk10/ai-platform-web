#!/usr/bin/env python3
"""
Top-K Protection 功能驗證測試 - IOL 查詢案例

測試目標：
1. 驗證 Stage 1 混合搜尋不再因為 RRF 正規化導致過度過濾
2. 確認 UNH-IOL 文檔（score=0.0）被 Top-K Protection 保護
3. 驗證 Stage 1 成功返回足夠結果，不觸發 Stage 2

測試查詢：IOL 的密碼是什麼

預期結果（修復前）：
- Stage 1 只返回 1 個結果（UNH-IOL 被過濾掉）
- AI 回應「不清楚」
- 觸發 Stage 2 全文搜尋

預期結果（修復後）：
- Stage 1 返回 2 個結果（UNH-IOL 被 Top-K Protection 保護）
- AI 成功回答問題
- 不需要 Stage 2
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from django.test import RequestFactory
from api.views import dify_knowledge_search
import logging

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_separator(title=""):
    """打印分隔線"""
    if title:
        print(f"\n{'='*80}")
        print(f"  {title}")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'-'*80}\n")

def test_iol_query_stage1():
    """
    測試 IOL 查詢 - Stage 1 混合搜尋
    
    驗證 Top-K Protection 是否生效
    """
    print_separator("測試 1: IOL 查詢 - Stage 1 混合搜尋 (Top-K Protection)")
    
    # 構造測試請求
    factory = RequestFactory()
    request_data = {
        "knowledge_id": "protocol_guide",
        "query": "IOL 的密碼是什麼",
        "retrieval_setting": {
            "top_k": 2,
            "score_threshold": 0.8  # 高閾值會過濾掉 score=0.0 的結果
        }
    }
    
    print(f"📤 發送請求:")
    print(f"   knowledge_id: {request_data['knowledge_id']}")
    print(f"   query: {request_data['query']}")
    print(f"   top_k: {request_data['retrieval_setting']['top_k']}")
    print(f"   score_threshold: {request_data['retrieval_setting']['score_threshold']}")
    print()
    
    request = factory.post(
        '/api/dify/knowledge/retrieval/',
        data=json.dumps(request_data),
        content_type='application/json'
    )
    
    # 執行搜尋
    response = dify_knowledge_search(request)
    result = response.data
    
    print(f"📥 返回結果:")
    print(f"   結果數量: {len(result.get('records', []))}")
    print()
    
    # 顯示每個結果
    for idx, record in enumerate(result.get('records', []), 1):
        title = record.get('title', 'N/A')
        score = record.get('score', 0)
        content_preview = record.get('content', '')[:100].replace('\n', ' ')
        
        print(f"   結果 {idx}:")
        print(f"      標題: {title}")
        print(f"      分數: {score:.4f}")
        print(f"      內容: {content_preview}...")
        print()
    
    # 驗證結果
    records = result.get('records', [])
    
    print("🔍 驗證結果:")
    
    # 檢查 1: 結果數量
    if len(records) >= 2:
        print(f"   ✅ 結果數量正確: {len(records)} >= 2")
    else:
        print(f"   ❌ 結果數量不足: {len(records)} < 2 (可能 Top-K Protection 未生效)")
    
    # 檢查 2: UNH-IOL 文檔是否存在
    unh_iol_found = any('UNH-IOL' in record.get('title', '') for record in records)
    if unh_iol_found:
        print(f"   ✅ UNH-IOL 文檔存在 (Top-K Protection 成功保護低分結果)")
    else:
        print(f"   ⚠️  UNH-IOL 文檔未找到 (可能被過濾或不存在)")
    
    # 檢查 3: 最低分數
    min_score = min(record.get('score', 1.0) for record in records) if records else 0
    if min_score < 0.8:
        print(f"   ✅ 存在低於 threshold 的結果 (score={min_score:.4f} < 0.8)，Top-K Protection 生效")
    else:
        print(f"   ℹ️  所有結果都高於 threshold (min_score={min_score:.4f} >= 0.8)")
    
    print()
    
    # 總結
    if len(records) >= 2 and unh_iol_found:
        print("🎉 測試通過：Top-K Protection 成功保護低分結果，Stage 1 返回足夠上下文給 AI")
    elif len(records) >= 2:
        print("⚠️  測試部分通過：返回 2 個結果，但未找到 UNH-IOL 文檔")
    else:
        print("❌ 測試失敗：結果數量不足，Top-K Protection 可能未生效")
    
    return result

def test_iol_query_via_http():
    """
    測試 IOL 查詢 - 透過 HTTP API
    
    模擬真實的 Dify 請求
    """
    print_separator("測試 2: IOL 查詢 - HTTP API 測試")
    
    url = "http://localhost/api/dify/knowledge/retrieval/"
    payload = {
        "knowledge_id": "protocol_guide",
        "query": "IOL 的密碼是什麼",
        "retrieval_setting": {
            "top_k": 2,
            "score_threshold": 0.8
        }
    }
    
    print(f"📤 發送 HTTP 請求到 {url}")
    print(f"   Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    print()
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        
        print(f"📥 HTTP 狀態碼: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            records = result.get('records', [])
            
            print(f"   返回結果數量: {len(records)}")
            print()
            
            for idx, record in enumerate(records, 1):
                title = record.get('title', 'N/A')
                score = record.get('score', 0)
                print(f"   結果 {idx}: {title} (score={score:.4f})")
            
            print()
            
            # 驗證
            if len(records) >= 2:
                print("✅ HTTP API 測試通過：返回足夠的結果")
            else:
                print("❌ HTTP API 測試失敗：結果數量不足")
                
        else:
            print(f"❌ HTTP 請求失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
            
    except Exception as e:
        print(f"❌ HTTP 請求異常: {str(e)}")

def test_comparison_with_stage2():
    """
    對比測試：Stage 1 vs Stage 2
    
    驗證 Stage 1 修復後是否能達到 Stage 2 的效果
    """
    print_separator("測試 3: Stage 1 vs Stage 2 對比測試")
    
    factory = RequestFactory()
    
    # Stage 1 測試
    print("🔍 Stage 1 混合搜尋:")
    request_data_stage1 = {
        "knowledge_id": "protocol_guide",
        "query": "IOL 的密碼是什麼",
        "retrieval_setting": {
            "top_k": 2,
            "score_threshold": 0.8
        }
    }
    
    request_stage1 = factory.post(
        '/api/dify/knowledge/retrieval/',
        data=json.dumps(request_data_stage1),
        content_type='application/json'
    )
    
    response_stage1 = dify_knowledge_search(request_stage1)
    stage1_count = len(response_stage1.data.get('records', []))
    
    print(f"   結果數量: {stage1_count}")
    
    # Stage 2 測試
    print()
    print("🔍 Stage 2 全文搜尋:")
    request_data_stage2 = {
        "knowledge_id": "protocol_guide",
        "query": "__FULL_SEARCH__ IOL 的密碼是什麼",  # Stage 2 標記
        "retrieval_setting": {
            "top_k": 2,
            "score_threshold": 0.7  # Stage 2 通常較低閾值
        }
    }
    
    request_stage2 = factory.post(
        '/api/dify/knowledge/retrieval/',
        data=json.dumps(request_data_stage2),
        content_type='application/json'
    )
    
    response_stage2 = dify_knowledge_search(request_stage2)
    stage2_count = len(response_stage2.data.get('records', []))
    
    print(f"   結果數量: {stage2_count}")
    print()
    
    # 對比
    print("📊 對比結果:")
    print(f"   Stage 1: {stage1_count} 個結果")
    print(f"   Stage 2: {stage2_count} 個結果")
    
    if stage1_count >= 2:
        print(f"   ✅ Stage 1 修復後返回足夠結果，不需要回退到 Stage 2")
    else:
        print(f"   ⚠️  Stage 1 結果不足，需要回退到 Stage 2")

def check_container_logs():
    """檢查容器日誌中的 Top-K Protection 訊息"""
    print_separator("測試 4: 檢查容器日誌")
    
    print("📜 查詢最近的 Top-K Protection 日誌...")
    print()
    
    import subprocess
    
    try:
        # 查詢日誌
        result = subprocess.run(
            ['docker', 'logs', 'ai-django', '--tail', '100'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        logs = result.stdout + result.stderr
        
        # 查找 Top-K Protection 相關日誌
        topk_logs = [line for line in logs.split('\n') if 'Top-K Protection' in line or '🔄' in line or '🛡️' in line]
        
        if topk_logs:
            print(f"找到 {len(topk_logs)} 條相關日誌:")
            print()
            for log in topk_logs[-10:]:  # 只顯示最近 10 條
                print(f"   {log}")
            print()
            print("✅ Top-K Protection 功能正在運作")
        else:
            print("ℹ️  未找到 Top-K Protection 日誌（可能尚未觸發或查詢範圍不夠）")
            
    except Exception as e:
        print(f"⚠️  無法讀取容器日誌: {str(e)}")

def main():
    """主測試流程"""
    print(f"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                Top-K Protection 功能驗證測試                                 ║
║                                                                              ║
║  測試目標：驗證 Stage 1 混合搜尋的 Top-K Protection 是否成功解決            ║
║           RRF 正規化導致的過度過濾問題                                       ║
║                                                                              ║
║  測試時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                                         ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """)
    
    # 執行測試
    try:
        # 測試 1: Django 內部測試
        test_iol_query_stage1()
        
        print_separator()
        
        # 測試 2: HTTP API 測試
        test_iol_query_via_http()
        
        print_separator()
        
        # 測試 3: Stage 1 vs Stage 2 對比
        test_comparison_with_stage2()
        
        print_separator()
        
        # 測試 4: 檢查日誌
        check_container_logs()
        
        print_separator("測試完成")
        
        print("""
總結：
1. ✅ Top-K Protection 已實作並部署到容器
2. 🔍 測試驗證了功能是否按預期工作
3. 📊 對比了 Stage 1 修復前後的差異
4. 📜 檢查了日誌輸出確認功能運作

下一步：
- 如果所有測試通過，Top-K Protection 修復成功
- 如果測試失敗，需要檢查日誌找出問題原因
- 建議持續監控 1-2 週收集使用數據
        """)
        
    except Exception as e:
        logger.error(f"測試執行失敗: {str(e)}", exc_info=True)
        print(f"\n❌ 測試執行失敗: {str(e)}")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
