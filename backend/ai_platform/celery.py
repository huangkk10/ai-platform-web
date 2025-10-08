"""
Celery 配置 - AI Platform
用於執行向量服務預載入和問題分類預計算任務
"""

import os
from celery import Celery
from django.conf import settings

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

# 建立 Celery 應用實例
app = Celery('ai_platform')

# 從 Django settings 載入配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動發現所有 app 中的 tasks.py
app.autodiscover_tasks()

# Celery Beat 定時任務配置
app.conf.beat_schedule = {
    'preload-vector-services-dawn': {
        'task': 'library.rvt_analytics.tasks.preload_vector_services',
        'schedule': {'hour': 3, 'minute': 0},  # 每天凌晨 3:00
        'options': {'expires': 1800}  # 30 分鐘過期
    },
    'preload-vector-services-noon': {
        'task': 'library.rvt_analytics.tasks.preload_vector_services',
        'schedule': {'hour': 12, 'minute': 0},  # 每天中午 12:00
        'options': {'expires': 1800}
    },
    'preload-vector-services-evening': {
        'task': 'library.rvt_analytics.tasks.preload_vector_services',
        'schedule': {'hour': 18, 'minute': 0},  # 每天晚上 6:00
        'options': {'expires': 1800}
    },
    'precompute-question-classifications-dawn': {
        'task': 'library.rvt_analytics.tasks.precompute_question_classifications',
        'schedule': {'hour': 3, 'minute': 15},  # 凌晨 3:15 (稍後執行)
        'options': {'expires': 3600}  # 1 小時過期
    },
    'precompute-question-classifications-noon': {
        'task': 'library.rvt_analytics.tasks.precompute_question_classifications',
        'schedule': {'hour': 12, 'minute': 15},  # 中午 12:15
        'options': {'expires': 3600}
    },
    'precompute-question-classifications-evening': {
        'task': 'library.rvt_analytics.tasks.precompute_question_classifications',
        'schedule': {'hour': 18, 'minute': 15},  # 晚上 6:15
        'options': {'expires': 3600}
    },
    'cleanup-expired-cache-daily': {
        'task': 'library.rvt_analytics.tasks.cleanup_expired_cache',
        'schedule': {'hour': 2, 'minute': 0},  # 每天凌晨 2:00 清理過期快取
        'options': {'expires': 1800}
    }
}

# 時區設定
app.conf.timezone = 'Asia/Taipei'

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """除錯任務"""
    print(f'Request: {self.request!r}')
    return 'Debug task completed'

# 任務路由配置
app.conf.task_routes = {
    'library.rvt_analytics.tasks.*': {'queue': 'analytics'},
    'library.rvt_guide.tasks.*': {'queue': 'rvt_guide'},
}

# 配置任務序列化
app.conf.task_serializer = 'json'
app.conf.accept_content = ['json']
app.conf.result_serializer = 'json'
app.conf.result_expires = 3600  # 結果 1 小時後過期

# 工作進程配置
app.conf.worker_prefetch_multiplier = 1
app.conf.task_acks_late = True
app.conf.worker_max_tasks_per_child = 1000

print("✅ Celery 應用初始化完成")