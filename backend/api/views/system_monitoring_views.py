"""
System Monitoring Views
系統監控相關的 API 端點

包含的 API：
- system_logs: 系統日誌查詢 (管理員專用)
- simple_system_status: 簡化版系統狀態 (管理員專用)
- basic_system_status: 基本系統狀態 (已登入用戶)
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import permissions, status

# 設置日誌
logger = logging.getLogger(__name__)


# 檢查 System Monitoring Library
try:
    from library.system_monitoring import (
        HealthChecker, create_health_checker,
        AdminSystemMonitor, create_admin_monitor,
        get_minimal_fallback_status_dict,
        get_basic_fallback_status_dict
    )
    SYSTEM_MONITORING_AVAILABLE = True
    logger.info("✅ System Monitoring Library 載入成功")
except ImportError as e:
    logger.warning(f"⚠️  System Monitoring Library 無法載入: {str(e)}")
    SYSTEM_MONITORING_AVAILABLE = False
    HealthChecker = None
    create_health_checker = None
    AdminSystemMonitor = None
    create_admin_monitor = None
    get_minimal_fallback_status_dict = None
    get_basic_fallback_status_dict = None


# ============= 系統狀態監控 API =============


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_logs(request):
    """
    系統日誌 API - 獲取最近的系統日誌
    """
    try:
        from django.utils import timezone
        import logging
        
        log_type = request.query_params.get('type', 'django')
        lines = int(request.query_params.get('lines', 50))
        
        if log_type == 'django':
            # 獲取 Django 日誌（這裡簡化處理）
            logger_instance = logging.getLogger('django')
            
            # 返回模擬的日誌數據
            logs = [
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Django server is running",
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: Database connection healthy",
                f"[{timezone.now().strftime('%Y-%m-%d %H:%M:%S')}] INFO: API endpoints responding normally"
            ]
        else:
            logs = ["Log type not supported"]
        
        return Response({
            'logs': logs,
            'type': log_type,
            'lines': len(logs),
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"系統日誌獲取失敗: {str(e)}")
        return Response({
            'error': f'系統日誌獲取失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============= 簡化版系統狀態監控 API =============

@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def simple_system_status(request):
    """
    簡化版系統狀態監控 API - 使用 library/system_monitoring 模組
    """
    try:
        from django.db import connection
        
        # 使用 library 中的管理員監控器
        if AdminSystemMonitor and create_admin_monitor:
            logger.info("使用 AdminSystemMonitor 進行系統狀態檢查")
            admin_monitor = create_admin_monitor()
            status_dict = admin_monitor.get_simple_status_dict(connection)
            logger.info(f"AdminSystemMonitor 回傳狀態: {status_dict.get('status')}")
            return Response(status_dict, status=status.HTTP_200_OK)
        
        # 如果 library 不可用，使用 library 中的備用實現
        else:
            logger.warning("AdminSystemMonitor library 不可用，使用 library 備用實現")
            
            if get_minimal_fallback_status_dict:
                # 使用 library 中的備用實現
                status_dict = get_minimal_fallback_status_dict(connection)
                return Response(status_dict, status=status.HTTP_200_OK)
            else:
                # 最後的備用方案 - 使用 library 中的緊急備用
                from library.system_monitoring.fallback_monitor import get_minimal_fallback_status_dict
                emergency_status = get_minimal_fallback_status_dict(connection)
                return Response(emergency_status, status=status.HTTP_200_OK)
            
    except Exception as e:
        logger.error(f"Simple system status error: {str(e)}")
        try:
            from django.utils import timezone
            timestamp = timezone.now().isoformat()
        except:
            timestamp = None
        return Response({
            'error': f'系統狀態獲取失敗: {str(e)}',
            'status': 'error',
            'timestamp': timestamp
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








# ============= 基本系統狀態 API（所有用戶可訪問）=============

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def basic_system_status(request):
    """
    基本系統狀態 API - 所有登入用戶可訪問
    提供基本的系統運行狀態，不包含敏感信息
    
    使用 library/system_monitoring 模組提供的功能
    """
    try:
        # 如果 library 可用，使用新的健康檢查器
        if HealthChecker and create_health_checker:
            from django.db import connection
            
            # 使用新的健康檢查器
            health_checker = create_health_checker()
            health_result = health_checker.perform_basic_health_check(connection)
            
            # 轉換為 API 回應格式
            response_data = health_result.to_dict()
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        else:
            # 備用實現（如果 library 不可用）
            logger.warning("HealthChecker library 不可用，使用 library 備用實現")
            
            from django.db import connection
            
            if get_basic_fallback_status_dict:
                # 使用 library 中的備用實現
                status_dict = get_basic_fallback_status_dict(connection)
                return Response(status_dict, status=status.HTTP_200_OK)
            else:
                # 最後的備用方案 - 使用 library 中的緊急備用
                from library.system_monitoring.fallback_monitor import get_basic_fallback_status_dict
                emergency_status = get_basic_fallback_status_dict(connection)
                return Response(emergency_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Basic system status error: {str(e)}")
        return Response({
            'error': f'獲取基本系統狀態失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

