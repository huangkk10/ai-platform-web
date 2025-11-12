#!/usr/bin/env python
"""
测试 CrystalDiskMark 向量搜索
"""
import os
import sys
import django

# 设置 Django 环境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.protocol_guide.search_service import ProtocolGuideSearchService

def test_crystaldiskmark_search():
    """测试 CrystalDiskMark 搜索"""
    search_service = ProtocolGuideSearchService()
    
    test_queries = [
        'crystaldiskmark',
        'CrystalDiskMark',
        'crystal disk mark',
        'diskmark',
    ]
    
    print("=" * 80)
    print("🔍 测试 CrystalDiskMark 搜索（使用 search_knowledge）")
    print("=" * 80)
    
    for query in test_queries:
        print(f"\n📝 查询: '{query}'")
        print("-" * 80)
        
        try:
            # 使用 search_knowledge 方法（启用向量搜索）
            results = search_service.search_knowledge(
                query=query,
                limit=3,
                use_vector=True,
                threshold=0.3  # 降低阈值以获取更多结果
            )
            
            print(f"✅ 找到 {len(results)} 个结果\n")
            
            for i, result in enumerate(results, 1):
                print(f"  结果 {i}:")
                print(f"    相似度: {result.get('similarity', 0):.2%}")
                print(f"    文档 ID: {result.get('id')}")
                print(f"    标题: {result.get('title', 'N/A')}")
                print(f"    内容预览: {result.get('content', '')[:100]}...")
                print()
        
        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✨ 测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_crystaldiskmark_search()
