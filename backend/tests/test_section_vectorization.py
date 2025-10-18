"""
Protocol Guide 段落向量生成測試

為所有 Protocol Guide 生成段落向量。
"""

import os
import django

# Django 設置
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService


def generate_section_vectors_for_all_guides():
    """為所有 Protocol Guide 生成段落向量"""
    
    service = SectionVectorizationService()
    
    # 獲取所有 Protocol Guide
    guides = ProtocolGuide.objects.all()
    
    print("\n" + "="*70)
    print("開始為 Protocol Guide 生成段落向量")
    print("="*70 + "\n")
    
    total_docs = 0
    total_sections = 0
    total_vectorized = 0
    failed_docs = []
    
    for guide in guides:
        total_docs += 1
        
        print(f"\n📄 處理文檔 {guide.id}: {guide.title}")
        print("-" * 70)
        
        try:
            # 生成段落向量
            result = service.vectorize_document_sections(
                source_table='protocol_guide',
                source_id=guide.id,
                markdown_content=guide.content,
                document_title=guide.title
            )
            
            if result['success']:
                sections_count = result['total_sections']
                vectorized_count = result['vectorized_count']
                
                total_sections += sections_count
                total_vectorized += vectorized_count
                
                print(f"  ✅ 解析出 {sections_count} 個段落")
                print(f"  ✅ 成功生成 {vectorized_count} 個向量")
                
                # 顯示段落詳情
                if result['sections']:
                    print(f"\n  段落列表:")
                    for i, section in enumerate(result['sections'], 1):
                        print(f"    {i}. [{section.section_id}] "
                              f"{'#' * section.level} {section.title}")
                        print(f"       路徑: {section.path}")
                        print(f"       內容長度: {section.word_count} 字元")
                        if section.has_code:
                            print(f"       包含代碼: ✅")
                        if section.has_images:
                            print(f"       包含圖片: ✅")
            else:
                print(f"  ❌ 向量化失敗: {result.get('error', '未知錯誤')}")
                failed_docs.append((guide.id, guide.title))
                
        except Exception as e:
            print(f"  ❌ 處理失敗: {str(e)}")
            failed_docs.append((guide.id, guide.title))
            import traceback
            traceback.print_exc()
    
    # 統計報告
    print("\n" + "="*70)
    print("📊 統計報告")
    print("="*70)
    print(f"處理文檔數: {total_docs}")
    print(f"總段落數: {total_sections}")
    print(f"成功向量化: {total_vectorized}")
    print(f"成功率: {(total_vectorized / total_sections * 100) if total_sections > 0 else 0:.1f}%")
    
    if failed_docs:
        print(f"\n❌ 失敗文檔 ({len(failed_docs)}):")
        for doc_id, title in failed_docs:
            print(f"  - [{doc_id}] {title}")
    else:
        print(f"\n✅ 所有文檔處理成功！")
    
    print("="*70 + "\n")


if __name__ == "__main__":
    generate_section_vectors_for_all_guides()
