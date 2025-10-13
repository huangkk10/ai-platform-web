# 🔄 RVT Assistant 分析系統運作流程圖

## 📋 **系統運作概覽**

```mermaid
graph TB
    A[用戶提問] --> B[ChatMessage 存儲]
    B --> C{向量化處理}
    C -->|每小時執行| D[生成 1024維向量]
    D --> E[存儲到向量表]
    E --> F{問題分析}
    F -->|每日執行| G[聚類分析]
    F -->|每日執行| H[頻率統計]
    G --> I[智慧分析引擎]
    H --> I
    I --> J{檢測聚類問題}
    J -->|有問題| K[選擇頻率模式]
    J -->|無問題| L[選擇聚類模式]
    K --> M[前端顯示結果]
    L --> M
```

---

## 🎯 **智慧分析決策流程**

```mermaid
flowchart TD
    Start([API 請求 mode=smart]) --> GetData[獲取頻率+聚類數據]
    GetData --> Compare[比較兩種分析結果]
    Compare --> CheckDiff{檢查差異度}
    
    CheckDiff -->|差異 < 2倍| UseCluster[使用聚類模式]
    CheckDiff -->|差異 ≥ 2倍| CountProblems{問題數量 ≥ 2?}
    
    CountProblems -->|Yes| UseFreq[使用頻率模式]
    CountProblems -->|No| UseCluster
    
    UseFreq --> AddReport[添加差異報告]
    AddReport --> Response[返回頻率結果]
    UseCluster --> Response2[返回聚類結果]
    
    Response --> Frontend[前端顯示 🤖智慧分析]
    Response2 --> Frontend
```

---

## 🕐 **定時任務執行時序**

```mermaid
gantt
    title RVT Assistant 定時任務執行計劃
    dateFormat HH:mm
    axisFormat %H:%M
    
    section 每小時任務
    用戶問題向量化    :active, hourly1, 00:00, 10m
    用戶問題向量化    :hourly2, 01:00, 10m
    用戶問題向量化    :hourly3, 02:00, 10m
    用戶問題向量化    :hourly4, 03:00, 10m
    
    section 每日凌晨任務  
    快取清理        :cleanup, 02:00, 15m
    向量服務預載入   :preload, 03:00, 20m
    問題分類更新    :analytics, 03:30, 30m
    
    section 每6小時任務
    助手回覆向量化   :assistant1, 00:30, 15m
    助手回覆向量化   :assistant2, 06:30, 15m
    助手回覆向量化   :assistant3, 12:30, 15m
    助手回覆向量化   :assistant4, 18:30, 15m
```

---

## 🗄️ **數據流架構**

```mermaid
erDiagram
    ChatMessage {
        int id PK
        text content
        string role
        timestamp created_at
        int conversation_id
        boolean is_helpful
    }
    
    ChatEmbeddings {
        int id PK
        int chat_message_id FK
        text text_content
        vector embedding
        string user_role
        int cluster_id
        float confidence_score
        timestamp created_at
    }
    
    AnalyticsCache {
        string cache_key PK
        json data
        timestamp expires_at
    }
    
    ChatMessage ||--o| ChatEmbeddings : "vectorizes"
    ChatEmbeddings }o--|| AnalyticsCache : "aggregates_to"
```

---

## 🌊 **前端數據流**

```mermaid
sequenceDiagram
    participant U as 用戶瀏覽器
    participant F as React 前端
    participant A as Django API
    participant E as 分析引擎
    participant D as 資料庫
    
    U->>F: 訪問分析頁面
    F->>A: GET /api/rvt-analytics/questions/?mode=smart
    A->>E: 調用智慧分析
    E->>D: 查詢聊天記錄
    E->>D: 查詢向量數據
    E->>E: 執行差異檢測
    E->>A: 返回最佳分析結果
    A->>F: JSON 響應 + 分析元數據
    F->>U: 渲染熱門問題排名
    
    Note over F,U: 顯示分析模式標籤<br/>🤖 智慧分析 (頻率模式)
```

---

## 🔧 **問題診斷流程**

```mermaid
flowchart TD
    Problem([用戶回報問題]) --> Identify{問題類型識別}
    
    Identify -->|數據不更新| CheckTasks[檢查定時任務]
    Identify -->|排名異常| CheckMode[檢查分析模式]
    Identify -->|API 錯誤| CheckAuth[檢查權限認證]
    
    CheckTasks --> TaskStatus{任務運行狀態}
    TaskStatus -->|正常| ManualUpdate[手動執行更新]
    TaskStatus -->|異常| RestartCelery[重啟 Celery 服務]
    
    CheckMode --> ModeCheck{使用智慧模式?}
    ModeCheck -->|No| SwitchSmart[切換到 mode=smart]
    ModeCheck -->|Yes| CheckClustering[檢查聚類問題]
    
    CheckAuth --> AuthStatus{用戶權限}
    AuthStatus -->|無權限| GrantAdmin[分配管理員權限]
    AuthStatus -->|有權限| CheckAPI[檢查 API 端點]
    
    ManualUpdate --> TestResult[測試結果]
    RestartCelery --> TestResult
    SwitchSmart --> TestResult
    CheckClustering --> TestResult
    GrantAdmin --> TestResult
    CheckAPI --> TestResult
    
    TestResult --> Success[問題解決]
```

---

## 📊 **性能監控指標**

```mermaid
graph LR
    subgraph "數據指標"
        A[向量化覆蓋率] --> A1[目標: >80%]
        B[聚類準確度] --> B1[檢測差異問題]
        C[響應時間] --> C1[API <2秒]
    end
    
    subgraph "任務指標"  
        D[定時任務成功率] --> D1[目標: 100%]
        E[向量處理速度] --> E1[~5 消息/秒]
        F[統計更新延遲] --> F1[<24小時]
    end
    
    subgraph "用戶體驗"
        G[智慧分析準確性] --> G1[差異檢測率]
        H[前端載入速度] --> H1[<3秒顯示]
        I[數據新鮮度] --> I1[最新問題可見]
    end
```

---

## 🔄 **系統自癒機制**

```mermaid
flowchart TB
    Monitor[系統監控] --> Detect{檢測異常}
    
    Detect -->|向量化率低| AutoRebuild[自動重建向量]
    Detect -->|聚類問題| AutoSwitch[自動切換模式]
    Detect -->|任務失敗| RetryTask[任務重試機制]
    
    AutoRebuild --> Health1{健康檢查}
    AutoSwitch --> Health2{健康檢查}  
    RetryTask --> Health3{健康檢查}
    
    Health1 -->|成功| Normal[恢復正常]
    Health2 -->|成功| Normal
    Health3 -->|成功| Normal
    
    Health1 -->|失敗| Alert[發送警報]
    Health2 -->|失敗| Alert
    Health3 -->|失敗| Alert
    
    Alert --> Manual[手動干預]
    Manual --> Fix[問題修復]
    Fix --> Normal
```

---

## 🚀 **部署更新流程**

```mermaid
gitgraph
    commit id: "開發新功能"
    branch feature
    checkout feature
    commit id: "實現智慧分析"
    commit id: "添加前端顯示"
    checkout main
    merge feature
    commit id: "測試通過"
    commit id: "部署到生產" tag: "v2.1"
    
    commit id: "監控運行狀態"
    branch hotfix
    checkout hotfix
    commit id: "修復聚類問題"
    checkout main
    merge hotfix
    commit id: "熱修復部署" tag: "v2.1.1"
```

---

## 📋 **運維檢查清單**

### **日常監控** ✅
- [ ] Celery Beat 任務執行狀態
- [ ] 向量化處理成功率
- [ ] API 響應時間監控
- [ ] 資料庫連接健康度
- [ ] 前端頁面載入正常

### **週期性維護** 🔧
- [ ] 清理過期向量數據
- [ ] 重建向量索引
- [ ] 更新聚類參數
- [ ] 備份統計數據
- [ ] 性能基準測試

### **故障應對** 🚨
- [ ] 定時任務失敗處理
- [ ] 向量服務異常恢復
- [ ] API 端點故障修復
- [ ] 數據不一致修正
- [ ] 前端顯示異常處理

---

**🎯 此流程圖文檔幫助 AI 助手理解系統各組件間的協作關係和數據流轉過程。**