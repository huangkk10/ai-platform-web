# Dify 外部知識庫 API 完整建立指南

## 🎯 概述
本指南詳細記錄如何從零開始建立 Dify 外部知識庫 API，包含後端 API 開發、URL 路由配置、以及 Dify 前端配置的完整流程。

## 📋 系統架構

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Dify AI      │────│   Nginx Proxy    │────│   Django API    │
│   (外部系統)    │    │   (Port 80)      │    │   (Port 8000)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                          │
                                                ┌─────────────────┐
                                                │  PostgreSQL DB  │
                                                │ (多個知識庫)    │
                                                └─────────────────┘
```

## 🔧 後端實作步驟

### 步驟 1：建立資料庫搜索函數

為每個知識庫建立專門的搜索函數：

```python
# backend/api/views.py

def search_know_issue_knowledge(query_text, limit=5):
    """
    在 PostgreSQL 中搜索 Know Issue 知識庫
    """
    try:
        with connection.cursor() as cursor:
            sql = """
            SELECT 
                ki.id,
                ki.issue_id,
                ki.test_version,
                ki.jira_number,
                ki.project,
                ki.test_class_id,
                tc.name as test_class_name,
                ki.script,
                ki.issue_type,
                ki.status,
                ki.error_message,
                ki.supplement,
                ki.created_at,
                CASE 
                    WHEN ki.issue_id ILIKE %s THEN 1.0
                    WHEN ki.project ILIKE %s THEN 0.9
                    WHEN tc.name ILIKE %s THEN 0.8
                    WHEN ki.error_message ILIKE %s THEN 0.7
                    WHEN ki.supplement ILIKE %s THEN 0.6
                    WHEN ki.script ILIKE %s THEN 0.5
                    ELSE 0.3
                END as score
            FROM know_issue ki
            LEFT JOIN test_class tc ON ki.test_class_id = tc.id
            WHERE 
                ki.issue_id ILIKE %s OR 
                ki.project ILIKE %s OR 
                tc.name ILIKE %s OR 
                ki.error_message ILIKE %s OR 
                ki.supplement ILIKE %s OR 
                ki.script ILIKE %s
            ORDER BY score DESC, ki.created_at DESC
            LIMIT %s
            """
            
            search_pattern = f'%{query_text}%'
            cursor.execute(sql, [
                search_pattern, search_pattern, search_pattern, 
                search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern,
                search_pattern, search_pattern, search_pattern,
                limit
            ])
            
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            results = []
            for row in rows:
                issue_data = dict(zip(columns, row))
                
                # 格式化為知識片段
                content = f"問題編號: {issue_data['issue_id']}\n"
                content += f"專案: {issue_data['project']}\n"
                content += f"測試版本: {issue_data['test_version']}\n"
                if issue_data['test_class_name']:
                    content += f"測試類別: {issue_data['test_class_name']}\n"
                if issue_data['jira_number']:
                    content += f"JIRA編號: {issue_data['jira_number']}\n"
                content += f"問題類型: {issue_data['issue_type']}\n"
                content += f"狀態: {issue_data['status']}\n"
                if issue_data['error_message']:
                    content += f"錯誤訊息: {issue_data['error_message']}\n"
                if issue_data['supplement']:
                    content += f"補充說明: {issue_data['supplement']}\n"
                if issue_data['script']:
                    content += f"相關腳本: {issue_data['script']}\n"
                content += f"建立時間: {issue_data['created_at']}"
                
                results.append({
                    'id': str(issue_data['id']),
                    'title': f"{issue_data['issue_id']} - {issue_data['project']}",
                    'content': content,
                    'score': float(issue_data['score']),
                    'metadata': {
                        'source': 'know_issue_database',
                        'issue_id': issue_data['issue_id'],
                        'project': issue_data['project'],
                        'test_version': issue_data['test_version'],
                        'issue_type': issue_data['issue_type'],
                        'status': issue_data['status']
                    }
                })
            
            return results
            
    except Exception as e:
        logger.error(f"Know Issue database search error: {str(e)}")
        return []
```

### 步驟 2：建立統一的 Dify API 端點

修改現有的 `dify_knowledge_search` 函數來支援多個知識庫：

```python
@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def dify_knowledge_search(request):
    """
    Dify 外部知識 API 端點 - 支援多個知識庫
    根據 knowledge_id 自動路由到不同的搜索函數
    """
    try:
        data = json.loads(request.body) if request.body else {}
        query = data.get('query', '')
        knowledge_id = data.get('knowledge_id', 'employee_database')
        retrieval_setting = data.get('retrieval_setting', {})
        
        top_k = retrieval_setting.get('top_k', 5)
        score_threshold = retrieval_setting.get('score_threshold', 0.0)
        
        # 確保分數閾值不會太高
        if score_threshold > 0.9:
            score_threshold = 0.0
        
        logger.info(f"Dify knowledge search - Knowledge ID: {knowledge_id}, Query: '{query}', top_k: {top_k}, score_threshold: {score_threshold}")
        
        if not query:
            return Response({
                'error_code': 2001,
                'error_msg': 'Query parameter is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # 根據 knowledge_id 決定搜索哪個知識庫
        if knowledge_id in ['know_issue_db', 'know_issue', 'know-issue']:
            search_results = search_know_issue_knowledge(query, limit=top_k)
            logger.info(f"Know Issue search results count: {len(search_results)}")
        else:
            # 默認搜索員工知識庫
            search_results = search_postgres_knowledge(query, limit=top_k)
            logger.info(f"Employee search results count: {len(search_results)}")
        
        # 過濾分數低於閾值的結果
        filtered_results = [
            result for result in search_results 
            if result['score'] >= score_threshold
        ]
        
        # 構建符合 Dify 規格的響應
        records = []
        for result in filtered_results:
            records.append({
                'content': result['content'],
                'score': result['score'],
                'title': result['title'],
                'metadata': result['metadata']
            })
        
        return Response({'records': records}, status=status.HTTP_200_OK)
        
    except json.JSONDecodeError:
        return Response({
            'error_code': 1001,
            'error_msg': 'Invalid JSON format'
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Dify knowledge search error: {str(e)}")
        return Response({
            'error_code': 2001,
            'error_msg': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
```

### 步驟 3：配置 URL 路由

在 `urls.py` 中添加完整的路由支援：

```python
# backend/api/urls.py

urlpatterns = [
    # 其他路由...
    
    # Dify 外部知識 API - 支援多種路徑格式
    path('dify/knowledge/retrieval', views.dify_knowledge_search, name='dify_knowledge_search_no_slash'),
    path('dify/knowledge/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search'),
    # Dify 自動附加 /retrieval 的基礎路由
    path('dify/knowledge/', views.dify_knowledge_search, name='dify_knowledge_auto_retrieval'),
    # 相容舊路徑
    path('dify/knowledge/search/', views.dify_knowledge_search, name='dify_knowledge_search_legacy'),
    path('dify/knowledge/search/retrieval/', views.dify_knowledge_search, name='dify_knowledge_search_official'),
]
```

### 步驟 4：測試 API 端點

```bash
# 測試員工知識庫
curl -X POST "http://localhost:8000/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "employee_database",
    "query": "test",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.3
    }
  }'

# 測試 Know Issue 知識庫
curl -X POST "http://localhost:8000/api/dify/knowledge/retrieval/" \
  -H "Content-Type: application/json" \
  -d '{
    "knowledge_id": "know_issue_db",
    "query": "Samsung",
    "retrieval_setting": {
      "top_k": 3,
      "score_threshold": 0.3
    }
  }'
```

## 🛠️ Dify 前端配置步驟

### 步驟 1：創建或修改外部知識 API

1. **進入 Dify → 知識庫 → 外部知識 API**
2. **如果已有 API，修改名稱為通用名稱**：
   ```
   Name: ai_platform_knowledge_api (或 universal_knowledge_api)
   API Endpoint: http://10.10.172.127/api/dify/knowledge
   API Key: (可選，如 "ai-platform-key-2024")
   ```

### 步驟 2：創建外部知識庫

1. **進入 Dify → 知識庫 → 創建知識庫**
2. **選擇資料來源時，點擊「建立一個空知識庫」**
3. **進入「連接到外部知識庫」頁面**
4. **填寫配置**：
   ```
   外部知識名稱: Know Issue Knowledge Base
   知識描述: AI Platform Know Issue Knowledge Base - Provides test issues, error messages, solutions and troubleshooting information.
   外部知識 API: ai_platform_knowledge_api (選擇現有的)
   外部知識 ID: know_issue_db  ← 這是關鍵！
   Top K: 3-5
   Score 閾值: 0.5
   ```

### 步驟 3：測試知識庫

1. **在知識庫頁面進行召回測試**
2. **測試查詢**：
   - `Samsung` → 應返回 Samsung 相關問題
   - `NVMe` → 應返回 NVMe 協議問題
   - `JIRA` → 應返回有 JIRA 編號的問題

## 🔑 關鍵概念

### 1. **一個 API，多個知識庫**
- 使用同一個 API 端點 (`/api/dify/knowledge`)
- 通過 `knowledge_id` 參數區分不同知識庫
- 後端根據 `knowledge_id` 路由到不同的搜索函數

### 2. **knowledge_id 映射**
```python
知識庫配置中的「外部知識 ID」 → API 中的 knowledge_id 參數

員工知識庫: external_knowledge_id = "employee_database"
Know Issue: external_knowledge_id = "know_issue_db"
其他知識庫: external_knowledge_id = "custom_db_name"
```

### 3. **路由兼容性**
支援多種 URL 格式以適應 Dify 的不同調用方式：
- `dify/knowledge/` (基礎路徑，Dify 自動附加 /retrieval)
- `dify/knowledge/retrieval/` (完整路徑)
- `dify/knowledge/retrieval` (無斜槓版本)

## 🧪 測試檢查清單

### API 測試
- [ ] `curl` 測試員工知識庫 (`employee_database`)
- [ ] `curl` 測試 Know Issue 知識庫 (`know_issue_db`)
- [ ] 檢查返回格式符合 Dify 規格
- [ ] 驗證分數計算和排序正確

### Dify 測試
- [ ] 外部知識 API 連接成功
- [ ] 知識庫創建成功
- [ ] 召回測試返回正確資料
- [ ] 聊天應用中知識庫正常調用

## 🚨 常見問題和解決方案

### 問題 1：Dify 前端 API 驗證失敗
**症狀**：`invalid endpoint` 或 `failed to connect` 錯誤
**解決**：
1. 使用基礎路徑：`http://10.10.172.127/api/dify/knowledge`
2. 不要包含 `/retrieval`，讓 Dify 自動附加
3. 確保以 `/` 結尾（但不是 `/retrieval/`）

### 問題 2：知識庫返回錯誤資料
**症狀**：返回員工資料而不是 Know Issue 資料
**解決**：
1. 檢查「外部知識 ID」是否填寫為 `know_issue_db`
2. 確認後端 knowledge_id 判斷邏輯
3. 查看 Django 日誌確認收到的 knowledge_id

### 問題 3：空結果或低相關性
**症狀**：API 返回 `{"records":[]}`
**解決**：
1. 降低 Score 閾值到 0.3 或更低
2. 檢查搜索關鍵字是否存在於資料庫
3. 驗證資料庫表名和欄位名正確

## 📊 擴展指南

### 添加新知識庫
1. **建立新的搜索函數**：`search_new_knowledge(query, limit)`
2. **修改 knowledge_id 判斷邏輯**：
   ```python
   elif knowledge_id in ['new_db', 'new-db']:
       search_results = search_new_knowledge(query, limit=top_k)
   ```
3. **在 Dify 中創建新的外部知識庫**，使用相應的 `external_knowledge_id`

### 優化搜索功能
1. **改善分數計算**：調整不同欄位的權重
2. **添加模糊搜索**：使用 PostgreSQL 的 `similarity()` 函數
3. **支援多語言**：添加中英文搜索支援
4. **緩存機制**：使用 Redis 緩存熱門查詢

## 🎯 成功標準

一個正確配置的 Dify 外部知識庫系統應該滿足：

1. ✅ **API 測試成功**：curl 請求返回正確知識庫資料
2. ✅ **多知識庫支援**：能根據 knowledge_id 正確路由
3. ✅ **Dify 召回測試成功**：在知識庫管理中能看到搜索結果
4. ✅ **聊天測試成功**：AI 回答具體知識而非通用描述
5. ✅ **擴展性良好**：易於添加新的知識庫

---

**建立日期**: 2025-01-15  
**版本**: v2.0  
**狀態**: ✅ 生產可用  
**架構**: 統一 API + 多知識庫路由  
**負責人**: AI Platform Team

## 📝 變更記錄

### v2.0 (2025-01-15)
- 實現統一 API 支援多知識庫
- 添加 knowledge_id 路由機制
- 簡化 Dify 前端配置流程
- 解決路徑重複和驗證問題

### v1.0 (2025-01-14)
- 初始版本，獨立 API 端點方案
- 基礎 Know Issue 知識庫實現