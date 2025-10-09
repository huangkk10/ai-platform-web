#!/bin/bash

# AI Platform - 系統監控腳本
# 監控 Redis 快取、Celery 任務和系統效能

echo "📊 AI Platform 系統監控"
echo "========================"

# 檢查服務狀態
echo "🔍 檢查容器狀態..."
docker-compose ps

echo ""
echo "💾 Redis 統計..."
docker exec ai-redis redis-cli --no-raw info memory | grep -E "(used_memory_human|used_memory_peak_human)"
docker exec ai-redis redis-cli --no-raw info keyspace
echo "Redis 鍵總數: $(docker exec ai-redis redis-cli dbsize)"

echo ""
echo "🧠 向量服務快取統計..."
docker exec ai-django python -c "
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

try:
    from library.rvt_analytics.optimized_embedding_service import get_cache_statistics, OptimizedEmbeddingService
    
    stats = get_cache_statistics()
    if 'error' not in stats:
        print(f'Redis 記憶體使用: {stats.get(\"redis_memory_used\", \"N/A\")}')
        cache_keys = stats.get('cache_keys', {})
        print(f'向量快取鍵: {cache_keys.get(\"embeddings\", 0)}')
        print(f'模型狀態鍵: {cache_keys.get(\"status\", 0)}')
        print(f'載入的模型實例: {stats.get(\"loaded_models\", 0)}')
        print(f'快取的模型: {stats.get(\"cached_models\", 0)}')
    else:
        print(f'快取統計錯誤: {stats[\"error\"]}')
except Exception as e:
    print(f'獲取統計失敗: {e}')
"

echo ""
echo "⚙️  Celery 任務統計..."
docker exec ai-django python -c "
import sys
import os
sys.path.append('/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')

import django
django.setup()

try:
    from celery import current_app
    
    # 獲取 active 任務
    inspect = current_app.control.inspect()
    active = inspect.active()
    scheduled = inspect.scheduled()
    
    if active:
        total_active = sum(len(tasks) for tasks in active.values())
        print(f'執行中任務: {total_active}')
    else:
        print('執行中任務: 0')
        
    if scheduled:
        total_scheduled = sum(len(tasks) for tasks in scheduled.values())
        print(f'已排程任務: {total_scheduled}')
    else:
        print('已排程任務: 0')
        
except Exception as e:
    print(f'Celery 統計錯誤: {e}')
"

echo ""
echo "📈 最近的預載入任務..."
docker logs ai-celery-worker --tail 5 | grep -E "(preload|classification|SUCCESS|ERROR)" || echo "沒有找到相關日誌"

echo ""
echo "🔥 系統資源使用..."
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"

echo ""
echo "🎯 API 回應時間測試..."
echo "測試配置 API..."
time curl -s "http://10.10.173.12/api/rvt-guide/config/" > /dev/null && echo "✅ RVT Guide Config API 正常" || echo "❌ RVT Guide Config API 異常"

echo ""
echo "測試優化的分析 API..."
time curl -s "http://10.10.173.12/api/rvt-analytics/overview/?days=7" > /dev/null && echo "✅ Analytics Overview API 正常" || echo "❌ Analytics Overview API 異常"

echo ""
echo "📱 可用的管理介面:"
echo "  • Celery 任務監控: http://10.10.173.12:5555"
echo "  • Portainer 容器管理: http://10.10.173.12:9000"
echo "  • Adminer 資料庫: http://10.10.173.12:9090"
echo ""
echo "🔄 監控完成 - $(date)"