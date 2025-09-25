#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 整合功能簡化測試腳本
測試基本的 OCR 解析和保存功能
"""

import sys
import os
from datetime import datetime

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

def test_ocr_basic_functionality():
    """測試 OCR 基本功能"""
    print("🧪 測試 OCR 基本功能")
    print("="*60)
    
    try:
        # 1. 測試 OCR 分析器導入
        print("\n📦 步驟 1: 測試模組導入")
        from library.data_processing.ocr_analyzer import (
            create_ocr_analyzer,
            create_ocr_database_manager
        )
        print("✅ OCR 分析器模組導入成功")
        
        # 2. 創建分析器實例
        print("\n🔧 步驟 2: 創建分析器實例")
        ocr_analyzer = create_ocr_analyzer()
        ocr_db_manager = create_ocr_database_manager()
        print("✅ 分析器實例創建成功")
        
        # 3. 測試解析功能
        print("\n🔬 步驟 3: 測試解析功能")
        
        # 模擬 AI 回覆中包含儲存基準測試表格的內容
        mock_ai_response = """
        根據您上傳的圖片，我分析了存儲基準測試結果，以下是詳細資訊：

        | 項目 | 結果 |
        |------|------|
        | **儲存基準分數 (Storage Benchmark Score)** | 6883 |
        | **平均頻寬 (Average Bandwidth)** | 1174.89 MB/s |
        | **裝置型號** | KINGSTON SFYR2S1TO |
        | **韌體 (Firmware)** | SGWO904A |
        | **測試時間** | 2025-09-21 16:13 (+08:00) |
        | **3DMark 軟體版本** | 2.28.8228 (已安裝) |

        這個 SSD 的性能表現相當不錯，基準分數達到 6883 分。
        """
        
        parsed_data = ocr_analyzer.parse_storage_benchmark_table(mock_ai_response)
        
        if parsed_data and len(parsed_data) > 5:
            print(f"✅ 解析成功，共解析出 {len(parsed_data)} 個欄位")
            print("📋 解析結果預覽:")
            for key, value in list(parsed_data.items())[:8]:
                print(f"  {key}: {value}")
        else:
            print("❌ 解析失敗或結果不完整")
            return False
        
        # 4. 測試資料庫保存功能（不需要真實的 Django 環境）
        print("\n💾 步驟 4: 測試資料庫保存功能")
        
        # 模擬原始分析結果
        mock_original_result = {
            'success': True,
            'answer': mock_ai_response,
            'response_time': 2.5,
            'conversation_id': 'test_conversation_123',
            'message_id': 'test_message_456'
        }
        
        save_result = ocr_db_manager.save_to_ocr_database(
            parsed_data=parsed_data,
            file_path="/tmp/test_storage_benchmark.png",
            ocr_raw_text=mock_ai_response,
            original_result=mock_original_result,
            user_id=1  # 測試用戶 ID
        )
        
        if save_result['success']:
            print("✅ 資料庫保存測試成功（模擬模式）")
            print("📊 保存摘要:")
            summary = save_result.get('performance_summary', {})
            print(f"  讀取速度: {summary.get('read_speed')} MB/s")
            print(f"  寫入速度: {summary.get('write_speed')} MB/s")
            print(f"  總 IOPS: {summary.get('total_iops'):,}")
            
            print("📋 準備保存的欄位:")
            data_fields = save_result.get('structured_fields', [])
            for field in data_fields[:10]:
                print(f"  - {field}")
        else:
            print(f"❌ 資料庫保存測試失敗: {save_result.get('error', '未知錯誤')}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_api_integration():
    """測試 API 整合"""
    print("\n📡 測試 API 整合功能")
    print("-"*30)
    
    try:
        # 檢查 views.py 文件中的整合
        views_file_path = "/home/user/codes/ai-platform-web/backend/api/views.py"
        
        if not os.path.exists(views_file_path):
            print("❌ views.py 文件不存在")
            return False
        
        with open(views_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 檢查是否包含必要的整合代碼
        checks = [
            ('create_ocr_analyzer', 'OCR 分析器導入'),
            ('create_ocr_database_manager', 'OCR 資料庫管理器導入'),
            ('parse_storage_benchmark_table', 'OCR 解析功能'),
            ('save_to_ocr_database', 'OCR 保存功能'),
            ('ocr_analysis_result', 'OCR 分析結果處理')
        ]
        
        for check_text, description in checks:
            if check_text in content:
                print(f"✅ {description} 已整合")
            else:
                print(f"❌ {description} 未整合")
                return False
        
        print("✅ API 整合驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ API 整合測試失敗: {str(e)}")
        return False


def test_workflow_simulation():
    """測試完整工作流程模擬"""
    print("\n🔄 測試完整工作流程模擬")
    print("-"*30)
    
    try:
        from library.data_processing.ocr_analyzer import (
            create_ocr_analyzer,
            create_ocr_database_manager
        )
        
        # 模擬完整的工作流程
        steps = [
            "📤 用戶上傳圖檔",
            "🤖 AI 分析圖檔內容",
            "📝 AI 回覆分析結果",
            "🔬 自動執行 OCR 解析",
            "💾 自動保存到資料庫"
        ]
        
        print("完整工作流程:")
        for i, step in enumerate(steps, 1):
            print(f"  {i}. {step}")
        
        print("\n執行模擬:")
        
        # 步驟 1-3: 用戶上傳圖檔，AI 分析並回覆
        print("📤 模擬: 用戶上傳 storage_benchmark.png")
        print("🤖 模擬: AI 正在分析圖檔...")
        print("📝 模擬: AI 回覆包含基準測試表格")
        
        # 步驟 4: 自動執行 OCR 解析
        print("🔬 執行: OCR 自動解析...")
        ocr_analyzer = create_ocr_analyzer()
        
        mock_response = """| **儲存基準分數** | 7200 |
| **平均頻寬** | 1250.5 MB/s |
| **裝置型號** | SAMSUNG SSD980 |"""
        
        parsed = ocr_analyzer.parse_storage_benchmark_table(mock_response)
        
        if parsed:
            print(f"✅ OCR 解析成功: {len(parsed)} 個欄位")
        else:
            print("❌ OCR 解析失敗")
            return False
        
        # 步驟 5: 自動保存到資料庫
        print("💾 執行: 自動保存到資料庫...")
        ocr_db_manager = create_ocr_database_manager()
        
        save_result = ocr_db_manager.save_to_ocr_database(
            parsed_data=parsed,
            file_path="/tmp/storage_benchmark.png",
            ocr_raw_text=mock_response,
            original_result={'success': True, 'response_time': 1.8}
        )
        
        if save_result['success']:
            print("✅ 資料庫保存成功")
        else:
            print("❌ 資料庫保存失敗")
            return False
        
        print("\n🎉 完整工作流程模擬成功！")
        return True
        
    except Exception as e:
        print(f"❌ 工作流程模擬失敗: {str(e)}")
        return False


def main():
    """主函數"""
    print("🚀 開始 OCR 整合功能完整測試")
    print(f"測試時間: {datetime.now()}")
    print("="*60)
    
    # 執行測試
    test1_passed = test_ocr_basic_functionality()
    test2_passed = test_api_integration()
    test3_passed = test_workflow_simulation()
    
    # 總結
    print("\n" + "="*60)
    print("🏁 測試完成總結")
    print("="*60)
    
    if test1_passed and test2_passed and test3_passed:
        print("🎉 所有測試通過！")
        print("✅ OCR 整合功能已正確部署")
        print("\n🔄 完整工作流程:")
        print("  1. 用戶上傳圖檔到 /api/dify-chat-with-file/")
        print("  2. AI 分析並回覆圖檔內容")
        print("  3. 自動執行 OCR 解析 parse_storage_benchmark_table")
        print("  4. 自動保存結構化數據到資料庫 save_to_ocr_database")
        print("  5. 回傳給用戶（包含解析狀態）")
        
        print("\n📊 API 回應示例:")
        print("  {")
        print("    'success': true,")
        print("    'answer': '[AI 回覆內容]',")
        print("    'ocr_analysis': {")
        print("      'parsed': true,")
        print("      'fields_count': 14,")
        print("      'database_saved': true,")
        print("      'record_info': {")
        print("        'read_speed': 1292.39,")
        print("        'write_speed': 1057.13,")
        print("        'total_iops': 1376000")
        print("      }")
        print("    }")
        print("  }")
        
        print("\n🎯 使用方式:")
        print("  1. 重啟 Django 服務: docker compose restart django")
        print("  2. 前端上傳圖檔到 dify_chat_with_file API")
        print("  3. 系統會自動解析並保存 OCR 數據")
        
    else:
        print("❌ 部分測試失敗")
        if not test1_passed:
            print("  - OCR 基本功能測試失敗")
        if not test2_passed:
            print("  - API 整合測試失敗")
        if not test3_passed:
            print("  - 工作流程模擬失敗")


if __name__ == "__main__":
    main()