"""
Django 管理命令 - 預載入向量服務
手動執行向量服務和模型的預載入
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '預載入向量服務和 embedding 模型，提升系統回應速度'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model-type',
            type=str,
            default='all',
            help='指定載入的模型類型 (lightweight, standard, high_precision, ultra_high, all)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制重新載入所有模型'
        )

    def handle(self, *args, **options):
        model_type = options['model_type']
        force_reload = options['force']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 開始預載入向量服務 - {timezone.now()}')
        )

        try:
            from library.rvt_analytics.optimized_embedding_service import (
                OptimizedEmbeddingService,
                preload_embedding_services,
                get_cache_statistics
            )

            # 清除現有快取 (如果強制重載)
            if force_reload:
                self.stdout.write(self.style.WARNING('🔄 清除現有模型快取...'))
                OptimizedEmbeddingService.clear_model_cache()

            # 預載入指定模型
            if model_type == 'all':
                self.stdout.write('📚 載入所有模型類型...')
                results = preload_embedding_services()
            else:
                self.stdout.write(f'📚 載入 {model_type} 模型...')
                service = OptimizedEmbeddingService.get_instance(model_type)
                _ = service.model  # 觸發載入
                results = {model_type: {'status': 'success'}}

            # 顯示載入結果
            self.stdout.write('\n📊 模型載入結果:')
            for model, result in results.items():
                if result.get('status') == 'success':
                    dimension = result.get('dimension', 'N/A')
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ {model}: {dimension}維')
                    )
                else:
                    error = result.get('error', '未知錯誤')
                    self.stdout.write(
                        self.style.ERROR(f'  ❌ {model}: {error}')
                    )

            # 顯示快取統計
            cache_stats = get_cache_statistics()
            if 'error' not in cache_stats:
                self.stdout.write('\n💾 快取統計:')
                if 'redis_memory_used' in cache_stats:
                    self.stdout.write(f'  Redis 記憶體使用: {cache_stats["redis_memory_used"]}')
                
                cache_keys = cache_stats.get('cache_keys', {})
                self.stdout.write(f'  快取鍵數量: {cache_keys.get("total", 0)}')
                self.stdout.write(f'  載入的模型實例: {cache_stats.get("loaded_models", 0)}')
            
            self.stdout.write(
                self.style.SUCCESS(f'\n🎉 向量服務預載入完成 - {timezone.now()}')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 預載入失敗: {str(e)}')
            )
            logger.error(f"預載入向量服務失敗: {e}")
            raise