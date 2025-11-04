#!/usr/bin/env python3
"""
測試圖片 ID 顯示功能
檢查 ContentImage 模型是否正確顯示資料庫 ID
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ContentImage, ProtocolGuide
from django.contrib.contenttypes.models import ContentType


def test_image_id_display():
    """測試圖片 ID 顯示"""
    print('=' * 70)
    print('🖼️ 測試圖片 ID 顯示功能')
    print('=' * 70)
    print()

    # 查詢 Protocol Guide 相關的圖片
    protocol_content_type = ContentType.objects.get_for_model(ProtocolGuide)
    
    # 查詢前 5 張圖片
    images = ContentImage.objects.filter(
        content_type=protocol_content_type
    )[:5]
    
    if images.exists():
        print(f'✅ 找到 {images.count()} 張 Protocol Guide 相關圖片:')
        print()
        
        for img in images:
            print(f'  📷 圖片 ID: {img.id}')
            print(f'     檔案名稱: {img.filename}')
            print(f'     標題: {img.title or "無標題"}')
            print(f'     尺寸: {img.width}×{img.height}' if img.width and img.height else '     尺寸: 未知')
            print(f'     大小: {img.file_size} bytes' if img.file_size else '     大小: 未知')
            print(f'     是否為主要圖片: {"是" if img.is_primary else "否"}')
            
            # 檢查關聯的 Protocol Guide
            if img.protocol_guide:
                print(f'     關聯 Protocol: {img.protocol_guide.title}')
            elif img.content_object:
                print(f'     關聯內容: {img.content_object}')
                
            print()
            
    else:
        print('❌ 沒有找到 Protocol Guide 相關的圖片')
        print()
        
        # 檢查是否有其他類型的圖片
        all_images = ContentImage.objects.all()[:3]
        if all_images.exists():
            print(f'ℹ️  找到其他類型的圖片 ({all_images.count()} 張):')
            for img in all_images:
                print(f'   ID: {img.id}, 檔案: {img.filename}, 類型: {img.content_type}')
        else:
            print('ℹ️  資料庫中沒有任何圖片記錄')


if __name__ == '__main__':
    test_image_id_display()