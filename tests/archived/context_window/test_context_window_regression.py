#!/usr/bin/env python3
"""
上下文视窗扩展回归测试

用途：快速验证核心功能是否正常
执行时间：< 30 秒
适用场景：代码修改后的快速验证

执行方式：
    docker exec ai-django python test_context_window_regression.py
"""

import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.common.knowledge_base.section_search_service import SectionSearchService
from library.protocol_guide.search_service import ProtocolGuideSearchService


def test_basic_functionality():
    """基本功能快速检查"""
    print("🧪 上下文视窗扩展回归测试\n")
    
    service = SectionSearchService()
    results = {
        'adjacent': False,
        'hierarchical': False,
        'both': False,
        'child_expansion': False
    }
    
    try:
        # 测试 1: Adjacent Mode
        print("1. 测试 Adjacent Mode... ", end='')
        r1 = service.search_with_context(
            query="IOL 测试",
            source_table='protocol_guide',
            context_mode='adjacent',
            context_window=1,
            limit=1
        )
        results['adjacent'] = len(r1) > 0
        print("✅" if results['adjacent'] else "❌")
        
        # 测试 2: Hierarchical Mode
        print("2. 测试 Hierarchical Mode... ", end='')
        r2 = service.search_with_context(
            query="IOL 测试",
            source_table='protocol_guide',
            context_mode='hierarchical',
            include_siblings=True,
            limit=1
        )
        results['hierarchical'] = len(r2) > 0
        print("✅" if results['hierarchical'] else "❌")
        
        # 测试 3: Both Mode
        print("3. 测试 Both Mode... ", end='')
        r3 = service.search_with_context(
            query="IOL 测试",
            source_table='protocol_guide',
            context_mode='both',
            context_window=1,
            include_siblings=True,
            limit=1
        )
        results['both'] = len(r3) > 0
        print("✅" if results['both'] else "❌")
        
        # 测试 4: Child Expansion
        print("4. 测试 Child Expansion... ", end='')
        ps = ProtocolGuideSearchService()
        r4 = ps.search_knowledge("IOL 放测 SOP", limit=1)
        has_content = len(r4) > 0 and len(r4[0]['content']) > 200
        results['child_expansion'] = has_content
        print("✅" if has_content else "❌")
        
        # 总结
        passed = sum(results.values())
        total = len(results)
        
        print(f"\n{'='*50}")
        print(f"结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
        print(f"{'='*50}")
        
        if passed == total:
            print("✅ 所有功能正常")
            return True
        else:
            print("❌ 部分功能异常")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = test_basic_functionality()
    sys.exit(0 if success else 1)
