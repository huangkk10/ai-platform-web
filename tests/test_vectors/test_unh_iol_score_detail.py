#!/usr/bin/env python
"""
詳細驗證：UNH-IOL 分數計算過程
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.protocol_guide.search_service import ProtocolGuideSearchService

def main():
    print("=" * 80)
    print("🔬 詳細驗證：UNH-IOL 分數計算過程")
    print("=" * 80)
    
    # 獲取 UNH-IOL 文檔
    try:
        unh_iol = ProtocolGuide.objects.get(title="UNH-IOL")
        print(f"\n📄 文檔資訊:")
        print(f"   ID: {unh_iol.id}")
        print(f"   標題: {unh_iol.title}")
        print(f"   內容長度: {len(unh_iol.content)} 字元")
        
        # 查找 "sop" 在內容中的位置
        content_lower = unh_iol.content.lower()
        query = "sop"
        
        if query in content_lower:
            position = content_lower.find(query)
            count = content_lower.count(query)
            
            print(f"\n🔍 匹配資訊:")
            print(f"   查詢字串: '{query}'")
            print(f"   首次出現位置: {position} / {len(content_lower)} ({position/len(content_lower)*100:.1f}%)")
            print(f"   出現次數: {count}")
            
            # 顯示匹配上下文
            start = max(0, position - 50)
            end = min(len(unh_iol.content), position + 50)
            context = unh_iol.content[start:end]
            print(f"\n   匹配上下文:")
            print(f"   ...{context}...")
            
            # 手動計算分數
            print(f"\n🧮 分數計算（手動驗證）:")
            
            # 1. 標題檢查
            title_lower = unh_iol.title.lower()
            print(f"\n   1. 標題匹配檢查:")
            print(f"      標題: '{unh_iol.title}'")
            print(f"      查詢: '{query}'")
            if query in title_lower:
                print(f"      ✅ 標題包含查詢字串")
            else:
                print(f"      ❌ 標題不包含查詢字串")
            
            # 2. 內容匹配計算
            print(f"\n   2. 內容匹配計算:")
            position_factor = 1.0 - (position / len(content_lower))
            density_bonus = min(count * 0.05, 0.3)
            base_score = 0.3
            position_contribution = position_factor * 0.2
            content_score = base_score + position_contribution + density_bonus
            final_content_score = min(content_score, 0.6)
            
            print(f"      基礎分: {base_score}")
            print(f"      位置因素: {position_factor:.3f} (1 - {position}/{len(content_lower)})")
            print(f"      位置貢獻: {position_contribution:.3f} ({position_factor:.3f} * 0.2)")
            print(f"      密度因素: 出現 {count} 次")
            print(f"      密度加成: {density_bonus:.3f} (min({count} * 0.05, 0.3))")
            print(f"      內容分數: {content_score:.3f} ({base_score} + {position_contribution:.3f} + {density_bonus:.3f})")
            print(f"      限制上限: {final_content_score:.3f} (max 0.6)")
            
            print(f"\n   3. 最終分數:")
            print(f"      預期分數: {final_content_score:.2f}")
        
        # 使用實際的 service 計算
        print(f"\n" + "=" * 80)
        print("🎯 實際計算結果")
        print("=" * 80)
        
        service = ProtocolGuideSearchService()
        actual_score = service._calculate_keyword_score(unh_iol, "sop")
        
        print(f"\n   實際計算分數: {actual_score:.2f}")
        print(f"\n   閾值比較:")
        print(f"   - threshold = 0.75")
        print(f"   - 實際分數 = {actual_score:.2f}")
        
        if actual_score < 0.75:
            print(f"   - ✅ {actual_score:.2f} < 0.75 → 會被過濾掉（正確！）")
        else:
            print(f"   - ❌ {actual_score:.2f} >= 0.75 → 會通過過濾（錯誤！）")
        
        print(f"\n" + "=" * 80)
        print("✅ 驗證完成")
        print("=" * 80)
        
    except ProtocolGuide.DoesNotExist:
        print("\n❌ 找不到 UNH-IOL 文檔")
        return
    except Exception as e:
        print(f"\n❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
