"""
OCR API Views
=============

提供 OCR 圖片分析 API 端點
"""

import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

logger = logging.getLogger(__name__)


class OCRAnalyzeView(APIView):
    """
    OCR 圖片分析 API
    
    POST /api/ocr/analyze/
    - 接收圖片檔案
    - 呼叫 OCR Function (Dify) 取得文字
    - 回傳辨識結果
    
    Request:
        - file: 圖片檔案 (multipart/form-data)
        
    Response:
        {
            "success": true,
            "text": "辨識出的文字內容",
            "filename": "原始檔名"
        }
    """
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [IsAuthenticated]  # 需要登入才能使用 OCR
    
    # 允許的圖片格式
    ALLOWED_TYPES = [
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/bmp',
        'image/webp'
    ]
    
    # 最大檔案大小 (10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    def post(self, request):
        """處理 OCR 圖片分析請求"""
        
        # 1. 檢查是否有上傳檔案
        file = request.FILES.get('file')
        if not file:
            logger.warning('OCR API: 未上傳檔案')
            return Response(
                {'success': False, 'error': '請上傳檔案'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 2. 檢查檔案類型
        content_type = file.content_type
        if content_type not in self.ALLOWED_TYPES:
            logger.warning(f'OCR API: 不支援的檔案格式 - {content_type}')
            return Response(
                {'success': False, 'error': f'不支援的檔案格式: {content_type}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 3. 檢查檔案大小
        if file.size > self.MAX_FILE_SIZE:
            logger.warning(f'OCR API: 檔案過大 - {file.size} bytes')
            return Response(
                {'success': False, 'error': '檔案大小不能超過 10MB'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 4. 讀取檔案內容
            image_data = file.read()
            filename = file.name
            
            logger.info(f'OCR API: 開始處理圖片 - {filename} ({len(image_data)} bytes)')
            
            # 5. 呼叫 OCR 服務
            try:
                from library.ocr_function import ocr_image_from_bytes
                
                result = ocr_image_from_bytes(
                    image_data=image_data,
                    filename=filename
                )
            except ImportError as e:
                logger.error(f'OCR API: 無法載入 OCR 服務模組 - {str(e)}')
                return Response(
                    {'success': False, 'error': 'OCR 服務暫時無法使用'},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            # 6. 回傳結果
            if result.get('success'):
                text = result.get('text', '')
                logger.info(f'OCR API: 辨識成功 - {filename}, 文字長度: {len(text)}')
                
                return Response({
                    'success': True,
                    'text': text,
                    'filename': filename
                })
            else:
                error_msg = result.get('error', 'OCR 辨識失敗')
                logger.error(f'OCR API: 辨識失敗 - {filename}, 錯誤: {error_msg}')
                
                return Response(
                    {'success': False, 'error': error_msg},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            logger.exception(f'OCR API: 處理過程發生錯誤 - {str(e)}')
            return Response(
                {'success': False, 'error': f'處理過程發生錯誤: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
