#!/usr/bin/env python3
"""
段落搜尋 API 測試腳本
===================

測試新整合的三個 API：
1. search_sections - 段落級別搜尋
2. compare_search - 新舊系統對比
3. regenerate_section_vectors - 批量生成段落向量

使用方式：
    python tests/test_section_search_api.py
"""

import sys
import os
import django
import json
from datetime import datetime

# 設置 Django 環境
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from rest_framework.test import APIRequestFactory, force_authenticate
from django.contrib.auth.models import User
from api.views.viewsets.knowledge_viewsets import ProtocolGuideViewSet


class APITester:
    """API 測試工具"""
    
    def __init__(self):
        self.factory = APIRequestFactory()
        
        # 獲取或創建測試用戶
        self.user, _ = User.objects.get_or_create(
            username='test_user',
            defaults={'is_staff': True, 'is_superuser': True}
        )
        
        print("=" * 80)
        print("🧪 Protocol Guide 段落搜尋 API 測試")
        print("=" * 80)
        print(f"測試時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"測試用戶: {self.user.username}")
        print()
    
    def test_search_sections(self):
        """測試 1: 段落級別搜尋 API"""
        print("\n" + "=" * 80)
        print("📍 測試 1: 段落級別搜尋 API")
        print("=" * 80)
        
        # 測試查詢
        test_queries = [
            {
                'query': 'ULINK 連接失敗',
                'limit': 3,
                'threshold': 0.7
            },
            {
                'query': '測試環境準備',
                'limit': 5,
                'threshold': 0.6,
                'with_context': True,
                'context_window': 1
            },
            {
                'query': 'Samsung Protocol',
                'limit': 3,
                'min_level': 2,
                'max_level': 3
            }
        ]
        
        for i, query_data in enumerate(test_queries, 1):
            print(f"\n查詢 {i}: {query_data['query']}")
            print(f"參數: {json.dumps(query_data, ensure_ascii=False, indent=2)}")
            
            # 創建請求
            request = self.factory.post(
                '/api/protocol-guides/search_sections/',
                data=query_data,
                format='json'
            )
            force_authenticate(request, user=self.user)
            
            # 執行 API
            view = ProtocolGuideViewSet.as_view({'post': 'search_sections'})
            response = view(request)
            
            # 顯示結果
            if response.status_code == 200:
                data = response.data
                print(f"\n✅ 搜尋成功!")
                print(f"找到 {data['total']} 個結果:")
                
                for j, result in enumerate(data['results'], 1):
                    print(f"\n  結果 {j}:")
                    print(f"    標題: {result['section_title']}")
                    print(f"    路徑: {result['section_path']}")
                    print(f"    相似度: {result['similarity']:.2%}")
                    print(f"    層級: Level {result['level']}")
                    content_preview = result['content'][:100] + '...' if len(result['content']) > 100 else result['content']
                    print(f"    內容預覽: {content_preview}")
            else:
                print(f"\n❌ 搜尋失敗: {response.status_code}")
                print(f"錯誤訊息: {response.data}")
    
    def test_compare_search(self):
        """測試 2: 新舊系統對比 API"""
        print("\n" + "=" * 80)
        print("📍 測試 2: 新舊系統對比 API")
        print("=" * 80)
        
        query_data = {
            'query': 'ULINK 測試環境準備',
            'limit': 3
        }
        
        print(f"\n查詢: {query_data['query']}")
        
        # 創建請求
        request = self.factory.post(
            '/api/protocol-guides/compare_search/',
            data=query_data,
            format='json'
        )
        force_authenticate(request, user=self.user)
        
        # 執行 API
        view = ProtocolGuideViewSet.as_view({'post': 'compare_search'})
        response = view(request)
        
        # 顯示結果
        if response.status_code == 200:
            data = response.data
            print(f"\n✅ 對比搜尋成功!\n")
            
            # 舊系統結果
            old_system = data['old_system']
            print("🔵 舊系統 (整篇文檔搜尋):")
            print(f"  平均內容長度: {old_system['avg_content_length']:.0f} 字元")
            print(f"  平均相似度: {old_system['avg_similarity']:.2f}%")
            print(f"  結果數量: {len(old_system['results'])}")
            
            for i, result in enumerate(old_system['results'], 1):
                print(f"\n    結果 {i}:")
                print(f"      標題: {result['title']}")
                print(f"      相似度: {result['similarity']:.2%}")
                print(f"      內容長度: {result['content_length']} 字元")
            
            # 新系統結果
            new_system = data['new_system']
            print(f"\n🟢 新系統 (段落級別搜尋):")
            print(f"  平均內容長度: {new_system['avg_content_length']:.0f} 字元")
            print(f"  平均相似度: {new_system['avg_similarity']:.2f}%")
            print(f"  結果數量: {len(new_system['results'])}")
            
            for i, result in enumerate(new_system['results'], 1):
                print(f"\n    結果 {i}:")
                print(f"      標題: {result['section_title']}")
                print(f"      路徑: {result['section_path']}")
                print(f"      相似度: {result['similarity']:.2%}")
                print(f"      層級: Level {result['level']}")
            
            # 對比結果
            comparison = data['comparison']
            print(f"\n📊 對比分析:")
            print(f"  內容長度減少: {comparison['content_length_reduction']}")
            print(f"  相似度改善: {comparison['similarity_improvement']}")
            print(f"  結論: {comparison['conclusion']}")
        else:
            print(f"\n❌ 對比搜尋失敗: {response.status_code}")
            print(f"錯誤訊息: {response.data}")
    
    def test_regenerate_vectors(self):
        """測試 3: 批量重新生成段落向量 API"""
        print("\n" + "=" * 80)
        print("📍 測試 3: 批量重新生成段落向量 API")
        print("=" * 80)
        
        # 測試重新生成第一個 Guide 的向量
        from api.models import ProtocolGuide
        
        first_guide = ProtocolGuide.objects.first()
        if not first_guide:
            print("\n⚠️  沒有 Protocol Guide 資料，跳過測試")
            return
        
        query_data = {
            'guide_ids': [first_guide.id],
            'force': True  # 強制重新生成
        }
        
        print(f"\n要重新生成的 Guide ID: {query_data['guide_ids']}")
        print(f"強制模式: {query_data['force']}")
        
        # 創建請求
        request = self.factory.post(
            '/api/protocol-guides/regenerate_section_vectors/',
            data=query_data,
            format='json'
        )
        force_authenticate(request, user=self.user)
        
        # 執行 API
        view = ProtocolGuideViewSet.as_view({'post': 'regenerate_section_vectors'})
        response = view(request)
        
        # 顯示結果
        if response.status_code == 200:
            data = response.data
            print(f"\n✅ 批量生成成功!")
            print(f"\n統計:")
            print(f"  處理數量: {data['processed']}")
            print(f"  成功: {data['success']}")
            print(f"  失敗: {data['failed']}")
            
            print(f"\n詳細結果:")
            for detail in data['details']:
                status_icon = "✅" if detail['status'] == 'success' else "❌"
                print(f"  {status_icon} Guide {detail['guide_id']} - {detail['title']}")
                print(f"     生成段落數: {detail.get('sections', 0)}")
                if detail['status'] == 'failed':
                    print(f"     錯誤: {detail.get('error', 'Unknown')}")
        else:
            print(f"\n❌ 批量生成失敗: {response.status_code}")
            print(f"錯誤訊息: {response.data}")
    
    def run_all_tests(self):
        """執行所有測試"""
        try:
            self.test_search_sections()
            self.test_compare_search()
            self.test_regenerate_vectors()
            
            print("\n" + "=" * 80)
            print("🎉 所有測試完成!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 測試過程中發生錯誤: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    tester = APITester()
    tester.run_all_tests()
