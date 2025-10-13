# 🤖 RVT Assistant 分析報告系統完整架構文檔

## 📖 **文檔目的**
此文檔詳細說明 RVT Assistant 分析報告系統的運作方式，供 AI 助手和開發者理解系統架構、數據流程和功能實現。

---

## 🏗️ **系統架構概覽**

### **核心組件架構**
```
Web前端 (React) 
    ↓ API 請求
後端 API (Django REST) 
    ↓ 調用
分析引擎 (Python Libraries)
    ↓ 查詢
資料庫層 (PostgreSQL + 向量資料庫)
    ↓ 處理
定時任務 (Celery Beat)
```

### **主要模組結構**
```
/library/rvt_analytics/
├── api_handlers.py          # API 端點處理器
├── statistics_manager.py    # 統計數據管理器  
├── vector_question_analyzer.py  # 向量化問題分析器
├── question_classifier.py   # 問題分類器
├── satisfaction_analyzer.py # 滿意度分析器
├── chat_vector_service.py   # 聊天向量服務
├── chat_clustering_service.py # 聊天聚類服務
├── message_feedback.py     # 消息反饋處理
├── tasks.py               # Celery 定時任務
└── __init__.py            # 模組初始化
```

---

## 📊 **分析模式系統**

### **三種分析模式**

#### 1. **聚類分析模式** (`mode=clustered`)
- **用途**：發現問題模式和趨勢
- **原理**：使用向量聚類演算法將語義相似的問題歸併
- **優點**：能識別問題類型和模式
- **缺點**：可能掩蓋具體問題的真實頻率

#### 2. **原始頻率模式** (`mode=frequency`) 
- **用途**：顯示真實問題排名
- **原理**：直接統計每個問題的出現次數
- **優點**：準確反映用戶實際關注點
- **缺點**：相似問題會分散排名

#### 3. **智慧分析模式** (`mode=smart`) ⭐
- **用途**：自動選擇最適合的分析模式
- **原理**：檢測聚類是否掩蓋高頻問題，自動切換模式
- **決策邏輯**：
  ```python
  if 檢測到 >= 2個高頻問題被聚類掩蓋:
      使用頻率模式
  else:
      使用聚類模式
  ```

---

## 🔄 **數據處理流程**

### **1. 聊天數據收集**
```mermaid
用戶提問 → ChatMessage 模型存儲 → 等待向量化處理
```

### **2. 向量化處理** (定時任務)
```python
# 每小時執行 (crontab: minute=0)
process-new-chat-vectors-hourly:
    - 處理未向量化的用戶問題
    - 生成 1024 維向量
    - 存儲到 chat_message_embeddings_1024 表
```

### **3. 問題分析處理** (每日執行)
```python  
# 每日凌晨 3:30 執行
update-question-analytics-daily:
    - 重新計算聚類
    - 更新熱門問題排名
    - 刷新統計快取
```

### **4. 前端數據展示**
```javascript
// API 請求流程
fetch('/api/rvt-analytics/questions/?days=7&mode=smart')
    ↓
智慧分析引擎處理
    ↓
返回最佳分析結果
```

---

## 🗄️ **數據庫架構**

### **核心資料表**

#### **chat_messages** (聊天消息表)
```sql
- id: 主鍵
- content: 聊天內容
- role: 角色 (user/assistant)  
- created_at: 創建時間
- conversation_id: 對話 ID
- is_helpful: 反饋狀態
```

#### **chat_message_embeddings_1024** (向量表)
```sql
- id: 主鍵
- chat_message_id: 關聯聊天消息
- text_content: 文本內容
- embedding: 1024維向量 (pgvector)
- user_role: 用戶角色
- cluster_id: 聚類 ID
- predicted_category: 預測分類
- confidence_score: 信心分數
- created_at: 創建時間
```

### **關鍵索引**
```sql
-- 向量搜索索引
CREATE INDEX chat_embeddings_vector_idx 
ON chat_message_embeddings_1024 
USING ivfflat (embedding vector_cosine_ops);

-- 查詢優化索引
CREATE INDEX chat_embeddings_cluster_idx ON chat_message_embeddings_1024(cluster_id);
CREATE INDEX chat_embeddings_message_id_idx ON chat_message_embeddings_1024(chat_message_id);
```

---

## 🔧 **API 端點系統**

### **主要 API 端點**

#### **1. 問題分析 API**
```http
GET /api/rvt-analytics/questions/
Parameters:
- days: 統計天數 (default: 7)
- mode: 分析模式 (clustered/frequency/smart)
- category: 分類過濾 (optional)

Response:
{
  "success": true,
  "data": {
    "analysis_method": "smart_frequency",
    "reason": "檢測到3個高頻問題被聚類掩蓋，使用頻率模式",
    "total_questions": 178,
    "popular_questions": [...],
    "category_distribution": {...},
    "discrepancies": [...]  // 智慧模式特有
  }
}
```

#### **2. 滿意度分析 API**
```http
GET /api/rvt-analytics/satisfaction/
Parameters:
- days: 統計天數 (default: 30)
- detail: 詳細分析 (true/false)
```

#### **3. 概覽統計 API**
```http
GET /api/rvt-analytics/overview/
Parameters:
- days: 統計天數 (default: 30)
- user_id: 特定用戶 (admin only)
```

---

## 🎯 **智慧分析演算法**

### **差異檢測邏輯**
```python
def detect_clustering_issues(freq_analysis, cluster_analysis):
    """檢測聚類是否掩蓋高頻問題"""
    major_discrepancies = []
    
    for freq_question in freq_analysis:
        freq_count = freq_question['count']
        
        # 在聚類結果中尋找對應問題
        for cluster_group in cluster_analysis:
            if question_matches_cluster(freq_question, cluster_group):
                cluster_count = cluster_group['count']
                
                # 如果頻率差異超過2倍，標記為問題
                if freq_count > cluster_count * 2:
                    major_discrepancies.append({
                        'severity': freq_count / cluster_count,
                        'original_count': freq_count,
                        'cluster_count': cluster_count
                    })
    
    return major_discrepancies
```

### **模式選擇決策**
```python
def choose_analysis_mode(discrepancies):
    """根據差異情況選擇分析模式"""
    if len(discrepancies) >= 2:  # 有2個以上嚴重差異
        return "frequency_mode"  # 使用頻率模式
    else:
        return "clustered_mode"  # 使用聚類模式
```

---

## ⚙️ **定時任務系統**

### **Celery Beat 配置** (`backend/ai_platform/celery.py`)

```python
app.conf.beat_schedule = {
    # 每小時處理新的聊天向量
    'process-new-chat-vectors-hourly': {
        'task': 'library.rvt_analytics.tasks.rebuild_chat_vectors',
        'schedule': crontab(minute=0),  # 每小時 0 分執行
        'kwargs': {
            'force_rebuild': False,
            'user_role': 'user',
            'min_length': 5
        }
    },
    
    # 每天更新問題分類統計
    'update-question-analytics-daily': {
        'task': 'library.rvt_analytics.tasks.precompute_question_classifications',
        'schedule': crontab(hour=3, minute=30),  # 每天凌晨 3:30
    }
}
```

### **任務執行流程**
1. **向量重建任務**：處理未向量化的聊天記錄
2. **問題分類任務**：更新聚類和統計
3. **快取清理任務**：清理過期數據

---

## 🎨 **前端實現**

### **React 組件結構**
```javascript
RVTAnalyticsPage.js
├── fetchAnalyticsData()     // 數據獲取
├── renderQuestionAnalysis() // 問題分析渲染
├── preparePopularQuestionsData() // 數據準備
└── 智慧分析說明組件         // 模式說明
```

### **關鍵 API 調用**
```javascript
// 使用智慧分析模式
fetch(`/api/rvt-analytics/questions/?days=${days}&mode=smart`)
```

### **前端狀態管理**
```javascript
const [questionData, setQuestionData] = useState(null);
// questionData 包含：
// - analysis_method: 分析方法
// - reason: 選擇原因  
// - popular_questions: 熱門問題
// - discrepancies: 差異報告
```

---

## 🔍 **問題聚類系統**

### **向量聚類演算法**
- **模型**：multilingual-e5-large (1024維)
- **聚類方法**：K-means + DBSCAN
- **相似度計算**：餘弦相似度
- **閾值設定**：0.7 (可調整)

### **聚類問題檢測**
系統會檢測以下聚類問題：
1. **過度合併**：不同主題被歸為同類
2. **頻率掩蓋**：高頻問題被稀釋
3. **語義混淆**：相似表述但不同含義

---

## 📈 **性能優化**

### **向量化效率**
- **批量處理**：~5 消息/秒
- **增量更新**：只處理未向量化記錄
- **重複檢測**：content_hash 避免重複

### **查詢優化**
- **索引策略**：向量索引 + 復合索引
- **快取機制**：統計結果快取
- **分頁查詢**：大數據集分批處理

---

## 🛠️ **故障診斷**

### **常見問題排除**

#### **1. 熱門問題不更新**
```bash
# 檢查定時任務狀態
docker logs ai-celery-beat --tail 20
docker logs ai-celery-worker --tail 20

# 手動執行更新
docker exec ai-django python manage.py shell -c "
from library.rvt_analytics.tasks import precompute_question_classifications
result = precompute_question_classifications()
print(result)
"
```

#### **2. 向量化率低**
```bash
# 檢查向量化覆蓋率
docker exec postgres_db psql -U postgres -d ai_platform -c "
SELECT 
  COUNT(*) as total_messages,
  COUNT(cme.id) as vectorized_messages,
  ROUND(COUNT(cme.id) * 100.0 / COUNT(*), 2) as coverage_rate
FROM chat_messages cm
LEFT JOIN chat_message_embeddings_1024 cme ON cm.id = cme.chat_message_id
WHERE cm.role = 'user';
"
```

#### **3. API 權限問題**
- 確認用戶具有 `is_staff` 權限
- 檢查 session 認證狀態
- 驗證 CSRF token 設置

---

## 🔮 **系統擴展**

### **新增分析模式**
1. 在 `api_handlers.py` 添加新模式處理
2. 實現對應的分析函數
3. 更新前端模式選擇邏輯

### **新增統計維度**
1. 擴展 `statistics_manager.py`
2. 添加對應的資料庫查詢
3. 更新 API 回應格式

### **性能調優**
1. 調整聚類參數 (`similarity_threshold`)
2. 優化向量索引配置
3. 增加快取層級

---

## 📚 **相關文檔**

- **向量搜尋系統**: `/docs/vector-search-guide.md`
- **定時任務架構**: `/docs/celery-beat-architecture-guide.md`  
- **API 整合指南**: `/docs/guide/api-integration.md`
- **前端開發規範**: `/docs/ui-component-guidelines.md`

---

## 🎯 **AI 助手指導原則**

### **回答用戶問題時**：

1. **數據更新問題**：參考定時任務機制（每小時向量化，每日統計更新）
2. **分析結果異常**：優先檢查智慧分析模式是否啟用
3. **性能問題**：檢查向量化覆蓋率和索引狀態
4. **API 錯誤**：驗證用戶權限和參數格式

### **系統診斷流程**：

1. **檢查服務狀態** → Celery Beat/Worker 運行狀態
2. **驗證數據完整性** → 向量化覆蓋率檢查  
3. **測試 API 功能** → 手動調用分析函數
4. **檢查前端集成** → 確認 mode 參數傳遞

---

## 🏷️ **版本資訊**

- **文檔版本**: v1.0
- **系統版本**: AI Platform v2.1
- **最後更新**: 2025-10-13
- **維護者**: AI Platform Team

**🤖 此文檔專為 AI 助手設計，包含完整的系統運作邏輯和診斷方法。**