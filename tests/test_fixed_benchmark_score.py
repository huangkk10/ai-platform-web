#!/usr/bin/env python3
"""
測試修正後的 benchmark_score 解析功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from library.data_processing.ocr_analyzer import create_ocr_analyzer

def test_fixed_benchmark_score():
    """測試修正後的 benchmark_score 解析"""
    
    print("🧪 測試修正後的 benchmark_score 解析功能")
    print("=" * 80)
    
    # 模擬用戶實際的 AI 回答格式
    user_ai_response = """測試總結

| 項目 | 結果 |
|------|------|
| 存儲基準分數 | 3467 |
| 平均帶寬 | 596.38 MB/s |
| 裝置型號 | YMTC 42QS2ED08B56MC |
| 韌體版本 | LN13D303 |
| 測試時間 | 2025-07-31 12:42 +08:00 |
| 軟體版本 | 3DMark Professional Edition v2.28.8228 (最新為 v2.30.8330.0) |"""
    
    # 創建 OCR 分析器
    ocr_analyzer = create_ocr_analyzer()
    
    print(f"📄 測試用戶的 AI 回答:")
    print(f"回答長度: {len(user_ai_response)} 字符")
    print("-" * 60)
    print(user_ai_response)
    print("-" * 60)
    
    # 解析 AI 回答
    parsed_data = ocr_analyzer.parse_storage_benchmark_table(user_ai_response)
    
    print(f"\n📊 解析結果:")
    print(f"  解析欄位數量: {len(parsed_data) if parsed_data else 0}")
    
    if parsed_data:
        # 重點檢查的欄位
        key_fields = [
            'benchmark_score', 
            'average_bandwidth', 
            'device_model', 
            'firmware_version', 
            'test_datetime', 
            'benchmark_version'
        ]
        
        print(f"  重要欄位檢查:")
        for field in key_fields:
            value = parsed_data.get(field)
            status = "✅" if value else "❌"
            print(f"    {status} {field}: {repr(value)}")
            
        # 🚨 關鍵檢查：benchmark_score 是否正確
        benchmark_score = parsed_data.get('benchmark_score')
        if benchmark_score == 3467:
            print(f"\n🎉 ✅ BENCHMARK_SCORE 解析正確: {benchmark_score}")
        elif benchmark_score == 2981:
            print(f"\n❌ BENCHMARK_SCORE 仍然錯誤: {benchmark_score} (應該是 3467)")
        else:
            print(f"\n🤔 BENCHMARK_SCORE 解析結果: {benchmark_score}")
            
        # 檢查平均帶寬是否正確
        average_bandwidth = parsed_data.get('average_bandwidth')
        if average_bandwidth and "596.38" in str(average_bandwidth):
            print(f"✅ 平均帶寬解析正確: {average_bandwidth}")
        else:
            print(f"❌ 平均帶寬解析錯誤: {average_bandwidth}")
    else:
        print("  ❌ 解析失敗，沒有返回任何數據")
    
    print("-" * 60)

if __name__ == "__main__":
    test_fixed_benchmark_score()
    print("\n🎯 測試完成！")