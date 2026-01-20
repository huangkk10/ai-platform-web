"""
測試 Know Issue 搜尋服務

執行方式：
docker exec ai-django python test_know_issue_search.py
"""

import os
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.know_issue.search_service import KnowIssueSearchService
from api.models import KnowIssue
from django.db import connection


def test_initialization():
    """測試 1: KnowIssueSearchService 初始化"""
    print("=" * 60)
    print("測試 1: KnowIssueSearchService 初始化")
    print("=" * 60)
    
    try:
        service = KnowIssueSearchService()
        print("✅ KnowIssueSearchService 初始化成功")
        print(f"   - Source Table: {service.source_table}")
        print(f"   - Model Class: {service.model_class.__name__}")
        print(f"   - Search Fields: {service.default_search_fields}")
        return service
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_data_count():
    """測試 2: 檢查資料數量"""
    print("\n" + "=" * 60)
    print("測試 2: Know Issue 資料數量")
    print("=" * 60)
    
    try:
        count = KnowIssue.objects.count()
        print(f"✅ Know Issue 資料數量: {count} 筆")
        
        if count > 0:
            print("\n前 3 筆資料範例：")
            for i, issue in enumerate(KnowIssue.objects.all()[:3], 1):
                print(f"\n[{i}] Issue ID: {issue.issue_id}")
                print(f"    Project: {issue.project}")
                print(f"    Test Class: {issue.test_class.name if issue.test_class else 'N/A'}")
                print(f"    Error Message: {issue.error_message[:80]}...")
        
        return count > 0
    except Exception as e:
        print(f"❌ 查詢失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_keyword_search(service):
    """測試 3: 關鍵字搜尋"""
    print("\n" + "=" * 60)
    print("測試 3: 關鍵字搜尋（不使用向量）")
    print("=" * 60)
    
    test_queries = ['YMTC', 'ULINK', 'PC300']
    
    for query in test_queries:
        print(f"\n查詢: '{query}'")
        try:
            results = service.search_knowledge(
                query=query,
                limit=3,
                use_vector=False  # 只用關鍵字
            )
            print(f"✅ 找到 {len(results)} 個結果")
            
            for i, result in enumerate(results, 1):
                print(f"   [{i}] Issue ID: {result.get('issue_id', 'N/A')}")
                print(f"       Project: {result.get('project', 'N/A')}")
                print(f"       Score: {result.get('score', 0):.2%}")
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")


def test_vector_availability():
    """測試 4: 檢查向量是否存在"""
    print("\n" + "=" * 60)
    print("測試 4: 檢查 know_issue 向量資料")
    print("=" * 60)
    
    try:
        with connection.cursor() as cursor:
            # 檢查 document_embeddings 表中 know_issue 的向量數量
            cursor.execute("""
                SELECT COUNT(*) 
                FROM document_embeddings 
                WHERE source_table = 'know_issue'
            """)
            vector_count = cursor.fetchone()[0]
            
            print(f"向量數量: {vector_count} 個")
            
            if vector_count > 0:
                print("✅ Know Issue 已有向量資料")
                
                # 查看向量詳情
                cursor.execute("""
                    SELECT 
                        source_id,
                        LEFT(text_content, 100) as preview,
                        vector_dims(embedding) as dims,
                        created_at
                    FROM document_embeddings 
                    WHERE source_table = 'know_issue'
                    ORDER BY created_at DESC
                    LIMIT 3
                """)
                
                print("\n最新的 3 個向量：")
                for row in cursor.fetchall():
                    print(f"   - Source ID: {row[0]}")
                    print(f"     Content: {row[1]}...")
                    print(f"     Dimensions: {row[2]}")
                    print(f"     Created: {row[3]}")
                    print()
                
                return True
            else:
                print("⚠️  Know Issue 尚未生成向量")
                print("   需要執行向量生成腳本")
                return False
                
    except Exception as e:
        print(f"❌ 檢查失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vector_search(service):
    """測試 5: 向量搜尋（如果向量存在）"""
    print("\n" + "=" * 60)
    print("測試 5: 向量搜尋")
    print("=" * 60)
    
    test_queries = ['YMTC PC300 錯誤', 'ULINK 問題']
    
    for query in test_queries:
        print(f"\n查詢: '{query}'")
        try:
            results = service.search_knowledge(
                query=query,
                limit=3,
                use_vector=True,
                threshold=0.6
            )
            
            if results:
                print(f"✅ 找到 {len(results)} 個結果")
                
                for i, result in enumerate(results, 1):
                    print(f"   [{i}] Issue ID: {result.get('issue_id', 'N/A')}")
                    print(f"       Project: {result.get('project', 'N/A')}")
                    print(f"       Score: {result.get('score', 0):.2%}")
            else:
                print("⚠️  無搜尋結果")
                
        except Exception as e:
            print(f"❌ 搜尋失敗: {e}")
            import traceback
            traceback.print_exc()


def main():
    """執行所有測試"""
    print("\n" + "🔍" * 30)
    print("Know Issue 搜尋服務測試")
    print("🔍" * 30 + "\n")
    
    # 測試 1: 初始化
    service = test_initialization()
    if not service:
        print("\n❌ 初始化失敗，終止測試")
        return
    
    # 測試 2: 資料數量
    has_data = test_data_count()
    if not has_data:
        print("\n❌ 沒有資料，終止測試")
        return
    
    # 測試 3: 關鍵字搜尋
    test_keyword_search(service)
    
    # 測試 4: 檢查向量
    has_vectors = test_vector_availability()
    
    # 測試 5: 向量搜尋（如果有向量）
    if has_vectors:
        test_vector_search(service)
    else:
        print("\n⚠️  跳過向量搜尋測試（無向量資料）")
    
    # 總結
    print("\n" + "=" * 60)
    print("測試總結")
    print("=" * 60)
    print(f"✅ Service 初始化: 成功")
    print(f"✅ 資料檢查: {KnowIssue.objects.count()} 筆資料")
    print(f"{'✅' if has_vectors else '⚠️ '} 向量資料: {'已生成' if has_vectors else '尚未生成'}")
    
    if not has_vectors:
        print("\n💡 下一步：執行向量生成腳本")
        print("   指令：docker exec ai-django python generate_know_issue_vectors.py")


if __name__ == "__main__":
    main()
