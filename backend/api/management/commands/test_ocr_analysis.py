#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django 管理命令：測試 OCR 分析並保存到資料庫
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime
import os
import sys
import json

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

from api.models import OCRStorageBenchmark


class Command(BaseCommand):
    help = '測試 OCR 分析功能並保存結果到資料庫'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--test-file',
            type=str,
            help='要分析的測試文件路徑',
            default=None
        )
        parser.add_argument(
            '--mock-data',
            action='store_true',
            help='使用模擬資料進行測試',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='指定上傳者用戶名',
            default='admin'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🧪 開始 OCR 分析測試')
        self.stdout.write('=' * 50)
        
        # 獲取或創建用戶
        username = options.get('user', 'admin')
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f'{username}@example.com',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            user.set_password('admin123')
            user.save()
            self.stdout.write(f'✅ 創建用戶: {username}')
        else:
            self.stdout.write(f'📋 使用現有用戶: {username}')
        
        if options.get('mock_data'):
            self.create_mock_ocr_records(user)
        elif options.get('test_file'):
            self.analyze_file_and_save(options['test_file'], user)
        else:
            self.show_usage_examples()
    
    def create_mock_ocr_records(self, user):
        """創建模擬的 OCR 分析記錄"""
        self.stdout.write('\n🎭 創建模擬 OCR 分析記錄')
        
        mock_records = [
            {
                'project_name': 'SSD Performance Analysis',
                'benchmark_score': 6883,
                'average_bandwidth': '1174.89 MB/s',
                'device_model': 'KINGSTON SFYR2S1TO',
                'firmware_version': 'SGW0904A',
                'test_datetime': datetime(2025, 9, 6, 16, 13),
                'benchmark_version': '2.28.8228 (測試專用版)',
                'test_environment': 'benchmark',
                'test_type': 'comprehensive',
                'ocr_raw_text': '''
                測試得分: 6883
                平均帶寬: 1174.89 MB/s
                裝置型號: KINGSTON SFYR2S1TO
                韌體版本: SGW0904A
                測試時間: 2025-09-06 16:13 +08:00
                3DMark 版本: 2.28.8228 (測試專用版)
                ''',
                'ai_structured_data': {
                    'benchmark_score': 6883,
                    'average_bandwidth': '1174.89 MB/s',
                    'device_model': 'KINGSTON SFYR2S1TO',
                    'firmware_version': 'SGW0904A',
                    'test_datetime': '2025-09-06 16:13 +08:00',
                    'benchmark_version': '2.28.8228 (測試專用版)',
                    'extracted_fields': ['benchmark_score', 'average_bandwidth', 'device_model'],
                    'confidence': 0.95
                },
                'processing_status': 'completed',
                'ocr_confidence': 0.95,
                'ocr_processing_time': 2.5,
                'uploaded_by': user
            },
            {
                'project_name': 'NVMe Speed Test',
                'benchmark_score': 8950,
                'average_bandwidth': '1456.78 MB/s',
                'device_model': 'Samsung 980 PRO 2TB',
                'firmware_version': '5B2QGXA7',
                'test_datetime': datetime(2025, 9, 5, 14, 30),
                'benchmark_version': '2.28.8230',
                'read_speed': 7100.0,
                'write_speed': 6500.0,
                'iops_read': 950000,
                'iops_write': 850000,
                'test_environment': 'production',
                'test_type': 'sequential_read',
                'ocr_raw_text': '''
                測試得分: 8950
                平均帶寬: 1456.78 MB/s
                裝置型號: Samsung 980 PRO 2TB
                韌體版本: 5B2QGXA7
                讀取速度: 7100 MB/s
                寫入速度: 6500 MB/s
                讀取IOPS: 950,000
                寫入IOPS: 850,000
                ''',
                'ai_structured_data': {
                    'benchmark_score': 8950,
                    'average_bandwidth': '1456.78 MB/s',
                    'device_model': 'Samsung 980 PRO 2TB',
                    'firmware_version': '5B2QGXA7',
                    'read_speed': 7100,
                    'write_speed': 6500,
                    'confidence': 0.98
                },
                'processing_status': 'completed',
                'ocr_confidence': 0.98,
                'ocr_processing_time': 1.8,
                'uploaded_by': user
            }
        ]
        
        created_count = 0
        for record_data in mock_records:
            # 檢查是否已存在
            existing = OCRStorageBenchmark.objects.filter(
                device_model=record_data['device_model'],
                benchmark_score=record_data['benchmark_score']
            ).first()
            
            if not existing:
                record = OCRStorageBenchmark.objects.create(**record_data)
                created_count += 1
                self.stdout.write(f'✅ 創建記錄: {record}')
                self.stdout.write(f'   效能評級: {record.get_performance_grade()}')
                self.stdout.write(f'   AI 資料摘要: {record.get_ai_data_summary()}')
            else:
                self.stdout.write(f'⚠️ 記錄已存在: {existing}')
        
        self.stdout.write(f'\n🎉 完成！共創建 {created_count} 筆模擬 OCR 記錄')
        
        # 顯示統計
        total_records = OCRStorageBenchmark.objects.count()
        verified_records = OCRStorageBenchmark.objects.filter(is_verified=True).count()
        
        self.stdout.write(f'\n📊 資料庫統計:')
        self.stdout.write(f'   總記錄數: {total_records}')
        self.stdout.write(f'   已驗證記錄: {verified_records}')
        self.stdout.write(f'   驗證比例: {verified_records/total_records*100:.1f}%' if total_records > 0 else '   驗證比例: 0%')
    
    def analyze_file_and_save(self, file_path, user):
        """分析文件並保存結果"""
        self.stdout.write(f'\n🔍 分析文件: {file_path}')
        
        if not os.path.exists(file_path):
            self.stdout.write(f'❌ 文件不存在: {file_path}')
            return
        
        try:
            # 這裡可以集成實際的 OCR 或 AI 分析服務
            # 目前使用模擬分析結果
            
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            self.stdout.write(f'📄 文件信息:')
            self.stdout.write(f'   名稱: {file_name}')
            self.stdout.write(f'   大小: {file_size/1024:.2f} KB')
            
            # 模擬分析結果
            mock_analysis_result = {
                'project_name': f'OCR Analysis - {file_name}',
                'benchmark_score': 7245,  # 模擬分數
                'average_bandwidth': '1285.32 MB/s',
                'device_model': 'Unknown Device',
                'firmware_version': 'Unknown',
                'test_datetime': datetime.now(),
                'benchmark_version': 'Auto Detected',
                'test_environment': 'testing',
                'test_type': 'mixed_workload',
                'ocr_raw_text': f'Auto generated OCR text for {file_name}',
                'ai_structured_data': {
                    'file_name': file_name,
                    'file_size': file_size,
                    'analysis_timestamp': datetime.now().isoformat(),
                    'confidence': 0.85
                },
                'processing_status': 'completed',
                'ocr_confidence': 0.85,
                'ocr_processing_time': 3.2,
                'uploaded_by': user
            }
            
            # 如果是圖片文件，嘗試讀取並存儲
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                try:
                    with open(file_path, 'rb') as f:
                        mock_analysis_result['original_image_data'] = f.read()
                        mock_analysis_result['original_image_filename'] = file_name
                        mock_analysis_result['original_image_content_type'] = f'image/{file_path.split(".")[-1].lower()}'
                    self.stdout.write(f'📷 已讀取圖片數據: {len(mock_analysis_result["original_image_data"])} bytes')
                except Exception as e:
                    self.stdout.write(f'⚠️ 讀取圖片失敗: {e}')
            
            # 保存到資料庫
            record = OCRStorageBenchmark.objects.create(**mock_analysis_result)
            
            self.stdout.write(f'✅ 分析完成並保存: {record}')
            self.stdout.write(f'   記錄 ID: {record.id}')
            self.stdout.write(f'   效能評級: {record.get_performance_grade()}')
            self.stdout.write(f'   摘要: {record.get_summary()}')
            
        except Exception as e:
            self.stdout.write(f'❌ 分析文件失敗: {e}')
    
    def show_usage_examples(self):
        """顯示使用範例"""
        self.stdout.write('\n📚 使用範例:')
        self.stdout.write('=' * 30)
        
        self.stdout.write('\n1. 創建模擬資料:')
        self.stdout.write('   python manage.py test_ocr_analysis --mock-data')
        
        self.stdout.write('\n2. 分析特定文件:')
        self.stdout.write('   python manage.py test_ocr_analysis --test-file /path/to/image.png')
        
        self.stdout.write('\n3. 指定用戶:')
        self.stdout.write('   python manage.py test_ocr_analysis --mock-data --user testuser')
        
        self.stdout.write('\n🚀 API 測試指令:')
        self.stdout.write('   # 列出所有 OCR 記錄')
        self.stdout.write('   curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/ocr-storage-benchmarks/')
        
        self.stdout.write('\n   # 獲取統計資料')
        self.stdout.write('   curl -H "Authorization: Token YOUR_TOKEN" http://localhost/api/ocr-storage-benchmarks/statistics/')
        
        self.stdout.write('\n   # 搜尋特定裝置')
        self.stdout.write('   curl -H "Authorization: Token YOUR_TOKEN" "http://localhost/api/ocr-storage-benchmarks/?device_model=KINGSTON"')