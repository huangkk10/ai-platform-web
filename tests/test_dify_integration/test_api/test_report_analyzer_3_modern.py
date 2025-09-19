#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用新 Library 模組的示例
展示如何重構原來的測試代碼
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

# 使用新的 library 模組
from library.config.dify_app_configs import get_report_analyzer_3_config
from library.dify_integration import (
    create_report_analyzer_client,
    quick_file_analysis,
    analyze_files_batch
)
from library.data_processing.file_utils import (
    get_file_info,
    validate_file_for_upload,
    get_default_analysis_query,
    format_file_size
)


class ModernReportAnalyzer3Test:
    """使用新 Library 模組的現代化測試器"""
    
    def __init__(self):
        """初始化"""
        self.config = get_report_analyzer_3_config()
        self.client = create_report_analyzer_client(
            self.config['api_url'],
            self.config['api_key'],
            self.config['base_url']
        )
        
        print(f"🔧 初始化現代化 Report Analyzer 3 測試器")
        print(f"工作室: {self.config['workspace']}")
        print(f"API URL: {self.config['api_url']}")
        print(f"Base URL: {self.config['base_url']}")
        print(f"API Key: {self.config['api_key'][:12]}...")
    
    def test_single_file_analysis(self, file_path: str, custom_query: str = None):
        """測試單個文件分析"""
        print(f"\n🧪 測試單個文件分析")
        print(f"文件路徑: {file_path}")
        
        # 1. 驗證文件
        is_valid, error_msg = validate_file_for_upload(file_path)
        if not is_valid:
            print(f"❌ 文件驗證失敗: {error_msg}")
            return None
        
        # 2. 獲取文件信息
        file_info = get_file_info(file_path)
        print(f"📄 文件信息:")
        print(f"  名稱: {file_info['file_name']}")
        print(f"  大小: {format_file_size(file_info['file_size'])}")
        print(f"  類型: {'圖片' if file_info['is_image'] else '文檔'}")
        print(f"  MIME: {file_info['mime_type']}")
        
        # 3. 生成查詢
        query = custom_query or get_default_analysis_query(file_path)
        print(f"📝 使用查詢: {query}")
        
        # 4. 執行分析
        result = self.client.upload_and_analyze(file_path, query, verbose=True)
        
        if result['success']:
            print(f"\n🎉 分析成功！")
            print(f"answer: {result.get('answer', 'N/A')}")
            print(f"📊 結果摘要:")
            print(f"  響應時間: {result.get('response_time', 0):.2f}秒")
            print(f"  使用格式: {result.get('format_used', 'Unknown')}")
            print(f"  會話 ID: {result.get('conversation_id', 'N/A')}")
            
            return result
        else:
            print(f"❌ 分析失敗: {result.get('error', 'Unknown error')}")
            return None
    
    def test_batch_file_analysis(self, file_paths: list, custom_queries: list = None):
        """測試批量文件分析"""
        print(f"\n🧪 測試批量文件分析")
        print(f"文件數量: {len(file_paths)}")
        
        # 使用 library 的批量分析功能
        results = self.client.batch_file_analysis(
            file_paths, 
            custom_queries, 
            verbose=True
        )
        
        # 生成報告
        summary_report = self.client.get_analysis_report(results, "summary")
        print(f"\n📋 批量分析摘要:")
        print(summary_report)
        
        return results
    
    def test_basic_chat_formats(self, query: str = "你好，請介紹一下你的功能"):
        """測試基本聊天的多種格式"""
        print(f"\n🧪 測試基本聊天的多種格式")
        
        result = self.client.test_basic_chat_with_formats(query, verbose=True)
        
        if result['success']:
            print(f"\n🎉 基本聊天測試成功！")
            print(f"使用格式: {result.get('format_used', 'Unknown')}")
            return result
        else:
            print(f"❌ 基本聊天測試失敗: {result.get('error', 'Unknown error')}")
            return None
    
    def test_cdm8_file_analysis(self, file_path: str):
        """專門測試 CDM8 檔案分析"""
        print(f"\n🔬 專門測試 CDM8 檔案分析")
        print(f"檔案: {os.path.basename(file_path)}")
        
        # CDM8 檔案的專門查詢
        cdm8_queries = [
            "請分析這個 CDM8 測試結果檔案，提供關鍵資訊摘要",
            "這個檔案中有哪些重要的測試參數和結果？",
            "請解讀檔案中的測試數據，有什麼需要注意的地方嗎？"
        ]
        
        results = []
        for i, query in enumerate(cdm8_queries, 1):
            print(f"\n📝 查詢 {i}: {query}")
            result = self.test_single_file_analysis(file_path, query)
            if result:
                results.append({
                    'query': query,
                    'result': result,
                    'success': True
                })
                print(f"✅ 查詢 {i} 成功")
            else:
                results.append({
                    'query': query,
                    'result': None,
                    'success': False
                })
                print(f"❌ 查詢 {i} 失敗")
        
        # 總結 CDM8 測試結果
        successful_queries = sum(1 for r in results if r['success'])
        print(f"\n📊 CDM8 檔案測試總結: {successful_queries}/{len(cdm8_queries)} 成功")
        
        return results
    
    def run_comprehensive_test(self, test_files: list = None, cdm8_file: str = None):
        """運行綜合測試"""
        print(f"\n{'='*60}")
        print(f"🧪 開始綜合測試")
        print(f"{'='*60}")
        print(f"時間: {datetime.now()}")
        
        test_results = {
            'basic_chat': None,
            'single_file': None,
            'batch_files': None,
            'cdm8_analysis': None
        }
        
        # 測試 1: 基本聊天
        # print(f"\n📌 測試 1: 基本聊天功能")
        # test_results['basic_chat'] = self.test_basic_chat_formats()
        
        # 測試 2: CDM8 檔案專門分析
        if cdm8_file and os.path.exists(cdm8_file):
            print(f"\n📌 測試 2: CDM8 檔案專門分析")
            test_results['cdm8_analysis'] = self.test_cdm8_file_analysis(cdm8_file)
        
        # 測試 3: 單個文件分析
        if test_files and len(test_files) > 0:
            print(f"\n📌 測試 3: 單個文件分析")
            test_results['single_file'] = self.test_single_file_analysis(test_files[0])
            
            # 測試 4: 批量文件分析（如果有多個文件）
            # if len(test_files) > 1:
            #     print(f"\n📌 測試 4: 批量文件分析")
            #     test_results['batch_files'] = self.test_batch_file_analysis(test_files[:3])  # 最多測試3個文件
        else:
            print(f"\n⚠️ 跳過文件相關測試（未提供測試文件）")
        
        # 生成測試總結
        self._print_test_summary(test_results)
        
        return test_results
    
    def _print_test_summary(self, test_results: dict):
        """打印測試總結"""
        print(f"\n{'='*60}")
        print(f"🎯 測試總結")
        print(f"{'='*60}")
        
        # 基本聊天結果
        if test_results['basic_chat']:
            print(f"✅ 基本聊天功能：正常")
        else:
            print(f"❌ 基本聊天功能：失敗")
        
        # CDM8 檔案分析結果
        if test_results['cdm8_analysis']:
            successful_count = sum(1 for result in test_results['cdm8_analysis'] 
                                 if result.get('success', False))
            total_count = len(test_results['cdm8_analysis'])
            print(f"🔬 CDM8 檔案分析：{successful_count}/{total_count} 成功")
        elif test_results['cdm8_analysis'] is None:
            print(f"⚠️ CDM8 檔案分析：未測試")
        else:
            print(f"❌ CDM8 檔案分析：失敗")
        
        # 單個文件分析結果
        if test_results['single_file']:
            print(f"✅ 單個文件分析：正常")
        elif test_results['single_file'] is None:
            print(f"⚠️ 單個文件分析：未測試")
        else:
            print(f"❌ 單個文件分析：失敗")
        
        # 批量文件分析結果
        if test_results['batch_files']:
            successful_count = sum(1 for result in test_results['batch_files'].values() 
                                 if result.get('success', False))
            total_count = len(test_results['batch_files'])
            print(f"📊 批量文件分析：{successful_count}/{total_count} 成功")
        elif test_results['batch_files'] is None:
            print(f"⚠️ 批量文件分析：未測試")
        else:
            print(f"❌ 批量文件分析：失敗")
        
        print(f"\n測試完成！")


def demonstrate_library_usage():
    """演示新 library 的使用方法"""
    print("🎯 新 Library 模組使用示例")
    print("="*50)
    
    # 示例 1: 快速文件分析
    # print("\n📌 示例 1: 快速文件分析")
    # print("```python")
    # print("from library.dify_integration import quick_file_analysis")
    # print("result = quick_file_analysis('path/to/file.txt')")
    # print("if result['success']:")
    # print("    print(result['answer'])")
    # print("```")
    
    # 示例 2: 批量文件分析
    print("\n📌 示例 2: 批量文件分析")
    print("```python")
    print("from library.dify_integration import analyze_files_batch")
    print("files = ['file1.txt', 'file2.png', 'file3.pdf']")
    print("results = analyze_files_batch(files)")
    print("```")
    
    # 示例 3: 完整客戶端使用
    # print("\n📌 示例 3: 完整客戶端使用")
    # print("```python")
    # print("from library.dify_integration import create_report_analyzer_client")
    # print("client = create_report_analyzer_client()")
    # print("result = client.upload_and_analyze('file.txt', '自定義查詢')")
    # print("```")
    
    # 示例 4: 文件工具使用
    # print("\n📌 示例 4: 文件工具使用")
    # print("```python")
    # print("from library.data_processing.file_utils import get_file_info, validate_file_for_upload")
    # print("info = get_file_info('file.txt')")
    # print("is_valid, error = validate_file_for_upload('file.txt', max_size_mb=50)")
    # print("```")
    
    # 示例 5: CDM8 檔案專門測試
    print("\n📌 示例 5: CDM8 檔案專門測試")
    print("```python")
    print("tester = ModernReportAnalyzer3Test()")
    print("cdm8_results = tester.test_cdm8_file_analysis('1_SSD-Y-06421_CDM8(MB)_1.txt')")
    print("for result in cdm8_results:")
    print("    if result['success']:")
    print("        print(f\"查詢: {result['query']}\")")
    print("        print(f\"結果: {result['result']['answer']}\")")
    print("```")


def main():
    """主程式"""
    print("🧪 現代化 Report Analyzer 3 測試")
    print("使用新的 Library 模組")
    print("="*60)
    
    # 演示用法
    demonstrate_library_usage()
    
    # 初始化測試器
    tester = ModernReportAnalyzer3Test()
    
    # 檢查測試文件
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # CDM8 檔案（特別指定）
    cdm8_file = os.path.join(current_dir, "1_SSD-Y-06421_CDM8(MB)_1.txt")
    
    # 其他測試文件
    test_files = [
        os.path.join(current_dir, "3.png"),
        os.path.join(current_dir, "test_report.txt"),
        os.path.join(current_dir, "../test_upload/test_image.png"),
        os.path.join(current_dir, "../test_upload/test_document.txt")
    ]
    
    # 過濾存在的文件
    existing_files = [f for f in test_files if os.path.exists(f)]
    
    # 檢查 CDM8 檔案
    if os.path.exists(cdm8_file):
        cdm8_info = get_file_info(cdm8_file)
        print(f"\n🔬 找到 CDM8 特殊測試檔案:")
        print(f"  - {cdm8_info['file_name']} ({format_file_size(cdm8_info['file_size'])})")
    else:
        print(f"\n⚠️ 未找到 CDM8 測試檔案: {cdm8_file}")
        cdm8_file = None
    
    if existing_files:
        print(f"\n📄 找到 {len(existing_files)} 個其他測試文件:")
        for file_path in existing_files:
            file_info = get_file_info(file_path)
            print(f"  - {file_info['file_name']} ({format_file_size(file_info['file_size'])})")
    else:
        print(f"\n⚠️ 未找到其他測試文件")
        print("可用的測試文件位置：")
        for file_path in test_files:
            print(f"  - {file_path}")
    
    # 運行綜合測試
    tester.run_comprehensive_test(existing_files, cdm8_file)


if __name__ == "__main__":
    main()