#!/usr/bin/env python
"""創建 Dify 基準測試版本"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from django.contrib.auth.models import User


def create_baseline_version():
    """創建 Dify 二階搜尋 v1.1 版本"""
    
    print("=" * 80)
    print("🚀 創建 Dify 二階搜尋 v1.1 基準版本")
    print("=" * 80)
    
    # 獲取管理員用戶
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ 找不到超級管理員用戶")
        return
    
    # 完整的版本描述
    description = """📝 Dify 二階搜尋版本
🎯 使用場景：Protocol 相關問題查詢，結合分段與全文搜尋策略

⚙️ 搜尋策略配置：
   
   第一階段：分段向量搜尋（Section-level Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：95%
     • 內容權重：5%
     • 說明：極度強調標題匹配，適合查找特定章節
   
   第二階段：全文向量搜尋（Full Document Vector Search）
     • 段落向量 Threshold：80%
     • 標題權重：10%
     • 內容權重：90%
     • 說明：極度強調內容匹配，適合理解完整文檔脈絡

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：使用 ProtocolGuideSearchService.search_knowledge(stage=1)
   - 上下文來源：二階搜尋結果（最多 20 筆文檔）
   - 響應模式：Blocking（同步回應）

📊 技術特點：
   - ✅ 第一階段：標題導向（95/5），快速定位章節位置
   - ✅ 第二階段：內容導向（10/90），深度理解文檔內容
   - ✅ 兩階段形成互補：先精準定位，後全文理解
   - ✅ Threshold 保持一致（80%），確保搜尋品質
   - ✅ 透過後端搜尋 API 提供高品質上下文給 Dify

🎯 預期效果：
   - 提高 Protocol SOP 類問題的精準度
   - 第一階段快速找到相關章節（標題匹配）
   - 第二階段深入理解內容細節（內容匹配）
   - 兼顧定位速度和理解深度
"""
    
    # RAG 設置
    rag_settings = {
        "stage1": {
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
            "top_k": 20
        },
        "stage2": {
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
            "top_k": 10
        },
        "retrieval_mode": "two_stage",
        "use_backend_search": True,
        "search_service": "ProtocolGuideSearchService"
    }
    
    # 模型配置
    model_config = {
        "temperature": 0.2,
        "max_tokens": 4000,
        "response_mode": "blocking"
    }
    
    # 創建或更新版本
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.1",
        defaults={
            'version_name': "Dify 二階搜尋 v1.1",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-MgZZOhADkEmdUrj2DtQLJ23G",  # 注意：實際使用時需要正確的 API Key
            'dify_api_url': "http://10.10.172.37/v1/chat-messages",
            'description': description,
            'rag_settings': rag_settings,
            'model_config': model_config,
            'retrieval_mode': 'two_stage',
            'is_active': True,
            'is_baseline': True,
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"\n✅ 成功創建版本: {version.version_name}")
        print(f"   版本代碼: {version.version_code}")
        print(f"   App ID: {version.dify_app_id}")
        print(f"   API URL: {version.dify_api_url}")
        print(f"\n📋 配置摘要:")
        print(f"   • Stage 1 - Threshold: {rag_settings['stage1']['threshold']*100}%, 標題: {rag_settings['stage1']['title_weight']}%, 內容: {rag_settings['stage1']['content_weight']}%")
        print(f"   • Stage 2 - Threshold: {rag_settings['stage2']['threshold']*100}%, 標題: {rag_settings['stage2']['title_weight']}%, 內容: {rag_settings['stage2']['content_weight']}%")
        print(f"   • 檢索模式: {version.retrieval_mode}")
        print(f"   • 基準版本: {'是' if version.is_baseline else '否'}")
    else:
        print(f"\n⚠️  版本已存在: {version.version_name}")
        print(f"   版本代碼: {version.version_code}")
        print(f"   如需更新，請手動修改或刪除後重新執行")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    create_baseline_version()
