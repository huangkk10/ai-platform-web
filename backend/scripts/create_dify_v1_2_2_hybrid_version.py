#!/usr/bin/env python
"""
創建 Dify v1.2.2 版本（Hybrid Search + Title Boost）
============================================================

基於 v1.2.1 版本，新增混合搜尋（向量 + 關鍵字 + RRF）功能。

核心特性：
- ✅ 混合搜尋：第一階段使用向量 + 關鍵字 + RRF 融合
- ✅ 保留 Title Boost：標題匹配加分機制（15%/10%）
- ✅ 保留動態 Threshold：從 Web UI 讀取最新配置
- ✅ 第二階段不變：全文向量搜尋（與 v1.2.1 相同）
- ✅ 向後兼容：不影響其他版本（v1.1, v1.2, v1.2.1）

執行方式：
    docker exec ai-django python backend/scripts/create_dify_v1_2_2_hybrid_version.py
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

# 導入配置載入器
try:
    from config.config_loader import get_ai_pc_ip_with_env
except ImportError:
    def get_ai_pc_ip_with_env():
        return os.getenv('AI_PC_IP', '10.10.172.37')

from api.models import DifyConfigVersion
from django.contrib.auth.models import User


def get_dify_api_url():
    """獲取 Dify API URL"""
    ai_pc_ip = get_ai_pc_ip_with_env()
    return f"http://{ai_pc_ip}/v1/chat-messages"


def create_v1_2_2_hybrid_version():
    """創建 Dify 二階搜尋 v1.2.2 版本（Hybrid Search + Title Boost）"""
    
    print("=" * 80)
    print("🚀 創建 Dify 二階搜尋 v1.2.2 版本（Hybrid Search + Title Boost）")
    print("=" * 80)
    
    # 獲取管理員用戶
    admin_user = User.objects.filter(is_superuser=True).first()
    if not admin_user:
        print("❌ 找不到超級管理員用戶")
        return
    
    # 完整的版本描述
    description = """📝 Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)
🎯 使用場景：Protocol 相關問題查詢，混合搜尋 + 標題匹配加分

🆕 核心特性（v1.2.2 新增）：
   ✅ 混合搜尋：第一階段使用向量 + 關鍵字 + RRF 融合
   ✅ 精確關鍵字：解決「iol 密碼」等精確關鍵字查詢排名問題
   ✅ RRF 融合：使用 Reciprocal Rank Fusion (k=60) 融合兩種搜尋結果
   ✅ 保留語義：向量搜尋保持語義理解能力
   ✅ 保留 Title Boost：標題匹配加分機制仍然有效
   ✅ 動態配置：繼承 v1.2.1 的動態 Threshold 功能

⚙️ 混合搜尋架構：
   
   第一階段：混合搜尋 + Title Boost ⭐ 重點改進
     🔄 搜尋流程：
       1. 向量搜尋（語義理解）
       2. 關鍵字搜尋（精確匹配）
       3. RRF 融合（排名融合）
       4. Title Boost 加分（標題匹配）
     
     🔍 向量搜尋（語義）：
       • 使用 1024 維向量
       • 餘弦相似度計算
       • Threshold: 從 DB 讀取（預設 80%）
       • 權重：標題 95%, 內容 5%
     
     🔍 關鍵字搜尋（精確）：
       • PostgreSQL 全文搜尋（GIN 索引）
       • ts_rank 分數排序
       • 適合精確關鍵字（如 "iol 密碼"）
     
     🔗 RRF 融合算法：
       • 公式：RRF_score = 1/(k + rank)
       • k 值：60（業界標準）
       • 不依賴分數範圍（排名穩定）
       • 自動去重（同一文檔取最高分）
     
     ⭐ Title Boost（最後加分）：
       • 標題關鍵詞匹配：+15%
       • 最小關鍵詞長度：2
       • 應用於 RRF 融合後的結果
   
   第二階段：全文向量搜尋 + Title Boost（與 v1.2.1 相同）
     • 不使用混合搜尋（保持全文語義理解）
     • Threshold: 從 DB 讀取（預設 80%）
     • 權重：標題 10%, 內容 90%
     • Title Boost: 10%

⚙️ Dify 配置：
   - App ID: app-MgZZOhADkEmdUrj2DtQLJ23G (Protocol Guide)
   - 後端搜尋：ProtocolGuideSearchService.search_knowledge(stage=1/2)
   - 響應模式：Blocking（同步回應）

📊 技術特點：
   - ✅ 混合搜尋：向量 + 關鍵字 + RRF（業界標準方法）
   - ✅ GIN 索引：高效全文搜尋（PostgreSQL 原生支援）
   - ✅ RRF 算法：無需分數正規化，排名穩定
   - ✅ 動態配置：Web UI 調整 Threshold 即時生效
   - ✅ Title Boost：標題匹配加分（15%/10%）
   - ✅ 零侵入：不影響其他版本

🎯 解決的問題：

   問題：「iol 密碼」查詢中，sec_5（包含密碼）排名第 5
   
   v1.2.1 (純向量搜尋)：
     ✅ 語義理解好（"如何測試 USB"）
     ❌ 精確關鍵字弱（"iol 密碼" 排名不佳）
   
   v1.2.2 (混合搜尋)：
     ✅ 語義理解好（向量搜尋）
     ✅ 精確關鍵字強（關鍵字搜尋 + RRF）
     ✅ 兩者融合（RRF 算法）
     ✅ 標題加分（Title Boost）

🔄 與其他版本的差異：

   v1.1 (靜態 + 純向量)：
     • Threshold: 80%（寫死）
     • Title Weight: 95%（寫死）
     • 無 Title Boost
     • 純向量搜尋
   
   v1.2 (靜態 + Title Boost)：
     • Threshold: 80%（寫死）
     • Title Weight: 95%（寫死）
     • Title Boost: 15%/10%
     • 純向量搜尋
   
   v1.2.1 (動態 + Title Boost)：
     • Threshold: 從 Web UI 讀取 ✨
     • Title Weight: 從 Web UI 讀取 ✨
     • Title Boost: 15%/10%
     • 純向量搜尋
   
   v1.2.2 (混合搜尋 + Title Boost)：
     • Threshold: 從 Web UI 讀取 ✨
     • Title Weight: 從 Web UI 讀取 ✨
     • Title Boost: 15%/10%
     • 混合搜尋（向量 + 關鍵字 + RRF）⭐

⚠️  重要提醒：
   • 混合搜尋只在第一階段啟用（段落搜尋）
   • 第二階段保持全文向量搜尋（語義理解）
   • RRF k=60 是業界標準，通常不需要調整
   • 測試結果會記錄 rrf_score, vector_rank, keyword_rank
   • 建議先在 Baseline 測試，確認無問題後再切換

📖 測試建議：
   1. 使用 10 條驗證問題（詳見快速檢查清單）
   2. 重點測試精確關鍵字查詢（如「iol 密碼」）
   3. 對比 v1.2.1 和 v1.2.2 的排名差異
   4. 檢查 RRF 融合是否正常（rrf_score, vector_rank, keyword_rank）
   5. 確認 Title Boost 仍然有效
   6. 測試通過後設為 Baseline
"""
    
    # RAG 設置（v1.2.2 - 混合搜尋版本）
    rag_settings = {
        # 指定 Assistant 類型（用於動態載入）
        "assistant_type": "protocol_assistant",
        
        "stage1": {
            # 🆕 啟用混合搜尋（v1.2.2 新增）
            "use_hybrid_search": True,
            "rrf_k": 60,  # RRF 融合常數（業界標準）
            
            # 🔄 動態 Threshold（繼承 v1.2.1）
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            # 📌 版本特定設定（固定，不從 DB 讀取）
            "title_match_bonus": 15,   # Title Boost 加分（版本特性）
            "min_keyword_length": 2,   # 最小關鍵詞長度
            "top_k": 20,               # 返回結果數量
            
            # ⚠️ 預設值（當 DB 無設定時使用）
            "threshold": 0.80,
            "title_weight": 95,
            "content_weight": 5,
        },
        
        "stage2": {
            # ⚠️ 第二階段不使用混合搜尋（保持全文語義理解）
            "use_hybrid_search": False,
            
            # 🔄 動態 Threshold
            "use_dynamic_threshold": True,
            "assistant_type": "protocol_assistant",
            
            # 📌 版本特定設定（固定）
            "title_match_bonus": 10,   # Title Boost 加分
            "min_keyword_length": 2,
            "top_k": 10,
            
            # ⚠️ 預設值
            "threshold": 0.80,
            "title_weight": 10,
            "content_weight": 90,
        },
        
        # 檢索模式和服務（更新為混合搜尋）
        "retrieval_mode": "hybrid_search_with_title_boost",  # v1.2.2 新模式
        "use_backend_search": True,
        "search_service": "ProtocolGuideSearchService"
    }
    
    # 模型配置（與 v1.2.1 相同）
    model_config = {
        "temperature": 0.2,
        "max_tokens": 4000,
        "response_mode": "blocking"
    }
    
    # 創建或更新版本
    version, created = DifyConfigVersion.objects.get_or_create(
        version_code="dify-two-tier-v1.2.2",
        defaults={
            'version_name': "Dify 二階搜尋 v1.2.2 (Hybrid Search + Title Boost)",
            'dify_app_id': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_key': "app-MgZZOhADkEmdUrj2DtQLJ23G",
            'dify_api_url': get_dify_api_url(),  # 動態獲取 API URL
            'description': description,
            'rag_settings': rag_settings,
            'model_config': model_config,
            'retrieval_mode': 'hybrid_search_with_title_boost',
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
        print(f"   • 混合搜尋版本: 是 ⭐")
        print(f"   • Assistant 類型: {rag_settings['assistant_type']}")
        print(f"\n   第一階段配置（混合搜尋 ⭐）:")
        print(f"     🔄 混合搜尋:")
        print(f"        • 啟用: {rag_settings['stage1']['use_hybrid_search']}")
        print(f"        • RRF k 值: {rag_settings['stage1']['rrf_k']}")
        print(f"     🔄 動態配置（從 Web UI）:")
        print(f"        • Threshold: {rag_settings['stage1']['threshold']*100}% (預設)")
        print(f"        • 標題權重: {rag_settings['stage1']['title_weight']}% (預設)")
        print(f"        • 內容權重: {rag_settings['stage1']['content_weight']}% (預設)")
        print(f"     📌 固定配置（版本定義）:")
        print(f"        • Title Boost: {rag_settings['stage1']['title_match_bonus']}%")
        print(f"        • Top K: {rag_settings['stage1']['top_k']}")
        print(f"\n   第二階段配置（全文向量搜尋）:")
        print(f"     • 混合搜尋: {rag_settings['stage2']['use_hybrid_search']} (保持全文語義)")
        print(f"     🔄 動態配置（從 Web UI）:")
        print(f"        • Threshold: {rag_settings['stage2']['threshold']*100}% (預設)")
        print(f"        • 標題權重: {rag_settings['stage2']['title_weight']}% (預設)")
        print(f"        • 內容權重: {rag_settings['stage2']['content_weight']}% (預設)")
        print(f"     📌 固定配置（版本定義）:")
        print(f"        • Title Boost: {rag_settings['stage2']['title_match_bonus']}%")
        print(f"        • Top K: {rag_settings['stage2']['top_k']}")
        print(f"\n   • 檢索模式: {version.retrieval_mode}")
        print(f"   • 基準版本: {'是' if version.is_baseline else '否'}")
        print(f"\n🎯 混合搜尋特性:")
        print(f"   • 向量搜尋：語義理解（餘弦相似度）")
        print(f"   • 關鍵字搜尋：精確匹配（PostgreSQL GIN 索引）")
        print(f"   • RRF 融合：排名融合（k=60，業界標準）")
        print(f"   • Title Boost：標題加分（15%，最後應用）")
        print(f"   • 動態配置：Web UI 調整即時生效")
        print(f"\n⚠️  重要提醒:")
        print(f"   • 混合搜尋只在第一階段啟用（段落搜尋）")
        print(f"   • 第二階段保持全文向量搜尋（語義理解）")
        print(f"   • RRF k=60 是業界標準，通常不需要調整")
        print(f"   • 測試結果會記錄 rrf_score, vector_rank, keyword_rank")
        print(f"   • 建議使用 10 條驗證問題進行全面測試")
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
            print(f"   • Stage 1 混合搜尋: {stage1.get('use_hybrid_search', False)}")
            print(f"   • Stage 1 RRF k: {stage1.get('rrf_k', 60)}")
            print(f"   • Stage 1 Title Boost: {stage1.get('title_match_bonus', 0)}%")
            print(f"   • Stage 2 混合搜尋: {stage2.get('use_hybrid_search', False)}")
            print(f"   • Stage 2 Title Boost: {stage2.get('title_match_bonus', 0)}%")
    
    print("\n" + "=" * 80)
    print("✅ 版本創建流程完成")
    print("\n下一步：")
    print("  1. 在 VSA 版本管理中刷新，確認 v1.2.2 版本出現（帶 🔄+⭐ 標記）")
    print("  2. 使用 10 條驗證問題進行測試（詳見快速檢查清單）")
    print("  3. 重點測試精確關鍵字查詢（如「iol 密碼」）")
    print("  4. 對比 v1.2.1 和 v1.2.2 的排名差異")
    print("  5. 檢查測試結果中的 rrf_score, vector_rank, keyword_rank")
    print("  6. 確認 Title Boost 仍然有效（title_boost_applied）")
    print("  7. 測試通過率 ≥ 90% 後，設為 Baseline（Protocol Assistant 預設版本）")
    print("  8. 使用 curl 命令測試 Dify 外部知識庫整合")
    print("=" * 80)


if __name__ == "__main__":
    try:
        create_v1_2_2_hybrid_version()
    except Exception as e:
        print(f"\n❌ 創建版本時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
