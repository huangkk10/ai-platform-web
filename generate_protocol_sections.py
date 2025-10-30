#!/usr/bin/env python3
"""
為 Protocol Guide 生成段落向量
================================

此腳本會為所有現有的 Protocol Guide 文檔生成段落向量，
提升搜尋精準度，實現段落級別的語義搜尋。

使用方式：
    docker exec ai-django python generate_protocol_sections.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
from api.models import ProtocolGuide
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def generate_sections_for_all_guides():
    """為所有 Protocol Guide 生成段落向量"""
    
    print("=" * 70)
    print("🚀 Protocol Guide 段落向量生成工具")
    print("=" * 70)
    print()
    
    # 初始化服務
    service = SectionVectorizationService()
    
    # 獲取所有 Protocol Guide
    guides = ProtocolGuide.objects.all()
    total_guides = guides.count()
    
    print(f"📊 找到 {total_guides} 篇 Protocol Guide")
    print()
    
    if total_guides == 0:
        print("⚠️  沒有找到任何 Protocol Guide，程式結束")
        return
    
    # 統計變數
    success_count = 0
    fail_count = 0
    total_sections = 0
    
    # 處理每一篇文檔
    for i, guide in enumerate(guides, 1):
        print(f"\n{'='*70}")
        print(f"📝 處理第 {i}/{total_guides} 篇")
        print(f"{'='*70}")
        print(f"ID: {guide.id}")
        print(f"標題: {guide.title}")
        print(f"內容長度: {len(guide.content) if guide.content else 0} 字元")
        print()
        
        try:
            # 生成段落向量
            print("⏳ 開始生成段落向量...")
            
            result = service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=guide.id,
                markdown_content=guide.content,
                document_title=guide.title
            )
            
            section_count = result.get('vectorized_count', 0)
            
            print(f"✅ 成功生成 {section_count} 個段落向量")
            success_count += 1
            total_sections += section_count
            
        except Exception as e:
            print(f"❌ 生成失敗: {str(e)}")
            logger.exception(f"處理 Protocol Guide {guide.id} 時發生錯誤")
            fail_count += 1
    
    # 最終統計
    print("\n" + "=" * 70)
    print("📊 生成結果統計")
    print("=" * 70)
    print(f"✅ 成功: {success_count}/{total_guides} 篇文檔")
    print(f"❌ 失敗: {fail_count}/{total_guides} 篇文檔")
    print(f"📄 總共生成: {total_sections} 個段落向量")
    print("=" * 70)
    print()
    
    if success_count > 0:
        print("🎉 段落向量生成完成！")
        print()
        print("💡 下一步：")
        print("   1. 驗證段落向量資料")
        print("   2. 測試段落搜尋效果")
        print("   3. 使用 Protocol Assistant 測試實際效果")
        print()
    else:
        print("⚠️  沒有成功生成任何段落向量，請檢查錯誤訊息")
        print()


def verify_sections():
    """驗證段落向量是否生成成功"""
    from django.db import connection
    
    print("\n" + "=" * 70)
    print("🔍 驗證段落向量資料")
    print("=" * 70)
    print()
    
    with connection.cursor() as cursor:
        # 查詢段落向量統計
        cursor.execute("""
            SELECT 
                COUNT(*) as total_sections,
                COUNT(DISTINCT source_id) as unique_docs,
                MIN(word_count) as min_words,
                MAX(word_count) as max_words,
                AVG(word_count)::int as avg_words
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide';
        """)
        
        row = cursor.fetchone()
        if row:
            total_sections, unique_docs, min_words, max_words, avg_words = row
            
            print(f"📊 統計資料：")
            print(f"   - 段落總數: {total_sections}")
            print(f"   - 文檔數量: {unique_docs}")
            print(f"   - 最少字數: {min_words}")
            print(f"   - 最多字數: {max_words}")
            print(f"   - 平均字數: {avg_words}")
            print()
            
            if total_sections > 0:
                print("✅ 段落向量資料存在")
                
                # 顯示每個文檔的段落數
                cursor.execute("""
                    SELECT 
                        source_id,
                        COUNT(*) as section_count
                    FROM document_section_embeddings
                    WHERE source_table = 'protocol_guide'
                    GROUP BY source_id
                    ORDER BY source_id;
                """)
                
                print("\n📄 各文檔段落數：")
                for doc_id, count in cursor.fetchall():
                    print(f"   - 文檔 ID {doc_id}: {count} 個段落")
                
            else:
                print("⚠️  沒有找到任何段落向量資料")
        
        print()


if __name__ == '__main__':
    try:
        # 生成段落向量
        generate_sections_for_all_guides()
        
        # 驗證結果
        verify_sections()
        
        print("✅ 程式執行完成")
        
    except KeyboardInterrupt:
        print("\n⚠️  使用者中斷程式")
    except Exception as e:
        print(f"\n❌ 程式執行失敗: {str(e)}")
        logger.exception("程式執行過程中發生錯誤")
