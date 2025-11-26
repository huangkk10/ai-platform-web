#!/usr/bin/env python
"""測試為什麼 CrystalDiskMark 搜尋找不到正確的文檔"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service

def test_search():
    service = get_embedding_service()
    
    # 測試查詢
    query = "CrystalDiskMark 是什麼"
    
    print(f"\n{'='*80}")
    print(f"🔍 測試查詢: {query}")
    print(f"{'='*80}\n")
    
    # 執行語義搜尋（不設門檻，看所有結果）
    results = service.search_similar_documents(
        query=query,
        source_table='protocol_guide',
        limit=10,
        threshold=0.0,
        use_1024_table=False  # 使用統一表
    )
    
    print(f"找到 {len(results)} 筆結果:\n")
    
    # 顯示第一筆結果的所有欄位
    if results:
        print(f"第一筆結果的欄位: {list(results[0].keys())}\n")
    
    for i, result in enumerate(results, 1):
        title = result.get('document_name', result.get('title', 'N/A'))
        similarity = result.get('similarity', result.get('score', 0))
        source_id = result.get('source_id', result.get('id', 0))
        
        # 標記出 CrystalDiskMark 5
        marker = " ⭐ [目標文檔]" if source_id == 16 else ""
        
        print(f"結果 {i}:{marker}")
        print(f"  ID: {source_id}")
        print(f"  標題: {title}")
        print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
        
        # 顯示內容預覽
        content = result.get('content', '')
        if content:
            preview = content[:150].replace('\n', ' ')
            print(f"  內容: {preview}...")
        
        print()
    
    # 特別檢查 CrystalDiskMark 5 的排名
    crystaldiskmark_result = next((r for r in results if r['source_id'] == 16), None)
    if crystaldiskmark_result:
        rank = results.index(crystaldiskmark_result) + 1
        print(f"\n{'='*80}")
        print(f"📊 CrystalDiskMark 5 (ID=16) 的排名: 第 {rank} 名")
        print(f"   相似度: {crystaldiskmark_result['score']:.4f} ({crystaldiskmark_result['score']*100:.2f}%)")
        print(f"{'='*80}\n")
    else:
        print(f"\n⚠️ 找不到 CrystalDiskMark 5 (ID=16) 的結果\n")

if __name__ == '__main__':
    test_search()
