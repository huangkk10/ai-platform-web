#!/usr/bin/env python3
"""
測試腳本：驗證 get_embedding_service() 預設使用 1024 維向量

目的：
- 確認預設模型為 ultra_high (1024 維)
- 驗證生成的向量維度正確
- 測試向量可以正確插入資料庫
"""

import os
import sys
import django

# 設定 Django 環境
sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from django.db import connection


def test_default_embedding_dimension():
    """測試 1: 預設 embedding service 使用 1024 維"""
    print("\n" + "="*60)
    print("測試 1: 預設模型維度檢查")
    print("="*60)
    
    try:
        # 不指定模型類型，使用預設值
        service = get_embedding_service()
        
        print(f"✅ 模型類型: {service.model_type}")
        print(f"✅ 模型名稱: {service.model_name}")
        print(f"✅ 向量維度: {service.embedding_dimension}")
        
        # 驗證維度
        if service.embedding_dimension == 1024:
            print("✅ 預設維度正確：1024 維")
            return True
        else:
            print(f"❌ 預設維度錯誤：預期 1024，實際 {service.embedding_dimension}")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False


def test_vector_generation():
    """測試 2: 生成向量並驗證維度"""
    print("\n" + "="*60)
    print("測試 2: 向量生成驗證")
    print("="*60)
    
    try:
        service = get_embedding_service()
        
        # 生成測試向量
        test_texts = [
            "USB Type-C 測試指南",
            "Protocol 測試流程",
            "RVT Assistant 使用說明"
        ]
        
        for i, text in enumerate(test_texts, 1):
            embedding = service.generate_embedding(text)
            print(f"\n測試文本 {i}: {text}")
            print(f"  生成向量維度: {len(embedding)}")
            
            if len(embedding) == 1024:
                print(f"  ✅ 維度正確")
            else:
                print(f"  ❌ 維度錯誤：預期 1024，實際 {len(embedding)}")
                return False
        
        print("\n✅ 所有向量生成測試通過")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_database_insertion():
    """測試 3: 測試向量可以正確插入資料庫"""
    print("\n" + "="*60)
    print("測試 3: 資料庫插入驗證")
    print("="*60)
    
    try:
        service = get_embedding_service()
        
        # 測試資料
        test_source_table = 'test_dimension_check'
        test_source_id = 99999
        test_content = "這是一個測試向量維度的內容，用於驗證 1024 維向量可以正確插入資料庫。"
        
        print(f"\n準備插入測試向量:")
        print(f"  來源表: {test_source_table}")
        print(f"  來源 ID: {test_source_id}")
        print(f"  內容長度: {len(test_content)} 字元")
        
        # 嘗試插入
        success = service.store_document_embedding(
            source_table=test_source_table,
            source_id=test_source_id,
            content=test_content,
            use_1024_table=True
        )
        
        if success:
            print("✅ 向量插入成功")
            
            # 驗證資料庫中的向量維度
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        source_table,
                        source_id,
                        vector_dims(embedding) as dimension,
                        LENGTH(text_content) as content_length
                    FROM document_embeddings
                    WHERE source_table = %s AND source_id = %s
                """, [test_source_table, test_source_id])
                
                result = cursor.fetchone()
                if result:
                    print(f"\n資料庫驗證:")
                    print(f"  來源表: {result[0]}")
                    print(f"  來源 ID: {result[1]}")
                    print(f"  向量維度: {result[2]}")
                    print(f"  內容長度: {result[3]}")
                    
                    if result[2] == 1024:
                        print("✅ 資料庫中的向量維度正確：1024 維")
                    else:
                        print(f"❌ 資料庫中的向量維度錯誤：{result[2]} 維")
                        return False
            
            # 清理測試資料
            print("\n清理測試資料...")
            cleanup_success = service.delete_document_embedding(
                source_table=test_source_table,
                source_id=test_source_id,
                use_1024_table=True
            )
            
            if cleanup_success:
                print("✅ 測試資料清理成功")
            else:
                print("⚠️  測試資料清理失敗（可能需要手動刪除）")
            
            return True
        else:
            print("❌ 向量插入失敗")
            return False
            
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 嘗試清理
        try:
            service.delete_document_embedding(test_source_table, test_source_id, use_1024_table=True)
        except:
            pass
        
        return False


def test_explicit_model_types():
    """測試 4: 驗證可以明確指定不同模型類型"""
    print("\n" + "="*60)
    print("測試 4: 明確指定模型類型")
    print("="*60)
    
    try:
        model_types = {
            'lightweight': 384,
            'standard': 768,
            'high_precision': 768,
            'ultra_high': 1024
        }
        
        for model_type, expected_dim in model_types.items():
            service = get_embedding_service(model_type)
            actual_dim = service.embedding_dimension
            
            if actual_dim == expected_dim:
                print(f"✅ {model_type:15s} → {actual_dim} 維（正確）")
            else:
                print(f"❌ {model_type:15s} → {actual_dim} 維（預期 {expected_dim}）")
                return False
        
        print("\n✅ 所有模型類型驗證通過")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        return False


def main():
    """執行所有測試"""
    print("\n" + "="*60)
    print("🚀 開始測試 get_embedding_service() 預設維度修改")
    print("="*60)
    
    results = []
    
    # 測試 1: 預設維度
    results.append(("預設模型維度檢查", test_default_embedding_dimension()))
    
    # 測試 2: 向量生成
    results.append(("向量生成驗證", test_vector_generation()))
    
    # 測試 3: 資料庫插入
    results.append(("資料庫插入驗證", test_database_insertion()))
    
    # 測試 4: 明確指定模型
    results.append(("明確指定模型類型", test_explicit_model_types()))
    
    # 總結
    print("\n" + "="*60)
    print("📊 測試結果總結")
    print("="*60)
    
    for test_name, result in results:
        status = "✅ 通過" if result else "❌ 失敗"
        print(f"{status} - {test_name}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, result in results if result)
    
    print(f"\n總計: {passed_tests}/{total_tests} 個測試通過")
    
    if passed_tests == total_tests:
        print("\n🎉 所有測試通過！預設維度修改成功！")
        print("✅ get_embedding_service() 現在預設使用 1024 維向量")
        print("✅ 與資料庫維度完全一致")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查錯誤訊息")
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  測試被用戶中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 測試執行失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
