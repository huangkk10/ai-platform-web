from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from api.models import TestClass


class Command(BaseCommand):
    help = 'Create default test classes'

    def handle(self, *args, **options):
        # 取得一個 admin 用戶作為建立者，如果沒有就建立一個
        try:
            admin_user = User.objects.filter(is_staff=True).first()
            if not admin_user:
                admin_user = User.objects.filter(is_superuser=True).first()
            if not admin_user:
                # 如果沒有管理員用戶，建立一個默認的
                admin_user = User.objects.create_user(
                    username='admin',
                    email='admin@example.com',
                    password='admin123',
                    is_staff=True,
                    is_superuser=True
                )
                self.stdout.write(
                    self.style.SUCCESS('✅ 建立了默認管理員用戶: admin (密碼: admin123)')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 無法建立管理員用戶: {e}')
            )
            return

        # 預設的測試類別資料
        default_classes = [
            {
                'name': 'ULINK NVMe Protocol',
                'description': '預設的 ULINK NVMe 協議測試類別',
            }
        ]

        created_count = 0
        for class_data in default_classes:
            test_class, created = TestClass.objects.get_or_create(
                name=class_data['name'],
                defaults={
                    'description': class_data['description'],
                    'created_by': admin_user,
                    'is_active': True
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✅ 建立測試類別: {test_class.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  測試類別已存在: {test_class.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'🎉 完成！共建立了 {created_count} 個測試類別')
        )