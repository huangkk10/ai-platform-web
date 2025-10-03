#!/usr/bin/env python3
"""
Django 管理指令：為 Know Issue 資料生成 1024 維向量嵌入
使用 multilingual-e5-large 模型
"""

import sys
import time
import logging
from django.core.management.base import BaseCommand
from django.db import transaction
from api.models import KnowIssue

# 配置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '為 Know Issue 資料生成 1024 維向量嵌入（使用 multilingual-e5-large 模型）'
    
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
            help='批量處理大小（預設: 5，因為 1024 維模型比較大）',
        )
        parser.add_argument(
            '--model-type',
            type=str,
            default='ultra_high',
            help='使用的模型類型（ultra_high: 1024維 multilingual-e5-large）',
        )
    
    def handle(self, *args, **options):
        try:
            # 從配置文件載入設定
            try:
                import yaml
                import os
                config_path = '/app/config/settings.yaml'
                
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = yaml.safe_load(f)
                    self.stdout.write("✅ 配置載入成功: /app/config/settings.yaml")
                else:
                    config = {}
                    self.stdout.write("⚠️  配置文件不存在，使用預設設定")
            except Exception as config_error:
                config = {}
                self.stdout.write(f"⚠️  配置載入失敗: {config_error}")
            
            force_regenerate = options['force']
            batch_size = options['batch_size']
            model_type = options['model_type']
            
            self.stdout.write("🚀 開始為 Know Issue 生成 1024 維向量嵌入")
            self.stdout.write("📊 參數配置:")
            self.stdout.write(f"   - 模型類型: {model_type}")
            self.stdout.write(f"   - 批量大小: {batch_size}")
            self.stdout.write(f"   - 強制重新生成: {force_regenerate}")
            
            # 初始化嵌入服務
            try:
                from api.services.embedding_service import get_embedding_service
                
                self.stdout.write("🔧 初始化 1024 維嵌入服務...")
                self.stdout.write("🧠 載入 multilingual-e5-large 模型...")
                
                embedding_service = get_embedding_service()
                
                # 測試向量生成
                test_text = "測試文本"
                test_embedding = embedding_service.generate_embedding(test_text)
                
                if len(test_embedding) < 1000:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️  警告：實際向量維度 {len(test_embedding)} 小於預期的 1024 維")
                    )
                
                self.stdout.write(f"✅ 模型載入成功！向量維度: {len(test_embedding)}")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ 嵌入服務初始化失敗: {str(e)}")
                )
                logger.error(f"1024 維向量生成命令執行錯誤: {str(e)}")
                return
            
            # 查詢所有 Know Issue 資料
            know_issues = KnowIssue.objects.all().order_by('id')
            total_count = know_issues.count()
            
            if total_count == 0:
                self.stdout.write(
                    self.style.WARNING("⚠️  沒有找到 Know Issue 資料")
                )
                return
            
            self.stdout.write(f"📚 找到 {total_count} 筆 Know Issue 資料")
            
            processed_count = 0
            skipped_count = 0
            error_count = 0
            
            # 批量處理
            for i in range(0, total_count, batch_size):
                batch = know_issues[i:i + batch_size]
                batch_num = i // batch_size + 1
                self.stdout.write(f"\n📦 處理批次 {batch_num} ({len(batch)} 個文檔)...")
                
                for know_issue in batch:
                    try:
                        # 檢查是否已存在向量（除非強制重新生成）
                        if not force_regenerate:
                            from django.db import connection
                            with connection.cursor() as cursor:
                                cursor.execute(
                                    "SELECT COUNT(*) FROM document_embeddings_1024 WHERE source_table = %s AND source_id = %s",
                                    ['know_issue', know_issue.id]
                                )
                                existing_count = cursor.fetchone()[0]
                                if existing_count > 0:
                                    skipped_count += 1
                                    self.stdout.write(f"  ⏭️  跳過 (已存在): {know_issue.issue_id}")
                                    continue
                        
                        # 生成內容用於嵌入
                        content = self._format_know_issue_content(know_issue)
                        
                        # 生成並儲存向量
                        success = embedding_service.store_document_embedding(
                            source_table='know_issue',
                            source_id=know_issue.id,
                            content=content,
                            use_1024_table=True
                        )
                        
                        if success:
                            processed_count += 1
                            self.stdout.write(f"  ✅ {know_issue.issue_id}")
                        else:
                            error_count += 1
                            self.stdout.write(f"  ❌ 失敗: {know_issue.issue_id}")
                            
                    except Exception as e:
                        error_count += 1
                        self.stdout.write(f"  ❌ 錯誤: {know_issue.issue_id} - {str(e)}")
                        logger.error(f"處理 Know Issue {know_issue.id} 時發生錯誤: {str(e)}")
                
                # 顯示進度
                progress = min(100.0, ((i + batch_size) / total_count) * 100)
                self.stdout.write(f"📈 進度: {progress:.1f}%")
            
            # 輸出統計結果
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write("🎉 1024 維向量生成完成！")
            self.stdout.write("📊 統計結果:")
            self.stdout.write(f"   - 總文檔數: {total_count}")
            self.stdout.write(f"   - 成功處理: {processed_count}")
            self.stdout.write(f"   - 跳過: {skipped_count}")
            self.stdout.write(f"   - 錯誤: {error_count}")
            
            # 測試向量搜索
            if processed_count > 0:
                self.stdout.write("\n🔍 測試 1024 維向量搜索...")
                try:
                    search_results = embedding_service.search_similar_documents(
                        query="Samsung",
                        source_table='know_issue',
                        limit=3,
                        use_1024_table=True
                    )
                    
                    if search_results:
                        self.stdout.write(f"✅ 1024 維搜索測試成功！找到 {len(search_results)} 個結果")
                        for i, result in enumerate(search_results, 1):
                            self.stdout.write(f"   {i}. 相似度: {result['similarity_score']:.3f}")
                    else:
                        self.stdout.write("⚠️  搜索測試無結果")
                        
                except Exception as e:
                    self.stdout.write(f"❌ 搜索測試失敗: {str(e)}")
            
            # 建立向量索引（如果支援）
            try:
                self.stdout.write("\n🏗️  建立 1024 維向量搜索索引...")
                from django.db import connection
                
                with connection.cursor() as cursor:
                    # 檢查索引是否存在
                    cursor.execute("""
                        SELECT indexname FROM pg_indexes 
                        WHERE tablename = 'document_embeddings_1024' 
                        AND indexname = 'idx_document_embeddings_1024_vector'
                    """)
                    
                    if not cursor.fetchone():
                        # 創建 IVFFlat 索引以加速向量搜索
                        cursor.execute("""
                            CREATE INDEX IF NOT EXISTS idx_document_embeddings_1024_vector 
                            ON document_embeddings_1024 
                            USING ivfflat (embedding vector_cosine_ops)
                            WITH (lists = 100)
                        """)
                        self.stdout.write("✅ 1024 維向量索引建立成功")
                    else:
                        self.stdout.write("✅ 1024 維向量索引已存在")
                        
            except Exception as e:
                self.stdout.write(f"⚠️  向量索引建立失敗: {str(e)}")
            
        except Exception as e:
            error_message = f"1024 維向量生成過程中發生嚴重錯誤: {str(e)}"
            self.stdout.write(self.style.ERROR(f"❌ {error_message}"))
            logger.error(f"1024 維向量生成命令執行錯誤: {str(e)}")
            raise
    
    def _format_know_issue_content(self, know_issue):
        """格式化 Know Issue 內容用於向量嵌入"""
        content_parts = []
        
        # 基本資訊
        content_parts.append(f"Issue ID: {know_issue.issue_id}")
        content_parts.append(f"專案: {know_issue.project}")
        content_parts.append(f"問題類型: {know_issue.issue_type}")
        content_parts.append(f"狀態: {know_issue.status}")
        
        # 錯誤訊息
        content_parts.append(f"錯誤訊息: {know_issue.error_message}")
        
        # 補充說明
        if know_issue.supplement:
            content_parts.append(f"補充說明: {know_issue.supplement}")
        
        # 相關腳本
        if know_issue.script:
            content_parts.append(f"相關腳本: {know_issue.script}")
        
        return "\n".join(content_parts)