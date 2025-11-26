#!/usr/bin/env python
"""測試 Stage 2 全文搜尋，查看實際找到的是哪個文檔"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from api.models import ProtocolGuide

def test_stage2_search():
    """測試 Stage 2 全文搜尋"""
    
    query = "CrystalDiskMark ？"  # 清理後的查詢
    
    print(f"\n{'='*80}")
    print(f"🔍 測試 Stage 2 全文搜尋 (模擬實際搜尋)")
    print(f"{'='*80}\n")
    print(f"查詢: {query}")
    print(f"權重: 標題 10% / 內容 90%")
    print(f"source_table: protocol_guide")
    print(f"limit: 5 (多看幾筆)")
    print(f"\n執行搜尋...")
    
    # 使用 embedding_service 的多向量搜尋
    service = get_embedding_service()
    
    results = service.search_similar_documents_multi(
        query=query,
        source_table='protocol_guide',
        limit=5,
        threshold=0.0,  # 不設門檻，看所有結果
        title_weight=0.1,  # Stage 2: 標題 10%
        content_weight=0.9  # Stage 2: 內容 90%
    )
    
    print(f"\n{'='*80}")
    print(f"📊 搜尋結果 (前 5 名)")
    print(f"{'='*80}\n")
    
    if results:
        for i, result in enumerate(results, 1):
            source_id = result.get('source_id')
            combined_score = result.get('combined_score', 0)
            
            # 查詢標題
            try:
                guide = ProtocolGuide.objects.get(id=source_id)
                title = guide.title
            except:
                title = 'N/A'
            
            # 標記是否為 CrystalDiskMark 5
            is_target = " ⭐ [目標文檔]" if source_id == 16 else ""
            is_lenovo = " ⚠️ [實際找到的: Lenovo SSDV Ulink]" if source_id == 31 else ""
            
            print(f"結果 {i}:{is_target}{is_lenovo}")
            print(f"  ID: {source_id}")
            print(f"  標題: {title}")
            print(f"  組合分數: {combined_score:.4f} ({combined_score*100:.2f}%)")
            
            # 顯示詳細分數
            if 'title_score' in result:
                print(f"  ├─ 標題分數: {result['title_score']:.4f} (權重 10%)")
            if 'content_score' in result:
                print(f"  └─ 內容分數: {result['content_score']:.4f} (權重 90%)")
            
            print()
    else:
        print("⚠️ 沒有找到任何結果")
    
    # 總結
    print(f"\n{'='*80}")
    print(f"🎯 搜尋結果分析")
    print(f"{'='*80}\n")
    
    if results:
        top_result_id = results[0].get('source_id')
        
        if top_result_id == 16:
            print("✅ 正確找到 CrystalDiskMark 5 (ID=16)")
        elif top_result_id == 31:
            print("❌ 找到錯誤文檔: Lenovo SSDV Ulink (ID=31)")
            print("   預期找到: CrystalDiskMark 5 (ID=16)")
            print("\n🔍 可能原因:")
            print("   1. Lenovo Ulink 文檔的內容向量與查詢更相似")
            print("   2. CrystalDiskMark 5 的內容向量相似度較低")
            print("   3. 權重 90% 集中在內容向量，導致標題相關性被忽略")
            
            # 檢查 CrystalDiskMark 5 的排名
            cdm_result = next((r for r in results if r.get('source_id') == 16), None)
            if cdm_result:
                rank = results.index(cdm_result) + 1
                print(f"\n📊 CrystalDiskMark 5 實際排名: 第 {rank} 名")
                print(f"   相似度: {cdm_result.get('combined_score', 0):.4f}")
            else:
                print("\n⚠️ CrystalDiskMark 5 不在前 5 名結果中")
        else:
            try:
                guide = ProtocolGuide.objects.get(id=top_result_id)
                print(f"❌ 找到錯誤文檔: {guide.title} (ID={top_result_id})")
            except:
                print(f"❌ 找到錯誤文檔: ID={top_result_id}")
            print(f"   預期找到: CrystalDiskMark 5 (ID=16)")
    else:
        print("❌ 沒有找到任何結果")
    
    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    test_stage2_search()
