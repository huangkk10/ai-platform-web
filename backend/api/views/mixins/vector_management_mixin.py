"""
Vector Management Mixin
統一向量資料生成和管理

消除 3 個 ViewSet 中的重複向量處理代碼
"""

import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class VectorManagementMixin:
    """
    向量資料管理 Mixin
    
    統一處理：
    1. 向量內容格式化
    2. Embedding 生成
    3. 向量存儲
    4. 向量刪除
    5. 錯誤處理
    
    使用方式：
        class MyViewSet(VectorManagementMixin, viewsets.ModelViewSet):
            vector_config = {
                'source_table': 'know_issue',
                'content_fields': ['issue_id', 'project', 'error_message'],
                'use_1024_table': True,
            }
            
            def perform_create(self, serializer):
                instance = super().perform_create(serializer)
                self.generate_vector_for_instance(instance, action='create')
                return instance
    """
    
    # 子類需要定義
    vector_config: Dict[str, Any] = {
        'source_table': None,      # 例如: 'know_issue'
        'content_fields': [],      # 例如: ['issue_id', 'project', 'error_message']
        'use_1024_table': True,    # 是否使用 1024 維向量表
        'enable_vector': True,     # 是否啟用向量功能
    }
    
    def generate_vector_for_instance(self, instance, action='create') -> bool:
        """
        為實例生成向量資料
        
        Args:
            instance: 模型實例
            action: 操作類型 ('create' 或 'update')
        
        Returns:
            bool: 是否成功
        """
        # 檢查是否啟用向量功能
        if not self.vector_config.get('enable_vector', True):
            logger.debug(f"向量功能未啟用，跳過: {self.vector_config.get('source_table')}")
            return False
        
        try:
            # 動態導入避免循環依賴
            from api.services.embedding_service import get_embedding_service
            
            # 格式化內容
            content = self._format_vector_content(instance)
            
            if not content or not content.strip():
                logger.warning(f"向量內容為空，跳過生成: ID {instance.id}")
                return False
            
            # 獲取 embedding 服務
            service = get_embedding_service()
            
            # 生成並存儲向量
            config = self.vector_config
            success = service.store_document_embedding(
                source_table=config.get('source_table'),
                source_id=instance.id,
                content=content,
                use_1024_table=config.get('use_1024_table', True)
            )
            
            if success:
                logger.info(
                    f"✅ {config.get('source_table')} 向量生成成功 ({action}): "
                    f"ID {instance.id}"
                )
            else:
                logger.warning(
                    f"⚠️ {config.get('source_table')} 向量生成失敗 ({action}): "
                    f"ID {instance.id}"
                )
            
            return success
            
        except ImportError:
            logger.warning("embedding_service 不可用，跳過向量生成")
            return False
        except Exception as e:
            logger.error(
                f"❌ {self.vector_config.get('source_table')} 向量生成異常 ({action}): "
                f"ID {instance.id} - {str(e)}"
            )
            return False
    
    def _format_vector_content(self, instance) -> str:
        """
        格式化向量內容（子類可覆寫）
        
        預設行為：將配置中的欄位拼接成字串
        
        Args:
            instance: 模型實例
        
        Returns:
            str: 格式化後的內容
        """
        content_parts = []
        
        for field_name in self.vector_config.get('content_fields', []):
            value = getattr(instance, field_name, None)
            if value:
                # 格式化欄位名稱（轉換為可讀）
                readable_name = field_name.replace('_', ' ').title()
                content_parts.append(f"{readable_name}: {value}")
        
        return "\n".join(content_parts)
    
    def delete_vector_for_instance(self, instance) -> bool:
        """
        刪除實例的向量資料
        
        Args:
            instance: 模型實例
        
        Returns:
            bool: 是否成功
        """
        # 檢查是否啟用向量功能
        if not self.vector_config.get('enable_vector', True):
            return False
        
        try:
            from api.services.embedding_service import get_embedding_service
            
            service = get_embedding_service()
            config = self.vector_config
            
            # 檢查服務是否有刪除方法
            if not hasattr(service, 'delete_document_embedding'):
                logger.warning("embedding_service 不支援刪除功能")
                return False
            
            # 刪除向量
            success = service.delete_document_embedding(
                source_table=config.get('source_table'),
                source_id=instance.id,
                use_1024_table=config.get('use_1024_table', True)
            )
            
            if success:
                logger.info(
                    f"✅ 向量刪除成功: {config.get('source_table')} ID {instance.id}"
                )
            else:
                logger.warning(
                    f"⚠️ 向量刪除失敗: {config.get('source_table')} ID {instance.id}"
                )
            
            return success
            
        except ImportError:
            logger.warning("embedding_service 不可用，跳過向量刪除")
            return False
        except Exception as e:
            logger.error(f"❌ 向量刪除失敗: {str(e)}")
            return False
    
    def update_vector_for_instance(self, instance) -> bool:
        """
        更新實例的向量資料（實際上是重新生成）
        
        Args:
            instance: 模型實例
        
        Returns:
            bool: 是否成功
        """
        return self.generate_vector_for_instance(instance, action='update')
