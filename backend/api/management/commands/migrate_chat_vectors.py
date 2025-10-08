"""
Django Management Command - 聊天消息向量化遷移

此命令負責：
- 處理現有聊天消息數據的向量化
- 批量生成向量並存儲到 chat_message_embeddings_1024 表
- 執行聚類分析
- 提供進度報告和統計
"""

import logging
from typing import Dict, List
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

# 導入模型
try:
    from api.models import ChatMessage, ConversationSession
    MODELS_AVAILABLE = True
except ImportError:
    MODELS_AVAILABLE = False
    print("⚠️ 無法導入 ChatMessage 模型")

# 導入向量化服務
try:
    from library.rvt_analytics.chat_vector_service import get_chat_vector_service
    from library.rvt_analytics.chat_clustering_service import get_clustering_service
    VECTOR_SERVICES_AVAILABLE = True
except ImportError:
    VECTOR_SERVICES_AVAILABLE = False
    print("⚠️ 無法導入向量化服務")

class Command(BaseCommand):
    help = '批量處理聊天消息向量化和聚類分析'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='批量處理大小（預設: 50）'
        )
        
        parser.add_argument(
            '--user-role',
            type=str,
            default='user',
            choices=['user', 'assistant', 'all'],
            help='處理的消息角色（預設: user）'
        )
        
        parser.add_argument(
            '--min-length',
            type=int,
            default=5,
            help='最小消息長度過濾（預設: 5）'
        )
        
        parser.add_argument(
            '--perform-clustering',
            action='store_true',
            help='處理完成後執行聚類分析'
        )
        
        parser.add_argument(
            '--clustering-algorithm',
            type=str,
            default='kmeans',
            choices=['kmeans', 'dbscan'],
            help='聚類算法（預設: kmeans）'
        )
        
        parser.add_argument(
            '--force-rebuild',
            action='store_true',
            help='強制重新處理已有向量的消息'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='僅顯示處理計劃，不實際執行'
        )
    
    def handle(self, *args, **options):
        """主處理流程"""
        
        # 檢查依賴
        if not self._check_dependencies():
            return
        
        self.stdout.write(
            self.style.SUCCESS('🚀 開始聊天消息向量化處理')
        )
        
        # 獲取參數
        batch_size = options['batch_size']
        user_role = options['user_role']
        min_length = options['min_length']
        perform_clustering = options['perform_clustering']
        clustering_algorithm = options['clustering_algorithm']
        force_rebuild = options['force_rebuild']
        dry_run = options['dry_run']
        
        self.stdout.write(f"📋 處理參數:")
        self.stdout.write(f"   - 批量大小: {batch_size}")
        self.stdout.write(f"   - 用戶角色: {user_role}")
        self.stdout.write(f"   - 最小長度: {min_length}")
        self.stdout.write(f"   - 執行聚類: {perform_clustering}")
        self.stdout.write(f"   - 聚類算法: {clustering_algorithm}")
        self.stdout.write(f"   - 強制重建: {force_rebuild}")
        self.stdout.write(f"   - 模擬執行: {dry_run}")
        
        try:
            # 初始化服務
            vector_service = get_chat_vector_service()
            
            # 獲取待處理的聊天消息
            messages = self._get_chat_messages(user_role, min_length, force_rebuild)
            
            if not messages:
                self.stdout.write(
                    self.style.WARNING('⚠️ 沒有找到需要處理的聊天消息')
                )
                return
            
            total_messages = len(messages)
            self.stdout.write(f"📊 找到 {total_messages} 條待處理消息")
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('🔍 模擬執行模式，不會實際處理數據')
                )
                self._show_processing_plan(messages, batch_size)
                return
            
            # 批量處理向量化
            results = self._process_vectorization(messages, vector_service, batch_size)
            
            # 顯示處理結果
            self._show_vectorization_results(results)
            
            # 執行聚類分析（如果指定）
            if perform_clustering and results['successful'] > 0:
                self.stdout.write("\n🧠 開始執行聚類分析...")
                clustering_results = self._perform_clustering_analysis(clustering_algorithm)
                self._show_clustering_results(clustering_results)
            
            # 顯示最終統計
            self._show_final_stats(vector_service)
            
            self.stdout.write(
                self.style.SUCCESS('\n✅ 聊天消息向量化處理完成!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 處理過程發生錯誤: {str(e)}')
            )
            raise CommandError(f'向量化處理失敗: {str(e)}')
    
    def _check_dependencies(self) -> bool:
        """檢查依賴是否可用"""
        if not MODELS_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('❌ ChatMessage 模型不可用')
            )
            return False
        
        if not VECTOR_SERVICES_AVAILABLE:
            self.stdout.write(
                self.style.ERROR('❌ 向量化服務不可用')
            )
            return False
        
        # 檢查資料庫表是否存在
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_name = 'chat_message_embeddings_1024'
                """)
                if cursor.fetchone()[0] == 0:
                    self.stdout.write(
                        self.style.ERROR('❌ chat_message_embeddings_1024 表不存在')
                    )
                    return False
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 資料庫檢查失敗: {str(e)}')
            )
            return False
        
        return True
    
    def _get_chat_messages(self, user_role: str, min_length: int, 
                          force_rebuild: bool) -> List[Dict]:
        """獲取待處理的聊天消息"""
        try:
            # 構建查詢條件
            role_filter = ""
            if user_role != 'all':
                role_filter = f"AND cm.role = '{user_role}'"
            
            # 如果不強制重建，排除已處理的消息
            exclude_processed = ""
            if not force_rebuild:
                exclude_processed = """
                AND NOT EXISTS (
                    SELECT 1 FROM chat_message_embeddings_1024 ce 
                    WHERE ce.chat_message_id = cm.id
                )
                """
            
            with connection.cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        cm.id,
                        cm.conversation_id,
                        cm.content,
                        cm.role,
                        LENGTH(cm.content) as content_length,
                        cm.created_at
                    FROM chat_messages cm
                    WHERE LENGTH(cm.content) >= %s
                    {role_filter}
                    {exclude_processed}
                    ORDER BY cm.created_at DESC
                """, [min_length])
                
                columns = [col[0] for col in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    message_data = dict(zip(columns, row))
                    results.append(message_data)
                
                return results
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 獲取聊天消息失敗: {str(e)}')
            )
            return []
    
    def _show_processing_plan(self, messages: List[Dict], batch_size: int):
        """顯示處理計劃"""
        total_messages = len(messages)
        total_batches = (total_messages + batch_size - 1) // batch_size
        
        self.stdout.write(f"\n📋 處理計劃:")
        self.stdout.write(f"   - 總消息數: {total_messages}")
        self.stdout.write(f"   - 批量大小: {batch_size}")
        self.stdout.write(f"   - 總批次數: {total_batches}")
        
        # 角色分布
        role_counts = {}
        for msg in messages:
            role = msg.get('role', 'unknown')
            role_counts[role] = role_counts.get(role, 0) + 1
        
        self.stdout.write(f"\n👥 角色分布:")
        for role, count in role_counts.items():
            self.stdout.write(f"   - {role}: {count}")
        
        # 長度分布
        lengths = [msg.get('content_length', 0) for msg in messages]
        if lengths:
            avg_length = sum(lengths) / len(lengths)
            min_length = min(lengths)
            max_length = max(lengths)
            
            self.stdout.write(f"\n📏 消息長度統計:")
            self.stdout.write(f"   - 平均長度: {avg_length:.1f}")
            self.stdout.write(f"   - 最短長度: {min_length}")
            self.stdout.write(f"   - 最長長度: {max_length}")
    
    def _process_vectorization(self, messages: List[Dict], 
                             vector_service, batch_size: int) -> Dict:
        """批量處理向量化"""
        total_messages = len(messages)
        processed = 0
        successful = 0
        failed = 0
        errors = []
        
        self.stdout.write(f"\n🔄 開始批量向量化處理...")
        
        # 分批處理
        for i in range(0, total_messages, batch_size):
            batch = messages[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_messages + batch_size - 1) // batch_size
            
            self.stdout.write(
                f"⚡ 處理批次 {batch_num}/{total_batches} "
                f"({len(batch)} 條消息)..."
            )
            
            # 處理當前批次
            for msg in batch:
                try:
                    success = vector_service.generate_and_store_vector(
                        chat_message_id=msg['id'],
                        content=msg['content'],
                        conversation_id=msg.get('conversation_id'),
                        user_role=msg.get('role', 'user')
                    )
                    
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        
                    processed += 1
                    
                    # 顯示進度
                    if processed % 10 == 0:
                        progress = (processed / total_messages) * 100
                        self.stdout.write(
                            f"   進度: {processed}/{total_messages} ({progress:.1f}%)"
                        )
                
                except Exception as e:
                    failed += 1
                    processed += 1
                    errors.append({
                        'message_id': msg['id'],
                        'error': str(e)
                    })
                    self.stdout.write(
                        self.style.WARNING(f"   ⚠️ 消息 {msg['id']} 處理失敗: {str(e)}")
                    )
        
        return {
            'total_processed': processed,
            'successful': successful,
            'failed': failed,
            'errors': errors
        }
    
    def _show_vectorization_results(self, results: Dict):
        """顯示向量化處理結果"""
        self.stdout.write(f"\n📊 向量化處理結果:")
        self.stdout.write(f"   - 總處理數: {results['total_processed']}")
        self.stdout.write(f"   - 成功數量: {results['successful']}")
        self.stdout.write(f"   - 失敗數量: {results['failed']}")
        
        if results['successful'] > 0:
            success_rate = (results['successful'] / results['total_processed']) * 100
            self.stdout.write(
                self.style.SUCCESS(f"   - 成功率: {success_rate:.1f}%")
            )
        
        if results['errors']:
            self.stdout.write(
                self.style.WARNING(f"   - 錯誤詳情: {len(results['errors'])} 個錯誤")
            )
    
    def _perform_clustering_analysis(self, algorithm: str) -> Dict:
        """執行聚類分析"""
        try:
            clustering_service = get_clustering_service()
            results = clustering_service.perform_clustering_analysis(algorithm)
            return results
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ 聚類分析失敗: {str(e)}')
            )
            return {'error': str(e)}
    
    def _show_clustering_results(self, results: Dict):
        """顯示聚類分析結果"""
        if 'error' in results:
            self.stdout.write(
                self.style.ERROR(f"❌ 聚類分析錯誤: {results['error']}")
            )
            return
        
        summary = results.get('analysis_summary', {})
        
        self.stdout.write(f"\n🧠 聚類分析結果:")
        self.stdout.write(f"   - 總消息數: {summary.get('total_messages', 0)}")
        self.stdout.write(f"   - 聚類數量: {summary.get('n_clusters', 0)}")
        self.stdout.write(f"   - 使用算法: {summary.get('algorithm_used', 'unknown')}")
        self.stdout.write(f"   - 生成類別: {summary.get('categories_generated', 0)}")
        
        # 顯示類別建議
        categories = results.get('category_suggestions', {})
        if categories:
            self.stdout.write(f"\n🏷️ 自動生成類別:")
            for cluster_id, cat_info in categories.items():
                category = cat_info.get('category', 'unknown')
                confidence = cat_info.get('confidence', 0)
                keywords = cat_info.get('keywords', [])
                
                self.stdout.write(
                    f"   - 聚類 {cluster_id}: {category} "
                    f"(信心度: {confidence:.2f}, 關鍵字: {', '.join(keywords[:3])})"
                )
    
    def _show_final_stats(self, vector_service):
        """顯示最終統計"""
        try:
            stats = vector_service.get_embedding_stats()
            basic_stats = stats.get('basic_stats', {})
            
            self.stdout.write(f"\n📈 最終統計:")
            self.stdout.write(f"   - 總向量數: {basic_stats.get('total_embeddings', 0)}")
            self.stdout.write(f"   - 用戶消息: {basic_stats.get('user_messages', 0)}")
            self.stdout.write(f"   - AI 消息: {basic_stats.get('assistant_messages', 0)}")
            self.stdout.write(f"   - 已分類數: {basic_stats.get('categorized_messages', 0)}")
            self.stdout.write(f"   - 已聚類數: {basic_stats.get('clustered_messages', 0)}")
            
            # 語言分布
            lang_dist = stats.get('language_distribution', {})
            if lang_dist:
                self.stdout.write(f"\n🌐 語言分布:")
                for lang, count in lang_dist.items():
                    self.stdout.write(f"   - {lang}: {count}")
            
            # 類別分布
            cat_dist = stats.get('category_distribution', {})
            if cat_dist:
                self.stdout.write(f"\n🏷️ 類別分布 (前5名):")
                sorted_categories = sorted(cat_dist.items(), key=lambda x: x[1], reverse=True)[:5]
                for category, count in sorted_categories:
                    self.stdout.write(f"   - {category}: {count}")
                    
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ 獲取最終統計失敗: {str(e)}')
            )