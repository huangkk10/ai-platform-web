#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Django 管理命令：測試 CDM8 OCR 解析並保存到資料庫
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import datetime
import os
import sys
import json
import re

# 添加項目路徑
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../../'))

from api.models import OCRStorageBenchmark


class Command(BaseCommand):
    help = '測試 CDM8 OCR 解析功能並保存結果到資料庫'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--mock-cdm8',
            action='store_true',
            help='使用模擬 CDM8 資料進行測試',
        )
        parser.add_argument(
            '--user',
            type=str,
            help='指定上傳者用戶名',
            default='admin'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('🔬 開始 CDM8 OCR 解析測試')
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
        
        if options.get('mock_cdm8'):
            self.test_cdm8_parsing_and_save(user)
    
    def test_cdm8_parsing_and_save(self, user):
        """測試 CDM8 解析並保存"""
        self.stdout.write('\n🧪 測試 CDM8 解析功能')
        
        # 模擬 CDM8 分析結果（來自您的執行輸出）
        mock_cdm8_answer = """📦 測試環境資訊  
| 項目 | 數值 |
|------|------|
| Profile | Default |
| Test | 1 GiB (x5) [K: 0% (0/954GiB)] |
| Mode | [Admin] |
| Date | 2025/07/21 13:36:57 |
| OS | Windows 11 Pro 24H2 [10.0 Build 26100] (x64) |

📊 循序讀取 (Sequential Read)  
| 測試項目 | MB/s | IOPS | Latency (us) |
|----------|------|------|--------------|
| SEQ-1MiB (Q8T1) | 7804.655 | 7443.1 | 1074.01 |
| SEQ-128KiB (Q32T1) | 7800.023 | 59509.5 | 537.45 |

📝 循序寫入 (Sequential Write)  
| 測試項目 | MB/s | IOPS | Latency (us) |
|----------|------|------|--------------|
| SEQ-1MiB (Q8T1) | 5207.282 | 4966.1 | 1608.38 |
| SEQ-128KiB (Q32T1) | 5082.502 | 38776.4 | 824.39 |

🔄 隨機讀取 (Random Read)  
| 測試項目 | MB/s | IOPS | Latency (us) |
|----------|------|------|--------------|
| RND-4KiB (Q32T16) | 3574.113 | 872586.2 | 585.76 |
| RND-4KiB (Q1T1) | 67.574 | 16497.6 | 60.54 |

🧪 隨機寫入 (Random Write)  
| 測試項目 | MB/s | IOPS | Latency (us) |
|----------|------|------|--------------|
| RND-4KiB (Q32T16) | 5276.224 | 1288140.6 | 396.84 |
| RND-4KiB (Q1T1) | 237.201 | 57910.4 | 17.20 |"""
        
        # 使用改進的解析功能
        parsed_data = self.parse_cdm8_data(mock_cdm8_answer)
        
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
                project_name=parsed_data.get('project_name', 'CDM8 Analysis'),
                benchmark_score=parsed_data.get('benchmark_score'),
                average_bandwidth=parsed_data.get('average_bandwidth'),
                device_model=parsed_data.get('device_model', 'CDM8 Test Device'),
                firmware_version=parsed_data.get('firmware_version', 'Unknown'),
                test_datetime=parsed_data.get('test_datetime', datetime.now()),
                benchmark_version='CDM8',
                read_speed=parsed_data.get('read_speed'),
                write_speed=parsed_data.get('write_speed'),
                iops_read=parsed_data.get('iops_read'),
                iops_write=parsed_data.get('iops_write'),
                test_environment=parsed_data.get('test_environment', 'testing'),
                test_type=parsed_data.get('test_type', 'comprehensive'),
                ocr_raw_text=mock_cdm8_answer,
                ai_structured_data=ai_structured_data,  # 使用處理過的資料
                processing_status='completed',
                ocr_confidence=0.98,
                ocr_processing_time=3.2,
                uploaded_by=user
            )
            
            self.stdout.write(f'\n✅ CDM8 資料已保存到資料庫')
            self.stdout.write(f'   記錄 ID: {ocr_record.id}')
            self.stdout.write(f'   專案名稱: {ocr_record.project_name}')
            self.stdout.write(f'   基準分數: {ocr_record.benchmark_score}')
            self.stdout.write(f'   效能評級: {ocr_record.get_performance_grade()}')
            self.stdout.write(f'   平均帶寬: {ocr_record.average_bandwidth}')
            
            if ocr_record.read_speed and ocr_record.write_speed:
                self.stdout.write(f'   讀取速度: {ocr_record.read_speed:.2f} MB/s')
                self.stdout.write(f'   寫入速度: {ocr_record.write_speed:.2f} MB/s')
            
            if ocr_record.iops_read and ocr_record.iops_write:
                self.stdout.write(f'   讀取IOPS: {ocr_record.iops_read:,}')
                self.stdout.write(f'   寫入IOPS: {ocr_record.iops_write:,}')
                
        except Exception as e:
            self.stdout.write(f'❌ 保存失敗: {e}')
    
    def parse_cdm8_data(self, cdm8_text: str) -> dict:
        """
        基於資料庫欄位結構解析 CDM8 資料
        
        Args:
            cdm8_text (str): CDM8 分析結果文本
            
        Returns:
            dict: 結構化的資料，對應 OCRStorageBenchmark 欄位
        """
        # 初始化基於資料庫欄位的結構
        parsed_data = {
            'project_name': 'CDM8 Storage Benchmark',
            'benchmark_score': None,
            'average_bandwidth': None,
            'device_model': None,
            'firmware_version': None,
            'test_datetime': None,
            'benchmark_version': 'CDM8',
            'read_speed': None,
            'write_speed': None,
            'iops_read': None,
            'iops_write': None,
            'test_environment': 'testing',
            'test_type': 'comprehensive',
            'sequential_read_data': {},
            'sequential_write_data': {},
            'random_read_data': {},
            'random_write_data': {},
            'system_info': {}
        }
        
        try:
            # 1. 解析系統環境資訊
            self._parse_system_environment(cdm8_text, parsed_data)
            
            # 2. 解析循序讀取效能
            self._parse_sequential_read(cdm8_text, parsed_data)
            
            # 3. 解析循序寫入效能
            self._parse_sequential_write(cdm8_text, parsed_data)
            
            # 4. 解析隨機讀取效能
            self._parse_random_read(cdm8_text, parsed_data)
            
            # 5. 解析隨機寫入效能
            self._parse_random_write(cdm8_text, parsed_data)
            
            # 6. 計算綜合指標
            self._calculate_cdm8_metrics(parsed_data)
            
            return parsed_data
            
        except Exception as e:
            self.stdout.write(f'⚠️ CDM8 解析錯誤: {e}')
            return parsed_data
    
    def _parse_system_environment(self, text: str, data: dict):
        """解析系統環境資訊"""
        # 解析 Profile
        profile_match = re.search(r'Profile\s*\|\s*([^\n\|]+)', text)
        if profile_match:
            data['project_name'] = f"CDM8 - {profile_match.group(1).strip()}"
        
        # 解析測試模式
        mode_match = re.search(r'Mode\s*\|\s*\[([^\]]+)\]', text)
        if mode_match:
            mode = mode_match.group(1).lower()
            data['test_environment'] = 'production' if mode == 'admin' else 'testing'
        
        # 解析測試日期
        date_match = re.search(r'Date\s*\|\s*([\d/\s:]+)', text)
        if date_match:
            try:
                date_str = date_match.group(1).strip().replace('/', '-')
                data['test_datetime'] = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                data['test_datetime'] = datetime.now()
        
        # 解析作業系統
        os_match = re.search(r'OS\s*\|\s*([^\n\|]+)', text)
        if os_match:
            data['system_info']['os'] = os_match.group(1).strip()
        
        # 解析測試配置
        test_match = re.search(r'Test\s*\|\s*([^\n\|]+)', text)
        if test_match:
            data['system_info']['test_config'] = test_match.group(1).strip()
    
    def _parse_sequential_read(self, text: str, data: dict):
        """解析循序讀取效能"""
        # 尋找 SEQ-1MiB (Q8T1) 的數據
        seq_read_pattern = r'SEQ-1MiB \(Q8T1\)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
        match = re.search(seq_read_pattern, text)
        
        if match:
            mb_s = float(match.group(1))
            iops = float(match.group(2))
            latency = float(match.group(3))
            
            data['read_speed'] = mb_s
            data['iops_read'] = int(iops)
            data['sequential_read_data'] = {
                'speed_mb_s': mb_s,
                'iops': iops,
                'latency_us': latency,
                'test_type': 'SEQ-1MiB (Q8T1)'
            }
    
    def _parse_sequential_write(self, text: str, data: dict):
        """解析循序寫入效能"""
        # 尋找循序寫入區段中的 SEQ-1MiB (Q8T1)
        write_section = re.search(r'循序寫入.*?(?=🔄|$)', text, re.DOTALL)
        if write_section:
            write_text = write_section.group(0)
            seq_write_pattern = r'SEQ-1MiB \(Q8T1\)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
            match = re.search(seq_write_pattern, write_text)
            
            if match:
                mb_s = float(match.group(1))
                iops = float(match.group(2))
                latency = float(match.group(3))
                
                data['write_speed'] = mb_s
                data['iops_write'] = int(iops)
                data['sequential_write_data'] = {
                    'speed_mb_s': mb_s,
                    'iops': iops,
                    'latency_us': latency,
                    'test_type': 'SEQ-1MiB (Q8T1)'
                }
    
    def _parse_random_read(self, text: str, data: dict):
        """解析隨機讀取效能"""
        # 尋找隨機讀取區段中的 RND-4KiB (Q32T16) - 高性能模式
        read_section = re.search(r'隨機讀取.*?(?=🧪|$)', text, re.DOTALL)
        if read_section:
            read_text = read_section.group(0)
            rnd_read_pattern = r'RND-4KiB \(Q32T16\)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
            match = re.search(rnd_read_pattern, read_text)
            
            if match:
                mb_s = float(match.group(1))
                iops = float(match.group(2))
                latency = float(match.group(3))
                
                data['random_read_data'] = {
                    'speed_mb_s': mb_s,
                    'iops': iops,
                    'latency_us': latency,
                    'test_type': 'RND-4KiB (Q32T16)'
                }
    
    def _parse_random_write(self, text: str, data: dict):
        """解析隨機寫入效能"""
        # 尋找隨機寫入區段中的 RND-4KiB (Q32T16) - 高性能模式
        write_section = re.search(r'隨機寫入.*?$', text, re.DOTALL)
        if write_section:
            write_text = write_section.group(0)
            rnd_write_pattern = r'RND-4KiB \(Q32T16\)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)'
            match = re.search(rnd_write_pattern, write_text)
            
            if match:
                mb_s = float(match.group(1))
                iops = float(match.group(2))
                latency = float(match.group(3))
                
                data['random_write_data'] = {
                    'speed_mb_s': mb_s,
                    'iops': iops,
                    'latency_us': latency,
                    'test_type': 'RND-4KiB (Q32T16)'
                }
    
    def _calculate_cdm8_metrics(self, data: dict):
        """計算 CDM8 綜合指標"""
        # 計算平均帶寬
        if data['read_speed'] and data['write_speed']:
            avg_bandwidth = (data['read_speed'] + data['write_speed']) / 2
            data['average_bandwidth'] = f"{avg_bandwidth:.2f} MB/s"
        elif data['read_speed']:
            data['average_bandwidth'] = f"{data['read_speed']:.2f} MB/s"
        
        # 計算基準分數（基於 IOPS 和速度的加權平均）
        if data['iops_read'] and data['iops_write'] and data['read_speed'] and data['write_speed']:
            # 權重: IOPS 70%, Speed 30%
            iops_score = (data['iops_read'] + data['iops_write']) / 1000 * 0.7
            speed_score = (data['read_speed'] + data['write_speed']) / 100 * 0.3
            data['benchmark_score'] = int(iops_score + speed_score)
        
        # 設置裝置型號（如果沒有檢測到的話）
        if not data['device_model']:
            # 基於效能特徵推測裝置類型
            if data['read_speed'] and data['read_speed'] > 7000:
                data['device_model'] = 'High-Performance NVMe SSD'
            elif data['read_speed'] and data['read_speed'] > 5000:
                data['device_model'] = 'Standard NVMe SSD'
            else:
                data['device_model'] = 'Storage Device'