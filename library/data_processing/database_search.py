"""
資料庫搜索服務模組
提供各種知識庫的 PostgreSQL 全文搜索功能
"""
import logging
from django.db import connection
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class DatabaseSearchService:
    """
    資料庫搜索服務類
    提供統一的搜索介面用於各種知識庫
    """
    
    @staticmethod
    def search_know_issue_knowledge(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        在 PostgreSQL 中搜索 Know Issue 知識庫
        
        Args:
            query_text: 搜索關鍵字
            limit: 返回結果數量限制
            
        Returns:
            搜索結果列表，每個結果包含 id, title, content, score, metadata
        """
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT 
                    ki.id,
                    ki.issue_id,
                    ki.test_version,
                    ki.jira_number,
                    ki.project,
                    ki.test_class_id,
                    tc.name as test_class_name,
                    ki.script,
                    ki.issue_type,
                    ki.status,
                    ki.error_message,
                    ki.supplement,
                    ki.created_at,
                    ki.updated_at,
                    ki.updated_by_id,
                    u.username as updated_by_name,
                    u.first_name as updated_by_first_name,
                    u.last_name as updated_by_last_name,
                    CASE 
                        WHEN ki.issue_id ILIKE %s THEN 1.0
                        WHEN ki.project ILIKE %s THEN 0.9
                        WHEN tc.name ILIKE %s THEN 0.8
                        WHEN u.username ILIKE %s THEN 0.8
                        WHEN u.first_name ILIKE %s THEN 0.8
                        WHEN u.last_name ILIKE %s THEN 0.8
                        WHEN ki.error_message ILIKE %s THEN 0.7
                        WHEN ki.supplement ILIKE %s THEN 0.6
                        WHEN ki.script ILIKE %s THEN 0.5
                        ELSE 0.3
                    END as score
                FROM know_issue ki
                LEFT JOIN protocol_test_class tc ON ki.test_class_id = tc.id
                LEFT JOIN auth_user u ON ki.updated_by_id = u.id
                WHERE 
                    ki.issue_id ILIKE %s OR 
                    ki.project ILIKE %s OR 
                    tc.name ILIKE %s OR 
                    u.username ILIKE %s OR 
                    u.first_name ILIKE %s OR 
                    u.last_name ILIKE %s OR 
                    ki.error_message ILIKE %s OR 
                    ki.supplement ILIKE %s OR 
                    ki.script ILIKE %s
                ORDER BY score DESC, ki.created_at DESC
                LIMIT %s
                """
                
                search_pattern = f'%{query_text}%'
                cursor.execute(sql, [
                    search_pattern, search_pattern, search_pattern, 
                    search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern, search_pattern,
                    limit
                ])
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                results = []
                for row in rows:
                    issue_data = dict(zip(columns, row))
                    
                    # 格式化為知識片段
                    content = f"問題編號: {issue_data['issue_id']}\n"
                    content += f"專案: {issue_data['project']}\n"
                    content += f"測試版本: {issue_data['test_version']}\n"
                    if issue_data['test_class_name']:
                        content += f"測試類別: {issue_data['test_class_name']}\n"
                    if issue_data['jira_number']:
                        content += f"JIRA編號: {issue_data['jira_number']}\n"
                    content += f"問題類型: {issue_data['issue_type']}\n"
                    content += f"狀態: {issue_data['status']}\n"
                    if issue_data['error_message']:
                        content += f"錯誤訊息: {issue_data['error_message']}\n"
                    if issue_data['supplement']:
                        content += f"補充說明: {issue_data['supplement']}\n"
                    if issue_data['script']:
                        content += f"相關腳本: {issue_data['script']}\n"
                    
                    # 添加更改人員資訊
                    if issue_data['updated_by_name']:
                        updated_by_display = issue_data['updated_by_name']
                        if issue_data['updated_by_first_name'] or issue_data['updated_by_last_name']:
                            full_name = f"{issue_data['updated_by_first_name'] or ''} {issue_data['updated_by_last_name'] or ''}".strip()
                            if full_name:
                                updated_by_display = f"{full_name} ({issue_data['updated_by_name']})"
                        content += f"更新人員: {updated_by_display}\n"
                    
                    content += f"建立時間: {issue_data['created_at']}\n"
                    content += f"更新時間: {issue_data['updated_at']}"
                    
                    results.append({
                        'id': str(issue_data['id']),
                        'title': f"{issue_data['issue_id']} - {issue_data['project']}",
                        'content': content,
                        'score': float(issue_data['score']),
                        'metadata': {
                            'source': 'know_issue_database',
                            'issue_id': issue_data['issue_id'],
                            'project': issue_data['project'],
                            'test_version': issue_data['test_version'],
                            'issue_type': issue_data['issue_type'],
                            'status': issue_data['status'],
                            'updated_by_id': issue_data['updated_by_id'],
                            'updated_by_name': issue_data['updated_by_name'],
                            'updated_at': str(issue_data['updated_at']) if issue_data['updated_at'] else None
                        }
                    })
                
                logger.info(f"Know Issue search found {len(results)} results for query: '{query_text}'")
                return results
                
        except Exception as e:
            logger.error(f"Know Issue database search error: {str(e)}")
            return []
    
    @staticmethod
    def search_rvt_guide_knowledge(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        在 PostgreSQL 中搜索 RVT Guide 知識庫
        
        Args:
            query_text: 搜索關鍵字
            limit: 返回結果數量限制
            
        Returns:
            搜索結果列表，每個結果包含 id, title, content, score, metadata
        """
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT 
                    id,
                    title,
                    content,
                    created_at,
                    updated_at,
                    CASE 
                        WHEN title ILIKE %s THEN 1.0
                        WHEN content ILIKE %s THEN 0.8
                        ELSE 0.5
                    END as score
                FROM rvt_guide
                WHERE 
                    title ILIKE %s OR 
                    content ILIKE %s
                ORDER BY score DESC, created_at DESC
                LIMIT %s
                """
                
                search_pattern = f'%{query_text}%'
                cursor.execute(sql, [
                    search_pattern, search_pattern,
                    search_pattern, search_pattern,
                    limit
                ])
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                results = []
                for row in rows:
                    guide_data = dict(zip(columns, row))
                    
                    # 格式化為知識片段
                    content = f"# {guide_data['title']}\n\n"
                    content += f"**內容**:\n{guide_data['content']}"
                    
                    results.append({
                        'id': str(guide_data['id']),
                        'title': guide_data['title'],
                        'content': content,
                        'score': float(guide_data['score']),
                        'metadata': {
                            'source': 'rvt_guide_database',
                            'created_at': str(guide_data['created_at']) if guide_data['created_at'] else None,
                            'updated_at': str(guide_data['updated_at']) if guide_data['updated_at'] else None
                        }
                    })
                
                logger.info(f"RVT Guide search found {len(results)} results for query: '{query_text}'")
                return results
                
        except Exception as e:
            logger.error(f"RVT Guide database search error: {str(e)}")
            return []
    
    @staticmethod
    def search_ocr_storage_benchmark(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        PostgreSQL 全文搜索 OCR 存儲基準測試資料
        
        Args:
            query_text: 搜索關鍵字
            limit: 返回結果數量限制
            
        Returns:
            搜索結果列表，每個結果包含 id, title, content, score, metadata
        """
        try:
            with connection.cursor() as cursor:
                sql = """
                SELECT 
                    id, benchmark_score, average_bandwidth, test_datetime,
                    project_name, device_model, firmware_version, benchmark_version,
                    ocr_confidence, created_at, updated_at,
                    CASE 
                        WHEN device_model ILIKE %s THEN 0.9
                        WHEN CAST(benchmark_score AS TEXT) ILIKE %s THEN 0.8
                        WHEN average_bandwidth ILIKE %s THEN 0.7
                        WHEN project_name ILIKE %s THEN 0.6
                        ELSE 0.5
                    END as score
                FROM ocr_storage_benchmark
                WHERE 
                    device_model ILIKE %s OR
                    CAST(benchmark_score AS TEXT) ILIKE %s OR
                    average_bandwidth ILIKE %s OR
                    project_name ILIKE %s OR
                    firmware_version ILIKE %s OR
                    benchmark_version ILIKE %s
                ORDER BY score DESC, benchmark_score DESC, created_at DESC
                LIMIT %s
                """
                
                search_pattern = f'%{query_text}%'
                cursor.execute(sql, [
                    search_pattern, search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern, search_pattern, search_pattern,
                    search_pattern, search_pattern,
                    limit
                ])
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                results = []
                for row in rows:
                    benchmark_data = dict(zip(columns, row))
                    
                    # 格式化為知識片段
                    content = f"# 存儲基準測試報告: {benchmark_data['project_name'] or '未命名'}\n\n"
                    content += f"**基準分數**: {benchmark_data['benchmark_score'] or 'N/A'}\n"
                    content += f"**平均帶寬**: {benchmark_data['average_bandwidth'] or 'N/A'}\n"
                    content += f"**測試時間**: {benchmark_data['test_datetime'] or 'N/A'}\n"
                    content += f"**裝置型號**: {benchmark_data['device_model'] or 'N/A'}\n"
                    content += f"**固件版本**: {benchmark_data['firmware_version'] or 'N/A'}\n"
                    content += f"**基準軟體版本**: {benchmark_data['benchmark_version'] or 'N/A'}\n"
                    content += f"**專案名稱**: {benchmark_data['project_name'] or 'N/A'}\n"
                    content += f"**OCR 信心度**: {benchmark_data['ocr_confidence'] or 'N/A'}\n"
                    
                    results.append({
                        'id': str(benchmark_data['id']),
                        'title': f"存儲基準測試: {benchmark_data['project_name'] or '未命名'} (分數: {benchmark_data['benchmark_score'] or 'N/A'})",
                        'content': content,
                        'score': float(benchmark_data['score']),
                        'metadata': {
                            'source': 'ocr_storage_benchmark',
                            'benchmark_score': benchmark_data['benchmark_score'],
                            'average_bandwidth': benchmark_data['average_bandwidth'],
                            'test_datetime': str(benchmark_data['test_datetime']) if benchmark_data['test_datetime'] else None,
                            'device_model': benchmark_data['device_model'],
                            'firmware_version': benchmark_data['firmware_version'],
                            'benchmark_version': benchmark_data['benchmark_version'],
                            'project_name': benchmark_data['project_name'],
                            'ocr_confidence': benchmark_data['ocr_confidence'],
                            'created_at': str(benchmark_data['created_at']) if benchmark_data['created_at'] else None,
                            'updated_at': str(benchmark_data['updated_at']) if benchmark_data['updated_at'] else None
                        }
                    })
                
                logger.info(f"OCR Storage Benchmark search found {len(results)} results for query: '{query_text}'")
                return results
                
        except Exception as e:
            logger.error(f"OCR Storage Benchmark database search error: {str(e)}")
            return []
    
    @classmethod
    def search_all_knowledge_bases(cls, query_text: str, limit_per_type: int = 3) -> Dict[str, List[Dict[str, Any]]]:
        """
        同時搜索所有知識庫
        
        Args:
            query_text: 搜索關鍵字
            limit_per_type: 每種知識庫的結果限制
            
        Returns:
            包含所有搜索結果的字典，按知識庫類型分組
        """
        results = {
            'know_issues': cls.search_know_issue_knowledge(query_text, limit_per_type),
            'rvt_guides': cls.search_rvt_guide_knowledge(query_text, limit_per_type),
            'ocr_benchmarks': cls.search_ocr_storage_benchmark(query_text, limit_per_type)
        }
        
        # 統計總結果數
        total_results = sum(len(results[key]) for key in results)
        logger.info(f"All knowledge bases search found {total_results} total results for query: '{query_text}'")
        
        return results


# 向後相容的函數別名，讓現有代碼可以繼續使用
def search_know_issue_knowledge(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """向後相容的函數別名"""
    return DatabaseSearchService.search_know_issue_knowledge(query_text, limit)


def search_rvt_guide_knowledge(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """向後相容的函數別名"""
    return DatabaseSearchService.search_rvt_guide_knowledge(query_text, limit)


def search_ocr_storage_benchmark(query_text: str, limit: int = 5) -> List[Dict[str, Any]]:
    """向後相容的函數別名"""
    return DatabaseSearchService.search_ocr_storage_benchmark(query_text, limit)