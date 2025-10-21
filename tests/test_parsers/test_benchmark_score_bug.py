#!/usr/bin/env python3
"""
緊急測試：檢查為什麼 benchmark_score 解析錯誤
基於用戶提供的實際 AI 回答來測試
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from library.data_processing.ocr_analyzer import create_ocr_analyzer

def test_actual_ai_response():
    """測試實際的 AI 回答"""
    
    print("🚨 緊急測試：benchmark_score 解析錯誤問題")
    print("=" * 80)
    
    # 基於用戶截圖重建的 AI 回答
    actual_ai_response = """## 📊 測試總結

| 項目 | 結果 |
|------|------|
| **存儲基準分數** | **3467** |
| **平均帶寬** | **596.38 MB/s** |
| **裝置型號** | **YMTC 42QS2ED08B56MC** |
| **韌體版本** | **LN13D303** |
| **測試時間** | **2025-07-31 12:42 +08:00** |
| **軟體版本** | **3DMark Professional Edition v2.28.8228 (最新為 v2.30.8330.0)** |

---

**其他詳細資訊...**"""
    
    print(f"📄 測試實際 AI 回答:")
    print(f"回答長度: {len(actual_ai_response)} 字符")
    print("-" * 60)
    print(actual_ai_response)
    print("-" * 60)
    
    # 創建 OCR 分析器
    ocr_analyzer = create_ocr_analyzer()
    
    # 解析 AI 回答
    parsed_data = ocr_analyzer.parse_storage_benchmark_table(actual_ai_response)
    
    print(f"\n📊 解析結果:")
    print(f"  解析欄位數量: {len(parsed_data) if parsed_data else 0}")
    
    if parsed_data:
        # 重點檢查 benchmark_score
        benchmark_score = parsed_data.get('benchmark_score')
        print(f"\n🎯 關鍵檢查:")
        print(f"  benchmark_score: {repr(benchmark_score)}")
        
        if benchmark_score == 3467:
            print(f"  ✅ benchmark_score 解析正確！")
        elif benchmark_score == 2981:
            print(f"  ❌ benchmark_score 被錯誤解析為 2981")
        else:
            print(f"  ⚠️ benchmark_score 是其他值: {benchmark_score}")
        
        # 檢查其他重要欄位
        key_fields = ['average_bandwidth', 'device_model', 'firmware_version', 'test_datetime']
        print(f"\n📋 其他重要欄位:")
        for field in key_fields:
            value = parsed_data.get(field)
            print(f"  {field}: {repr(value)}")
            
        # 檢查是否有計算邏輯覆蓋了解析值
        print(f"\n🔧 檢查計算邏輯:")
        if 'read_speed' in parsed_data or 'write_speed' in parsed_data:
            print(f"  read_speed: {parsed_data.get('read_speed')}")
            print(f"  write_speed: {parsed_data.get('write_speed')}")
            print(f"  ⚠️ 可能有計算邏輯覆蓋了原始 benchmark_score")
        
    else:
        print("  ❌ 解析完全失敗")
    
    print("-" * 60)

if __name__ == "__main__":
    test_actual_ai_response()
    print("\n🎯 緊急測試完成！")