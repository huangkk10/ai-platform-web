#!/usr/bin/env python3
"""
Protocol Assistant 搜尋診斷工具
================================

診斷為什麼找不到特定文檔的詳細原因
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService
from api.models import ProtocolGuide
from django.db import connection
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def diagnose_search():
    """診斷搜尋問題"""
    service = ProtocolGuideSearchService()
    
    print("=" * 100)
    print("Protocol Assistant 搜尋診斷")
    print("=" * 100)
    
    # 1. 確認目標文檔
    print("\n【步驟 1】確認 UNH-IOL 文檔存在")
    print("-" * 100)
    try:
        guide = ProtocolGuide.objects.get(title__icontains='UNH-IOL')
        print(f"✅ 找到文檔: ID={guide.id}, 標題='{guide.title}'")
        print(f"   內容長度: {len(guide.content)} 字元")
        print(f"   內容前 200 字元: {guide.content[:200]}")
        
        # 檢查向量
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM document_embeddings 
                WHERE source_table = 'protocol_guide' AND source_id = %s
            """, [guide.id])
            doc_vector = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM document_section_embeddings 
                WHERE source_table = 'protocol_guide' AND source_id = %s
            """, [guide.id])
            section_vector = cursor.fetchone()[0]
            
            print(f"   向量狀態: 文檔向量={doc_vector}, 段落向量={section_vector}")
            
            if doc_vector == 0 and section_vector == 0:
                print("   ⚠️  警告：此文檔沒有向量！需要生成向量。")
                return
                
    except ProtocolGuide.DoesNotExist:
        print("❌ 錯誤：找不到 UNH-IOL 文檔")
        return
    
    # 2. 測試不同查詢詞
    print("\n【步驟 2】測試不同查詢詞和閾值")
    print("-" * 100)
    
    test_queries = [
        ("UNH-IOL", "精確標題匹配"),
        ("iol", "簡短關鍵字"),
        ("iol sop 請說明", "原始查詢"),
        ("iol sop", "移除請求指令"),
        ("IOL", "大寫"),
    ]
    
    test_thresholds = [0.4, 0.5, 0.6, 0.7]
    
    for query, description in test_queries:
        print(f"\n📝 查詢: '{query}' ({description})")
        print("   " + "-" * 96)
        
        for threshold in test_thresholds:
            # Stage 1 搜尋
            results_stage1 = service.search_knowledge(
                query=query,
                limit=5,
                use_vector=True,
                threshold=threshold,
                search_mode='auto'
            )
            
            # 檢查是否找到 UNH-IOL
            found_unh_iol = any(
                r.get('metadata', {}).get('id') == guide.id 
                for r in results_stage1
            )
            
            if found_unh_iol:
                # 找到了，顯示分數
                for r in results_stage1:
                    if r.get('metadata', {}).get('id') == guide.id:
                        print(f"   ✅ threshold={threshold:.2f}: 找到 (分數={r.get('score', 0):.3f})")
                        break
            else:
                print(f"   ❌ threshold={threshold:.2f}: 未找到")
    
    # 3. 測試關鍵字搜尋
    print("\n【步驟 3】測試關鍵字搜尋 (備用方案)")
    print("-" * 100)
    
    for query, description in test_queries[:3]:
        print(f"\n📝 查詢: '{query}' ({description})")
        results_keyword = service.search_with_keywords(query, limit=5, threshold=0.3)
        
        found = any(r.get('metadata', {}).get('id') == guide.id for r in results_keyword)
        if found:
            for r in results_keyword:
                if r.get('metadata', {}).get('id') == guide.id:
                    print(f"   ✅ 關鍵字搜尋找到 (分數={r.get('score', 0):.3f})")
                    break
        else:
            print(f"   ❌ 關鍵字搜尋未找到")
    
    # 4. 建議
    print("\n" + "=" * 100)
    print("【診斷結論與建議】")
    print("=" * 100)
    
    print("""
如果上面的測試顯示：

1. **使用 "UNH-IOL" 或 "iol" 可以找到，但 "iol sop 請說明" 找不到**
   → 問題：查詢詞中的 "sop 請說明" 干擾了語義理解
   → 解決方案：
      a) 降低 threshold（從 0.7 降到 0.5 或 0.4）
      b) 在 Dify Studio 中調整提示詞，讓 AI 提取關鍵字後再搜尋
      c) 優化查詢詞預處理（移除 "請說明" 等指令性詞語）

2. **所有測試都找不到**
   → 問題：向量不存在或內容不匹配
   → 解決方案：
      a) 重新生成向量
      b) 檢查內容是否包含相關關鍵字

3. **關鍵字搜尋可以找到，向量搜尋找不到**
   → 問題：向量相似度不夠高
   → 解決方案：
      a) 降低 threshold
      b) 在搜尋策略中提高關鍵字搜尋的優先級
      
4. **使用較低 threshold (0.4-0.5) 可以找到**
   → 建議：在 Django Admin 中將 Protocol Assistant 的 threshold 調整為較低值
   → 路徑：兩階段搜尋權重配置 → Protocol Assistant → 修改 threshold
    """)

if __name__ == "__main__":
    diagnose_search()
