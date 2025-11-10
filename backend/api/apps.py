from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api'
    
    def ready(self):
        """
        應用啟動時執行
        
        導入 signals 以註冊 Django signal handlers
        這會自動為 ProtocolGuide、RVTGuide、KnowIssue 
        設置向量自動生成/刪除機制
        """
        # 導入 signals（觸發 @receiver 裝飾器註冊）
        import api.signals  # noqa: F401