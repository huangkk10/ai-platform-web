#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理命令：將照片直接上傳到資料庫中
"""

from django.core.management.base import BaseCommand
from api.models import Employee
import os


class Command(BaseCommand):
    help = '將照片檔案直接存儲到資料庫中的員工記錄'

    def add_arguments(self, parser):
        parser.add_argument('--employee-name', type=str, help='員工姓名')
        parser.add_argument('--photo-path', type=str, help='照片檔案路徑')

    def handle(self, *args, **options):
        employee_name = options.get('employee_name') or '張小明'
        photo_path = options.get('photo_path') or '/app/edward.jpg'

        self.stdout.write("🚀 開始將照片存儲到資料庫...")
        self.stdout.write(f"📝 員工姓名: {employee_name}")
        self.stdout.write(f"📸 照片路徑: {photo_path}")

        # 檢查照片檔案是否存在
        if not os.path.exists(photo_path):
            self.stdout.write(
                self.style.ERROR(f"❌ 照片檔案不存在: {photo_path}")
            )
            return

        # 檢查檔案大小
        file_size = os.path.getsize(photo_path)
        size_mb = file_size / (1024 * 1024)
        self.stdout.write(f"📊 照片大小: {file_size} bytes ({size_mb:.2f} MB)")

        if size_mb > 10:
            self.stdout.write(
                self.style.WARNING("⚠️  照片檔案很大，可能會影響資料庫效能")
            )

        try:
            # 查找員工
            employee = Employee.objects.get(name=employee_name)
            self.stdout.write(f"✅ 找到員工: {employee.name} - {employee.position}")

            # 存儲照片到資料庫
            success = employee.save_photo_to_db(photo_path)

            if success:
                # 驗證存儲結果
                employee.refresh_from_db()
                stored_size = len(employee.photo_binary) if employee.photo_binary else 0
                
                self.stdout.write(
                    self.style.SUCCESS(f"🎉 照片已成功存儲到資料庫！")
                )
                self.stdout.write(f"📄 檔案名: {employee.photo_filename}")
                self.stdout.write(f"🏷️  類型: {employee.photo_content_type}")
                self.stdout.write(f"💾 存儲大小: {stored_size} bytes")
                
                # 顯示資料庫影響
                self.stdout.write("\n📈 資料庫影響:")
                self.stdout.write(f"   • 新增 {stored_size} bytes 到 api_employee 表")
                self.stdout.write(f"   • 該記錄現在佔用約 {stored_size / 1024:.1f} KB")
                
                # 生成 data URL 示例
                data_url = employee.get_photo_data_url()
                if data_url:
                    preview = data_url[:100] + "..." if len(data_url) > 100 else data_url
                    self.stdout.write(f"\n🖼️  Data URL 預覽: {preview}")
                
            else:
                self.stdout.write(
                    self.style.ERROR("❌ 照片存儲失敗")
                )

        except Employee.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f"❌ 找不到員工: {employee_name}")
            )
            
            # 顯示現有員工列表
            employees = Employee.objects.all()
            if employees:
                self.stdout.write("\n📋 現有員工:")
                for emp in employees:
                    self.stdout.write(f"   • {emp.name}")
        
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 執行失敗: {str(e)}")
            )

        self.stdout.write("\n✨ 完成")