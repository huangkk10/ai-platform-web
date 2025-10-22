# Common Analytics Library

共用分析基礎設施，為所有 Assistant 提供統一的分析功能架構。

## 📋 概述

本 Library 提供可重用的基礎類別，讓各個 Assistant（RVT, Protocol, QA 等）能夠快速建立自己的分析系統。

## 🏗️ 架構設計

### 核心組件

1. **BaseStatisticsManager** - 統計管理器基礎類別
2. **BaseQuestionAnalyzer** - 問題分析器基礎類別
3. **BaseSatisfactionAnalyzer** - 滿意度分析器基礎類別
4. **BaseAPIHandler** - API 處理器基礎類別

### 設計原則

- **抽象基礎類別（ABC）**：使用 Python ABC 定義抽象介面
- **共用邏輯**：將 80% 的共用邏輯放在基礎類別
- **靈活擴展**：子類別只需實作 20% 的專屬邏輯
- **統一介面**：所有 Assistant 使用相同的 API 介面

## 🚀 使用方式

### 步驟 1：創建 Assistant 專屬的統計管理器

```python
# library/protocol_analytics/statistics_manager.py

from library.common.analytics.base_statistics_manager import BaseStatisticsManager

class ProtocolStatisticsManager(BaseStatisticsManager):
    """Protocol Assistant 統計管理器"""
    
    def get_assistant_type(self) -> str:
        return 'protocol_assistant'
    
    def get_conversation_model(self):
        from api.models import ConversationSession
        return ConversationSession
    
    def get_message_model(self):
        from api.models import ChatMessage
        return ChatMessage
```

### 步驟 2：創建問題分析器

```python
# library/protocol_analytics/question_analyzer.py

from library.common.analytics.base_question_analyzer import BaseQuestionAnalyzer

class ProtocolQuestionAnalyzer(BaseQuestionAnalyzer):
    """Protocol Assistant 問題分析器"""
    
    def get_assistant_type(self) -> str:
        return 'protocol_assistant'
    
    def get_message_model(self):
        from api.models import ChatMessage
        return ChatMessage
    
    def get_conversation_model(self):
        from api.models import ConversationSession
        return ConversationSession
    
    def get_question_categories(self) -> list:
        """覆寫預設分類以提供 Protocol 專屬分類"""
        return [
            'Protocol 配置問題',
            'Protocol 測試問題',
            'Protocol 錯誤排除',
            '其他'
        ]
```

### 步驟 3：創建滿意度分析器

```python
# library/protocol_analytics/satisfaction_analyzer.py

from library.common.analytics.base_satisfaction_analyzer import BaseSatisfactionAnalyzer

class ProtocolSatisfactionAnalyzer(BaseSatisfactionAnalyzer):
    """Protocol Assistant 滿意度分析器"""
    
    def get_assistant_type(self) -> str:
        return 'protocol_assistant'
    
    def get_message_model(self):
        from api.models import ChatMessage
        return ChatMessage
    
    def get_conversation_model(self):
        from api.models import ConversationSession
        return ConversationSession
```

### 步驟 4：創建 API 處理器

```python
# library/protocol_analytics/api_handler.py

from library.common.analytics.base_api_handler import BaseAPIHandler
from .statistics_manager import ProtocolStatisticsManager
from .question_analyzer import ProtocolQuestionAnalyzer
from .satisfaction_analyzer import ProtocolSatisfactionAnalyzer

class ProtocolAnalyticsAPIHandler(BaseAPIHandler):
    """Protocol Assistant Analytics API 處理器"""
    
    def __init__(self):
        super().__init__()
        self._stats_manager = ProtocolStatisticsManager()
        self._question_analyzer = ProtocolQuestionAnalyzer()
        self._satisfaction_analyzer = ProtocolSatisfactionAnalyzer()
    
    def get_assistant_type(self) -> str:
        return 'protocol_assistant'
    
    def get_statistics_manager(self):
        return self._stats_manager
    
    def get_question_analyzer(self):
        return self._question_analyzer
    
    def get_satisfaction_analyzer(self):
        return self._satisfaction_analyzer
```

### 步驟 5：註冊 API 端點

```python
# backend/api/views/analytics_views.py

from library.protocol_analytics.api_handler import ProtocolAnalyticsAPIHandler

protocol_handler = ProtocolAnalyticsAPIHandler()

def protocol_analytics_overview(request):
    """Protocol 分析概覽 API"""
    result = protocol_handler.handle_analytics_overview_api(request)
    return JsonResponse(result)

def protocol_analytics_questions(request):
    """Protocol 問題分析 API"""
    result = protocol_handler.handle_question_analysis_api(request)
    return JsonResponse(result)

def protocol_analytics_satisfaction(request):
    """Protocol 滿意度分析 API"""
    result = protocol_handler.handle_satisfaction_analysis_api(request)
    return JsonResponse(result)

def protocol_analytics_feedback(request):
    """Protocol 反饋 API"""
    result = protocol_handler.handle_message_feedback_api(request)
    return JsonResponse(result)
```

```python
# backend/api/urls.py

urlpatterns = [
    # Protocol Analytics APIs
    path('protocol-analytics/overview/', views.protocol_analytics_overview),
    path('protocol-analytics/questions/', views.protocol_analytics_questions),
    path('protocol-analytics/satisfaction/', views.protocol_analytics_satisfaction),
    path('protocol-analytics/feedback/', views.protocol_analytics_feedback),
]
```

## 📊 前端使用範例

### 創建前端頁面（複製 RVTAnalyticsPage）

```javascript
// frontend/src/pages/ProtocolAnalyticsPage.js

import React, { useState, useEffect } from 'react';
// ... 其他 imports（與 RVTAnalyticsPage 相同）

const ProtocolAnalyticsPage = () => {
  // ... 狀態管理（與 RVTAnalyticsPage 相同）
  
  const fetchAnalyticsData = async () => {
    // 🔄 只需修改 API 端點前綴
    const [overviewResponse, questionResponse, satisfactionResponse] = await Promise.all([
      fetch(`/api/protocol-analytics/overview/?days=${selectedDays}`),
      fetch(`/api/protocol-analytics/questions/?days=${selectedDays}&mode=smart`),
      fetch(`/api/protocol-analytics/satisfaction/?days=${selectedDays}&detail=true`)
    ]);
    
    // ... 其餘邏輯完全相同
  };
  
  // ... 其餘組件邏輯（與 RVTAnalyticsPage 相同）
};

export default ProtocolAnalyticsPage;
```

### 註冊前端路由

```javascript
// frontend/src/App.js

import ProtocolAnalyticsPage from './pages/ProtocolAnalyticsPage';

<Route path="/admin/protocol-analytics" element={<ProtocolAnalyticsPage />} />
```

## 🎯 核心優勢

### 1. **代碼複用率高**

- ✅ 統計邏輯：100% 複用
- ✅ 性能分析：100% 複用
- ✅ 趨勢分析：100% 複用
- ✅ API 處理：90% 複用
- ✅ 前端頁面：95% 複用（只需改 API 端點）

### 2. **一致性**

- ✅ 所有 Assistant 使用相同的 API 介面
- ✅ 統一的數據格式
- ✅ 統一的錯誤處理

### 3. **易於維護**

- ✅ 共用邏輯集中管理
- ✅ Bug 修復一次即可惠及所有 Assistant
- ✅ 功能增強同步更新

### 4. **快速開發**

- ✅ 新 Assistant 分析系統可在 **2-3 小時內完成**
- ✅ 只需實作 20% 的專屬邏輯
- ✅ 大部分代碼直接複製粘貼

## 📋 新 Assistant 開發檢查清單

創建新 Assistant 分析系統時：

### 後端 Library（2 小時）
- [ ] 創建 `library/{assistant}_analytics/` 目錄
- [ ] 創建 `statistics_manager.py`（繼承 BaseStatisticsManager）
- [ ] 創建 `question_analyzer.py`（繼承 BaseQuestionAnalyzer）
- [ ] 創建 `satisfaction_analyzer.py`（繼承 BaseSatisfactionAnalyzer）
- [ ] 創建 `api_handler.py`（繼承 BaseAPIHandler）
- [ ] 創建 `__init__.py`（導出主要類別）

### 後端 API（30 分鐘）
- [ ] 在 `analytics_views.py` 中添加 4 個 view 函數
- [ ] 在 `urls.py` 中註冊 4 個 API 端點
- [ ] 測試 API 端點（使用 curl 或 Postman）

### 前端頁面（1 小時）
- [ ] 複製 `RVTAnalyticsPage.js` 為 `{Assistant}AnalyticsPage.js`
- [ ] 修改 API 端點前綴（`rvt-analytics` → `{assistant}-analytics`）
- [ ] 修改頁面標題和文字
- [ ] 在 `App.js` 中註冊路由
- [ ] 在 `Sidebar.js` 中添加選單項目

### 測試驗證（30 分鐘）
- [ ] 測試概覽 API
- [ ] 測試問題分析 API
- [ ] 測試滿意度 API
- [ ] 測試反饋 API
- [ ] 前端頁面功能測試

**總計時間：約 4 小時**

## 🔧 高級功能

### 覆寫專屬邏輯

如果需要實作專屬邏輯，可以覆寫基礎類別的方法：

```python
class ProtocolQuestionAnalyzer(BaseQuestionAnalyzer):
    def _smart_analyze_popular_questions(self, questions):
        """覆寫智慧分析邏輯（使用 Protocol 專屬的向量服務）"""
        # 實作 Protocol 專屬的向量聚類邏輯
        pass
    
    def get_question_categories(self):
        """覆寫問題分類"""
        return ['Protocol 配置', 'Protocol 測試', 'Protocol 錯誤']
```

### 添加額外過濾條件

```python
class ProtocolStatisticsManager(BaseStatisticsManager):
    def get_additional_conversation_filters(self):
        """添加 Protocol 專屬的過濾條件"""
        return {
            'protocol_version__isnull': False  # 只統計有 protocol_version 的對話
        }
```

## 📚 參考範例

### 完整實作範例
- **RVT Analytics**：`library/rvt_analytics/`（已重構為使用基礎類別）

### 文檔
- 架構設計：`docs/architecture/common-analytics-architecture.md`
- API 規格：`docs/api/common-analytics-api-spec.md`

## 🎓 學習資源

### Python ABC (Abstract Base Classes)
- 官方文檔：https://docs.python.org/3/library/abc.html
- 用於定義抽象介面和強制子類別實作特定方法

### Django ORM
- 查詢優化：使用 `select_related()`, `prefetch_related()`
- 聚合函數：`Count()`, `Avg()`, `Max()`, `Min()`

---

**📅 更新日期**: 2025-10-23  
**📝 版本**: v1.0  
**✍️ 作者**: AI Platform Team  
**🎯 用途**: 提供統一的 Analytics 基礎設施
