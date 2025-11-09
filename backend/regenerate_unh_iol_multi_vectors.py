#!/usr/bin/env python
"""
重新为 UNH-IOL 生成多向量（标题 + 内容分离向量）
解决搜索无法找到 UNH-IOL 的问题
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.protocol_guide.vector_service import ProtocolGuideVectorService
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService

def main():
    print("=" * 80)
    print("为 UNH-IOL 重新生成多向量（标题 + 内容分离）")
    print("=" * 80)
    
    # Step 1: 获取 UNH-IOL 文档
    print("\n📂 Step 1: 获取 UNH-IOL 文档...")
    try:
        guide = ProtocolGuide.objects.get(id=10)
        print(f"✅ 找到文档: {guide.title} (ID: {guide.id})")
        print(f"   内容长度: {len(guide.content)} 字符")
    except ProtocolGuide.DoesNotExist:
        print("❌ 错误: 找不到 ID=10 的文档")
        return
    
    # Step 2: 检查当前向量状态
    print("\n📊 Step 2: 检查当前向量...")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_len,
                CASE WHEN title_embedding IS NOT NULL THEN 'YES' ELSE 'NO' END as has_title_vec,
                CASE WHEN content_embedding IS NOT NULL THEN 'YES' ELSE 'NO' END as has_content_vec
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = 10
            ORDER BY section_id;
        """)
        rows = cursor.fetchall()
        
        print(f"   找到 {len(rows)} 个段落")
        no_multi_vec = 0
        for row in rows:
            section_id, heading, content_len, has_title, has_content = row
            if has_title == 'NO' or has_content == 'NO':
                no_multi_vec += 1
                print(f"   ⚠️  {section_id}: {heading[:40]}... - 标题向量:{has_title}, 内容向量:{has_content}")
        
        print(f"\n   总结: {no_multi_vec}/{len(rows)} 个段落缺少多向量")
    
    # Step 3: 删除旧向量
    print("\n🗑️  Step 3: 删除旧的单一向量...")
    with connection.cursor() as cursor:
        cursor.execute("""
            DELETE FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = 10;
        """)
        deleted_count = cursor.rowcount
        print(f"✅ 已删除 {deleted_count} 个旧向量")
    
    # Step 4: 使用新的多向量服务重新生成
    print("\n🔄 Step 4: 使用 SectionVectorizationService 重新生成多向量...")
    try:
        service = SectionVectorizationService()
        
        # 调用向量化服务
        result = service.vectorize_document_sections(
            source_table='protocol_guide',
            source_id=guide.id,
            markdown_content=guide.content,
            document_title=guide.title
        )
        
        print(f"✅ 向量生成成功!")
        print(f"   成功: {result['success_count']} 个段落")
        print(f"   失败: {result['failed_count']} 个段落")
        
        if result['failed_sections']:
            print("\n⚠️  失败的段落:")
            for section_id, error in result['failed_sections']:
                print(f"   - {section_id}: {error}")
        
    except Exception as e:
        print(f"❌ 向量生成失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 5: 验证多向量是否生成成功
    print("\n✅ Step 5: 验证多向量...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_len,
                vector_dims(title_embedding) as title_dim,
                vector_dims(content_embedding) as content_dim
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = 10
            ORDER BY section_id;
        """)
        rows = cursor.fetchall()
        
        print(f"   找到 {len(rows)} 个段落（应该与之前相同）")
        success_count = 0
        for row in rows:
            section_id, heading, content_len, title_dim, content_dim = row
            if title_dim == 1024 and content_dim == 1024:
                success_count += 1
                print(f"   ✅ {section_id}: 标题 {title_dim}维, 内容 {content_dim}维")
            else:
                print(f"   ❌ {section_id}: 标题 {title_dim}维, 内容 {content_dim}维 (应该都是 1024)")
        
        print(f"\n   总结: {success_count}/{len(rows)} 个段落有完整的多向量")
    
    # Step 6: 测试搜索
    print("\n🔍 Step 6: 测试搜索是否能找到 UNH-IOL...")
    from library.common.knowledge_base.section_search_service import SectionSearchService
    
    search_service = SectionSearchService()
    query = "iol 如何放測"
    
    print(f"\n   搜索查询: '{query}'")
    results = search_service.search_sections(
        query=query,
        source_table='protocol_guide',
        limit=10,
        threshold=0.7
    )
    
    print(f"\n   搜索结果 (阈值: 0.7):")
    unh_iol_found = False
    for i, result in enumerate(results, 1):
        is_unh_iol = result['source_id'] == 10
        marker = "🎯" if is_unh_iol else "  "
        print(f"{marker} #{i}: {result['document_title'][:30]:30} | {result['section_id']:8} | {result['similarity']:.4f} | {result['heading_text'][:40]}")
        if is_unh_iol:
            unh_iol_found = True
    
    if unh_iol_found:
        print("\n✅✅✅ 成功! UNH-IOL 现在出现在搜索结果中!")
    else:
        print("\n❌ UNH-IOL 仍然不在搜索结果中...")
        print("   可能需要进一步调查搜索服务配置")
    
    print("\n" + "=" * 80)
    print("完成!")
    print("=" * 80)

if __name__ == '__main__':
    main()
