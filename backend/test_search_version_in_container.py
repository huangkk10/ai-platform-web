#!/usr/bin/env python
"""
Django 容器內搜尋版本切換功能測試
在容器內直接測試 Django 組件
"""

import os
import sys
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

print("=" * 80)
print("  搜尋版本切換功能 - Django 容器測試")
print("=" * 80)

# 1. 測試導入
print("\n1️⃣ 測試模組導入...")
try:
    from api.views.viewsets.knowledge_viewsets import RVTGuideViewSet
    from library.common.knowledge_base.section_search_service import SectionSearchService
    from api.models import RVTGuide
    print("✅ 所有必要模組導入成功")
except Exception as e:
    print(f"❌ 導入失敗: {e}")
    sys.exit(1)

# 2. 測試 SectionSearchService 方法
print("\n2️⃣ 檢查 SectionSearchService 可用方法...")
service = SectionSearchService()

# 檢查關鍵方法
key_methods = {
    'search_sections': 'V1 基礎搜尋方法',
    'search_sections_with_expanded_context': 'V2 上下文增強搜尋方法',
    'search_with_context': '舊版上下文搜尋方法'
}

for method, description in key_methods.items():
    if hasattr(service, method):
        print(f"  ✅ {method} - {description}")
    else:
        print(f"  ❌ {method} - {description} (不存在)")

# 3. 檢查 RVT Guide 資料
print("\n3️⃣ 檢查 RVT Guide 資料...")
try:
    count = RVTGuide.objects.count()
    print(f"📊 RVT Guide 總數量: {count}")
    
    if count > 0:
        # 顯示前 3 筆
        guides = RVTGuide.objects.all()[:3]
        print(f"\n前 3 筆資料:")
        for i, guide in enumerate(guides, 1):
            title = guide.title[:50] + "..." if len(guide.title) > 50 else guide.title
            print(f"  {i}. [{guide.id}] {title}")
    else:
        print("⚠️  資料庫中沒有 RVT Guide 資料")
        print("   提示: 需要先在前端創建一些 RVT Guide 資料")
        
except Exception as e:
    print(f"❌ 查詢失敗: {e}")
    count = 0

# 4. 測試 V1 搜尋
print("\n4️⃣ 測試 V1 基礎搜尋...")
if count > 0:
    try:
        import time
        start_time = time.time()
        
        results = service.search_sections(
            query="測試",
            source_table='rvt_guide',
            limit=3,
            threshold=0.3  # 降低閾值以獲得更多結果
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ V1 搜尋完成")
        print(f"  - 執行時間: {elapsed:.0f}ms")
        print(f"  - 找到結果: {len(results)} 個")
        
        if results:
            print(f"\n  前 {min(3, len(results))} 個結果:")
            for i, result in enumerate(results[:3], 1):
                title = result.get('heading_text', 'N/A')[:40]
                similarity = result.get('similarity', 0)
                print(f"    {i}. [{similarity:.2%}] {title}")
        else:
            print("  ⚠️  沒有找到匹配結果（可能需要調整查詢或閾值）")
            
    except Exception as e:
        print(f"❌ V1 搜尋失敗: {e}")
        import traceback
        traceback.print_exc()
else:
    print("⏭️  跳過（無資料）")

# 5. 測試 V2 搜尋
print("\n5️⃣ 測試 V2 上下文增強搜尋...")
if count > 0 and hasattr(service, 'search_sections_with_expanded_context'):
    try:
        import time
        start_time = time.time()
        
        results = service.search_sections_with_expanded_context(
            query="測試",
            source_table='rvt_guide',
            limit=3,
            threshold=0.3,
            context_window=1,
            context_mode='adjacent'
        )
        
        elapsed = (time.time() - start_time) * 1000
        
        print(f"✅ V2 搜尋完成")
        print(f"  - 執行時間: {elapsed:.0f}ms")
        print(f"  - 找到結果: {len(results)} 個")
        
        if results:
            print(f"\n  前 {min(3, len(results))} 個結果:")
            for i, result in enumerate(results[:3], 1):
                title = result.get('heading_text', 'N/A')[:40]
                similarity = result.get('similarity', 0)
                has_context = result.get('has_context', False)
                context_info = result.get('context', {})
                
                print(f"    {i}. [{similarity:.2%}] {title}")
                print(f"        包含上下文: {'✅ 是' if has_context else '❌ 否'}")
                
                if has_context and context_info:
                    ctx_parts = []
                    if context_info.get('previous'):
                        ctx_parts.append("前段落")
                    if context_info.get('next'):
                        ctx_parts.append("後段落")
                    if context_info.get('parent'):
                        ctx_parts.append("父段落")
                    if ctx_parts:
                        print(f"        上下文類型: {', '.join(ctx_parts)}")
        else:
            print("  ⚠️  沒有找到匹配結果")
            
    except Exception as e:
        print(f"❌ V2 搜尋失敗: {e}")
        import traceback
        traceback.print_exc()
elif not hasattr(service, 'search_sections_with_expanded_context'):
    print("❌ search_sections_with_expanded_context 方法不存在")
    print("   可能的原因:")
    print("   1. SectionSearchService 尚未實作此方法")
    print("   2. Library 路徑不正確")
    print("   3. 方法名稱拼寫錯誤")
else:
    print("⏭️  跳過（無資料）")

# 6. 測試 ViewSet 的 search_sections action
print("\n6️⃣ 測試 ViewSet search_sections action...")
try:
    from django.test import RequestFactory
    from rest_framework.test import force_authenticate
    from django.contrib.auth.models import User
    
    # 創建測試請求
    factory = RequestFactory()
    
    # 獲取或創建測試用戶
    user, created = User.objects.get_or_create(
        username='test_user',
        defaults={'email': 'test@example.com'}
    )
    
    # 測試 V1
    print("\n  測試 V1 請求...")
    request = factory.post('/api/rvt-guides/search_sections/', {
        'query': '測試',
        'version': 'v1',
        'limit': 2,
        'threshold': 0.3
    }, content_type='application/json')
    force_authenticate(request, user=user)
    
    viewset = RVTGuideViewSet()
    viewset.request = request
    
    try:
        response = viewset.search_sections(request)
        print(f"  ✅ V1 API 回應狀態: {response.status_code}")
        if response.status_code == 200:
            data = response.data
            print(f"     - 版本: {data.get('version')}")
            print(f"     - 結果數量: {data.get('total')}")
            print(f"     - 執行時間: {data.get('execution_time')}")
    except Exception as e:
        print(f"  ❌ V1 API 測試失敗: {e}")
    
    # 測試 V2
    print("\n  測試 V2 請求...")
    request = factory.post('/api/rvt-guides/search_sections/', {
        'query': '測試',
        'version': 'v2',
        'limit': 2,
        'threshold': 0.3,
        'context_window': 1,
        'context_mode': 'adjacent'
    }, content_type='application/json')
    force_authenticate(request, user=user)
    
    viewset = RVTGuideViewSet()
    viewset.request = request
    
    try:
        response = viewset.search_sections(request)
        print(f"  ✅ V2 API 回應狀態: {response.status_code}")
        if response.status_code == 200:
            data = response.data
            print(f"     - 版本: {data.get('version')}")
            print(f"     - 結果數量: {data.get('total')}")
            print(f"     - 執行時間: {data.get('execution_time')}")
    except Exception as e:
        print(f"  ❌ V2 API 測試失敗: {e}")
    
except Exception as e:
    print(f"❌ ViewSet 測試失敗: {e}")
    import traceback
    traceback.print_exc()

# 總結
print("\n" + "=" * 80)
print("  測試總結")
print("=" * 80)

print("\n✅ 測試完成！")
print("\n📝 下一步:")
print("  1. 如果所有測試通過，可以在瀏覽器中測試前端 UI")
print("  2. 訪問: http://localhost/rvt-chat")
print("  3. 檢查輸入框上方是否顯示版本切換開關")
print("  4. 嘗試切換 V1/V2 並發送測試訊息")
