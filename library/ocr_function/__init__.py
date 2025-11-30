"""
OCR Function Library
====================

提供 OCR 圖片文字辨識功能的服務模組。

使用方式：
    from library.ocr_function import ocr_image, ocr_image_from_bytes, ocr_image_from_base64
    
    # 從檔案路徑辨識
    result = ocr_image('/path/to/image.jpg')
    
    # 從 bytes 辨識
    result = ocr_image_from_bytes(image_bytes, 'image.png')
    
    # 從 Base64 辨識
    result = ocr_image_from_base64(base64_string)
    
    # 檢查結果
    if result['success']:
        print(result['text'])
    else:
        print(f"錯誤: {result['error']}")
"""

from .ocr_service import (
    OCRService,
    ocr_image,
    ocr_image_from_bytes,
    ocr_image_from_base64,
)

__all__ = [
    'OCRService',
    'ocr_image',
    'ocr_image_from_bytes',
    'ocr_image_from_base64',
]
