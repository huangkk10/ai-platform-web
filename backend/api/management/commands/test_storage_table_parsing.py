#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django 管理命令：測試儲存基準測試表格解析並保存到資料庫
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime
import os
import sys

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

from api.models import OCRStorageBenchmark


class Command(BaseCommand):
    help = '測試儲存基準測試表格解析功能並保存結果到資料庫'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mock-table',
            action='store_true',
            help='使用模擬儲存基準測試表格資料進行測試',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='指定上傳者用戶名',
            default='admin'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔬 開始儲存基準測試表格解析測試')
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
        
        if options.get('mock_table'):
            self.test_storage_table_parsing_and_save(user)
    
    def test_storage_table_parsing_and_save(self, user):
        """測試儲存基準測試表格解析並保存"""
        self.stdout.write('\n🧪 測試儲存基準測試表格解析功能')
        
        # 模擬儲存基準測試表格分析結果
        mock_table_answer = """根據您提供的圖片，這是一個儲存基準測試的結果表格：

| 項目 | 結果 |
|------|------|
| **儲存基準分數 (Storage Benchmark Score)** | 6883 |
| **平均頻寬 (Average Bandwidth)** | 1 174.89 MB/s |
| **裝置型號** | KINGSTON SFYR2S1TO |
| **韌體 (Firmware)** | SGW0904A |
| **測試時間** | 2025‑09‑06 16:13 (+08:00) |
| **3DMark 軟體版本** | 2.28.8228 (已安裝) – 最新可用 2.29.8294.0 |

這個測試結果顯示了一個 Kingston 固態硬碟的效能表現，基準分數為 6883，平均頻寬達到 1174.89 MB/s，是一個相當不錯的儲存裝置效能。"""
        
        # 使用改進的解析功能
        parsed_data = self.parse_storage_benchmark_table(mock_table_answer)
        
        self.stdout.write('\n📋 解析出的結構化資料:')
        for key, value in parsed_data.items():
            if isinstance(value, dict):
                self.stdout.write(f'  {key}:')
                for sub_key, sub_value in value.items():
                    self.stdout.write(f'    {sub_key}: {sub_value}')
            else:
                self.stdout.write(f'  {key}: {value}')
        
        # 保存到資料庫
        try:
            # 處理 datetime 序列化問題
            ai_structured_data = parsed_data.copy()
            if 'test_datetime' in ai_structured_data and isinstance(ai_structured_data['test_datetime'], datetime):
                ai_structured_data['test_datetime'] = ai_structured_data['test_datetime'].isoformat()
            
            ocr_record = OCRStorageBenchmark.objects.create(
                project_name=parsed_data.get('project_name', 'Storage Benchmark Analysis'),
                benchmark_score=parsed_data.get('benchmark_score'),
                average_bandwidth=parsed_data.get('average_bandwidth'),
                device_model=parsed_data.get('device_model', 'Storage Benchmark Device'),
                firmware_version=parsed_data.get('firmware_version', 'Unknown'),
                test_datetime=parsed_data.get('test_datetime', datetime.now()),
                benchmark_version=parsed_data.get('benchmark_version', '3DMark'),
                read_speed=parsed_data.get('read_speed'),
                write_speed=parsed_data.get('write_speed'),
                iops_read=parsed_data.get('iops_read'),
                iops_write=parsed_data.get('iops_write'),
                test_environment=parsed_data.get('test_environment', 'benchmark'),
                test_type=parsed_data.get('test_type', 'comprehensive'),
                ocr_raw_text=mock_table_answer,
                ai_structured_data=ai_structured_data,
                processing_status='completed',
                ocr_confidence=0.98,
                ocr_processing_time=2.1,
                uploaded_by=user
            )
            
            self.stdout.write(f'\n✅ 儲存基準測試資料已保存到資料庫')
            self.stdout.write(f'   記錄 ID: {ocr_record.id}')
            self.stdout.write(f'   專案名稱: {ocr_record.project_name}')
            self.stdout.write(f'   基準分數: {ocr_record.benchmark_score}')
            self.stdout.write(f'   效能評級: {ocr_record.get_performance_grade()}')
            self.stdout.write(f'   平均帶寬: {ocr_record.average_bandwidth}')
            self.stdout.write(f'   裝置型號: {ocr_record.device_model}')
            self.stdout.write(f'   韌體版本: {ocr_record.firmware_version}')
            
            if ocr_record.read_speed and ocr_record.write_speed:
                self.stdout.write(f'   讀取速度: {ocr_record.read_speed:.2f} MB/s')
                self.stdout.write(f'   寫入速度: {ocr_record.write_speed:.2f} MB/s')
            
            if ocr_record.iops_read and ocr_record.iops_write:
                self.stdout.write(f'   讀取IOPS: {ocr_record.iops_read:,}')
                self.stdout.write(f'   寫入IOPS: {ocr_record.iops_write:,}')
                
        except Exception as e:
            self.stdout.write(f'❌ 保存失敗: {e}')
    
    def parse_storage_benchmark_table(self, table_text: str) -> dict:
        """
        專門解析儲存基準測試表格格式的資料
        """
        import re
        from datetime import datetime
        
        # 初始化基於資料庫欄位的結構
        parsed_data = {
            'project_name': 'Storage Benchmark Analysis',
            'benchmark_score': None,
            'average_bandwidth': None,
            'device_model': None,
            'firmware_version': None,
            'test_datetime': None,
            'benchmark_version': None,
            'test_environment': 'benchmark',
            'test_type': 'comprehensive',
            'processing_status': 'completed',
            'ocr_confidence': 0.98
        }
        
        try:
            # 定義欄位對映模式
            field_patterns = {
                'benchmark_score': [
                    r'\*\*儲存基準分數.*?\*\*\s*\|\s*(\d+)',
                    r'Storage Benchmark Score.*?\|\s*(\d+)',
                    r'儲存基準分數.*?\|\s*(\d+)'
                ],
                'average_bandwidth': [
                    r'\*\*平均頻寬.*?\*\*\s*\|\s*([\d\s,.]+\s*MB/s)',
                    r'Average Bandwidth.*?\|\s*([\d\s,.]+\s*MB/s)',
                    r'平均頻寬.*?\|\s*([\d\s,.]+\s*MB/s)'
                ],
                'device_model': [
                    r'\*\*裝置型號\*\*\s*\|\s*([A-Z0-9\s]+)',
                    r'裝置型號.*?\|\s*([A-Z0-9\s]+)',
                    r'Device.*?\|\s*([A-Z0-9\s]+)'
                ],
                'firmware_version': [
                    r'\*\*韌體.*?\*\*\s*\|\s*([A-Z0-9]+)',
                    r'Firmware.*?\|\s*([A-Z0-9]+)',
                    r'韌體.*?\|\s*([A-Z0-9]+)'
                ],
                'test_datetime': [
                    r'\*\*測試時間\*\*\s*\|\s*([\d\-‑\s:+()]+)',
                    r'測試時間.*?\|\s*([\d\-‑\s:+()]+)',
                    r'Test.*?Time.*?\|\s*([\d\-‑\s:+()]+)'
                ],
                'benchmark_version': [
                    r'\*\*3DMark.*?版本\*\*\s*\|\s*([\d.]+[^|]*)',
                    r'3DMark.*?版本.*?\|\s*([\d.]+[^|]*)',
                    r'3DMark.*?\|\s*([\d.]+[^|]*)'
                ]
            }
            
            # 逐一解析每個欄位
            for field, patterns in field_patterns.items():
                for pattern in patterns:
                    matches = re.findall(pattern, table_text, re.IGNORECASE | re.MULTILINE)
                    if matches:
                        value = matches[0].strip()
                        
                        # 針對不同欄位進行特殊處理
                        if field == 'benchmark_score':
                            try:
                                parsed_data[field] = int(value)
                            except ValueError:
                                pass
                                
                        elif field == 'average_bandwidth':
                            # 清理帶寬格式 "1 174.89 MB/s" -> "1174.89 MB/s"
                            cleaned_bandwidth = re.sub(r'(\d)\s+(\d)', r'\1\2', value)
                            parsed_data[field] = cleaned_bandwidth
                            
                        elif field == 'device_model':
                            parsed_data[field] = value.strip()
                            
                        elif field == 'firmware_version':
                            parsed_data[field] = value.strip()
                            
                        elif field == 'test_datetime':
                            # 處理日期格式 "2025‑09‑06 16:13 (+08:00)"
                            try:
                                # 移除時區資訊並正規化分隔符
                                date_str = re.sub(r'\s*\([^)]+\)', '', value)  # 移除 (+08:00)
                                date_str = date_str.replace('‑', '-').strip()  # 正規化分隔符
                                
                                # 嘗試解析不同的日期格式
                                date_formats = [
                                    '%Y-%m-%d %H:%M',
                                    '%Y-%m-%d %H:%M:%S',
                                    '%Y/%m/%d %H:%M',
                                    '%Y/%m/%d %H:%M:%S'
                                ]
                                
                                for fmt in date_formats:
                                    try:
                                        parsed_data[field] = datetime.strptime(date_str, fmt)
                                        break
                                    except ValueError:
                                        continue
                                        
                            except Exception as e:
                                self.stdout.write(f"⚠️ 日期解析失敗: {value} -> {e}")
                                parsed_data[field] = datetime.now()
                                
                        elif field == 'benchmark_version':
                            # 提取版本號 "2.28.8228 (已安裝) – 最新可用 2.29.8294.0"
                            version_match = re.match(r'([\d.]+)', value)
                            if version_match:
                                parsed_data[field] = version_match.group(1)
                            else:
                                parsed_data[field] = value
                        
                        break  # 找到匹配就跳出內層循環
            
            # 計算衍生欄位
            self._calculate_derived_fields(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            self.stdout.write(f'⚠️ 儲存基準測試表格解析錯誤: {e}')
            return parsed_data
    
    def _calculate_derived_fields(self, data: dict):
        """計算衍生欄位"""
        import re
        
        # 基於平均頻寬推算讀寫速度
        if data.get('average_bandwidth'):
            try:
                # 提取數值 "1174.89 MB/s" -> 1174.89
                bandwidth_match = re.search(r'([\d.]+)', data['average_bandwidth'])
                if bandwidth_match:
                    avg_speed = float(bandwidth_match.group(1))
                    # 假設讀取速度稍高於平均值，寫入速度稍低
                    data['read_speed'] = round(avg_speed * 1.1, 2)
                    data['write_speed'] = round(avg_speed * 0.9, 2)
            except ValueError:
                pass
        
        # 基於基準分數推算 IOPS（簡化計算）
        if data.get('benchmark_score'):
            # 簡化的 IOPS 估算公式
            estimated_iops = data['benchmark_score'] * 100
            data['iops_read'] = int(estimated_iops * 1.2)
            data['iops_write'] = int(estimated_iops * 0.8)
        
        # 設置項目名稱
        if data.get('device_model'):
            data['project_name'] = f"Storage Benchmark - {data['device_model']}"