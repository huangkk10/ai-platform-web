#!/usr/bin/env python3
"""
測試方案 C - Threshold 完全參數化

測試流程：
1. 模擬 Dify Studio 傳遞不同的 threshold
2. 驗證 threshold 是否正確傳遞到 SQL 查詢
3. 檢查結果是否符合預期

測試案例：
- threshold=0.50 → 應該返回 3 個結果（包含 UNH-IOL 51%）
- threshold=0.70 → 應該返回 2 個結果（排除 UNH-IOL）
- threshold=0.80 → 應該返回 0 個結果（全部低於 0.80）
"""

import requests
import json

# API 端點
API_URL = "http://10.10.172.127/api/dify/knowledge/retrieval/"

def test_threshold_parameterization():
    """測試 threshold 完全參數化"""
    
    print("=" * 80)
    print("🧪 測試方案 C - Threshold 完全參數化")
    print("=" * 80)
    
    # 測試案例
    test_cases = [
        {
            "name": "測試 1: 低 threshold (0.50) - 應該包含 UNH-IOL",
            "threshold": 0.50,
            "expected_min_results": 3,
            "should_include_unh": True
        },
        {
            "name": "測試 2: 標準 threshold (0.70) - 應該排除 UNH-IOL",
            "threshold": 0.70,
            "expected_min_results": 2,
            "should_include_unh": False
        },
        {
            "name": "測試 3: 高 threshold (0.80) - 應該幾乎無結果",
            "threshold": 0.80,
            "expected_max_results": 0,
            "should_include_unh": False
        },
        {
            "name": "測試 4: Dify 預設 threshold (0.75) - Protocol Assistant 標準",
            "threshold": 0.75,
            "expected_min_results": 2,
            "should_include_unh": False
        }
    ]
    
    query = "UNH-IOL"
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 80}")
        print(f"📋 {test_case['name']}")
        print(f"{'─' * 80}")
        
        # 構建請求
        payload = {
            "knowledge_id": "protocol_assistant",
            "query": query,
            "retrieval_setting": {
                "top_k": 5,
                "score_threshold": test_case["threshold"]  # ✅ 從 Dify Studio 傳入
            }
        }
        
        print(f"\n📤 請求參數:")
        print(f"   query: '{query}'")
        print(f"   threshold: {test_case['threshold']}")
        print(f"   top_k: 5")
        
        try:
            # 發送請求
            response = requests.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                records = result.get('records', [])
                
                print(f"\n📥 回應結果:")
                print(f"   狀態碼: {response.status_code}")
                print(f"   結果數量: {len(records)}")
                
                if records:
                    print(f"\n   結果詳情:")
                    for j, record in enumerate(records, 1):
                        title = record.get('title', 'Unknown')
                        score = record.get('score', 0)
                        print(f"   {j}. {title} - 相似度: {score:.2%}")
                    
                    # 檢查是否包含 UNH-IOL
                    unh_found = any('UNH' in r.get('title', '') for r in records)
                    
                    # 驗證結果
                    print(f"\n✅ 驗證:")
                    
                    # 檢查結果數量
                    if 'expected_min_results' in test_case:
                        if len(records) >= test_case['expected_min_results']:
                            print(f"   ✓ 結果數量符合預期 (>= {test_case['expected_min_results']})")
                        else:
                            print(f"   ✗ 結果數量不符 (預期 >= {test_case['expected_min_results']}, 實際 {len(records)})")
                    
                    if 'expected_max_results' in test_case:
                        if len(records) <= test_case['expected_max_results']:
                            print(f"   ✓ 結果數量符合預期 (<= {test_case['expected_max_results']})")
                        else:
                            print(f"   ✗ 結果數量不符 (預期 <= {test_case['expected_max_results']}, 實際 {len(records)})")
                    
                    # 檢查 UNH-IOL 是否存在
                    if test_case['should_include_unh']:
                        if unh_found:
                            print(f"   ✓ 包含 UNH-IOL 相關結果")
                        else:
                            print(f"   ✗ 預期應包含 UNH-IOL，但未找到")
                    else:
                        if not unh_found:
                            print(f"   ✓ 正確排除 UNH-IOL (低於 threshold)")
                        else:
                            print(f"   ✗ 不應包含 UNH-IOL，但找到了")
                    
                    # 檢查所有結果的分數是否 >= threshold
                    all_above_threshold = all(r.get('score', 0) >= test_case['threshold'] for r in records)
                    if all_above_threshold:
                        print(f"   ✓ 所有結果分數都 >= {test_case['threshold']}")
                    else:
                        print(f"   ✗ 部分結果分數低於 threshold")
                        for r in records:
                            if r.get('score', 0) < test_case['threshold']:
                                print(f"      - {r.get('title', 'Unknown')}: {r.get('score', 0):.2%} < {test_case['threshold']}")
                
                else:
                    print(f"\n   無結果返回")
                    if 'expected_max_results' in test_case and test_case['expected_max_results'] == 0:
                        print(f"   ✓ 符合預期（threshold 過高，無符合條件的結果）")
                    else:
                        print(f"   ⚠️ 無結果（可能是 threshold 設定過高或查詢無匹配）")
            
            else:
                print(f"\n❌ 請求失敗:")
                print(f"   狀態碼: {response.status_code}")
                print(f"   錯誤: {response.text}")
        
        except Exception as e:
            print(f"\n❌ 測試失敗: {str(e)}")
    
    print(f"\n{'=' * 80}")
    print("🎉 測試完成！")
    print("=" * 80)
    
    print(f"\n📊 總結:")
    print(f"   - 測試了 {len(test_cases)} 個不同的 threshold 設定")
    print(f"   - 驗證了 threshold 是否從 Dify Studio 一路傳遞到 SQL 查詢")
    print(f"   - 確認了結果是否正確過濾")
    print(f"\n💡 建議:")
    print(f"   1. 在 Dify 工作室中設定 threshold=0.75（Protocol Assistant 推薦值）")
    print(f"   2. 根據實際需求調整 threshold（提高 = 更嚴格，降低 = 更寬鬆）")
    print(f"   3. 不需要重啟容器，即時生效！")


if __name__ == "__main__":
    test_threshold_parameterization()
