"""
Content ViewSets Module
內容和圖片管理 ViewSets

包含：
- ContentImageViewSet: 通用內容圖片管理
"""

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from api.models import ContentImage, RVTGuide, KnowIssue, ProtocolGuide
from api.serializers import ContentImageSerializer

import logging
logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ContentImageViewSet(viewsets.ModelViewSet):
    """
    通用內容圖片管理 ViewSet
    
    🔧 基本遷移（無需 Mixin，邏輯已足夠清晰）
    """
    queryset = ContentImage.objects.all()
    serializer_class = ContentImageSerializer
    permission_classes = [permissions.AllowAny]  # 允許所有用戶訪問圖片
    
    def get_queryset(self):
        """根據查詢參數過濾圖片"""
        queryset = super().get_queryset()
        content_type = self.request.query_params.get('content_type')
        content_id = self.request.query_params.get('content_id')
        filename = self.request.query_params.get('filename')
        
        # 改善檔名搜索邏輯 - 支持更靈活的匹配
        if filename:
            # 1. 精確匹配
            exact_match = Q(filename=filename)
            
            # 2. 包含匹配
            contains_match = Q(filename__icontains=filename)
            
            # 3. 數字串匹配
            clean_filename = filename.replace('.png', '').replace('.jpg', '').replace('.jpeg', '').replace('.gif', '').replace('.bmp', '').replace('.webp', '')
            if clean_filename.isdigit() and len(clean_filename) > 5:
                number_match = Q(filename__icontains=clean_filename)
            else:
                number_match = Q(pk=-1)
            
            # 4. jenkins 關鍵詞匹配
            if 'jenkins' in filename.lower():
                jenkins_match = Q(filename__icontains='jenkins')
            else:
                jenkins_match = Q(pk=-1)
            
            # 5. kisspng 相關匹配
            if 'kisspng' in filename.lower() or 'jenkins' in filename.lower():
                kisspng_match = Q(filename__istartswith='kisspng-') & Q(filename__icontains='jenkins')
            else:
                kisspng_match = Q(pk=-1)
            
            # 6. 反向匹配
            reverse_match = Q(pk=-1)
            if len(filename) > 10:
                reverse_match = Q(filename__icontains=filename)
            
            # 組合所有條件（OR 關係）
            queryset = queryset.filter(
                exact_match | contains_match | number_match | jenkins_match | kisspng_match | reverse_match
            )
        
        if content_type and content_id:
            if content_type == 'rvt-guide':
                queryset = queryset.filter(rvt_guide_id=content_id)
            elif content_type == 'protocol-guide':
                queryset = queryset.filter(protocol_guide_id=content_id)
            else:
                # 使用通用的 content_type 和 object_id 過濾
                from django.contrib.contenttypes.models import ContentType
                try:
                    ct = ContentType.objects.get(model=content_type.replace('-', ''))
                    queryset = queryset.filter(content_type=ct, object_id=content_id)
                except ContentType.DoesNotExist:
                    queryset = queryset.none()
        
        return queryset.filter(is_active=True).order_by('display_order')
    
    def perform_create(self, serializer):
        """處理圖片上傳"""
        uploaded_file = self.request.FILES.get('image')
        content_type = self.request.data.get('content_type')
        content_id = self.request.data.get('content_id')
        title = self.request.data.get('title', '')
        description = self.request.data.get('description', '')
        
        if not uploaded_file:
            raise ValidationError("請提供圖片檔案")
        
        if not content_type or not content_id:
            raise ValidationError("請提供內容類型和內容 ID")
        
        # 檔案驗證
        self._validate_image_file(uploaded_file)
        
        # 根據內容類型獲取對象
        content_object = self._get_content_object(content_type, content_id)
        
        # 創建圖片記錄
        try:
            image = ContentImage.create_from_upload(
                content_object=content_object,
                uploaded_file=uploaded_file,
                title=title,
                description=description
            )
            
            # 更新關聯的向量資料（如果是 RVT Guide 或 Protocol Guide）
            if content_type == 'rvt-guide':
                self._update_rvt_guide_vectors(content_object)
            elif content_type == 'protocol-guide':
                self._update_protocol_guide_vectors(content_object)
            
            serializer.instance = image
            
        except Exception as e:
            logger.error(f"圖片創建失敗: {str(e)}")
            raise ValidationError(f"圖片上傳失敗: {str(e)}")
    
    def _validate_image_file(self, file):
        """驗證圖片檔案"""
        max_size = 2 * 1024 * 1024  # 2MB
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        
        if file.size > max_size:
            raise ValidationError(f"檔案大小不能超過 {max_size // (1024*1024)}MB")
        
        if file.content_type not in allowed_types:
            raise ValidationError(f"不支援的檔案類型: {file.content_type}")
    
    def _get_content_object(self, content_type, content_id):
        """根據內容類型獲取對象"""
        if content_type == 'rvt-guide':
            try:
                return RVTGuide.objects.get(id=content_id)
            except RVTGuide.DoesNotExist:
                raise ValidationError("指定的 RVT Guide 不存在")
        elif content_type == 'protocol-guide':
            try:
                return ProtocolGuide.objects.get(id=content_id)
            except ProtocolGuide.DoesNotExist:
                raise ValidationError("指定的 Protocol Guide 不存在")
        elif content_type == 'know-issue':
            try:
                return KnowIssue.objects.get(id=content_id)
            except KnowIssue.DoesNotExist:
                raise ValidationError("指定的 Know Issue 不存在")
        else:
            raise ValidationError(f"不支援的內容類型: {content_type}")
    
    def _update_rvt_guide_vectors(self, rvt_guide):
        """更新 RVT Guide 的向量資料"""
        try:
            from library.rvt_guide.vector_service import RVTGuideVectorService
            vector_service = RVTGuideVectorService()
            vector_service.generate_and_store_vector(rvt_guide, action='update')
        except Exception as e:
            logger.warning(f"RVT Guide 向量更新失敗: {str(e)}")
    
    def _update_protocol_guide_vectors(self, protocol_guide):
        """更新 Protocol Guide 的向量資料"""
        try:
            from library.protocol_guide.vector_service import ProtocolGuideVectorService
            vector_service = ProtocolGuideVectorService()
            vector_service.generate_and_store_vector(protocol_guide, action='update')
        except Exception as e:
            logger.warning(f"Protocol Guide 向量更新失敗: {str(e)}")
    
    @action(detail=False, methods=['post'], url_path='batch-upload')
    def batch_upload(self, request):
        """批量上傳圖片"""
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        uploaded_files = request.FILES.getlist('images')
        
        if not uploaded_files:
            return Response({'error': '請提供至少一張圖片'}, status=400)
        
        if not content_type or not content_id:
            return Response({'error': '請提供內容類型和內容 ID'}, status=400)
        
        try:
            content_object = self._get_content_object(content_type, content_id)
        except ValidationError as e:
            return Response({'error': str(e)}, status=404)
        
        created_images = []
        errors = []
        
        for uploaded_file in uploaded_files:
            try:
                self._validate_image_file(uploaded_file)
                image = ContentImage.create_from_upload(
                    content_object=content_object,
                    uploaded_file=uploaded_file
                )
                created_images.append(ContentImageSerializer(image).data)
            except Exception as e:
                errors.append(f"{uploaded_file.name}: {str(e)}")
        
        # 更新向量資料
        if created_images:
            if content_type == 'rvt-guide':
                self._update_rvt_guide_vectors(content_object)
            elif content_type == 'protocol-guide':
                self._update_protocol_guide_vectors(content_object)
        
        return Response({
            'success': len(created_images),
            'errors': errors,
            'created_images': created_images
        })
    
    @action(detail=True, methods=['post'])
    def set_primary(self, request, pk=None):
        """設定為主要圖片"""
        image = self.get_object()
        
        # 清除同內容的其他主要圖片
        if image.rvt_guide:
            ContentImage.objects.filter(rvt_guide=image.rvt_guide, is_primary=True).update(is_primary=False)
        else:
            ContentImage.objects.filter(
                content_type=image.content_type, 
                object_id=image.object_id, 
                is_primary=True
            ).update(is_primary=False)
        
        # 設定當前圖片為主要圖片
        image.is_primary = True
        image.save()
        
        return Response({'success': True, 'message': '主要圖片設定成功'})
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """重新排序圖片"""
        image_ids = request.data.get('image_ids', [])
        content_type = request.data.get('content_type')
        content_id = request.data.get('content_id')
        
        if not image_ids:
            return Response({'error': '請提供圖片 ID 列表'}, status=400)
        
        try:
            for index, image_id in enumerate(image_ids, 1):
                ContentImage.objects.filter(id=image_id).update(display_order=index)
            
            return Response({'success': True, 'message': '排序更新成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
