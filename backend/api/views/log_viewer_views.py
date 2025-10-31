"""
系統日誌查看 API Views
提供系統日誌檔案的查看、下載、搜尋和統計功能

API 端點：
- list_log_files: 列出所有日誌檔案
- view_log_file: 查看日誌內容
- download_log_file: 下載日誌檔案
- search_log_file: 搜尋日誌內容
- log_file_stats: 日誌統計資訊

權限要求：IsAdminUser 或 is_super_admin
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status
from django.http import FileResponse, HttpResponse
from django.utils import timezone
import json

logger = logging.getLogger(__name__)


# 檢查日誌管理 Library
try:
    from library.system_monitoring import (
        LogFileReader,
        LogLineParser,
        LOG_MANAGEMENT_AVAILABLE
    )
    logger.info("✅ 日誌管理 Library 載入成功")
except ImportError as e:
    logger.warning(f"⚠️  日誌管理 Library 無法載入: {str(e)}")
    LOG_MANAGEMENT_AVAILABLE = False
    LogFileReader = None
    LogLineParser = None


# 自訂權限類別：管理員或超級管理員
class IsAdminOrSuperAdmin(permissions.BasePermission):
    """只有管理員或超級管理員可以訪問日誌"""
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_staff or 
             getattr(request.user.userprofile, 'is_super_admin', False))
        )


# ============= API 端點 1: 列出所有日誌檔案 =============

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def list_log_files(request):
    """
    列出所有可用的日誌檔案
    
    GET /api/system/logs/list/
    
    Response:
    {
        "success": true,
        "log_files": [...],
        "total_files": 8
    }
    """
    try:
        if not LOG_MANAGEMENT_AVAILABLE:
            return Response({
                'success': False,
                'error': '日誌管理功能不可用'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 使用 Library 類別方法列出日誌檔案
        log_files = LogFileReader.list_log_files()
        
        logger.info(f"用戶 {request.user.username} 列出日誌檔案，共 {len(log_files)} 個")
        
        return Response({
            'success': True,
            'log_files': log_files,
            'total_files': len(log_files),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"列出日誌檔案失敗: {str(e)}")
        return Response({
            'success': False,
            'error': f'列出日誌檔案失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= API 端點 2: 查看日誌內容 =============

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def view_log_file(request):
    """
    查看日誌檔案內容
    
    GET /api/system/logs/view/?file=django.log&lines=100&level=ERROR&search=keyword
    
    Query Parameters:
    - file: 日誌檔案名稱（必填）
    - lines: 顯示行數（預設 100）
    - tail: 從尾部讀取（預設 true）
    - level: 過濾日誌等級（可選）
    - search: 搜尋關鍵字（可選）
    - start_date: 開始日期（可選，格式 YYYY-MM-DD）
    - end_date: 結束日期（可選，格式 YYYY-MM-DD）
    
    Response:
    {
        "success": true,
        "file_name": "django.log",
        "total_lines": 513,
        "showing_lines": 100,
        "content": [...],
        "filters_applied": {...},
        "file_stats": {...}
    }
    """
    try:
        if not LOG_MANAGEMENT_AVAILABLE:
            return Response({
                'success': False,
                'error': '日誌管理功能不可用'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 獲取參數
        filename = request.query_params.get('file')
        lines = int(request.query_params.get('lines', 100))
        from_tail = request.query_params.get('tail', 'true').lower() == 'true'
        level_filter = request.query_params.get('level')
        search_keyword = request.query_params.get('search')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # 驗證必要參數
        if not filename:
            return Response({
                'success': False,
                'error': '缺少必要參數: file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 讀取日誌內容
        if from_tail:
            raw_lines = LogFileReader.read_tail(filename, lines)
        else:
            raw_lines = LogFileReader.read_all(filename, max_lines=lines)
        
        # 解析日誌行
        parsed_logs = LogLineParser.parse_lines(raw_lines)
        
        # 應用過濾器
        filtered_logs = parsed_logs
        filters_applied = {}
        
        # 等級過濾
        if level_filter:
            filtered_logs = LogLineParser.filter_by_level(filtered_logs, level_filter)
            filters_applied['level'] = level_filter
        
        # 關鍵字過濾
        if search_keyword:
            filtered_logs = LogLineParser.filter_by_keyword(filtered_logs, search_keyword)
            filters_applied['search'] = search_keyword
        
        # 日期範圍過濾
        if start_date and end_date:
            filtered_logs = LogLineParser.filter_by_date_range(
                filtered_logs, start_date, end_date
            )
            filters_applied['date_range'] = f"{start_date} ~ {end_date}"
        
        # 獲取檔案統計
        file_stats = LogFileReader.get_file_stats(filename)
        
        logger.info(
            f"用戶 {request.user.username} 查看日誌 {filename}，"
            f"顯示 {len(filtered_logs)}/{len(parsed_logs)} 行"
        )
        
        return Response({
            'success': True,
            'file_name': filename,
            'total_lines': file_stats['line_count'],
            'showing_lines': len(filtered_logs),
            'from_tail': from_tail,
            'content': filtered_logs,
            'filters_applied': filters_applied,
            'file_stats': file_stats,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        logger.warning(f"無效的日誌檔案請求: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except FileNotFoundError as e:
        logger.warning(f"日誌檔案不存在: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"查看日誌失敗: {str(e)}")
        return Response({
            'success': False,
            'error': f'查看日誌失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= API 端點 3: 下載日誌檔案 =============

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def download_log_file(request):
    """
    下載日誌檔案
    
    GET /api/system/logs/download/?file=django.log&format=txt
    
    Query Parameters:
    - file: 日誌檔案名稱（必填）
    - format: 檔案格式（txt 或 json，預設 txt）
    
    Response: 檔案串流
    """
    try:
        if not LOG_MANAGEMENT_AVAILABLE:
            return Response({
                'success': False,
                'error': '日誌管理功能不可用'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 獲取參數
        filename = request.query_params.get('file')
        file_format = request.query_params.get('format', 'txt')
        
        # 驗證參數
        if not filename:
            return Response({
                'success': False,
                'error': '缺少必要參數: file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 獲取檔案路徑
        filepath = LogFileReader._validate_and_get_path(filename)
        
        logger.info(f"用戶 {request.user.username} 下載日誌 {filename}")
        
        # 根據格式返回檔案
        if file_format == 'json':
            # JSON 格式：解析後返回
            raw_lines = LogFileReader.read_all(filename)
            parsed_logs = LogLineParser.parse_lines(raw_lines)
            
            response = HttpResponse(
                json.dumps(parsed_logs, ensure_ascii=False, indent=2),
                content_type='application/json'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}.json"'
        else:
            # TXT 格式：直接返回原始檔案
            response = FileResponse(
                open(filepath, 'rb'),
                content_type='text/plain'
            )
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except FileNotFoundError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"下載日誌失敗: {str(e)}")
        return Response({
            'success': False,
            'error': f'下載日誌失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= API 端點 4: 搜尋日誌 =============

@api_view(['POST'])
@permission_classes([IsAdminOrSuperAdmin])
def search_log_file(request):
    """
    搜尋日誌內容
    
    POST /api/system/logs/search/
    
    Body:
    {
        "file": "django.log",
        "search": "ERROR",
        "case_sensitive": false,
        "max_results": 50
    }
    
    Response:
    {
        "success": true,
        "file_name": "django.log",
        "search_query": "ERROR",
        "total_matches": 15,
        "results": [...]
    }
    """
    try:
        if not LOG_MANAGEMENT_AVAILABLE:
            return Response({
                'success': False,
                'error': '日誌管理功能不可用'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 獲取參數
        filename = request.data.get('file')
        search_query = request.data.get('search')
        case_sensitive = request.data.get('case_sensitive', False)
        max_results = request.data.get('max_results', 50)
        
        # 驗證參數
        if not filename or not search_query:
            return Response({
                'success': False,
                'error': '缺少必要參數: file 和 search'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 讀取並解析日誌
        raw_lines = LogFileReader.read_all(filename)
        parsed_logs = LogLineParser.parse_lines(raw_lines)
        
        # 搜尋
        matched_logs = LogLineParser.filter_by_keyword(parsed_logs, search_query)
        
        # 限制結果數量
        if len(matched_logs) > max_results:
            matched_logs = matched_logs[:max_results]
        
        logger.info(
            f"用戶 {request.user.username} 搜尋日誌 {filename}，"
            f"關鍵字 '{search_query}'，找到 {len(matched_logs)} 筆"
        )
        
        return Response({
            'success': True,
            'file_name': filename,
            'search_query': search_query,
            'total_matches': len(matched_logs),
            'showing_results': len(matched_logs),
            'results': matched_logs,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except FileNotFoundError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"搜尋日誌失敗: {str(e)}")
        return Response({
            'success': False,
            'error': f'搜尋日誌失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= API 端點 5: 日誌統計 =============

@api_view(['GET'])
@permission_classes([IsAdminOrSuperAdmin])
def log_file_stats(request):
    """
    獲取日誌統計資訊
    
    GET /api/system/logs/stats/?file=django.log&days=7
    
    Query Parameters:
    - file: 日誌檔案名稱（必填）
    - days: 統計最近 N 天（可選，預設 7）
    
    Response:
    {
        "success": true,
        "file_name": "django.log",
        "stats": {
            "total_lines": 513,
            "level_distribution": {...},
            "file_info": {...}
        }
    }
    """
    try:
        if not LOG_MANAGEMENT_AVAILABLE:
            return Response({
                'success': False,
                'error': '日誌管理功能不可用'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        # 獲取參數
        filename = request.query_params.get('file')
        
        # 驗證參數
        if not filename:
            return Response({
                'success': False,
                'error': '缺少必要參數: file'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 獲取檔案統計
        file_stats = LogFileReader.get_file_stats(filename)
        
        # 讀取並解析日誌以獲取等級分佈
        raw_lines = LogFileReader.read_tail(filename, lines=500)  # 分析最近 500 行
        parsed_logs = LogLineParser.parse_lines(raw_lines)
        level_stats = LogLineParser.get_level_statistics(parsed_logs)
        
        # 計算錯誤率
        total_logs = sum(level_stats.values())
        error_count = level_stats.get('ERROR', 0) + level_stats.get('CRITICAL', 0)
        error_percentage = (error_count / total_logs * 100) if total_logs > 0 else 0
        
        logger.info(f"用戶 {request.user.username} 查詢日誌統計 {filename}")
        
        return Response({
            'success': True,
            'file_name': filename,
            'stats': {
                'total_lines': file_stats['line_count'],
                'file_size': file_stats['size_human'],
                'last_modified': file_stats['modified_time'],
                'level_distribution': level_stats,
                'error_percentage': round(error_percentage, 2),
                'analyzed_lines': len(parsed_logs)
            },
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except ValueError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
    except FileNotFoundError as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"獲取日誌統計失敗: {str(e)}")
        return Response({
            'success': False,
            'error': f'獲取日誌統計失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
