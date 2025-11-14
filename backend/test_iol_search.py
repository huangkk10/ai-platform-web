#!/usr/bin/env python
"""
測試查詢 "iol" 的向量搜尋結果

執行方式：
docker exec ai-django python test_iol_search.py
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_platform.settings')
django.setup()

from api.services.embedding_service import get_embedding_service
from api.models import SearchThresholdSetting
from django.db import connection

# 顏色輸出
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(description):
    print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
    print(f"{Colors.BLUE}{description}{Colors.NC}")
    print(f"{Colors.BLUE}{'='*70}{Colors.NC}")

print_header("測試查詢 'iol' 的向量搜尋")

# 1. 獲取當前 Threshold 設定
print(f"\n{Colors.YELLOW}📊 當前 Protocol Assistant Threshold 設定:{Colors.NC}")
try:
    setting = SearchThresholdSetting.objects.get(assistant_type='protocol_assistant')
    print(f"  Stage1 Threshold: {float(setting.stage1_threshold)*100:.0f}%")
    print(f"  Stage1 Weights: Title={setting.stage1_title_weight}%, Content={setting.stage1_content_weight}%")
    print(f"  Stage2 Threshold: {float(setting.stage2_threshold)*100:.0f}%")
except Exception as e:
    print(f"{Colors.RED}✗ 無法載入設定: {e}{Colors.NC}")
    setting = None

# 2. 測試 Stage1 搜尋（段落向量）
print(f"\n{Colors.YELLOW}🔍 Stage1 搜尋測試 (段落向量):{Colors.NC}")
print(f"  查詢字串: 'iol'")
print(f"  Threshold: {float(setting.stage1_threshold)*100:.0f}%")

service = get_embedding_service()

try:
    # 執行搜尋
    results = service.search_similar_documents(
        query='iol',
        source_table='protocol_guide',
        limit=5,
        threshold=float(setting.stage1_threshold) if setting else 0.80,
        use_1024_table=False
    )
    
    print(f"\n  找到 {len(results)} 筆結果:")
    
    if len(results) == 0:
        print(f"  {Colors.RED}✗ 沒有找到任何結果！{Colors.NC}")
    else:
        for i, result in enumerate(results, 1):
            similarity = result.get('similarity', 0)
            title = result.get('title', 'N/A')
            content_preview = result.get('content', '')[:100]
            
            color = Colors.GREEN if similarity >= 0.80 else Colors.YELLOW
            print(f"\n  {color}結果 {i}:{Colors.NC}")
            print(f"    相似度: {similarity:.2%}")
            print(f"    標題: {title}")
            print(f"    內容預覽: {content_preview}...")
            
except Exception as e:
    print(f"{Colors.RED}✗ 搜尋失敗: {e}{Colors.NC}")
    import traceback
    traceback.print_exc()

# 3. 手動計算 UNH-IOL 的相似度
print(f"\n{Colors.YELLOW}🧮 手動計算 UNH-IOL (ID=10) 的相似度:{Colors.NC}")

try:
    # 生成查詢向量
    query_embedding = service.generate_embedding('iol')
    
    # 查詢 UNH-IOL 的向量並計算相似度
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                source_id,
                text_content,
                1 - (embedding <=> %s::vector) as similarity
            FROM document_embeddings
            WHERE source_table = 'protocol_guide' 
              AND source_id = 10
            ORDER BY similarity DESC
            LIMIT 1;
        """, [query_embedding])
        
        row = cursor.fetchone()
        if row:
            source_id, text_content, similarity = row
            print(f"\n  Document ID: {source_id}")
            print(f"  相似度: {similarity:.4f} ({similarity*100:.2f}%)")
            print(f"  內容預覽: {text_content[:100]}...")
            
            # 與 Threshold 比較
            threshold = float(setting.stage1_threshold) if setting else 0.80
            if similarity >= threshold:
                print(f"  {Colors.GREEN}✓ 相似度 >= Threshold ({threshold*100:.0f}%) - 應該被找到{Colors.NC}")
            else:
                print(f"  {Colors.RED}✗ 相似度 < Threshold ({threshold*100:.0f}%) - 被過濾掉了！{Colors.NC}")
                print(f"  {Colors.YELLOW}💡 建議：降低 Threshold 到 {similarity*100:.0f}% 以下{Colors.NC}")
        else:
            print(f"  {Colors.RED}✗ 找不到 ID=10 的向量資料{Colors.NC}")
            
except Exception as e:
    print(f"{Colors.RED}✗ 計算失敗: {e}{Colors.NC}")
    import traceback
    traceback.print_exc()

# 4. 測試不同查詢字串
print(f"\n{Colors.YELLOW}🔬 測試不同查詢字串的相似度:{Colors.NC}")

test_queries = [
    'iol',
    'IOL',
    'unh-iol',
    'UNH-IOL',
    'UNH IOL',
]

for query in test_queries:
    try:
        query_embedding = service.generate_embedding(query)
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    1 - (embedding <=> %s::vector) as similarity
                FROM document_embeddings
                WHERE source_table = 'protocol_guide' 
                  AND source_id = 10
                LIMIT 1;
            """, [query_embedding])
            
            row = cursor.fetchone()
            if row:
                similarity = row[0]
                threshold = float(setting.stage1_threshold) if setting else 0.80
                status = '✓' if similarity >= threshold else '✗'
                color = Colors.GREEN if similarity >= threshold else Colors.RED
                
                print(f"  {color}{status}{Colors.NC} 查詢: '{query:15}' → 相似度: {similarity:.4f} ({similarity*100:.2f}%)")
    except Exception as e:
        print(f"  {Colors.RED}✗ 查詢 '{query}' 失敗: {e}{Colors.NC}")

# 5. 檢查所有 protocol_guide 的向量相似度
print(f"\n{Colors.YELLOW}📋 所有 Protocol Guide 文件與 'iol' 的相似度 (Top 10):{Colors.NC}")

try:
    query_embedding = service.generate_embedding('iol')
    
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                de.source_id,
                pg.title,
                1 - (de.embedding <=> %s::vector) as similarity
            FROM document_embeddings de
            JOIN protocol_guide pg ON de.source_id = pg.id
            WHERE de.source_table = 'protocol_guide'
            ORDER BY similarity DESC
            LIMIT 10;
        """, [query_embedding])
        
        rows = cursor.fetchall()
        threshold = float(setting.stage1_threshold) if setting else 0.80
        
        for i, (source_id, title, similarity) in enumerate(rows, 1):
            status = '✓' if similarity >= threshold else '✗'
            color = Colors.GREEN if similarity >= threshold else Colors.RED
            
            print(f"  {color}{status}{Colors.NC} {i:2}. ID={source_id:3} | {similarity:.4f} ({similarity*100:.2f}%) | {title}")
            
except Exception as e:
    print(f"{Colors.RED}✗ 查詢失敗: {e}{Colors.NC}")

print(f"\n{Colors.BLUE}{'='*70}{Colors.NC}")
print(f"{Colors.YELLOW}📝 總結:{Colors.NC}")
print(f"  1. 如果相似度 < Threshold，資料會被過濾掉")
print(f"  2. 當前 Protocol Assistant Threshold = {float(setting.stage1_threshold)*100:.0f}%")
print(f"  3. 建議根據實際相似度調整 Threshold 設定")
print(f"{Colors.BLUE}{'='*70}{Colors.NC}\n")
