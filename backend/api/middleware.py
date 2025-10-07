from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile


class DisableCSRFMiddleware(MiddlewareMixin):
    """
    Disable CSRF protection for specific API endpoints
    """
    
    EXEMPT_URLS = [
        '/api/auth/login/',
        '/api/auth/logout/',
        '/api/chat/',  # 聊天相關 API
        '/api/dify/',
        '/api/rvt-guide/',
        '/api/rvt-guides/',  # RVT Guide CRUD API
        '/api/users/',  # 用戶管理 API
        '/api/profiles/',  # 用戶檔案和權限管理 API
        '/api/projects/',  # 專案管理 API
        '/api/tasks/',  # 任務管理 API
        '/api/know-issues/',  # Know Issue API
        '/api/test-classes/',  # 測試類別 API
        '/api/ocr-test-classes/',  # OCR 測試類別 API
        '/api/ocr-storage-benchmarks/',  # OCR Storage Benchmark API
    ]
    
    def process_request(self, request):
        """
        Check if the request URL should be exempt from CSRF protection
        """
        path = request.path_info
        
        for exempt_url in self.EXEMPT_URLS:
            if path.startswith(exempt_url):
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
                
        return None


class UserProfileMiddleware(MiddlewareMixin):
    """
    自動為登入用戶創建 UserProfile，並在每次請求時確保 profile 存在
    """
    
    def process_request(self, request):
        """
        在每次請求時檢查並自動創建 UserProfile
        """
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                # 嘗試獲取用戶的 profile
                profile = request.user.userprofile
            except UserProfile.DoesNotExist:
                # 如果不存在，則自動創建
                UserProfile.objects.create(
                    user=request.user,
                    # 新用戶預設沒有任何權限，需要管理員手動授權
                    web_protocol_rag=False,
                    web_ai_ocr=False,
                    web_rvt_assistant=False,
                    kb_protocol_rag=False,
                    kb_ai_ocr=False,
                    kb_rvt_assistant=False,
                    is_super_admin=False
                )
        
        return None