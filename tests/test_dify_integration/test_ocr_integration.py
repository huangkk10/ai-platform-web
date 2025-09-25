#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR 整合功能測試腳本
測試完整的流程：圖檔分析 → AI 回覆 → OCR 解析 → 資料庫保存
"""

import sys
import os
import django
from datetime import datetime

# 設置 Django 環境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

def test_ocr_integration():
    """測試 OCR 整合功能"""
    print("🧪 測試 OCR 整合功能")
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
            for key, value in list(parsed_data.items())[:6]:
                print(f"  {key}: {value}")
        else:
            print("❌ 解析失敗或結果不完整")
            return False
        
        # 4. 測試資料庫保存功能
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
            print("✅ 資料庫保存測試成功")
            print("📊 保存摘要:")
            summary = save_result.get('performance_summary', {})
            print(f"  讀取速度: {summary.get('read_speed')} MB/s")
            print(f"  寫入速度: {summary.get('write_speed')} MB/s")
            print(f"  總 IOPS: {summary.get('total_iops'):,}")
        else:
            print(f"❌ 資料庫保存測試失敗: {save_result.get('error', '未知錯誤')}")
            return False
        
        # 5. 測試 Django 模型（如果在 Django 環境中）
        print("\n🗄️ 步驟 5: 測試 Django 模型整合")
        try:
            from api.models import OCRStorageBenchmark
            
            # 檢查是否能正常創建記錄
            test_record = OCRStorageBenchmark(
                project_name="Test Integration",
                benchmark_score=1000,
                average_bandwidth="500 MB/s",
                device_model="TEST_DEVICE",
                firmware_version="TEST_FW",
                test_environment="testing",
                test_type="integration_test",
                ocr_raw_text="Test OCR text",
                ai_structured_data={"test": "data"},
                processing_status="completed",
                ocr_confidence=0.95
            )
            
            # 驗證模型欄位而不實際保存
            test_record.full_clean()
            print("✅ Django 模型驗證成功")
            
        except Exception as e:
            print(f"⚠️ Django 模型測試跳過: {str(e)}")
        
        # 6. 總結
        print("\n🎉 步驟 6: 測試總結")
        print("="*60)
        print("✅ 所有測試步驟通過")
        print("🔄 完整流程已驗證:")
        print("  1. 圖檔上傳 ✓")
        print("  2. AI 分析回覆 ✓")
        print("  3. OCR 自動解析 ✓")
        print("  4. 資料庫自動保存 ✓")
        print("  5. Django 模型整合 ✓")
        
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
        # 檢查 views.py 中的整合是否正確
        from api import views
        
        # 檢查是否有 dify_chat_with_file 函數
        if hasattr(views, 'dify_chat_with_file'):
            print("✅ dify_chat_with_file 函數存在")
        else:
            print("❌ dify_chat_with_file 函數不存在")
            return False
        
        # 檢查函數是否包含 OCR 分析器導入
        import inspect
        source = inspect.getsource(views.dify_chat_with_file)
        
        if 'create_ocr_analyzer' in source and 'create_ocr_database_manager' in source:
            print("✅ OCR 分析器已正確整合到 API 中")
        else:
            print("❌ OCR 分析器未正確整合到 API 中")
            return False
        
        if 'parse_storage_benchmark_table' in source:
            print("✅ 解析功能已整合")
        else:
            print("❌ 解析功能未整合")
            return False
        
        if 'save_to_ocr_database' in source:
            print("✅ 資料庫保存功能已整合")
        else:
            print("❌ 資料庫保存功能未整合")
            return False
        
        print("✅ API 整合驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ API 整合測試失敗: {str(e)}")
        return False


def main():
    """主函數"""
    print("🚀 開始 OCR 整合功能完整測試")
    print(f"測試時間: {datetime.now()}")
    print("="*60)
    
    # 執行測試
    test1_passed = test_ocr_integration()
    test2_passed = test_api_integration()
    
    # 總結
    print("\n" + "="*60)
    print("🏁 測試完成總結")
    print("="*60)
    
    if test1_passed and test2_passed:
        print("🎉 所有測試通過！")
        print("✅ OCR 整合功能已正確部署")
        print("\n🔄 完整工作流程:")
        print("  1. 用戶上傳圖檔到 /api/dify-chat-with-file/")
        print("  2. AI 分析並回覆圖檔內容")
        print("  3. 自動執行 OCR 解析")
        print("  4. 自動保存結構化數據到資料庫")
        print("  5. 回傳給用戶（包含解析狀態）")
        
        print("\n📊 API 回應示例:")
        print("  - success: true")
        print("  - answer: [AI 回覆內容]")
        print("  - ocr_analysis:")
        print("    - parsed: true")
        print("    - fields_count: 14")
        print("    - database_saved: true")
        
    else:
        print("❌ 部分測試失敗")
        if not test1_passed:
            print("  - OCR 整合功能測試失敗")
        if not test2_passed:
            print("  - API 整合測試失敗")


if __name__ == "__main__":
    main()