"""
Django 管理命令：為 Protocol Guide 資料生成向量嵌入
使用開源 Sentence Transformers 模型
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import ProtocolGuide
from api.services.embedding_service import get_embedding_service
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '為 Protocol Guide 資料生成向量嵌入（預設使用 1024 維模型）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制重新生成所有向量（即使已存在）',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='批量處理大小（預設: 10）',
        )
        parser.add_argument(
            '--model-type',
            type=str,
            default='ultra_high',
            help='模型類型 (ultra_high: 1024維, standard: 768維)',
        )
    
    def handle(self, *args, **options):
        force_regenerate = options['force']
        batch_size = options['batch_size']
        model_type = options['model_type']
        
        self.stdout.write(
            self.style.HTTP_INFO(f"🚀 開始為 Protocol Guide 生成向量嵌入")
        )
        self.stdout.write(f"📊 參數配置:")
        self.stdout.write(f"   - 模型類型: {model_type}")
        self.stdout.write(f"   - 批量大小: {batch_size}")
        self.stdout.write(f"   - 強制重新生成: {force_regenerate}")
        
        try:
            # 初始化嵌入服務
            self.stdout.write("🔧 初始化嵌入服務...")
            embedding_service = get_embedding_service(model_type)
            
            # 測試模型載入
            self.stdout.write("🧠 載入 Sentence Transformers 模型...")
            test_embedding = embedding_service.generate_embedding("測試文本")
            self.stdout.write(
                self.style.SUCCESS(f"✅ 模型載入成功！向量維度: {len(test_embedding)}")
            )
            
            # 查詢 Protocol Guide 資料
            protocol_guides = ProtocolGuide.objects.all().order_by('id')
            total_count = protocol_guides.count()
            
            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING("⚠️  沒有找到 Protocol Guide 資料")
                )
                return
            
            self.stdout.write(f"📚 找到 {total_count} 篇 Protocol Guide 文檔")
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            # 批量處理
            for i in range(0, total_count, batch_size):
                batch = protocol_guides[i:i + batch_size]
                
                self.stdout.write(f"\n📦 處理批次 {i//batch_size + 1} ({len(batch)} 個文檔)...")
                
                for protocol_guide in batch:
                    try:
                        # 準備文檔內容
                        content = self._prepare_document_content(protocol_guide)
                        
                        # 生成並存儲向量（使用 1024 維表格）
                        use_1024_table = model_type == 'ultra_high'
                        success = embedding_service.store_document_embedding(
                            source_table='protocol_guide',
                            source_id=protocol_guide.id,
                            content=content,
                            use_1024_table=use_1024_table
                        )
                        
                        if success:
                            processed_count += 1
                            self.stdout.write(f"  ✅ {protocol_guide.title}")
                        else:
                            error_count += 1
                            self.stdout.write(
                                self.style.ERROR(f"  ❌ 失敗: {protocol_guide.title}")
                            )
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(
                            self.style.ERROR(f"  ❌ 錯誤: {protocol_guide.title} - {str(e)}")
                        )
                        logger.error(f"處理 Protocol Guide {protocol_guide.id} 時發生錯誤: {str(e)}")
                
                # 顯示進度
                progress = ((i + batch_size) / total_count) * 100
                self.stdout.write(f"📈 進度: {min(progress, 100):.1f}%")
            
            # 顯示最終結果
            self.stdout.write("\n" + "="*50)
            self.stdout.write(
                self.style.SUCCESS(f"🎉 向量生成完成！")
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
            
            # 測試向量搜索
            self.stdout.write("\n🔍 測試向量搜索...")
            test_results = embedding_service.search_similar_documents(
                query="ULINK 連接測試",
                source_table='protocol_guide',
                limit=3
            )
            
            if test_results:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ 搜索測試成功！找到 {len(test_results)} 個結果")
                )
                for i, result in enumerate(test_results, 1):
                    self.stdout.write(f"   {i}. 相似度: {result['similarity_score']:.3f}")
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️  搜索測試沒有找到結果")
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ 向量生成過程中發生嚴重錯誤: {str(e)}")
            )
            logger.error(f"向量生成命令執行錯誤: {str(e)}")
            raise
    
    def _prepare_document_content(self, protocol_guide):
        """準備用於向量化的文檔內容"""
        content_parts = []
        
        # 添加標題
        content_parts.append(f"標題: {protocol_guide.title}")
        
        # 添加主要內容
        content_parts.append(f"內容: {protocol_guide.content}")
        
        return "\n".join(content_parts)
