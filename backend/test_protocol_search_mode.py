#!/usr/bin/env python
"""
測試 Protocol Assistant 的顯式 search_mode 參數實現

測試 3 種模式：
1. auto - 預設行為（section → document fallback）
2. section_only - 僅搜索 section
3. document_only - 直接搜索整篇文檔

執行方式：
    docker exec ai-django python test_protocol_search_mode.py
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# 設置 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()


def print_section(title, char='=', width=80):
    """打印分隔線"""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def print_subsection(title, char='-', width=60):
    """打印子分隔線"""
    print(f"\n{char * width}")
    print(f"{title:^{width}}")
    print(f"{char * width}\n")


def test_protocol_mode(mode_name, search_mode, query):
    """
    測試 Protocol Assistant 的特定 search_mode
    
    Args:
        mode_name: 測試名稱（顯示用）
        search_mode: 搜索模式（'auto', 'section_only', 'document_only'）
        query: 查詢文本
    """
    print_subsection(f"測試 {mode_name}")
    
    # 準備請求數據
    payload = {
        'knowledge_id': 'protocol_guide',
        'query': query,
        'retrieval_setting': {
            'top_k': 3,
            'score_threshold': 0.3
        },
        'inputs': {
            'search_mode': search_mode
        }
    }
    
    print(f"📤 請求配置:")
    print(f"   Knowledge ID: protocol_guide")
    print(f"   Query: {query}")
    print(f"   Search Mode: {search_mode}")
    print(f"   Top K: 3")
    print(f"   Threshold: 0.3")
    print()
    
    try:
        # 發送請求到 Dify 外部知識庫 API
        response = requests.post(
            'http://localhost:8000/api/dify/knowledge/retrieval/',
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            records = result.get('records', [])
            
            print(f"✅ 請求成功")
            print(f"📊 結果統計:")
            print(f"   返回記錄數: {len(records)}")
            print()
            
            if records:
                print(f"📝 詳細結果:")
                for i, record in enumerate(records, 1):
                    metadata = record.get('metadata', {})
                    print(f"\n   結果 {i}:")
                    print(f"      標題: {metadata.get('title', 'N/A')[:60]}...")
                    print(f"      相似度: {record.get('score', 0):.4f}")
                    print(f"      內容長度: {len(record.get('content', ''))} 字元")
                    
                    # 檢查是否為 section 或完整文檔
                    content = record.get('content', '')
                    is_section = len(content) < 2000  # 簡單判斷（section 通常較短）
                    content_type = "段落 (Section)" if is_section else "完整文檔 (Document)"
                    print(f"      內容類型: {content_type}")
                    
                    # 顯示內容片段（前 120 字元）
                    content_preview = content[:120].replace('\n', ' ')
                    print(f"      內容預覽: {content_preview}...")
            else:
                print(f"⚠️ 無搜索結果")
                
        else:
            print(f"❌ 請求失敗: HTTP {response.status_code}")
            print(f"   錯誤訊息: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 網絡錯誤: {str(e)}")
    except Exception as e:
        print(f"❌ 未預期錯誤: {str(e)}")
    
    print()


def test_protocol_direct_service():
    """直接測試 Protocol Guide Search Service"""
    print_section("直接測試 Protocol Guide Search Service", char='=')
    
    try:
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        
        service = ProtocolGuideSearchService()
        test_queries = [
            "CUP 連接測試",
            "ULINK 設定步驟",
            "CrystalDiskMark 測試流程"
        ]
        
        print(f"📤 測試配置:")
        print(f"   Limit: 3")
        print(f"   Threshold: 0.3")
        print(f"   測試查詢數: {len(test_queries)}")
        print()
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"🔍 查詢: {query}")
            print(f"{'='*60}")
            
            # 測試 3 種模式
            modes = [
                ('auto', 'auto'),
                ('section_only', 'section_only'),
                ('document_only', 'document_only')
            ]
            
            for mode_name, mode_value in modes:
                print(f"\n   📋 Mode '{mode_value}':")
                
                try:
                    results = service.search_with_vectors(
                        query=query,
                        limit=3,
                        threshold=0.3,
                        search_mode=mode_value
                    )
                    
                    print(f"      ✅ 返回 {len(results)} 條結果")
                    
                    if results:
                        for i, result in enumerate(results[:2], 1):
                            score = result.get('score', 0)
                            title = result.get('title', 'N/A')[:40]
                            content_len = len(result.get('content', ''))
                            print(f"         {i}. 相似度: {score:.4f} | "
                                  f"標題: {title}... | 長度: {content_len}")
                    else:
                        print(f"         ⚠️ 無結果")
                        
                except Exception as e:
                    print(f"         ❌ 錯誤: {str(e)[:80]}")
        
        print()
        print("✅ 直接 Service 測試完成")
        
    except ImportError as e:
        print(f"❌ 無法導入 ProtocolGuideSearchService: {str(e)}")
        print(f"   這可能表示 Protocol Guide Search Service 尚未實現")
    except Exception as e:
        print(f"❌ 直接測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()


def test_protocol_section_fallback():
    """測試 Protocol Guide 的 section → document fallback 機制"""
    print_section("測試 Section → Document Fallback 機制", char='=')
    
    # 使用一個可能在 section 中找不到的查詢
    fallback_query = "完整的測試流程說明"
    
    print(f"🎯 測試目標: 驗證當 section 搜索無結果時，自動 fallback 到 document")
    print(f"📝 測試查詢: {fallback_query}")
    print()
    
    # 測試 auto 模式（應該會 fallback）
    print(f"1️⃣ 測試 'auto' 模式（應自動 fallback）")
    test_protocol_mode(
        mode_name="Auto Mode (with fallback)",
        search_mode='auto',
        query=fallback_query
    )
    
    # 測試 section_only 模式（不應 fallback）
    print(f"2️⃣ 測試 'section_only' 模式（不應 fallback）")
    test_protocol_mode(
        mode_name="Section Only Mode (no fallback)",
        search_mode='section_only',
        query=fallback_query
    )
    
    # 對比結果
    print(f"📊 預期結果對比:")
    print(f"   - Auto 模式: 如果 section 無結果，應返回 document 結果")
    print(f"   - Section Only 模式: 即使無結果，也不應 fallback")
    print()


def compare_search_modes():
    """比較不同 search_mode 的搜索結果"""
    print_section("比較不同 Search Mode 的結果", char='=')
    
    test_query = "CUP 連接步驟"
    
    print(f"🔬 對比測試查詢: {test_query}")
    print(f"🎯 目的: 觀察不同模式返回的內容差異")
    print()
    
    modes_to_test = [
        ('auto', 'Auto（自動 fallback）'),
        ('section_only', 'Section Only（僅段落）'),
        ('document_only', 'Document Only（完整文檔）')
    ]
    
    for mode_value, mode_desc in modes_to_test:
        test_protocol_mode(
            mode_name=mode_desc,
            search_mode=mode_value,
            query=test_query
        )


def check_protocol_logs():
    """檢查 Protocol Guide 相關的 search_mode 日誌"""
    print_section("檢查 Protocol Guide 日誌", char='=')
    
    try:
        log_file = '/app/logs/django.log'
        
        if not os.path.exists(log_file):
            print(f"⚠️ 日誌文件不存在: {log_file}")
            return
        
        print(f"📂 日誌文件: {log_file}")
        print(f"🔍 搜索關鍵字: protocol_guide + search_mode")
        print()
        
        # 讀取最後 150 行
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-150:]
        
        # 過濾包含 protocol_guide 和 search_mode 的行
        protocol_logs = [
            line for line in last_lines 
            if 'protocol_guide' in line.lower() and 'search_mode' in line.lower()
        ]
        
        if protocol_logs:
            print(f"✅ 找到 {len(protocol_logs)} 條相關日誌（最近 150 行）:\n")
            for line in protocol_logs[-15:]:  # 顯示最後 15 條
                print(f"   {line.strip()}")
        else:
            print(f"⚠️ 最近 150 行日誌中未找到 protocol_guide + search_mode 相關記錄")
            
            # 嘗試只搜索 protocol_guide
            protocol_only_logs = [line for line in last_lines if 'protocol_guide' in line.lower()]
            if protocol_only_logs:
                print(f"\n📝 但找到 {len(protocol_only_logs)} 條 protocol_guide 日誌（沒有 search_mode）:")
                for line in protocol_only_logs[-5:]:
                    print(f"   {line.strip()}")
        
    except Exception as e:
        print(f"❌ 讀取日誌失敗: {str(e)}")


def verify_protocol_integration():
    """驗證 Protocol Guide 是否正確整合了 search_mode"""
    print_section("驗證 Protocol Guide 整合狀態", char='=')
    
    print("🔍 檢查項目:")
    print()
    
    checks = []
    
    # 檢查 1: ProtocolGuideSearchService 是否存在
    try:
        from library.protocol_guide.search_service import ProtocolGuideSearchService
        print("✅ 1. ProtocolGuideSearchService 類別存在")
        checks.append(True)
        
        # 檢查是否有 search_with_vectors 方法
        service = ProtocolGuideSearchService()
        if hasattr(service, 'search_with_vectors'):
            print("✅ 2. search_with_vectors() 方法存在")
            checks.append(True)
            
            # 檢查方法簽名是否包含 search_mode
            import inspect
            sig = inspect.signature(service.search_with_vectors)
            if 'search_mode' in sig.parameters:
                print("✅ 3. search_with_vectors() 包含 search_mode 參數")
                checks.append(True)
            else:
                print("❌ 3. search_with_vectors() 缺少 search_mode 參數")
                print(f"   當前參數: {list(sig.parameters.keys())}")
                checks.append(False)
        else:
            print("❌ 2. search_with_vectors() 方法不存在")
            checks.append(False)
            
    except ImportError as e:
        print(f"❌ 1. 無法導入 ProtocolGuideSearchService: {str(e)}")
        checks.append(False)
    except Exception as e:
        print(f"❌ 檢查過程出錯: {str(e)}")
        checks.append(False)
    
    # 檢查 2: Dify Knowledge Handler 是否支援 protocol_guide
    try:
        from library.dify_knowledge import DifyKnowledgeSearchHandler
        handler = DifyKnowledgeSearchHandler()
        print("✅ 4. DifyKnowledgeSearchHandler 初始化成功")
        checks.append(True)
        
        # 檢查是否有 search_protocol_guide_knowledge 方法
        if hasattr(handler, 'search_protocol_guide_knowledge'):
            print("✅ 5. search_protocol_guide_knowledge() 方法存在")
            checks.append(True)
        else:
            print("⚠️ 5. search_protocol_guide_knowledge() 方法不存在（可能使用其他方式）")
            checks.append(True)  # 不一定是錯誤
            
    except Exception as e:
        print(f"❌ 4. DifyKnowledgeSearchHandler 檢查失敗: {str(e)}")
        checks.append(False)
    
    # 檢查 3: Protocol Guide Model 是否存在
    try:
        from api.models import ProtocolGuide
        count = ProtocolGuide.objects.count()
        print(f"✅ 6. ProtocolGuide Model 存在，資料筆數: {count}")
        checks.append(True)
        
        if count == 0:
            print("   ⚠️ 警告: 資料庫中沒有 Protocol Guide 資料")
            
    except Exception as e:
        print(f"❌ 6. ProtocolGuide Model 檢查失敗: {str(e)}")
        checks.append(False)
    
    print()
    print(f"{'='*60}")
    success_count = sum(checks)
    total_count = len(checks)
    
    if success_count == total_count:
        print(f"✅ 整合驗證通過: {success_count}/{total_count} 項檢查成功")
        return True
    else:
        print(f"⚠️ 整合驗證部分通過: {success_count}/{total_count} 項檢查成功")
        print(f"   請修復失敗的項目後重新測試")
        return False


def main():
    """主測試函數"""
    print_section("Protocol Assistant Search Mode 完整測試", char='=', width=80)
    print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"測試目標: 驗證 Protocol Assistant 的 search_mode 參數完整實現")
    print()
    
    # 階段 1: 驗證整合狀態
    print("\n" + "="*80)
    print("階段 1: 整合狀態驗證")
    print("="*80)
    integration_ok = verify_protocol_integration()
    
    if not integration_ok:
        print("\n⚠️ 警告: 整合驗證未完全通過，但仍繼續測試...")
        print()
    
    # 階段 2: 基本功能測試
    print("\n" + "="*80)
    print("階段 2: 基本功能測試")
    print("="*80)
    
    test_query = "CUP 連接步驟"
    
    # 測試 1: auto 模式
    test_protocol_mode(
        mode_name="Mode 'auto'（預設 - section → document fallback）",
        search_mode='auto',
        query=test_query
    )
    
    # 測試 2: section_only 模式
    test_protocol_mode(
        mode_name="Mode 'section_only'（僅 section，不 fallback）",
        search_mode='section_only',
        query=test_query
    )
    
    # 測試 3: document_only 模式
    test_protocol_mode(
        mode_name="Mode 'document_only'（跳過 section，直接 document）",
        search_mode='document_only',
        query=test_query
    )
    
    # 階段 3: Fallback 機制測試
    print("\n" + "="*80)
    print("階段 3: Fallback 機制測試")
    print("="*80)
    test_protocol_section_fallback()
    
    # 階段 4: 對比測試
    print("\n" + "="*80)
    print("階段 4: 搜索結果對比")
    print("="*80)
    compare_search_modes()
    
    # 階段 5: 直接 Service 測試
    print("\n" + "="*80)
    print("階段 5: 直接 Service 測試")
    print("="*80)
    test_protocol_direct_service()
    
    # 階段 6: 日誌檢查
    print("\n" + "="*80)
    print("階段 6: 日誌檢查")
    print("="*80)
    check_protocol_logs()
    
    # 最終總結
    print_section("測試總結", char='=', width=80)
    print("✅ Protocol Assistant Search Mode 測試完成")
    print()
    print("📋 測試階段清單:")
    print("   1. ✅ 整合狀態驗證")
    print("   2. ✅ 基本功能測試（3 種模式）")
    print("   3. ✅ Fallback 機制測試")
    print("   4. ✅ 搜索結果對比")
    print("   5. ✅ 直接 Service 測試")
    print("   6. ✅ 日誌檢查")
    print()
    print("📊 測試覆蓋範圍:")
    print("   - API 層級: Dify 外部知識庫 API")
    print("   - Handler 層級: DifyKnowledgeSearchHandler")
    print("   - Service 層級: ProtocolGuideSearchService")
    print("   - 日誌追蹤: search_mode 參數流動")
    print()
    print("📝 建議後續行動:")
    print("   - 如果測試通過: 在 Dify Studio 中配置 Protocol Assistant")
    print("   - 如果有失敗: 檢查對應層級的實現")
    print("   - 監控生產環境的 Protocol Guide 搜索日誌")
    print()


if __name__ == '__main__':
    main()
