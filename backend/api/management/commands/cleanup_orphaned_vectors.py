#!/usr/bin/env python
"""
清理孤立向量資料管理指令

當主表資料被刪除但向量資料未被清理時，使用此指令清理孤立的向量資料
確保向量資料庫與主資料庫的一致性
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '清理孤立的向量嵌入資料（主表已刪除但向量仍存在）'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--source-table',
            type=str,
            help='指定要清理的來源表 (例如: rvt_guide, know_issue)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='只顯示將要清理的資料，不實際執行刪除',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='強制清理，不詢問確認',
        )
        parser.add_argument(
            '--table-type',
            type=str,
            choices=['768', '1024', 'both'],
            default='both',
            help='指定要清理的向量表類型',
        )
    
    def handle(self, *args, **options):
        """執行清理孤立向量資料"""
        
        self.stdout.write("🔍 開始檢查孤立的向量資料...")
        
        source_table = options.get('source_table')
        dry_run = options.get('dry_run')
        force = options.get('force')
        table_type = options.get('table_type')
        
        # 決定要處理的表格
        tables_to_check = []
        if table_type in ['768', 'both']:
            tables_to_check.append('document_embeddings')
        if table_type in ['1024', 'both']:
            tables_to_check.append('document_embeddings_1024')
        
        total_orphaned = 0
        cleanup_summary = {}
        
        for vector_table in tables_to_check:
            self.stdout.write(f"\n📊 檢查表格: {vector_table}")
            
            # 如果指定了來源表，只檢查該表
            if source_table:
                source_tables = [source_table]
            else:
                # 獲取所有來源表
                source_tables = self._get_all_source_tables(vector_table)
            
            for src_table in source_tables:
                orphaned_count = self._check_orphaned_vectors(vector_table, src_table)
                if orphaned_count > 0:
                    total_orphaned += orphaned_count
                    cleanup_summary[f"{vector_table}:{src_table}"] = orphaned_count
                    
                    self.stdout.write(
                        self.style.WARNING(f"  ⚠️  發現 {orphaned_count} 個孤立向量: {src_table}")
                    )
                    
                    if not dry_run:
                        if force or self._confirm_cleanup(src_table, orphaned_count, vector_table):
                            cleaned = self._cleanup_orphaned_vectors(vector_table, src_table)
                            self.stdout.write(
                                self.style.SUCCESS(f"  ✅ 已清理 {cleaned} 個孤立向量")
                            )
                else:
                    self.stdout.write(f"  ✅ {src_table}: 無孤立向量")
        
        # 顯示摘要
        self.stdout.write(f"\n📋 清理摘要:")
        if total_orphaned == 0:
            self.stdout.write(self.style.SUCCESS("✅ 未發現孤立向量資料"))
        else:
            if dry_run:
                self.stdout.write(self.style.WARNING(f"⚠️  發現總共 {total_orphaned} 個孤立向量"))
                self.stdout.write("使用 --dry-run=false 執行實際清理")
            else:
                self.stdout.write(self.style.SUCCESS(f"✅ 清理完成，總共處理 {total_orphaned} 個孤立向量"))
        
        # 顯示詳細摘要
        if cleanup_summary:
            self.stdout.write("\n詳細資訊:")
            for table_source, count in cleanup_summary.items():
                self.stdout.write(f"  - {table_source}: {count} 個")
    
    def _get_all_source_tables(self, vector_table):
        """獲取所有來源表"""
        with connection.cursor() as cursor:
            cursor.execute(f"""
                SELECT DISTINCT source_table 
                FROM {vector_table}
                ORDER BY source_table
            """)
            return [row[0] for row in cursor.fetchall()]
    
    def _check_orphaned_vectors(self, vector_table, source_table):
        """檢查指定來源表的孤立向量數量"""
        try:
            # 根據來源表名決定主表名
            main_table = self._get_main_table_name(source_table)
            
            with connection.cursor() as cursor:
                # 查找在向量表中存在但在主表中不存在的記錄
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM {vector_table} v
                    WHERE v.source_table = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM {main_table} m 
                        WHERE m.id = v.source_id
                    )
                """, [source_table])
                
                return cursor.fetchone()[0]
                
        except Exception as e:
            logger.error(f"檢查孤立向量失敗: {str(e)}")
            return 0
    
    def _cleanup_orphaned_vectors(self, vector_table, source_table):
        """清理孤立向量"""
        try:
            main_table = self._get_main_table_name(source_table)
            
            with connection.cursor() as cursor:
                # 刪除孤立的向量記錄
                cursor.execute(f"""
                    DELETE FROM {vector_table}
                    WHERE source_table = %s
                    AND source_id NOT IN (
                        SELECT id FROM {main_table}
                    )
                """, [source_table])
                
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"清理孤立向量失敗: {str(e)}")
            return 0
    
    def _get_main_table_name(self, source_table):
        """根據來源表名獲取實際的資料表名"""
        # 映射來源表名到實際表名
        table_mapping = {
            'rvt_guide': 'rvt_guide',
            'know_issue': 'know_issue',
            'employee': 'employee',
            'dify_employee': 'dify_employee'
        }
        
        return table_mapping.get(source_table, source_table)
    
    def _confirm_cleanup(self, source_table, count, vector_table):
        """詢問用戶確認是否清理"""
        self.stdout.write(
            f"\n⚠️  即將清理 {vector_table} 中 {source_table} 的 {count} 個孤立向量"
        )
        confirm = input("是否繼續？(y/N): ")
        return confirm.lower() in ['y', 'yes']


# 便利函數
def cleanup_orphaned_vectors_for_table(source_table: str, dry_run: bool = False) -> dict:
    """
    程式化清理指定表的孤立向量
    
    Args:
        source_table: 來源表名
        dry_run: 是否只檢查不清理
        
    Returns:
        清理結果統計
    """
    result = {
        'total_orphaned': 0,
        'cleaned': 0,
        'errors': []
    }
    
    try:
        # 檢查兩種向量表
        for table_name, use_1024 in [('document_embeddings', False), ('document_embeddings_1024', True)]:
            with connection.cursor() as cursor:
                # 檢查孤立向量
                main_table = source_table  # 假設來源表名就是主表名
                
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM {table_name} v
                    WHERE v.source_table = %s
                    AND NOT EXISTS (
                        SELECT 1 FROM {main_table} m 
                        WHERE m.id = v.source_id
                    )
                """, [source_table])
                
                orphaned_count = cursor.fetchone()[0]
                result['total_orphaned'] += orphaned_count
                
                if orphaned_count > 0 and not dry_run:
                    # 執行清理
                    cursor.execute(f"""
                        DELETE FROM {table_name}
                        WHERE source_table = %s
                        AND source_id NOT IN (
                            SELECT id FROM {main_table}
                        )
                    """, [source_table])
                    
                    cleaned = cursor.rowcount
                    result['cleaned'] += cleaned
                    
                    logger.info(f"清理完成: {table_name} 中 {source_table} 的 {cleaned} 個孤立向量")
        
        return result
        
    except Exception as e:
        result['errors'].append(str(e))
        logger.error(f"清理孤立向量失敗: {str(e)}")
        return result