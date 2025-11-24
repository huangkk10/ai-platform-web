#!/usr/bin/env python
"""
Protocol Assistant 圖片顯示問題快速修復腳本
===========================================

問題：Protocol Assistant 顯示與查詢無關的圖片（如 Kingston 開卡圖片出現在 IOL 密碼查詢中）
原因：文檔搜尋 threshold 過低，返回了相似度不足的文檔
解決：提高 Protocol Assistant 的搜尋閾值到 0.85

使用方式：
    docker exec -it ai-django python fix_protocol_image_threshold.py
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ThresholdSetting


def main():
    """主函數：調整 Protocol Assistant 的 threshold"""
    
    print("=" * 60)
    print("Protocol Assistant 圖片過濾閾值調整工具")
    print("=" * 60)
    print()
    
    try:
        # 獲取 Protocol Assistant 的 threshold 設定
        threshold_obj = ThresholdSetting.objects.get(
            assistant_type='protocol_assistant'
        )
        
        print(f"📊 當前設定：")
        print(f"   Assistant: {threshold_obj.assistant_type}")
        print(f"   Threshold: {threshold_obj.threshold}")
        print(f"   更新時間: {threshold_obj.updated_at}")
        print()
        
        # 儲存舊值
        old_threshold = threshold_obj.threshold
        
        # 設定新值（建議：0.85）
        new_threshold = 0.85
        
        print(f"🔧 調整計畫：")
        print(f"   舊 Threshold: {old_threshold}")
        print(f"   新 Threshold: {new_threshold}")
        print()
        
        # 確認是否執行
        confirm = input("是否執行調整？(y/n): ").strip().lower()
        
        if confirm == 'y':
            # 更新 threshold
            threshold_obj.threshold = new_threshold
            threshold_obj.save()
            
            # 驗證更新
            threshold_obj.refresh_from_db()
            
            print()
            print("=" * 60)
            print("✅ 調整完成")
            print("=" * 60)
            print(f"📊 新設定：")
            print(f"   Threshold: {threshold_obj.threshold}")
            print(f"   更新時間: {threshold_obj.updated_at}")
            print()
            print("📋 預期效果：")
            print("   - 減少低相關度文檔被包含在搜尋結果中")
            print("   - 減少無關圖片顯示")
            print("   - 提高回答準確度")
            print()
            print("🧪 測試建議：")
            print("   1. 重新查詢「iol root密碼」")
            print("   2. 確認不再出現 Kingston 開卡圖片")
            print("   3. 確認仍然返回 UNH-IOL 相關內容")
            print()
            print("⚠️ 注意事項：")
            print("   - 如果發現相關文檔被過度過濾，可調回 0.80")
            print("   - 建議測試多個查詢場景")
            print()
            
        else:
            print()
            print("❌ 取消調整")
            print()
    
    except ThresholdSetting.DoesNotExist:
        print("❌ 錯誤：找不到 Protocol Assistant 的 threshold 設定")
        print()
        print("💡 解決方案：")
        print("   1. 確認資料庫中是否存在 ThresholdSetting 記錄")
        print("   2. 如果不存在，請先創建：")
        print()
        print("   from api.models import ThresholdSetting")
        print("   ThresholdSetting.objects.create(")
        print("       assistant_type='protocol_assistant',")
        print("       threshold=0.85")
        print("   )")
        print()
        sys.exit(1)
    
    except Exception as e:
        print(f"❌ 發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
