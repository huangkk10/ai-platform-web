"""
RVT Guide 向量服務

統一處理 RVT Guide 向量相關功能：
- 向量生成
- 向量存儲
- 向量更新
- 向量搜索

減少 views.py 中向量處理相關程式碼
"""

import logging

logger = logging.getLogger(__name__)


class RVTGuideVectorService:
    """RVT Guide 向量服務 - 統一管理向量相關操作"""
    
    def __init__(self):
        self.logger = logger
        self._embedding_service = None
    
    @property
    def embedding_service(self):
        """獲取 embedding 服務"""
        if self._embedding_service is None:
            try:
                # 動態導入 embedding_service 避免循環導入
                from backend.api.services.embedding_service import get_embedding_service
                self._embedding_service = get_embedding_service()  # 使用 1024 維模型
            except ImportError:
                self._embedding_service = None
        return self._embedding_service
    
    def generate_and_store_vector(self, instance, action='create'):
        """
        為 RVT Guide 生成並存儲向量資料
        
        Args:
            instance: RVTGuide 實例
            action: 操作類型 ('create' 或 'update')
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        try:
            if not self.embedding_service:
                self.logger.warning("Embedding service 不可用，跳過向量生成")
                return False
            
            # 格式化內容用於向量化
            content = self._format_content_for_embedding(instance)
            
            # 生成並儲存向量
            success = self.embedding_service.store_document_embedding(
                source_table='rvt_guide',
                source_id=instance.id,
                content=content,
                use_1024_table=True  # 使用 1024 維表格
            )
            
            if success:
                self.logger.info(f"✅ RVT Guide 向量生成成功 ({action}): ID {instance.id}")
            else:
                self.logger.error(f"❌ RVT Guide 向量生成失敗 ({action}): ID {instance.id}")
                
            return success
                
        except Exception as e:
            self.logger.error(f"❌ RVT Guide 向量生成異常 ({action}): ID {instance.id} - {str(e)}")
            return False
    
    def _format_content_for_embedding(self, instance):
        """
        格式化 RVT Guide 內容用於向量化
        
        Args:
            instance: RVTGuide 實例
            
        Returns:
            str: 格式化後的內容
        """
        content_parts = []
        
        # 標題
        if hasattr(instance, 'title') and instance.title:
            content_parts.append(f"標題: {instance.title}")
        
        # 內容
        if hasattr(instance, 'content') and instance.content:
            content_parts.append(f"內容: {instance.content}")
        
        # 關鍵字
        if hasattr(instance, 'keywords') and instance.keywords:
            content_parts.append(f"關鍵字: {instance.keywords}")
        
        # 子分類
        if hasattr(instance, 'sub_category') and instance.sub_category:
            content_parts.append(f"分類: {instance.sub_category}")
        
        # 文檔名稱
        if hasattr(instance, 'document_name') and instance.document_name:
            content_parts.append(f"文檔: {instance.document_name}")
        
        return "\n".join(content_parts)
    
    def delete_vector(self, instance):
        """
        刪除 RVT Guide 的向量資料
        
        Args:
            instance: RVTGuide 實例
            
        Returns:
            bool: 成功返回 True，失敗返回 False
        """
        try:
            if not self.embedding_service:
                self.logger.warning("Embedding service 不可用，跳過向量刪除")
                return False
            
            # 使用新的 delete_document_embedding 方法
            success_1024 = False
            success_768 = False
            
            if hasattr(self.embedding_service, 'delete_document_embedding'):
                # 刪除 1024 維向量（預設）
                success_1024 = self.embedding_service.delete_document_embedding(
                    source_table='rvt_guide',
                    source_id=instance.id,
                    use_1024_table=True
                )
                
                # 刪除 768 維向量（備用）
                success_768 = self.embedding_service.delete_document_embedding(
                    source_table='rvt_guide',
                    source_id=instance.id,
                    use_1024_table=False
                )
                
                if success_1024 or success_768:
                    dimensions = []
                    if success_1024:
                        dimensions.append("1024維")
                    if success_768:
                        dimensions.append("768維")
                    self.logger.info(f"✅ RVT Guide 向量刪除成功 ({', '.join(dimensions)}): ID {instance.id}")
                    return True
                else:
                    self.logger.warning(f"⚠️  未找到 RVT Guide 對應的向量資料: ID {instance.id}")
                    return False
                    
            else:
                self.logger.warning("Embedding service 不支援向量刪除")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ RVT Guide 向量刪除異常: ID {instance.id} - {str(e)}")
            return False
    
    def batch_generate_vectors(self, instances):
        """
        批量生成向量
        
        Args:
            instances: RVTGuide 實例列表
            
        Returns:
            dict: 批量操作結果統計
        """
        result = {
            'total': len(instances),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for instance in instances:
            try:
                success = self.generate_and_store_vector(instance, action='batch')
                if success:
                    result['success'] += 1
                else:
                    result['failed'] += 1
                    result['errors'].append(f"ID {instance.id}: 向量生成失敗")
            except Exception as e:
                result['failed'] += 1
                result['errors'].append(f"ID {instance.id}: {str(e)}")
        
        self.logger.info(f"批量向量生成完成: {result}")
        return result
    
    def rebuild_all_vectors(self, queryset=None):
        """
        重建所有 RVT Guide 的向量
        
        Args:
            queryset: 可選的查詢集，如果不提供則處理所有記錄
            
        Returns:
            dict: 重建結果統計
        """
        try:
            if queryset is None:
                from api.models import RVTGuide
                queryset = RVTGuide.objects.all()
            
            self.logger.info(f"開始重建 {queryset.count()} 個 RVT Guide 的向量")
            
            return self.batch_generate_vectors(queryset)
            
        except Exception as e:
            self.logger.error(f"重建向量失敗: {str(e)}")
            return {
                'total': 0,
                'success': 0,
                'failed': 0,
                'errors': [str(e)]
            }