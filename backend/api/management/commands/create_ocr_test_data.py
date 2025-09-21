from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import OCRStorageBenchmark
from datetime import datetime
from django.utils import timezone
import json


class Command(BaseCommand):
    help = 'Create test OCR storage benchmark data for AI OCR system demonstration'
    
    def handle(self, *args, **options):
        # 獲取或創建管理員用戶
        admin_user = User.objects.filter(is_superuser=True).first()
        if not admin_user:
            admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(f"✅ 創建管理員用戶: {admin_user.username}")
        
        # 基於附件的測試資料
        test_records = [
            {
                'project_name': 'Storage Benchmark Score',
                'benchmark_score': 6883,
                'average_bandwidth': '1174.89 MB/s',
                'device_model': 'KINGSTON SFYR2S1TO',
                'firmware_version': 'SGW0904A',
                'test_datetime': timezone.make_aware(datetime(2025, 9, 6, 16, 13)),
                'benchmark_version': '2.28.8228 (測試專用版)',
                'test_environment': 'benchmark',
                'test_type': 'comprehensive',
                'processing_status': 'completed',
                'is_verified': True,
                'verified_by': admin_user,
                'verification_notes': '根據附件圖片創建的測試資料',
                'ocr_confidence': 0.95,
                'ocr_processing_time': 2.3,
                'ocr_raw_text': """專案名稱: Storage Benchmark Score
測試得分: 6883
平均帶寬: 1174.89 MB/s
裝置型號: KINGSTON SFYR2S1TO
韌體版本: SGW0904A
測試時間: 2025-09-06 16:13 +08:00
3DMark 版本: 2.28.8228 (測試專用版)""",
                'ai_structured_data': {
                    'project_name': 'Storage Benchmark Score',
                    'benchmark_score': 6883,
                    'average_bandwidth': '1174.89 MB/s',
                    'device_model': 'KINGSTON SFYR2S1TO',
                    'firmware_version': 'SGW0904A',
                    'test_datetime': '2025-09-06 16:13 +08:00',
                    'benchmark_version': '2.28.8228 (測試專用版)',
                    'extracted_fields': ['project_name', 'benchmark_score', 'average_bandwidth', 'device_model', 'firmware_version', 'test_datetime', 'benchmark_version'],
                    'confidence': 0.95,
                    'processing_method': 'ai_ocr'
                }
            },
            {
                'project_name': 'SSD Performance Test',
                'benchmark_score': 7245,
                'average_bandwidth': '1285.32 MB/s',
                'device_model': 'Samsung 980 PRO',
                'firmware_version': '5B2QGXA7',
                'test_datetime': timezone.make_aware(datetime(2025, 9, 5, 14, 30)),
                'benchmark_version': '2.28.8228',
                'test_environment': 'testing',
                'test_type': 'sequential_read',
                'processing_status': 'completed',
                'is_verified': False,
                'ocr_confidence': 0.92,
                'ocr_processing_time': 1.8,
                'read_speed': 7200.0,
                'write_speed': 6900.0,
                'iops_read': 1000000,
                'iops_write': 950000,
                'ai_structured_data': {
                    'project_name': 'SSD Performance Test',
                    'benchmark_score': 7245,
                    'average_bandwidth': '1285.32 MB/s',
                    'device_model': 'Samsung 980 PRO',
                    'firmware_version': '5B2QGXA7',
                    'confidence': 0.92
                }
            },
            {
                'project_name': 'Enterprise NVMe Test',
                'benchmark_score': 8950,
                'average_bandwidth': '1456.78 MB/s',
                'device_model': 'Intel P5800X',
                'firmware_version': 'VDV10184',
                'test_datetime': timezone.make_aware(datetime(2025, 9, 4, 10, 15)),
                'benchmark_version': '2.28.8228',
                'test_environment': 'production',
                'test_type': 'mixed_workload',
                'processing_status': 'pending',
                'is_verified': False,
                'ocr_confidence': 0.88,
                'ocr_processing_time': 3.1,
                'read_speed': 6800.0,
                'write_speed': 6100.0,
                'ai_structured_data': {
                    'project_name': 'Enterprise NVMe Test',
                    'benchmark_score': 8950,
                    'average_bandwidth': '1456.78 MB/s',
                    'device_model': 'Intel P5800X',
                    'firmware_version': 'VDV10184',
                    'confidence': 0.88
                }
            }
        ]
        
        created_count = 0
        for record_data in test_records:
            # 檢查是否已存在相同的記錄
            existing = OCRStorageBenchmark.objects.filter(
                project_name=record_data['project_name'],
                device_model=record_data['device_model'],
                test_datetime=record_data['test_datetime']
            ).first()
            
            if existing:
                self.stdout.write(f"⚠️  記錄已存在: {existing}")
                continue
            
            # 設置上傳者
            record_data['uploaded_by'] = admin_user
            
            # 創建記錄
            record = OCRStorageBenchmark.objects.create(**record_data)
            created_count += 1
            
            self.stdout.write(f"✅ 創建記錄: {record}")
            self.stdout.write(f"   效能評級: {record.get_performance_grade()}")
            self.stdout.write(f"   AI 資料摘要: {record.get_ai_data_summary()}")
        
        self.stdout.write(
            self.style.SUCCESS(f"🎉 完成！共創建 {created_count} 筆 OCR 存儲基準測試資料")
        )
        
        # 顯示統計信息
        total_records = OCRStorageBenchmark.objects.count()
        verified_records = OCRStorageBenchmark.objects.filter(is_verified=True).count()
        
        self.stdout.write("\n📊 資料庫統計:")
        self.stdout.write(f"   總記錄數: {total_records}")
        self.stdout.write(f"   已驗證記錄: {verified_records}")
        self.stdout.write(f"   驗證比例: {(verified_records/total_records*100):.1f}%" if total_records > 0 else "   驗證比例: 0%")
        
        # 顯示 API 測試指令
        self.stdout.write("\n🚀 API 測試指令:")
        self.stdout.write("   # 列出所有記錄")
        self.stdout.write("   curl -H 'Authorization: Token YOUR_TOKEN' http://localhost/api/ocr-storage-benchmarks/")
        self.stdout.write("\n   # 獲取統計資料")
        self.stdout.write("   curl -H 'Authorization: Token YOUR_TOKEN' http://localhost/api/ocr-storage-benchmarks/statistics/")
        self.stdout.write("\n   # 搜尋特定裝置")
        self.stdout.write("   curl -H 'Authorization: Token YOUR_TOKEN' 'http://localhost/api/ocr-storage-benchmarks/?device_model=KINGSTON'")