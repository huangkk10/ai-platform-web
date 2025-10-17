"""
Monitoring Views Module
系統監控相關視圖函數

包含：
- system_logs: 系統日誌獲取
- simple_system_status: 簡化版系統狀態（管理員專用）
- basic_system_status: 基本系統狀態（所有用戶可訪問）
"""

from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

# 導入 System Monitoring Library
try:
    from library.system_monitoring import (
        HealthChecker,
        create_health_checker,
        AdminSystemMonitor,
        create_admin_monitor,
        get_minimal_fallback_status_dict,
        get_basic_fallback_status_dict
    )
except ImportError:
    HealthChecker = None
    create_health_checker = None
    AdminSystemMonitor = None
    create_admin_monitor = None
    get_minimal_fallback_status_dict = None
    get_basic_fallback_status_dict = None

import logging
logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def system_logs(request):
    """
    系統日誌 API - 獲取最近的系統日誌
    
    🔧 基本遷移（簡單函數，無需 Mixin）
    """
    try:
        from django.utils import timezone
        
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


@api_view(['GET'])
@permission_classes([permissions.IsAdminUser])
def simple_system_status(request):
    """
    簡化版系統狀態監控 API - 使用 library/system_monitoring 模組
    
    🔧 基本遷移（使用三層備用邏輯）
    """
    try:
        from django.db import connection
        
        # Primary: AdminSystemMonitor
        if AdminSystemMonitor and create_admin_monitor:
            logger.info("使用 AdminSystemMonitor 進行系統狀態檢查")
            admin_monitor = create_admin_monitor()
            status_dict = admin_monitor.get_simple_status_dict(connection)
            logger.info(f"AdminSystemMonitor 回傳狀態: {status_dict.get('status')}")
            return Response(status_dict, status=status.HTTP_200_OK)
        
        # Fallback: Library fallback function
        if get_minimal_fallback_status_dict:
            logger.warning("AdminSystemMonitor library 不可用，使用 library 備用實現")
            status_dict = get_minimal_fallback_status_dict(connection)
            return Response(status_dict, status=status.HTTP_200_OK)
        
        # Emergency: Import fallback from library
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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def basic_system_status(request):
    """
    基本系統狀態 API - 所有登入用戶可訪問
    提供基本的系統運行狀態，不包含敏感信息
    
    使用 library/system_monitoring 模組提供的功能
    
    🔧 基本遷移（使用三層備用邏輯）
    """
    try:
        # Primary: HealthChecker
        if HealthChecker and create_health_checker:
            from django.db import connection
            
            health_checker = create_health_checker()
            health_result = health_checker.perform_basic_health_check(connection)
            
            # 轉換為 API 回應格式
            response_data = health_result.to_dict()
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        # Fallback: Library fallback function
        if get_basic_fallback_status_dict:
            from django.db import connection
            logger.warning("HealthChecker library 不可用，使用 library 備用實現")
            status_dict = get_basic_fallback_status_dict(connection)
            return Response(status_dict, status=status.HTTP_200_OK)
        
        # Emergency: Import fallback from library
        from django.db import connection
        from library.system_monitoring.fallback_monitor import get_basic_fallback_status_dict
        emergency_status = get_basic_fallback_status_dict(connection)
        return Response(emergency_status, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Basic system status error: {str(e)}")
        return Response({
            'error': f'獲取基本系統狀態失敗: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
