#!/usr/bin/env python
"""
創建 Dify v1.2 版本（Title Boost）
==========================================

基於 v1.1 版本，新增 Title 匹配加分機制。

執行方式：
    docker exec ai-django python backend/scripts/create_dify_v1_2_version.py
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from django.contrib.auth.models import User


def create_v1_2_version():
    """創建 Dify 二階搜尋 v1.2 版本（Title Boost）"""
    
    print("=" * 80)
    print("🚀 創建 Dify 二階搜尋 v1.2 版本（Title Boost）")
    print("=" * 80)
    
    # 獲取管理員用戶
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ 找不到超級管理員用戶")
        return
    
    # 完整的版本描述
    description = """📝 Dify 二階搜尋 v1.2 (Title Boost)
🎯 使用場景：Protocol 相關問題查詢，結合分段與全文搜尋策略 + 標題匹配加分

⚙️ 搜尋策略配置：
   
   第一階段：分段向量搜尋 + Title Boost
     • 段落向量 Threshold：80%
     • 標題權重：95%
     • 內容權重：5%
     • 🆕 Title Match Bonus：15%（標題關鍵字匹配加分）
     • 說明：極度強調標題匹配，Title Boost 進一步提升精準匹配結果
   
   第二階段：全文向量搜尋 + Title Boost
     • 段落向量 Threshold：80%
     • 標題權重：10%
     • 內容權重：90%
     • 🆕 Title Match Bonus：10%（標題關鍵字匹配加分）
     • 說明：極度強調內容匹配，Title Boost 輔助提升相關結果

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：使用 ProtocolGuideSearchService.search_knowledge(stage=1/2)
   - 上下文來源：二階搜尋結果（最多 20 筆文檔）
   - 響應模式：Blocking（同步回應）

📊 技術特點（v1.2 新增）：
   - ✅ Title Boost：查詢關鍵字出現在標題時，額外加分
   - ✅ 智能關鍵詞提取：自動移除停用詞、正規化縮寫詞（iol → IOL）
   - ✅ 第一階段加分 15%：標題導向搜尋，強化精準匹配
   - ✅ 第二階段加分 10%：內容導向搜尋，輔助排名優化
   - ✅ 裝飾器模式：不修改原有搜尋邏輯，完全向後兼容
   - ✅ 零侵入設計：不影響 v1.1 和原有 Protocol Assistant

🎯 預期效果：
   - 提高標題精準匹配查詢的準確度（如 "IOL SOP", "USB 測試"）
   - 第一階段快速找到標題匹配章節（向量分數 + Title Boost）
   - 第二階段深入理解內容，Title Boost 輔助最終排序
   - 兼顧精準匹配（關鍵字）和語義理解（向量相似度）

🔄 與 v1.1 的差異：
   - v1.1: 純向量相似度排序
   - v1.2: 向量相似度 + Title 關鍵字匹配加分
   - 向後兼容：v1.1 完全不受影響

📖 範例查詢效果：
   查詢："IOL SOP"
   - v1.1: IOL 文檔（向量分數 0.85）排第一
   - v1.2: IOL 文檔（0.85 + Title Boost 0.15 = 1.0）排第一 ✨
"""
    
    # RAG 設置（v1.2 新增 title_match_bonus）
    rag_settings = {
        "stage1": {
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
            "title_match_bonus": 15,  # 🆕 新增（百分比）
            "min_keyword_length": 2,   # 🆕 最小關鍵詞長度
            "top_k": 20
        },
        "stage2": {
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
            "title_match_bonus": 10,  # 🆕 新增（百分比）
            "min_keyword_length": 2,   # 🆕 最小關鍵詞長度
            "top_k": 10
        },
        "retrieval_mode": "two_stage_with_title_boost",  # 🆕 新模式（包含 'title_boost' 標識）
        "use_backend_search": True,
        "search_service": "ProtocolGuideSearchService"
    }
    
    # 模型配置（與 v1.1 相同）
    model_config = {
        "temperature": 0.2,
        "max_tokens": 4000,
        "response_mode": "blocking"
    }
    
    # 創建或更新版本
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.2",
        defaults={
            'version_name': "Dify 二階搜尋 v1.2 (Title Boost)",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_url': "http://10.10.172.37/v1/chat-messages",
            'description': description,
            'rag_settings': rag_settings,
            'model_config': model_config,
            'retrieval_mode': 'two_stage_with_title_boost',  # 🆕 標識
            'is_active': True,
            'is_baseline': False,  # 不是 baseline（v1.1 仍是 baseline）
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"\n✅ 成功創建版本: {version.version_name}")
        print(f"   版本代碼: {version.version_code}")
        print(f"   App ID: {version.dify_app_id}")
        print(f"   API URL: {version.dify_api_url}")
        print(f"\n📋 配置摘要:")
        print(f"   • Stage 1 - Threshold: {rag_settings['stage1']['threshold']*100}%, "
              f"標題: {rag_settings['stage1']['title_weight']}%, "
              f"內容: {rag_settings['stage1']['content_weight']}%, "
              f"🆕 Title Boost: {rag_settings['stage1']['title_match_bonus']}%")
        print(f"   • Stage 2 - Threshold: {rag_settings['stage2']['threshold']*100}%, "
              f"標題: {rag_settings['stage2']['title_weight']}%, "
              f"內容: {rag_settings['stage2']['content_weight']}%, "
              f"🆕 Title Boost: {rag_settings['stage2']['title_match_bonus']}%")
        print(f"   • 檢索模式: {version.retrieval_mode}")
        print(f"   • 基準版本: {'是' if version.is_baseline else '否'}")
        print(f"\n🎯 Title Boost 特性:")
        print(f"   • 自動關鍵詞提取（移除停用詞）")
        print(f"   • 縮寫詞正規化（iol → IOL）")
        print(f"   • 第一階段加分更高（精準定位）")
        print(f"   • 第二階段加分輔助（內容理解）")
        print(f"\n⚠️  重要提醒:")
        print(f"   • v1.1 版本不受影響，可同時使用")
        print(f"   • 建議在 VSA 測試中對比 v1.1 vs v1.2")
        print(f"   • Title Boost 可在版本配置中調整加分值")
    else:
        print(f"\n⚠️  版本已存在: {version.version_name}")
        print(f"   版本代碼: {version.version_code}")
        print(f"   如需更新配置，請手動修改或刪除後重新執行")
        
        # 顯示現有配置
        print(f"\n📋 現有配置:")
        print(f"   • retrieval_mode: {version.retrieval_mode}")
        print(f"   • is_active: {version.is_active}")
        print(f"   • is_baseline: {version.is_baseline}")
        
        if version.rag_settings:
            stage1 = version.rag_settings.get('stage1', {})
            stage2 = version.rag_settings.get('stage2', {})
            print(f"   • Stage 1 Title Boost: {stage1.get('title_match_bonus', 0)}%")
            print(f"   • Stage 2 Title Boost: {stage2.get('title_match_bonus', 0)}%")
    
    print("\n" + "=" * 80)
    print("✅ 版本創建流程完成")
    print("\n下一步：")
    print("  1. 在 VSA 版本管理中刷新，確認新版本出現")
    print("  2. 選擇 v1.2 版本進行測試")
    print("  3. 對比 v1.1 vs v1.2 的測試結果")
    print("  4. 使用測試查詢：'IOL SOP', 'USB 測試', 'CrystalDiskMark 完整流程'")
    print("=" * 80)


if __name__ == "__main__":
    try:
        create_v1_2_version()
    except Exception as e:
        print(f"\n❌ 創建版本時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
