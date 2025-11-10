#!/usr/bin/env python
"""
測試新建立 Protocol Guide 是否正確產生所有必要欄位
==================================================

測試項目：
1. 創建新的 Protocol Guide
2. 驗證段落向量是否正確生成
3. 驗證所有必要欄位是否填充（包括 document_id, document_title）
4. 驗證多向量是否完整（embedding, title_embedding, content_embedding）
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.models import ProtocolGuide
from django.db import connection
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def test_new_protocol_guide_creation():
    """測試新建 Protocol Guide 的完整流程"""
    
    print("\n" + "="*80)
    print("🧪 測試新建 Protocol Guide 的向量生成")
    print("="*80 + "\n")
    
    # 1. 創建測試文檔
    test_content = """# 測試文檔標題

## 第一段：介紹
這是第一段的內容，用於測試向量生成。

## 第二段：功能
這是第二段的內容，包含功能說明。

## 第三段：結論
這是第三段的內容，總結測試。
"""
    
    print("📝 創建測試 Protocol Guide...")
    try:
        guide = ProtocolGuide.objects.create(
            title="測試向量生成完整性",
            content=test_content
        )
        print(f"✅ 文檔創建成功，ID: {guide.id}")
    except Exception as e:
        print(f"❌ 文檔創建失敗: {str(e)}")
        return False
    
    # 2. 等待向量生成（應該是同步的）
    import time
    time.sleep(2)
    
    # 3. 檢查段落向量
    print(f"\n🔍 檢查文檔 {guide.id} 的段落向量...")
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                section_id,
                heading_text,
                document_id,
                document_title,
                embedding IS NOT NULL as has_embedding,
                title_embedding IS NOT NULL as has_title_emb,
                content_embedding IS NOT NULL as has_content_emb,
                vector_dims(embedding) as embedding_dim,
                vector_dims(title_embedding) as title_dim,
                vector_dims(content_embedding) as content_dim
            FROM document_section_embeddings
            WHERE source_table = 'protocol_guide' AND source_id = %s
            ORDER BY section_id;
        """, [guide.id])
        
        sections = cursor.fetchall()
    
    if not sections:
        print(f"❌ 沒有找到段落向量！文檔 {guide.id} 的向量生成失敗")
        # 清理測試數據
        guide.delete()
        return False
    
    # 4. 驗證結果
    print(f"\n📊 找到 {len(sections)} 個段落向量：\n")
    
    all_pass = True
    for section in sections:
        (section_id, heading_text, document_id, document_title,
         has_embedding, has_title_emb, has_content_emb,
         embedding_dim, title_dim, content_dim) = section
        
        print(f"段落 {section_id}: {heading_text}")
        print(f"  document_id: {document_id or '❌ NULL'}")
        print(f"  document_title: {document_title or '❌ NULL'}")
        print(f"  embedding: {'✅' if has_embedding else '❌'} ({embedding_dim} 維)")
        print(f"  title_embedding: {'✅' if has_title_emb else '❌'} ({title_dim} 維)")
        print(f"  content_embedding: {'✅' if has_content_emb else '❌'} ({content_dim} 維)")
        
        # 檢查必要欄位
        checks = {
            'document_id': document_id is not None and document_id != '',
            'document_title': document_title is not None and document_title != '',
            'embedding': has_embedding and embedding_dim == 1024,
            'title_embedding': has_title_emb and title_dim == 1024,
            'content_embedding': has_content_emb and content_dim == 1024
        }
        
        section_pass = all(checks.values())
        print(f"  狀態: {'✅ PASS' if section_pass else '❌ FAIL'}\n")
        
        if not section_pass:
            all_pass = False
            print(f"  失敗項目:")
            for field, passed in checks.items():
                if not passed:
                    print(f"    - {field}")
            print()
    
    # 5. 總結
    print("\n" + "="*80)
    if all_pass:
        print("🎉 測試通過！所有段落向量都正確生成了必要欄位")
        print("="*80 + "\n")
        
        print("✅ 驗證項目：")
        print("  1. document_id 欄位已填充（格式：protocol_guide_{id}）")
        print("  2. document_title 欄位已填充")
        print("  3. embedding 向量已生成（1024 維）")
        print("  4. title_embedding 向量已生成（1024 維）")
        print("  5. content_embedding 向量已生成（1024 維）")
        
    else:
        print("❌ 測試失敗！部分段落向量缺少必要欄位")
        print("="*80 + "\n")
    
    # 6. 清理測試數據
    print(f"\n🧹 清理測試數據（刪除文檔 {guide.id}）...")
    guide.delete()
    print("✅ 測試數據已清理\n")
    
    return all_pass


if __name__ == '__main__':
    success = test_new_protocol_guide_creation()
    sys.exit(0 if success else 1)
