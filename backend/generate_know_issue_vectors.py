"""
為 Know Issue 資料生成向量

執行方式：
docker exec ai-django python generate_know_issue_vectors.py
"""

import os
import django

# 設置 Django 環境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from library.know_issue.vector_service import KnowIssueVectorService
from api.models import KnowIssue
import time


def main():
    """為所有 Know Issue 生成向量"""
    print("\n" + "🚀" * 30)
    print("Know Issue 向量生成工具")
    print("🚀" * 30 + "\n")
    
    # 初始化服務
    print("步驟 1: 初始化向量服務...")
    try:
        service = KnowIssueVectorService()
        print("✅ KnowIssueVectorService 初始化成功")
        print(f"   - Source Table: {service.source_table}")
        print(f"   - Model Class: {service.model_class.__name__}")
    except Exception as e:
        print(f"❌ 初始化失敗: {e}")
        return
    
    # 獲取所有 Know Issue
    print("\n步驟 2: 獲取所有 Know Issue 資料...")
    issues = KnowIssue.objects.all().order_by('id')
    total = issues.count()
    print(f"✅ 找到 {total} 筆 Know Issue 資料")
    
    if total == 0:
        print("❌ 沒有資料需要處理")
        return
    
    # 生成向量
    print(f"\n步驟 3: 開始生成向量（總共 {total} 筆）...")
    print("-" * 60)
    
    success_count = 0
    fail_count = 0
    start_time = time.time()
    
    for i, issue in enumerate(issues, 1):
        try:
            print(f"\n[{i}/{total}] 處理 Issue ID: {issue.issue_id}")
            print(f"   Project: {issue.project}")
            print(f"   Error: {issue.error_message[:60]}...")
            
            # 生成並存儲向量
            service.generate_and_store_vector(issue)
            
            success_count += 1
            print(f"   ✅ 向量生成成功")
            
        except Exception as e:
            fail_count += 1
            print(f"   ❌ 失敗: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # 顯示進度
        progress = (i / total) * 100
        print(f"   進度: {progress:.1f}% ({i}/{total})")
    
    # 總結
    elapsed = time.time() - start_time
    print("\n" + "=" * 60)
    print("生成完成！")
    print("=" * 60)
    print(f"✅ 成功: {success_count} 筆")
    print(f"❌ 失敗: {fail_count} 筆")
    print(f"⏱️  耗時: {elapsed:.2f} 秒")
    print(f"⚡ 平均速度: {elapsed/total:.2f} 秒/筆")
    
    # 驗證結果
    print("\n步驟 4: 驗證向量生成結果...")
    from django.db import connection
    
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM document_embeddings 
                WHERE source_table = 'know_issue'
            """)
            vector_count = cursor.fetchone()[0]
            
            print(f"✅ 向量表中的記錄數: {vector_count}")
            
            if vector_count == success_count:
                print("✅ 驗證通過：向量數量與成功數量一致")
            else:
                print(f"⚠️  向量數量 ({vector_count}) 與成功數量 ({success_count}) 不一致")
                
    except Exception as e:
        print(f"❌ 驗證失敗: {e}")
    
    print("\n" + "🎉" * 30)
    print("向量生成完成！現在可以使用語義搜尋了")
    print("🎉" * 30 + "\n")


if __name__ == "__main__":
    main()
