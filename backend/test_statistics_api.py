#!/usr/bin/env python
"""測試統計 API"""
import sys
import os
import django

sys.path.append('/home/user/codes/ai-platform-web/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import UnifiedBenchmarkTestCase
from django.db.models import Count

# 模擬統計 API 的邏輯
queryset = UnifiedBenchmarkTestCase.objects.filter(test_type='vsa')

print("=" * 60)
print("VSA 測試案例統計")
print("=" * 60)

# 基本統計
total_count = queryset.count()
active_count = queryset.filter(is_active=True).count()
inactive_count = queryset.filter(is_active=False).count()

print(f"\n總數: {total_count}")
print(f"啟用: {active_count}")
print(f"停用: {inactive_count}")

# 難度分布
difficulty_stats = queryset.values('difficulty_level').annotate(count=Count('id'))
difficulty_dict = {
    'easy': 0,
    'medium': 0,
    'hard': 0,
}

print("\n難度分布（原始查詢結果）:")
for stat in difficulty_stats:
    print(f"  {stat['difficulty_level']}: {stat['count']}")
    difficulty_dict[stat['difficulty_level']] = stat['count']

print("\n難度分布（字典格式）:")
print(f"  簡單 (easy): {difficulty_dict['easy']}")
print(f"  中等 (medium): {difficulty_dict['medium']}")
print(f"  困難 (hard): {difficulty_dict['hard']}")

print("\n" + "=" * 60)
print("測試完成")
print("=" * 60)
