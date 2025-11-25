#!/usr/bin/env python
"""
創建 Dify v1.2.1 版本（Dynamic Threshold + Title Boost）
============================================================

基於 v1.2 版本，新增動態 Threshold 讀取功能。

核心特性：
- ✅ 動態讀取 Web UI「搜尋 Threshold 設定」頁面的配置
- ✅ 管理員可即時調整參數無需創建新版本
- ✅ 保留 Title Boost 加分機制（版本特性）
- ✅ 向後兼容所有靜態版本（v1.1, v1.2）

執行方式：
    docker exec ai-django python backend/scripts/create_dify_v1_2_1_dynamic_version.py
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import DifyConfigVersion
from django.contrib.auth.models import User


def create_v1_2_1_dynamic_version():
    """創建 Dify 二階搜尋 v1.2.1 版本（動態 Threshold + Title Boost）"""
    
    print("=" * 80)
    print("🚀 創建 Dify 二階搜尋 v1.2.1 版本（Dynamic Threshold + Title Boost）")
    print("=" * 80)
    
    # 獲取管理員用戶
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ 找不到超級管理員用戶")
        return
    
    # 完整的版本描述
    description = """📝 Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)
🎯 使用場景：Protocol 相關問題查詢，動態 Threshold + 標題匹配加分

🆕 核心特性（v1.2.1 新增）：
   ✅ 動態 Threshold：從 Web UI「搜尋 Threshold 設定」讀取最新配置
   ✅ 即時生效：管理員調整設定後，測試立即使用新值（無需創建新版本）
   ✅ 靈活測試：支援快速 A/B 測試不同參數組合
   ✅ 向後兼容：不影響 v1.1, v1.2 等靜態版本
   ✅ 保留 Title Boost：標題匹配加分機制仍由版本定義（不從 DB 讀取）

⚙️ 動態配置架構：
   
   第一階段：分段向量搜尋 + Title Boost
     🔄 動態讀取（從 search_threshold_settings）：
       • 段落向量 Threshold：從 DB 讀取（預設 80%）
       • 標題權重：從 DB 讀取（預設 95%）
       • 內容權重：從 DB 讀取（預設 5%）
     
     📌 固定配置（由版本定義）：
       • Title Match Bonus：15%（標題關鍵字匹配加分）
       • 最小關鍵詞長度：2
       • Top K：20
   
   第二階段：全文向量搜尋 + Title Boost
     🔄 動態讀取（從 search_threshold_settings）：
       • 段落向量 Threshold：從 DB 讀取（預設 80%）
       • 標題權重：從 DB 讀取（預設 10%）
       • 內容權重：從 DB 讀取（預設 90%）
     
     📌 固定配置（由版本定義）：
       • Title Match Bonus：10%（標題關鍵字匹配加分）
       • 最小關鍵詞長度：2
       • Top K：10

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：使用 ProtocolGuideSearchService.search_knowledge(stage=1/2)
   - 動態載入：DynamicThresholdLoader.load_full_rag_settings()
   - 響應模式：Blocking（同步回應）

📊 技術特點：
   - ✅ 配置優先順序：Web UI > 版本預設值 > 程式碼預設值
   - ✅ 快取機制：ThresholdManager 提供 5 分鐘快取（可手動刷新）
   - ✅ 錯誤處理：DB 無設定時自動使用預設值
   - ✅ 完整追蹤：測試結果記錄實際使用的配置（config_source, actual_config）
   - ✅ 零侵入：靜態版本（v1.1, v1.2）完全不受影響

🎯 使用情境：

   情境 1：快速參數調優
     1. 在「搜尋 Threshold 設定」調整參數（80% → 85%）
     2. 選擇 v1.2.1 執行批量測試
     3. 無需創建新版本，立即使用新設定
     4. 查看測試結果（detailed_results 記錄實際配置）
   
   情境 2：A/B 對比測試
     測試組 A：Threshold 80%, 標題 95%, 內容 5%
     測試組 B：Threshold 85%, 標題 90%, 內容 10%
     ✅ 同一個版本（v1.2.1），不同配置，快速對比

🔄 與其他版本的差異：

   v1.1 (靜態)：
     • Threshold: 80%（寫死）
     • Title Weight: 95%（寫死）
     • 無 Title Boost
   
   v1.2 (靜態 + Title Boost)：
     • Threshold: 80%（寫死）
     • Title Weight: 95%（寫死）
     • Title Boost: 15%/10%
   
   v1.2.1 (動態 + Title Boost)：
     • Threshold: 從 Web UI 讀取 ✨
     • Title Weight: 從 Web UI 讀取 ✨
     • Title Boost: 15%/10%（版本固定）

⚠️  重要提醒：
   • 動態配置只影響 threshold, title_weight, content_weight
   • Title Boost 值（15%/10%）仍由版本定義（不會被 DB 覆蓋）
   • 測試結果中會記錄實際使用的配置（便於追蹤和對比）
   • 建議在測試前記錄當前 Threshold 設定值

📖 範例使用流程：
   1. 進入「搜尋 Threshold 設定」頁面
   2. 調整 Protocol Assistant 第一階段：85%, 90%, 10%
   3. 在 VSA 選擇 v1.2.1 版本執行測試
   4. 系統自動載入最新設定（85%, 90%, 10%）
   5. 測試結果記錄實際使用的配置（可追蹤）
   6. 如需調整，修改設定後再次執行（無需創建新版本）
"""
    
    # RAG 設置（v1.2.1 - 動態版本）
    rag_settings = {
        # 指定 Assistant 類型（用於動態載入）
        "assistant_type": "protocol_assistant",
        
        "stage1": {
            # 🆕 啟用動態載入
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            # 📌 版本特定設定（固定，不從 DB 讀取）
            "title_match_bonus": 15,   # Title Boost 加分（版本特性）
            "min_keyword_length": 2,   # 最小關鍵詞長度
            "top_k": 20,               # 返回結果數量
            
            # ⚠️ 預設值（當 DB 無設定時使用）
            # 這些值會被 DB 中的設定覆蓋（如果存在）
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
        },
        
        "stage2": {
            # 🆕 啟用動態載入
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            # 📌 版本特定設定（固定）
            "title_match_bonus": 10,   # Title Boost 加分
            "min_keyword_length": 2,
            "top_k": 10,
            
            # ⚠️ 預設值（當 DB 無設定時使用）
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
        },
        
        # 檢索模式和服務（固定）
        "retrieval_mode": "two_stage_with_title_boost",
        "use_backend_search": True,
        "search_service": "ProtocolGuideSearchService"
    }
    
    # 模型配置（與 v1.2 相同）
    model_config = {
        "temperature": 0.2,
        "max_tokens": 4000,
        "response_mode": "blocking"
    }
    
    # 創建或更新版本
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.2.1",
        defaults={
            'version_name': "Dify 二階搜尋 v1.2.1 (Dynamic Threshold + Title Boost)",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_url': "http://10.10.172.37/v1/chat-messages",
            'description': description,
            'rag_settings': rag_settings,
            'model_config': model_config,
            'retrieval_mode': 'two_stage_with_title_boost',
            'is_active': True,
            'is_baseline': False,  # 不是 baseline（可透過 UI 切換）
            'created_by': admin_user
        }
    )
    
    if created:
        print(f"\n✅ 成功創建版本: {version.version_name}")
        print(f"   版本代碼: {version.version_code}")
        print(f"   App ID: {version.dify_app_id}")
        print(f"   API URL: {version.dify_api_url}")
        print(f"\n📋 配置摘要:")
        print(f"   • 動態版本: 是 ✨")
        print(f"   • Assistant 類型: {rag_settings['assistant_type']}")
        print(f"\n   第一階段配置:")
        print(f"     - use_dynamic_threshold: {rag_settings['stage1']['use_dynamic_threshold']}")
        print(f"     🔄 動態（從 Web UI）：")
        print(f"        • Threshold: {rag_settings['stage1']['threshold']*100}% (預設)")
        print(f"        • 標題權重: {rag_settings['stage1']['title_weight']}% (預設)")
        print(f"        • 內容權重: {rag_settings['stage1']['content_weight']}% (預設)")
        print(f"     📌 固定（版本定義）：")
        print(f"        • Title Boost: {rag_settings['stage1']['title_match_bonus']}%")
        print(f"        • Top K: {rag_settings['stage1']['top_k']}")
        print(f"\n   第二階段配置:")
        print(f"     - use_dynamic_threshold: {rag_settings['stage2']['use_dynamic_threshold']}")
        print(f"     🔄 動態（從 Web UI）：")
        print(f"        • Threshold: {rag_settings['stage2']['threshold']*100}% (預設)")
        print(f"        • 標題權重: {rag_settings['stage2']['title_weight']}% (預設)")
        print(f"        • 內容權重: {rag_settings['stage2']['content_weight']}% (預設)")
        print(f"     📌 固定（版本定義）：")
        print(f"        • Title Boost: {rag_settings['stage2']['title_match_bonus']}%")
        print(f"        • Top K: {rag_settings['stage2']['top_k']}")
        print(f"\n   • 檢索模式: {version.retrieval_mode}")
        print(f"   • 基準版本: {'是' if version.is_baseline else '否'}")
        print(f"\n🎯 動態 Threshold 特性:")
        print(f"   • 配置來源：Web UI「搜尋 Threshold 設定」頁面")
        print(f"   • 優先順序：DB > 版本預設 > 程式碼預設")
        print(f"   • 快取機制：ThresholdManager（5 分鐘 TTL）")
        print(f"   • 錯誤處理：DB 無設定時使用版本預設值")
        print(f"   • 結果追蹤：actual_config 記錄實際使用的配置")
        print(f"\n⚠️  重要提醒:")
        print(f"   • 管理員可在 UI 調整參數，測試立即使用新值")
        print(f"   • Title Boost 值由版本定義（不會被 DB 覆蓋）")
        print(f"   • 靜態版本（v1.1, v1.2）完全不受影響")
        print(f"   • 測試結果會記錄實際使用的配置（便於追蹤）")
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
            print(f"   • Stage 1 動態: {stage1.get('use_dynamic_threshold', False)}")
            print(f"   • Stage 1 Title Boost: {stage1.get('title_match_bonus', 0)}%")
            print(f"   • Stage 2 動態: {stage2.get('use_dynamic_threshold', False)}")
            print(f"   • Stage 2 Title Boost: {stage2.get('title_match_bonus', 0)}%")
    
    print("\n" + "=" * 80)
    print("✅ 版本創建流程完成")
    print("\n下一步：")
    print("  1. 在 VSA 版本管理中刷新，確認新版本出現（帶 🔄 動態標記）")
    print("  2. 進入「搜尋 Threshold 設定」頁面調整 Protocol Assistant 參數")
    print("  3. 選擇 v1.2.1 版本進行測試")
    print("  4. 查看測試結果中的 detailed_results.actual_config")
    print("  5. 調整參數後再次測試（無需創建新版本）")
    print("  6. 對比不同參數組合的測試結果（A/B 測試）")
    print("  7. （可選）在版本管理中點擊「設為 Baseline」，作為 Protocol Assistant 預設版本")
    print("=" * 80)


if __name__ == "__main__":
    try:
        create_v1_2_1_dynamic_version()
    except Exception as e:
        print(f"\n❌ 創建版本時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
