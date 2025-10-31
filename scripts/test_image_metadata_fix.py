#!/usr/bin/env python
"""
測試圖片資訊是否已恢復到段落搜尋結果中

測試目的：
- 驗證段落搜尋結果是否包含圖片資訊
- 確認 get_images_summary() 是否正確整合

修復位置：
- library/common/knowledge_base/base_search_service.py
- _format_section_results_to_standard() 方法
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService

def test_image_metadata_in_section_search():
    """測試段落搜尋結果是否包含圖片資訊"""
    
    print("=" * 80)
    print("🧪 測試：段落搜尋結果中的圖片資訊")
    print("=" * 80)
    
    # 初始化搜尋服務
    search_service = ProtocolGuideSearchService()
    
    # 測試查詢（選擇一個可能包含圖片的文檔相關查詢）
    test_queries = [
        "ULINK 測試方法",
        "Protocol 流程圖",
        "測試步驟說明"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n📝 測試 {i}: 查詢「{query}」")
        print("-" * 80)
        
        try:
            results = search_service.semantic_search(
                query=query,
                top_k=2,
                threshold=0.6
            )
            
            if not results:
                print("❌ 沒有找到結果")
                continue
            
            for j, result in enumerate(results, 1):
                print(f"\n結果 {j}:")
                print(f"  📊 相似度: {result.get('score', 0):.2%}")
                print(f"  📄 標題: {result.get('title', 'N/A')}")
                
                content = result.get('content', '')
                
                # 檢查是否包含圖片資訊
                if '包含' in content and '張圖片' in content:
                    print(f"  ✅ 包含圖片資訊")
                    
                    # 提取圖片資訊部分
                    image_info_start = content.find('包含')
                    if image_info_start != -1:
                        image_info = content[image_info_start:].split('\n')[0]
                        print(f"  🖼️  圖片資訊: {image_info}")
                else:
                    print(f"  ⚠️  未包含圖片資訊")
                
                # 顯示內容預覽
                content_preview = content[:200] + "..." if len(content) > 200 else content
                print(f"  📝 內容預覽:\n{content_preview}")
                
                # 顯示元數據
                metadata = result.get('metadata', {})
                if 'sections_found' in metadata:
                    print(f"  📊 找到 {metadata['sections_found']} 個相關段落")
                    print(f"  🎯 最高相似度: {metadata.get('max_similarity', 0):.2%}")
        
        except Exception as e:
            print(f"❌ 測試失敗: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 測試完成")
    print("=" * 80)

def test_specific_document_with_images():
    """測試特定包含圖片的文檔"""
    
    print("\n" + "=" * 80)
    print("🔍 檢查資料庫中有圖片的文檔")
    print("=" * 80)
    
    from api.models import ProtocolGuide
    
    # 找出有圖片的文檔
    docs_with_images = []
    for doc in ProtocolGuide.objects.all():
        if hasattr(doc, 'has_images') and doc.has_images():
            image_count = doc.get_image_count()
            image_summary = doc.get_images_summary()
            docs_with_images.append({
                'id': doc.id,
                'title': doc.title,
                'image_count': image_count,
                'summary': image_summary
            })
            print(f"\n📄 ID: {doc.id}")
            print(f"   標題: {doc.title}")
            print(f"   圖片數量: {image_count}")
            print(f"   圖片摘要: {image_summary}")
    
    if not docs_with_images:
        print("\n⚠️  資料庫中沒有包含圖片的文檔")
        print("提示：請先透過後台或 API 上傳包含圖片的 Protocol Guide 文檔")
    else:
        print(f"\n✅ 找到 {len(docs_with_images)} 個包含圖片的文檔")
        
        # 針對有圖片的文檔進行搜尋測試
        if docs_with_images:
            test_doc = docs_with_images[0]
            print(f"\n🧪 針對文檔「{test_doc['title']}」進行搜尋測試")
            
            search_service = ProtocolGuideSearchService()
            
            # 使用文檔標題的關鍵字進行搜尋
            title_keywords = test_doc['title'].split()[:3]
            query = " ".join(title_keywords)
            
            print(f"   查詢關鍵字: {query}")
            
            results = search_service.semantic_search(
                query=query,
                top_k=1,
                threshold=0.5
            )
            
            if results:
                result = results[0]
                content = result.get('content', '')
                
                print(f"\n   搜尋結果:")
                print(f"   相似度: {result.get('score', 0):.2%}")
                
                if '包含' in content and '張圖片' in content:
                    print(f"   ✅ 圖片資訊已成功包含在搜尋結果中")
                else:
                    print(f"   ❌ 圖片資訊未包含（修復失敗）")
                
                print(f"\n   完整內容:")
                print(f"   {content}")
            else:
                print(f"   ⚠️  未找到搜尋結果")
    
    print("\n" + "=" * 80)

if __name__ == '__main__':
    print("\n🚀 開始測試圖片資訊修復...")
    print("=" * 80)
    
    # 測試 1: 一般段落搜尋
    test_image_metadata_in_section_search()
    
    # 測試 2: 特定有圖片的文檔
    test_specific_document_with_images()
    
    print("\n" + "=" * 80)
    print("🎉 所有測試完成")
    print("=" * 80)
