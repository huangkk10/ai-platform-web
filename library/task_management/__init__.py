"""
Task Management Library - 統一任務管理模組

提供任務管理相關的所有組件：
- TaskViewSetManager: ViewSet 管理器
- TaskQueryManager: 查詢管理器
- TaskAssignmentHandler: 任務指派處理器
- TaskStatusManager: 狀態管理器
- 備用處理器

使用方式：
    from library.task_management import TaskViewSetManager, TaskAssignmentHandler
"""

# 核心組件導入
try:
    from .viewset_manager import (
        TaskViewSetManager,
        create_task_viewset_manager
    )
    from .query_manager import (
        TaskQueryManager,
        create_task_query_manager,
        get_user_related_tasks
    )
    from .assignment_handler import (
        TaskAssignmentHandler,
        create_task_assignment_handler,
        handle_task_assignment
    )
    from .status_manager import (
        TaskStatusManager,
        create_task_status_manager,
        handle_status_change
    )
    from .fallback_handlers import (
        TaskFallbackHandler,
        fallback_task_assignment,
        fallback_status_change,
        fallback_task_query
    )
    
    TASK_MANAGEMENT_LIBRARY_AVAILABLE = True
    
except ImportError as e:
    # 如果有任何導入失敗，提供備用
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Task Management library 組件導入失敗: {e}")
    
    # 設定所有組件為 None
    TaskViewSetManager = None
    create_task_viewset_manager = None
    TaskQueryManager = None
    create_task_query_manager = None
    get_user_related_tasks = None
    TaskAssignmentHandler = None
    create_task_assignment_handler = None
    handle_task_assignment = None
    TaskStatusManager = None
    create_task_status_manager = None
    handle_status_change = None
    TaskFallbackHandler = None
    fallback_task_assignment = None
    fallback_status_change = None
    fallback_task_query = None
    
    TASK_MANAGEMENT_LIBRARY_AVAILABLE = False


# 便利函數：統一創建服務
def create_task_manager():
    """創建完整的任務管理器"""
    if TASK_MANAGEMENT_LIBRARY_AVAILABLE:
        try:
            return TaskViewSetManager()
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"無法創建任務管理器: {e}")
            return None
    return None


def get_task_library_status():
    """獲取 Task Management library 狀態"""
    return {
        'available': TASK_MANAGEMENT_LIBRARY_AVAILABLE,
        'components': {
            'viewset_manager': TaskViewSetManager is not None,
            'query_manager': TaskQueryManager is not None,
            'assignment_handler': TaskAssignmentHandler is not None,
            'status_manager': TaskStatusManager is not None,
            'fallback_handler': TaskFallbackHandler is not None
        }
    }


# 導出所有主要組件
__all__ = [
    # 核心組件
    'TaskViewSetManager',
    'TaskQueryManager', 
    'TaskAssignmentHandler',
    'TaskStatusManager',
    
    # 便利函數
    'create_task_viewset_manager',
    'create_task_query_manager',
    'create_task_assignment_handler',
    'create_task_status_manager',
    'create_task_manager',
    
    # 統一處理函數
    'get_user_related_tasks',
    'handle_task_assignment',
    'handle_status_change',
    
    # 備用組件
    'TaskFallbackHandler',
    'fallback_task_assignment',
    'fallback_status_change',
    'fallback_task_query',
    
    # 狀態
    'TASK_MANAGEMENT_LIBRARY_AVAILABLE',
    'get_task_library_status'
]