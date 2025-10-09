"""
Celery 配置 - AI Platform
用於執行向量服務預載入和問題分類預計算任務
"""

import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# 設定 Django 環境變數
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

# 建立 Celery 應用實例
app = Celery('ai_platform')

# 從 Django settings 載入配置
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自動發現所有 app 中的 tasks.py
app.autodiscover_tasks()

# ==================================================================================
# RVT Assistant 向量資料庫定時更新架構 - Celery Beat 定時任務配置
# ==================================================================================
# 
# 📋 設計說明:
# 本系統採用定時批量處理方式來更新向量資料庫，而非即時生成向量
# 
# 🎯 核心原因:
# 1. 聊天過程中不會自動生成向量 (ConversationRecorder 未集成向量生成)
# 2. 手動向量化效率低，需要自動化處理累積的未向量化消息
# 3. 批量處理比即時處理更高效，不影響聊天功能穩定性
#
# 📊 實施效果 (2025-10-09 驗證):
# - 向量化率從 8.1% 提升到 30.6%
# - 熱門問題組群從 2 個增加到 3 個
# - 處理效率: ~5 消息/秒，10秒內完成50條消息
#
# 📖 詳細文檔: /docs/vector-database-scheduled-update-architecture.md
# ==================================================================================
app.conf.beat_schedule = {
    # 每小時處理新的聊天向量（高頻率確保及時性）
    'process-new-chat-vectors-hourly': {
        'task': 'library.rvt_analytics.tasks.rebuild_chat_vectors',
        'schedule': crontab(minute=0),  # 每小時的 0 分執行
        'kwargs': {
            'force_rebuild': False,  # 只處理未向量化的消息
            'user_role': 'user',     # 主要處理用戶問題
            'min_length': 5          # 過濾太短的消息
        },
        'options': {'expires': 3300}  # 55 分鐘過期，避免重疊
    },
    
    # 每6小時處理助手回覆向量（較低頻率）
    'process-assistant-vectors-periodic': {
        'task': 'library.rvt_analytics.tasks.rebuild_chat_vectors', 
        'schedule': crontab(minute=30, hour='*/6'),  # 每6小時的30分執行
        'kwargs': {
            'force_rebuild': False,
            'user_role': 'assistant',  # 處理助手回覆
            'min_length': 10
        },
        'options': {'expires': 3300}
    },
    
    # 每天凌晨預載入向量服務
    'preload-vector-services-daily': {
        'task': 'library.rvt_analytics.tasks.preload_vector_services',
        'schedule': crontab(hour=3, minute=0),  # 每天凌晨 3:00
        'options': {'expires': 1800}
    },
    
    # 每天更新問題分類和統計
    'update-question-analytics-daily': {
        'task': 'library.rvt_analytics.tasks.precompute_question_classifications',
        'schedule': crontab(hour=3, minute=30),  # 每天凌晨 3:30
        'options': {'expires': 3600}
    },
    
    # 每天清理過期快取
    'cleanup-cache-daily': {
        'task': 'library.rvt_analytics.tasks.cleanup_expired_cache',
        'schedule': crontab(hour=2, minute=0),  # 每天凌晨 2:00
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