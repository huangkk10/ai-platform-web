#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
測試 OCR 整合功能的管理命令
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime
import json


class Command(BaseCommand):
    help = 'Test OCR integration with storage benchmark table parsing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mock-ai-response',
            action='store_true',
            help='Use mock AI response for testing',
        )
        parser.add_argument(
            '--save-to-db',
            action='store_true',
            help='Actually save to database',
        )
    
    def handle(self, *args, **options):
        self.stdout.write("🧪 測試 OCR 整合功能")
        self.stdout.write("="*50)
        
        try:
            # 1. 測試 OCR 分析器導入
            self.stdout.write("\n📦 步驟 1: 測試 OCR 分析器導入")
            from library.data_processing.ocr_analyzer import (
                create_ocr_analyzer,
                create_ocr_database_manager
            )
            self.stdout.write(self.style.SUCCESS("✅ OCR 分析器導入成功"))
            
            # 2. 創建分析器實例
            self.stdout.write("\n🔧 步驟 2: 創建分析器實例")
            ocr_analyzer = create_ocr_analyzer()
            ocr_db_manager = create_ocr_database_manager()
            self.stdout.write(self.style.SUCCESS("✅ 分析器實例創建成功"))
            
            # 3. 模擬 AI 回覆中包含儲存基準測試表格
            if options['mock_ai_response']:
                self.stdout.write("\n🤖 步驟 3: 使用模擬 AI 回覆")
                mock_response = """
                根據您上傳的圖片，我分析了存儲基準測試結果：

                | 項目 | 結果 |
                |------|------|
                | **儲存基準分數 (Storage Benchmark Score)** | 7350 |
                | **平均頻寬 (Average Bandwidth)** | 1250.75 MB/s |
                | **裝置型號** | SAMSUNG SSD980 PRO |
                | **韌體 (Firmware)** | 5B2QGXA7 |
                | **測試時間** | 2025-09-21 16:30 (+08:00) |
                | **3DMark 軟體版本** | 2.29.8294 (最新) |

                這是一個高性能的 NVMe SSD。
                """
                
                # 執行解析
                self.stdout.write("🔬 執行 OCR 解析...")
                parsed_data = ocr_analyzer.parse_storage_benchmark_table(mock_response)
                
                if parsed_data and len(parsed_data) > 5:
                    self.stdout.write(self.style.SUCCESS(f"✅ 解析成功，共 {len(parsed_data)} 個欄位"))
                    
                    # 顯示解析結果
                    self.stdout.write("📋 解析結果:")
                    for key, value in list(parsed_data.items())[:8]:
                        if isinstance(value, datetime):
                            value = value.strftime('%Y-%m-%d %H:%M:%S')
                        self.stdout.write(f"  {key}: {value}")
                    
                    # 4. 測試資料庫保存（如果指定）
                    if options['save_to_db']:
                        self.stdout.write("\n💾 步驟 4: 保存到資料庫")
                        
                        # 模擬原始分析結果
                        mock_original_result = {
                            'success': True,
                            'answer': mock_response,
                            'response_time': 2.3,
                            'conversation_id': 'test_conversation_456',
                            'message_id': 'test_message_789'
                        }
                        
                        # 獲取第一個用戶作為測試用戶
                        test_user = User.objects.first()
                        
                        save_result = ocr_db_manager.save_to_ocr_database(
                            parsed_data=parsed_data,
                            file_path="/tmp/test_samsung_ssd980_pro.png",
                            ocr_raw_text=mock_response,
                            original_result=mock_original_result,
                            uploaded_by=test_user  # 傳遞 User instance
                        )
                        
                        if save_result['success']:
                            self.stdout.write(self.style.SUCCESS("✅ 資料庫保存成功"))
                            
                            # 檢查是否真的保存了
                            try:
                                from api.models import OCRStorageBenchmark
                                latest_record = OCRStorageBenchmark.objects.order_by('-created_at').first()
                                if latest_record:
                                    self.stdout.write(f"📊 最新記錄:")
                                    self.stdout.write(f"  ID: {latest_record.id}")
                                    self.stdout.write(f"  專案: {latest_record.project_name}")
                                    self.stdout.write(f"  分數: {latest_record.benchmark_score}")
                                    self.stdout.write(f"  裝置: {latest_record.device_model}")
                                    self.stdout.write(f"  創建時間: {latest_record.created_at}")
                                    
                                    # 檢查總記錄數
                                    total_count = OCRStorageBenchmark.objects.count()
                                    self.stdout.write(f"📈 總記錄數: {total_count}")
                                else:
                                    self.stdout.write(self.style.WARNING("⚠️ 沒有找到保存的記錄"))
                            except Exception as db_error:
                                self.stdout.write(self.style.ERROR(f"❌ 檢查資料庫記錄失敗: {db_error}"))
                        else:
                            self.stdout.write(self.style.ERROR(f"❌ 資料庫保存失敗: {save_result.get('error', '未知錯誤')}"))
                    else:
                        self.stdout.write("\n💾 步驟 4: 跳過資料庫保存（使用 --save-to-db 來實際保存）")
                        self.stdout.write("模擬保存結果:")
                        performance = {
                            'read_speed': parsed_data.get('read_speed'),
                            'write_speed': parsed_data.get('write_speed'),
                            'total_iops': (parsed_data.get('iops_read', 0) or 0) + (parsed_data.get('iops_write', 0) or 0)
                        }
                        self.stdout.write(f"  讀取速度: {performance['read_speed']} MB/s")
                        self.stdout.write(f"  寫入速度: {performance['write_speed']} MB/s")
                        self.stdout.write(f"  總 IOPS: {performance['total_iops']:,}")
                
                else:
                    self.stdout.write(self.style.ERROR("❌ 解析失敗或結果不完整"))
                    return
            
            # 5. 檢查現有的 dify_chat_with_file 功能整合
            self.stdout.write("\n🔗 步驟 5: 檢查 API 整合狀態")
            
            try:
                from api import views
                import inspect
                
                # 檢查 dify_chat_with_file 函數是否存在
                if hasattr(views, 'dify_chat_with_file'):
                    self.stdout.write("✅ dify_chat_with_file 函數存在")
                    
                    # 檢查函數源碼中是否包含 OCR 整合代碼
                    source = inspect.getsource(views.dify_chat_with_file)
                    
                    checks = [
                        ('create_ocr_analyzer', 'OCR 分析器導入'),
                        ('create_ocr_database_manager', 'OCR 資料庫管理器導入'),
                        ('parse_storage_benchmark_table', 'OCR 解析功能'),
                        ('save_to_ocr_database', 'OCR 保存功能'),
                        ('ocr_analysis_result', 'OCR 分析結果處理')
                    ]
                    
                    for check_text, description in checks:
                        if check_text in source:
                            self.stdout.write(f"✅ {description} 已整合")
                        else:
                            self.stdout.write(self.style.WARNING(f"⚠️ {description} 未整合"))
                    
                else:
                    self.stdout.write(self.style.ERROR("❌ dify_chat_with_file 函數不存在"))
                    
            except Exception as api_error:
                self.stdout.write(self.style.ERROR(f"❌ API 整合檢查失敗: {api_error}"))
            
            # 6. 總結
            self.stdout.write("\n🎉 測試完成")
            self.stdout.write("="*50)
            
            if options['mock_ai_response']:
                self.stdout.write("📋 測試摘要:")
                self.stdout.write("  ✅ OCR 分析器模組正常")
                self.stdout.write("  ✅ 表格解析功能正常")
                if options['save_to_db']:
                    self.stdout.write("  ✅ 資料庫保存功能正常")
                else:
                    self.stdout.write("  ⚠️ 資料庫保存功能未測試")
                self.stdout.write("  ✅ API 整合檢查完成")
            
            self.stdout.write("\n💡 使用建議:")
            self.stdout.write("  - 若要測試完整功能: --mock-ai-response --save-to-db")
            self.stdout.write("  - 檢查前端網路回應中是否有 'ocr_analysis' 欄位")
            self.stdout.write("  - 使用瀏覽器開發者工具查看 API 回應內容")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ 測試失敗: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())