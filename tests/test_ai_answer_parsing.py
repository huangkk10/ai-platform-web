#!/usr/bin/env python3
"""
測試 AI 回答解析功能
專門用於調試從 Web UI 上傳的圖片和解析邏輯
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../'))

from library.data_processing.ocr_analyzer import create_ocr_analyzer

def test_ai_answer_parsing():
    """測試 AI 回答解析功能"""
    
    print("🧪 測試 AI 回答解析功能")
    print("=" * 80)
    
    # 模擬真實的 AI 回答內容（來自測試結果）
    sample_ai_answers = [
        # 第一個 AI 回答樣本
        """**📊 測試總結**  
| 項目 | 數值 | 備註 |
|------|------|------|
| **Storage Benchmark Score** | **6883** | 代表整體讀寫表現 |
| **平均頻寬** | **1174.89 MB/s** | 讀寫速率（平均） |
| **裝置型號** | **KINGSTON SFYR2S1TO** | SSD 內部標示 |
| **韌體版本** | **SGWO904A** | 內部固件 |
| **測試時間** | **2025‑09‑06 16:13 +08:00** | 由系統日誌取得 |
| **軟體版本** | **3DMark 2.28.8228** | 目前使用版本（有可更新） |""",
        
        # 第二個 AI 回答樣本
        """## 📊 測試總結

| 項目 | 內容 |
|------|------|
| **3DMark 分數** | **6883** |
| **平均帶寬** | **1174.89 MB/s** |
| **測試日期 & 時間** | 2025‑09‑06 16:13 +08:00 |
| **SSD 型號** | **KINGSTON SFYR2S1TO** |
| **固件版本** | **SGWO904A** |
| **3DMark 版本** | **Professional Edition 2.28.8228** (最新 2.29.8294.0) |""",
        
        # 第三個 AI 回答樣本
        """## 📊 測試總結

| 項目 | 數值 |
|------|------|
| **測試總分（Storage Benchmark Score）** | **6883** |
| **平均帶寬（Average Bandwidth）** | **1174.89 MB/s** |
| **裝置型號** | **KINGSTON SFYR2S1TO** |
| **韌體版本** | **SGWO904A** |
| **測試日期與時間** | **2025‑09‑06 16:13 +08:00** |
| **3DMark 版本** | **2.28.8228**（最新：2.29.8294.0） |"""
    ]
    
    # 創建 OCR 分析器
    ocr_analyzer = create_ocr_analyzer()
    
    for i, ai_answer in enumerate(sample_ai_answers, 1):
        print(f"\n📄 測試樣本 {i}:")
        print("-" * 60)
        print(f"AI 回答長度: {len(ai_answer)} 字符")
        print(f"前 200 字符: {ai_answer[:200]}...")
        print("-" * 60)
        
        # 解析 AI 回答
        parsed_data = ocr_analyzer.parse_storage_benchmark_table(ai_answer)
        
        print(f"📊 解析結果:")
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
        else:
            print("  ❌ 解析失敗，沒有返回任何數據")
        
        print("-" * 60)

def test_individual_patterns():
    """測試個別的正則表達式模式"""
    
    print("\n🔍 測試個別正則表達式模式")
    print("=" * 80)
    
    import re
    
    # 測試分數解析
    score_patterns = [
        r'\|\s*\*\*3DMark\s*分數\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
        r'\|\s*\*\*Storage Benchmark Score\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
        r'\|\s*\*\*測試總分[^|]*\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|'
    ]
    
    test_texts = [
        "| **3DMark 分數** | **6883** |",
        "| **Storage Benchmark Score** | **6883** | 代表整體讀寫表現 |",
        "| **測試總分（Storage Benchmark Score）** | **6883** |"
    ]
    
    print("📊 測試分數解析:")
    for text in test_texts:
        print(f"  測試文本: {text}")
        for pattern in score_patterns:
            match = re.search(pattern, text)
            if match:
                print(f"    ✅ 匹配成功: {match.group(1)}")
                break
        else:
            print(f"    ❌ 所有模式都未匹配")
    
    # 測試帶寬解析
    bandwidth_patterns = [
        r'\|\s*\*\*平均帶寬\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
        r'\|\s*\*\*平均頻寬\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
        r'\|\s*\*\*平均帶寬[^|]*\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|'
    ]
    
    bandwidth_texts = [
        "| **平均帶寬** | **1174.89 MB/s** |",
        "| **平均頻寬** | **1174.89 MB/s** | 讀寫速率（平均） |",
        "| **平均帶寬（Average Bandwidth）** | **1174.89 MB/s** |"
    ]
    
    print("\n🌐 測試帶寬解析:")
    for text in bandwidth_texts:
        print(f"  測試文本: {text}")
        for pattern in bandwidth_patterns:
            match = re.search(pattern, text)
            if match:
                print(f"    ✅ 匹配成功: {match.group(1)}")
                break
        else:
            print(f"    ❌ 所有模式都未匹配")

if __name__ == "__main__":
    test_ai_answer_parsing()
    test_individual_patterns()
    print("\n🎯 測試完成！")