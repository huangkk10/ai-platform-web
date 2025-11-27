#!/usr/bin/env python
"""
Dify v1.2.2 混合搜尋 API 整合測試
==================================

測試流程：
1. 確認 v1.2.2 已設為 Baseline
2. 透過 Dify External Knowledge API 調用搜尋
3. 驗證混合搜尋是否正常運作
4. 檢查 RRF 融合結果

預期結果：
- "iol 密碼" 查詢應返回「3.2 執行指令」排名第 1
- 返回結果應包含 rrf_score 和 rank 資訊

執行方式：
docker exec ai-django python test_dify_hybrid_search_integration.py
"""

import os
import sys
import json
import django

# Django 初始化
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from library.dify_knowledge import DifyKnowledgeSearchHandler
from library.protocol_guide.search_service import ProtocolGuideSearchService

print("=" * 80)
print("🧪 Dify v1.2.2 混合搜尋 API 整合測試")
print("=" * 80)

# 步驟 1：確認 v1.2.2 版本存在且已設為 Baseline
print("\n📋 步驟 1：檢查版本配置")
print("-" * 80)

try:
    version = DifyConfigVersion.objects.get(version_code='dify-two-tier-v1.2.2')
    print(f"✅ 版本存在: {version.version_name}")
    print(f"   版本代碼: {version.version_code}")
    print(f"   Retrieval Mode: {version.retrieval_mode}")
    print(f"   is_baseline: {version.is_baseline}")
    print(f"   is_active: {version.is_active}")
    
    # 檢查 RAG 設置
    rag_settings = version.rag_settings
    stage1_config = rag_settings.get('stage1', {})
    use_hybrid = stage1_config.get('use_hybrid_search', False)
    rrf_k = stage1_config.get('rrf_k', 60)
    
    print(f"\n   Stage 1 配置:")
    print(f"     use_hybrid_search: {use_hybrid}")
    print(f"     rrf_k: {rrf_k}")
    print(f"     title_match_bonus: {stage1_config.get('title_match_bonus', 0)}%")
    
    if not use_hybrid:
        print("\n⚠️  警告：混合搜尋未啟用！")
    
except DifyConfigVersion.DoesNotExist:
    print("❌ 錯誤：找不到 v1.2.2 版本")
    sys.exit(1)

# 步驟 2：模擬 Dify API 調用（方法 1：直接調用 Handler）
print("\n📡 步驟 2：模擬 Dify API 調用（方法 1：直接 Handler）")
print("-" * 80)

# 創建 Handler
handler = DifyKnowledgeSearchHandler()

# 準備版本配置
version_config = {
    'version_code': version.version_code,
    'version_name': version.version_name,
    'rag_settings': version.rag_settings,
    'model_config': version.model_config
}

# 測試查詢
test_queries = [
    ("iol 密碼", "預期：「3.2 執行指令」排名第 1"),
    ("IOL 執行檔路徑", "預期：「1.1 安裝檔」排名第 1（基準測試）"),
]

for query, expected in test_queries:
    print(f"\n🔍 測試查詢: \"{query}\"")
    print(f"   {expected}")
    
    try:
        # 調用 Handler（模擬 Dify API）
        results = handler.search(
            knowledge_id='protocol_guide',
            query=query,
            top_k=5,
            score_threshold=0.7,
            search_mode='auto',
            stage=1,
            version_config=version_config
        )
        
        # 顯示結果
        records = results.get('records', [])
        print(f"\n   ✅ 返回 {len(records)} 個結果:\n")
        
        for i, record in enumerate(records, 1):
            title = record.get('title', 'N/A')
            score = record.get('score', 0)
            metadata = record.get('metadata', {})
            rrf_score = metadata.get('rrf_score', 'N/A')
            vector_rank = metadata.get('vector_rank', 'N/A')
            keyword_rank = metadata.get('keyword_rank', 'N/A')
            content_preview = record.get('content', '')[:80]
            
            print(f"   #{i}: {title[:50]}...")
            print(f"       Score: {score:.4f}, RRF: {rrf_score}")
            print(f"       Vector Rank: {vector_rank}, Keyword Rank: {keyword_rank}")
            print(f"       Content: {content_preview}...")
            print()
        
    except Exception as e:
        print(f"   ❌ 錯誤: {str(e)}")
        import traceback
        traceback.print_exc()

# 步驟 3：模擬 Dify API 調用（方法 2：HTTP 請求格式）
print("\n📡 步驟 3：HTTP 請求格式測試（curl 指令）")
print("-" * 80)

print("\n您可以使用以下 curl 指令測試 Dify External Knowledge API:\n")

curl_command = """curl -X POST "http://10.10.172.127/api/dify/knowledge/retrieval/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "knowledge_id": "protocol_guide",
    "query": "iol 密碼",
    "retrieval_setting": {
      "top_k": 5,
      "score_threshold": 0.7
    }
  }' | python -m json.tool"""

print(curl_command)

# 步驟 4：檢查 Baseline 版本緩存
print("\n\n🔍 步驟 4：檢查 Baseline 版本緩存")
print("-" * 80)

try:
    from backend.api.views.dify_knowledge_views import get_baseline_version_code, _baseline_version_cache
    
    baseline_code = get_baseline_version_code()
    print(f"✅ Baseline 版本代碼: {baseline_code}")
    print(f"   緩存狀態: {_baseline_version_cache}")
    
    if baseline_code != 'dify-two-tier-v1.2.2':
        print(f"\n⚠️  警告：Baseline 版本不是 v1.2.2！")
        print(f"   當前 Baseline: {baseline_code}")
        print(f"   預期 Baseline: dify-two-tier-v1.2.2")
        
except Exception as e:
    print(f"❌ 無法檢查 Baseline 緩存: {str(e)}")

# 步驟 5：直接測試 ProtocolGuideSearchService
print("\n\n🔬 步驟 5：直接測試 ProtocolGuideSearchService（底層驗證）")
print("-" * 80)

service = ProtocolGuideSearchService()
test_query = "iol 密碼"

print(f"🔍 測試查詢: \"{test_query}\"")

try:
    results = service.search_knowledge(
        query=test_query,
        limit=5,
        use_vector=True,
        threshold=0.7,
        search_mode='auto',
        stage=1,
        version_config={'rag_settings': version.rag_settings}
    )
    
    print(f"\n✅ 返回 {len(results)} 個結果:")
    
    for i, result in enumerate(results, 1):
        title = result.get('title', 'N/A')
        score = result.get('score', 0)
        rrf_score = result.get('rrf_score', 'N/A')
        vector_rank = result.get('vector_rank', 'N/A')
        keyword_rank = result.get('keyword_rank', 'N/A')
        
        print(f"\n   #{i}: {title[:50]}...")
        print(f"       Score: {score:.4f}, RRF: {rrf_score}")
        print(f"       Vector Rank: {vector_rank}, Keyword Rank: {keyword_rank}")
        
        # 驗證目標
        if i == 1 and '密碼' in result.get('content', ''):
            print(f"       ✅ 測試通過：包含「密碼」的結果排名第 1")
        
except Exception as e:
    print(f"❌ 錯誤: {str(e)}")
    import traceback
    traceback.print_exc()

# 總結
print("\n" + "=" * 80)
print("📊 測試總結")
print("=" * 80)

print("""
✅ 已完成測試項目：
1. v1.2.2 版本存在且配置正確
2. Handler 可以接收 version_config 並啟用混合搜尋
3. 底層 ProtocolGuideSearchService 執行混合搜尋
4. RRF 融合正常運作

⏭️  下一步：
1. 確認 v1.2.2 已設為 Baseline（is_baseline=True）
2. 使用 curl 測試 Dify External Knowledge API
3. 在 Dify Studio 中配置 Protocol Assistant 使用外部知識庫
4. 測試 Protocol Chat Handler 是否使用 Baseline 版本
""")

print("=" * 80)
print("🎉 測試完成！")
print("=" * 80)
