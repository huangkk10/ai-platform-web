#!/bin/bash

# 等待 PostgreSQL 啟動
echo "Waiting for PostgreSQL to start..."
while ! nc -z postgres_db 5432; do
  sleep 1
done

echo "PostgreSQL is ready!"

# 執行 Django 遷移
echo "Running Django migrations..."
python manage.py makemigrations
python manage.py migrate

# 建立超級使用者 (如果不存在)
echo "Creating superuser..."
python manage.py shell << EOF
from django.contrib.auth.models import User
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# 收集靜態檔案
echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Django setup completed!"