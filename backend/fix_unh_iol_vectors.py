"""
为 UNH-IOL 文档生成段落向量的修复脚本
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from library.common.knowledge_base.section_vectorization_service import SectionVectorizationService
import logging

logger = logging.getLogger(__name__)

def fix_unh_iol_vectors():
    """为 UNH-IOL 文档生成段落向量"""
    
    print("=" * 80)
    print("🔧 UNH-IOL 段落向量修复脚本")
    print("=" * 80)
    print()
    
    # 步骤 1：检查 UNH-IOL 文档是否存在
    print("📋 步骤 1：检查 UNH-IOL 文档...")
    try:
        guide = ProtocolGuide.objects.get(title='UNH-IOL')
        print(f"✅ 找到文档：{guide.title}")
        print(f"   文档 ID: {guide.id}")
        print(f"   内容长度: {len(guide.content)} 字元")
        print(f"   创建时间: {guide.created_at}")
        print()
    except ProtocolGuide.DoesNotExist:
        print("❌ 错误：找不到 UNH-IOL 文档")
        return False
    
    # 步骤 2：检查现有段落向量
    print("📋 步骤 2：检查现有段落向量...")
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM document_section_embeddings 
            WHERE source_table = 'protocol_guide' AND source_id = %s
        """, [guide.id])
        existing_count = cursor.fetchone()[0]
    
    print(f"   现有段落向量数: {existing_count}")
    if existing_count > 0:
        print("   ⚠️  警告：已存在段落向量，将重新生成")
        # 删除现有向量
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM document_section_embeddings 
                WHERE source_table = 'protocol_guide' AND source_id = %s
            """, [guide.id])
        print(f"   ✅ 已删除 {existing_count} 个旧向量")
    print()
    
    # 步骤 3：初始化段落向量服务
    print("📋 步骤 3：初始化段落向量服务...")
    try:
        section_service = SectionVectorizationService()
        print("✅ 段落向量服务初始化成功")
        print()
    except Exception as e:
        print(f"❌ 错误：段落向量服务初始化失败 - {str(e)}")
        return False
    
    # 步骤 4：生成段落向量
    print("📋 步骤 4：生成段落向量...")
    print("   ⏳ 正在处理...")
    print()
    
    try:
        result = section_service.vectorize_document_sections(
            source_table='protocol_guide',
            source_id=guide.id,
            markdown_content=guide.content,
            document_title=guide.title
        )
        
        if result['success']:
            vectorized_count = result.get('vectorized_count', 0)
            print("✅ 段落向量生成成功！")
            print()
            print("📊 生成结果：")
            print(f"   - 总段落数: {vectorized_count}")
            print()
            
            if result.get('sections', []):
                print("📝 段落详情：")
                for i, section in enumerate(result.get('sections', []), 1):
                    print(f"   {i}. {section.get('section_id', '')} - {section.get('heading_text', '')[:50]}")
                print()
        else:
            error = result.get('error', '未知错误')
            print(f"❌ 错误：段落向量生成失败 - {error}")
            return False
        
    except Exception as e:
        print(f"❌ 错误：段落向量生成失败 - {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 步骤 5：验证生成结果
    print("📋 步骤 5：验证生成结果...")
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_length,
                vector_dims(embedding) as vector_dim
            FROM document_section_embeddings 
            WHERE source_table = 'protocol_guide' AND source_id = %s
            ORDER BY section_id
        """, [guide.id])
        vectors = cursor.fetchall()
    
    if vectors:
        print(f"✅ 验证通过：找到 {len(vectors)} 个段落向量")
        print()
        print("📋 段落向量列表：")
        for vector in vectors:
            section_id, heading, content_len, vector_dim = vector
            print(f"   - {section_id}: {heading}")
            print(f"     内容: {content_len} 字元, 向量: {vector_dim} 维")
        print()
    else:
        print("❌ 验证失败：没有找到生成的段落向量")
        return False
    
    # 步骤 6：测试搜索
    print("📋 步骤 6：测试搜索功能...")
    from library.common.knowledge_base.section_search_service import SectionSearchService
    
    search_service = SectionSearchService()
    test_query = "iol 如何放測"
    
    print(f"   查询: \"{test_query}\"")
    print("   ⏳ 正在搜索...")
    
    try:
        results = search_service.search_sections(
            query=test_query,
            source_table='protocol_guide',
            limit=5,
            threshold=0.7
        )
        
        print(f"✅ 搜索完成，找到 {len(results)} 个结果")
        print()
        
        # 检查 UNH-IOL 是否在结果中
        unh_iol_found = False
        for i, result in enumerate(results, 1):
            print(f"   结果 {i}:")
            print(f"      文档 ID: {result.get('source_id')}")
            print(f"      段落: {result.get('section_id')} - {result.get('heading_text')}")
            print(f"      相似度: {result.get('similarity', 0):.2%}")
            
            if result.get('source_id') == guide.id:
                print("      ✅ 这是 UNH-IOL 文档！")
                unh_iol_found = True
            print()
        
        if unh_iol_found:
            print("🎉 成功！UNH-IOL 文档现在可以被搜索到了！")
        else:
            print("⚠️  警告：搜索结果中没有 UNH-IOL，可能需要调整阈值")
        
    except Exception as e:
        print(f"❌ 搜索测试失败 - {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("=" * 80)
    print("✅ 修复完成！")
    print("=" * 80)
    
    return True

if __name__ == '__main__':
    try:
        success = fix_unh_iol_vectors()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 脚本执行失败：{str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
