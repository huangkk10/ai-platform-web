#!/usr/bin/env python3
"""
測試改進後的 OCR 解析器
專門處理測試時間和平均帶寬的問題
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from library.data_processing.ocr_analyzer import create_ocr_analyzer

def test_problematic_ai_response():
    """測試有問題的 AI 回答格式"""
    
    print("🧪 測試有問題的 AI 回答解析")
    print("=" * 80)
    
    # 模擬從資料庫截圖中看到的 AI 回答格式
    problematic_ai_response = """## 📊 測試總結

| 項目 | 結果 |
|------|------|
| **Storage Benchmark Score** | **6883** | 代表整體讀寫表現 |
| **裝置型號** | **KINGSTON SFYR2S1TO** | SSD 內部標示 |
| **韌體版本** | **SGWO904A** | 內部固件 |
| **測試時間** | **35 s（主要考慮載入時間）** | 由系統日誌取得 |
| **軟體版本** | **3DMark 2.28.8228** | 目前使用版本（有可更新） |

---

**📋 子測項表格**

| 測試項目 | Bandwidth | 平均存取時間 |
|----------|-----------|--------------|
| **Overall Test** | 1174.89 MB/s | 26 ps |
| Load **Battlefield** | 2228.69 MB/s | 35 s |
| Load **Call of Duty: Black Ops 4** | 1673.37 MB/s | 40 µs |
| Load **Overwatch** | 917.74 MB/s | 26 µs |
| **Save Export XML Record game** | 453.25 MB/s | 19 ps |
| **Validate Install game** | 597.60 MB/s | 22 ps |
| **Save game** | 506.52 MB/s | 14 s |
| **Move game** | 6580.81 MB/s | 39 s |

> **說明**  
> *「ps」＝皮秒、µs＝微秒，s＝秒。平均帶寬為 1174.89 MB/s，表現良好。*"""
    
    # 創建 OCR 分析器
    ocr_analyzer = create_ocr_analyzer()
    
    print(f"📄 測試有問題的 AI 回答:")
    print(f"回答長度: {len(problematic_ai_response)} 字符")
    print("-" * 60)
    print(problematic_ai_response[:300] + "...")
    print("-" * 60)
    
    # 解析 AI 回答
    parsed_data = ocr_analyzer.parse_storage_benchmark_table(problematic_ai_response)
    
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
            
        # 特別檢查我們的改進
        print(f"\n🔍 特殊檢查:")
        
        # 檢查測試時間是否被正確識別為無效
        test_datetime = parsed_data.get('test_datetime')
        if test_datetime == "35 s（主要考慮載入時間）":
            print(f"    ❌ 測試時間仍然是無效格式: {test_datetime}")
        elif test_datetime is None:
            print(f"    ✅ 測試時間正確識別為無效，設為 None")
        else:
            print(f"    🤔 測試時間: {test_datetime}")
            
        # 檢查平均帶寬是否被備用解析找到
        average_bandwidth = parsed_data.get('average_bandwidth')
        if average_bandwidth and "1174.89" in str(average_bandwidth):
            print(f"    ✅ 平均帶寬成功提取: {average_bandwidth}")
        else:
            print(f"    ❌ 平均帶寬未能提取: {average_bandwidth}")
    else:
        print("  ❌ 解析失敗，沒有返回任何數據")
    
    print("-" * 60)

def test_bandwidth_extraction():
    """測試帶寬提取的各種情況"""
    
    print("\n🌐 測試帶寬提取功能")
    print("=" * 80)
    
    test_cases = [
        ("Overall Test | 1174.89 MB/s | 26 ps", "1174.89 MB/s"),
        ("平均帶寬為 1174.89 MB/s，表現良好", "1174.89 MB/s"),
        ("bandwidth: 2500.5 MB/s", "2500.5 MB/s"),
        ("速度: 3000 MB/s", "3000 MB/s"),
        ("測試顯示 1200.45 mb/s 的結果", "1200.45 MB/s"),
        ("沒有帶寬信息的文本", None),
    ]
    
    ocr_analyzer = create_ocr_analyzer()
    
    for text, expected in test_cases:
        result = ocr_analyzer._extract_bandwidth_fallback(text)
        status = "✅" if result == expected else "❌"
        print(f"  {status} '{text[:40]}...' -> {repr(result)} (期望: {repr(expected)})")

if __name__ == "__main__":
    test_problematic_ai_response()
    test_bandwidth_extraction()
    print("\n🎯 測試完成！")