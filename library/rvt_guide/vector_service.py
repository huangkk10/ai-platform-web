"""
RVT Guide 向量服務

統一處理 RVT Guide 向量相關功能：
- 向量生成
- 向量存儲
- 向量更新
- 向量搜索

減少 views.py 中向量處理相關程式碼

✨ 已遷移至新架構 - 繼承 BaseKnowledgeBaseVectorService
"""

import logging
from library.common.knowledge_base import BaseKnowledgeBaseVectorService
from api.models import RVTGuide

logger = logging.getLogger(__name__)


class RVTGuideVectorService(BaseKnowledgeBaseVectorService):
    """
    RVT Guide 向量服務 - 繼承基礎向量服務
    
    ✅ 已遷移至新架構，代碼從 253 行減少至 ~40 行
    
    繼承自 BaseKnowledgeBaseVectorService，自動獲得：
    - generate_and_store_vector(): 生成並存儲向量
    - delete_vector(): 刪除向量
    - batch_generate_vectors(): 批量生成向量
    - rebuild_all_vectors(): 重建所有向量
    """
    
    # 設定必要屬性
    source_table = 'rvt_guide'
    model_class = RVTGuide
    
    def _format_content_for_embedding(self, instance):
        """
        覆寫父類方法 - 自定義 RVT Guide 內容格式化邏輯
        
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
        
        # 🆕 圖片摘要資訊 - 使用新的便利方法
        if hasattr(instance, 'get_images_summary'):
            try:
                images_summary = instance.get_images_summary()
                if images_summary:
                    content_parts.append(images_summary)
            except Exception as e:
                self.logger.warning(f"取得圖片摘要失敗: {str(e)}")
        
        return "\n".join(content_parts)