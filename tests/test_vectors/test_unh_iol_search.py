"""
测试 UNH-IOL 搜索
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService
from api.models import ProtocolGuide

def test_unh_iol_search():
    """测试 UNH-IOL 搜索"""
    
    print("=" * 80)
    print("🔍 UNH-IOL 搜索测试")
    print("=" * 80)
    print()
    
    # 初始化搜索服务
    search_service = SectionSearchService()
    
    # 测试查询
    test_queries = [
        "iol 如何放測",
        "IOL 測試",
        "UNH-IOL 放測流程",
        "IOL 執行檔",
    ]
    
    for query in test_queries:
        print(f"\n{'─'*80}")
        print(f"📋 查询: \"{query}\"")
        print(f"{'─'*80}")
        
        try:
            results = search_service.search_sections(
                query=query,
                source_table='protocol_guide',
                limit=5,
                threshold=0.7
            )
            
            print(f"找到 {len(results)} 个结果：\n")
            
            # 检查 UNH-IOL 是否在结果中
            unh_iol_rank = None
            
            for i, result in enumerate(results, 1):
                source_id = result.get('source_id')
                guide = ProtocolGuide.objects.get(id=source_id)
                
                is_unh_iol = (guide.title == 'UNH-IOL')
                symbol = "✅" if is_unh_iol else "  "
                
                print(f"{symbol} 结果 {i}:")
                print(f"    文档: {guide.title}")
                print(f"    段落: {result.get('section_id')} - {result.get('heading_text')}")
                print(f"    相似度: {result.get('similarity', 0):.2%}")
                
                if is_unh_iol and unh_iol_rank is None:
                    unh_iol_rank = i
                
                print()
            
            # 显示 UNH-IOL 排名
            if unh_iol_rank:
                print(f"🎯 UNH-IOL 排名: #{unh_iol_rank}")
            else:
                print(f"⚠️  UNH-IOL 不在前 5 名结果中")
            
        except Exception as e:
            print(f"❌ 搜索失败: {str(e)}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 80)
    print("✅ 测试完成")
    print("=" * 80)

if __name__ == '__main__':
    test_unh_iol_search()
