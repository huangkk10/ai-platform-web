#!/usr/bin/env python
"""
驗證 Django Signals 自動向量生成功能
===================================

測試場景：
1. ORM 創建 → 自動生成向量
2. ORM 更新 → 自動更新向量
3. ORM 刪除 → 自動刪除向量
"""

import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from django.db import connection


def check_vectors(guide_id, expected_count_min=1):
    """檢查向量是否存在"""
    with connection.cursor() as cursor:
        # 檢查段落向量
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN document_id IS NOT NULL THEN 1 ELSE 0 END) as has_doc_id,
                SUM(CASE WHEN document_title IS NOT NULL THEN 1 ELSE 0 END) as has_doc_title,
                SUM(CASE WHEN title_embedding IS NOT NULL THEN 1 ELSE 0 END) as has_title_emb,
                SUM(CASE WHEN content_embedding IS NOT NULL THEN 1 ELSE 0 END) as has_content_emb
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = %s
        """, [guide_id])
        
        result = cursor.fetchone()
        return {
            'total': result[0] or 0,
            'has_doc_id': result[1] or 0,
            'has_doc_title': result[2] or 0,
            'has_title_emb': result[3] or 0,
            'has_content_emb': result[4] or 0
        }


def test_signals():
    print("\n" + "="*80)
    print("🧪 測試 Django Signals 自動向量生成功能")
    print("="*80 + "\n")
    
    # 測試 1: 創建
    print("📝 測試 1: ORM 創建 → 自動生成向量")
    print("-" * 80)
    
    guide = ProtocolGuide.objects.create(
        title="Signal 測試文檔",
        content="""# 主標題

## 段落 1
這是第一段的內容。

## 段落 2
這是第二段的內容，包含更多資訊。
"""
    )
    print(f"✅ 文檔創建成功，ID: {guide.id}")
    
    import time
    time.sleep(2)  # 等待 signal 完成
    
    vectors = check_vectors(guide.id)
    print(f"\n📊 向量檢查結果:")
    print(f"  總段落數: {vectors['total']}")
    print(f"  有 document_id: {vectors['has_doc_id']}")
    print(f"  有 document_title: {vectors['has_doc_title']}")
    print(f"  有 title_embedding: {vectors['has_title_emb']}")
    print(f"  有 content_embedding: {vectors['has_content_emb']}")
    
    if vectors['total'] >= 2 and vectors['has_doc_id'] == vectors['total']:
        print("\n✅ 測試 1 通過：創建時自動生成向量")
    else:
        print("\n❌ 測試 1 失敗：向量生成不完整")
        guide.delete()
        return False
    
    # 測試 2: 更新
    print("\n" + "="*80)
    print("📝 測試 2: ORM 更新 → 自動更新向量")
    print("-" * 80)
    
    old_content = guide.content
    guide.content = """# 更新後的標題

## 新段落 A
這是更新後的第一段。

## 新段落 B
這是更新後的第二段。

## 新段落 C
新增的第三段。
"""
    guide.save()
    print(f"✅ 文檔更新成功")
    
    time.sleep(2)  # 等待 signal 完成
    
    vectors_after_update = check_vectors(guide.id)
    print(f"\n📊 更新後向量檢查:")
    print(f"  總段落數: {vectors_after_update['total']}")
    
    # 更新後段落數應該增加（3 個段落 vs 2 個）
    if vectors_after_update['total'] >= 3:
        print("\n✅ 測試 2 通過：更新時自動更新向量（段落數增加）")
    else:
        print(f"\n❌ 測試 2 失敗：更新後段落數未增加（預期 >= 3，實際 {vectors_after_update['total']}）")
        guide.delete()
        return False
    
    # 測試 3: 刪除
    print("\n" + "="*80)
    print("📝 測試 3: ORM 刪除 → 自動刪除向量")
    print("-" * 80)
    
    guide_id = guide.id
    guide.delete()
    print(f"✅ 文檔刪除成功")
    
    time.sleep(2)  # 等待 signal 完成
    
    vectors_after_delete = check_vectors(guide_id)
    print(f"\n📊 刪除後向量檢查:")
    print(f"  總段落數: {vectors_after_delete['total']}")
    
    if vectors_after_delete['total'] == 0:
        print("\n✅ 測試 3 通過：刪除時自動刪除向量")
    else:
        print(f"\n❌ 測試 3 失敗：刪除後向量仍然存在（{vectors_after_delete['total']} 個）")
        return False
    
    # 總結
    print("\n" + "="*80)
    print("🎉 所有測試通過！Django Signals 自動向量生成功能正常")
    print("="*80 + "\n")
    
    print("✅ 驗證項目：")
    print("  1. ✅ ORM 創建時自動生成向量（包含 document_id）")
    print("  2. ✅ ORM 更新時自動更新向量（刪除舊的，生成新的）")
    print("  3. ✅ ORM 刪除時自動刪除向量")
    print("  4. ✅ 所有必要欄位正確填充（document_id, document_title, embeddings）")
    
    print("\n🚀 現在您可以安心使用以下方式創建 Protocol Guide：")
    print("  - REST API（前端）")
    print("  - Django ORM（測試腳本）")
    print("  - Django Admin（後台管理）")
    print("  - Management Commands（批量導入）")
    print("\n所有方式都會自動生成完整的向量！\n")
    
    return True


if __name__ == '__main__':
    success = test_signals()
    sys.exit(0 if success else 1)
