"""
深度分析：为什么 UNH-IOL 搜索不到
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService
from api.services.embedding_service import get_embedding_service
from api.models import ProtocolGuide

def analyze_unh_iol_search():
    """分析为什么 UNH-IOL 搜索不到"""
    
    print("=" * 80)
    print("🔍 UNH-IOL 搜索失败深度分析")
    print("=" * 80)
    print()
    
    # 初始化服务
    search_service = SectionSearchService()
    embedding_service = get_embedding_service()
    
    # 查询文本
    query = "iol 如何放測"
    
    print(f"📋 查询文本: \"{query}\"")
    print()
    
    # 步骤 1：生成查询向量
    print("步骤 1：生成查询向量")
    print("-" * 80)
    query_embedding = embedding_service.generate_embedding(query)
    print(f"✅ 查询向量维度: {len(query_embedding)}")
    print(f"✅ 向量前 5 个值: {query_embedding[:5]}")
    print()
    
    # 步骤 2：获取 UNH-IOL 的所有段落向量
    print("步骤 2：获取 UNH-IOL 的所有段落")
    print("-" * 80)
    
    from django.db import connection
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                id,
                section_id,
                heading_text,
                LENGTH(content) as content_len,
                SUBSTRING(content, 1, 100) as content_preview
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = 10
            ORDER BY section_id
        """)
        unh_sections = cursor.fetchall()
    
    print(f"找到 {len(unh_sections)} 个 UNH-IOL 段落：")
    for sec in unh_sections:
        sec_id, section_id, heading, content_len, preview = sec
        print(f"  - {section_id}: {heading} ({content_len} 字元)")
    print()
    
    # 步骤 3：手动计算相似度
    print("步骤 3：手动计算每个段落与查询的相似度")
    print("-" * 80)
    
    import numpy as np
    from numpy.linalg import norm
    
    def cosine_similarity(a, b):
        return np.dot(a, b) / (norm(a) * norm(b))
    
    # 获取 UNH-IOL 段落的向量
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                LENGTH(content) as content_len,
                embedding
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = 10
            ORDER BY section_id
        """)
        sections_with_vectors = cursor.fetchall()
    
    print("UNH-IOL 各段落的相似度：")
    print()
    
    similarities = []
    for section_id, heading, content_len, embedding_bytes in sections_with_vectors:
        # 将 pgvector 格式转换为 numpy 数组
        embedding_str = embedding_bytes.strip('[]')
        embedding_vec = np.array([float(x) for x in embedding_str.split(',')])
        
        # 计算相似度
        similarity = cosine_similarity(query_embedding, embedding_vec)
        similarities.append((section_id, heading, content_len, similarity))
        
        print(f"  {section_id}: {heading}")
        print(f"    内容长度: {content_len} 字元")
        print(f"    相似度: {similarity:.4f} ({similarity*100:.2f}%)")
        print()
    
    # 找出最高相似度
    max_similarity = max(similarities, key=lambda x: x[3])
    print(f"✅ UNH-IOL 最高相似度: {max_similarity[3]:.4f} ({max_similarity[3]*100:.2f}%)")
    print(f"   段落: {max_similarity[0]} - {max_similarity[1]}")
    print()
    
    # 步骤 4：对比其他文档的相似度
    print("步骤 4：对比其他文档（前 5 名结果）")
    print("-" * 80)
    
    results = search_service.search_sections(
        query=query,
        source_table='protocol_guide',
        limit=10,
        threshold=0.0  # 降低阈值，看所有结果
    )
    
    print(f"搜索到 {len(results)} 个结果：")
    print()
    
    unh_iol_rank = None
    for i, result in enumerate(results, 1):
        source_id = result.get('source_id')
        guide = ProtocolGuide.objects.get(id=source_id)
        similarity = result.get('similarity', 0)
        
        is_unh = (source_id == 10)
        symbol = "✅" if is_unh else "  "
        
        print(f"{symbol} #{i}: {guide.title}")
        print(f"     段落: {result.get('section_id')} - {result.get('heading_text')}")
        print(f"     相似度: {similarity:.4f} ({similarity*100:.2f}%)")
        
        if is_unh and unh_iol_rank is None:
            unh_iol_rank = i
        print()
    
    if unh_iol_rank:
        print(f"🎯 UNH-IOL 排名: #{unh_iol_rank}")
    else:
        print(f"❌ UNH-IOL 不在搜索结果中")
    print()
    
    # 步骤 5：分析阈值问题
    print("步骤 5：分析阈值问题")
    print("-" * 80)
    
    threshold = 0.7
    print(f"当前搜索阈值: {threshold} ({threshold*100}%)")
    print(f"UNH-IOL 最高相似度: {max_similarity[3]:.4f} ({max_similarity[3]*100:.2f}%)")
    
    if max_similarity[3] < threshold:
        print(f"❌ UNH-IOL 最高相似度 < 阈值")
        print(f"   差距: {(threshold - max_similarity[3])*100:.2f}%")
        print()
        print("🔍 原因分析：")
        print("   1. 查询文本 '放測' 可能不常见于 UNH-IOL 文档")
        print("   2. UNH-IOL 段落内容较短（平均 101 字元）")
        print("   3. 其他文档（Burn in Test, I3C）内容更详细")
    else:
        print(f"✅ UNH-IOL 相似度 >= 阈值，应该会被找到")
    
    print()
    print("=" * 80)
    print("分析完成")
    print("=" * 80)

if __name__ == '__main__':
    analyze_unh_iol_search()
