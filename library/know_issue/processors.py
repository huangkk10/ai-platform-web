"""
Know Issue Processors - 資料處理器
================================

處理 Know Issue 相關的資料處理邏輯：
- 圖片上傳處理
- 資料驗證
- 回應格式化
"""

import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class KnowIssueProcessor:
    """Know Issue 資料處理器 - 處理圖片上傳、驗證、格式化等"""
    
    def __init__(self):
        self.logger = logger
        self.max_images = 5  # 最大圖片數量
        
    def process_image_uploads(self, request) -> Dict[int, Dict[str, Any]]:
        """
        處理圖片上傳
        
        Args:
            request: HTTP 請求對象
            
        Returns:
            Dict[int, Dict[str, Any]]: 上傳的圖片資料 {image_index: {data, filename, content_type}}
        """
        try:
            uploaded_images = {}
            
            for i in range(1, self.max_images + 1):  # image1 到 image5
                image_field = f'image{i}'
                if image_field in request.FILES:
                    image_file = request.FILES[image_field]
                    uploaded_images[i] = {
                        'data': image_file.read(),
                        'filename': image_file.name,
                        'content_type': image_file.content_type,
                        'size': len(image_file.read()) if hasattr(image_file, 'read') else 0
                    }
                    # 重置文件指針
                    image_file.seek(0)
                    uploaded_images[i]['data'] = image_file.read()
                    
            self.logger.info(f"處理了 {len(uploaded_images)} 張圖片上傳")
            return uploaded_images
            
        except Exception as e:
            self.logger.error(f"圖片上傳處理失敗: {e}")
            return {}
    
    def save_images_to_instance(self, instance, uploaded_images: Dict[int, Dict[str, Any]]) -> bool:
        """
        將上傳的圖片保存到 Know Issue 實例
        
        Args:
            instance: KnowIssue 實例
            uploaded_images: 上傳的圖片資料
            
        Returns:
            bool: 是否成功保存
        """
        try:
            for image_index, image_data in uploaded_images.items():
                if hasattr(instance, 'set_image_data'):
                    instance.set_image_data(
                        image_index,
                        image_data['data'],
                        image_data['filename'],
                        image_data['content_type']
                    )
                    self.logger.info(f"保存圖片 {image_index}: {image_data['filename']}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"圖片保存失敗: {e}")
            return False
    
    def validate_know_issue_data(self, data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        驗證 Know Issue 資料
        
        Args:
            data: 要驗證的資料
            
        Returns:
            Tuple[bool, Optional[str]]: (是否有效, 錯誤訊息)
        """
        try:
            # 必填欄位檢查
            required_fields = ['project', 'error_message']
            
            for field in required_fields:
                if not data.get(field):
                    return False, f"必填欄位 '{field}' 不能為空"
            
            # 資料格式檢查
            if 'issue_type' in data and data['issue_type'] not in ['bug', 'feature', 'enhancement', 'question']:
                return False, "無效的問題類型"
                
            if 'status' in data and data['status'] not in ['open', 'in_progress', 'resolved', 'closed']:
                return False, "無效的狀態"
            
            return True, None
            
        except Exception as e:
            self.logger.error(f"資料驗證異常: {e}")
            return False, f"資料驗證失敗: {str(e)}"
    
    def format_know_issue_response(self, instance, action: str = 'create') -> Dict[str, Any]:
        """
        格式化 Know Issue 回應資料
        
        Args:
            instance: KnowIssue 實例
            action: 操作類型
            
        Returns:
            Dict[str, Any]: 格式化的回應資料
        """
        try:
            response_data = {
                'id': instance.id,
                'issue_id': getattr(instance, 'issue_id', ''),
                'project': getattr(instance, 'project', ''),
                'issue_type': getattr(instance, 'issue_type', ''),
                'status': getattr(instance, 'status', ''),
                'error_message': getattr(instance, 'error_message', ''),
                'supplement': getattr(instance, 'supplement', ''),
                'created_at': getattr(instance, 'created_at', None),
                'updated_at': getattr(instance, 'updated_at', None),
                'action': action
            }
            
            # 添加用戶信息
            if hasattr(instance, 'updated_by') and instance.updated_by:
                response_data['updated_by'] = instance.updated_by.username
                
            return response_data
            
        except Exception as e:
            self.logger.error(f"回應格式化失敗: {e}")
            return {'error': f'回應格式化失敗: {str(e)}'}