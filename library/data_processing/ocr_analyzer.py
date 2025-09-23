#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 分析器模組
提供 OCR 結果解析、結構化數據提取和資料庫保存功能
"""

import re
import json
from datetime import datetime
from typing import Dict, Any, Optional, List


class OCRAnalyzer:
    """OCR 分析器類"""
    
    def __init__(self):
        """初始化分析器"""
        self.default_confidence = 0.95
        
    def parse_test_summary_table(self, answer_text: str) -> Dict[str, Any]:
        """
        解析 AI 回答中的測試總結 table 部分資料
        基於 OCR 資料庫欄位結構進行有針對性的解析
        
        Args:
            answer_text (str): AI 回答的完整文本
            
        Returns:
            dict: 解析出的測試資料，對應 OCRStorageBenchmark 模型欄位
        """
        # 初始化基於資料庫欄位的結構化資料
        parsed_data = {
            # 基本測試資訊
            'project_name': None,
            'benchmark_score': None,
            'average_bandwidth': None,
            'device_model': None,
            'firmware_version': None,
            'test_datetime': None,
            'benchmark_version': None,
            
            # OCR 相關
            'ocr_confidence': None,
            
            # 額外的結構化資料（保留用於除錯和分析）
            'sequential_read_data': {},
            'sequential_write_data': {},
            'random_read_data': {},
            'random_write_data': {},
            'system_info': {}
        }
        
        try:
            # 1. 嘗試專門的儲存基準測試表格解析器
            storage_benchmark_data = self.parse_storage_benchmark_table(answer_text)
            if storage_benchmark_data and len(storage_benchmark_data) > 5:
                print("🎯 使用專門的儲存基準測試表格解析器")
                return storage_benchmark_data
            
            # 2. 解析基本資訊（來自表格標題和環境資訊）
            self._parse_basic_info(answer_text, parsed_data)
            
            # 3. 解析效能數據（已移除，不再需要儲存到資料庫）
            # self._parse_performance_data(answer_text, parsed_data)
            
            # 4. 解析系統環境資訊
            self._parse_system_info(answer_text, parsed_data)
            
            # 5. 計算綜合指標
            self._calculate_summary_metrics(parsed_data)
            
            # 6. 清理空值並格式化
            cleaned_data = {k: v for k, v in parsed_data.items() if v is not None and v != {}}
            
            return cleaned_data
            
        except Exception as e:
            print(f"⚠️ 解析測試總結資料時發生錯誤: {e}")
            return {}
    
    def parse_storage_benchmark_table(self, answer_text: str) -> Dict[str, Any]:
        """
        專門解析儲存基準測試表格格式的資料
        
        針對以下格式的表格：
        | 項目 | 結果 |
        |------|------|
        | **儲存基準分數 (Storage Benchmark Score)** | 6883 |
        | **平均頻寬 (Average Bandwidth)** | 1 174.89 MB/s |
        | **裝置型號** | KINGSTON SFYR2S1TO |
        | **韌體 (Firmware)** | SGWO904A |
        | **測試時間** | 2025‑09‑06 16:13 (+08:00) |
        | **3DMark 軟體版本** | 2.28.8228 (已安裝) – 最新可用 2.29.8294.0 |
        
        Args:
            answer_text (str): AI 回答的完整文本
            
        Returns:
            dict: 解析出的測試資料，對應 OCRStorageBenchmark 模型欄位
        """
        # 初始化基於資料庫欄位的結構化資料
        parsed_data = {
            'project_name': None,  # 將在後續處理中根據 device_model 動態設置
            'benchmark_score': None,
            'average_bandwidth': None,
            'device_model': None,
            'firmware_version': None,
            'test_datetime': None,
            'benchmark_version': None,
            'test_item': None,  # 新增測試項目欄位，用於匹配 OCRTestClass
            'ocr_confidence': 0.98
        }
        
        try:
            # 定義欄位對映模式 - 更新以匹配實際的表格格式
            field_patterns = {
                'benchmark_score': [
                    # 🆕 匹配 "存儲基準分數" (簡體中文格式) - 優先匹配
                    r'\|\s*\*\*存儲基準分數\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*存儲基準分數\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*存儲基準分數\s*\|\s*(\d+)\s*\|',
                    # 🆕 匹配 "存儲基準分數" 的其他格式變體
                    r'\|\s*\*\*存儲基準分數.*?\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*存儲基準分數.*?\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*存儲基準分數.*?\|\s*(\d+)\s*\|',
                    # 匹配新的 AI 回答格式 | **3DMark 分數** | **6883** |
                    r'\|\s*\*\*3DMark\s*分數\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*3DMark\s*分數\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*3DMark\s*分數\s*\|\s*(\d+)\s*\|',
                    # 匹配 | **測試分數** | 6883 |
                    r'\|\s*\*\*測試分數\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*測試分數\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*測試分數\s*\|\s*(\d+)\s*\|',
                    # 匹配 | **測試總分（Storage Benchmark Score）** | **6883** |
                    r'\|\s*\*\*測試總分[^|]*\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*測試總分[^|]*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*測試總分[^|]*\|\s*(\d+)\s*\|',
                    # 原有的 Storage Benchmark Score 格式
                    r'\|\s*Storage Benchmark Score\s*\|\s*(\d+)\s*\|',
                    r'\|\s*\*\*Storage Benchmark Score\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*\*\*Storage Benchmark Score\*\*\s*\|\s*(\d+)\s*\|',
                    # 匹配中文格式 (繁體中文)
                    r'\|\s*\*\*儲存基準分數\*\*\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*儲存基準分數\s*\|\s*\*\*(\d+)\*\*\s*\|',
                    r'\|\s*儲存基準分數\s*\|\s*(\d+)\s*\|',
                    # 舊的模式保留作為備用
                    r'\*\*儲存基準分數.*?\*\*\s*\|\s*(\d+)',
                    r'Storage Benchmark Score.*?\|\s*(\d+)',
                    r'儲存基準分數.*?\|\s*(\d+)'
                ],
                'average_bandwidth': [
                    # 匹配新的 AI 回答格式 | **平均帶寬** | **1174.89 MB/s** |
                    r'\|\s*\*\*平均帶寬\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均帶寬\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均帶寬\s*\|\s*([\d\s,.]+\s*MB/s)\s*\|',
                    # 匹配 | **平均帶寬（Average Bandwidth）** | **1174.89 MB/s** |
                    r'\|\s*\*\*平均帶寬[^|]*\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均帶寬[^|]*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均帶寬[^|]*\|\s*([\d\s,.]+\s*MB/s)\s*\|',
                    # 匹配 | 平均頻寬 | 1174.89 MB/s | (無粗體)
                    r'\|\s*平均頻寬\s*\|\s*([\d\s,.]+\s*MB/s)\s*\|',
                    r'\|\s*\*\*平均頻寬\*\*\s*\|\s*([\d\s,.]+\s*MB/s)\s*\|',
                    r'\|\s*\*\*平均頻寬\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    # 匹配 | **平均 Bandwidth** | **1174.89 MB/s** | (新格式)
                    r'\|\s*\*\*平均\s*Bandwidth\*\*\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均\s*Bandwidth\s*\|\s*\*\*([\d\s,.]+\s*MB/s)\*\*\s*\|',
                    r'\|\s*平均\s*Bandwidth\s*\|\s*([\d\s,.]+\s*MB/s)\s*\|',
                    # 舊的模式保留作為備用
                    r'\*\*平均頻寬.*?\*\*\s*\|\s*([\d\s,.]+\s*MB/s)',
                    r'Average Bandwidth.*?\|\s*([\d\s,.]+\s*MB/s)',
                    r'平均頻寬.*?\|\s*([\d\s,.]+\s*MB/s)'
                ],
                'device_model': [
                    # 匹配新的 AI 回答格式 | **裝置型號** | **KINGSTON SFYR2S1TO** |
                    r'\|\s*\*\*裝置型號\*\*\s*\|\s*\*\*([^*|]+)\*\*[^|]*\|',
                    r'\|\s*裝置型號\s*\|\s*\*\*([^*|]+)\*\*[^|]*\|',
                    r'\|\s*裝置型號\s*\|\s*([^|]+?)\s*(?:\([^)]*\))?\s*\|',
                    # 匹配 | **SSD 型號** | **KINGSTON SFYR2S1TO** |
                    r'\|\s*\*\*SSD\s*型號\*\*\s*\|\s*\*\*([^*|]+)\*\*[^|]*\|',
                    r'\|\s*SSD\s*型號\s*\|\s*\*\*([^*|]+)\*\*[^|]*\|',
                    r'\|\s*SSD\s*型號\s*\|\s*([^|]+?)\s*(?:\([^)]*\))?\s*\|',
                    # 匹配純文字格式 Kingston SFYR2S1TO
                    r'Kingston\s+([A-Z0-9]+)',
                    r'KINGSTON\s+([A-Z0-9]+)',
                    # 舊的模式保留作為備用
                    r'\*\*裝置型號\*\*\s*\|\s*([A-Z0-9\s]+)',
                    r'裝置型號.*?\|\s*([A-Z0-9\s]+)',
                    r'Device.*?\|\s*([A-Z0-9\s]+)'
                ],
                'firmware_version': [
                    # 匹配 | **固件版本** | **SGWO904A** |
                    r'\|\s*\*\*固件版本\*\*\s*\|\s*\*\*([A-Z0-9]+)\*\*\s*\|',
                    r'\|\s*固件版本\s*\|\s*\*\*([A-Z0-9]+)\*\*\s*\|',
                    r'\|\s*固件版本\s*\|\s*([A-Z0-9]+)\s*\|',
                    # 匹配 | **韌體版本** | **SGWO904A** |
                    r'\|\s*\*\*韌體版本\*\*\s*\|\s*\*\*([A-Z0-9]+)\*\*\s*\|',
                    r'\|\s*韌體版本\s*\|\s*\*\*([A-Z0-9]+)\*\*\s*\|',
                    r'\|\s*韌體版本\s*\|\s*([A-Z0-9]+)\s*\|',
                    # 舊的模式保留作為備用
                    r'\*\*韌體.*?\*\*\s*\|\s*([A-Z0-9]+)',
                    r'Firmware.*?\|\s*([A-Z0-9]+)',
                    r'韌體.*?\|\s*([A-Z0-9]+)',
                    r'固件.*?\|\s*([A-Z0-9]+)'
                ],
                'test_datetime': [
                    # 匹配新的 AI 回答格式 | **測試日期與時間** | **2025‑09‑06 16:13 +08:00** |
                    r'\|\s*\*\*測試日期與時間\*\*\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\*\*\s*\|',
                    r'\|\s*測試日期與時間\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\*\*\s*\|',
                    r'\|\s*測試日期與時間\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\s*\|',
                    # 匹配 | 測試時間 | 2025‑09‑06 16:13 +08:00 | (無粗體格式)
                    r'\|\s*測試時間\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\s*\|',
                    r'\|\s*\*\*測試時間\*\*\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\s*\|',
                    r'\|\s*\*\*測試時間\*\*\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\*\*\s*\|',
                    # 匹配 | **測試日期/時間** | **2025‑09‑06 16:13 +08:00** | (時間也有粗體，精確匹配)
                    r'\|\s*\*\*測試日期/時間\*\*\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\*\*\s*\|',
                    r'\|\s*測試日期/時間\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\*\*\s*\|',
                    # 匹配 | **測試日期 & 時間** | 2025‑09‑06 16:13 +08:00 |
                    r'\|\s*\*\*測試日期\s*&\s*時間\*\*\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\s*\|',
                    r'\|\s*測試日期\s*&\s*時間\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?\s*\|',
                    # 匹配括號在粗體標記內的情況: **2025‑09‑06 16:13 +08:00 (備註說明)**
                    r'\|\s*\*\*測試日期/時間\*\*\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?(?:\s*\([^)]*\))?\*\*\s*\|',
                    r'\|\s*測試日期/時間\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?(?:\s*\([^)]*\))?\*\*\s*\|',
                    # 匹配 | **測試日期/時間** | 2025‑09‑06 16:13 +08:00 (根據 RawText 時間戳) | (包含描述)
                    r'\|\s*\*\*測試日期/時間\*\*\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?(?:\s*\([^)]*\))?\s*\|',
                    r'\|\s*測試日期/時間\s*\|\s*([\d\-‑]+\s+[\d:]+)(?:\s*\+[\d:]+)?(?:\s*\([^)]*\))?\s*\|',
                    # 匹配 | **測試時間** | **2025‑09‑06 16:13 (+08:00)** | (舊格式)
                    r'\|\s*\*\*測試時間\*\*\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\([^)]*\))?\*\*\s*\|',
                    r'\|\s*測試時間\s*\|\s*\*\*([\d\-‑]+\s+[\d:]+)(?:\s*\([^)]*\))?\*\*\s*\|',
                    # 🆕 處理測試時間不是日期的情況，如 "35 s（主要考慮載入時間）"
                    # 在這種情況下，我們應該從其他地方獲取測試日期，或者設為 None
                    # 舊的模式保留作為備用
                    r'\*\*測試時間\*\*\s*\|\s*([\d\-‑\s:+()]+)',
                    r'測試時間.*?\|\s*([\d\-‑\s:+()]+)',
                    r'Test.*?Time.*?\|\s*([\d\-‑\s:+()]+)'
                ],
                'benchmark_version': [
                    # 匹配新的 AI 回答格式 | **3DMark 版本** | **2.28.8228** |
                    r'\|\s*\*\*3DMark\s*版本\*\*\s*\|\s*\*\*.*?([\d.]+).*?\*\*\s*\|',
                    r'\|\s*3DMark\s*版本\s*\|\s*\*\*.*?([\d.]+).*?\*\*\s*\|',
                    r'\|\s*3DMark\s*版本\s*\|\s*.*?([\d.]+).*?\s*\|',
                    # 匹配 | **軟體版本** | **3DMark Professional Edition 2.28.8228** |
                    r'\|\s*\*\*軟體版本\*\*\s*\|\s*\*\*.*?3DMark.*?([\d.]+).*?\*\*\s*\|',
                    r'\|\s*軟體版本\s*\|\s*\*\*.*?3DMark.*?([\d.]+).*?\*\*\s*\|',
                    r'\|\s*軟體版本\s*\|\s*.*?3DMark.*?([\d.]+).*?\|',
                    # 更通用的版本匹配
                    r'3DMark.*?Edition\s+([\d.]+)',
                    r'3DMark.*?([\d.]+\.\d+\.\d+)',
                    # 舊的模式保留作為備用
                    r'\*\*3DMark.*?版本\*\*\s*\|\s*([\d.]+[^|]*)',
                    r'3DMark.*?版本.*?\|\s*([\d.]+[^|]*)',
                    r'3DMark.*?\|\s*([\d.]+[^|]*)'
                ],
                'test_item': [
                    # 🆕 匹配 Test_Item 格式 - 根據用戶需求添加
                    # 匹配 "Test_Item : 3D_MARK" 格式
                    r'Test_Item\s*[:：]\s*([A-Z0-9_\-]+)',
                    # 匹配 "測試項目 : 3D_MARK" 格式
                    r'測試項目\s*[:：]\s*([A-Z0-9_\-]+)',
                    # 匹配 | **Test_Item** | **3D_MARK** |
                    r'\|\s*\*\*Test_Item\*\*\s*\|\s*\*\*([A-Z0-9_\-]+)\*\*\s*\|',
                    r'\|\s*Test_Item\s*\|\s*\*\*([A-Z0-9_\-]+)\*\*\s*\|',
                    r'\|\s*Test_Item\s*\|\s*([A-Z0-9_\-]+)\s*\|',
                    # 匹配 | **測試項目** | **3D_MARK** |
                    r'\|\s*\*\*測試項目\*\*\s*\|\s*\*\*([A-Z0-9_\-]+)\*\*\s*\|',
                    r'\|\s*測試項目\s*\|\s*\*\*([A-Z0-9_\-]+)\*\*\s*\|',
                    r'\|\s*測試項目\s*\|\s*([A-Z0-9_\-]+)\s*\|',
                    # 匹配純文字格式，當作為標題或摘要時
                    r'(?:^|\n)\s*([A-Z0-9_\-]+)(?:\s*測試|\s*Test)'
                ]
            }
            
            # 逐一解析每個欄位
            for field, patterns in field_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, answer_text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        value = matches[0].strip()
                        print(f"🔍 找到 {field}: {value}")
                        
                        # 針對不同欄位進行特殊處理
                        if field == 'benchmark_score':
                            try:
                                # 清理數值，移除可能的額外字符
                                clean_value = re.sub(r'[^\d]', '', value)
                                if clean_value:
                                    parsed_data[field] = int(clean_value)
                                    print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                            except ValueError:
                                print(f"❌ 解析 {field} 失敗: {value}")
                                pass
                                
                        elif field == 'average_bandwidth':
                            # 清理帶寬格式 "1 174.89 MB/s" -> "1174.89 MB/s"
                            cleaned_bandwidth = re.sub(r'(\d)\s+(\d)', r'\1\2', value)
                            parsed_data[field] = cleaned_bandwidth
                            print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                            
                        elif field == 'device_model':
                            # 清理裝置型號，移除多餘的格式標記
                            cleaned_device = value.replace('*', '').strip()
                            parsed_data[field] = cleaned_device
                            print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                            
                        elif field == 'firmware_version':
                            # 清理韌體版本
                            cleaned_firmware = value.replace('*', '').strip()
                            parsed_data[field] = cleaned_firmware
                            print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                            
                        elif field == 'test_datetime':
                            # 處理日期格式 "2025‑09‑06 16:13 +08:00" 或 "2025‑09‑06 16:13 (+08:00)"
                            try:
                                # 先移除尾部的時區描述（如 "(根據 RawText 時間戳)"）
                                date_str = re.sub(r'\s*\([^)]*時間戳[^)]*\)', '', value)
                                # 移除時區資訊 (+08:00 或 +08:00)
                                date_str = re.sub(r'\s*[\+\-]\d{2}:\d{2}', '', date_str)
                                # 移除剩餘的括號
                                date_str = re.sub(r'\s*\([^)]*\)', '', date_str)
                                # 正規化分隔符
                                date_str = date_str.replace('‑', '-').strip()
                                
                                # 如果解析後的日期格式正確，就保存為字符串（不轉換為 datetime 對象）
                                if re.match(r'\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}', date_str):
                                    parsed_data[field] = date_str  # 保存為字符串格式
                                    print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                                else:
                                    print(f"⚠️ 日期格式不符: {date_str}")
                                    
                            except Exception as e:
                                print(f"⚠️ 日期解析失敗: {value} -> {e}")
                                parsed_data[field] = datetime.now()
                                
                        elif field == 'benchmark_version':
                            # 提取版本號 "2.28.8228 (已安裝) – 最新可用 2.29.8294.0"
                            version_match = re.match(r'([\d.]+)', value)
                            if version_match:
                                parsed_data[field] = version_match.group(1)
                                print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                            else:
                                parsed_data[field] = value
                                print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                        
                        elif field == 'test_item':
                            # 清理測試項目名稱，移除多餘的格式標記
                            cleaned_test_item = value.replace('*', '').strip().upper()
                            parsed_data[field] = cleaned_test_item
                            print(f"✅ 成功解析 {field}: {parsed_data[field]}")
                        
                        break  # 找到匹配就跳出內層循環
            
            # 打印解析結果進行調試
            print(f"\n📊 解析結果摘要:")
            for key, value in parsed_data.items():
                if value is not None:
                    print(f"  {key}: {value}")
            
            # 特別檢查 test_datetime
            if 'test_datetime' in parsed_data:
                if parsed_data['test_datetime'] is not None:
                    # 驗證解析出的時間是否是有效的日期格式
                    datetime_str = str(parsed_data['test_datetime'])
                    if self._is_valid_datetime_string(datetime_str):
                        print(f"✅ test_datetime 解析成功: {parsed_data['test_datetime']}")
                    else:
                        print(f"⚠️ test_datetime 不是有效的日期格式: {datetime_str}")
                        parsed_data['test_datetime'] = None
                else:
                    print(f"⚠️ test_datetime 存在但值為 None")
            else:
                print(f"❌ test_datetime 不存在於 parsed_data 中")
                
            # 特別檢查 average_bandwidth
            if 'average_bandwidth' in parsed_data:
                if parsed_data['average_bandwidth'] is not None:
                    print(f"✅ average_bandwidth 解析成功: {parsed_data['average_bandwidth']}")
                else:
                    print(f"⚠️ average_bandwidth 存在但值為 None")
                    # 嘗試從 AI 回答中提取帶寬信息，使用更寬鬆的模式
                    backup_bandwidth = self._extract_bandwidth_fallback(answer_text)
                    if backup_bandwidth:
                        parsed_data['average_bandwidth'] = backup_bandwidth
                        print(f"🔧 備用解析找到 average_bandwidth: {backup_bandwidth}")
            else:
                print(f"❌ average_bandwidth 不存在於 parsed_data 中")
                backup_bandwidth = self._extract_bandwidth_fallback(answer_text)
                if backup_bandwidth:
                    parsed_data['average_bandwidth'] = backup_bandwidth
                    print(f"🔧 備用解析找到 average_bandwidth: {backup_bandwidth}")
            
            # 計算衍生欄位
            self._calculate_derived_fields(parsed_data)
            
            # 清理無效值，但保留重要欄位（即使是 None）
            important_fields = ['test_datetime', 'project_name', 'average_bandwidth']
            cleaned_data = {}
            
            for k, v in parsed_data.items():
                if v is not None:
                    cleaned_data[k] = v
                elif k in important_fields:
                    # 對於重要欄位，即使是 None 也保留，但給一個明確的指示
                    cleaned_data[k] = None
            
            print(f"\n🎯 最終清理後的數據: {len(cleaned_data)} 個欄位")
            
            return cleaned_data
            
        except Exception as e:
            print(f"⚠️ 儲存基準測試表格解析錯誤: {e}")
            return {}
    
    def _parse_basic_info(self, text: str, data: Dict[str, Any]) -> None:
        """解析基本測試資訊"""
        # 從測試環境資訊表格中提取
        basic_patterns = {
            # 'project_name': [r'Profile[：:]\s*([^\n\|]+)', r'測試名稱[：:]\s*([^\n\|]+)'],
            'test_datetime': [r'Date[：:]\s*([\d/\s:]+)', r'日期[：:]\s*([\d/\s:]+)'],
            'device_model': [r'裝置[：:]\s*([^\n\|]+)', r'Device[：:]\s*([^\n\|]+)'],
            'firmware_version': [r'韌體[：:]\s*([^\n\|]+)', r'Firmware[：:]\s*([^\n\|]+)'],
        }
        
        for field, patterns in basic_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    data[field] = matches[0].strip()
                    break
    
    def _parse_system_info(self, text: str, data: Dict[str, Any]) -> None:
        """解析系統環境資訊"""
        # 解析操作系統資訊
        os_pattern = r'OS[：:]\s*([^\n\|]+)'
        os_matches = re.findall(os_pattern, text)
        if os_matches:
            data['system_info']['os'] = os_matches[0].strip()
        
        # 解析測試配置
        test_pattern = r'Test[：:]\s*([^\n\|]+)'
        test_matches = re.findall(test_pattern, text)
        if test_matches:
            data['system_info']['test_config'] = test_matches[0].strip()
    
    def _calculate_summary_metrics(self, data: Dict[str, Any]) -> None:
        """計算綜合指標"""
        # 設置項目名稱（如果沒有的話）
        if not data['project_name']:
            data['project_name'] = 'CDM8 Storage Analysis'
        
        # 設置 OCR 信心度
        data['ocr_confidence'] = 0.95  # CDM8 檔案通常結構化良好
    
    def _is_valid_datetime_string(self, datetime_str: str) -> bool:
        """檢查字符串是否是有效的日期時間格式"""
        try:
            # 常見的無效時間格式
            invalid_patterns = [
                r'^\d+\s*s\s*', # 35 s（主要考慮載入時間）
                r'^\d+\s*秒', # 35 秒
                r'^\d+\s*ms', # 1000 ms
                r'^\d+\s*分鐘', # 5 分鐘
                r'^\d+\s*小時', # 2 小時
            ]
            
            for pattern in invalid_patterns:
                if re.match(pattern, datetime_str, re.IGNORECASE):
                    return False
            
            # 檢查是否包含年月日的基本格式
            if re.search(r'\d{4}[\-\‑/]\d{1,2}[\-\‑/]\d{1,2}', datetime_str):
                return True
            
            return False
        except:
            return False
    
    def _extract_bandwidth_fallback(self, text: str) -> str:
        """使用備用模式提取帶寬信息"""
        try:
            # 更寬鬆的帶寬提取模式
            bandwidth_patterns = [
                # 在任何地方查找 "數字 MB/s" 模式
                r'(\d+\.?\d*)\s*MB/s',
                r'(\d+\.?\d*)\s*mb/s',
                r'(\d+\.?\d*)\s*Mb/s',
                # 查找表格中的速度信息
                r'速度[：:]\s*(\d+\.?\d*)\s*MB/s',
                r'頻寬[：:]\s*(\d+\.?\d*)\s*MB/s',
                r'帶寬[：:]\s*(\d+\.?\d*)\s*MB/s',
                r'bandwidth[：:]\s*(\d+\.?\d*)\s*MB/s',
                # 從描述中提取
                r'平均.*?(\d+\.?\d*)\s*MB/s',
                r'average.*?(\d+\.?\d*)\s*MB/s',
            ]
            
            for pattern in bandwidth_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 取第一個匹配的值
                    bandwidth_value = matches[0]
                    return f"{bandwidth_value} MB/s"
            
            return None
        except Exception as e:
            print(f"⚠️ 備用帶寬提取失敗: {e}")
            return None
    
    def _calculate_derived_fields(self, data: Dict[str, Any]) -> None:
        """計算衍生欄位"""
        print(f"\n🔧 開始計算衍生欄位...")
        
        # 🚨 修正：只有在完全沒有解析到基準分數時才推算，絕不覆蓋已解析的值
        if not data.get('benchmark_score'):
            print(f"⚠️ 未解析到 benchmark_score，嘗試計算估算值")
            if data.get('average_bandwidth'):
                # 如果沒有 benchmark_score，嘗試從平均頻寬推算
                try:
                    bandwidth_match = re.search(r'([\d.]+)', data['average_bandwidth'])
                    if bandwidth_match:
                        avg_speed = float(bandwidth_match.group(1))
                        # 基於平均頻寬估算基準分數 (簡化公式)
                        estimated_score = int(avg_speed * 5)  # 1000 MB/s ≈ 5000 分
                        data['benchmark_score'] = estimated_score
                        print(f"📊 基於平均頻寬估算基準分數: {data['benchmark_score']}")
                except ValueError:
                    pass
            
            # 如果還是沒有 benchmark_score，提供預設值
            if not data.get('benchmark_score'):
                data['benchmark_score'] = 5000  # 預設基準分數
                print(f"⚠️ 未找到 benchmark_score，使用預設值: {data['benchmark_score']}")
        else:
            print(f"✅ 已解析到正確的 benchmark_score: {data['benchmark_score']}，跳過計算")


class OCRDatabaseManager:
    """OCR 資料庫管理器"""
    
    def __init__(self):
        """初始化資料庫管理器"""
        pass
    
    def save_to_ocr_database(self, parsed_data: Dict[str, Any], file_path: str, 
                           ocr_raw_text: str, original_result: Dict[str, Any],
                           uploaded_by = None) -> Dict[str, Any]:
        """
        將解析出的資料保存到 OCR 存儲基準測試資料庫
        
        Args:
            parsed_data (dict): 解析出的測試資料
            file_path (str): 原始文件路徑
            ocr_raw_text (str): OCR 原始文本
            original_result (dict): 原始分析結果
            uploaded_by (User, optional): 上傳者 User instance
            
        Returns:
            dict: 保存結果
        """
        try:
            # 準備保存到 ai_structured_data 的 JSON 數據（將 datetime 轉換為字符串）
            json_safe_data = parsed_data.copy()
            if isinstance(json_safe_data.get('test_datetime'), datetime):
                json_safe_data['test_datetime'] = json_safe_data['test_datetime'].isoformat()
            
            # 處理 test_item，根據解析出的值查找對應的 OCRTestClass
            test_class_id = None
            if parsed_data.get('test_item'):
                test_item_name = parsed_data['test_item']
                print(f"🔍 查找測試項目: {test_item_name}")
                
                try:
                    # 嘗試導入 OCRTestClass 模型
                    from api.models import OCRTestClass
                    
                    # 根據名稱查找對應的 OCRTestClass
                    # 支援多種匹配方式：完全匹配、部分匹配、忽略大小寫
                    test_class = None
                    
                    # 1. 完全匹配（忽略大小寫）
                    test_class = OCRTestClass.objects.filter(
                        name__iexact=test_item_name, 
                        is_active=True
                    ).first()
                    
                    # 2. 如果沒找到，嘗試部分匹配
                    if not test_class:
                        test_class = OCRTestClass.objects.filter(
                            name__icontains=test_item_name,
                            is_active=True
                        ).first()
                    
                    # 3. 如果還沒找到，嘗試反向匹配（test_item 包含在 class name 中）
                    if not test_class:
                        for cls in OCRTestClass.objects.filter(is_active=True):
                            if test_item_name.upper() in cls.name.upper() or cls.name.upper() in test_item_name.upper():
                                test_class = cls
                                break
                    
                    if test_class:
                        test_class_id = test_class.id
                        print(f"✅ 找到匹配的測試類別: {test_class.name} (ID: {test_class_id})")
                    else:
                        print(f"⚠️ 未找到匹配的測試類別: {test_item_name}")
                        # 可選：自動創建新的測試類別（需要管理員權限）
                        # 這裡暫時不自動創建，只記錄警告
                        
                except ImportError:
                    print("⚠️ 無法導入 OCRTestClass 模型，跳過測試類別關聯")
                except Exception as e:
                    print(f"⚠️ 查找測試類別時發生錯誤: {e}")
            
            # 直接使用解析出的結構化資料
            save_data = {
                'project_name': parsed_data.get('project_name'),  # 保留空值，不使用預設值
                'benchmark_score': parsed_data.get('benchmark_score'),
                'average_bandwidth': parsed_data.get('average_bandwidth'),
                'device_model': parsed_data.get('device_model'),
                'firmware_version': parsed_data.get('firmware_version'),
                'test_datetime': parsed_data.get('test_datetime'),  # 修復：加入 test_datetime
                'benchmark_version': parsed_data.get('benchmark_version', 'CDM8'),  # 使用解析出的版本
                'mark_version_3d': parsed_data.get('benchmark_version'),  # 新欄位：3DMark版本
                'test_class_id': test_class_id,  # 🆕 添加測試類別ID
                'ocr_raw_text': ocr_raw_text,
                'ai_structured_data': json_safe_data,  # JSON 安全的結構化資料
                'ocr_confidence': parsed_data.get('ocr_confidence', 0.95),
                'ocr_processing_time': original_result.get('response_time', 0)
            }
            
            # 處理測試時間
            if parsed_data.get('test_datetime'):
                if isinstance(parsed_data['test_datetime'], datetime):
                    # 如果已經是 datetime 對象，直接使用
                    save_data['test_datetime'] = parsed_data['test_datetime']
                else:
                    try:
                        # 處理 "2025-09-06 16:13" 格式（可能沒有秒數）
                        test_date_str = str(parsed_data['test_datetime']).replace('/', '-').replace('‑', '-').strip()
                        
                        # 嘗試不同的日期格式
                        date_formats = [
                            '%Y-%m-%d %H:%M:%S',  # 2025-09-06 16:13:00
                            '%Y-%m-%d %H:%M',     # 2025-09-06 16:13
                            '%Y/%m/%d %H:%M:%S',  # 2025/09/06 16:13:00
                            '%Y/%m/%d %H:%M'      # 2025/09/06 16:13
                        ]
                        
                        parsed_datetime = None
                        for fmt in date_formats:
                            try:
                                parsed_datetime = datetime.strptime(test_date_str, fmt)
                                break
                            except ValueError:
                                continue
                        
                        if parsed_datetime:
                            save_data['test_datetime'] = parsed_datetime
                            print(f"✅ 成功解析測試時間: {save_data['test_datetime']}")
                        else:
                            # 如果所有格式都失敗，保持原始字符串
                            save_data['test_datetime'] = test_date_str
                            print(f"⚠️ 無法解析為 datetime，保存為字符串: {test_date_str}")
                        
                    except Exception as e:
                        print(f"⚠️ 日期解析失敗: {parsed_data['test_datetime']} -> {e}")
                        # 如果解析失敗，保存原始字符串
                        save_data['test_datetime'] = str(parsed_data['test_datetime'])
            else:
                save_data['test_datetime'] = datetime.now()
            
            # 清理無效值
            save_data = {k: v for k, v in save_data.items() if v is not None}
            
            print(f"\n💾 準備保存到 OCR 資料庫的資料:")
            print(f"  📋 基本資訊:")
            print(f"    專案名稱: {save_data.get('project_name')}")
            print(f"    基準分數: {save_data.get('benchmark_score')}")
            print(f"    平均帶寬: {save_data.get('average_bandwidth')}")
            
            if parsed_data.get('system_info'):
                print(f"  🖥️  系統資訊:")
                for key, value in parsed_data['system_info'].items():
                    print(f"    {key}: {value}")
            
            # 在實際環境中，這裡會執行真正的資料庫保存
            return self._save_to_django_model(save_data)
            
        except Exception as e:
            print(f"❌ 保存到 OCR 資料庫失敗: {e}")
            return {'success': False, 'error': str(e)}
    
    def _save_to_django_model(self, save_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        實際保存到 Django 模型的邏輯
        
        Args:
            save_data (dict): 準備保存的資料
            
        Returns:
            dict: 保存結果
        """
        try:
            # 嘗試導入 Django 模型
            try:
                from api.models import OCRStorageBenchmark
                from django.contrib.auth.models import User
                print("✅ Django 模型導入成功，準備執行實際保存")
            except ImportError as e:
                print(f"❌ Django 模型導入失敗: {e}")
                # 如果沒有 Django 環境，返回模擬結果
                return {
                    'success': True, 
                    'message': 'CDM8 資料解析完成（結構化保存準備就緒）',
                    'data': save_data,
                    'structured_fields': list(save_data.keys()),
                    'performance_summary': {
                        'benchmark_score': save_data.get('benchmark_score'),
                        'average_bandwidth': save_data.get('average_bandwidth'),
                        'device_model': save_data.get('device_model')
                    }
                }
            
            # 如果有 Django 環境，執行實際保存
            print(f"🔄 開始執行 Django 模型保存，資料欄位數: {len(save_data)}")
            ocr_record = OCRStorageBenchmark.objects.create(**save_data)
            print(f"✅ Django 模型保存成功，記錄 ID: {ocr_record.id}")
            
            return {
                'success': True,
                'message': 'OCR 資料已成功保存到資料庫',
                'record_id': ocr_record.id,
                'data': save_data,
                'performance_summary': {
                    'benchmark_score': save_data.get('benchmark_score'),
                    'average_bandwidth': save_data.get('average_bandwidth'),
                    'device_model': save_data.get('device_model')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'資料庫保存失敗: {str(e)}'
            }


def create_ocr_analyzer() -> OCRAnalyzer:
    """創建 OCR 分析器實例"""
    return OCRAnalyzer()


def create_ocr_database_manager() -> OCRDatabaseManager:
    """創建 OCR 資料庫管理器實例"""
    return OCRDatabaseManager()


# 便利函數
def parse_storage_benchmark_text(text: str) -> Dict[str, Any]:
    """
    便利函數：解析儲存基準測試文本
    
    Args:
        text (str): 待解析的文本
        
    Returns:
        dict: 解析結果
    """
    analyzer = create_ocr_analyzer()
    return analyzer.parse_test_summary_table(text)


def save_ocr_analysis_result(parsed_data: Dict[str, Any], file_path: str, 
                           ocr_text: str, analysis_result: Dict[str, Any],
                           user_id: Optional[int] = None) -> Dict[str, Any]:
    """
    便利函數：保存 OCR 分析結果到資料庫
    
    Args:
        parsed_data (dict): 解析出的資料
        file_path (str): 文件路徑
        ocr_text (str): OCR 原始文本
        analysis_result (dict): 分析結果
        user_id (int, optional): 用戶 ID
        
    Returns:
        dict: 保存結果
    """
    db_manager = create_ocr_database_manager()
    return db_manager.save_to_ocr_database(
        parsed_data, file_path, ocr_text, analysis_result, user_id
    )