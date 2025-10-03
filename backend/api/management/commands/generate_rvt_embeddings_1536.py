"""
Django 管理命令：為 RVT Guide 資料生成 1536 維向量嵌入
使用 multilingual-e5-large 模型
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import RVTGuide
from api.services.embedding_service import get_embedding_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '為 RVT Guide 資料生成 1024 維向量嵌入（使用 multilingual-e5-large 模型）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制重新生成所有向量（即使已存在）',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=5,
            help='批量處理大小（預設: 5，因為 1536 維模型比較大）',
        )
        parser.add_argument(
            '--model-type',
            type=str,
            default='ultra_high',
            help='使用的模型類型（ultra_high: 1024維 multilingual-e5-large）',
        )
    
    def handle(self, *args, **options):
        force_regenerate = options['force']
        batch_size = options['batch_size']
        model_type = options['model_type']
        
        self.stdout.write(
            self.style.HTTP_INFO(f"🚀 開始為 RVT Guide 生成 1024 維向量嵌入")
        )
        self.stdout.write(f"📊 參數配置:")
        self.stdout.write(f"   - 模型類型: {model_type}")
        self.stdout.write(f"   - 批量大小: {batch_size}")
        self.stdout.write(f"   - 強制重新生成: {force_regenerate}")
        
        try:
            # 初始化嵌入服務 - 使用 1024 維模型
            self.stdout.write("🔧 初始化 1024 維嵌入服務...")
            embedding_service = get_embedding_service(model_type)
            
            # 測試模型載入
            self.stdout.write("🧠 載入 multilingual-e5-large 模型...")
            test_embedding = embedding_service.generate_embedding("測試文本")
            self.stdout.write(
                self.style.SUCCESS(f"✅ 模型載入成功！向量維度: {len(test_embedding)}")
            )
            
            if len(test_embedding) < 1000:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  警告：實際向量維度 {len(test_embedding)} 小於預期的 1024 維")
                )
            
            # 查詢所有 RVT Guide 資料
            rvt_guides = RVTGuide.objects.all().order_by('id')
            total_count = rvt_guides.count()
            
            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING("⚠️  沒有找到 RVT Guide 資料")
                )
                return
            
            self.stdout.write(f"📚 找到 {total_count} 篇 RVT Guide 文檔")
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            # 批量處理
            for i in range(0, total_count, batch_size):
                batch = rvt_guides[i:i + batch_size]
                
                self.stdout.write(f"\n📦 處理批次 {i//batch_size + 1} ({len(batch)} 個文檔)...")
                
                for rvt_guide in batch:
                    try:
                        # 準備文檔內容
                        content = self._prepare_document_content(rvt_guide)
                        
                        # 生成並存儲向量到 1024 維表格
                        success = embedding_service.store_document_embedding(
                            source_table='rvt_guide',
                            source_id=rvt_guide.id,
                            content=content,
                            use_1024_table=True  # 使用 1024 維表格
                        )
                        
                        if success:
                            processed_count += 1
                            self.stdout.write(f"  ✅ {rvt_guide.title}")
                        else:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f"  ❌ 失敗: {rvt_guide.title}")
                            )
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ 錯誤: {rvt_guide.title} - {str(e)}")
                        )
                        logger.error(f"處理 RVT Guide {rvt_guide.id} 時發生錯誤: {str(e)}")
                
                # 顯示進度
                progress = ((i + batch_size) / total_count) * 100
                self.stdout.write(f"📈 進度: {min(progress, 100):.1f}%")
            
            # 顯示最終結果
            self.stdout.write("\n" + "="*50)
            self.stdout.write(
                self.style.SUCCESS(f"🎉 1024 維向量生成完成！")
            )
            self.stdout.write(f"📊 統計結果:")
            self.stdout.write(f"   - 總文檔數: {total_count}")
            self.stdout.write(f"   - 成功處理: {processed_count}")
            self.stdout.write(f"   - 跳過: {skipped_count}")
            self.stdout.write(f"   - 錯誤: {error_count}")
            
            if error_count > 0:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  有 {error_count} 個文檔處理失敗，請檢查日誌")
                )
            
            # 測試 1024 維向量搜索
            self.stdout.write("\n🔍 測試 1024 維向量搜索...")
            test_results = embedding_service.search_similar_documents(
                query="Jenkins 測試階段",
                source_table='rvt_guide',
                limit=3,
                use_1024_table=True
            )
            
            if test_results:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ 1024 維搜索測試成功！找到 {len(test_results)} 個結果")
                )
                for i, result in enumerate(test_results, 1):
                    self.stdout.write(f"   {i}. 相似度: {result['similarity_score']:.3f}")
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  1024 維搜索測試沒有找到結果")
                )
            
            # 建立向量搜索索引
            self.stdout.write("\n🏗️  建立 1024 維向量搜索索引...")
            try:
                from django.db import connection
                with connection.cursor() as cursor:
                    # 先檢查是否有足夠的資料建立索引
                    cursor.execute("SELECT COUNT(*) FROM document_embeddings_1024 WHERE embedding IS NOT NULL")
                    count = cursor.fetchone()[0]
                    
                    if count >= 5:  # 需要至少 5 筆資料才建立索引
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS idx_document_embeddings_1024_vector 
                            ON document_embeddings_1024 USING ivfflat (embedding vector_cosine_ops)
                        """)
                        self.stdout.write(
                            self.style.SUCCESS("✅ 1024 維向量索引建立成功")
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️  資料量不足 ({count} < 5)，跳過索引建立")
                        )
                        
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f"⚠️  索引建立失敗: {str(e)}")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 1024 維向量生成過程中發生嚴重錯誤: {str(e)}")
            )
            logger.error(f"1024 維向量生成命令執行錯誤: {str(e)}")
            raise
    
    def _prepare_document_content(self, rvt_guide):
        """準備用於向量化的文檔內容"""
        content_parts = []
        
        # 添加標題
        content_parts.append(f"標題: {rvt_guide.title}")
        
        # 添加主要內容
        content_parts.append(f"內容: {rvt_guide.content}")
        
        return "\n".join(content_parts)