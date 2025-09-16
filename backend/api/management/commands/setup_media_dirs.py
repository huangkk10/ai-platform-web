import os
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Setup media directories for file uploads'
    
    def handle(self, *args, **options):
        """創建媒體檔案所需的目錄結構"""
        
        # 創建主 media 目錄
        media_root = settings.MEDIA_ROOT
        if not os.path.exists(media_root):
            os.makedirs(media_root)
            self.stdout.write(f"✅ 創建目錄: {media_root}")
        else:
            self.stdout.write(f"📁 目錄已存在: {media_root}")
        
        # 創建 know_issues 子目錄
        know_issues_dir = os.path.join(media_root, 'know_issues')
        if not os.path.exists(know_issues_dir):
            os.makedirs(know_issues_dir)
            self.stdout.write(f"✅ 創建目錄: {know_issues_dir}")
        else:
            self.stdout.write(f"📁 目錄已存在: {know_issues_dir}")
        
        # 創建其他可能需要的子目錄
        subdirs = ['avatars', 'documents', 'temp']
        for subdir in subdirs:
            dir_path = os.path.join(media_root, subdir)
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
                self.stdout.write(f"✅ 創建目錄: {dir_path}")
            else:
                self.stdout.write(f"📁 目錄已存在: {dir_path}")
        
        # 檢查目錄權限
        try:
            test_file = os.path.join(media_root, '.test_write')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            self.stdout.write(f"✅ 目錄權限正常: {media_root}")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 目錄權限錯誤: {media_root} - {str(e)}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("🎉 媒體目錄設定完成！")
        )